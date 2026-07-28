"""Probe generated video, build a review strip, and record QA gate state."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from math import ceil
from pathlib import Path
import subprocess
import sys
from typing import Any

from PIL import Image, ImageDraw, ImageFont


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import manifest


RESOLUTION_DIMENSIONS = {
    ("9:16", "1080p"): (1080, 1920),
    ("9:16", "720p"): (720, 1280),
    ("9:16", "480p"): (480, 854),
    ("16:9", "1080p"): (1920, 1080),
    ("16:9", "720p"): (1280, 720),
    ("16:9", "480p"): (854, 480),
    ("1:1", "1080p"): (1080, 1080),
    ("1:1", "720p"): (720, 720),
    ("1:1", "480p"): (480, 480),
}


class VideoQAError(RuntimeError):
    """Raised when video QA cannot run or change state."""


def _run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )


def _fraction(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    if "/" not in value:
        return float(value)
    numerator, denominator = value.split("/", 1)
    parsed_denominator = float(denominator)
    if parsed_denominator == 0:
        return None
    return float(numerator) / parsed_denominator


def probe_video(
    video: str | Path,
    *,
    run_command=None,
) -> dict[str, Any]:
    path = Path(video)
    if not path.is_file():
        raise VideoQAError(f"Missing video for QA: {path}")
    run_command = run_command or _run
    try:
        result = run_command(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate",
                "-of",
                "json",
                str(path),
            ]
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise VideoQAError(f"ffprobe failed for {path}: {exc}") from exc
    payload = json.loads(result.stdout)
    streams = payload.get("streams") or []
    video_stream = next(
        (
            stream
            for stream in streams
            if stream.get("codec_type") == "video"
        ),
        None,
    )
    if not isinstance(video_stream, dict):
        raise VideoQAError(f"No video stream found in {path}")
    audio_streams = [
        stream for stream in streams if stream.get("codec_type") == "audio"
    ]
    duration = float((payload.get("format") or {}).get("duration") or 0)
    return {
        "path": str(path),
        "duration": duration,
        "width": int(video_stream.get("width") or 0),
        "height": int(video_stream.get("height") or 0),
        "fps": _fraction(
            video_stream.get("avg_frame_rate")
            or video_stream.get("r_frame_rate")
        ),
        "video_codec": video_stream.get("codec_name"),
        "audio_stream_count": len(audio_streams),
        "audio_codecs": [
            stream.get("codec_name") for stream in audio_streams
        ],
    }


def validate_probe(
    metadata: dict[str, Any],
    *,
    ratio: str | None = None,
    resolution: str | None = None,
    expected_duration: float | None = None,
    duration_tolerance: float | None = None,
    expect_audio: bool | None = None,
) -> list[str]:
    errors: list[str] = []
    expected_dimensions = RESOLUTION_DIMENSIONS.get(
        (str(ratio), str(resolution).lower())
    )
    if expected_dimensions and (
        metadata["width"],
        metadata["height"],
    ) != expected_dimensions:
        errors.append(
            f"expected {expected_dimensions[0]}x{expected_dimensions[1]}, got "
            f"{metadata['width']}x{metadata['height']}"
        )
    if expected_duration is not None:
        tolerance = (
            float(duration_tolerance)
            if duration_tolerance is not None
            else max(0.5, float(expected_duration) * 0.05)
        )
        if abs(float(metadata["duration"]) - float(expected_duration)) > tolerance:
            errors.append(
                f"expected duration {expected_duration:.3f}s +/- {tolerance:.3f}s, "
                f"got {float(metadata['duration']):.3f}s"
            )
    if expect_audio is True and metadata["audio_stream_count"] < 1:
        errors.append("expected an audio stream, found none")
    if expect_audio is False and metadata["audio_stream_count"] > 0:
        errors.append(
            f"expected no audio stream, found {metadata['audio_stream_count']}"
        )
    return errors


def review_timestamps(duration: float, count: int = 5) -> list[float]:
    if duration <= 0:
        raise VideoQAError("Video duration must be greater than zero")
    if count < 3:
        raise VideoQAError("Review strip needs at least three frames")
    start = min(0.1, duration * 0.02)
    end = max(start, duration - min(0.1, duration * 0.02))
    step = (end - start) / (count - 1)
    return [round(start + index * step, 3) for index in range(count)]


def extract_review_frames(
    video: str | Path,
    output_dir: str | Path,
    *,
    timestamps: list[float],
    run_command=None,
) -> list[Path]:
    run_command = run_command or _run
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for index, timestamp in enumerate(timestamps, 1):
        output = target / f"review-{index:02d}-{timestamp:.3f}s.jpg"
        try:
            run_command(
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
                    str(output),
                ]
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise VideoQAError(
                f"ffmpeg failed while extracting {timestamp:.3f}s: {exc}"
            ) from exc
        outputs.append(output)
    return outputs


def build_review_strip(
    frames: list[str | Path],
    output: str | Path,
    *,
    timestamps: list[float],
) -> Path:
    if not frames or len(frames) != len(timestamps):
        raise VideoQAError("Review strip needs one timestamp per frame")
    thumb = (270, 480)
    label_height = 36
    columns = min(5, len(frames))
    rows = ceil(len(frames) / columns)
    canvas = Image.new(
        "RGB",
        (columns * thumb[0], rows * (thumb[1] + label_height)),
        "#111111",
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=18)
    for index, (frame, timestamp) in enumerate(zip(frames, timestamps)):
        with Image.open(frame) as source:
            image = source.convert("RGB")
            image.thumbnail(thumb, Image.Resampling.LANCZOS)
        x = (index % columns) * thumb[0]
        y = (index // columns) * (thumb[1] + label_height)
        paste_x = x + (thumb[0] - image.width) // 2
        paste_y = y + (thumb[1] - image.height) // 2
        canvas.paste(image, (paste_x, paste_y))
        draw.text(
            (x + 10, y + thumb[1] + 8),
            f"{timestamp:.3f}s",
            fill="white",
            font=font,
        )
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target)
    return target


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _update_workflow(
    run_dir: Path,
    *,
    status: str,
    visual_qa: str | None = None,
    export_qa: str | None = None,
    reason: str | None = None,
) -> None:
    manifest_path = run_dir / "analysis" / "manifest.json"
    data = manifest.load(manifest_path)
    workflow = data.get("video_workflow")
    workflow = workflow if isinstance(workflow, dict) else {}
    history = workflow.get("history")
    history = history if isinstance(history, list) else []
    event = {
        "status": status,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    if reason:
        event["reason"] = reason
    history.append(event)
    workflow.update({"status": status, "history": history})
    if visual_qa is not None:
        workflow["visual_qa"] = visual_qa
    if export_qa is not None:
        workflow["export_qa"] = export_qa
    data["video_workflow"] = workflow
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _run_video_path(run_dir: Path, data: dict, video: str | Path | None) -> Path:
    if video:
        path = Path(video)
        return path if path.is_absolute() else run_dir / path
    generation = data.get("video_generation")
    generation = generation if isinstance(generation, dict) else {}
    output = generation.get("output")
    if not output:
        raise VideoQAError(
            "Manifest video_generation.output is missing; pass --video"
        )
    return run_dir / str(output)


def prepare_review(
    run_dir: str | Path,
    *,
    video: str | Path | None = None,
    frame_count: int = 5,
    extract_frames: bool = True,
    run_command=None,
) -> dict[str, Any]:
    run = Path(run_dir).resolve()
    manifest_path = run / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        raise VideoQAError(f"Missing manifest: {manifest_path}")
    data = manifest.load(manifest_path)
    video_path = _run_video_path(run, data, video)
    metadata = probe_video(video_path, run_command=run_command)
    generation = data.get("video_generation")
    generation = generation if isinstance(generation, dict) else {}
    options = generation.get("generation")
    options = options if isinstance(options, dict) else {}
    errors = validate_probe(
        metadata,
        ratio=options.get("ratio"),
        resolution=options.get("resolution"),
        expected_duration=options.get("duration"),
        expect_audio=options.get("generate_audio"),
    )

    timestamps = review_timestamps(metadata["duration"], frame_count)
    frame_paths: list[Path] = []
    strip_path: Path | None = None
    if extract_frames:
        frame_paths = extract_review_frames(
            video_path,
            run / "qa" / "video-frames",
            timestamps=timestamps,
            run_command=run_command,
        )
        strip_path = build_review_strip(
            frame_paths,
            run / "qa" / "video-review-strip.jpg",
            timestamps=timestamps,
        )

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "metadata_failed" if errors else "awaiting_human_review",
        "valid_metadata": not errors,
        "errors": errors,
        "metadata": metadata,
        "timestamps": timestamps,
        "frames": [
            path.relative_to(run).as_posix() for path in frame_paths
        ],
        "review_strip": (
            strip_path.relative_to(run).as_posix() if strip_path else None
        ),
        "human_checks": [
            "no subtitles, title cards, labels, watermarks, or extra logos",
            "product/package appearance matches references",
            "food state and physics progress plausibly",
            "camera and background remain continuous",
            "clip start/end and any continuation join are usable",
        ],
    }
    _write_json(run / "qa" / "video-visual-review.json", report)
    _update_workflow(
        run,
        status=report["status"],
        visual_qa=report["status"],
    )
    return report


def set_review_decision(
    run_dir: str | Path,
    *,
    decision: str,
    reason: str | None = None,
) -> dict[str, Any]:
    run = Path(run_dir).resolve()
    report_path = run / "qa" / "video-visual-review.json"
    if not report_path.is_file():
        raise VideoQAError("Run prepare before recording a visual QA decision")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if decision == "passed" and not report.get("valid_metadata"):
        raise VideoQAError("Cannot pass visual QA while metadata validation fails")
    if decision == "failed" and not reason:
        raise VideoQAError("A failed visual QA decision requires --reason")
    report["status"] = decision
    report["decision_at"] = datetime.now(timezone.utc).isoformat()
    report["reason"] = reason
    _write_json(report_path, report)
    workflow_status = "visual_qa_passed" if decision == "passed" else "visual_qa_failed"
    _update_workflow(
        run,
        status=workflow_status,
        visual_qa=decision,
        reason=reason,
    )
    return report


def _require_visual_qa(data: dict[str, Any]) -> None:
    workflow = data.get("video_workflow")
    workflow = workflow if isinstance(workflow, dict) else {}
    if workflow.get("visual_qa") != "passed":
        raise VideoQAError(
            "Export QA requires video_workflow.visual_qa to be passed first"
        )


def prepare_export_review(
    run_dir: str | Path,
    *,
    video: str | Path,
    frame_count: int = 5,
    extract_frames: bool = True,
    expected_duration: float | None = None,
    expect_audio: bool | None = None,
    run_command=None,
) -> dict[str, Any]:
    run = Path(run_dir).resolve()
    manifest_path = run / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        raise VideoQAError(f"Missing manifest: {manifest_path}")
    data = manifest.load(manifest_path)
    _require_visual_qa(data)

    video_path = Path(video)
    if not video_path.is_absolute():
        video_path = run / video_path
    metadata = probe_video(video_path, run_command=run_command)
    video_section = data.get("video")
    video_section = video_section if isinstance(video_section, dict) else {}
    delivery = video_section.get("delivery")
    delivery = delivery if isinstance(delivery, dict) else {}
    generation = video_section.get("generation")
    generation = generation if isinstance(generation, dict) else {}
    ratio = delivery.get("ratio") or generation.get("ratio")
    resolution = delivery.get("resolution") or generation.get("resolution")
    configured_duration = (
        expected_duration
        if expected_duration is not None
        else delivery.get("duration")
    )
    configured_audio = (
        expect_audio
        if expect_audio is not None
        else delivery.get("expect_audio")
    )
    errors = validate_probe(
        metadata,
        ratio=ratio,
        resolution=resolution,
        expected_duration=(
            float(configured_duration)
            if configured_duration is not None
            else None
        ),
        expect_audio=(
            bool(configured_audio)
            if configured_audio is not None
            else None
        ),
    )

    timestamps = review_timestamps(metadata["duration"], frame_count)
    frame_paths: list[Path] = []
    strip_path: Path | None = None
    if extract_frames:
        frame_paths = extract_review_frames(
            video_path,
            run / "qa" / "export-frames",
            timestamps=timestamps,
            run_command=run_command,
        )
        strip_path = build_review_strip(
            frame_paths,
            run / "qa" / "export-review-strip.jpg",
            timestamps=timestamps,
        )
    status = "metadata_failed" if errors else "awaiting_human_review"
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "valid_metadata": not errors,
        "errors": errors,
        "metadata": metadata,
        "expected": {
            "ratio": ratio,
            "resolution": resolution,
            "duration": configured_duration,
            "expect_audio": configured_audio,
        },
        "timestamps": timestamps,
        "frames": [
            path.relative_to(run).as_posix() for path in frame_paths
        ],
        "review_strip": (
            strip_path.relative_to(run).as_posix() if strip_path else None
        ),
        "human_checks": [
            "no unintended black frames, frozen joins, gaps, or audio tail",
            "editable text and graphics stay inside platform safe areas",
            "brand treatment matches the declared manifest strategy",
            "music, voice, and effects are balanced without clipping",
            "the final frame and ending duration feel intentional",
            "no provider watermark, accidental logo, or hidden draft element",
        ],
    }
    report_path = run / "qa" / "export-review.json"
    _write_json(report_path, report)
    _update_workflow(
        run,
        status=(
            "export_metadata_failed"
            if errors
            else "export_qa_awaiting_human_review"
        ),
        export_qa=status,
    )
    return report


def set_export_decision(
    run_dir: str | Path,
    *,
    decision: str,
    reason: str | None = None,
) -> dict[str, Any]:
    run = Path(run_dir).resolve()
    report_path = run / "qa" / "export-review.json"
    if not report_path.is_file():
        raise VideoQAError(
            "Run prepare-export before recording an export QA decision"
        )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if decision == "passed" and not report.get("valid_metadata"):
        raise VideoQAError(
            "Cannot pass export QA while metadata validation fails"
        )
    if decision == "failed" and not reason:
        raise VideoQAError("A failed export QA decision requires --reason")
    report["status"] = decision
    report["decision_at"] = datetime.now(timezone.utc).isoformat()
    report["reason"] = reason
    _write_json(report_path, report)
    _update_workflow(
        run,
        status=(
            "export_qa_passed"
            if decision == "passed"
            else "export_qa_failed"
        ),
        export_qa=decision,
        reason=reason,
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe Seedance/ChatCut video and manage the visual QA gate."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("run_dir", type=Path)
    prepare.add_argument("--video")
    prepare.add_argument("--frame-count", type=int, default=5)
    prepare.add_argument("--no-extract-frames", action="store_true")

    approve = subparsers.add_parser("approve")
    approve.add_argument("run_dir", type=Path)

    reject = subparsers.add_parser("reject")
    reject.add_argument("run_dir", type=Path)
    reject.add_argument("--reason", required=True)

    prepare_export = subparsers.add_parser("prepare-export")
    prepare_export.add_argument("run_dir", type=Path)
    prepare_export.add_argument("--video", required=True)
    prepare_export.add_argument("--frame-count", type=int, default=5)
    prepare_export.add_argument("--no-extract-frames", action="store_true")
    prepare_export.add_argument("--expected-duration", type=float)
    export_audio = prepare_export.add_mutually_exclusive_group()
    export_audio.add_argument(
        "--expect-audio",
        dest="expect_audio",
        action="store_true",
        default=None,
    )
    export_audio.add_argument(
        "--expect-no-audio",
        dest="expect_audio",
        action="store_false",
    )

    approve_export = subparsers.add_parser("approve-export")
    approve_export.add_argument("run_dir", type=Path)

    reject_export = subparsers.add_parser("reject-export")
    reject_export.add_argument("run_dir", type=Path)
    reject_export.add_argument("--reason", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare_review(
                args.run_dir,
                video=args.video,
                frame_count=args.frame_count,
                extract_frames=not args.no_extract_frames,
            )
            code = 0 if result["valid_metadata"] else 1
        elif args.command == "approve":
            result = set_review_decision(args.run_dir, decision="passed")
            code = 0
        elif args.command == "reject":
            result = set_review_decision(
                args.run_dir,
                decision="failed",
                reason=args.reason,
            )
            code = 1
        elif args.command == "prepare-export":
            result = prepare_export_review(
                args.run_dir,
                video=args.video,
                frame_count=args.frame_count,
                extract_frames=not args.no_extract_frames,
                expected_duration=args.expected_duration,
                expect_audio=args.expect_audio,
            )
            code = 0 if result["valid_metadata"] else 1
        elif args.command == "approve-export":
            result = set_export_decision(
                args.run_dir,
                decision="passed",
            )
            code = 0
        else:
            result = set_export_decision(
                args.run_dir,
                decision="failed",
                reason=args.reason,
            )
            code = 1
    except VideoQAError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
