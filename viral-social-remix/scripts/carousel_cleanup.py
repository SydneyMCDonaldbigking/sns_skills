"""White-cover fake prices, mosaics, and placeholder UI in carousel images."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


def parse_rect(value: str) -> tuple[float, float, float, float]:
    parts = [part.strip() for part in value.replace(";", ",").split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--rect must be x,y,w,h")
    try:
        rect = tuple(float(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--rect must contain numbers") from exc
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        raise argparse.ArgumentTypeError("--rect width and height must be positive")
    if x < 0 or y < 0:
        raise argparse.ArgumentTypeError("--rect x and y must be non-negative")
    return rect


def load_rect_file(path: Path, image: Path) -> list[tuple[float, float, float, float]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_rects: Any
    if isinstance(data, list):
        raw_rects = data
    elif isinstance(data, dict):
        raw_rects = (
            data.get(image.name)
            or data.get(image.stem)
            or data.get(str(image))
            or data.get("rects")
            or data.get("rectangles")
            or []
        )
    else:
        raw_rects = []
    rects = []
    for item in raw_rects:
        if isinstance(item, str):
            rects.append(parse_rect(item))
        elif isinstance(item, dict):
            rects.append(
                (
                    float(item["x"]),
                    float(item["y"]),
                    float(item["w"]),
                    float(item["h"]),
                )
            )
        elif isinstance(item, list) and len(item) == 4:
            rects.append(tuple(float(part) for part in item))
        else:
            raise SystemExit(f"Unsupported rectangle entry in {path}: {item!r}")
    return rects


def normalize_rect(
    rect: tuple[float, float, float, float],
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    x, y, w, h = rect
    if max(abs(x), abs(y), abs(w), abs(h)) <= 1.0:
        x *= width
        w *= width
        y *= height
        h *= height
    left = max(0, round(x))
    top = max(0, round(y))
    right = min(width, round(x + w))
    bottom = min(height, round(y + h))
    if right <= left or bottom <= top:
        raise SystemExit(f"Rectangle outside image bounds: {rect}")
    return left, top, right, bottom


def output_path_for(image: Path, args: argparse.Namespace) -> Path:
    if args.output and len(args.images) == 1:
        return Path(args.output)
    output_dir = Path(args.output_dir) if args.output_dir else image.parent
    return output_dir / f"{image.stem}{args.suffix}{image.suffix}"


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_images(args: argparse.Namespace) -> int:
    if args.output and len(args.images) != 1:
        raise SystemExit("--output can be used with exactly one image")
    explicit_rects = [parse_rect(value) for value in args.rect]
    outputs = []
    for image_path in args.images:
        image_path = Path(image_path)
        if not image_path.is_file():
            raise SystemExit(f"Missing image: {image_path}")
        rects = list(explicit_rects)
        if args.rect_file:
            rects.extend(load_rect_file(Path(args.rect_file), image_path))
        if not rects:
            raise SystemExit("No rectangles supplied. Use --rect or --rect-file.")
        with Image.open(image_path) as source:
            image = source.convert("RGBA")
        draw = ImageDraw.Draw(image)
        pixel_rects = [
            normalize_rect(rect, image.width, image.height)
            for rect in rects
        ]
        for rect in pixel_rects:
            draw.rectangle(rect, fill=args.fill)
        output = output_path_for(image_path, args)
        output.parent.mkdir(parents=True, exist_ok=True)
        image.convert("RGB").save(output)
        outputs.append(
            {
                "input": str(image_path),
                "output": str(output),
                "rectangles": [
                    {"left": left, "top": top, "right": right, "bottom": bottom}
                    for left, top, right, bottom in pixel_rects
                ],
            }
        )
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fill": args.fill,
        "outputs": outputs,
        "policy": "white-cover fake prices, mosaic placeholders, and uncertain UI; do not invent replacement prices",
    }
    if args.report:
        write_report(Path(args.report), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="White-cover carousel artifact rectangles.")
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--rect", action="append", default=[], help="Rectangle x,y,w,h. Values 0-1 are treated as fractions.")
    parser.add_argument("--rect-file", help="JSON list or image-keyed rectangle map.")
    parser.add_argument("--fill", default="#ffffff")
    parser.add_argument("--output")
    parser.add_argument("--output-dir")
    parser.add_argument("--suffix", default="-white-covered")
    parser.add_argument("--report", help="Optional QA JSON report path.")
    return clean_images(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
