# Self-Distillation

The goal is to make repeated production work lighter without turning the repo
into a messy diary.

## What To Distill

Distill lessons when they are reusable:

- The user corrected the workflow.
- A model/provider behaved differently than expected.
- A validation or visual QA failure reveals a repeatable rule.
- A prompt pattern consistently improves or damages output.
- A platform route needs a guardrail.

## What Not To Distill

Do not promote one-off preferences, raw assets, private data, full prompts with
embedded image data, or anything that belongs only to one campaign.

## Cadence

After a run:

1. Write `output/<run>/qa/run-notes.md`.
2. If the lesson is reusable, update the relevant memory note.
3. If the lesson is large or painful, write a dated retrospective.
4. Run the distill script to rebuild the summary:

```powershell
python viral-social-remix/scripts/distill_memory.py --write
```

## Future Milvus Rule

Milvus should index sanitized Markdown memory and run summaries only. It should
not become the source of truth, and it should never index `.env.local`,
`output/*/raw/`, source images, generated images, or full API payloads.
