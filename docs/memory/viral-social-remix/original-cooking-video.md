# Original Cooking Video Memory

Use this for original English cooking or recipe videos.

## Story Arc

The video should feel original and useful, not like a stitched ad. The reliable
arc is:

1. Ingredient, seasoning, or product close-up.
2. Prep or cutting.
3. Hot pan, oil, aromatics, or first cooking action.
4. Main ingredient enters the pan.
5. Core stir-fry/cooking process.
6. Sauce, seasoning, or product mechanism.
7. Texture/doneness close-up.
8. Plating.
9. Finished dish hero with company table sign, logo prop, or packaging.

## Text Policy

Storyboard frames and final video should have no visible subtitles, title
cards, lower-thirds, ingredient labels, stickers, or ad banners.

Branding can appear as a real physical object in the scene, especially frame 01
and frame 09. For English-region output, use the `ASIAN GROCER ONLINE` lockup
with small `powered by UMALL`.

## Continuity

Keep the same kitchen, lighting, cookware, dish, product packaging, and hand
model across all nine frames. The food state must progress logically from raw
ingredients to finished dish.

## Handoff

Generate nine vertical storyboard frames first, review them, then hand off to
Seedance with `viral-social-remix/scripts/run_seedance_video.py`.

For Seedance, run a 5-second no-audio preview before paying for a longer final.
The mapo tofu test showed that sparse food-motion scenes work much better than
rigid mechanical motion. Keep the set minimal, the motion controlled, and the
brand sign physical. See `seedance-video-generation.md` for cost and QA rules.

After Seedance produces accepted MP4 clips, continue through
[[chatcut-handoff-workflow]] when the user wants the video imported for editing,
clip ordering, BGM, subtitle labels, review, or export. Prefer importing split
Seedance clips as separate editable ChatCut items instead of only importing one
stitched MP4.
