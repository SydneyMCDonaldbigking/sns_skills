---
name: viral-social-remix
description: |
  Use when a user provides a viral social-post URL, active Chrome tab, image,
  video, local file/folder, product image, or original food brief and wants a
  branded English-region or Chinese-region social remix: Xiaohongshu capture,
  Instagram/Facebook carousel, shopping-guide image, or Seedance/Grok product
  and cooking commercial. Also use for UMALL / Asian Grocer Online workflows,
  English-region logo/size decisions, Chrome MCP capture, OpenRouter image
  generation, Seedance three-clip cooking videos, 10s product commercials,
  NewB Seedance 2.5 takes, Opue_video_add post-production (logo, Reels
  captions, end card), final-frame video extensions, and fixing generated
  carousel artifacts such as fake prices, blurred/mosaic UI, wrong logo, or
  wrong target region.
---

# Viral Social Remix

Use this file only as a route map. Current user instructions override memory.
Never load the whole vault.

## Critical defaults

- Default company output is English-region unless the user explicitly asks for
  Chinese-region or Chinese Xiaohongshu target output. A Chinese source post is
  source/capture context only; it must not flip the target region.
- English-region carousel output is `instagram-facebook`, natural English,
  `1152x1152`, `caption-en.txt`, and the official English lockup:
  `viral-social-remix/umall_logo/asian-grocer-online-powered-by-umall.png`.
  Never use the Chinese `umall_logo.png` unless the user explicitly chooses
  Chinese-region output.
- Preserve source page count, order, role, and meaning. Do not invent prices,
  discounts, app claims, fake UI, fake product availability, or fake screens.
  If generated shopping-card prices/placeholders are uncertain, remove them,
  cover them cleanly in white, or leave the space blank; never keep blurred or
  mosaic UI artifacts.
- If the user mentions Chrome, Chrome MCP, or links `chrome:control-chrome`,
  control the user's existing logged-in Chrome tab. Do not silently use the
  in-app browser or a fresh unauthenticated tab.
- **All videos go to NewB Seedance 2.5 by default** (company API, set
  2026-10-10). The work is mostly stir-fry and other wok cooking. One take is
  fixed at `30s`, `720p`, `9:16`. Prepare it with
  `scripts/run_pipeline.py prepare-original-video` (route `newb-30s` is the
  default) and submit it with `scripts/run_newb_video.py`. Read
  `references/newb-seedance25.md`. Don't ask which account to bill.
- **The user supplies the reference images, two per segment** (start state,
  end state). The default is 9 images = 5 segments of about 6s: four pairs plus
  a start-only last segment (the plated dish). NewB allows at most 9 images;
  simpler dishes may use fewer. Pass them as `--image-reference` in order. One
  NewB request carries all segments. If one segment breaks, trim it in Opue
  first, then reroll only that segment as its own take, and reroll the whole
  take last. Do not call the OpenRouter image
  API to design first frames for video. Look at the user's references, name
  each one as `@图N` in the prompt, and check product/food identity in the
  generated take instead.
- **Single-product commercials** use route `newb-product`. The user gives a
  few references (`@图1` = the product) and the agent is the designer: it
  invents one coherent 30s story around a buying occasion and writes the
  prompt. There are no segment pairs; see `references/newb-seedance25.md`.
- Generated clips keep native ambient sound only (sizzle, wok, utensils):
  every video prompt ends with
  `soundscape: <ambient sounds>. No dialogue, no music.` No BGM, voiceover,
  subtitles, or overlays come from the generator. Use accepted MP4s only. Opue
  renders the final at a `1080x1920` canvas from the 720p source.
- Video post-production is `Opue_video_add`, not ChatCut (retired 2026-10-10).
  Read `references/opue-finish.md`. Opue draws the logo and every on-screen word;
  generated frames carry no logo, sign, price, label, or brand text. Video brand
  is `umall` or `asian_grocer`, chosen per video (ask when not given), with a
  full-colour transparent logo; the combined lockup stays for carousels only.
