"""Validate platform delivery contracts."""

import argparse
import json
from pathlib import Path
import sys

from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import video_job


DIMENSIONS = {
    "xiaohongshu": (1152, 1536),
    "instagram-facebook": (1152, 1152),
    "video": (1920, 1080),
    "vertical-video": (1080, 1920),
}
STORYBOARD_ASSET_IDS = [f"{index:02d}" for index in range(1, 10)]
STORYBOARD_CLIP_GROUPS = [
    ["01", "02", "03"],
    ["04", "05", "06"],
    ["07", "08", "09"],
]


def _load_manifest(base: Path) -> dict | None:
    manifest_path = base / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _video_mode(data: dict | None) -> str:
    if not data:
        return "storyboard"
    return video_job.video_mode(data)


def _is_compact_reference(data: dict | None) -> bool:
    return _video_mode(data) == "compact-reference"


def _is_three_clip_storyboard(data: dict | None) -> bool:
    return _video_mode(data) == "storyboard-three-clips"


def _validate_three_clip_storyboard_job(data: dict) -> list[str]:
    errors: list[str] = []
    video = video_job.video_section(data)
    groups = video.get("clip_groups")
    actual_groups = [
        item.get("frames")
        for item in groups
        if isinstance(item, dict)
    ] if isinstance(groups, list) else []
    if actual_groups != STORYBOARD_CLIP_GROUPS:
        errors.append(
            "storyboard-three-clips groups must be exactly 01-03, 04-06, 07-09"
        )
    generation = video.get("generation")
    generation = generation if isinstance(generation, dict) else {}
    if generation.get("duration") != 6:
        errors.append("storyboard-three-clips duration must be 6 seconds")
    if generation.get("ratio") != "9:16":
        errors.append("storyboard-three-clips ratio must be 9:16")
    if generation.get("resolution") != "1080p":
        errors.append("storyboard-three-clips resolution must be 1080p")
    if generation.get("generate_audio") is not False:
        errors.append("storyboard-three-clips must generate without audio")
    brand = video.get("brand")
    brand = brand if isinstance(brand, dict) else {}
    if brand.get("strategy") != "storyboard-physical-prop":
        errors.append(
            "storyboard-three-clips brand strategy must be storyboard-physical-prop"
        )
    workflow = data.get("video_workflow")
    workflow = workflow if isinstance(workflow, dict) else {}
    clips = workflow.get("clips")
    if not isinstance(clips, dict) or list(clips) != [
        "clip-01",
        "clip-02",
        "clip-03",
    ]:
        errors.append(
            "storyboard-three-clips workflow must track clip-01, clip-02, clip-03"
        )
    return errors


