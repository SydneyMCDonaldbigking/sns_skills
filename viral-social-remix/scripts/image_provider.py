"""Resolve image provider defaults without exposing secrets."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


ROOT = Path(__file__).parents[1]
LOCAL_ENV = ROOT.parent / ".env.local"

DEFAULTS = {
    "provider": "openrouter",
    "model": "openai/gpt-5.4-image-2",
    "quality": "medium",
    "endpoint": "",
}


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value
    return values


def _resolve_value(key: str, env_file: dict[str, str], default: str) -> str:
    return os.environ.get(key, env_file.get(key, default))


def resolve() -> dict:
    env_file = _load_env_file(LOCAL_ENV)
    api_key = _resolve_value("OPENROUTER_API_KEY", env_file, "")
    return {
        "provider": _resolve_value("VSR_IMAGE_PROVIDER", env_file, DEFAULTS["provider"]),
        "model": _resolve_value("VSR_IMAGE_MODEL", env_file, DEFAULTS["model"]),
        "quality": _resolve_value("VSR_IMAGE_QUALITY", env_file, DEFAULTS["quality"]),
        "endpoint": _resolve_value("VSR_IMAGE_ENDPOINT", env_file, DEFAULTS["endpoint"]),
        "api_key_set": bool(api_key),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print redacted viral-social-remix image provider config."
    )
    parser.add_argument(
        "--require-key",
        action="store_true",
        help="Exit non-zero when OPENROUTER_API_KEY is not available.",
    )
    args = parser.parse_args()
    config = resolve()
    print(json.dumps(config, ensure_ascii=False, indent=2))
    if args.require_key and not config["api_key_set"]:
        raise SystemExit("OPENROUTER_API_KEY is not set")


if __name__ == "__main__":
    main()
