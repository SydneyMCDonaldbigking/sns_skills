import json
import subprocess
import sys
from pathlib import Path

from viral_social_test_loader import load_script


enrich_brand_assets = load_script("enrich_brand_assets")

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "viral-social-remix" / "scripts" / "enrich_brand_assets.py"


def make_run_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / "brand-run"
    run_dir.mkdir()
    (run_dir / "assets_manifest.json").write_text(
        json.dumps(
            {
                "assets": [
                    {
                        "index": 1,
                        "kind": "category",
                        "file": "assets/001-category-Pasta-&-Rice.png",
                        "source_url": "https://cdn.shopify.com/files/rice-category.png?v=1",
                        "alt": "Pasta & Rice",
                        "natural_width": 360,
                        "natural_height": 240,
                        "status": "downloaded",
                    },
                    {
                        "index": 2,
                        "kind": "product_or_promo",
                        "file": "assets/002-product_or_promo-product_or_promo.jpg",
                        "source_url": (
                            "https://www.umall.com.au/cdn/shop/files/"
                            "umall-half-price-premium-wagyu-ms9-beef-slice-rolls-600g-hotpot_540x.jpg?v=1"
                        ),
                        "alt": "",
                        "natural_width": 540,
                        "natural_height": 540,
                        "status": "downloaded",
                    },
                    {
                        "index": 3,
                        "kind": "hero_banner",
                        "file": "assets/003-hero_banner-Durian-Season.png",
                        "source_url": "https://cdn.shopify.com/files/durian-season-1440x800.png",
                        "alt": "Durian Season",
                        "natural_width": 1080,
                        "natural_height": 600,
                        "status": "downloaded",
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return run_dir


def test_enrich_brand_asset_derives_title_tags_and_use_case():
    asset = {
        "kind": "product_or_promo",
        "file": "assets/001-product_or_promo-product_or_promo.jpg",
        "source_url": "https://www.umall.com.au/cdn/shop/files/umall-half-price-wagyu-beef-rolls_540x.jpg?v=1",
        "alt": "",
        "natural_width": 540,
        "natural_height": 540,
        "status": "downloaded",
    }

    enriched = enrich_brand_assets.enrich_asset(asset)

    assert "wagyu" in enriched["title"].casefold()
    assert "meat" in enriched["tags"]
    assert "discount" in enriched["tags"]
    assert enriched["use_case"] == "promotion-reference"
    assert enriched["quality"] == "medium"


def test_enrich_brand_asset_does_not_tag_price_as_rice():
    asset = {
        "kind": "product_or_promo",
        "file": "assets/001-product_or_promo-product_or_promo.jpg",
        "source_url": "https://www.umall.com.au/cdn/shop/files/umall-half-price-wagyu-beef-rolls_540x.jpg?v=1",
        "alt": "",
        "natural_width": 540,
        "natural_height": 540,
        "status": "downloaded",
    }

    enriched = enrich_brand_assets.enrich_asset(asset)

    assert "discount" in enriched["tags"]
    assert "rice" not in enriched["tags"]


def test_enrich_brand_assets_cli_writes_catalog_json_and_markdown(tmp_path):
    run_dir = make_run_dir(tmp_path)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--run-dir", str(run_dir)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["assets"] == 3
    catalog = json.loads((run_dir / "brand_asset_catalog.json").read_text(encoding="utf-8"))
    assert catalog["by_kind"] == {"category": 1, "product_or_promo": 1, "hero_banner": 1}
    assert catalog["assets"][1]["title"] == "half price premium wagyu ms9 beef slice rolls 600g hotpot"
    assert "meat" in catalog["assets"][1]["tags"]
    assert (run_dir / "brand_asset_catalog.md").read_text(encoding="utf-8").startswith(
        "# Umall 官网素材精修目录"
    )
