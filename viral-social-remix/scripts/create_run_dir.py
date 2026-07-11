"""Create collision-safe timestamped output directories."""

import re
from datetime import datetime
from pathlib import Path


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value.strip(), flags=re.UNICODE)
    return cleaned.strip("-") or "task"


def create(root: str | Path, task_name: str, now: datetime | None = None) -> Path:
    base = Path(root)
    timestamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    stem = f"{timestamp}-{_slug(task_name)}"
    candidate = base / stem
    suffix = 2
    while candidate.exists():
        candidate = base / f"{stem}-{suffix:02d}"
        suffix += 1
    candidate.mkdir(parents=True)
    return candidate
