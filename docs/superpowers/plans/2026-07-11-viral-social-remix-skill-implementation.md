# Viral Social Remix Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable Codex skill that ingests social-post links, individual media files, or local media folders; decomposes viral content; and produces platform-specific GPT Image 2 image sets or nine-frame video storyboards with resumable manifests and deterministic validation.

**Architecture:** Keep creative judgment and Codex tool orchestration in a concise `SKILL.md`, while deterministic media operations live in focused Python scripts. Store platform rules, breakdown fields, prompt contracts, and output schemas in progressively loaded references. Use a JSON manifest as the stable boundary between analysis, generation, retries, validation, and resume behavior.

**Tech Stack:** Codex skills, Python 3.11+, Pillow, pytest, ffmpeg/ffprobe executables, GPT Image 2 through Codex's built-in image generation capability.

---

## File map

- `pyproject.toml`: Python package metadata and test dependencies.
- `viral-social-remix/SKILL.md`: top-level routing, required inputs, Codex tool calls, quality gates, and recovery flow.
- `viral-social-remix/agents/openai.yaml`: UI-facing skill metadata.
- `viral-social-remix/scripts/scan_media.py`: recursively discover and group supported local media.
- `viral-social-remix/scripts/manifest.py`: create, load, update, and resume task manifests.
- `viral-social-remix/scripts/extract_keyframes.py`: probe videos, create candidate frames, and export nine selected timestamps.
- `viral-social-remix/scripts/make_contact_sheet.py`: build carousel overviews and 3×3 storyboard sheets.
- `viral-social-remix/scripts/validate_output.py`: validate dimensions, required files, text-review state, and completion.
- `viral-social-remix/references/platform-profiles.md`: Xiaohongshu, Instagram/Facebook, and video output rules.
- `viral-social-remix/references/breakdown-schema.md`: required image-page and video-frame analysis fields.
- `viral-social-remix/references/prompt-patterns.md`: GPT Image 2 prompt contracts, text rules, and consistency locks.
- `viral-social-remix/references/output-schema.md`: manifest and delivery-directory contracts.
- `tests/`: unit and integration tests mirroring the scripts.

## Task 1: Initialize the skill and test project

**Files:**
- Create: `pyproject.toml`
- Create: `viral-social-remix/SKILL.md`
- Create: `viral-social-remix/agents/openai.yaml`
- Create: `tests/test_skill_structure.py`

- [ ] **Step 1: Write the failing structure test**

```python
from pathlib import Path
import yaml


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "viral-social-remix"


def test_skill_has_valid_minimal_structure():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    frontmatter = yaml.safe_load(text.split("---", 2)[1])
    assert frontmatter["name"] == "viral-social-remix"
    assert "Use when" in frontmatter["description"]
    metadata = yaml.safe_load(
        (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    )
    assert metadata["interface"]["display_name"] == "Viral Social Remix"
```

- [ ] **Step 2: Run the test and verify the missing files fail**

Run: `python -m pytest tests/test_skill_structure.py -v`

Expected: FAIL with `FileNotFoundError` for `viral-social-remix/SKILL.md`.

- [ ] **Step 3: Initialize the skill using the official scaffolder**

Run:

```powershell
python C:\Users\zzyyds\.codex\skills\.system\skill-creator\scripts\init_skill.py viral-social-remix --path . --resources scripts,references --interface display_name="Viral Social Remix" --interface short_description="Remix viral social posts into platform-ready image sets and storyboards" --interface default_prompt="Analyze this viral post or local media folder and generate a platform-ready branded remix."
```

Expected: creates `viral-social-remix/SKILL.md`, `viral-social-remix/agents/openai.yaml`, `scripts/`, and `references/`.

- [ ] **Step 4: Add the Python project configuration**

```toml
[project]
name = "viral-social-remix-skill"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["Pillow>=10.0", "PyYAML>=6.0"]

[project.optional-dependencies]
test = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
```

- [ ] **Step 5: Replace the scaffold frontmatter with the triggering contract**

