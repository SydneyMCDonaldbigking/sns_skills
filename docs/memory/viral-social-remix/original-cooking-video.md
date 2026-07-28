# Original Cooking Video Memory

Current company production rule for original no-face cooking commercials:

`9 API-generated storyboard frames -> 3 groups of 3 -> 3 silent Seedance clips x 6s -> ChatCut finish at the coherent duration`

This rule overrides the older compact one-prompt/three-soft-shot experiment.
Each Seedance request receives three separate ordered images as its start,
middle, and end anchors:

1. `01-03`: product hook and pan setup.
2. `04-06`: frying, steam, lid, and cooking transformation.
3. `07-09`: crisp reveal, plating, and finished hero.

Create the official `ASIAN GROCER ONLINE` with small `powered by UMALL`
tabletop sign inside the storyboard image API pass as the same real physical
prop. Do not ask Seedance to invent it and do not default to a floating
post-production logo overlay.

Maintain the same no-face hand model, sleeves, kitchen, cookware, light,
dumplings, package, and sign across all nine frames. Generate each later frame
as an edit of the preceding frame with the product and logo references still
attached.

The single canonical specification is:
`../../../viral-social-remix/references/cooking-video-workflow.md`.
Do not duplicate its shot list or prompt template here.

After generation, import the three clips separately into ChatCut. Do not force
18 seconds down to 15 seconds when the sequence is coherent; trim only defects,
repetition, awkward joins, or dead time.

Add the user-recorded voiceover. The agent generates and mixes the BGM and
cooking SFX. Add editable English current-step captions at the visual center:
white type, subtle dark stroke/shadow, no colored box, timed to the action.
