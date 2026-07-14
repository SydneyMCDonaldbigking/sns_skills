import json
import subprocess
import sys
from pathlib import Path

from viral_social_test_loader import load_script


ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "viral-social-remix" / "scripts"
VALIDATE_SCRIPT = SCRIPTS / "validate_prepared_run.py"
sys.path.insert(0, str(SCRIPTS))

material_index = load_script("material_index")
prepare_remix_run = load_script("prepare_remix_run")
validate_prepared_run = load_script("validate_prepared_run")


def seed_index(path: Path):
    material_index.append_many(
        path,
        [
            {
                "record_id": "ig-001",
                "record_type": "post",
                "platform": "instagram_facebook",
                "title": "pantry carousel",
                "source_url": "https://www.instagram.com/p/demo",
                "content_path": "output/ig/post/content.md",
                "caption_path": "output/ig/post/caption.txt",
                "image_count": 2,
                "image_paths": ["output/ig/post/images/01.jpg", "output/ig/post/images/02.jpg"],
            },
            {
                "record_id": "brand-wagyu",
                "record_type": "asset",
                "platform": "brand_site",
                "kind": "product_or_promo",
                "title": "wagyu beef official product image",
                "tags": ["wagyu", "meat"],
                "quality": "medium",
                "use_case": "product-pack-reference",
                "source_url": "https://www.umall.com.au/wagyu.jpg",
                "image_count": 1,
                "image_paths": ["output/brand/assets/wagyu.jpg"],
            },
        ],
    )


def make_run(tmp_path: Path) -> Path:
    index = tmp_path / "material-index.jsonl"
    seed_index(index)
    summary = prepare_remix_run.prepare_run(
        output_root=tmp_path / "output",
        task_name="ig pantry wagyu",
        index=index,
        source_platform="instagram_facebook",
        source_query="pantry",
        product_query="wagyu",
    )
    return Path(summary["run_dir"])


def test_validate_prepared_run_accepts_complete_run(tmp_path):
    run_dir = make_run(tmp_path)

    result = validate_prepared_run.validate(run_dir)

    assert result == {
        "valid": True,
        "run_dir": str(run_dir),
        "asset_count": 2,
        "errors": [],
    }


def test_validate_prepared_run_rejects_missing_prompt_section(tmp_path):
    run_dir = make_run(tmp_path)
    prompts_path = run_dir / "analysis" / "prompts.md"
    prompts_path.write_text(prompts_path.read_text(encoding="utf-8").replace("## 02", "## XX"), encoding="utf-8")

    result = validate_prepared_run.validate(run_dir)

    assert result["valid"] is False
    assert "prompts missing section for: 02" in result["errors"]


def test_validate_prepared_run_cli_returns_nonzero_on_invalid_run(tmp_path):
    run_dir = make_run(tmp_path)
    (run_dir / "analysis" / "selected-assets.json").write_text(
        json.dumps({"source_images_by_asset": {}, "product_images": []}, ensure_ascii=False),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), str(run_dir)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert "selected-assets has no product_images" in payload["errors"]
