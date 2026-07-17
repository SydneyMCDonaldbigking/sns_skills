"""Create a local source package from a browser-captured social post.

The browser controller is responsible for reading a logged-in tab and exporting
visible post data as JSON. This script turns that JSON into a resumable local
folder: caption, metadata, source URLs, downloaded media, and optional
screenshot copy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import shutil
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, url2pathname, urlopen


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
)
DEFAULT_REFERER = "https://www.xiaohongshu.com/"
IMAGE_EXTENSIONS_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def _pick(data: dict[str, Any], *names: str, default: Any = "") -> Any:
    for name in names:
        if name in data and data[name] not in (None, ""):
            return data[name]
    return default


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\r\n", "\n").replace("\u00a0", " ").strip()


def _slug(value: str, fallback: str = "source") -> str:
    value = value.strip().lower()
    value = re.sub(r"https?://", "", value)
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-._")
    return value[:80] or fallback


def _parse_indicator(value: Any) -> tuple[int | None, int | None]:
    if value is None:
        return None, None
    match = re.search(r"(\d+)\s*/\s*(\d+)", str(value))
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _media_url(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        return str(
            _pick(
                item,
                "url",
                "src",
                "currentSrc",
                "current_src",
                "href",
                default="",
            )
        ).strip()
    return ""


def _media_index(item: Any) -> int | None:
    if not isinstance(item, dict):
        return None
    for key in ("index", "page", "position"):
        value = item.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().isdigit():
            return int(value)
    current, _total = _parse_indicator(item.get("indicator") or item.get("pageIndicator"))
    return current


def _candidate_media(data: dict[str, Any]) -> list[Any]:
    for key in (
        "slides",
        "images",
        "media",
        "mediaUrls",
        "media_urls",
        "imageUrls",
        "image_urls",
    ):
        value = data.get(key)
        if isinstance(value, list) and value:
            return value
    return []


def ordered_media_urls(data: dict[str, Any]) -> list[str]:
    """Return ordered, de-duplicated media URLs.

    When items carry page indexes or indicators, the order is sorted by that
    index. Otherwise the browser-provided order is preserved.
    """

    items = _candidate_media(data)
    indexed: list[tuple[int, int, str]] = []
    plain: list[tuple[int, str]] = []
    for order, item in enumerate(items):
        url = _media_url(item)
        if not url or url.startswith("data:"):
            continue
        index = _media_index(item)
        if index is None:
            plain.append((order, url))
        else:
            indexed.append((index, order, url))

    if indexed and len(indexed) >= len(plain):
        ordered = [url for _index, _order, url in sorted(indexed)]
    else:
        ordered = [url for _order, url in sorted(plain)]

    seen: set[str] = set()
    unique: list[str] = []
    for url in ordered:
        if url in seen:
            continue
        seen.add(url)
        unique.append(url)
    return unique


def _infer_page_count(data: dict[str, Any], media_count: int) -> int:
    explicit = _pick(data, "pageCount", "page_count", "detectedPageCount", "detected_page_count", default=None)
    if isinstance(explicit, int):
        return explicit
    if isinstance(explicit, str) and explicit.strip().isdigit():
        return int(explicit)
    for key in ("pageIndicator", "page_indicator", "currentIndicator", "current_indicator"):
        _current, total = _parse_indicator(data.get(key))
        if total:
            return total
    for item in _candidate_media(data):
        if isinstance(item, dict):
            _current, total = _parse_indicator(item.get("indicator") or item.get("pageIndicator"))
            if total:
                return total
    return media_count


def normalize_capture(data: dict[str, Any]) -> dict[str, Any]:
    image_urls = ordered_media_urls(data)
    source_url = _clean_text(_pick(data, "sourceUrl", "source_url", "url", default=""))
    title = _clean_text(_pick(data, "title", default="Untitled source post"))
    description = _clean_text(_pick(data, "description", "caption", "body", "text", default=""))
    hashtags = _pick(data, "hashtags", "tags", default=[])
    if not isinstance(hashtags, list):
        hashtags = []
    return {
        "platform": _clean_text(_pick(data, "platform", default="unknown")),
        "sourceUrl": source_url,
        "pageTitle": _clean_text(_pick(data, "pageTitle", "page_title", default="")),
        "title": title,
        "author": _clean_text(_pick(data, "author", "username", default="")),
        "dateLocation": _clean_text(_pick(data, "dateLocation", "date_location", "date", default="")),
        "description": description,
        "hashtags": [_clean_text(tag) for tag in hashtags if _clean_text(tag)],
        "pageCount": _infer_page_count(data, len(image_urls)),
        "imageUrls": image_urls,
        "capturedAt": _clean_text(_pick(data, "capturedAt", "captured_at", default="")),
        "sourcePackageCreatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def _extension_from_url(url: str) -> str:
    path = unquote(urlparse(url).path)
    suffix = Path(path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return ".webp"


def _download(url: str, timeout: int, user_agent: str, referer: str) -> tuple[bytes, str | None]:
    parsed = urlparse(url)
    if parsed.scheme == "file":
        file_path = Path(url2pathname(unquote(parsed.path)))
        return file_path.read_bytes(), mimetypes.guess_type(file_path.name)[0]

    request = Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Referer": referer,
        },
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - user-supplied source capture URLs
        content_type = response.headers.get("content-type")
        return response.read(), content_type.split(";", 1)[0].lower() if content_type else None


def _write_text_files(package_dir: Path, meta: dict[str, Any]) -> None:
    caption = f"{meta['title']}\n\n{meta['description']}\n"
    package_dir.joinpath("caption.txt").write_text(caption, encoding="utf-8")
    package_dir.joinpath("source_urls.txt").write_text(
        "\n".join(meta["imageUrls"]) + ("\n" if meta["imageUrls"] else ""),
        encoding="utf-8",
    )

    image_lines = [
        f"- {index}: images/{index:02d}{_extension_from_url(url)}"
        for index, url in enumerate(meta["imageUrls"], start=1)
    ]
    post = "\n".join(
        [
            f"# {meta['title']}",
            "",
            f"Source: {meta['sourceUrl']}",
            f"Platform: {meta['platform']}",
            f"Author: {meta['author']}",
            f"Captured: {meta['capturedAt']}",
            f"Page count: {meta['pageCount']}",
            f"Date/location: {meta['dateLocation']}",
            "",
            "## Caption",
            "",
            meta["description"],
            "",
            "## Images",
            "",
            *image_lines,
            "",
        ]
    )
    package_dir.joinpath("post.md").write_text(post, encoding="utf-8")


def create_package(
    capture: dict[str, Any],
    output_dir: str | Path | None = None,
    *,
    download: bool = True,
    screenshot: str | Path | None = None,
    timeout: int = 30,
    user_agent: str = DEFAULT_USER_AGENT,
    referer: str = DEFAULT_REFERER,
    allow_download_failures: bool = False,
) -> dict[str, Any]:
    meta = normalize_capture(capture)
    if output_dir is None:
        source_hint = meta["sourceUrl"].rstrip("/").split("/")[-1] or meta["title"]
        output_dir = Path("samples") / _slug(f"{meta['platform']}-{source_hint}")
    package_dir = Path(output_dir)
    images_dir = package_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    screenshot_path = screenshot or _pick(capture, "screenshotPath", "screenshot_path", default="")
    if screenshot_path:
        src = Path(screenshot_path)
        if src.is_file():
            shutil.copy2(src, package_dir / "screenshot.png")

    saved_images: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    if download:
        for index, url in enumerate(meta["imageUrls"], start=1):
            try:
                content, content_type = _download(url, timeout, user_agent, referer)
            except (OSError, URLError, ValueError) as exc:
                failures.append({"index": str(index), "url": url, "reason": str(exc)})
                continue

            extension = IMAGE_EXTENSIONS_BY_TYPE.get(content_type or "", _extension_from_url(url))
            filename = f"{index:02d}{extension}"
            path = images_dir / filename
            path.write_bytes(content)
            saved_images.append(
                {
                    "index": index,
                    "filename": filename,
                    "path": str(path.resolve()),
                    "url": url,
                    "contentType": content_type,
                    "bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )

    if failures and not allow_download_failures:
        meta["downloadFailures"] = failures
        meta["savedImages"] = saved_images
        package_dir.joinpath("metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        raise RuntimeError(f"failed to download {len(failures)} media file(s)")

    meta["savedImages"] = saved_images
    meta["downloadFailures"] = failures
    meta["localFiles"] = {
        "post": str((package_dir / "post.md").resolve()),
        "caption": str((package_dir / "caption.txt").resolve()),
        "sourceUrls": str((package_dir / "source_urls.txt").resolve()),
        "metadata": str((package_dir / "metadata.json").resolve()),
        "imagesDirectory": str(images_dir.resolve()),
    }
    if (package_dir / "screenshot.png").is_file():
        meta["localFiles"]["screenshot"] = str((package_dir / "screenshot.png").resolve())

    _write_text_files(package_dir, meta)
    package_dir.joinpath("metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "package_dir": str(package_dir.resolve()),
        "page_count": meta["pageCount"],
        "image_url_count": len(meta["imageUrls"]),
        "downloaded_count": len(saved_images),
        "failed_count": len(failures),
        "metadata_path": str((package_dir / "metadata.json").resolve()),
    }


def _load_capture(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("capture JSON must contain an object")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a local source package from browser-captured post JSON.")
    parser.add_argument("capture_json", help="Path to browser-captured source JSON.")
    parser.add_argument("--output-dir", help="Directory to write the source package.")
    parser.add_argument("--screenshot", help="Optional screenshot file to copy into the package.")
    parser.add_argument("--skip-download", action="store_true", help="Write text/metadata only; do not download media.")
    parser.add_argument(
        "--allow-download-failures",
        action="store_true",
        help="Keep the package even if one or more media downloads fail.",
    )
    parser.add_argument("--timeout", type=int, default=30, help="Per-media download timeout in seconds.")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument("--referer", default=DEFAULT_REFERER)
    args = parser.parse_args()

    result = create_package(
        _load_capture(args.capture_json),
        args.output_dir,
        download=not args.skip_download,
        screenshot=args.screenshot,
        timeout=args.timeout,
        user_agent=args.user_agent,
        referer=args.referer,
        allow_download_failures=args.allow_download_failures,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
