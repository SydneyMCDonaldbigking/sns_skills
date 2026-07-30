"""Minimal deterministic orchestration for viral-social-remix runs."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import create_run_dir
import image_provider
import manifest
import openrouter_image
import scan_media
import validate_output


VIDEO_PLATFORMS = {"video", "vertical-video"}
PLATFORMS = {"xiaohongshu", "instagram-facebook"} | VIDEO_PLATFORMS
COMMERCIAL_ROUTES = {"three-clip", "single-10s"}
VIDEO_REFERENCE_EXTENSIONS = {
    "image": {".jpg", ".jpeg", ".png", ".webp", ".heic"},
    "video": {".mp4", ".mov", ".webm", ".m4v"},
    "audio": {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"},
}
DEFAULT_SIZES = {
    "xiaohongshu": "1152x1536",
    "instagram-facebook": "1152x1152",
    "video": "1920x1080",
    "vertical-video": "1080x1920",
}
FIXED_COOKING_SHOTS = [
    "Clip 1 / first frame 01 / opening reference / 6s: product hook, package/prep, and first close-up insert.",
    "Clip 2 / first frame 02 / opening reference / 6s: move to real cooking location; show heat, stove, steamer, steam, or appliance action.",
    "Clip 3 / first frame 03 / opening reference / 6s: plate, serve, use, or present the finished product state and final hero.",
    "",
    "Seedance workshop contract: write instruction, not description. Every prompt must name SETTINGS, SUBJECTS/OBJECTS, VISUAL STYLE, LIGHTING/TONE, CAMERA, ACTION MECHANICS, TIMED BEATS, QUALITY, AUDIO, and CONSTRAINTS.",
    "Use the core formula subject + action + scene, then expand it into physical action details, explicit camera verbs, consistent visual style, concrete technical quality, and negative constraints.",
    "Direct each 6s Seedance clip as 2-3 commercial micro-shots, not one long camera move.",
    "Use timed beats: 0-2s establishing/action, 2-4s close-up insert or location move, 4-6s endpoint and transition handle.",
    "Official camera rule: write each micro-shot as a shot-order storyboard: subject + location + action + how the camera shoots it.",
    "Official lens rule: camera movement = starting frame composition + movement verb + direction/amplitude/speed + ending frame composition.",
    "Name shot size, camera angle, lens/focus feel, start frame, camera movement, and end frame. Prefer one camera move per micro-shot; combine only compatible moves deliberately.",
    "Use precise camera vocabulary: wide, medium, close-up, extreme close-up; eye-level, high angle, low angle, bird view; dolly-in/out, pan, track/follow, tilt, rise/fall, rotate/surround, zoom, rack focus, locked-off.",
    "Define physical lighting and emotional tone together; do not combine contradictory lighting and mood.",
    "Use one visual style across all references and clips. If references differ in style, make a consistent image reference before Seedance.",
    "Include at least one cooking-location/heat/steamer/stove beat when the product needs cooking.",
    "Include at least two close-up inserts across the sequence, such as product texture, steam, package opening, pour, utensil movement, sauce, crunch, plating, or final use.",
    "Brand as a commercial through clip 1 opening-frame product/sign visibility only; later clips do not need logo-sign continuity.",
    "Generate clip 1's 1080x1920 opening frame first with the configured image API.",
    "After each accepted clip, inspect its returned last frame and final motion strip. Use it directly only when clean; otherwise generate a transition opening anchor with the image model for a deliberate camera bridge.",
    "After each accepted clip except the final clip, run scripts/handoff_review.py to extract the final motion strip, write qa/handoffs/, and create the next prompt draft.",
    "During Seedance polling, prewrite the next clip prompt draft under analysis/seedance-prompts/drafts/ and leave only OPENING_REFERENCE and HANDOFF_MECHANISM unresolved.",
    "After each major stage, run scripts/next_step.py so analysis/next-step.json carries the next deterministic command.",
    "Give Seedance only the selected opening reference for each request.",
    "Every Seedance clip is 6s, 9:16, 1080p, and silent.",
    "While each Seedance clip is polling, draft external editable caption cues in analysis/caption-cues/clip-XX.json with clip-relative start/end/text; never burn captions into Seedance.",
    "Before ChatCut caption placement, run scripts/caption_cues.py with actual trims to compile analysis/caption-cues/chatcut-caption-plan.json.",
    "Before ChatCut import, run scripts/edit_plan.py with accepted MP4s and actual trims; read analysis/edit-plan.json before trimming/reframing.",
    "Before final handoff, run scripts/qa_decision_sheet.py to build qa/decision-sheet.html.",
    "Keep the same no-face hands, clothing, kitchen/table, light logic, product identity, and package when naturally visible.",
    "Opening references, returned last frames, and transition anchors are generation references and must not be imported into ChatCut.",
]
FIXED_SINGLE_10S_SHOTS = [
    "Single 10s route: one Seedance request, one coherent environment, 5-6 motivated commercial micro-shots.",
    "Use this for drinks, snacks, pantry, shelf-stable products, office rituals, and other products where the whole story can happen in one scene.",
    "Use the supplied product/page image as product bible and opening reference. Product/logo/package readability is required only in the first shot.",
    "Do not force logo, package text, or brand props to remain visible after the opening shot.",
    "Seedance workshop contract: write instruction, not description. The prompt must name SETTINGS, SUBJECTS/OBJECTS, VISUAL STYLE, LIGHTING/TONE, CAMERA, ACTION MECHANICS, QUALITY, AUDIO, and CONSTRAINTS.",
    "Write timed beats such as 0-1.2s product hero, 1.2-2.4s hand/use action, 2.4-4.2s preparation/pour, 4.2-6.2s macro texture/liquid/steam, 6.2-8.0s user ritual, 8.0-10.0s final hero.",
    "Use Shot 1 / Shot 2 / Shot 3 style ordering inside the 10s prompt when needed; each shot must state who/what, where, action, and camera.",
    "For each camera move, state start frame, movement verb, direction/amplitude/speed, and end frame. Use motivated cuts, macro inserts, push-ins, rack focus, object wipes, pour/steam motion bridges, and reframing.",
    "Keep camera movement simple, smooth, stable, and attached to the action's purpose. Do not make a single continuous camera drift.",
    "Keep visual style consistent across references; avoid style mixtures from mismatched source images.",
    "Every single-10s Seedance clip is 10s, 9:16, 1080p, and silent.",
    "While the Seedance job is polling, draft external editable caption cues in analysis/caption-cues/single-10s.json with clip-relative start/end/text; never burn captions into Seedance.",
    "Before ChatCut caption placement, run scripts/caption_cues.py with actual trims to compile analysis/caption-cues/chatcut-caption-plan.json.",
    "After generation, run scripts/next_step.py, scripts/edit_plan.py, and scripts/qa_decision_sheet.py before ChatCut handoff when editing is needed.",
    "Import the accepted MP4 into ChatCut only if BGM, captions, voiceover, trimming, or digital reframing is needed. Do not generate SFX.",
]
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
}


def _is_ignored(path: Path, root: Path) -> bool:
    return any(
        part in scan_media.IGNORED_DIRS or part.startswith(".")
        for part in path.relative_to(root).parts
    )


def is_url(value: str | Path) -> bool:
    parsed = urlparse(str(value))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _clean_content_type(value: str | None) -> str:
    return (value or "").split(";", 1)[0].strip().lower()


def _safe_stem(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", value.strip(), flags=re.UNICODE)
    return cleaned.strip(".-") or "remote-media"


def _filename_for_url(url: str, content_type: str) -> str:
    parsed = urlparse(url)
    name = Path(unquote(parsed.path)).name
    suffix = Path(name).suffix.lower()
    extension = suffix if suffix in scan_media.SUPPORTED else CONTENT_TYPE_EXTENSIONS.get(content_type)
    if not extension:
        raise ValueError(
            "URL did not resolve to a direct supported media file. "
            "Download the post media locally or provide a readable media URL."
        )
    stem = _safe_stem(Path(name).stem if name else "remote-media")
    return f"{stem}{extension}"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    suffix = path.suffix
    stem = path.stem
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}-{counter:02d}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def download_direct_media_url(url: str, target_dir: str | Path, opener=urlopen) -> dict:
    request = Request(url, headers={"User-Agent": "viral-social-remix/0.1"})
    try:
        with opener(request, timeout=60) as response:
            content_type = _clean_content_type(response.headers.get("Content-Type"))
            filename = _filename_for_url(url, content_type)
            data = response.read()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Unable to download URL: {url}") from exc

    if not data:
        raise ValueError(f"URL returned no media bytes: {url}")

    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    output = _unique_path(target / filename)
    output.write_bytes(data)
    return {
        "path": output.resolve(),
        "content_type": content_type,
        "bytes": len(data),
        "url": url,
    }


def collect_media(path: str | Path) -> list[Path]:
    source = Path(path)
    if source.is_file():
        if source.suffix.lower() not in scan_media.SUPPORTED:
            raise ValueError(f"Unsupported media file: {source}")
        return [source.resolve()]
    if not source.is_dir():
        raise ValueError(f"Expected a media file or directory: {source}")

    files = sorted(
        item.resolve()
        for item in source.rglob("*")
        if item.is_file()
        and item.suffix.lower() in scan_media.SUPPORTED
        and not _is_ignored(item, source)
    )
    if not files:
        raise ValueError(f"No supported media found in: {source}")
    return files


def _validate_media_for_platform(files: list[Path], platform: str) -> None:
    has_image = any(path.suffix.lower() in scan_media.IMAGE_EXTENSIONS for path in files)
    has_video = any(path.suffix.lower() in scan_media.VIDEO_EXTENSIONS for path in files)
    if platform in VIDEO_PLATFORMS and not has_video:
        raise ValueError("Video platform requires at least one video file")
    if platform not in VIDEO_PLATFORMS and has_video:
        raise ValueError("Image carousel platforms do not accept video files")
    if platform not in VIDEO_PLATFORMS and not has_image:
        raise ValueError("Image carousel platforms require image files")


def _asset_ids(platform: str, files: list[Path]) -> list[str]:
    count = 9 if platform in VIDEO_PLATFORMS else len(files)
    return [f"{index:02d}" for index in range(1, count + 1)]


def _caption_language(platform: str, value: str | None) -> str:
    if value:
        return value
    return "zh" if platform == "xiaohongshu" else "en"


def _write_if_missing(path: Path, text: str) -> None:
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def fixed_cooking_shot_list() -> str:
    return "# Shot List\n\n" + "\n".join(FIXED_COOKING_SHOTS) + "\n"


def fixed_single_10s_shot_list() -> str:
    return "# Shot List\n\n" + "\n".join(FIXED_SINGLE_10S_SHOTS) + "\n"


def director_opening_frame_prompt(brief_text: str, group: int) -> str:
    opening_plans = {
        1: (
            "Design the clip 1 opening reference. Start the commercial with a "
            "readable product/package hero, the official physical tabletop brand "
            "sign, and the first no-face hand action implied by the brief."
        ),
        2: (
            "This is the clip 2 on-demand transition opening slot. Generate it "
            "only after clip 1 has an accepted returned last frame and only if "
            "that last frame is too weak to use directly for the next action. "
            "Do not copy a damaged endpoint literally; design a cleaner camera "
            "bridge into cooking/preparation. When a prior last-frame or last "
            "motion-strip reference is supplied, preserve its usable food state, "
            "hands, lighting, camera angle, and action direction."
        ),
        3: (
            "This is the clip 3 on-demand transition opening slot. Generate it "
            "only after clip 2 has an accepted returned last frame and only if "
            "that last frame is too weak to use directly for the next action. "
            "Do not copy a damaged endpoint literally; design a cleaner camera "
            "bridge into serving or the final hero. When a prior last-frame or "
            "last motion-strip reference is supplied, preserve its usable "
            "product state, hands, lighting, camera angle, and action direction."
        ),
    }
    transition_plans = {
        1: "The frame must be able to move into clip 1's first action.",
        2: "The frame must bridge from clip 1's usable endpoint into the main transformation through match action, steam/lid/pour/object occlusion, rack focus, texture insert, or another motivated camera transition.",
        3: "The frame must bridge from clip 2's usable endpoint into serving, use, or final presentation through match action, steam/lid/pour/object occlusion, rack focus, texture insert, plate movement, or another motivated camera transition.",
    }
    brand_plan = (
        "Render the official ASIAN GROCER ONLINE / powered by UMALL logo only "
        "as a real printed tabletop sign with perspective, shadow, and partial "
        "scene occlusion. It must be readable in clip 1's opening frame."
        if group == 1
        else (
            "Do not force the physical logo sign into this later opening. Include "
            "the product package only when it naturally supports the composition."
        )
    )
    return (
        f"# Opening Frame {group:02d}\n\n"
        f"PRODUCT BRIEF:\n{brief_text}\n\n"
        "Create a single 1080x1920 photorealistic premium grocery/product "
        "commercial opening reference for Seedance. This is a still-image "
        "direction prompt, not a finished-video description.\n\n"
        f"USE CONDITION: {opening_plans[group]}\n"
        "SCENE: choose the exact product-appropriate location, surface, props, "
        "time of day, atmosphere, and commercial mood for this clip's starting "
        "state.\n"
        "SUBJECTS/OBJECTS: no-face hands, the exact product from the brief, "
        "package only when useful, cookware/tableware/props, and the current "
        "food/product state. Keep hands, clothing, product identity, lighting, "
        "and color grade consistent with the sequence.\n"
        "COMPOSITION: vertical 9:16 frame with a clear action start, product "
        "readability where needed, and negative space only when it serves the "
        "shot. No floating graphics.\n"
        "FRAMING/LENS: name the shot size, camera angle, lens/focus feel, focal "
        "plane, and subject placement. The still must clearly imply the first "
        "motion's start frame and the intended end frame.\n"
        "BRAND: "
        f"{brand_plan}\n"
        "MOTION READINESS: "
        f"{transition_plans[group]} Show the hand/tool/object position that can "
        "continue into motion with a matched action, steam/lid/object occlusion, "
        "pour/mix/plate movement, texture insert, or rack-focus bridge.\n"
        "QUALITY: sharp focus, believable food/product texture, realistic hands, "
        "natural steam/liquid/material behavior, premium controlled lighting, "
        "coherent commercial color grade.\n"
        "NEGATIVE: face, extra fingers, warped hands/tools, invented packaging, "
        "floating logo, overlay text, captions, title cards, lower-thirds, "
        "watermarks, unrelated props, scene teleporting.\n"
    )


def _mark_director_three_clip_mode(
    manifest_path: Path,
    storyboard_references: list[dict] | None = None,
) -> None:
    data = manifest.load(manifest_path)
    data["schema_version"] = 2
    data["video_mode"] = "director-first-frame-three-clips"
    data["storyboard_references"] = storyboard_references or []
    data["video"] = {
        "mode": "director-first-frame-three-clips",
        "profile": "final-clip",
        "clip_groups": [
            {
                "id": "clip-01",
                "frames": ["01"],
                "duration": 6,
            },
            {
                "id": "clip-02",
                "frames": ["02"],
                "duration": 6,
            },
            {
                "id": "clip-03",
                "frames": ["03"],
                "duration": 6,
            },
        ],
        "generation": {
            "ratio": "9:16",
            "duration": 6,
            "resolution": "1080p",
            "generate_audio": False,
            "return_last_frame": True,
            "watermark": False,
        },
        "delivery": {
            "ratio": "9:16",
            "resolution": "1080p",
            "target_duration": None,
            "duration_policy": "natural edit duration; do not force a fixed final length; use ChatCut as a second editing pass with split/trim, punch-in, reframe, subtle digital camera moves, and motivated short transitions",
            "expect_audio": True,
            "audio_policy": "user voiceover plus agent-generated BGM only; do not generate or place cooking SFX",
            "text_policy": "draft external clip-relative caption cues in analysis/caption-cues/ while Seedance is polling; before ChatCut caption placement run scripts/caption_cues.py with actual trims and read chatcut-caption-plan.json; place editable white centered current-step captions, subtle dark stroke/shadow, no colored box",
            "edit_policy": "before ChatCut import run scripts/edit_plan.py with accepted MP4s and actual trims, then follow analysis/edit-plan.json",
            "qa_policy": "use scripts/handoff_review.py after clip joins and scripts/qa_decision_sheet.py before final handoff",
        },
        "continuity": {
            "last_frame_path": None,
            "available": False,
            "handoff_policy": "inspect accepted prior clip's returned last frame and final motion strip; use a clean last frame directly or generate a transition opening anchor when the last frame is weak",
        },
        "brand": {
            "strategy": "first-frame-physical-prop",
            "asset": "viral-social-remix/umall_logo/asian-grocer-online-powered-by-umall.png",
            "visible_text": "physical-prop-only",
        },
        "budget": {
            "retry_limit": 1,
            "stop_before_final": True,
        },
    }
    data["video_workflow"] = {
        "status": "prepared",
        "visual_qa": "not_started",
        "chatcut": "not_started",
        "export_qa": "user_acceptance",
        "history": [],
        "clips": {
            "clip-01": {"frames": ["01"], "status": "prepared"},
            "clip-02": {"frames": ["02"], "status": "prepared"},
            "clip-03": {"frames": ["03"], "status": "prepared"},
        },
    }
    data["assumptions"].append(
        {
            "inferred": True,
            "value": "Director-led sequential handoff: generate clip 1 opening first; for clips 2 and 3 inspect the accepted prior clip's returned last frame and final motion strip before using it directly or generating a transition opening anchor for the next camera bridge. ChatCut imports only accepted MP4 clips.",
        }
    )
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _mark_single_10s_mode(
    manifest_path: Path,
    references: list[dict] | None = None,
) -> None:
    image_references = [
        item for item in references or [] if item.get("type") == "image"
    ]
    if not image_references:
        raise ValueError(
            "single-10s commercial route needs at least one product/page image reference"
        )
    data = manifest.load(manifest_path)
    data["schema_version"] = 2
    data["video_mode"] = "single-10s-commercial"
    data["storyboard_references"] = references or []
    data["assets"] = {}
    data["video"] = {
        "mode": "single-10s-commercial",
        "profile": "single-10s-final",
        "references": references or [],
        "shots": [
            {
                "id": "shot-01",
                "time": "0-1.2s",
                "purpose": "product identity",
                "note": "Readable product/package opening reference only.",
            },
            {
                "id": "shot-02",
                "time": "1.2-2.4s",
                "purpose": "convenience action",
                "note": "Hand opens, takes, places, tears, scoops, or prepares the product.",
            },
            {
                "id": "shot-03",
                "time": "2.4-4.2s",
                "purpose": "real use or preparation",
                "note": "Pour, brew, heat, mix, plate, or otherwise show practical use.",
            },
            {
                "id": "shot-04",
                "time": "4.2-6.2s",
                "purpose": "premium texture",
                "note": "Macro insert: steam, liquid bloom, gloss, crunch, texture, or ingredient detail.",
            },
            {
                "id": "shot-05",
                "time": "6.2-8.0s",
                "purpose": "lifestyle payoff",
                "note": "User ritual in the selected setting, no face.",
            },
            {
                "id": "shot-06",
                "time": "8.0-10.0s",
                "purpose": "final hero",
                "note": "Settled product/use-state hero. Package may return only if natural.",
            },
        ],
        "generation": {
            "ratio": "9:16",
            "duration": 10,
            "resolution": "1080p",
            "generate_audio": False,
            "return_last_frame": False,
            "watermark": False,
        },
        "delivery": {
            "ratio": "9:16",
            "resolution": "1080p",
            "target_duration": None,
            "duration_policy": "single coherent 10s Seedance multi-shot; ChatCut may trim/reframe when useful but should not force a fixed final length",
            "expect_audio": True,
            "audio_policy": "user voiceover plus agent-generated BGM only; do not generate or place SFX",
            "text_policy": "draft external clip-relative caption cues in analysis/caption-cues/ while Seedance is polling; before ChatCut caption placement run scripts/caption_cues.py with actual trims and read chatcut-caption-plan.json when captions are requested",
            "edit_policy": "after generation run scripts/edit_plan.py when ChatCut trimming/reframing is needed",
            "qa_policy": "run scripts/next_step.py and scripts/qa_decision_sheet.py before final handoff when editing is needed",
        },
        "brand": {
            "strategy": "first-frame-product-reference",
            "visible_text": "opening-product-or-package-only",
        },
        "budget": {
            "retry_limit": 1,
            "stop_before_final": True,
        },
    }
    data["video_workflow"] = {
        "status": "prepared",
        "visual_qa": "not_started",
        "chatcut": "not_started",
        "export_qa": "user_acceptance",
        "history": [],
        "clips": {
            "single-10s": {"status": "prepared", "duration": 10},
        },
    }
    data.setdefault("assumptions", []).append(
        {
            "inferred": True,
            "value": "Single-10s commercial route: use product/page image reference as visual bible, generate one 10s multi-shot Seedance clip, and use ChatCut only for trim/reframe/BGM/captions/handoff.",
        }
    )
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _video_reference_id(kind: str, index: int, value: str) -> str:
    stem = Path(urlparse(value).path if is_url(value) else value).stem
    return f"{kind}-{index:02d}-{_safe_stem(stem)[:32]}"


def _prepare_video_references(
    run_dir: Path,
    *,
    image_references: list[str] | None = None,
    video_references: list[str] | None = None,
    audio_references: list[str] | None = None,
) -> list[dict]:
    prepared: list[dict] = []
    reference_dir = run_dir / "references" / "inputs"
    for kind, values in [
        ("image", image_references or []),
        ("video", video_references or []),
        ("audio", audio_references or []),
    ]:
        for index, value in enumerate(values, 1):
            entry = {
                "id": _video_reference_id(kind, index, value),
                "type": kind,
                "order": index,
            }
            if is_url(value):
                entry["url"] = value
            else:
                source = Path(value).resolve()
                if not source.is_file():
                    raise ValueError(f"Missing {kind} reference: {source}")
                if source.suffix.lower() not in VIDEO_REFERENCE_EXTENSIONS[kind]:
                    raise ValueError(
                        f"Unsupported {kind} reference extension: {source.suffix}"
                    )
                reference_dir.mkdir(parents=True, exist_ok=True)
                target = _unique_path(reference_dir / source.name)
                shutil.copy2(source, target)
                entry["path"] = target.relative_to(run_dir).as_posix()
            prepared.append(entry)
    return prepared


def _copy_sources(input_path: Path, files: list[Path], run_dir: Path) -> list[str]:
    source_dir = run_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    base = input_path if input_path.is_dir() else input_path.parent
    for file_path in files:
        relative = file_path.relative_to(base.resolve())
        target = source_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, target)
        copied.append(target.relative_to(run_dir).as_posix())
    return copied


def _create_run_layout(run_dir: Path, platform: str, caption_language: str | None) -> None:
    for directory in [
        run_dir / "analysis",
        run_dir / "analysis" / "caption-cues",
        run_dir / "analysis" / "page-prompts",
        run_dir / "analysis" / "seedance-prompts" / "drafts",
        run_dir / "references" / "keyframes",
        run_dir / "generated",
        run_dir / "overview",
        run_dir / "qa",
        run_dir / "qa" / "handoffs",
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    analysis = run_dir / "analysis"
    if platform == "vertical-video":
        _write_if_missing(analysis / "shot-list.md", fixed_cooking_shot_list())
        _write_if_missing(analysis / "seedance-prompt.md", "# Seedance Prompt\n\nTODO\n")
        (analysis / "seedance-prompts").mkdir(parents=True, exist_ok=True)
        return

    language = _caption_language(platform, caption_language)
    _write_if_missing(analysis / "breakdown.md", "# Breakdown\n\nTODO\n")
    _write_if_missing(analysis / "copy.md", "# Copy\n\nTODO\n")
    _write_if_missing(analysis / "prompts.md", "# Prompts\n\nTODO\n")
    _write_if_missing(analysis / f"caption-{language}.txt", "TODO\n")
    if platform in VIDEO_PLATFORMS:
        _write_if_missing(analysis / "shot-list.md", "# Shot List\n\nTODO\n")
        _write_if_missing(analysis / "seedance-prompt.md", "# Seedance Prompt\n\nTODO\n")


def _task_name_for_url(url: str) -> str:
    parsed = urlparse(url)
    stem = Path(unquote(parsed.path)).stem
    return _safe_stem(stem or parsed.netloc or "url-source")


def prepare_url_run(
    url: str,
    platform: str,
    output_root: str | Path = "output",
    task_name: str | None = None,
    caption_language: str | None = None,
    opener=urlopen,
) -> Path:
    if platform not in PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")

    run_dir = create_run_dir.create(output_root, task_name or _task_name_for_url(url))
    media = download_direct_media_url(url, run_dir / "source", opener=opener)
    files = [Path(media["path"])]
    _validate_media_for_platform(files, platform)
    _create_run_layout(run_dir, platform, caption_language)

    copied_sources = [files[0].relative_to(run_dir).as_posix()]
    manifest.create(
        run_dir / "analysis" / "manifest.json",
        platform,
        _asset_ids(platform, files),
        source={
            "kind": "direct_url",
            "paths": copied_sources,
            "url": url,
            "content_type": media["content_type"],
            "bytes": media["bytes"],
        },
        provider=image_provider.resolve(),
    )
    return run_dir


def prepare_run(
    input_path: str | Path,
    platform: str,
    output_root: str | Path = "output",
    task_name: str | None = None,
    caption_language: str | None = None,
) -> Path:
    if platform not in PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")

    if is_url(input_path):
        return prepare_url_run(
            str(input_path),
            platform,
            output_root=output_root,
            task_name=task_name,
            caption_language=caption_language,
        )

    source = Path(input_path).resolve()
    files = collect_media(source)
    _validate_media_for_platform(files, platform)

    run_dir = create_run_dir.create(output_root, task_name or source.stem)
    copied_sources = _copy_sources(source, files, run_dir)
    _create_run_layout(run_dir, platform, caption_language)

    manifest.create(
        run_dir / "analysis" / "manifest.json",
        platform,
        _asset_ids(platform, files),
        source={
            "kind": "local_folder" if source.is_dir() else "local_file",
            "paths": copied_sources,
            "url": None,
        },
        provider=image_provider.resolve(),
    )
    return run_dir


def _read_brief(brief: str | None, brief_file: str | Path | None) -> tuple[str, str | None]:
    if brief and brief_file:
        raise ValueError("Use either --brief or --brief-file, not both")
    if brief_file:
        path = Path(brief_file)
        if not path.is_file():
            raise ValueError(f"Brief file does not exist: {path}")
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            raise ValueError(f"Brief file is empty: {path}")
        return text, str(path.resolve())
    if brief and brief.strip():
        return brief.strip(), None
    raise ValueError("Original video preparation requires --brief or --brief-file")


def prepare_original_video_run(
    *,
    brief: str | None = None,
    brief_file: str | Path | None = None,
    platform: str = "vertical-video",
    commercial_route: str = "three-clip",
    output_root: str | Path = "output",
    task_name: str | None = None,
    caption_language: str | None = None,
    image_references: list[str] | None = None,
    video_references: list[str] | None = None,
    audio_references: list[str] | None = None,
) -> Path:
    if platform not in VIDEO_PLATFORMS:
        raise ValueError(f"Original video platform must be one of: {', '.join(sorted(VIDEO_PLATFORMS))}")
    if commercial_route not in COMMERCIAL_ROUTES:
        raise ValueError(
            f"Commercial route must be one of: {', '.join(sorted(COMMERCIAL_ROUTES))}"
        )
    if platform != "vertical-video" and commercial_route != "three-clip":
        raise ValueError("single-10s commercial route is only supported for vertical-video")
    brief_text, brief_source = _read_brief(brief, brief_file)
    name = task_name or _safe_stem(brief_text.splitlines()[0][:48])
    run_dir = create_run_dir.create(output_root, name)
    _create_run_layout(run_dir, platform, caption_language)

    (run_dir / "analysis" / "brief.md").write_text(
        f"# Brief\n\n{brief_text}\n",
        encoding="utf-8",
    )
    video_references_prepared = _prepare_video_references(
        run_dir,
        image_references=image_references,
        video_references=video_references,
        audio_references=audio_references,
    )
    if platform == "vertical-video" and commercial_route == "single-10s":
        (run_dir / "analysis" / "shot-list.md").write_text(
            fixed_single_10s_shot_list(),
            encoding="utf-8",
        )
        (run_dir / "analysis" / "seedance-prompt.md").write_text(
            (
                "# Seedance Prompt\n\n"
                f"PRODUCT BRIEF:\n{brief_text}\n\n"
                "Create a premium 10-second vertical product commercial. This is an "
                "instruction prompt, not a description of an already finished video. "
                "Use [Image 1] as the opening product/package reference and visual "
                "product bible. The product/package/logo must be readable in the first "
                "shot only; do not force logo, package text, or product-pack visibility "
                "after the opening shot.\n\n"
                "SETTINGS: choose one practical real-life setting implied by the brief "
                "(office desk, home kitchen, pantry counter, beverage table, or another "
                "product-appropriate location) and keep it continuous for the whole "
                "clip. Name the environment, time of day, atmosphere, and commercial "
                "mood.\n"
                "SUBJECTS/OBJECTS: no-face human hands interact with the exact product "
                "from [Image 1]. Keep the product shape, pack color, key ingredients, "
                "props, tabletop, and hands/clothing consistent.\n"
                "VISUAL STYLE: photorealistic premium grocery/product commercial with "
                "one coherent color grade. Do not mix 3D/cartoon/stylized looks with "
                "real product photography.\n"
                "LIGHTING/TONE: specify a physical light source, direction, intensity, "
                "shadow behavior, contrast, and matching emotional tone. Avoid "
                "contradictory lighting and mood.\n"
                "CAMERA: for each micro-shot name shot size, angle, lens/focus feel, "
                "start frame, movement verb, direction/amplitude/speed, and end frame. "
                "Use simple purposeful moves such as locked-off product hero, stable "
                "dolly-in/push-in, cut-in, rack focus, object wipe, slight pan, or "
                "subtle follow. Smooth and stable, no jitter, no conflicting camera "
                "commands.\n"
                "ACTION MECHANICS: tie every action to hands, package, liquid, spoon, "
                "cup, bowl, plate, steam, wrapper, or product texture. State speed, "
                "force, range, and continuity between beats; prefer slow, gentle, "
                "continuous small movements.\n\n"
                "Commercial multi-shot rhythm:\n"
                "0-1.2s: product/package hero shot in the chosen real-life setting.\n"
                "1.2-2.4s: close-up hand action showing the product is easy to use.\n"
                "2.4-4.2s: practical preparation or serving action with a motivated cut.\n"
                "4.2-6.2s: macro premium texture insert: steam, liquid bloom, gloss, "
                "ingredient detail, or product texture.\n"
                "6.2-8.0s: no-face lifestyle payoff in the same setting.\n"
                "8.0-10.0s: final refined hero shot; product pack may appear only if it "
                "fits naturally.\n\n"
                "QUALITY: rich product detail, sharp focus, detailed food or packaging "
                "texture, natural steam/liquid/material behavior, realistic hands and "
                "props, controlled depth of field, clean premium color grading.\n"
                "AUDIO: generate_audio is false for this workflow. Do not ask Seedance "
                "for SFX, dialogue, music, subtitles, or voiceover; audio is finished "
                "later in ChatCut unless the user explicitly selects native audio.\n"
                "CONSTRAINTS: no face, no subtitles, no captions, no title cards, no "
                "lower-thirds, no burned-in text, no overlay graphics, no floating "
                "logo, no watermarks, no extra logos, no warped hands, no invented "
                "packaging, no scene teleporting.\n"
            ),
            encoding="utf-8",
        )
    elif platform == "vertical-video":
        for group in range(1, 4):
            _write_if_missing(
                run_dir
                / "analysis"
                / "page-prompts"
                / f"page-{group:02d}.md",
                director_opening_frame_prompt(brief_text, group),
            )
        group_actions = {
            1: (
                "0-2s establish the product pack, physical brand sign, setting, "
                "and the first no-face hand action from the brief. 2-4s cut or "
                "push into a close-up insert of package opening, ingredient "
                "texture, hand placement, pour, spoon, wrapper, or product surface. "
                "4-6s move toward the next preparation/cooking location and create "
                "a deliberate hand, object, steam, lid, pour, or rack-focus bridge "
                "for clip 2."
            ),
            2: (
                "0-2s begin from the selected clip 2 opening reference, chosen "
                "after inspecting clip 1's accepted returned last frame, and arrive "
                "at the main cooking/preparation action. 2-4s show the transformation "
                "that proves the product: heat, steamer, stove, appliance, pour, mix, "
                "sizzle, steam, liquid bloom, texture close-up, or assembly detail as "
                "appropriate to the brief. 4-6s use steam, lid lift, hand match, "
                "plate move, pour motion, or object occlusion as the bridge toward "
                "serving."
            ),
            3: (
                "0-2s begin from the selected clip 3 opening reference, chosen "
                "after inspecting clip 2's accepted returned last frame, and plate, "
                "serve, pour, scoop, lift, or present the finished product state. "
                "2-4s cut into the strongest texture/usage insert from the brief. "
                "4-6s settle on a refined final hero with the finished food or "
                "product-use state; include the product pack only if it fits "
                "naturally, and do not force the logo sign to return."
            ),
        }
        for group, action in group_actions.items():
            _write_if_missing(
                run_dir
                / "analysis"
                / "seedance-prompts"
                / f"clip-{group:02d}.md",
                (
                    f"# Seedance Clip {group:02d}\n\n"
                    f"PRODUCT BRIEF:\n{brief_text}\n\n"
                    "Begin exactly from the selected opening reference for this "
                    "clip. This is an instruction prompt, not a description of a "
                    "finished video.\n\n"
                    "SETTINGS: name the exact product-appropriate location, "
                    "environment, time of day, atmosphere, and commercial mood. "
                    "Keep it continuous with the accepted prior clip when this is "
                    "clip 2 or 3.\n"
                    "SUBJECTS/OBJECTS: no-face hands, the product from the brief, "
                    "its package when naturally visible, cookware/tableware/props, "
                    "and the current food/product state. Keep hands, clothing, "
                    "kitchen/table, product identity, and color grade consistent.\n"
                    "VISUAL STYLE: photorealistic premium grocery food commercial "
                    "with one coherent visual style; no style mixing from mismatched "
                    "references.\n"
                    "LIGHTING/TONE: physical light source, direction, intensity, "
                    "shadow behavior, contrast, and matching emotional tone.\n"
                    "CAMERA: direct a compact Shot 1 / Shot 2 / Shot 3 montage. "
                    "For each shot, name shot size, angle, lens/focus feel, start "
                    "frame composition, movement verb, direction/amplitude/speed, "
                    "and ending frame composition. Use simple purposeful moves such "
                    "as locked-off, stable dolly-in/push-in, cut-in, rack focus, "
                    "slight pan, track/follow, object wipe, steam/lid occlusion, or "
                    "match-action cut. Smooth, stable, no jitter, no conflicting "
                    "moves.\n"
                    "ACTION MECHANICS: tie actions to hands, package, liquid, heat, "
                    "steam, utensil, lid, plate, cup, wrapper, or product texture. "
                    "State speed, force, range, inertia, and how the action continues "
                    "into the next beat.\n\n"
                    f"TIMED BEATS: {action}\n\n"
                    "QUALITY: rich food/product detail, sharp focus, detailed texture, "
                    "natural steam/liquid/heat behavior, realistic hands and cookware, "
                    "controlled depth of field, premium believable color grading.\n"
                    "AUDIO: generate_audio is false for this workflow. Do not ask "
                    "Seedance for SFX, music, dialogue, voiceover, or subtitles; audio "
                    "is finished later in ChatCut unless the user explicitly selects "
                    "native audio.\n"
                    "BRAND: the physical ASIAN GROCER ONLINE / powered by UMALL "
                    "tabletop sign must read only in clip 1's opening reference / "
                    "first frame. Later clips do not need to preserve or repeat it; "
                    "food texture, cooking, plating, and usage can naturally push it "
                    "out of frame.\n"
                    "CONSTRAINTS: no face, no new objects, no scene teleporting, no "
                    "subtitles, no overlay text, no title cards, no lower-thirds, no "
                    "floating logo, no watermarks, no extra logos, no warped hands, "
                    "no invented packaging.\n"
                ),
            )
        draft_dir = run_dir / "analysis" / "seedance-prompts" / "drafts"
        for group in (2, 3):
            source_prompt = (
                run_dir / "analysis" / "seedance-prompts" / f"clip-{group:02d}.md"
            )
            if source_prompt.is_file():
                _write_if_missing(
                    draft_dir / f"clip-{group:02d}-handoff-draft.md",
                    (
                        f"# Clip {group:02d} Handoff Draft\n\n"
                        "Prewrite this while the prior Seedance clip is polling. "
                        "After the prior clip returns, fill only these two fields "
                        "from `scripts/handoff_review.py`:\n\n"
                        "OPENING_REFERENCE: <accepted previous last frame OR "
                        "generated transition opening anchor>\n"
                        "HANDOFF_MECHANISM: <match action / steam-lid occlusion / "
                        "pour-object bridge / rack focus / plate move / texture insert>\n\n"
                        "---\n\n"
                        + source_prompt.read_text(encoding="utf-8")
                    ),
                )
    manifest_path = run_dir / "analysis" / "manifest.json"
    manifest.create(
        manifest_path,
        platform,
        (
            ["01", "02", "03"]
            if platform == "vertical-video" and commercial_route == "three-clip"
            else ([] if platform == "vertical-video" else _asset_ids(platform, []))
        ),
        source={
            "kind": "original_brief",
            "paths": [brief_source] if brief_source else [],
            "url": None,
            "brief_path": "analysis/brief.md",
        },
        provider=image_provider.resolve(),
    )
    if platform == "vertical-video" and commercial_route == "single-10s":
        _mark_single_10s_mode(manifest_path, video_references_prepared)
    elif platform == "vertical-video":
        _mark_director_three_clip_mode(
            manifest_path,
            video_references_prepared,
        )
    return run_dir


def validate_run(
    run_dir: str | Path,
    platform: str,
    caption_language: str | None = None,
) -> dict:
    target = Path(run_dir)
    validation_path = target / "qa" / "validation.json"
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    if not validation_path.exists():
        validation_path.write_text("{}", encoding="utf-8")

    result = validate_output.validate_delivery(
        target,
        platform,
        caption_language=caption_language,
    )
    validation_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def pending_assets(manifest_path: str | Path) -> list[str]:
    return manifest.pending(manifest_path)


def generate_asset(
    run_dir: str | Path,
    asset_id: str,
    *,
    prompt_file: str | Path | None = None,
    out_dir: str | Path | None = None,
    size: str | None = None,
    stem: str | None = None,
    references: list[str] | None = None,
    max_attempts: int = 2,
    force: bool = False,
    dry_run: bool = False,
) -> dict:
    base = Path(run_dir)
    manifest_path = base / "analysis" / "manifest.json"
    data = manifest.load(manifest_path)
    platform = data["platform"]
    if platform not in DEFAULT_SIZES and not size:
        raise ValueError(f"No default size for platform: {platform}")

    return openrouter_image.generate_image(
        prompt_file=prompt_file or base / "analysis" / "prompts.md",
        out_dir=out_dir or base / "generated",
        stem=stem or asset_id,
        size=size or DEFAULT_SIZES[platform],
        references=references or [],
        max_attempts=max_attempts,
        manifest_path=manifest_path,
        asset_id=asset_id,
        force=force,
        dry_run=dry_run,
    )


def cmd_scan(args: argparse.Namespace) -> int:
    print(json.dumps(scan_media.scan(args.directory), ensure_ascii=False, indent=2))
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    run_dir = prepare_run(
        args.input,
        args.platform,
        output_root=args.output_root,
        task_name=args.task_name,
        caption_language=args.caption_language,
    )
    print(json.dumps({"run_dir": str(run_dir)}, ensure_ascii=False, indent=2))
    return 0


def cmd_prepare_original_video(args: argparse.Namespace) -> int:
    run_dir = prepare_original_video_run(
        brief=args.brief,
        brief_file=args.brief_file,
        platform=args.platform,
        commercial_route=args.commercial_route,
        output_root=args.output_root,
        task_name=args.task_name,
        caption_language=args.caption_language,
        image_references=args.image_reference,
        video_references=args.video_reference,
        audio_references=args.audio_reference,
    )
    print(json.dumps({"run_dir": str(run_dir)}, ensure_ascii=False, indent=2))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    result = validate_run(
        args.run_dir,
        args.platform,
        caption_language=args.caption_language,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


def cmd_pending(args: argparse.Namespace) -> int:
    print(
        json.dumps(
            {"pending": pending_assets(args.manifest)},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    result = generate_asset(
        args.run_dir,
        args.asset_id,
        prompt_file=args.prompt_file,
        out_dir=args.out_dir,
        size=args.size,
        stem=args.stem,
        references=args.reference,
        max_attempts=args.max_attempts,
        force=args.force,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan")
    scan.add_argument("directory")
    scan.set_defaults(func=cmd_scan)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("input")
    prepare.add_argument("--platform", required=True, choices=sorted(PLATFORMS))
    prepare.add_argument("--output-root", default="output")
    prepare.add_argument("--task-name")
    prepare.add_argument("--caption-language", choices=["zh", "en"])
    prepare.set_defaults(func=cmd_prepare)

    original = subparsers.add_parser("prepare-original-video")
    original.add_argument("--brief")
    original.add_argument("--brief-file")
    original.add_argument("--platform", choices=sorted(VIDEO_PLATFORMS), default="vertical-video")
    original.add_argument("--commercial-route", choices=sorted(COMMERCIAL_ROUTES), default="three-clip")
    original.add_argument("--output-root", default="output")
    original.add_argument("--task-name")
    original.add_argument("--caption-language", choices=["zh", "en"])
    original.add_argument("--image-reference", action="append", default=[])
    original.add_argument("--video-reference", action="append", default=[])
    original.add_argument("--audio-reference", action="append", default=[])
    original.set_defaults(func=cmd_prepare_original_video)

    validate = subparsers.add_parser("validate")
    validate.add_argument("run_dir")
    validate.add_argument("--platform", required=True, choices=sorted(PLATFORMS))
    validate.add_argument("--caption-language", choices=["zh", "en"])
    validate.set_defaults(func=cmd_validate)

    pending = subparsers.add_parser("pending")
    pending.add_argument("manifest")
    pending.set_defaults(func=cmd_pending)

    generate = subparsers.add_parser("generate")
    generate.add_argument("run_dir")
    generate.add_argument("--asset-id", required=True)
    generate.add_argument("--prompt-file")
    generate.add_argument("--out-dir")
    generate.add_argument("--size")
    generate.add_argument("--stem")
    generate.add_argument("--reference", action="append", default=[])
    generate.add_argument("--max-attempts", type=int, default=2)
    generate.add_argument("--force", action="store_true")
    generate.add_argument("--dry-run", action="store_true")
    generate.set_defaults(func=cmd_generate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())
