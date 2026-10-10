# Cooking Video Workflow

This is the single authority for original no-face cooking commercials. Do not
load old run notes unless something fails.

House rules since 2026-10-10:

- **No text or logo from the generator.** Generated frames and clips show the
  real product and food only: no logo, store sign, price, label, caption, or
  brand text.
- **Post-production is `Opue_video_add`** (`references/opue-finish.md`). It
  draws the brand logo (`umall` or `asian_grocer`, chosen per video), the
  headline, step captions, product sticker, and end card. ChatCut is retired.
- **Audio is the clips' native ambient sound only**: sizzle, simmer, utensils,
  pour. Every video prompt ends with
  `soundscape: <ambient sounds>. No dialogue, no music.` No BGM or voiceover
  unless the user supplies or asks for it.

## Route selection

**Default (2026-10-10): NewB Seedance 2.5 single take**, route `newb-30s`.
This is the company API; the work is mostly stir-fry and wok cooking.

- One fixed `30s`, `720p`, `9:16` take with ambient sound carries the whole
  action chain:
  `ingredients -> hot oil/aromatics -> main ingredient into the wok -> toss and sauce gloss -> plate -> chopstick lift / final hero`.
- **The user supplies the reference images, two per segment**: `@图(2k-1)`
  is where segment k starts and `@图(2k)` is where it ends. The default is 9
  images = 5 segments of about 6s: four pairs plus a start-only final segment
  (the plated dish). That fills NewB's 9-image cap; simpler dishes may use
  fewer. The segments share the 30s. Do not generate first frames with the image API. Write one prompt
  paragraph per segment that names both images and says what they show.
- If one segment breaks, fix it in this order: trim it in Opue; reroll only
  that segment as its own take and splice it in; reroll the whole take. The
  details are in `references/newb-seedance25.md#segments-two-references-each-user-rule-2026-10-10`.
- Prompt rules (from NewB):
  - simple subject/action/camera/light;
  - ordered shots, never timestamps;
  - no face, text, logo, or sign;
  - end with `soundscape: 热油滋滋声、锅铲碰锅、翻炒声. No dialogue, no music.`
  - The details are in `references/newb-seedance25.md`.
- The identity check moves to the generated take. Reject and reroll
  (`--label take-02`) if the dish, ingredients, or product changes into
  something else, a face appears, or the model writes text.
- Then caption cues -> `qa_decision_sheet.py` -> `opue_project.py` -> Opue
  pick/preview/render, as in the Opue finish section below.

**Single-product commercials** (not stir-fry) use the NewB route
`newb-product`. The user sends a few references and you design one coherent 30s
story around a buying occasion. The approved patterns below (e.g. the office
beverage chain) are still the taste anchors. See
`references/newb-seedance25.md`.

The routes below are **legacy Seedance 2.0** routes (BytePlus or kuaipao). Use
them only when the user explicitly asks. Choose one before paid generation:

- **Single-10s commercial**: one `10s`, `9:16`, `1080p` Seedance request with
  ambient sound only. Use for drinks, snacks, pantry, office rituals, and simple
  one-setting product-use stories. Pass the product/page image directly as the
  visual bible and opening product reference. Write 4-6 timed micro-shots in one
  prompt. The product must be recognisable in the first shot. Do not create a
  separate OpenRouter first-frame Identity Gate unless the user explicitly asks
  for a still-frame review. Do not force package continuity later. Finish in
  Opue.
- **Three-clip 6s director route**: three `6s`, `9:16`, `1080p` Seedance
  requests with ambient sound only. Use for actual cooking, large scene changes,
  stove/heat, steamer/fire, transformation beats, or when reroll control
  matters.

Default to three-clip for cooked foods. Prefer single-10s for a simple,
coherent one-setting product-use ritual.

Three-clip chain:

`three script beats -> clip 1 designed first frame -> sequential 6s Seedance commercial micro-shot clips with handoff_review.py decisions and next-prompt drafts -> qa_decision_sheet.py -> opue_project.py -> Opue pick/preview/render`

Opening references are generation inputs, not editing assets. They may be a
director-designed first frame, an accepted prior clip's returned last frame, or
a generated transition opening anchor/bridge frame.

Three-clip Identity Gate before paid video:

- Generate clip 1's opening frame with high-quality `openai/gpt-image-2`
  through the OpenRouter Image API, with the supplied product image as an
  actual image reference.
