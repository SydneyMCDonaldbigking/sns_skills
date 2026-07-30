# Cooking Video Workflow

This is the single authority for original no-face cooking commercials. Do not
load old run notes unless something fails.

## Route selection

Choose one commercial route before paid generation:

- **Single-10s commercial**: one silent `10s`, `9:16`, `1080p` Seedance
  request. Use for drinks, snacks, pantry, office rituals, and simple
  one-setting product-use stories. Pass the product/page image directly as the
  visual bible and opening product reference. Write 4-6 timed micro-shots in one
  prompt. Product/logo/package readability is required only in the first shot.
  Do not force logo or package continuity later. ChatCut is optional for
  trim/reframe/BGM/captions/voiceover handoff.
- **Three-clip 6s director route**: three silent `6s`, `9:16`, `1080p`
  Seedance requests. Use for actual cooking, large scene changes, stove/heat,
  steamer/fire, transformation beats, or when reroll control matters.

Default to three-clip for cooked foods. Prefer single-10s for a simple,
coherent one-setting product-use ritual.

Three-clip chain:

`three script beats -> clip 1 designed first frame -> sequential silent 6s Seedance commercial micro-shot clips with handoff_review.py decisions and next-prompt drafts -> edit_plan.py + caption_cues.py -> ChatCut finish -> qa_decision_sheet.py`

Opening references are generation inputs, not editing assets. They may be a
director-designed first frame, an accepted prior clip's returned last frame, or
a generated transition opening anchor/bridge frame.

Size preflight is mandatory. Seedance requires the local opening reference PNG
to be exactly `1080x1920`. OpenRouter image requests may reject `1080x1920`
because provider dimensions must be divisible by 16. Prefer
`scripts/run_openrouter_carousel.py --run output/... --api-only --asset-id 01`
for clip 1 and `--asset-id 02` / `03` only when a handoff decision requires a
transition anchor; the runner uses a provider-safe request size and locally
reframes the delivered PNG to `1080x1920`. If manual `openrouter_image.py` is
used as a fallback, generate a provider-safe portrait such as `1088x1920`, then
immediately run `scripts/reframe_image.py --size story` and update the manifest
to the reframed `generated/page-XX.png`. Never submit or mark `1088x1920`,
`1024x1536`, or any non-`1080x1920` opening reference as Seedance-ready.

Default to RPA helpers before manual judgement:

- Run `scripts/next_step.py` after each major stage to write
  `analysis/next-step.json` and the next command.
- Run `scripts/handoff_review.py` after each accepted clip except the final
  clip. It extracts the final motion strip, writes the handoff report, and
  creates the next prompt draft.
- Run `scripts/edit_plan.py` after clips are accepted and trims are known.
- Run `scripts/qa_decision_sheet.py` before handoff or export review.

## Approved patterns to reuse

Use these as taste anchors when a new product resembles them. Do not copy the
product; copy the route choice, action chain, and prompt structure.

- **Leek gyoza / dumpling cooking pattern**: use the three-clip 6s route for
  frozen dumplings, gyoza, buns, or any product whose appeal depends on visible
  cooking transformation. The approved chain is `package identity -> pan action
  -> water/lid/steam -> reveal -> crisp underside -> plated hero`. Keep the
  product pack/sign readable at the opening, then let stove, lid, steam, crisp
  texture, chopsticks, sauce, and plating carry the rest. Continue clip 2 from
  clip 1's clean last-frame state; continue clip 3 from the condensation/lid
  state. Write prompts as three physical shots per clip, not as a recipe
  summary.
- **Longan five-red tea / office beverage pattern**: use the single-10s route
  for tea, drinks, and desk-side wellness products where one coherent setting
  can tell the whole story. Use product/package art as `[Image 1]` and beverage
  texture/pour imagery as `[Image 2]` when available. The approved chain is
  `office product hero -> sachet/serving action -> hot water pour -> amber bloom
  macro -> hand pause beside laptop -> final desk hero`. Do not default these
  products to breakfast; choose the usage occasion that creates a buying reason.
