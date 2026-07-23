"""Submit a prepared storyboard run to Seedance through BytePlus ModelArk.

This runner is meant for the user's local terminal. Codex prepares the run
directory, storyboard frames, and Seedance prompt; the local runner reads the
ignored `.env.local` or environment for the API key, submits the async task,
polls it, and downloads the returned video.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import json
import mimetypes
import os
from pathlib import Path
import re
import sys
import time
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import manifest
import validate_output


ROOT = Path(__file__).parents[2]
LOCAL_ENV = ROOT / ".env.local"
DEFAULT_ENDPOINT = "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks"
DEFAULT_MODEL = "dreamina-seedance-2-0-260128"
DEFAULT_RATIO = "9:16"
DEFAULT_RATIOS = {
    "vertical-video": "9:16",
    "video": "16:9",
}
DEFAULT_RESOLUTION = "1080p"
DEFAULT_GENERATE_AUDIO = True
DEFAULT_WATERMARK = False
NO_SUBTITLE_POLICY = (
    "No subtitles, captions, title cards, lower-thirds, burned-in text, "
    "or any on-screen text. Voiceover and natural cooking audio are allowed "
    "if the selected model supports audio."
)
DEFAULT_DURATION = "5"
DEFAULT_TIMEOUT = 1800
DEFAULT_POLL_INTERVAL = 10
TERMINAL_FAILURES = {"failed", "cancelled"}
KEY_ENV_NAMES = [
    "BYTEPLUS_ARK_API_KEY",
    "BYTEPLUS_API_KEY",
    "VSR_SEEDANCE_API_KEY",
    "ARK_API_KEY",
    "SEEDANCE_API_KEY",
]
TRUTHY = {"1", "true", "yes", "y", "on"}
FALSY = {"0", "false", "no", "n", "off"}


class SeedanceRunnerError(RuntimeError):
    """Raised when Seedance generation cannot complete."""


class SeedanceHTTPError(RuntimeError):
    def __init__(self, code: int, body: str):
        self.code = code
        self.body = body
        super().__init__(f"Seedance HTTP {code}: {body}")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_env_file(path: Path | None = None) -> None:
    env_path = path or LOCAL_ENV
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _api_key() -> str | None:
    for name in KEY_ENV_NAMES:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _supports_seed(model: str) -> bool:
    return "seedance-2-0" not in model.lower()


def resolve_config(*, model: str | None = None, endpoint: str | None = None) -> dict[str, Any]:
    _load_env_file()
    return {
        "provider": "byteplus-modelark",
        "model": model or os.environ.get("VSR_SEEDANCE_MODEL", DEFAULT_MODEL),
        "endpoint": endpoint or os.environ.get("VSR_SEEDANCE_ENDPOINT", DEFAULT_ENDPOINT),
        "api_key": _api_key(),
    }


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    normalized = value.strip().lower()
    if normalized in TRUTHY:
        return True
    if normalized in FALSY:
        return False
    raise SeedanceRunnerError(
        f"{name} must be a boolean value such as true/false, 1/0, yes/no, or on/off"
    )


def resolve_generation_options(
    *,
    platform: str,
    ratio: str | None = None,
    duration: str | int | None = None,
    resolution: str | None = None,
    generate_audio: bool | None = None,
    watermark: bool | None = None,
) -> dict[str, Any]:
    default_ratio = DEFAULT_RATIOS.get(platform, DEFAULT_RATIO)
    duration_value = (
        duration
        if duration is not None
        else os.environ.get("VSR_SEEDANCE_DURATION", DEFAULT_DURATION)
    )
    try:
        parsed_duration = int(duration_value)
    except (TypeError, ValueError) as exc:
        raise SeedanceRunnerError("Seedance duration must be an integer number of seconds") from exc
    if parsed_duration <= 0:
        raise SeedanceRunnerError("Seedance duration must be greater than zero")

    return {
        "ratio": ratio or os.environ.get("VSR_SEEDANCE_RATIO", default_ratio),
        "duration": parsed_duration,
        "resolution": resolution or os.environ.get("VSR_SEEDANCE_RESOLUTION", DEFAULT_RESOLUTION),
        "generate_audio": (
            generate_audio
            if generate_audio is not None
            else _env_bool("VSR_SEEDANCE_GENERATE_AUDIO", DEFAULT_GENERATE_AUDIO)
        ),
        "watermark": (
            watermark
            if watermark is not None
            else _env_bool("VSR_SEEDANCE_WATERMARK", DEFAULT_WATERMARK)
        ),
    }


def _relative_to_run(path: str | Path, run_dir: Path) -> str:
    target = Path(path).resolve()
    try:
        return target.relative_to(run_dir).as_posix()
    except ValueError:
        return str(target)


def _page_label(asset_id: str) -> str:
    match = re.search(r"(\d+)$", asset_id)
    if match:
        return f"page-{int(match.group(1)):02d}"
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", asset_id).strip(".-")
    return f"page-{cleaned or asset_id}"


def _generated_path(run_dir: Path, asset_id: str) -> Path:
    return run_dir / "generated" / f"{_page_label(asset_id)}.png"


def _expected_storyboard_ids() -> list[str]:
    return [f"{index:02d}" for index in range(1, 10)]


def _validate_storyboard_ready(
    run_dir: Path,
    data: dict[str, Any],
    platform: str,
    asset_ids: list[str],
) -> None:
    expected_ids = _expected_storyboard_ids()
    if asset_ids != expected_ids:
        raise SeedanceRunnerError(
            "Seedance requires exactly 9 storyboard assets with ids 01 through 09 "
            f"before submission; found {', '.join(asset_ids) or 'none'}"
        )

    expected_size = validate_output.DIMENSIONS[platform]
    errors: list[str] = []
    for asset_id in expected_ids:
        item = data.get("assets", {}).get(asset_id, {})
        if item.get("status") != "validated":
            errors.append(f"asset {asset_id} is not validated")

        image_path = _generated_path(run_dir, asset_id)
        if not image_path.is_file():
            errors.append(f"missing {image_path.relative_to(run_dir).as_posix()}")
            continue
        try:
            with Image.open(image_path) as image:
                if image.size != expected_size:
                    errors.append(
                        f"{image_path.name}: expected {expected_size[0]}x{expected_size[1]}, "
                        f"got {image.width}x{image.height}"
                    )
        except OSError:
            errors.append(f"{image_path.name}: unreadable image")

    if errors:
        raise SeedanceRunnerError(
            "Storyboard is not ready for Seedance submission: " + "; ".join(errors)
        )


def _data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    redacted = json.loads(json.dumps(payload))
    for item in redacted.get("content", []):
        image_url = item.get("image_url") if isinstance(item, dict) else None
        if isinstance(image_url, dict) and str(image_url.get("url", "")).startswith("data:"):
            image_url["url"] = "<redacted data URL>"
    return redacted


def _task_url(endpoint: str, task_id: str) -> str:
    return f"{endpoint.rstrip('/')}/{task_id}"


def request_json(
    method: str,
    url: str,
    api_key: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SeedanceHTTPError(exc.code, body) from exc


def download_video(url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=300) as response:
        output.write_bytes(response.read())


def _is_placeholder(text: str) -> bool:
    cleaned = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    ).strip()
    return not cleaned or cleaned.upper() == "TODO"


def _read_usable_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if _is_placeholder(text):
        return None
    return text


def load_prompt(
    run_dir: Path,
    *,
    prompt: str | None = None,
    prompt_file: str | Path | None = None,
) -> tuple[str, str | None]:
    if prompt and prompt_file:
        raise SeedanceRunnerError("Use either --prompt or --prompt-file, not both")
    if prompt and prompt.strip():
        return prompt.strip(), None
    candidates = []
    if prompt_file:
        candidates.append(Path(prompt_file))
    candidates.extend(
        [
            run_dir / "analysis" / "seedance-prompt.md",
            run_dir / "analysis" / "video-prompt.md",
        ]
    )
    for candidate in candidates:
        text = _read_usable_text(candidate)
        if text:
            return text, _relative_to_run(candidate, run_dir)
    raise SeedanceRunnerError(
        "Missing Seedance prompt. Write analysis/seedance-prompt.md or pass --prompt."
    )


def compose_prompt(
    run_dir: Path,
    base_prompt: str,
    *,
    platform: str = "vertical-video",
    ratio: str | None = None,
    duration: str | None = None,
    seed: int | None = None,
) -> str:
    prompt = base_prompt.strip()
    shot_list = _read_usable_text(run_dir / "analysis" / "shot-list.md")
    if shot_list and shot_list not in prompt:
        prompt = f"{prompt}\n\nStoryboard beats to follow:\n{shot_list}"

    if platform == "vertical-video" and "no subtitles" not in prompt.lower():
        prompt = f"{prompt}\n\n{NO_SUBTITLE_POLICY}"
    return prompt


def _list_from_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _manifest_storyboard_urls(data: dict[str, Any], asset_ids: list[str]) -> list[str]:
    urls: list[str] = []
    for asset_id in asset_ids:
        asset = data.get("assets", {}).get(asset_id, {})
        for key in ["storyboard_url", "image_url", "reference_url"]:
            urls.extend(_list_from_value(asset.get(key)))
        request = asset.get("request")
        if isinstance(request, dict):
            for key in ["storyboard_url", "image_url", "reference_url"]:
                urls.extend(_list_from_value(request.get(key)))
    return [url for url in urls if url]


def select_image_urls(
    run_dir: Path,
    data: dict[str, Any],
    asset_ids: list[str],
    *,
    image_urls: list[str] | None = None,
    include_all_frames: bool = False,
    allow_data_url: bool = False,
) -> list[str]:
    urls = [url for url in image_urls or [] if url]
    if not urls:
        urls = _manifest_storyboard_urls(data, asset_ids)
    if urls:
        return urls if include_all_frames else urls[:1]

    if not allow_data_url:
        raise SeedanceRunnerError(
            "Seedance needs at least one storyboard image URL. Pass --image-url, "
            "store storyboard_url on manifest assets, or use --allow-data-url only "
            "after confirming your provider accepts local data URLs."
        )

    selected = asset_ids if include_all_frames else asset_ids[:1]
    data_urls: list[str] = []
    for asset_id in selected:
        path = _generated_path(run_dir, asset_id)
        if not path.is_file():
            raise SeedanceRunnerError(f"Missing generated storyboard frame: {path}")
        data_urls.append(_data_url(path))
    return data_urls


def build_payload(
    prompt: str,
    *,
    model: str,
    image_urls: list[str],
    ratio: str,
    duration: int,
    resolution: str,
    generate_audio: bool,
    watermark: bool,
    seed: int | None = None,
    callback_url: str | None = None,
    return_last_frame: bool = False,
    image_role: str | None = None,
) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for url in image_urls:
        item: dict[str, Any] = {"type": "image_url", "image_url": {"url": url}}
        if image_role:
            item["role"] = image_role
        content.append(item)

    payload: dict[str, Any] = {
        "model": model,
        "content": content,
        "ratio": ratio,
        "duration": duration,
        "resolution": resolution,
        "generate_audio": generate_audio,
        "watermark": watermark,
    }
    if seed is not None and not _supports_seed(model):
        raise SeedanceRunnerError(
            "Seedance 2.0 does not support --seed; remove --seed or override --model "
            "to a Seedance model that supports seed"
        )
    if seed is not None:
        payload["seed"] = seed
    if callback_url:
        payload["callback_url"] = callback_url
    if return_last_frame:
        payload["return_last_frame"] = True
    return payload


def _task_id(response: dict[str, Any]) -> str:
    task_id = response.get("id") or response.get("task_id")
    if not task_id:
        raise SeedanceRunnerError("Seedance create response did not include a task id")
    return str(task_id)


def _video_url(response: dict[str, Any]) -> str:
    content = response.get("content")
    if isinstance(content, dict):
        value = content.get("video_url") or content.get("url")
        if value:
            return str(value)
    value = response.get("video_url") or response.get("url")
    if value:
        return str(value)
    raise SeedanceRunnerError("Seedance succeeded but did not return a video URL")


def _update_manifest_video(run_dir: Path, fields: dict[str, Any]) -> None:
    manifest_path = run_dir / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        return
    data = manifest.load(manifest_path)
    current = data.get("video_generation", {})
    current.update(fields)
    data["video_generation"] = current
    _write_json(manifest_path, data)


def poll_task(
    task_id: str,
    *,
    api_key: str,
    endpoint: str,
    timeout_seconds: float,
    poll_interval: float,
    request_fn=None,
    on_status=None,
) -> dict[str, Any]:
    request_fn = request_fn or request_json
    deadline = time.monotonic() + timeout_seconds
    while True:
        response = request_fn("GET", _task_url(endpoint, task_id), api_key, None)
        if on_status:
            on_status(response)
        status = str(response.get("status", "")).lower()
        if status == "succeeded":
            return response
        if status in TERMINAL_FAILURES:
            raise SeedanceRunnerError(f"Seedance task {task_id} ended as {status}: {response}")
        if time.monotonic() >= deadline:
            raise SeedanceRunnerError(f"Timed out waiting for Seedance task {task_id}")
        time.sleep(max(0, poll_interval))


def run_seedance_video(
    run_dir: str | Path,
    *,
    prompt: str | None = None,
    prompt_file: str | Path | None = None,
    image_urls: list[str] | None = None,
    include_all_frames: bool = False,
    allow_data_url: bool = False,
    model: str | None = None,
    endpoint: str | None = None,
    ratio: str | None = None,
    duration: str | None = None,
    resolution: str | None = None,
    generate_audio: bool | None = None,
    watermark: bool | None = None,
    seed: int | None = None,
    callback_url: str | None = None,
    return_last_frame: bool = False,
    image_role: str | None = None,
    output: str | Path | None = None,
    dry_run: bool = False,
    timeout_seconds: float = DEFAULT_TIMEOUT,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    request_fn=None,
    download_fn=None,
) -> dict[str, Any]:
    run = Path(run_dir).resolve()
    manifest_path = run / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        raise SeedanceRunnerError(f"Missing manifest: {manifest_path}")
    data = manifest.load(manifest_path)
    platform = data.get("platform")
    if platform not in DEFAULT_RATIOS:
        raise SeedanceRunnerError("Seedance video runner requires a video storyboard run")
    asset_ids = list(data.get("assets", {}).keys())
    if not asset_ids:
        raise SeedanceRunnerError("Manifest does not contain storyboard assets")

    config = resolve_config(model=model, endpoint=endpoint)
    options = resolve_generation_options(
        platform=platform,
        ratio=ratio,
        duration=duration,
        resolution=resolution,
        generate_audio=generate_audio,
        watermark=watermark,
    )
    base_prompt, prompt_path = load_prompt(run, prompt=prompt, prompt_file=prompt_file)
    final_prompt = compose_prompt(
        run,
        base_prompt,
        platform=platform,
        ratio=ratio,
        duration=duration,
        seed=seed,
    )
    if not dry_run:
        _validate_storyboard_ready(run, data, platform, asset_ids)
    selected_urls = select_image_urls(
        run,
        data,
        asset_ids,
        image_urls=image_urls,
        include_all_frames=include_all_frames,
        allow_data_url=allow_data_url,
    )
    effective_image_role = image_role
    if effective_image_role is None and include_all_frames:
        effective_image_role = "reference_image"
    payload = build_payload(
        final_prompt,
        model=config["model"],
        image_urls=selected_urls,
        ratio=options["ratio"],
        duration=options["duration"],
        resolution=options["resolution"],
        generate_audio=options["generate_audio"],
        watermark=options["watermark"],
        seed=seed,
        callback_url=callback_url,
        return_last_frame=return_last_frame,
        image_role=effective_image_role,
    )
    redacted_payload = _redact_payload(payload)
    if dry_run:
        return {
            "endpoint": config["endpoint"],
            "api_key_set": bool(config.get("api_key")),
            "image_count": len(selected_urls),
            "generation": options,
            "payload": redacted_payload,
        }

    api_key = config.get("api_key")
    if not api_key:
        raise SeedanceRunnerError(
            "Set BYTEPLUS_ARK_API_KEY, BYTEPLUS_API_KEY, VSR_SEEDANCE_API_KEY, "
            "ARK_API_KEY, or SEEDANCE_API_KEY in .env.local or the local environment"
        )

    raw_dir = run / "raw"
    qa_dir = run / "qa"
    request_fn = request_fn or request_json
    download_fn = download_fn or download_video
    output_path = Path(output) if output else run / "generated" / "seedance-video.mp4"
    if not output_path.is_absolute():
        output_path = run / output_path

    _write_json(raw_dir / "seedance-create-request.json", redacted_payload)
    create_response = request_fn("POST", config["endpoint"], api_key, payload)
    _write_json(raw_dir / "seedance-create-response.json", create_response)
    task_id = _task_id(create_response)
    _update_manifest_video(
        run,
        {
            "status": "submitted",
            "task_id": task_id,
            "model": config["model"],
            "endpoint": config["endpoint"],
            "prompt_path": prompt_path,
            "image_count": len(selected_urls),
            "generation": options,
        },
    )

    def on_status(response: dict[str, Any]) -> None:
        _write_json(raw_dir / "seedance-status.json", response)

    try:
        final_response = poll_task(
            task_id,
            api_key=api_key,
            endpoint=config["endpoint"],
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
            request_fn=request_fn,
            on_status=on_status,
        )
        url = _video_url(final_response)
        download_fn(url, output_path)
    except Exception as exc:
        _update_manifest_video(
            run,
            {
                "status": "failed",
                "task_id": task_id,
                "last_error": {"type": exc.__class__.__name__, "message": str(exc)},
            },
        )
        raise

    relative_output = _relative_to_run(output_path, run)
    ledger = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": {
            "name": config["provider"],
            "model": config["model"],
            "endpoint": config["endpoint"],
            "api_key_set": True,
        },
        "task_id": task_id,
        "status": "succeeded",
        "prompt_path": prompt_path,
        "image_count": len(selected_urls),
        "generation": options,
        "video_url": url,
        "output": relative_output,
        "usage": final_response.get("usage", {}),
        "final_response": final_response,
    }
    _write_json(qa_dir / "seedance-video.json", ledger)
    _update_manifest_video(
        run,
        {
            "status": "succeeded",
            "task_id": task_id,
            "output": relative_output,
            "qa_path": "qa/seedance-video.json",
            "usage": final_response.get("usage", {}),
            "generation": options,
        },
    )
    return ledger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a Seedance video from a prepared storyboard run."
    )
    parser.add_argument("--run", required=True, help="Prepared video storyboard run.")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument(
        "--image-url",
        action="append",
        default=[],
        help="Public or provider-accepted storyboard image URL. Repeat for references.",
    )
    parser.add_argument(
        "--include-all-frames",
        action="store_true",
        help="Send every available storyboard URL/reference instead of only the first.",
    )
    parser.add_argument(
        "--allow-data-url",
        action="store_true",
        help="Send local generated frames as data URLs when no image URL is available.",
    )
    parser.add_argument("--model")
    parser.add_argument("--endpoint")
    parser.add_argument("--ratio")
    parser.add_argument("--duration")
    parser.add_argument("--resolution")
    audio = parser.add_mutually_exclusive_group()
    audio.add_argument("--generate-audio", dest="generate_audio", action="store_true", default=None)
    audio.add_argument("--no-generate-audio", dest="generate_audio", action="store_false")
    watermark = parser.add_mutually_exclusive_group()
    watermark.add_argument("--watermark", dest="watermark", action="store_true", default=None)
    watermark.add_argument("--no-watermark", dest="watermark", action="store_false")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--callback-url")
    parser.add_argument("--return-last-frame", action="store_true")
    parser.add_argument("--image-role")
    parser.add_argument("--output")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_seedance_video(
            args.run,
            prompt=args.prompt,
            prompt_file=args.prompt_file,
            image_urls=args.image_url,
            include_all_frames=args.include_all_frames,
            allow_data_url=args.allow_data_url,
            model=args.model,
            endpoint=args.endpoint,
            ratio=args.ratio,
            duration=args.duration,
            resolution=args.resolution,
            generate_audio=args.generate_audio,
            watermark=args.watermark,
            seed=args.seed,
            callback_url=args.callback_url,
            return_last_frame=args.return_last_frame,
            image_role=args.image_role,
            output=args.output,
            dry_run=args.dry_run,
            timeout_seconds=args.timeout,
            poll_interval=args.poll_interval,
        )
    except SeedanceRunnerError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
