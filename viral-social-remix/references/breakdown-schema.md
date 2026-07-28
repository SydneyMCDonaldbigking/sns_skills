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

Record `shot_id`, `soft_timing`, `narrative_role`, `cooking_state`, `shot`,
`camera_motion`, `motion_intent`, `text_policy`, `voiceover_or_audio`,
`continuity`, `reference_assets`, and `product_or_brand_cue`.

For this route, `text_policy` must be `no visible text, subtitles, captions,
title cards, lower-thirds, labels, or ingredient callouts`. Voiceover or natural
cooking audio may be planned separately.

Preferred Seedance 2.0 structure is three soft shots for a 5-6s preview:
opening ingredient/product setup, middle cooking transformation, and final
texture/plating/hero result. Do not treat `[0-2s]`, `[2-4s]`, `[4-6s]` as hard
timing constraints unless the user is intentionally testing timing obedience.

Use the nine recipe beats only as planning logic: ingredient/product close-up;
prep/cutting; hot pan/oil/aromatics; main ingredient into pan; core cooking;
sauce/product mechanism; texture close-up; plating; finished hero. Branding
must be a real physical prop, not a screen subtitle, floating sticker, overlay,
or ad banner. For English-region deliverables, `product_or_brand_cue` must name
`ASIAN GROCER ONLINE` with small `powered by UMALL`, and must not use the
Chinese-region UMALL logo.

## Assumptions

The product and brand are user-supplied. Audience, setting, benefits, and theme
may be inferred; store every inference as `{ "inferred": true, "value": ... }`.