- **Pork belly vermicelli casserole / braised noodle pot pattern**: use the
  three-clip 6s route for pork belly strips, braised meat casseroles, sweet
  potato vermicelli dishes, and similar products where the sale depends on raw
  meat becoming a glossy hot dish. The approved chain is `package identity and
  prep board -> blanch or first heat action -> aromatics and soy-rich braise ->
  soaked vermicelli enters near the end -> glossy pork and noodles lift -> hot
  casserole hero`. Build clip 1's opening frame from the real product image,
  cover/product reference, and English physical logo sign; reject and regenerate
  the opening frame if the product or sign is cropped. For clips 2 and 3,
  inspect the prior returned last frame and last motion strip, then continue
  from that frame only when the pot, hands, lighting, and food state are clean.
  Do not force the logo sign after the opening. Keep the recipe logic physical:
  soaked vermicelli should enter late, steam and sauce should bridge the cuts,
  and the final payoff should be chopsticks lifting translucent sauced noodles
  with tender pork belly above the simmering pot.

Reusable lesson: user approval came from route fit and physical commercial
logic, not from generic "cinematic" styling. Good outputs had visible cause and
effect, controlled hand/tool/liquid/steam motion, restrained logo use, macro
texture payoff, and a final hero that felt like a real ad endpoint.

## Workshop-distilled Seedance rules

Apply these rules to both commercial routes:

- Treat Seedance as a short-film generator, not a prompt-to-slideshow tool.
  Start from a mini script: product, location, action, emotion/payoff,
  continuity objects, and endpoint.
- Use structured instructions, not a descriptive paragraph. The workshop basic
  formula is `subject + action + scene`; production prompts should expand that
  into settings, timed beats, subject/object identity, action detail, camera,
  lighting/tone, quality, and constraints.
- Use official shot sequencing for complex clips: write `Shot 1`, `Shot 2`,
  `Shot 3` in event order, and describe each shot as who/what + where + action
  + how the camera shoots it. Time ranges such as `0-2s` are useful, but the
  shot order and camera intent must be clear even if timing shifts slightly.
- Preserve a consistent visual style across the request: photorealistic food
  commercial, coherent lighting, stable hands/clothing/cookware, and one color
  grade.
- Prompt natural motion explicitly: hand action, steam, pour, shake, rack focus,
  push-in, cut-in, object wipe, or another motivated movement. Avoid vague
  "beautiful motion" language.
- Make action physical. Tie actions to hands, utensils, liquid, flame, steam,
  lid, packaging, cookware, or product texture; specify speed, force, range, and
  continuity. Prefer slow, gentle, continuous small movements unless the product
  brief truly needs a large dynamic action.
- Express emotion through visible behavior: shoulders relaxing, a hand pausing
  before lifting the cup, steam revealing the finished dish, or a tidy final
  table moment. Do not write invisible feelings such as "the viewer feels
  satisfied" as the action instruction.
- Define scene and light concretely: location plus environment, time of day,
  atmosphere, tone, lighting source, direction, intensity, shadow behavior, and
  contrast. Keep the same light logic across the sequence.
- Use the official lens-control formula for every camera move:
  starting-frame composition + camera movement + direction/amplitude/speed +
  ending-frame composition. Every beat must name shot size, camera angle,
  lens/focus feel, start frame, movement, and end frame.
- Use precise camera vocabulary. Shot sizes: wide, medium, medium close-up,
  close-up, extreme close-up. Angles: eye-level, high angle, low angle, bird
  view, overhead/tabletop. Lens/focus: wide lens for environment, 45-50mm
  natural product view, 85mm compression for premium close-ups, shallow depth of
  field, deep focus, rack focus foreground-to-product. Movements: locked-off,
  dolly-in/out, push-in/pull-back, pan, tilt, track/follow, rise/fall,
  rotate/surround, zoom, object wipe, match-action cut.
- Keep camera movement simple and purposeful. Prefer one camera move per
  micro-shot; combine only compatible moves deliberately, such as slow dolly-in
  plus slight tilt, or a Hitchcock-style dolly/zoom when specifically needed.
  Every move must serve texture, convenience, heat, transformation, or final
  hero. Do not stack unrelated moves or write vague phrases such as "cinematic
  camera movement".
