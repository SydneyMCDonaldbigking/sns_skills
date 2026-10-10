import json
from pathlib import Path

from PIL import Image
import pytest

from viral_social_test_loader import load_script


manifest = load_script("manifest")
runner = load_script("run_newb_video")


@pytest.fixture(autouse=True)
def _isolated_env(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(runner, "LOCAL_ENV", tmp_path / ".env.local")
    for name in runner.KEY_ENV_NAMES + ["VSR_NEWB_BASE_URL"]:
        monkeypatch.delenv(name, raising=False)


def _run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "output" / "run"
    analysis = run_dir / "analysis"
    analysis.mkdir(parents=True)
    (run_dir / "generated").mkdir()
    (analysis / "newb-prompt.md").write_text(
        "# director note, not sent\n@图1 里的煎饺在平底锅里煎到底部金黄，镜头缓慢推近。\n"
        "soundscape: 热油滋滋声。No dialogue, no music.",
        encoding="utf-8",
    )
    manifest.create(analysis / "manifest.json", "vertical-video", ["01"])
    Image.new("RGB", (1080, 1920), "white").save(run_dir / "generated" / "page-01.png")
    return run_dir


class FakeApi:
    def __init__(self, statuses, *, quota=None, submit=None):
        self.statuses = list(statuses)
        self.quota = quota or {"quota_remaining": 10, "membership_active": True, "active": 0, "max_concurrent": 5}
        self.submit = submit
        self.calls = []

    def __call__(self, method, url, api_key, *, body=None, content_type=None):
        self.calls.append({"method": method, "url": url, "body": body, "content_type": content_type})
        assert api_key == "wfv_test"
        if url.endswith("/api/v1/quota"):
            return 200, {}, dict(self.quota)
        if method == "POST":
            if self.submit:
                return self.submit()
            return 201, {}, {"id": "task123", "status": "queued", "quota_remaining": 9}
        return self.statuses.pop(0)


def _succeeded():
    return 200, {}, {
        "id": "task123",
        "status": "succeeded",
        "video_url": "https://video.haoniubi.cloud/api/v1/files/x?exp=1&sig=secret",
    }


def test_dry_run_reads_prompt_and_validates_images_without_key(tmp_path):
    run_dir = _run(tmp_path)
    result = runner.run_newb_video(run_dir, images=["generated/page-01.png"], dry_run=True)
    assert result["ratio"] == "9:16"
    assert result["duration_seconds"] == 30
    assert result["api_key_set"] is False
    assert result["images"][0]["label"] == "@图1"
    assert "director note" not in result["prompt"]
    assert result["warnings"] == []


def test_timeline_prompts_are_rejected_but_ratio_is_not_a_timestamp(tmp_path):
    assert runner.lint_prompt("9:16 竖屏，镜头缓慢推近") == []
    assert runner.lint_prompt("Shot 1 (0-2s) pan, 0:10 cut, 第3秒 pour")
    run_dir = _run(tmp_path)
    with pytest.raises(runner.NewBRunnerError, match="timelines"):
        runner.run_newb_video(run_dir, prompt="0-2s 开场，2-4s 特写", dry_run=True)
    result = runner.run_newb_video(
        run_dir, prompt="0-2s 开场", allow_timeline=True, dry_run=True
    )
    assert result["prompt"] == "0-2s 开场"


def test_image_limits_and_aspect_warning(tmp_path):
    run_dir = _run(tmp_path)
    square = run_dir / "square.jpg"
    Image.new("RGB", (800, 800), "white").save(square)
    result = runner.run_newb_video(run_dir, images=[str(square)], dry_run=True)
    assert "aspect ratio" in result["warnings"][0]
    gif = run_dir / "x.gif"
    Image.new("RGB", (10, 10)).save(gif)
    with pytest.raises(runner.NewBRunnerError, match="JPG, PNG, or WebP"):
        runner.run_newb_video(run_dir, images=[str(gif)], dry_run=True)
    with pytest.raises(runner.NewBRunnerError, match="at most 9"):
        runner.run_newb_video(run_dir, images=[str(square)] * 10, dry_run=True)


def test_multipart_encoding_carries_fields_and_files():
    body, content_type = runner.encode_multipart(
        [("prompt", "煎饺"), ("ratio", "9:16")],
        [("images[]", "image-01.png", "image/png", b"PNGDATA")],
        boundary="BOUND",
    )
    assert content_type == "multipart/form-data; boundary=BOUND"
    assert 'name="prompt"\r\n\r\n煎饺\r\n'.encode() in body
    assert b'name="images[]"; filename="image-01.png"\r\nContent-Type: image/png\r\n\r\nPNGDATA' in body
    assert body.endswith(b"--BOUND--\r\n")


def test_missing_no_music_line_warns(tmp_path):
    run_dir = _run(tmp_path)
    result = runner.run_newb_video(run_dir, prompt="煎饺煎到金黄", dry_run=True)
    assert any("No dialogue, no music" in warning for warning in result["warnings"])


def test_submit_poll_download_strips_audio_and_redacts_signed_url(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWB_API_KEY", "wfv_test")
    run_dir = _run(tmp_path)
    api = FakeApi([(200, {}, {"status": "queued"}), (503, {}, {}), (429, {"Retry-After": "30"}, {}), _succeeded()])
    sleeps, downloads = [], []

    def fake_download(url, output):
        downloads.append(url)
        output.write_bytes(b"mp4-with-audio")

    def fake_strip(source, output):
        output.write_bytes(b"mp4-silent")
        return True

    def fake_frame(source, output):
        assert source.name == "newb-video.mp4"
        output.write_bytes(b"png")
        return True

    ledger = runner.run_newb_video(
        run_dir,
        images=["generated/page-01.png"],
        strip_audio=True,
        request_fn=api,
        download_fn=fake_download,
        strip_audio_fn=fake_strip,
        extract_frame_fn=fake_frame,
        sleep_fn=sleeps.append,
    )

    post = next(call for call in api.calls if call["method"] == "POST")
    assert post["content_type"].startswith("multipart/form-data")
    assert b'filename="image-01.png"' in post["body"]
    assert sleeps == [15, 15, 30.0]
    assert downloads == ["https://video.haoniubi.cloud/api/v1/files/x?exp=1&sig=secret"]
    assert (run_dir / "generated" / "newb-video.mp4").read_bytes() == b"mp4-silent"
    assert ledger["postprocess"]["audio_original"] == "generated/newb-video.audio.mp4"
    assert ledger["postprocess"]["last_frame"] == "generated/newb-video-last-frame.png"

    on_disk = "".join(path.read_text(encoding="utf-8") for path in run_dir.rglob("*.json"))
    assert "sig=secret" not in on_disk
    assert "wfv_test" not in on_disk
    entry = manifest.load(run_dir / "analysis" / "manifest.json")["newb_video_generation"]["newb-video"]
    assert entry["status"] == "succeeded"
    assert entry["task_id"] == "task123"


def test_failed_task_reports_refund_and_records_manifest(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWB_API_KEY", "wfv_test")
    run_dir = _run(tmp_path)
    api = FakeApi([(200, {}, {"status": "failed", "error": "内容不符合规范", "quota_refunded": True})])
    with pytest.raises(runner.NewBRunnerError, match="quota refunded: True"):
        runner.run_newb_video(run_dir, request_fn=api, sleep_fn=lambda _: None)
    entry = manifest.load(run_dir / "analysis" / "manifest.json")["newb_video_generation"]["newb-video"]
    assert entry["status"] == "failed"


def test_submit_timeout_with_new_active_job_forbids_resubmit(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWB_API_KEY", "wfv_test")
    run_dir = _run(tmp_path)
    api = FakeApi([])
    quotas = iter([
        {"quota_remaining": 5, "membership_active": True, "active": 1, "max_concurrent": 5},
        {"quota_remaining": 4, "membership_active": True, "active": 2, "max_concurrent": 5},
    ])

    def request(method, url, api_key, **kwargs):
        if url.endswith("/api/v1/quota"):
            return 200, {}, next(quotas)
        raise runner.NewBNetworkError("timed out")

    with pytest.raises(runner.NewBRunnerError, match="Do NOT resubmit"):
        runner.run_newb_video(run_dir, request_fn=request)


def test_preflight_blocks_exhausted_quota_and_full_concurrency(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWB_API_KEY", "wfv_test")
    run_dir = _run(tmp_path)
    for quota, message in [
        ({"quota_remaining": 0, "membership_active": True, "active": 0}, "used up"),
        ({"quota_remaining": 3, "membership_active": True, "active": 5, "max_concurrent": 5}, "active jobs"),
    ]:
        api = FakeApi([], quota=quota)
        with pytest.raises(runner.NewBRunnerError, match=message):
            runner.run_newb_video(run_dir, request_fn=api)
        assert not any(call["method"] == "POST" for call in api.calls)


def test_poll_timeout_keeps_task_id_for_resume(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWB_API_KEY", "wfv_test")
    run_dir = _run(tmp_path)
    api = FakeApi([(200, {}, {"status": "processing"})] * 5)
    now = [0.0]

    def sleep(seconds):
        now[0] += seconds

    with pytest.raises(runner.NewBRunnerError, match="--resume task123"):
        runner.run_newb_video(
            run_dir, request_fn=api, sleep_fn=sleep, clock=lambda: now[0], timeout_seconds=40
        )
    assert runner._manifest_task_id(run_dir, "newb-video") == "task123"

    resume_api = FakeApi([_succeeded()])
    ledger = runner.run_newb_video(
        run_dir,
        resume_task_id="auto",
        request_fn=resume_api,
        download_fn=lambda url, output: output.write_bytes(b"mp4"),
        extract_frame_fn=lambda source, output: False,
        sleep_fn=lambda _: None,
    )
    assert not any(call["method"] == "POST" for call in resume_api.calls)
    assert ledger["task_id"] == "task123"
    assert ledger["postprocess"] == {"last_frame": None}


def test_existing_output_requires_new_label(tmp_path):
    run_dir = _run(tmp_path)
    (run_dir / "generated" / "newb-video.mp4").write_bytes(b"old")
    with pytest.raises(runner.NewBRunnerError, match="new --label"):
        runner.run_newb_video(run_dir, dry_run=True)
    assert runner.run_newb_video(run_dir, label="take-02", dry_run=True)["label"] == "take-02"
