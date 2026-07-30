import json
from pathlib import Path

from PIL import Image

from viral_social_test_loader import load_script


manifest = load_script("manifest")
runner = load_script("run_seedance_video")


def _isolated_seedance_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(runner, "LOCAL_ENV", tmp_path / ".env.local")
    for name in runner.KEY_ENV_NAMES + [
        "VSR_SEEDANCE_ENDPOINT",
        "VSR_SEEDANCE_MODEL",
        "VSR_SEEDANCE_RATIO",
        "VSR_SEEDANCE_DURATION",
        "VSR_SEEDANCE_RESOLUTION",
        "VSR_SEEDANCE_GENERATE_AUDIO",
        "VSR_SEEDANCE_WATERMARK",
    ]:
        monkeypatch.delenv(name, raising=False)


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


def _prepared_compact_video_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "output" / "compact"
    analysis = run_dir / "analysis"
    refs = run_dir / "references"
    analysis.mkdir(parents=True)
    refs.mkdir(parents=True)
    (analysis / "seedance-prompt.md").write_text(
        "Create a 6-second no-face cooking video. Shot 1 opening setup, Shot 2 cooking, Shot 3 final hero.",
        encoding="utf-8",
    )
    (analysis / "shot-list.md").write_text(
        "Shot 1 opening third\nShot 2 middle third\nShot 3 final third",
        encoding="utf-8",
    )
    manifest.create(
        analysis / "manifest.json",
        "vertical-video",
        ["01", "02", "03"],
    )
    data = manifest.load(analysis / "manifest.json")
    data["video_mode"] = "compact-reference"
    for index in range(1, 4):
        data["assets"][f"{index:02d}"]["storyboard_url"] = (
            f"https://cdn.example/reference-{index:02d}.png"
        )
    (analysis / "manifest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return run_dir


def _prepared_three_clip_storyboard_run(tmp_path: Path) -> Path:
    run_dir = _prepared_video_run(tmp_path)
    prompt_dir = run_dir / "analysis" / "seedance-prompts"
    prompt_dir.mkdir()
    for index in range(1, 4):
        (prompt_dir / f"clip-{index:02d}.md").write_text(
            f"Animate cooking clip {index} with realistic motion.",
            encoding="utf-8",
        )
    manifest_path = run_dir / "analysis" / "manifest.json"
    data = manifest.load(manifest_path)
    data["schema_version"] = 2
    data["video_mode"] = "storyboard-three-clips"
    data["video"] = {
        "mode": "storyboard-three-clips",
        "profile": "final-clip",
        "generation": {
            "ratio": "9:16",
            "duration": 6,
            "resolution": "1080p",
            "generate_audio": False,
            "return_last_frame": False,
            "watermark": False,
        },
        "budget": {"retry_limit": 1, "stop_before_final": False},
    }
    data["video_workflow"] = {
        "status": "prepared",
        "visual_qa": "not_started",
        "chatcut": "not_started",
        "export_qa": "not_started",
        "history": [],
        "clips": {
            f"clip-{index:02d}": {
                "frames": [
                    f"{(index - 1) * 3 + offset:02d}"
                    for offset in range(1, 4)
                ],
                "status": "prepared",
            }
            for index in range(1, 4)
        },
    }
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return run_dir


def _prepared_director_three_clip_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "output" / "director"
    analysis = run_dir / "analysis"
    generated = run_dir / "generated"
    prompt_dir = analysis / "seedance-prompts"
    prompt_dir.mkdir(parents=True)
    generated.mkdir(parents=True)
    (analysis / "seedance-prompt.md").write_text(
        "Create a premium no-face cooking commercial.",
        encoding="utf-8",
    )
    (analysis / "shot-list.md").write_text(
        "Clip 1 hook\nClip 2 cook\nClip 3 finish",
        encoding="utf-8",
    )
    for index in range(1, 4):
        (prompt_dir / f"clip-{index:02d}.md").write_text(
            f"Animate clip {index} from its opening frame with one camera move.",
            encoding="utf-8",
        )
        Image.new("RGB", (1080, 1920), "white").save(
            generated / f"page-{index:02d}.png"
        )
    manifest_path = analysis / "manifest.json"
    manifest.create(manifest_path, "vertical-video", ["01", "02", "03"])
    data = manifest.load(manifest_path)
    data["schema_version"] = 2
    data["video_mode"] = "director-first-frame-three-clips"
    data["video"] = {
        "mode": "director-first-frame-three-clips",
        "profile": "final-clip",
        "generation": {
            "ratio": "9:16",
            "duration": 6,
            "resolution": "1080p",
            "generate_audio": False,
            "return_last_frame": True,
            "watermark": False,
        },
        "budget": {"retry_limit": 1, "stop_before_final": False},
    }
    data["video_workflow"] = {
        "status": "prepared",
        "visual_qa": "not_started",
        "chatcut": "not_started",
        "export_qa": "not_started",
        "history": [],
        "clips": {
            f"clip-{index:02d}": {
                "frames": [f"{index:02d}"],
                "status": "prepared",
            }
            for index in range(1, 4)
        },
    }
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return run_dir


def _prepared_multimodal_video_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "output" / "multimodal"
    analysis = run_dir / "analysis"
    analysis.mkdir(parents=True)
    (analysis / "seedance-prompt.md").write_text(
        "Use {{ref:food}} for the opening and {{ref:product}} for package "
        "fidelity. Follow the camera rhythm from {{ref:motion}} and the "
        "ambience from {{ref:ambience}}.",
        encoding="utf-8",
    )
    (analysis / "shot-list.md").write_text(
        "Shot 1 opening third\nShot 2 middle third\nShot 3 final third",
        encoding="utf-8",
    )
    manifest.create(
        analysis / "manifest.json",
        "vertical-video",
        [],
    )
    data = manifest.load(analysis / "manifest.json")
    data["schema_version"] = 2
    data["video_mode"] = "compact-reference"
    data["video"] = {
        "mode": "compact-reference",
        "profile": "visual-preview",
        "references": [
            {
                "id": "food",
                "type": "image",
                "order": 1,
                "url": "https://cdn.example/food.png",
            },
            {
                "id": "product",
                "type": "image",
                "order": 2,
                "url": "https://cdn.example/product.png",
            },
            {
                "id": "motion",
                "type": "video",
                "order": 1,
                "url": "https://cdn.example/motion.mp4",
            },
            {
                "id": "ambience",
                "type": "audio",
                "order": 1,
                "url": "https://cdn.example/ambience.mp3",
            },
        ],
        "generation": {
            "duration": 5,
            "resolution": "1080p",
            "generate_audio": False,
            "return_last_frame": True,
            "watermark": False,
        },
        "continuity": {
            "last_frame_path": None,
            "available": False,
        },
    }
    data["video_workflow"] = {
        "status": "prepared",
        "visual_qa": "not_started",
        "chatcut": "not_started",
        "export_qa": "not_started",
        "history": [],
    }
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


def test_resolve_config_uses_byteplus_modelark_defaults_and_key_priority(
    tmp_path,
    monkeypatch,
):
    _isolated_seedance_env(tmp_path, monkeypatch)
    monkeypatch.setenv("ARK_API_KEY", "ark-key")
    monkeypatch.setenv("BYTEPLUS_ARK_API_KEY", "byteplus-key")

    config = runner.resolve_config()

    assert config["provider"] == "byteplus-modelark"
    assert config["endpoint"] == runner.DEFAULT_ENDPOINT
    assert config["model"] == "dreamina-seedance-2-0-260128"
    assert config["api_key"] == "byteplus-key"


def test_run_seedance_video_dry_run_uses_manifest_storyboard_url(tmp_path, monkeypatch):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_video_run(tmp_path)
    manifest_path = run_dir / "analysis" / "manifest.json"
    data = manifest.load(manifest_path)
    data["assets"]["01"]["storyboard_url"] = "https://cdn.example/frame-01.png"
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    result = runner.run_seedance_video(run_dir, dry_run=True)

    assert result["api_key_set"] is False
    assert result["image_count"] == 1
    assert result["endpoint"] == runner.DEFAULT_ENDPOINT
    assert result["generation"] == {
        "ratio": "9:16",
        "duration": 5,
        "resolution": "1080p",
        "generate_audio": False,
        "watermark": False,
    }
    payload = result["payload"]
    assert payload["model"] == runner.DEFAULT_MODEL
    assert payload["ratio"] == "9:16"
    assert payload["duration"] == 5
    assert payload["resolution"] == "1080p"
    assert payload["generate_audio"] is False
    assert payload["watermark"] is False
    assert payload["content"][0]["type"] == "text"
    assert "tomato egg stir-fry" in payload["content"][0]["text"]
    assert "No subtitles" in payload["content"][0]["text"]
    assert "Voiceover" in payload["content"][0]["text"]
    assert "--ratio" not in payload["content"][0]["text"]
    assert "--dur" not in payload["content"][0]["text"]
    assert payload["content"][1]["image_url"]["url"] == "https://cdn.example/frame-01.png"


def test_run_seedance_video_dry_run_can_redact_local_data_url(tmp_path, monkeypatch):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_video_run(tmp_path)

    result = runner.run_seedance_video(run_dir, dry_run=True, allow_data_url=True)

    assert result["image_count"] == 1
    assert result["payload"]["content"][1]["image_url"]["url"] == "<redacted data URL>"


def test_run_seedance_video_marks_all_storyboard_images_as_references(tmp_path, monkeypatch):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_video_run(tmp_path)
    manifest_path = run_dir / "analysis" / "manifest.json"
    data = manifest.load(manifest_path)
    for index in range(1, 10):
        data["assets"][f"{index:02d}"]["storyboard_url"] = (
            f"https://cdn.example/frame-{index:02d}.png"
        )
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    result = runner.run_seedance_video(
        run_dir,
        dry_run=True,
        include_all_frames=True,
    )

    image_items = result["payload"]["content"][1:]
    assert len(image_items) == 9
    assert all(item["role"] == "reference_image" for item in image_items)


def test_three_clip_storyboard_dry_run_selects_exact_group(tmp_path, monkeypatch):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_three_clip_storyboard_run(tmp_path)

    result = runner.run_seedance_video(
        run_dir,
        storyboard_group=2,
        allow_data_url=True,
        dry_run=True,
    )

    assert result["video_mode"] == "storyboard-three-clips"
    assert result["storyboard_group"] == 2
    assert result["image_count"] == 3
    assert result["generation"]["duration"] == 6
    assert result["generation"]["generate_audio"] is False
    assert "frames 04-06" in result["payload"]["content"][0]["text"]
    assert [
        item["image_url"]["url"]
        for item in result["payload"]["content"][1:]
    ] == ["<redacted data URL>"] * 3


def test_director_three_clip_dry_run_uses_only_matching_first_frame(
    tmp_path,
    monkeypatch,
):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_director_three_clip_run(tmp_path)

    result = runner.run_seedance_video(
        run_dir,
        storyboard_group=2,
        allow_data_url=True,
        dry_run=True,
    )

    assert result["video_mode"] == "director-first-frame-three-clips"
    assert result["storyboard_group"] == 2
    assert result["image_count"] == 1
    assert result["generation"]["duration"] == 6
    assert result["generation"]["generate_audio"] is False
    assert "planned frame 02" in result["payload"]["content"][0]["text"]
    assert "generated transition opening anchor" in result["payload"]["content"][0]["text"]
    assert "continuity repair frame" not in result["payload"]["content"][0]["text"]
    assert [
        item["image_url"]["url"]
        for item in result["payload"]["content"][1:]
    ] == ["<redacted data URL>"]


def test_director_three_clip_can_use_previous_last_frame_without_page_two(
    tmp_path,
    monkeypatch,
):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_director_three_clip_run(tmp_path)
    (run_dir / "generated" / "page-02.png").unlink()
    previous = run_dir / "generated" / "clip-01-last-frame.png"
    Image.new("RGB", (1080, 1920), "white").save(previous)
    manifest_path = run_dir / "analysis" / "manifest.json"
    data = manifest.load(manifest_path)
    data["video"]["continuity"] = {
        "clips": {
            "clip-01": {
                "last_frame_path": "generated/clip-01-last-frame.png",
                "available": True,
            }
        }
    }
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = runner.run_seedance_video(
        run_dir,
        storyboard_group=2,
        allow_data_url=True,
        continue_from_last_frame=True,
        dry_run=True,
    )

    assert result["video_mode"] == "director-first-frame-three-clips"
    assert result["storyboard_group"] == 2
    assert result["image_count"] == 1
    assert result["preflight"]["references"][0]["source"] == (
        "generated/clip-01-last-frame.png"
    )
    assert [
        item["image_url"]["url"]
        for item in result["payload"]["content"][1:]
    ] == ["<redacted data URL>"]


def test_three_clip_storyboard_requires_group(tmp_path, monkeypatch):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_three_clip_storyboard_run(tmp_path)

    try:
        runner.run_seedance_video(run_dir, allow_data_url=True, dry_run=True)
    except runner.SeedanceRunnerError as exc:
        assert "--storyboard-group 1, 2, or 3" in str(exc)
    else:
        raise AssertionError("Expected SeedanceRunnerError")


def test_three_clip_storyboard_tracks_each_paid_clip_separately(tmp_path, monkeypatch):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_three_clip_storyboard_run(tmp_path)
    _mark_storyboard_validated(run_dir)
    monkeypatch.setenv("BYTEPLUS_ARK_API_KEY", "test-key")

    def fake_request(method, url, api_key, payload):
        if method == "POST":
            assert len(payload["content"][1:]) == 3
            return {"id": "task"}
        return {
            "id": "task",
            "status": "succeeded",
            "content": {"video_url": "https://cdn.example/clip.mp4"},
        }

    def fake_download(url, output):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"clip")

    for group in range(1, 4):
        result = runner.run_seedance_video(
            run_dir,
            storyboard_group=group,
            allow_data_url=True,
            request_fn=fake_request,
            download_fn=fake_download,
            poll_interval=0,
        )
        assert result["output"] == f"generated/seedance-clip-{group:02d}.mp4"

    data = manifest.load(run_dir / "analysis" / "manifest.json")
    assert list(data["video_generations"]) == [
        "clip-01",
        "clip-02",
        "clip-03",
    ]
    assert all(
        item["status"] == "succeeded"
        for item in data["video_generations"].values()
    )
    assert data["video_workflow"]["status"] == "generated"
    assert all(
        item["status"] == "generated"
        for item in data["video_workflow"]["clips"].values()
    )


