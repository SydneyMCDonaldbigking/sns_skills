from viral_social_test_loader import load_script


frames = load_script("extract_keyframes")


def test_candidate_timestamps_exclude_unstable_edges():
    assert frames.candidate_timestamps(20.0, count=5) == [1.0, 5.5, 10.0, 14.5, 19.0]


def test_selected_export_requires_exactly_nine_timestamps(tmp_path):
    try:
        frames.export_selected(tmp_path / "a.mp4", [1.0] * 8, tmp_path / "out")
    except ValueError as exc:
        assert "exactly 9" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
