import json
import subprocess
import sys
from pathlib import Path

from viral_social_test_loader import load_script


ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "viral-social-remix" / "scripts"
SCRIPT = SCRIPTS / "prepare_remix_run.py"
sys.path.insert(0, str(SCRIPTS))

material_index = load_script("material_index")
prepare_remix_run = load_script("prepare_remix_run")


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


def test_prepare_remix_run_creates_standard_analysis_files(tmp_path):
    index = tmp_path / "material-index.jsonl"
    output_root = tmp_path / "output"
    seed_index(index)

    summary = prepare_remix_run.prepare_run(
        output_root=output_root,
        task_name="rednote rice",
        index=index,
        source_platform="rednote",
        source_query="补贴",
        product_query="大米 rice",
    )

    run_dir = Path(summary["run_dir"])
    assert run_dir.exists()
    assert summary["asset_count"] == 4
    assert (run_dir / "source").is_dir()
    assert (run_dir / "analysis" / "remix-context.md").read_text(encoding="utf-8").startswith("# 复刻上下文包")
    selected = json.loads((run_dir / "analysis" / "selected-assets.json").read_text(encoding="utf-8"))
    assert selected["source_images_by_asset"]["01"] == "output/rednote/post/images/01.webp"
    assert selected["product_images"] == ["output/brand/assets/rice.jpg"]
    prompts = (run_dir / "analysis" / "prompts.md").read_text(encoding="utf-8")
    assert "Source image: `output/rednote/post/images/01.webp`" in prompts
    assert "product_refs: `output/brand/assets/rice.jpg`" in prompts
    assert "标题：TODO" in (run_dir / "analysis" / "caption-zh.txt").read_text(encoding="utf-8")
    assert (run_dir / "generated").is_dir()
    manifest = json.loads((run_dir / "analysis" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["platform"] == "rednote"
    assert manifest["output_size"] == "1152x1536"
    assert list(manifest["assets"]) == ["01", "02", "03", "04"]


def test_prepare_remix_run_cli_allows_explicit_asset_count(tmp_path):
    index = tmp_path / "material-index.jsonl"
    output_root = tmp_path / "output"
    seed_index(index)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--output-root",
            str(output_root),
            "--task-name",
            "ig wagyu",
            "--index",
            str(index),
            "--source-platform",
            "rednote",
            "--source-query",
            "补贴",
            "--product-query",
            "rice",
            "--asset-count",
            "2",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["asset_count"] == 2
    run_dir = Path(payload["run_dir"])
    manifest = json.loads((run_dir / "analysis" / "manifest.json").read_text(encoding="utf-8"))
    assert list(manifest["assets"]) == ["01", "02"]
