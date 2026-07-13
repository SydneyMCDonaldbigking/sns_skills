# Product Reference Cache

Use this file when visible product packaging matters, especially for Umall /
今日优选 food, pantry, grocery, haul, restock, and delivery-box creatives.

## Goal

Prevent fake Chinese/Japanese/Korean packaging text by grounding visible products
in real SKU images.

## Low-token capture

- Prefer the brand's official product/category pages.
- Capture only 4-10 relevant SKUs for a theme.
- Store only: product name, product URL, image URL, local image path, category,
  captured date, and short usage notes.
- Do not paste long product descriptions, page dumps, or full catalog text into
  analysis files.
- Save downloaded product images under `data/product-cache/<brand>/`; this path
  is local cache and must stay ignored by git.

## Generation rules

- Feed 2-4 real product images as references per generated asset.
- Visible front-facing packaging must come from reference images.
- Do not ask the image model to invent readable packaging labels.
- If a product is not referenced, show it back-facing, side-facing, cropped,
  partially covered, or background-blurred.
- Let the model generate lifestyle scene, hands, delivery box, lighting, and
  platform copy; keep product packaging faithful to references.
- If the model still creates fake packaging text, regenerate with fewer visible
  products or composite real packshots after generation.

## Umall quick path

For Umall pantry/grocery tests, start with one category page such as:

- `https://www.umall.com.au/collections/pantry`

Extract product anchors and image attributes from the visible product grid. For
Shopify lazy images, prefer `currentSrc`; otherwise replace `{width}` in
`data-src` with `640`.
