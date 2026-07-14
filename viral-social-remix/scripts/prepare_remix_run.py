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

ROLE_TEMPLATES = {
    "rednote": [
        ("hook", "封面钩子：明确省钱/补贴/囤货利益点，像真实用户分享。"),
        ("proof", "福利证据：突出补贴、包邮、价格或官方来源。"),
        ("haul", "囤货场景：展示适合家庭/留学生/上班族的采购组合。"),
        ("cta", "行动收口：提醒去 Umall 搜索、下单或收藏。"),
    ],
    "instagram_facebook": [
        ("hook", "Cover hook: concise pantry/restock reason with clean editorial composition."),
        ("item", "Product focus: one useful item or category, practical everyday use case."),
        ("proof", "Why it works: convenience, freshness, price, delivery, or trusted grocery angle."),
        ("cta", "Soft CTA: save the list, restock from Umall, or try the highlighted item."),
    ],
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


def _product_titles(context: dict, limit: int = 5) -> list[str]:
    return [
        asset.get("title")
        for asset in context.get("product_assets", [])[:limit]
        if asset.get("title")
    ]


def _role_for(platform: str, index: int) -> tuple[str, str]:
    roles = ROLE_TEMPLATES[platform]
    if index < len(roles):
        return roles[index]
    return (
        "detail" if platform == "rednote" else "supporting item",
        "补充细节：延续源帖节奏，保持一个页面一个清晰信息点。"
        if platform == "rednote"
        else "Supporting detail: keep one clear point per page and maintain the source carousel rhythm.",
    )


def _role_lines(platform: str, asset_ids: list[str]) -> list[str]:
    lines = []
    for index, asset_id in enumerate(asset_ids):
        role, description = _role_for(platform, index)
        lines.append(f"- {asset_id} `{role}`: {description}")
    return lines


def _breakdown_template(context: dict, platform_config: dict, asset_ids: list[str]) -> str:
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
            *_role_lines(context["source_platform"], asset_ids),
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
    product_titles = _product_titles(context)
    product_label = product_titles[0] if product_titles else context["product_query"]
    if platform_config["language"] == "zh":
        hook = f"Umall 补贴囤货清单：{product_label}也能轻松补齐"
        body = (
            "适合想省时间又想买得靠谱的人。参考官方商品图做主视觉，保留真实囤货/补贴分享的节奏，"
            "重点讲清楚：买什么、为什么现在买、怎么更省。"
        )
        cta = "收藏这份清单，下次打开 Umall 直接照着搜。"
    else:
        hook = f"Restock idea: {product_label} from Umall"
        body = (
            "A practical grocery carousel built around one clear pantry need, official product references, "
            "and a soft everyday-use angle."
        )
        cta = "Save this before your next Umall restock."
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
            hook,
            "",
            "## Body",
            "",
            body,
            "",
            "## CTA",
            "",
            cta,
            "",
        ]
    )


def _prompt_for(platform: str, platform_config: dict, role: str, role_description: str, product_titles: list[str]) -> str:
    product_text = ", ".join(product_titles[:3]) or "Umall official grocery product references"
    if platform == "rednote":
        return (
            f"生成一张 {platform_config['size']} 小红书竖版图。页面角色：{role}。{role_description} "
            f"参考源图的构图、层级和节奏，但替换为 Umall 场景与官方商品参考：{product_text}。"
            "画面要像真实澳洲华人/留学生囤货分享，中文标题自然、短、有生活感。"
            "商品包装文字必须准确；如果不确定，把包装放远、缩小或轻微背景虚化，不要生成假中文。"
            "不要复制源帖水印、真实人物身份或未经授权 logo。"
        )
    return (
        f"Create one {platform_config['size']} Instagram/Facebook carousel image. Page role: {role}. "
        f"{role_description} Use the source image composition as structural reference and replace the product with "
        f"Umall official grocery references: {product_text}. Keep a clean editorial grocery style, natural English text, "
        "accurate product packaging, and a soft restock/pantry angle. If package text is uncertain, make it small, distant, "
        "or softly blurred instead of inventing fake text. Do not copy source watermarks or unauthorized logos."
    )


def _prompts_template(asset_ids: list[str], platform_config: dict, context: dict) -> str:
    product_images = _product_images(context)
    product_titles = _product_titles(context)
    platform = context["source_platform"]
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
        role, role_description = _role_for(platform, index)
        lines.extend(
            [
                f"## {asset_id}",
                "",
                f"Source image: `{source_image}`",
                "",
                f"Source role: `{role}`",
                "",
                "Prompt:",
                "",
                _prompt_for(platform, platform_config, role, role_description, product_titles),
                "",
            ]
        )
    return "\n".join(lines)


def _caption_template(platform: str, context: dict) -> str:
    product_titles = _product_titles(context)
    product_label = product_titles[0] if product_titles else context["product_query"]
    source_title = _first_source(context).get("title") or context["source_query"]
    if platform == "rednote":
        return "\n".join(
            [
                f"标题：Umall补贴囤货｜{product_label}也能这样买",
                "",
                "正文：",
                f"刷到这个{source_title}思路，感觉很适合拿来做一版真实囤货清单。",
                f"这次主角先放在 {product_label}，优先参考 Umall 官网商品图，避免包装文字乱飞。",
                "适合：想省时间、想看清楚买什么、想趁补贴/活动顺手补货的人。",
                "图片会按源帖节奏做，但商品和场景会换成 Umall 自己的。",
                "",
                "#Umall #澳洲生活 #囤货 #省钱 #澳洲华人超市",
                "",
            ]
        )
    return "\n".join(
        [
            f"Hook: A practical Umall restock idea: {product_label}",
            "",
            "Body:",
            f"Built from a proven {context['source_query']} carousel structure, with official Umall product references.",
            "The goal is simple: clear grocery value, useful pantry context, and product visuals that feel real instead of AI-random.",
            "",
            "CTA: Save this for your next Umall grocery run.",
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
    _write(run_dir / "analysis" / "breakdown.md", _breakdown_template(context, platform_config, asset_ids))
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
