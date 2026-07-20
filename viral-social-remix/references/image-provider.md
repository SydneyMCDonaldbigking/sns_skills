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

## Request Defaults

Send one image request per asset with the resolved model and quality. Preserve
the exact in-image copy from `analysis/prompts.md`.

Include these headers when using OpenRouter:

- `Authorization: Bearer <OPENROUTER_API_KEY>`
- `Content-Type: application/json`

Use `VSR_IMAGE_ENDPOINT` when set. Otherwise use the provider's current image
generation endpoint from its official documentation. Do not guess a changed
endpoint during a live run; verify first if the request fails.
