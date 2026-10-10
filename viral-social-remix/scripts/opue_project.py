"""Draft an Opue_video_add recipe project from a run's accepted video clips.

Opue_video_add is the post-production engine (logo, Reels captions, step labels,
end card) that replaced ChatCut. This script turns the accepted clips and the
clip-relative caption cues in `analysis/caption-cues/` into
`<opue>/projects/<name>/project.yaml` plus an untracked `roots.local.yaml`
pointing at this run, and extracts one still per shot/step into
`qa/opue-frames/` so the agent, as the editor, can look at the picture and
decide the step emoji, keywords, ingredient callouts, and product sticker
before running the Opue commands it prints.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import caption_cues


ROOT = Path(__file__).parents[2]
LOCAL_ENV = ROOT / ".env.local"
DEFAULT_OPUE_ROOT = ROOT.parent / "test_opus" / "Opue_video_add"
OPUE_PYTHON = "D:/anaconda/envs/motion-video/python.exe"
BRANDS = {"umall": "umall", "asian_grocer": "ago"}
DEFAULT_HOOK_SECONDS = 2.0
DEFAULT_CTA_SECONDS = 2.2
MIN_SHOT_SECONDS = 0.8
DEFAULT_DURATIONS = {"single-10s": 10.0}
EDITOR_TODO = [
    "look at every still in qa/opue-frames/ before writing anything on screen",
    "headline angle in title (10-Min Light Dinner / Fine Dining at Home / Make This for the Kids), dish name in kicker",
    "dish emoji in `emoji:`; one ingredient emoji per step (`emoji:` on each step)",
    "mark 1-2 keywords per step with *stars* and list them under `keywords`",
    "if the hook lays out ingredients: `ingredients` with `at`/`label` (0-1 of the hook still) and `callouts: true`",
    "real product image as the `product` sticker when the run has one; `cta.search` with the dish or product name",
    "only facts from the user or the package; then engine.pick, engine.preview (look at it), engine.render --sheet",
]


class OpueProjectError(RuntimeError):
    pass


def _load_env_file(path: Path | None = None) -> None:
    env_path = path or LOCAL_ENV
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def resolve_opue_root(value: str | Path | None = None) -> Path:
    _load_env_file()
    root = Path(value or os.environ.get("OPUE_VIDEO_ADD_ROOT") or DEFAULT_OPUE_ROOT)
    if not (root / "engine" / "spec.py").is_file():
        raise OpueProjectError(
            f"Opue_video_add not found at {root}; pass --opue-root or set OPUE_VIDEO_ADD_ROOT"
        )
    return root


def _manifest(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "analysis" / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def infer_clips(run_dir: Path) -> dict[str, Path]:
    """Accepted clips in edit order: NewB takes, else Seedance three-clip, else single-10s."""
    data = _manifest(run_dir)
    newb = data.get("newb_video_generation") or {}
    clips = {
        label: run_dir / entry["output"]
        for label, entry in newb.items()
        if isinstance(entry, dict) and entry.get("status") == "succeeded" and entry.get("output")
    }
    if clips:
        return clips
    generated = run_dir / "generated"
    three = {f"clip-{i:02d}": generated / f"seedance-clip-{i:02d}.mp4" for i in range(1, 4)}
    three = {name: path for name, path in three.items() if path.is_file()}
    if three:
        return three
    single = generated / "seedance-video.mp4"
    return {"single-10s": single} if single.is_file() else {}


def probe(path: Path) -> dict[str, float]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe or not path.is_file():
        return {}
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate:format=duration", "-of", "json", str(path)],
            check=True, capture_output=True, text=True,
        ).stdout
        info = json.loads(out)
        num, den = info["streams"][0]["r_frame_rate"].split("/")
        return {"fps": float(num) / float(den), "duration": float(info["format"]["duration"])}
    except (OSError, subprocess.CalledProcessError, KeyError, IndexError, ValueError, ZeroDivisionError):
        return {}


def extract_frame(source: Path, seconds: float, output: Path) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not source.is_file():
        return False
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{max(seconds, 0.0):.3f}",
             "-i", str(source), "-frames:v", "1", "-q:v", "3", str(output)],
            check=True,
        )
        return output.is_file()
    except (OSError, subprocess.CalledProcessError):
        return False


def editor_frames(run_dir: Path, shots: list[dict[str, Any]], frame_fn=extract_frame) -> list[dict[str, Any]]:
    """Stills the editor looks at: the hook's first frame (callout coordinates are 0-1 of
    it), one frame just after each step starts (emoji, keywords), and the end card."""
    out_dir = run_dir / "qa" / "opue-frames"
    frames = []
    for shot in shots:
        moments = [(shot["id"], shot["in"])]
        if shot.get("steps"):
            moments = [
                (f"{shot['id']}-step{n:02d}", shot["in"] + min(step["at_s"] + 0.6, shot["seconds"] - 0.05))
                for n, step in enumerate(shot["steps"], start=1)
            ]
        elif shot["role"] == "step":
            moments = [(shot["id"], shot["in"] + shot["seconds"] / 2)]
        for label, seconds in moments:
            path = out_dir / f"{label}.jpg"
            if shot.get("source") and frame_fn(Path(shot["source"]), seconds, path):
                frames.append({"shot": shot["id"], "role": shot["role"], "at": round(seconds, 3),
                               "frame": path.relative_to(run_dir).as_posix()})
    return frames


def _cues_for(run_dir: Path, clip: str) -> list[caption_cues.Cue]:
    path = run_dir / "analysis" / "caption-cues" / f"{clip}.json"
    if not path.is_file():
        return []
    _, _, _, cues = caption_cues.read_cue_file(path)
    return cues


def _q(value: Any) -> str:
    """A YAML flow scalar: JSON strings and numbers are valid YAML."""
    return json.dumps(value, ensure_ascii=False)


def _en(text: str | None) -> str | None:
    return f"{{en: {_q(text)}}}" if text else None


def plan_shots(
    clips: list[dict[str, Any]],
    *,
    hook_seconds: float = DEFAULT_HOOK_SECONDS,
    cta_seconds: float = DEFAULT_CTA_SECONDS,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Split clips into hook / step / cta shots; cues become steps at clip-relative seconds.

    Each clip dict carries name, take, trim_in, trim_out, cues.
    """
    shots: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, clip in enumerate(clips):
        start, end = clip["trim_in"], clip["trim_out"]
        if end - start < MIN_SHOT_SECONDS:
            raise OpueProjectError(f"{clip['name']}: trimmed length {end - start:.2f}s is too short")
        cues = [cue for cue in clip["cues"] if start <= cue.start < end]
        dropped = len(clip["cues"]) - len(cues)
        if dropped:
            warnings.append(f"{clip['name']}: {dropped} cue(s) fall outside the trim and were dropped")
        first, last = index == 0, index == len(clips) - 1
        body_start, body_end = start, end
        if first:
            hook_end = cues[0].start if cues and cues[0].start - start >= MIN_SHOT_SECONDS else start + hook_seconds
            hook_end = min(hook_end, end - MIN_SHOT_SECONDS)
            shots.append({"id": "hook", "role": "hook", "take": clip["take"], "in": start,
                          "seconds": hook_end - start, "source": clip.get("path")})
            body_start = hook_end
        cta_start = None
        if last:
            cta_start = max(end - cta_seconds, body_start + MIN_SHOT_SECONDS)
            if cta_start >= end - 0.3:
                raise OpueProjectError(f"{clip['name']}: no room for a {cta_seconds}s end card; widen the trim")
            body_end = cta_start
        steps = []
        for cue in cues:
            if cue.start >= body_end - 0.3:
                warnings.append(f"{clip['name']}: cue {cue.text!r} starts in the end card and was dropped")
                continue
            at = max(0.0, cue.start - body_start)
            if steps and steps[-1]["at_s"] == 0.0 and at == 0.0:
                warnings.append(f"{clip['name']}: cue {steps[-1]['text']!r} was covered by the hook and dropped")
                steps.pop()
            steps.append({"at_s": round(at, 3), "text": cue.text})
        if body_end - body_start >= MIN_SHOT_SECONDS - 1e-6:
            shots.append({"id": clip["name"], "role": "step", "take": clip["take"], "in": body_start,
                          "seconds": body_end - body_start, "steps": steps, "source": clip.get("path")})
        elif steps:
            warnings.append(f"{clip['name']}: body too short after hook/end card; its cues were dropped")
        if cta_start is not None:
            shots.append({"id": "shop", "role": "cta", "take": clip["take"], "in": cta_start,
                          "seconds": end - cta_start, "source": clip.get("path")})
    return shots, warnings