```markdown
---
name: viral-social-remix
description: Use when a user provides a viral social-post link, image, video, or local media folder and wants a branded Xiaohongshu, Instagram, Facebook, or nine-frame video storyboard remix.
---

# Viral Social Remix

Follow the workflow below. Load only the reference files required by the detected platform and media type.
```

- [ ] **Step 6: Run the structure test**

Run: `python -m pytest tests/test_skill_structure.py -v`

Expected: PASS.

- [ ] **Step 7: Commit the initialized project**

```powershell
git add pyproject.toml viral-social-remix tests/test_skill_structure.py
git commit -m "chore: initialize viral social remix skill"
```

## Task 2: Implement recursive local-media scanning and grouping

**Files:**
- Create: `viral-social-remix/scripts/scan_media.py`
- Create: `tests/test_scan_media.py`

- [ ] **Step 1: Write failing scanner tests**

```python
from pathlib import Path
from viral_social_test_loader import load_script


scan_media = load_script("scan_media")


def test_scan_groups_direct_subfolder_and_root_files(tmp_path: Path):
    (tmp_path / "root.jpg").write_bytes(b"image")
    group = tmp_path / "carousel"
    group.mkdir()
    (group / "01.png").write_bytes(b"image")
    (group / "02.webp").write_bytes(b"image")
    (group / "notes.txt").write_text("ignore", encoding="utf-8")
    output = tmp_path / "output"
    output.mkdir()
    (output / "old.png").write_bytes(b"image")

    result = scan_media.scan(tmp_path)

    assert [item["name"] for item in result["tasks"]] == ["carousel", "root"]
    assert len(result["tasks"][0]["files"]) == 2
    assert result["ignored_count"] == 2


def test_scan_rejects_missing_directory(tmp_path: Path):
    missing = tmp_path / "missing"
    try:
        scan_media.scan(missing)
    except ValueError as exc:
        assert "readable directory" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
```

- [ ] **Step 2: Add the shared test loader**

Create `tests/viral_social_test_loader.py`:

```python
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def load_script(name: str):
    path = Path(__file__).parents[1] / "viral-social-remix" / "scripts" / f"{name}.py"
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module
```

- [ ] **Step 3: Run the scanner tests and verify failure**

Run: `python -m pytest tests/test_scan_media.py -v`

Expected: FAIL because `scan_media.py` does not exist.

- [ ] **Step 4: Implement the scanner**

```python
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


def scan(directory: str | Path) -> dict:
    root = Path(directory)
    if not root.is_dir():
        raise ValueError(f"Expected a readable directory: {root}")

    tasks = []
    accepted: set[Path] = set()
    for child in sorted(p for p in root.iterdir() if p.is_dir() and p.name not in IGNORED_DIRS):
        files = sorted(
            p for p in child.rglob("*")
            if p.is_file()
            and p.suffix.lower() in SUPPORTED
            and not any(part in IGNORED_DIRS or part.startswith(".") for part in p.relative_to(root).parts)
        )
        if files:
            accepted.update(files)
            tasks.append({"name": child.name, "input_kind": "folder", "files": [_record(p, root) for p in files]})

    for path in sorted(root.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED and not path.name.startswith("."):
            accepted.add(path)
            tasks.append({"name": path.stem, "input_kind": "file", "files": [_record(path, root)]})

    all_files = {
        p for p in root.rglob("*")
        if p.is_file() and not any(part in IGNORED_DIRS for part in p.relative_to(root).parts)
    }
    return {"root": str(root.resolve()), "tasks": tasks, "ignored_count": len(all_files - accepted)}
```

- [ ] **Step 5: Run scanner tests**

Run: `python -m pytest tests/test_scan_media.py -v`

Expected: PASS.

- [ ] **Step 6: Commit the scanner**

```powershell
git add viral-social-remix/scripts/scan_media.py tests/test_scan_media.py tests/viral_social_test_loader.py
git commit -m "feat: scan and group local social media"
```

## Task 3: Implement resumable manifests

**Files:**
- Create: `viral-social-remix/scripts/manifest.py`
- Create: `tests/test_manifest.py`

- [ ] **Step 1: Write failing manifest tests**

