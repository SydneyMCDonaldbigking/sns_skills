"""Discover and group local social-media inputs."""

import argparse
import json
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".heic"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v"}
SUPPORTED = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
IGNORED_DIRS = {"output", ".git", "__pycache__"}


def _media_type(path: Path) -> str:
    return "image" if path.suffix.lower() in IMAGE_EXTENSIONS else "video"


def _record(path: Path, root: Path) -> dict:
    return {
        "path": str(path.resolve()),
        "relative_path": path.relative_to(root).as_posix(),
        "media_type": _media_type(path),
        "extension": path.suffix.lower(),
    }


def _ignored(path: Path, root: Path) -> bool:
    return any(
        part in IGNORED_DIRS or part.startswith(".")
        for part in path.relative_to(root).parts
    )


def scan(directory: str | Path) -> dict:
    root = Path(directory)
    if not root.is_dir():
        raise ValueError(f"Expected a readable directory: {root}")

    tasks = []
    accepted: set[Path] = set()
    subfolders = sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and path.name not in IGNORED_DIRS and not path.name.startswith(".")
    )
    for child in subfolders:
        files = sorted(
            path
            for path in child.rglob("*")
            if path.is_file()
            and path.suffix.lower() in SUPPORTED
            and not _ignored(path, root)
        )
        if files:
            accepted.update(files)
            tasks.append(
                {
                    "name": child.name,
                    "input_kind": "folder",
                    "files": [_record(path, root) for path in files],
                }
            )

    for path in sorted(root.iterdir()):
        if (
            path.is_file()
            and path.suffix.lower() in SUPPORTED
            and not path.name.startswith(".")
        ):
            accepted.add(path)
            tasks.append(
                {
                    "name": path.stem,
                    "input_kind": "file",
                    "files": [_record(path, root)],
                }
            )

    all_files = {
        path
        for path in root.rglob("*")
        if path.is_file() and not _ignored(path, root)
    }
    return {
        "root": str(root.resolve()),
        "tasks": tasks,
        "ignored_count": len(all_files - accepted),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="Directory containing local media inputs.")
    args = parser.parse_args()

    print(json.dumps(scan(args.directory), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
