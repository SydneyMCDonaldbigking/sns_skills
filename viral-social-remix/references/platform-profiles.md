# Platform Profiles

| Profile | Language | Asset size | Asset count | Caption |
|---|---|---:|---|---|
| Xiaohongshu source to English carousel | Natural English | 1152x1152 | Match source page count | `caption-en.txt` |
| Xiaohongshu target carousel | Chinese | 1152x1536 | Match source page count | `caption-zh.txt` |
| Instagram/Facebook carousel | Natural English | 1152x1152 | Match source page count | `caption-en.txt` |
| English vertical cooking video | Natural English | 9:16 video, 1080p; opening frames 1080x1920 | exactly 3 opening frames; 1 per 6s Seedance clip; 3 clips | `caption-en.txt` |
| Video storyboard | Target-market language | 1920x1080 | exactly 9 frames plus one 1920x1080 contact sheet | Target-platform caption |

Use an explicit user target platform when supplied. Otherwise infer source and
target separately: a Xiaohongshu URL identifies the source/capture workflow, not
the output language. For "搬运", English, overseas, Instagram, or Facebook
requests from Xiaohongshu sources, use the English carousel profile and
`caption-en.txt`. Use the Chinese Xiaohongshu target profile only when the user
explicitly asks for Chinese Xiaohongshu output. Ask only when target confidence
is low.

For video, map the selected frames to Hook, setup, pain, product, mechanism,
benefit, proof, result, and CTA. Do not use nine evenly spaced frames as the
final selection; inspect candidates and choose narrative nodes.

For English vertical cooking video, use platform `vertical-video`, vertical
`9:16`, and generate exactly three director-designed `1080x1920` opening
frames. Submit frame `01`, `02`, or `03` to its own silent 6s Seedance request,
then finish only the accepted MP4 clips in ChatCut. Preserve a coherent full
sequence; trim only defects or dead time. Add agent-generated BGM/SFX and
editable white centered English current-step captions.
