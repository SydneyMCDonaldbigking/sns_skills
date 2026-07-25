# ChatCut Post-Generation Editing Workflow

Use this after Seedance or another video model has generated cooking/social MP4
clips and the next step is to bring them into ChatCut for editable cutting,
review, ordering, trimming, and final export.

ChatCut is already installed locally. Do not start by reinstalling it.

## Memory Links

- Start from [[index]] for the route map.
- Comes after [[seedance-video-generation]] when MP4 clips are ready.
- For original recipe structure and brand/no-text rules, also read
  [[original-cooking-video]].
- This note covers both plain import and later ChatCut finishing: editable clip
  ordering, BGM, subtitles/labels, review, and export.

## Fast Path: Generated Video To Editable Timeline

After video generation finishes:

1. Collect the generated MP4 outputs from the run directory.
2. Prefer importing the individual generated segments as separate ChatCut assets
   and sequential V1 timeline items. This keeps the edit adjustable at segment
   boundaries.
3. Use a stitched MP4 only as a quick review/reference asset, or when the user
   explicitly asks to import the already stitched final as one clip.
4. Create a new ChatCut project with the final platform canvas.
   - Douyin/TikTok vertical: `1080x1920`.
   - Use `30fps` in ChatCut unless a specific project needs otherwise.
5. Import local MP4 files through ChatCut's media import flow.
6. Place clips on `V1` in order, starting at frame `0`, with no gaps unless
   intentionally requested.
7. Do not add subtitles, title cards, lower-thirds, text, logos, music,
   voiceover, overlays, transitions, or effects unless the user explicitly asks.
8. Verify the timeline state and return the editor URL for review.

If the user says they want to "串视频剪辑", "接上剪辑", "导入剪辑",
"进 ChatCut", "后面剪一下", "加 BGM", "加字幕", "加英文标签", or "导出",
this is the note to follow after generation.

For the oyakodon split-video run, the preferred editable imports are:

```text
C:\Users\uryuu\Desktop\sns_skill\output\20260725-oyakodon-fixed-view-remake\generated\seedance-oyakodon-clip-a-0-5s-noaudio.mp4
C:\Users\uryuu\Desktop\sns_skill\output\20260725-oyakodon-fixed-view-remake\generated\seedance-oyakodon-clip-b-5-11s-noaudio.mp4
C:\Users\uryuu\Desktop\sns_skill\output\20260725-oyakodon-fixed-view-remake\generated\seedance-oyakodon-clip-c-11-17s-noaudio.mp4
```

Reference-only stitched file:

```text
C:\Users\uryuu\Desktop\sns_skill\output\20260725-oyakodon-fixed-view-remake\generated\seedance-oyakodon-stitched-17s-noaudio.mp4
```

## If ChatCut Tools Are Not Visible

For a fresh generated MP4 or segment set, create a new Codex task in the same
`sns_skill` project if this task cannot see `mcp__chatcut__*` tools. Newly
installed plugin tools may not hot-load into the current task.

Reusable new-task prompt:

```text
ChatCut is already installed and authenticated in this Codex desktop app.
Please verify the ChatCut MCP/tools are available in this new task, then create
a new editable ChatCut project from these local no-audio vertical generated
video clips:

<absolute local mp4 path 1>
<absolute local mp4 path 2>
<absolute local mp4 path 3>

Put them on V1 in this order, starting at frame 0, as separate editable timeline
items with no intentional gaps. Do not add captions, subtitles, title cards,
lower-thirds, dialogue, logos, visible text, music, voiceover, overlays,
transitions, or effects. Open or return the ChatCut editor/project URL when
ready, and report any blocker clearly. Use ChatCut plugin skills and MCP tools
if available.
```

After the new task starts:

1. Verify ChatCut MCP tools are visible.
2. Create a `1080x1920`, `30fps` project.
3. Open the editor handoff URL in the in-app browser when possible.
4. Import local MP4s with ChatCut's `import_media` session plus the bundled
   `asset-import/scripts/upload-media.mjs` helper. The helper supports up to
   four local file paths per import session.
5. Place uploaded video assets on `V1` in order.
6. Read `V1` again to verify placement, order, frame starts, durations, and
   absence of unexpected extra items.
7. Return the clean editor URL.

