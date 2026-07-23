from PIL import Image

from viral_social_test_loader import load_script


validation = load_script("validate_output")


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
