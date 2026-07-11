"""Persist resumable generation state atomically."""

import json
from datetime import datetime, timezone
from pathlib import Path


STATUSES = {"pending", "prompted", "generated", "validated", "failed"}


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def create(path: str | Path, platform: str, asset_ids: list[str]) -> dict:
    target = Path(path)
    data = {
        "schema_version": 1,
        "platform": platform,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "assets": {
            asset_id: {"status": "pending", "attempts": 0}
            for asset_id in asset_ids
        },
    }
    _write(target, data)
    return data


def load(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def mark(path: str | Path, asset_id: str, status: str, **fields) -> dict:
    if status not in STATUSES:
        raise ValueError(f"Unsupported status: {status}")
    target = Path(path)
    data = load(target)
    if asset_id not in data["assets"]:
        raise KeyError(asset_id)
    item = data["assets"][asset_id]
    item.update(fields)
    item["status"] = status
    if status in {"generated", "failed"}:
        item["attempts"] += 1
    _write(target, data)
    return data


def pending(path: str | Path) -> list[str]:
    data = load(path)
    return [
        asset_id
        for asset_id, item in data["assets"].items()
        if item["status"] != "validated"
    ]
