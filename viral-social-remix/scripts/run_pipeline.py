"""Minimal deterministic orchestration for viral-social-remix runs."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import create_run_dir
import image_provider
import manifest
import openrouter_image
import scan_media
import validate_output


PLATFORMS = {"xiaohongshu", "instagram-facebook", "video"}
DEFAULT_SIZES = {
    "xiaohongshu": "1152x1536",
    "instagram-facebook": "1152x1152",
    "video": "1920x1080",
}
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
}


def _is_ignored(path: Path, root: Path) -> bool:
    return any(
        part in scan_media.IGNORED_DIRS or part.startswith(".")
        for part in path.relative_to(root).parts
    )


def is_url(value: str | Path) -> bool:
    parsed = urlparse(str(value))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _clean_content_type(value: str | None) -> str:
    return (value or "").split(";", 1)[0].strip().lower()


def _safe_stem(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", value.strip(), flags=re.UNICODE)
    return cleaned.strip(".-") or "remote-media"


def _filename_for_url(url: str, content_type: str) -> str:
    parsed = urlparse(url)
    name = Path(unquote(parsed.path)).name
    suffix = Path(name).suffix.lower()
    extension = suffix if suffix in scan_media.SUPPORTED else CONTENT_TYPE_EXTENSIONS.get(content_type)
    if not extension:
        raise ValueError(
            "URL did not resolve to a direct supported media file. "
            "Download the post media locally or provide a readable media URL."
        )
    stem = _safe_stem(Path(name).stem if name else "remote-media")
    return f"{stem}{extension}"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    suffix = path.suffix
    stem = path.stem
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}-{counter:02d}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def download_direct_media_url(url: str, target_dir: str | Path, opener=urlopen) -> dict:
    request = Request(url, headers={"User-Agent": "viral-social-remix/0.1"})
    try:
        with opener(request, timeout=60) as response:
            content_type = _clean_content_type(response.headers.get("Content-Type"))
            filename = _filename_for_url(url, content_type)
            data = response.read()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Unable to download URL: {url}") from exc

    if not data:
        raise ValueError(f"URL returned no media bytes: {url}")

    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    output = _unique_path(target / filename)
    output.write_bytes(data)
    return {
        "path": output.resolve(),
        "content_type": content_type,
        "bytes": len(data),
        "url": url,
    }


def collect_media(path: str | Path) -> list[Path]:
    source = Path(path)
    if source.is_file():
        if source.suffix.lower() not in scan_media.SUPPORTED:
            raise ValueError(f"Unsupported media file: {source}")
        return [source.resolve()]
    if not source.is_dir():
        raise ValueError(f"Expected a media file or directory: {source}")

    files = sorted(
        item.resolve()
        for item in source.rglob("*")
        if item.is_file()
        and item.suffix.lower() in scan_media.SUPPORTED
        and not _is_ignored(item, source)
    )
    if not files:
        raise ValueError(f"No supported media found in: {source}")
    return files


def _validate_media_for_platform(files: list[Path], platform: str) -> None:
    has_image = any(path.suffix.lower() in scan_media.IMAGE_EXTENSIONS for path in files)
    has_video = any(path.suffix.lower() in scan_media.VIDEO_EXTENSIONS for path in files)
    if platform == "video" and not has_video:
        raise ValueError("Video platform requires at least one video file")
    if platform != "video" and has_video:
        raise ValueError("Image carousel platforms do not accept video files")
    if platform != "video" and not has_image:
        raise ValueError("Image carousel platforms require image files")


def _asset_ids(platform: str, files: list[Path]) -> list[str]:
    count = 9 if platform == "video" else len(files)
    return [f"{index:02d}" for index in range(1, count + 1)]


def _caption_language(platform: str, value: str | None) -> str:
    if value:
        return value
    return "zh" if platform == "xiaohongshu" else "en"


def _write_if_missing(path: Path, text: str) -> None:
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _copy_sources(input_path: Path, files: list[Path], run_dir: Path) -> list[str]:
    source_dir = run_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    base = input_path if input_path.is_dir() else input_path.parent
    for file_path in files:
        relative = file_path.relative_to(base.resolve())
        target = source_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, target)
        copied.append(target.relative_to(run_dir).as_posix())
    return copied


def _create_run_layout(run_dir: Path, platform: str, caption_language: str | None) -> None:
    for directory in [
        run_dir / "analysis",
        run_dir / "analysis" / "page-prompts",
        run_dir / "references" / "keyframes",
        run_dir / "generated",
        run_dir / "overview",
        run_dir / "qa",
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    analysis = run_dir / "analysis"
    language = _caption_language(platform, caption_language)
    _write_if_missing(analysis / "breakdown.md", "# Breakdown\n\nTODO\n")
    _write_if_missing(analysis / "copy.md", "# Copy\n\nTODO\n")
    _write_if_missing(analysis / "prompts.md", "# Prompts\n\nTODO\n")
    _write_if_missing(analysis / f"caption-{language}.txt", "TODO\n")


def _task_name_for_url(url: str) -> str:
    parsed = urlparse(url)
    stem = Path(unquote(parsed.path)).stem
    return _safe_stem(stem or parsed.netloc or "url-source")


def prepare_url_run(
    url: str,
    platform: str,
    output_root: str | Path = "output",
    task_name: str | None = None,
    caption_language: str | None = None,
    opener=urlopen,
) -> Path:
    if platform not in PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")

    run_dir = create_run_dir.create(output_root, task_name or _task_name_for_url(url))
    media = download_direct_media_url(url, run_dir / "source", opener=opener)
    files = [Path(media["path"])]
    _validate_media_for_platform(files, platform)
    _create_run_layout(run_dir, platform, caption_language)

    copied_sources = [files[0].relative_to(run_dir).as_posix()]
    manifest.create(
        run_dir / "analysis" / "manifest.json",
        platform,
        _asset_ids(platform, files),
        source={
            "kind": "direct_url",
            "paths": copied_sources,
            "url": url,
            "content_type": media["content_type"],
            "bytes": media["bytes"],
        },
        provider=image_provider.resolve(),
    )
    return run_dir


def prepare_run(
    input_path: str | Path,
    platform: str,
    output_root: str | Path = "output",
    task_name: str | None = None,
    caption_language: str | None = None,
) -> Path:
    if platform not in PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")

    if is_url(input_path):
        return prepare_url_run(
            str(input_path),
            platform,
            output_root=output_root,
            task_name=task_name,
            caption_language=caption_language,
        )

    source = Path(input_path).resolve()
    files = collect_media(source)
    _validate_media_for_platform(files, platform)

    run_dir = create_run_dir.create(output_root, task_name or source.stem)
    copied_sources = _copy_sources(source, files, run_dir)
    _create_run_layout(run_dir, platform, caption_language)

    manifest.create(
        run_dir / "analysis" / "manifest.json",
        platform,
        _asset_ids(platform, files),
        source={
            "kind": "local_folder" if source.is_dir() else "local_file",
            "paths": copied_sources,
            "url": None,
        },
        provider=image_provider.resolve(),
    )
    return run_dir


def validate_run(
    run_dir: str | Path,
    platform: str,
    caption_language: str | None = None,
) -> dict:
    target = Path(run_dir)
    validation_path = target / "qa" / "validation.json"
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    if not validation_path.exists():
        validation_path.write_text("{}", encoding="utf-8")

    result = validate_output.validate_delivery(
        target,
        platform,
        caption_language=caption_language,
    )
    validation_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def pending_assets(manifest_path: str | Path) -> list[str]:
    return manifest.pending(manifest_path)


def generate_asset(
    run_dir: str | Path,
    asset_id: str,
    *,
    prompt_file: str | Path | None = None,
    out_dir: str | Path | None = None,
    size: str | None = None,
    stem: str | None = None,
    references: list[str] | None = None,
    max_attempts: int = 2,
    force: bool = False,
    dry_run: bool = False,
) -> dict:
    base = Path(run_dir)
    manifest_path = base / "analysis" / "manifest.json"
    data = manifest.load(manifest_path)
    platform = data["platform"]
    if platform not in DEFAULT_SIZES and not size:
        raise ValueError(f"No default size for platform: {platform}")

    return openrouter_image.generate_image(
        prompt_file=prompt_file or base / "analysis" / "prompts.md",
        out_dir=out_dir or base / "generated",
        stem=stem or asset_id,
        size=size or DEFAULT_SIZES[platform],
        references=references or [],
        max_attempts=max_attempts,
        manifest_path=manifest_path,
        asset_id=asset_id,
        force=force,
        dry_run=dry_run,
    )


def cmd_scan(args: argparse.Namespace) -> int:
    print(json.dumps(scan_media.scan(args.directory), ensure_ascii=False, indent=2))
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    run_dir = prepare_run(
        args.input,
        args.platform,
        output_root=args.output_root,
        task_name=args.task_name,
        caption_language=args.caption_language,
    )
    print(json.dumps({"run_dir": str(run_dir)}, ensure_ascii=False, indent=2))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    result = validate_run(
        args.run_dir,
        args.platform,
        caption_language=args.caption_language,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


def cmd_pending(args: argparse.Namespace) -> int:
    print(
        json.dumps(
            {"pending": pending_assets(args.manifest)},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    result = generate_asset(
        args.run_dir,
        args.asset_id,
        prompt_file=args.prompt_file,
        out_dir=args.out_dir,
        size=args.size,
        stem=args.stem,
        references=args.reference,
        max_attempts=args.max_attempts,
        force=args.force,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan")
    scan.add_argument("directory")
    scan.set_defaults(func=cmd_scan)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("input")
    prepare.add_argument("--platform", required=True, choices=sorted(PLATFORMS))
    prepare.add_argument("--output-root", default="output")
    prepare.add_argument("--task-name")
    prepare.add_argument("--caption-language", choices=["zh", "en"])
    prepare.set_defaults(func=cmd_prepare)

    validate = subparsers.add_parser("validate")
    validate.add_argument("run_dir")
    validate.add_argument("--platform", required=True, choices=sorted(PLATFORMS))
    validate.add_argument("--caption-language", choices=["zh", "en"])
    validate.set_defaults(func=cmd_validate)

    pending = subparsers.add_parser("pending")
    pending.add_argument("manifest")
    pending.set_defaults(func=cmd_pending)

    generate = subparsers.add_parser("generate")
    generate.add_argument("run_dir")
    generate.add_argument("--asset-id", required=True)
    generate.add_argument("--prompt-file")
    generate.add_argument("--out-dir")
    generate.add_argument("--size")
    generate.add_argument("--stem")
    generate.add_argument("--reference", action="append", default=[])
    generate.add_argument("--max-attempts", type=int, default=2)
    generate.add_argument("--force", action="store_true")
    generate.add_argument("--dry-run", action="store_true")
    generate.set_defaults(func=cmd_generate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())
