# OpenRouter Grok Video Generation Memory

Use this for low-cost OpenRouter Grok video smoke tests after a nine-frame
`vertical-video` storyboard has already been generated and validated.

## Config

- Use `GROK_OPENROUTER_API_KEY` in `.env.local` for the separate Grok key.
- Fallback keys are `VSR_OPENROUTER_VIDEO_API_KEY`,
  `OPENROUTER_VIDEO_API_KEY`, then `OPENROUTER_API_KEY`.
- Default runner: `viral-social-remix/scripts/run_openrouter_video.py`.
- Default model: `x-ai/grok-imagine-video`.
- Default test controls: `9:16`, `720p`, `duration: 5`, `generate_audio:
  false`.
- This is a video-only path. Do not change Xiaohongshu, Instagram/Facebook, or
  GPT Image 2 carousel sizing.

## Smoke Test Rule

Run a dry-run first, then a one-second live test:

```powershell
.\.venv\python.exe .\viral-social-remix\scripts\run_openrouter_video.py --run output/xxx --allow-data-url --duration 1 --resolution 720p --ratio 9:16 --no-generate-audio --dry-run
.\.venv\python.exe .\viral-social-remix\scripts\run_openrouter_video.py --run output/xxx --allow-data-url --duration 1 --resolution 720p --ratio 9:16 --no-generate-audio --output generated/openrouter-grok-1s-test-720p.mp4
```

Observed on 2026-07-25: a one-second 720p vertical Grok test completed at
`720x1280`, about `1.04s`, `24fps`, with provider usage cost `$0.072`.
OpenRouter returned an AAC audio stream even with `generate_audio: false`, so
the runner now strips audio after download when no audio was requested.

## Prompting

- Grok testing uses the first storyboard frame as the video `first_frame`.
- Do not rely on nine images as hard visual constraints unless the selected
  model is confirmed to support extra references.
- On the 2026-07-25 spicy soft tofu soup test, sending frame 01 as
  `first_frame` plus the other eight storyboard frames as `input_references`
  failed during job creation with HTTP 500. The first-frame-only fallback
  succeeded.
- For longer cooking remakes, split into short segments and make each segment's
  first frame match that segment's starting action.
- Use `--first-frame-asset-id` on `run_openrouter_video.py` to choose the
  local storyboard frame for each segment. This avoids copying/swapping files
  when making Segment A/B/C from frames such as 01, 04, and 07.
- For the spicy soft tofu soup test, three 5s first-frame-only segments using
  frames 01, 04, and 07 worked better than one compressed 5s full-recipe clip.
  The three video segments cost `$1.056` total.
- If a Grok prep segment fakes the action badly, do not keep it just because it
  was paid for. Replace the weak prep portion with storyboard stills plus subtle
  Ken Burns motion, then stitch that to the usable cooking segments. On the
  2026-07-25 soup run, Segment A's cutting action was replaced this way before
  ChatCut import.
- If Grok adds edge watermarking or border marks, create a review/export copy by
  zooming and cropping locally, then upscale/crop to the target vertical canvas.
  The soup test used a light zoom crop to `1080x1920` before stitching.
- Keep no-subtitle rules in the prompt: no title cards, captions,
  lower-thirds, ingredient labels, sticker ads, floating graphics, or screen
  overlay text.
- Company branding may appear only if it is a real physical sign, logo prop, or
  packaging already present in the storyboard. It must not become an overlay.
- Grok can use product and brand images as `input_references`, but it cannot be
  trusted to reproduce the exact `ASIAN GROCER ONLINE powered by UMALL` lockup.
  For final delivery, do not ask Grok to render the company logo text. Use the
  real product package in generation, then place the official logo PNG in
  ChatCut/post if exact brand identity is required.

## Local Foley

When ChatCut finishing asks for cooking sound but video generation is no-audio,
it is acceptable to create low-volume local Foley/SFX and light BGM before or
inside ChatCut:

- Prep: short cutting-board taps and knife clicks.
- Cooking base: gentle sizzle and wet spoon stirring.
- Soup finish: broth pour, small ingredient drops, bubbling, and spoon lift.
- BGM: local synthetic music can sound cheap. For reviewable cooking shorts,
  prefer one tasteful ChatCut AI or stock BGM pass, then trim it to the final
  video duration on a separate ChatCut audio track. Keep it adjustable and
  around background level so Foley remains audible.
- Text: when the generated video has no voice, do not wait for ASR captions.
  Add concise English cooking-step labels as a Motion Graphic overlay timed to
  the visual beats. Default subtitles/step labels should be white, horizontally
  centered, and placed in the middle of the video frame unless the user asks for
  another layout. Use shadow/stroke for contrast instead of colored boxes.

Keep Foley subtle, original, and generated for our video. Do not copy source
audio from the reference reel.

## QA Checklist

After Grok finishes:

- Confirm `qa/openrouter-video.json` has `status: succeeded`.
- Confirm the output MP4 exists at the configured path.
- Run `ffprobe` for duration, resolution, and frame rate.
- Confirm there is no audio stream when the request used `--no-generate-audio`.
- Review for cooking continuity, warped ingredients, extra hands/people,
  subtitles, overlay text, and unexpected logo or packaging text.
- Treat misspelled or visually altered generated logo signs as a fail. Fix by
  removing logo generation from the video prompt and adding the official logo
  asset in post.
- Report provider `usage.cost` when present.

## Relevant Runs

- Japanese spicy steak ramen 1s Grok smoke test:
  `output/20260725-134408-japaneseramen-action-remake/generated/openrouter-grok-1s-test-720p.mp4`
- Spicy soft tofu soup 5s Grok test:
  `output/20260725-153706-japansoup-grok-remake/generated/openrouter-grok-5s-test-720p.mp4`
- Spicy soft tofu soup 15s three-segment review with local Foley:
  `output/20260725-153706-japansoup-grok-remake/generated/grok-japansoup-clean-stitched-15s-1080x1920-sfx.mp4`
- Spicy soft tofu soup C-version ChatCut import, with storyboard Ken Burns prep
  montage replacing the bad fake-cutting Segment A:
  `output/20260725-153706-japansoup-grok-remake/generated/grok-japansoup-c-version-stitched-15s-1080x1920-sfx.mp4`
- Honey butter chicken 15s three-segment Grok draft with white centered label
  review copy:
  `output/20260725-171158-honeybutter-chicken-grok-remake/generated/grok-honeybutter-chicken-stitched-15s-1080x1920-white-center-labels-noaudio.mp4`
