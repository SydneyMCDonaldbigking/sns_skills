import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from viral_social_test_loader import load_script


validation = load_script("validate_output")
SCRIPT = Path(__file__).parents[1] / "viral-social-remix" / "scripts" / "validate_output.py"


def test_xiaohongshu_rejects_wrong_dimensions(tmp_path):
    path = tmp_path / "01.png"
    Image.new("RGB", (1152, 1152)).save(path)
    result = validation.validate_asset(path, "xiaohongshu", text_review="passed")
    assert result["valid"] is False
    assert "1152x1536" in result["errors"][0]


def test_instagram_asset_passes_with_text_review(tmp_path):
    path = tmp_path / "01.png"
    Image.new("RGB", (1152, 1152)).save(path)
    result = validation.validate_asset(path, "instagram-facebook", text_review="passed")
    assert result == {"valid": True, "errors": []}


def test_video_delivery_requires_nine_frames_and_english_caption(tmp_path):
    generated = tmp_path / "generated"
    generated.mkdir()
    for index in range(8):
        Image.new("RGB", (1920, 1080)).save(generated / f"{index + 1:02d}.png")
    result = validation.validate_delivery(tmp_path, "video", caption_language="en")
    assert "exactly 9 generated frames" in result["errors"]
    assert any("caption-en.txt" in error for error in result["errors"])


def test_vertical_video_delivery_uses_english_caption_and_vertical_dimensions(tmp_path):
    generated = tmp_path / "generated"
    analysis = tmp_path / "analysis"
    page_prompts = analysis / "page-prompts"
    overview = tmp_path / "overview"
    qa = tmp_path / "qa"
    generated.mkdir()
    analysis.mkdir()
    page_prompts.mkdir()
    overview.mkdir()
    qa.mkdir()
    for name in [
        "breakdown.md",
        "copy.md",
        "caption-en.txt",
        "prompts.md",
        "brief.md",
        "shot-list.md",
        "seedance-prompt.md",
    ]:
        (analysis / name).write_text("fixture", encoding="utf-8")
    for index in range(1, 10):
        (page_prompts / f"page-{index:02d}.md").write_text(
            "fixture",
            encoding="utf-8",
        )
    (analysis / "manifest.json").write_text(
        '{"assets":{"01":{"status":"pending"}}}',
        encoding="utf-8",
    )
    (overview / "contact-sheet.png").write_text("fixture", encoding="utf-8")
    (qa / "validation.json").write_text("{}", encoding="utf-8")
    for index in range(1, 10):
        Image.new("RGB", (1080, 1920)).save(generated / f"page-{index:02d}.png")

    result = validation.validate_delivery(tmp_path, "vertical-video")

    assert result["valid"] is False
    assert any("manifest contains incomplete assets" in error for error in result["errors"])
    assert not any("caption-zh.txt" in error for error in result["errors"])


def test_vertical_video_delivery_requires_handoff_files(tmp_path):
    generated = tmp_path / "generated"
    analysis = tmp_path / "analysis"
    overview = tmp_path / "overview"
    qa = tmp_path / "qa"
    generated.mkdir()
    analysis.mkdir()
    overview.mkdir()
    qa.mkdir()
    for name in ["breakdown.md", "copy.md", "caption-en.txt", "prompts.md"]:
        (analysis / name).write_text("fixture", encoding="utf-8")
    (analysis / "manifest.json").write_text(
        '{"assets":{"01":{"status":"validated"}}}',
        encoding="utf-8",
    )
    (overview / "contact-sheet.png").write_text("fixture", encoding="utf-8")
    (qa / "validation.json").write_text("{}", encoding="utf-8")
    for index in range(1, 10):
        Image.new("RGB", (1080, 1920)).save(generated / f"page-{index:02d}.png")

    result = validation.validate_delivery(tmp_path, "vertical-video")

    assert any("brief.md" in error for error in result["errors"])
    assert any("shot-list.md" in error for error in result["errors"])
    assert any("seedance-prompt.md" in error for error in result["errors"])
    assert any("page-prompts" in error for error in result["errors"])