def test_run_seedance_video_compact_reference_sends_all_manifest_references_by_default(
    tmp_path,
    monkeypatch,
):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_compact_video_run(tmp_path)

    result = runner.run_seedance_video(run_dir, dry_run=True)

    assert result["video_mode"] == "compact-reference"
    assert result["image_count"] == 3
    image_items = result["payload"]["content"][1:]
    assert [item["image_url"]["url"] for item in image_items] == [
        "https://cdn.example/reference-01.png",
        "https://cdn.example/reference-02.png",
        "https://cdn.example/reference-03.png",
    ]
    assert all(item["role"] == "reference_image" for item in image_items)


def test_run_seedance_video_compiles_and_sends_multimodal_references(
    tmp_path,
    monkeypatch,
):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_multimodal_video_run(tmp_path)

    result = runner.run_seedance_video(run_dir, dry_run=True)

    assert result["profile"] == "visual-preview"
    assert result["image_count"] == 2
    assert result["video_count"] == 1
    assert result["audio_count"] == 1
    assert result["reference_count"] == 4
    assert result["generation"]["generate_audio"] is False
    assert result["payload"]["return_last_frame"] is True
    prompt = result["payload"]["content"][0]["text"]
    assert "[Image 1]" in prompt
    assert "[Image 2]" in prompt
    assert "[Video 1]" in prompt
    assert "[Audio 1]" in prompt
    assert "{{ref:" not in prompt
    assert [item["type"] for item in result["payload"]["content"][1:]] == [
        "image_url",
        "image_url",
        "video_url",
        "audio_url",
    ]
    assert [item["role"] for item in result["payload"]["content"][1:]] == [
        "reference_image",
        "reference_image",
        "reference_video",
        "reference_audio",
    ]


