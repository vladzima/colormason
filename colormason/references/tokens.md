# colormason token contract

Stable contract for every palette the generator emits. Agents writing UI
against a colormason palette should rely on these names, not on hex values.

Token names and step mappings are fixed across brands, schemes, and targets.
Only the hex values change with the brand. When contrast auto-fix nudges a
text token to a different ramp step, the name and role stay the same.

## Ramps

Every ramp has steps 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950
(50 lightest, 950 darkest). OKLCH-derived, perceptually even.

| ramp | present in scope | source of hue |
|---|---|---|
| `primary` | full, basic | brand color |
| `accent` | full only | derived from scheme (or `--accent` pin) |
| `accent-2` | full only | derived from scheme (or `--accent-2` pin) |
| `neutral` | full, basic | brand hue at very low chroma |
| `success` | full, basic | fixed green hue (150) |
| `warning` | full, basic | fixed yellow hue (100) |
| `error` | full, basic | fixed red hue (29) |
| `info` | full, basic | fixed blue hue (240) |

## Semantic tokens

Format: `token = ramp-light-step / ramp-dark-step`. `pair` is the background
token whose contrast is verified for this text token.

### Background

| token | ramp | light/dark | role |
|---|---|---|---|
| `bg-canvas` | neutral | 100/950 | page background |
| `bg-surface` | neutral | 50/900 | card, panel |
| `bg-surface-raised` | neutral | 50/800 | dropdown, popover (light = surface; separate with shadow) |
| `bg-muted` | neutral | 200/700 | table row hover, muted fill |
| `bg-brand` | primary | 700/500 | primary button |
| `bg-brand-hover` | primary | 800/400 | primary button hover |
| `bg-brand-active` | primary | 900/300 | primary button pressed |
| `bg-accent` | accent | 700/500 | secondary button |
| `bg-accent-hover` | accent | 800/400 | secondary button hover |
| `bg-accent-active` | accent | 900/300 | secondary button pressed |
| `bg-tertiary` | accent-2 | 700/500 | tertiary button |
| `bg-tertiary-hover` | accent-2 | 800/400 | tertiary button hover |
| `bg-tertiary-active` | accent-2 | 900/300 | tertiary button pressed |
| `bg-success` | success | 700/500 | success badge |
| `bg-success-subtle` | success | 100/900 | success banner |
| `bg-warning` | warning | 500/400 | warning badge |
| `bg-warning-subtle` | warning | 100/900 | warning banner |
| `bg-error` | error | 700/500 | destructive button |
| `bg-error-subtle` | error | 100/900 | error banner |
| `bg-info` | info | 700/500 | info badge |
| `bg-info-subtle` | info | 100/900 | info banner |
| `bg-inverse` | neutral | 900/100 | tooltip, toast |

### Text

| token | ramp | light/dark | pair | role |
|---|---|---|---|---|
| `text-primary` | neutral | 900/100 | bg-canvas | body copy |
| `text-secondary` | neutral | 800/300 | bg-canvas | helper text |
| `text-tertiary` | neutral | 700/400 | bg-canvas | timestamps, captions |
| `text-disabled` | neutral | 400/600 | - (WCAG-exempt) | greyed-out label |
| `text-link` | primary | 700/400 | bg-canvas | inline link |
| `text-on-brand` | primary | 50/950 | bg-brand | label on primary button |
| `text-on-accent` | accent | 50/950 | bg-accent | label on secondary button |
| `text-on-tertiary` | accent-2 | 50/950 | bg-tertiary | label on tertiary button |
| `text-on-success` | success | 50/950 | bg-success | label on success badge |
| `text-on-warning` | warning | 950/950 | bg-warning | label on warning badge (dark text both modes) |
| `text-on-error` | error | 50/950 | bg-error | label on destructive button |
| `text-on-info` | info | 50/950 | bg-info | label on info badge |
| `text-success` | success | 700/400 | bg-canvas | saved confirmation |
| `text-error` | error | 700/400 | bg-canvas | field error message |
| `text-warning` | warning | 700/400 | bg-canvas | quota running low |
| `text-info` | info | 700/400 | bg-canvas | inline tip |
| `text-inverse` | neutral | 50/900 | bg-inverse | text on tooltip or toast |

### Border

| token | ramp | light/dark | role |
|---|---|---|---|
| `border-subtle` | neutral | 200/800 | divider between rows |
| `border-default` | neutral | 300/700 | input outline |
| `border-strong` | neutral | 400/600 | emphasised card edge |
| `border-active` | primary | 600/500 | selected tab |
| `border-error` | error | 500/500 | outline on invalid field |

### Focus

| token | ramp | light/dark | role |
|---|---|---|---|
| `ring-focus` | primary | 500/400 | keyboard focus ring |

## Notes

- Steps shown here are the defaults; contrast auto-fix may shift a text
  token one or two steps (closest passing step wins). The emitted JSON is
  always the source of truth for actual steps.
- `basic` scope omits every token whose ramp is absent (all accent/tertiary
  tokens).
- `--exclude` drops a ramp plus every token referencing it.
