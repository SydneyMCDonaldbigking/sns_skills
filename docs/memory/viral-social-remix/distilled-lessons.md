# Distilled Lessons

Generated at `2026-07-23T11:16:45+00:00` from sanitized run notes and retrospectives.
The script does not read `raw/`, `source/`, or `generated/` directories.

## Run Notes

- No `output/*/qa/run-notes.md` files found yet.

## Retrospectives

### 2026-07-13 API / Token Waste / Secret Handling Retrospective

- Source: `docs/retrospectives/2026-07-13-api-token-waste-and-secret-handling.md`

### 2026-07-23 Chinese Remix Source Drift

- Source: `docs/retrospectives/2026-07-23-chinese-remix-source-drift.md`

**API Lesson**
- OpenRouter chat-completions image generation returned square `1024x1024` for a portrait Xiaohongshu request. Production carousel generation should default to the dedicated Images API with `openai/gpt-image-2`, target aspect ratio, API-only failure behavior, and resumable skips.

**Correct Behavior**
- For Chinese Xiaohongshu 搬运/remix tasks:
- If the user says the original post is open, claim the existing browser tab first and capture the carousel before preparing prompts.
- Treat the source post's main images as the primary content and structure unless the user explicitly asks to replace them.
- Treat supplied phone screenshots as CTA/search/app-reference assets only when the user says they are for the final page.
- Verify the source contact sheet before writing page roles: page count, page order, main cover, detail pages, CTA/search pages.
- Do not trust PowerShell console rendering for Chinese. Use UTF-8 file reads, browser visual inspection, or image inspection.
- Do not mark a run blocked when the source can be captured from an open authenticated browser tab.

**Prompting Rule**
- Before generation, every page prompt must state:
- Primary reference image for that page.
- Whether the phone screenshot is allowed on that page.
- Exact product list/order.
- Target language and platform size.
- Whether the output is carry-over, localization, or final CTA.
- For this run:
- Chinese version: `output/20260723-172529-australia-winter-drinks-xhs`

## Promotion Rule

Promote stable lessons into the route-specific notes in this folder.
Keep this generated file as a scan-friendly summary, not the only memory.
