# Seedance Video Handoff

Use this reference after a `vertical-video` or `video` run has a finished
`analysis/seedance-prompt.md`, structured references, and an approved spend
profile.

For the current company product/cooking-commercial routes, first follow
`cooking-video-workflow.md`: either one silent 10s request (`single-10s`) or
three separate silent 6s director requests using `--storyboard-group`. In the
three-clip route, generate clip 1's opening frame first; clips 2 and 3 use one
selected opening anchor chosen after the prior accepted clip's returned last
frame and final motion strip are inspected. Use a clean returned last frame
directly; if the last frame is bad, generate a transition opening anchor first.
The examples below document provider controls and older jobs; they do not
override that contract.

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
- Workshop raw API examples also show `duration: -1` for provider auto
  duration and `bitrate_mode: "standard"` / `"high"`. Use those only when the
  local runner/profile exposes the control or after extending the runner; do
  not confuse `bitrate_mode` with the provider's 8-bit / 10-bit output note.
- Workshop capability notes: Seedance 2.0 family supports 24 fps output, 8-bit
  or 10-bit bitrate, and native audio generation is enabled by provider default
  unless explicitly turned off. This workflow normally sends
  `generate_audio: false` and finishes audio in ChatCut.
- Seedance 2.0 can support `4k`; keep local production profiles at `1080p`
  unless the user explicitly requests a 4k final and budget/runtime has been
  approved.
- Seedance 2.0 Fast is limited locally to at most `720p`.
- Seedance 2.0 is the quality/default production model. Seedance 2.0 Fast is
  for lower-cost or faster iteration when quality close to 2.0 is acceptable.
  Do not silently switch to Fast for final production.
- If a workshop page mentions newer preview models or product-briefing
  features, treat them as planning knowledge only until this repo's provider
  adapter and model config explicitly support them.
- Multimodal limits: at most 9 images, 3 videos, and 3 audio references.
- At least one image or video is required. Audio-only input is rejected.
- The API is asynchronous: create the task, poll the task ID, then download
  provider URLs immediately because they may expire.

## Moderation and Rights

Seedance may block inputs or outputs for human-face/deepfake risk, NSFW
content, or IP-rights violations. IP protection applies to both visuals and
audio references.

- Do not use unowned characters, logos, celebrity likenesses, music, voices,
  video clips, or brand assets as generation references.
- For real-human or virtual-character face work, use only an approved route
  such as provider built-in assets (`asset://...`) or a private asset library
  with the required verification/authorization. Do not infer consent from a
  random image.
- Film/drama endpoints with relaxed pre-filtering are special approved
  configurations. Do not make them the default skill route.

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

Provider roles:

- Images may be `reference_image`, `first_frame`, or `last_frame`. Use
  `first_frame` when the first visual state must be obeyed; use `last_frame`
  only for deliberate ending control or handoff tests.
- Videos use `reference_video` and must be provider-accessible URLs.
- Audio uses `reference_audio`. Do not submit text+audio or audio-only requests;
  pair audio with at least one image or video when native audio is explicitly
  selected.

## Workshop Prompt Architecture

Write Seedance prompts as structured film instructions, not as a paragraph that
merely describes a finished video. The workshop's basic formula is:

`subject + action + scene`

For reliable production prompts, expand that into only the fields that matter:

- **Settings**: location, environment, time of day, weather/atmosphere, and the
  intended mood or tone.
- **Subject**: name each recurring subject or object consistently, including
  the matching `[Image N]` reference when used. Keep face/outfit/action
  references separated when character consistency matters.
- **Timed beats**: write `0-2s`, `2-4s`, `4-6s` style instructions with camera
  cuts or transitions. Give instructions for what should happen, not a summary
  of what exists.
- **Shot sequencing**: for complex prompts, use `Shot 1`, `Shot 2`, `Shot 3`
  in event order. Each shot should read as who/what + where + action + how the
  camera shoots it.
