# Cooking Video Workflow

This is the single authority for original no-face cooking commercials. Do not
load old run notes unless something fails.

## Default chain

`three script beats -> three director-designed first frames -> three silent 6s Seedance clips -> ChatCut finish`

The first frames are generation references, not editing assets.

## Direct the three clips

Write one useful cooking beat per clip:

1. Product hook and first preparation action.
2. Main cooking or assembly transformation.
3. Finish, pack/plate, and branded result.

For each beat, decide before generating:

- the shot size and camera angle;
- the starting food/action state;
- the product and physical logo-sign placement;
- one camera movement;
- the intended end composition and handoff to the next clip.

Generate one `1080x1920` opening frame per clip with the configured image API.
Do not generate nine storyboard frames by default. Do not import the three
opening frames into ChatCut.

Use the official English logo:
`viral-social-remix/umall_logo/asian-grocer-online-powered-by-umall.png`.
Render it as a real printed tabletop sign with scene perspective, lighting,
shadow, and occlusion. Never use the Chinese-region logo or a floating overlay.

Keep the product, kitchen, hands/clothing, light, cookware, and color grade
consistent. No face. Product-package text and the physical logo sign are
allowed; other generated text, subtitles, labels, watermarks, and title cards
are forbidden.

## First-frame prompt

```text
Create opening frame [01/02/03] for a premium vertical no-face food commercial,
1080x1920. This frame begins clip [1/2/3] and depicts [starting action].

DIRECTOR: [shot size, camera angle, lens feel, composition].
CONTINUITY: preserve [product, package, kitchen, hands/clothing, cookware,
lighting, food state, color grade].
END INTENTION: the six-second shot should naturally arrive at [end composition].
LOGO PROP: reproduce the supplied ASIAN GROCER ONLINE / powered by UMALL logo
as a real tabletop sign with correct perspective, shadow, and occlusion.
NEGATIVE: face, extra fingers, warped tools, invented packaging, floating logo,
subtitles, captions, labels, title cards, lower-thirds, watermarks.
```

## Seedance motion prompt

Give each request only its matching opening frame. Let Seedance create the
intermediate motion.

```text
Begin exactly from the supplied opening frame. [Subject action].
Camera: [one restrained movement].
End with [specific composition/action state] so the next clip can begin cleanly.
Preserve the product, package, physical logo sign, kitchen, hands/clothing,
food identity, lighting, and color grade. Natural cooking physics. No face,
new objects, scene teleporting, subtitles, overlays, watermarks, or extra logos.
```

For every request: `6s`, `9:16`, `1080p`, `generate_audio: false`, and
`return_last_frame: true`.

Use only the first frame by default. When a join needs exact control, design the
prior endpoint or use its returned last frame as the next clip's opening
reference. Do not add extra still anchors merely for reassurance.

## Fast review

Review one strip covering all three clips. Check only:

- correct product and logo prop;
- no face or broken hands;
- believable food/action progression;
- usable join and no generated overlay text.

Retry only the failed clip.

## ChatCut finish

Import only the three accepted MP4 clips, in order. Never import opening frames,
product/logo references, contact sheets, or QA images.

Keep the coherent natural duration; do not force 18 seconds to 15. Add separate
editable tracks for agent-generated Japanese BGM and timed cooking SFX. Add the
user's voiceover only when supplied. Add editable English current-step captions
at the visual center: white, subtle dark stroke/shadow, no colored box.

Do one final visual/audio check and export. Use deeper QA or troubleshooting
only when that check finds a concrete defect.