```python
import json
from viral_social_test_loader import load_script


manifest = load_script("manifest")


def test_manifest_resumes_only_incomplete_assets(tmp_path):
    path = tmp_path / "manifest.json"
    manifest.create(path, "xiaohongshu", ["01", "02"])
    manifest.mark(path, "01", "generated", output="generated/01.png")

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["assets"]["01"]["status"] == "generated"
    assert manifest.pending(path) == ["02"]


def test_manifest_rejects_invalid_status(tmp_path):
    path = tmp_path / "manifest.json"
    manifest.create(path, "video", ["01"])
    try:
        manifest.mark(path, "01", "unknown")
    except ValueError as exc:
        assert "status" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_manifest.py -v`

Expected: FAIL because `manifest.py` does not exist.

- [ ] **Step 3: Implement atomic manifest operations**

```python
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
        "assets": {asset_id: {"status": "pending", "attempts": 0} for asset_id in asset_ids},
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
    return [key for key, value in data["assets"].items() if value["status"] != "validated"]
```

- [ ] **Step 4: Run manifest tests**

Run: `python -m pytest tests/test_manifest.py -v`

Expected: PASS.

- [ ] **Step 5: Commit manifest support**

```powershell
git add viral-social-remix/scripts/manifest.py tests/test_manifest.py
git commit -m "feat: add resumable generation manifest"
```

## Task 4: Implement video probing and frame export

**Files:**
- Create: `viral-social-remix/scripts/extract_keyframes.py`
- Create: `tests/test_extract_keyframes.py`

- [ ] **Step 1: Write failing timestamp and command tests**

```python
from viral_social_test_loader import load_script


frames = load_script("extract_keyframes")


def test_candidate_timestamps_exclude_unstable_edges():
    assert frames.candidate_timestamps(20.0, count=5) == [1.0, 5.5, 10.0, 14.5, 19.0]


def test_selected_export_requires_exactly_nine_timestamps(tmp_path, monkeypatch):
    monkeypatch.setattr(frames, "_run", lambda command: command)
    try:
        frames.export_selected(tmp_path / "a.mp4", [1.0] * 8, tmp_path / "out")
    except ValueError as exc:
        assert "exactly 9" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_extract_keyframes.py -v`

Expected: FAIL because `extract_keyframes.py` does not exist.

- [ ] **Step 3: Implement candidate selection and exact export**

```python
import json
import subprocess
from pathlib import Path


def _run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def duration(video: str | Path) -> float:
    result = _run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", str(video),
    ])
    return float(json.loads(result.stdout)["format"]["duration"])


def candidate_timestamps(seconds: float, count: int = 18) -> list[float]:
    if seconds <= 0 or count < 2:
        raise ValueError("Video duration and candidate count must be positive")
    margin = min(1.0, seconds * 0.05)
    start, end = margin, seconds - margin
    step = (end - start) / (count - 1)
    return [round(start + index * step, 3) for index in range(count)]


def export(video: str | Path, timestamps: list[float], output: str | Path, prefix: str) -> list[str]:
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, timestamp in enumerate(timestamps, 1):
        path = target / f"{prefix}-{index:02d}.jpg"
        _run(["ffmpeg", "-y", "-ss", str(timestamp), "-i", str(video), "-frames:v", "1", "-q:v", "2", str(path)])
        paths.append(str(path))
    return paths


def export_candidates(video: str | Path, output: str | Path, count: int = 18) -> list[str]:
    return export(video, candidate_timestamps(duration(video), count), output, "candidate")


def export_selected(video: str | Path, timestamps: list[float], output: str | Path) -> list[str]:
    if len(timestamps) != 9:
        raise ValueError("Video storyboards require exactly 9 timestamps")
    return export(video, timestamps, output, "keyframe")
```

- [ ] **Step 4: Run unit tests**

Run: `python -m pytest tests/test_extract_keyframes.py -v`

Expected: PASS.

- [ ] **Step 5: Add a real ffmpeg smoke check**

Run: `ffmpeg -version`

Expected: exit code 0 and an ffmpeg version header. If missing, stop execution and ask the user to install ffmpeg; do not silently replace video extraction with approximate image sampling.

- [ ] **Step 6: Commit frame extraction**

