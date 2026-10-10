"""Submit a Seedance 2.5 job through the NewB video membership API.

This runner is separate from the BytePlus/kuaipao Seedance 2.0 runner. NewB
uses a different contract: multipart uploads of local image files, fixed 30s
720p output with native audio, no last-frame return, and a membership quota
shared with the NewB web app. Keys are loaded from the ignored `.env.local` or
the local environment and are never written to disk.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid

from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import manifest


ROOT = Path(__file__).parents[2]
LOCAL_ENV = ROOT / ".env.local"
DEFAULT_BASE_URL = "https://video.haoniubi.cloud"
KEY_ENV_NAMES = ["NEWB_API_KEY", "VSR_NEWB_API_KEY"]
MODEL = "seedance-2.5"
FIXED_DURATION_SECONDS = 30
FIXED_RESOLUTION = "720p"
RATIOS = ("9:16", "16:9", "1:1")
DEFAULT_RATIOS = {"vertical-video": "9:16", "video": "16:9"}
MAX_IMAGES = 9
MAX_IMAGE_BYTES = 15 * 1024 * 1024
IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
MAX_PROMPT_CHARS = 6000
DEFAULT_LABEL = "newb-video"
DEFAULT_PROMPT_FILE = "analysis/newb-prompt.md"
DEFAULT_POLL_INTERVAL = 15
DEFAULT_TIMEOUT = 60 * 60
REQUEST_TIMEOUT = 180
SIGNED_URL_PLACEHOLDER = "<signed-url-redacted>"
# NewB: "别写时间轴" - the model does not follow per-second timelines.
TIMELINE_PATTERNS = [
    re.compile(r"\d+(?:\.\d+)?\s*(?:s|秒)?\s*[-–—~～到至]\s*\d+(?:\.\d+)?\s*(?:s\b|秒|sec)", re.I),
    re.compile(r"(?<![\d:])\d{1,2}:\d{2}(?![\d:])"),
    re.compile(r"第\s*\d+\s*秒"),
]
NO_MUSIC_RE = re.compile(r"no music|without music|不要(?:背景)?音乐|无(?:背景)?音乐|没有(?:背景)?音乐|不要\s*BGM", re.I)


class NewBRunnerError(RuntimeError):
    pass


class NewBNetworkError(RuntimeError):
    pass


class NewBHTTPError(NewBRunnerError):
    def __init__(self, status: int, body: dict[str, Any]):
        error = body.get("error") if isinstance(body, dict) else None
        self.status = status
        self.code = error.get("code") if isinstance(error, dict) else None
        message = error.get("message") if isinstance(error, dict) else body
        super().__init__(f"NewB HTTP {status} {self.code or ''}: {message}".strip())


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_env_file(path: Path | None = None) -> None:
    env_path = path or LOCAL_ENV
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def resolve_config(*, base_url: str | None = None) -> dict[str, Any]:
    _load_env_file()
    api_key = next((os.environ[name] for name in KEY_ENV_NAMES if os.environ.get(name)), None)
    return {
        "provider": "newb-seedance-2.5",
        "base_url": (base_url or os.environ.get("VSR_NEWB_BASE_URL") or DEFAULT_BASE_URL).rstrip("/"),
        "api_key": api_key,
    }


def lint_prompt(prompt: str) -> list[str]:
    """Return timeline fragments NewB says the model will not follow."""
    hits: list[str] = []
    for pattern in TIMELINE_PATTERNS:
        hits.extend(match.group(0) for match in pattern.finditer(prompt))
    return [hit for hit in hits if hit not in RATIOS]


def load_prompt(
    run_dir: Path,
    *,
    prompt: str | None = None,
    prompt_file: str | Path | None = None,
) -> tuple[str, str]:
    if prompt is not None:
        text, source = prompt, "inline"
    else:
        path = Path(prompt_file) if prompt_file else run_dir / DEFAULT_PROMPT_FILE
        if not path.is_absolute() and not path.is_file():
            path = run_dir / path
        if not path.is_file():
            raise NewBRunnerError(f"Missing prompt: pass --prompt or write {path}")
        lines = [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")
        ]
        text = "\n".join(lines)
        try:
            source = path.resolve().relative_to(run_dir).as_posix()
        except ValueError:
            source = str(path)
    text = text.strip()
    if not text:
        raise NewBRunnerError("Prompt is empty after removing comment lines")
    if len(text) > MAX_PROMPT_CHARS:
        raise NewBRunnerError(f"Prompt has {len(text)} characters; NewB allows {MAX_PROMPT_CHARS}")
    return text, source


def _ratio_value(ratio: str) -> float:
    width, height = ratio.split(":")
    return int(width) / int(height)


def validate_images(paths: list[str | Path], run_dir: Path, ratio: str) -> tuple[list[dict[str, Any]], list[str]]:
    if len(paths) > MAX_IMAGES:
        raise NewBRunnerError(f"NewB accepts at most {MAX_IMAGES} reference images, got {len(paths)}")
    images: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, raw in enumerate(paths, start=1):
        path = Path(raw)
        if not path.is_absolute() and not path.is_file():
            path = run_dir / path
        if not path.is_file():
            raise NewBRunnerError(f"Missing reference image: {raw}")
        content_type = IMAGE_TYPES.get(path.suffix.lower())
        if not content_type:
            raise NewBRunnerError(f"{path.name}: NewB accepts only JPG, PNG, or WebP")
        size = path.stat().st_size
        if size > MAX_IMAGE_BYTES:
            raise NewBRunnerError(f"{path.name}: {size} bytes exceeds the 15 MB limit")
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                width, height = image.size
        except Exception as exc:
            raise NewBRunnerError(f"{path.name}: not a readable image ({exc})") from exc
        if index == 1 and abs(width / height - _ratio_value(ratio)) > 0.03:
            warnings.append(
                f"@图1 is {width}x{height} but ratio is {ratio}; a single reference is usually "
                "treated as the first frame, so match its aspect ratio."
            )
        images.append(
            {
                "label": f"@图{index}",
                "path": str(path),
                "filename": f"image-{index:02d}{path.suffix.lower()}",
                "content_type": content_type,
                "size": [width, height],
                "bytes": size,
            }
        )
    return images, warnings


def unreferenced_images(prompt: str, image_count: int) -> list[str]:
    """@图N labels that were uploaded but never named in the prompt."""
    return [f"@图{n}" for n in range(1, image_count + 1)
            if not re.search(rf"@图{n}(?!\d)", prompt)]


def encode_multipart(
    fields: list[tuple[str, str]],
    files: list[tuple[str, str, str, bytes]],
    boundary: str | None = None,
) -> tuple[bytes, str]:
    boundary = boundary or f"----newb{uuid.uuid4().hex}"
    body = bytearray()
    for name, value in fields:
        body += f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        body += value.encode("utf-8") + b"\r\n"
    for name, filename, content_type, data in files:
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
            f'filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'
        ).encode()
        body += data + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def request_json(
    method: str,
    url: str,
    api_key: str,
    *,
    body: bytes | None = None,
    content_type: str | None = None,
) -> tuple[int, dict[str, str], dict[str, Any]]:
    """Return (status, headers, json). HTTP errors return; network errors raise."""
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    if content_type:
        headers["Content-Type"] = content_type
    request = Request(url, data=body, method=method, headers=headers)
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            raw, status, response_headers = response.read(), response.status, dict(response.headers)
    except HTTPError as exc:
        raw, status, response_headers = exc.read(), exc.code, dict(exc.headers or {})
    except (URLError, socket.timeout, TimeoutError, ConnectionError) as exc:
        raise NewBNetworkError(str(exc)) from exc
    try:
        parsed = json.loads(raw.decode("utf-8")) if raw else {}
    except ValueError:
        parsed = {"error": {"code": "NON_JSON_RESPONSE", "message": raw[:300].decode("utf-8", "replace")}}
    return status, response_headers, parsed


def download_video(url: str, output: Path) -> None:
    # The signed URL is its own credential; never send the API key with it.
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(f"{output.name}.part")
    with urlopen(Request(url), timeout=300) as response, temp.open("wb") as handle:
        shutil.copyfileobj(response, handle, 1 << 20)
    temp.replace(output)


def _ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def strip_audio_track(source: Path, output: Path) -> bool:
    ffmpeg = _ffmpeg()
    if not ffmpeg or not source.is_file():
        return False
    try:
        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-c", "copy", "-an", str(output)],
            check=True,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def extract_last_frame(source: Path, output: Path) -> bool:
    ffmpeg = _ffmpeg()
    if not ffmpeg or not source.is_file():
        return False
    try:
        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-sseof", "-0.5", "-i", str(source),
             "-update", "1", "-q:v", "1", str(output)],
            check=True,
        )
        return output.is_file()
    except (OSError, subprocess.CalledProcessError):
        return False


def _redact(response: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(response)
    if "video_url" in redacted:
        redacted["video_url"] = SIGNED_URL_PLACEHOLDER
    return redacted


def _relative_to_run(path: Path, run_dir: Path) -> str:
    try:
        return path.resolve().relative_to(run_dir).as_posix()
    except ValueError:
        return str(path)


def _update_manifest(run_dir: Path, label: str, fields: dict[str, Any]) -> None:
    manifest_path = run_dir / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        return
    data = manifest.load(manifest_path)
    generations = data.get("newb_video_generation", {})
    current = generations.get(label, {})
    current.update(fields)
    current["updated_at"] = datetime.now(timezone.utc).isoformat()
    generations[label] = current
    data["newb_video_generation"] = generations
    _write_json(manifest_path, data)


def _manifest_task_id(run_dir: Path, label: str) -> str | None:
    manifest_path = run_dir / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        return None
    entry = manifest.load(manifest_path).get("newb_video_generation", {}).get(label, {})
    return entry.get("task_id")


def _manifest_reference_images(run_dir: Path) -> list[str]:
    """User-supplied reference images recorded by prepare-original-video, in order."""
    manifest_path = run_dir / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        return []
    video = manifest.load(manifest_path).get("video") or {}
    refs = sorted(
        (item for item in video.get("references") or [] if item.get("type") == "image" and item.get("path")),
        key=lambda item: item.get("order", 0),
    )
    return [item["path"] for item in refs]


def _default_ratio(run_dir: Path) -> str:
    manifest_path = run_dir / "analysis" / "manifest.json"
    if manifest_path.is_file():
        platform = manifest.load(manifest_path).get("platform")
        if platform in DEFAULT_RATIOS:
            return DEFAULT_RATIOS[platform]
    return "9:16"


def get_quota(config: dict[str, Any], *, request_fn=None) -> dict[str, Any]:
    request_fn = request_fn or request_json
    status, _, body = request_fn("GET", f"{config['base_url']}/api/v1/quota", config["api_key"])
    if status != 200:
        raise NewBHTTPError(status, body)
    return body


def submit_task(
    config: dict[str, Any],
    prompt: str,
    ratio: str,
    images: list[dict[str, Any]],
    *,
    request_fn=None,
) -> dict[str, Any]:
    request_fn = request_fn or request_json
    quota_before = get_quota(config, request_fn=request_fn)
    if quota_before.get("membership_active") is False:
        raise NewBRunnerError("NewB membership is inactive; renew before submitting (would return 402)")
    if quota_before.get("quota_remaining", 1) <= 0:
        raise NewBRunnerError("NewB membership quota for this period is used up")
    if quota_before.get("active", 0) >= quota_before.get("max_concurrent", 5):
        raise NewBRunnerError(
            f"NewB already has {quota_before.get('active')} active jobs (max "
            f"{quota_before.get('max_concurrent', 5)}); wait for one to finish"
        )
    files = [
        ("images[]", image["filename"], image["content_type"], Path(image["path"]).read_bytes())
        for image in images
    ]
    body, content_type = encode_multipart([("prompt", prompt), ("ratio", ratio)], files)
    try:
        status, _, response = request_fn(
            "POST", f"{config['base_url']}/api/v1/videos", config["api_key"],
            body=body, content_type=content_type,
        )
    except NewBNetworkError as exc:
        # No idempotency key: check whether the job was created before anyone retries.
        try:
            quota_after = get_quota(config, request_fn=request_fn)
        except (NewBNetworkError, NewBHTTPError):
            raise NewBRunnerError(
                f"Submit got no response ({exc}) and quota could not be checked. Do NOT resubmit "
                "until NewB web history or /api/v1/quota confirms no new job was created."
            ) from exc
        if quota_after.get("active", 0) > quota_before.get("active", 0):
            raise NewBRunnerError(
                f"Submit got no response ({exc}) but NewB shows a new active job. Do NOT resubmit; "
                "find the task in NewB web history and continue with --resume TASK_ID."
            ) from exc
        raise NewBRunnerError(f"Submit failed before the job was created ({exc}); safe to retry") from exc
    if status != 201:
        raise NewBHTTPError(status, response)
    return response


def poll_task(
    config: dict[str, Any],
    task_id: str,
    *,
    timeout_seconds: float,
    poll_interval: float,
    request_fn=None,
    sleep_fn: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    on_status: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    request_fn = request_fn or request_json
    url = f"{config['base_url']}/api/v1/videos/{task_id}"
    deadline = clock() + timeout_seconds
    while True:
        wait = poll_interval
        try:
            status, headers, body = request_fn("GET", url, config["api_key"])
        except NewBNetworkError:
            status, headers, body = None, {}, {}
        if status == 200:
            if on_status:
                on_status(body)
            if body.get("status") in {"succeeded", "failed"}:
                return body
        elif status == 429:
            try:
                wait = max(float(headers.get("Retry-After", poll_interval)), 1.0)
            except ValueError:
                wait = poll_interval
        elif status is not None and status < 500:
            raise NewBHTTPError(status, body)
        # 5xx and network errors: keep polling the same id, never declare failure locally.
        if clock() + wait > deadline:
            raise NewBRunnerError(
                f"Stopped waiting after {int(timeout_seconds)}s; the job was not cancelled. "
                f"Continue later with --resume {task_id}"
            )
        sleep_fn(wait)


def run_newb_video(
    run_dir: str | Path,
    *,
    prompt: str | None = None,
    prompt_file: str | Path | None = None,
    images: list[str | Path] | None = None,
    ratio: str | None = None,
    label: str = DEFAULT_LABEL,
    strip_audio: bool = False,
    allow_timeline: bool = False,
    resume_task_id: str | None = None,
    overwrite: bool = False,
    base_url: str | None = None,
    dry_run: bool = False,
    timeout_seconds: float = DEFAULT_TIMEOUT,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    request_fn=None,
    download_fn=None,
    strip_audio_fn=None,
    extract_frame_fn=None,
    sleep_fn: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    run = Path(run_dir).resolve()
    if not run.is_dir():
        raise NewBRunnerError(f"Missing run directory: {run}")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", label):
        raise NewBRunnerError("--label may contain only letters, digits, '.', '_' and '-'")
    config = resolve_config(base_url=base_url)
    generated = run / "generated"
    output_path = generated / f"{label}.mp4"
    audio_path = generated / f"{label}.audio.mp4"
    frame_path = generated / f"{label}-last-frame.png"
    raw_dir = run / "raw"
    ledger_path = run / "qa" / f"{label}.json"

    resume_task_id = resume_task_id or None
    if resume_task_id == "auto":
        resume_task_id = _manifest_task_id(run, label)
        if not resume_task_id:
            raise NewBRunnerError(f"No saved NewB task id for label {label!r} in the manifest")

    prompt_text = prompt_source = None
    image_specs: list[dict[str, Any]] = []
    warnings: list[str] = []
    ratio = ratio or _default_ratio(run)
    if ratio not in RATIOS:
        raise NewBRunnerError(f"ratio must be one of {', '.join(RATIOS)}")
    if not resume_task_id:
        if output_path.exists() and not overwrite:
            raise NewBRunnerError(
                f"{_relative_to_run(output_path, run)} already exists; use a new --label for a "
                "reroll or pass --overwrite"
            )
        prompt_text, prompt_source = load_prompt(run, prompt=prompt, prompt_file=prompt_file)
        timeline_hits = lint_prompt(prompt_text)
        if timeline_hits and not allow_timeline:
            raise NewBRunnerError(
                "NewB Seedance 2.5 does not follow per-second timelines; rewrite as ordered shots "
                f"without timestamps. Found: {', '.join(timeline_hits[:5])}. "
                "Pass --allow-timeline to submit anyway."
            )
        image_specs, warnings = validate_images(images or _manifest_reference_images(run), run, ratio)
        missing = unreferenced_images(prompt_text, len(image_specs))
        if missing:
            warnings.append(
                f"Uploaded but never named in the prompt: {', '.join(missing)}; say what "
                "each segment's start/end image shows"
            )
        if not NO_MUSIC_RE.search(prompt_text):
            warnings.append(
                "Prompt does not rule out music: end it with "
                "'soundscape: <ambient sounds>. No dialogue, no music.'"
            )

    plan = {
        "provider": config["provider"],
        "model": MODEL,
        "base_url": config["base_url"],
        "api_key_set": bool(config["api_key"]),
        "label": label,
        "ratio": ratio,
        "duration_seconds": FIXED_DURATION_SECONDS,
        "resolution": FIXED_RESOLUTION,
        "prompt_source": prompt_source,
        "prompt_chars": len(prompt_text) if prompt_text else None,
        "images": [
            {key: spec[key] for key in ("label", "path", "size", "bytes")} for spec in image_specs
        ],
        "strip_audio": strip_audio,
        "resume_task_id": resume_task_id,
        "warnings": warnings,
    }
    if dry_run:
        return {"dry_run": True, **plan, "prompt": prompt_text}
    if not config["api_key"]:
        raise NewBRunnerError(f"Set {' or '.join(KEY_ENV_NAMES)} in .env.local or the environment")

    if resume_task_id:
        task_id = resume_task_id
        _update_manifest(run, label, {"status": "polling", "task_id": task_id})
    else:
        create = submit_task(config, prompt_text, ratio, image_specs, request_fn=request_fn)
        task_id = create["id"]
        _write_json(raw_dir / f"{label}-create-response.json", _redact(create))
        _update_manifest(
            run,
            label,
            {
                "status": create.get("status", "queued"),
                "task_id": task_id,
                "provider": config["provider"],
                "model": MODEL,
                "ratio": ratio,
                "prompt_source": prompt_source,
                "image_count": len(image_specs),
                "quota_remaining": create.get("quota_remaining"),
            },
        )
        print(f"NewB task submitted: {task_id} (quota remaining {create.get('quota_remaining')})",
              file=sys.stderr, flush=True)

    def on_status(body: dict[str, Any]) -> None:
        _write_json(raw_dir / f"{label}-status.json", _redact(body))
        print(f"NewB {task_id}: {body.get('status')}", file=sys.stderr, flush=True)

    try:
        final = poll_task(
            config, task_id,
            timeout_seconds=timeout_seconds, poll_interval=poll_interval,
            request_fn=request_fn, sleep_fn=sleep_fn, clock=clock, on_status=on_status,
        )
    except NewBRunnerError as exc:
        _update_manifest(run, label, {"status": "waiting", "task_id": task_id, "last_error": str(exc)})
        raise
    if final["status"] == "failed":
        _update_manifest(
            run, label,
            {"status": "failed", "task_id": task_id, "error": final.get("error"),
             "quota_refunded": final.get("quota_refunded")},
        )
        raise NewBRunnerError(
            f"NewB task {task_id} failed: {final.get('error')} (quota refunded: {final.get('quota_refunded')})"
        )
    if final.get("video_expired"):
        raise NewBRunnerError(f"NewB task {task_id} succeeded but the file passed its 7-day retention")

    download_fn = download_fn or download_video
    strip_audio_fn = strip_audio_fn or strip_audio_track
    extract_frame_fn = extract_frame_fn or extract_last_frame
    postprocess: dict[str, Any] = {}
    if not strip_audio:
        download_fn(final["video_url"], output_path)
    else:
        download_fn(final["video_url"], audio_path)
        postprocess["audio_stripped"] = strip_audio_fn(audio_path, output_path)
        if not postprocess["audio_stripped"]:
            raise NewBRunnerError(
                f"Downloaded {_relative_to_run(audio_path, run)} but could not strip audio; "
                "install ffmpeg or rerun with --resume without --strip-audio"
            )
        postprocess["audio_original"] = _relative_to_run(audio_path, run)
    postprocess["last_frame"] = (
        _relative_to_run(frame_path, run) if extract_frame_fn(output_path, frame_path) else None
    )

    ledger = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **{key: value for key, value in plan.items() if key not in {"api_key_set", "resume_task_id"}},
        "task_id": task_id,
        "status": "succeeded",
        "output": _relative_to_run(output_path, run),
        "postprocess": postprocess,
        "final_response": _redact(final),
    }
    _write_json(ledger_path, ledger)
    _update_manifest(
        run, label,
        {"status": "succeeded", "task_id": task_id, "output": ledger["output"],
         "qa_path": _relative_to_run(ledger_path, run), "postprocess": postprocess},
    )
    return ledger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a fixed 30s/720p Seedance 2.5 video through the NewB membership API."
    )
    parser.add_argument("--run", help="Run directory (outputs go to generated/, raw/, qa/).")
    parser.add_argument("--quota", action="store_true", help="Only print the NewB membership quota.")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file", help=f"Default: <run>/{DEFAULT_PROMPT_FILE}")
    parser.add_argument(
        "--image", action="append", default=[],
        help="Local JPG/PNG/WebP reference. Repeat; order defines @图1, @图2, ... (max 9).",
    )
    parser.add_argument("--ratio", choices=RATIOS, help="Default: from the manifest platform, else 9:16.")
    parser.add_argument("--label", default=DEFAULT_LABEL, help="Output name; use take-02 etc. for rerolls.")
    parser.add_argument(
        "--strip-audio", action="store_true",
        help="Remove NewB native audio. Default keeps it: the house audio is ambient sound only.",
    )
    parser.add_argument("--allow-timeline", action="store_true", help="Submit even if the prompt has timestamps.")
    parser.add_argument(
        "--resume", metavar="TASK_ID",
        help="Poll and download an existing task instead of submitting. 'auto' reads the manifest.",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--base-url")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.quota:
            config = resolve_config(base_url=args.base_url)
            if not config["api_key"]:
                raise NewBRunnerError(f"Set {' or '.join(KEY_ENV_NAMES)} in .env.local or the environment")
            result = get_quota(config)
        else:
            if not args.run:
                raise NewBRunnerError("--run is required unless --quota is used")
            result = run_newb_video(
                args.run,
                prompt=args.prompt,
                prompt_file=args.prompt_file,
                images=args.image,
                ratio=args.ratio,
                label=args.label,
                strip_audio=args.strip_audio,
                allow_timeline=args.allow_timeline,
                resume_task_id=args.resume,
                overwrite=args.overwrite,
                base_url=args.base_url,
                dry_run=args.dry_run,
                timeout_seconds=args.timeout,
                poll_interval=max(args.poll_interval, 10.0),
            )
    except (NewBRunnerError, NewBNetworkError) as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
