"""Validate platform delivery contracts."""

import argparse
import json
from pathlib import Path

from PIL import Image


DIMENSIONS = {
    "xiaohongshu": (1152, 1536),
    "instagram-facebook": (1152, 1152),
    "video": (1920, 1080),
}


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
    language = caption_language or ("zh" if platform == "xiaohongshu" else "en")
    required = [
        base / "analysis" / "breakdown.md",
        base / "analysis" / "copy.md",
        base / "analysis" / f"caption-{language}.txt",
        base / "analysis" / "prompts.md",
        base / "analysis" / "manifest.json",
        base / "overview" / "contact-sheet.png",
    ]
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
    if platform == "video" and len(generated) != 9:
        errors.append("exactly 9 generated frames")

    manifest_path = base / "analysis" / "manifest.json"
    if manifest_path.is_file():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        incomplete = [
            asset_id
            for asset_id, item in data.get("assets", {}).items()
            if item.get("status") != "validated"
        ]
        if incomplete:
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
