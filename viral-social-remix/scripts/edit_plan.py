"""Build an editor-ready cut plan from accepted generated clips."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import video_qa


def parse_time(value: str | float | int) -> float:
    if isinstance(value, (float, int)):
        seconds = float(value)
    else:
        text = str(value).strip().replace(",", ".")
        if ":" in text:
            parts = [float(part) for part in text.split(":")]
            if len(parts) == 2:
                seconds = parts[0] * 60 + parts[1]
            elif len(parts) == 3:
                seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
            else:
                raise ValueError(f"unsupported time: {value}")
        else:
            seconds = float(text)
    if seconds < 0:
        raise ValueError("time must be non-negative")
    return round(seconds, 3)


def parse_assignment(value: str, label: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"{label} must look like clip-01=value")
    key, raw = value.split("=", 1)
    key = key.strip()
    raw = raw.strip()
    if not key or not raw:
        raise argparse.ArgumentTypeError(f"{label} must look like clip-01=value")
    return key, raw


def parse_trim(value: str) -> tuple[str, tuple[float, float]]:
    clip, raw = parse_assignment(value, "--trim")
    if ".." in raw:
        start_raw, end_raw = raw.split("..", 1)
    elif "," in raw:
        start_raw, end_raw = raw.split(",", 1)
    else:
        parts = raw.split(":")
        if len(parts) != 2:
            raise argparse.ArgumentTypeError("--trim example: clip-01=0.25:5.70")
        start_raw, end_raw = parts
    start = parse_time(start_raw)
    end = parse_time(end_raw)
    if end <= start:
        raise argparse.ArgumentTypeError("--trim end must be greater than start")
    return clip, (start, end)


def parse_clip_path(value: str) -> tuple[str, Path]:
    clip, raw = parse_assignment(value, "--clip")
    return clip, Path(raw)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "clip",
        "source",
        "trim_in",
        "trim_out",
        "timeline_start",
        "timeline_end",
        "duration",
        "editor_notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def rel(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path)


def load_manifest(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / "analysis" / "manifest.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def infer_clip_paths(run_dir: Path, manifest: dict[str, Any] | None) -> dict[str, Path]:
    mode = ""
    if manifest:
        video = manifest.get("video")
        if isinstance(video, dict):
            mode = str(video.get("mode") or "")
        mode = mode or str(manifest.get("video_mode") or "")
    if mode == "single-10s-commercial":
        return {"single-10s": run_dir / "generated" / "seedance-video.mp4"}
    paths = {
        f"clip-{index:02d}": run_dir / "generated" / f"seedance-clip-{index:02d}.mp4"
        for index in range(1, 4)
    }
    return {clip: path for clip, path in paths.items() if path.is_file() or mode}


def default_editor_notes(clip: str, first: bool, last: bool) -> str:
    if first and last:
        return "trim weak start/end, add subtle push-in or pull-back only if useful"
    if first:
        return "trim weak start, keep product hook readable, bridge into next clip"
    if last:
        return "trim awkward ending, use strongest texture/hero moment, settle cleanly"
    return "trim dead air, punch in on texture/steam/pour, preserve planned handoff"


def build_edit_plan(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    manifest = load_manifest(run_dir)
    clip_paths = infer_clip_paths(run_dir, manifest)
    clip_paths.update(dict(parse_clip_path(value) for value in args.clip))
    trims = dict(parse_trim(value) for value in args.trim)
    if not clip_paths:
        raise SystemExit("edit_plan.py: no generated clips found; pass --clip clip-01=path")

    rows: list[dict[str, Any]] = []
    cursor = args.timeline_start
    ordered = sorted(clip_paths)
    for index, clip in enumerate(ordered):
        path = clip_paths[clip]
        metadata = None
        duration = 6.0 if clip.startswith("clip-") else 10.0
        if path.is_file():
            try:
                metadata = video_qa.probe_video(path)
                duration = round(float(metadata["duration"]), 3)
            except Exception as exc:  # noqa: BLE001 - keep plan usable.
                metadata = {"probe_error": f"{exc.__class__.__name__}: {exc}"}
        trim_in, trim_out = trims.get(clip, (0.0, duration))
        if trim_out > duration:
            raise SystemExit(
                f"edit_plan.py: {clip} trim_out {trim_out} exceeds duration {duration}"
            )
        clip_duration = round(trim_out - trim_in, 3)
        if clip_duration <= 0:
            raise SystemExit(f"edit_plan.py: {clip} trim leaves no duration")
        first = index == 0
        last = index == len(ordered) - 1
        rows.append(
            {
                "clip": clip,
                "source": rel(path, run_dir),
                "metadata": metadata,
                "trim_in": trim_in,
                "trim_out": trim_out,
                "timeline_start": round(cursor, 3),
                "timeline_end": round(cursor + clip_duration, 3),
                "duration": clip_duration,
                "editor_notes": default_editor_notes(clip, first, last),
            }
        )
        cursor += clip_duration + args.gap

    transitions = []
    for left, right in zip(rows, rows[1:]):
        transitions.append(
            {
                "from": left["clip"],
                "to": right["clip"],
                "at": left["timeline_end"],
                "preferred": "match cut, steam/lid/object wipe, or very short dissolve only if the handoff supports it",
            }
        )

    caption_plan = run_dir / "analysis" / "caption-cues" / "chatcut-caption-plan.json"
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "timing_unit": "seconds",
        "timeline": {
            "start": args.timeline_start,
            "duration": round(max(row["timeline_end"] for row in rows) - args.timeline_start, 3),
            "gap": args.gap,
        },
        "clips": rows,
        "transitions": transitions,
        "caption_plan": rel(caption_plan, run_dir) if caption_plan.is_file() else None,
        "chatcut_instructions": {
            "import": "accepted MP4 clips only; do not import opening frames, last frames, anchors, or QA images",
            "style": "natural edit duration, split/trim/punch-in/reframe, no cooking SFX by default",
            "captions": "run scripts/caption_cues.py with final trims before placing editable captions",
        },
    }
    output = run_dir / "analysis" / "edit-plan.json"
    csv_output = run_dir / "analysis" / "edit-plan.csv"
    write_json(output, payload)
    write_csv(csv_output, rows)
    print(
        json.dumps(
            {
                "edit_plan": str(output),
                "csv": str(csv_output),
                "clips": len(rows),
                "duration": payload["timeline"]["duration"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build analysis/edit-plan.json for ChatCut.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--clip", action="append", default=[], metavar="CLIP=PATH")
    parser.add_argument("--trim", action="append", default=[], metavar="CLIP=IN:OUT")
    parser.add_argument("--gap", type=float, default=0.0)
    parser.add_argument("--timeline-start", type=float, default=0.0)
    args = parser.parse_args(argv)
    if args.gap < 0:
        parser.error("--gap must be non-negative")
    if args.timeline_start < 0:
        parser.error("--timeline-start must be non-negative")
    return build_edit_plan(args)


if __name__ == "__main__":
    raise SystemExit(main())
