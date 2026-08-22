# BREADCRUMBS — onboarding (Ritchie, frontend/UI)

Welcome aboard. This is the Dell × NVIDIA hackathon build (today). One-page catch-up so you can
start on the frontend without reverse-engineering anything.

## What BREADCRUMBS is (30 seconds)
An always-on, **on-prem food-safety agent** for a NYC food operator. When an FDA recall drops, it
tells the operator — in seconds, offline, on the GB10 — **which of their locations are exposed, how
bad, and what to do.** Not a dashboard: an agent that watches, reasons, and acts.

One-liner: *"When a food recall drops, BREADCRUMBS tells a NYC operator which of their sites are exposed
and what to do — on a box in the back office, data never leaving the building."*

Full premise: `docs/premise.md` (read this second).

## Why it wins this hackathon
Dell/NVIDIA are judging **local AI on their hardware.** Our edge: a buyer's supplier list is a trade
secret they'd never send to a cloud LLM → the agent *must* run on-prem → the GB10 is the product, not
a demo prop. FSMA 204 makes food traceability a legal mandate on top.

## THE WOW we're building toward (your UI work targets this)
The map is the stage; the **AI agents + the GB10** are the star. Four pieces, all frontend-heavy:
1. **Agent swarm view** — Watcher → Tracer → Risk → Briefer → Comms, running *concurrently*, each a
   live card showing status + streaming output. This is the "five agents in parallel on one box" flex.
2. **GB10 telemetry panel** — tokens/sec, GPU mem, watts, model name, as C2 chrome. Cheapest proof
   it's really on the hardware.
3. **Live agent reasoning** — Nemotron's actual streamed tokens over the real recall text (not the
   current fake `setTimeout` narration).
4. **SMS / Comms action** (your idea) — the Comms agent drafts + fires an SMS to affected site
   managers. A real phone buzzing on stage = the most tangible wow in the room. This is pillar 3.

## Where we are (built + real)
- **Real data, all free/offline-cacheable** (in `globe/assets/`):
  - `nyc-restaurants.json` — 17,204 geocoded NYC restaurants w/ DOHMH health grades.
  - `nyc-stores.json` — 11,224 food stores. `nyc-nta.geojson` — 262 neighborhoods.
  - `distributor-scorecard.json` — real openFDA recall history (Dole 205 Class-I, Sysco 24, Baldor 0).
  - `food-types.json`, `food-sources.json` — recall risk by food category + import origins.
  - `manhattan_buildings.json` — 45,194 buildings w/ LiDAR heights (from the Sixth Borough engine).
- **Consoles** (in `globe/`): `food3d.html` = the primary (pitched 3D NYC, extruded buildings, risk
  hexbins, distributor hubs, recall-trace). `food.html` = 2D fallback. `maritime` version on `main`.
- Premise is LOCKED (`docs/premise.md`). Data fetchers in `scripts/` (`fetch_nyc_food.py`, etc.).

## Where you plug in (frontend/UI — we'll firm up scope in person)
- **Polish `food3d.html`** — layout, motion, the C2 aesthetic (see `docs/design-system.md` for tokens;
  amber/cyan on near-black, hairline borders, IBM Plex / JetBrains mono). It's clean but first-pass.
- **Build the agent-swarm panel + GB10 telemetry** (the wow). Static mock first, wire to the model later.
- **Build the SMS/Comms action UI** — the draft + send flow, a phone-mockup for the demo.
- **The product/pitch one-pager** — `mockups/product-concept.html` is a starting visual; make it sing.

## Stack (deliberately dependency-light)
- **deck.gl 9** standalone from unpkg (one `<script>`), vanilla JS, no build step, no framework.
  Every console is a single self-contained `.html`. Easy to edit, fast to iterate.
- Data is static JSON fetched over a local server. Python only for the fetchers (data prep).
- ⚠️ For the offline GB10 demo, deck.gl + fonts must be **vendored locally** (still on unpkg now).

## Run it
```bash
git clone <repo> && cd straits && git checkout food
cd globe && python3 -m http.server 8777
# open http://localhost:8777/food3d.html   (also food.html, mockups/product-concept.html)
```
Click a distributor in the scorecard → camera traces its establishments. Hit `⚠ SIMULATE RECALL`.

## Conventions
- Branch: `food` (maritime is `main`, our fallback). Commit as yourself; small, real messages.
- New data → `globe/assets/`. New console/mock → `globe/` or `mockups/`.
- Keep consoles self-contained (no shared build). Match the design-system tokens, kill vibecode defaults.

## First sync
Grab me (Amadeus) once you've run `food3d.html` and skimmed `premise.md` — we'll split the swarm UI
vs console polish and lock your scope then.
