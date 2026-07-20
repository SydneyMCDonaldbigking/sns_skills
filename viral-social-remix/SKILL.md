---
name: viral-social-remix
description: Use when a user provides a viral social-post link, image, video, or local media folder and wants a branded Xiaohongshu, Instagram, Facebook, or nine-frame video storyboard remix.
---

# Viral Social Remix

Follow the workflow below. Load only the reference files required by the detected platform and media type.

## Intake

Read `brand-profile.md` before asking intake questions. Reuse every completed
field. Ask for brand or product only when their values remain `未填写`; infer
other missing fields and label the assumptions. Current-task user input always
overrides the profile.

Accept a public post URL, logged-in browser tab, local file, or local folder.
For a local folder, run `scripts/scan_media.py`, show the discovered task list,
and process each valid group independently. Inspect every local image before
analysis. Product and brand are mandatory. Infer audience, setting, benefits,
and theme; label those assumptions. Ask only for missing mandatory fields or low-confidence platform.

Do not ask again for values already supplied. A user's explicit platform always
overrides automatic detection.

Before asking for examples or product visuals, check the local material index at
`data/material-index.jsonl` when it exists. Use it as a memory of already
collected Xiaohongshu posts, Instagram/Facebook posts, and official brand-site
assets. If it is missing or stale, rebuild it from completed output folders with
`scripts/collect_source_assets.py`. Search it with
`scripts/query_material_index.py` by platform, keyword, record type, or asset
kind before doing new browser/OCR collection. When preparing a remix, use
`scripts/build_remix_context.py` to create a compact source-post plus
brand-asset context pack before loading full source folders into context. For a
new generation task, prefer `scripts/prepare_remix_run.py` to create the
timestamped run directory, analysis skeleton, context pack, caption placeholder,
selected asset mapping, and manifest before drafting prompts.
Run `scripts/validate_prepared_run.py output/<run>` before image generation to
catch missing analysis files, mismatched asset mappings, or leftover `TODO`
draft placeholders.

## API handoff and autonomy

Codex prepares the local source package, localized copy, page prompts, captions,
and manifest. The image API still needs the relevant page prompts and local
reference assets, but that upload must happen from the user's own terminal via
the local runner, not directly from the Codex environment.

For carousel image generation, hand off to the user's local terminal with
`scripts/run_openrouter_carousel.py`. The local runner reads the prepared
`run_dir/analysis/manifest.json`, `run_dir/analysis/page-prompts/page-XX.md`,
and any manifest-listed local reference image paths, uploads them to OpenRouter
page by page, and writes generated output back into the same run directory.
Store page references under `assets[asset_id].reference_paths`; the runner also
accepts legacy `assets[asset_id].request.reference_images`. Use `--api-only
--concurrency 2` for production runs.