## What Happened On 2026-07-25

Goal: after Seedance generation, bring the no-audio vertical oyakodon video into
ChatCut for editing/review.

Source video:

```text
C:\Users\uryuu\Desktop\sns_skill\output\20260725-oyakodon-fixed-view-remake\generated\seedance-oyakodon-stitched-17s-noaudio.mp4
```

Result:

- ChatCut plugin was available as `chatcut@chatcut-inc`, version `0.2.20`.
- New Codex task created so the freshly installed plugin could load cleanly.
- New ChatCut project created at `1080x1920`, `30fps`.
- The stitched review MP4 was uploaded as one editable video asset and placed on
  `V1` at frame 0.
- No captions, subtitles, title cards, lower-thirds, logos, overlays, dialogue,
  or visible text were added.

Lesson: for future post-generation editing, import the three segment clips as
separate V1 timeline items when the user wants real editing flexibility. Import
the stitched MP4 only for quick review or if the user asks for a single clip.

Project record:

- ChatCut project id: `a596a26f-8cf0-4212-b110-871cd067f13b`
- Editor link:
  `https://app.chatcut.io/editor/a596a26f-8cf0-4212-b110-871cd067f13b?chatcutLaunchClient=codex_app&chatcutLaunchSurface=ext_browser`
- Timeline item id: `9f5a3cf272`
- Asset id: `6cc6928d-9e14-4a83-94d7-9f2d2fbcadfb`
- Timeline duration: `514` frames
- New Codex task id: `019f9725-7b96-7b52-9f4f-cad4458cc4c0`

## Oyakodon Finishing Pass: Audio + English Subtitles

After the editable import, the user asked to generate audio and subtitles using
the local Instagram Japanese food sample only as a reference:

```text
C:\Users\uryuu\Desktop\sns_skill\samples\ig_japanesefood
```

The folder contained one reference video:

```text
C:\Users\uryuu\Desktop\sns_skill\samples\ig_japanesefood\japanese_sample.mp4
```

Important interpretation:

- Use the reference video for pacing, subtitle style, and broad food-reel
  language only.
- Do not reuse or copy the reference audio.
- English labels/subtitles may reference the original video's timing, rhythm,
  and style, but the final wording must match our generated video frames.
- Base the final audio/BGM on our generated video itself, not on the reference
  video's audio.
- BGM duration should align to the video duration. Do not leave long music tails
  beyond the final frame.
- English-only subtitles were requested.
- The source generated MP4 had no audio track, so there was no original speech
  to preserve or transcribe.

Reference inspection:

- `japanese_sample.mp4`: `544x960`, `30fps`, about `17.6s`, with mono AAC audio.
- Oyakodon source: `1080x1920`, about `17.125s`, no audio.
- The reference subtitle style was bold white English ingredient labels with a
  second Japanese line. For this run, keep only the English line.
- Local frame contact sheets showed the oyakodon visual beats:
  sauce pour, sugar, chicken/onions, egg pour, over rice, green onions.

Final edit strategy:

1. Keep the imported video unchanged on `V1`.
2. Generate original no-vocal BGM with ChatCut `submit_music` based on the
   generated video mood and timing, not local audio editing and not
   reference-audio reuse.
3. Do not generate TTS unless the user explicitly asks for spoken narration.
   For a no-audio food B-roll clip, a warm no-vocal BGM bed is the safer default.
4. Use a reusable ChatCut Motion Graphic as the English subtitle/ingredient label
   template. The label timing/style can follow the reference video, but label
   content must describe the generated video. This keeps the text editable and
   avoids inventing transcript data.
5. Place subtitle MG instances on `V2`, one per visual beat, with per-instance
   `captionText` overrides.
6. Place generated music on `A1`, trimmed to the exact video duration with fade
   in/out. If the generated BGM is longer than the video, cut it at the final
   video frame and fade out there.
7. Verify timeline structure with `read_project`, and verify representative
   subtitle frames with `view_timeline_frames` plus pixel inspection.

Reusable subtitle labels for this oyakodon structure:

```text
Soy Sauce
Brown Sugar
Chicken & Onions
Beaten Eggs
Over Rice
Green Onions
```

Subtitle visual style:

