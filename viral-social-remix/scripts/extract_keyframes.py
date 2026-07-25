"""Extract video candidates and selected keyframes with ffmpeg."""

import argparse
import json
import subprocess
from pathlib import Path


def _run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def duration(video: str | Path) -> float:
    result = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(video),
        ]
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def candidate_timestamps(seconds: float, count: int = 18) -> list[float]:
    if seconds <= 0 or count < 2:
        raise ValueError("Video duration must be positive and count at least 2")
    margin = min(1.0, seconds * 0.05)
    start, end = margin, seconds - margin
    step = (end - start) / (count - 1)
    return [round(start + index * step, 3) for index in range(count)]


def export(
    video: str | Path,
    timestamps: list[float],
    output: str | Path,
    prefix: str,
) -> list[str]:
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, timestamp in enumerate(timestamps, 1):
        path = target / f"{prefix}-{index:02d}.jpg"
        _run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(timestamp),
                "-i",
                str(video),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(path),
            ]
        )
        paths.append(str(path))
    return paths


def export_candidates(
    video: str | Path, output: str | Path, count: int = 18
) -> list[str]:
    return export(
        video,
        candidate_timestamps(duration(video), count),
        output,
        "candidate",
    )


def export_selected(
    video: str | Path, timestamps: list[float], output: str | Path
) -> list[str]:
    if len(timestamps) != 9:
        raise ValueError("Video storyboards require exactly 9 timestamps")
    return export(video, timestamps, output, "keyframe")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export candidate or selected video keyframes with FFmpeg."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    candidates = subparsers.add_parser(
        "candidates", help="Export evenly spaced frames for narrative review."
    )
    candidates.add_argument("video", type=Path)
    candidates.add_argument("output", type=Path)
    candidates.add_argument("--count", type=int, default=18)

    selected = subparsers.add_parser(
        "selected", help="Export exactly nine narratively selected timestamps."
    )
    selected.add_argument("video", type=Path)
    selected.add_argument("output", type=Path)
    selected.add_argument("--timestamps", type=float, nargs=9, required=True)

    args = parser.parse_args()
    if args.command == "candidates":
        paths = export_candidates(args.video, args.output, args.count)
    else:
        paths = export_selected(args.video, args.timestamps, args.output)
    print(json.dumps({"exported": paths}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
