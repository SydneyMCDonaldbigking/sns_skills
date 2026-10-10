import json
from pathlib import Path

import pytest
import yaml

from viral_social_test_loader import load_script


manifest = load_script("manifest")
caption_cues = load_script("caption_cues")
opue = load_script("opue_project")
next_step = load_script("next_step")


def _opue_root(tmp_path: Path) -> Path:
    root = tmp_path / "Opue_video_add"
    (root / "engine").mkdir(parents=True)
    (root / "engine" / "spec.py").write_text("", encoding="utf-8")
    return root


def _three_clip_run(tmp_path: Path) -> Path:
    run = tmp_path / "output" / "run"
    (run / "generated").mkdir(parents=True)
    cue_dir = run / "analysis" / "caption-cues"
    cue_dir.mkdir(parents=True)
    manifest.create(run / "analysis" / "manifest.json", "vertical-video", ["01", "02", "03"])
    for index, texts in enumerate(
        [[(2.2, "Sear the *gyoza*")], [(0.4, "Add water"), (3.0, "Lid on, steam")], [(0.5, "Crisp bottoms")]],
        start=1,
    ):
        (run / "generated" / f"seedance-clip-{index:02d}.mp4").write_bytes(b"mp4")
        (cue_dir / f"clip-{index:02d}.json").write_text(
            json.dumps({"source_clip": f"clip-{index:02d}", "cues": [
                {"start": start, "end": start + 1.2, "text": text} for start, text in texts
            ]}),
            encoding="utf-8",
        )
    return run


def _probe(path: Path) -> dict:
    return {"fps": 24.0, "duration": 6.0}


def test_plan_splits_hook_steps_and_end_card(tmp_path):
    run = _three_clip_run(tmp_path)
    root = _opue_root(tmp_path)
    result = opue.build_project(
        run, brand="asian_grocer", title="Crispy Gyoza in 10 Min", kicker="Pan-fried gyoza",
        emoji="🥟", trims={"clip-03": (0.0, 5.5)}, opue_root=root, probe_fn=_probe,
    )
    project_dir = Path(result["project"])
    assert project_dir == root / "projects" / "ago_crispy_gyoza_in_10_min"
    data = yaml.safe_load((project_dir / "project.yaml").read_text(encoding="utf-8"))
    assert data["template"] == "recipe"
    assert data["brand"] == "asian_grocer"
    assert data["audio"] == {"clips": True}
    assert data["canvas"] == {"fps": 24}
    assert data["title"] == {"en": "Crispy Gyoza in 10 Min"}
    roles = [(shot["id"], shot["role"]) for shot in data["shots"]]
    assert roles == [("hook", "hook"), ("clip-01", "step"), ("clip-02", "step"), ("clip-03", "step"), ("shop", "cta")]
    hook, first, second, third, cta = data["shots"]
    assert hook["seconds"] == pytest.approx(2.2)
    assert first["in"] == pytest.approx(2.2)
    assert first["steps"] == [{"at_s": 0.0, "text": {"en": "Sear the *gyoza*"}}]
    assert [step["at_s"] for step in second["steps"]] == [0.4, 3.0]
    assert third["seconds"] + cta["seconds"] == pytest.approx(5.5)
    assert cta["take"] == "${run}/generated/seedance-clip-03.mp4"
    assert (project_dir / "roots.local.yaml").read_text(encoding="utf-8").strip() == f"run: {run.resolve().as_posix()}"
    saved = json.loads((run / "analysis" / "manifest.json").read_text(encoding="utf-8"))["opue_project"]
    assert saved["brand"] == "asian_grocer"
    assert "engine.pick asian_grocer" in saved["next"][0]
    assert result["warnings"] == []


