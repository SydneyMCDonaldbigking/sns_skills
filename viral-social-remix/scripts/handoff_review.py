"""Create deterministic handoff review artifacts between Seedance clips."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import video_qa


CLIP_RE = re.compile(r"^clip-(\d+)$")
DECISIONS = {"undecided", "use-last-frame", "transition-anchor", "retry"}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _rel(path: Path | None, base: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path)


def _clip_number(clip: str) -> int | None:
    match = CLIP_RE.match(clip)
    return int(match.group(1)) if match else None


def infer_next_clip(clip: str) -> str | None:
    number = _clip_number(clip)
    if number is None:
        return None
    return f"clip-{number + 1:02d}"


def default_video_path(run_dir: Path, clip: str) -> Path:
    return run_dir / "generated" / f"seedance-{clip}.mp4"


def default_last_frame_path(run_dir: Path, clip: str) -> Path:
    return run_dir / "generated" / f"seedance-{clip}-last-frame.png"


def motion_timestamps(duration: float, count: int, window: float) -> list[float]:
    if duration <= 0:
        return []
    count = max(3, count)
    end = max(0.02, duration - min(0.05, duration * 0.01))
    start = max(0.0, end - min(window, duration))
    if count == 1:
        return [round(end, 3)]
    step = (end - start) / (count - 1)
    return [round(start + index * step, 3) for index in range(count)]


def command_templates(run_dir: Path, clip: str, next_clip: str | None) -> dict[str, str]:
    python = "python"
    current_number = _clip_number(clip)
    next_number = _clip_number(next_clip or "") if next_clip else None
    templates = {
        "retry": (
            f"{python} scripts/run_seedance_video.py --run {run_dir} "
            f"--storyboard-group {current_number or 1} --force"
        ),
    }
    if next_number:
        templates.update(
            {
                "use-last-frame": (
                    f"{python} scripts/run_seedance_video.py --run {run_dir} "
                    f"--storyboard-group {next_number} --continue-from-last-frame"
                ),
                "transition-anchor": (
                    "Update analysis/page-prompts/"
                    f"page-{next_number:02d}.md from the handoff notes, generate "
                    f"generated/page-{next_number:02d}.png, then run "
                    f"{python} scripts/run_seedance_video.py --run {run_dir} "
                    f"--storyboard-group {next_number}"
                ),
            }
        )
    return templates


def write_next_prompt_draft(
    run_dir: Path,
    *,
    clip: str,
    next_clip: str | None,
    handoff_dir: Path,
) -> str | None:
    if not next_clip:
        return None
    source = run_dir / "analysis" / "seedance-prompts" / f"{next_clip}.md"
    if not source.is_file():
        return None
    target = (
        run_dir
        / "analysis"
        / "seedance-prompts"
        / "drafts"
        / f"{next_clip}-handoff-draft.md"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    base_prompt = source.read_text(encoding="utf-8")
    target.write_text(
        (
            f"# {next_clip} Handoff Draft\n\n"
            f"Use while {clip} is polling or immediately after {clip} returns. "
            "Fill only the two placeholders below after reviewing the returned "
            "last frame and final motion strip.\n\n"
            "OPENING_REFERENCE: <accepted previous last frame OR generated "
            "transition opening anchor>\n"
            "HANDOFF_MECHANISM: <match action / steam-lid occlusion / pour-object "
            "bridge / rack focus / plate move / texture insert>\n"
            f"HANDOFF_REVIEW: {handoff_dir.relative_to(run_dir).as_posix()}\n\n"
            "---\n\n"
            f"{base_prompt}"
        ),
        encoding="utf-8",
    )
    return _rel(target, run_dir)


def html_escape(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_html(path: Path, report: dict[str, Any], run_dir: Path) -> None:
    images: list[str] = []
    last_frame = report.get("last_frame")
    if last_frame:
        images.append(str(last_frame))
    strip = report.get("review_strip")
    if strip:
        images.append(str(strip))
    frames = report.get("last_motion_frames") or []
    images.extend(str(item) for item in frames)
    image_html = "\n".join(
        f'<figure><img src="../../../{html_escape(image)}"><figcaption>{html_escape(image)}</figcaption></figure>'
        for image in images
    )
    checks = "\n".join(
        f"<li>{html_escape(item)}</li>" for item in report.get("checks", [])
    )
    commands = "\n".join(
        f"<dt>{html_escape(key)}</dt><dd><code>{html_escape(value)}</code></dd>"
        for key, value in (report.get("commands") or {}).items()
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Handoff Review {html_escape(report.get("handoff_id"))}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2933; }}
    .meta, dl {{ background: #f6f8fa; padding: 12px; border-radius: 6px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    img {{ width: 100%; height: auto; border: 1px solid #d9e2ec; }}
    figure {{ margin: 0; }}
    figcaption {{ font-size: 12px; color: #52606d; word-break: break-all; }}
    code {{ white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Handoff Review {html_escape(report.get("handoff_id"))}</h1>
  <div class="meta">
    <p><b>Decision:</b> {html_escape(report.get("decision"))}</p>
    <p><b>Recommendation:</b> {html_escape(report.get("recommendation"))}</p>
    <p><b>Notes:</b> {html_escape(report.get("notes"))}</p>
  </div>
  <h2>Checks</h2>
  <ul>{checks}</ul>
  <h2>Next Commands</h2>
  <dl>{commands}</dl>
  <h2>Frames</h2>
  <div class="grid">{image_html}</div>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def update_manifest_handoff(run_dir: Path, report: dict[str, Any]) -> None:
    manifest_path = run_dir / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        return
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = data.setdefault("video_workflow", {})
    handoffs = workflow.setdefault("handoffs", {})
    handoffs[report["handoff_id"]] = {
        "status": "awaiting_decision" if report["decision"] == "undecided" else "decided",
        "decision": report["decision"],
        "report": report["report_path"],
        "html": report["html_path"],
        "recommendation": report["recommendation"],
        "created_at": report["created_at"],
    }
    history = workflow.setdefault("history", [])
    history.append(
        {
            "at": report["created_at"],
            "event": "handoff_review",
            "handoff": report["handoff_id"],
            "decision": report["decision"],
        }
    )
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_handoff_review(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    clip = args.clip
    next_clip = args.next_clip or infer_next_clip(clip)
    video = Path(args.video) if args.video else default_video_path(run_dir, clip)
    last_frame = (
        Path(args.last_frame)
        if args.last_frame
        else default_last_frame_path(run_dir, clip)
    )
    handoff_id = f"{clip}-to-{next_clip}" if next_clip else f"{clip}-final"
    handoff_dir = run_dir / "qa" / "handoffs" / handoff_id
    frames_dir = handoff_dir / "frames"
    handoff_dir.mkdir(parents=True, exist_ok=True)

    metadata: dict[str, Any] | None = None
    frame_paths: list[Path] = []
    strip_path: Path | None = None
    extraction_error = None
    if video.is_file():
        try:
            metadata = video_qa.probe_video(video)
            timestamps = motion_timestamps(
                float(metadata["duration"]),
                count=args.frames,
                window=args.window,
            )
            frame_paths = video_qa.extract_review_frames(
                video,
                frames_dir,
                timestamps=timestamps,
            )
            strip_path = video_qa.build_review_strip(
                frame_paths,
                handoff_dir / "last-motion-strip.jpg",
                timestamps=timestamps,
            )
        except Exception as exc:  # noqa: BLE001 - report, do not hide the run.
            extraction_error = f"{exc.__class__.__name__}: {exc}"

    checks = [
        "product or food state remains coherent",
        "hands, cookware, set, lighting, and camera angle can continue",
        "last second has a motivated bridge, not a dead endpoint",
        "no face, warped hands, generated overlay text, or damaged product",
        "later clips do not need the opening logo sign unless it is natural",
    ]
    if args.decision == "use-last-frame":
        recommendation = "Use the returned last frame directly as the next opening reference."
    elif args.decision == "transition-anchor":
        recommendation = "Generate a transition opening anchor before the next Seedance clip."
    elif args.decision == "retry":
        recommendation = "Retry the source clip before continuing."
    else:
        recommendation = (
            "Choose use-last-frame, transition-anchor, or retry after reading the "
            "strip and checks."
        )

    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "handoff_id": handoff_id,
        "source_clip": clip,
        "next_clip": next_clip,
        "decision": args.decision,
        "recommendation": recommendation,
        "notes": args.notes or "",
        "video": _rel(video, run_dir) if video.is_file() else None,
        "last_frame": _rel(last_frame, run_dir) if last_frame.is_file() else None,
        "video_metadata": metadata,
        "last_motion_frames": [_rel(path, run_dir) for path in frame_paths],
        "review_strip": _rel(strip_path, run_dir) if strip_path else None,
        "extraction_error": extraction_error,
        "checks": checks,
        "commands": command_templates(run_dir, clip, next_clip),
    }
    draft = write_next_prompt_draft(
        run_dir,
        clip=clip,
        next_clip=next_clip,
        handoff_dir=handoff_dir,
    )
    report["next_prompt_draft"] = draft

    report_path = handoff_dir / "handoff-review.json"
    html_path = handoff_dir / "index.html"
    report["report_path"] = _rel(report_path, run_dir)
    report["html_path"] = _rel(html_path, run_dir)
    _write_json(report_path, report)
    write_html(html_path, report, run_dir)
    update_manifest_handoff(run_dir, report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract final motion frames and create a Seedance handoff report."
    )
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--clip", required=True, help="Source clip id, e.g. clip-01.")
    parser.add_argument("--next-clip", help="Next clip id. Defaults to clip+1.")
    parser.add_argument("--video", help="Override source MP4 path.")
    parser.add_argument("--last-frame", help="Override returned last-frame path.")
    parser.add_argument("--frames", type=int, default=12)
    parser.add_argument("--window", type=float, default=1.2)
    parser.add_argument("--notes", default="")
    parser.add_argument("--decision", choices=sorted(DECISIONS), default="undecided")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.frames < 3:
        parser.error("--frames must be at least 3")
    if args.window <= 0:
        parser.error("--window must be greater than 0")
    return create_handoff_review(args)


if __name__ == "__main__":
    raise SystemExit(main())
