import json
from pathlib import Path

from PIL import Image

from viral_social_test_loader import load_script


scanner = load_script("scan_media")
manifest = load_script("manifest")
run_dirs = load_script("create_run_dir")
validation = load_script("validate_output")


def _write_delivery_files(delivery: Path, platform: str):
    analysis = delivery / "analysis"
    analysis.mkdir(parents=True)
    caption = "caption-zh.txt" if platform == "xiaohongshu" else "caption-en.txt"
    for name in ["breakdown.md", "copy.md", caption, "prompts.md"]:
        (analysis / name).write_text("fixture", encoding="utf-8")
    (delivery / "overview").mkdir()
    Image.new("RGB", (1536, 384), "white").save(
        delivery / "overview" / "contact-sheet.png"
    )
    (delivery / "qa").mkdir()
    (delivery / "qa" / "validation.json").write_text(
        json.dumps({"valid": True}), encoding="utf-8"
    )


def test_local_folder_to_validated_carousel_fixture(tmp_path: Path):
    incoming = tmp_path / "incoming" / "carousel"
    incoming.mkdir(parents=True)
    Image.new("RGB", (800, 450), "red").save(incoming / "01.jpg")
    Image.new("RGB", (800, 450), "blue").save(incoming / "02.jpg")
    scan = scanner.scan(tmp_path / "incoming")
    assert len(scan["tasks"]) == 1
    assert len(scan["tasks"][0]["files"]) == 2

    delivery = run_dirs.create(tmp_path / "output", "carousel")
    _write_delivery_files(delivery, "xiaohongshu")
    manifest_path = delivery / "analysis" / "manifest.json"
    manifest.create(manifest_path, "xiaohongshu", ["01", "02"])
    generated = delivery / "generated"
    generated.mkdir()
    for asset_id in ["01", "02"]:
        Image.new("RGB", (2048, 1152), "white").save(generated / f"{asset_id}.png")
        manifest.mark(manifest_path, asset_id, "validated", output=f"generated/{asset_id}.png")

    assert validation.validate_delivery(delivery, "xiaohongshu")["valid"] is True
    assert manifest.pending(manifest_path) == []


def test_delivery_rejects_wrong_generated_asset_dimensions(tmp_path: Path):
    delivery = run_dirs.create(tmp_path / "output", "bad-carousel")
    _write_delivery_files(delivery, "xiaohongshu")
    manifest_path = delivery / "analysis" / "manifest.json"
    manifest.create(manifest_path, "xiaohongshu", ["01"])
    generated = delivery / "generated"
    generated.mkdir()
    Image.new("RGB", (1152, 1152), "white").save(generated / "01.png")
    manifest.mark(manifest_path, "01", "validated", output="generated/01.png")

    result = validation.validate_delivery(delivery, "xiaohongshu")

    assert any("expected 2048x1152" in error for error in result["errors"])
