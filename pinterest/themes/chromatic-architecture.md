# Chromatic Architecture

A deterministic multi-palette system for architectural Pinterest cards. Every project receives a unique color identity while the complete collection remains structured and readable.

## Color Generation

- Seed: stable hash of the project ID, so reruns preserve the same palette.
- Primary: random hue, 55–78% saturation, 24–34% lightness.
- Accent: complementary or split-complementary hue, 65–88% saturation, 48–62% lightness.
- Surface: primary hue at 18–28% saturation and 94–97% lightness.
- Secondary: analogous hue at 30–48% saturation and 72–84% lightness.
- Text: near-black tinted toward the primary hue or crisp white, selected by contrast.
- Minimum text contrast target: 4.5:1.

## Layout Families

Four layout families rotate deterministically across the 200 projects:

1. Full-bleed editorial — large house visualization, floating facts panel.
2. Split architecture — image and SEO title divided by a strong color plane.
3. Gallery card — framed visualization with stacked characteristic chips.
4. Modern poster — oversized area figure, asymmetrical image and CTA.

## Typography

- Headers: DejaVu Sans Bold.
- Body: DejaVu Sans.
- All visible copy is Russian.

## Guardrails

- No uncontrolled neon backgrounds behind body text.
- Characteristics always sit on a high-contrast surface.
- House visualization remains the dominant element.
- Each card contains project number, area, floors, dimensions, material, SEO phrase, domain, and CTA.
