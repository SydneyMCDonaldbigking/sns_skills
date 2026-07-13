"""Reframe generated images for social formats."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageFilter


PRESETS = {
    "xhs-portrait": (1080, 1440),
    "story": (1080, 1920),
    "square": (1152, 1152),
    "landscape": (2048, 1152),
}


def _parse_size(value: str) -> tuple[int, int]:
    if value in PRESETS:
        return PRESETS[value]
    try:
        width, height = value.lower().split("x", 1)
        return int(width), int(height)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid size: {value}") from exc


def cover_crop(
    image: Image.Image,
    size: tuple[int, int],
    x_anchor: float = 0.5,
    y_anchor: float = 0.45,
) -> Image.Image:
    ratio = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize(
        (round(image.width * ratio), round(image.height * ratio)),
        Image.Resampling.LANCZOS,
    )
    max_left = resized.width - size[0]
    max_top = resized.height - size[1]
    left = round(max_left * x_anchor) if max_left > 0 else 0
    top = round(max_top * y_anchor) if max_top > 0 else 0
    left = min(max(left, 0), max_left)
    top = min(max(top, 0), max_top)
    return resized.crop((left, top, left + size[0], top + size[1]))


def blur_pad(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    bg = cover_crop(image, size).filter(ImageFilter.GaussianBlur(24))
    ratio = min(size[0] / image.width, size[1] / image.height)
    fg = image.resize(
        (round(image.width * ratio), round(image.height * ratio)),
        Image.Resampling.LANCZOS,
    )
    bg.paste(fg, ((size[0] - fg.width) // 2, (size[1] - fg.height) // 2))
    return bg


def reframe(
    input_path: str | Path,
    output_path: str | Path,
    size: tuple[int, int],
    mode: str = "cover",
    x_anchor: float = 0.5,
    y_anchor: float = 0.45,
) -> None:
    with Image.open(input_path) as source:
        image = source.convert("RGB")
    if mode == "cover":
        result = cover_crop(image, size, x_anchor=x_anchor, y_anchor=y_anchor)
    elif mode == "blur-pad":
        result = blur_pad(image, size)
    else:
        raise ValueError(f"Unsupported mode: {mode}")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--size", type=_parse_size, default=PRESETS["xhs-portrait"])
    parser.add_argument("--mode", choices=["cover", "blur-pad"], default="cover")
    parser.add_argument("--x-anchor", type=float, default=0.5)
    parser.add_argument("--y-anchor", type=float, default=0.45)
    args = parser.parse_args()

    for raw_input in args.inputs:
        input_path = Path(raw_input)
        output_path = Path(args.out_dir) / input_path.name
        reframe(
            input_path,
            output_path,
            args.size,
            mode=args.mode,
            x_anchor=args.x_anchor,
            y_anchor=args.y_anchor,
        )
        print(output_path)


if __name__ == "__main__":
    main()