If the Codex environment blocks upload or API access, do not bypass it. Finish
the run preparation and output the exact local command for the user to run:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_openrouter_carousel.py --run output/xxx --api-only --concurrency 2
```

Only stop before handoff for a real blocker: missing mandatory brand/product
data, inaccessible logged-in source page, unreadable local source files, or an
incomplete run directory that cannot be fixed locally.

## Source capture

For Xiaohongshu, Instagram, or Facebook posts, treat a user-opened logged-in
browser tab as the preferred source when the page is not publicly readable.
This skill is browser-assisted, not an anonymous crawler. If the user says the
post is open in a browser, claim that existing tab with the available Browser or
Chrome control skill; do not open a duplicate URL, reload the page, or switch
browsers unless the visible tab cannot be reached.

Before analysis, materialize the source into a local source package, then
continue through the normal local-folder path. The package must preserve enough
evidence to resume without the live page:

- `metadata.json` with platform, source URL, page title, author, captured time,
  detected page count, and ordered media list.
- `caption.txt` or platform-specific caption files with the visible source
  copy, hashtags, and date/location when visible.
- `source_urls.txt` for observed media URLs when available.
- `images/01.*`, `images/02.*`, ... in source order for every carousel page or
  video key source frame that can be exported.
- `screenshot.png` or `screenshots/` as visual proof and fallback when original
  media cannot be exported.

For carousel posts, verify the visible page count indicator when present (for
example `1/9`) and preserve that count. Use page assets, visible DOM media URLs,
or authenticated browser context to export media. If originals are blocked,
save ordered screenshots of each slide and record the limitation in
`metadata.json`; do not pretend the original files were downloaded.

For speed and repeatability, export the browser-observed source data to a JSON
file and run `scripts/capture_source_package.py`. For Xiaohongshu profile,
search, or home pages, use `scripts/xhs_browser_capture.mjs` from the browser
control runtime to search from the Xiaohongshu home page or reuse an open
profile/search page. Do not manually browse one post at a time to decide
whether it is usable. First collect and rank visible `/explore/` cards in bulk:
prefer reusable formats such as recommendations, lists, guides, reviews,
recipes, tutorials, and "what to buy" posts; reject ads, livestreams, giveaways,
recruiting, rentals, and obvious commerce-only cards. Open only the highest
ranked candidate unless the user explicitly names a source. Then save
`capture.json` and record `observedImageUrls` after the carousel has loaded.
This lets the package script replace preview URLs such as `nd_prv` with
higher-quality `nd_dft` URLs when both are visible.
The helper should use the DOM-first carousel path: collect non-duplicate swiper
slides in page order without clicking when all pages are present. Fall back to
one right/left warm-up click when a preview URL needs a higher-quality observed
match. Use full active-slide clicking only when DOM media is incomplete or the
preview URL still cannot be upgraded from observed images.

Prefer this JSON shape for carousels so duplicate swiper slides cannot reorder
the media:

```json
{
  "platform": "xiaohongshu",
  "sourceUrl": "https://...",
  "title": "...",
  "author": "...",
  "description": "...",
  "pageCount": 6,
  "slides": [
    {"indicator": "1/6", "url": "https://..."},
    {"indicator": "2/6", "url": "https://..."}
  ]
}
```

Then run:

```powershell
python viral-social-remix/scripts/capture_source_package.py capture.json --output-dir samples/<source-slug>
```

## Route

Infer platform from source domain, page metadata, media dimensions, language,
UI traces, and folder naming. Load `references/platform-profiles.md`, then load
the relevant fields from `references/breakdown-schema.md`.

- Xiaohongshu: preserve source page count, use Chinese, output 1152×1536
  vertical assets by default; 1080×1440 is acceptable when explicitly requested.
- Instagram/Facebook: preserve source page count, use natural English, output
  1152×1152.
- Video: identify the target publishing platform and language, then produce a
  1920×1080 storyboard and 16:9 contact sheet.

## Analyze

For image posts, preserve source page count and assign each page a role. Record
composition, subject, text hierarchy, palette, hook, transition, and replacement
mapping.

For each source image, preserve that image's own format. Do not force a format
learned from a different page onto the current page. If the source page is an
8-combo cover, localize it as one 8-combo cover. If it is an app-entry guide,
localize it as an app-entry guide. If it is a ranked list, recipe step, product
comparison, tutorial, quote card, or detail page, preserve that exact page role,
count, layout logic, and copy rhythm.

For cross-platform localization, translate and rewrite the source post's own
visible copy and caption into natural target-platform language. Do not invent a
new marketing angle when the source copy already provides the angle. Keep the
source meaning, claims, examples, warnings, and sequence; localize wording,
brand, products, units, and platform tone only. If source text is unreadable or
missing, mark the gap in `analysis/copy.md` and infer conservatively from the
visible page, instead of writing unrelated promotional copy.

For the first creative draft, do not decompose one source poster into many
separate generated sub-assets unless the user explicitly asks for that. Use the
source page itself as the main structural reference and make one localized
version of that page first. Only split into ingredient cutouts, product cards,
or local overlays after the whole-page direction is accepted or when the user
asks for a production-accuracy pass.

For video, run `scripts/extract_keyframes.py` to export candidate frames. Inspect
the candidates and select exactly nine timestamps mapped to Hook, setup, pain,
product, mechanism, benefit, proof, result, and CTA. Export those selected
frames. Do not treat evenly spaced candidates as the final narrative selection.

Preserve source composition, hierarchy, rhythm, and copy structure while
replacing the product, brand, and specific expression.

For a Xiaohongshu source whose hook is a first-person return report, hidden
detail, candid warning, concrete mistake, or exact cost, classify it as
`real-talk` and load `references/xiaohongshu-real-talk-template.md`. Apply its
structure only when the source evidence supports it; never invent first-hand
experience for the user.

For an Instagram/Facebook source whose hook is a ranked list, pantry essential,
haul, restock, or "what to buy" post, classify it as `pantry-essentials` and
load `references/instagram-pantry-essentials-template.md`. Preserve the
education-first rhythm: one item per page, one practical use case, and one soft
brand reason.

## Prepare the run

Run `scripts/create_run_dir.py` so each task writes to a new local-system-time
directory. Follow `references/output-schema.md`; never overwrite a previous run.

Before generation, write:

- `analysis/breakdown.md`
- `analysis/copy.md`
- `analysis/prompts.md`
- `analysis/page-prompts/page-XX.md` for every carousel page
- `analysis/manifest.json` using `scripts/manifest.py`
- `analysis/caption-zh.txt` for Xiaohongshu
- `analysis/caption-en.txt` for Instagram/Facebook

Prefer using `scripts/prepare_remix_run.py` to create these files when the task
starts from local indexed examples and brand assets.

For video, write the caption file required by its target publishing platform.
The caption must be ready to paste into the platform, including a hook, body,
CTA, and relevant hashtags. Keep the Chinese natural for Xiaohongshu and the
English natural for Instagram/Facebook.

When visible packaged products matter, load
`references/product-reference-cache.md` and use cached or official SKU images
before image generation.

## Generate

Load `references/prompt-patterns.md` and `references/image-provider.md`. Resolve
the redacted provider defaults with `scripts/image_provider.py`, but do not call
OpenRouter directly from Codex for carousel generation. Default local runner
configuration is OpenRouter `openai/gpt-5.4-image-2` at medium quality when
`OPENROUTER_API_KEY` is available in the user's `.env.local` or environment.
Treat this as the GPT Image 2 generation path for carousel assets.

Write one complete prompt per page in `analysis/page-prompts/page-XX.md`.
Generate the exact Chinese or English text directly in the image; do not default
to local text overlay. Use each source page or selected source frame as a
structural reference while locking product, packaging, recurring people, palette,
lighting, and typography across the group.

For carousel output, instruct the user to run the local API-only runner:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_openrouter_carousel.py --run output/xxx --api-only --concurrency 2
```

