"""OCR Rednote screenshots or downloaded post images for keyword filtering."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


DEFAULT_PATTERNS = [
    r"补[贴帖]",
    r"百[万萬].{0,4}补[贴帖]",
]


def load_ocr_engine():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise SystemExit(
            "rapidocr_onnxruntime is not installed. "
            "Install the OCR extra with: pip install -e .[ocr]"
        ) from exc
    return RapidOCR()


def iter_images(path: Path) -> Iterable[Path]:
    if path.is_file():
        if ".ocr." not in path.name:
            yield path
        return
    for suffix in ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp"):
        yield from (
            image
            for image in sorted(path.rglob(suffix))
            if ".ocr." not in image.name
        )


def ocr_image(ocr, path: Path) -> dict:
    result, elapsed = ocr(str(path))
    lines = []
    if result:
        for item in result:
            if len(item) >= 3:
                lines.append(
                    {
                        "text": str(item[1]),
                        "score": float(item[2]),
                        "box": item[0],
                    }
                )
    text = "\n".join(line["text"] for line in lines)
    return {
        "path": str(path),
        "text": text,
        "lines": lines,
        "elapsed": elapsed,
    }


def compile_patterns(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


def mark_hits(item: dict, patterns: list[re.Pattern[str]]) -> dict:
    text = item["text"]
    hits = []
    for pattern in patterns:
        for match in pattern.finditer(text):
            hits.append(
                {
                    "pattern": pattern.pattern,
                    "match": match.group(0),
                    "span": [match.start(), match.end()],
                }
            )
    item["hit"] = bool(hits)
    item["hits"] = hits
    return item


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Image file or directory to OCR.")
    parser.add_argument("--pattern", action="append", default=[])
    parser.add_argument("--out", help="Optional JSON output path.")
    args = parser.parse_args()

    patterns = compile_patterns(args.pattern or DEFAULT_PATTERNS)
    ocr = load_ocr_engine()
    results = [
        mark_hits(ocr_image(ocr, path), patterns)
        for path in iter_images(Path(args.path))
    ]
    payload = {
        "patterns": [pattern.pattern for pattern in patterns],
        "count": len(results),
        "hit_count": sum(1 for item in results if item["hit"]),
        "results": results,
    }

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
