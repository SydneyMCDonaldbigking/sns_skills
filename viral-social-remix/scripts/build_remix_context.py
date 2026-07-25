#!/usr/bin/env python3
"""Build a compact source + product context pack from the material index."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import material_index


def _pick(records: list[dict], limit: int) -> list[dict]:
    def score(record: dict) -> tuple[int, int]:
        quality_score = {"high": 3, "medium": 2, "needs-review": 1}.get(record.get("quality"), 2)
        image_score = min(int(record.get("image_count") or len(record.get("image_paths") or [])), 9)
        return (quality_score, image_score)

    return sorted(records, key=score, reverse=True)[:limit]


def build_context(
    index: Path,
    *,
    source_platform: str,
    source_query: str,
    product_query: str,
    source_limit: int,
    product_limit: int,
) -> dict:
    source_posts = material_index.search(
        index,
        query=source_query,
        platform=source_platform,
        record_type="post",
        limit=source_limit,
    )
    product_assets = material_index.search(
        index,
        query=product_query,
        platform="brand_site",
        record_type="asset",
    )
    return {
        "index": str(index),
        "source_platform": source_platform,
        "source_query": source_query,
        "product_query": product_query,
        "source_posts": source_posts[:source_limit],
        "product_assets": _pick(product_assets, product_limit),
    }


def _first_image(record: dict) -> str:
    image_paths = record.get("image_paths") or []
    return image_paths[0] if image_paths else ""


def format_markdown(context: dict) -> str:
    lines = [
        "# 复刻上下文包",
        "",
        f"- source_platform: `{context['source_platform']}`",
        f"- source_query: `{context['source_query']}`",
        f"- product_query: `{context['product_query']}`",
        f"- source_posts: {len(context['source_posts'])}",
        f"- product_assets: {len(context['product_assets'])}",
        "",
        "## 源爆款候选",
        "",
    ]
    for index, post in enumerate(context["source_posts"], start=1):
        lines.extend(
            [
                f"### {index}. {post.get('title') or post.get('record_id')}",
                "",
                f"- source: {post.get('source_url', '')}",
                f"- content: `{post.get('content_path', '')}`",
            ]
        )
        if post.get("caption_path"):
            lines.append(f"- caption: `{post['caption_path']}`")
        if _first_image(post):
            lines.append(f"- first_image: `{_first_image(post)}`")
        if post.get("image_count"):
            lines.append(f"- image_count: {post['image_count']}")
        lines.append("")
    lines.extend(["## 官网商品/场景参考", ""])
    for index, asset in enumerate(context["product_assets"], start=1):
        lines.extend(
            [
                f"### {index}. {asset.get('title') or asset.get('record_id')}",
                "",
                f"- tags: {', '.join(asset.get('tags') or [])}",
                f"- use_case: `{asset.get('use_case', '')}`",
                f"- quality: `{asset.get('quality', '')}`",
                f"- image: `{_first_image(asset)}`",
                f"- source: {asset.get('source_url', '')}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, default=material_index.DEFAULT_INDEX)
    parser.add_argument("--source-platform", choices=["rednote", "instagram_facebook"], required=True)
    parser.add_argument("--source-query", required=True)
    parser.add_argument("--product-query", required=True)
    parser.add_argument("--source-limit", type=int, default=3)
    parser.add_argument("--product-limit", type=int, default=6)
    parser.add_argument("--format", choices=["md", "json"], default="md")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    context = build_context(
        args.index,
        source_platform=args.source_platform,
        source_query=args.source_query,
        product_query=args.product_query,
        source_limit=args.source_limit,
        product_limit=args.product_limit,
    )
    output = json.dumps(context, ensure_ascii=False, indent=2) if args.format == "json" else format_markdown(context)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