- Lock the visual style. For this skill the default is photorealistic premium
  grocery food commercial. If product, scene, or reference images have mixed
  styles, create a consistent image reference before Seedance instead of asking
  the model to reconcile them.
- Keep technical quality concrete: rich detail, sharp focus, readable product
  shape, detailed food texture, cinematic color grade. Do not rely only on
  "cinematic" or "high quality".
- Use references deliberately. Seedance supports up to 9 images, 3 videos, and
  3 audio references, but extra anchors can create conflict. Prefer the minimum
  set that carries product identity, first frame, camera rhythm, or continuity.
- Do not overload character/object references. Too many independent references
  can cause missing people, mixed objects, or changed products. For multiple
  products or props, prefer one clean composed reference when their relationship
  matters; for one product, prefer a clean object-only or package reference.
- When selecting references from a local library, search like an AI-search
  workflow: combine product names, visual scene words, action verbs, and
  modality filters such as image/video. For video references, prefer clips whose
  natural-language description matches camera rhythm or action beats, not just
  subject labels.
- Use `first_frame` / opening reference for exact starting state. Use returned
  `last_frame` only when it creates a cleaner handoff than a designed frame.
- For final-clip extensions, extra ending shots, or pull-back hero shots from a
  returned `last_frame`, treat scene/background continuity as a hard constraint.
  Preserve the same kitchen/stove/table, cookware placement, visible background
  props, lighting direction, color grade, and camera height. If the pull-back
  reveals more space, extrapolate only from the already established set; do not
  invent a new window, shelf wall, counter layout, burner type, or room style.
- If packaging or brand text must be readable, provide a high-resolution
  reference and spell the exact text in the prompt. Still expect small generated
  text to drift; critical logo text should be in the opening physical prop or
  repaired/tracked in post, not trusted to mid-clip generation.
- If a reference object is embedded in a busy image, first create or request a
  clean object-only reference. This is especially useful for clothing, bags,
  packaging, utensils, and hero products that Seedance might deform.
- Use storyboard/keyframe references to cue expressionless hand action, camera
  movement, product/prop emphasis, and endpoint composition. A screenplay beat
  plus a small number of consistent keyframes is more reliable than one loose
  descriptive paragraph.
- Keep native audio off for this workflow. The workshop notes that provider
  audio can be enabled, but food commercials here finish BGM, voiceover, and any
  captions in ChatCut unless the user explicitly selects native audio.
- If the user explicitly requests Seedance-generated sound, first lock a silent
  visual direction, then use `references/seedance-video.md#native-audio-prompting`.
  Write audio as timed beats: room tone, action sounds, music bed, voice line,
  language, and sync point. Align SFX tightly to cuts and actions, such as cup
  set-down, ice clink, pour, shake, lid lift, flame ignition, page flip, or prop
  movement. Use one restrained music bed plus sparse diegetic sounds; reject or
  move sound to ChatCut when native audio damages an otherwise good picture.
  For spoken lines, spell symbols/numbers phonetically and avoid long or fast
  multilingual dialogue unless an audio reference is provided.

## Single-10s commercial

Use `scripts/run_pipeline.py prepare-original-video --commercial-route single-10s`
with at least one product/page `--image-reference`. The generated
`analysis/seedance-prompt.md` is the production prompt; rewrite its timed beats
for the product and setting before submission.

Use this shot grammar:

- `0-1.2s`: product/package hero in the real setting. The product/logo/package
  must be readable here.
- `1.2-2.4s`: hand action that proves convenience or use.
- `2.4-4.2s`: practical preparation, pour, brew, mix, plate, open, or serve.
- `4.2-6.2s`: macro premium texture: steam, liquid bloom, gloss, ingredient
  detail, crunch, sauce, or product surface.
- `6.2-8.0s`: no-face lifestyle payoff in the same setting.
- `8.0-10.0s`: final hero. The pack may return only if natural.

Seedance prompt rules:

- Refer to `[Image 1]` as the opening product/page reference and product bible.
- Keep one coherent environment and color grade.
- Use cuts, macro inserts, push-ins, rack focus, object wipes, pour/steam/action
  bridges, and reframing. Do not make a single continuous camera drift.
