import json
from pathlib import Path
import subprocess
import sys

from PIL import Image

from viral_social_test_loader import load_script


manifest = load_script("manifest")
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


def test_pending_assets_returns_non_validated_asset_ids(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    manifest.create(manifest_path, "xiaohongshu", ["01", "02", "03"])
    manifest.mark(manifest_path, "01", "validated")
    manifest.mark(manifest_path, "02", "generated", output="generated/02.png")

    assert pipeline.pending_assets(manifest_path) == ["02", "03"]


def test_pending_cli_outputs_json(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    manifest.create(manifest_path, "xiaohongshu", ["01", "02"])
    manifest.mark(manifest_path, "01", "validated")
    script = Path(__file__).parents[1] / "viral-social-remix" / "scripts" / "run_pipeline.py"

    result = subprocess.run(
        [sys.executable, str(script), "pending", str(manifest_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(result.stdout) == {"pending": ["02"]}


def test_generate_asset_uses_run_defaults(tmp_path: Path, monkeypatch):
    run_dir = tmp_path / "output" / "run"
    analysis = run_dir / "analysis"
    analysis.mkdir(parents=True)
    (analysis / "prompts.md").write_text("prompt", encoding="utf-8")
    manifest.create(analysis / "manifest.json", "xiaohongshu", ["01"])
    captured = {}

    def fake_generate_image(**kwargs):
        captured.update(kwargs)
        return {"saved": ["generated/01.png"]}

    monkeypatch.setattr(pipeline.openrouter_image, "generate_image", fake_generate_image)

    result = pipeline.generate_asset(run_dir, "01", dry_run=True)

    assert result == {"saved": ["generated/01.png"]}
    assert captured["prompt_file"] == analysis / "prompts.md"
    assert captured["out_dir"] == run_dir / "generated"
    assert captured["stem"] == "01"
    assert captured["size"] == "1152x1536"
    assert captured["manifest_path"] == analysis / "manifest.json"
    assert captured["asset_id"] == "01"
    assert captured["dry_run"] is True


def test_generate_cli_outputs_json(tmp_path: Path, monkeypatch, capsys):
    run_dir = tmp_path / "output" / "run"
    analysis = run_dir / "analysis"
    analysis.mkdir(parents=True)
    (analysis / "prompts.md").write_text("prompt", encoding="utf-8")
    manifest.create(analysis / "manifest.json", "instagram-facebook", ["02"])

    def fake_generate_image(**kwargs):
        assert kwargs["size"] == "1152x1152"
        assert kwargs["asset_id"] == "02"
        assert kwargs["force"] is True
        return {"saved": ["generated/02.png"]}

    monkeypatch.setattr(pipeline.openrouter_image, "generate_image", fake_generate_image)

    code = pipeline.main(
        [
            "generate",
            str(run_dir),
            "--asset-id",
            "02",
            "--force",
        ]
    )

    assert code == 0
    assert json.loads(capsys.readouterr().out) == {"saved": ["generated/02.png"]}
