import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "viral-social-remix" / "scripts" / "collect_source_assets.py"


def run_collector(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_collect_brand_site_assets_dry_run_does_not_write_index(tmp_path):
    run_dir = tmp_path / "brand-run"
    run_dir.mkdir()
    (run_dir / "assets_manifest.json").write_text(
        json.dumps(
            {
                "assets": [
                    {
                        "status": "downloaded",
                        "kind": "product_or_promo",
                        "alt": "真实商品图",
                        "source_url": "https://www.umall.com.au/item-a.jpg",
                        "file": "assets/item-a.jpg",
                    },
                    {
                        "status": "failed",
                        "kind": "product_or_promo",
                        "file": "assets/missing.jpg",
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    index = tmp_path / "material-index.jsonl"

    result = run_collector(
        "--platform",
        "brand-site",
        "--run-dir",
        run_dir,
        "--index",
        index,
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["records"] == 1
    assert payload["written"] == 0
    assert payload["skipped_existing"] == 0
    assert not index.exists()


def test_collect_rednote_post_assets_writes_post_record(tmp_path):
    run_dir = tmp_path / "rednote-run"
    post_dir = run_dir / "posts" / "post-001-subsidy"
    post_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "posts": [
                    {
                        "folder": "posts/post-001-subsidy",
                        "title": "百万补贴合集",
                        "source_url": "https://www.rednote.com/explore/demo",
                        "date": "2026-07-14",
                        "image_count": 2,
                        "reasons": ["title"],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (post_dir / "metadata.json").write_text(
        json.dumps(
            {
                "images": [
                    {"status": "downloaded", "file": "images/01.jpg"},
                    {"status": "failed", "file": "images/02.jpg"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    index = tmp_path / "material-index.jsonl"

    result = run_collector("--platform", "rednote", "--run-dir", run_dir, "--index", index)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["records"] == 1
    assert payload["written"] == 1
    row = json.loads(index.read_text(encoding="utf-8").splitlines()[0])
    assert row["platform"] == "rednote"
    assert row["record_id"] == "rednote::https://www.rednote.com/explore/demo::posts/post-001-subsidy"
    assert row["title"] == "百万补贴合集"
    assert row["image_paths"] == [str(post_dir / "images/01.jpg").replace("\\", "/")]
