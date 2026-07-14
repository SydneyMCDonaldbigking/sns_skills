#!/usr/bin/env python3
"""Create a searchable catalog for official brand-site assets."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


STOP_WORDS = {
    "cdn",
    "shop",
    "files",
    "image",
    "images",
    "preview",
    "clean",
    "copy",
    "umall",
    "app",
    "web",
    "pc",
    "hero",
    "banner",
    "product",
    "promo",
    "pos",
    "ago",
}

TAG_RULES = [
    ("rice", ["rice", "grain", "pasta", "koshihikari", "hom mali"]),
    ("dumplings", ["dumpling", "gyoza", "wonton"]),
    ("fruit", ["fruit", "durian", "tropical", "mango", "banana"]),
    ("vegetables", ["vegetable", "veggie", "greens"]),
    ("meat", ["meat", "beef", "wagyu", "pork", "chicken", "lamb"]),
    ("seafood", ["seafood", "fish", "prawn", "shrimp", "salmon"]),
    ("instant_food", ["instant", "noodle", "ramen", "hotpot"]),
    ("snacks", ["snack", "confection", "candy", "chips"]),
    ("drink", ["drink", "tea", "milk", "juice", "soda"]),
    ("alcohol", ["alcohol", "liquor", "beer", "wine", "whisky", "soju"]),
    ("delivery", ["delivery", "shipping", "postage"]),
    ("discount", ["sale", "discount", "half price", "flash", "code", "deal"]),
    ("asian_grocery", ["asian", "grocery", "southeast", "yum cha"]),
]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clean_source_name(source_url: str, fallback: str) -> str:
    parsed = urlparse(source_url or "")
    name = Path(unquote(parsed.path)).stem or fallback
    name = re.sub(r"(_|-)?\d{6,}.*$", "", name)
    name = re.sub(r"_[a-f0-9]{8,}.*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"(_|-)?\d+x\d+.*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"(_|-)?\d+x$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"[_-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" -_")
    return name or fallback


def display_title(asset: dict, source_name: str) -> str:
    alt = (asset.get("alt") or "").strip()
    if alt and alt.lower() not in {"product_or_promo", "hero_banner", "banner"}:
        return alt
    words = [word for word in source_name.split() if word.casefold() not in STOP_WORDS]
    title = " ".join(words[:12]).strip()
    return title or asset.get("kind") or "brand asset"


def infer_tags(text: str, kind: str) -> list[str]:
    folded = text.casefold()
    tokens = set(re.findall(r"[a-z0-9]+", folded))
    tags = [kind]
    for tag, needles in TAG_RULES:
        if any((needle in folded if " " in needle else needle in tokens) for needle in needles):
            tags.append(tag)
    return sorted(set(tags))


def infer_use_case(kind: str, tags: list[str], width: int | None, height: int | None) -> str:
    if kind == "hero_banner":
        return "campaign-background"
    if kind == "category":
        return "category-context"
    if kind == "brand":
        return "brand-ui-reference"
    if "discount" in tags:
        return "promotion-reference"
    if width and height and width >= height:
        return "product-scene-reference"
    return "product-pack-reference"


def infer_quality(asset: dict, title: str, source_name: str) -> str:
    kind = asset.get("kind")
    if kind in {"hero_banner", "category", "brand"}:
        return "high"
    if title == kind or title == "brand asset":
        return "needs-review"
    if len(source_name) < 8:
        return "needs-review"
    return "medium"


def enrich_asset(asset: dict) -> dict:
    fallback = Path(asset.get("file", "")).stem or asset.get("kind", "asset")
    source_name = clean_source_name(asset.get("source_url", ""), fallback)
    title = display_title(asset, source_name)
    search_text = " ".join([title, source_name, asset.get("kind", ""), asset.get("source_url", "")])
    tags = infer_tags(search_text, asset.get("kind", "asset"))
    width = asset.get("natural_width")
    height = asset.get("natural_height")
    enriched = {
        **asset,
        "source_name": source_name,
        "title": title,
        "tags": tags,
        "use_case": infer_use_case(asset.get("kind", "asset"), tags, width, height),
        "quality": infer_quality(asset, title, source_name),
    }
    return enriched


def build_catalog(run_dir: Path) -> dict:
    manifest = _load_json(run_dir / "assets_manifest.json")
    assets = [enrich_asset(asset) for asset in manifest.get("assets", []) if asset.get("status") == "downloaded"]
    by_kind: dict[str, int] = {}
    by_quality: dict[str, int] = {}
    by_use_case: dict[str, int] = {}
    for asset in assets:
        by_kind[asset["kind"]] = by_kind.get(asset["kind"], 0) + 1
        by_quality[asset["quality"]] = by_quality.get(asset["quality"], 0) + 1
        by_use_case[asset["use_case"]] = by_use_case.get(asset["use_case"], 0) + 1
    return {
        "source": "umall_official_site",
        "run_dir": str(run_dir),
        "total_assets": len(assets),
        "by_kind": by_kind,
        "by_quality": by_quality,
        "by_use_case": by_use_case,
        "assets": assets,
    }


def write_markdown(path: Path, catalog: dict) -> None:
    lines = [
        "# Umall 官网素材精修目录",
        "",
        f"- total_assets: {catalog['total_assets']}",
        f"- by_kind: {catalog['by_kind']}",
        f"- by_quality: {catalog['by_quality']}",
        f"- by_use_case: {catalog['by_use_case']}",
        "",
        "| # | title | kind | tags | use_case | quality | file |",
        "|---:|---|---|---|---|---|---|",
    ]
    for asset in catalog["assets"]:
        tags = ", ".join(asset.get("tags", []))
        lines.append(
            "| {index} | {title} | {kind} | {tags} | {use_case} | {quality} | `{file}` |".format(
                index=asset.get("index", ""),
                title=str(asset.get("title", "")).replace("|", "/"),
                kind=asset.get("kind", ""),
                tags=tags.replace("|", "/"),
                use_case=asset.get("use_case", ""),
                quality=asset.get("quality", ""),
                file=asset.get("file", ""),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    catalog = build_catalog(args.run_dir)
    output_json = args.output_json or args.run_dir / "brand_asset_catalog.json"
    output_md = args.output_md or args.run_dir / "brand_asset_catalog.md"
    _write_json(output_json, catalog)
    write_markdown(output_md, catalog)
    print(
        json.dumps(
            {
                "assets": catalog["total_assets"],
                "output_json": str(output_json),
                "output_md": str(output_md),
                "by_quality": catalog["by_quality"],
                "by_use_case": catalog["by_use_case"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
