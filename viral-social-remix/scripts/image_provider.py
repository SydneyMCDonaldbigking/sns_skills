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
    "model": "openai/gpt-image-2",
    "quality": "medium",
    "endpoint": "",
}


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def resolve() -> dict:
    _load_env_file(LOCAL_ENV)
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    return {
        "provider": os.environ.get("VSR_IMAGE_PROVIDER", DEFAULTS["provider"]),
        "model": os.environ.get("VSR_IMAGE_MODEL", DEFAULTS["model"]),
        "quality": os.environ.get("VSR_IMAGE_QUALITY", DEFAULTS["quality"]),
        "endpoint": os.environ.get("VSR_IMAGE_ENDPOINT", DEFAULTS["endpoint"]),
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
