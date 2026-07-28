---
name: viral-social-remix
description: Use when a user provides a viral social-post URL, image, video, local file, local folder, or original food brief and wants a branded Xiaohongshu, Instagram/Facebook, carousel, or Seedance/Grok video remix.
---

# Viral Social Remix

Keep this file as the route map. Load only the reference needed for the chosen
output. Do not load the whole vault.

## 1. Read persistent context

Read `docs/memory/viral-social-remix/index.md`, then only the linked memory for
the active route. Current user instructions override memory.

Read `brand-profile.md` and `references/brand-region-assets.md` before asking
questions. Reuse completed values; ask only when product or brand is still
`未填写`. Product and brand are mandatory. Ask only for missing mandatory fields or low-confidence platform.

Search `data/material-index.jsonl` before recollecting known sources or brand
assets. Use `scripts/query_material_index.py` and
`scripts/build_remix_context.py` when relevant.

## 2. Classify the route

Infer the source platform and target output platform separately.

- **Xiaohongshu source to English carousel**: preserve page count and meaning,
  output natural English `1152x1152`, write `caption-en.txt`.
- **Chinese Xiaohongshu output**: output `1152x1536`, write
  `caption-zh.txt`.
- **Instagram/Facebook carousel**: preserve source page count, output natural
  English `1152x1152`, write `caption-en.txt`.
- **General video remix**: select exactly nine narrative frames and create a
  `1920x1080` storyboard/contact sheet.
- **Original cooking commercial**: use `vertical-video`, `9:16`,
  `1080x1920`; follow the nine-frame/three-clip contract below.

Load `references/platform-profiles.md` and
`references/breakdown-schema.md`. For `real-talk` Xiaohongshu posts, also load
`references/xiaohongshu-real-talk-template.md`. For `pantry-essentials`
Instagram/Facebook posts, load
`references/instagram-pantry-essentials-template.md`.

## 3. Acquire the source

Accept a post URL, logged-in browser tab, local file, local folder, or original
brief.

- Local folder: run `scripts/scan_media.py`; inspect every discovered image.
- Logged-in social page: reuse the existing Browser/Chrome tab. Do not reload
  or open a duplicate unless necessary.
- Xiaohongshu capture: use `scripts/xhs_browser_capture.mjs`, then
  `scripts/capture_source_package.py`.
- Other source packages: use `scripts/capture_source_package.py`.

Preserve source order, caption, author, URL, page count, media files, and a
screenshot fallback. Do not pretend blocked originals were downloaded.

## 4. Prepare a resumable run

Use `scripts/create_run_dir.py` or `scripts/prepare_remix_run.py`. Follow
`references/output-schema.md`. Store generation state in
`scripts/manifest.py`; never overwrite a prior run.

Required analysis files:

- `analysis/breakdown.md`
- `analysis/copy.md`
- `analysis/prompts.md`
- `analysis/page-prompts/page-XX.md`
- `analysis/manifest.json`
- the required `caption-zh.txt` or `caption-en.txt`

Run `scripts/validate_prepared_run.py` before paid generation.

## 5. Carousel workflow

Preserve each source page's role, layout logic, copy meaning, and page count.
For commerce posts, retain the final shopping/search guide unless the user
waives it. Use real supplied UI/screenshots; do not invent prices, products, or
app screens.

Load `references/prompt-patterns.md` and
`references/image-provider.md`. Resolve the provider through
`scripts/image_provider.py`. GPT Image 2 production uses the configured image
API; `openai/gpt-5.4-image-2` remains the explicit legacy chat-completions
route. If a warehouse scene is required, load
`references/fixed-brand-scenes.md`.

