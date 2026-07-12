# Image Provider

Use this file when generating or retrying images for the remix workflow.

## Default

- Provider: OpenRouter
- API key variable: `OPENROUTER_API_KEY`
- Model: `openai/gpt-image-2`
- Quality: `medium`
- Xiaohongshu size: `2048x1152`
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

## Request Defaults

Send one image request per asset with the resolved model and quality. Preserve
the exact in-image copy from `analysis/prompts.md`.

Include these headers when using OpenRouter:

- `Authorization: Bearer <OPENROUTER_API_KEY>`
- `Content-Type: application/json`

Use `VSR_IMAGE_ENDPOINT` when set. Otherwise use the provider's current image
generation endpoint from its official documentation. Do not guess a changed
endpoint during a live run; verify first if the request fails.
