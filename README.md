# ◈ BREADCRUMBS

**An always-on, on-prem food-safety agent for a NYC food operator.** When an FDA recall drops,
BREADCRUMBS tells you — in seconds, offline, on the box — **which of your locations are exposed,
how bad, and what to do.** Not a dashboard: an agent that watches, reasons, and acts.

> *"When a food recall drops, BREADCRUMBS tells a NYC operator which of their sites are exposed and
> what to do — on a box in the back office, data never leaving the building."*

Built for the **Dell × NVIDIA AI Factory (BuilderBase) hackathon**, Aug 22 2026.

---

## Why it matters
48M Americans get food poisoning a year; 3,000 die. When a recall or undeclared-allergen alert hits —
hundreds a year — an operator has *hours* to answer "am I exposed?" Today that's days of manual
invoice-and-phone-call scrambling. One missed recall = an outbreak (Chipotle's 2015 E. coli wiped ~$11B
in market cap). BREADCRUMBS turns that scramble into a 4-second automated brief.

## Why it must be local
An operator's supplier list, volumes, and margins are trade secrets — they will never send them to a
cloud LLM. And FSMA 204 makes lot-level traceability a legal mandate. So the agent runs **on-premises,
private, on the GB10.** Sovereignty is the product — one local brain, and the only thing that leaves the
building is the alert.

## How it works
```
FDA recall lands ─▶ [MongoDB change stream] ─▶ Agent swarm (local Nemotron via NemoClaw)
                                                   Watcher → Tracer → Risk → Briefer → Comms
                                                        │        │        │        │       │
                                     which sites got the lot ◀──┘   how bad ◀┘  brief ◀┘  Telegram
```
- **Exposure** — real openFDA recalls × your suppliers × your locations.
- **Risk** — real distributor recall history + each site's real *critical* DOHMH food-handling violations.
- **Action** — hold / pull / swap-supplier, delivered as a Telegram alert.

## Four live risk dimensions (all real, free, offline-cacheable data)
| Dimension | Source | Scale |
|---|---|---|
| Recall exposure | openFDA food enforcement | 29,309 recalls |
| **Allergen radar** | openFDA (undeclared-allergen) | 6,896 — the #2 cause |
| Supplier risk | openFDA recall history by firm | Dole 205 Class-I, Baldor 0* |
| Establishment risk | NYC DOHMH critical violations | 155,091 |

\* firms with `0` recalls are labeled **unverified** (no openFDA name match ≠ a clean record).

## Stack
- **MongoDB** (required) — documents + 2dsphere geo (`$near` blast-radius) + aggregation (`$lookup`
  joins) + a **change stream** as the always-on Watcher + `agent_memory` (survives restart, dedupes).
  *Not a JSON store — every use is something a flat file can't do.*
- **NemoClaw + local Nemotron** on the GB10 (OpenClaw off-box for dev, one adapter to swap).
- **deck.gl** — 3D NYC console: extruded LiDAR buildings (from the Sixth Borough engine), risk
  ground-heat + building tint, supplier hubs, supply-flow, search-spotlight, free-fly camera.
- **openFDA · NYC DOHMH · NYS Ag&Markets · UN Comtrade** — the data.

## Repo layout
```
globe/            the deck.gl consoles — food3d.html (3D, primary), food.html (2D)
globe/assets/     cached real data (recalls, DOHMH, distributors, buildings) — offline
agent/ sim/ db/   backend (loop-built): swarm, recall-response, Mongo queries      [ralph branch]
bridge/           the ONLY backend↔frontend seam (Mongo-backed JSON + CONTRACT.md) [ralph branch]
rust-engine/      experimental Bevy 3D fly-through (parallel track)                 [rust branch]
mockups/          product-concept, vision, theme-lab
docs/             premise, onboarding, branching, system-map, ideas
PRD.JSON          milestones the ralph loop builds against
```

## Branches
- `main` — maritime fallback, frozen.
- `food` — **shared base** (frontend + data + docs). Teammates PR here.
- `ralph` — the autonomous loop's backend build (backend-only). Don't hand-edit.
- `rust` — experimental Bevy engine (parallel, upside only).
- `ui-*` / `assets-*` — teammate playgrounds off `food`.

Ownership + workflow: [`docs/branching.md`](docs/branching.md).

## Run it
```bash
git clone https://github.com/TheApexWu/breadcrumbs.git && cd breadcrumbs && git checkout food
# start MongoDB as a replica set (change streams need it):
mongod --dbpath ./.mongo --replSet rs0 &   # then: mongosh --eval 'rs.initiate()'
python3 scripts/load_mongo.py               # load cached data into Mongo
cd globe && python3 -m http.server 8777     # open http://localhost:8777/food3d.html
```
On the console: click a supplier to trace it · type a cuisine (e.g. `pizza`) to spotlight · `⚠ SIMULATE
RECALL` to watch exposure light up. Drag the HUD panels; free-fly with drag-rotate + scroll.

## Status
Backend **M0–M5 built + verified** (Mongo load, operator model, recall-response, agent swarm, bridge,
Telegram). **M6–M8 human-gated** (on-box Nemotron + real GB10 telemetry, agent-quality, pitch).

## Honesty by design
Every payload separates **real** from **modeled**. Real: recalls, violations, distributor history,
buildings. Modeled (labeled in UI + narration): supplier→site links (proprietary in reality — the
FSMA-204 gap itself), the illustrative operator portfolio. An instrument, not an oracle.
