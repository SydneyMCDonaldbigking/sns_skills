---
name: viral-social-remix
description: Use when a user provides a viral social-post link, image, video, or local media folder and wants a branded Xiaohongshu, Instagram, Facebook, or nine-frame video storyboard remix.
---

# Viral Social Remix

Follow the workflow below. Load only the reference files required by the detected platform and media type.

## Intake

Accept a public post URL, local file, or local folder. For a local folder, run
`scripts/scan_media.py`, show the discovered task list, and process each valid
group independently. Inspect every local image before analysis. Product and brand are mandatory. Infer audience, setting, benefits, and theme; label those
assumptions. Ask only for missing mandatory fields or low-confidence platform.

Do not ask again for values already supplied. A user's explicit platform always
overrides automatic detection.

## Route

Infer platform from source domain, page metadata, media dimensions, language,
UI traces, and folder naming. Load `references/platform-profiles.md`, then load
the relevant fields from `references/breakdown-schema.md`.

- Xiaohongshu: preserve source page count, use Chinese, output 2048×1152.
- Instagram/Facebook: preserve source page count, use natural English, output
  1152×1152.
- Video: identify the target publishing platform and language, then produce a
  1920×1080 storyboard.

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

## Generate

Load `references/prompt-patterns.md`. Call GPT Image 2 once per pending asset
using the built-in image generation tool. Generate the exact Chinese or English
text directly in the image; do not default to local text overlay. Use each source
page or selected source frame as a structural reference while locking product,
packaging, recurring people, palette, lighting, and typography across the group.

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

Do not bypass login or anti-scraping restrictions. If a post URL cannot be read,
ask for an upload or readable local folder. Continue past damaged files while
recording their errors. Do not reproduce source watermarks, unauthorized logos,
or a real person's identity. Keep final deliverables in the project workspace.
