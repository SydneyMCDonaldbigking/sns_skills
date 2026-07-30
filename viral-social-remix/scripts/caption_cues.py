"""Compile external caption cue JSON into editor-ready timeline files."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


OUTPUT_JSON_NAMES = {"timeline.json", "chatcut-caption-plan.json"}
DEFAULT_STYLE = (
    "editable centered white text with subtle dark stroke/shadow, no colored box"
)
CLIP_RE = re.compile(r"^clip-(\d+)$")


@dataclass(frozen=True)
class Cue:
    source_clip: str
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class ClipPlacement:
    source_clip: str
    trim_in: float
    trim_out: float
    timeline_start: float

    @property
    def duration(self) -> float:
        return self.trim_out - self.trim_in

    @property
    def timeline_end(self) -> float:
        return self.timeline_start + self.duration


def _die(message: str) -> None:
    raise SystemExit(f"caption_cues.py: {message}")


def parse_time(value: object) -> float:
    """Parse seconds or simple SRT-like times into seconds."""
    if isinstance(value, (int, float)):
        seconds = float(value)
    elif isinstance(value, str):
        text = value.strip().replace(",", ".")
        if not text:
            raise ValueError("empty time")
        if ":" in text:
            parts = [float(part) for part in text.split(":")]
            if len(parts) == 2:
                minutes, seconds_part = parts
                seconds = minutes * 60 + seconds_part
            elif len(parts) == 3:
                hours, minutes, seconds_part = parts
                seconds = hours * 3600 + minutes * 60 + seconds_part
            else:
                raise ValueError(f"unsupported time format: {value!r}")
        else:
            seconds = float(text)
    else:
        raise ValueError(f"unsupported time value: {value!r}")
    if seconds < 0:
        raise ValueError(f"time must be non-negative: {value!r}")
    return round(seconds, 3)


def parse_assignment(value: str, label: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"{label} must look like clip-01=value")
    name, raw = value.split("=", 1)
    name = name.strip()
    raw = raw.strip()
    if not name or not raw:
        raise argparse.ArgumentTypeError(f"{label} must look like clip-01=value")
    return name, raw


def parse_trim(value: str) -> tuple[str, tuple[float, float]]:
    name, raw = parse_assignment(value, "--trim")
    if ".." in raw:
        start_raw, end_raw = raw.split("..", 1)
    elif "," in raw:
        start_raw, end_raw = raw.split(",", 1)
    else:
        parts = raw.split(":")
        if len(parts) != 2:
            raise argparse.ArgumentTypeError(
                "--trim uses seconds, for example clip-01=0.25:5.70"
            )
        start_raw, end_raw = parts
    start = parse_time(start_raw)
    end = parse_time(end_raw)
    if end <= start:
        raise argparse.ArgumentTypeError("--trim end must be greater than start")
    return name, (start, end)


def parse_duration(value: str) -> tuple[str, float]:
    name, raw = parse_assignment(value, "--duration")
    duration = parse_time(raw)
    if duration <= 0:
        raise argparse.ArgumentTypeError("--duration must be greater than zero")
    return name, duration


def format_srt_time(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def round_time(value: float) -> float:
    return round(value + 0.0, 3)


def relpath(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path)


def sorted_clip_names(names: list[str]) -> list[str]:
    def key(name: str) -> tuple[int, int | str]:
        if name == "single-10s":
            return (0, 0)
        match = CLIP_RE.match(name)
        if match:
            return (1, int(match.group(1)))
        return (2, name)

    return sorted(names, key=key)


def default_duration(source_clip: str, cues: list[Cue]) -> float:
    if source_clip == "single-10s":
        return 10.0
    if CLIP_RE.match(source_clip):
        return 6.0
    if cues:
        return max(cue.end for cue in cues)
    return 0.0


def read_cue_file(path: Path) -> tuple[str, str, str, list[Cue]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    source_clip = str(data.get("source_clip") or path.stem)
    language = str(data.get("language") or "en")
    style = str(data.get("style") or DEFAULT_STYLE)
    raw_cues = data.get("cues")
    if not isinstance(raw_cues, list):
        _die(f"{path} must contain a cues array")

    cues: list[Cue] = []
    previous_end = -1.0
    for index, raw in enumerate(raw_cues, start=1):
        if not isinstance(raw, dict):
            _die(f"{path} cue {index} must be an object")
        try:
            start = parse_time(raw["start"])
            end = parse_time(raw["end"])
        except KeyError as exc:
            _die(f"{path} cue {index} missing {exc.args[0]!r}")
        except ValueError as exc:
            _die(f"{path} cue {index}: {exc}")
        if end <= start:
            _die(f"{path} cue {index} end must be greater than start")
        text = str(raw.get("text", "")).strip()
        if not text:
            _die(f"{path} cue {index} has empty text")
        if start < previous_end:
            _die(f"{path} cue {index} overlaps the previous cue")
        previous_end = end
        cues.append(Cue(source_clip=source_clip, start=start, end=end, text=text))
    return source_clip, language, style, cues


def write_srt(path: Path, cues: list[dict]) -> None:
    lines: list[str] = []
    for index, cue in enumerate(cues, start=1):
        lines.extend(
            [
                str(index),
                f"{format_srt_time(cue['start'])} --> {format_srt_time(cue['end'])}",
                str(cue["text"]),
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(path: Path, cues: list[dict]) -> None:
    fieldnames = ["index", "start", "end", "text", "source_clip", "source_start", "source_end"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, cue in enumerate(cues, start=1):
            writer.writerow(
                {
                    "index": index,
                    "start": cue["start"],
                    "end": cue["end"],
                    "text": cue["text"],
                    "source_clip": cue.get("source_clip", ""),
                    "source_start": cue.get("source_start", ""),
                    "source_end": cue.get("source_end", ""),
                }
            )


def build_timeline(
    cues_by_clip: dict[str, list[Cue]],
    order: list[str],
    trims: dict[str, tuple[float, float]],
    durations: dict[str, float],
    *,
    gap: float,
    timeline_start: float,
    min_duration: float,
) -> tuple[list[ClipPlacement], list[dict]]:
    placements: list[ClipPlacement] = []
    timeline_cues: list[dict] = []
    cursor = timeline_start

    for source_clip in order:
        cues = cues_by_clip.get(source_clip, [])
        duration = durations.get(source_clip, default_duration(source_clip, cues))
        if duration <= 0:
            _die(f"cannot infer duration for {source_clip}; pass --duration")
        trim_in, trim_out = trims.get(source_clip, (0.0, duration))
        if trim_out > duration:
            _die(f"{source_clip} trim out {trim_out} exceeds duration {duration}")
        placement = ClipPlacement(source_clip, trim_in, trim_out, cursor)
        placements.append(placement)

        for cue in cues:
            local_start = max(cue.start, trim_in)
            local_end = min(cue.end, trim_out)
            if local_end - local_start < min_duration:
                continue
            timeline_cues.append(
                {
                    "start": round_time(cursor + local_start - trim_in),
                    "end": round_time(cursor + local_end - trim_in),
                    "text": cue.text,
                    "source_clip": source_clip,
                    "source_start": round_time(local_start),
                    "source_end": round_time(local_end),
                }
            )
        cursor = placement.timeline_end + gap

    return placements, timeline_cues


def compile_cues(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    cue_dir = Path(args.cue_dir) if args.cue_dir else run_dir / "analysis" / "caption-cues"
    if not cue_dir.exists():
        _die(f"caption cue directory does not exist: {cue_dir}")

    cue_paths = [
        path
        for path in cue_dir.glob("*.json")
        if path.name not in OUTPUT_JSON_NAMES and not path.name.startswith(".")
    ]
    if not cue_paths:
        _die(f"no source cue JSON files found in {cue_dir}")

    requested_order = [item.strip() for item in args.order.split(",") if item.strip()] if args.order else None
    trims = dict(parse_trim(value) for value in args.trim)
    durations = dict(parse_duration(value) for value in args.duration)
    cues_by_clip: dict[str, list[Cue]] = {}
    source_files: dict[str, str] = {}
    languages: set[str] = set()
    styles: list[str] = []

    for path in sorted(cue_paths):
        source_clip, language, style, cues = read_cue_file(path)
        cues_by_clip[source_clip] = cues
        source_files[source_clip] = relpath(path, run_dir)
        languages.add(language)
        if style not in styles:
            styles.append(style)

    order = requested_order or sorted_clip_names(list(cues_by_clip))
    missing = [name for name in order if name not in cues_by_clip]
    if missing:
        _die(f"order references missing cue files: {', '.join(missing)}")

    placements, timeline_cues = build_timeline(
        cues_by_clip,
        order,
        trims,
        durations,
        gap=args.gap,
        timeline_start=args.timeline_start,
        min_duration=args.min_duration,
    )

    for source_clip, cues in cues_by_clip.items():
        clip_dicts = [
            {
                "start": cue.start,
                "end": cue.end,
                "text": cue.text,
                "source_clip": source_clip,
                "source_start": cue.start,
                "source_end": cue.end,
            }
            for cue in cues
        ]
        write_srt(cue_dir / f"{source_clip}.srt", clip_dicts)

    total_duration = 0.0
    if placements:
        total_duration = max(placement.timeline_end for placement in placements)

    language = languages.pop() if len(languages) == 1 else "mixed"
    style = styles[0] if styles else DEFAULT_STYLE
    timeline = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_run": str(run_dir),
        "timing_unit": "seconds",
        "timing_basis": "timeline-relative",
        "language": language,
        "style": style,
        "source_files": source_files,
        "clips": [
            {
                "source_clip": placement.source_clip,
                "trim_in": round_time(placement.trim_in),
                "trim_out": round_time(placement.trim_out),
                "timeline_start": round_time(placement.timeline_start),
                "timeline_end": round_time(placement.timeline_end),
            }
            for placement in placements
        ],
        "timeline": {
            "start": round_time(args.timeline_start),
            "duration": round_time(total_duration - args.timeline_start),
        },
        "cues": [
            {"index": index, **cue}
            for index, cue in enumerate(timeline_cues, start=1)
        ],
    }

    chatcut_plan = {
        "schema_version": 1,
        "kind": "chatcut-editable-caption-placement-plan",
        "timing_unit": "seconds",
        "style": {
            "placement": "center",
            "text_color": "white",
            "stroke_or_shadow": "subtle dark stroke/shadow",
            "box": "none",
        },
        "captions": timeline["cues"],
    }

    timeline_path = cue_dir / "timeline.json"
    chatcut_path = cue_dir / "chatcut-caption-plan.json"
    timeline_srt_path = cue_dir / "timeline.srt"
    timeline_csv_path = cue_dir / "timeline.csv"

    timeline_path.write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    chatcut_path.write_text(
        json.dumps(chatcut_plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_srt(timeline_srt_path, timeline_cues)
    write_csv(timeline_csv_path, timeline_cues)

    print(
        json.dumps(
            {
                "cue_dir": str(cue_dir),
                "clips": len(placements),
                "captions": len(timeline_cues),
                "outputs": [
                    str(timeline_path),
                    str(chatcut_path),
                    str(timeline_srt_path),
                    str(timeline_csv_path),
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compile analysis/caption-cues/*.json into per-clip SRT plus "
            "timeline JSON/SRT/CSV for editable caption placement."
        )
    )
    parser.add_argument("run_dir", help="Run directory containing analysis/caption-cues")
    parser.add_argument(
        "--cue-dir",
        help="Override cue directory. Defaults to RUN_DIR/analysis/caption-cues.",
    )
    parser.add_argument(
        "--order",
        help="Comma-separated clip order, e.g. clip-01,clip-02,clip-03.",
    )
    parser.add_argument(
        "--trim",
        action="append",
        default=[],
        metavar="CLIP=IN:OUT",
        help="Source trim in seconds, e.g. --trim clip-01=0.25:5.70. Repeat per clip.",
    )
    parser.add_argument(
        "--duration",
        action="append",
        default=[],
        metavar="CLIP=SECONDS",
        help="Override source duration when it cannot be inferred.",
    )
    parser.add_argument(
        "--gap",
        type=float,
        default=0.0,
        help="Timeline gap between placed clips in seconds. Default: 0.",
    )
    parser.add_argument(
        "--timeline-start",
        type=float,
        default=0.0,
        help="Timeline start offset in seconds. Default: 0.",
    )
    parser.add_argument(
        "--min-duration",
        type=float,
        default=0.25,
        help="Drop captions shorter than this after trim clipping. Default: 0.25.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.gap < 0:
        parser.error("--gap must be non-negative")
    if args.timeline_start < 0:
        parser.error("--timeline-start must be non-negative")
    if args.min_duration <= 0:
        parser.error("--min-duration must be greater than zero")
    return compile_cues(args)


if __name__ == "__main__":
    raise SystemExit(main())
