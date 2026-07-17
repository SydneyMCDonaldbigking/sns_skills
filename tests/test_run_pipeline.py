import json
from pathlib import Path

from PIL import Image

from viral_social_test_loader import load_script


pipeline = load_script("run_pipeline")


def test_prepare_run_creates_delivery_skeleton(tmp_path: Path):
    incoming = tmp_path / "incoming" / "carousel"
    incoming.mkdir(parents=True)
    Image.new("RGB", (800, 450), "red").save(incoming / "01.jpg")
    Image.new("RGB", (800, 450), "blue").save(incoming / "02.jpg")

    run_dir = pipeline.prepare_run(
        incoming,
        "xiaohongshu",
        output_root=tmp_path / "output",
        task_name="carousel",
    )

    assert (run_dir / "source" / "01.jpg").is_file()
    assert (run_dir / "source" / "02.jpg").is_file()
    assert (run_dir / "analysis" / "breakdown.md").is_file()
    assert (run_dir / "analysis" / "caption-zh.txt").is_file()
    assert (run_dir / "references" / "keyframes").is_dir()
    assert (run_dir / "generated").is_dir()
    assert (run_dir / "overview").is_dir()
    assert (run_dir / "qa").is_dir()

    data = json.loads((run_dir / "analysis" / "manifest.json").read_text(encoding="utf-8"))
    assert data["source"]["kind"] == "local_folder"
    assert data["source"]["paths"] == ["source/01.jpg", "source/02.jpg"]
    assert list(data["assets"]) == ["01", "02"]


def test_validate_run_writes_validation_json_for_incomplete_delivery(tmp_path: Path):
    incoming = tmp_path / "incoming" / "carousel"
    incoming.mkdir(parents=True)
    Image.new("RGB", (800, 450), "red").save(incoming / "01.jpg")
    run_dir = pipeline.prepare_run(
        incoming,
        "instagram-facebook",
        output_root=tmp_path / "output",
    )

    result = pipeline.validate_run(run_dir, "instagram-facebook")

    assert result["valid"] is False
    assert (run_dir / "qa" / "validation.json").is_file()
    saved = json.loads((run_dir / "qa" / "validation.json").read_text(encoding="utf-8"))
    assert saved == result
