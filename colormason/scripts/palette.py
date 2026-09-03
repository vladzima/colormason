#!/usr/bin/env python3
"""colormason - turn one brand color into a full color system.

Generates perceptually even OKLCH ramps (50-950) and WCAG-checked
semantic design tokens (light + dark) from a single brand hex.
Zero dependencies, stdlib only, no network.

Usage:
  python3 palette.py --brand 3d7dff
  python3 palette.py --brand 0f766e --scheme analogous --target AAA --format tailwind
  python3 palette.py --brand e11d48 --scope basic --exclude info --format json
"""

import argparse
import json
import math
import sys

VERSION = "1.0.0"

# --------------------------------------------------------------- color math

def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c):
    if c <= 0.0031308:
        return 12.92 * c
    return 1.055 * (c ** (1 / 2.4)) - 0.055


def hex_to_rgb(value):
    v = value.lstrip("#").strip()
    if len(v) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in v):
        raise ValueError("invalid hex color: %r (expected 6 digits, with or without #)" % value)
    return tuple(int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb_to_hex(rgb):
    def enc(c):
        return max(0, min(255, round(c * 255)))
    return "#%02x%02x%02x" % (enc(rgb[0]), enc(rgb[1]), enc(rgb[2]))


def rgb_to_oklab(rgb):
    r, g, b = (_srgb_to_linear(c) for c in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = l ** (1 / 3), m ** (1 / 3), s ** (1 / 3)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b2 = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, a, b2


def _oklab_to_linear_rgb(L, a, b):
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b2 = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return r, g, b2


def hex_to_oklch(value):
    L, a, b = rgb_to_oklab(hex_to_rgb(value))
    C = math.hypot(a, b)
    H = math.degrees(math.atan2(b, a)) % 360
    return L, C, H


def oklch_to_srgb(L, C, H):
    """May return values outside [0,1] when out of gamut; callers handle."""
    h = math.radians(H)
    r, g, b = _oklab_to_linear_rgb(L, C * math.cos(h), C * math.sin(h))
    return (_linear_to_srgb(r), _linear_to_srgb(g), _linear_to_srgb(b))


def _in_gamut(rgb, eps=1e-6):
    return all(-eps <= c <= 1 + eps for c in rgb)


def clamp_chroma(L, C, H):
    """Largest chroma at (L, H) that still fits inside sRGB."""
    if C <= 0:
        return 0.0
    if _in_gamut(oklch_to_srgb(L, C, H)):
        return C
    lo, hi = 0.0, C
    for _ in range(28):
        mid = (lo + hi) / 2
        if _in_gamut(oklch_to_srgb(L, mid, H)):
            lo = mid
        else:
            hi = mid
    return lo


def luminance(hex_value):
    r, g, b = (_srgb_to_linear(c) for c in hex_to_rgb(hex_value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg_hex, bg_hex):
    y1, y2 = luminance(fg_hex), luminance(bg_hex)
    if y1 < y2:
        y1, y2 = y2, y1
    return (y1 + 0.05) / (y2 + 0.05)


# ------------------------------------------------------------ ramp building

LADDER = {
    50: 0.977, 100: 0.951, 200: 0.902, 300: 0.842, 400: 0.765, 500: 0.675,
    600: 0.586, 700: 0.494, 800: 0.399, 900: 0.303, 950: 0.213,
}
STEPS = sorted(LADDER)


def chroma_weight(L):
    """Full chroma near the middle of the ladder, tapered toward both ends
    (harder at the light end, where the gamut is smaller)."""
    if L >= 0.586:
        t = (L - 0.586) / (0.977 - 0.586)
        return max(0.22, 1.0 - 0.8 * t * t)
    t = (0.586 - L) / (0.586 - 0.213)
    return max(0.35, 1.0 - 0.55 * t * t)


def build_ramp(H, base_chroma):
    ramp = {}
    for step in STEPS:
        L = LADDER[step]
        C = clamp_chroma(L, base_chroma * chroma_weight(L), H)
        ramp[step] = rgb_to_hex(oklch_to_srgb(L, C, H))
    return ramp


SCHEMES = {
    # scheme: (accent hue, accent-2 hue) offsets from the brand hue
    "complementary": lambda h: ((h + 180) % 360, (h + 210) % 360),
    "analogous": lambda h: ((h + 30) % 360, (h - 30) % 360),
    "triadic": lambda h: ((h + 120) % 360, (h + 240) % 360),
    "split": lambda h: ((h + 150) % 360, (h + 210) % 360),
    "monochromatic": lambda h: (h, h),
}

# Fixed semantic hues: (ramp name, hue, base chroma)
STATUS_RAMPS = [
    ("success", 150, 0.130),
    ("warning", 100, 0.125),
    ("error", 29, 0.170),
    ("info", 240, 0.120),
]

# ----------------------------------------------------------- semantic tokens
# (name, ramp, light step, dark step, group, role, contrast pair or None)

TOKEN_TABLE = [
    ("bg-canvas", "neutral", 100, 950, "Background", "Page background", None),
    ("bg-surface", "neutral", 50, 900, "Background", "Card, panel", None),
    ("bg-surface-raised", "neutral", 50, 800, "Background", "Dropdown menu, popover", None),
    ("bg-muted", "neutral", 200, 700, "Background", "Table row hover, muted fill", None),
    ("bg-brand", "primary", 700, 500, "Background", "Primary button", None),
    ("bg-brand-hover", "primary", 800, 400, "Background", "Primary button hover", None),
    ("bg-brand-active", "primary", 900, 300, "Background", "Primary button pressed", None),
    ("bg-accent", "accent", 700, 500, "Background", "Secondary button", None),
    ("bg-accent-hover", "accent", 800, 400, "Background", "Secondary button hover", None),
    ("bg-accent-active", "accent", 900, 300, "Background", "Secondary button pressed", None),
    ("bg-tertiary", "accent-2", 700, 500, "Background", "Tertiary button", None),
    ("bg-tertiary-hover", "accent-2", 800, 400, "Background", "Tertiary button hover", None),
    ("bg-tertiary-active", "accent-2", 900, 300, "Background", "Tertiary button pressed", None),
    ("bg-success", "success", 700, 500, "Background", "Success badge", None),
    ("bg-success-subtle", "success", 100, 900, "Background", "Success banner", None),
    ("bg-warning", "warning", 500, 400, "Background", "Warning badge", None),
    ("bg-warning-subtle", "warning", 100, 900, "Background", "Warning banner", None),
    ("bg-error", "error", 700, 500, "Background", "Destructive button", None),
    ("bg-error-subtle", "error", 100, 900, "Background", "Error banner", None),
    ("bg-info", "info", 700, 500, "Background", "Info badge", None),
    ("bg-info-subtle", "info", 100, 900, "Background", "Info banner", None),
    ("bg-inverse", "neutral", 900, 100, "Background", "Tooltip, toast", None),
    ("text-primary", "neutral", 900, 100, "Text", "Body copy", "bg-canvas"),
    ("text-secondary", "neutral", 800, 300, "Text", "Helper text", "bg-canvas"),
    ("text-tertiary", "neutral", 700, 400, "Text", "Timestamps, captions", "bg-canvas"),
    ("text-disabled", "neutral", 400, 600, "Text", "Greyed-out label (WCAG-exempt)", None),
    ("text-link", "primary", 700, 400, "Text", "Inline link", "bg-canvas"),
    ("text-on-brand", "primary", 50, 950, "Text", "Label on primary button", "bg-brand"),
    ("text-on-accent", "accent", 50, 950, "Text", "Label on secondary button", "bg-accent"),
    ("text-on-tertiary", "accent-2", 50, 950, "Text", "Label on tertiary button", "bg-tertiary"),
    ("text-on-success", "success", 50, 950, "Text", "Label on success badge", "bg-success"),
    ("text-on-warning", "warning", 950, 950, "Text", "Label on warning badge", "bg-warning"),
    ("text-on-error", "error", 50, 950, "Text", "Label on destructive button", "bg-error"),
    ("text-on-info", "info", 50, 950, "Text", "Label on info badge", "bg-info"),
    ("text-success", "success", 700, 400, "Text", "Saved confirmation", "bg-canvas"),
    ("text-error", "error", 700, 400, "Text", "Field error message", "bg-canvas"),
    ("text-warning", "warning", 700, 400, "Text", "Quota running low", "bg-canvas"),
    ("text-info", "info", 700, 400, "Text", "Inline tip", "bg-canvas"),
    ("text-inverse", "neutral", 50, 900, "Text", "Text on tooltip or toast", "bg-inverse"),
    ("border-subtle", "neutral", 200, 800, "Border", "Divider between rows", None),
    ("border-default", "neutral", 300, 700, "Border", "Input outline", None),
    ("border-strong", "neutral", 400, 600, "Border", "Emphasised card edge", None),
    ("border-active", "primary", 600, 500, "Border", "Selected tab", None),
    ("border-error", "error", 500, 500, "Border", "Outline on invalid field", None),
    ("ring-focus", "primary", 500, 400, "Focus", "Keyboard focus ring", None),
]

WCAG_TARGETS = {"AA": 4.5, "AAA": 7.0}


# ------------------------------------------------------------------ pipeline

def generate(brand, scheme, scope, target, accent_pin=None, accent2_pin=None,
             exclude=None, no_fix=False):
    exclude = [e.strip() for e in (exclude or []) if e.strip()]
    warnings = []
    target_ratio = WCAG_TARGETS[target]

    try:
        Lb, Cb, Hb = hex_to_oklch(brand)
    except ValueError as e:
        raise SystemExit("error: %s" % e)
    brand = "#" + brand.lstrip("#").lower()

    if Cb < 0.02:
        warnings.append(
            "brand %s is near-neutral (chroma %.3f); hue-derived accents and the "
            "neutral tint may look arbitrary. Consider pinning --accent/--accent-2."
            % (brand, Cb))

    ramps = {"primary": build_ramp(Hb, Cb)}
    ramps["neutral"] = build_ramp(Hb, min(0.015, max(0.006, Cb * 0.05)))
    for name, H, C in STATUS_RAMPS:
        ramps[name] = build_ramp(H, C)

    if scope == "full":
        h1, h2 = SCHEMES[scheme](Hb)
        if scheme == "monochromatic":
            c1, c2 = Cb * 0.55, Cb * 0.30
        else:
            c1, c2 = Cb * 0.80, Cb * 0.70
        if accent_pin:
            _, c1, h1 = hex_to_oklch(accent_pin)
        if accent2_pin:
            _, c2, h2 = hex_to_oklch(accent2_pin)
        ramps["accent"] = build_ramp(h1, c1)
        ramps["accent-2"] = build_ramp(h2, c2)

    for name in exclude:
        if name not in ramps:
            raise SystemExit("error: cannot exclude unknown ramp %r" % name)
        del ramps[name]

    tokens = []
    for name, ramp, ls, ds, group, role, pair in TOKEN_TABLE:
        if ramp not in ramps:
            continue
        tokens.append({
            "name": name,
            "group": group,
            "ramp": ramp,
            "steps": {"light": ls, "dark": ds},
            "light": ramps[ramp][ls],
            "dark": ramps[ramp][ds],
            "role": role,
            "pair": pair,
        })

    # WCAG check + auto-fix: nudge text-token steps within their ramp until
    # the pair meets the target; keep the step closest to the original.
    by_name = {t["name"]: t for t in tokens}
    for t in tokens:
        if not t["pair"] or t["name"] == "text-disabled":
            continue
        bg = by_name.get(t["pair"])
        if bg is None:
            continue
        t["contrast"] = {}
        for mode in ("light", "dark"):
            bg_hex = bg[mode]
            ratio = contrast(t[mode], bg_hex)
            adjusted = False
            if ratio < target_ratio and not no_fix:
                ramp = ramps[t["ramp"]]
                cur = t["steps"][mode]
                cands = [s for s in STEPS if contrast(ramp[s], bg_hex) >= target_ratio]
                if cands:
                    best = min(cands, key=lambda s: abs(LADDER[s] - LADDER[cur]))
                    t["steps"][mode] = best
                    t[mode] = ramp[best]
                    ratio = contrast(t[mode], bg_hex)
                    adjusted = True
            if ratio < target_ratio:
                warnings.append(
                    "%s (%s) vs %s: %.2f:1, below %s target - no ramp step passes; "
                    "pin a different accent or adjust manually"
                    % (t["name"], mode, t["pair"], ratio, target))
            t["contrast"][mode] = {
                "vs": t["pair"], "ratio": round(ratio, 2), "adjusted": adjusted}

    return {
        "generator": "colormason %s" % VERSION,
        "brand": brand,
        "scheme": scheme,
        "scope": scope,
        "target": target,
        "ramps": ramps,
        "tokens": tokens,
        "warnings": warnings,
    }


# ------------------------------------------------------------------ renderers

def render_json(d):
    ramps = {name: {str(s): h for s, h in ramp.items()} for name, ramp in d["ramps"].items()}
    return json.dumps(
        {k: ramps if k == "ramps" else v for k, v in d.items()},
        indent=2)


def _ramp_comment(lines, ramp_name, ramp):
    lines.append("  /* %s */" % ramp_name)
    for step in STEPS:
        lines.append("  --%s-%d: %s;" % (ramp_name, step, ramp[step]))


def render_css(d):
    lines = [
        "/* colormason %s - brand %s - %s - %s scope - WCAG %s */" % (
            VERSION, d["brand"], d["scheme"], d["scope"], d["target"]),
        "",
        ":root {",
    ]
    for ramp_name, ramp in d["ramps"].items():
        _ramp_comment(lines, ramp_name, ramp)
    lines.append("  /* semantic tokens - light */")
    group = None
    for t in d["tokens"]:
        if t["group"] != group:
            group = t["group"]
            lines.append("  /* %s */" % group.lower())
        lines.append("  --%s: %s;" % (t["name"], t["light"]))
    lines.append("}")
    lines.append("")
    lines.append('[data-theme="dark"], .dark {')
    group = None
    for t in d["tokens"]:
        if t["group"] != group:
            group = t["group"]
            lines.append("  /* %s */" % group.lower())
        lines.append("  --%s: %s;" % (t["name"], t["dark"]))
    lines.append("}")
    return "\n".join(lines)


def render_tailwind(d):
    lines = ['@import "tailwindcss";', "", "@theme {"]
    for ramp_name, ramp in d["ramps"].items():
        _ramp_comment(lines, ramp_name, ramp)
    lines.append("}")
    lines.append("")
    lines.append("@theme inline {")
    group = None
    for t in d["tokens"]:
        if t["group"] != group:
            group = t["group"]
            lines.append("  /* %s */" % group.lower())
        lines.append("  --color-%s: var(--%s);" % (t["name"], t["name"]))
    lines.append("}")
    lines.append("")
    lines.append("/* Light/dark values for the semantic tokens. Toggle via")
    lines.append('   <html class="dark"> or [data-theme="dark"]. */')
    lines.append(":root {")
    for t in d["tokens"]:
        lines.append("  --%s: %s;" % (t["name"], t["light"]))
    lines.append("}")
    lines.append("")
    lines.append('[data-theme="dark"], .dark {')
    for t in d["tokens"]:
        lines.append("  --%s: %s;" % (t["name"], t["dark"]))
    lines.append("}")
    return "\n".join(lines)


def render_markdown(d):
    out = []
    out.append("# colormason palette")
    out.append("")
    out.append("Brand %s - %s scheme - %s scope - WCAG %s target" % (
        d["brand"], d["scheme"], d["scope"], d["target"]))
    out.append("")
    out.append("## Ramps (50 lightest to 950 darkest, OKLCH-derived)")
    out.append("")
    for ramp_name, ramp in d["ramps"].items():
        out.append("**%s**" % ramp_name)
        out.append("")
        out.append("| " + " | ".join(str(s) for s in STEPS) + " |")
        out.append("|" + "---|" * len(STEPS))
        out.append("| " + " | ".join(ramp[s] for s in STEPS) + " |")
        out.append("")
    out.append("## Semantic tokens (light / dark)")
    out.append("")
    group = None
    for t in d["tokens"]:
        if t["group"] != group:
            group = t["group"]
            out.append("### %s" % group)
            out.append("")
            out.append("| token | light | dark | ramp steps | contrast | role |")
            out.append("|---|---|---|---|---|---|")
        steps = "%s-%d/%s-%d" % (t["ramp"], t["steps"]["light"], t["ramp"], t["steps"]["dark"])
        if t.get("contrast"):
            c = t["contrast"]
            contrast_s = "%s/%s vs %s" % (
                _fmt_ratio(c["light"]["ratio"]), _fmt_ratio(c["dark"]["ratio"]), c["light"]["vs"])
        else:
            contrast_s = "-"
        out.append("| %s | %s | %s | %s | %s | %s |" % (
            t["name"], t["light"], t["dark"], steps, contrast_s, t["role"]))
    out.append("")
    out.append("## Notes")
    out.append("")
    out.append("- Prefer semantic tokens over raw ramp steps; they already carry the light/dark mapping.")
    out.append("- The brand hex does not appear verbatim in the ramps: steps sit on a fixed OKLCH lightness ladder so the scale stays perceptually even. Use the ramp values, not the original input.")
    out.append("- bg-surface and bg-surface-raised are the same value in light mode; use a shadow to separate a raised surface in light mode.")
    out.append("- text-disabled is deliberately below WCAG minimums; the exemption covers disabled controls only. Use text-tertiary for low-emphasis but readable copy.")
    if d["warnings"]:
        out.append("")
        out.append("## Warnings")
        out.append("")
        for w in d["warnings"]:
            out.append("- %s" % w)
    return "\n".join(out)


def _fmt_ratio(r):
    return ("%.2f:1" % r).rstrip("0").rstrip(".") if isinstance(r, float) else str(r)


RENDERERS = {
    "json": render_json,
    "css": render_css,
    "tailwind": render_tailwind,
    "markdown": render_markdown,
}


# ----------------------------------------------------------------------- cli

def main(argv=None):
    p = argparse.ArgumentParser(
        prog="palette.py",
        description="Generate OKLCH ramps and WCAG-checked semantic tokens from one brand color.")
    p.add_argument("--brand", required=True,
                   help="brand color, 6-digit hex with or without # (e.g. 3d7dff)")
    p.add_argument("--scheme", default="complementary",
                   choices=sorted(SCHEMES),
                   help="accent derivation scheme (default: complementary)")
    p.add_argument("--scope", default="full", choices=["full", "basic"],
                   help="full adds accent + accent-2 ramps; basic omits them (default: full)")
    p.add_argument("--target", default="AA", choices=["AA", "AAA"],
                   help="WCAG contrast target for text pairs (default: AA)")
    p.add_argument("--format", default="css",
                   choices=["json", "css", "tailwind", "markdown"],
                   help="output format (default: css)")
    p.add_argument("--accent", metavar="HEX",
                   help="pin the secondary accent to a specific color instead of deriving it")
    p.add_argument("--accent-2", metavar="HEX",
                   help="pin the tertiary accent to a specific color instead of deriving it")
    p.add_argument("--exclude", default="",
                   help="comma-separated ramp names to omit, e.g. accent-2,info")
    p.add_argument("--no-fix", action="store_true",
                   help="disable automatic contrast fixing of text token steps")
    args = p.parse_args(argv)

    for label, val in (("--accent", args.accent), ("--accent-2", args.accent_2)):
        if val:
            try:
                hex_to_oklch(val)
            except ValueError as e:
                raise SystemExit("error: %s: %s" % (label, e))

    data = generate(
        brand=args.brand,
        scheme=args.scheme,
        scope=args.scope,
        target=args.target,
        accent_pin=args.accent,
        accent2_pin=args.accent_2,
        exclude=args.exclude.split(",") if args.exclude else [],
        no_fix=args.no_fix,
    )
    print(RENDERERS[args.format](data))
    if args.format != "markdown" and data["warnings"]:
        print("", file=sys.stderr)
        for w in data["warnings"]:
            print("warning: %s" % w, file=sys.stderr)


if __name__ == "__main__":
    main()
