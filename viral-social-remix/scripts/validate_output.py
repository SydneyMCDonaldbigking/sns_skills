"""Validate platform delivery contracts."""

import json
from pathlib import Path

from PIL import Image


DIMENSIONS = {
    "xiaohongshu": (1152, 1536),
    "instagram-facebook": (1152, 1152),
    "video": (1920, 1080),
    "vertical-video": (1080, 1920),
}
STORYBOARD_ASSET_IDS = [f"{index:02d}" for index in range(1, 10)]


def validate_asset(path: str | Path, platform: str, text_review: str) -> dict:
    errors = []
    target = Path(path)
    if platform not in DIMENSIONS:
        errors.append(f"unsupported platform: {platform}")
    elif not target.is_file():
        errors.append(f"missing file: {target}")
    else:
        with Image.open(target) as image:
            expected = DIMENSIONS[platform]
            if image.size != expected:
                errors.append(
                    f"expected {expected[0]}x{expected[1]}, "
                    f"got {image.width}x{image.height}"
                )
    if text_review != "passed":
        errors.append("text review must be passed")
    return {"valid": not errors, "errors": errors}


def validate_delivery(
    root: str | Path,
    platform: str,
    caption_language: str | None = None,
) -> dict:
    base = Path(root)
    errors = []
    generated_dir = base / "generated"
    generated = sorted(generated_dir.glob("*.png")) if generated_dir.exists() else []
    language = caption_language or (
        "zh" if platform == "xiaohongshu" else "en"
    )
    required = [
        base / "analysis" / "breakdown.md",
        base / "analysis" / "copy.md",
        base / "analysis" / f"caption-{language}.txt",
        base / "analysis" / "prompts.md",
        base / "analysis" / "manifest.json",
        base / "overview" / "contact-sheet.png",
        base / "qa" / "validation.json",
    ]
    if platform == "vertical-video":
        required.extend(
            [
                base / "analysis" / "brief.md",
                base / "analysis" / "shot-list.md",
                base / "analysis" / "seedance-prompt.md",
            ]
        )
        required.extend(
            base / "analysis" / "page-prompts" / f"page-{index:02d}.md"
            for index in range(1, 10)
        )
    errors.extend(
        f"missing required file: {path}" for path in required if not path.is_file()
    )
    if platform in DIMENSIONS:
        expected = DIMENSIONS[platform]
        for asset in generated:
            with Image.open(asset) as image:
                if image.size != expected:
                    errors.append(
                        f"{asset.name}: expected {expected[0]}x{expected[1]}, "
                        f"got {image.width}x{image.height}"
                    )
    if platform in {"video", "vertical-video"} and len(generated) != 9:
        errors.append("exactly 9 generated frames")
    if platform == "vertical-video":
        for index in range(1, 10):
            expected_frame = generated_dir / f"page-{index:02d}.png"
            if not expected_frame.is_file():
                errors.append(f"missing required storyboard frame: {expected_frame}")

    manifest_path = base / "analysis" / "manifest.json"
    if manifest_path.is_file():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if platform == "vertical-video":
            asset_ids = list(data.get("assets", {}).keys())
            if asset_ids != STORYBOARD_ASSET_IDS:
                errors.append(
                    "vertical-video manifest assets must be exactly: "
                    + ", ".join(STORYBOARD_ASSET_IDS)
                )
        incomplete = [
            asset_id
            for asset_id, item in data.get("assets", {}).items()
            if item.get("status") != "validated"
        ]
        if incomplete:
            errors.append(f"manifest contains incomplete assets: {', '.join(incomplete)}")
    return {"valid": not errors, "errors": errors}
