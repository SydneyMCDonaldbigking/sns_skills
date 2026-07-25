"""Submit a prepared storyboard run to OpenRouter video generation.

This runner is separate from the BytePlus Seedance runner. It is intended for
low-cost Grok video tests through OpenRouter's async `/api/v1/videos` API.
Keys are loaded from the ignored `.env.local` or the local environment.
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
import shutil
import subprocess
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
DEFAULT_ENDPOINT = "https://openrouter.ai/api/v1/videos"
DEFAULT_MODEL = "x-ai/grok-imagine-video"
DEFAULT_RATIO = "9:16"
DEFAULT_RATIOS = {
    "vertical-video": "9:16",
    "video": "16:9",
}
DEFAULT_RESOLUTION = "720p"
DEFAULT_GENERATE_AUDIO = False
DEFAULT_DURATION = "5"
DEFAULT_TIMEOUT = 1800
DEFAULT_POLL_INTERVAL = 30
TERMINAL_FAILURES = {"failed", "cancelled", "canceled", "expired"}
KEY_ENV_NAMES = [
    "GROK_OPENROUTER_API_KEY",
    "VSR_OPENROUTER_VIDEO_API_KEY",
    "OPENROUTER_VIDEO_API_KEY",
    "OPENROUTER_API_KEY",
]
TRUTHY = {"1", "true", "yes", "y", "on"}
FALSY = {"0", "false", "no", "n", "off"}
NO_SUBTITLE_POLICY = (
    "No subtitles, captions, title cards, lower-thirds, burned-in text, "
    "ingredient labels, floating graphics, sticker ads, or any screen overlay "
    "text. If company branding appears, it must be a real physical prop already "
    "present in the storyboard, never a generated overlay or caption."
)


class OpenRouterVideoRunnerError(RuntimeError):
    """Raised when OpenRouter video generation cannot complete."""


class OpenRouterVideoHTTPError(RuntimeError):
    def __init__(self, code: int, body: str):
        self.code = code
        self.body = body
        super().__init__(f"OpenRouter video HTTP {code}: {body}")


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


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    normalized = value.strip().lower()
    if normalized in TRUTHY:
        return True
    if normalized in FALSY:
        return False
    raise OpenRouterVideoRunnerError(
        f"{name} must be a boolean value such as true/false, 1/0, yes/no, or on/off"
    )


def resolve_config(*, model: str | None = None, endpoint: str | None = None) -> dict[str, Any]:
    _load_env_file()
    return {
        "provider": "openrouter-video",
        "model": model or os.environ.get("VSR_OPENROUTER_VIDEO_MODEL", DEFAULT_MODEL),
        "endpoint": endpoint or os.environ.get("VSR_OPENROUTER_VIDEO_ENDPOINT", DEFAULT_ENDPOINT),
        "api_key": _api_key(),
    }


def resolve_generation_options(
    *,
    platform: str,
    ratio: str | None = None,
    duration: str | int | None = None,
    resolution: str | None = None,
    generate_audio: bool | None = None,
) -> dict[str, Any]:
    default_ratio = DEFAULT_RATIOS.get(platform, DEFAULT_RATIO)
    duration_value = (
        duration
        if duration is not None
        else os.environ.get("VSR_OPENROUTER_VIDEO_DURATION", DEFAULT_DURATION)
    )
    try:
        parsed_duration = int(duration_value)
    except (TypeError, ValueError) as exc:
        raise OpenRouterVideoRunnerError(
            "OpenRouter video duration must be an integer number of seconds"
        ) from exc
    if parsed_duration < 1 or parsed_duration > 15:
        raise OpenRouterVideoRunnerError(
            "OpenRouter video duration must be between 1 and 15 seconds"
        )

    return {
        "aspect_ratio": ratio or os.environ.get("VSR_OPENROUTER_VIDEO_RATIO", default_ratio),
        "duration": parsed_duration,
        "resolution": resolution
        or os.environ.get("VSR_OPENROUTER_VIDEO_RESOLUTION", DEFAULT_RESOLUTION),
        "generate_audio": (
            generate_audio
            if generate_audio is not None
            else _env_bool("VSR_OPENROUTER_VIDEO_GENERATE_AUDIO", DEFAULT_GENERATE_AUDIO)
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
        raise OpenRouterVideoRunnerError(
            "OpenRouter video requires exactly 9 storyboard assets with ids 01 through 09 "
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
        raise OpenRouterVideoRunnerError(
            "Storyboard is not ready for OpenRouter video submission: " + "; ".join(errors)
        )


def _data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    redacted = json.loads(json.dumps(payload))
    for key in ["frame_images", "input_references"]:
        for item in redacted.get(key, []) or []:
            image_url = item.get("image_url") if isinstance(item, dict) else None
            if isinstance(image_url, dict) and str(image_url.get("url", "")).startswith("data:"):
                image_url["url"] = "<redacted data URL>"
    return redacted


def _redact_response(response: dict[str, Any]) -> dict[str, Any]:
    redacted = json.loads(json.dumps(response))
    if "unsigned_urls" in redacted:
        redacted["unsigned_urls"] = ["<redacted video URL>" for _ in redacted.get("unsigned_urls", [])]
    for key in ["url", "video_url", "output_url"]:
        if key in redacted:
            redacted[key] = "<redacted video URL>"
    return redacted


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
        raise OpenRouterVideoHTTPError(exc.code, body) from exc


def download_video(job: dict[str, Any], api_key: str, output: Path, opener=urlopen) -> None:
    urls = job.get("unsigned_urls") or []
    video_url = urls[0] if urls else f"https://openrouter.ai/api/v1/videos/{job['id']}/content?index=0"
    headers = {"Authorization": f"Bearer {api_key}"} if "openrouter.ai/api/" in video_url else {}
    request = Request(video_url, headers=headers)
    output.parent.mkdir(parents=True, exist_ok=True)
    with opener(request, timeout=300) as response:
        output.write_bytes(response.read())


def strip_audio(output: Path, *, ffmpeg_path: str | None = None) -> bool:
    ffmpeg = ffmpeg_path or shutil.which("ffmpeg")
    if not ffmpeg or not output.is_file():
        return False
    temp = output.with_name(f"{output.stem}.noaudio.tmp{output.suffix}")
    try:
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(output),
                "-c",
                "copy",
                "-an",
                str(temp),
            ],
            check=True,
        )
        temp.replace(output)
        return True
    except (OSError, subprocess.CalledProcessError):
        if temp.exists():
            temp.unlink()
        return False


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
        raise OpenRouterVideoRunnerError("Use either --prompt or --prompt-file, not both")
    if prompt and prompt.strip():
        return prompt.strip(), None
    candidates = []
    if prompt_file:
        candidates.append(Path(prompt_file))
    candidates.extend(
        [
            run_dir / "analysis" / "openrouter-video-prompt.md",
            run_dir / "analysis" / "seedance-prompt.md",
            run_dir / "analysis" / "video-prompt.md",
        ]
    )
    for candidate in candidates:
        text = _read_usable_text(candidate)
        if text:
            return text, _relative_to_run(candidate, run_dir)
    raise OpenRouterVideoRunnerError(
        "Missing video prompt. Write analysis/openrouter-video-prompt.md, "
        "analysis/seedance-prompt.md, or pass --prompt."
    )


def compose_prompt(run_dir: Path, base_prompt: str, *, platform: str) -> str:
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
        raise OpenRouterVideoRunnerError(
            "OpenRouter video needs a directly downloadable storyboard image URL. "
            "Pass --image-url, store storyboard_url on manifest assets, or use "
            "--allow-data-url only for an experimental test."
        )

    selected = asset_ids if include_all_frames else asset_ids[:1]
    data_urls: list[str] = []
    for asset_id in selected:
        path = _generated_path(run_dir, asset_id)
        if not path.is_file():
            raise OpenRouterVideoRunnerError(f"Missing generated storyboard frame: {path}")
        data_urls.append(_data_url(path))
    return data_urls


def build_payload(
    prompt: str,
    *,
    model: str,
    image_urls: list[str],
    aspect_ratio: str,
    duration: int,
    resolution: str,
    generate_audio: bool,
    include_reference_images: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
        "generate_audio": generate_audio,
    }
    if image_urls:
        payload["frame_images"] = [
            {
                "type": "image_url",
                "image_url": {"url": image_urls[0]},
                "frame_type": "first_frame",
            }
        ]
    if include_reference_images and len(image_urls) > 1:
        payload["input_references"] = [
            {"type": "image_url", "image_url": {"url": url}}
            for url in image_urls[1:]
        ]
    return payload


def _task_id(response: dict[str, Any]) -> str:
    task_id = response.get("id") or response.get("task_id")
    if not task_id:
        raise OpenRouterVideoRunnerError("OpenRouter create response did not include a job id")
    return str(task_id)


def _polling_url(endpoint: str, job: dict[str, Any]) -> str:
    value = job.get("polling_url")
    if value:
        return str(value) if str(value).startswith("http") else f"https://openrouter.ai{value}"
    return f"{endpoint.rstrip('/')}/{_task_id(job)}"


def _update_manifest_video(run_dir: Path, fields: dict[str, Any]) -> None:
    manifest_path = run_dir / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        return
    data = manifest.load(manifest_path)
    current = data.get("openrouter_video_generation", {})
    current.update(fields)
    data["openrouter_video_generation"] = current
    _write_json(manifest_path, data)


def poll_task(
    job: dict[str, Any],
    *,
    api_key: str,
    endpoint: str,
    timeout_seconds: float,
    poll_interval: float,
    request_fn=None,
    on_status=None,
) -> dict[str, Any]:
    request_fn = request_fn or request_json
    current = job
    deadline = time.monotonic() + timeout_seconds
    while True:
        status = str(current.get("status", "")).lower()
        if on_status:
            on_status(current)
        if status in {"completed", "succeeded"}:
            return current
        if status in TERMINAL_FAILURES:
            raise OpenRouterVideoRunnerError(
                f"OpenRouter video job {_task_id(current)} ended as {status}: {current}"
            )
        if time.monotonic() >= deadline:
            raise OpenRouterVideoRunnerError(
                f"Timed out waiting for OpenRouter video job {_task_id(current)}"
            )
        time.sleep(max(0, poll_interval))
        current = request_fn("GET", _polling_url(endpoint, current), api_key, None)


def run_openrouter_video(
    run_dir: str | Path,
    *,
    prompt: str | None = None,
    prompt_file: str | Path | None = None,
    image_urls: list[str] | None = None,
    include_all_frames: bool = False,
    include_reference_images: bool = False,
    allow_data_url: bool = False,
    model: str | None = None,
    endpoint: str | None = None,
    ratio: str | None = None,
    duration: str | None = None,
    resolution: str | None = None,
    generate_audio: bool | None = None,
    output: str | Path | None = None,
    dry_run: bool = False,
    timeout_seconds: float = DEFAULT_TIMEOUT,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    request_fn=None,
    download_fn=None,
    strip_audio_fn=None,
) -> dict[str, Any]:
    run = Path(run_dir).resolve()
    manifest_path = run / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        raise OpenRouterVideoRunnerError(f"Missing manifest: {manifest_path}")
    data = manifest.load(manifest_path)
    platform = data.get("platform")
    if platform not in DEFAULT_RATIOS:
        raise OpenRouterVideoRunnerError("OpenRouter video runner requires a video storyboard run")
    asset_ids = list(data.get("assets", {}).keys())
    if not asset_ids:
        raise OpenRouterVideoRunnerError("Manifest does not contain storyboard assets")

    config = resolve_config(model=model, endpoint=endpoint)
    options = resolve_generation_options(
        platform=platform,
        ratio=ratio,
        duration=duration,
        resolution=resolution,
        generate_audio=generate_audio,
    )
    base_prompt, prompt_path = load_prompt(run, prompt=prompt, prompt_file=prompt_file)
    final_prompt = compose_prompt(run, base_prompt, platform=platform)
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
    payload = build_payload(
        final_prompt,
        model=config["model"],
        image_urls=selected_urls,
        aspect_ratio=options["aspect_ratio"],
        duration=options["duration"],
        resolution=options["resolution"],
        generate_audio=options["generate_audio"],
        include_reference_images=include_reference_images,
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
        raise OpenRouterVideoRunnerError(
            "Set GROK_OPENROUTER_API_KEY, VSR_OPENROUTER_VIDEO_API_KEY, "
            "OPENROUTER_VIDEO_API_KEY, or OPENROUTER_API_KEY in .env.local "
            "or the local environment"
        )

    raw_dir = run / "raw"
    qa_dir = run / "qa"
    request_fn = request_fn or request_json
    download_fn = download_fn or download_video
    strip_audio_fn = strip_audio_fn or strip_audio
    output_path = Path(output) if output else run / "generated" / "openrouter-video.mp4"
    if not output_path.is_absolute():
        output_path = run / output_path

    _write_json(raw_dir / "openrouter-video-create-request.json", redacted_payload)
    create_response = request_fn("POST", config["endpoint"], api_key, payload)
    task_id = _task_id(create_response)
    _write_json(raw_dir / "openrouter-video-create-response.json", _redact_response(create_response))
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
        _write_json(raw_dir / "openrouter-video-status.json", _redact_response(response))

    try:
        final_response = poll_task(
            create_response,
            api_key=api_key,
            endpoint=config["endpoint"],
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
            request_fn=request_fn,
            on_status=on_status,
        )
        download_fn(final_response, api_key, output_path)
        postprocess = {}
        if not options["generate_audio"]:
            postprocess["audio_stripped"] = strip_audio_fn(output_path)
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
        "output": relative_output,
        "usage": final_response.get("usage", {}),
        "final_response": _redact_response(final_response),
    }
    if postprocess:
        ledger["postprocess"] = postprocess
    _write_json(qa_dir / "openrouter-video.json", ledger)
    _update_manifest_video(
        run,
        {
            "status": "succeeded",
            "task_id": task_id,
            "output": relative_output,
            "qa_path": "qa/openrouter-video.json",
            "usage": final_response.get("usage", {}),
            "generation": options,
            "postprocess": postprocess,
        },
    )
    return ledger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a video from a prepared storyboard run through OpenRouter."
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
        help="Collect all storyboard URLs/frames. Grok's first_frame support still anchors only the first frame unless --include-reference-images is also used.",
    )
    parser.add_argument(
        "--include-reference-images",
        action="store_true",
        help="Send images after the first as input_references. Use only after confirming the selected model handles reference images.",
    )
    parser.add_argument(
        "--allow-data-url",
        action="store_true",
        help="Send local generated frames as data URLs. OpenRouter recommends public HTTPS image URLs for production.",
    )
    parser.add_argument("--model")
    parser.add_argument("--endpoint")
    parser.add_argument("--ratio")
    parser.add_argument("--duration")
    parser.add_argument("--resolution")
    audio = parser.add_mutually_exclusive_group()
    audio.add_argument("--generate-audio", dest="generate_audio", action="store_true", default=None)
    audio.add_argument("--no-generate-audio", dest="generate_audio", action="store_false")
    parser.add_argument("--output")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_openrouter_video(
            args.run,
            prompt=args.prompt,
            prompt_file=args.prompt_file,
            image_urls=args.image_url,
            include_all_frames=args.include_all_frames,
            include_reference_images=args.include_reference_images,
            allow_data_url=args.allow_data_url,
            model=args.model,
            endpoint=args.endpoint,
            ratio=args.ratio,
            duration=args.duration,
            resolution=args.resolution,
            generate_audio=args.generate_audio,
            output=args.output,
            dry_run=args.dry_run,
            timeout_seconds=args.timeout,
            poll_interval=args.poll_interval,
        )
    except OpenRouterVideoRunnerError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
