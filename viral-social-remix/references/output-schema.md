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
assumptions, per-asset prompt and output path, text-review state, validation
errors, retry count, and status. Status is one of `pending`, `prompted`,
`generated`, `validated`, or `failed`.
