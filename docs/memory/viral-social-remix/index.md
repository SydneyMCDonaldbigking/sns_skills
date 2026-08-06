# Viral Social Remix Memory

This is the first page to read after `viral-social-remix/SKILL.md`.

## Non-Negotiables

- If the user says the original post is already open, use the live browser tab
  first and capture the source package before analysis.
- Default company remix/"搬运" output is English-region. A Xiaohongshu URL or
  Chinese source post is only the source/capture platform unless the user
  explicitly asks for Chinese-region or Chinese Xiaohongshu target output.
- Keep source page count, page order, and page role unless the user explicitly
  asks to change them.
- A supplied phone screenshot is not automatically the source. If the user says
  it is for the final page, use it only for the final CTA/search/app page.
- For image/carousel posts with commerce intent, do not forget the final
  shopping guide page. If the source/original has a purchase/app-entry page,
  localize that exact page structure into the English region. If the user
  supplies real English app search screenshots, use them inside the final guide
  page with the English-region `ASIAN GROCER ONLINE powered by UMALL` logo. Do
  not finish the carousel until the final shopping handoff is present, or the
  user explicitly waives it.
- Carousel generation is API-only for production. Do not fall back to local
  composite pages when `--api-only` is selected.
- Keys come only from `.env.local` or environment variables and must never be
  written into Git, prompts, docs, or logs.
- After generation, run validation and build/review a contact sheet.

## Route Memory

- [[video-production-map]]: relationship map for the current Seedance video
  chain, transition anchors, provider notes, visual taste, and ChatCut handoff.
- `chinese-xhs-remix.md`: Chinese Xiaohongshu target-only/source-drift rules.
- [[openrouter-image-generation]]: current image API/model/cost rules.
- [[original-cooking-video]]: original cooking video structure and text policy.
- [[seedance-video-generation]]: Seedance video cost, preview, and QA rules.
- [[seedance-official-prompting]]: official Seedance 2.0 prompt-writing notes:
  compact shot sequencing, multimodal references, camera motion, and text/logo
  constraints.
- [[seedance-prompt-optimizer]]: distilled `new_base` lesson for optimizing
  vague prompts, multimodal asset mapping, no-silent-modification rules, and
  editing/stitching prompt structure.
- [[openrouter-grok-video-generation]]: low-cost Grok/OpenRouter 720p video
  smoke tests using `GROK_OPENROUTER_API_KEY`.
- [[aesthetic-library/README]]: English-region IG/Reels food taste memory,
  recent-year pattern studies, no-face cooking style, subtitle/BGM preferences,
  and product integration rules.
- [[chatcut/README|ChatCut editing memory]]: confirmed editor capability map,
  low-model execution contract, theme playbooks, Agent prompt recipes, and QA
  discipline.
- [[chatcut-handoff-workflow]]: after Seedance/video generation, import
  generated MP4 segments into ChatCut as an editable timeline; then handle BGM,
  subtitle labels, review, and export when requested.
- [[run-notes-template]]: copy this into `output/<run>/qa/run-notes.md`.
- [[self-distillation]]: how to promote run lessons into this vault.

## Video Chain

For original cooking video work, use
`../../../viral-social-remix/references/cooking-video-workflow.md` as the only
production contract. Use [[video-production-map]] as the Obsidian relationship
map. Read aesthetic memory only when defining a new visual direction and
[[chatcut-handoff-workflow]] only after the generated MP4 clips pass review.

Provider research remains available in [[seedance-video-generation]] and
[[seedance-official-prompting]], but it does not override the company contract.

Do not treat Seedance as the end of the workflow when the user is talking about
剪辑, 串视频, BGM, subtitles, labels, review, or export.

## Image Carousel Rule

For image/carousel posts, do not rely on a saved taste library. Use the user's
source post, supplied screenshots, or a clearly selected competitor/reference
post as the visual and pacing reference, then rebuild it with our product
assets, English-region logo, and platform size.

For default company remix/"搬运" from a Xiaohongshu or Chinese source, rebuild
as an English-region carousel: `1152x1152`, `caption-en.txt`, and the
`ASIAN GROCER ONLINE / powered by UMALL` lockup. Do not use the Chinese UMALL
logo or `caption-zh.txt` unless the requested target is explicitly Chinese.

