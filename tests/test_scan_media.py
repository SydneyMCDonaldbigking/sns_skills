from pathlib import Path

from viral_social_test_loader import load_script


scan_media = load_script("scan_media")


def test_scan_groups_direct_subfolder_and_root_files(tmp_path: Path):
    (tmp_path / "root.jpg").write_bytes(b"image")
    group = tmp_path / "carousel"
    group.mkdir()
    (group / "01.png").write_bytes(b"image")
    (group / "02.webp").write_bytes(b"image")
    (group / "notes.txt").write_text("ignore", encoding="utf-8")
    output = tmp_path / "output"
    output.mkdir()
    (output / "old.png").write_bytes(b"image")

    result = scan_media.scan(tmp_path)

    assert [item["name"] for item in result["tasks"]] == ["carousel", "root"]
    assert len(result["tasks"][0]["files"]) == 2
    assert result["ignored_count"] == 1


def test_scan_rejects_missing_directory(tmp_path: Path):
    missing = tmp_path / "missing"
    try:
        scan_media.scan(missing)
    except ValueError as exc:
        assert "readable directory" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
