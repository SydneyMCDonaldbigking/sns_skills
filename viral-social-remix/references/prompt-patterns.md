# GPT Image 2 Prompt Contracts

For each asset provide: platform, source role, primary request, product and
brand, scene, subject, composition, text hierarchy, palette, exact copy,
invariants, and avoid list.

```text
Text (verbatim): "<exact Chinese or English copy>"
Consistency lock: preserve the approved product appearance, packaging geometry,
brand spelling, recurring person description, palette, lighting family, and
typography hierarchy across every asset in the group.
```

Use GPT Image 2 to render the text directly in the complete image. After each
generation, visually verify the brand name, product name, numbers, language,
and CTA. Retry only the failed asset. Use local text overlay only after repeated
targeted regeneration fails.

Preserve the source composition, hierarchy, rhythm, and copy structure while
replacing the product, brand, source watermarks, and specific expression. Do
not copy unauthorized logos or impersonate a real person.