Preserve source page count, page order, and page roles unless the user asks for
a new structure. If the source ends with a shopping/category/search/app-entry
guide, remake that final guide page for the English region instead of inventing
a generic CTA.

## Latest Lessons

- 2026-07-23: Do not judge Chinese by PowerShell mojibake. Verify with UTF-8
  reads, browser text, OCR, or visual inspection.
- 2026-07-23: OpenRouter chat-completions image route can ignore portrait size
  and return square images. Prefer `/api/v1/images` with `openai/gpt-image-2`.
- 2026-07-23: For Seedance 2.0, start with a 5s no-audio preview. Food motion
  is viable; exact conveyor-style mechanical physics is not reliable.
- 2026-07-23: For the winter drinks remix, pages 1-5 came from the original
  Xiaohongshu post. Only page 6 used the real UMALL mobile Drinks screenshot.
- 2026-07-25: After Seedance, use ChatCut for editable clipping/review. Prefer
  importing generated segments as separate V1 items; use the stitched MP4 only
  as quick review or when a single clip is requested.
- 2026-07-25: For cooking-video finishing in ChatCut, English labels/subtitles
  may reference the original video's pacing/style, but wording and BGM should be
  based on our generated video. Trim BGM to the exact video duration; no long
  music tail after the final frame.
- 2026-07-25: For cheap video API smoke tests, use OpenRouter Grok with
  `GROK_OPENROUTER_API_KEY`, `x-ai/grok-imagine-video`, 720p, 9:16, no audio,
  and a one-second first-frame test before spending on longer clips.
- 2026-07-25: For English carousels based on Chinese commerce/source posts, the
  last page should be an English shopping guide modeled on the original page,
  not a forgotten afterthought. Use the original guide layout as reference and
  place real English app/search results inside it.
- 2026-07-25: For English IG-style food videos, recent high-performing samples
  favor food-first close-ups, one-pan/lazy/time-saving hooks, sparse props,
  stable camera angles, and centered white post-production text. Generated
  storyboard/video frames still stay text-free; add labels/subtitles in ChatCut.
- 2026-07-26: Clear the saved image/carousel taste library. For graphically
  designed posts, reference the original/source or a chosen competitor post
  directly instead of improvising a house style from memory.
- 2026-07-28: Company cooking-commercial production uses the three-clip
  director route. Generate clip 1's opening anchor first; for clips 2 and 3,
  inspect the prior last frame and final motion strip before choosing the next
  opening anchor. Opening anchors stay outside ChatCut.
- 2026-07-28: A ChatCut theme is not a font/filter preset. Teach execution
  models each theme as audience promise + emotion + rhythm + proof, and force
  Structure, Continuity, Rhythm, Text, Motion, Audio, Brand, then visual/export
  QA instead of decorating an unverified rough cut.
- 2026-07-28: Make video generation manifest-driven. Compile semantic
  `{{ref:id}}` tokens to provider labels only after reference ordering, run
  official-limit preflight before spend, save a sanitized request lock/hash,
  use no-audio preview profiles, persist returned last frames for continuation,
  and require explicit human visual approval before ChatCut/export.
- 2026-07-30: For the three-clip Seedance route, do not use a bad returned last
  frame literally. Inspect the last motion strip; use a clean last frame
  directly, generate a transition opening anchor when the endpoint is weak, and
  retry the prior clip only when no honest bridge can be made.
- 2026-08-04: Approved Sauce and Orange final shopping pages worked only after
  treating the last page as a high-quality OpenRouter operation tutorial:
  left step panel, right dominant real phone screenshot, glossy red numbered
  arrows, small basket/crate, English-region logo, and three references
  together: real phone screenshot, original/source guide style reference, and
  brand lockup. Do not deliver local composite shopping guides as final when a
  polished last page is expected.

## Useful Links

- `../../retrospectives/2026-07-23-chinese-remix-source-drift.md`
- `../../../viral-social-remix/references/shopping-guide-page.md`
- `../../../viral-social-remix/references/image-provider.md`
- `../../../viral-social-remix/references/cooking-video-workflow.md`
- [[video-production-map]]
- [[seedance-video-generation]]
- [[seedance-official-prompting]]
- [[openrouter-grok-video-generation]]
- [[chatcut/README|ChatCut editing memory]]
- [[chatcut-handoff-workflow]]