- Check the runner output and manifest: references must not be empty.
- Do not pass a logo and do not ask for a sign; Opue adds branding in post.
- Reject the frame before Seedance if the package shape, colours, artwork,
  product form, or food identity is wrong. Never continue with a hallucinated
  or wrong-package opening, and never try to rescue a wrong opening with later
  clips.
- Also reject it if the model invented a logo, sign, price card, or extra
  brand text. Regenerate the whole first frame.

This gate is the main operational difference from single-10s.

Size preflight is mandatory:

- Seedance requires the local opening reference PNG to be exactly `1080x1920`.
- OpenRouter image requests may reject `1080x1920`, because provider
  dimensions must be divisible by 16.
- Prefer `scripts/run_openrouter_carousel.py --run output/... --api-only
  --asset-id 01` for clip 1, and `--asset-id 02` / `03` only when a handoff
  decision requires a transition anchor. The runner uses a provider-safe
  request size and locally reframes the delivered PNG to `1080x1920`.
- If manual `openrouter_image.py` is the fallback, generate a provider-safe
  portrait such as `1088x1920`, then immediately run
  `scripts/reframe_image.py --size story` and point the manifest at the
  reframed `generated/page-XX.png`.
- Never submit or mark `1088x1920`, `1024x1536`, or any non-`1080x1920`
  opening reference as Seedance-ready.

Default to RPA helpers before manual judgement:

- Run `scripts/next_step.py` after each major stage to write
  `analysis/next-step.json` and the next command.
- Run `scripts/handoff_review.py` after each accepted clip except the final
  clip. It extracts the final motion strip, writes the handoff report, and
  creates the next prompt draft.
- Run `scripts/qa_decision_sheet.py` before the Opue handoff.
- Run `scripts/opue_project.py` after clips are accepted and trims are known.

## Approved patterns to reuse

Use these as taste anchors when a new product resembles them. Do not copy the
product; copy the route choice, action chain, and prompt structure.

- **Leek gyoza / dumpling cooking pattern**: use the three-clip 6s route for
  frozen dumplings, gyoza, buns, or any product whose appeal depends on visible
  cooking transformation. The approved chain is `package identity -> pan action
  -> water/lid/steam -> reveal -> crisp underside -> plated hero`. Keep the
  product pack recognisable at the opening, then let stove, lid, steam, crisp
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
  cover/product reference; reject and regenerate the opening frame if the
  product is cropped or altered. For clips 2 and 3,
  inspect the prior returned last frame and last motion strip, then continue
  from that frame only when the pot, hands, lighting, and food state are clean.
  Keep the recipe logic physical:
  soaked vermicelli should enter late, steam and sauce should bridge the cuts,
  and the final payoff should be chopsticks lifting translucent sauced noodles
  with tender pork belly above the simmering pot.
- **Steamed buns / custard buns / kids-meal pattern**: use the three-clip 6s
  route for custard buns, bao, tangyuan, and other products where the ad must
  prove package-to-cooked convenience. Do not keep the whole sequence on one
  tabletop. The required chain is `package identity -> pack opens and buns are removed -> buns move onto a
  real stovetop steamer or cooking appliance -> lid/steam heat beat -> lid
  opens and buns are lifted out -> plated kids-meal hero with milk`. Clip 1
  must show the pack opening and a motivated move toward the stove/steamer.
  Clip 2 must show active steaming, lid condensation, and a clean open-lid
  reveal. Clip 3 must show out-of-pot plating, one appetizing custard reveal
  when appropriate, and the milk cup entering the final same-kitchen hero.
  Build at least five distinct commercial views across the sequence: package
  hero, hand/pack close-up, stove or steamer medium shot, steam/lid macro, and
  final plate pull-back. If the generated opening frame damages or crops the
  product, or invents a logo or sign, regenerate the whole first frame before
  Seedance.
  Keep the advertised product family stable all the way through: custard buns
  must stay smooth round custard buns with golden custard filling, not pleated
  soup dumplings, xiaolongbao, meat buns, tangyuan, or a generic bao basket.
  If Seedance drifts the food shape or filling, mark that clip failed and retry
  or create a corrected transition anchor before continuing.