```powershell
git add viral-social-remix/scripts/extract_keyframes.py tests/test_extract_keyframes.py
git commit -m "feat: extract candidate and selected video frames"
```

## Task 5: Implement carousel and storyboard contact sheets

**Files:**
- Create: `viral-social-remix/scripts/make_contact_sheet.py`
- Create: `tests/test_make_contact_sheet.py`

- [ ] **Step 1: Write failing contact-sheet tests**

```python
from PIL import Image
from viral_social_test_loader import load_script


sheets = load_script("make_contact_sheet")


def test_storyboard_is_1920_by_1080(tmp_path):
    inputs = []
    for index in range(9):
        path = tmp_path / f"{index}.png"
        Image.new("RGB", (640, 360), (index * 20, 40, 80)).save(path)
        inputs.append(path)
    output = tmp_path / "storyboard.png"

    sheets.make_storyboard(inputs, output, [f"Frame {index + 1}" for index in range(9)])

    assert Image.open(output).size == (1920, 1080)


def test_storyboard_rejects_non_nine_input(tmp_path):
    try:
        sheets.make_storyboard([], tmp_path / "out.png", [])
    except ValueError as exc:
        assert "9 images" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_make_contact_sheet.py -v`

Expected: FAIL because `make_contact_sheet.py` does not exist.

- [ ] **Step 3: Implement the 3×3 storyboard and generic carousel sheet**

```python
from math import ceil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    ratio = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize((round(image.width * ratio), round(image.height * ratio)))
    left = (resized.width - size[0]) // 2
    top = (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def make_storyboard(inputs, output, labels):
    if len(inputs) != 9 or len(labels) != 9:
        raise ValueError("Storyboard requires exactly 9 images and 9 labels")
    canvas = Image.new("RGB", (1920, 1080), "#111111")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=20)
    cell_w, cell_h, label_h = 640, 360, 38
    for index, (path, label) in enumerate(zip(inputs, labels)):
        x, y = (index % 3) * cell_w, (index // 3) * cell_h
        image = _cover(Image.open(path).convert("RGB"), (cell_w, cell_h))
        canvas.paste(image, (x, y))
        draw.rectangle((x, y + cell_h - label_h, x + cell_w, y + cell_h), fill=(0, 0, 0, 180))
        draw.text((x + 12, y + cell_h - 30), f"{index + 1}. {label}", fill="white", font=font)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def make_carousel(inputs, output, columns=4, thumb=(384, 384)):
    if not inputs:
        raise ValueError("Carousel requires at least one image")
    rows = ceil(len(inputs) / columns)
    canvas = Image.new("RGB", (columns * thumb[0], rows * thumb[1]), "#111111")
    for index, path in enumerate(inputs):
        image = _cover(Image.open(path).convert("RGB"), thumb)
        canvas.paste(image, ((index % columns) * thumb[0], (index // columns) * thumb[1]))
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
```

- [ ] **Step 4: Run contact-sheet tests**

Run: `python -m pytest tests/test_make_contact_sheet.py -v`

Expected: PASS.

- [ ] **Step 5: Commit contact sheets**

```powershell
git add viral-social-remix/scripts/make_contact_sheet.py tests/test_make_contact_sheet.py
git commit -m "feat: build carousel and storyboard overviews"
```

## Task 6: Implement deterministic output validation

**Files:**
- Create: `viral-social-remix/scripts/validate_output.py`
- Create: `tests/test_validate_output.py`

- [ ] **Step 1: Write failing platform-validation tests**

```python
from PIL import Image
from viral_social_test_loader import load_script


validation = load_script("validate_output")


def test_xiaohongshu_rejects_wrong_dimensions(tmp_path):
    path = tmp_path / "01.png"
    Image.new("RGB", (1152, 1152)).save(path)
    result = validation.validate_asset(path, "xiaohongshu", text_review="passed")
    assert result["valid"] is False
    assert "2048x1152" in result["errors"][0]


def test_instagram_asset_passes_with_text_review(tmp_path):
    path = tmp_path / "01.png"
    Image.new("RGB", (1152, 1152)).save(path)
    result = validation.validate_asset(path, "instagram-facebook", text_review="passed")
    assert result == {"valid": True, "errors": []}


def test_video_delivery_requires_nine_frames(tmp_path):
    generated = tmp_path / "generated"
    generated.mkdir()
    for index in range(8):
        Image.new("RGB", (1920, 1080)).save(generated / f"{index + 1:02d}.png")
    result = validation.validate_delivery(tmp_path, "video")
    assert "exactly 9 generated frames" in result["errors"]
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_validate_output.py -v`

