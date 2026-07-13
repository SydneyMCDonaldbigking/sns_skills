"""Generate images through OpenRouter's chat-completions image models."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).parents[2]
LOCAL_ENV = ROOT / ".env.local"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


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


def post_json(payload: dict, api_key: str) -> dict:
    request = Request(
        ENDPOINT,
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
        raise SystemExit(f"OpenRouter HTTP {exc.code}: {body}") from exc


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=os.environ.get("VSR_IMAGE_MODEL", "openai/gpt-5.4-image-2"))
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--stem", default="openrouter-image")
    parser.add_argument("--size", default="1152x1152")
    parser.add_argument("--quality", default=os.environ.get("VSR_IMAGE_QUALITY", "medium"))
    parser.add_argument("--reference", action="append", default=[])
    parser.add_argument("--raw-response")
    args = parser.parse_args()

    load_env()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is not set")

    prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    content = [
        {
            "type": "text",
            "text": (
                f"{prompt}\n\nOutput requirements: generate one square image at "
                f"{args.size}. Use medium quality. Return an image."
            ),
        }
    ]
    for ref in args.reference:
        content.append({"type": "image_url", "image_url": {"url": data_url(Path(ref))}})

    payload = {
        "model": args.model,
        "modalities": ["image", "text"],
        "size": args.size,
        "quality": args.quality,
        "messages": [{"role": "user", "content": content}],
    }
    response = post_json(payload, api_key)
    if args.raw_response:
        raw_path = Path(args.raw_response)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
    saved = save_images(response, Path(args.out_dir), args.stem)
    print(json.dumps({"saved": [str(path) for path in saved]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
