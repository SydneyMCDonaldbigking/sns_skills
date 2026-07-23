# Cooking Video Workflow

Use this reference when the user asks for an original cooking, recipe, stir-fry,
meal-prep, sauce, pantry, or kitchen-process video instead of remixing an
existing source post.

## Creative Contract

Create one coherent short English vertical cooking video from a
brand/product/recipe brief. The required structure is fixed:
ingredients/product close-ups -> cooking process -> plated finished dish with a
company table sign, logo prop, or packaging. The first production artifact is a
nine-frame vertical storyboard generated with GPT Image 2 at `1080x1920`;
Seedance then uses the storyboard and a motion prompt to produce the final
`9:16` cooking video.

The output should feel like a real social cooking clip, not a slideshow. Keep
food physics, heat, steam, oil, sauce thickness, utensil movement, and ingredient
state changes plausible.

## Nine-Frame Shot Map

Use exactly nine storyboard frames unless the user explicitly asks for another
structure.

01 Ingredient, seasoning, and product close-up on a clean prep table; company logo/signage or packaging may appear only as a real physical prop.
02 Main ingredient prep or cutting.
03 Cookware, hot oil, and aromatics starting.
04 Main ingredient goes into the pan.
05 Core cooking action: stir-fry, sear, simmer, or boil.
06 Seasoning, sauce, or product is added to show the flavor mechanism.
07 Doneness and texture close-up proving the dish is appetizing.
08 Plating process.
09 Finished dish hero shot with company table sign, logo prop, or packaging beside it; no visible subtitles or on-screen text.

For this original vertical video route, do not put any text in the generated
frames or final video: no subtitles, captions, title cards, lower-thirds, labels,
or ingredient callouts. Write any platform caption, script, or voiceover plan in
natural English outside the video file. Voiceover and natural cooking audio are
allowed when the selected video model supports audio.

Company branding may appear in frames 01 and 09 only as a real object in the
scene: a table sign, printed logo prop, product packaging, apron patch, or
similar physical item. Do not turn the logo into a screen subtitle, floating
sticker, overlay, or ad banner.

## Storyboard Image Prompt Rules

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

Prefer one consistent kitchen environment over nine unrelated beauty images.
Lock recurring props and packaging. Avoid fake flames, unsafe handling, and
unrealistic amounts of steam or splatter.

## Seedance Prompt Rules

Write `analysis/seedance-prompt.md` as one direct video-generation prompt:

- Start with the finished intent: dish, platform, pacing, visual style, and duration.
- Specify vertical short-video delivery: `9:16`, `1080x1920` storyboard,
  usually 5s for the first pass.
- Include the nine beats in order, using shot numbers.
- Describe motion between beats: pan, push-in, overhead cut, toss, sauce pour, steam rise, plating, final hold.
- Ask for continuity across cookware, ingredients, product packaging, lighting, and hand model.
- Specify realistic food physics and avoid sudden ingredient teleporting.
- Forbid all visible text overlays and subtitles. If narration is useful,
  include an English voiceover plan or voiceover tone, but keep the video image
  clean.

Do not ask Seedance to invent a different recipe after GPT Image 2 has produced
storyboard frames. The Seedance prompt should animate and connect the storyboard.
