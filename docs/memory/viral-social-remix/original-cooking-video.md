# Original Cooking Video Memory

The single production specification is:
`../../../viral-social-remix/references/cooking-video-workflow.md`.

Relationship map:
[[video-production-map]].

Current default:

`clip 1 opening anchor -> clip 1 Seedance -> inspect last motion strip -> direct handoff or transition opening anchor -> clip 2 -> repeat for clip 3 -> ChatCut finish`

For clips 2 and 3, use the prior returned last frame directly only when it is a
clean handoff. If the last frame is weak, blurry, malformed, or awkward for the
next action, generate a transition opening anchor with the image model. The
anchor must design a camera bridge such as match action, steam/lid/pour/object
occlusion, plate movement, rack focus, or texture insert. Retry the prior clip
only when no honest bridge can be made.

First frames, product/logo references, contact sheets, and QA images are
generation-only assets. Import only accepted MP4 clips into ChatCut.

Do not duplicate the full workflow in memory notes.
