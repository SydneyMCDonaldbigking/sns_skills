# Cooking Video Workflow

Use this reference for original no-face cooking commercials.

## Fixed production contract

The recipe arc is:

`ingredients/product close-ups -> cooking process -> plated finished dish`

The generation chain is:

`9 separate storyboard PNGs -> 3 groups of 3 frames -> 3 silent Seedance clips x 6s -> ChatCut finish at the coherent duration`

Each 6-second Seedance clip gets exactly three ordered storyboard images:

- Frames `01-03` -> clip 1: product hook and pan setup.
- Frames `04-06` -> clip 2: fry, steam, and browning.
- Frames `07-09` -> clip 3: reveal, plating, and brand hero.

Never use one frame per clip, one three-frame request for the whole commercial,
or all nine frames in one Seedance request.

## Draw the nine frames

Use the configured image API, normally GPT Image 2, to create nine individual
portrait images at `1080x1920`. The contact sheet is only for human review; it
is not a Seedance input.

Frame 01 establishes the visual world from the product image, official logo,
and art direction. Create frames 02-09 as controlled edits of the preceding
frame while also supplying the product and official logo references. Keep the
same:

- kitchen surface, pan, plate, light direction, and color grade;
- hand model, sleeves, skin tone, and manicure;
- dumpling shape, scale, count, and cooked-state progression;
- product package, tabletop sign, and camera language.

Do not show a face. Hands and torso below the shoulders are allowed.

Use this nine-frame story:

01 Ingredient, seasoning, and product close-up; frozen dumplings and package,
with the physical company table sign already present.

02 The same hands arrange dumplings in the same pan.

03 Oil begins to sizzle; low macro angle, first appetizing movement.

04 Water enters the pan and steam rises naturally.

05 The same lid covers the pan; condensation and heat are plausible.

06 Lid lifts to reveal cooked dumplings; steam direction remains consistent.

07 Dumplings turn to reveal an even golden crisp base.

08 The same hands plate the dumplings with a clean, controlled motion.

09 Finished dish hero shot with company table sign and product package.

Every frame prompt must name its prior-frame reference, product reference, logo
reference, unchanged continuity anchors, exact new food state, camera framing,
and what must not change. Describe only one meaningful action change per frame.

## Logo as a photographed prop

Use:
`viral-social-remix/umall_logo/asian-grocer-online-powered-by-umall.png`

The sign must show the English-region lockup `ASIAN GROCER ONLINE` with small
`powered by UMALL`. Do not use the Chinese-region UMALL logo.

Draw it during storyboard generation as one real physical prop: a small
premium printed tabletop card on the cooking surface. Keep its proportions,
wording, placement, material, perspective, lighting, contact shadow, and
occlusion consistent. It must not become a floating corner logo, screen
overlay, sticker, subtitle, or end-card graphic.

Place the same sign visibly in at least one anchor of every three-frame group,
and in frame 09. If the logo is misspelled or the sign changes identity, reject
and regenerate that storyboard frame before calling Seedance. Perspective or
occlusion may change naturally with the camera; the prop identity may not.

## Image prompt skeleton

Write one prompt per file in `analysis/page-prompts/page-XX.md`:

```text
Create storyboard frame XX of 09, vertical 1080x1920, premium no-face food
commercial. Edit the supplied previous frame; also use the supplied product and
official logo references.

UNCHANGED: [kitchen, pan, hands/sleeves, lighting, dumpling count/shape,
package, physical tabletop logo sign, color grade].
CHANGE ONLY: [one cooking action or food-state transition].
CAMERA: [shot size, angle, lens feel, static or one simple move intention].
LOGO PROP: preserve the exact ASIAN GROCER ONLINE / powered by UMALL printed
tabletop sign as a real object with correct perspective, shadow, and occlusion.
NEGATIVE: face, extra fingers, warped utensils, floating objects, invented
packaging, impossible food physics, text overlays, subtitles, captions, title
cards, lower-thirds, labels, watermarks, or any additional brand.
```

Product-package text and the exact printed logo on the real sign are allowed.
All other visible text is forbidden: no subtitles, captions, title cards, lower-thirds, labels, or watermarks.

## Seedance requests

Use image-to-video with three ordered input frames per request. Treat them as
start, middle, and end anchors for one continuous six-second action.

For every request:

- duration: `6s`
- aspect ratio: `9:16`
- resolution: `1080p`
- audio: off / `generate_audio: false`
- continuity: preserve the supplied people-free set, food, package, and sign
- motion: natural hands, oil, steam, lid, utensils, and food physics
- camera: one restrained commercial movement; no scene teleporting

Do not ask Seedance to invent text, narration, music, or a new logo.

## ChatCut finish

Import the three accepted clips as separate editable items in order. If all
three clips join coherently, preserve the full sequence even when it is close
to 18 seconds. Trim only failed motion, duplicated action, awkward joins, or
dead time; never force the edit to 15 seconds.

Add these as separate editable tracks:

- the user's recorded English voiceover;
- commercial BGM generated by the agent;
- frying, sizzling, steam, lid, plating, and plate-contact SFX generated by
  the agent.

Add editable English step captions describing the action currently visible,
for example `PAN-FRY`, `ADD WATER`, `COVER & STEAM`, and `CRISP & SERVE`.
Place them at the visual center of the video in white, with a subtle dark
stroke or shadow, no colored box, and exact timing to the cooking step.

The no-text rule applies to storyboard and Seedance generation. These required
step captions are created only in ChatCut, so they remain editable.
Finish only after visual QA confirms continuity, food progression, hand anatomy,
package fidelity, exact logo-sign fidelity, duration, framing, and a clean audio
tail.
