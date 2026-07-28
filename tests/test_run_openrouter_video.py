import json
from pathlib import Path

from PIL import Image

from viral_social_test_loader import load_script


manifest = load_script("manifest")
runner = load_script("run_openrouter_video")


def _isolated_openrouter_video_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(runner, "LOCAL_ENV", tmp_path / ".env.local")
    for name in runner.KEY_ENV_NAMES + [
        "VSR_OPENROUTER_VIDEO_ENDPOINT",
        "VSR_OPENROUTER_VIDEO_MODEL",
        "VSR_OPENROUTER_VIDEO_RATIO",
        "VSR_OPENROUTER_VIDEO_DURATION",
        "VSR_OPENROUTER_VIDEO_RESOLUTION",
        "VSR_OPENROUTER_VIDEO_GENERATE_AUDIO",
    ]:
        monkeypatch.delenv(name, raising=False)


def _prepared_video_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "output" / "run"
    analysis = run_dir / "analysis"
    generated = run_dir / "generated"
    analysis.mkdir(parents=True)
    generated.mkdir(parents=True)
    (analysis / "seedance-prompt.md").write_text(
        "Make a realistic no-person tomato egg stir-fry cooking video.",
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


def _prepared_compact_video_run(tmp_path: Path, *, with_urls: bool = False) -> Path:
    run_dir = tmp_path / "output" / "compact"
    analysis = run_dir / "analysis"
    analysis.mkdir(parents=True)
    (analysis / "openrouter-video-prompt.md").write_text(
        "Create a 5-second no-face Japanese gyoza cooking video.",
        encoding="utf-8",
    )
    (analysis / "shot-list.md").write_text(
        "Shot 1 gyoza in pan\nShot 2 steam and sear\nShot 3 plated crispy gyoza",
        encoding="utf-8",
    )
    manifest.create(
        analysis / "manifest.json",
        "vertical-video",
        ["01", "02", "03"],
    )
    data = manifest.load(analysis / "manifest.json")
    data["video_mode"] = "compact-reference"
    if with_urls:
        for index in range(1, 4):
            data["assets"][f"{index:02d}"]["storyboard_url"] = (
                f"https://cdn.example/reference-{index:02d}.png"
            )
    (analysis / "manifest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
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


def test_resolve_config_uses_grok_openrouter_key_priority(tmp_path, monkeypatch):
    _isolated_openrouter_video_env(tmp_path, monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "generic-key")
    monkeypatch.setenv("GROK_OPENROUTER_API_KEY", "grok-key")

    config = runner.resolve_config()

    assert config["provider"] == "openrouter-video"
    assert config["endpoint"] == runner.DEFAULT_ENDPOINT
    assert config["model"] == "x-ai/grok-imagine-video"
    assert config["api_key"] == "grok-key"


def test_openrouter_video_dry_run_builds_grok_720p_first_frame_payload(
    tmp_path,
    monkeypatch,
):
    _isolated_openrouter_video_env(tmp_path, monkeypatch)
    run_dir = _prepared_video_run(tmp_path)
    manifest_path = run_dir / "analysis" / "manifest.json"
    data = manifest.load(manifest_path)
    data["assets"]["01"]["storyboard_url"] = "https://cdn.example/frame-01.png"
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    result = runner.run_openrouter_video(run_dir, dry_run=True)

    assert result["api_key_set"] is False
    assert result["image_count"] == 1
    assert result["endpoint"] == runner.DEFAULT_ENDPOINT
    assert result["generation"] == {
        "aspect_ratio": "9:16",
        "duration": 5,
        "resolution": "720p",
        "generate_audio": False,
    }
    payload = result["payload"]
    assert payload["model"] == runner.DEFAULT_MODEL
    assert payload["aspect_ratio"] == "9:16"
    assert payload["duration"] == 5
    assert payload["resolution"] == "720p"
    assert payload["generate_audio"] is False
    assert payload["frame_images"] == [
        {
            "type": "image_url",
            "image_url": {"url": "https://cdn.example/frame-01.png"},
            "frame_type": "first_frame",
        }
    ]
    assert "No subtitles" in payload["prompt"]
    assert "Voiceover" not in payload["prompt"]


def test_openrouter_video_dry_run_can_redact_local_data_url(tmp_path, monkeypatch):
    _isolated_openrouter_video_env(tmp_path, monkeypatch)
    run_dir = _prepared_video_run(tmp_path)

    result = runner.run_openrouter_video(run_dir, dry_run=True, allow_data_url=True)

    assert result["image_count"] == 1
    assert result["payload"]["frame_images"][0]["image_url"]["url"] == "<redacted data URL>"


def test_openrouter_video_compact_reference_can_dry_run_text_only(
    tmp_path,
    monkeypatch,
):
    _isolated_openrouter_video_env(tmp_path, monkeypatch)
    run_dir = _prepared_compact_video_run(tmp_path)

    result = runner.run_openrouter_video(run_dir, dry_run=True)

    assert result["video_mode"] == "compact-reference"
    assert result["image_count"] == 0
    payload = result["payload"]
    assert "frame_images" not in payload
    assert "input_references" not in payload
    assert "Japanese gyoza cooking video" in payload["prompt"]
    assert "No subtitles" in payload["prompt"]


def test_openrouter_video_compact_reference_can_send_all_manifest_references(
    tmp_path,
    monkeypatch,
):
    _isolated_openrouter_video_env(tmp_path, monkeypatch)
    run_dir = _prepared_compact_video_run(tmp_path, with_urls=True)

    result = runner.run_openrouter_video(
        run_dir,
        dry_run=True,
        include_reference_images=True,
    )

    assert result["video_mode"] == "compact-reference"
    assert result["image_count"] == 3
    assert result["payload"]["frame_images"][0]["image_url"]["url"] == (
        "https://cdn.example/reference-01.png"
    )
    reference_urls = [
        item["image_url"]["url"] for item in result["payload"]["input_references"]
    ]
    assert reference_urls == [
        "https://cdn.example/reference-02.png",
        "https://cdn.example/reference-03.png",
    ]


def test_openrouter_video_compact_reference_can_send_reference_only_images(
    tmp_path,
    monkeypatch,
):
    _isolated_openrouter_video_env(tmp_path, monkeypatch)
    run_dir = _prepared_compact_video_run(tmp_path, with_urls=True)

    result = runner.run_openrouter_video(
        run_dir,
        dry_run=True,
        reference_only_images=True,
    )

    payload = result["payload"]
    assert "frame_images" not in payload
    assert [item["image_url"]["url"] for item in payload["input_references"]] == [
        "https://cdn.example/reference-01.png",
        "https://cdn.example/reference-02.png",
        "https://cdn.example/reference-03.png",
    ]


def test_openrouter_video_can_send_extra_input_references_when_requested(
    tmp_path,
    monkeypatch,
):
    _isolated_openrouter_video_env(tmp_path, monkeypatch)
    run_dir = _prepared_video_run(tmp_path)
    manifest_path = run_dir / "analysis" / "manifest.json"
    data = manifest.load(manifest_path)
    for index in range(1, 10):
        data["assets"][f"{index:02d}"]["storyboard_url"] = (
            f"https://cdn.example/frame-{index:02d}.png"
        )
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    result = runner.run_openrouter_video(
        run_dir,
        dry_run=True,
        include_all_frames=True,
        include_reference_images=True,
    )

    assert len(result["payload"]["frame_images"]) == 1
    assert result["payload"]["frame_images"][0]["frame_type"] == "first_frame"
    assert len(result["payload"]["input_references"]) == 8


def test_openrouter_video_can_choose_manifest_asset_as_first_frame(
    tmp_path,
    monkeypatch,
):
    _isolated_openrouter_video_env(tmp_path, monkeypatch)
    run_dir = _prepared_video_run(tmp_path)
    manifest_path = run_dir / "analysis" / "manifest.json"
    data = manifest.load(manifest_path)
    for index in range(1, 10):
        data["assets"][f"{index:02d}"]["storyboard_url"] = (
            f"https://cdn.example/frame-{index:02d}.png"
        )
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    result = runner.run_openrouter_video(
        run_dir,
        dry_run=True,
        first_frame_asset_id="04",
        include_all_frames=True,
        include_reference_images=True,
    )

    assert result["payload"]["frame_images"][0]["image_url"]["url"] == (
        "https://cdn.example/frame-04.png"
    )
    reference_urls = [
        item["image_url"]["url"] for item in result["payload"]["input_references"]
    ]
    assert "https://cdn.example/frame-01.png" in reference_urls
    assert "https://cdn.example/frame-04.png" not in reference_urls


def test_openrouter_video_submits_polls_downloads_and_updates_manifest(
    tmp_path,
    monkeypatch,
):
    _isolated_openrouter_video_env(tmp_path, monkeypatch)
    run_dir = _prepared_video_run(tmp_path)
    _mark_storyboard_validated(run_dir)
    monkeypatch.setenv("GROK_OPENROUTER_API_KEY", "test-key")
    calls = []
    statuses = [
        {"id": "orv-test", "status": "processing", "polling_url": "/api/v1/videos/orv-test"},
        {
            "id": "orv-test",
            "status": "completed",
            "unsigned_urls": ["https://cdn.example/video.mp4"],
            "usage": {"cost": 0.07},
        },
    ]

    def fake_request(method, url, api_key, payload):
        calls.append((method, url, api_key, payload))
        if method == "POST":
            assert api_key == "test-key"
            assert payload["model"] == runner.DEFAULT_MODEL
            assert payload["aspect_ratio"] == "9:16"
            assert payload["duration"] == 5
            assert payload["resolution"] == "720p"
            assert payload["generate_audio"] is False
            assert payload["frame_images"][0]["image_url"]["url"].startswith(
                "data:image/png;base64,"
            )
            return statuses.pop(0)
        return statuses.pop(0)

    def fake_download(job, api_key, output):
        assert api_key == "test-key"
        assert job["unsigned_urls"] == ["https://cdn.example/video.mp4"]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"fake mp4")

    result = runner.run_openrouter_video(
        run_dir,
        allow_data_url=True,
        timeout_seconds=10,
        poll_interval=0,
        request_fn=fake_request,
        download_fn=fake_download,
        strip_audio_fn=lambda output: True,
    )

    assert [call[0] for call in calls] == ["POST", "GET"]
    assert (run_dir / "generated" / "openrouter-video.mp4").read_bytes() == b"fake mp4"
    assert (run_dir / "raw" / "openrouter-video-create-request.json").is_file()
    assert (run_dir / "raw" / "openrouter-video-status.json").is_file()
    assert result["status"] == "succeeded"
    assert result["output"] == "generated/openrouter-video.mp4"
    assert result["postprocess"]["audio_stripped"] is True
    assert result["final_response"]["unsigned_urls"] == ["<redacted video URL>"]

    data = manifest.load(run_dir / "analysis" / "manifest.json")
    assert data["openrouter_video_generation"]["status"] == "succeeded"
    assert data["openrouter_video_generation"]["task_id"] == "orv-test"
    assert data["openrouter_video_generation"]["generation"]["resolution"] == "720p"
    assert data["openrouter_video_generation"]["postprocess"]["audio_stripped"] is True


def test_openrouter_video_compact_reference_can_submit_text_only_without_nine_validated_frames(
    tmp_path,
    monkeypatch,
):
    _isolated_openrouter_video_env(tmp_path, monkeypatch)
    run_dir = _prepared_compact_video_run(tmp_path)
    monkeypatch.setenv("GROK_OPENROUTER_API_KEY", "test-key")
    calls = []

    def fake_request(method, url, api_key, payload):
        calls.append((method, url, api_key, payload))
        assert api_key == "test-key"
        if method == "POST":
            assert "frame_images" not in payload
            assert payload["aspect_ratio"] == "9:16"
            return {
                "id": "orv-compact",
                "status": "completed",
                "unsigned_urls": ["https://cdn.example/compact.mp4"],
                "usage": {"cost": 0.07},
            }
        raise AssertionError("Compact completed response should not need polling")

    def fake_download(job, api_key, output):
        assert job["unsigned_urls"] == ["https://cdn.example/compact.mp4"]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"compact mp4")

    result = runner.run_openrouter_video(
        run_dir,
        timeout_seconds=10,
        poll_interval=0,
        request_fn=fake_request,
        download_fn=fake_download,
        strip_audio_fn=lambda output: False,
    )

    assert [call[0] for call in calls] == ["POST"]
    assert result["video_mode"] == "compact-reference"
    assert result["image_count"] == 0
    assert result["output"] == "generated/openrouter-video.mp4"

    data = manifest.load(run_dir / "analysis" / "manifest.json")
    assert data["openrouter_video_generation"]["video_mode"] == "compact-reference"
    assert data["openrouter_video_generation"]["image_count"] == 0


def test_openrouter_video_rejects_unvalidated_storyboard_before_post(
    tmp_path,
    monkeypatch,
):
    _isolated_openrouter_video_env(tmp_path, monkeypatch)
    run_dir = _prepared_video_run(tmp_path)
    monkeypatch.setenv("GROK_OPENROUTER_API_KEY", "test-key")

    def fail_request(*args, **kwargs):
        raise AssertionError("OpenRouter POST should not happen before storyboard validation")

    try:
        runner.run_openrouter_video(
            run_dir,
            image_urls=["https://cdn.example/frame-01.png"],
            request_fn=fail_request,
        )
    except runner.OpenRouterVideoRunnerError as exc:
        assert "Storyboard is not ready" in str(exc)
        assert "asset 01 is not validated" in str(exc)
    else:
        raise AssertionError("Expected OpenRouterVideoRunnerError")
