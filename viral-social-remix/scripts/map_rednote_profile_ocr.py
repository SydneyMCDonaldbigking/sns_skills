#!/usr/bin/env python3
"""Map OCR keyword hits from Rednote profile screenshots back to note cards."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image
from rapidocr_onnxruntime import RapidOCR


DEFAULT_PATTERNS = [r"补[贴帖]", r"百[万萬].{0,4}补[贴帖]"]


def box_center(box):
    xs = [pt[0] for pt in box]
    ys = [pt[1] for pt in box]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def match_card(cards, vx: float, vy: float, margin: float = 24):
    for card in cards:
        rect = card.get("rect") or {}
        x = float(rect.get("x", 0))
        y = float(rect.get("y", 0))
        w = float(rect.get("w") or rect.get("width") or 0)
        h = float(rect.get("h") or rect.get("height") or 0)
        if x - margin <= vx <= x + w + margin and y - margin <= vy <= y + h + margin:
            return card
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile_run_dir", type=Path)
    parser.add_argument("--scan-json", default="raw/screen-scan.json")
    parser.add_argument("--out", default="raw/screen-ocr-map.json")
    parser.add_argument("--pattern", action="append", default=[])
    args = parser.parse_args()

    root = args.profile_run_dir
    scan = json.loads((root / args.scan_json).read_text(encoding="utf-8"))
    patterns = [re.compile(p) for p in (args.pattern or DEFAULT_PATTERNS)]
    ocr = RapidOCR()

    screens_out = []
    candidates = {}
    unassigned = []

    for screen in scan.get("screens", []):
        img_path = root / screen["screenshot"]
        if not img_path.exists():
            continue
        img = Image.open(img_path)
        sw, sh = img.size
        vw = float(screen.get("innerWidth") or sw)
        vh = float(screen.get("innerHeight") or sh)
        sx = sw / vw if vw else 1
        sy = sh / vh if vh else 1
        result, _ = ocr(str(img_path))
        hits = []

        for item in result or []:
            box, text, score = item[0], str(item[1]), float(item[2])
            if not any(p.search(text) for p in patterns):
                continue
            cx, cy = box_center(box)
            vx, vy = cx / sx, cy / sy
            card = match_card(screen.get("cards", []), vx, vy)
            hit = {
                "text": text,
                "score": score,
                "box": box,
                "center_screen": [vx, vy],
                "matched_note_id": card.get("noteId") if card else None,
                "matched_title": card.get("title") if card else None,
                "matched_href": card.get("href") if card else None,
            }
            hits.append(hit)
            if card:
                key = card.get("noteId") or card.get("href") or card.get("title")
                rec = candidates.setdefault(
                    key,
                    {
                        "noteId": card.get("noteId"),
                        "title": card.get("title"),
                        "href": card.get("href"),
                        "reasons": set(),
                        "ocr_hits": [],
                    },
                )
                rec["reasons"].add("profile_image_ocr")
                rec["ocr_hits"].append(
                    {"screen": screen.get("screen"), "text": text, "score": score}
                )
            else:
                unassigned.append(
                    {
                        "screen": screen.get("screen"),
                        "text": text,
                        "score": score,
                        "center_screen": [vx, vy],
                    }
                )

        screens_out.append(
            {
                "screen": screen.get("screen"),
                "screenshot": screen.get("screenshot"),
                "size": [sw, sh],
                "hits": hits,
            }
        )

    title_pat = re.compile(r"补[贴帖]|百[万萬].{0,4}补[贴帖]")
    for note in scan.get("notes", []):
        title = note.get("title") or ""
        if not title_pat.search(title):
            continue
        key = note.get("noteId") or note.get("href") or title
        rec = candidates.setdefault(
            key,
            {
                "noteId": note.get("noteId"),
                "title": title,
                "href": note.get("href"),
                "reasons": set(),
                "ocr_hits": [],
            },
        )
        rec["reasons"].add("profile_title")

    cand_list = []
    for rec in candidates.values():
        rec["reasons"] = sorted(rec["reasons"])
        cand_list.append(rec)

    cand_list.sort(key=lambda r: (r.get("title") or "", r.get("noteId") or ""))
    summary = {
        "screens": len(screens_out),
        "profile_image_ocr_cards": sum(
            1 for c in cand_list if "profile_image_ocr" in c["reasons"]
        ),
        "profile_title_cards": sum(1 for c in cand_list if "profile_title" in c["reasons"]),
        "total_candidates": len(cand_list),
        "unassigned_hits": len(unassigned),
    }
    out = {
        "source": str(root),
        "summary": summary,
        "candidates": cand_list,
        "unassigned_hits": unassigned,
        "screens": screens_out,
    }
    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for i, cand in enumerate(cand_list, 1):
        print(
            f"{i:02d}. {cand.get('title')} | "
            f"{','.join(cand.get('reasons', []))} | {cand.get('href')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