def test_run_seedance_video_rejects_official_duration_violation(
    tmp_path,
    monkeypatch,
):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_multimodal_video_run(tmp_path)

    try:
        runner.run_seedance_video(run_dir, dry_run=True, duration="3")
    except runner.SeedanceRunnerError as exc:
        assert "between 4 and 15" in str(exc)
    else:
        raise AssertionError("Expected SeedanceRunnerError")


def test_run_seedance_video_compact_reference_can_submit_without_nine_validated_frames(
    tmp_path,
    monkeypatch,
):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_compact_video_run(tmp_path)
    monkeypatch.setenv("BYTEPLUS_ARK_API_KEY", "test-key")
    calls = []

    def fake_request(method, url, api_key, payload):
        calls.append((method, payload))
        if method == "POST":
            assert len(payload["content"][1:]) == 3
            return {"id": "cgt-compact"}
        return {
            "id": "cgt-compact",
            "status": "succeeded",
            "content": {"video_url": "https://cdn.example/compact.mp4"},
            "usage": {"total_tokens": 456},
        }

    def fake_download(url, output):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"compact mp4")

    result = runner.run_seedance_video(
        run_dir,
        timeout_seconds=10,
        poll_interval=0,
        request_fn=fake_request,
        download_fn=fake_download,
    )

    assert [call[0] for call in calls] == ["POST", "GET"]
    assert result["video_mode"] == "compact-reference"
    assert result["output"] == "generated/seedance-video.mp4"


