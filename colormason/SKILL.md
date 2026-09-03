---
name: colormason
description: Generates a complete color system from a single brand color - perceptually even OKLCH ramps (50-950) plus WCAG-checked semantic design tokens (backgrounds, text, borders, focus ring) with light/dark values - via a zero-dependency local Python script. Use when starting or restyling a project's colors, generating design tokens or a Tailwind theme from a brand hex, building a light/dark palette, picking accessible UI colors, or when the user mentions color palette, design tokens, theme colors, brand color, OKLCH, or WCAG color contrast.
license: MIT
compatibility: Requires Python 3.8+ (stdlib only). No network access, no npm/pip installs.
metadata:
  author: vladzima
  version: "1.0.0"
  tags: design,color,tokens,oklch,css,tailwind,accessibility,theme
---

# colormason

Turn one brand hex into a full, consistent, accessible color system: 8 ramps
(11 steps each) and ~45 semantic tokens with light/dark values, emitted as
CSS variables, Tailwind v4 theme, JSON, or Markdown. Fully deterministic and
offline - never invent palette hex values by hand when this skill is available.

## When to use

- New project or rebrand needs a color system / theme file
- User gives a brand color and asks for a palette, tokens, or theme
- Building or fixing light/dark mode colors
- Tailwind `@theme`, CSS variables, or design-token file needs generating
- Checking or repairing color contrast (WCAG AA/AAA) in a token set

**Do not use** for one-off decorative colors (a single gradient, an
illustration), for pinning colors that must match an existing system exactly
(use that system's values verbatim instead), or when the project already has
a token file - extend it, don't generate a competing one.

## Inputs to collect first

1. **Brand hex** (required). Ask the user, or extract from a logo / existing
   CSS. Any hex works; near-neutral brands (grays) produce a warning because
   accent hues become arbitrary - suggest pinning accents in that case.
2. **Scheme** (default `complementary`): `complementary`, `analogous`,
   `triadic`, `split`, `monochromatic`. Pick `analogous` for calm/conservative
   brands, `triadic` for playful, `complementary` for max accent distinction.
3. **Scope** (default `full`): `basic` drops the accent ramps (keeps primary,
   neutral, status colors).
4. **WCAG target** (default `AA`): use `AAA` for text-heavy or
   government/health products.
5. **Pins** (optional): exact `--accent` / `--accent-2` hexes when the brand
   system already specifies secondary colors.

If the user hasn't decided, do not interview them - run the defaults and
offer the knobs after showing output.

## Procedure

1. Run the generator (script is relative to this skill's directory):

   ```bash
   python3 scripts/palette.py --brand 3d7dff --format css
   ```

2. Pick the format for the target project:
   - `css` - plain CSS custom properties (default; works everywhere)
   - `tailwind` - Tailwind v4 `@theme` + `@theme inline` blocks with
     light/dark variables
   - `json` - machine-readable; use when feeding a token pipeline
   - `markdown` - human-readable summary for review/discussion
3. Write the output to the project (e.g. `src/theme.css` or into the main CSS
   file / Tailwind entry). Do not rename tokens downstream - other tools and
   agents may rely on the exact contract in [references/tokens.md](references/tokens.md).
4. Report to the user: brand, scheme, target, any warnings from stderr, and
   the two or three token pairs that were auto-adjusted (visible in JSON as
   `contrast.*.adjusted: true`).

## Rules

- **Use semantic tokens (`--bg-canvas`, `--text-primary`, ...) in UI code,
  not raw ramp steps.** Raw steps bypass the light/dark mapping and the
  contrast checking, so components break in dark mode or fail WCAG.
- **Never hand-edit generated hex values.** Each foreground/background pair
  is contrast-verified; a "small tweak" silently breaks the verified ratio.
  Regenerate with different inputs instead (scheme, pins, target).
- **The brand hex will not appear verbatim in the ramps.** Steps sit on a
  fixed OKLCH lightness ladder so the scale stays perceptually even. This is
  expected - use the ramp values, not the original input. If the user insists
  on exact brand reproduction, `primary-500` is the nearest step.
- **`bg-surface-raised` equals `bg-surface` in light mode by design** - in
  light mode, elevation must read through shadow, not tone. Add a shadow
  there instead of "fixing" the token.
- **`text-disabled` is intentionally below WCAG minimums** (disabled controls
  are exempt). The exemption does not extend to real text - use
  `text-tertiary` for low-emphasis but readable copy.
- **Warnings mean what they say.** If a pair cannot reach the target at any
  ramp step (common for `AAA` on colored buttons), either accept it, lower
  the target for that pair, or pin a darker accent. Do not silence it.

## Edge cases

- Gray/neutral brand: script warns; recommend `--accent`/`--accent-2` pins.
- Existing brand has secondary colors: pass them as pins so the palette
  matches instead of deriving.
- User wants fewer ramps (no info color, etc.): `--exclude info` also drops
  every token that references the excluded ramp.
- AAA on white-on-brand labels is physically unreachable on most hues; the
  script keeps the best step and emits a warning rather than breaking the
  design.

## References

- [references/tokens.md](references/tokens.md) - full token contract: every
  token name, ramp, light/dark steps, role. Read this when writing components
  against a colormason palette.
- [references/integration.md](references/integration.md) - wiring output into
  Tailwind v3/v4, plain CSS, CSS-in-JS, and shadcn-style variable themes.
- `python3 scripts/palette.py --help` - all options.