def render_yaml(
    *,
    brand: str,
    title: str,
    kicker: str | None,
    emoji: str | None,
    fps: int | None,
    shots: list[dict[str, Any]],
    run_name: str,
) -> str:
    lines = [
        f"# Drafted by sns_skill opue_project.py from run {run_name}. Generated clips keep their",
        "# native ambient sound (no BGM). The agent is the editor: from the stills in the run's",
        "# qa/opue-frames/ it fills step emoji, keywords, ingredient callouts, and the product",
        "# sticker itself, then runs:",
        f"#   python -m engine.pick {brand} --for projects/<this project>",
        "#   python -m engine.preview projects/<this project>",
        "#   python -m engine.render  projects/<this project> --sheet",
        "# Clip media is not in git: `run:` lives in roots.local.yaml.",
        "template: recipe",
        f"brand: {brand}",
        "roots: {}",
        "",
    ]
    if fps:
        lines.append(f"canvas: {{fps: {fps}}}         # the clips' own frame rate, frame for frame")
    lines += [
        "continuous: true          # handoffs were designed at generation; no default cut transitions",
        "look: {fade_out: 0.0}     # Reels loop, so no fade to black",
        "audio: {clips: true}      # keep the generated ambient cooking sound; no BGM",
        "",
        f"title: {_en(title)}",
    ]
    if kicker:
        lines.append(f"kicker: {_en(kicker)}")
    if emoji:
        lines.append(f"emoji: {_q(emoji)}")
    lines += [
        "cta:",
        "  line: {en: \"Shop the ingredients 🛒\"}",
        "keywords: {en: []}        # words to highlight; or mark them with *stars* in step text",
        "",
        "shots:",
    ]
    for shot in shots:
        head = (
            f"  - {{id: {_q(shot['id'])}, role: {shot['role']}, seconds: {shot['seconds']:.4f}, "
            f"take: {_q(shot['take'])}, in: {shot['in']:.4f}"
        )
        steps = shot.get("steps")
        if not steps:
            lines.append(head + "}")
            continue
        lines.append(head + ",")
        lines.append("     steps: [")
        for step in steps:
            lines.append(f"       {{at_s: {step['at_s']}, text: {_en(step['text'])}}},")
        lines.append("     ]}")
    return "\n".join(lines) + "\n"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "video"


