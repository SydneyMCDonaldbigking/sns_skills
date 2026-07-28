# No-Face Asian Cooking Style

Use this when making English-region Asian food videos without真人/personality
shots.

## Default Taste

- Real kitchen, not ad studio.
- Vertical 9:16, tight food-first framing.
- One main surface, one pan or pot, one plate or bowl, one active utensil.
- Warm practical lighting. Avoid dark moody scenes unless the source is clearly
  a night-kitchen recipe.
- Food should occupy most of the frame. Hands can enter, but the face and body
  should not become the subject.

## Shot Rhythm

For a 10-17s reel, favor this rhythm:

1. 0-2s: sensory hook, already delicious-looking.
2. 2-6s: fastest prep or sauce mechanism.
3. 6-11s: heat transformation, bubbling, stir-fry, sear, or sauce coating.
4. 11-15s: plating, garnish, chopstick/spoon lift.
5. Last 1-2s: final hero with physical brand sign, package, or grocery product
   in the scene.

For 3 x 5s API video segments:

- Segment 1: hook plus prep/setup.
- Segment 2: cooking transformation.
- Segment 3: plating, garnish, and product/brand hero.

## Visual Rules For Generation

- Keep generated frames and videos free of visible text, captions, labels,
  title cards, stickers, lower-thirds, or fake UI.
- Do not ask the image/video model to render ingredient labels. Put labels in
  ChatCut later if needed.
- Keep props sparse: table, pan/pot, burner, knife, cutting board, one bowl,
  one utensil, product package or brand sign only when needed.
- Do not show a creator face. Use hands-only cooking action.
- Keep the same camera angle, cookware, countertop, hand model, and lighting
  across Seedance shots, generated reference frames, and split videos.
- Prefer real tactile actions: pour sauce, add tofu, stir noodles, toss chicken,
  spoon broth, drizzle chili oil, sprinkle scallions, lift dumpling, plate rice.

## Text And ChatCut

- IG examples often use short centered white text. In our generation pipeline,
  that text belongs in ChatCut, not in the AI storyboard/video prompt.
- When subtitles or labels are requested, default to white centered text with a
  subtle shadow, placed near the visual middle so upload UI does not hide it.
- Keep subtitle lines short: 2-5 words or one compact sentence.
- BGM should be trimmed to exact video duration. Add light food SFX only when
  it matches visible action: chopping, sizzling, bubbling, pouring, plating.

## Product And Brand Integration

- Product should be a physical object, not an overlay ad.
- For English-region output, use the `ASIAN GROCER ONLINE powered by UMALL`
  logo lockup if a brand prop is needed.
- Strong product scenes:
  - package standing beside raw ingredients in the opening setup;
  - sauce/seasoning bottle being used in the mechanism shot;
  - final plate with package or small tabletop sign in the final hero;
  - grocery shelf/list framing for guide-style content.
- Weak product scenes:
  - floating logo;
  - fake banner;
  - text pasted over food;
  - product labels too small or distorted;
  - too many packages competing with the dish.

## Reusable Hooks

- `one-pan`
- `lazy dinner`
- `10-minute`
- `15-minute`
- `weeknight`
- `no-fold`
- `grocery shortcut`
- `comfort bowl`
- `starter pack`
- `use what you have`

Use hooks as caption/post-production language. Do not render them inside
generated frames unless the user explicitly asks for visible text.
