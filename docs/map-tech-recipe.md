# STRAITS — Google-Maps-grade detailed OFFLINE geography (recipe, verified Aug 21 2026)

Source: deep-research `was5zk87m` (93 agents, adversarially verified). The current `ne_110m`
GeoJSON is coarse (Suez = a rough line). To resolve canals/rivers/coastlines to street level as
you zoom, offline, use **vector tiles (PMTiles) rendered by MapLibre, with deck.gl on top**.

## 1. Generate a small regional tile archive (don't build the 120 GB planet)
Two paths — pick the fast one:
- **FASTEST — carve a region from a remote planet archive (HTTP range requests, no full download):**
  ```
  pmtiles extract <remote-or-local-planet>.pmtiles theater.pmtiles \
    --bbox=25,10,60,42 --maxzoom=14        # Suez / Red Sea / Med / Gulf
  ```
- **Or build from OSM with Planetiler + the Protomaps profile** (regional):
  ```
  java -jar planetiler.jar --area=egypt --download --output=theater.pmtiles
  # or --clip=theater.geojson for a custom bbox
  ```
- Or `tippecanoe -zg -o out.pmtiles input.geojson` from your own GeoJSON.
- **Size control:** each zoom level ~doubles the file. bbox-clip + cap `--maxzoom` (z14–16 gets
  canals/harbors) → demo-sized. Measure after the first build, trim maxzoom if big.

## 2. Render: MapLibre basemap UNDER deck.gl (recommended)
- MapLibre GL JS registers the `pmtiles://` protocol (the `pmtiles` JS lib) and serves `theater.pmtiles`.
- deck.gl composites via **`MapboxOverlay({interleaved:true})`** — moving vessels / arcs / labels
  draw above the vector chart; use `beforeId` to sit them below MapLibre's own text.
- (Alt: deck.gl `MVTLayer`/`TileLayer` reading PMTiles directly — more DIY styling, no MapLibre.)
- This is a real refactor: our console is currently pure standalone deck.gl; this swaps in a
  MapLibre map as the base + deck as an overlay. Adds `maplibre-gl` + `pmtiles` deps.

## 3. Detail sources (what resolves at high zoom)
- **Canals:** OSM `waterway=canal` — Suez (relation 7719838), Panama. Named+large → surface z12+.
- **Rivers:** `waterway=river` (the Nile). **Coastlines:** OSM coastline / GSHHG full-res. Harbor polygons from OSM.

## 4. Dark C2 style
- **Protomaps 'dark' theme style JSON (CC0)** — matches the aesthetic; restyle water/land/labels to our tokens.
- (CARTO dark-matter / OpenMapTiles dark are alternates.)

## 5. ⚠ THE OFFLINE GOTCHA (the thing that breaks unplugged)
- **Glyphs (font PBFs) and sprites are NOT inside the PMTiles archive and NOT cached by the protocol handler.**
- Self-host them from **`protomaps/basemaps-assets`** and repoint the style's `glyphs` + `sprite` keys
  to local paths. Only then does the full chain (PMTiles + MapLibre + style + glyphs + sprite) run
  with the network unplugged.

## Offline checklist (for the unplug-the-ethernet demo)
- [ ] `theater.pmtiles` self-hosted · [ ] `maplibre-gl` + `pmtiles` vendored locally
- [ ] Protomaps dark style JSON local · [ ] glyphs (PBF) + sprite self-hosted, style repointed
- [ ] deck.gl `dist.min.js` vendored (not unpkg) · [ ] fonts self-hosted woff2
- Verify: pull the network, hard-reload — canals/coast/labels + vessels all render.

Performance: fine on a modest laptop and the GB10.
