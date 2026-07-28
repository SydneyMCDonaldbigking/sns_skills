# Seedance Video Handoff

Use this reference after a `vertical-video` or `video` run has reference assets
and a finished `analysis/seedance-prompt.md`.

## Provider Contract

Default provider: BytePlus ModelArk video generation API, configured for
Seedance 2.0.

- API key variables, in priority order: `BYTEPLUS_ARK_API_KEY`,
  `BYTEPLUS_API_KEY`, `VSR_SEEDANCE_API_KEY`, `ARK_API_KEY`,
  `SEEDANCE_API_KEY`.
- Default endpoint: `https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks`.
- Default model: `dreamina-seedance-2-0-260128`.
- Environment overrides: `VSR_SEEDANCE_ENDPOINT`, `VSR_SEEDANCE_MODEL`,
  `VSR_SEEDANCE_RATIO`, `VSR_SEEDANCE_DURATION`,
  `VSR_SEEDANCE_RESOLUTION`, `VSR_SEEDANCE_GENERATE_AUDIO`,
  `VSR_SEEDANCE_WATERMARK`.
- English vertical cooking default: request body `ratio: 9:16`,
  `resolution: 1080p`, `duration: 5`, `generate_audio: true`, and
  `watermark: false`.
- No-subtitle policy: no visible subtitles, captions, title cards, lower-thirds,
  or on-screen text. English voiceover and natural cooking audio are allowed if
  the selected model supports audio.

The API is asynchronous: create a task, poll the task id, then download
`content.video_url` immediately because provider media URLs can expire.

## Local Runner

Codex prepares the prompt, references, and manifest. The API task should run
from the user's terminal:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_seedance_video.py --run output/xxx --image-url https://example.com/storyboard-frame-01.png
```

Dry-run the payload without sending a task:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_seedance_video.py --run output/xxx --image-url https://example.com/storyboard-frame-01.png --dry-run
```

By default the runner sends only the first image URL, matching first-frame
image-to-video behavior. If the chosen Seedance model/provider supports
multiple visual references, provide all intended reference URLs and add
`--include-all-frames`. For Seedance 2.0, all included images are sent with
role `reference_image`. In the prompt, refer to them by order as `Image 1`,
`Image 2`, etc.; do not refer to raw asset IDs.

If frames are only local files, upload them to trusted private storage and pass
their URLs. Use `--allow-data-url` only after confirming the current provider
accepts data URLs in `image_url.url`.

## Expected Files

Before running Seedance for English vertical cooking, ensure these files exist
for the preferred compact-reference route:

- `analysis/manifest.json`
- `analysis/shot-list.md`
- `analysis/seedance-prompt.md`
- reference assets listed in the manifest or passed by `--image-url`

For the legacy nine-frame storyboard route, also ensure:

- `generated/page-01.png` through `generated/page-09.png` at `1080x1920`
- `overview/contact-sheet.png`

The runner writes:

- `raw/seedance-create-request.json` with data URLs redacted.
- `raw/seedance-create-response.json`.
- `raw/seedance-status.json`.
- `generated/seedance-video.mp4`.
- `qa/seedance-video.json`.
- `analysis/manifest.json` top-level `video_generation` status.

## Request Controls

The runner sends Seedance 2.0 generation controls as top-level JSON fields,
not as prompt suffixes. Override from the command line when needed:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_seedance_video.py --run output/xxx --image-url https://example.com/frame.png --ratio 9:16 --duration 10 --resolution 1080p --generate-audio --no-watermark
```

For an English vertical cooking video, default `ratio: 9:16`, `duration: 5`,
`resolution: 1080p`, `generate_audio: true`, and `watermark: false` is the safe
preview pass. Increase duration only after the storyboard motion works.
The default Seedance 2.0 model does not support `--seed`; the runner stops
locally if `--seed` is passed with a Seedance 2.0 model.

The local runner automatically appends the no-subtitle policy to
`vertical-video` prompts unless the prompt already says "no subtitles".

For 5-6 second cooking previews, prefer three ordered soft shots over nine
forced still beats. Describe one camera movement per shot and use product,
packaging, and physical-logo reference images when product fidelity matters.

## Secret Handling

Never write API keys into prompts, manifests, raw responses, or committed files.
Use `.env.local` or the local shell environment only. Do not commit provider
responses if they echo request headers or signed long-lived URLs.

Recommended local key format:

```dotenv
BYTEPLUS_ARK_API_KEY=...
```
