"""Append-only material index for collected social and brand assets."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_INDEX = Path("data/material-index.jsonl")


def _json_default(value):
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def append(path: str | Path, record: dict) -> dict:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        **record,
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, default=_json_default) + "\n")
    return payload


def record_key(record: dict) -> str:
    if record.get("record_id"):
        return str(record["record_id"])
    parts = [
        record.get("platform", "unknown"),
        record.get("record_type", "unknown"),
        record.get("source_url") or record.get("folder") or record.get("title") or "unknown",
    ]
    image_paths = record.get("image_paths") or []
    if image_paths:
        parts.append(str(image_paths[0]))
    return "::".join(str(part) for part in parts)


def append_many(path: str | Path, records: Iterable[dict], *, skip_existing: bool = True) -> list[dict]:
    existing_keys = {record_key(row) for row in load(path)} if skip_existing else set()
    written = []
    for record in records:
        key = record_key(record)
        if skip_existing and key in existing_keys:
            continue
        payload = append(path, {**record, "record_id": key})
        written.append(payload)
        existing_keys.add(key)
    return written


def load(path: str | Path = DEFAULT_INDEX) -> list[dict]:
    target = Path(path)
    if not target.exists():
        return []
    rows = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def summarize(path: str | Path = DEFAULT_INDEX) -> dict:
    rows = load(path)
    by_platform: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for row in rows:
        platform = row.get("platform", "unknown")
        record_type = row.get("record_type", "unknown")
        by_platform[platform] = by_platform.get(platform, 0) + 1
        by_type[record_type] = by_type.get(record_type, 0) + 1
    return {
        "index": str(path),
        "total": len(rows),
        "by_platform": by_platform,
        "by_type": by_type,
    }