def test_cues_inside_end_card_are_dropped_with_warning(tmp_path):
    run = _three_clip_run(tmp_path)
    result = opue.build_project(
        run, brand="umall", title="Gyoza", trims={"clip-03": (0.0, 2.5)}, cta_seconds=2.2,
        opue_root=_opue_root(tmp_path), probe_fn=_probe, dry_run=True,
    )
    assert result["dry_run"] is True
    assert any("end card" in warning or "too short" in warning for warning in result["warnings"])
    assert "umall_gyoza" in result["project"]


def test_newb_take_is_inferred_from_manifest(tmp_path):
    run = tmp_path / "output" / "newb"
    (run / "generated").mkdir(parents=True)
    (run / "generated" / "take-01.mp4").write_bytes(b"mp4")
    manifest.create(run / "analysis" / "manifest.json", "vertical-video", ["01"])
    data = manifest.load(run / "analysis" / "manifest.json")
    data["newb_video_generation"] = {
        "take-01": {"status": "succeeded", "output": "generated/take-01.mp4"},
        "take-02": {"status": "failed"},
    }
    (run / "analysis" / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
    assert opue.infer_clips(run) == {"take-01": run / "generated" / "take-01.mp4"}
    result = opue.build_project(
        run, brand="umall", title="Garlic Clams", opue_root=_opue_root(tmp_path),
        probe_fn=lambda path: {}, dry_run=True,
    )
    shots = yaml.safe_load(result["project_yaml"])["shots"]
    assert shots[-1]["role"] == "cta"
    assert shots[-1]["in"] + shots[-1]["seconds"] == pytest.approx(30.0)
    assert any("no caption cues" in warning for warning in result["warnings"])


def test_refuses_overwrite_and_missing_opue(tmp_path):
    run = _three_clip_run(tmp_path)
    root = _opue_root(tmp_path)
    opue.build_project(run, brand="umall", title="Gyoza", opue_root=root, probe_fn=_probe)
    with pytest.raises(opue.OpueProjectError, match="exists"):
        opue.build_project(run, brand="umall", title="Gyoza", opue_root=root, probe_fn=_probe)
    with pytest.raises(opue.OpueProjectError, match="not found"):
        opue.build_project(run, brand="umall", title="Gyoza", opue_root=tmp_path / "nope", probe_fn=_probe)


def test_next_step_moves_from_qa_sheet_to_opue(tmp_path):
    run = _three_clip_run(tmp_path)
    states = {"decision_sheet": False}
    assert next_step.finish(run, states, {})["stage"] == "qa-sheet"
    states["decision_sheet"] = True
    reco = next_step.finish(run, states, {})
    assert reco["stage"] == "opue-project"
    assert "opue_project.py" in reco["command"]
    reco = next_step.finish(run, states, {"opue_project": {"path": "p", "root": "R", "next": ["a", "b"]}})
    assert reco == {"stage": "opue-render", "action": reco["action"], "command": "cd R && a && b"}


def test_editor_stills_cover_hook_each_step_and_end_card(tmp_path):
    run = _three_clip_run(tmp_path)
    seen = []

    def fake_frame(source, seconds, output):
        seen.append((source.name, round(seconds, 2), output.name))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"jpg")
        return True

    result = opue.build_project(
        run, brand="umall", title="Gyoza", opue_root=_opue_root(tmp_path),
        probe_fn=_probe, frame_fn=fake_frame,
    )
    labels = [frame["frame"] for frame in result["editor_frames"]]
    assert labels == [
        "qa/opue-frames/hook.jpg",
        "qa/opue-frames/clip-01-step01.jpg",
        "qa/opue-frames/clip-02-step01.jpg",
        "qa/opue-frames/clip-02-step02.jpg",
        "qa/opue-frames/clip-03-step01.jpg",
        "qa/opue-frames/shop.jpg",
    ]
    assert seen[0] == ("seedance-clip-01.mp4", 0.0, "hook.jpg")
    assert seen[3] == ("seedance-clip-02.mp4", 3.6, "clip-02-step02.jpg")
    assert any("callouts" in item for item in result["editor_todo"])