- **Japanese pan-fried salmon / pan-seared fish pattern**: use the three-clip
  6s route for salmon portions, fish fillets, and similar products where the
  sale depends on raw freshness becoming a glossy plated meal. The approved
  chain is `product identity and prep board -> tongs move fish to the same pan
  -> oil sear and glaze -> clean returned last-frame handoff -> plate with rice
  and garnish -> slow pull-back in the same kitchen`. Build clip 1's opening
  frame from the real fish texture and product-pack context; reject and
  regenerate the opening frame when the product is cropped or a fake brand
  appears. Continue clips 2 and 3 from returned last
  frames when the pan, tongs, hand, window/shelf/counter anchors, and warm light
  remain clean. If the fish is still visibly underdone at a handoff, write the
  next prompt to continue searing briefly before plating instead of pretending
  it is finished. Final pull-backs must reveal only the established window,
  shelf, pan, counter, and light direction.

- **MiniMax H3 local multi-reference production pattern**: use this when the user selects local ComfyUI / MiniMax H3 R2V instead of Seedance. Prefer the native `3 x 5s` route for 1080x1920 production on A100-class GPUs: generate or collect reference images first, then run each 5s clip with 4-step Turbo LoRA, previous-last-frame continuity, ambient-only native audio, and exact per-clip crop from 1088x1920 to 1080x1920. Accepted clips go to `scripts/opue_project.py` for the Opue finish; do not concatenate them yourself. H3 can preserve fictional people from references, so do not default to hands-only when the brief needs family, actor, cook, model, or product spokesperson continuity. Build a deliberate reference stack before video: fictional character/person reference, action hands/tool reference, fixed scene reference, product/package reference, process-state reference, mid-state reference, final hero reference, with no logo or brand prop (Opue adds branding in post). Keep the stack under H3's 9-image limit, counting any previous last frame inserted as a reference.
  For family heat-and-serve products such as egg tarts, do not start from the finished afternoon-tea table unless the user explicitly asks for only a serving moment. The default commercial chain is `fridge/freezer take-out -> package/tray close-up -> oven/preheat/tray-in -> oven glow and baking macro -> mitt pulls hot tray out -> plating close-up -> parent/child afternoon-tea hero`. Generate specific Image2/Seedream references for `fridge-to-oven` and `oven-baking`; keep children safely away from heat, usually behind the counter or softly in the background. Each 5s H3 prompt should use exactly three stable shots by default: establish/action, one close-up proof insert, and endpoint/handoff. Choose close-up subjects such as package peel, foil cup, custard shine, crust layers, oven glow, mitt action, steam, plating, and final product hero, but do not cram all of them into the same 5s clip. Do not waste a whole clip on a single table arrival.
  For real cooking dishes such as old duck soup, give H3 the missing process knowledge with references and prompt beats. The approved old-duck-soup chain is `fictional cook character -> cutting board -> daikon/duck/ginger/scallion close-ups -> ingredients into pot -> visible blue flame -> lid/steam bridge -> clear broth simmer macro -> ladle stir/lift -> bowl pour -> garnish -> finished table hero`. Always include prep/cut-state and cooked/final-state references, or H3 may skip cutting, keep ingredients raw, or make the final dish muddy. Prompts must name the physical action, shot size, angle, lens/focus, camera move, endpoint, and handoff for every shot. Use the fixed three-shot H3 rhythm for stability: `0.0-1.6s establish`, `1.6-3.4s close-up proof`, `3.4-5.0s endpoint/handoff`. Use close framing inside those three shots instead of adding extra cuts. Favor locked-off, tiny push-in, short tilt, gentle pull-back, or one rack focus; avoid continuous drifting, stacked camera moves, or too many simultaneous actions. Each H3 prompt ends with an Opue-style `soundscape: ... No dialogue, no music.` line.
Reusable lesson: user approval came from route fit and physical commercial
logic, not from generic "cinematic" styling. Good outputs had visible cause and
effect, controlled hand/tool/liquid/steam motion, branding left to post, macro
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
- Never rely on generated text. Packaging may appear from a high-resolution
  product reference, but its printed text is not the brand proof and will drift.
  Names, prices, and the logo are drawn by Opue in post. Show the real product
  with Opue's `product` sticker (the real product image) when it must be
  readable.
- If a reference object is embedded in a busy image, first create or request a
  clean object-only reference. This is especially useful for clothing, bags,
  packaging, utensils, and hero products that Seedance might deform.
