# Platform Profiles

| Profile | Language | Asset size | Asset count | Caption |
|---|---|---:|---|---|
| Xiaohongshu carousel | Chinese | 2048×1152 | Match source page count | `caption-zh.txt` |
| Instagram/Facebook carousel | Natural English | 1152×1152 | Match source page count | `caption-en.txt` |
| Video storyboard | Target-market language | 1920×1080 | exactly 9 frames plus one 1920×1080 contact sheet | Target-platform caption |

Use an explicit user platform when supplied. Otherwise infer from URL domain,
page metadata, media dimensions, language, UI traces, and folder naming. Ask
only when confidence is low.

For video, map the selected frames to Hook, setup, pain, product, mechanism,
benefit, proof, result, and CTA. Do not use nine evenly spaced frames as the
final selection; inspect candidates and choose narrative nodes.
