# Seedance Official Prompting Notes

Use this after reading `seedance-video-generation.md` when preparing Seedance
2.0 cooking, product, or reference-remake videos.

Sources studied on 2026-07-28:

- BytePlus ModelArk Dreamina Seedance 2.0 series tutorial:
  https://docs.byteplus.com/en/docs/ModelArk/2291680
- BytePlus ModelArk Create video generation task API:
  https://docs.byteplus.com/en/docs/modelark/1520757
- BytePlus ModelArk Dreamina Seedance 2.0 prompt guide:
  https://docs.byteplus.com/en/docs/modelark/2222480
- BytePlus official note: Seedance 2.0 prompt optimization skill, invoked as
  `/sd2-pe + prompt` in a code/AI agent after installing its `SKILL.md`.
- ChatCut `video-gen` / `seedance2` skill notes: reference assets anchor
  product/object/style far better than text-only prompts.

## Main Takeaway

Do not over-control Seedance with too many still storyboard frames. The official
prompt guide favors a compact timeline storyboard:

- `Shot 1`
- `Shot 2`
- `Shot 3`

Each shot should describe, in order:

1. camera movement or transition;
2. subject action;
3. spatial relationship or cooking state;
4. optional audio information.

For our 6-second cooking tests, use three soft segments:

- `Shot 1, opening third`: product/ingredient setup and first food action.
- `Shot 2, middle third`: main cooking transformation.
- `Shot 3, final third`: texture, plating, or hero result.

Do not treat `[0-2s]`, `[2-4s]`, `[4-6s]` as hard timing constraints. The
official guide warns that precise second-level timing can be unstable. Use those
labels only as pacing hints.

## Reference Assets

Seedance 2.0 supports multimodal reference generation with:

- images: 0-9;
- videos: 0-3;
- audio: 0-3;
- text prompt.

For multimodal reference generation, at least one image or video is required;
audio-only and text-plus-audio-only are not supported.

In prompts, refer to assets by request order, such as `Image 1`, `Image 2`,
`Video 1`, and `Audio 1`. Do not refer to the raw Asset ID in the prompt.

For our English no-face cooking videos, prefer a 4-6 asset pack:

- `Image 1`: clean first-frame food scene or finished dish mood reference.
- `Image 2`: real hero product/package reference, cropped clearly.
- `Image 3`: second product/package reference when product fidelity matters,
  such as sauce bottle, soup base pack, package back/front, or ingredient pack.
- `Image 4`: English-region physical brand prop or logo/sign reference.
- `Video 1`: source cooking rhythm or camera movement reference, when
  available.
- `Audio 1`: optional rhythm/ambience reference only for final audio-enabled
  tests. For first visual QA, keep Seedance no-audio and finish sound in
  ChatCut.

Use more real product and brand references when product fidelity matters. For a
logo, ask for it as a physical printed sign, packaging label, table card, or
scene prop. Do not ask for floating logos, screen overlays, stickers, lower
thirds, or ad banners.

Do not rely on a single logo image plus text prompt to preserve brand identity.
Treat product/package and logo/sign as visual anchors:

- pass them as `reference_image`;
- give each manifest reference a stable semantic ID such as `hero-food` or
  `product-pack`;
- write `{{ref:hero-food}}` and `{{ref:product-pack}}` while authoring; the
  local prompt compiler converts them to BytePlus labels such as `[Image 1]`
  and `[Image 2]` after the final request order is known;
- after each reference, add a noun/clarifier, e.g. `[Image 2] product package`;
- never use `@Image1`; that syntax is rejected locally because it is not the
  provider label used by the official request examples;
- describe where the physical object appears in the scene;
- do not write raw asset IDs inside the prompt.

## Camera And Action Rules

- Specify only one camera movement per shot: fixed close-up, slow push-in,
  smooth lateral tracking, overhead cut, gentle handheld follow, or final hold.
- Avoid stacking push, pull, pan, orbit, and zoom in the same shot.
- Prefer slow, gentle, continuous cooking motion: steam rising, oil shimmering,
  sauce pouring, noodles loosening, tofu sliding, spatula stirring, plating.
- Avoid high-burst or physically strict motion unless a real video reference is
  supplied.
- Keep scene elements sparse: table/counter, pan/pot, stove, cutting board,
  knife, bowl/plate, product package, and physical logo prop.

## Text And Logo Constraints

Seedance can generate text, subtitles, slogans, and speech bubbles, so do not
leave the text policy implicit.

For our raw generated video:

- keep it subtitle-free;
- avoid any text or subtitles;
- no title cards, lower-thirds, ingredient labels, captions, sticker ads, or
  watermarks;
- no extra logos or platform marks;
- only the explicitly referenced real physical brand prop/package may show.

Add English captions, labels, BGM, and SFX later in ChatCut.

Avoid asking Seedance to generate subtitles for production cooking videos.
Model-generated subtitles are burned in, harder to edit, prone to spelling or
layout drift, and can fight the composition. The only exception is when the
task is explicitly a text-generation/text-layout test. Normal publishing
captions, labels, and subtitles belong in ChatCut, where they stay editable,
centered, white, and safe from platform UI.

## Continuity Strategy

Use the model's strengths:

- Images lock product appearance, scene style, and composition.
- Video references lock cooking rhythm, camera movement, and motion language.
- Audio references can lock music/ambience/timbre when audio is needed.

For multi-clip generation, request `return_last_frame: true` when supported and
use the previous clip's last frame as the next clip's first visual reference.
Still verify joins in post, because official guidance says extension/stitching
can show frame jumps and may need trimming/alignment in an editor.

The local runner downloads the returned frame, records it under
`video.continuity.last_frame_path`, and can prepend it to the next request with
`--continue-from-last-frame`. This improves control, but it does not replace a
visual join review.
