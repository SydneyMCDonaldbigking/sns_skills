import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image
import pytest

from viral_social_test_loader import load_script


manifest = load_script("manifest")
video_qa = load_script("video_qa")


def _prepared_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "output" / "run"
    analysis = run_dir / "analysis"
    generated = run_dir / "generated"
    analysis.mkdir(parents=True)
    generated.mkdir(parents=True)
    (generated / "seedance-video.mp4").write_bytes(b"fake video")
    manifest.create(
        analysis / "manifest.json",
        "vertical-video",
        [],
    )
    data = manifest.load(analysis / "manifest.json")
    data["video_generation"] = {
        "status": "generated",
        "output": "generated/seedance-video.mp4",
        "generation": {
            "ratio": "9:16",
            "duration": 5,
            "resolution": "1080p",
            "generate_audio": False,
        },
    }
    data["video_workflow"] = {
        "status": "generated",
        "visual_qa": "not_started",
        "history": [],
    }
    (analysis / "manifest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return run_dir


def _ffprobe_result(
    *,
    duration: float = 5.0,
    width: int = 1080,
    height: int = 1920,
    audio: bool = False,
):
    streams = [
        {
            "index": 0,
            "codec_type": "video",
            "codec_name": "h264",
            "width": width,
            "height": height,
            "avg_frame_rate": "30/1",
        }
    ]
    if audio:
        streams.append(
            {
                "index": 1,
                "codec_type": "audio",
                "codec_name": "aac",
            }
        )
    return SimpleNamespace(
        stdout=json.dumps(
            {
                "format": {"duration": str(duration)},
                "streams": streams,
            }
        )
    )


def test_prepare_review_records_metadata_and_waits_for_human_approval(tmp_path):
    run_dir = _prepared_run(tmp_path)

    report = video_qa.prepare_review(
        run_dir,
        extract_frames=False,
        run_command=lambda _command: _ffprobe_result(),
    )

    assert report["status"] == "awaiting_human_review"
    assert report["valid_metadata"] is True
    assert report["metadata"]["fps"] == 30
    assert len(report["timestamps"]) == 5
    stored = json.loads(
        (run_dir / "qa" / "video-visual-review.json").read_text(
            encoding="utf-8"
        )
    )
    assert stored["human_checks"]
    data = manifest.load(run_dir / "analysis" / "manifest.json")
    assert data["video_workflow"]["status"] == "awaiting_human_review"
    assert data["video_workflow"]["visual_qa"] == "awaiting_human_review"


def test_review_can_pass_only_after_metadata_validation(tmp_path):
    run_dir = _prepared_run(tmp_path)
    video_qa.prepare_review(
        run_dir,
        extract_frames=False,
        run_command=lambda _command: _ffprobe_result(),
    )

    report = video_qa.set_review_decision(
        run_dir,
        decision="passed",
    )

    assert report["status"] == "passed"
    data = manifest.load(run_dir / "analysis" / "manifest.json")
    assert data["video_workflow"]["status"] == "visual_qa_passed"
    assert data["video_workflow"]["visual_qa"] == "passed"


def test_metadata_failure_blocks_approval(tmp_path):
    run_dir = _prepared_run(tmp_path)
    report = video_qa.prepare_review(
        run_dir,
        extract_frames=False,
        run_command=lambda _command: _ffprobe_result(
            duration=7,
            width=720,
            height=1280,
            audio=True,
        ),
    )

    assert report["status"] == "metadata_failed"
    assert len(report["errors"]) == 3
    with pytest.raises(video_qa.VideoQAError, match="metadata validation"):
        video_qa.set_review_decision(run_dir, decision="passed")


def test_rejection_requires_and_records_a_reason(tmp_path):
    run_dir = _prepared_run(tmp_path)
    video_qa.prepare_review(
        run_dir,
        extract_frames=False,
        run_command=lambda _command: _ffprobe_result(),
    )

    with pytest.raises(video_qa.VideoQAError, match="requires --reason"):
        video_qa.set_review_decision(run_dir, decision="failed")

    report = video_qa.set_review_decision(
        run_dir,
        decision="failed",
        reason="package drifts between the middle and final shot",
    )
    assert report["status"] == "failed"
    assert report["reason"].startswith("package drifts")


def test_review_strip_has_one_labelled_panel_per_frame(tmp_path):
    frames = []
    timestamps = [0.1, 1.5, 2.9]
    for index, colour in enumerate(["red", "green", "blue"], 1):
        frame = tmp_path / f"frame-{index}.jpg"
        Image.new("RGB", (1080, 1920), colour).save(frame)
        frames.append(frame)

    output = video_qa.build_review_strip(
        frames,
        tmp_path / "review-strip.jpg",
        timestamps=timestamps,
    )

    assert output.is_file()
    with Image.open(output) as image:
        assert image.size == (810, 516)


def test_export_review_requires_visual_approval(tmp_path):
    run_dir = _prepared_run(tmp_path)
    export = run_dir / "generated" / "final-export.mp4"
    export.write_bytes(b"fake export")

    with pytest.raises(video_qa.VideoQAError, match="visual_qa"):
        video_qa.prepare_export_review(
            run_dir,
            video=export,
            extract_frames=False,
            run_command=lambda _command: _ffprobe_result(),
        )


def test_export_review_and_approval_close_the_workflow(tmp_path):
    run_dir = _prepared_run(tmp_path)
    video_qa.prepare_review(
        run_dir,
        extract_frames=False,
        run_command=lambda _command: _ffprobe_result(),
    )
    video_qa.set_review_decision(run_dir, decision="passed")
    manifest_path = run_dir / "analysis" / "manifest.json"
    data = manifest.load(manifest_path)
    data["video"] = {
        "delivery": {
            "ratio": "9:16",
            "resolution": "1080p",
            "duration": 8,
            "expect_audio": True,
        }
    }
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    export = run_dir / "generated" / "final-export.mp4"
    export.write_bytes(b"fake export")

    report = video_qa.prepare_export_review(
        run_dir,
        video=export,
        extract_frames=False,
        run_command=lambda _command: _ffprobe_result(
            duration=8,
            audio=True,
        ),
    )
    assert report["status"] == "awaiting_human_review"
    assert report["expected"]["expect_audio"] is True

    approved = video_qa.set_export_decision(
        run_dir,
        decision="passed",
    )
    assert approved["status"] == "passed"
    data = manifest.load(manifest_path)
    assert data["video_workflow"]["visual_qa"] == "passed"
    assert data["video_workflow"]["export_qa"] == "passed"
    assert data["video_workflow"]["status"] == "export_qa_passed"
