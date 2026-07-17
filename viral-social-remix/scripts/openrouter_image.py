"""Generate images through OpenRouter's chat-completions image models."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).parents[2]
LOCAL_ENV = ROOT / ".env.local"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import image_provider
import manifest


class OpenRouterHTTPError(RuntimeError):
    def __init__(self, code: int, body: str, attempts: int = 1):
        self.code = code
        self.body = body
        self.attempts = attempts
        super().__init__(f"OpenRouter HTTP {code}: {body}")


class OpenRouterImageError(RuntimeError):
    def __init__(self, message: str, error_type: str = "openrouter_image"):
        self.error_type = error_type
        super().__init__(message)


def load_env(path: Path = LOCAL_ENV) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def post_json(payload: dict, api_key: str, endpoint: str = ENDPOINT) -> dict:
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/SydneyMCDonaldbigking/sns_skills",
            "X-Title": "viral-social-remix",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise OpenRouterHTTPError(exc.code, body) from exc


def save_images(response: dict, out_dir: Path, stem: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    choices = response.get("choices", [])
    for choice_index, choice in enumerate(choices, start=1):
        message = choice.get("message", {})
        candidates = []
        candidates.extend(message.get("images") or [])
        content = message.get("content")
        if isinstance(content, list):
            candidates.extend(
                item for item in content if isinstance(item, dict) and "image_url" in item
            )
        elif isinstance(content, str) and "data:image" in content:
            start = content.find("data:image")
            end = content.find(")", start)
            candidates.append({"image_url": {"url": content[start:end if end > start else None]}})

        for image_index, candidate in enumerate(candidates, start=1):
            image_url = candidate.get("image_url", candidate)
            if isinstance(image_url, dict):
                url = image_url.get("url", "")
            else:
                url = str(image_url)
            if not url:
                continue
            suffix = f"{choice_index}-{image_index}"
            out_path = out_dir / f"{stem}-{suffix}.png"
            if url.startswith("data:image"):
                header, encoded = url.split(",", 1)
                out_path.write_bytes(base64.b64decode(encoded))
            else:
                with urlopen(url, timeout=180) as response_obj:
                    out_path.write_bytes(response_obj.read())
            saved.append(out_path)
    return saved


def request_with_retries(
    payload: dict,
    api_key: str,
    *,
    endpoint: str = ENDPOINT,
    max_attempts: int = 2,
    request_fn=None,
) -> dict:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    request_fn = request_fn or post_json
    last_signature = None
    same_error_count = 0
    for attempt in range(1, max_attempts + 1):
        try:
            return request_fn(payload, api_key, endpoint=endpoint)
        except OpenRouterHTTPError as exc:
            signature = (exc.code, exc.body)
            same_error_count = same_error_count + 1 if signature == last_signature else 1
            last_signature = signature
            exc.attempts = attempt
            if same_error_count >= 2 or attempt == max_attempts:
                raise

    raise RuntimeError("unreachable retry state")


def mark_manifest_failed(
    manifest_path: str | Path | None,
    asset_id: str | None,
    error: Exception,
) -> None:
    if not manifest_path or not asset_id:
        return

    path = Path(manifest_path)
    data = manifest.load(path)
    current_attempts = int(data["assets"][asset_id].get("attempts", 0))
    attempts = getattr(error, "attempts", 1)
    last_error = {
        "type": getattr(error, "error_type", "openrouter_error"),
        "message": str(error),
        "attempts": attempts,
    }
    if isinstance(error, OpenRouterHTTPError):
        last_error.update(
            {
                "type": "openrouter_http",
                "code": error.code,
                "body": error.body[:1000],
            }
        )
    manifest.mark(
        path,
        asset_id,
        "failed",
        attempts=current_attempts + attempts - 1,
        validation_errors=[str(error)],
        last_error=last_error,
    )


def _manifest_root(manifest_path: str | Path) -> Path:
    manifest_file = Path(manifest_path)
    return (
        manifest_file.parent.parent
        if manifest_file.parent.name == "analysis"
        else manifest_file.parent
    ).resolve()


def _relative_to_root(path: str | Path, root: Path) -> str:
    target = Path(path).resolve()
    try:
        return target.relative_to(root).as_posix()
    except ValueError:
        return str(target)


def mark_manifest_prompted(
    manifest_path: str | Path | None,
    asset_id: str | None,
    *,
    prompt_path: str | Path,
    endpoint: str,
    payload: dict,
) -> None:
    if not manifest_path or not asset_id:
        return

    root = _manifest_root(manifest_path)
    manifest.mark(
        manifest_path,
        asset_id,
        "prompted",
        prompt_path=_relative_to_root(prompt_path, root),
        request={
            "endpoint": endpoint,
            "payload": redact_payload(payload),
        },
        validation_errors=[],
    )


def mark_manifest_generated(
    manifest_path: str | Path | None,
    asset_id: str | None,
    saved: list[Path],
    *,
    run_root: str | Path | None = None,
    prompt_path: str | Path | None = None,
) -> None:
    if not manifest_path or not asset_id:
        return

    root = Path(run_root).resolve() if run_root else _manifest_root(manifest_path)
    outputs = []
    for path in saved:
        outputs.append(_relative_to_root(path, root))

    fields = {
        "output": outputs[0] if len(outputs) == 1 else outputs,
        "outputs": outputs,
        "validation_errors": [],
    }
    if prompt_path:
        fields["prompt_path"] = _relative_to_root(prompt_path, root)

    manifest.mark(
        manifest_path,
        asset_id,
        "generated",
        **fields,
    )


def load_manifest_asset(
    manifest_path: str | Path | None,
    asset_id: str | None,
) -> dict | None:
    if not manifest_path or not asset_id:
        return None
    data = manifest.load(manifest_path)
    return data["assets"][asset_id]


def should_skip_validated(
    manifest_path: str | Path | None,
    asset_id: str | None,
    *,
    force: bool = False,
) -> bool:
    item = load_manifest_asset(manifest_path, asset_id)
    return bool(item and item.get("status") == "validated" and not force)


def build_payload(
    prompt: str,
    *,
    model: str,
    size: str,
    quality: str,
    references: list[str] | None = None,
) -> dict:
    content = [
        {
            "type": "text",
            "text": (
                f"{prompt}\n\nOutput requirements: generate one image at "
                f"{size}. Use {quality} quality. Return an image."
            ),
        }
    ]
    for ref in references or []:
        content.append({"type": "image_url", "image_url": {"url": data_url(Path(ref))}})

    return {
        "model": model,
        "modalities": ["image", "text"],
        "size": size,
        "quality": quality,
        "messages": [{"role": "user", "content": content}],
    }


def redact_payload(payload: dict) -> dict:
    redacted = json.loads(json.dumps(payload))
    for message in redacted.get("messages", []):
        content = message.get("content", [])
        if not isinstance(content, list):
            continue
        for item in content:
            image_url = item.get("image_url") if isinstance(item, dict) else None
            if isinstance(image_url, dict) and str(image_url.get("url", "")).startswith("data:"):
                image_url["url"] = "<redacted data URL>"
    return redacted


def resolve_generation_config(
    *,
    model: str | None = None,
    quality: str | None = None,
) -> dict:
    load_env()
    config = image_provider.resolve()
    return {
        "model": model or config["model"],
        "quality": quality or config["quality"],
        "endpoint": config["endpoint"] or ENDPOINT,
        "api_key": os.environ.get("OPENROUTER_API_KEY"),
    }


def generate_image(
    *,
    prompt_file: str | Path,
    out_dir: str | Path,
    stem: str = "openrouter-image",
    size: str = "1152x1152",
    quality: str | None = None,
    model: str | None = None,
    references: list[str] | None = None,
    raw_response: str | Path | None = None,
    max_attempts: int = 2,
    manifest_path: str | Path | None = None,
    asset_id: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> dict:
    if bool(manifest_path) != bool(asset_id):
        raise SystemExit("--manifest and --asset-id must be used together")

    config = resolve_generation_config(model=model, quality=quality)
    if not dry_run and should_skip_validated(
        manifest_path,
        asset_id,
        force=force,
    ):
        return {
            "skipped": True,
            "reason": "asset already validated",
            "asset_id": asset_id,
            "status": "validated",
        }

    api_key = config["api_key"]
    if not api_key and not dry_run:
        raise SystemExit("OPENROUTER_API_KEY is not set")

    prompt = Path(prompt_file).read_text(encoding="utf-8")
    payload = build_payload(
        prompt,
        model=config["model"],
        size=size,
        quality=config["quality"],
        references=references or [],
    )
    if dry_run:
        return {
            "endpoint": config["endpoint"],
            "api_key_set": bool(api_key),
            "payload": redact_payload(payload),
        }

    mark_manifest_prompted(
        manifest_path,
        asset_id,
        prompt_path=prompt_file,
        endpoint=config["endpoint"],
        payload=payload,
    )
    try:
        response = request_with_retries(
            payload,
            api_key,
            endpoint=config["endpoint"],
            max_attempts=max_attempts,
        )
    except OpenRouterHTTPError as exc:
        mark_manifest_failed(manifest_path, asset_id, exc)
        raise SystemExit(str(exc)) from exc

    if raw_response:
        raw_path = Path(raw_response)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(
            json.dumps(response, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    saved = save_images(response, Path(out_dir), stem)
    if not saved:
        error = OpenRouterImageError("OpenRouter response did not contain any images")
        mark_manifest_failed(manifest_path, asset_id, error)
        raise SystemExit(str(error))
    mark_manifest_generated(
        manifest_path,
        asset_id,
        saved,
        prompt_path=prompt_file,
    )
    return {"saved": [str(path) for path in saved]}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model")
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--stem", default="openrouter-image")
    parser.add_argument("--size", default="1152x1152")
    parser.add_argument("--quality")
    parser.add_argument("--reference", action="append", default=[])
    parser.add_argument("--raw-response")
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--manifest", help="Optional manifest path to mark failed assets.")
    parser.add_argument("--asset-id", help="Asset id to update when --manifest is used.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even when the manifest asset is already validated.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the redacted request payload without calling OpenRouter.",
    )
    args = parser.parse_args(argv)
    result = generate_image(
        prompt_file=args.prompt_file,
        out_dir=args.out_dir,
        stem=args.stem,
        size=args.size,
        quality=args.quality,
        model=args.model,
        references=args.reference,
        raw_response=args.raw_response,
        max_attempts=args.max_attempts,
        manifest_path=args.manifest,
        asset_id=args.asset_id,
        force=args.force,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