def test_vertical_video_compact_reference_delivery_skips_legacy_storyboard_requirements(tmp_path):
    analysis = tmp_path / "analysis"
    qa = tmp_path / "qa"
    analysis.mkdir()
    qa.mkdir()
    for name in [
        "breakdown.md",
        "copy.md",
        "caption-en.txt",
        "prompts.md",
        "brief.md",
        "shot-list.md",
        "seedance-prompt.md",
    ]:
        (analysis / name).write_text("fixture", encoding="utf-8")
    (analysis / "manifest.json").write_text(
        json.dumps(
            {
                "platform": "vertical-video",
                "video_mode": "compact-reference",
                "assets": {
                    "01": {"status": "pending", "storyboard_url": "https://cdn.example/01.png"},
                    "02": {"status": "pending", "storyboard_url": "https://cdn.example/02.png"},
                    "03": {"status": "pending", "storyboard_url": "https://cdn.example/03.png"},
                },
            }
        ),
        encoding="utf-8",
    )
    (qa / "validation.json").write_text("{}", encoding="utf-8")

    result = validation.validate_delivery(tmp_path, "vertical-video")

    assert result["valid"] is True
    assert not any("exactly 9 generated frames" in error for error in result["errors"])
    assert not any("page-prompts" in error for error in result["errors"])
    assert not any("contact-sheet" in error for error in result["errors"])


def _write_compact_delivery_files(tmp_path):
    analysis = tmp_path / "analysis"
    qa = tmp_path / "qa"
    analysis.mkdir()
    qa.mkdir()
    for name in [
        "breakdown.md",
        "copy.md",
        "caption-en.txt",
        "prompts.md",
        "brief.md",
        "shot-list.md",
        "seedance-prompt.md",
    ]:
        (analysis / name).write_text("fixture", encoding="utf-8")
    (qa / "validation.json").write_text("{}", encoding="utf-8")
    return analysis


def test_vertical_video_compact_reference_rejects_empty_structured_references(
    tmp_path,
):
    analysis = _write_compact_delivery_files(tmp_path)
    (analysis / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "platform": "vertical-video",
                "video": {
                    "mode": "compact-reference",
                    "profile": "visual-preview",
                    "references": [],
                },
                "assets": {"01": {"status": "pending"}},
            }
        ),
        encoding="utf-8",
    )

    result = validation.validate_delivery(tmp_path, "vertical-video")

    assert result["valid"] is False
    assert any("at least one image or video" in error for error in result["errors"])


def test_vertical_video_compact_reference_rejects_audio_only_manifest(tmp_path):
    analysis = _write_compact_delivery_files(tmp_path)
    (analysis / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "platform": "vertical-video",
                "video": {
                    "mode": "compact-reference",
                    "profile": "visual-preview",
                    "references": [
                        {
                            "id": "ambience",
                            "type": "audio",
                            "order": 1,
                            "url": "https://cdn.example/ambience.mp3",
                        }
                    ],
                },
                "assets": {},
            }
        ),
        encoding="utf-8",
    )

    result = validation.validate_delivery(tmp_path, "vertical-video")

    assert result["valid"] is False
    assert any("audio-only" in error for error in result["errors"])


def test_vertical_video_compact_reference_rejects_at_image_prompt_syntax(tmp_path):
    analysis = _write_compact_delivery_files(tmp_path)
    (analysis / "seedance-prompt.md").write_text(
        "Use @Image1 as the product reference.",
        encoding="utf-8",
    )
    (analysis / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "platform": "vertical-video",
                "video": {
                    "mode": "compact-reference",
                    "profile": "visual-preview",
                    "references": [
                        {
                            "id": "product",
                            "type": "image",
                            "order": 1,
                            "url": "https://cdn.example/product.png",
                        }
                    ],
                },
                "assets": {},
            }
        ),
        encoding="utf-8",
    )

    result = validation.validate_delivery(tmp_path, "vertical-video")

    assert result["valid"] is False
    assert any("[Image 1]" in error for error in result["errors"])


def test_manifest_v2_compact_requires_control_sections(tmp_path):
    analysis = _write_compact_delivery_files(tmp_path)
    (analysis / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "platform": "vertical-video",
                "video": {
                    "mode": "compact-reference",
                    "profile": "visual-preview",
                    "references": [
                        {
                            "id": "product",
                            "type": "image",
                            "order": 1,
                            "url": "https://cdn.example/product.png",
                        }
                    ],
                    "shots": [],
                },
                "assets": {},
            }
        ),
        encoding="utf-8",
    )

    result = validation.validate_delivery(tmp_path, "vertical-video")

    assert result["valid"] is False
    assert any("exactly three soft shots" in error for error in result["errors"])
    assert any("video.delivery" in error for error in result["errors"])
    assert any("video_workflow" in error for error in result["errors"])
    assert any("video.brand" in error for error in result["errors"])


def test_delivery_cli_writes_validation_report(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "delivery",
            str(tmp_path),
            "--platform",
            "xiaohongshu",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    report = tmp_path / "qa" / "validation.json"
    assert result.returncode == 1
    assert report.is_file()
    assert json.loads(report.read_text(encoding="utf-8"))["valid"] is False
