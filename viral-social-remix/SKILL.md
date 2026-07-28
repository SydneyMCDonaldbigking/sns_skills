---
name: viral-social-remix
description: Use when a user provides a viral social-post URL, image, video, local file, local folder, or original food brief and wants a branded Xiaohongshu, Instagram/Facebook, carousel, or Seedance/Grok video remix.
---

# Viral Social Remix

Use this file only as a route map. Current user instructions override memory.
Never load the whole vault.

## Context

Always read `brand-profile.md` and `references/brand-region-assets.md`. Reuse
known product and brand values. Product and brand are mandatory.
Ask only for missing mandatory fields or low-confidence platform when a value
is still `未填写`.

For an original cooking commercial, skip the memory index and read only
`references/cooking-video-workflow.md`. For other routes, read
`docs/memory/viral-social-remix/index.md`, then only the linked route note.

Search `data/material-index.jsonl` before recollecting known sources or assets.
Use `scripts/query_material_index.py` or `scripts/build_remix_context.py` only
when needed.

## Choose one route

Infer the source platform and target output platform separately.

- **Xiaohongshu source to English carousel**: preserve page count, order,
  meaning, and page roles; output natural English `1152x1152` and
  `caption-en.txt`.
- **Chinese Xiaohongshu output**: preserve the source structure; output
  `1152x1536` and `caption-zh.txt`.
- **Instagram/Facebook carousel**: preserve page count and roles; output
  natural English `1152x1152` and `caption-en.txt`.
- **General video remix**: select exactly nine narrative frames and build the
  requested storyboard/contact sheet.
- **Original cooking commercial**: use `vertical-video`, `9:16`,
  `1080x1920`, and the director-first-frame route below.

For carousel and general video routes, load `references/platform-profiles.md`
and `references/breakdown-schema.md`. Load
`references/xiaohongshu-real-talk-template.md` only for real-talk posts and
`references/instagram-pantry-essentials-template.md` only for pantry posts.

## Acquire and prepare

Accept a post URL, active logged-in tab, local file, local folder, or original
brief.

- Scan a local folder with `scripts/scan_media.py`.
- Capture Xiaohongshu with `scripts/xhs_browser_capture.mjs`, then
  `scripts/capture_source_package.py`.
- Use `scripts/capture_source_package.py` for other source packages.

Preserve source order, caption, author, URL, page count, media files, and a
screenshot fallback. Do not claim blocked originals were downloaded.

Create a resumable run with `scripts/create_run_dir.py`,
`scripts/prepare_remix_run.py`, or `scripts/run_pipeline.py`. Follow
`references/output-schema.md`; keep state in `scripts/manifest.py`; never
overwrite a prior run. Run deterministic validation before paid generation.

## Carousel

Preserve layout logic and copy meaning. Keep the final shopping/search guide
unless the user waives it. Use real supplied UI/screenshots; never invent
prices, products, or app screens.

Load `references/prompt-patterns.md` and `references/image-provider.md`. Resolve
the provider with `scripts/image_provider.py`. Production GPT Image 2 uses the
configured image API; `openai/gpt-5.4-image-2` is the explicit legacy route.
Load `references/fixed-brand-scenes.md` only when a warehouse scene is required.
When the API is available, generate the assets; do not stop at prompts.

## Original cooking commercial

Load `references/cooking-video-workflow.md` as the single production authority.
Load `references/seedance-video.md` only after a runner/API failure.

Default:

`3 director-designed first frames -> 3 silent Seedance clips x 6s -> ChatCut finish`

- Direct three script beats. For each clip choose the angle, composition,
  starting action, one camera move, and intended endpoint.
- Generate exactly three `1080x1920` first frames containing the supplied
  product and official physical `ASIAN GROCER ONLINE / powered by UMALL`
  company table sign as a real physical prop.
- Give each Seedance request only its own opening frame. Use a designed or
  returned last frame only when a join needs exact control.
- Use `6s`, `9:16`, `1080p`, silent generation, no face, and no generated
  subtitles or overlays.
- Review all three clips once and retry only a visible failure.
- Import only accepted MP4 clips into ChatCut. Never import first frames,
  storyboards, product/logo references, contact sheets, or QA images.
- Keep the coherent natural duration. Generate editable BGM and cooking SFX;
  add the user's voiceover when supplied; add centered white editable
  current-step captions with a subtle dark stroke/shadow and no colored box.

Prepare with `scripts/run_pipeline.py prepare-original-video`. Generate each
clip with `scripts/run_seedance_video.py --storyboard-group 1`, then repeat for
groups 2 and 3. Use `scripts/run_openrouter_video.py` and
`references/openrouter-video.md` only for an explicitly selected Grok route.

## Finish

After generation, make one representative visual pass across all clips. After
export, verify the actual file's duration, dimensions, streams, opening, joins,
ending, and audio tail. Use deeper QA or troubleshooting only after a concrete
failure.

Write a run note only after success and only when it contains a reusable
lesson. Never store keys, raw provider responses, signed URLs, or base64
payloads in Obsidian.

Do not bypass authentication or anti-scraping controls. Do not reproduce source
watermarks, unauthorized logos, or real-person identity.