Expected: FAIL because `validate_output.py` does not exist.

- [ ] **Step 3: Implement validation rules**

```python
from pathlib import Path
from PIL import Image


DIMENSIONS = {
    "xiaohongshu": (2048, 1152),
    "instagram-facebook": (1152, 1152),
    "video": (1920, 1080),
}


def validate_asset(path: str | Path, platform: str, text_review: str) -> dict:
    errors = []
    target = Path(path)
    if platform not in DIMENSIONS:
        errors.append(f"unsupported platform: {platform}")
    elif not target.is_file():
        errors.append(f"missing file: {target}")
    else:
        with Image.open(target) as image:
            expected = DIMENSIONS[platform]
            if image.size != expected:
                errors.append(f"expected {expected[0]}x{expected[1]}, got {image.width}x{image.height}")
    if text_review != "passed":
        errors.append("text review must be passed")
    return {"valid": not errors, "errors": errors}


def validate_delivery(root: str | Path, platform: str) -> dict:
    base = Path(root)
    errors = []
    generated = sorted((base / "generated").glob("*.png")) if (base / "generated").exists() else []
    required = [
        base / "analysis" / "breakdown.md",
        base / "analysis" / "copy.md",
        base / "analysis" / "prompts.md",
        base / "analysis" / "manifest.json",
        base / "overview" / "contact-sheet.png",
        base / "qa" / "validation.json",
    ]
    errors.extend(f"missing required file: {path}" for path in required if not path.is_file())
    if platform == "video" and len(generated) != 9:
        errors.append("exactly 9 generated frames")
    return {"valid": not errors, "errors": errors}
```

- [ ] **Step 4: Run validation tests**

Run: `python -m pytest tests/test_validate_output.py -v`

Expected: PASS.

- [ ] **Step 5: Commit validation**

```powershell
git add viral-social-remix/scripts/validate_output.py tests/test_validate_output.py
git commit -m "feat: validate platform output contracts"
```

## Task 7: Write platform, analysis, prompt, and output references

**Files:**
- Create: `viral-social-remix/references/platform-profiles.md`
- Create: `viral-social-remix/references/breakdown-schema.md`
- Create: `viral-social-remix/references/prompt-patterns.md`
- Create: `viral-social-remix/references/output-schema.md`
- Create: `tests/test_reference_contracts.py`

- [ ] **Step 1: Write failing reference-contract tests**

```python
from pathlib import Path


REF = Path(__file__).parents[1] / "viral-social-remix" / "references"


def test_platform_profiles_contain_exact_output_contracts():
    text = (REF / "platform-profiles.md").read_text(encoding="utf-8")
    for required in ["2048×1152", "1152×1152", "1920×1080", "exactly 9"]:
        assert required in text


def test_prompt_contract_requires_verbatim_text_and_consistency():
    text = (REF / "prompt-patterns.md").read_text(encoding="utf-8")
    assert "Text (verbatim)" in text
    assert "Consistency lock" in text


def test_output_schema_names_every_delivery_file():
    text = (REF / "output-schema.md").read_text(encoding="utf-8")
    for required in ["breakdown.md", "copy.md", "prompts.md", "manifest.json", "validation.json"]:
        assert required in text
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_reference_contracts.py -v`

Expected: FAIL because the reference files do not yet exist.

- [ ] **Step 3: Write `platform-profiles.md`**

Include this exact table and routing rule:

```markdown
# Platform Profiles

| Profile | Language | Asset size | Asset count |
|---|---|---:|---|
| Xiaohongshu image carousel | Chinese | 2048×1152 | Match source page count |
| Instagram/Facebook carousel | Natural English | 1152×1152 | Match source page count |
| Video storyboard | Match target market | 1920×1080 | exactly 9 generated frames plus one 1920×1080 contact sheet |

Use an explicit user platform when supplied. Otherwise infer from URL domain, page metadata, media dimensions, language, UI traces, and folder naming. Ask only when confidence is low.
```