- Name the setting, camera, lighting, action mechanics, endpoint, and negative
  constraints in the prompt. Replace abstract promises with visible proof:
  readable opening package, controlled hand movement, steam/liquid/texture
  detail, and a clear final product state.
- No face, subtitles, overlays, watermarks, extra logos, or forced package/logo
  continuity after the opening shot.

Submit with `scripts/run_seedance_video.py --profile single-10s-final`. Use
`--allow-data-url` only when the provider path for local images has already been
accepted in the current workflow. Do not generate SFX.

## Direct the three clips

Write one useful cooking beat per clip:

1. Product hook and first preparation action.
2. Main cooking or assembly transformation.
3. Finish, pack/plate, and branded result.

Do not treat a 6s Seedance clip as one unbroken camera move. Direct it like a
short food commercial with 2-3 micro-shots inside the clip:

- `0-2s`: establish the action and spatial context.
- `2-4s`: cut, push, rack-focus, or occlusion-wipe into a close-up insert or
  the next cooking location.
- `4-6s`: land the product state and create the transition handle for the next
  clip.

For each beat, decide before generating:

- the shot size and camera angle;
- the lens/focus feel and focus plane;
- the starting frame composition;
- the starting food/action state;
- the product and physical logo-sign placement;
- the setting, time of day, atmosphere, light source, light direction, shadow
  behavior, contrast, and color grade;
- the visual style and whether every reference matches it;
- the micro-shot rhythm and which frame gets the close-up insert;
- the camera verb, movement direction/amplitude/speed, and why the move exists;
- the ending frame composition;
- the exact action mechanics: which hand/tool/object moves, how far, how fast,
  how strongly, and how the action continues into the next beat;
- the intended end composition and handoff to the next clip;
- the exact transition handle: a matched object/action, lid/steam occlusion,
  pour/object motion bridge, rack/plate move, or another motivated bridge.

When the product is cooked or heated, include a real cooking location and action:
move from the prep counter to the stove, show active flame/heat/steamer/cooking
appliance, and make steam, lid movement, or cookware occlusion part of the
transition language. Do not keep the whole commercial on one tabletop unless the
brief explicitly asks for no cooking process.

Generate the clip 1 exact `1080x1920` opening frame first with the configured
image API, preferably through `scripts/run_openrouter_carousel.py --api-only
--asset-id 01` so OpenRouter's provider-safe request size is reframed locally
before Seedance. The prepared `page-02.md` and `page-03.md` files are on-demand
opening slots, not permission to pre-generate all three opening frames.

After each accepted clip, inspect its returned last frame before choosing the
next opening reference. Also inspect the last 8-12 frames when possible so the
join is judged from motion, not only a still:

- Use the returned last frame directly when the product/food state, hands,
  lighting, and camera angle are intact and it can begin the next action
  naturally. For clips after the opening, do not reject a good handoff merely
  because the logo sign leaves frame.
- Generate a transition opening anchor when the returned last frame is visually
  weak, too blurry, malformed, awkwardly composed, or cannot begin the next
  action cleanly. Do not copy the damaged endpoint literally. Use the last
  usable motion cue, product/food state, lighting, camera direction, and planned
  next beat to create a clean bridge frame.
- Make the generated transition anchor a camera transition, not a generic replacement still:
  use match action, steam/lid/pour/object occlusion, plate movement, rack focus,
  texture insert, or another motivated lens bridge.
- Fall back to the planned director-designed opening frame only when the prior
  clip provides no usable motion cue for a transition anchor.
- Reject or retry a clip when its endpoint cannot support the next transition
  handle. Do not hide an incoherent handoff with a plain cross-dissolve.
- If the user asks to extend the final clip or add a standalone ending shot,
  begin from the accepted final returned last frame and lock the set. The prompt
  must name the visible background anchors from that frame, such as stovetop or
  table surface, burner/flame, pot position, window direction, shelf/counter
  shape, background blur, and warm practical light. Use pull-back or settle
  motion only when it keeps those anchors consistent; a wider hero is worse than
  a new-looking kitchen.

RPA handoff review:

