#!/usr/bin/env python3
"""Export screened Rednote subsidy posts into one folder per post."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


KEYWORD_PATTERNS = [re.compile(r"补[贴帖]"), re.compile(r"百[万萬].{0,6}补[贴帖]")]
REDNOTE_SUFFIX = re.compile(r"\s*-\s*rednote\s*$", re.I)
DATE_RE = re.compile(r"(?:编辑于\s*)?(20\d{2}-\d{2}-\d{2})")


def load_runtime():
    try:
        from PIL import Image
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise SystemExit(
            "Missing OCR dependencies. Install with: pip install '.[ocr]'"
        ) from exc
    return Image, RapidOCR()


def safe_name(text: str, max_len: int = 40) -> str:
    text = re.sub(r"[\\/:*?\"<>|]+", "_", text or "")
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text[:max_len] or "untitled"


def clean_text(text: str) -> str:
    text = (text or "").replace("\t", "\n")
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def keyword_hit(text: str) -> bool:
    return any(p.search(text or "") for p in KEYWORD_PATTERNS)


def download(url: str, out: Path, referer: str) -> bool:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
        ),
        "Referer": referer or "https://www.rednote.com/",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        out.write_bytes(resp.read())
    return out.exists() and out.stat().st_size > 0


def ext_for(url: str) -> str:
    path = urlparse(url).path.lower()
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        if path.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return ".webp"


def run_ocr(engine, image_path: Path):
    result, _ = engine(str(image_path))
    rows = []
    for item in result or []:
        box, text, score = item[0], str(item[1]), float(item[2])
        rows.append({"text": text, "score": score, "hit": keyword_hit(text), "box": box})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--detail-json", default="raw/detail-extract.json")
    args = parser.parse_args()

    Image, ocr = load_runtime()
    root = args.run_dir
    details = json.loads((root / args.detail_json).read_text(encoding="utf-8"))["details"]
    posts_dir = root / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    manifest_posts = []
    for idx, item in enumerate(details, 1):
        cand = item["candidate"]
        data = item["data"]
        metas = data.get("metas") or {}
        raw_title = cand.get("title") or metas.get("og:title") or data.get("documentTitle") or ""
        title = REDNOTE_SUFFIX.sub("", raw_title).strip() or f"post-{idx:03d}"
        body = clean_text(metas.get("description") or metas.get("og:description") or "")
        date_match = DATE_RE.search(body)
        date = date_match.group(1) if date_match else None

        reasons = set(cand.get("reasons") or [])
        if keyword_hit(title):
            reasons.add("detail_title")
        if keyword_hit(body):
            reasons.add("detail_body")

        folder = posts_dir / f"post-{idx:03d}-{safe_name(title)}"
        images_dir = folder / "images"
        raw_dir = folder / "raw"
        images_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)

        image_records = []
        seen = set()
        for img in data.get("images") or []:
            url = img.get("src") or ""
            key = url.split("?")[0]
            if not url or key in seen:
                continue
            seen.add(key)
            out = images_dir / f"{len(image_records)+1:02d}{ext_for(url)}"
            status = "pending"
            error = None
            for attempt in range(2):
                try:
                    download(url, out, data.get("url") or cand.get("href"))
                    status = "downloaded"
                    break
                except Exception as exc:  # noqa: BLE001 - keep export resilient.
                    error = str(exc)
                    time.sleep(1 + attempt)
            size = None
            ocr_rows = []
            if status == "downloaded":
                try:
                    with Image.open(out) as im:
                        size = list(im.size)
                    ocr_rows = run_ocr(ocr, out)
                    if any(r["hit"] for r in ocr_rows):
                        reasons.add("detail_image_ocr")
                except Exception as exc:  # noqa: BLE001
                    error = f"{error or ''} OCR/size error: {exc}".strip()
            image_records.append(
                {
                    "file": str(out.relative_to(folder)).replace("\\", "/"),
                    "source_url": url,
                    "status": status,
                    "error": error,
                    "size": size,
                    "ocr_hits": [r for r in ocr_rows if r["hit"]],
                    "ocr_all": ocr_rows,
                }
            )

        metadata = {
            "post_index": idx,
            "note_id": cand.get("noteId"),
            "title": title,
            "body": body,
            "date": date,
            "source_url": data.get("url") or cand.get("href"),
            "profile_candidate_reasons": cand.get("reasons") or [],
            "final_reasons": sorted(reasons),
            "profile_ocr_hits": cand.get("ocr_hits") or [],
            "image_count": len(image_records),
            "images": image_records,
            "raw_candidate": cand,
        }
        (folder / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (raw_dir / "detail.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        lines = [
            f"# {title}",
            "",
            f"- 来源：{metadata['source_url']}",
            f"- 日期：{date or '未识别'}",
            f"- 命中原因：{', '.join(metadata['final_reasons'])}",
            f"- 图片数：{len(image_records)}",
            "",
            "## 正文",
            "",
            body or "（未提取到正文）",
            "",
            "## 图片",
            "",
        ]
        for rec in image_records:
            lines.append(f"- `{rec['file']}` {rec.get('size') or ''}")
            if rec["ocr_hits"]:
                hit_text = " / ".join(h["text"] for h in rec["ocr_hits"])
                lines.append(f"  - OCR 命中：{hit_text}")
        lines.extend(["", "## 主页/详情 OCR 线索", ""])
        for hit in cand.get("ocr_hits") or []:
            lines.append(f"- 主页截图 {hit.get('screen')}: {hit.get('text')}")
        (folder / "content.md").write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

        manifest_posts.append(
            {
                "folder": str(folder.relative_to(root)).replace("\\", "/"),
                "title": title,
                "date": date,
                "note_id": cand.get("noteId"),
                "source_url": metadata["source_url"],
                "reasons": metadata["final_reasons"],
                "image_count": len(image_records),
            }
        )

    manifest = {
        "run_dir": str(root),
        "total_posts": len(manifest_posts),
        "posts": manifest_posts,
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    index_lines = [
        "# Umall 小红书“补贴”相关帖子整理",
        "",
        f"- 总数：{len(manifest_posts)}",
        "- 筛选逻辑：主页标题命中 + 主页截图 OCR 命中 + 详情正文/图片 OCR 复核",
        "",
    ]
    for post in manifest_posts:
        index_lines.extend(
            [
                f"## {post['folder']}",
                "",
                f"- 标题：{post['title']}",
                f"- 日期：{post['date'] or '未识别'}",
                f"- 命中：{', '.join(post['reasons'])}",
                f"- 图片数：{post['image_count']}",
                f"- 链接：{post['source_url']}",
                "",
            ]
        )
    (root / "index.md").write_text("\n".join(index_lines).strip() + "\n", encoding="utf-8")
    print(json.dumps({"total_posts": len(manifest_posts), "root": str(root)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