- [ ] **Step 4: Write `breakdown-schema.md`**

Define required image fields `page_id`, `page_role`, `composition`, `subject`, `text_hierarchy`, `palette`, `viral_hook`, `transition`, and `replacement_mapping`. Define required video fields `frame_id`, `timestamp`, `narrative_role`, `shot`, `on_screen_text`, `continuity`, and `replacement_mapping`. Mark inferred audience, setting, benefits, and theme with `inferred: true`.

- [ ] **Step 5: Write `prompt-patterns.md`**

```markdown
# GPT Image 2 Prompt Contracts

For each asset, provide: platform, source role, primary request, product and brand, scene, subject, composition, text hierarchy, palette, exact copy, invariants, and avoid list.

Text (verbatim): "<exact Chinese or English copy>"

Consistency lock: preserve the approved product appearance, packaging geometry, brand spelling, recurring person description, palette, lighting family, and typography hierarchy across every asset in the group.

Generate text directly in the image. After generation, visually verify brand name, product name, numbers, language, and CTA. Retry only the failed asset. Use local text overlay only after repeated targeted regeneration fails.
```

- [ ] **Step 6: Write `output-schema.md`**

Specify the exact delivery tree from the design, manifest schema version `1`, statuses from Task 3, source provenance, platform confidence, assumptions, per-asset prompt, output path, text-review state, validation errors, and retry count.

- [ ] **Step 7: Run reference tests**

Run: `python -m pytest tests/test_reference_contracts.py -v`

Expected: PASS.

- [ ] **Step 8: Commit references**

```powershell
git add viral-social-remix/references tests/test_reference_contracts.py
git commit -m "docs: define platform and generation contracts"
```

## Task 8: Complete the top-level Skill workflow

**Files:**
- Modify: `viral-social-remix/SKILL.md`
- Modify: `viral-social-remix/agents/openai.yaml`
- Modify: `tests/test_skill_structure.py`

- [ ] **Step 1: Extend the failing Skill contract test**

```python
def test_skill_routes_every_input_and_platform():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    required = [
        "post URL", "local file", "local folder", "scan_media.py",
        "Xiaohongshu", "Instagram/Facebook", "exactly nine",
        "GPT Image 2", "manifest.py", "validate_output.py",
    ]
    for phrase in required:
        assert phrase in text


def test_skill_requires_product_and_brand_only():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "Product and brand are mandatory" in text
    assert "Ask only for missing mandatory fields or low-confidence platform" in text
```

- [ ] **Step 2: Run the Skill tests and verify failure**

Run: `python -m pytest tests/test_skill_structure.py -v`

Expected: FAIL listing missing workflow phrases.

- [ ] **Step 3: Write the complete concise workflow**

The final `SKILL.md` must contain these imperative sections:

```markdown
## Intake

Accept a public post URL, local file, or local folder. For a local folder, run `scripts/scan_media.py`, show the discovered task list, and process each valid group independently. Product and brand are mandatory. Infer audience, setting, benefits, and theme; label those assumptions.

## Route

Infer platform from source and media signals. Ask only for missing mandatory fields or low-confidence platform. Load `references/platform-profiles.md`, then load the media-specific fields from `references/breakdown-schema.md`.

## Analyze

For image posts, preserve source page count and assign each page a role. For video, export candidate frames with `scripts/extract_keyframes.py`, inspect them, select exactly nine timestamps mapped to Hook, setup, pain, product, mechanism, benefit, proof, result, and CTA, then export the selected frames.

## Generate

Write `breakdown.md`, `copy.md`, `prompts.md`, and `manifest.json` before image generation. Load `references/prompt-patterns.md`. Call GPT Image 2 once per pending asset. Generate the exact Chinese or English text directly in the image. Preserve source composition, hierarchy, rhythm, and copy structure while replacing product, brand, and specific expression.

## Validate and resume

Visually review text and product fidelity, then run `scripts/validate_output.py`. Retry only failed assets and update `scripts/manifest.py` after each state change. Build the carousel overview or exactly nine-frame storyboard with `scripts/make_contact_sheet.py`. On restart, skip assets already marked `validated`.

## Boundaries

Do not bypass login or anti-scraping restrictions. Ask for an upload or readable local folder. Do not reproduce source watermarks, unauthorized logos, or a real person's identity. Keep all final deliverables in the project workspace.
```

