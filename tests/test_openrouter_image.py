import json
import base64
import os

import pytest

from viral_social_test_loader import load_script


manifest = load_script("manifest")
openrouter_image = load_script("openrouter_image")


def test_build_payload_uses_requested_size_and_quality():
    payload = openrouter_image.build_payload(
        "Make a carousel cover.",
        model="test-model",
        size="1152x1536",
        quality="high",
    )

    content = payload["messages"][0]["content"][0]["text"]
    assert payload["model"] == "test-model"
    assert payload["size"] == "1152x1536"
    assert payload["quality"] == "high"
    assert "1152x1536" in content
    assert "high quality" in content


def test_dry_run_prints_redacted_payload_without_api_key(tmp_path, monkeypatch, capsys):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Render this.", encoding="utf-8")
    reference = tmp_path / "reference.png"
    reference.write_bytes(b"image bytes")

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(openrouter_image, "LOCAL_ENV", tmp_path / "missing.env.local")
    monkeypatch.setattr(
        openrouter_image.image_provider,
        "LOCAL_ENV",
        tmp_path / "missing.env.local",
    )

    openrouter_image.main(
        [
            "--prompt-file",
            str(prompt),
            "--out-dir",
            str(tmp_path / "out"),
            "--reference",
            str(reference),
            "--dry-run",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert output["api_key_set"] is False
    assert output["payload"]["model"] == "openai/gpt-5.4-image-2"
    assert output["payload"]["messages"][0]["content"][1]["image_url"]["url"] == "<redacted data URL>"
    assert "image bytes" not in json.dumps(output)


def test_dry_run_does_not_mark_manifest_prompted(tmp_path, monkeypatch, capsys):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Render this.", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest.create(manifest_path, "xiaohongshu", ["01"])

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(openrouter_image, "LOCAL_ENV", tmp_path / "missing.env.local")
    monkeypatch.setattr(
        openrouter_image.image_provider,
        "LOCAL_ENV",
        tmp_path / "missing.env.local",
    )

    openrouter_image.main(
        [
            "--prompt-file",
            str(prompt),
            "--out-dir",
            str(tmp_path / "out"),
            "--manifest",
            str(manifest_path),
            "--asset-id",
            "01",
            "--dry-run",
        ]
    )

    capsys.readouterr()
    assert manifest.load(manifest_path)["assets"]["01"]["status"] == "pending"


def test_main_skips_validated_asset_without_api_key(tmp_path, monkeypatch, capsys):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Render this.", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest.create(manifest_path, "xiaohongshu", ["01"])
    manifest.mark(manifest_path, "01", "validated", output="generated/01.png")

    def unexpected_request(payload, api_key, endpoint):
        raise AssertionError("OpenRouter should not be called")

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(openrouter_image, "LOCAL_ENV", tmp_path / "missing.env.local")
    monkeypatch.setattr(
        openrouter_image.image_provider,
        "LOCAL_ENV",
        tmp_path / "missing.env.local",
    )
    monkeypatch.setattr(openrouter_image, "post_json", unexpected_request)

    openrouter_image.main(
        [
            "--prompt-file",
            str(prompt),
            "--out-dir",
            str(tmp_path / "generated"),
            "--manifest",
            str(manifest_path),
            "--asset-id",
            "01",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert output == {
        "skipped": True,
        "reason": "asset already validated",
        "asset_id": "01",
        "status": "validated",
    }
    assert manifest.load(manifest_path)["assets"]["01"]["status"] == "validated"


def test_request_with_retries_stops_after_same_http_error_twice():
    calls = []

    def failing_request(payload, api_key, endpoint):
        calls.append(endpoint)
        raise openrouter_image.OpenRouterHTTPError(502, "bad gateway")

    try:
        openrouter_image.request_with_retries(
            {"messages": []},
            "secret",
            endpoint="https://example.test",
            max_attempts=5,
            request_fn=failing_request,
        )
    except openrouter_image.OpenRouterHTTPError as exc:
        assert exc.attempts == 2
    else:
        raise AssertionError("Expected OpenRouterHTTPError")

    assert calls == ["https://example.test", "https://example.test"]


def test_main_marks_manifest_failed_after_repeated_http_error(tmp_path, monkeypatch):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Render this.", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest.create(manifest_path, "xiaohongshu", ["01"])
    calls = []

    def failing_request(payload, api_key, endpoint):
        calls.append(endpoint)
        raise openrouter_image.OpenRouterHTTPError(502, "bad gateway")

    monkeypatch.setenv("OPENROUTER_API_KEY", "secret")
    monkeypatch.setattr(openrouter_image, "LOCAL_ENV", tmp_path / "missing.env.local")
    monkeypatch.setattr(
        openrouter_image.image_provider,
        "LOCAL_ENV",
        tmp_path / "missing.env.local",
    )
    monkeypatch.setattr(openrouter_image, "post_json", failing_request)

    try:
        openrouter_image.main(
            [
                "--prompt-file",
                str(prompt),
                "--out-dir",
                str(tmp_path / "out"),
                "--manifest",
                str(manifest_path),
                "--asset-id",
                "01",
                "--max-attempts",
                "5",
            ]
        )
    except SystemExit as exc:
        assert "OpenRouter HTTP 502" in str(exc)
    else:
        raise AssertionError("Expected SystemExit")

    data = manifest.load(manifest_path)
    asset = data["assets"]["01"]
    assert len(calls) == 2
    assert asset["status"] == "failed"
    assert asset["attempts"] == 2
    assert asset["last_error"]["code"] == 502
    assert asset["last_error"]["attempts"] == 2
    assert asset["validation_errors"] == ["OpenRouter HTTP 502: bad gateway"]


def test_main_marks_manifest_prompted_before_request(tmp_path, monkeypatch):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Render this.", encoding="utf-8")
    reference = tmp_path / "reference.png"
    reference.write_bytes(b"image bytes")
    manifest_path = tmp_path / "analysis" / "manifest.json"
    manifest.create(manifest_path, "xiaohongshu", ["01"])
    observed = {}

    def failing_request(payload, api_key, endpoint):
        observed["asset"] = manifest.load(manifest_path)["assets"]["01"]
        raise openrouter_image.OpenRouterHTTPError(502, "bad gateway")

    monkeypatch.setenv("OPENROUTER_API_KEY", "secret")
    monkeypatch.setattr(openrouter_image, "LOCAL_ENV", tmp_path / "missing.env.local")
    monkeypatch.setattr(
        openrouter_image.image_provider,
        "LOCAL_ENV",
        tmp_path / "missing.env.local",
    )
    monkeypatch.setattr(openrouter_image, "post_json", failing_request)

    try:
        openrouter_image.main(
            [
                "--prompt-file",
                str(prompt),
                "--out-dir",
                str(tmp_path / "generated"),
                "--reference",
                str(reference),
                "--manifest",
                str(manifest_path),
                "--asset-id",
                "01",
                "--max-attempts",
                "1",
            ]
        )
    except SystemExit:
        pass
    else:
        raise AssertionError("Expected SystemExit")

    asset = observed["asset"]
    assert asset["status"] == "prompted"
    assert asset["prompt_path"] == "prompt.txt"
    assert asset["request"]["endpoint"] == openrouter_image.ENDPOINT
    content = asset["request"]["payload"]["messages"][0]["content"]
    assert content[1]["image_url"]["url"] == "<redacted data URL>"
    assert "image bytes" not in json.dumps(asset["request"])


def test_main_marks_manifest_generated_after_saving_image(tmp_path, monkeypatch, capsys):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Render this.", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest.create(manifest_path, "instagram-facebook", ["01"])
    encoded = base64.b64encode(b"png bytes").decode("ascii")

    def successful_request(payload, api_key, endpoint):
        return {
            "choices": [
                {
                    "message": {
                        "images": [
                            {"image_url": {"url": f"data:image/png;base64,{encoded}"}}
                        ]
                    }
                }
            ]
        }

    monkeypatch.setenv("OPENROUTER_API_KEY", "secret")
    monkeypatch.setattr(openrouter_image, "LOCAL_ENV", tmp_path / "missing.env.local")
    monkeypatch.setattr(
        openrouter_image.image_provider,
        "LOCAL_ENV",
        tmp_path / "missing.env.local",
    )
    monkeypatch.setattr(openrouter_image, "post_json", successful_request)

    openrouter_image.main(
        [
            "--prompt-file",
            str(prompt),
            "--out-dir",
            str(tmp_path / "generated"),
            "--stem",
            "01",
            "--manifest",
            str(manifest_path),
            "--asset-id",
            "01",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    saved_path = tmp_path / "generated" / "01-1-1.png"
    assert output["saved"] == [str(saved_path)]
    assert saved_path.read_bytes() == b"png bytes"

    data = manifest.load(manifest_path)
    asset = data["assets"]["01"]
    assert asset["status"] == "generated"
    assert asset["attempts"] == 1
    assert asset["output"] == "generated/01-1-1.png"
    assert asset["outputs"] == ["generated/01-1-1.png"]
    assert asset["prompt_path"] == "prompt.txt"
    assert asset["request"]["payload"]["model"] == "openai/gpt-5.4-image-2"
    assert asset["validation_errors"] == []


def test_force_regenerates_validated_asset(tmp_path, monkeypatch, capsys):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Render this.", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest.create(manifest_path, "instagram-facebook", ["01"])
    manifest.mark(manifest_path, "01", "validated", output="generated/old.png")
    encoded = base64.b64encode(b"new png").decode("ascii")
    calls = []

    def successful_request(payload, api_key, endpoint):
        calls.append(endpoint)
        return {
            "choices": [
                {
                    "message": {
                        "images": [
                            {"image_url": {"url": f"data:image/png;base64,{encoded}"}}
                        ]
                    }
                }
            ]
        }

    monkeypatch.setenv("OPENROUTER_API_KEY", "secret")
    monkeypatch.setattr(openrouter_image, "LOCAL_ENV", tmp_path / "missing.env.local")
    monkeypatch.setattr(
        openrouter_image.image_provider,
        "LOCAL_ENV",
        tmp_path / "missing.env.local",
    )
    monkeypatch.setattr(openrouter_image, "post_json", successful_request)

    openrouter_image.main(
        [
            "--prompt-file",
            str(prompt),
            "--out-dir",
            str(tmp_path / "generated"),
            "--stem",
            "01",
            "--manifest",
            str(manifest_path),
            "--asset-id",
            "01",
            "--force",
        ]
    )

    capsys.readouterr()
    data = manifest.load(manifest_path)
    assert calls == [openrouter_image.ENDPOINT]
    assert data["assets"]["01"]["status"] == "generated"
    assert data["assets"]["01"]["output"] == "generated/01-1-1.png"


def test_live_openrouter_contract_generates_image(tmp_path):
    if os.environ.get("VSR_RUN_LIVE_TESTS") != "1":
        pytest.skip("set VSR_RUN_LIVE_TESTS=1 to run live OpenRouter contract test")

    config = openrouter_image.resolve_generation_config()
    if not config["api_key"]:
        pytest.skip("OPENROUTER_API_KEY is not set")

    prompt = tmp_path / "prompt.txt"
    prompt.write_text(
        (
            "Contract test image. Create a simple clean square graphic with "
            "the text VSR TEST. No brands, no people."
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "analysis" / "manifest.json"
    manifest.create(manifest_path, "instagram-facebook", ["live"])

    result = openrouter_image.generate_image(
        prompt_file=prompt,
        out_dir=tmp_path / "generated",
        stem="live",
        size="1152x1152",
        manifest_path=manifest_path,
        asset_id="live",
        max_attempts=1,
    )

    assert result["saved"]
    for saved in result["saved"]:
        assert os.path.isfile(saved)
    asset = manifest.load(manifest_path)["assets"]["live"]
    assert asset["status"] == "generated"
    assert asset["output"]


def test_main_marks_manifest_failed_when_response_has_no_images(tmp_path, monkeypatch):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Render this.", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest.create(manifest_path, "instagram-facebook", ["01"])

    def empty_request(payload, api_key, endpoint):
        return {"choices": [{"message": {"content": "no image here"}}]}

    monkeypatch.setenv("OPENROUTER_API_KEY", "secret")
    monkeypatch.setattr(openrouter_image, "LOCAL_ENV", tmp_path / "missing.env.local")
    monkeypatch.setattr(
        openrouter_image.image_provider,
        "LOCAL_ENV",
        tmp_path / "missing.env.local",
    )
    monkeypatch.setattr(openrouter_image, "post_json", empty_request)

    try:
        openrouter_image.main(
            [
                "--prompt-file",
                str(prompt),
                "--out-dir",
                str(tmp_path / "generated"),
                "--manifest",
                str(manifest_path),
                "--asset-id",
                "01",
            ]
        )
    except SystemExit as exc:
        assert "did not contain any images" in str(exc)
    else:
        raise AssertionError("Expected SystemExit")

    data = manifest.load(manifest_path)
    asset = data["assets"]["01"]
    assert asset["status"] == "failed"
    assert asset["attempts"] == 1
    assert asset["last_error"]["type"] == "openrouter_image"
    assert asset["validation_errors"] == [
        "OpenRouter response did not contain any images"
    ]
