---
tags:
  - video
  - post-production
  - opue
aliases:
  - Opue Finish
updated: 2026-10-10
---

# Opue Finish Workflow

ChatCut was retired on 2026-10-10. Video post-production is the local
`Opue_video_add` engine. The contract is
[[viral-social-remix/references/opue-finish|Opue Finish]]; this note only
records why the switch happened and how it connects to the video chain.

## Why

- Opue draws every word and the logo in code, so generated video never has to
  spell brand text. Misspelled or cropped generated signs were the biggest
  rejection reason for opening frames.
- Text, timing, and style changes rerun locally in minutes with no GPU or API
  spend.
- Its style kits give Reels-native captions (word-by-word pop, keyword
  highlight, step badges, end card with search box). They rotate per video so
  the feed does not look the same every time.

## User decisions (2026-10-10)

- Generated frames carry no logo, sign, price, or brand text; Opue draws it all.
  The product Identity Gate keeps checking the product only.
- Video brand is `umall` or `asian_grocer`, chosen per video. The combined
  `ASIAN GROCER ONLINE / powered by UMALL` lockup stays for carousels.
- Audio is native ambient sound only (cooking sounds). Prompts end with
  `soundscape: ... No dialogue, no music.` There is no BGM by default.
- The agent is the main editor. It decides the ingredient callouts, keyword
  highlights, per-step emoji, and product sticker from the clip stills, renders
  the video, and hands it over. These choices are not left for the user to
  fill in.

## Chain

`accepted MP4 clips + analysis/caption-cues/*.json -> scripts/opue_project.py -> engine.pick -> engine.preview -> engine.render --sheet -> user review`

Generation references stay out of the Opue project. That means opening
anchors, transition anchors or returned last-frame references,
product/package references, contact sheets, and QA strips.

Related: [[video-production-map]], [[original-cooking-video]].
