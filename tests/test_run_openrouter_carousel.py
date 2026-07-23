import base64
from io import BytesIO
import json
from pathlib import Path

from PIL import Image

from viral_social_test_loader import load_script


manifest = load_script("manifest")
runner = load_script("run_openrouter_carousel")


def _data_image(size: tuple[int, int]) -> str:
    buffer = BytesIO()
    Image.new("RGB", size, "white").save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _response(size: tuple[int, int], cost: float = 0.01) -> dict:
    return {
        "choices": [
            {
                "message": {
                    "images": [
                        {"image_url": {"url": _data_image(size)}},
                    ],
                },
            }
        ],
        "usage": {"total_tokens": 12, "cost": cost, "currency": "USD"},
    }


def _prepared_run(tmp_path: Path, platform: str, assets: list[str]) -> Path:
    run_dir = tmp_path / "output" / "run"
    analysis = run_dir / "analysis"
    page_prompts = analysis / "page-prompts"
    page_prompts.mkdir(parents=True)
    caption = (
        "caption-zh.txt"
        if platform == "xiaohongshu"
        else "caption-en.txt"
    )
    for name in ["breakdown.md", "copy.md", "prompts.md", caption]:
        (analysis / name).write_text("fixture", encoding="utf-8")
    if platform == "vertical-video":
        for name in ["brief.md", "shot-list.md", "seedance-prompt.md"]:
            (analysis / name).write_text("fixture", encoding="utf-8")
    for asset_id in assets:
        (page_prompts / f"page-{asset_id}.md").write_text(
            f"Prompt for {asset_id}",
            encoding="utf-8",
        )
    manifest.create(analysis / "manifest.json", platform, assets)
    return run_dir


def test_run_openrouter_carousel_generates_pages_and_writes_outputs(tmp_path, monkeypatch):
    run_dir = _prepared_run(tmp_path, "instagram-facebook", ["01", "02"])
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    calls = []

    def fake_request(payload, api_key, endpoint):
        calls.append((payload["size"], api_key, endpoint))
        return _response((1152, 1152), cost=0.01)

    result = runner.run_carousel(
        run_dir,
        api_only=True,
        concurrency=2,
        request_fn=fake_request,
    )

    assert len(calls) == 2
    assert {call[0] for call in calls} == {"1152x1152"}
    assert (run_dir / "raw" / "page-01-response.json").is_file()
    assert (run_dir / "raw" / "page-02-response.json").is_file()
    assert (run_dir / "generated" / "page-01.png").is_file()
    assert (run_dir / "generated" / "page-02.png").is_file()
    assert (run_dir / "overview" / "contact-sheet.png").is_file()

    cost = json.loads((run_dir / "qa" / "openrouter-cost.json").read_text(encoding="utf-8"))
    assert cost["provider"]["api_key_set"] is True
    assert cost["total_cost"] == 0.02
    assert result["validation"]["valid"] is True

    data = manifest.load(run_dir / "analysis" / "manifest.json")
    assert data["assets"]["01"]["status"] == "validated"
    assert data["assets"]["01"]["output"] == "generated/page-01.png"


