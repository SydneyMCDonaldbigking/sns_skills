# Platform Profiles

| Profile | Language | Asset size | Asset count | Caption |
|---|---|---:|---|---|
| Xiaohongshu source to English carousel | Natural English | 1152x1152 | Match source page count | `caption-en.txt` |
| Xiaohongshu target carousel | Chinese | 1152x1536 | Match source page count | `caption-zh.txt` |
| Instagram/Facebook carousel | Natural English | 1152x1152 | Match source page count | `caption-en.txt` |
| English vertical product/cooking video | Natural English | 9:16 video, 1080p; optional opening frames 1080x1920 | single 10s Seedance clip or 3 silent 6s Seedance clips | `caption-en.txt` |
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
  silent `10s`, `1080p` multi-shot clip with 4-6 timed beats. Product/logo
  readability is required only in the opening shot; do not force logo/package
  continuity later.
- **Three 6s route**: for cooked products, large location changes, stove/heat,
  steamer/fire, visible transformation, or when reroll control matters. Use one
  selected `1080x1920` opening reference per silent 6s Seedance request.
  Generate clip 1's opening reference first; for clips 2 and 3, run
  `scripts/handoff_review.py` on the accepted prior clip before deciding whether
  to use the returned last frame directly or generate a transition opening
  anchor for a cleaner camera bridge.

Both routes need real commercial shot variety, close-up inserts, and motivated
cuts; do not rely on single-take prompts. Include stove/heat/steamer/cooking
appliance action when the product requires cooking. Finish only accepted MP4
clips in ChatCut. Preserve a coherent sequence and natural edit duration; do not
force a fixed final length. ChatCut is a second editing pass when needed:
run `scripts/edit_plan.py`, split/trim weak moments, punch in on
product/steam/pour/details, reframe with subtle digital camera movement, and
use motivated short transitions when they improve rhythm. Build
`qa/decision-sheet.html` before handoff. Do not run an agent-owned final
acceptance pass; hand off the editable project/export to the user for review.
Add agent-generated BGM and editable white centered English current-step
captions when requested. Do not generate or place cooking SFX by default.
