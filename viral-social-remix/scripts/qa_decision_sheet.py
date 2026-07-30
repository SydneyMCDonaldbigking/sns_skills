"""Build a one-page QA decision sheet for video runs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def html_escape(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def rel(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path)


def link(path: str | None, label: str | None = None) -> str:
    if not path:
        return "<span class=\"missing\">missing</span>"
    return f"<a href=\"../{html_escape(path)}\">{html_escape(label or path)}</a>"


def img(path: str | None, label: str | None = None) -> str:
    if not path:
        return ""
    return (
        "<figure>"
        f"<img src=\"../{html_escape(path)}\" alt=\"{html_escape(label or path)}\">"
        f"<figcaption>{html_escape(label or path)}</figcaption>"
        "</figure>"
    )


def handoff_rows(run_dir: Path) -> tuple[str, list[str]]:
    reports = sorted((run_dir / "qa" / "handoffs").glob("*/handoff-review.json"))
    rows: list[str] = []
    images: list[str] = []
    for report_path in reports:
        report = load_json(report_path) or {}
        rows.append(
            "<tr>"
            f"<td>{html_escape(report.get('handoff_id', report_path.parent.name))}</td>"
            f"<td>{html_escape(report.get('decision', 'missing'))}</td>"
            f"<td>{html_escape(report.get('recommendation', ''))}</td>"
            f"<td>{link(rel(report_path, run_dir), 'json')} / {link(str(report.get('html_path') or ''), 'html')}</td>"
            "</tr>"
        )
        if report.get("review_strip"):
            images.append(str(report["review_strip"]))
        if report.get("last_frame"):
            images.append(str(report["last_frame"]))
    if not rows:
        rows.append("<tr><td colspan=\"4\" class=\"missing\">no handoff reports yet</td></tr>")
    return "\n".join(rows), images


def clip_rows(edit_plan: dict[str, Any] | None) -> str:
    if not edit_plan:
        return "<tr><td colspan=\"7\" class=\"missing\">missing analysis/edit-plan.json</td></tr>"
    rows = []
    for clip in edit_plan.get("clips", []):
        rows.append(
            "<tr>"
            f"<td>{html_escape(clip.get('clip'))}</td>"
            f"<td>{html_escape(clip.get('source'))}</td>"
            f"<td>{html_escape(clip.get('trim_in'))}</td>"
            f"<td>{html_escape(clip.get('trim_out'))}</td>"
            f"<td>{html_escape(clip.get('timeline_start'))}</td>"
            f"<td>{html_escape(clip.get('timeline_end'))}</td>"
            f"<td>{html_escape(clip.get('editor_notes'))}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def caption_summary(caption_plan: dict[str, Any] | None) -> str:
    if not caption_plan:
        return "<p class=\"missing\">missing analysis/caption-cues/chatcut-caption-plan.json</p>"
    captions = caption_plan.get("captions") or []
    if not captions:
        return "<p class=\"missing\">caption plan has no captions</p>"
    first = captions[0]
    last = captions[-1]
    return (
        f"<p>{len(captions)} captions, from "
        f"{html_escape(first.get('start'))}s to {html_escape(last.get('end'))}s.</p>"
    )


def build_sheet(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    manifest = load_json(run_dir / "analysis" / "manifest.json")
    edit_plan = load_json(run_dir / "analysis" / "edit-plan.json")
    caption_plan = load_json(run_dir / "analysis" / "caption-cues" / "chatcut-caption-plan.json")
    next_step = load_json(run_dir / "analysis" / "next-step.json")
    handoff_table, handoff_images = handoff_rows(run_dir)
    images_html = "\n".join(
        img(path, Path(path).name)
        for path in handoff_images
    )
    checks = [
        "opening product/sign readable when required",
        "joins have a motivated handoff or transition anchor",
        "no face, damaged hands, overlay text, fake UI, or burned-in captions",
        "edit plan uses accepted MP4 clips only",
        "caption plan exists before editable caption placement when captions are used",
        "final set/background stays consistent for ending extensions",
    ]
    check_html = "\n".join(f"<li>{html_escape(item)}</li>" for item in checks)
    mode = ""
    if manifest:
        video = manifest.get("video")
        if isinstance(video, dict):
            mode = str(video.get("mode") or "")
        mode = mode or str(manifest.get("video_mode") or "")
    next_reco = (next_step or {}).get("recommendation") or {}
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>QA Decision Sheet</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2933; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 8px; vertical-align: top; }}
    th {{ background: #f6f8fa; text-align: left; }}
    .missing {{ color: #b42318; font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    img {{ width: 100%; height: auto; border: 1px solid #d9e2ec; }}
    figure {{ margin: 0; }}
    figcaption {{ font-size: 12px; color: #52606d; word-break: break-all; }}
    code {{ white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>QA Decision Sheet</h1>
  <p><b>Generated:</b> {datetime.now(timezone.utc).isoformat()}</p>
  <p><b>Run:</b> {html_escape(run_dir)}</p>
  <p><b>Mode:</b> {html_escape(mode or "unknown")}</p>
  <h2>Next Step</h2>
  <p><b>{html_escape(next_reco.get("stage", "unknown"))}:</b> {html_escape(next_reco.get("action", ""))}</p>
  <p><code>{html_escape(next_reco.get("command", "run scripts/next_step.py first"))}</code></p>
  <h2>Required Checks</h2>
  <ul>{check_html}</ul>
  <h2>Handoffs</h2>
  <table><thead><tr><th>Handoff</th><th>Decision</th><th>Recommendation</th><th>Links</th></tr></thead><tbody>{handoff_table}</tbody></table>
  <h2>Edit Plan</h2>
  <p>{link("analysis/edit-plan.json", "edit-plan.json")} / {link("analysis/edit-plan.csv", "edit-plan.csv")}</p>
  <table><thead><tr><th>Clip</th><th>Source</th><th>In</th><th>Out</th><th>Timeline In</th><th>Timeline Out</th><th>Notes</th></tr></thead><tbody>{clip_rows(edit_plan)}</tbody></table>
  <h2>Captions</h2>
  {caption_summary(caption_plan)}
  <p>{link("analysis/caption-cues/chatcut-caption-plan.json", "chatcut-caption-plan.json")}</p>
  <h2>Visual References</h2>
  <div class="grid">{images_html or '<p class="missing">no handoff images yet</p>'}</div>
</body>
</html>
"""
    output = run_dir / "qa" / "decision-sheet.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    summary = {
        "decision_sheet": str(output),
        "mode": mode,
        "handoff_reports": len(list((run_dir / "qa" / "handoffs").glob("*/handoff-review.json"))),
        "edit_plan": bool(edit_plan),
        "caption_plan": bool(caption_plan),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build qa/decision-sheet.html.")
    parser.add_argument("run_dir", type=Path)
    return build_sheet(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