- Legacy Seedance 2.0 accounts are used only when the user names them, and
  their keys are never mixed: `--provider byteplus` (company ModelArk) and
  `--provider kuaipao` (the user's personal gifted relay). Everything below
  about three-clip, single-10s, opening frames, and handoffs applies only to
  those legacy routes.
- Legacy three-clip product/cooking commercials have a product Identity Gate before
  Seedance: generate clip 1's opening frame with OpenRouter Image API model
  `openai/gpt-image-2` at high quality, pass the supplied product image as an
  actual image reference, and verify the runner reports non-empty `references`.
  Do not pass a logo and do not ask for a sign. If the package, product shape,
  colours, or food identity is hallucinated, cropped, or replaced, reject the
  frame before Seedance and regenerate; do not continue with a wrong-product
  clip.
- Single-10s commercials do not use the three-clip Identity Gate by default.
  Feed the product/page image directly to the single Seedance request as the
  visual bible and opening product reference. Require a recognisable product in
  the first shot, then allow the package to leave frame naturally.
- For Seedance opening references, the delivered local PNG must be exactly
  `1080x1920` before submission. OpenRouter image requests may need a
  provider-safe size such as `1088x1920` or `1024x1536`; prefer
  `scripts/run_openrouter_carousel.py --api-only --asset-id XX`, because it
  reframes to `1080x1920`. If using `scripts/openrouter_image.py` manually,
  immediately run `scripts/reframe_image.py --size story` and point the
  manifest at the reframed PNG. Never mark or submit a `1088x1920` opening
  frame as validated for Seedance.
- While a Seedance clip is polling, use the wait time to draft external editable
  caption cues in `analysis/caption-cues/`. Store clip-relative JSON such as
  `clip-02.json` with `start`, `end`, and `text` (2-6 English words naming a
  visible action, `*star*` the keyword). Check them with `scripts/caption_cues.py`.
  They become Opue step captions through `scripts/opue_project.py`; never burn
  them into generated video.
- Use the RPA helper scripts before manual judgement when they apply:
  `scripts/next_step.py` for command choice, `scripts/handoff_review.py` for
  clip joins, `scripts/qa_decision_sheet.py` for one-page review,
  `scripts/opue_project.py` to draft the Opue project from accepted clips, and
  `scripts/carousel_cleanup.py` for fake price/mosaic/placeholder white-cover
  repairs.
- In the three-clip route, inspect the prior clip's returned last frame and last
  motion strip before the next clip. Use the returned frame only when it is
  clean; generate a transition opening anchor when the frame is weak, malformed,
  blurry, awkward, or cannot begin the next action.
- Product identity still must remain stable after the opening. If Seedance
  changes the product family, package, ingredient shape, filling, or serving
  identity across clips, stop and retry or create a corrected transition anchor;
  never hand off a raw concat where the advertised product becomes a different
  product.
- For final-frame extensions, extra ending shots, or slow pull-back hero shots,
  begin from the accepted final last frame and lock the exact kitchen/stove/table
  set: cookware position, visible background props, window/shelf/counter layout,
  burner/flame, light direction, color grade, and camera height. Pull back only
  into the same established room; do not invent a new kitchen.
- Stop at the user's requested handoff. If they say no editing, stop at the
  accepted clips and skip Opue. The user is the reviewer.

## Context

Always read `brand-profile.md` and `references/brand-region-assets.md`. Reuse
known product and brand values. Product and brand are mandatory.
Ask only for missing mandatory fields or low-confidence platform when a value
is still `未填写`.

For an original product/cooking commercial, skip the memory index and read only
`references/cooking-video-workflow.md`. For other routes, read
`docs/memory/viral-social-remix/index.md`, then only the linked route note.

Search `data/material-index.jsonl` before recollecting known sources or assets.
Use `scripts/query_material_index.py` or `scripts/build_remix_context.py` only
when needed.
When searching known materials, use a hybrid retrieval mindset: combine exact
product/platform keywords with visual scene terms, modality clues, and natural
language intent. For vague visual requests, ask or infer a narrower scene,
style, use case, or product need before generating new assets.

## Choose one route

Infer the source platform and target output platform separately.

Default company remix output is English-region unless the user explicitly asks
for Chinese-region or Chinese Xiaohongshu target output. A Xiaohongshu URL or
Chinese source copy identifies capture/localization work only; it must not flip
the target to Chinese. For default "搬运" from Xiaohongshu, use the English
carousel profile: `instagram-facebook`, natural English, `1152x1152`,
`caption-en.txt`, and the English-region `ASIAN GROCER ONLINE / powered by
UMALL` logo.

- **Xiaohongshu source to English carousel**: preserve page count, order,
  meaning, and page roles; output natural English `1152x1152` and
  `caption-en.txt`.
- **Chinese Xiaohongshu output**: preserve the source structure; output
  `1152x1536` and `caption-zh.txt`; choose only for explicit Chinese-region or
  Chinese Xiaohongshu target requests.
- **Instagram/Facebook carousel**: preserve page count and roles; output
  natural English `1152x1152` and `caption-en.txt`.
- **General video remix**: select exactly nine narrative frames and build the
  requested storyboard/contact sheet.
- **Original product/cooking commercial**: use `vertical-video`, `9:16`,
  `1080x1920`, then choose either the single-10s route or the three-clip
  director-first-frame route below.

For carousel and general video routes, load `references/platform-profiles.md`
and `references/breakdown-schema.md`. Load
`references/xiaohongshu-real-talk-template.md` only for real-talk posts and
`references/instagram-pantry-essentials-template.md` only for pantry posts.

## Acquire and prepare

Accept a post URL, active logged-in tab, local file, local folder, or original
brief.

- If the user explicitly mentions Chrome, Chrome MCP, or links
  `chrome:control-chrome`, use Chrome control to connect to the user's existing
  logged-in Chrome tab. Claim the current/open source tab and capture from that
  state; do not silently fall back to the in-app browser or a fresh unauthenticated
  tab.
- Scan a local folder with `scripts/scan_media.py`.
- Capture Xiaohongshu with `scripts/xhs_browser_capture.mjs`, then
  `scripts/capture_source_package.py`.
- Use `scripts/capture_source_package.py` for other source packages.

Preserve source order, caption, author, URL, page count, media files, and a
screenshot fallback. Do not claim blocked originals were downloaded.

Create a resumable run with `scripts/create_run_dir.py`,
`scripts/prepare_remix_run.py`, or `scripts/run_pipeline.py`. Follow
`references/output-schema.md`; keep state in `scripts/manifest.py`; never
overwrite a prior run. Run deterministic validation before paid generation.

## Carousel

Preserve layout logic and copy meaning. Keep the final shopping/search guide
unless the user waives it. Use real supplied UI/screenshots; never invent
prices, products, or app screens.
For final shopping, category, search, or app-entry pages, load
`references/shopping-guide-page.md`. These pages are operation tutorials, not
generic CTA posters. When a real phone screenshot and a source/style guide page
are available, generate the final page with OpenRouter Image API at high
quality, pass the real phone screenshot, style reference, and English-region
brand lockup as references, and only use local composites as temporary layout
sketches or emergency placeholders.
When generated output contains fake prices, mosaic placeholders, blurred UI, or
uncertain shopping widgets, use `scripts/carousel_cleanup.py` to white-cover
those regions instead of hand-patching them in an image editor.

For English-region carousels, use `1152x1152`, `caption-en.txt`, and
`viral-social-remix/umall_logo/asian-grocer-online-powered-by-umall.png`. Do
not use `viral-social-remix/umall_logo/umall_logo.png` unless the user
explicitly requests a Chinese-region or Chinese Xiaohongshu target.

Load `references/prompt-patterns.md` and `references/image-provider.md`. Resolve
the provider with `scripts/image_provider.py`. Production GPT Image 2 uses the
configured image API; `openai/gpt-5.4-image-2` is the explicit legacy route.
Load `references/fixed-brand-scenes.md` only when a warehouse scene is required.
When the API is available, generate the assets; do not stop at prompts.

## Original product/cooking commercial

Default (2026-10-10): NewB Seedance 2.5, route `newb-30s`, with the user's
reference images:

1. `scripts/run_pipeline.py prepare-original-video --brief ...
   --image-reference <opening-state image> --image-reference ...`
2. Rewrite `analysis/newb-prompt.md` for the dish:
   - one paragraph per segment (第N段：从 @图(2k-1) 到 @图(2k)), never
     timestamps;
   - name every `@图N` the user supplied;
   - no face, text, logo, or sign;
   - end with the `soundscape:` line.
3. Run `scripts/run_newb_video.py --run <run> --quota`, then
   `scripts/run_newb_video.py --run <run>`. The images come from the manifest.
   Never resubmit a slow job; use `--resume auto`. Use `--label take-02` for a
   reroll.
4. While it generates, write `analysis/caption-cues/newb-video.json`.
5. Accept the take, run `scripts/qa_decision_sheet.py`, then do the Opue
   finish below.

Load `references/cooking-video-workflow.md` as the single production authority.
It already includes the Seedance workshop rules needed for food/product
commercial prompting. Load `references/seedance-video.md` for non-cooking
Seedance generation, provider/API controls, video extension, native-audio
experiments, prompt-quality repair, or after a runner/API failure. For cooking
commercial final-clip extensions, keep `references/cooking-video-workflow.md`
as the continuity authority and apply its exact kitchen/background lock before
using any generic Seedance extension guidance.

Choose the route before generation:

- **Single-10s commercial**: use for drinks, snacks, pantry products,
  shelf-stable products, office rituals, and other products where one coherent
  environment can carry the whole ad. Feed the product/page image directly as
  the visual bible and opening product reference. Generate one `10s`, `9:16`,
  `1080p` Seedance multi-shot clip with 4-6 timed beats and ambient sound only.
  The product must be recognisable in the opening shot; do not force package
  continuity later. Finish logo, captions, and end card in Opue.
- **Three-clip 6s director route**: use for cooked products, big location
  changes, stove/heat/steamer action, complex transformations, or when the user
  wants more reroll/control. Chain:
  `script beats -> clip 1 first frame -> commercial micro-shot Seedance clips with handoff/transition-anchor decisions -> Opue finish`.

Default to three-clip for actual cooking. Prefer single-10s when the story is a
simple product-use ritual in one place, such as an office product break.

For the three-clip route:

- Direct three script beats. For each 6s clip choose a 2-3 shot commercial
  rhythm: establishing/action shot, close-up insert or scene move, and endpoint
  bridge. Do not write one-camera-move prompts unless the user explicitly asks
  for a single-take film.
- Use official camera structure for every micro-shot: shot size, camera angle,
  lens/focus feel, starting frame composition, movement verb with
  direction/amplitude/speed, and ending frame composition. Prefer one purposeful
  camera move per micro-shot.
- Include real cooking-film grammar when the product requires heat: move from
  prep counter to stove, show active flame/heat/steamer or cooking appliance,
  cut into food texture, and use steam/lid/pour/object occlusion as transitions.
- Generate the clip 1 `1080x1920` first frame first, and require that delivered
  frame to be exact `1080x1920`. Use
  `scripts/run_openrouter_carousel.py --api-only --asset-id 01` so provider-safe
  OpenRouter sizes are locally reframed before Seedance. For clips 2 and 3,
  inspect the accepted prior clip's returned last frame before choosing the next
  opening reference. Use that returned last frame directly when it is the most
  coherent handoff. If the returned last frame is visually weak, malformed, too
  blurry, awkwardly composed, or unable to begin the next action, generate a new
  transition opening anchor with the image model instead of using the bad frame
  literally. When an anchor is needed, generate the corresponding exact
  `1080x1920` `page-02.png` or `page-03.png` with the same runner before
  calling Seedance. The transition anchor must design the camera bridge: match
  action, steam/lid/pour/object occlusion, plate movement, rack focus, or
  another motivated lens transition. Retry the prior clip only when no honest
  bridge can be made.
- Brand the sequence in post, not in the frame. Generated frames carry the real
  product and food only: no logo, store sign, price, or brand text. Opue adds the
  brand logo, headline, step captions, product sticker, and end card.
- Give each Seedance request only its selected opening reference: a designed
  first frame, an accepted returned last frame, or a generated transition
  opening anchor.
- Use `6s`, `9:16`, `1080p`, native ambient sound only, no face, and no
  generated subtitles or overlays. Write the prompt as timed shot beats such as
  `0-2s`, `2-4s`, `4-6s`, ending with
  `soundscape: <ambient sounds>. No dialogue, no music.`
- Review each clip's last 8-12 frames before approving the next clip. The next
  prompt must name the handoff mechanism: same object/action match, steam/lid
  occlusion, pour/object motion bridge, or another deliberate bridge.
- Review all three clips once and retry any visible failure, bad join, damaged
  product, or endpoint that cannot support the planned handoff.
- Only accepted MP4 clips go into the Opue project. Never use first frames,
  storyboards, product references, contact sheets, or QA images as takes.
- Finish with `scripts/opue_project.py` (brand, headline, actual trims). You are
  the editor: from the stills it writes to `qa/opue-frames/`, decide the
  per-step emoji, highlighted keywords, ingredient callouts, and product sticker
  yourself, without handing them back to the user. Then in the Opue repo run
  `engine.pick` and `engine.preview` (check it), then `engine.render --sheet`.
  Keep a natural edit duration; follow `references/opue-finish.md` for headline
  angle, per-step emoji, ingredient callouts, and fact rules. No BGM, voiceover,
  or SFX stingers unless the user supplies or asks for them.

Prepare three-clip with
`scripts/run_pipeline.py prepare-original-video --commercial-route three-clip`.
Generate clips sequentially with
`scripts/run_seedance_video.py --storyboard-group 1`, inspect the returned last
frame and last motion strip, then either use it directly or generate the group 2
transition opening anchor; repeat this handoff check before group 3.

Prepare single-10s with
`scripts/run_pipeline.py prepare-original-video --commercial-route single-10s`
and pass at least one product/page `--image-reference`. Submit one Seedance job
with `scripts/run_seedance_video.py --profile single-10s-final`.

Use `scripts/run_openrouter_video.py` and `references/openrouter-video.md` only
for an explicitly selected Grok route.

When the user selects Seedance 2.5 / NewB, keep the route choice, action chain,
Identity Gate, and Opue finish from `references/cooking-video-workflow.md`, but
follow `references/newb-seedance25.md` for generation: one 30s take per
commercial by default, the gate-approved opening frame as the sole `@图1`, ordered
shots without timestamps, `--quota` before batches, and `--resume` instead of
resubmitting slow jobs.

## Finish

After the Opue render, hand over the MP4 from `projects/<name>/out/` together
with its contact sheet. The user is the reviewer. Do only Opue's own pre-handoff
checks: cuts on their frames, ambient sound in sync, no frozen frames, and
readable captions. Do not run an extra agent-owned acceptance pass or judge
whether the cut is good unless the user asks for review or troubleshooting.

When the user says a commercial is good, satisfying, approved, or ready to post,
distill the reusable lesson immediately into
`references/cooking-video-workflow.md`: route choice, action chain, reference
strategy, Opue finish choices, and why the result worked. Keep it concise and reusable,
not a chat-only memory. Write a run note only after success and only when it
contains a reusable lesson. Never store keys, raw provider responses, signed
URLs, or base64 payloads in Obsidian.

Do not bypass authentication or anti-scraping controls. Do not reproduce source
watermarks, unauthorized logos, or real-person identity.
