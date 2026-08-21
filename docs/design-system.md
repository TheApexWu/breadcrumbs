# STRAITS — design system (maritime C2 / intelligence terminal)

Kill the vibecode. Every choice below is deliberate. References: Palantir Gotham, ECDIS
nautical charts, NATO APP-6 symbology, Bloomberg terminal. The console must read as an
*instrument*, not an art piece.

## Principles
1. **Color is meaning, not decoration.** Status hues (green/amber/orange/red) appear ONLY on status. Everything else is neutral ink + one brand accent.
2. **Dense but aligned.** 8px base grid. Hairline (1px) chrome. Sharp corners (0–2px radius, consistent). No rounded-soup, no drop-shadow gloss.
3. **Honest by design.** A persistent classification banner `UNCLASSIFIED // SIMULATION` — authentic C2 chrome *and* it doubles as the declared-fabulation label. Observed vs simulated data are visually distinct (solid vs hatched/ghosted).
4. **Restraint in motion.** No gratuitous spin. Motion is purposeful: a sonar sweep on a monitored chokepoint, a pulse on a new alert. Nothing else moves without a reason.

## Color tokens
```
--abyss    #060a12   page
--panel    #0b111c   surfaces
--panel-2  #0e1626   raised
--line     #1b2740   hairline borders
--ink      #c3ccdd   primary text
--ink-mut  #6b7a95   labels / secondary
--ink-faint#38455e   grid / disabled
--brand    #3fb6c9   ONE accent — cold radar cyan (alt: amber #e0a95a for warmth; pick one)
-- status (ONLY on status) --
--nominal  #3fb950   green   · under control
--watch    #d29922   amber   · anomaly building
--warning  #e0823d   orange  · projected impact
--critical #e5484d   red     · active disruption
```
Brand decision: **cyan** reads "naval C2 / radar," amber reads "warm/editorial." Recommend cyan; amber then becomes purely the WATCH status. Do not use both as brand.

## Typography
- **Data / mono:** IBM Plex Mono or JetBrains Mono (self-host a woff2, don't rely on system mono — that's the vibecoded tell). Tabular figures on.
- **Labels / headers:** a tight grotesk — IBM Plex Sans Condensed or Space Grotesk. UPPERCASE, tracked `+0.12em`.
- **Scale:** 10 (micro-label) · 11 (data) · 12 (body) · 14 (panel title) · 20 (brand). Line-height 1.5 for data blocks.

## Components (one kit, reused everywhere)
- **Panel:** hairline border, `--panel` fill, 3px corner ticks (targeting-reticle), header row (uppercase label, tracked) + body.
- **Stat tile:** micro-label / big value (tabular) / delta chip (status-colored). Used in the metric bar.
- **Alert row:** severity glyph (▲ crit / ● warn / ◦ watch) + text + right-aligned timestamp. Left border = severity color.
- **Data row:** name (ink) · meta (muted), 1px divider, hover raise.
- **Chip / filter:** ghost by default, brand-outlined when active.
- **Button:** ghost; `.armed` = critical outline (the BLOCK action).
- **Readout:** monospace, muted, tabular — coordinates, zoom, tok/s.
- **Classification banner:** thin top strip, centered, muted caps.

## Map / chart styling (this is what jumps it from dots to C2)
- **Nautical dark ocean** + a faint **graticule** (10° lat/lon grid, `--ink-faint`). Coastlines = 0.5px hairlines, land barely raised.
- **Vessel glyph = a directional chevron oriented by course** (not a circle) — sized by class, colored by type; this alone reads "tracked contact." Selected = white with a bracket reticle.
- **Ports = square nodes**; fill by congestion status. **Chokepoints = ring + slow sonar sweep** when monitored; red barrier + pulse when blocked.
- **Rerouted flow = dashed/animated path** (moving dash) distinct from solid observed lanes.
- **Observed vs simulated:** observed tracks solid; simulated-future tracks **hatched or 60% opacity** — the eye must tell them apart.

## Anti-patterns (the vibecode to remove)
- Default system monospace + one amber everywhere → replace with the token system + self-hosted fonts.
- Status colors used decoratively → status-only.
- Circles for vessels → chevrons.
- Constant auto-spin → purposeful motion only.
- Handwavy numbers with false precision → every metric shows its basis (see metrics methodology).
