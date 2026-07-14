#!/usr/bin/env python3
"""Validate a prepared remix run before image generation starts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_ANALYSIS = [
    "remix-context.md",
    "selected-assets.json",
    "selected-assets.md",
    "breakdown.md",
    "copy.md",
    "prompts.md",
    "manifest.json",
]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(run_dir: str | Path) -> dict:
    base = Path(run_dir)
    errors = []
    for folder in ["source", "analysis", "generated", "overview", "qa"]:
        if not (base / folder).is_dir():
            errors.append(f"missing directory: {folder}")
    analysis = base / "analysis"
    for name in REQUIRED_ANALYSIS:
        if not (analysis / name).is_file():
            errors.append(f"missing analysis file: {name}")

    manifest_path = analysis / "manifest.json"
    selected_path = analysis / "selected-assets.json"
    prompts_path = analysis / "prompts.md"
    if manifest_path.is_file():
        manifest = _load_json(manifest_path)
        platform = manifest.get("platform")
        if platform == "rednote" and not (analysis / "caption-zh.txt").is_file():
            errors.append("missing analysis file: caption-zh.txt")
        if platform == "instagram_facebook" and not (analysis / "caption-en.txt").is_file():
            errors.append("missing analysis file: caption-en.txt")
        asset_ids = list((manifest.get("assets") or {}).keys())
        if not asset_ids:
            errors.append("manifest has no assets")
    else:
        manifest = {}
        asset_ids = []

    if selected_path.is_file():
        selected = _load_json(selected_path)
        mapping = selected.get("source_images_by_asset") or {}
        for asset_id in asset_ids:
            if asset_id not in mapping:
                errors.append(f"selected-assets missing source mapping for: {asset_id}")
        if not selected.get("product_images"):
            errors.append("selected-assets has no product_images")

    if prompts_path.is_file() and asset_ids:
        prompts = prompts_path.read_text(encoding="utf-8")
        for asset_id in asset_ids:
            if f"## {asset_id}" not in prompts:
                errors.append(f"prompts missing section for: {asset_id}")

    return {
        "valid": not errors,
        "run_dir": str(base),
        "asset_count": len(asset_ids),
        "errors": errors,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    result = validate(args.run_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
