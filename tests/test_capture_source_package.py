from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from viral_social_test_loader import load_script


capture_source_package = load_script("capture_source_package")


def test_ordered_media_urls_sorts_indicator_slides_and_dedupes():
    payload = {
        "slides": [
            {"indicator": "3/3", "url": "https://cdn.example/03.webp"},
            {"indicator": "1/3", "url": "https://cdn.example/01.webp"},
            {"indicator": "2/3", "url": "https://cdn.example/02.webp"},
            {"indicator": "1/3", "url": "https://cdn.example/01.webp"},
        ]
    }

    assert capture_source_package.ordered_media_urls(payload) == [
        "https://cdn.example/01.webp",
        "https://cdn.example/02.webp",
        "https://cdn.example/03.webp",
    ]


def test_ordered_media_urls_falls_back_when_preferred_list_is_empty():
    payload = {
        "slides": [],
        "imageUrls": ["https://cdn.example/01.webp"],
    }

    assert capture_source_package.ordered_media_urls(payload) == [
        "https://cdn.example/01.webp",
    ]


def test_create_package_downloads_file_urls_and_writes_metadata(tmp_path: Path):
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    first = media_dir / "first.webp"
    second = media_dir / "second.webp"
    first.write_bytes(b"first-image")
    second.write_bytes(b"second-image")

    result = capture_source_package.create_package(
        {
            "platform": "xiaohongshu",
            "sourceUrl": "https://www.xiaohongshu.com/explore/example",
            "title": "Sauce formula",
            "author": "Umall",
            "description": "A local source caption.",
            "slides": [
                {"indicator": "2/2", "url": second.as_uri()},
                {"indicator": "1/2", "url": first.as_uri()},
            ],
        },
        tmp_path / "package",
    )

    package = Path(result["package_dir"])
    assert result["page_count"] == 2
    assert result["downloaded_count"] == 2
    assert (package / "caption.txt").read_text(encoding="utf-8").startswith("Sauce formula")
    assert (package / "source_urls.txt").read_text(encoding="utf-8").splitlines() == [
        first.as_uri(),
        second.as_uri(),
    ]
    assert (package / "images" / "01.webp").read_bytes() == b"first-image"
    assert (package / "images" / "02.webp").read_bytes() == b"second-image"

    metadata = json.loads((package / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["pageCount"] == 2
    assert metadata["savedImages"][0]["sha256"] == hashlib.sha256(b"first-image").hexdigest()
    assert metadata["downloadFailures"] == []


def test_create_package_can_skip_downloads(tmp_path: Path):
    result = capture_source_package.create_package(
        {
            "platform": "instagram",
            "source_url": "https://instagram.example/p/abc",
            "title": "No download",
            "image_urls": ["https://cdn.example/01.jpg"],
        },
        tmp_path / "package",
        download=False,
    )

    metadata = json.loads(Path(result["metadata_path"]).read_text(encoding="utf-8"))
    assert result["downloaded_count"] == 0
    assert metadata["imageUrls"] == ["https://cdn.example/01.jpg"]
    assert metadata["savedImages"] == []


def test_capture_source_package_cli_outputs_json(tmp_path: Path):
    image = tmp_path / "one.webp"
    image.write_bytes(b"one")
    capture = tmp_path / "capture.json"
    capture.write_text(
        json.dumps(
            {
                "platform": "xiaohongshu",
                "sourceUrl": "https://example.test/post",
                "title": "CLI package",
                "imageUrls": [image.as_uri()],
            }
        ),
        encoding="utf-8",
    )
    script = Path(__file__).parents[1] / "viral-social-remix" / "scripts" / "capture_source_package.py"

    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            str(capture),
            "--output-dir",
            str(tmp_path / "out"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["downloaded_count"] == 1
    assert Path(payload["metadata_path"]).is_file()
