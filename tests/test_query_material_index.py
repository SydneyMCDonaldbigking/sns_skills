import json
import subprocess
import sys
from pathlib import Path

from viral_social_test_loader import load_script


material_index = load_script("material_index")

ROOT = Path(__file__).parents[1]
QUERY_SCRIPT = ROOT / "viral-social-remix" / "scripts" / "query_material_index.py"


def seed_index(path: Path):
    material_index.append_many(
        path,
        [
            {
                "record_id": "rednote-001",
                "record_type": "post",
                "platform": "rednote",
                "title": "百万补贴晒单🎁",
                "reasons": ["title"],
                "image_paths": ["output/rednote/post-001/images/01.jpg"],
            },
            {
                "record_id": "brand-001",
                "record_type": "asset",
                "platform": "brand_site",
                "kind": "product_or_promo",
                "title": "东北大米官方商品图",
                "image_paths": ["output/brand/assets/rice.jpg"],
            },
            {
                "record_id": "ig-001",
                "record_type": "post",
                "platform": "instagram_facebook",
                "label": "pantry essentials",
                "title": "restock carousel",
                "caption_path": "output/ig/post-001/caption.txt",
            },
        ],
    )


def run_query(*args):
    return subprocess.run(
        [sys.executable, str(QUERY_SCRIPT), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_material_index_search_filters_by_query_platform_type_and_kind(tmp_path):
    index = tmp_path / "material-index.jsonl"
    seed_index(index)

    assert [row["record_id"] for row in material_index.search(index, query="补贴")] == ["rednote-001"]
    assert [row["record_id"] for row in material_index.search(index, platform="brand_site")] == ["brand-001"]
    assert [row["record_id"] for row in material_index.search(index, record_type="post")] == [
        "rednote-001",
        "ig-001",
    ]
    assert [row["record_id"] for row in material_index.search(index, kind="product_or_promo")] == ["brand-001"]


def test_query_material_index_cli_outputs_markdown_and_json(tmp_path):
    index = tmp_path / "material-index.jsonl"
    seed_index(index)

    markdown = run_query(
        "大米",
        "--index",
        index,
        "--platform",
        "brand_site",
        "--format",
        "md",
    )
    assert markdown.returncode == 0, markdown.stderr
    assert "# 本地素材索引检索结果" in markdown.stdout
    assert "东北大米官方商品图" in markdown.stdout

    emoji = run_query("补贴", "--index", index, "--format", "md")
    assert emoji.returncode == 0, emoji.stderr
    assert "百万补贴晒单🎁" in emoji.stdout

    json_result = run_query("pantry", "--index", index, "--format", "json")
    assert json_result.returncode == 0, json_result.stderr
    assert json.loads(json_result.stdout)[0]["record_id"] == "ig-001"
