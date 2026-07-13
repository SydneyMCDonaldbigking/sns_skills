"""Clean and rebuild Rednote post exports.

The Chrome/PowerShell pipeline can produce two different "garbling" problems:

1. Console display mojibake: the JSON is actually valid UTF-8, but PowerShell
   renders Chinese as `馃/鐧/琛`. Do not rewrite data just because terminal output
   looks bad.
2. Real markdown damage: shell-created labels can become `???` even when the
   JSON fields are clean. Rebuild markdown from JSON instead of patching those
   labels in place.

This script cleans string fields conservatively and regenerates `content.md`.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


MOJIBAKE_MARKERS = re.compile(r"[馃锔鐧琛鎮绾鍥鏃搴鍔緐鈥銆€锘�]")
TEXT_RUN = re.compile(r"[\u0080-\uffff]{2,}")
BROKEN_NEWLINE = re.compile(r"[縗碶]\s*n")


def _badness(text: str) -> int:
    """Higher means more likely to be mojibake."""

    return (
        len(MOJIBAKE_MARKERS.findall(text)) * 4
        + text.count("?") * 2
        + text.count("�") * 6
        + text.count("锟") * 8
    )


def _goodness(text: str) -> int:
    """Reward ordinary CJK text and common punctuation."""

    cjk = sum("\u4e00" <= ch <= "\u9fff" for ch in text)
    punctuation = sum(ch in "，。！？、：；（）《》“”" for ch in text)
    return cjk + punctuation


def _score(text: str) -> int:
    return _goodness(text) - _badness(text)


def _try_decode_fragment(fragment: str) -> str:
    """Try fixing UTF-8 bytes that were decoded as GBK/GB18030.

    Example: `琛ヨ创` should become `补贴`. The function is intentionally
    conservative: it only replaces a fragment when the decoded candidate scores
    better than the original.
    """

    if not MOJIBAKE_MARKERS.search(fragment):
        return fragment
    best = fragment
    best_score = _score(fragment)
    for encoding in ("gb18030", "gbk", "cp936"):
        try:
            candidate = fragment.encode(encoding).decode("utf-8")
        except UnicodeError:
            continue
        candidate_score = _score(candidate)
        if candidate_score > best_score:
            best = candidate
            best_score = candidate_score
    return best


def clean_text(value: str) -> str:
    """Clean one text value while avoiding changes to already-good Chinese."""

    value = value.replace("\\n", "\n")
    value = BROKEN_NEWLINE.sub("\n", value)
    value = TEXT_RUN.sub(lambda match: _try_decode_fragment(match.group(0)), value)
    value = re.sub(r"[ \t]+\n", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def clean_obj(value: Any) -> Any:
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, list):
        return [clean_obj(item) for item in value]
    if isinstance(value, dict):
        return {key: clean_obj(item) for key, item in value.items()}
    return value


def _image_size_text(image: dict[str, Any]) -> str:
    size = image.get("size")
    if isinstance(size, list | tuple) and len(size) == 2:
        return f"{size[0]}×{size[1]}"
    return "未知"


def build_markdown(meta: dict[str, Any]) -> str:
    lines: list[str] = [
        f"# {meta.get('title', 'Untitled')}",
        "",
        f"链接：{meta.get('url', '')}",
        f"日期：{meta.get('date', '未识别')}",
        f"图集：{meta.get('counter', '未识别')}",
        "",
        "## 正文",
        "",
        meta.get("body") or "（未提取到正文）",
        "",
    ]

    hashtags = meta.get("hashtags") or []
    if hashtags:
        lines += ["## 话题", ""]
        lines += [f"- {tag}" for tag in hashtags]
        lines += [""]

    images = meta.get("images") or []
    lines += ["## 图片", ""]
    if not images:
        lines += ["（未提取到图片）", ""]
    for image in images:
        index = int(image.get("index", len(lines)))
        local_path = str(image.get("local_path", ""))
        lines += [
            f"![{index:02d}]({local_path})",
            f"- 文件：`{local_path}`",
            f"- 尺寸：{_image_size_text(image)}",
            f"- 大小：{image.get('bytes', 0)} bytes",
            f"- 源图：{image.get('url', '')}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def clean_post_dir(post_dir: Path, apply: bool = False) -> dict[str, Any]:
    metadata_path = post_dir / "metadata.json"
    if not metadata_path.is_file():
        raise FileNotFoundError(f"missing metadata.json: {post_dir}")

    raw = json.loads(metadata_path.read_text(encoding="utf-8"))
    cleaned = clean_obj(raw)
    markdown = build_markdown(cleaned)

    cleaned_metadata_path = post_dir / "metadata.cleaned.json"
    cleaned_content_path = post_dir / "content.cleaned.md"
    cleaned_metadata_path.write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    cleaned_content_path.write_text(markdown, encoding="utf-8")

    if apply:
        metadata_path.write_text(
            json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (post_dir / "content.md").write_text(markdown, encoding="utf-8")

    return {
        "post_dir": str(post_dir),
        "title": cleaned.get("title", ""),
        "images": len(cleaned.get("images") or []),
        "wrote": [str(cleaned_metadata_path), str(cleaned_content_path)],
        "applied": apply,
    }


def iter_post_dirs(path: Path) -> list[Path]:
    if (path / "metadata.json").is_file():
        return [path]
    return sorted(child for child in path.iterdir() if (child / "metadata.json").is_file())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="A post folder or a folder containing post folders.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Overwrite metadata.json and content.md after writing cleaned copies.",
    )
    args = parser.parse_args()

    results = [clean_post_dir(post_dir, apply=args.apply) for post_dir in iter_post_dirs(Path(args.path))]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
