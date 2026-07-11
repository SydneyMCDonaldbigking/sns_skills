import json
from datetime import datetime

from viral_social_test_loader import load_script


manifest = load_script("manifest")
run_dirs = load_script("create_run_dir")


def test_run_directory_uses_local_system_timestamp_and_avoids_collision(tmp_path):
    fixed = datetime(2026, 7, 11, 14, 5, 9)
    first = run_dirs.create(tmp_path, "summer launch", now=fixed)
    second = run_dirs.create(tmp_path, "summer launch", now=fixed)
    assert first.name == "20260711-140509-summer-launch"
    assert second.name == "20260711-140509-summer-launch-02"


def test_manifest_resumes_only_incomplete_assets(tmp_path):
    path = tmp_path / "manifest.json"
    manifest.create(path, "xiaohongshu", ["01", "02"])
    manifest.mark(path, "01", "generated", output="generated/01.png")
    manifest.mark(path, "01", "validated")

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["assets"]["01"]["status"] == "validated"
    assert manifest.pending(path) == ["02"]


def test_manifest_rejects_invalid_status(tmp_path):
    path = tmp_path / "manifest.json"
    manifest.create(path, "video", ["01"])
    try:
        manifest.mark(path, "01", "unknown")
    except ValueError as exc:
        assert "status" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
