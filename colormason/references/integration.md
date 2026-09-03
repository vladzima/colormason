# Integrating colormason output

## Tailwind v4 (recommended)

Use `--format tailwind`. It emits:

1. `@theme { --color-primary-50: ... }` - ramps become utilities like
   `bg-primary-700`, `text-primary-400`.
2. `@theme inline { --color-bg-canvas: var(--bg-canvas); }` - semantic tokens
   become utilities (`bg-bg-canvas`, `text-text-primary`) that follow the
   CSS variable, so they flip with dark mode.
3. `:root` / `[data-theme="dark"], .dark` blocks holding the light/dark
   values.

Paste the whole block into your Tailwind entry CSS (where `@import
"tailwindcss"` lives). Toggle dark mode by setting `class="dark"` on
`<html>` or `data-theme="dark"` - match whatever the app already uses.

Prefer semantic utilities (`bg-bg-canvas`, `text-text-primary`,
`border-border-default`, `ring-ring-focus`) in components; reserve raw ramp
utilities (`bg-primary-700`) for one-off accents or when a semantic token
does not exist.

## Plain CSS / CSS variables

Use `--format css`. Paste into a global stylesheet. Reference tokens as
`var(--bg-canvas)` etc. The dark block overrides the same variables, so
components need no dark-mode branches of their own.

If the app keys dark mode off `prefers-color-scheme`, replace the selector
line with:

```css
@media (prefers-color-scheme: dark) { /* paste the token values here */ }
```

## Tailwind v3

v3 has no `@theme`. Use `--format css` for the variables, then map the
semantic tokens into `tailwind.config.js` so utilities exist for them:

```js
module.exports = {
  theme: {
    extend: {
      colors: {
        canvas: "var(--bg-canvas)",
        surface: "var(--bg-surface)",
        // ...map the tokens you use
      },
    },
  },
  darkMode: ["class", '[data-theme="dark"]'],
};
```

Ramp utilities can be mapped directly by pasting the ramp hex values into
the config instead of variables (ramps are mode-independent).

## CSS-in-JS (styled-components, emotion)

Use `--format json`, then either:

- Generate a TS module from the JSON (`tokens.ts` exporting each token as a
  string), or
- Keep the CSS variables from `--format css` in a global style sheet and
  reference `var(--token)` in component styles. The variable route keeps
  dark mode working with zero JS.

## shadcn/ui-style themes

shadcn expects a specific variable set (`--background`, `--foreground`,
`--primary`, ...). Do not rename colormason tokens to fake shadcn names -
instead write the shadcn variables as aliases in your global CSS:

```css
:root {
  --background: var(--bg-canvas);
  --foreground: var(--text-primary);
  --primary: var(--bg-brand);
  --primary-foreground: var(--text-on-brand);
  --destructive: var(--bg-error);
  --border: var(--border-default);
  --ring: var(--ring-focus);
  /* ...remaining shadcn variables as needed */
}
```

Both contracts stay intact: shadcn components read theirs, your code reads
colormason's.

## Token pipelines (Style Dictionary, DTCG)

Use `--format json` and wrap it in the DTCG `$value` / `$type` shape your
pipeline expects. Ramp entries are colors; semantic tokens are aliases if
your tool supports resolving `ramp + step` references.