- [ ] **Step 4: Regenerate matching UI metadata**

Run:

```powershell
python C:\Users\zzyyds\.codex\skills\.system\skill-creator\scripts\generate_openai_yaml.py viral-social-remix --interface display_name="Viral Social Remix" --interface short_description="Remix viral social posts into branded image sets and storyboards" --interface default_prompt="Analyze this viral post, media file, or local folder and create a platform-ready branded remix."
```

Expected: `agents/openai.yaml` matches the final Skill purpose and contains no optional fields not explicitly requested.

- [ ] **Step 5: Run Skill contract tests**

Run: `python -m pytest tests/test_skill_structure.py -v`

Expected: PASS.

- [ ] **Step 6: Commit the orchestrator**

```powershell
git add viral-social-remix/SKILL.md viral-social-remix/agents/openai.yaml tests/test_skill_structure.py
git commit -m "feat: orchestrate viral social remix workflow"
```

## Task 9: Add an end-to-end fixture test and validate the skill package

**Files:**
- Create: `tests/test_end_to_end_fixture.py`
- Modify: `.gitignore`
- Modify: `viral-social-remix/scripts/validate_output.py`

- [ ] **Step 1: Write the failing local-folder integration test**

```python
import json
from pathlib import Path
from PIL import Image
from viral_social_test_loader import load_script


scanner = load_script("scan_media")
manifest = load_script("manifest")
validation = load_script("validate_output")


def test_local_folder_to_validated_carousel_fixture(tmp_path: Path):
    incoming = tmp_path / "incoming" / "carousel"
    incoming.mkdir(parents=True)
    Image.new("RGB", (800, 450), "red").save(incoming / "01.jpg")
    Image.new("RGB", (800, 450), "blue").save(incoming / "02.jpg")
    scan = scanner.scan(tmp_path / "incoming")
    assert len(scan["tasks"]) == 1
    assert len(scan["tasks"][0]["files"]) == 2

    delivery = tmp_path / "output" / "carousel"
    manifest_path = delivery / "analysis" / "manifest.json"
    manifest.create(manifest_path, "xiaohongshu", ["01", "02"])
    for name in ["breakdown.md", "copy.md", "prompts.md"]:
        path = delivery / "analysis" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture", encoding="utf-8")
    generated = delivery / "generated"
    generated.mkdir(parents=True)
    for asset_id in ["01", "02"]:
        Image.new("RGB", (2048, 1152), "white").save(generated / f"{asset_id}.png")
        manifest.mark(manifest_path, asset_id, "validated", output=f"generated/{asset_id}.png")
    (delivery / "overview").mkdir()
    Image.new("RGB", (1536, 384), "white").save(delivery / "overview" / "contact-sheet.png")
    (delivery / "qa").mkdir()
    (delivery / "qa" / "validation.json").write_text(json.dumps({"valid": True}), encoding="utf-8")

    assert validation.validate_delivery(delivery, "xiaohongshu")["valid"] is True
    assert manifest.pending(manifest_path) == []


def test_delivery_rejects_incomplete_manifest(tmp_path: Path):
    delivery = tmp_path / "output" / "carousel"
    manifest_path = delivery / "analysis" / "manifest.json"
    manifest.create(manifest_path, "xiaohongshu", ["01"])
    for name in ["breakdown.md", "copy.md", "prompts.md"]:
        path = delivery / "analysis" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture", encoding="utf-8")
    (delivery / "overview").mkdir(parents=True)
    Image.new("RGB", (1536, 384), "white").save(delivery / "overview" / "contact-sheet.png")
    (delivery / "qa").mkdir()
    (delivery / "qa" / "validation.json").write_text(json.dumps({"valid": False}), encoding="utf-8")

    result = validation.validate_delivery(delivery, "xiaohongshu")

    assert "manifest contains incomplete assets: 01" in result["errors"]
```

