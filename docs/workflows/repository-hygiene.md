# Repository Hygiene

This repo has two jobs:

- Track the reusable skill runtime: `viral-social-remix/`, `tests/`, `docs/`,
  `pyproject.toml`, `environment.yml`, and top-level navigation notes.
- Keep local working material nearby without letting it become Git noise.

## Tracked Structure

- `viral-social-remix/`: the Codex skill package, including route map,
  scripts, references, brand profile, and stable bundled assets.
- `tests/`: deterministic checks for skill structure, scripts, workflow
  contracts, and secret hygiene.
- `docs/workflows/`: durable workflow docs that explain how local production
  systems should be used.
- `docs/memory/`: stable operating memory and distilled lessons. Do not store
  raw run artifacts here.
- `docs/retrospectives/`: incident writeups and guardrail rationale.
- `00-start-here.md`: Obsidian and agent navigation map.

## Local-Only Structure

These directories are intentionally ignored:

- `output/`: timestamped run outputs, generated images, videos, QA files, raw
  provider responses, and delivery packages.
- `samples/`: captured source packages and reference social posts.
- `new_base/`: raw teaching/source material waiting to be distilled.
- `claude_only/`: local product/source images meant for Claude-only or manual
  experiments.
- `.codex_tmp/`, `.tmp/`, `.cleanup-archive/`: scratch runs, smoke artifacts,
  and archived local clutter.
- `.venv/`, `.pytest_cache/`, `__pycache__/`: local Python/runtime state.

## Rules

- Do not commit API keys, `.env.local`, provider payloads, signed URLs, raw
  base64, generated media, or private source screenshots.
- Promote only reusable lessons from `output/<run>/qa/run-notes.md` into
  `docs/memory/` or `viral-social-remix/references/`.
- Keep new production scripts under `viral-social-remix/scripts/` when they are
  part of the skill runtime. Keep one-off helper experiments in `.codex_tmp/`.
- Prefer documenting new local-only directories here and in `.gitignore` before
  using them repeatedly.