The runner saves `raw/page-XX-response.json`, `generated/page-XX.png`, and
`qa/openrouter-cost.json`. It uses at most two concurrent requests, skips pages
already generated at the correct platform size, updates `analysis/manifest.json`,
and stops on the first missing-page API failure when `--api-only` is set. There
is no local-composite fallback in API-only mode.

## Validate and resume

Visually review every generated image for product fidelity, brand spelling,
product spelling, numbers, language, CTA, anatomy, perspective, and continuity.
Run `scripts/validate_output.py asset` for deterministic per-asset checks and
retry only failed assets. For API-only carousel runs, do not use local text
overlay as a fallback.

Build the carousel overview or exactly nine-frame storyboard with
`scripts/make_contact_sheet.py`, then run `scripts/validate_output.py delivery`
to write `qa/validation.json` and check the complete delivery contract. After
successful local runner completion, confirm its generated
`overview/contact-sheet.png`, `qa/validation.json`, and any
`qa/openrouter-cost.json`. On restart, read the manifest and skip assets already
marked `validated` or already present at the correct generated size.

After a successful source collection run, register the result into the local
material index:

```bash
python viral-social-remix/scripts/collect_source_assets.py --platform rednote --run-dir output/<run>
python viral-social-remix/scripts/collect_source_assets.py --platform instagram --run-dir output/<run>
python viral-social-remix/scripts/collect_source_assets.py --platform brand-site --run-dir output/<run>
```

For official brand-site assets, run
`scripts/enrich_brand_assets.py --run-dir output/<run>` before registering the
run. This creates `brand_asset_catalog.json` with searchable `title`, `tags`,
`use_case`, and `quality` fields, then `collect_source_assets.py` will ingest
those enriched fields.

Keep `data/material-index.jsonl` local and ignored by Git. Commit the collector
script and workflow documentation, not downloaded media or private indexes. The
collector writes stable `record_id` values and skips duplicates when the same
run is registered again.

## Boundaries and recovery

Do not bypass login or anti-scraping restrictions. If a post URL cannot be read
anonymously but the user can open it in a logged-in browser, use the source
capture workflow above. If no readable browser tab, upload, or local folder is
available, ask the user to open the post in a controllable browser or provide a
local source package. Continue past damaged files while recording their errors.
Do not reproduce source watermarks, unauthorized logos, or a real person's
identity. Keep final deliverables in the project workspace.
