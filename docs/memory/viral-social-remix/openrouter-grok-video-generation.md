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
- For longer cooking remakes, split into short segments and make each segment's
  first frame match that segment's starting action.
- Keep no-subtitle rules in the prompt: no title cards, captions,
  lower-thirds, ingredient labels, sticker ads, floating graphics, or screen
  overlay text.
- Company branding may appear only if it is a real physical sign, logo prop, or
  packaging already present in the storyboard. It must not become an overlay.

## QA Checklist

After Grok finishes:

- Confirm `qa/openrouter-video.json` has `status: succeeded`.
- Confirm the output MP4 exists at the configured path.
- Run `ffprobe` for duration, resolution, and frame rate.
- Confirm there is no audio stream when the request used `--no-generate-audio`.
- Review for cooking continuity, warped ingredients, extra hands/people,
  subtitles, overlay text, and unexpected logo or packaging text.
- Report provider `usage.cost` when present.

## Relevant Runs

- Japanese spicy steak ramen 1s Grok smoke test:
  `output/20260725-134408-japaneseramen-action-remake/generated/openrouter-grok-1s-test-720p.mp4`