- **Action detail**: tie motion to body parts or object mechanics; include
  range, speed, force, and continuity. Prefer slow, gentle, continuous small
  movements unless the brief needs a large dynamic action.
- **Transitions**: specify inertia and bridges between actions, such as object
  wipes, rack focus, steam/lid occlusion, hand match, pour motion, or cut-ins.
- **Scene and lighting**: make the scene experiential. Use location plus
  atmosphere, then lighting source, direction, intensity, shadow behavior,
  contrast, and tone.
- **Camera**: use official lens-control structure: starting composition +
  movement verb + direction/amplitude/speed + ending composition. Specify shot
  size, angle, lens/focus feel, movement, and endpoint composition. Use precise
  terms: wide, medium, close-up, extreme close-up; eye-level, high angle, low
  angle, bird view; dolly-in/out, pan, track/follow, tilt, rise/fall,
  rotate/surround, zoom, rack focus, locked-off, cut, or object wipe. Tie the
  camera move to purpose, such as pushing in to emphasize a nervous expression
  or cutting to reveal product texture. Avoid conflicting camera commands in
  one beat.
- **Visual style**: name the actual style and visual tone. Avoid vague labels
  such as only "Hollywood style" or "cool futuristic"; write a specific style
  such as cold blue-purple cyberpunk tone, vintage film grain, Japanese fresh
  aesthetic, or photorealistic premium grocery commercial. If references have
  mixed styles, first create consistent references; otherwise Seedance may blend
  incompatible looks.
- **Quality and constraints**: request rich detail, sharp focus, detailed skin,
  fabric, food, or product texture as applicable, cinematic color grade, and
  exact negative constraints.

Write prompts as concrete timed film direction. Name framing, shot size, camera
angle, lighting, action, motion bridge, and endpoint. Avoid weak quality phrases
such as only "cinematic, high quality"; replace them with specific standards
such as rich detail, cinematic color grade, sharp focus, detailed product or
food texture, and the exact text that must remain readable.

When exact text, packaging, or a logo matters, provide a high-resolution
reference and spell out the text in the prompt. Expect generated video to drift
on small typography; prefer first-frame control, a real physical prop, or
post-composited tracking for critical brand text.

For object consistency, use clean isolated references when possible. If a
reference object is attached to a person or busy scene, make or request a clean
object-only reference first, then use that as the Seedance reference.

## Prompt Optimizer Checklist

The workshop's `general-sd2-skills.md` attachment is a prompt-optimizer
reference, not a second production workflow. Distill it into this checklist:

- Check the eight core elements before paid generation: precise subject, action
  details, setting/environment, light/shadow tone, camera movement, visual
  style, quality details, and constraints.
- If the user provides only a vague requirement, ask only for missing facts that
  materially affect generation, especially subject identity, scene, reference
  mapping, and camera intent. Do not fabricate those specifics as if they came
  from the user.
- Classify intent before rewriting: new generation, editing an existing video,
  extension/stitching, or text/layout generation. Also decide whether the scene
  is static/fine-control or dynamic/reference-driven, because those need
  different reference and camera discipline.
- If the user pastes multimodal JSON or text containing a `content` array, scan
  non-text entries in order (`image_url`, `video_url`, `audio_url`) and map
  them to local labels `[Image 1]`, `[Image 2]`, `[Video 1]`, `[Audio 1]`. If the
  user's text contains raw `asset-xxx` IDs, replace those IDs with the mapped
  labels before provider submission; never leave a raw asset ID as the subject
  of an action.
- If the user supplies multiple images or videos, map them by request order to
  the local prompt labels `[Image 1]`, `[Image 2]`, `[Video 1]`, etc. In text,
  immediately explain the referent after the label, such as `[Image 1] (product package)`
  or `[Image 2] (left-side reference)`, so the model does not read the number as
  a quantity.
- If a supplied asset is a long image, contact sheet, 9-grid, or collage, ask
  for or create single-image references before Seedance. Do not make Seedance
  infer several unrelated frames from one composite unless it is deliberately a
  composed relationship reference.
