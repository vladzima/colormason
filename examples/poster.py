#!/usr/bin/env python3
"""Render a presentation poster for colormason from real generated output.

Requires: python3, ImageMagick (`convert`) on PATH.

Usage:
  python3 examples/poster.py                          # full poster
  python3 examples/poster.py --style minimal          # minimal poster
  python3 examples/poster.py --brand 0f766e --style minimal
"""

import argparse
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, os.pardir, "colormason", "scripts")

spec = importlib.util.spec_from_file_location(
    "palette", os.path.join(SCRIPTS, "palette.py"))
palette = importlib.util.module_from_spec(spec)
spec.loader.exec_module(palette)

W, H = 1920, 1080
BG = "#0e1116"
GRAY = "#8b93a1"
GRAY_DIM = "#646c78"
CHIP_BG = "#161b22"
CHIP_BORDER = "#242b36"
SANS = "DejaVu Sans"
SANS_BOLD = "DejaVu-Sans-Bold"
MONO = "DejaVu-Sans-Mono"
MONO_BOLD = "DejaVu-Sans-Mono-Bold"


def tw(s, size, mono=False, bold=False):
    per = 0.60 if mono else (0.64 if bold else 0.58)
    return len(s) * size * per


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size, fill, font=SANS, bold=False, mono=False):
    fam = MONO_BOLD if (mono and bold) else MONO if mono else (
        SANS_BOLD if bold else SANS)
    weight = ' font-weight="bold"' if bold else ""
    return ('<text x="%d" y="%d" font-family="%s" font-size="%d" '
            'fill="%s"%s>%s</text>') % (x, y, fam, size, fill, weight, esc(s))


def ctext(cx, y, s, size, fill, font=SANS, bold=False, mono=False):
    return text(cx - tw(s, size, mono, bold) / 2, y, s, size, fill,
                font, bold, mono)


def rect(x, y, w, h, fill, rx=0, stroke=None, sw=0):
    st = ' stroke="%s" stroke-width="%s"' % (stroke, sw) if stroke else ""
    return '<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s"%s/>' % (
        x, y, w, h, rx, fill, st)


def tok(d, name, mode):
    return next(t for t in d["tokens"] if t["name"] == name)[mode]


def ramp(d, name, step):
    return d["ramps"][name][step]


def ratio(d, name, mode="light"):
    t = next(t for t in d["tokens"] if t["name"] == name)
    return "%.2f:1" % t["contrast"][mode]["ratio"]


RAMP_ORDER = ["primary", "accent", "accent-2", "neutral",
              "success", "warning", "error", "info"]
STEP_LABELS = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]


def build_svg_minimal(d):
    """Minimal poster - the poster itself is set in the generated system:
    background, text, link and ramp colors are all real token values."""
    el = []
    el.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">' % (W, H))
    el.append(rect(0, 0, W, H, tok(d, "bg-canvas", "light")))
    tp = tok(d, "text-primary", "light")
    ts = tok(d, "text-secondary", "light")
    tt = tok(d, "text-tertiary", "light")

    # header
    el.append(text(120, 140, "colormason", 44, tp, bold=True))
    el.append(text(122, 180, "one brand color " + chr(0x2192) +
                   " an accessible color system", 20, ts))
    el.append(text(1800 - tw("#" + d["brand"].lstrip("#"), 17, mono=True), 118,
                   d["brand"], 17, ts, mono=True))
    el.append(rect(1800 - 44, 134, 44, 44, d["brand"], rx=10))

    # hero: the primary ramp, one full-width bar
    el.append(text(122, 428, "primary", 14, tt, mono=True))
    x0, bar_w, bar_y, bar_h, gap = 120, 1680, 452, 240, 3
    sw = (bar_w - gap * 10) / 11.0
    for i, step in enumerate(STEP_LABELS):
        el.append(rect(x0 + i * (sw + gap), bar_y, sw, bar_h,
                       ramp(d, "primary", step), rx=8))
    for i in (0, 5, 10):
        cx = x0 + i * (sw + gap) + sw / 2
        el.append(ctext(cx, bar_y + bar_h + 34, str(STEP_LABELS[i]), 13,
                        tt, mono=True))

    # footer
    el.append(text(120, 952, "8 ramps  " + chr(0xb7) + "  45 semantic tokens  " +
                   chr(0xb7) + "  light + dark  " + chr(0xb7) +
                   "  every text pair WCAG AA", 15, ts, mono=True))
    install = "$ npx skills add vladzima/colormason"
    el.append(text(1800 - tw(install, 17, mono=True, bold=True), 952, install,
                   17, tok(d, "text-link", "light"), bold=True, mono=True))

    el.append("</svg>")
    return "\n".join(el)


