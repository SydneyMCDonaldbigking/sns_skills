#!/usr/bin/env python3
"""Prepare a timestamped remix run from the local material index."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import build_remix_context
import create_run_dir
import manifest


PLATFORM_DEFAULTS = {
    "rednote": {
        "task_slug": "rednote-remix",
        "caption_file": "caption-zh.txt",
        "language": "zh",
        "size": "1152x1536",
    },
    "instagram_facebook": {
        "task_slug": "ig-fb-remix",
        "caption_file": "caption-en.txt",
        "language": "en",
        "size": "1152x1152",
    },
}


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _asset_count(context: dict, explicit_count: int | None) -> int:
    if explicit_count:
        return explicit_count
    if context.get("source_posts"):
        count = context["source_posts"][0].get("image_count")
        if count:
            return max(1, int(count))
    return 1


def _asset_ids(count: int) -> list[str]:
    return [f"{index:02d}" for index in range(1, count + 1)]


def _first_source(context: dict) -> dict:
    return context["source_posts"][0] if context.get("source_posts") else {}


def _source_image_for(context: dict, index: int) -> str:
    image_paths = _first_source(context).get("image_paths") or []
    if not image_paths:
        return ""
    return image_paths[min(index, len(image_paths) - 1)]


def _product_images(context: dict, limit: int = 3) -> list[str]:
    images = []
    for asset in context.get("product_assets", []):
        image_paths = asset.get("image_paths") or []
        if image_paths:
            images.append(image_paths[0])
        if len(images) >= limit:
            break
    return images


def _breakdown_template(context: dict, platform_config: dict) -> str:
    source_title = _first_source(context).get("title", "")
    product_titles = [asset.get("title") for asset in context.get("product_assets", []) if asset.get("title")]
    return "\n".join(
        [
            "# Breakdown",
            "",
            f"- source_platform: `{context['source_platform']}`",
            f"- source_query: `{context['source_query']}`",
            f"- product_query: `{context['product_query']}`",
            f"- output_size: `{platform_config['size']}`",
            f"- language: `{platform_config['language']}`",
            f"- primary_source: {source_title}",
            f"- product_refs: {', '.join(product_titles[:5])}",
            "",
            "## Page roles",
            "",
            "Fill one role per generated page after inspecting the selected source post.",
            "",
            "## Visual rules",
            "",
            "- Preserve the source composition rhythm, not unauthorized logos or watermarks.",
            "- Prefer official product references from `remix-context.md`.",
            "- If packaging text is uncertain, keep it small, blurred, or backgrounded.",
            "",
        ]
    )


def _copy_template(context: dict, platform_config: dict) -> str:
    return "\n".join(
        [
            "# Copy",
            "",
            f"- language: `{platform_config['language']}`",
            f"- source_query: `{context['source_query']}`",
            f"- product_query: `{context['product_query']}`",
            "",
            "## Hook",
            "",
            "TODO",
            "",
            "## Body",
            "",
            "TODO",
            "",
            "## CTA",
            "",
            "TODO",
            "",
        ]
    )


def _prompts_template(asset_ids: list[str], platform_config: dict, context: dict) -> str:
    product_images = _product_images(context)
    lines = [
        "# Prompts",
        "",
        f"- output_size: `{platform_config['size']}`",
        f"- language: `{platform_config['language']}`",
        f"- product_refs: {', '.join(f'`{path}`' for path in product_images) or 'none'}",
        "",
    ]
    for index, asset_id in enumerate(asset_ids):
        source_image = _source_image_for(context, index)
        lines.extend(
            [
                f"## {asset_id}",
                "",
                f"Source image: `{source_image}`",
                "",
                "Source role: TODO",
                "",
                "Prompt:",
                "",
                (
                    f"Create one {platform_config['size']} social carousel image. "
                    "Use the source image composition as structural reference, replace the product with Umall brand/product references, "
                    "keep packaging text accurate or visually small/blurred if uncertain, and keep the language natural for the target platform."
                ),
                "",
            ]
        )
    return "\n".join(lines)


def _caption_template(platform: str, context: dict) -> str:
    if platform == "rednote":
        return "\n".join(
            [
                "标题：TODO",
                "",
                "正文：",
                "TODO",
                "",
                "#Umall #澳洲生活 #囤货 #省钱",
                "",
            ]
        )
    return "\n".join(
        [
            "Hook: TODO",
            "",
            "Body:",
            "TODO",
            "",
            "CTA: TODO",
            "",
            "#asian groceries #pantry staples #umall",
            "",
        ]
    )


def _selected_assets(context: dict, asset_ids: list[str]) -> dict:
    source = _first_source(context)
    source_images = source.get("image_paths") or []
    product_assets = context.get("product_assets", [])
    return {
        "primary_source": source,
        "source_images_by_asset": {
            asset_id: _source_image_for(context, index)
            for index, asset_id in enumerate(asset_ids)
        },
        "product_assets": product_assets,
        "product_images": _product_images(context, limit=10),
        "notes": [
            "Use source images for composition only.",
            "Use official product images for product fidelity.",
            "Avoid copying watermarks, unauthorized logos, or real-person identity.",
        ],
    }


def _selection_markdown(selection: dict) -> str:
    source = selection.get("primary_source") or {}
    lines = [
        "# Selected Assets",
        "",
        "## Primary source",
        "",
        f"- title: {source.get('title', '')}",
        f"- url: {source.get('source_url', '')}",
        f"- content: `{source.get('content_path', '')}`",
        "",
        "## Source image mapping",
        "",
    ]
    for asset_id, image_path in selection.get("source_images_by_asset", {}).items():
        lines.append(f"- {asset_id}: `{image_path}`")
    lines.extend(["", "## Product references", ""])
    for asset in selection.get("product_assets", []):
        image_paths = asset.get("image_paths") or []
        lines.extend(
            [
                f"- {asset.get('title', asset.get('record_id', 'asset'))}",
                f"  - tags: {', '.join(asset.get('tags') or [])}",
                f"  - use_case: `{asset.get('use_case', '')}`",
                f"  - quality: `{asset.get('quality', '')}`",
                f"  - image: `{image_paths[0] if image_paths else ''}`",
            ]
        )
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in selection.get("notes", []))
    return "\n".join(lines) + "\n"


def prepare_run(
    *,
    output_root: Path,
    task_name: str,
    index: Path,
    source_platform: str,
    source_query: str,
    product_query: str,
    source_limit: int = 3,
    product_limit: int = 6,
    asset_count: int | None = None,
) -> dict:
    platform_config = PLATFORM_DEFAULTS[source_platform]
    run_dir = create_run_dir.create(output_root, task_name or platform_config["task_slug"])
    for folder in [
        "source",
        "analysis",
        "references/keyframes",
        "generated",
        "overview",
        "qa",
    ]:
        (run_dir / folder).mkdir(parents=True, exist_ok=True)

    context = build_remix_context.build_context(
        index,
        source_platform=source_platform,
        source_query=source_query,
        product_query=product_query,
        source_limit=source_limit,
        product_limit=product_limit,
    )
    count = _asset_count(context, asset_count)
    asset_ids = _asset_ids(count)

    _write(run_dir / "analysis" / "remix-context.md", build_remix_context.format_markdown(context))
    _write(run_dir / "analysis" / "breakdown.md", _breakdown_template(context, platform_config))
    _write(run_dir / "analysis" / "copy.md", _copy_template(context, platform_config))
    selection = _selected_assets(context, asset_ids)
    _write(run_dir / "analysis" / "selected-assets.json", json.dumps(selection, ensure_ascii=False, indent=2))
    _write(run_dir / "analysis" / "selected-assets.md", _selection_markdown(selection))
    _write(run_dir / "analysis" / "prompts.md", _prompts_template(asset_ids, platform_config, context))
    _write(run_dir / "analysis" / platform_config["caption_file"], _caption_template(source_platform, context))
    if platform_config["caption_file"] != "caption-zh.txt":
        _write(run_dir / "analysis" / "caption-zh.txt", "")
    if platform_config["caption_file"] != "caption-en.txt":
        _write(run_dir / "analysis" / "caption-en.txt", "")

    manifest_data = manifest.create(run_dir / "analysis" / "manifest.json", source_platform, asset_ids)
    manifest_data.update(
        {
            "source_query": source_query,
            "product_query": product_query,
            "output_size": platform_config["size"],
            "language": platform_config["language"],
            "context_path": "analysis/remix-context.md",
        }
    )
    (run_dir / "analysis" / "manifest.json").write_text(
        json.dumps(manifest_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "run_dir": str(run_dir),
        "platform": source_platform,
        "asset_count": count,
        "source_posts": len(context["source_posts"]),
        "product_assets": len(context["product_assets"]),
        "analysis_files": [
            "analysis/remix-context.md",
            "analysis/selected-assets.json",
            "analysis/selected-assets.md",
            "analysis/breakdown.md",
            "analysis/copy.md",
            "analysis/prompts.md",
            f"analysis/{platform_config['caption_file']}",
            "analysis/manifest.json",
        ],
    }
    _write(run_dir / "run-summary.json", json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=Path("output"))
    parser.add_argument("--task-name", default="")
    parser.add_argument("--index", type=Path, default=Path("data/material-index.jsonl"))
    parser.add_argument("--source-platform", choices=sorted(PLATFORM_DEFAULTS), required=True)
    parser.add_argument("--source-query", required=True)
    parser.add_argument("--product-query", required=True)
    parser.add_argument("--source-limit", type=int, default=3)
    parser.add_argument("--product-limit", type=int, default=6)
    parser.add_argument("--asset-count", type=int)
    args = parser.parse_args()

    summary = prepare_run(
        output_root=args.output_root,
        task_name=args.task_name,
        index=args.index,
        source_platform=args.source_platform,
        source_query=args.source_query,
        product_query=args.product_query,
        source_limit=args.source_limit,
        product_limit=args.product_limit,
        asset_count=args.asset_count,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
