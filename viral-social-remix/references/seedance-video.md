# Seedance Video Handoff

Use this reference after a `vertical-video` or `video` run has nine generated
storyboard frames and a finished `analysis/seedance-prompt.md`.

## Provider Contract

Default provider: Volcengine Ark video generation API.

- API key variables, in priority order: `VSR_SEEDANCE_API_KEY`, `ARK_API_KEY`, `SEEDANCE_API_KEY`.
- Default endpoint: `https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks`.
- Default model: `doubao-seedance-1-0-pro-250528`.
- Environment overrides: `VSR_SEEDANCE_ENDPOINT`, `VSR_SEEDANCE_MODEL`, `VSR_SEEDANCE_RATIO`, `VSR_SEEDANCE_DURATION`.
- English vertical cooking default: `--ratio 9:16`, with `1080x1920` storyboard frames.
- No-subtitle policy: no visible subtitles, captions, title cards, lower-thirds,
  or on-screen text. English voiceover and natural cooking audio are allowed if
  the selected model supports audio.

The API is asynchronous: create a task, poll the task id, then download
`content.video_url` immediately because provider media URLs can expire.

## Local Runner

Codex prepares the prompt, storyboard frames, and manifest. The API task should
run from the user's terminal:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_seedance_video.py --run output/xxx --image-url https://example.com/storyboard-frame-01.png
```

Dry-run the payload without sending a task:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_seedance_video.py --run output/xxx --image-url https://example.com/storyboard-frame-01.png --dry-run
```

By default the runner sends only the first storyboard image URL, matching
first-frame image-to-video behavior. If the chosen Seedance model/provider
supports multiple visual references, provide every storyboard URL and add
`--include-all-frames`.

If frames are only local files, upload them to trusted private storage and pass
their URLs. Use `--allow-data-url` only after confirming the current provider
accepts data URLs in `image_url.url`.

## Expected Files

Before running Seedance for English vertical cooking, ensure these files exist:

- `analysis/manifest.json`
- `analysis/shot-list.md`
- `analysis/seedance-prompt.md`
- `generated/page-01.png` through `generated/page-09.png` at `1080x1920`
- `overview/contact-sheet.png`

The runner writes:

- `raw/seedance-create-request.json` with data URLs redacted.
- `raw/seedance-create-response.json`.
- `raw/seedance-status.json`.
- `generated/seedance-video.mp4`.
- `qa/seedance-video.json`.
- `analysis/manifest.json` top-level `video_generation` status.

## Prompt Controls

The runner appends `--ratio` and `--dur` prompt controls when the prompt does not
already contain them. Override from the command line when needed:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_seedance_video.py --run output/xxx --image-url https://example.com/frame.png --ratio 9:16 --duration 10
```

For an English vertical cooking video, default `--ratio 9:16 --dur 5` is the safe preview
pass. Increase duration only after the storyboard motion works.

The local runner automatically appends the no-subtitle policy to
`vertical-video` prompts unless the prompt already says "no subtitles".

## Secret Handling

Never write API keys into prompts, manifests, raw responses, or committed files.
Use `.env.local` or the local shell environment only. Do not commit provider
responses if they echo request headers or signed long-lived URLs.