def test_run_seedance_video_downloads_and_registers_last_frame(
    tmp_path,
    monkeypatch,
):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_multimodal_video_run(tmp_path)
    monkeypatch.setenv("BYTEPLUS_ARK_API_KEY", "test-key")
    downloads = []

    def fake_request(method, url, api_key, payload):
        if method == "POST":
            assert payload["return_last_frame"] is True
            return {"id": "cgt-last-frame"}
        return {
            "id": "cgt-last-frame",
            "status": "succeeded",
            "content": {
                "video_url": "https://cdn.example/final.mp4",
                "last_frame_url": "https://cdn.example/final-frame.png",
            },
            "usage": {"total_tokens": 789},
        }

    def fake_download(url, output):
        downloads.append((url, output.name))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"download")

    result = runner.run_seedance_video(
        run_dir,
        timeout_seconds=10,
        poll_interval=0,
        request_fn=fake_request,
        download_fn=fake_download,
    )

    assert downloads == [
        ("https://cdn.example/final.mp4", "seedance-video.mp4"),
        (
            "https://cdn.example/final-frame.png",
            "seedance-video-last-frame.png",
        ),
    ]
    assert result["last_frame_output"] == (
        "generated/seedance-video-last-frame.png"
    )
    assert "video_url" not in result
    lock_path = run_dir / "analysis" / "seedance-request.lock.json"
    assert lock_path.is_file()
    request_lock = json.loads(lock_path.read_text(encoding="utf-8"))
    assert request_lock["request_sha256"] == result["request_sha256"]
    assert all(
        item.get(item["type"], {}).get("url") == "<external URL>"
        for item in request_lock["payload"]["content"][1:]
    )
    assert all(
        reference["source"] == "<external URL>"
        for reference in request_lock["references"]
    )

    data = manifest.load(run_dir / "analysis" / "manifest.json")
    assert data["video"]["continuity"] == {
        "last_frame_path": "generated/seedance-video-last-frame.png",
        "available": True,
    }
    assert data["video_workflow"]["status"] == "generated"
    assert data["video_workflow"]["visual_qa"] == "pending"
    assert data["video_generation"]["request_sha256"] == result["request_sha256"]


