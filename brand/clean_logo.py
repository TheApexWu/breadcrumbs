#!/usr/bin/env python3
"""Clean the traced BREADCRUMBS logo and emit adaptive / light / dark variants.

Input is the raw converter output, which has three problems:

  1. Two paths, not one. Path 0 is a full-canvas white plate with the artwork
     knocked out via evenodd; path 1 is the same 103 shapes filled dark. The
     plate is pure redundancy and it forces an opaque background on a logo.
  2. The canvas is off-centre -- margins run 44.2 / 15.7 / 56.2 / 22.5.
  3. Ink is hardcoded #181819, which belongs to neither theme.

Everything else in the trace is sound: no watermark fragments survived, and
every subpath has a near-exact mirror twin, so the symmetry is intact.

    python3 brand/clean_logo.py [source.svg]
"""
import re
import sys
from pathlib import Path

OUT = Path(__file__).parent
SRC_DEFAULT = OUT / "source" / "breadcrumbs-logo.raw.svg"

# Design system, inherited from vision.html and the Figma deck.
INK_LIGHT = "#0b111c"   # panel  -- near-black, faintly blue
INK_DARK = "#e8edf4"    # ink    -- off-white

MARGIN = 24.0           # uniform padding around the ink bbox
PRECISION = 1           # decimal places; 0.1 unit on a ~1040 canvas is invisible

TOKEN = re.compile(r"([MCZmcz])|(-?\d*\.?\d+)")


def parse(d):
    """-> [(cmd, [floats])]. The converter only ever emits M, C and Z."""
    toks = [a or b for a, b in TOKEN.findall(d)]
    ops, i = [], 0
    while i < len(toks):
        t = toks[i]
        if t in "Zz":
            ops.append((t, []))
            i += 1
        elif t in "Mm":
            i += 1
            ops.append((t, [float(toks[i]), float(toks[i + 1])]))
            i += 2
        elif t in "Cc":
            i += 1
            # A C run may carry many implicit repeats before the next letter.
            while i < len(toks) and not toks[i].isalpha():
                ops.append(("C", [float(v) for v in toks[i:i + 6]]))
                i += 6
        else:
            raise ValueError(f"unexpected path command {t!r}")
    return ops


def bbox(ops):
    """Control-point bbox. Cubic hulls contain their curves, so this never
    clips the ink -- at worst it pads a hair, which the margin absorbs."""
    xs, ys = [], []
    for _, a in ops:
        xs += a[0::2]
        ys += a[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def emit(ops, dx, dy):
    """Bake the translation into the coordinates -- no wrapper transform."""
    def n(v):
        return f"{round(v, PRECISION):g}"

    out = []
    for cmd, a in ops:
        if not a:
            out.append("Z")
            continue
        pts = " ".join(
            f"{n(a[i] + dx)} {n(a[i + 1] + dy)}" for i in range(0, len(a), 2)
        )
        out.append(f"{cmd}{pts}")
    return "".join(out)


def build(d, w, h, color, adaptive):
    if adaptive:
        # svg:root matches only a standalone document, so an inlined copy keeps
        # inheriting the host page's `color` rather than being overridden here.
        style = (
            "\n  <style>\n"
            f"    svg:root {{ color: {INK_LIGHT}; }}\n"
            "    @media (prefers-color-scheme: dark) {\n"
            f"      svg:root {{ color: {INK_DARK}; }}\n"
            "    }\n"
            "  </style>"
        )
    else:
        style = ""

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}"'
        f' width="{w:g}" height="{h:g}" role="img"\n'
        '     aria-label="Two halves of a broken loaf pulling apart,'
        ' crumbs falling between them">\n'
        "  <title>BREADCRUMBS</title>"
        f"{style}\n"
        f'  <path fill="{color}" fill-rule="evenodd" d="{d}"/>\n'
        "</svg>\n"
    )


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else SRC_DEFAULT
    raw = src.read_text()

    # Take the ink path only. The white plate is discarded outright.
    ink = None
    for attrs in re.findall(r"<path\b([^>]*?)/?>", raw):
        fill = re.search(r'fill="([^"]*)"', attrs)
        d = re.search(r'd="([^"]*)"', attrs)
        if not (fill and d):
            continue
        if fill.group(1).lower() in ("#fefefe", "#fff", "#ffffff", "white"):
            continue          # the knocked-out plate
        ink = d.group(1)
    if ink is None:
        raise SystemExit(f"no ink path found in {src}")

    ops = parse(ink)
    x0, y0, x1, y1 = bbox(ops)
    w = round(x1 - x0 + 2 * MARGIN, PRECISION)
    h = round(y1 - y0 + 2 * MARGIN, PRECISION)
    d = emit(ops, MARGIN - x0, MARGIN - y0)

    print(f"source        {len(raw):>7} bytes, {len(re.findall(r'<path', raw))} paths")
    print(f"ink bbox      {x0:.1f} {y0:.1f} -> {x1:.1f} {y1:.1f}")
    print(f"new viewBox   0 0 {w:g} {h:g}  (margin {MARGIN:g} all sides)")
    print(f"subpaths      {ink.count('M')}\n")

    for name, svg in {
        "breadcrumbs-logo.svg": build(d, w, h, "currentColor", True),
        "breadcrumbs-logo-light.svg": build(d, w, h, INK_LIGHT, False),
        "breadcrumbs-logo-dark.svg": build(d, w, h, INK_DARK, False),
    }.items():
        (OUT / name).write_text(svg, encoding="utf-8")
        pct = 100 * (1 - len(svg) / len(raw))
        print(f"{name:30} {len(svg):>7} bytes  ({pct:+.0f}%)")


if __name__ == "__main__":
    main()