def test_run_openrouter_carousel_uses_manifest_request_reference_images(tmp_path, monkeypatch):
    run_dir = _prepared_run(tmp_path, "instagram-facebook", ["01"])
    reference = run_dir / "source" / "images" / "01.png"
    reference.parent.mkdir(parents=True)
    Image.new("RGB", (16, 16), "green").save(reference)
    data = manifest.load(run_dir / "analysis" / "manifest.json")
    data["assets"]["01"]["request"] = {"reference_images": ["source/images/01.png"]}
    (run_dir / "analysis" / "manifest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    calls = []

    def fake_request(payload, api_key, endpoint):
        calls.append(payload)
        return _response((1152, 1152), cost=0.01)

    runner.run_carousel(
        run_dir,
        api_only=True,
        concurrency=1,
        request_fn=fake_request,
    )

    content = calls[0]["messages"][0]["content"]
    assert [item["type"] for item in content] == ["text", "image_url"]
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_run_openrouter_carousel_normalizes_square_api_size(tmp_path, monkeypatch):
    run_dir = _prepared_run(tmp_path, "instagram-facebook", ["01"])
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    result = runner.run_carousel(
        run_dir,
        api_only=True,
        concurrency=1,
        request_fn=lambda payload, api_key, endpoint: _response((1024, 1024), cost=0.01),
    )

    with Image.open(run_dir / "generated" / "page-01.png") as image:
        assert image.size == (1152, 1152)
    with Image.open(run_dir / "generated-original-size" / "page-01.png") as image:
        assert image.size == (1024, 1024)
    assert result["validation"]["valid"] is True


def test_run_openrouter_carousel_generates_video_storyboard(tmp_path, monkeypatch):
    run_dir = _prepared_run(tmp_path, "video", [f"{index:02d}" for index in range(1, 10)])
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    result = runner.run_carousel(
        run_dir,
        api_only=True,
        concurrency=2,
        request_fn=lambda payload, api_key, endpoint: _response((1920, 1080), cost=0.01),
    )

    assert (run_dir / "generated" / "page-01.png").is_file()
    assert (run_dir / "generated" / "page-09.png").is_file()
    assert (run_dir / "overview" / "contact-sheet.png").is_file()
    with Image.open(run_dir / "overview" / "contact-sheet.png") as image:
        assert image.size == (1920, 1080)
    assert result["validation"]["valid"] is True


def test_run_openrouter_carousel_generates_english_vertical_storyboard(tmp_path, monkeypatch):
    run_dir = _prepared_run(
        tmp_path,
        "vertical-video",
        [f"{index:02d}" for index in range(1, 10)],
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    result = runner.run_carousel(
        run_dir,
        api_only=True,
        concurrency=2,
        request_fn=lambda payload, api_key, endpoint: _response((1080, 1920), cost=0.01),
    )

    assert (run_dir / "generated" / "page-01.png").is_file()
    assert (run_dir / "generated" / "page-09.png").is_file()
    with Image.open(run_dir / "generated" / "page-01.png") as image:
        assert image.size == (1080, 1920)
    with Image.open(run_dir / "overview" / "contact-sheet.png") as image:
        assert image.size == (1080, 1920)
    assert result["validation"]["valid"] is True


def test_run_openrouter_carousel_skips_existing_correct_size_without_key(tmp_path, monkeypatch):
    run_dir = _prepared_run(tmp_path, "xiaohongshu", ["01"])
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    generated = run_dir / "generated"
    generated.mkdir(parents=True)
    Image.new("RGB", (1152, 1536), "white").save(generated / "page-01.png")

    def fail_request(*args, **kwargs):
        raise AssertionError("request should not be called for a valid existing page")

    result = runner.run_carousel(
        run_dir,
        api_only=True,
        concurrency=2,
        request_fn=fail_request,
    )

    assert len(result["skipped"]) == 1
    assert result["validation"]["valid"] is True
    data = manifest.load(run_dir / "analysis" / "manifest.json")
    assert data["assets"]["01"]["status"] == "validated"


def test_run_openrouter_carousel_api_only_stops_on_failure(tmp_path, monkeypatch):
    run_dir = _prepared_run(tmp_path, "xiaohongshu", ["01", "02", "03"])
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_request(payload, api_key, endpoint):
        if "Prompt for 02" in payload["messages"][0]["content"][0]["text"]:
            raise runner.openrouter_image.OpenRouterHTTPError(500, "boom")
        return _response((1152, 1536), cost=0.01)

    try:
        runner.run_carousel(
            run_dir,
            api_only=True,
            concurrency=1,
            max_attempts=1,
            request_fn=fake_request,
        )
    except runner.CarouselRunnerError as exc:
        assert "API-only generation failed for 02" in str(exc)
    else:
        raise AssertionError("Expected API-only failure")

    assert (run_dir / "generated" / "page-01.png").is_file()
    assert not (run_dir / "generated" / "page-03.png").exists()
    data = manifest.load(run_dir / "analysis" / "manifest.json")
    assert data["assets"]["01"]["status"] == "validated"
    assert data["assets"]["02"]["status"] == "failed"
    assert data["assets"]["03"]["status"] == "pending"

    cost = json.loads((run_dir / "qa" / "openrouter-cost.json").read_text(encoding="utf-8"))
    assert cost["errors"][0]["asset_id"] == "02"


def test_run_openrouter_carousel_rejects_more_than_two_concurrent_requests(tmp_path):
    run_dir = _prepared_run(tmp_path, "instagram-facebook", ["01"])

    try:
        runner.run_carousel(run_dir, concurrency=3)
    except runner.CarouselRunnerError as exc:
        assert "--concurrency must be 1 or 2" in str(exc)
    else:
        raise AssertionError("Expected concurrency validation error")


def test_run_openrouter_storyboard_rejects_wrong_asset_count_before_request(
    tmp_path,
    monkeypatch,
):
    run_dir = _prepared_run(tmp_path, "vertical-video", ["01", "02"])
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fail_request(*args, **kwargs):
        raise AssertionError("OpenRouter request should not run for invalid storyboard count")

    try:
        runner.run_carousel(run_dir, api_only=True, request_fn=fail_request)
    except runner.CarouselRunnerError as exc:
        assert "requires exactly 9 assets" in str(exc)
    else:
        raise AssertionError("Expected CarouselRunnerError")


def test_run_openrouter_rejects_markdown_todo_prompt_before_request(
    tmp_path,
    monkeypatch,
):
    run_dir = _prepared_run(
        tmp_path,
        "vertical-video",
        [f"{index:02d}" for index in range(1, 10)],
    )
    (run_dir / "analysis" / "page-prompts" / "page-01.md").write_text(
        "# Prompt\n\nTODO\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fail_request(*args, **kwargs):
        raise AssertionError("OpenRouter request should not run for TODO prompt")

    try:
        runner.run_carousel(
            run_dir,
            api_only=True,
            concurrency=1,
            request_fn=fail_request,
        )
    except runner.CarouselRunnerError as exc:
        assert "Page prompt is empty or TODO" in str(exc)
    else:
        raise AssertionError("Expected CarouselRunnerError")