- If mapping is ambiguous, ask which image controls the first frame, last frame,
  character/product identity, left/right placement, or scene background.
- Detect camera conflicts. Within one time slice or micro-shot, use only one
  primary camera movement; enforce only one primary camera movement unless a
  deliberate compatible combo is named. Replace
  "dolly in and pan left and zoom" style piles with a chosen movement and a
  clear start/end composition.
- Do not silently modify user intent. When a prompt is missing important facts
  or contains a camera/reference conflict, show the concrete issue and ask for
  confirmation or a choice before inventing identity, placement, direction,
  first/last-frame control, or a different camera move.
- For editing prompts, name the operation and spatial/temporal target: add,
  remove, modify, extend, or stitch; give the exact time range, screen position,
  object/person target, and transition description. For text generation tests,
  name the exact text, timing, position, and appearance.
- For complex multi-person front-facing dynamic scenes, use strong orientation
  constraints such as left/right placement, clothing, and fixed camera control.
  This is mostly a general Seedance guardrail; company cooking-commercial routes
  remain no-face by default.
- When optimizing a user-written prompt, report the concrete defects and the
  principle used to fix them: missing core element, weak asset label, camera
  conflict, ambiguous image mapping, unsupported audio-only input, or missing
  anti-distortion constraints.
- Structure optimizer output as three short sections when the user asks for
  prompt optimization: `Optimized prompt`, `Optimization`, and `Relevant
  principles`. The optimized prompt must include quality/detail and
  anti-distortion constraints.

## Reference Strategy

Use references as anchors, not clutter:

- Keep the count as low as possible. The provider allows up to 9 images, but
  too many anchors can conflict; more than 4 distinct characters or too many
  unrelated image refs may cause omissions or mixed identities.
- For multiple people, a single composed reference that already shows their
  relationship is often more reliable than many independent portraits.
- For one character, use a clean character sheet or front/side references when
  identity consistency matters; long clips can degrade faces even with good
  references.
- For product/object consistency, prefer clean object-only references. Avoid
  making the model extract a product from a hand, outfit, or busy background
  unless there is no cleaner source.
- For video references, match camera rhythm, action timing, or movement style,
  not just subject labels. Video references must be provider-accessible URLs.
- For storyboard-driven clips, use storyboard frames to cue expression, camera
  movement, and prop emphasis. A screenplay plus a small number of consistent
  storyboard/keyframe references can produce crisper multi-shot videos than a
  loose all-in-one paragraph.
- For text on objects, provide a high-resolution reference and write the exact
  text in the prompt. If the text is critical and small, plan first-frame
  control or post repair rather than trusting the model to redraw it mid-clip.

## Video Extension

The workshop demonstrates backward and forward extension from a reference
video. In this repo, keep local prompt syntax as `[Video 1]` rather than the
workshop's UI-style `@Video 1`.

- Use backward extension when the user wants a prequel/opening that leads into
  an existing clip. Preserve the existing clip's start state and explain the
  final frame that should match it.
- Use forward extension when the user wants continuation after an existing
  clip. Preserve the existing clip's final state and explain the new endpoint.
- Do not use extension language for an unrelated scene jump; make a separate
  clip and bridge it editorially.

## Film Pipeline

For narrative, drama, branded mini-film, or complex commercial work, follow the
workshop's high-level production pipeline:

1. Write the film script first: characters or products, locations, dialogue,
   emotion, storyline, and endpoint.
2. Generate assets: consistent character/product/scene references and keyframes.
3. Produce clips: Seedance prompts should combine the screenplay beats with the
   chosen references.

A high-quality AI-native film should satisfy storytelling, world building,
believable subjects or products, natural motion, natural sound when enabled,
and consistent visual style.

## Native Audio Prompting

Seedance Workshop treats natural sound as a quality dimension, alongside
natural motion and consistent visual style. Use native audio only when the user
explicitly asks for model-generated sound, or after the silent picture has been
approved and a native-audio experiment is intentional.

