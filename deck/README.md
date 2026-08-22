# BREADCRUMBS — pitch deck

15 slides in 5 sections, with **speaker notes on every slide**.

| File | What it's for |
|---|---|
| `breadcrumbs-deck.pptx` | the deliverable — import this into Figma Slides |
| `breadcrumbs-deck.pdf` | fallback for handing out or presenting off a machine with nothing installed |
| `build_deck.py` | generates both; edit this, never the .pptx |

## Importing into Figma Slides

Figma Slides → **File ▸ Import** → pick `breadcrumbs-deck.pptx`. Speaker notes
come across with it; that is the whole reason this is a .pptx and not a stack of
SVGs. It also opens as-is in PowerPoint, Keynote and Google Slides.

This route exists because the Figma **Starter plan caps MCP tool calls**, and we
kept hitting the cap mid-write. Importing a file needs no API calls at all.

## Fonts

Archivo (headlines) and IBM Plex Mono (all data). Both are Google Fonts and both
are deliberately not Inter. If they aren't installed the renderer substitutes
silently and the deck still reads, but the mono columns stop lining up — install
them before presenting, or accept the substitution knowingly.

## Structure

| Section | Slides |
|---|---|
| Problem | Title · How it works today · 4 seconds vs 2 days · Why local |
| Demo | Live demo · Class I recall · Trace forward · Two real signals |
| Credibility | The output · Coverage boundary · Instrument not oracle · The swarm |
| Business | The FSMA 204 hinge · The ask |
| Internal | The six we never overclaim — **slide 15, do not present** |

## Where the content comes from

Everything traces to `docs/team-bible.md`, which is marked AUTHORITATIVE and
supersedes `premise.md` and `pitch-script.md`.

Speaker notes are **not** retyped here — `build_deck.py` parses them straight out
of `scripts/figma-speaker-notes.js`, so the .pptx and the Figma deck cannot drift
apart. Edit the notes in that one file and rebuild.

## One thing that needs a decision

The Bible's §C site table and the live backend disagree, and they are different
datasets rather than a bug:

|  | Sites | crit_violations |
|---|---|---|
| Team Bible §C | Site 03 / 05 / 07 / 09 / 11, masked CAMIS | 14 · 9 · 6 · 4 · 2 |
| Live backend | JUST SALAD ×3, SWEETGREEN, SALAD DON | 11 · 10 · 10 · 8 · 8 |

The deck currently follows **the Bible**, because the embedded speaker notes
quote "Site 05 (LES, 14 crit violations)" and "Site 11 (Harlem, 9)" verbatim —
so the slide matches what actually gets said out loud.

The cost of that choice: **the slide will not match the demo screen.** If a judge
reads both, they see different numbers. Flip `SITE_TABLE = "backend"` at the top
of `build_deck.py` and rebuild to invert the tradeoff — but then also fix the two
notes in `scripts/figma-speaker-notes.js` that name the old figures, or the
deck's own script contradicts its slide.

## Regenerating

```bash
python3 deck/build_deck.py
```

To re-export the PDF (needs LibreOffice):

```bash
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf --outdir deck deck/breadcrumbs-deck.pptx
```

The title slide pulls `brand/breadcrumbs-logo-dark.png`. That raster is a
convenience for PowerPoint, which cannot place SVG — the vector master is
`brand/breadcrumbs-logo-dark.svg`.