- Use storyboard/keyframe references to cue expressionless hand action, camera
  movement, product/prop emphasis, and endpoint composition. A screenplay beat
  plus a small number of consistent keyframes is more reliable than one loose
  descriptive paragraph.
- Keep native audio on, ambient only. Describe the diegetic sounds of the
  visible action (oil sizzle, utensil on cookware, simmer, pour, lid) and end
  the prompt with `soundscape: <ambient sounds>. No dialogue, no music.`
- No music bed, voice lines, or SFX stingers. If native audio damages an
  otherwise good picture, keep the picture and ask the user before stripping
  the audio. Voiceover or BGM only when the user supplies or explicitly asks
  for it; then follow `references/seedance-video.md#native-audio-prompting`.

## Single-10s commercial

Use `scripts/run_pipeline.py prepare-original-video --commercial-route single-10s`
with at least one product/page `--image-reference`. The generated
`analysis/seedance-prompt.md` is the production prompt; rewrite its timed beats
for the product and setting before submission. Single-10s goes directly from
product/page reference into one Seedance request; do not pre-generate a
separate OpenRouter clip-1 first frame unless the user explicitly asks for a
still image review.

Use this shot grammar:

- `0-1.2s`: product/package hero in the real setting. The product must be
  recognisable here.
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
  recognisable opening product, controlled hand movement, steam/liquid/texture
  detail, and a clear final product state.
- No face, subtitles, overlays, watermarks, logos, signs, or forced package
  continuity after the opening shot. End with the `soundscape:` line.

Submit with `scripts/run_seedance_video.py --profile single-10s-final`. Use
`--allow-data-url` only when the provider path for local images has already been
accepted in the current workflow. Ambient sound only: no music or SFX stingers.

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
- the product placement (no logo or sign in frame);
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

Generate the clip 1 `1080x1920` opening frame first with the configured image
API, and require the delivered frame to be exact `1080x1920`, preferably through
`scripts/run_openrouter_carousel.py --api-only
--asset-id 01` so OpenRouter's provider-safe request size is reframed locally
before Seedance. The prepared `page-02.md` and `page-03.md` files are on-demand opening
slots, not permission to pre-generate all three opening frames.

After each accepted clip, inspect its returned last frame before choosing the
next opening reference. Also inspect the last 8-12 frames when possible so the
join is judged from motion, not only a still:

- Use the returned last frame directly when the product/food state, hands,
  lighting, and camera angle are intact and it can begin the next action
  naturally. Do not reject a good handoff merely because the product pack
  leaves frame.
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

Do not generate nine storyboard frames by default. Opening frames, returned
last frames, transition anchors, and other generation references never become
takes in the Opue project.

Generate no logo, store sign, price, label, or brand text in any frame or clip.
Branding is Opue's job in post: the brand logo, headline, step captions, product
sticker, and end card. The product pack may return in the final hero only when
it fits the composition naturally.

