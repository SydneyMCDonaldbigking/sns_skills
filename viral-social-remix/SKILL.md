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
  final-frame video extensions, and fixing generated carousel artifacts such as
  fake prices, blurred/mosaic UI, wrong logo, or wrong target region.
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
- For original cooking commercials, use `vertical-video`, `9:16`, `1080x1920`.
  Default actual cooking to the three-clip 6s director route; use single-10s
  only for simple one-setting product rituals. Seedance cooking clips are
  silent, no subtitles/overlays, no cooking SFX, and use accepted MP4s only.
- While a Seedance clip is polling, use the wait time to draft external editable
  caption cues in `analysis/caption-cues/`. Store clip-relative JSON such as
  `clip-02.json` with `start`, `end`, and `text`; add SRT only when useful.
  These cues are for later ChatCut/editor placement, never burned into Seedance.
  Before ChatCut caption placement, run `scripts/caption_cues.py` with actual
  trims to compile `timeline.json`, `timeline.srt`, `timeline.csv`, and
  `chatcut-caption-plan.json`.
- In the three-clip route, inspect the prior clip's returned last frame and last
  motion strip before the next clip. Use the returned frame only when it is
  clean; generate a transition opening anchor when the frame is weak, malformed,
  blurry, awkward, or cannot begin the next action.
- Product/logo branding is commercial context, not a billboard. The physical
  `ASIAN GROCER ONLINE / powered by UMALL` sign must read in clip 1's opening
  reference only. Do not force logo/sign continuity in later cooking clips.
- For final-frame extensions, extra ending shots, or slow pull-back hero shots,
  begin from the accepted final last frame and lock the exact kitchen/stove/table
  set: cookware position, visible background props, window/shelf/counter layout,
  burner/flame, light direction, color grade, and camera height. Pull back only
  into the same established room; do not invent a new kitchen.
- Stop at the user's requested handoff. If they say no editing, do not enter
  ChatCut. The user is the reviewer.

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
  the visual bible and opening product reference. Generate one silent `10s`,
  `9:16`, `1080p` Seedance multi-shot clip with 4-6 timed beats. Product/logo
  readability is required only in the opening shot; do not force logo or package
  continuity later. Use ChatCut only for trim/reframe/BGM/captions/voiceover
  handoff when needed.
- **Three-clip 6s director route**: use for cooked products, big location
  changes, stove/heat/steamer action, complex transformations, or when the user
  wants more reroll/control. Chain:
  `script beats -> clip 1 first frame -> commercial micro-shot Seedance clips with handoff/transition-anchor decisions -> ChatCut finish`.

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
- Generate the clip 1 `1080x1920` first frame first. For clips 2 and 3, inspect
  the accepted prior clip's returned last frame before choosing the next opening
  reference. Use that returned last frame directly when it is the most coherent
  handoff. If the returned last frame is visually weak, malformed, too blurry,
  awkwardly composed, or unable to begin the next action, generate a new
  transition opening anchor with the image model instead of using the bad frame
  literally. The transition anchor must design the camera bridge: match action,
  steam/lid/pour/object occlusion, plate movement, rack focus, or another
  motivated lens transition. Retry the prior clip only when no honest bridge can
  be made.
- Brand the sequence as a commercial, not every frame as a billboard. The
  supplied product and official physical `ASIAN GROCER ONLINE / powered by
  UMALL` table sign must read in clip 1's opening reference / first frame only.
  Later clips do not need to preserve, repeat, or match the logo sign; close-up
  food, stove, heat, pour, plating, or texture inserts may leave it out of
  frame naturally.
- Give each Seedance request only its selected opening reference: a designed
  first frame, an accepted returned last frame, or a generated transition
  opening anchor.
- Use `6s`, `9:16`, `1080p`, silent generation, no face, and no generated
  subtitles or overlays. Write the prompt as timed shot beats such as
  `0-2s`, `2-4s`, `4-6s`.
- Review each clip's last 8-12 frames before approving the next clip. The next
  prompt must name the handoff mechanism: same object/action match, steam/lid
  occlusion, pour/object motion bridge, or another deliberate bridge.
- Review all three clips once and retry any visible failure, bad join, damaged
  product/sign, or endpoint that cannot support the planned handoff.
- Import only accepted MP4 clips into ChatCut. Never import first frames,
  storyboards, product/logo references, contact sheets, or QA images.
- Treat ChatCut as a second editing pass, not an assembler. Split each accepted
  MP4 into usable beats when needed; trim weak starts/ends; punch in on texture,
  steam, pour, utensils, packaging, or plating; reframe with subtle
  digital push-ins, pull-backs, pans, and rack-focus-like zooms; add match cuts
  or motivated short transitions only where they improve rhythm.
- Keep a natural edit duration. Do not force the final commercial to a fixed
  length when the visual rhythm works. In ChatCut, place clips by actual seconds
  or convert durations with the editor's real timebase; never assume that source
  fps equals timeline framebase. Generate and place editable BGM only; do not
  generate or place cooking SFX. Add the user's voiceover when supplied; add
  centered white editable current-step captions with a subtle dark stroke/shadow
  and no colored box.

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

## Finish

After generation and ChatCut editing, do not run an agent-owned acceptance pass.
The user is the reviewer. Stop after the requested handoff is available: an
editable ChatCut project link, an export job, or a downloaded/exported file. Do
not extract proof frames, inspect opening/joins/ending, or judge whether the cut
is good unless the user explicitly asks for review or troubleshooting. Only do
minimal tool-state checks needed to know that the handoff exists.

When the user says a commercial is good, satisfying, approved, or ready to post,
distill the reusable lesson immediately into
`references/cooking-video-workflow.md`: route choice, action chain, reference
strategy, logo policy, and why the result worked. Keep it concise and reusable,
not a chat-only memory. Write a run note only after success and only when it
contains a reusable lesson. Never store keys, raw provider responses, signed
URLs, or base64 payloads in Obsidian.

Do not bypass authentication or anti-scraping controls. Do not reproduce source
watermarks, unauthorized logos, or real-person identity.
