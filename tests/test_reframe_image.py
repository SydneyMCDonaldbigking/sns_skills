from PIL import Image

from viral_social_test_loader import load_script


reframe_image = load_script("reframe_image")


def test_cover_crop_outputs_requested_portrait_size(tmp_path):
    source = tmp_path / "square.png"
    output = tmp_path / "portrait.png"
    Image.new("RGB", (1024, 1024), "red").save(source)

    reframe_image.reframe(source, output, (1080, 1440), mode="cover")

    assert Image.open(output).size == (1080, 1440)


def test_blur_pad_outputs_requested_story_size(tmp_path):
    source = tmp_path / "square.png"
    output = tmp_path / "story.png"
    Image.new("RGB", (1024, 1024), "blue").save(source)

    reframe_image.reframe(source, output, (1080, 1920), mode="blur-pad")

    assert Image.open(output).size == (1080, 1920)


def test_feather_pad_outputs_requested_xhs_size(tmp_path):
    source = tmp_path / "square.png"
    output = tmp_path / "xhs.png"
    Image.new("RGB", (1024, 1024), "green").save(source)

    reframe_image.reframe(
        source,
        output,
        (1152, 1536),
        mode="feather-pad",
        center_size=(1152, 1152),
    )

    assert Image.open(output).size == (1152, 1536)
