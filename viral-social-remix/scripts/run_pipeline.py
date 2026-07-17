"""Minimal deterministic orchestration for viral-social-remix runs."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import create_run_dir
import image_provider
import manifest
import scan_media
import validate_output


PLATFORMS = {"xiaohongshu", "instagram-facebook", "video"}


def _is_ignored(path: Path, root: Path) -> bool:
    return any(
        part in scan_media.IGNORED_DIRS or part.startswith(".")
        for part in path.relative_to(root).parts
    )


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


def prepare_run(
    input_path: str | Path,
    platform: str,
    output_root: str | Path = "output",
    task_name: str | None = None,
    caption_language: str | None = None,
) -> Path:
    if platform not in PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")

    source = Path(input_path).resolve()
    files = collect_media(source)
    _validate_media_for_platform(files, platform)

    run_dir = create_run_dir.create(output_root, task_name or source.stem)
    copied_sources = _copy_sources(source, files, run_dir)

    for directory in [
        run_dir / "analysis",
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

    manifest.create(
        analysis / "manifest.json",
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
