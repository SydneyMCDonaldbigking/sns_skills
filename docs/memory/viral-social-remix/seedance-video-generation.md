# Seedance Video Generation Memory

Use this for Seedance 2.0 video handoff, cost estimates, and QA habits.

## Cost Rule

Observed local runs on 2026-07-23:

- Warehouse conveyor test, 10s, 1080p, no audio: `488,025` tokens, about
  `$3.76` at `$7.7 / 1M tokens`.
- Mapo tofu preview, 5s, 1080p, no audio: `245,025` tokens, about `$1.89`.
- Oyakodon action-remake preview, 5s, 1080p, no audio: `245,025` tokens,
  about `$1.89`.
- Oyakodon action-remake split final, 5s + 6s + 6s, 1080p, no audio:
  `832,275` tokens total, about `$6.41`.
- Japanese spicy steak ramen action-remake preview, 5s, 1080p, no audio:
  `245,025` tokens, about `$1.89`.
- Japanese spicy steak ramen action-remake split final, 5s + 6s + 5s, 1080p,
  no audio: `783,675` tokens total, about `$6.03`.

Rule of thumb for 1080p Seedance 2.0:

- About `48.8k` tokens per second.
- 5 seconds is about `$1.9`.
- 10 seconds is about `$3.8`.

If exact billing matters, check the BytePlus ModelArk billing page and the
provider dashboard. Failed tasks may not return usage in the local ledger; do
not assume they were free without checking the dashboard.

## Preview Habit

Start with a 5-second no-audio preview before spending on a 10-second final.

Use no audio for first visual QA because the first mapo tofu attempt with
`generate_audio: true` failed on `OutputAudioSensitiveContentDetected`. Add
voiceover later after the picture is accepted.

For cheaper 720p smoke tests before spending on Seedance, use
[[openrouter-grok-video-generation]].

Good preview command shape:

```powershell
.\.venv\python.exe .\viral-social-remix\scripts\run_seedance_video.py --run output/xxx --allow-data-url --include-all-frames --duration 5 --ratio 9:16 --resolution 1080p --no-generate-audio --no-watermark
```

`--include-all-frames` is for the legacy 9-frame cooking storyboard route. For
new Seedance 2.0 cooking tests, prefer the official compact prompt style in
[[seedance-official-prompting]]: 3 soft shot beats, 3-5 real reference assets,
and one camera movement per shot. For a single first-frame image-to-video test,
omit `--include-all-frames` so only the first image is sent.

## Official Prompting Update

BytePlus official guidance studied on 2026-07-28:

- Use `Shot 1`, `Shot 2`, `Shot 3` to organize complex videos in event order.
- Do not over-constrain exact segment durations; second-level timing can be
  unstable. Use `[0-2s]`, `[2-4s]`, `[4-6s]` only as soft pacing labels.
- Reference assets by prompt order: `Image 1`, `Image 2`, `Video 1`, `Audio 1`.
- Use more real object references for product/package/logo fidelity.
- Specify only one camera movement per shot.
- Explicitly forbid subtitles, watermarks, extra logos, and overlay text; allow
  only the referenced physical brand prop/package when needed.

See [[seedance-official-prompting]] for the full note.

## What Worked

Seedance is much better for food motion than rigid mechanical physics.

The mapo tofu 5-second preview was usable because the storyboard had:

- Minimal scene elements: table/counter, wok, stove, cutting board, knife,
  serving bowl, food, and physical brand sign only when needed.
- Clear food progression: ingredients, tofu prep, hot oil, tofu into wok, stir,
  sauce, texture close-up, plating, final hero.
- Strong still frames from OpenRouter Images API before video generation.
- No subtitles or visible text except the physical English-region sign in the
  permitted frames.

The oyakodon action-remake preview was usable because the storyboard locked the
camera very aggressively:

- Same 35 to 45 degree overhead three-quarter phone-camera angle in every
  prompt.
- Same warm wooden table, compact black burner, shallow black pan, wooden
  handle direction, and upper-left daylight.
- No people, hands, labels, subtitles, logos, packaging text, or dialogue.
- Plain unmarked cups only. Avoid measuring marks because video models may
  enlarge them into readable text.
