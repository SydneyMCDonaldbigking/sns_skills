"""Submit a prepared video run to Seedance through BytePlus ModelArk.

This runner is meant for the user's local terminal. Codex prepares the run
directory, reference assets, and Seedance prompt; the local runner reads the
ignored `.env.local` or environment for the API key, submits the async task,
polls it, and downloads the returned video.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
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
import video_job


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
DEFAULT_GENERATE_AUDIO = False
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
THREE_CLIP_STORYBOARD_MODE = "storyboard-three-clips"
DIRECTOR_THREE_CLIP_MODE = "director-first-frame-three-clips"
STORYBOARD_GROUPS = {
    1: ["01", "02", "03"],
    2: ["04", "05", "06"],
    3: ["07", "08", "09"],
}
DIRECTOR_GROUPS = {
    1: ["01"],
    2: ["02"],
    3: ["03"],
}
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
    defaults: dict[str, Any] | None = None,
    ratio: str | None = None,
    duration: str | int | None = None,
    resolution: str | None = None,
    generate_audio: bool | None = None,
    watermark: bool | None = None,
) -> dict[str, Any]:
    configured = defaults or {}
    default_ratio = str(
        configured.get("ratio") or DEFAULT_RATIOS.get(platform, DEFAULT_RATIO)
    )
    duration_value = (
        duration
        if duration is not None
        else os.environ.get(
            "VSR_SEEDANCE_DURATION",
            str(configured.get("duration") or DEFAULT_DURATION),
        )
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
        "resolution": resolution
        or os.environ.get(
            "VSR_SEEDANCE_RESOLUTION",
            str(configured.get("resolution") or DEFAULT_RESOLUTION),
        ),
        "generate_audio": (
            generate_audio
            if generate_audio is not None
            else _env_bool(
                "VSR_SEEDANCE_GENERATE_AUDIO",
                bool(configured.get("generate_audio", DEFAULT_GENERATE_AUDIO)),
            )
        ),
        "watermark": (
            watermark
            if watermark is not None
            else _env_bool(
                "VSR_SEEDANCE_WATERMARK",
                bool(configured.get("watermark", DEFAULT_WATERMARK)),
            )
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


def _video_mode(data: dict[str, Any]) -> str:
    return video_job.video_mode(data)


def _is_compact_reference(data: dict[str, Any]) -> bool:
    return _video_mode(data) == "compact-reference"


def _is_three_clip_storyboard(data: dict[str, Any]) -> bool:
    return _video_mode(data) == THREE_CLIP_STORYBOARD_MODE


def _is_director_three_clip(data: dict[str, Any]) -> bool:
    return _video_mode(data) == DIRECTOR_THREE_CLIP_MODE


def _validate_storyboard_ready(
    run_dir: Path,
    data: dict[str, Any],
    platform: str,
    asset_ids: list[str],
    expected_ids: list[str] | None = None,
) -> None:
    expected_ids = expected_ids or _expected_storyboard_ids()
    if asset_ids != expected_ids:
        raise SeedanceRunnerError(
            "Seedance requires the prepared opening/storyboard asset ids "
            f"{', '.join(expected_ids)} "
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


def _validate_compact_references(data: dict[str, Any], explicit_urls: list[str] | None) -> None:
    if explicit_urls:
        return
    urls = _manifest_storyboard_urls(data, list(data.get("assets", {}).keys()))
    paths = _manifest_reference_paths(data, list(data.get("assets", {}).keys()))
    if urls or paths:
        return
    raise SeedanceRunnerError(
        "Compact Seedance mode needs at least one reference image URL or local "
        "reference path. Pass --image-url, store image_url/reference_url/storyboard_url "
        "on manifest assets, or store reference_paths and use --allow-data-url."
    )


def _data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    redacted = json.loads(json.dumps(payload))
    for item in redacted.get("content", []):
        if not isinstance(item, dict):
            continue
        for field in ["image_url", "video_url", "audio_url"]:
            media_url = item.get(field)
            if isinstance(media_url, dict) and str(
                media_url.get("url", "")
            ).startswith("data:"):
                media_url["url"] = "<redacted data URL>"
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
    storyboard_group: int | None = None,
    director_first_frame: bool = False,
) -> str:
    prompt = base_prompt.strip()
    if storyboard_group:
        if director_first_frame:
            frame_id = DIRECTOR_GROUPS[storyboard_group][0]
            prompt = (
                f"{prompt}\n\nBegin exactly from the one supplied opening frame "
                f"{frame_id}. Treat it as the composition and continuity anchor, "
                "then create the intermediate action and camera movement. Reach "
                "the director-specified endpoint without repeating the full "
                "recipe or introducing actions from another clip."
            )
        else:
            frame_ids = STORYBOARD_GROUPS[storyboard_group]
            prompt = (
                f"{prompt}\n\nUse the three supplied images in order as the start, "
                f"middle, and end anchors for one continuous 6-second clip "
                f"(storyboard frames {frame_ids[0]}-{frame_ids[-1]}). Do not repeat "
                "the full recipe or introduce actions from another clip."
            )
    else:
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


def _manifest_reference_paths(data: dict[str, Any], asset_ids: list[str]) -> list[str]:
    paths: list[str] = []
    for asset_id in asset_ids:
        asset = data.get("assets", {}).get(asset_id, {})
        paths.extend(_list_from_value(asset.get("reference_paths")))
        request = asset.get("request")
        if isinstance(request, dict):
            paths.extend(_list_from_value(request.get("reference_paths")))
            paths.extend(_list_from_value(request.get("reference_images")))
    return [path for path in paths if path]


def select_image_urls(
    run_dir: Path,
    data: dict[str, Any],
    asset_ids: list[str],
    *,
    image_urls: list[str] | None = None,
    include_all_frames: bool = False,
    allow_data_url: bool = False,
    compact_reference: bool = False,
) -> list[str]:
    urls = [url for url in image_urls or [] if url]
    if not urls:
        urls = _manifest_storyboard_urls(data, asset_ids)
    if urls:
        return urls if include_all_frames or compact_reference else urls[:1]

    if not allow_data_url:
        raise SeedanceRunnerError(
            "Seedance needs at least one reference image URL. Pass --image-url, "
            "store storyboard_url/image_url/reference_url on manifest assets, "
            "or use --allow-data-url only "
            "after confirming your provider accepts local data URLs."
        )

    reference_paths = _manifest_reference_paths(data, asset_ids)
    if reference_paths:
        selected_paths = reference_paths if include_all_frames or compact_reference else reference_paths[:1]
        data_urls: list[str] = []
        for raw_path in selected_paths:
            path = Path(raw_path)
            if not path.is_absolute():
                path = run_dir / path
            if not path.is_file():
                raise SeedanceRunnerError(f"Missing local reference image: {path}")
            data_urls.append(_data_url(path))
        return data_urls

    selected = asset_ids if include_all_frames or compact_reference else asset_ids[:1]
    data_urls: list[str] = []
    for asset_id in selected:
        path = _generated_path(run_dir, asset_id)
        if not path.is_file():
            raise SeedanceRunnerError(f"Missing generated/reference frame: {path}")
        data_urls.append(_data_url(path))
    return data_urls


def build_payload(
    prompt: str,
    *,
    model: str,
    image_urls: list[str] | None = None,
    references: list[dict[str, Any]] | None = None,
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
    if references is not None:
        content.extend(video_job.content_item(reference) for reference in references)
    else:
        for url in image_urls or []:
            item: dict[str, Any] = {
                "type": "image_url",
                "image_url": {"url": url},
            }
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


def _last_frame_url(response: dict[str, Any]) -> str | None:
    candidates: list[Any] = []
    content = response.get("content")
    if isinstance(content, dict):
        candidates.extend(
            [
                content.get("last_frame_url"),
                content.get("last_frame_image_url"),
                content.get("last_frame"),
            ]
        )
    candidates.extend(
        [
            response.get("last_frame_url"),
            response.get("last_frame_image_url"),
            response.get("last_frame"),
        ]
    )
    for value in candidates:
        if isinstance(value, str) and value:
            return value
        if isinstance(value, dict):
            nested = value.get("url") or value.get("image_url")
            if isinstance(nested, dict):
                nested = nested.get("url")
            if nested:
                return str(nested)
    return None


def _update_manifest_video(
    run_dir: Path,
    fields: dict[str, Any],
    *,
    workflow_status: str | None = None,
    generation_key: str | None = None,
) -> None:
    manifest_path = run_dir / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        return
    data = manifest.load(manifest_path)
    if generation_key:
        generations = data.get("video_generations")
        generations = generations if isinstance(generations, dict) else {}
        current = generations.get(generation_key)
        current = current if isinstance(current, dict) else {}
        current.update(fields)
        generations[generation_key] = current
        data["video_generations"] = generations
    else:
        current = data.get("video_generation")
        current = current if isinstance(current, dict) else {}
        current.update(fields)
        data["video_generation"] = current
    if workflow_status:
        workflow = data.get("video_workflow")
        workflow = workflow if isinstance(workflow, dict) else {}
        history = workflow.get("history")
        history = history if isinstance(history, list) else []
        history.append(
            {
                "status": workflow_status,
                "at": datetime.now(timezone.utc).isoformat(),
                **({"clip": generation_key} if generation_key else {}),
            }
        )
        if generation_key:
            clips = workflow.get("clips")
            clips = clips if isinstance(clips, dict) else {}
            clip = clips.get(generation_key)
            clip = clip if isinstance(clip, dict) else {}
            clip.update({**fields, "status": workflow_status})
            clips[generation_key] = clip
            clip_statuses = [
                str((clips.get(f"clip-{index:02d}") or {}).get("status"))
                for index in range(1, 4)
            ]
            if all(status == "generated" for status in clip_statuses):
                workflow["status"] = "generated"
                workflow["visual_qa"] = "pending"
            elif workflow_status == "failed":
                workflow["status"] = "clip_failed"
            else:
                workflow["status"] = "clips_generating"
            workflow["clips"] = clips
        else:
            workflow["status"] = workflow_status
            if workflow_status == "generated":
                workflow["visual_qa"] = "pending"
        workflow["history"] = history
        workflow.setdefault("chatcut", "not_started")
        workflow.setdefault("export_qa", "not_started")
        data["video_workflow"] = workflow
    _write_json(manifest_path, data)


def _register_last_frame(
    run_dir: Path,
    relative_path: str,
    *,
    generation_key: str | None = None,
) -> None:
    manifest_path = run_dir / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        return
    data = manifest.load(manifest_path)
    video = data.get("video")
    video = video if isinstance(video, dict) else {}
    continuity = video.get("continuity")
    continuity = continuity if isinstance(continuity, dict) else {}
    if generation_key:
        clips = continuity.get("clips")
        clips = clips if isinstance(clips, dict) else {}
        clips[generation_key] = {
            "last_frame_path": relative_path,
            "available": True,
        }
        continuity["clips"] = clips
    else:
        continuity.update(
            {
                "last_frame_path": relative_path,
                "available": True,
            }
        )
    video["continuity"] = continuity
    data["video"] = video
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


def _data_with_profile(
    data: dict[str, Any],
    profile: str | None,
) -> dict[str, Any]:
    if not profile:
        return data
    updated = json.loads(json.dumps(data))
    video = updated.get("video")
    video = video if isinstance(video, dict) else {}
    video["profile"] = profile
    updated["video"] = video
    return updated


def _legacy_generated_references(
    run_dir: Path,
    asset_ids: list[str],
    *,
    include_all_frames: bool,
) -> list[dict[str, Any]]:
    selected = asset_ids if include_all_frames else asset_ids[:1]
    return video_job.merge_reference_overrides(
        [],
        video_job.cli_references(
            image_refs=[
                str(_generated_path(run_dir, asset_id))
                for asset_id in selected
            ]
        ),
    )


def _continuity_reference_from_manifest(data: dict[str, Any]) -> str | None:
    video = video_job.video_section(data)
    continuity = video.get("continuity")
    if not isinstance(continuity, dict):
        return None
    value = continuity.get("last_frame_url") or continuity.get("last_frame_path")
    return str(value) if value else None


def _request_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _payload_for_lock(payload: dict[str, Any]) -> dict[str, Any]:
    locked = _redact_payload(payload)
    for item in locked.get("content", []):
        if not isinstance(item, dict):
            continue
        for field in ["image_url", "video_url", "audio_url"]:
            value = item.get(field)
            if isinstance(value, dict) and value.get("url") != "<redacted data URL>":
                value["url"] = "<external URL>"
    return locked


def run_seedance_video(
    run_dir: str | Path,
    *,
    prompt: str | None = None,
    prompt_file: str | Path | None = None,
    image_urls: list[str] | None = None,
    video_urls: list[str] | None = None,
    audio_urls: list[str] | None = None,
    include_all_frames: bool = False,
    storyboard_group: int | None = None,
    allow_data_url: bool = False,
    model: str | None = None,
    endpoint: str | None = None,
    profile: str | None = None,
    ratio: str | None = None,
    duration: str | None = None,
    resolution: str | None = None,
    generate_audio: bool | None = None,
    watermark: bool | None = None,
    seed: int | None = None,
    callback_url: str | None = None,
    return_last_frame: bool | None = None,
    approve_final_spend: bool = False,
    force: bool = False,
    continuity_reference: str | None = None,
    continue_from_last_frame: bool = False,
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
    compact_reference = _is_compact_reference(data)
    three_clip_storyboard = _is_three_clip_storyboard(data)
    director_three_clip = _is_director_three_clip(data)
    grouped_three_clip = three_clip_storyboard or director_three_clip
    generation_key: str | None = None
    selected_storyboard_ids = asset_ids
    selected_groups = DIRECTOR_GROUPS if director_three_clip else STORYBOARD_GROUPS
    if grouped_three_clip:
        if storyboard_group not in selected_groups:
            raise SeedanceRunnerError(
                "This run requires --storyboard-group 1, 2, or 3. "
                "Each paid Seedance request uses its prepared opening reference."
            )
        if include_all_frames:
            raise SeedanceRunnerError(
                "Do not use --include-all-frames with a three-clip cooking run; "
                "the selected group already supplies the intended reference."
            )
        if video_urls or audio_urls:
            raise SeedanceRunnerError(
                "The three-clip cooking route accepts only its image anchor(s); "
                "BGM, voiceover, and SFX are added later in ChatCut."
            )
        selected_storyboard_ids = selected_groups[storyboard_group]
        generation_key = f"clip-{storyboard_group:02d}"
    job_data = _data_with_profile(data, profile)
    if generation_key:
        generations = data.get("video_generations")
        generations = generations if isinstance(generations, dict) else {}
        job_data["video_generation"] = generations.get(generation_key, {})

    config = resolve_config(model=model, endpoint=endpoint)
    try:
        defaults = video_job.generation_defaults(job_data, str(platform))
    except video_job.VideoJobError as exc:
        raise SeedanceRunnerError(str(exc)) from exc
    options = resolve_generation_options(
        platform=platform,
        defaults=defaults,
        ratio=ratio,
        duration=duration,
        resolution=resolution,
        generate_audio=generate_audio,
        watermark=watermark,
    )
    effective_return_last_frame = (
        return_last_frame
        if return_last_frame is not None
        else bool(defaults.get("return_last_frame", False))
    )
    effective_prompt_file = prompt_file
    if generation_key and not prompt and not prompt_file:
        candidate = run / "analysis" / "seedance-prompts" / f"{generation_key}.md"
        if candidate.is_file():
            effective_prompt_file = candidate
    base_prompt, prompt_path = load_prompt(
        run,
        prompt=prompt,
        prompt_file=effective_prompt_file,
    )
    composed_prompt = compose_prompt(
        run,
        base_prompt,
        platform=platform,
        ratio=ratio,
        duration=duration,
        seed=seed,
        storyboard_group=storyboard_group if grouped_three_clip else None,
        director_first_frame=director_three_clip,
    )

    if not compact_reference and not dry_run:
        if not asset_ids:
            raise SeedanceRunnerError("Manifest does not contain storyboard assets")
        _validate_storyboard_ready(
            run,
            data,
            platform,
            asset_ids,
            expected_ids=["01", "02", "03"] if director_three_clip else None,
        )

    try:
        manifest_references = video_job.collect_manifest_references(job_data)
        explicit_references = video_job.cli_references(
            image_refs=image_urls,
            video_refs=video_urls,
            audio_refs=audio_urls,
        )
        references = video_job.merge_reference_overrides(
            manifest_references,
            explicit_references,
        )
        if grouped_three_clip:
            sources = [value for value in image_urls or [] if value]
            if not sources:
                sources = _manifest_storyboard_urls(
                    data,
                    selected_storyboard_ids,
                )
            if not sources:
                sources = [
                    str(_generated_path(run, asset_id))
                    for asset_id in selected_storyboard_ids
                ]
            expected_source_count = 1 if director_three_clip else 3
            if len(sources) != expected_source_count:
                raise video_job.VideoJobError(
                    f"{generation_key} requires exactly {expected_source_count} "
                    "image reference(s); "
                    f"found {len(sources)}"
                )
            references = video_job.merge_reference_overrides(
                [],
                video_job.cli_references(image_refs=sources),
            )
        elif not compact_reference and not include_all_frames:
            first_image = next(
                (item for item in references if item["type"] == "image"),
                None,
            )
            references = (
                ([first_image] if first_image else [])
                + [item for item in references if item["type"] != "image"]
            )
        if not references and not compact_reference and asset_ids:
            references = _legacy_generated_references(
                run,
                asset_ids,
                include_all_frames=include_all_frames,
            )

        continuity_value = continuity_reference
        if continue_from_last_frame:
            continuity_value = _continuity_reference_from_manifest(job_data)
            if not continuity_value:
                raise video_job.VideoJobError(
                    "Manifest does not contain video.continuity.last_frame_path "
                    "or last_frame_url"
                )
        if continuity_value:
            references = video_job.add_continuity_reference(
                references,
                continuity_value,
            )

        materialized_references = video_job.materialize_references(
            run,
            references,
            allow_data_url=allow_data_url,
        )
        if image_role:
            for reference in materialized_references:
                if reference["type"] == "image":
                    reference["role"] = image_role

        video_job.validate_generation(
            model=config["model"],
            options=options,
            references=materialized_references,
        )
        if grouped_three_clip:
            counts = video_job.reference_counts(materialized_references)
            expected_image_count = 1 if director_three_clip else 3
            expected_counts = {
                "image": expected_image_count,
                "video": 0,
                "audio": 0,
            }
            if counts != expected_counts:
                raise video_job.VideoJobError(
                    f"{generation_key} must compile to exactly "
                    f"{expected_image_count} image(s) and no "
                    f"video/audio references; found {counts}"
                )
            if options["duration"] != 6 or options["generate_audio"]:
                raise video_job.VideoJobError(
                    "The three-clip cooking route requires a silent 6-second Seedance "
                    "generation"
                )
        final_prompt, prompt_warnings = video_job.compile_prompt(
            composed_prompt,
            materialized_references,
        )
    except video_job.VideoJobError as exc:
        raise SeedanceRunnerError(str(exc)) from exc

    payload = build_payload(
        final_prompt,
        model=config["model"],
        references=materialized_references,
        ratio=options["ratio"],
        duration=options["duration"],
        resolution=options["resolution"],
        generate_audio=options["generate_audio"],
        watermark=options["watermark"],
        seed=seed,
        callback_url=callback_url,
        return_last_frame=effective_return_last_frame,
    )
    redacted_payload = _redact_payload(payload)
    counts = video_job.reference_counts(materialized_references)
    request_sha256 = _request_digest(payload)
    profile_name = str(defaults["profile"])
    preflight = {
        "schema_version": 1,
        "status": "passed",
        "video_mode": _video_mode(job_data),
        "storyboard_group": storyboard_group,
        "profile": profile_name,
        "model": config["model"],
        "prompt_path": prompt_path,
        "request_sha256": request_sha256,
        "references": video_job.sanitized_references(materialized_references),
        "reference_counts": counts,
        "generation": {
            **options,
            "return_last_frame": effective_return_last_frame,
        },
        "budget": video_job.budget_summary(job_data),
        "warnings": prompt_warnings,
    }
    if dry_run:
        return {
            "endpoint": config["endpoint"],
            "api_key_set": bool(config.get("api_key")),
            "image_count": counts["image"],
            "video_count": counts["video"],
            "audio_count": counts["audio"],
            "reference_count": sum(counts.values()),
            "video_mode": _video_mode(job_data),
            "storyboard_group": storyboard_group,
            "profile": profile_name,
            "generation": options,
            "request_sha256": request_sha256,
            "preflight": preflight,
            "payload": redacted_payload,
        }

    api_key = config.get("api_key")
    if not api_key:
        raise SeedanceRunnerError(
            "Set BYTEPLUS_ARK_API_KEY, BYTEPLUS_API_KEY, VSR_SEEDANCE_API_KEY, "
            "ARK_API_KEY, or SEEDANCE_API_KEY in .env.local or the local environment"
        )
    try:
        submission = video_job.authorize_submission(
            job_data,
            profile=profile_name,
            approve_final_spend=approve_final_spend,
            force=force,
        )
    except video_job.VideoJobError as exc:
        raise SeedanceRunnerError(str(exc)) from exc

    raw_dir = run / "raw"
    qa_dir = run / "qa"
    request_fn = request_fn or request_json
    download_fn = download_fn or download_video
    default_output = (
        run / "generated" / f"seedance-{generation_key}.mp4"
        if generation_key
        else run / "generated" / "seedance-video.mp4"
    )
    output_path = Path(output) if output else default_output
    if not output_path.is_absolute():
        output_path = run / output_path
    artifact_stem = f"seedance-{generation_key}" if generation_key else "seedance"

    request_lock = {
        **preflight,
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "submission": submission,
        "payload": _payload_for_lock(payload),
    }
    request_lock_path = (
        run / "analysis" / f"{artifact_stem}-request.lock.json"
    )
    _write_json(request_lock_path, request_lock)
    _write_json(raw_dir / f"{artifact_stem}-create-request.json", redacted_payload)
    _update_manifest_video(
        run,
        {
            "status": "preflight_validated",
            "profile": profile_name,
            "request_sha256": request_sha256,
            "request_lock": _relative_to_run(request_lock_path, run),
            "reference_counts": counts,
            "attempts": submission["attempt"],
            "generation": {
                **options,
                "return_last_frame": effective_return_last_frame,
            },
        },
        workflow_status="preflight_validated",
        generation_key=generation_key,
    )
    task_id: str | None = None
    try:
        create_response = request_fn("POST", config["endpoint"], api_key, payload)
        _write_json(raw_dir / f"{artifact_stem}-create-response.json", create_response)
        task_id = _task_id(create_response)
        _update_manifest_video(
            run,
            {
                "status": "submitted",
                "task_id": task_id,
                "model": config["model"],
                "endpoint": config["endpoint"],
                "prompt_path": prompt_path,
                "profile": profile_name,
                "reference_counts": counts,
                "attempts": submission["attempt"],
                "video_mode": _video_mode(job_data),
                "generation": {
                    **options,
                    "return_last_frame": effective_return_last_frame,
                },
            },
            workflow_status="submitted",
            generation_key=generation_key,
        )

        def on_status(response: dict[str, Any]) -> None:
            _write_json(raw_dir / f"{artifact_stem}-status.json", response)

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
        last_frame_output = None
        if effective_return_last_frame:
            last_frame_url = _last_frame_url(final_response)
            if last_frame_url:
                last_frame_path = output_path.with_name(
                    f"{output_path.stem}-last-frame.png"
                )
                download_fn(last_frame_url, last_frame_path)
                last_frame_output = _relative_to_run(last_frame_path, run)
                _register_last_frame(
                    run,
                    last_frame_output,
                    generation_key=generation_key,
                )
            else:
                prompt_warnings.append(
                    "return_last_frame was requested but the provider response "
                    "did not include a recognized last-frame URL"
                )
    except Exception as exc:
        failure = {
            "status": "failed",
            "attempts": submission["attempt"],
            "last_error": {"type": exc.__class__.__name__, "message": str(exc)},
        }
        if task_id:
            failure["task_id"] = task_id
        _update_manifest_video(
            run,
            failure,
            workflow_status="failed",
            generation_key=generation_key,
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
        "profile": profile_name,
        "image_count": counts["image"],
        "video_count": counts["video"],
        "audio_count": counts["audio"],
        "reference_count": sum(counts.values()),
        "reference_counts": counts,
        "video_mode": _video_mode(job_data),
        "storyboard_group": storyboard_group,
        "generation": {
            **options,
            "return_last_frame": effective_return_last_frame,
        },
        "request_sha256": request_sha256,
        "output": relative_output,
        "last_frame_output": last_frame_output,
        "warnings": prompt_warnings,
        "usage": final_response.get("usage", {}),
    }
    qa_path = qa_dir / f"{artifact_stem}-video.json"
    _write_json(qa_path, ledger)
    _update_manifest_video(
        run,
        {
            "status": "succeeded",
            "task_id": task_id,
            "output": relative_output,
            "qa_path": _relative_to_run(qa_path, run),
            "profile": profile_name,
            "request_sha256": request_sha256,
            "reference_counts": counts,
            "attempts": submission["attempt"],
            "last_frame_output": last_frame_output,
            "usage": final_response.get("usage", {}),
            "video_mode": _video_mode(job_data),
            "generation": {
                **options,
                "return_last_frame": effective_return_last_frame,
            },
        },
        workflow_status="generated",
        generation_key=generation_key,
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
        "--image-ref",
        dest="image_url",
        action="append",
        default=[],
        help="Image reference URL or local path. Repeat for references.",
    )
    parser.add_argument(
        "--video-url",
        "--video-ref",
        dest="video_url",
        action="append",
        default=[],
        help="Public video reference URL. Repeat up to three times.",
    )
    parser.add_argument(
        "--audio-url",
        "--audio-ref",
        dest="audio_url",
        action="append",
        default=[],
        help="Public audio reference URL. Repeat up to three times.",
    )
    parser.add_argument(
        "--include-all-frames",
        action="store_true",
        help="Send every available storyboard URL/reference instead of only the first.",
    )
    parser.add_argument(
        "--storyboard-group",
        type=int,
        choices=sorted(DIRECTOR_GROUPS),
        help=(
            "For three-clip cooking runs, select clip 1, 2, or 3. "
            "Director-first-frame mode maps these to opening frames 01, 02, or 03."
        ),
    )
    parser.add_argument(
        "--allow-data-url",
        action="store_true",
        help="Send local generated frames as data URLs when no image URL is available.",
    )
    parser.add_argument("--model")
    parser.add_argument("--endpoint")
    parser.add_argument(
        "--profile",
        choices=sorted(video_job.PROFILE_DEFAULTS),
        help="Generation profile; explicit CLI options still take precedence.",
    )
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
    last_frame = parser.add_mutually_exclusive_group()
    last_frame.add_argument(
        "--return-last-frame",
        dest="return_last_frame",
        action="store_true",
        default=None,
    )
    last_frame.add_argument(
        "--no-return-last-frame",
        dest="return_last_frame",
        action="store_false",
    )
    parser.add_argument(
        "--continuity-reference",
        help="Previous clip last-frame URL or local image path to prepend.",
    )
    parser.add_argument(
        "--continue-from-last-frame",
        action="store_true",
        help="Use video.continuity.last_frame_path/url from the manifest.",
    )
    parser.add_argument(
        "--approve-final-spend",
        action="store_true",
        help="Approve a final-spend profile when manifest budget requires it.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow an intentional new paid attempt despite a prior active/succeeded state.",
    )
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
            video_urls=args.video_url,
            audio_urls=args.audio_url,
            include_all_frames=args.include_all_frames,
            storyboard_group=args.storyboard_group,
            allow_data_url=args.allow_data_url,
            model=args.model,
            endpoint=args.endpoint,
            profile=args.profile,
            ratio=args.ratio,
            duration=args.duration,
            resolution=args.resolution,
            generate_audio=args.generate_audio,
            watermark=args.watermark,
            seed=args.seed,
            callback_url=args.callback_url,
            return_last_frame=args.return_last_frame,
            approve_final_spend=args.approve_final_spend,
            force=args.force,
            continuity_reference=args.continuity_reference,
            continue_from_last_frame=args.continue_from_last_frame,
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
