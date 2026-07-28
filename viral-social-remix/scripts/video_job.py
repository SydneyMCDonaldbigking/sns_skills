"""Deterministic Seedance video-job planning and reference compilation.

The manifest stores semantic reference ids and editorial intent. This module
turns that stable plan into provider-ordered media references and compiles
``{{ref:<id>}}`` placeholders into BytePlus labels such as ``[Image 1]``.
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse


REFERENCE_TYPES = ("image", "video", "audio")
REFERENCE_LABELS = {
    "image": "Image",
    "video": "Video",
    "audio": "Audio",
}
REFERENCE_ROLES = {
    "image": "reference_image",
    "video": "reference_video",
    "audio": "reference_audio",
}
REFERENCE_CONTENT_FIELDS = {
    "image": "image_url",
    "video": "video_url",
    "audio": "audio_url",
}
REFERENCE_LIMITS = {
    "image": 9,
    "video": 3,
    "audio": 3,
}
PROFILE_DEFAULTS = {
    "smoke": {
        "duration": 5,
        "resolution": "720p",
        "generate_audio": False,
        "watermark": False,
        "return_last_frame": False,
    },
    "visual-preview": {
        "duration": 5,
        "resolution": "1080p",
        "generate_audio": False,
        "watermark": False,
        "return_last_frame": True,
    },
    "final-clip": {
        "duration": 6,
        "resolution": "1080p",
        "generate_audio": False,
        "watermark": False,
        "return_last_frame": True,
    },
    "native-audio-final": {
        "duration": 6,
        "resolution": "1080p",
        "generate_audio": True,
        "watermark": False,
        "return_last_frame": True,
    },
    "legacy-storyboard": {
        "duration": 5,
        "resolution": "1080p",
        "generate_audio": False,
        "watermark": False,
        "return_last_frame": False,
    },
}
FINAL_SPEND_PROFILES = {"final-clip", "native-audio-final"}
SUPPORTED_RATIOS = {"21:9", "16:9", "4:3", "1:1", "3:4", "9:16", "adaptive"}
SUPPORTED_RESOLUTIONS = {"480p", "720p", "1080p"}
SEMANTIC_REFERENCE_RE = re.compile(r"\{\{ref:([A-Za-z0-9_.-]+)\}\}")
PROVIDER_REFERENCE_RE = re.compile(r"\[(Image|Video|Audio)\s+(\d+)\]", re.IGNORECASE)
AT_REFERENCE_RE = re.compile(r"@(?:Image|Video|Audio)\s*\d+", re.IGNORECASE)


class VideoJobError(ValueError):
    """Raised when a video job cannot be compiled deterministically."""


def video_section(data: dict[str, Any]) -> dict[str, Any]:
    value = data.get("video")
    return value if isinstance(value, dict) else {}


def video_mode(data: dict[str, Any]) -> str:
    video = video_section(data)
    return str(
        video.get("mode")
        or data.get("video_mode")
        or data.get("generation_mode")
        or "storyboard"
    )


def default_profile(data: dict[str, Any]) -> str:
    video = video_section(data)
    explicit = video.get("profile") or data.get("video_profile")
    if explicit:
        name = str(explicit)
    elif video_mode(data) == "compact-reference":
        name = "visual-preview"
    else:
        name = "legacy-storyboard"
    if name not in PROFILE_DEFAULTS:
        raise VideoJobError(
            f"Unsupported video profile {name!r}; choose one of: "
            + ", ".join(sorted(PROFILE_DEFAULTS))
        )
    return name


def generation_defaults(data: dict[str, Any], platform: str) -> dict[str, Any]:
    profile = default_profile(data)
    defaults = dict(PROFILE_DEFAULTS[profile])
    defaults["ratio"] = "9:16" if platform == "vertical-video" else "16:9"
    video = video_section(data)
    configured = video.get("generation")
    if isinstance(configured, dict):
        for key in [
            "ratio",
            "duration",
            "resolution",
            "generate_audio",
            "watermark",
            "return_last_frame",
        ]:
            if configured.get(key) is not None:
                defaults[key] = configured[key]
    defaults["profile"] = profile
    return defaults


def budget_summary(data: dict[str, Any]) -> dict[str, Any]:
    video = video_section(data)
    configured = video.get("budget")
    configured = configured if isinstance(configured, dict) else {}
    generation = data.get("video_generation")
    generation = generation if isinstance(generation, dict) else {}
    try:
        retry_limit = int(configured.get("retry_limit", 1))
        attempts = int(generation.get("attempts", 0))
    except (TypeError, ValueError) as exc:
        raise VideoJobError(
            "video.budget.retry_limit and video_generation.attempts must be integers"
        ) from exc
    if retry_limit < 0 or attempts < 0:
        raise VideoJobError(
            "video.budget.retry_limit and video_generation.attempts cannot be negative"
        )
    return {
        "retry_limit": retry_limit,
        "max_attempts": retry_limit + 1,
        "attempts": attempts,
        "remaining_attempts": max(0, retry_limit + 1 - attempts),
        "stop_before_final": bool(configured.get("stop_before_final", False)),
    }


def authorize_submission(
    data: dict[str, Any],
    *,
    profile: str,
    approve_final_spend: bool,
    force: bool = False,
) -> dict[str, Any]:
    budget = budget_summary(data)
    generation = data.get("video_generation")
    generation = generation if isinstance(generation, dict) else {}
    prior_status = str(generation.get("status") or "")
    if prior_status in {
        "preflight_validated",
        "submitted",
        "succeeded",
    } and not force:
        raise VideoJobError(
            f"Manifest video_generation.status is {prior_status!r}; refusing a "
            "possible duplicate paid submission. Inspect the existing task/output "
            "and pass --force only when a new attempt is intentional."
        )
    if (
        budget["stop_before_final"]
        and profile in FINAL_SPEND_PROFILES
        and not approve_final_spend
    ):
        raise VideoJobError(
            f"Profile {profile!r} is a final-spend profile and the manifest has "
            "video.budget.stop_before_final enabled; review the dry run and pass "
            "--approve-final-spend to submit"
        )
    if budget["attempts"] >= budget["max_attempts"]:
        raise VideoJobError(
            "Seedance submission budget is exhausted: "
            f"{budget['attempts']} attempt(s) recorded with retry_limit "
            f"{budget['retry_limit']}"
        )
    return {
        **budget,
        "attempt": budget["attempts"] + 1,
        "remaining_attempts_after_submit": max(
            0,
            budget["max_attempts"] - budget["attempts"] - 1,
        ),
        "final_spend_approved": bool(approve_final_spend),
        "forced": bool(force),
    }


def _values(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _kind_from_value(value: str, fallback: str = "image") -> str:
    path = urlparse(value).path if _is_url(value) else value
    mime = mimetypes.guess_type(path)[0] or ""
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("audio/"):
        return "audio"
    if mime.startswith("image/"):
        return "image"
    return fallback


def _source_from_entry(entry: dict[str, Any], kind: str) -> tuple[str, str]:
    url_keys = [
        "url",
        f"{kind}_url",
        "reference_url",
        "storyboard_url" if kind == "image" else "",
    ]
    path_keys = ["path", f"{kind}_path", "reference_path"]
    urls = [str(entry[key]) for key in url_keys if key and entry.get(key)]
    paths = [str(entry[key]) for key in path_keys if entry.get(key)]
    if len(urls) + len(paths) != 1:
        raise VideoJobError(
            f"Reference {entry.get('id')!r} must contain exactly one URL or path"
        )
    return ("url", urls[0]) if urls else ("path", paths[0])


def _normalize_reference(
    entry: dict[str, Any],
    *,
    index: int,
    default_kind: str | None = None,
) -> dict[str, Any]:
    raw_kind = entry.get("type") or entry.get("kind") or default_kind
    if raw_kind is None:
        candidate = (
            entry.get("url")
            or entry.get("path")
            or entry.get("reference_url")
            or entry.get("reference_path")
            or ""
        )
        raw_kind = _kind_from_value(str(candidate))
    kind = str(raw_kind).lower()
    if kind not in REFERENCE_TYPES:
        raise VideoJobError(
            f"Reference {entry.get('id')!r} has unsupported type {kind!r}"
        )
    source_kind, source = _source_from_entry(entry, kind)
    reference_id = str(entry.get("id") or f"{kind}-{index:02d}")
    raw_order = entry.get("order")
    if raw_order is None:
        order = index
    else:
        try:
            order = int(raw_order)
        except (TypeError, ValueError) as exc:
            raise VideoJobError(
                f"Reference {reference_id!r} order must be an integer"
            ) from exc
        if order <= 0:
            raise VideoJobError(
                f"Reference {reference_id!r} order must be greater than zero"
            )
    return {
        "id": reference_id,
        "type": kind,
        "order": order,
        "source_kind": source_kind,
        "source": source,
        "role": str(entry.get("role") or REFERENCE_ROLES[kind]),
        "_index": index,
    }


def _legacy_references(data: dict[str, Any]) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    counter = 0
    for asset_id, asset_value in data.get("assets", {}).items():
        asset = asset_value if isinstance(asset_value, dict) else {}
        request = asset.get("request")
        request = request if isinstance(request, dict) else {}
        sources = [asset, request]
        for source in sources:
            for kind, keys in {
                "image": ["storyboard_url", "image_url", "reference_url"],
                "video": ["video_url", "reference_video_url"],
                "audio": ["audio_url", "reference_audio_url"],
            }.items():
                for key in keys:
                    for value in _values(source.get(key)):
                        counter += 1
                        references.append(
                            {
                                "id": f"{asset_id}-{kind}-{counter:02d}",
                                "type": kind,
                                "url": str(value),
                                "order": counter,
                            }
                        )
            for key in ["reference_paths", "reference_images"]:
                for value in _values(source.get(key)):
                    counter += 1
                    path = str(value)
                    references.append(
                        {
                            "id": f"{asset_id}-path-{counter:02d}",
                            "type": _kind_from_value(path),
                            "path": path,
                            "order": counter,
                        }
                    )
    return references


def collect_manifest_references(data: dict[str, Any]) -> list[dict[str, Any]]:
    video = video_section(data)
    configured = video.get("references")
    strict = isinstance(configured, list)
    raw_references = configured if strict else _legacy_references(data)
    normalized: list[dict[str, Any]] = []
    ids: set[str] = set()
    seen_sources: set[tuple[str, str]] = set()
    for index, raw in enumerate(raw_references or [], 1):
        if not isinstance(raw, dict):
            raise VideoJobError(f"Video reference #{index} must be an object")
        reference = _normalize_reference(raw, index=index)
        if reference["id"] in ids:
            raise VideoJobError(f"Duplicate video reference id: {reference['id']}")
        ids.add(reference["id"])
        source_key = (reference["type"], reference["source"])
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        normalized.append(reference)

    ordered: list[dict[str, Any]] = []
    for kind in REFERENCE_TYPES:
        group = sorted(
            (item for item in normalized if item["type"] == kind),
            key=lambda item: (item["order"], item["_index"]),
        )
        explicit_orders: set[int] = set()
        for ordinal, item in enumerate(group, 1):
            if item["order"] in explicit_orders and strict:
                raise VideoJobError(
                    f"Duplicate {kind} reference order: {item['order']}"
                )
            explicit_orders.add(item["order"])
            item = dict(item)
            item.pop("_index", None)
            item["ordinal"] = ordinal
            item["prompt_label"] = f"[{REFERENCE_LABELS[kind]} {ordinal}]"
            ordered.append(item)
    return ordered


def cli_references(
    *,
    image_refs: list[str] | None = None,
    video_refs: list[str] | None = None,
    audio_refs: list[str] | None = None,
) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    index = 0
    for kind, values in [
        ("image", image_refs or []),
        ("video", video_refs or []),
        ("audio", audio_refs or []),
    ]:
        for ordinal, value in enumerate(values, 1):
            index += 1
            source_key = "url" if _is_url(value) or value.startswith("data:") else "path"
            reference = _normalize_reference(
                {
                    "id": f"cli-{kind}-{ordinal:02d}",
                    "type": kind,
                    source_key: value,
                    "order": ordinal,
                },
                index=index,
            )
            references.append(reference)
    return references


def merge_reference_overrides(
    manifest_references: list[dict[str, Any]],
    explicit_references: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not explicit_references:
        return manifest_references
    overridden_types = {item["type"] for item in explicit_references}
    combined = [
        item for item in manifest_references if item["type"] not in overridden_types
    ] + explicit_references
    ordered: list[dict[str, Any]] = []
    for kind in REFERENCE_TYPES:
        group = sorted(
            (item for item in combined if item["type"] == kind),
            key=lambda item: (item["order"], item.get("id", "")),
        )
        for ordinal, item in enumerate(group, 1):
            item = dict(item)
            item.pop("_index", None)
            item["ordinal"] = ordinal
            item["prompt_label"] = f"[{REFERENCE_LABELS[kind]} {ordinal}]"
            ordered.append(item)
    return ordered


def add_continuity_reference(
    references: list[dict[str, Any]],
    value: str,
) -> list[dict[str, Any]]:
    source_key = "url" if _is_url(value) or value.startswith("data:") else "path"
    continuity = {
        "id": "previous-last-frame",
        "type": "image",
        "order": 0,
        "source_kind": source_key,
        "source": value,
        "role": REFERENCE_ROLES["image"],
    }
    return merge_reference_overrides(
        references,
        [continuity] + [
            item for item in references if item["type"] == "image"
        ],
    )


def _resolve_path(run_dir: Path, raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else run_dir / path


def materialize_references(
    run_dir: Path,
    references: list[dict[str, Any]],
    *,
    allow_data_url: bool,
) -> list[dict[str, Any]]:
    materialized: list[dict[str, Any]] = []
    for reference in references:
        item = dict(reference)
        source = str(item["source"])
        if item["source_kind"] == "url":
            if source.startswith("data:") and not allow_data_url:
                raise VideoJobError(
                    f"Reference {item['id']!r} uses a data URL; pass --allow-data-url "
                    "only after confirming provider support"
                )
            item["url"] = source
        else:
            path = _resolve_path(run_dir, source)
            if not path.is_file():
                raise VideoJobError(f"Missing local {item['type']} reference: {path}")
            if item["type"] != "image":
                raise VideoJobError(
                    f"Local {item['type']} reference {path} needs a public URL. "
                    "Upload it to trusted storage and store the URL in the manifest."
                )
            if not allow_data_url:
                raise VideoJobError(
                    f"Local image reference {path} needs a public reference image URL or "
                    "--allow-data-url after provider support is confirmed"
                )
            mime = mimetypes.guess_type(path.name)[0] or "image/png"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            item["url"] = f"data:{mime};base64,{encoded}"
        materialized.append(item)
    return materialized


def reference_counts(references: list[dict[str, Any]]) -> dict[str, int]:
    return {
        kind: sum(1 for item in references if item["type"] == kind)
        for kind in REFERENCE_TYPES
    }


def is_seedance_2(model: str) -> bool:
    lowered = model.lower()
    return "seedance-2-0" in lowered or "seedance-2.0" in lowered


def is_seedance_2_fast(model: str) -> bool:
    return is_seedance_2(model) and "fast" in model.lower()


def validate_generation(
    *,
    model: str,
    options: dict[str, Any],
    references: list[dict[str, Any]],
) -> None:
    counts = reference_counts(references)
    for kind, limit in REFERENCE_LIMITS.items():
        if counts[kind] > limit:
            raise VideoJobError(
                f"Seedance supports at most {limit} {kind} references; "
                f"found {counts[kind]}"
            )
    if counts["image"] + counts["video"] < 1:
        raise VideoJobError(
            "Seedance multimodal reference generation needs at least one image "
            "or video reference; audio-only input is not supported"
        )
    if not is_seedance_2(model):
        return
    duration = int(options["duration"])
    if duration < 4 or duration > 15:
        raise VideoJobError(
            f"Seedance 2.0 duration must be between 4 and 15 seconds; got {duration}"
        )
    ratio = str(options["ratio"])
    if ratio not in SUPPORTED_RATIOS:
        raise VideoJobError(
            f"Unsupported Seedance 2.0 ratio {ratio!r}; choose one of: "
            + ", ".join(sorted(SUPPORTED_RATIOS))
        )
    resolution = str(options["resolution"]).lower()
    if resolution not in SUPPORTED_RESOLUTIONS:
        raise VideoJobError(
            f"Unsupported Seedance 2.0 resolution {resolution!r}; choose one of: "
            + ", ".join(sorted(SUPPORTED_RESOLUTIONS))
        )
    if is_seedance_2_fast(model) and resolution == "1080p":
        raise VideoJobError("Seedance 2.0 Fast supports at most 720p")


def compile_prompt(
    prompt: str,
    references: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    by_id = {item["id"]: item for item in references}
    used_ids: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        reference_id = match.group(1)
        reference = by_id.get(reference_id)
        if reference is None:
            raise VideoJobError(
                f"Prompt references unknown semantic asset {reference_id!r}"
            )
        used_ids.add(reference_id)
        return str(reference["prompt_label"])

    compiled = SEMANTIC_REFERENCE_RE.sub(replace, prompt)
    invalid_at = AT_REFERENCE_RE.search(compiled)
    if invalid_at:
        raise VideoJobError(
            f"Use BytePlus provider labels such as [Image 1], not "
            f"{invalid_at.group(0)!r}"
        )

    counts = reference_counts(references)
    mentioned_labels: set[str] = set()
    for match in PROVIDER_REFERENCE_RE.finditer(compiled):
        kind_label = match.group(1).title()
        ordinal = int(match.group(2))
        kind = kind_label.lower()
        if ordinal < 1 or ordinal > counts[kind]:
            raise VideoJobError(
                f"Prompt uses [{kind_label} {ordinal}] but the request contains "
                f"{counts[kind]} {kind} reference(s)"
            )
        mentioned_labels.add(f"[{kind_label} {ordinal}]")

    warnings: list[str] = []
    unused = [
        item["id"]
        for item in references
        if item["id"] not in used_ids
        and item["prompt_label"] not in mentioned_labels
    ]
    if unused:
        warnings.append(
            "References sent but not explicitly named in the prompt: "
            + ", ".join(unused)
        )
    return compiled, warnings


def content_item(reference: dict[str, Any]) -> dict[str, Any]:
    kind = str(reference["type"])
    field = REFERENCE_CONTENT_FIELDS[kind]
    item = {
        "type": field,
        field: {"url": str(reference["url"])},
    }
    role = reference.get("role")
    if role:
        item["role"] = str(role)
    return item


def sanitized_references(references: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized: list[dict[str, Any]] = []
    for reference in references:
        item = {
            "id": reference["id"],
            "type": reference["type"],
            "ordinal": reference["ordinal"],
            "prompt_label": reference["prompt_label"],
            "role": reference["role"],
            "source_kind": reference["source_kind"],
        }
        if reference["source_kind"] == "path":
            item["source"] = reference["source"]
        else:
            item["source"] = "<external URL>"
        sanitized.append(item)
    return sanitized
