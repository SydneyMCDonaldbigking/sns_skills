"""Create visual overviews for generated assets."""

from math import ceil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    ratio = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize(
        (round(image.width * ratio), round(image.height * ratio)),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - size[0]) // 2
    top = (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def make_storyboard(inputs, output, labels) -> None:
    if len(inputs) != 9 or len(labels) != 9:
        raise ValueError("Storyboard requires exactly 9 images and 9 labels")
    canvas = Image.new("RGB", (1920, 1080), "#111111")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=20)
    cell_w, cell_h, label_h = 640, 360, 38
    for index, (path, label) in enumerate(zip(inputs, labels)):
        x, y = (index % 3) * cell_w, (index // 3) * cell_h
        with Image.open(path) as source:
            image = _cover(source.convert("RGB"), (cell_w, cell_h))
        canvas.paste(image, (x, y))
        draw.rectangle(
            (x, y + cell_h - label_h, x + cell_w, y + cell_h), fill="#000000"
        )
        draw.text(
            (x + 12, y + cell_h - 31),
            f"{index + 1}. {label}",
            fill="white",
            font=font,
        )
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def make_carousel(inputs, output, columns=4, thumb=(384, 384)) -> None:
    if not inputs:
        raise ValueError("Carousel requires at least one image")
    rows = ceil(len(inputs) / columns)
    canvas = Image.new("RGB", (columns * thumb[0], rows * thumb[1]), "#111111")
    for index, path in enumerate(inputs):
        with Image.open(path) as source:
            image = _cover(source.convert("RGB"), thumb)
        canvas.paste(
            image,
            ((index % columns) * thumb[0], (index // columns) * thumb[1]),
        )
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
