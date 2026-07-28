import json
from pathlib import Path
import subprocess
import sys

from PIL import Image

from viral_social_test_loader import load_script


manifest = load_script("manifest")
pipeline = load_script("run_pipeline")


class FakeResponse:
    def __init__(self, data: bytes, content_type: str):
        self._data = data
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return self._data


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


def test_prepare_original_video_run_creates_three_clip_storyboard_skeleton(tmp_path: Path):
    run_dir = pipeline.prepare_original_video_run(
        brief="Brand: UMall. Dish: quick tomato egg stir fry.",
        output_root=tmp_path / "output",
        task_name="tomato-egg",
    )

    assert (run_dir / "analysis" / "brief.md").is_file()
    assert (run_dir / "analysis" / "shot-list.md").is_file()
    assert (run_dir / "analysis" / "seedance-prompt.md").is_file()
    assert (run_dir / "analysis" / "caption-en.txt").is_file()
    shot_list = (run_dir / "analysis" / "shot-list.md").read_text(encoding="utf-8")
    assert "TODO" not in shot_list
    for phrase in [
        "frames 01-03",
        "frames 04-06",
        "frames 07-09",
        "exactly three ordered frames per request",
    ]:
        assert phrase in shot_list
    for index in range(1, 4):
        assert (
            run_dir
            / "analysis"
            / "seedance-prompts"
            / f"clip-{index:02d}.md"
        ).is_file()

    data = json.loads((run_dir / "analysis" / "manifest.json").read_text(encoding="utf-8"))
    assert data["platform"] == "vertical-video"
    assert data["schema_version"] == 2
    assert data["video_mode"] == "storyboard-three-clips"
    assert data["video"]["mode"] == "storyboard-three-clips"
    assert data["video"]["profile"] == "final-clip"
    assert [group["frames"] for group in data["video"]["clip_groups"]] == [
        ["01", "02", "03"],
        ["04", "05", "06"],
        ["07", "08", "09"],
    ]
    assert data["video"]["generation"]["generate_audio"] is False
    assert data["video"]["generation"]["return_last_frame"] is True
    assert data["video"]["delivery"] == {
        "ratio": "9:16",
        "resolution": "1080p",
        "target_duration": None,
        "duration_policy": "preserve coherent sequence; trim only defects, repetition, awkward joins, or dead time",
        "expect_audio": True,
        "audio_policy": "user voiceover plus agent-generated BGM and cooking SFX",
        "text_policy": "editable white centered current-step captions in ChatCut",
    }
    assert data["storyboard_references"] == []
    assert data["video_workflow"]["status"] == "prepared"
    assert data["source"]["kind"] == "original_brief"
    assert data["source"]["brief_path"] == "analysis/brief.md"
    assert list(data["assets"]) == [
        "01", "02", "03", "04", "05", "06", "07", "08", "09"
    ]


def test_prepare_original_video_run_records_structured_references(tmp_path: Path):
    image = tmp_path / "product.png"
    image.write_bytes(b"image")

    run_dir = pipeline.prepare_original_video_run(
        brief="Brand: UMall. Dish: quick tomato egg stir fry.",
        output_root=tmp_path / "output",
        task_name="tomato-egg-refs",
        image_references=[str(image)],
        video_references=["https://cdn.example/motion.mp4"],
        audio_references=["https://cdn.example/ambience.mp3"],
    )

    data = json.loads(
        (run_dir / "analysis" / "manifest.json").read_text(encoding="utf-8")
    )
    references = data["storyboard_references"]
    assert [item["type"] for item in references] == [
        "image",
        "video",
        "audio",
    ]
    assert references[0]["path"].startswith("references/inputs/")
    assert (run_dir / references[0]["path"]).read_bytes() == b"image"
    assert references[1]["url"] == "https://cdn.example/motion.mp4"
    assert references[2]["url"] == "https://cdn.example/ambience.mp3"


def test_prepare_url_run_downloads_direct_media_url(tmp_path: Path):
    requests = []

    def fake_open(request, timeout):
        requests.append((request.full_url, timeout, request.headers["User-agent"]))
        return FakeResponse(b"image bytes", "image/png; charset=binary")

    run_dir = pipeline.prepare_url_run(
        "https://example.test/media/cover",
        "instagram-facebook",
        output_root=tmp_path / "output",
        opener=fake_open,
    )

    source = run_dir / "source" / "cover.png"
    assert requests == [("https://example.test/media/cover", 60, "viral-social-remix/0.1")]
    assert source.read_bytes() == b"image bytes"

    data = json.loads((run_dir / "analysis" / "manifest.json").read_text(encoding="utf-8"))
    assert data["source"]["kind"] == "direct_url"
    assert data["source"]["url"] == "https://example.test/media/cover"
    assert data["source"]["paths"] == ["source/cover.png"]
    assert data["source"]["content_type"] == "image/png"
    assert data["source"]["bytes"] == len(b"image bytes")


def test_prepare_url_run_rejects_html_pages(tmp_path: Path):
    def fake_open(request, timeout):
        return FakeResponse(b"<html></html>", "text/html")

    try:
        pipeline.prepare_url_run(
            "https://example.test/post/123",
            "xiaohongshu",
            output_root=tmp_path / "output",
            opener=fake_open,
        )
    except ValueError as exc:
        assert "direct supported media file" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_prepare_url_run_rejects_image_for_video_platform(tmp_path: Path):
    def fake_open(request, timeout):
        return FakeResponse(b"image bytes", "image/jpeg")

    try:
        pipeline.prepare_url_run(
            "https://example.test/media/cover.jpg",
            "video",
            output_root=tmp_path / "output",
            opener=fake_open,
        )
    except ValueError as exc:
        assert "Video platform requires" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


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
