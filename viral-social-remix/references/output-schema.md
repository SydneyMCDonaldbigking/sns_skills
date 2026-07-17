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
│   └── manifest.json
├── references/keyframes/
├── generated/
├── overview/contact-sheet.png
└── qa/validation.json
```

Only the platform-relevant caption is mandatory: `caption-zh.txt` for
Xiaohongshu and `caption-en.txt` for Instagram/Facebook. Video uses the target
publishing platform's caption language.

Manifest schema version `1` records source provenance, platform confidence,
assumptions, provider configuration, and per-asset generation state.

Top-level fields:

- `schema_version`: currently `1`.
- `source`: `{ "kind": ..., "paths": [...], "url": ... }`.
- `platform`: `xiaohongshu`, `instagram-facebook`, or `video`.
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
