# Shopping Guide Page

Use this reference for the final shopping, category, search, or app-entry page
in a commerce carousel.

## Production Rule

- Treat the final page as an operation tutorial, not a generic CTA poster.
- Generate the final approved page with OpenRouter Image API at high quality
  when the user supplies a real phone screenshot, a source guide page, or asks
  for a polished final shopping guide.
- Use local composites only as temporary layout sketches or emergency
  placeholders. Do not deliver a local composite as the final when a high-quality
  generated guide is expected.
- Preserve the real app evidence. Do not invent app screens, products, prices,
  discounts, category names, claims, or extra phones.

## Required References

Pass these references on the final guide asset whenever available:

- Real phone screenshot: the supplied app/category/search screen.
- Style reference: the original source shopping guide page or the closest
  approved guide page.
- English brand lockup:
  `viral-social-remix/umall_logo/asian-grocer-online-powered-by-umall.png`.

For English-region output, use `ASIAN GROCER ONLINE / powered by UMALL`. Do not
use the Chinese UMALL logo unless the target is explicitly Chinese-region.

## Layout Contract

- Canvas: `1152x1152` for Instagram/Facebook.
- Left 40-45%: official brand lockup, short tagline, huge stacked action title,
  a one-line promise, three rounded step cards with red circular number badges,
  and one small contextual basket/crate at the bottom.
- Right 50-55%: one dominant rounded phone frame containing the real app screen
  content. The phone is the proof and should be larger than decorative food.
- Add three glossy red numbered arrows on the phone. Each arrow must point to a
  real UI target such as search icon, search field, category tab, category row,
  product card, or add-cart button.
- Use warm cream/gold/brown retail styling with red only for the product/action
  word and numbered arrows.

## Copy Pattern

For search-result screenshots:

```text
FIND <PRODUCT> FAST
3 steps to find <product benefit>
1 Tap Search / Open the app search page
2 Type <Keyword> / Use or search the exact keyword
3 Add your pick / Choose <product> and cart it
```

For category screenshots:

```text
FIND <PRODUCT> FAST
3 steps to find <product/category>
1 Tap Categories / Open the category page
2 Choose <Parent Category> / Use the category list
3 Select <Target Category> / Find the product range
```

Keep wording literal and operational. Avoid vague main copy such as `Shop now`,
`Stock up`, or `Ready to add to cart` unless it is a small secondary line.

## Prompt Contract

The final page prompt must include:

- Source role: final shopping/search/category handoff.
- References: style guide page, real phone screenshot, English brand lockup.
- Exact copy.
- Composition: left instruction panel, right dominant phone, three red numbered
  arrows, small basket/crate.
- Invariants: one phone only, real screenshot content, English-region brand.
- Avoid list: generic CTA poster, random four-corner ingredient stickers, fake
  UI/prices/products, extra phones, Chinese logo for English output, copied
  Chinese text, unreadable microtext, arrows that point nowhere.

Use:

```powershell
.\.venv\python.exe viral-social-remix\scripts\run_openrouter_carousel.py --run output\<run> --api-only --asset-id <last-id> --quality high --api-mode images --concurrency 1 --max-attempts 2
```

If an older placeholder page exists at `generated/page-XX.png`, move it into
`qa/backup-*` first so the runner does not skip generation.

## QA And Archiving

- Visually inspect the generated page at full size before accepting it.
- Reject and retry if the phone is too small, the page reads as a poster rather
  than a tutorial, arrows do not point to real UI targets, the logo is wrong,
  the app screen is invented, or the copy is unreadable.
- Rebuild the full carousel contact sheet after a partial final-page rerun.
- Run full delivery validation and write `qa/validation.json`.
- After user approval, collect the approved final page, phone screenshot, style
  reference, brand lockup, prompt, raw response, cost JSON, and contact sheet in
  `qa/approved-shopping-guide/`.
