"""Append-only material index for collected social and brand assets."""

from __future__ import annotations

import json
import re
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


def searchable_text(record: dict) -> str:
    values: list[str] = []
    for key in [
        "record_id",
        "record_type",
        "platform",
        "source",
        "kind",
        "title",
        "label",
        "source_name",
        "use_case",
        "quality",
        "source_url",
        "folder",
        "content_path",
        "caption_path",
    ]:
        value = record.get(key)
        if value:
            values.append(str(value))
    for key in ["reasons", "image_paths", "tags"]:
        value = record.get(key) or []
        if isinstance(value, list):
            values.extend(str(item) for item in value)
    return " ".join(values).casefold()


def _contains_cjk(value: str) -> bool:
    return bool(re.search(r"[\u3400-\u9fff]", value))


def _ascii_tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.casefold()))


def _matches_terms(haystack: str, terms: list[str]) -> bool:
    tokens = _ascii_tokens(haystack)
    for term in terms:
        if _contains_cjk(term):
            if term not in haystack:
                return False
            continue
        term_tokens = _ascii_tokens(term)
        if term_tokens:
            if not term_tokens.issubset(tokens):
                return False
        elif term not in haystack:
            return False
    return True


def search(
    path: str | Path = DEFAULT_INDEX,
    *,
    query: str | None = None,
    platform: str | None = None,
    record_type: str | None = None,
    kind: str | None = None,
    quality: str | None = None,
    use_case: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    rows = load(path)
    terms = [term.casefold() for term in (query or "").split() if term.strip()]
    results = []
    for row in rows:
        if platform and row.get("platform") != platform:
            continue
        if record_type and row.get("record_type") != record_type:
            continue
        if kind and row.get("kind") != kind:
            continue
        if quality and row.get("quality") != quality:
            continue
        if use_case and row.get("use_case") != use_case:
            continue
        haystack = searchable_text(row)
        if terms and not _matches_terms(haystack, terms):
            continue
        results.append(row)
        if limit and len(results) >= limit:
            break
    return results
