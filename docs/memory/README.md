# SNS Skill Memory

This repository is now an Obsidian vault. Open this folder in Obsidian:

```text
C:\Users\uryuu\Desktop\sns_skill
```

The memory source of truth lives in `docs/memory/`. It is for stable workflow
rules, mistakes that should not repeat, model/provider decisions, and reusable
production checklists.

## Start Here

- `viral-social-remix/index.md`: daily operating memory for the social remix skill.
- `viral-social-remix/chatcut/README.md`: ChatCut product map, editing themes,
  low-model execution contract, prompt recipes, and finishing QA.
- `../retrospectives/`: incident-level writeups after a painful run.
- `inbox/`: temporary notes that still need to be cleaned up.

## Agent Rule

Before doing a `viral-social-remix` task, read:

1. `viral-social-remix/SKILL.md`
2. `docs/memory/viral-social-remix/index.md`
3. Any route-specific memory linked from that index.

After a successful run, add `output/<run>/qa/run-notes.md` from the template and
distill anything reusable back into `docs/memory/viral-social-remix/`.

## Hygiene

Never put these into memory notes:

- API keys, `.env.local`, Authorization headers, or full request logs.
- Base64 image payloads or vendor raw responses.
- Private source images copied into Markdown attachments.
- Anything from `output/*/raw/`, unless it is summarized without secrets.

Use paths and short summaries instead. Markdown is the memory; any future Milvus
or vector database should index only these notes and sanitized run summaries.
