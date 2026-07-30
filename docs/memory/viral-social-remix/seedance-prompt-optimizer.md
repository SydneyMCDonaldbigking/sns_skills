---
tags:
  - seedance
  - prompt-optimizer
  - teaching-distillation
aliases:
  - Seedance Prompt Optimizer
  - sd2-pe Distillation
updated: 2026-07-30
source_material:
  - new_base/general-sd2-skills (1).md
---

# Seedance Prompt Optimizer

This note distills the raw teaching material in
`new_base/general-sd2-skills (1).md`. Keep the raw file as lesson material; use
this note as the Obsidian memory node.

## What It Is

The source is a Seedance 2.0 prompt optimizer pattern, not a production video workflow.
It teaches how to turn vague, adjective-heavy, or asset-confused user requests
into structured Seedance prompts.

For current production, follow:

- [[video-production-map]] for the relationship map;
- [[viral-social-remix/references/cooking-video-workflow|Cooking Video Workflow]]
  for the company cooking-commercial contract;
- [[seedance-official-prompting]] for official/provider prompting notes.

## Optimizer Flow

1. Classify intent before rewriting: new generation, edit, extension/stitching,
   or text/layout generation.
2. Decide whether the scene is static/fine-control or dynamic/reference-driven.
3. For vague requirements, ask only for missing facts that materially affect
   generation.
4. Check the eight core elements: subject, action, setting, light/tone, camera,
   visual style, quality, and constraints.
5. Detect reference ambiguity, raw asset IDs, long/collage images, and camera
   movement conflicts before paid generation.
6. Output the optimized result as `Optimized prompt`, `Optimization`, and
   `Relevant principles` when the user asks for prompt optimization.

## Local Syntax Rule

The teaching file uses `@Image N` examples. In this repository, final provider
prompts use local labels such as `[Image 1]`, `[Image 2]`, `[Video 1]`, and
`[Audio 1]`.

Keep the principle, not the literal teaching syntax:

- map assets by request order;
- explain each label immediately, e.g. `[Image 1] (product package)`;
- never leave raw `asset-xxx` IDs as the action subject;
- do not use `@Image1` in provider-bound prompts.

## Ask Before Changing

Do not silently modify user intent. Ask or present concrete choices when any of
these are unclear:

- who or what the subject is;
- which image controls first frame, last frame, identity, left/right placement,
  or background;
- whether a long image, contact sheet, 9-grid, or collage needs splitting;
- whether stacked camera moves should become one primary move;
- whether a video edit target is add, remove, modify, extend, stitch, or text.

## Editing And Stitching

For editing-style prompts, name the operation, time range, spatial position, and
target object/person. For extension or stitching, describe the transition. For
text-generation tests, name exact text, timing, placement, and appearance.

Normal company cooking videos remain no-face and text-free in raw generation;
add captions, labels, and BGM later in ChatCut only when requested.

## Guardrails

- Use one primary camera movement per time slice unless a compatible combo is
  deliberately chosen.
- Add quality/detail constraints and anti-distortion constraints.
- For complex multi-person front-facing dynamic scenes, use strong orientation
  and clothing constraints plus fixed camera control.
- Treat this as prompt-quality memory. It does not override the three-clip
  handoff rule: bad returned last frames need generated transition opening
  anchors, not literal continuation.