def build_project(
    run_dir: str | Path,
    *,
    brand: str,
    title: str,
    kicker: str | None = None,
    emoji: str | None = None,
    name: str | None = None,
    clips: dict[str, str] | None = None,
    trims: dict[str, tuple[float, float]] | None = None,
    hook_seconds: float = DEFAULT_HOOK_SECONDS,
    cta_seconds: float = DEFAULT_CTA_SECONDS,
    opue_root: str | Path | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
    probe_fn=probe,
    frame_fn=extract_frame,
) -> dict[str, Any]:
    run = Path(run_dir).resolve()
    if brand not in BRANDS:
        raise OpueProjectError(f"--brand must be one of {', '.join(BRANDS)}")
    clip_paths = {key: (Path(value) if Path(value).is_absolute() else run / value)
                  for key, value in (clips or {}).items()} or infer_clips(run)
    if not clip_paths:
        raise OpueProjectError("No accepted clips found; pass --clip NAME=PATH")
    trims = trims or {}
    planned, fps_values = [], set()
    for clip_name, path in clip_paths.items():
        if not path.is_file():
            raise OpueProjectError(f"{clip_name}: missing clip {path}")
        try:
            take = "${run}/" + path.resolve().relative_to(run).as_posix()
        except ValueError:
            raise OpueProjectError(f"{clip_name}: clip must live inside the run directory") from None
        info = probe_fn(path)
        if info.get("fps"):
            fps_values.add(round(info["fps"]))
        duration = info.get("duration") or DEFAULT_DURATIONS.get(clip_name) or (
            30.0 if clip_name.startswith(("newb", "take")) else 6.0
        )
        trim_in, trim_out = trims.get(clip_name, (0.0, duration))
        planned.append({"name": clip_name, "take": take, "path": path, "trim_in": trim_in,
                        "trim_out": min(trim_out, duration), "cues": _cues_for(run, clip_name)})
    shots, warnings = plan_shots(planned, hook_seconds=hook_seconds, cta_seconds=cta_seconds)
    if len(fps_values) > 1:
        warnings.append(f"clips have different frame rates {sorted(fps_values)}; Opue resamples to the first")
    if not any(shot.get("steps") for shot in shots):
        warnings.append("no caption cues found: the video will have no step captions")

    root = resolve_opue_root(opue_root)
    project_name = name or f"{BRANDS[brand]}_{_slug(title)}"
    project_dir = root / "projects" / project_name
    text = render_yaml(brand=brand, title=title, kicker=kicker, emoji=emoji,
                       fps=min(fps_values) if fps_values else None, shots=shots, run_name=run.name)
    result = {
        "project": str(project_dir),
        "shots": len(shots),
        "steps": sum(len(shot.get("steps") or []) for shot in shots),
        "warnings": warnings,
        "next": [
            f"cd {root}",
            f"{OPUE_PYTHON} -m engine.pick {brand} --for projects/{project_name}",
            f"{OPUE_PYTHON} -m engine.preview projects/{project_name}",
            f"{OPUE_PYTHON} -m engine.render projects/{project_name} --sheet",
        ],
    }
    if dry_run:
        return {**result, "dry_run": True, "project_yaml": text}
    if (project_dir / "project.yaml").exists() and not overwrite:
        raise OpueProjectError(f"{project_dir / 'project.yaml'} exists; pass --overwrite or --name")
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project.yaml").write_text(text, encoding="utf-8")
    (project_dir / "roots.local.yaml").write_text(f"run: {run.as_posix()}\n", encoding="utf-8")
    result["editor_frames"] = editor_frames(run, shots, frame_fn)
    result["editor_todo"] = EDITOR_TODO
    manifest_path = run / "analysis" / "manifest.json"
    if manifest_path.is_file():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["opue_project"] = {"path": str(project_dir), "root": str(root), "brand": brand,
                                "name": project_name, "next": result["next"][1:]}
        manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_dir")
    parser.add_argument("--brand", required=True, choices=sorted(BRANDS))
    parser.add_argument("--title", required=True, help="Opening headline (English, on screen).")
    parser.add_argument("--kicker", help="Small label above the headline, e.g. the dish name.")
    parser.add_argument("--emoji", help="The dish emoji for the headline and {dish} slots.")
    parser.add_argument("--name", help="Opue project folder name. Default: <ago|umall>_<title>.")
    parser.add_argument("--clip", action="append", default=[], metavar="NAME=PATH",
                        help="Clip in edit order; NAME matches analysis/caption-cues/NAME.json.")
    parser.add_argument("--trim", action="append", default=[], metavar="NAME=IN:OUT")
    parser.add_argument("--hook-seconds", type=float, default=DEFAULT_HOOK_SECONDS)
    parser.add_argument("--cta-seconds", type=float, default=DEFAULT_CTA_SECONDS)
    parser.add_argument("--opue-root")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        clips = dict(caption_cues.parse_assignment(value, "--clip") for value in args.clip)
        trims = dict(caption_cues.parse_trim(value) for value in args.trim)
        result = build_project(
            args.run_dir, brand=args.brand, title=args.title, kicker=args.kicker, emoji=args.emoji,
            name=args.name, clips=clips, trims=trims, hook_seconds=args.hook_seconds,
            cta_seconds=args.cta_seconds, opue_root=args.opue_root, overwrite=args.overwrite,
            dry_run=args.dry_run,
        )
    except OpueProjectError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
