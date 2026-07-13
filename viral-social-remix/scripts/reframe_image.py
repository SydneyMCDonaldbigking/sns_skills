"""Reframe generated images for social formats."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


PRESETS = {
    "xhs-portrait": (1080, 1440),
    "xhs-portrait-1152": (1152, 1536),
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


def _feather_mask(size: tuple[int, int], feather: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle(
        (feather, feather, size[0] - feather, size[1] - feather),
        fill=255,
    )
    return mask.filter(ImageFilter.GaussianBlur(feather / 2))


def feather_pad(
    image: Image.Image,
    size: tuple[int, int],
    center_size: tuple[int, int] | None = None,
    blur_radius: int = 28,
    feather: int = 48,
) -> Image.Image:
    bg = cover_crop(image, size).filter(ImageFilter.GaussianBlur(blur_radius))
    bg = bg.point(lambda value: min(255, round(value * 0.96 + 8)))

    target = center_size or (min(size[0], image.width), min(size[0], image.width))
    ratio = min(target[0] / image.width, target[1] / image.height, 1.0)
    fg = image.resize(
        (round(image.width * ratio), round(image.height * ratio)),
        Image.Resampling.LANCZOS,
    )
    mask = _feather_mask(fg.size, min(feather, fg.width // 6, fg.height // 6))
    x = (size[0] - fg.width) // 2
    y = (size[1] - fg.height) // 2
    bg.paste(fg, (x, y), mask)
    return bg


def reframe(
    input_path: str | Path,
    output_path: str | Path,
    size: tuple[int, int],
    mode: str = "cover",
    x_anchor: float = 0.5,
    y_anchor: float = 0.45,
    center_size: tuple[int, int] | None = None,
    feather: int = 48,
) -> None:
    with Image.open(input_path) as source:
        image = source.convert("RGB")
    if mode == "cover":
        result = cover_crop(image, size, x_anchor=x_anchor, y_anchor=y_anchor)
    elif mode == "blur-pad":
        result = blur_pad(image, size)
    elif mode == "feather-pad":
        result = feather_pad(image, size, center_size=center_size, feather=feather)
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
    parser.add_argument(
        "--mode",
        choices=["cover", "blur-pad", "feather-pad"],
        default="cover",
    )
    parser.add_argument("--x-anchor", type=float, default=0.5)
    parser.add_argument("--y-anchor", type=float, default=0.45)
    parser.add_argument("--center-size", type=_parse_size)
    parser.add_argument("--feather", type=int, default=48)
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
            center_size=args.center_size,
            feather=args.feather,
        )
        print(output_path)


if __name__ == "__main__":
    main()
