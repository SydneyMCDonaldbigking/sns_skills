from PIL import Image

from viral_social_test_loader import load_script


sheets = load_script("make_contact_sheet")


def test_storyboard_is_1920_by_1080(tmp_path):
    inputs = []
    for index in range(9):
        path = tmp_path / f"{index}.png"
        Image.new("RGB", (640, 360), (index * 20, 40, 80)).save(path)
        inputs.append(path)
    output = tmp_path / "storyboard.png"

    sheets.make_storyboard(inputs, output, [f"Frame {index + 1}" for index in range(9)])

    assert Image.open(output).size == (1920, 1080)


def test_storyboard_rejects_non_nine_input(tmp_path):
    try:
        sheets.make_storyboard([], tmp_path / "out.png", [])
    except ValueError as exc:
        assert "9 images" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
