# OpenRouter Grok Video Handoff

Use this reference after a `vertical-video` run has nine generated storyboard
frames and a finished video prompt. This is the low-cost Grok test path, kept
separate from the BytePlus Seedance runner.

## Provider Contract

Default provider: OpenRouter async video generation API, configured for Grok
Imagine video.

- API key variables, in priority order: `GROK_OPENROUTER_API_KEY`,
  `VSR_OPENROUTER_VIDEO_API_KEY`, `OPENROUTER_VIDEO_API_KEY`,
  `OPENROUTER_API_KEY`.
- Default endpoint: `https://openrouter.ai/api/v1/videos`.
- Default model: `x-ai/grok-imagine-video`.
- Environment overrides: `VSR_OPENROUTER_VIDEO_ENDPOINT`,
  `VSR_OPENROUTER_VIDEO_MODEL`, `VSR_OPENROUTER_VIDEO_RATIO`,
  `VSR_OPENROUTER_VIDEO_DURATION`, `VSR_OPENROUTER_VIDEO_RESOLUTION`,
  `VSR_OPENROUTER_VIDEO_GENERATE_AUDIO`.
- English vertical cooking default: request body `aspect_ratio: 9:16`,
  `resolution: 720p`, `duration: 5`, and `generate_audio: false`, with
  `1080x1920` storyboard frames.
- No-subtitle policy: no visible subtitles, captions, title cards, lower-thirds,
  ingredient labels, sticker ads, floating graphics, or screen overlay text.
  Company branding may appear only when it is already in the storyboard as a
  real physical prop.

The API is asynchronous: create a video job, poll the job id, then download the
returned video URL or authenticated content endpoint immediately.

## Local Runner

Codex prepares the prompt, storyboard frames, and manifest. The API task should
run from the user's terminal or local Codex environment:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_openrouter_video.py --run output/xxx --allow-data-url --duration 5 --resolution 720p --ratio 9:16 --no-generate-audio
```

Dry-run the payload without sending a task:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_openrouter_video.py --run output/xxx --allow-data-url --duration 1 --resolution 720p --ratio 9:16 --no-generate-audio --dry-run
```

For the cheapest real smoke test, use one second:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_openrouter_video.py --run output/xxx --allow-data-url --duration 1 --resolution 720p --ratio 9:16 --no-generate-audio --output generated/openrouter-grok-1s-test-720p.mp4
```

By default the runner sends only the first storyboard frame as `first_frame`.
This matches the current Grok test path and keeps spend low. If a chosen model
is confirmed to accept extra reference images, add both `--include-all-frames`
and `--include-reference-images`.

If frames are only local files, `--allow-data-url` can be used for testing. For
production reliability, prefer public HTTPS storyboard image URLs via
`--image-url` or manifest `storyboard_url` fields.

## Expected Files

Before running a real OpenRouter video task for English vertical cooking, ensure
these files exist:

- `analysis/manifest.json`
- `analysis/shot-list.md`
- `analysis/seedance-prompt.md` or `analysis/openrouter-video-prompt.md`
- `generated/page-01.png` through `generated/page-09.png` at `1080x1920`
- `overview/contact-sheet.png`

The runner refuses to call the API unless the manifest has exactly nine assets
with ids `01` through `09`, every asset is `validated`, and every generated
storyboard frame exists at the platform dimensions.

The runner writes:

- `raw/openrouter-video-create-request.json` with data URLs redacted.
- `raw/openrouter-video-create-response.json` with video URLs redacted.
- `raw/openrouter-video-status.json` with video URLs redacted.
- `generated/openrouter-video.mp4`, or the path passed with `--output`.
- `qa/openrouter-video.json`.
- `analysis/manifest.json` top-level `openrouter_video_generation` status.

When `generate_audio` is false, the runner strips any returned audio stream with
`ffmpeg` after download and records `postprocess.audio_stripped`. This protects
against providers returning a low-level AAC track despite a no-audio request.

## Request Controls

Override generation controls from the command line when needed:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_openrouter_video.py --run output/xxx --image-url https://example.com/frame.png --ratio 9:16 --duration 5 --resolution 720p --no-generate-audio
```

Use `720p` for cost tests. Treat `1080p` or newer Grok models as a deliberate
quality upgrade, not the default smoke-test setting.

The local runner automatically appends the no-subtitle policy to
`vertical-video` prompts unless the prompt already says "no subtitles".

## Secret Handling

Never write API keys into prompts, manifests, raw responses, committed files, or
Obsidian notes. Use `.env.local` or the local shell environment only. Do not
commit signed media URLs or provider responses that echo secrets.

Recommended local key format:

```dotenv
GROK_OPENROUTER_API_KEY=...
```
