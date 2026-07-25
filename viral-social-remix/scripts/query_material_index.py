#!/usr/bin/env python3
"""Search the local social/brand material index."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import material_index


def _first_image(record: dict) -> str:
    image_paths = record.get("image_paths") or []
    return image_paths[0] if image_paths else ""


def _format_markdown(records: list[dict], *, index: Path, query: str | None) -> str:
    lines = [
        "# 本地素材索引检索结果",
        "",
        f"- index: `{index}`",
        f"- query: `{query or ''}`",
        f"- results: {len(records)}",
        "",
    ]
    for number, record in enumerate(records, start=1):
        title = record.get("title") or record.get("record_id") or f"record {number}"
        lines.extend(
            [
                f"## {number}. {title}",
                "",
                f"- platform: `{record.get('platform', '')}`",
                f"- type: `{record.get('record_type', '')}`",
            ]
        )
        if record.get("kind"):
            lines.append(f"- kind: `{record['kind']}`")
        if record.get("label"):
            lines.append(f"- label: {record['label']}")
        if record.get("source_name"):
            lines.append(f"- source_name: {record['source_name']}")
        if record.get("tags"):
            lines.append(f"- tags: {', '.join(record['tags'])}")
        if record.get("use_case"):
            lines.append(f"- use_case: `{record['use_case']}`")
        if record.get("quality"):
            lines.append(f"- quality: `{record['quality']}`")
        if record.get("source_url"):
            lines.append(f"- source: {record['source_url']}")
        if record.get("content_path"):
            lines.append(f"- content: `{record['content_path']}`")
        if record.get("caption_path"):
            lines.append(f"- caption: `{record['caption_path']}`")
        if record.get("metadata_path"):
            lines.append(f"- metadata: `{record['metadata_path']}`")
        if _first_image(record):
            lines.append(f"- first_image: `{_first_image(record)}`")
        if record.get("image_count"):
            lines.append(f"- image_count: {record['image_count']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="?", help="Space-separated keywords to match.")
    parser.add_argument("--index", type=Path, default=material_index.DEFAULT_INDEX)
    parser.add_argument("--platform", choices=["rednote", "instagram_facebook", "brand_site"])
    parser.add_argument("--type", dest="record_type", choices=["post", "asset"])
    parser.add_argument("--kind")
    parser.add_argument("--quality", choices=["high", "medium", "needs-review"])
    parser.add_argument("--use-case")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--format", choices=["json", "md"], default="md")
    args = parser.parse_args()

    records = material_index.search(
        args.index,
        query=args.query,
        platform=args.platform,
        record_type=args.record_type,
        kind=args.kind,
        quality=args.quality,
        use_case=args.use_case,
        limit=args.limit,
    )
    if args.format == "json":
        print(json.dumps(records, ensure_ascii=False, indent=2))
    else:
        print(_format_markdown(records, index=args.index, query=args.query))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
