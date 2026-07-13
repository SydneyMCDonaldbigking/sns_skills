# 2026-07-13 API / Token Waste / Secret Handling Retrospective

## What went wrong

- Treated `git backup` as permission to stage too much, including `.env.example`.
- Put a real OpenRouter key into `.env.example`, even briefly.
- Relied on GitHub push protection as a last-line defense instead of preventing the mistake locally.
- Used too many exploratory API/browser/tool calls before narrowing the exact provider model and failure mode.
- Mixed built-in image generation and OpenRouter API testing in the same flow, creating extra output and extra token/tool cost.

## Root causes

- Did not apply a strict secret rule before staging: `.env*` must never be tracked.
- Did not run `git check-ignore` before `git add`.
- Did not separate "find the correct API contract" from "generate the carousel".
- Did not stop early enough after repeated OpenRouter `502` responses.
- Wrote too much status narration while the user wanted fast execution and durable memory.

## Hard rules going forward

- Never commit `.env`, `.env.*`, `.env.example`, API keys, tokens, cookies, or provider secrets.
- Before any commit, run:
  - `git status --short`
  - `git diff --cached --name-only`
  - secret search for known key prefixes
  - `git check-ignore -v .env.local`
- For API image generation, first run one tiny contract test, then one real image, then batch.
- If a provider returns the same transient error twice, stop and record it instead of retrying blindly.
- Keep progress updates short; put durable lessons here instead of spending chat tokens repeating them.

## Current correction

- `.gitignore` blocks `.env*`.
- `.env.example` was removed from git.
- `tests/test_secret_hygiene.py` prevents re-allowing `.env.example`.
- OpenRouter key lives only in ignored `.env.local`.
