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
- `analysis/manifest.json` using `scripts/manifest.py`
- `analysis/caption-zh.txt` for Xiaohongshu
- `analysis/caption-en.txt` for Instagram/Facebook

For video, write the caption file required by its target publishing platform.
The caption must be ready to paste into the platform, including a hook, body,
CTA, and relevant hashtags. Keep the Chinese natural for Xiaohongshu and the
English natural for Instagram/Facebook.

When visible packaged products matter, load
`references/product-reference-cache.md` and use cached or official SKU images
before image generation.

## Generate

Load `references/prompt-patterns.md` and `references/image-provider.md`. Resolve
the image provider with `scripts/image_provider.py`. Default to OpenRouter
`openai/gpt-5.4-image-2` at medium quality when `OPENROUTER_API_KEY` is available.
Generate the exact Chinese or English text directly in the image; do not default
to local text overlay. Use each source page or selected source frame as a
structural reference while locking product, packaging, recurring people, palette,
lighting, and typography across the group.

Save every project-bound generated asset into the run directory. Update
`scripts/manifest.py` after prompting and after each generation.

## Validate and resume

Visually review every generated image for product fidelity, brand spelling,
product spelling, numbers, language, CTA, anatomy, perspective, and continuity.
Run `scripts/validate_output.py` for deterministic checks. Retry only failed
assets. Use local text overlay only after repeated targeted GPT Image 2 retries
fail.

Build the carousel overview or exactly nine-frame storyboard with
`scripts/make_contact_sheet.py`. On restart, read the manifest and skip assets
already marked `validated`.

## Boundaries and recovery

Do not bypass login or anti-scraping restrictions. If a post URL cannot be read
anonymously but the user can open it in a logged-in browser, use the source
capture workflow above. If no readable browser tab, upload, or local folder is
available, ask the user to open the post in a controllable browser or provide a
local source package. Continue past damaged files while recording their errors.
Do not reproduce source watermarks, unauthorized logos, or a real person's
identity. Keep final deliverables in the project workspace.
