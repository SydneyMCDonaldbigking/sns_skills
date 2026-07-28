# Breakdown Schema

## Image page

Record `page_id`, `page_role`, `composition`, `subject`, `text_hierarchy`,
`palette`, `viral_hook`, `transition`, and `replacement_mapping`. Preserve the
page count and explain how each page advances the carousel.

## Video frame

Record `frame_id`, `timestamp`, `narrative_role`, `shot`, `on_screen_text`,
`continuity`, and `replacement_mapping`. The nine `narrative_role` values must
cover the required story functions even when the source order differs.

## Original cooking video frame

Record `frame_id`, `clip_group`, `narrative_role`, `cooking_state`, `shot`,
`camera_motion`, `motion_intent`, `text_policy`, `continuity`,
`reference_assets`, and `product_or_brand_cue`.

For this route, `text_policy` must be `no visible text, subtitles, captions,
title cards, lower-thirds, labels, or ingredient callouts`. Voiceover or natural
cooking audio may be planned separately.

Create exactly nine storyboard frames and group them as `01-03`, `04-06`, and
`07-09`. Each group becomes one silent 6s Seedance clip and every request
receives its three separate ordered images. Branding must be the same real
physical tabletop sign drawn in the storyboard, not a screen subtitle, floating
sticker, overlay, or ad banner. For English-region deliverables,
`product_or_brand_cue` must name `ASIAN GROCER ONLINE` with small
`powered by UMALL`, and must not use the Chinese-region UMALL logo.

## Assumptions

The product and brand are user-supplied. Audience, setting, benefits, and theme
may be inferred; store every inference as `{ "inferred": true, "value": ... }`.