```bash
python scripts/handoff_review.py output/YYYYMMDD-HHmmss-task --clip clip-01
python scripts/handoff_review.py output/YYYYMMDD-HHmmss-task --clip clip-02
```

Use `qa/handoffs/clip-XX-to-clip-YY/index.html` as the review surface and
`handoff-review.json` as the decision ledger. If the decision is
`use-last-frame`, run the next Seedance clip with `--continue-from-last-frame`.
If the decision is `transition-anchor`, update/generate the relevant
`page-YY.md`/`page-YY.png` opening anchor first with
`scripts/run_openrouter_carousel.py --api-only --asset-id YY`; confirm the PNG
is exact `1080x1920` before Seedance. If the decision is `retry`,
rerun the source clip before continuing.

During polling, prewrite the next clip prompt from
`analysis/seedance-prompts/drafts/clip-YY-handoff-draft.md` when present. Leave
only `OPENING_REFERENCE` and `HANDOFF_MECHANISM` unresolved until the returned
last frame and motion strip are reviewed.

Do not generate nine storyboard frames by default. Do not import opening frames,
returned last frames, transition anchors, or other generation references into
ChatCut.

Use the official English logo:
`viral-social-remix/umall_logo/asian-grocer-online-powered-by-umall.png`.
Render it as a real printed tabletop sign with scene perspective, lighting,
shadow, and occlusion. Its visible text is
`ASIAN GROCER ONLINE / powered by UMALL`. Never use the Chinese-region logo or a
floating overlay.
The physical sign only needs to read in clip 1's opening reference / first
frame. Do not force the logo sign to remain consistent or visible in later
clips; stove, heat, steam, pour, plating, and food-texture inserts should
prioritize natural commercial cinematography. The product pack may return in the
final hero only when it fits the composition naturally.

Keep the product, kitchen, hands/clothing, light, cookware, and color grade
consistent. No face. Product-package text and the physical logo sign are
allowed; other generated text, subtitles, labels, watermarks, and title cards
are forbidden.

## Opening-frame prompt

```text
Create opening reference [01/02/03] for a premium vertical no-face food
commercial, 1080x1920. This frame begins clip [1/2/3] and depicts [starting
action].

SETTINGS: [location + environment], [time of day], [weather/atmosphere],
[commercial mood/tone].
VISUAL STYLE: photorealistic premium grocery food commercial with one coherent
color grade; references must share this style.
LIGHTING: [source + direction + intensity], [shadow behavior + contrast],
[single color-grade logic].
DIRECTOR: [shot size], [camera angle], [lens/focus feel], START FRAME
[composition + subject placement], MOVE [simple camera verb + direction +
amplitude + speed + purpose], END FRAME [composition + focus target],
smooth/stable/no-jitter.
ACTION MECHANICS: [which hand/tool/object moves], [speed/force/range],
[continuity into the next beat].
MICRO-SHOT RHYTHM:
0-2s [establishing/action shot].
2-4s [cut-in, push-in, rack-focus, occlusion wipe, stove move, flame/steam,
pour motion, or food/product-texture insert].
4-6s [endpoint and transition handle].
CONTINUITY: preserve [product, package, kitchen, hands/clothing, cookware,
lighting, food state, color grade].
HANDOFF: if this follows a prior clip, match its returned last frame unless a
cleaner setup is needed for the next action. If the prior last frame looks bad,
generate a transition opening anchor instead of copying it literally. Preserve
or design the transition handle: [same object/action match, steam/lid occlusion,
pour/object bridge, plate move, rack focus, texture insert, or other specific
bridge].
END INTENTION: the six-second shot should naturally arrive at [end composition].
LOGO PROP: for clip 1 opening reference only, reproduce the supplied ASIAN
GROCER ONLINE / powered by UMALL logo as a real tabletop sign with correct
perspective, shadow, and occlusion. For clips 2 and 3, do not force logo
continuity; omit the sign unless it naturally belongs in the shot.
QUALITY: rich food/product detail, sharp focus, realistic hands and cookware,
natural steam/liquid/heat behavior, premium but believable grocery-commercial
color.
NEGATIVE: face, extra fingers, warped tools, invented packaging, floating logo,
subtitles, captions, labels, title cards, lower-thirds, watermarks.
```

