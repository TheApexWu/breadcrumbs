# BREADCRUMBS — logo assets

The mark: two halves of a broken loaf pulling apart, crumbs falling between them.
Trace forward from the source, trace back from the plate — the crumbs are the product.

## Use these

| File | Use on | Ink |
|---|---|---|
| `breadcrumbs-logo-light.svg` | light backgrounds | `#0b111c` |
| `breadcrumbs-logo-dark.svg` | dark backgrounds — the console, the deck | `#e8edf4` |
| `breadcrumbs-logo.svg` | anywhere the theme is unknown | `currentColor` |

All three are the **same geometry** — one `<path>`, 103 subpaths, `fill-rule="evenodd"`.
Only the ink colour differs. Background is transparent in all three.

`breadcrumbs-logo.svg` is the one to reach for by default:

- **Inlined in HTML** it inherits the parent's `color`, so it follows whatever
  theme the page is already in. Set `color` on an ancestor to recolour it.
- **Standalone** (opened directly, or used in `<img>`) it falls back to `#0b111c`
  and flips to `#e8edf4` under `prefers-color-scheme: dark`. That switch is
  scoped to `svg:root`, which matches *only* a standalone document — so the
  inline case above is never overridden by it.

`fill-rule="evenodd"` is load-bearing. Drop it and every counter in the drawing
fills in, turning the line art into solid black slabs.

Colours are the product palette from `globe/food3d.html` and the deck, not new ones.

## Do not

- Do not add a background plate. These are transparent by design.
- Do not recolour to anything outside the palette above.
- Do not re-export from the raster source; regenerate from `source/` instead.

## Provenance

`source/breadcrumbs-logo.raw.svg` is the unmodified output of the converter the
raster illustration was run through. `clean_logo.py` turns it into the three
shipped files:

1. **Drops the white plate.** The converter emitted two paths: a full-canvas
   `#fefefe` rectangle with the artwork knocked out via evenodd, plus the same
   103 shapes filled dark. The plate is redundant and forces an opaque
   background on a logo. Removing it is most of the 58% size reduction
   (46,586 → 19,381 bytes).
2. **Recentres the canvas.** Margins in the raw file ran 44.2 / 15.7 / 56.2 /
   22.5. Now a uniform 24 on all four sides, baked into the coordinates rather
   than applied as a wrapper transform.
3. **Tokenises the ink.** Raw was hardcoded `#181819`, which belongs to neither
   theme.
4. **Rounds to 1 decimal.** 0.1 unit on a ~1040-unit canvas is well below a
   pixel at any size this renders at.

The trace itself was already clean and was left alone: no watermark fragments
survived thresholding, and every subpath has a near-exact mirror twin
(112825/112812, 69010/68995, 36469/36441 …), so the drawing's symmetry is intact.
The smallest shape is a 29-unit crumb — there is no speckle to cull.

**One thing to settle before this goes on anything public:** the raster it was
traced from was a watermarked stock illustration. The watermark is gone, but a
trace is a derivative work — so the licence needs checking, or the mark needs
redrawing from scratch, before it ships outside the hackathon.

## Regenerating

```bash
python3 brand/clean_logo.py brand/source/breadcrumbs-logo.raw.svg
```

Open `brand/preview.html` to check both themes at three sizes. It holds down to
about 200px wide; below that the crumb scatter mushes and the mark needs a
simplified small-size cut.