def test_run_seedance_video_records_create_failure_and_attempt(tmp_path, monkeypatch):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_multimodal_video_run(tmp_path)
    monkeypatch.setenv("BYTEPLUS_ARK_API_KEY", "test-key")

    def fail_create(method, url, api_key, payload):
        assert method == "POST"
        raise runner.SeedanceHTTPError(503, "provider unavailable")

    try:
        runner.run_seedance_video(
            run_dir,
            request_fn=fail_create,
        )
    except runner.SeedanceHTTPError:
        pass
    else:
        raise AssertionError("Expected SeedanceHTTPError")

    data = manifest.load(run_dir / "analysis" / "manifest.json")
    assert data["video_generation"]["status"] == "failed"
    assert data["video_generation"]["attempts"] == 1
    assert data["video_generation"]["last_error"]["type"] == (
        "SeedanceHTTPError"
    )
    assert data["video_workflow"]["status"] == "failed"
    assert [event["status"] for event in data["video_workflow"]["history"]] == [
        "preflight_validated",
        "failed",
    ]


def test_run_seedance_video_can_continue_from_registered_last_frame(
    tmp_path,
    monkeypatch,
):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_multimodal_video_run(tmp_path)
    previous = run_dir / "generated" / "previous-last-frame.png"
    previous.parent.mkdir(parents=True)
    Image.new("RGB", (1080, 1920), "white").save(previous)
    manifest_path = run_dir / "analysis" / "manifest.json"
    data = manifest.load(manifest_path)
    data["video"]["continuity"] = {
        "last_frame_path": "generated/previous-last-frame.png",
        "available": True,
    }
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = runner.run_seedance_video(
        run_dir,
        dry_run=True,
        allow_data_url=True,
        continue_from_last_frame=True,
    )

    assert result["image_count"] == 3
    image_items = [
        item
        for item in result["payload"]["content"]
        if item["type"] == "image_url"
    ]
    assert image_items[0]["image_url"]["url"] == "<redacted data URL>"
    assert "[Image 2]" in result["payload"]["content"][0]["text"]
    assert "[Image 3]" in result["payload"]["content"][0]["text"]


