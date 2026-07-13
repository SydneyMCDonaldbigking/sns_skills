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