When native audio is selected:

- Use `native-audio-final` or set `generate_audio: true` deliberately. Do not
  rely on the provider default to decide audio state.
- Include at least one image or video reference. Audio-only and text+audio-only
  requests are not supported.
- Use up to 3 `reference_audio` inputs for BGM, rhythm, voice style, or sonic
  texture. Reference audio can guide the soundtrack, but the prompt must still
  describe how it should be used.
- Write a timed sound script inside the video prompt. For each beat, specify
  diegetic action sounds, ambience, music behavior, voice line, voice type,
  language, and sync point when relevant.
- Use an `AUDIO` block for sound-critical clips: separate ambience, SFX,
  music/BGM, dialogue or voiceover, and sync notes. Align every SFX tightly to
  the cut, hand action, page flip, prop movement, pour, shake, or impact it
  belongs to.
- Keep spoken lines short and exact. If dialogue or voiceover matters, state the
  speaker voice and line timing; expect retries for pronunciation, timing, or
  voice drift.
- Text prompt and image references do not fully describe audio. For dialogue,
  singing, voice style, or lip sync, generate or provide an audio reference
  when quality matters, then instruct Seedance to follow or lip sync that
  reference.
- Keep prompt language consistent when possible. For multilingual dialogue, use
  audio references for the language-specific lines and avoid long or fast
  dialogue such as rap.
- Spell symbols and numbers the way they should sound. For example, write
  "R-O-I" or "one hundred and fifty percent" when pronunciation matters instead
  of relying on `ROI` or `150%`.
- Avoid mixing too many sound goals in one short clip. Prefer one music bed plus
  a few synchronized action sounds, or one spoken/voiceover idea with restrained
  ambience. If a prop sound should happen once, say it happens once.
- QA native audio for sync, clipped starts/ends, wrong language, unwanted
  voices, distracting music, and audio tails. If audio is wrong but picture is
  good, finish sound in ChatCut rather than rerolling good visuals.

Example sound grammar:

```text
0-2s: soft kitchen room tone, gentle ceramic cup set-down synced to the hand.
2-4s: crisp ice clink and liquid pour aligned with the close-up; quiet upbeat
music bed stays under the action.
4-6s: short warm female voice line in English: "Fresh, ready, done." Music
ducks slightly under the line, then resolves cleanly before the final frame.
```

## Profiles

Profiles make cost and approval intent explicit:

| Profile | Duration | Resolution | Native audio | Last frame |
|---|---:|---:|---|---|
| `smoke` | 5s | 720p | no | no |
| `visual-preview` | 5s | 1080p | no | yes |
| `final-clip` | 6s | 1080p | no | yes |
| `single-10s-final` | 10s | 1080p | no | no |
| `native-audio-final` | 6s | 1080p | yes | yes |
| `legacy-storyboard` | 5s | 1080p | no | no |

Explicit CLI flags override profile values. Start with `visual-preview`. Use
`single-10s-final` only for a deliberate one-request commercial route. Use
`native-audio-final` only after the picture is approved; otherwise finish audio
in ChatCut. Compact/single-10s manifests default to one retry and
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
`video.continuity.last_frame_path` or, for the director three-clip route,
`video.continuity.clips.clip-XX.last_frame_path`. For a separate next run:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_seedance_video.py `
  --run output/<next-run> `
  --profile final-clip `
  --continuity-reference output/<previous-run>/generated/seedance-video-last-frame.png `
  --allow-data-url
```

Within the same prepared director three-clip run, use
`--continue-from-last-frame` only after the previous clip's registered last
frame has been visually approved as a clean opening anchor. That last frame
replaces the selected opening image for the next Seedance request; do not send
it as an extra second image anchor. If the returned last frame is weak,
malformed, blurry, or awkward for the next action, generate a transition opening
anchor with the image model first, then pass that generated anchor as the sole
Seedance reference. Always inspect the resulting join; a continuity reference
reduces drift but cannot guarantee a clean edit.

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
