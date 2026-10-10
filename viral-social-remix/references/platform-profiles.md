# Platform Profiles

| Profile | Language | Asset size | Asset count | Caption |
|---|---|---:|---|---|
| Xiaohongshu source to English carousel | Natural English | 1152x1152 | Match source page count | `caption-en.txt` |
| Xiaohongshu target carousel | Chinese | 1152x1536 | Match source page count | `caption-zh.txt` |
| Instagram/Facebook carousel | Natural English | 1152x1152 | Match source page count | `caption-en.txt` |
| English vertical product/cooking video | Natural English | 9:16 video, 1080p; optional opening frames 1080x1920 | single 10s Seedance clip, 3 ambient-sound 6s Seedance clips, or one NewB 30s take | `caption-en.txt` |
| Video storyboard | Target-market language | 1920x1080 | exactly 9 frames plus one 1920x1080 contact sheet | Target-platform caption |

Use an explicit user target platform when supplied. Otherwise infer source and
target separately: a Xiaohongshu URL identifies the source/capture workflow, not
the output language. Company remix/"搬运" defaults to the English-region carousel
profile: natural English, `1152x1152`, `caption-en.txt`, platform
`instagram-facebook`, and the `ASIAN GROCER ONLINE / powered by UMALL` logo.
Use the Chinese Xiaohongshu target profile only when the user explicitly asks
for Chinese-region or Chinese Xiaohongshu output. Ask only when target
confidence is low.

For video, map the selected frames to Hook, setup, pain, product, mechanism,
benefit, proof, result, and CTA. Do not use nine evenly spaced frames as the
final selection; inspect candidates and choose narrative nodes.

For English vertical product/cooking video, use platform `vertical-video`,
vertical `9:16`, and choose one of two routes before generation:

- **Single 10s route**: for drinks, snacks, pantry products, office rituals,
  or any simple one-setting product-use story. Pass the product/page image
  directly to Seedance as the opening reference and visual bible. Generate one
  `10s`, `1080p` multi-shot clip with 4-6 timed beats and ambient sound only.
  The product must be recognisable in the opening shot; do not force package
  continuity later.
- **Three 6s route**: for cooked products, large location changes, stove/heat,
  steamer/fire, visible transformation, or when reroll control matters. Use one
  selected `1080x1920` opening reference per ambient-sound 6s Seedance request.
  Generate clip 1's opening reference first; for clips 2 and 3, run
  `scripts/handoff_review.py` on the accepted prior clip before deciding whether
  to use the returned last frame directly or generate a transition opening
  anchor for a cleaner camera bridge.

Both routes need real commercial shot variety, close-up inserts, and motivated
cuts; do not rely on single-take prompts. Include stove/heat/steamer/cooking
appliance action when the product requires cooking. Generated frames carry no
logo, sign, or text. Build `qa/decision-sheet.html`, then finish only accepted
MP4 clips in `Opue_video_add` (`opue-finish.md`): `scripts/opue_project.py`
drafts the project, and Opue draws the `umall` or `asian_grocer` logo, English
headline, step captions, and end card. Preserve a natural edit duration. Audio
is the clips' ambient sound only: no BGM or voiceover unless the user asks.
Hand the rendered MP4 and contact sheet to the user for review.
