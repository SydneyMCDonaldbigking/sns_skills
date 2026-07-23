# Image Provider

Use this file when generating or retrying images for the remix workflow.

## Default

- Provider: OpenRouter
- API key variable: `OPENROUTER_API_KEY`
- Model: `openai/gpt-5.4-image-2`
- Quality: `medium`
- Xiaohongshu size: `1152x1536`
- Instagram/Facebook size: `1152x1152`
- Video storyboard size: `1920x1080`
- English vertical cooking video storyboard size: `1080x1920`

Allow local overrides with these environment variables:

- `VSR_IMAGE_PROVIDER`
- `VSR_IMAGE_MODEL`
- `VSR_IMAGE_QUALITY`
- `VSR_IMAGE_ENDPOINT`

## Secret Handling

Never commit API keys, local `.env` files, generated requests containing
authorization headers, or vendor responses that echo secrets. Read keys from the
environment or an ignored local file only.

If the API key is missing, stop image generation and ask the user to set
`OPENROUTER_API_KEY`. Continue non-generation tasks such as analysis, prompts,
captions, manifests, and contact sheets.

For carousel production runs, Codex should prepare the run directory but should
not upload company source media, brand assets, app screenshots, or prompts from
the Codex environment. The OpenRouter upload still happens, but it happens from
the user's local terminal through the runner:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_openrouter_carousel.py --run output/xxx --api-only --concurrency 2
```

The runner loads `OPENROUTER_API_KEY` only from `.env.local` or the local
environment, caps concurrency at two requests, writes raw responses under
`raw/`, generated PNGs under `generated/`, and cost metadata under
`qa/openrouter-cost.json`.

For original English vertical cooking videos, use the same GPT Image 2 path to generate
exactly nine `1080x1920` storyboard frames before any Seedance call. The
prepared video run uses `analysis/page-prompts/page-01.md` through `page-09.md`;
the local runner writes `generated/page-01.png` through `page-09.png` and a
vertical 3x3 storyboard overview.

Seedance is a separate video handoff. Load `references/seedance-video.md` before
running or instructing `scripts/run_seedance_video.py`.

## Request Defaults

Send one image request per asset with the resolved model and quality. Preserve
the exact in-image copy from `analysis/prompts.md`.

Include these headers when using OpenRouter:

- `Authorization: Bearer <OPENROUTER_API_KEY>`
- `Content-Type: application/json`

Use `VSR_IMAGE_ENDPOINT` when set. Otherwise use the provider's current image
generation endpoint from its official documentation. Do not guess a changed
endpoint during a live run; verify first if the request fails.