Keep the product, kitchen, hands/clothing, light, cookware, and color grade
consistent. No face. Product packaging may appear as the real object; all other
generated text, subtitles, labels, watermarks, signs, and title cards are
forbidden.

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
BRAND: no logo, store sign, price card, or brand text anywhere in the frame;
Opue draws branding in post. Reproduce the supplied product/package shape,
colours, and artwork faithfully without inventing new package text.
QUALITY: rich food/product detail, sharp focus, realistic hands and cookware,
natural steam/liquid/heat behavior, premium but believable grocery-commercial
color.
NEGATIVE: face, extra fingers, warped tools, invented packaging, logo, sign,
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
Preserve the product pack when it naturally remains in frame. Natural cooking
physics. No face, new objects, scene teleporting, subtitles, overlays,
watermarks, logos, or signs.
soundscape: [ambient sounds of the visible action]. No dialogue, no music.
```

For every request: `6s`, `9:16`, `1080p`, `generate_audio: true` (ambient
only), and `return_last_frame: true`.

Use only the selected opening reference by default. For clips 2 and 3, compare
the accepted prior clip's returned last frame, last motion strip, and planned
opening. Use the returned last frame directly only when it is clean. If it is
bad or weak for the next action, generate a transition opening anchor first and
give Seedance that anchor as the sole reference. Do not add extra still anchors
merely for reassurance.

## Caption cue planning

Do not wait until the Opue finish to invent captions. During each Seedance polling wait,
draft external current-step captions for the submitted clip and store
them under `analysis/caption-cues/`. This uses otherwise idle time and makes
later editing read prepared timing instead of creating captions from scratch.

Use clip-relative timing first:

- Three-clip route: write `clip-01.json`, `clip-02.json`, and `clip-03.json`
  with times in each source clip's own `0.0-6.0s` range.
- Single-10s route: write `single-10s.json` with times in `0.0-10.0s`.
- NewB route: name the file after the take label, such as `newb-video.json`
  or `take-02.json`, with times in `0.0-30.0s`.

JSON cue format:

```json
{
  "schema_version": 1,
  "language": "en",
  "source_clip": "clip-02",
  "timing_basis": "clip-relative",
  "cues": [
    {"start": 0.4, "end": 1.8, "text": "Aromatics hit the heat"},
    {"start": 2.2, "end": 3.8, "text": "Soy-rich *braise* builds"},
    {"start": 4.2, "end": 5.6, "text": "Noodles soak up flavor"}
  ]
}
```

Cue text rules:

- Keep it short and useful: 2-6 words of natural English, one idea per cue.
- No prices, claims, hashtags, or recipe paragraphs. Opue also forbids facts
  without a source.
- Tie captions to visible action, for example `Blanch for clean flavor`,
  `Aromatics hit the heat`, `Sauce turns glossy`, or `Ready to serve`.
- Mark the keyword to highlight with `*stars*`.
- Each cue becomes an Opue step caption at its start time, with a step badge
  and the kit's word-by-word animation. A cue starts a new step, so write one
  cue per visible step.
- If a clip may be trimmed, keep cues away from the first and last 0.3
  seconds.

Captions are external data only. Generated video prompts must still say no
subtitles, no captions, no title cards, and no burned-in text.

Check the cue files during polling:

```bash
python scripts/caption_cues.py output/YYYYMMDD-HHmmss-task
```

This validates the cue files, writes per-clip SRT previews, and, with `--trim`,
writes a timeline preview. `scripts/opue_project.py` reads the cue JSON
directly.

## Fast review

Build a one-page decision sheet before final handoff:

```bash
python scripts/qa_decision_sheet.py output/YYYYMMDD-HHmmss-task
```

Review one strip/sheet covering all three clips. Check only:

- correct product identity, with no generated logo, sign, price, or brand text;
- product/package identity remains consistent across all clips; reject if the
  product mutates into another SKU, package, dumpling/bun type, filling, or
  serving style;
- no face or broken hands;
- real commercial shot variety: no more than one clip may feel like a single
  continuous tabletop shot;
- at least one cooking-location/heat/steamer/stove beat when the product needs
  cooking;
- at least two close-up inserts across the sequence, such as product texture,
  steam, sauce, utensils, packaging, pour, crunch, or plating;
- believable food/action progression;
- usable join, including the planned transition handle;
- no generated overlay text;
- ambient sound only: no music, dialogue, or voice.

Retry any failed clip or bad join. Do not proceed to the Opue finish with a clip
whose last second fights the next opening.

## Opue finish

Follow `references/opue-finish.md`. In short:

1. Ask for the brand if it is not given: `umall` or `asian_grocer`.
2. Draft the project from the accepted MP4s and actual trims:

   ```bash
   python scripts/opue_project.py output/YYYYMMDD-HHmmss-task \
     --brand asian_grocer --title "Make This for the Kids" \
     --kicker "Pan-fried gyoza" --emoji "🥟" \
     --trim clip-01=0.30:5.70 --trim clip-03=0.00:5.20
   ```

3. You are the editor. Look at the stills in `qa/opue-frames/` and decide
   these yourself, without asking the user:
   - the per-step `emoji`;
   - the highlighted `keywords`;
   - ingredient `callouts` when the opening lays out ingredients;
   - a `product` sticker made from the real product image;
   - `cta.search`.

   Every on-screen fact must come from the user or the package.
4. In the Opue repo, run `engine.pick <brand> --for projects/<name>`, then
   `engine.preview`. Check the preview yourself and fix what is off, then run
   `engine.render --sheet`.
5. Give the user the MP4 from `projects/<name>/out/` and its contact sheet. Keep
   a natural edit duration. The clips' ambient sound stays as the only audio.

Do not run an extra agent-owned acceptance pass after Opue's own pre-handoff
checks. The user reviews the cut.
