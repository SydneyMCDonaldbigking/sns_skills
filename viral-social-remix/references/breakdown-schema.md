# Breakdown Schema

## Image page

Record `page_id`, `page_role`, `composition`, `subject`, `text_hierarchy`,
`palette`, `viral_hook`, `transition`, and `replacement_mapping`. Preserve the
page count and explain how each page advances the carousel.

## Video frame

Record `frame_id`, `timestamp`, `narrative_role`, `shot`, `on_screen_text`,
`continuity`, and `replacement_mapping`. The nine `narrative_role` values must
cover the required story functions even when the source order differs.

## Assumptions

The product and brand are user-supplied. Audience, setting, benefits, and theme
may be inferred; store every inference as `{ "inferred": true, "value": ... }`.
