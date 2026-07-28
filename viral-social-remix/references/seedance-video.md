# Seedance Video Handoff

Use this reference after a `vertical-video` or `video` run has a finished
`analysis/seedance-prompt.md`, structured references, and an approved spend
profile.

For the current company cooking-commercial route, first follow
`cooking-video-workflow.md`: three director-designed opening frames and three
separate silent 6s requests using `--storyboard-group`. Each request gets only
its matching opening frame. The examples below document provider controls and
older jobs; they do not override that contract.

## Control Model

The manifest is the source of truth. The workflow is:

`prepare -> preflight -> submit -> download -> metadata QA -> human visual QA -> ChatCut -> export QA`

Do not submit a task directly from an improvised prompt. Prepare Manifest v2,
dry-run the compiled request, and let the runner stop on invalid references,
unsupported generation controls, or prompt/reference mismatches before money is
spent.

## Provider Contract

Default provider: BytePlus ModelArk, model
`dreamina-seedance-2-0-260128`.

- API key priority: `BYTEPLUS_ARK_API_KEY`, `BYTEPLUS_API_KEY`,
  `VSR_SEEDANCE_API_KEY`, `ARK_API_KEY`, `SEEDANCE_API_KEY`.
- Default endpoint:
  `https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks`.
- Supported local controls for Seedance 2.0: duration 4-15 seconds; ratio
  `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`, or `adaptive`; resolution
  `480p`, `720p`, or `1080p`.
- Seedance 2.0 Fast is limited locally to at most `720p`.
- Multimodal limits: at most 9 images, 3 videos, and 3 audio references.
- At least one image or video is required. Audio-only input is rejected.
- The API is asynchronous: create the task, poll the task ID, then download
  provider URLs immediately because they may expire.

Environment overrides:

- `VSR_SEEDANCE_ENDPOINT`
- `VSR_SEEDANCE_MODEL`
- `VSR_SEEDANCE_RATIO`
- `VSR_SEEDANCE_DURATION`
- `VSR_SEEDANCE_RESOLUTION`
- `VSR_SEEDANCE_GENERATE_AUDIO`
- `VSR_SEEDANCE_WATERMARK`

## Manifest v2

Prepare original video runs with structured references:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_pipeline.py prepare-original-video `
  --brief "English vertical cooking video for product X" `
  --task-name product-x-cooking `
  --image-reference C:\media\hero-food.png `
  --image-reference https://cdn.example.com/product-pack.png `
  --video-reference https://cdn.example.com/camera-rhythm.mp4
```

Local references are copied under `references/inputs/`. Local image references
can be sent only with explicit `--allow-data-url` after confirming provider
support. Local video and audio references must be uploaded to trusted storage
and represented by public or provider-accessible URLs.

The compact manifest section is:

```json
{
  "schema_version": 2,
  "video": {
    "mode": "compact-reference",
    "profile": "visual-preview",
    "references": [
      {
        "id": "hero-food",
        "type": "image",
        "order": 1,
        "url": "https://cdn.example.com/hero.png"
      },
      {
        "id": "camera-rhythm",
        "type": "video",
        "order": 1,
        "url": "https://cdn.example.com/rhythm.mp4"
      }
    ],
    "shots": [
      {"id": "shot-01", "soft_timing": "opening-third"},
      {"id": "shot-02", "soft_timing": "middle-third"},
      {"id": "shot-03", "soft_timing": "final-third"}
    ],
    "generation": {
      "ratio": "9:16",
      "duration": 5,
      "resolution": "1080p",
      "generate_audio": false,
      "return_last_frame": true,
      "watermark": false
    },
    "continuity": {
      "last_frame_path": null,
      "available": false
    },
    "brand": {
      "strategy": "post-composited-physical-prop",
      "visible_text": "none"
    },
    "budget": {
      "retry_limit": 1,
      "stop_before_final": true
    }
  },
  "video_workflow": {
    "status": "prepared",
    "visual_qa": "not_started",
    "chatcut": "not_started",
    "export_qa": "not_started",
    "history": []
  }
}
```

Reference IDs must be stable editorial names. `order` is per media type, not
one global sequence.

## Prompt Compilation

Author semantic references in `analysis/seedance-prompt.md`:

```text
Shot 1: open on {{ref:hero-food}} finished-dish texture.
Shot 2: follow the camera rhythm of {{ref:camera-rhythm}} while sauce is added.
```

The runner compiles those tokens after final reference ordering:

```text
Shot 1: open on [Image 1] finished-dish texture.
Shot 2: follow the camera rhythm of [Video 1] while sauce is added.
```

Use `[Image 1]`, `[Video 1]`, and `[Audio 1]` only when deliberately writing
provider-ordered prompts. Never use `@Image1`. The compiler rejects unknown
semantic IDs, references beyond the request count, and `@` syntax.

## Profiles

Profiles make cost and approval intent explicit:

| Profile | Duration | Resolution | Native audio | Last frame |
|---|---:|---:|---|---|
| `smoke` | 5s | 720p | no | no |
| `visual-preview` | 5s | 1080p | no | yes |
| `final-clip` | 6s | 1080p | no | yes |
| `native-audio-final` | 6s | 1080p | yes | yes |
| `legacy-storyboard` | 5s | 1080p | no | no |

Explicit CLI flags override profile values. Start with `visual-preview`. Use
`native-audio-final` only after the picture is approved; otherwise finish audio
in ChatCut. Compact manifests default to one retry and
`stop_before_final: true`; after reviewing a final-profile dry run, pass
`--approve-final-spend` for the intentional production submission.

## Dry Run and Production

Dry-run first:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_seedance_video.py `
  --run output/<run> `
  --profile visual-preview `
  --dry-run
