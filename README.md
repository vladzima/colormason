# colormason

An agent skill that turns **one brand color** into a complete, accessible
color system — fully offline, deterministic, zero dependencies.

![colormason — one brand color to a complete, accessible color system](https://cdn.arbatov.dev/jD8ZZ6NVhgfn32LZOhR4ZVbD4.png)

Given a single hex, colormason generates:

- **8 perceptually even OKLCH ramps** (50–950): primary, accent, accent-2,
  neutral, success, warning, error, info
- **~45 semantic design tokens** with light **and** dark values:
  backgrounds, text, borders, focus ring
- **WCAG-verified contrast pairs** — every text token is checked against its
  background; steps auto-adjust to meet AA/AAA where physically possible,
  and the generator warns honestly when a pair cannot pass

Output formats: CSS custom properties, Tailwind v4 `@theme`, JSON, or
Markdown.

Works with Claude Code, Codex, Cursor, OpenCode, and every other agent that
supports the [Agent Skills](https://agentskills.io) standard.

## Install

```bash
npx skills add vladzima/colormason
```

Or clone the repo and copy `colormason/` into your agent's skills directory
(e.g. `~/.claude/skills/`, `.agents/skills/`, `.cursor/skills/`).

## Use

Once installed, just ask your agent things like:

> Give me a color system for brand #0f766e, analogous scheme, AAA contrast,
> as a Tailwind theme.

The skill runs the bundled generator directly:

```bash
python3 colormason/scripts/palette.py --brand 0f766e --scheme analogous --target AAA --format tailwind
```

| option | values | default |
|---|---|---|
| `--brand` | any 6-digit hex | required |
| `--scheme` | `complementary`, `analogous`, `triadic`, `split`, `monochromatic` | `complementary` |
| `--scope` | `full`, `basic` (no accent ramps) | `full` |
| `--target` | `AA`, `AAA` | `AA` |
| `--format` | `css`, `tailwind`, `json`, `markdown` | `css` |
| `--accent`, `--accent-2` | pin accents to exact hexes | derived from scheme |
| `--exclude` | ramps to omit, e.g. `accent-2,info` | — |
| `--no-fix` | disable contrast auto-adjust | — |

## Example

`python3 colormason/scripts/palette.py --brand 3d7dff --format markdown`
(partial output):

```text
primary   50=#f4f8ff 100=#e7efff 200=#cedfff 300=#b0ccff 400=#89b2ff
          500=#5b92ff 600=#3372f3 700=#1b55cf 800=#083ba4 900=#012573 950=#021442

bg-brand        #1b55cf  #5b92ff   primary-700/500     primary button
bg-canvas       #eeeff1  #18191b   neutral-100/950     page background
text-on-brand   #f4f8ff  #021442   primary-50/950      6.07:1/5.93:1 vs bg-brand
text-primary    #2d2f32  #eeeff1   neutral-900/100     11.67:1/15.29:1 vs bg-canvas
```

Every light/dark pair of a text token meets WCAG AA against its stated
background, or the generator says otherwise in a warning.

## How it works

- Hex → OKLCH, hue preserved, steps snapped onto a fixed lightness ladder so
  scales are perceptually even (the input hex never appears verbatim — that
  is expected).
- Chroma tapered toward both ladder ends and binary-searched against the
  sRGB gamut at every step.
- Accents derived by hue rotation per scheme, or pinned to exact colors.
- Semantic tokens mapped onto ramp steps by a fixed contract; text pairs
  measured with WCAG relative-luminance contrast and nudged to the nearest
  passing step when below target.

The full token contract is in
[`colormason/references/tokens.md`](colormason/references/tokens.md);
integration recipes (Tailwind v3/v4, plain CSS, CSS-in-JS, shadcn) in
[`colormason/references/integration.md`](colormason/references/integration.md).

## Requirements

Python 3.8+, standard library only. No network, no packages, no API keys.

## License

MIT
