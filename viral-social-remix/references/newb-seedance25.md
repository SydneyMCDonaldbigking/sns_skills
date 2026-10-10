# NewB Seedance 2.5

**NewB is the default for all video** (since 2026-10-10). It is the company's
Seedance 2.5 API, mostly used for stir-fry and wok cooking. `--provider` is not
used; NewB has its own runner. Prepare runs with
`run_pipeline.py prepare-original-video` (default route `newb-30s`). The user
supplies the reference images, so no image-API first frames are made. Source contract:
`claude_only/NewB视频-API接入文档-会员版.md` (v1, 2026-09-29, local-only).

## What is different from Seedance 2.0

| | BytePlus / kuaipao Seedance 2.0 | NewB Seedance 2.5 |
|---|---|---|
| Runner | `scripts/run_seedance_video.py` | `scripts/run_newb_video.py` |
| Duration / resolution | chosen per request (`6s`, `10s`, `1080p`) | fixed `30s`, `720p` (720x1280 at 9:16) |
| Ratio | any provider ratio | `9:16`, `16:9`, `1:1` only |
| References | URLs / data URLs, roles | up to 9 local JPG/PNG/WebP files, each <= 15 MB, uploaded as multipart |
| Reference naming | `[Image 1]` | `@图1`, `@图2` in upload order |
| First frame | explicit `first_frame` role | a lone reference image is usually treated as the first frame; multiple images are looser references |
| Last frame | `return_last_frame: true` | not returned; the runner extracts it locally with ffmpeg |
| Audio | `generate_audio: true` on final profiles, ambient only | native audio always generated; kept by default (house audio is ambient only), `--strip-audio` removes it |
| Timing in prompt | timed beats work | do not write timelines; the runner rejects timestamps |
| Billing | per-request API spend | membership quota shared with the NewB web app; failed jobs are refunded automatically |
| Speed | minutes | usually 7-20 min, longer at peak |

## Key and quota

- Key: `NEWB_API_KEY=wfv_...` in the ignored `.env.local`. Never put it in a
  URL, prompt, doc, or log.
- Check quota before a batch: `python scripts/run_newb_video.py --quota`.
  `quota_used` counts web and API together; `active` is the current job count.
- Max 5 jobs in flight per key; max 60 requests/min across all endpoints.
- Never resubmit because a job is slow. There is no idempotency key and no
  cancel. If a submit times out, the runner compares `active` before and after
  and tells you whether a job was created. Continue an existing job with
  `--resume TASK_ID` or `--resume auto`, which reads the manifest.
- Signed `video_url` links last 6 hours and are not stored. Files are deleted
  from NewB after 7 days, so the runner downloads the result immediately.

## Route mapping for company commercials

A 30s request is long enough for a whole commercial. Default to one request per
commercial, then trim to a natural length in the Opue finish
(`opue-finish.md`).

- **Single-30s (default)**: one request covers the full action chain, e.g. for
  stir-fry: ingredients -> hot oil and aromatics -> main ingredient into the
  wok -> toss and sauce gloss -> plate -> chopstick lift / final hero.
  - **References come from the user.** `prepare-original-video
    --image-reference` copies them into the run in order, and
    `run_newb_video.py` uploads them in that order when `--image` is not
    given.
  - Put the opening state first. With one image, NewB treats it as the first
    frame. With several, say in the prompt what each `@图N` is (ingredients,
    a key step, the finished dish) and what to keep from it.
  - Do not generate first frames with the image API.
- **Chained takes**: only when one 30s take cannot carry the story. The local
  `generated/<label>-last-frame.png` is the handoff candidate. It is 720p, so
  prefer a generated `1080x1920` transition anchor when the frame is soft. Each
  take costs one 30s quota slot.
- **Rerolls**: use a new `--label take-02`. The runner refuses to overwrite an
  existing output without `--overwrite`.
- **Output size**: NewB delivers 720p. The company spec is `1080x1920`, so the
  upscale or acceptance of 720p is decided at the Opue render, which outputs
  its own canvas size. Keep generation
  references at exact `1080x1920` regardless.

## Prompt rules

NewB's own guidance overrides the timed-beat templates in
`cooking-video-workflow.md` for this provider:

1. **Keep it simple**: subject, action, camera, and light. No long setting
   blocks. The 6000-character limit is not a target.
2. **No timelines**: no `0-2s`, `1-5 秒`, `0:10`, or `第3秒`. Express order with
   shot sequence words instead, for example `先… 接着… 然后… 最后…` or
   `Shot 1 / Shot 2 / Shot 3` without times. The runner blocks timestamps
   unless `--allow-timeline` is passed.
3. **Avoid violent, gory, or horror words**: they are filtered and the job
   fails, though quota is refunded. Cooking wording to avoid: blood, `血水`,
   `砍`, `剁碎尸`-style phrasing. Prefer `焯水去浮沫`, `切块`, `改刀`.
4. **No clear real faces in references**: portrait protection may reject the
   job. This matches the no-face policy anyway.
5. **Refer to images by `@图N`** in the exact `--image` order.
6. **Still state the house constraints**: no face, no subtitles, no captions,
   no overlays, no watermarks, no logos or signs. Physical product packaging is
   allowed. Opue draws all branding and text in post.
7. **End with the ambient soundscape line**:
   `soundscape: <热油滋滋声、锅铲碰锅、汤咕嘟>. No dialogue, no music.` The
   runner warns when a prompt does not rule out music.

Prompt skeleton (Chinese or English both work; keep the brand text exact):

```text
@图1 是开场画面：[真实产品 + 场景]。
写实高级感超市美食广告，竖屏，暖色[光源与方向]，同一个厨房、同一套厨具、同一种色调，无人脸只出现手。
先 [开场动作，景别 + 机位 + 运镜]。
接着 [手/工具动作]，切到 [特写：纹理/蒸汽/酱汁]。
然后 [加热/转化动作，火焰/锅盖/蒸汽作为转场]。
最后 [装盘成品主镜头，缓慢拉远，只露出已出现过的厨房]。
产品外形和包装全程保持一致。不要字幕、文字叠加、水印、logo、招牌。
soundscape: [这一段动作的环境声]. No dialogue, no music.
```

## Commands

```bash
python scripts/run_newb_video.py --quota
python scripts/run_newb_video.py --run output/<run> --image generated/page-01.png --dry-run
python scripts/run_newb_video.py --run output/<run> --image generated/page-01.png
python scripts/run_newb_video.py --run output/<run> --resume auto
python scripts/run_newb_video.py --run output/<run> --label take-02 --image generated/page-01.png
```

Defaults: prompt from `analysis/newb-prompt.md` (lines starting with `#` are
director notes and are not sent), ratio from the manifest platform, and poll
interval 15s.

Outputs:

- `generated/<label>.mp4`: the main output, with the ambient audio kept.
- `generated/<label>.audio.mp4`: the original, written only with
  `--strip-audio`.
- `generated/<label>-last-frame.png`: the local handoff frame.
- `qa/<label>.json`: the ledger, with the signed URL redacted.
- The manifest entry `newb_video_generation.<label>`, which includes the
  task id, so the job can be resumed.
