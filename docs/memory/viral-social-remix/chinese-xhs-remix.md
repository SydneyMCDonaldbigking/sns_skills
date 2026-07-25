# Chinese Xiaohongshu Remix Memory

## Source Order

When the user asks to 搬运 a Xiaohongshu post, the source post is the structure.
Capture it first, then write copy and prompts.

Correct sequence:

1. Claim the already-open source tab when the user says it is open.
2. Capture ordered media into `source/xhs-package/` or
   `source/original-post/`.
3. Build or inspect a source contact sheet.
4. Map every generated page to a source page.
5. Only then write `analysis/copy.md`, `analysis/page-prompts/`, and manifest.

## Phone Screenshot Rule

If the user supplies a real phone screenshot and says it is for the final page:

- Use it as final CTA/search/app reference only.
- Do not use it for cover/list/product pages.
- Do not replace the source products with phone screenshot products.
- In each page prompt, explicitly state whether phone screenshot usage is
  allowed.

## Chinese Text Check

PowerShell output may render Chinese as mojibake. That is not evidence the file
is broken.

Use one of these instead:

- Read files as UTF-8 in a proper editor or browser.
- Inspect generated images/contact sheet visually.
- Use OCR when the image text itself is uncertain.
- Compare page prompts against `analysis/copy.md`, not console glyphs.

## Prompt Checklist

Each page prompt should name:

- Primary reference image path.
- Page role and source page number.
- Exact product names/order when products matter.
- Target platform and size.
- Allowed/disallowed reference assets.
- Required language.
- Whether the page is source carry-over, localization, or final CTA.