def _validate_compact_job(base: Path, data: dict) -> list[str]:
    errors: list[str] = []
    try:
        references = video_job.collect_manifest_references(data)
    except video_job.VideoJobError as exc:
        return [f"invalid compact-reference manifest: {exc}"]

    counts = video_job.reference_counts(references)
    for kind, limit in video_job.REFERENCE_LIMITS.items():
        if counts[kind] > limit:
            errors.append(
                f"compact-reference manifest has {counts[kind]} {kind} "
                f"references; maximum is {limit}"
            )
    if counts["image"] + counts["video"] < 1:
        errors.append(
            "compact-reference manifest needs at least one image or video reference"
        )
    try:
        options = video_job.generation_defaults(data, "vertical-video")
        model = str(
            video_job.video_section(data).get("model")
            or "dreamina-seedance-2-0-260128"
        )
        video_job.validate_generation(
            model=model,
            options=options,
            references=references,
        )
    except video_job.VideoJobError as exc:
        message = str(exc)
        if message not in errors:
            errors.append(f"invalid compact generation settings: {message}")
    for reference in references:
        if reference["source_kind"] != "path":
            continue
        path = Path(reference["source"])
        path = path if path.is_absolute() else base / path
        if not path.is_file():
            errors.append(f"missing compact reference file: {path}")
        if reference["type"] in {"video", "audio"}:
            errors.append(
                f"local {reference['type']} reference needs a public URL before "
                f"Seedance submission: {path}"
            )

    video = video_job.video_section(data)
    if data.get("schema_version") == 2:
        shots = video.get("shots")
        if not isinstance(shots, list) or len(shots) != 3:
            errors.append(
                "Manifest v2 compact video.shots must contain exactly three soft shots"
            )
        delivery = video.get("delivery")
        if not isinstance(delivery, dict):
            errors.append("Manifest v2 compact video.delivery is required")
        workflow = data.get("video_workflow")
        if not isinstance(workflow, dict):
            errors.append("Manifest v2 compact video_workflow is required")
        else:
            for field in ["status", "visual_qa", "chatcut", "export_qa", "history"]:
                if field not in workflow:
                    errors.append(
                        f"Manifest v2 video_workflow.{field} is required"
                    )
        try:
            video_job.budget_summary(data)
        except video_job.VideoJobError as exc:
            errors.append(f"invalid compact video budget: {exc}")

    brand = video.get("brand")
    if isinstance(brand, dict):
        allowed_strategies = {
            "product-only",
            "physical-prop-rough",
            "post-composited-physical-prop",
            "clean-end-card",
            "no-brand-visible",
        }
        strategy = brand.get("strategy")
        if strategy and strategy not in allowed_strategies:
            errors.append(
                f"unsupported video brand strategy {strategy!r}; choose one of: "
                + ", ".join(sorted(allowed_strategies))
            )
    elif data.get("schema_version") == 2:
        errors.append("Manifest v2 compact video.brand strategy is required")

    prompt_path = base / "analysis" / "seedance-prompt.md"
    if prompt_path.is_file() and references:
        prompt = prompt_path.read_text(encoding="utf-8")
        if prompt.strip() and prompt.strip().upper() != "TODO":
            try:
                video_job.compile_prompt(prompt, references)
            except video_job.VideoJobError as exc:
                errors.append(f"invalid Seedance prompt references: {exc}")
    return errors


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
    if generated_dir.exists():
        pattern = "page-*.png" if platform in {"video", "vertical-video"} else "*.png"
        generated = sorted(generated_dir.glob(pattern))
    else:
        generated = []
    data = _load_manifest(base)
    compact_reference = platform == "vertical-video" and _is_compact_reference(data)
    three_clip_storyboard = (
        platform == "vertical-video" and _is_three_clip_storyboard(data)
    )
    language = caption_language or (
        "zh" if platform == "xiaohongshu" else "en"
    )
    required = [
        base / "analysis" / "breakdown.md",
        base / "analysis" / "copy.md",
        base / "analysis" / f"caption-{language}.txt",
        base / "analysis" / "prompts.md",
        base / "analysis" / "manifest.json",
    ]
    if not compact_reference:
        required.append(base / "overview" / "contact-sheet.png")
    if platform == "vertical-video":
        required.extend(
            [
                base / "analysis" / "brief.md",
                base / "analysis" / "shot-list.md",
                base / "analysis" / "seedance-prompt.md",
            ]
        )
        if not compact_reference:
            required.extend(
                base / "analysis" / "page-prompts" / f"page-{index:02d}.md"
                for index in range(1, 10)
            )
        if three_clip_storyboard:
            required.extend(
                base
                / "analysis"
                / "seedance-prompts"
                / f"clip-{index:02d}.md"
                for index in range(1, 4)
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
    if platform in {"video", "vertical-video"} and not compact_reference and len(generated) != 9:
        errors.append("exactly 9 generated frames")
    if platform == "vertical-video" and not compact_reference:
        for index in range(1, 10):
            expected_frame = generated_dir / f"page-{index:02d}.png"
            if not expected_frame.is_file():
                errors.append(f"missing required storyboard frame: {expected_frame}")

    if data:
        if platform == "vertical-video":
            asset_ids = list(data.get("assets", {}).keys())
            if not compact_reference and asset_ids != STORYBOARD_ASSET_IDS:
                errors.append(
                    "vertical-video manifest assets must be exactly: "
                    + ", ".join(STORYBOARD_ASSET_IDS)
                )
            if compact_reference and not asset_ids:
                video = video_job.video_section(data)
                if not isinstance(video.get("references"), list):
                    errors.append(
                        "compact-reference manifest must contain reference assets"
                    )
            if compact_reference:
                errors.extend(_validate_compact_job(base, data))
            if three_clip_storyboard:
                errors.extend(_validate_three_clip_storyboard_job(data))
        incomplete = [
            asset_id
            for asset_id, item in data.get("assets", {}).items()
            if item.get("status") != "validated"
        ]
        if incomplete and not compact_reference:
            errors.append(f"manifest contains incomplete assets: {', '.join(incomplete)}")
    return {"valid": not errors, "errors": errors}


def _write_report(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated social assets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    asset = subparsers.add_parser("asset", help="Validate one generated image.")
    asset.add_argument("path", type=Path)
    asset.add_argument("--platform", choices=sorted(DIMENSIONS), required=True)
    asset.add_argument(
        "--text-review", choices=["passed", "failed"], required=True
    )
    asset.add_argument("--report", type=Path)

    delivery = subparsers.add_parser(
        "delivery", help="Validate a complete timestamped run directory."
    )
    delivery.add_argument("run_dir", type=Path)
    delivery.add_argument("--platform", choices=sorted(DIMENSIONS), required=True)
    delivery.add_argument("--caption-language", choices=["zh", "en"])
    delivery.add_argument(
        "--report",
        type=Path,
        help="Defaults to <run_dir>/qa/validation.json.",
    )

    args = parser.parse_args()
    if args.command == "asset":
        result = validate_asset(args.path, args.platform, args.text_review)
        if args.report:
            _write_report(args.report, result)
    else:
        result = validate_delivery(
            args.run_dir, args.platform, args.caption_language
        )
        _write_report(
            args.report or args.run_dir / "qa" / "validation.json",
            result,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