## Seedance motion prompt

Give each request only its selected opening reference. Let Seedance create the
intermediate motion.

```text
Begin exactly from the supplied opening reference. [Subject action].
SETTINGS: [location + atmosphere + tone]. VISUAL STYLE: photorealistic premium
grocery food commercial; no mixed reference styles. LIGHTING: [source +
direction + shadow/contrast behavior]. CAMERA: Shot size [wide/medium/close-up],
angle [eye-level/high/low], lens/focus [natural/wide/85mm/shallow DOF/rack
focus], START FRAME [composition], MOVE [verb + direction/amplitude/speed +
purpose], END FRAME [composition + focus target], smooth/stable/no-jitter.
ACTION MECHANICS: [hand/tool/object movement, speed, force, range, inertia].
Commercial micro-shot rhythm:
0-2s: [establishing/action shot].
2-4s: [close-up insert or location move such as stovetop flame/steamer, glossy
product texture, hand placing or lifting the product, pour motion, or
steam/lid occlusion].
4-6s: [endpoint shot] with [specific bridge] so the next clip can begin cleanly
from the same visual logic.
End with [specific composition/action state].
Preserve the food identity, exact kitchen/stove/table set, visible background
anchors, cookware placement, hands/clothing, lighting direction, and color
grade. When extending or pulling back from a returned last frame, reveal only
more of the same established room; do not change the window, shelf, counter,
burner, pot, room style, or background prop layout.
Preserve the product pack when it naturally remains in frame. Preserve the
physical logo sign only for clip 1's opening frame; later clips should not force
the sign back into stove, steam, pouring, plating, or close-up inserts. Natural
cooking physics. No face, new objects, scene teleporting, subtitles, overlays,
watermarks, or extra logos.
```

For every request: `6s`, `9:16`, `1080p`, `generate_audio: false`, and
`return_last_frame: true`.

Use only the selected opening reference by default. For clips 2 and 3, compare
the accepted prior clip's returned last frame, last motion strip, and planned
opening. Use the returned last frame directly only when it is clean. If it is
bad or weak for the next action, generate a transition opening anchor first and
give Seedance that anchor as the sole reference. Do not add extra still anchors
merely for reassurance.

## Caption cue planning

Do not wait until ChatCut to invent captions. During each Seedance polling wait,
draft external editable current-step captions for the submitted clip and store
them under `analysis/caption-cues/`. This uses otherwise idle time and makes
later editing read prepared timing instead of creating captions from scratch.

Use clip-relative timing first:

- Three-clip route: write `clip-01.json`, `clip-02.json`, and `clip-03.json`
  with times in each source clip's own `0.0-6.0s` range.
- Single-10s route: write `single-10s.json` with times in `0.0-10.0s`.
- After final trimming decisions, run `scripts/caption_cues.py` to write
  `timeline.json` with actual timeline-relative placement before placing
  captions in ChatCut.

JSON cue format:

```json
{
  "schema_version": 1,
  "language": "en",
  "source_clip": "clip-02",
  "timing_basis": "clip-relative",
  "style": "editable centered white text with subtle dark stroke/shadow, no colored box",
  "cues": [
    {"start": 0.4, "end": 1.8, "text": "Aromatics hit the heat"},
    {"start": 2.2, "end": 3.8, "text": "Soy-rich braise builds"},
    {"start": 4.2, "end": 5.6, "text": "Noodles soak up flavor"}
  ]
}
```

Keep cue text short and useful: 2-6 words, natural English for English-region,
one idea per cue, no prices, no claims, no hashtags, no recipe paragraphs. For
food commercials, prefer captions tied to visible action: `Blanch for clean
flavor`, `Aromatics hit the heat`, `Sauce turns glossy`, `Noodles soak up
flavor`, `Ready to serve`. If a clip may be trimmed, keep cues away from the
first and last 0.3 seconds.

When useful, also write a matching `clip-XX.srt` for quick manual preview, but
the JSON is the source of truth for ChatCut placement. Captions are external
editing data only: Seedance prompts must still say no subtitles, no captions,
no title cards, and no burned-in text.

