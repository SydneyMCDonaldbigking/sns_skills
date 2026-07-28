# Cooking Video Workflow

Use this reference when the user asks for an original cooking, recipe, stir-fry,
meal-prep, sauce, pantry, or kitchen-process video instead of remixing an
existing source post.

## Creative Contract

Create one coherent short English vertical cooking video from a
brand/product/recipe brief. The required structure is fixed:
ingredients/product close-ups -> cooking process -> plated finished dish with a
company table sign, logo prop, or packaging. The preferred Seedance 2.0 path is
a compact multimodal prompt with a small set of real references, not a forced
nine-still storyboard. Use product/package images, an English-region physical
logo/sign reference, and a source/motion reference video when available; then
ask Seedance to generate the final `9:16` cooking video with three ordered shot
beats.

The output should feel like a real social cooking clip, not a slideshow. Keep
food physics, heat, steam, oil, sauce thickness, utensil movement, and ingredient
state changes plausible.

The final video must be Douyin/TikTok vertical at `9:16`. If reference stills
are generated for this route, they must be portrait `1080x1920` and must not
reuse square carousel sizing.

## Recipe Beat Map

Use these nine beats as planning material for the recipe logic. Do not force
all nine beats into a 5-6 second Seedance clip.

01 Ingredient, seasoning, and product close-up on a clean prep table; company logo/signage or packaging may appear only as a real physical prop.
02 Main ingredient prep or cutting.
03 Cookware, hot oil, and aromatics starting.
04 Main ingredient goes into the pan.
05 Core cooking action: stir-fry, sear, simmer, or boil.
06 Seasoning, sauce, or product is added to show the flavor mechanism.
07 Doneness and texture close-up proving the dish is appetizing.
08 Plating process.
09 Finished dish hero shot with company table sign, logo prop, or packaging beside it; no visible subtitles or on-screen text.

## Preferred 6-Second Seedance Shot Plan

For a short Seedance preview, compress the recipe beat map into three soft
shots. Use timing labels only as pacing guidance:

Shot 1, opening third / approximately 0-2s: ingredient, seasoning, product, and
physical brand prop close-up in one clean cooking setup; begin the first food
action.

Shot 2, middle third / approximately 2-4s: main cooking transformation, such as
oil shimmering, aromatics blooming, ingredient entering the pan, sauce pouring,
or a gentle stir-fry. Use one camera movement only.

Shot 3, final third / approximately 4-6s: appetizing texture close-up, plating,
or finished dish hero. The physical English-region logo/sign/packaging may
appear beside the dish. Hold the final hero long enough for review.

For this original vertical video route, do not put any text in the generated
frames or final video: no subtitles, captions, title cards, lower-thirds, labels,
or ingredient callouts. Write any platform caption, script, or voiceover plan in
natural English outside the video file. Voiceover and natural cooking audio are
allowed when the selected video model supports audio.

Company branding may appear in frames 01 and 09 only as a real object in the
scene: a table sign, printed logo prop, product packaging, apron patch, or
similar physical item. Do not turn the logo into a screen subtitle, floating
sticker, overlay, or ad banner.

For English-region cooking videos, the physical brand prop must use the
`ASIAN GROCER ONLINE` lockup with small `powered by UMALL`, from
`viral-social-remix/umall_logo/asian-grocer-online-powered-by-umall.png`.
Do not use the Chinese-region UMALL logo in English-region videos. The logo's
real printed lockup is allowed only as part of the physical prop; no added
subtitles, ingredient labels, title cards, lower-thirds, stickers, or screen
text are allowed.

Important brand-fidelity rule: do not expect a video model to redraw the exact
company logo. Product packaging may be generated from references. When final
brand accuracy matters, composite the official PNG onto a real scene surface
in ChatCut/post as a perspective-matched table card, package face, sign, or
other physical prop. Preserve scene perspective, motion tracking, occlusion,
lighting, and texture so it remains part of the photographed world. A clean
brand end card is a separate explicit strategy. Never solve logo accuracy with
a floating corner bug or sticker-like overlay. AI-rendered physical logo signs
are acceptable only for rough review, and fail QA if the logo shape or wording
does not match the source asset.

## Storyboard Image Prompt Rules

Use this section only when still reference frames are needed. The default
Seedance 2.0 route should use a compact prompt plus real product/logo/motion
references.

Each `analysis/page-prompts/page-XX.md` prompt should specify vertical
composition at `1080x1920`:

- Continuity anchors: dish, kitchen, cookware, surface, lighting, plate, product packaging, hand model if used.
- The frame's exact cooking state and food transformation.
- Camera: angle, lens feel, motion intention for Seedance, and whether it is a macro, overhead, medium, or hero shot.
- Text: always "no in-image text".
- Negative constraints: no subtitles, captions, title cards, lower-thirds,
  labels, floating logo overlays, sticker-like ad badges, impossible ingredient
  jumps, extra brand names, deformed hands, floating utensils, or unreadable
  packaging.

Prefer one consistent kitchen environment over unrelated beauty images.
Lock recurring props and packaging. Avoid fake flames, unsafe handling, and
unrealistic amounts of steam or splatter.

## Seedance Prompt Rules

Write `analysis/seedance-prompt.md` as one direct video-generation prompt:

- Start with the finished intent: dish, platform, pacing, visual style, and duration.
- Specify vertical short-video delivery: `9:16`, `1080x1920` storyboard,
  usually 5s for the first pass.
- Include three shot beats in order for a 5-6s preview. Use the nine recipe
  beats only as source planning.
- Describe one camera movement per shot: fixed close-up, slow push-in, smooth
  lateral tracking, overhead cut, gentle handheld follow, or final hold.
- Ask for continuity across cookware, ingredients, product packaging, lighting,
  and physical brand prop.
- Refer to manifest assets with semantic placeholders such as
  `{{ref:product-pack}}`; let the runner compile them to `[Image 1]`,
  `[Video 1]`, and other final provider labels.
- Specify realistic food physics and avoid sudden ingredient teleporting.
- Forbid all visible text overlays and subtitles. If narration is useful,
  include an English voiceover plan or voiceover tone, but keep the video image
  clean.

Do not ask Seedance to invent a different recipe after reference assets have
been selected. The Seedance prompt should animate the chosen product, logo,
food, and motion references.
