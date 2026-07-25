import json
import subprocess
import sys
from pathlib import Path

from viral_social_test_loader import load_script


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "viral-social-remix" / "scripts" / "build_remix_context.py"
SCRIPTS = ROOT / "viral-social-remix" / "scripts"
sys.path.insert(0, str(SCRIPTS))

material_index = load_script("material_index")
build_remix_context = load_script("build_remix_context")


def seed_index(path: Path):
    material_index.append_many(
        path,
        [
            {
                "record_id": "rednote-001",
                "record_type": "post",
                "platform": "rednote",
                "title": "百万补贴囤货",
                "source_url": "https://www.rednote.com/explore/demo",
                "content_path": "output/rednote/post/content.md",
                "image_count": 4,
                "image_paths": ["output/rednote/post/images/01.webp"],
            },
            {
                "record_id": "brand-rice",
                "record_type": "asset",
                "platform": "brand_site",
                "kind": "product_or_promo",
                "title": "东北大米官方商品图",
                "tags": ["rice", "product_or_promo"],
                "quality": "medium",
                "use_case": "product-pack-reference",
                "source_url": "https://www.umall.com.au/rice.jpg",
                "image_count": 1,
                "image_paths": ["output/brand/assets/rice.jpg"],
            },
        ],
    )


def test_build_remix_context_pairs_source_posts_with_product_assets(tmp_path):
    index = tmp_path / "material-index.jsonl"
    seed_index(index)

    context = build_remix_context.build_context(
        index,
        source_platform="rednote",
        source_query="补贴",
        product_query="大米 rice",
        source_limit=2,
        product_limit=3,
    )

    assert context["source_posts"][0]["record_id"] == "rednote-001"
    assert context["product_assets"][0]["record_id"] == "brand-rice"
    markdown = build_remix_context.format_markdown(context)
    assert "# 复刻上下文包" in markdown
    assert "东北大米官方商品图" in markdown


def test_build_remix_context_cli_writes_markdown(tmp_path):
    index = tmp_path / "material-index.jsonl"
    output = tmp_path / "context.md"
    seed_index(index)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--index",
            str(index),
            "--source-platform",
            "rednote",
            "--source-query",
            "补贴",
            "--product-query",
            "大米 rice",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert output.read_text(encoding="utf-8").startswith("# 复刻上下文包")