- Reusable Motion Graphic asset.
- Natural box around the label, not a full-screen graphic.
- Font: `Playfair Display` from ChatCut `search_fonts`.
- Large white serif text, bold, with shadow/stroke for contrast.
- No Japanese line, no title card, no logo, no lower-third.

Music generation prompt shape:

```text
Original upbeat background music for a <exact video duration>-second vertical
Japanese home-cooking reel. Match the pacing and visual energy of our generated
video. Warm, appetizing, light percussion, soft plucked strings, gentle lo-fi
groove, bright kitchen energy, no vocals, no spoken words, not a copy of any
reference track, supportive under food preparation visuals. The music should end
cleanly with the video duration.
```

Final project/timeline record:

- ChatCut project id: `a596a26f-8cf0-4212-b110-871cd067f13b`
- Timeline id: `8891b0da-4665-4ba5-92aa-d0716d09abf7`
- Canvas: `1080x1920`, `30fps`
- Renderable duration: `514` frames
- Clean editor link:
  `https://app.chatcut.io/editor/a596a26f-8cf0-4212-b110-871cd067f13b?chatcutLaunchClient=codex_app&chatcutLaunchSurface=ext_browser`

Tracks after finishing:

- `V1`: original imported video asset `6cc6928d9e`, item `9f5a3cf272`,
  frames `0-514`.
- `V2`: six editable subtitle Motion Graphic items using asset `012c3324fa`:
  - `f319d51176`, frames `0-74`, `Soy Sauce`
  - `034c591e21`, frames `74-150`, `Brown Sugar`
  - `d6ca2f884f`, frames `150-255`, `Chicken & Onions`
  - `06c147ff93`, frames `255-350`, `Beaten Eggs`
  - `46cd425d23`, frames `350-435`, `Over Rice`
  - `138787ad5a`, frames `435-514`, `Green Onions`
- `A1`: generated original BGM asset `1f51eeecb4`, item `dd51e0362e`,
  frames `0-514`, with `0.25s` fade in, `1s` fade out, and `-4dB`
  adjustment.

Verification results:

- `V1` still had exactly one original video item, unchanged, frames `0-514`.
- `V2` covered frames `0-514` with no subtitle gaps.
- `A1` covered frames `0-514`, ending exactly with the video.
- Representative frame inspection confirmed the longest label,
  `Chicken & Onions`, fit without overflow.
- Ending frame inspection confirmed `Green Onions` stayed in the safe area.

Do not store import session tokens, editor boot tokens, signed render-frame URLs,
OAuth URLs, or authorization codes in this note.

## Honey Butter Chicken ChatCut Finishing: 30fps Export Pitfall

On 2026-07-25, the Grok honey butter chicken stitched source was:

```text
C:\Users\uryuu\Desktop\sns_skill\output\20260725-171158-honeybutter-chicken-grok-remake\generated\grok-honeybutter-chicken-stitched-15s-1080x1920-noaudio.mp4
```

ChatCut project:

```text
https://app.chatcut.io/editor/9c12cd52-d065-4136-849c-35ae0d5e2cb1?chatcutLaunchClient=codex_app&chatcutLaunchSurface=ext_browser
```

Final local export:

```text
C:\Users\uryuu\Downloads\honey-butter-chicken-chatcut-audio-labels-15s.mp4
```

Finishing choices:

- Kept the generated MP4 as the only V1 video source.
- Generated one tasteful no-vocal ChatCut BGM track and trimmed it to the
  final video.
- Generated one subtle 15s cooking Foley bed instead of many separate SFX.
- Added editable white centered English label Motion Graphics on V2.
- Used `Poppins`, white fill, light black stroke/shadow, and no colored box.

Important pitfall:

- The imported Grok source was `1080x1920`, `24fps`, `15.125s`, and `363`
  source frames.
- Creating/placing it as `363` frames and exporting from ChatCut produced a
  wrong `12.08s` file, because the renderer treated the timeline frame time as
  `30fps`.
- For this run, the correct 15s export used a `30fps` export and `453`
  renderable frames. The video item was stretched to `453` frames with
  `playbackRate: 0.8013245033112583`, and the 15s Foley item was stretched to
  `450` frames with `playbackRate: 0.8`.
- Always run `ffprobe` on the downloaded export. Confirm `1080x1920`, duration
  around the intended video length, and an AAC audio track before reporting done.