- Sending all 9 storyboard frames into a 5-second preview produced a coherent
  but compressed full-process video. For final 15-17s cooking videos, split
  into multiple clips so the timing breathes.
- For the 17s-style final, splitting into 5s + 6s + 6s worked better:
  seasoning base, onion/chicken/first egg, then second egg/plating/final hero.
  Segment prompts must not inherit the full 9-shot master list; otherwise every
  clip is tempted to repeat the whole recipe.

The Japanese spicy steak ramen action-remake worked even though the source
video had a person, package branding, and overlay text because the generation
prompts preserved only the cooking rhythm and food sequence:

- Use "no human presence at all" when the user wants no真人/no person. Include no
  people, faces, bodies, hands, fingers, wrists, arms, skin, or reflected people.
- Mention source people/packaging only in breakdown notes, never as positive
  generation subjects.
- A finished ramen hook as frame 01 can match food-reel rhythm, then the video
  returns to prep and cooking.
- If an intermediate storyboard frame already looks like the final dish, redraw
  it before Seedance; video timing gets compressed otherwise.
- For a 16.4s source, a 5s + 6s + 5s final split matched the reference better
  than forcing 17s.
- Segment prompts should use only the intended reference frames, e.g. 01-05,
  05-07, and 07-09 for steak ramen. Do not append the full nine-shot master
  list to every segment.

## What Failed

Seedance struggled with the warehouse conveyor test. It did not reliably obey
the rigid physical requirement that a gray tote follow a real conveyor curve
with the front edge turning first and rear edge following last. It tended to
invent motion paths and background changes even with a strict prompt.

Avoid spending heavily on videos that require exact mechanical physics,
collision constraints, conveyor turns, or strict object tracking unless there
is a specialized workflow or manual post-production plan.

## Prompting Rules

For cooking video prompts:

- Keep the set sparse. Fewer props usually means fewer video artifacts.
- Provide enough real references for product/package/logo fidelity. Product and
  brand references should be physical objects in the scene, not overlays.
- Say explicitly which props are allowed and which are banned.
- Put branding only on real physical props, not overlays or stickers.
- Repeat the no-visible-text policy in the Seedance prompt.
- Prefer controlled, small motions: steam, gentle stirring, sauce pour,
  spooning into a bowl.
- For a 6-second test, use three soft shots rather than nine forced beats.
- Avoid asking for too many distinct actions in 5 seconds unless the visual
  references already make the progression obvious.

## QA Checklist

After Seedance finishes:

- Confirm `generated/*.mp4` exists.
- Run `ffprobe` for duration, resolution, and frame rate.
- Extract a small frame strip at key timestamps.
- Check for visible subtitles, title cards, labels, floating logos, extra brand
  marks, warped hands, broken food, duplicated objects, and busy background
  drift.
- Report actual token usage and estimated cost to the user.

## Next Step: ChatCut Editing

After a Seedance MP4 passes visual QA, continue through
[[chatcut-handoff-workflow]] when the user wants editing, review, BGM, subtitle
labels, stitching, or final export.

For multi-segment cooking videos, keep the segment MP4s as separate editable
ChatCut timeline items on `V1`. Use a stitched MP4 only for quick review or when
the user explicitly asks for one flat clip.

For no-audio food B-roll finishing, ChatCut can add original no-vocal BGM on
`A1` and editable subtitle/ingredient-label Motion Graphics on `V2`. Do this
only after the user asks for audio/subtitles/finishing; the default Seedance
preview remains no-audio and no-subtitle.

## Relevant Runs

- Mapo tofu storyboard and 5s preview:
  `output/20260723-150614-mapo-tofu-api-test`
- Warehouse conveyor failed-quality test:
  `output/20260723-warehouse-conveyor-turn-test`
- Oyakodon action-remake storyboard and 5s preview:
  `output/20260725-oyakodon-fixed-view-remake`
- Oyakodon 3-segment no-audio stitched preview:
  `output/20260725-oyakodon-fixed-view-remake/generated/seedance-oyakodon-stitched-17s-noaudio.mp4`
