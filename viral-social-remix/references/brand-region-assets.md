# Brand Region Assets

Use this reference whenever a deliverable needs a visible company logo, product
packaging cue, or brand lockup.

## Video (since 2026-10-10)

Videos are branded only in post by `Opue_video_add` (`opue-finish.md`). Each
video picks one brand. Ask the user which one when it is not given.

| Brand | Opue id | Logo | Colours |
|---|---|---|---|
| Umall | `umall` | English wordmark `UMALL` only (never 今日优选) | red `#DB3A35`, yellow `#FAAD14` |
| Asian Grocer Online | `asian_grocer` | AGO wordmark | green `#149474`, mint `#7FD3B8` |

- The logo files live in the Opue repo (`brands/<id>/logo.png`) and are always
  the full-colour transparent version: no white mono logo, no white backing
  plate, no floating sticker made outside Opue.
- Generated frames and clips carry no logo, store sign, price card, or brand
  text. Do not pass a logo to the image or video model and do not ask for a
  table sign. A frame where the model invented a logo or sign is rejected and
  regenerated.
- Do not paste, composite, mask, or track a logo onto generated footage
  yourself. Opue draws the logo badge, headline, step captions, product sticker,
  and end card in post.
- All on-screen video text is English unless the user asks for a Chinese
  version (`--lang zh`).

## Carousels: English Region

- Visible brand: `ASIAN GROCER ONLINE`
- Lockup: `ASIAN GROCER ONLINE`, with small `powered by UMALL`
- Logo file: `viral-social-remix/umall_logo/asian-grocer-online-powered-by-umall.png`
- Use for English Instagram/Facebook carousels, shopping-guide pages, and
  Xiaohongshu source posts remixed into English.

## Carousels: Chinese Region

- Visible brand: UMALL Chinese-region logo
- Logo file: `viral-social-remix/umall_logo/umall_logo.png`
- Use only for Chinese-region or Chinese Xiaohongshu deliverables.

## Carousel Placement Rules

- Do not use the Chinese-region UMALL logo for English-region deliverables.
- Do not turn either logo into subtitles, labels, lower-thirds, stickers,
  floating overlays, or ad banners.
- When a carousel page shows the lockup inside a scene, the image model
  generates it from the official logo reference with scene perspective, shadow,
  and partial occlusion. Never use a floating corner overlay, and never accept a
  model-written approximation of the English lockup as "close enough".
  - If the lockup text or region is wrong, tighten the prompt and regenerate
    the page with high-quality image generation.
  - Do not hand-patch the logo in Photoshop, scripts, or any local editor.
