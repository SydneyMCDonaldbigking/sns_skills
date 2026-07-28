# Output Schema

Create each run at `output/YYYYMMDD-HHmmss-<task>/`. If that path exists,
append `-02`, then increment until the path is unused. Never overwrite a prior
run.

```text
output/YYYYMMDD-HHmmss-<task>/
├── source/
├── analysis/
│   ├── breakdown.md
│   ├── copy.md
│   ├── caption-zh.txt
│   ├── caption-en.txt
│   ├── prompts.md
│   ├── page-prompts/
│   │   ├── page-01.md
│   │   └── page-02.md
│   └── manifest.json
├── references/keyframes/
├── raw/
│   └── page-XX-response.json
├── generated/
│   └── page-XX.png
├── overview/contact-sheet.png
└── qa/
    ├── validation.json
    └── openrouter-cost.json
```

Only the target-output caption is mandatory: `caption-en.txt` for Xiaohongshu
source posts remixed into English, Instagram/Facebook, and English vertical
videos; `caption-zh.txt` only for explicit Chinese Xiaohongshu target output.
Video uses the target publishing platform's caption language.

Manifest schema version `1` records source provenance, platform confidence,
assumptions, provider configuration, and per-asset generation state.

Top-level fields:

- `schema_version`: currently `1`.
- `source`: `{ "kind": ..., "paths": [...], "url": ... }`. `kind` may be
  `local_file`, `local_folder`, `direct_url`, or `unknown`; direct URL inputs
  record `content_type` and byte count when downloaded.
- `platform`: `xiaohongshu`, `instagram-facebook`, `video`, or `vertical-video`.
- `platform_confidence`: optional numeric confidence.
- `assumptions`: inferred audience, setting, benefit, or theme notes.
- `provider`: redacted provider metadata such as name, model, quality, endpoint,
  and whether an API key was set.
- `assets`: mapping of asset id to state.

Each asset records:

- `status`: one of `pending`, `prompted`, `generated`, `validated`, or `failed`.
- `prompt_path`: prompt file path relative to the run directory when possible.
- `request`: redacted request metadata after the asset is marked `prompted`;
  image data URLs must be stored as `<redacted data URL>`.
- `output`: primary generated image path.
- `outputs`: all generated image paths for that asset.
- `text_review`: text review state, starting as `not_reviewed`.
- `validation_errors`: deterministic or provider failure messages.
- `last_error`: structured failure detail such as `openrouter_http` code/body
  or `openrouter_image` response errors.
- `attempts`: generation attempt count.

On resume, assets already marked `validated` must be skipped by default.
Regeneration requires an explicit force option.

For API-only carousel runs, Codex writes one prompt file per generated page under
`analysis/page-prompts/page-XX.md`. The local runner
`scripts/run_openrouter_carousel.py` reads those files and the manifest, then
writes `raw/page-XX-response.json`, `generated/page-XX.png`, and
`qa/openrouter-cost.json`. Pages that already have a generated PNG at the
platform's exact dimensions are skipped and marked resumable. Put per-page local
reference assets in `assets[asset_id].reference_paths`; the runner also accepts
the legacy `assets[asset_id].request.reference_images` field for existing runs.

For original English vertical cooking video runs, use platform
`vertical-video`. Preferred Seedance 2.0 runs use a compact reference pack and a
three-shot prompt. Additional video-prep files:

- `analysis/brief.md`: user/product/recipe brief.
- `analysis/shot-list.md`: the ordered Seedance shots, usually three soft
  beats for a 5-6s preview.
- `analysis/seedance-prompt.md`: one final motion prompt for Seedance.
- `analysis/caption-en.txt`: platform post caption only, not video subtitles.

When the legacy still-storyboard route is explicitly selected, also include:

- `analysis/page-prompts/page-01.md` through `page-09.md`: GPT Image 2 storyboard prompts.
- `generated/page-01.png` through `page-09.png`: `1080x1920` storyboard frames.
- `overview/contact-sheet.png`: 3x3 storyboard overview.

For the preferred compact-reference route, record product/package/logo/source
references in manifest asset entries, using `reference_paths`,
`storyboard_url`, or another explicit URL/reference field. The Seedance prompt
should refer to the selected references by order (`Image 1`, `Image 2`,
`Video 1`) after they are passed to the provider.

After Seedance handoff, store:

- `raw/seedance-create-request.json`: redacted request payload.
- `raw/seedance-create-response.json`: task creation response.
- `raw/seedance-status.json`: latest task status response.
- `generated/seedance-video.mp4`: downloaded generated video.
- `qa/seedance-video.json`: task id, provider metadata, output path, usage, and final response.

The manifest may include top-level `video_generation` with `status`, `task_id`,
`model`, `endpoint`, `prompt_path`, `image_count`, `output`, `qa_path`, `usage`,
and `last_error`. Store storyboard image URLs on per-asset `storyboard_url` when
the Seedance runner should use URLs from the manifest instead of `--image-url`.
The video itself must not contain subtitles or on-screen text; voiceover and
natural cooking audio are allowed when supported.

After OpenRouter Grok video handoff, store:

- `raw/openrouter-video-create-request.json`: redacted request payload.
- `raw/openrouter-video-create-response.json`: redacted task creation response.
- `raw/openrouter-video-status.json`: latest redacted task status response.
- `generated/openrouter-video.mp4`, or the custom MP4 path passed with
  `--output`.
- `qa/openrouter-video.json`: task id, provider metadata, output path, usage,
  generation controls, and redacted final response.

The manifest may include top-level `openrouter_video_generation` with `status`,
`task_id`, `model`, `endpoint`, `prompt_path`, `image_count`, `output`,
`qa_path`, `usage`, `generation`, `postprocess`, and `last_error`. The Grok
runner is a separate video-only path and must not change carousel image output
sizing.
