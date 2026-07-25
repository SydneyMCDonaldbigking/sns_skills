# 2026-07-23 Chinese Remix Source Drift

## What Happened

During the `澳洲冬季热饮清单｜本地感超市冲调饮品` run, the workflow drifted in
the Chinese remix stage:

- The user supplied a real UMALL mobile Drinks screenshot for the final page.
- I initially over-weighted that screenshot and prepared prompts around the
  phone page products.
- The user clarified: the main image and list pages should use the original
  post; only the generated final page should use the real phone screenshot.
- I also failed to immediately use the already-open Xiaohongshu tab, even
  though it was the fastest and most faithful source.
- PowerShell mojibake made Chinese source text look broken in console output,
  which increased hesitation. The actual files were valid UTF-8.

## Correct Behavior

For Chinese Xiaohongshu 搬运/remix tasks:

- If the user says the original post is open, claim the existing browser tab
  first and capture the carousel before preparing prompts.
- Treat the source post's main images as the primary content and structure
  unless the user explicitly asks to replace them.
- Treat supplied phone screenshots as CTA/search/app-reference assets only when
  the user says they are for the final page.
- Verify the source contact sheet before writing page roles: page count, page
  order, main cover, detail pages, CTA/search pages.
- Do not trust PowerShell console rendering for Chinese. Use UTF-8 file reads,
  browser visual inspection, or image inspection.
- Do not mark a run blocked when the source can be captured from an open
  authenticated browser tab.

## Prompting Rule

Before generation, every page prompt must state:

- Primary reference image for that page.
- Whether the phone screenshot is allowed on that page.
- Exact product list/order.
- Target language and platform size.
- Whether the output is carry-over, localization, or final CTA.

For this run:

- Chinese version: `output/20260723-172529-australia-winter-drinks-xhs`
- English version: `output/20260723-201422-australia-winter-drinks-english`

## API Lesson

OpenRouter chat-completions image generation returned square `1024x1024` for a
portrait Xiaohongshu request. Production carousel generation should default to
the dedicated Images API with `openai/gpt-image-2`, target aspect ratio,
API-only failure behavior, and resumable skips.
