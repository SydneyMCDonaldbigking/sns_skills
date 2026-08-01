# Image Provider

Use this file when generating or retrying images for the remix workflow.

## Default

- Provider: OpenRouter
- API key variable: `OPENROUTER_API_KEY`
- Model: `openai/gpt-image-2`
- Quality: `medium`
- Xiaohongshu size: `1152x1536`
- Instagram/Facebook size: `1152x1152`
- Video storyboard size: `1920x1080`
- Carousel API route: OpenRouter Image API
  `https://openrouter.ai/api/v1/images`, model `openai/gpt-image-2`, target
  platform `aspect_ratio`
- English vertical cooking video storyboard size: `1080x1920`
- English vertical cooking video API route: OpenRouter Image API
  `https://openrouter.ai/api/v1/images`, model `openai/gpt-image-2`, request
  size `1024x1536`, then the local runner reframes only `vertical-video`
  outputs to final `1080x1920`.
- Three-clip product/logo opening frames are always high-quality identity
  frames: run `scripts/run_openrouter_carousel.py --api-mode images --quality
  high --asset-id 01`, keep model `openai/gpt-image-2`, and include the
  supplied product image plus the official region logo as actual image
  references. Do not accept prompt-only generation for three-clip clip 1. If
  the generated sign is wrong, regenerate the whole image-model first frame.
  Single-10s commercials do not run this OpenRouter first-frame gate by
  default; pass product/page images directly to Seedance.

Allow local overrides with these environment variables:

- `VSR_IMAGE_PROVIDER`
- `VSR_IMAGE_MODEL`
- `VSR_IMAGE_API_MODEL`
- `VSR_IMAGE_API_MODE`
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
`qa/openrouter-cost.json`. Carousel production defaults to OpenRouter's
dedicated `/api/v1/images` endpoint with `aspect_ratio` set from the target
platform, because the chat-completions image route may return square images even
when a portrait size is requested.

For original English vertical cooking videos, the configured image API creates
selected director opening references on demand. Start with
`analysis/page-prompts/page-01.md` and generate only `generated/page-01.png`
before clip 1. For clips 2 and 3, inspect the accepted prior clip's returned
last frame first with `scripts/handoff_review.py`; use that frame directly when
it is coherent, or generate the corresponding `page-02`/`page-03` transition
opening anchor when the last frame is visually weak, malformed, blurry, or
awkward for the next action.

After each OpenRouter image run, inspect the JSON output. For three-clip clip 1
product-commercial frames, `generated[0].references` must list the product
image and official logo inputs. If it is empty, treat the result as invalid even
if the image looks plausible: fix the manifest/reference paths and rerun before
submitting Seedance. A model-invented package or logo is not an acceptable
identity reference. If the logo/sign is cropped, misspelled, replaced, or only
partly visible, tighten the prompt/reference placement and rerun high-quality
image generation. Never paste, composite, mask, track, or overlay the official
logo onto an otherwise bad first frame.

Use `scripts/run_openrouter_carousel.py --asset-id 01` for the clip 1 opening.
Use `--asset-id 02` or `--asset-id 03` only after the handoff decision requires
that slot. Seedance receives only the selected opening reference for each clip.
Opening PNGs, returned last frames, and transition anchors are generation
references and must not be imported into ChatCut.

For `vertical-video`, use OpenRouter's dedicated Image API instead of the
chat-completions image path. The request uses model
`openai/gpt-image-2` and provider-supported portrait size `1024x1536`; the
runner then stores the original under `generated-original-size/` and locally
reframes the delivered storyboard PNG to `1080x1920`. Carousel sizes and
horizontal video sizes are not changed by this rule. If the provider returns a
square image for `vertical-video`, stop and retry with the dedicated Image API
or a better vertical prompt instead of passing it to Seedance.

Use these optional overrides only for `vertical-video`:

- `VSR_VERTICAL_VIDEO_IMAGE_MODEL`
- `VSR_VERTICAL_VIDEO_IMAGE_ENDPOINT`

Seedance and OpenRouter Grok video are separate video handoffs. Load
`references/seedance-video.md` before running or instructing
`scripts/run_seedance_video.py`; load `references/openrouter-video.md` before
running or instructing `scripts/run_openrouter_video.py`. Neither video runner
changes carousel image generation.

## Request Defaults

Send one image request per asset with the resolved model and quality. Preserve
the exact in-image copy from `analysis/prompts.md`.

Include these headers when using OpenRouter:

- `Authorization: Bearer <OPENROUTER_API_KEY>`
- `Content-Type: application/json`

Use `VSR_IMAGE_ENDPOINT` when set. Otherwise use the provider's current image
generation endpoint from its official documentation. Do not guess a changed
endpoint during a live run; verify first if the request fails.
