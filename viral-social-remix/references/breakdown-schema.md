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

Record `frame_id`, `narrative_role`, `cooking_state`, `shot`, `motion_intent`,
`text_policy`, `voiceover_or_audio`, `continuity`, and `product_or_brand_cue`.
For this route, `text_policy` must be `no visible text, subtitles, captions,
title cards, lower-thirds, labels, or ingredient callouts`. Voiceover or natural
cooking audio may be planned separately. Use the fixed nine-frame structure:
01 ingredient/seasoning/product close-up on a clean prep table with optional
physical company logo/signage/packaging prop; 02 main ingredient prep or
cutting; 03 cookware, hot oil, and aromatics starting; 04 main ingredient into
the pan; 05 core cooking action; 06 seasoning/sauce/product added for flavor
mechanism; 07 doneness/texture close-up; 08 plating process; 09 finished dish
hero shot with company table sign, logo prop, or packaging beside it and no
visible subtitles or on-screen text. Branding must be a real physical prop, not
a screen subtitle, floating sticker, overlay, or ad banner. For English-region
deliverables, `product_or_brand_cue` must name `ASIAN GROCER ONLINE` with small
`powered by UMALL`, and must not use the Chinese-region UMALL logo.

## Assumptions

The product and brand are user-supplied. Audience, setting, benefits, and theme
may be inferred; store every inference as `{ "inferred": true, "value": ... }`.