Do not deliver the earlier 12s export from this run:

```text
C:\Users\uryuu\Downloads\honey-butter-chicken-chatcut-audio-labels.mp4
```

## Troubleshooting Only: Install/Auth Recipe

Use this section only if ChatCut disappears from the machine or authentication
expires. For normal runs, start from the fast paths above.

First read the official setup page:

```text
https://chatcut.io/chatgpt
```

On this Windows desktop app, the `codex.exe` under `C:\Program Files\WindowsApps`
returned `Access is denied`. Use the app-server bundled CLI instead:

```powershell
& C:\Users\uryuu\.codex\plugins\.plugin-appserver\codex.exe --version
```

Expected version observed:

```text
codex-cli 0.146.0-alpha.3.1
```

The official page mentioned a marketplace JSON URL, but this CLI build expects a
local path, Git repo, HTTPS Git URL, or SSH Git URL for `marketplace add`.
Working command:

```powershell
& C:\Users\uryuu\.codex\plugins\.plugin-appserver\codex.exe plugin marketplace add https://github.com/ChatCut-Inc/agent-plugin.git --ref main --json
```

Then install the plugin:

```powershell
& C:\Users\uryuu\.codex\plugins\.plugin-appserver\codex.exe plugin add chatcut@chatcut-inc --json
```

Then authenticate:

```powershell
& C:\Users\uryuu\.codex\plugins\.plugin-appserver\codex.exe mcp login chatcut
```

Do not store OAuth URLs, authorization codes, import tokens, editor boot tokens,
or signed media URLs in memory notes.

## Important Loading Quirk

The current task may not hot-load newly installed or newly authenticated ChatCut
tools. In the setup run, plugin files and config were present, but
`mcp__chatcut__*` tools appeared only in a newly created Codex task.

If ChatCut tools are missing after install/auth:

1. Create a new Codex task in the same `sns_skill` project.
2. Tell the new task that ChatCut was just installed and authenticated.
3. Ask it to verify ChatCut MCP tools, then do the import/editing work.

Codex app rule: only create that new task after the user explicitly asks for a
new task or confirms that the generated video should be handed to a new task for
ChatCut import.

Use the fast-path new-task prompt at the top of this note.

## ChatCut Import Flow

When the new task can see `mcp__chatcut__*` tools:

1. Load ChatCut plugin basics and asset-import guidance.
2. Create a project with the final target canvas.
   - For TikTok/Douyin-style vertical video: `compositionWidth=1080`,
     `compositionHeight=1920`.
   - Use `fps=30` for ChatCut timeline unless there is a specific reason to
     match another frame rate.
3. Open the returned editor handoff in the Codex in-app browser.
4. Call `import_media` with `action: create_session`.
5. Run the plugin's `asset-import/scripts/upload-media.mjs` helper with the
   returned import session data and the local MP4 path.
6. Read the timeline state with `read_project`.
7. Place the uploaded video asset on `V1` at frame `0` with `edit_item`.
8. Read the `V1` track again to verify exactly what was placed.
9. Return the clean editor URL to the user. Strip Codex-only editor boot
   parameters from any user-facing link.

Use the plugin helper for file upload/import. Do not replace this with local
ffmpeg composition or a flattened workaround when the goal is an editable
ChatCut timeline.

## Verification Checklist

Before reporting done:

- ChatCut MCP tools were visible in the task doing the work.
- Project canvas is `1080x1920` for vertical video.
- Source MP4 exists and was imported as a media asset.
- Timeline has the intended item on `V1`, starting at frame `0`.
- For a simple handoff/import task, there should be no extra captions, text,
  logos, overlays, audio, or generated elements.
- Report project id, editor URL, asset id, item id, and any known limits.

## Useful Installed Paths

ChatCut plugin cache:

```text
C:\Users\uryuu\.codex\plugins\cache\chatcut-inc\chatcut\0.2.20
```

Important skill files:

```text
C:\Users\uryuu\.codex\plugins\cache\chatcut-inc\chatcut\0.2.20\skills\chatcut-plugin-basics\SKILL.md
C:\Users\uryuu\.codex\plugins\cache\chatcut-inc\chatcut\0.2.20\skills\asset-import\SKILL.md
```
