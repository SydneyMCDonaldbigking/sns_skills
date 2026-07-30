"""Recommend the next deterministic command for a remix run."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CLIP_RE = re.compile(r"^clip-(\d+)$")


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path)


def video_mode(data: dict[str, Any] | None) -> str:
    if not data:
        return "unknown"
    video = data.get("video")
    if isinstance(video, dict) and video.get("mode"):
        return str(video["mode"])
    return str(data.get("video_mode") or "unknown")


def clip_number(clip: str) -> int | None:
    match = CLIP_RE.match(clip)
    return int(match.group(1)) if match else None


def command(run_dir: Path, script: str, args: str = "") -> str:
    suffix = f" {args}" if args else ""
    return f"python scripts/{script} {run_dir}{suffix}"


def seedance_command(run_dir: Path, args: str = "") -> str:
    suffix = f" {args}" if args else ""
    return f"python scripts/run_seedance_video.py --run {run_dir}{suffix}"


def openrouter_frame_command(run_dir: Path, asset_id: str) -> str:
    return (
        "python scripts/run_openrouter_carousel.py "
        f"--run {run_dir} --api-only --asset-id {asset_id}"
    )


def file_state(run_dir: Path) -> dict[str, bool]:
    cue_dir = run_dir / "analysis" / "caption-cues"
    return {
        "manifest": (run_dir / "analysis" / "manifest.json").is_file(),
        "page_01": (run_dir / "generated" / "page-01.png").is_file(),
        "page_02": (run_dir / "generated" / "page-02.png").is_file(),
        "page_03": (run_dir / "generated" / "page-03.png").is_file(),
        "clip_01": (run_dir / "generated" / "seedance-clip-01.mp4").is_file(),
        "clip_02": (run_dir / "generated" / "seedance-clip-02.mp4").is_file(),
        "clip_03": (run_dir / "generated" / "seedance-clip-03.mp4").is_file(),
        "single_10s": (run_dir / "generated" / "seedance-video.mp4").is_file(),
        "caption_cues": cue_dir.exists() and any(cue_dir.glob("*.json")),
        "caption_plan": (cue_dir / "chatcut-caption-plan.json").is_file(),
        "edit_plan": (run_dir / "analysis" / "edit-plan.json").is_file(),
        "decision_sheet": (run_dir / "qa" / "decision-sheet.html").is_file(),
    }


def latest_handoff_status(run_dir: Path, source_clip: str) -> dict[str, Any] | None:
    number = clip_number(source_clip)
    if number is None:
        return None
    handoff_id = f"{source_clip}-to-clip-{number + 1:02d}"
    report = run_dir / "qa" / "handoffs" / handoff_id / "handoff-review.json"
    return load_json(report)


def recommend_three_clip(run_dir: Path, states: dict[str, bool]) -> dict[str, Any]:
    if not states["page_01"]:
        return {
            "stage": "opening-frame",
            "action": "generate clip-01 exact 1080x1920 opening frame before paid video",
            "command": openrouter_frame_command(run_dir, "01"),
        }
    for index in range(1, 4):
        clip = f"clip-{index:02d}"
        if not states[f"clip_{index:02d}"]:
            if index == 1:
                args = "--storyboard-group 1"
            else:
                prev = f"clip-{index - 1:02d}"
                handoff = latest_handoff_status(run_dir, prev)
                decision = handoff.get("decision") if handoff else None
                if decision == "use-last-frame":
                    args = f"--storyboard-group {index} --continue-from-last-frame"
                elif decision == "transition-anchor":
                    asset_id = f"{index:02d}"
                    if not states[f"page_{index:02d}"]:
                        return {
                            "stage": "transition-anchor",
                            "action": (
                                f"generate {clip} exact 1080x1920 transition "
                                "opening anchor before Seedance"
                            ),
                            "command": openrouter_frame_command(run_dir, asset_id),
                        }
                    args = f"--storyboard-group {index}"
                else:
                    return {
                        "stage": "handoff-decision",
                        "action": f"review {prev} before generating {clip}",
                        "command": command(
                            run_dir,
                            "handoff_review.py",
                            f"--clip {prev}",
                        ),
                    }
            return {
                "stage": "seedance",
                "action": f"generate {clip}",
                "command": seedance_command(run_dir, args),
            }
        if index < 3 and not latest_handoff_status(run_dir, clip):
            return {
                "stage": "handoff-review",
                "action": f"create handoff review for {clip}",
                "command": command(run_dir, "handoff_review.py", f"--clip {clip}"),
            }

    if not states["edit_plan"]:
        return {
            "stage": "edit-plan",
            "action": "compile clip trims and editorial intent",
            "command": command(run_dir, "edit_plan.py"),
        }
    if states["caption_cues"] and not states["caption_plan"]:
        return {
            "stage": "caption-plan",
            "action": "compile caption cues with actual trims",
            "command": command(run_dir, "caption_cues.py"),
        }
    if not states["decision_sheet"]:
        return {
            "stage": "qa-sheet",
            "action": "build one-page QA decision sheet",
            "command": command(run_dir, "qa_decision_sheet.py"),
        }
    return {
        "stage": "chatcut",
        "action": "import accepted MP4s and follow analysis/edit-plan.json",
        "command": "open ChatCut and place clips/captions from edit-plan and chatcut-caption-plan",
    }


def recommend_single_10s(run_dir: Path, states: dict[str, bool]) -> dict[str, Any]:
    if not states["single_10s"]:
        return {
            "stage": "seedance",
            "action": "generate the single 10s commercial",
            "command": seedance_command(run_dir, "--profile single-10s-final"),
        }
    if not states["edit_plan"]:
        return {
            "stage": "edit-plan",
            "action": "compile single-clip edit plan",
            "command": command(run_dir, "edit_plan.py"),
        }
    if states["caption_cues"] and not states["caption_plan"]:
        return {
            "stage": "caption-plan",
            "action": "compile caption cues with actual trims",
            "command": command(run_dir, "caption_cues.py"),
        }
    if not states["decision_sheet"]:
        return {
            "stage": "qa-sheet",
            "action": "build one-page QA decision sheet",
            "command": command(run_dir, "qa_decision_sheet.py"),
        }
    return {
        "stage": "chatcut",
        "action": "import accepted MP4 and follow analysis/edit-plan.json",
        "command": "open ChatCut and place clip/captions from edit-plan and chatcut-caption-plan",
    }


def recommend(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    manifest = load_json(run_dir / "analysis" / "manifest.json")
    states = file_state(run_dir)
    if not states["manifest"]:
        result = {
            "stage": "prepare",
            "action": "create a run directory first",
            "command": "python scripts/run_pipeline.py prepare-original-video ...",
        }
    else:
        mode = video_mode(manifest)
        if mode == "director-first-frame-three-clips":
            result = recommend_three_clip(run_dir, states)
        elif mode == "single-10s-commercial":
            result = recommend_single_10s(run_dir, states)
        else:
            result = {
                "stage": "unknown",
                "action": f"unsupported or non-video mode: {mode}",
                "command": "inspect analysis/manifest.json",
            }
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "states": states,
        "recommendation": result,
    }
    output = run_dir / "analysis" / "next-step.json"
    write_json(output, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recommend the next RPA command for a run.")
    parser.add_argument("run_dir", type=Path)
    return recommend(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
