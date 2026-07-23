import json
from pathlib import Path

from PIL import Image

from viral_social_test_loader import load_script


manifest = load_script("manifest")
runner = load_script("run_seedance_video")


def _prepared_video_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "output" / "run"
    analysis = run_dir / "analysis"
    generated = run_dir / "generated"
    analysis.mkdir(parents=True)
    generated.mkdir(parents=True)
    (analysis / "seedance-prompt.md").write_text(
        "Make a realistic quick tomato egg stir-fry cooking video.",
        encoding="utf-8",
    )
    (analysis / "shot-list.md").write_text(
        "1. Finished dish hook\n2. Ingredient layout\n3. Egg pour",
        encoding="utf-8",
    )
    manifest.create(
        analysis / "manifest.json",
        "vertical-video",
        [f"{index:02d}" for index in range(1, 10)],
    )
    for index in range(1, 10):
        Image.new("RGB", (1080, 1920), "white").save(
            generated / f"page-{index:02d}.png"
        )
    return run_dir


def _mark_storyboard_validated(run_dir: Path) -> None:
    manifest_path = run_dir / "analysis" / "manifest.json"
    for index in range(1, 10):
        asset_id = f"{index:02d}"
        manifest.mark(
            manifest_path,
            asset_id,
            "validated",
            output=f"generated/page-{index:02d}.png",
        )


def test_run_seedance_video_dry_run_uses_manifest_storyboard_url(tmp_path):
    run_dir = _prepared_video_run(tmp_path)
    manifest_path = run_dir / "analysis" / "manifest.json"
    data = manifest.load(manifest_path)
    data["assets"]["01"]["storyboard_url"] = "https://cdn.example/frame-01.png"
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    result = runner.run_seedance_video(run_dir, dry_run=True)

    assert result["api_key_set"] is False
    assert result["image_count"] == 1
    payload = result["payload"]
    assert payload["model"] == runner.DEFAULT_MODEL
    assert payload["content"][0]["type"] == "text"
    assert "tomato egg stir-fry" in payload["content"][0]["text"]
    assert "No subtitles" in payload["content"][0]["text"]
    assert "Voiceover" in payload["content"][0]["text"]
    assert "--ratio 9:16" in payload["content"][0]["text"]
    assert "--dur 5" in payload["content"][0]["text"]
    assert payload["content"][1]["image_url"]["url"] == "https://cdn.example/frame-01.png"


def test_run_seedance_video_dry_run_can_redact_local_data_url(tmp_path):
    run_dir = _prepared_video_run(tmp_path)

    result = runner.run_seedance_video(run_dir, dry_run=True, allow_data_url=True)

    assert result["image_count"] == 1
    assert result["payload"]["content"][1]["image_url"]["url"] == "<redacted data URL>"


def test_run_seedance_video_requires_storyboard_url_by_default(tmp_path):
    run_dir = _prepared_video_run(tmp_path)

    try:
        runner.run_seedance_video(run_dir, dry_run=True)
    except runner.SeedanceRunnerError as exc:
        assert "storyboard image URL" in str(exc)
    else:
        raise AssertionError("Expected SeedanceRunnerError")


def test_run_seedance_video_submits_polls_downloads_and_updates_manifest(
    tmp_path,
    monkeypatch,
):
    run_dir = _prepared_video_run(tmp_path)
    _mark_storyboard_validated(run_dir)
    monkeypatch.setenv("ARK_API_KEY", "test-key")
    calls = []
    statuses = [
        {"id": "cgt-test", "status": "queued"},
        {
            "id": "cgt-test",
            "status": "succeeded",
            "content": {"video_url": "https://cdn.example/video.mp4"},
            "usage": {"total_tokens": 123},
        },
    ]

    def fake_request(method, url, api_key, payload):
        calls.append((method, url, api_key, payload))
        if method == "POST":
            assert payload["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
            return {"id": "cgt-test"}
        return statuses.pop(0)

    def fake_download(url, output):
        assert url == "https://cdn.example/video.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"fake mp4")

    result = runner.run_seedance_video(
        run_dir,
        allow_data_url=True,
        timeout_seconds=10,
        poll_interval=0,
        request_fn=fake_request,
        download_fn=fake_download,
    )

    assert [call[0] for call in calls] == ["POST", "GET", "GET"]
    assert (run_dir / "generated" / "seedance-video.mp4").read_bytes() == b"fake mp4"
    assert (run_dir / "raw" / "seedance-create-request.json").is_file()
    assert (run_dir / "raw" / "seedance-status.json").is_file()
    assert result["status"] == "succeeded"
    assert result["output"] == "generated/seedance-video.mp4"

    data = manifest.load(run_dir / "analysis" / "manifest.json")
    assert data["video_generation"]["status"] == "succeeded"
    assert data["video_generation"]["task_id"] == "cgt-test"


def test_run_seedance_video_rejects_unvalidated_storyboard_before_post(
    tmp_path,
    monkeypatch,
):
    run_dir = _prepared_video_run(tmp_path)
    monkeypatch.setenv("ARK_API_KEY", "test-key")

    def fail_request(*args, **kwargs):
        raise AssertionError("Seedance POST should not happen before storyboard validation")

    try:
        runner.run_seedance_video(
            run_dir,
            image_urls=["https://cdn.example/frame-01.png"],
            request_fn=fail_request,
        )
    except runner.SeedanceRunnerError as exc:
        assert "Storyboard is not ready" in str(exc)
        assert "asset 01 is not validated" in str(exc)
    else:
        raise AssertionError("Expected SeedanceRunnerError")