RPA handoff: use `scripts/caption_cues.py` whenever cue JSON exists. During
Seedance polling, run it without trims to validate cue files and write per-clip
SRT previews:

```bash
python scripts/caption_cues.py output/YYYYMMDD-HHmmss-task
```

Before ChatCut caption placement, run it again with actual edit trims so the
timeline math is deterministic:

```bash
python scripts/caption_cues.py output/YYYYMMDD-HHmmss-task \
  --trim clip-01=0.30:5.70 \
  --trim clip-02=0.10:5.40 \
  --trim clip-03=0.00:5.20
```

This writes `analysis/caption-cues/timeline.json`, `timeline.srt`,
`timeline.csv`, and `chatcut-caption-plan.json`. Treat
`chatcut-caption-plan.json` as the editor placement contract.

## Fast review

Build a one-page decision sheet before final handoff:

```bash
python scripts/qa_decision_sheet.py output/YYYYMMDD-HHmmss-task
```

Review one strip/sheet covering all three clips. Check only:

- correct product and logo prop;
- no face or broken hands;
- real commercial shot variety: no more than one clip may feel like a single
  continuous tabletop shot;
- at least one cooking-location/heat/steamer/stove beat when the product needs
  cooking;
- at least two close-up inserts across the sequence, such as product texture,
  steam, sauce, utensils, packaging, pour, crunch, or plating;
- believable food/action progression;
- usable join, including the planned transition handle;
- no generated overlay text.

Retry any failed clip or bad join. Do not proceed to ChatCut with a clip whose
last second fights the next opening.

## ChatCut finish

Import only the three accepted MP4 clips, in order. Never import opening frames,
product/logo references, contact sheets, or QA images.

Make a real editorial pass in ChatCut. Do not assume each Seedance MP4 should be
used as one intact shot. Split, trim, and duplicate only from committed timeline
items as the tool allows. Use the best moments:

- trim weak starts, dead air, repeated movement, and awkward endings;
- cut into close-up portions of the same source when the food/product texture,
  steam, pour, packaging, utensils, or plating moment is stronger than the wide
  view;
- use punch-in / digital push-in / pull-back / pan / reframe effects to create
  secondary camera movement on the best frames;
- add a short match cut, steam/lid/pour/object wipe, or very short dissolve only
  when it serves the already planned handoff;
- do not hide broken continuity with a long generic dissolve.

Keep a natural edit duration; do not force the commercial to exactly 18s or any
other fixed length when the rhythm works. Place by seconds when available; if
the tool requires frames, convert from the editor's actual timebase, not the
source clip fps.

Before ChatCut import, compile an edit plan from the accepted MP4s and actual
trim choices:

```bash
python scripts/edit_plan.py output/YYYYMMDD-HHmmss-task \
  --trim clip-01=0.30:5.70 \
  --trim clip-02=0.10:5.40 \
  --trim clip-03=0.00:5.20
```

Read `analysis/edit-plan.json` first in ChatCut. Import only the accepted MP4s,
place them by the plan's timeline seconds, then apply the listed trims,
transitions, punch-ins, reframes, and caption plan. If the edit changes, rerun
`scripts/edit_plan.py` and `scripts/caption_cues.py` before placing captions.

Add an editable track for agent-generated BGM only when requested or useful,
matching the target market and product tone. Do not generate, place, or time
cooking SFX; the user will handle sound effects later when desired. Add the
user's voiceover only when supplied. Before creating captions in ChatCut, run
`scripts/caption_cues.py` with the actual trims unless
`analysis/caption-cues/chatcut-caption-plan.json` already matches the current
edit. Read that plan first and place those editable current-step captions;
adjust manually only when the edit changes after compilation. Captions stay at
the visual center: white, subtle dark stroke/shadow, no colored box.

Do not run an agent-owned final acceptance pass. The user reviews the cut. After
the requested handoff is available, stop: provide the editable ChatCut project
link, export job status/link, or downloaded file path. Do not extract proof
frames, inspect opening/joins/ending, or judge the cut unless the user explicitly
asks for review or troubleshooting. Only check the minimal tool state required
to know that the handoff exists.
