# ChatCut Post-Generation Handoff

Use this only after the generated MP4 clips have passed a visual review.

## Fast path

1. Create or reuse the intended ChatCut project at the delivery canvas.
2. Import only the accepted generated MP4 segments.
3. Place the clips on V1 in script order with no accidental gaps.
4. Preserve the coherent natural duration. Trim only failed motion,
   repetition, awkward joins, or dead time.
5. Generate and place BGM as an editable track when requested. Add voiceover
   only when supplied or requested. Do not add cooking Foley/SFX unless the user
   explicitly asks and a visible action justifies it.
6. Add editable English current-step captions in the visual center: white,
   subtle dark stroke/shadow, no colored box.
7. Review representative opening, join, and ending frames once; check the
   audio tail; export.

## Asset boundary

Never import these into ChatCut:

- director first frames or storyboards;
- transition opening anchors or returned last-frame references;
- product/package reference images;
- logo reference files;
- contact sheets, review strips, or QA images;
- raw API responses.

They are generation references, not timeline media.

## Brand rule

The official physical `ASIAN GROCER ONLINE / powered by UMALL` tabletop sign
needs to read in clip 1's opening reference / first frame only. Preserve it
when it naturally remains visible, but do not force it back into later stove,
steam, pouring, plating, or close-up inserts. Do not add a floating logo
overlay. Repair the sign in post only when visual review finds a real fidelity
defect in a frame where the sign is supposed to appear.

## Verification

Read the timeline once after placement and once after the finishing pass.
After export, verify the actual file's dimensions, duration, video/audio
streams, opening, joins, ending, and audio tail. Use deeper debugging only
after a concrete failure.

Do not store import tokens, editor boot tokens, signed URLs, OAuth data, or
authorization codes in this note.
