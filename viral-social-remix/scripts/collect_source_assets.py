#!/usr/bin/env python3
"""Register collected source assets into the local material index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import material_index


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: Path) -> str:
    return str(path).replace("\\", "/")


def _record_id(*parts: object) -> str:
    return "::".join(str(part) for part in parts if part not in (None, ""))


def records_from_rednote(run_dir: Path) -> list[dict]:
    manifest = _load_json(run_dir / "manifest.json")
    records = []
    for post in manifest.get("posts", []):
        folder = run_dir / post["folder"]
        metadata_path = folder / "metadata.json"
        metadata = _load_json(metadata_path) if metadata_path.exists() else {}
        records.append(
            {
                "record_id": _record_id("rednote", post.get("source_url"), post.get("folder")),
                "record_type": "post",
                "platform": "rednote",
                "source": "rednote_export",
                "run_dir": _rel(run_dir),
                "folder": post.get("folder"),
                "title": post.get("title"),
                "source_url": post.get("source_url"),
                "date": post.get("date"),
                "image_count": post.get("image_count"),
                "reasons": post.get("reasons", []),
                "caption_path": None,
                "content_path": _rel(folder / "content.md"),
                "metadata_path": _rel(metadata_path),
                "image_paths": [
                    _rel(folder / image["file"])
                    for image in metadata.get("images", [])
                    if image.get("status") == "downloaded"
                ],
            }
        )
    return records


def records_from_instagram(run_dir: Path) -> list[dict]:
    manifest = _load_json(run_dir / "posts_manifest.json")
    records = []
    for post in manifest.get("posts", []):
        folder = next((run_dir / "posts").glob(f"post-{post['post_index']:03d}-*"), None)
        if folder is None:
            continue
        metadata_path = folder / "metadata.json"
        metadata = _load_json(metadata_path)
        records.append(
            {
                "record_id": _record_id("instagram_facebook", post.get("source_url"), post.get("id")),
                "record_type": "post",
                "platform": "instagram_facebook",
                "source": "instagram_export",
                "run_dir": _rel(run_dir),
                "folder": _rel(folder.relative_to(run_dir)),
                "title": post.get("id"),
                "source_url": post.get("source_url"),
                "date": post.get("metrics", {}).get("date_text"),
                "image_count": post.get("image_count"),
                "label": post.get("label"),
                "caption_path": _rel(folder / "caption.txt"),
                "content_path": _rel(folder / "content.md"),
                "metadata_path": _rel(metadata_path),
                "image_paths": [
                    _rel(folder / image["file"])
                    for image in metadata.get("images", [])
                    if image.get("status") == "downloaded"
                ],
            }
        )
    return records


def records_from_brand_assets(run_dir: Path) -> list[dict]:
    manifest = _load_json(run_dir / "assets_manifest.json")
    records = []
    for asset in manifest.get("assets", []):
        if asset.get("status") != "downloaded":
            continue
        records.append(
            {
                "record_id": _record_id("brand_site", asset.get("source_url"), asset.get("file")),
                "record_type": "asset",
                "platform": "brand_site",
                "source": "umall_official_site",
                "run_dir": _rel(run_dir),
                "kind": asset.get("kind"),
                "title": asset.get("alt") or asset.get("kind"),
                "source_url": asset.get("source_url"),
                "image_count": 1,
                "image_paths": [_rel(run_dir / asset["file"])],
                "metadata_path": _rel(run_dir / "assets_manifest.json"),
            }
        )
    return records


def build_records(platform: str, run_dir: Path) -> list[dict]:
    if platform == "rednote":
        return records_from_rednote(run_dir)
    if platform == "instagram":
        return records_from_instagram(run_dir)
    if platform == "brand-site":
        return records_from_brand_assets(run_dir)
    raise ValueError(f"Unsupported platform: {platform}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=["rednote", "instagram", "brand-site"], required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--index", type=Path, default=material_index.DEFAULT_INDEX)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    records = build_records(args.platform, args.run_dir)
    written = []
    if not args.dry_run:
        written = material_index.append_many(args.index, records)
    summary = material_index.summarize(args.index)
    print(
        json.dumps(
            {
                "records": len(records),
                "written": len(written),
                "skipped_existing": 0 if args.dry_run else len(records) - len(written),
                "index": str(args.index),
                "summary": summary,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