When the image API is available, run it; do not stop at writing prompts:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_openrouter_carousel.py --run output/<run> --api-only --concurrency 2
```

## 6. Original cooking commercial: fixed contract

Load `references/cooking-video-workflow.md`. Do not load the general
`references/seedance-video.md` unless the runner/API needs troubleshooting; its
provider examples do not override this production contract.

The production unit is:

`9 individual storyboard frames -> 3 groups -> 3 silent Seedance clips of 6s -> ChatCut finish at the natural coherent duration`

Hard rules:

1. Use our configured image API to generate all nine individual
   `1080x1920` storyboard frames. Do not send a text-only prompt directly to
   Seedance.
2. Create frame 01 from the product, official logo, and art direction.
   Generate every later frame by editing the previous frame while reusing the
   same product and logo references. Lock the kitchen, pan, hands, clothing,
   lighting, dumpling shape/count, packaging, and camera language.
3. Draw the official `ASIAN GROCER ONLINE` with small `powered by UMALL`
   directly on the same company table sign as a real physical prop in the
   storyboard. Use
   `viral-social-remix/umall_logo/asian-grocer-online-powered-by-umall.png`.
   Do not substitute the Chinese-region UMALL logo. The physical sign is
   established during storyboard generation, not added as a default floating
   post overlay.
4. Produce nine separate PNGs; the 3x3 contact sheet is review-only.
5. Submit exactly three ordered storyboard images per Seedance request:
   frames `01-03` -> clip 1, `04-06` -> clip 2, `07-09` -> clip 3.
   Each clip is 6 seconds, `9:16`, `1080p`, and `generate_audio: false`.
6. Never send one frame per clip, all nine frames to one request, or only one
   three-frame request for the whole commercial.
7. In ChatCut, place the three clips in order. If the 18-second sequence is
   coherent, keep it; trim only failed motion, repeated action, or dead time.
   Never force the edit to 15 seconds.
8. Add the user's recorded Voiceover. Generate the BGM and cooking SFX
   yourself, then place and mix them as separate editable tracks.
9. Add editable English captions that state the current cooking step. Put each
   caption in the visual center of the video, white, with a subtle dark
   stroke/shadow and no colored box. Time captions to the actual action.
10. No face. Storyboards and Seedance output enforce `no visible text`: no
   generated subtitles, title cards, lower-thirds, labels, watermarks, or other
   added text. Product packaging and the real logo sign remain allowed scene
   objects. Final step captions are added only in ChatCut.

Prepare the run with:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_pipeline.py prepare-original-video --brief "brand/product/dish brief" --task-name cooking-commercial
```

After the nine frames validate, dry-run and then submit each group separately:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_seedance_video.py --run output/<run> --storyboard-group 1 --allow-data-url --dry-run
.\.venv\python.exe viral-social-remix\scripts\run_seedance_video.py --run output/<run> --storyboard-group 1 --allow-data-url --approve-final-spend
```

Repeat only the group number for groups 2 and 3. The runner selects `01-03`,
`04-06`, or `07-09` and writes separate clip, request-lock, and QA files.

Use `scripts/run_openrouter_carousel.py` for the nine storyboard images and
`scripts/run_seedance_video.py` for Seedance. Use
`scripts/run_openrouter_video.py` only for an explicitly selected Grok test.
Load `references/openrouter-video.md` for the Grok route.

## 7. Validate and finish

Run `scripts/validate_output.py` and visually inspect the contact sheet. Retry
only failed assets.

For each generated video, inspect representative frames and run
`scripts/video_qa.py prepare`; record `approve` or `reject --reason`. Do not
send rejected clips to ChatCut.

After ChatCut export, run `scripts/video_qa.py prepare-export`, inspect the
actual final file, then record `approve-export` or `reject-export --reason`.
Check duration, aspect ratio, continuity, food state, hand anatomy, exact
product/logo fidelity, audio balance, and audio tail.

Write `output/<run>/qa/run-notes.md` from the memory template only after a
successful run. Distill only reusable lessons; never store keys, raw provider
responses, signed URLs, or base64 payloads in Obsidian.

## 8. Boundaries

Do not bypass authentication or anti-scraping controls. Do not reproduce source
watermarks, unauthorized logos, or real-person identity. If API access is
blocked, finish the resumable run package and give the exact local command
instead of inventing a fallback result.