def test_run_seedance_video_rejects_seed_for_default_seedance_2(tmp_path, monkeypatch):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_video_run(tmp_path)

    try:
        runner.run_seedance_video(
            run_dir,
            dry_run=True,
            image_urls=["https://cdn.example/frame-01.png"],
            seed=11,
        )
    except runner.SeedanceRunnerError as exc:
        assert "Seedance 2.0 does not support --seed" in str(exc)
    else:
        raise AssertionError("Expected SeedanceRunnerError")


def test_run_seedance_video_requires_storyboard_url_by_default(tmp_path, monkeypatch):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_video_run(tmp_path)

    try:
        runner.run_seedance_video(run_dir, dry_run=True)
    except runner.SeedanceRunnerError as exc:
        assert "reference image URL" in str(exc)
    else:
        raise AssertionError("Expected SeedanceRunnerError")


def test_run_seedance_video_submits_polls_downloads_and_updates_manifest(
    tmp_path,
    monkeypatch,
):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_video_run(tmp_path)
    _mark_storyboard_validated(run_dir)
    monkeypatch.setenv("BYTEPLUS_ARK_API_KEY", "test-key")
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
            assert api_key == "test-key"
            assert payload["model"] == runner.DEFAULT_MODEL
            assert payload["ratio"] == "9:16"
            assert payload["duration"] == 5
            assert payload["resolution"] == "1080p"
            assert payload["generate_audio"] is False
            assert payload["watermark"] is False
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
    assert data["video_generation"]["generation"]["resolution"] == "1080p"


def test_run_seedance_video_rejects_unvalidated_storyboard_before_post(
    tmp_path,
    monkeypatch,
):
    _isolated_seedance_env(tmp_path, monkeypatch)
    run_dir = _prepared_video_run(tmp_path)
    monkeypatch.setenv("BYTEPLUS_ARK_API_KEY", "test-key")

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
