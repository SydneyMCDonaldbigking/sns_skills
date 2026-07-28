# Original Cooking Video Memory

Use this for original English cooking or recipe videos.

## Story Arc

The video should feel original and useful, not like a stitched ad. The reliable
recipe arc is:

1. Ingredient, seasoning, or product close-up.
2. Prep or cutting.
3. Hot pan, oil, aromatics, or first cooking action.
4. Main ingredient enters the pan.
5. Core stir-fry/cooking process.
6. Sauce, seasoning, or product mechanism.
7. Texture/doneness close-up.
8. Plating.
9. Finished dish hero with company table sign, logo prop, or packaging.

For IG-style English food taste, read
[[aesthetic-library/no-face-asian-cooking-style]] before drafting storyboard
prompts. Recent IG samples show that frame 01 should still satisfy the fixed
ingredient/product role, but should be framed like a sensory hook: tight,
food-first, tactile, and already delicious-looking rather than a flat
ingredient inventory.

## Preferred Seedance Structure

For new Seedance 2.0 cooking tests, do not default to nine separate still
storyboard frames. Use the official compact shot-sequencing style from
[[seedance-official-prompting]].

For a 6-second visual test, write three soft shot beats:

1. `Shot 1, opening third`: ingredient/product close-up and first food action.
2. `Shot 2, middle third`: main cooking transformation.
3. `Shot 3, final third`: texture, plating, or finished hero.

Use the nine recipe arc beats above as planning material, not as nine forced
visual inputs. Only create nine storyboard frames when the user explicitly asks
for that legacy route or when a source-remake needs many still anchors.

## Text Policy

Storyboard frames and final video should have no visible subtitles, title
cards, lower-thirds, ingredient labels, stickers, or ad banners.

Branding can appear as a real physical object in the scene, especially frame 01
and frame 09. For English-region output, use the `ASIAN GROCER ONLINE` lockup
with small `powered by UMALL`.

Do not rely on Seedance or Grok to redraw the company logo accurately. Video
models often warp brand text and lockups even when a correct logo reference is
provided. If the logo must be exact, generate the cooking video with product
packaging or a non-critical brand prop only, then composite the official PNG in
ChatCut/post onto a real scene surface with matched perspective, tracking,
occlusion, lighting, and texture. It should read as a printed table card,
package face, or sign—not a floating logo bug. Use a clean end card only when
that is the declared brand strategy. Treat AI-generated physical logo signs as
review-only, not final brand-fidelity assets.

## Continuity

Keep the same kitchen, lighting, cookware, dish, product packaging, and physical
brand prop across all shots. The food state must progress logically from raw
ingredients to finished dish.

Use more real references when product fidelity matters:

- product/package image;
- physical English-region logo/sign prop;
- finished dish or first-frame mood image;
- source/reference cooking video for rhythm and camera movement when available.

## Handoff

Prepare a compact Seedance prompt and Manifest v2 first, review the real
reference assets, then dry-run the compiled request before handing off to
Seedance with `viral-social-remix/scripts/run_seedance_video.py`.

For Seedance, use the `visual-preview` profile for a 5-second no-audio pass
before paying for a longer final. After generation, run
`viral-social-remix/scripts/video_qa.py prepare`; do not hand off to ChatCut
until a human records `approve`.
The mapo tofu test showed that sparse food-motion scenes work much better than
rigid mechanical motion. Keep the set minimal, the motion controlled, the
camera language simple, and the brand sign physical. See
`seedance-video-generation.md` and `seedance-official-prompting.md` for cost,
prompting, and QA rules.

After Seedance produces accepted MP4 clips, continue through
[[chatcut-handoff-workflow]] when the user wants the video imported for editing,
clip ordering, BGM, subtitle labels, review, or export. Prefer importing split
Seedance clips as separate editable ChatCut items instead of only importing one
stitched MP4.