```

The dry run reports the compiled prompt, sanitized payload, reference counts,
warnings, generation controls, and request SHA-256 without submitting.

Production:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_seedance_video.py `
  --run output/<run> `
  --profile visual-preview
```

CLI reference overrides are available as repeatable `--image-ref`,
`--video-ref`, and `--audio-ref`. An explicit CLI list replaces manifest
references of the same media type but preserves the other types.

The runner refuses to create another paid task when the manifest already says
`preflight_validated`, `submitted`, or `succeeded`. Inspect the existing task
or output first. `--force` is only for an intentional new attempt and still
obeys the retry limit.

The runner writes:

- `analysis/seedance-request.lock.json`: sanitized compiled request, profile,
  references, warnings, and request SHA-256.
- `raw/seedance-create-request.json`: redacted provider request.
- `raw/seedance-create-response.json`: task creation response.
- `raw/seedance-status.json`: latest task response.
- `generated/seedance-video.mp4`: downloaded result.
- `generated/seedance-video-last-frame.png`: downloaded continuation frame
  when available.
- `qa/seedance-video.json`: redacted run ledger without expiring media URLs.
- `analysis/manifest.json`: `video_generation`, `video_workflow`, and
  continuity state.

Raw provider responses may contain expiring signed URLs and remain local.

## Multi-Clip Continuity

Profiles that request a last frame register it at
`video.continuity.last_frame_path`. For the next clip:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_seedance_video.py `
  --run output/<next-run> `
  --profile final-clip `
  --continuity-reference output/<previous-run>/generated/seedance-video-last-frame.png `
  --allow-data-url
```

Within the same prepared run, use `--continue-from-last-frame` to read the
manifest continuity entry. The previous frame is prepended as the first image
reference. Always inspect the resulting join; a continuity reference reduces
drift but cannot guarantee a clean edit.

## QA Gate

Generation success is not delivery approval. Prepare deterministic metadata and
visual review assets:

```powershell
.\.venv\python.exe viral-social-remix\scripts\video_qa.py prepare output/<run>
```

This validates duration, dimensions, and expected audio state, then writes:

- `qa/video-visual-review.json`
- `qa/video-review-strip.jpg`
- `qa/video-frames/review-*.jpg`

Review food physics, package/logo fidelity, background/camera continuity,
unsafe actions, duplicate objects, unwanted text, watermarks, extra logos, and
clip joins. Then record the decision:

```powershell
.\.venv\python.exe viral-social-remix\scripts\video_qa.py approve output/<run>
.\.venv\python.exe viral-social-remix\scripts\video_qa.py reject output/<run> --reason "product package changes shape"
```

Metadata failure cannot be approved. Only
`video_workflow.status: visual_qa_passed` may proceed to ChatCut and export.

After ChatCut export, close the second gate:

```powershell
.\.venv\python.exe viral-social-remix\scripts\video_qa.py prepare-export `
  output/<run> `
  --video generated/final-export.mp4 `
  --expect-audio

.\.venv\python.exe viral-social-remix\scripts\video_qa.py approve-export output/<run>
```

Use `reject-export --reason "..."` when the final file has a bad join, unsafe
text placement, an audio tail, clipping, wrong branding, or another delivery
problem. Final delivery requires `video_workflow.status: export_qa_passed`.

## Text and Brand Policy

The raw generated picture is subtitle-free: no captions, title cards,
lower-thirds, labels, stickers, watermarks, floating logos, or ad banners.
Burned-in model text is not editable.

For exact branding, use one declared strategy:

- `storyboard-physical-prop`
- `product-only`
- `physical-prop-rough`
- `post-composited-physical-prop`
- `clean-end-card`
- `no-brand-visible`

For `post-composited-physical-prop`, track the official logo PNG onto a real
scene surface with matching perspective, motion, occlusion, lighting, and
texture. It must not become a floating overlay.

For `first-frame-physical-prop`, keep the exact physical sign already present in
the supplied opening frame. Do not ask Seedance or ChatCut to redraw
or replace it.

## Secret Handling

Never write API keys into prompts, manifests, request locks, QA ledgers, raw
responses, or committed files. Use `.env.local` or the local shell environment.

Recommended local key format:

```dotenv
BYTEPLUS_ARK_API_KEY=...
```
