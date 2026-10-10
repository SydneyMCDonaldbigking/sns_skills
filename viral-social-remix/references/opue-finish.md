# Opue Finish

Post-production for every generated video. ChatCut is retired (2026-10-10):
logo, captions, step labels, product stickers, and the end card are drawn by the
local `Opue_video_add` engine, not by the video or image model.

- Engine repo: `OPUE_VIDEO_ADD_ROOT`, default `../test_opus/Opue_video_add`.
- Python: the `motion-video` conda env only (`D:/anaconda/envs/motion-video/python.exe`).
- **The agent is the editor** (user, 2026-10-10). The agent decides the
  headline angle, which ingredients to call out, which words to highlight, the
  per-step emoji, and whether to use a product sticker, from what it sees in the
  clips. It does not hand these choices back to the user; the user reviews the
  rendered cut.
- Opue's own `CLAUDE.md`, `templates/recipe/README.md`, and `styles/README.md`
  are the authority for its fields and kits. This note covers only the handoff
  from this skill.

## House rules (from Opue, user-confirmed)

- **No text from the generator**: generated frames and clips carry no logo,
  store sign, price, label, caption, or brand text. Opue draws every word and
  the logo in post, so the model never misspells them. The product package may
  appear as the real product, but its printed text is never the brand proof.
- **Two brands, chosen per video**: `umall` (red, English wordmark UMALL only,
  never 今日优选) or `asian_grocer` (AGO, green). Ask which one when the user
  has not said. Logos are always the full-colour transparent version: no white
  mono version and no white backing plate.
  - This replaces the combined `ASIAN GROCER ONLINE / powered by UMALL` lockup
    for video.
  - Carousels keep the combined lockup; see `brand-region-assets.md`.
- **English on screen**: captions, titles, labels, end card, and logo are
  English. Write text as `{en: ..}`. Use `{zh: ..}` / `--lang zh` only when
  the user asks for a Chinese version.
- **Facts only from the user or the package**: no prices, cook times, health
  claims, or "zero-fail" lines without a source.
- **Audio = native ambient sound only**: keep the clips' own cooking sound
  (`audio: {clips: true}`). No BGM, no voiceover, no dialogue.
  - Every video prompt ends with
    `soundscape: <ambient sounds>. No dialogue, no music.`
  - Use BGM only if the user explicitly supplies or asks for it.
- **A random style kit per video**: run `engine.pick <brand> --for
  projects/<name>`. It shuffles among the brand's least-used kits and never
  repeats the last one. Use a named kit only when the user names one.
- **Opening copy angle** goes in the big headline. The dish name goes in the
  kicker and the final title.
  - Easy dish: `10-Min Light Dinner`.
  - Beautiful dish: `Fine Dining at Home`.
  - Kid-friendly dish: `Make This for the Kids`.
- **Emoji follows content**:
  - The dish emoji goes in `emoji:`.
  - Each step gets its own ingredient emoji (`🍖`, `🫚`, `🥕`).
  - Don't use one kit emoji for the whole video.
- **Ingredients laid out in the opening shot** get `callouts` (`at` /
  `label` in 0-1 first-frame coordinates, plus `callouts: true` on the hook).
- **Static ingredient flat-lays are not generated as video**: the model
  invents ingredients. Use a still with `role: ingredients` and a post push-in.

## Handoff from a run

1. **Draft caption cues while clips generate.** Write
   `analysis/caption-cues/<clip>.json` with clip-relative `start`, `end`, and
   `text`. `<clip>` is `clip-01`..`clip-03`, `single-10s`, or the NewB label.
   - Text is 2-6 English words naming a visible action.
   - `*star*` marks the keyword to highlight.
   - Check the files with `scripts/caption_cues.py`.
2. **Accept clips** (handoff review, QA sheet). Only accepted MP4s go to Opue.
   Opening frames, returned last frames, and transition anchors never do.
3. **Draft the Opue project**:

   ```bash
   python scripts/opue_project.py output/<run> --brand asian_grocer \
     --title "Make This for the Kids" --kicker "Corn & pork rib soup" --emoji "🍲" \
     --trim clip-01=0.30:5.70 --trim clip-03=0.00:5.20
   ```

   - **What it writes**: `<opue>/projects/<ago|umall>_<title>/project.yaml`
     plus an untracked `roots.local.yaml` (`run: <run dir>`).
   - **What it records**: `opue_project` in the run manifest.
   - **Shot layout**:
     - A `hook` shot runs up to the first cue, the headline time.
     - Each clip becomes one `step` shot whose cues become `steps`
       (`at_s` + text).
     - The last `--cta-seconds` (default 2.2) of the final clip become the
       `cta` end card.
     - `continuous: true` means no automatic cut transitions, because handoffs
       were designed at generation.
4. **Edit as the editor.** Open every still the script wrote to
   `qa/opue-frames/`: the hook's first frame, one frame per step, and the end
   card. Then decide and write into `project.yaml` yourself:
   - tighten the step wording to what the picture shows;
   - add 1-2 `*keywords*` per step, also listed under `keywords`;
   - give each step its own ingredient `emoji`;
   - if the hook lays out ingredients, add `ingredients` with `at` / `label`
     in 0-1 coordinates of the hook still, plus `callouts: true` on the hook;
   - add a `product` sticker from the real product image when the run has one;
   - set `cta.search` to the dish or product name.

   Check every on-screen fact against the user or the package. Don't ask the
   user to fill these in.
5. **Render in the Opue repo**:

   ```bash
   python -m engine.pick asian_grocer --for projects/<name>
   python -m engine.preview projects/<name>            # one still per shot
   python -m engine.render  projects/<name> --sheet    # final + contact sheet
   ```

   Look at the preview stills yourself and fix anything cramped, mistimed, or
   covering the food before the full render. Text and timing changes only rerun
   locally; there is no GPU spend. Output goes to `projects/<name>/out/`.
6. **Check before handoff**, using the contact sheet and frame comparison:
   - cuts land on the intended frames;
   - the ambient sound has zero offset;
   - nothing freezes where the source moves;
   - stroked headline words never run together;
   - captions stay inside x 140-940.

   Then give the user the MP4 and the contact sheet. The user is the final
   reviewer.

## Do not

- Do not ask Seedance, NewB, or the image model for logos, signs, prices,
  captions, or packaging text.
- Do not add BGM, voiceover, or SFX stingers by default.
- Do not import generation references into the Opue project.
- Do not commit media, `out/`, `build/`, `roots.local.yaml`, server addresses,
  or keys in either repo.
