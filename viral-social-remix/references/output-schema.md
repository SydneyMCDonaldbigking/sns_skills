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
assumptions, provider configuration, and per-asset generation state. Controlled
video jobs use schema version `2`, retaining those fields and adding a
deterministic `video` plan and `video_workflow` state.

Top-level fields:

- `schema_version`: `1` for basic/carousel jobs; `2` for controlled video jobs.
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
`vertical-video` and mode `storyboard-three-clips`. Additional files:

- `analysis/brief.md`: user/product/recipe brief.
- `analysis/shot-list.md`: nine frames grouped `01-03`, `04-06`, `07-09`.
- `analysis/page-prompts/page-01.md` through `page-09.md`: image API prompts.
- `analysis/seedance-prompts/clip-01.md` through `clip-03.md`: one motion
  prompt per 6s group.
- `analysis/caption-en.txt`: platform post caption only, not video subtitles.
- `generated/page-01.png` through `page-09.png`: `1080x1920` storyboard frames.
- `overview/contact-sheet.png`: review-only 3x3 overview.
- `generated/seedance-clip-01.mp4` through `clip-03.mp4`: separate silent clips.
- `analysis/seedance-clip-XX-request.lock.json`, matching `raw/` records, and
  `qa/seedance-clip-XX-video.json`: independent request/QA state per clip.

The manifest records `video.clip_groups`, silent 6s generation controls,
`video.brand.strategy: storyboard-physical-prop`, per-clip
`video_generations`, and `video_workflow.clips`. Seedance receives exactly the
three separate storyboard images for the selected group.

Older or non-cooking `compact-reference` jobs may instead record
product/package/logo/source references in `video.references`. Each entry
contains a stable `id`, `type` (`image`, `video`, or `audio`), type-local
`order`, and exactly one `url` or `path`.

Local video/audio references must be uploaded to trusted storage before
submission. Legacy `reference_paths` and `storyboard_url` asset fields remain
readable for existing runs.

Author semantic prompt tokens such as `{{ref:hero-food}}`. The runner compiles
them to the official final request labels (`[Image 1]`, `[Video 1]`,
`[Audio 1]`) after ordering. `@Image1`, unknown IDs, and labels beyond the
submitted reference count fail preflight.

Compact-reference manifests also record:

- `video.mode` and `video.profile`.
- `video.shots`: three ordered soft beats for the default short-form route.
- `video.generation`: ratio, duration, resolution, `generate_audio`,
  `return_last_frame`, and watermark policy.
- `video.continuity`: returned last-frame path/URL and availability.
- `video.brand.strategy`: the chosen visibility/fidelity approach.
- `video.budget`: retry and final-spend stop controls.
- `video_workflow`: status, visual QA, ChatCut, export QA, and append-only
  history.

After Seedance handoff, store:

- `analysis/seedance-request.lock.json`: sanitized compiled prompt, generation
  controls, ordered references, warnings, and request SHA-256.
- `raw/seedance-create-request.json`: redacted request payload.
- `raw/seedance-create-response.json`: task creation response.
- `raw/seedance-status.json`: latest task status response.
- `generated/seedance-video.mp4`: downloaded generated video.
- `generated/seedance-video-last-frame.png`: optional downloaded continuation
  frame.
- `qa/seedance-video.json`: task id, provider metadata, relative output path,
  reference counts, request hash, generation controls, and usage. Do not copy
  expiring output URLs or full provider responses into this committed-safe
  ledger.
- `qa/video-visual-review.json`: metadata validation and human decision.
- `qa/video-review-strip.jpg`: extracted visual review strip.
- `qa/export-review.json`: final ChatCut/export metadata and human decision.
- `qa/export-review-strip.jpg`: final delivery review strip.

The manifest may include top-level `video_generation` with `status`, `task_id`,
`model`, `endpoint`, `profile`, `prompt_path`, media reference counts,
`request_sha256`, `request_lock`, `generation`, `output`, `last_frame`,
`qa_path`, `usage`, and `last_error`. `video_workflow.status` progresses through
`prepared`, `preflight_validated`, `submitted`, `generated`,
`awaiting_human_review`, and finally `visual_qa_passed` or
`visual_qa_failed`; `metadata_failed` is a hard QA stop. After ChatCut, it
continues through `export_qa_awaiting_human_review` and finishes at
`export_qa_passed` or `export_qa_failed`. Append each transition to
`video_workflow.history`.

The video itself must not contain subtitles or on-screen text. The default
visual-preview profile is no-audio. Voiceover and natural cooking audio are
allowed only in an explicitly selected audio-enabled final profile.

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
