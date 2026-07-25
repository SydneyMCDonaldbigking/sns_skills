"""Build a sanitized Obsidian memory summary for viral-social-remix."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
MEMORY_OUTPUT = ROOT / "docs" / "memory" / "viral-social-remix" / "distilled-lessons.md"

RUN_NOTE_SECTIONS = {
    "What Worked",
    "Problems",
    "Fix Next Time",
    "Memory Candidates",
}
RETROSPECTIVE_SECTIONS = {
    "Correct Behavior",
    "Prompting Rule",
    "API Lesson",
}
SENSITIVE_MARKERS = (
    "api_key",
    "api key",
    "authorization",
    "bearer ",
    ".env",
    "b64_json",
    "base64,",
    "data:image",
    "raw/page",
    "raw\\page",
    "openrouter_api_key",
    "grok_openrouter_api_key",
)


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _is_sensitive(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in SENSITIVE_MARKERS)


def _sanitize_lines(lines: Iterable[str]) -> list[str]:
    cleaned = []
    current_bullet: str | None = None
    current_paragraph: str | None = None

    def flush_bullet() -> None:
        nonlocal current_bullet
        if current_bullet:
            cleaned.append(current_bullet)
            current_bullet = None

    def flush_paragraph() -> None:
        nonlocal current_paragraph
        if current_paragraph:
            cleaned.append(current_paragraph)
            current_paragraph = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_bullet()
            flush_paragraph()
            continue
        if _is_sensitive(stripped):
            continue
        if stripped in {"-", "*"}:
            continue
        if stripped.startswith(("- ", "* ")):
            flush_bullet()
            flush_paragraph()
            current_bullet = stripped[2:].strip()
        elif current_bullet and line[:1].isspace():
            current_bullet = f"{current_bullet} {stripped}"
        else:
            flush_bullet()
            if current_paragraph:
                current_paragraph = f"{current_paragraph} {stripped}"
            else:
                current_paragraph = stripped
    flush_bullet()
    flush_paragraph()
    return cleaned


def _extract_sections(text: str, names: set[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {name: [] for name in names}
    current: str | None = None
    for line in text.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            continue
        if current in sections:
            sections[current].append(line)
    return {key: _sanitize_lines(value) for key, value in sections.items()}


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _cost_value(cost: dict) -> str:
    for key in ("total_cost", "total_cost_usd", "cost", "estimated_cost"):
        value = cost.get(key)
        if isinstance(value, (int, float)):
            return f"${value:.4f}"
        if isinstance(value, str) and value:
            return value
    return "unknown"


def summarize_run_note(path: Path, root: Path) -> list[str]:
    run_dir = path.parent.parent
    manifest = _read_json(run_dir / "analysis" / "manifest.json")
    validation = _read_json(run_dir / "qa" / "validation.json")
    cost = _read_json(run_dir / "qa" / "openrouter-cost.json")
    sections = _extract_sections(path.read_text(encoding="utf-8"), RUN_NOTE_SECTIONS)

    platform = manifest.get("platform", "unknown")
    assets = manifest.get("assets") or {}
    valid = validation.get("valid")
    status = "valid" if valid is True else "not valid" if valid is False else "unknown"

    lines = [
        f"### {_relative(run_dir, root)}",
        "",
        f"- Platform: {platform}",
        f"- Assets: {len(assets) if isinstance(assets, dict) else 'unknown'}",
        f"- Validation: {status}",
        f"- Cost: {_cost_value(cost)}",
    ]
    for heading in sorted(RUN_NOTE_SECTIONS):
        items = sections.get(heading, [])
        if not items:
            continue
        lines.extend(["", f"**{heading}**"])
        for item in items[:8]:
            bullet = item[2:].strip() if item.startswith(("- ", "* ")) else item
            lines.append(f"- {bullet}")
    return lines


def summarize_retrospective(path: Path, root: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    title = next(
        (line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("# ")),
        path.stem,
    )
    sections = _extract_sections(text, RETROSPECTIVE_SECTIONS)
    lines = [f"### {title}", "", f"- Source: `{_relative(path, root)}`"]
    for heading in sorted(RETROSPECTIVE_SECTIONS):
        items = sections.get(heading, [])
        if not items:
            continue
        lines.extend(["", f"**{heading}**"])
        for item in items[:8]:
            bullet = item[2:].strip() if item.startswith(("- ", "* ")) else item
            lines.append(f"- {bullet}")
    return lines


def build_summary(root: Path = ROOT) -> str:
    root = root.resolve()
    run_notes = sorted((root / "output").glob("*/qa/run-notes.md"))
    retrospectives = sorted((root / "docs" / "retrospectives").glob("*.md"))
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# Distilled Lessons",
        "",
        f"Generated at `{generated_at}` from sanitized run notes and retrospectives.",
        "The script does not read `raw/`, `source/`, or `generated/` directories.",
        "",
        "## Run Notes",
    ]

    if run_notes:
        for note in run_notes:
            lines.extend(["", *summarize_run_note(note, root)])
    else:
        lines.extend(["", "- No `output/*/qa/run-notes.md` files found yet."])

    lines.extend(["", "## Retrospectives"])
    if retrospectives:
        for retrospective in retrospectives:
            lines.extend(["", *summarize_retrospective(retrospective, root)])
    else:
        lines.extend(["", "- No retrospectives found yet."])

    lines.extend(
        [
            "",
            "## Promotion Rule",
            "",
            "Promote stable lessons into the route-specific notes in this folder.",
            "Keep this generated file as a scan-friendly summary, not the only memory.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root.")
    parser.add_argument(
        "--write",
        action="store_true",
        help=f"Write {MEMORY_OUTPUT.relative_to(ROOT).as_posix()} instead of printing.",
    )
    args = parser.parse_args()

    text = build_summary(args.root)
    if args.write:
        output = args.root / "docs" / "memory" / "viral-social-remix" / "distilled-lessons.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