def build_svg_full(d):
    el = []
    el.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">' % (W, H))
    el.append(rect(0, 0, W, H, BG))

    # ------------------------------------------------------------- header
    for i, step in enumerate((400, 600, 800)):
        el.append(rect(80 + i * 34, 58, 26, 26, ramp(d, "primary", step), rx=7))
    el.append(text(200, 106, "colormason", 62, "#f2f5f9", bold=True))
    el.append(text(202, 148, "One brand color " + chr(0x2192) +
                   " a complete, accessible color system", 24, GRAY))
    el.append(text(202, 178, "8 ramps  " + chr(0xb7) + "  45 semantic tokens  " +
                   chr(0xb7) + "  light + dark  " + chr(0xb7) +
                   "  WCAG-verified  " + chr(0xb7) + "  zero dependencies",
                   15, GRAY_DIM, mono=True))

    brand = d["brand"]
    el.append(ctext(1660, 66, "BRAND INPUT", 13, GRAY_DIM, bold=True))
    el.append(rect(1480, 78, 360, 64, brand, rx=14))
    el.append(ctext(1660, 118, brand, 26, "#ffffff", bold=True, mono=True))

    # ------------------------------------------------------------- ramps
    el.append(text(80, 252, "OKLCH RAMPS " + chr(0x2014) +
                   " 50 LIGHTEST " + chr(0x2192) + " 950 DARKEST", 16,
                   GRAY_DIM, bold=True))
    for i, step in enumerate(STEP_LABELS):
        el.append(ctext(200 + i * 58 + 27, 282, str(step), 12, "#4d545e", mono=True))
    for r, name in enumerate(RAMP_ORDER):
        y = 296 + r * 62
        el.append(text(190 - tw(name, 15, mono=True), y + 26, name, 15,
                       "#c8cdd5", mono=True))
        for i, step in enumerate(STEP_LABELS):
            el.append(rect(200 + i * 58, y, 54, 42, ramp(d, name, step), rx=7))

    # ------------------------------------------------------ preview cards
    el.append(text(940, 252, "SEMANTIC TOKENS " + chr(0x2014) +
                   " SAME UI, LIGHT / DARK", 16, GRAY_DIM, bold=True))

    def card(x, mode, label):
        surface = tok(d, "bg-surface", mode)
        border = tok(d, "border-default", mode)
        tp = tok(d, "text-primary", mode)
        ts = tok(d, "text-secondary", mode)
        tt = tok(d, "text-tertiary", mode)
        out = [rect(x, 272, 420, 470, surface, rx=16, stroke=border, sw="1.5")]
        out.append(text(x + 26, 306, label, 13, GRAY_DIM, bold=True))
        out.append(text(x + 26, 348, "Deployment", 26, tp, bold=True))
        out.append(text(x + 26, 378, "3 services " + chr(0xb7) + " 12 replicas " +
                        chr(0xb7) + " v2.4.1", 15, ts))
        # primary + ghost buttons
        out.append(rect(x + 26, 404, 172, 46, tok(d, "bg-brand", mode), rx=10))
        out.append(ctext(x + 112, 433, "Deploy now", 16,
                         tok(d, "text-on-brand", mode), bold=True))
        out.append(rect(x + 210, 404, 116, 46, "none", rx=10,
                        stroke=border, sw="1.5"))
        out.append(ctext(x + 268, 433, "Cancel", 16, tp))
        # badges
        for i, (ramp_name, lbl) in enumerate((("success", "Saved"),
                                              ("error", "Failed"),
                                              ("info", "Info"))):
            bx = x + 26 + i * 118
            out.append(rect(bx, 486, 104, 34, tok(d, "bg-" + ramp_name, mode), rx=17))
            out.append(ctext(bx + 52, 508, lbl, 13,
                             tok(d, "text-on-" + ramp_name, mode), bold=True))
        # error banner
        out.append(rect(x + 26, 544, 368, 54, tok(d, "bg-error-subtle", mode), rx=10))
        out.append(text(x + 42, 577, "Quota is running low", 15,
                        tok(d, "text-error", mode)))
        # input field
        canvas = tok(d, "bg-canvas", mode)
        out.append(rect(x + 26, 622, 368, 46, canvas, rx=10,
                        stroke=border, sw="1.5"))
        out.append(text(x + 42, 651, "Search services" + chr(0x2026), 14, tt))
        # link
        out.append(text(x + 26, 706, "Docs & runbook " + chr(0x2192), 15,
                        tok(d, "text-link", mode), bold=True))
        return out

    el.extend(card(940, "light", "LIGHT MODE"))
    el.extend(card(1420, "dark", "DARK MODE"))

    # -------------------------------------------------------- bottom band
    el.append(text(80, 856, "WCAG AA VERIFIED", 14, "#8fd6a8", bold=True))
    pairs = "   ".join("%s %s" % (n, ratio(d, n)) for n in
                       ("text-primary", "text-on-brand", "text-on-error",
                        "text-on-warning"))
    el.append(text(240, 856, pairs, 15, GRAY, mono=True))

    el.append(text(80, 952, "deterministic " + chr(0xb7) + " offline " + chr(0xb7) +
                   " no API keys " + chr(0xb7) + " python 3 stdlib only",
                   15, GRAY_DIM, mono=True))
    el.append(text(80, 986, "github.com/vladzima/colormason", 18, GRAY))
    el.append(rect(1150, 930, 710, 60, CHIP_BG, rx=12, stroke=CHIP_BORDER, sw="1.5"))
    el.append(ctext(1505, 967, "$ npx skills add vladzima/colormason", 20,
                    ramp(d, "primary", 400), bold=True, mono=True))

    el.append("</svg>")
    return "\n".join(el)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--brand", default="3d7dff")
    p.add_argument("--scheme", default="complementary")
    p.add_argument("--style", default="full", choices=["full", "minimal"])
    p.add_argument("--out", default=None)
    args = p.parse_args()

    d = palette.generate(brand=args.brand, scheme=args.scheme, scope="full",
                         target="AA")
    builder = build_svg_minimal if args.style == "minimal" else build_svg_full
    out = args.out or os.path.join(
        HERE, "colormason.png" if args.style == "full" else
        "colormason-minimal.png")
    svg = builder(d)
    svg_path = out + ".svg"
    with open(svg_path, "w") as f:
        f.write(svg)
    subprocess.run(["convert", svg_path, out], check=True)
    os.remove(svg_path)
    print("wrote %s (%s, brand %s)" % (out, args.style, d["brand"]))


if __name__ == "__main__":
    main()