- [ ] **Step 2: Run the integration test and verify the first failure**

Run: `python -m pytest tests/test_end_to_end_fixture.py -v`

Expected: FAIL because `validate_delivery()` does not yet inspect incomplete manifest assets.

- [ ] **Step 3: Make delivery validation reject incomplete manifests**

Add this logic inside `validate_delivery()` after the required-file check:

```python
    manifest_path = base / "analysis" / "manifest.json"
    if manifest_path.is_file():
        import json
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        incomplete = [
            asset_id for asset_id, item in data.get("assets", {}).items()
            if item.get("status") != "validated"
        ]
        if incomplete:
            errors.append(f"manifest contains incomplete assets: {', '.join(incomplete)}")
```

- [ ] **Step 4: Rerun the integration test**

Run: `python -m pytest tests/test_end_to_end_fixture.py -v`

Expected: PASS.

- [ ] **Step 5: Add repository ignores**

```gitignore
__pycache__/
.pytest_cache/
.venv/
output/
tmp/
*.tmp
```

- [ ] **Step 6: Run the full test suite**

Run: `python -m pytest -v`

Expected: all tests PASS.

- [ ] **Step 7: Run the official skill validator**

Run:

```powershell
python C:\Users\zzyyds\.codex\skills\.system\skill-creator\scripts\quick_validate.py viral-social-remix
```

Expected: validation succeeds with valid frontmatter, folder naming, and required metadata.

- [ ] **Step 8: Scan for unfinished placeholders**

Run:

```powershell
rg -n "T[B]D|T[O]DO|implement l[a]ter|fill i[n]" viral-social-remix tests
```

Expected: no matches.

- [ ] **Step 9: Commit the verified package**

```powershell
git add .gitignore tests viral-social-remix
git commit -m "test: verify viral social remix skill end to end"
```

## Task 10: Forward-test realistic Skill behavior

**Files:**
- Create during execution only: `tmp/forward-tests/`
- Modify if failures are discovered: the owning `viral-social-remix/` file and its matching test

- [ ] **Step 1: Record a RED baseline without loading the Skill**

Run three fresh-agent scenarios without the Skill and save raw responses under `tmp/forward-tests/baseline/`:

1. “Analyze this folder of Xiaohongshu images and remix it for Brand A Product B.”
2. “Turn this Instagram carousel into an English carousel for Brand A Product B.”
3. “Break this short video into a nine-frame branded storyboard.”

Record whether the agent misses platform dimensions, source page count, mandatory product/brand checks, exactly-nine frame logic, direct GPT Image 2 text generation, or resume behavior.

- [ ] **Step 2: Run the same scenarios with `$viral-social-remix` loaded**

Expected behavior:

- Local folders are scanned and grouped before analysis.
- Only product, brand, or low-confidence platform questions block execution.
- Xiaohongshu uses Chinese at 2048×1152 and preserves page count.
- Instagram/Facebook uses natural English at 1152×1152 and preserves page count.
- Video maps and exports exactly nine narrative frames at 1920×1080 plus one 1920×1080 storyboard.
- GPT Image 2 generates text directly; local overlay is only a repeated-failure fallback.
- Completed assets are not regenerated when resuming.

- [ ] **Step 3: Close only observed instruction gaps**

For every failure, first add a failing contract test to the owning test file, then minimally revise the relevant Skill or reference file, then rerun the affected test and the full suite.

- [ ] **Step 4: Remove temporary forward-test artifacts**

Delete `tmp/forward-tests/` after extracting the observed failures into permanent tests. Verify `git status --short` contains only intended Skill and test changes.

- [ ] **Step 5: Commit forward-test refinements**

```powershell
git add viral-social-remix tests
git commit -m "test: harden viral social remix workflow"
```

## Final verification and handoff

- [ ] Run `python -m pytest -v` and confirm all tests pass.
- [ ] Run `quick_validate.py viral-social-remix` and confirm validation succeeds.
- [ ] Run `git status --short` and confirm the worktree is clean.
- [ ] Push the implementation branch only after the user chooses the integration workflow.
