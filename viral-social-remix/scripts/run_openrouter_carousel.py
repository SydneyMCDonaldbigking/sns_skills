"""Run OpenRouter carousel generation from a prepared local run directory.

This runner is intended to be executed in the user's own terminal. Codex should
prepare the source package, copy, page prompts, and manifest, then hand off the
API upload step to this script.
"""

from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import base64
from datetime import datetime, timezone
import json
import re
import shutil
import sys
import threading
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import make_contact_sheet
import manifest
import openrouter_image
import validate_output


CAROUSEL_PLATFORMS = {"xiaohongshu", "instagram-facebook"}
MAX_CONCURRENCY = 2


class CarouselRunnerError(RuntimeError):
    """Raised when the carousel runner cannot complete the API-only contract."""


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _relative_to_run(path: str | Path, run_dir: Path) -> str:
    target = Path(path).resolve()
    try:
        return target.relative_to(run_dir).as_posix()
    except ValueError:
        return str(target)


def _resolve_run_path(run_dir: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else run_dir / path


def _expected_size(platform: str) -> tuple[int, int]:
    if platform not in CAROUSEL_PLATFORMS:
        raise CarouselRunnerError(
            f"run_openrouter_carousel.py supports only carousel platforms: "
            f"{', '.join(sorted(CAROUSEL_PLATFORMS))}"
        )
    return validate_output.DIMENSIONS[platform]


def _page_label(asset_id: str) -> str:
    match = re.search(r"(\d+)$", asset_id)
    if match:
        return f"page-{int(match.group(1)):02d}"
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", asset_id).strip(".-")
    return f"page-{cleaned or asset_id}"


def _generated_path(run_dir: Path, asset_id: str) -> Path:
    return run_dir / "generated" / f"{_page_label(asset_id)}.png"


def _raw_response_path(run_dir: Path, asset_id: str) -> Path:
    return run_dir / "raw" / f"{_page_label(asset_id)}-response.json"


def _image_matches(path: Path, expected_size: tuple[int, int]) -> bool:
    if not path.is_file():
        return False
    try:
        with Image.open(path) as image:
            return image.size == expected_size
    except OSError:
        return False


def _image_size(path: Path) -> tuple[int, int] | None:
    if not path.is_file():
        return None
    try:
        with Image.open(path) as image:
            return image.size
    except OSError:
        return None


def _same_aspect_ratio(size: tuple[int, int], expected_size: tuple[int, int]) -> bool:
    return size[0] * expected_size[1] == size[1] * expected_size[0]


def _normalize_image_size(path: Path, expected_size: tuple[int, int], run_dir: Path) -> bool:
    size = _image_size(path)
    if size is None:
        return False
    if size == expected_size:
        return True
    if not _same_aspect_ratio(size, expected_size):
        return False

    original_dir = run_dir / "generated-original-size"
    original_dir.mkdir(parents=True, exist_ok=True)
    original = original_dir / path.name
    if not original.exists():
        shutil.copy2(path, original)

    with Image.open(path) as image:
        resized = image.convert("RGB").resize(expected_size, Image.Resampling.LANCZOS)
    resized.save(path)
    return True


def _prompt_path(run_dir: Path, asset_id: str) -> Path:
    prompt_dir = run_dir / "analysis" / "page-prompts"
    candidates = [
        prompt_dir / f"{_page_label(asset_id)}.md",
        prompt_dir / f"{asset_id}.md",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    expected = ", ".join(str(path) for path in candidates)
    raise CarouselRunnerError(f"Missing page prompt for asset {asset_id}: {expected}")


def _read_prompt(run_dir: Path, asset_id: str) -> tuple[Path, str]:
    path = _prompt_path(run_dir, asset_id)
    text = path.read_text(encoding="utf-8").strip()
    if not text or text == "TODO":
        raise CarouselRunnerError(f"Page prompt is empty or TODO: {path}")
    return path, text


def _list_from_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _references_for_asset(run_dir: Path, data: dict[str, Any], asset_id: str) -> list[str]:
    asset = data["assets"].get(asset_id, {})
    references: list[str] = []
    global_refs = data.get("references")
    if isinstance(global_refs, dict):
        references.extend(_list_from_value(global_refs.get(asset_id)))
    else:
        references.extend(_list_from_value(global_refs))
    references.extend(_list_from_value(asset.get("references")))
    references.extend(_list_from_value(asset.get("reference_paths")))
    request = asset.get("request")
    if isinstance(request, dict):
        references.extend(_list_from_value(request.get("references")))
        references.extend(_list_from_value(request.get("reference_paths")))
        references.extend(_list_from_value(request.get("reference_images")))

    resolved: list[str] = []
    seen: set[str] = set()
    for reference in references:
        path = _resolve_run_path(run_dir, reference).resolve()
        if str(path) in seen:
            continue
        if not path.is_file():
            raise CarouselRunnerError(f"Reference file does not exist: {path}")
        seen.add(str(path))
        resolved.append(str(path))
    return resolved


def _first_image_url(response: dict[str, Any]) -> str:
    for choice in response.get("choices", []):
        message = choice.get("message", {})
        candidates: list[Any] = []
        candidates.extend(message.get("images") or [])
        content = message.get("content")
        if isinstance(content, list):
            candidates.extend(
                item for item in content if isinstance(item, dict) and "image_url" in item
            )
        elif isinstance(content, str) and "data:image" in content:
            start = content.find("data:image")
            end = content.find(")", start)
            candidates.append(
                {"image_url": {"url": content[start : end if end > start else None]}}
            )

        for candidate in candidates:
            image_url = candidate.get("image_url", candidate) if isinstance(candidate, dict) else candidate
            if isinstance(image_url, dict):
                url = str(image_url.get("url", ""))
            else:
                url = str(image_url)
            if url:
                return url
    raise CarouselRunnerError("OpenRouter response did not contain an image")


def _save_first_image(response: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    url = _first_image_url(response)
    if url.startswith("data:image"):
        _header, encoded = url.split(",", 1)
        output.write_bytes(base64.b64decode(encoded))
        return
    with urlopen(url, timeout=180) as response_obj:
        output.write_bytes(response_obj.read())


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_number(*values: Any) -> float | None:
    for value in values:
        number = _number(value)
        if number is not None:
            return number
    return None


def _cost_from_response(response: dict[str, Any]) -> dict[str, Any]:
    usage = response.get("usage") if isinstance(response.get("usage"), dict) else {}
    cost = _first_number(
        response.get("cost"),
        response.get("total_cost"),
        usage.get("cost"),
        usage.get("total_cost"),
    )
    return {
        "cost": cost,
        "currency": response.get("currency") or usage.get("currency") or "USD",
        "usage": usage,
    }


def _cost_from_raw_response(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"cost": 0.0, "currency": "USD", "usage": {}}
    try:
        return _cost_from_response(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return {"cost": 0.0, "currency": "USD", "usage": {}}


def _mark_manifest(
    manifest_path: Path,
    asset_id: str,
    status: str,
    lock: threading.Lock,
    **fields: Any,
) -> None:
    with lock:
        manifest.mark(manifest_path, asset_id, status, **fields)


def _mark_failed(
    manifest_path: Path,
    asset_id: str,
    lock: threading.Lock,
    error: Exception,
) -> None:
    _mark_manifest(
        manifest_path,
        asset_id,
        "failed",
        lock,
        validation_errors=[str(error)],
        last_error={
            "type": error.__class__.__name__,
            "message": str(error),
        },
    )


def _generate_page(
    *,
    run_dir: Path,
    manifest_path: Path,
    manifest_data: dict[str, Any],
    asset_id: str,
    expected_size: tuple[int, int],
    config: dict[str, Any],
    max_attempts: int,
    manifest_lock: threading.Lock,
    request_fn=None,
) -> dict[str, Any]:
    prompt_path, prompt = _read_prompt(run_dir, asset_id)
    output = _generated_path(run_dir, asset_id)
    raw_path = _raw_response_path(run_dir, asset_id)
    references = _references_for_asset(run_dir, manifest_data, asset_id)
    payload = openrouter_image.build_payload(
        prompt,
        model=config["model"],
        size=f"{expected_size[0]}x{expected_size[1]}",
        quality=config["quality"],
        references=references,
    )

    _mark_manifest(
        manifest_path,
        asset_id,
        "prompted",
        manifest_lock,
        prompt_path=_relative_to_run(prompt_path, run_dir),
        request={
            "endpoint": config["endpoint"],
            "payload": openrouter_image.redact_payload(payload),
        },
        validation_errors=[],
    )

    try:
        response = openrouter_image.request_with_retries(
            payload,
            config["api_key"],
            endpoint=config["endpoint"],
            max_attempts=max_attempts,
            request_fn=request_fn,
        )
        _write_json(raw_path, response)
        _save_first_image(response, output)
        if not _normalize_image_size(output, expected_size, run_dir):
            actual = _image_size(output)
            got = f", got {actual[0]}x{actual[1]}" if actual else ""
            raise CarouselRunnerError(
                f"{output.name}: expected {expected_size[0]}x{expected_size[1]}{got}"
            )
        relative_output = _relative_to_run(output, run_dir)
        _mark_manifest(
            manifest_path,
            asset_id,
            "generated",
            manifest_lock,
            prompt_path=_relative_to_run(prompt_path, run_dir),
            output=relative_output,
            outputs=[relative_output],
            raw_response=_relative_to_run(raw_path, run_dir),
            validation_errors=[],
        )
        _mark_manifest(
            manifest_path,
            asset_id,
            "validated",
            manifest_lock,
            prompt_path=_relative_to_run(prompt_path, run_dir),
            output=relative_output,
            outputs=[relative_output],
            raw_response=_relative_to_run(raw_path, run_dir),
            validation_errors=[],
        )
        page_cost = _cost_from_response(response)
        return {
            "asset_id": asset_id,
            "status": "generated",
            "output": relative_output,
            "raw_response": _relative_to_run(raw_path, run_dir),
            "prompt_path": _relative_to_run(prompt_path, run_dir),
            "references": [_relative_to_run(path, run_dir) for path in references],
            **page_cost,
        }
    except Exception as exc:
        _mark_failed(manifest_path, asset_id, manifest_lock, exc)
        raise


def _finalize_run(run_dir: Path, platform: str, asset_ids: list[str]) -> dict[str, Any]:
    generated = [_generated_path(run_dir, asset_id) for asset_id in asset_ids]
    if all(path.is_file() for path in generated):
        make_contact_sheet.make_carousel(
            generated,
            run_dir / "overview" / "contact-sheet.png",
        )

    validation_path = run_dir / "qa" / "validation.json"
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    if not validation_path.exists():
        validation_path.write_text("{}", encoding="utf-8")
    result = validate_output.validate_delivery(run_dir, platform)
    _write_json(validation_path, result)
    return result


def _new_cost_ledger(run_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": {
            "name": "openrouter",
            "model": config["model"],
            "quality": config["quality"],
            "endpoint": config["endpoint"],
            "api_key_set": bool(config.get("api_key")),
        },
        "run_dir": str(run_dir.resolve()),
        "currency": "USD",
        "total_cost": 0.0,
        "pages": [],
        "errors": [],
    }


def _append_cost_page(ledger: dict[str, Any], page: dict[str, Any]) -> None:
    ledger["pages"].append(page)
    cost = page.get("cost")
    if isinstance(cost, (int, float)):
        ledger["total_cost"] = round(float(ledger["total_cost"]) + float(cost), 8)
        ledger["currency"] = page.get("currency") or ledger["currency"]


def run_carousel(
    run_dir: str | Path,
    *,
    api_only: bool = False,
    concurrency: int = MAX_CONCURRENCY,
    max_attempts: int = 2,
    model: str | None = None,
    quality: str | None = None,
    request_fn=None,
) -> dict[str, Any]:
    if concurrency < 1 or concurrency > MAX_CONCURRENCY:
        raise CarouselRunnerError("--concurrency must be 1 or 2")

    run = Path(run_dir).resolve()
    manifest_path = run / "analysis" / "manifest.json"
    if not manifest_path.is_file():
        raise CarouselRunnerError(f"Missing manifest: {manifest_path}")
    data = manifest.load(manifest_path)
    platform = data.get("platform", "")
    expected_size = _expected_size(platform)
    asset_ids = list(data.get("assets", {}).keys())
    if not asset_ids:
        raise CarouselRunnerError("Manifest does not contain carousel assets")

    config = openrouter_image.resolve_generation_config(model=model, quality=quality)
    ledger = _new_cost_ledger(run, config)
    cost_path = run / "qa" / "openrouter-cost.json"
    manifest_lock = threading.Lock()

    pending: list[str] = []
    for asset_id in asset_ids:
        output = _generated_path(run, asset_id)
        _normalize_image_size(output, expected_size, run)
        if _image_matches(output, expected_size):
            relative_output = _relative_to_run(output, run)
            raw_path = _raw_response_path(run, asset_id)
            page_cost = _cost_from_raw_response(raw_path)
            _mark_manifest(
                manifest_path,
                asset_id,
                "validated",
                manifest_lock,
                output=relative_output,
                outputs=[relative_output],
                raw_response=_relative_to_run(raw_path, run) if raw_path.is_file() else None,
                validation_errors=[],
            )
            _append_cost_page(
                ledger,
                {
                    "asset_id": asset_id,
                    "status": "skipped",
                    "reason": "generated image already exists with expected size",
                    "output": relative_output,
                    "raw_response": _relative_to_run(raw_path, run) if raw_path.is_file() else None,
                    **page_cost,
                },
            )
        else:
            pending.append(asset_id)

    _write_json(cost_path, ledger)
    if pending and not config.get("api_key"):
        raise CarouselRunnerError("OPENROUTER_API_KEY is not set")

    errors: list[dict[str, str]] = []
    pending_iter = iter(pending)

    def submit_next(executor: ThreadPoolExecutor, futures: dict) -> bool:
        try:
            asset_id = next(pending_iter)
        except StopIteration:
            return False
        future = executor.submit(
            _generate_page,
            run_dir=run,
            manifest_path=manifest_path,
            manifest_data=data,
            asset_id=asset_id,
            expected_size=expected_size,
            config=config,
            max_attempts=max_attempts,
            manifest_lock=manifest_lock,
            request_fn=request_fn,
        )
        futures[future] = asset_id
        return True

    if pending:
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures: dict[Any, str] = {}
            for _ in range(min(concurrency, len(pending))):
                submit_next(executor, futures)
            while futures:
                done, _not_done = wait(futures, return_when=FIRST_COMPLETED)
                for future in done:
                    asset_id = futures.pop(future)
                    try:
                        page = future.result()
                    except Exception as exc:
                        error = {"asset_id": asset_id, "message": str(exc)}
                        errors.append(error)
                        ledger["errors"].append(error)
                        _write_json(cost_path, ledger)
                        if api_only:
                            for running in futures:
                                running.cancel()
                            raise CarouselRunnerError(
                                f"API-only generation failed for {asset_id}: {exc}"
                            ) from exc
                    else:
                        _append_cost_page(ledger, page)
                        _write_json(cost_path, ledger)
                        if not errors:
                            submit_next(executor, futures)

    if errors:
        raise CarouselRunnerError(f"Generation finished with {len(errors)} error(s)")

    validation = _finalize_run(run, platform, asset_ids)
    ledger["validation"] = validation
    _write_json(cost_path, ledger)
    return {
        "run_dir": str(run),
        "generated": [
            page for page in ledger["pages"] if page.get("status") == "generated"
        ],
        "skipped": [
            page for page in ledger["pages"] if page.get("status") == "skipped"
        ],
        "cost": {
            "path": str(cost_path),
            "total_cost": ledger["total_cost"],
            "currency": ledger["currency"],
        },
        "validation": validation,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a prepared viral-social-remix carousel via OpenRouter."
    )
    parser.add_argument("--run", required=True, help="Prepared output run directory.")
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Require API generation for every missing page and stop on first failure.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=MAX_CONCURRENCY,
        help="Concurrent OpenRouter requests. Maximum: 2.",
    )
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--model")
    parser.add_argument("--quality")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_carousel(
            args.run,
            api_only=args.api_only,
            concurrency=args.concurrency,
            max_attempts=args.max_attempts,
            model=args.model,
            quality=args.quality,
        )
    except CarouselRunnerError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
