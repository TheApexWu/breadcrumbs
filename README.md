# ◈ BREADCRUMBS

**An always-on, on-prem food-safety agent for a NYC food operator.** When an FDA recall drops,
BREADCRUMBS tells you — in seconds, offline, on the box — **which of your locations are exposed,
how bad, and what to do.** Not a dashboard: an agent that watches, reasons, and acts.

> *"When a food recall drops, BREADCRUMBS tells a NYC operator which of their sites are exposed and
> what to do — on a box in the back office, data never leaving the building."*

Built for the **Dell × NVIDIA AI Factory (BuilderBase) hackathon**, Aug 22 2026.

> 🏆 **Winner — Best Use of MongoDB.** The decision layer is real Mongo, not a JSON store: `$geoNear`
> blast-radius on a 2dsphere index, `$lookup`/`$group` aggregation joins, a **change stream** as the
> always-on Watcher, and a durable `agent_memory` that dedupes across restarts (retrieval that changes
> behavior). Ran live and offline on the GB10 with a local Nemotron model.

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
globe/            the deck.gl console — food3d.html (3D, primary), food.html (2D)
globe/assets/     cached real data (recalls, DOHMH, distributors, buildings) — offline
agent/            the 5-agent swarm (swarm.py) + Telegram/mock comms (comms.py)
db/               MongoDB aggregation primitives — $geoNear/$lookup/$group (queries.py)
sim/              operator model (operator.py) + recall-response engine (respond.py)
bridge/           the backend↔frontend seam — server.py + CONTRACT.md + sample payloads
tools/            telegram_relay.py — the live /ask + /report HTTP relay the console calls
scripts/          load_mongo.py (data → Mongo), fetch_recalls.py, verify_m0..m5.py (checks)
docs-notes/       m0..m5.md — how each milestone was built and verified
mockups/          product-concept, vision, theme-lab
docs/             premise, onboarding, branching, design-system, fda-report-spec
deck/             the pitch deck (pptx/pdf) + build_deck.py
PRD.JSON          the milestones the build targets
```

## Branches
- `main` / `food` — the full build (frontend + backend + data + docs). Both hold the shipped project.
- `ralph` — the autonomous loop's original backend build; its code now lives in `main`/`food`. Archival.
- `rust` — experimental Bevy engine (parallel, upside only).
- `Siri` / `nick` — teammate UI branches merged into the console.

Ownership + workflow: [`docs/branching.md`](docs/branching.md).

## Run it
```bash
git clone https://github.com/TheApexWu/breadcrumbs.git && cd breadcrumbs
pip install -r requirements.txt

# 1. MongoDB as a replica set (the change-stream Watcher needs it):
mongod --dbpath ./.mongo --replSet rs0 &   # then once: mongosh --eval 'rs.initiate()'
python3 scripts/load_mongo.py              # load the cached real data into Mongo
python3 scripts/verify_m0.py               # optional: prove the aggregations == pure-python control
```

**The console (what you demo):**
```bash
python3 tools/telegram_relay.py &          # the /ask + /report relay on :8899 (agent Q&A + Telegram PDF)
cd globe && python3 -m http.server 8777    # open http://localhost:8777/food3d.html
```
`⚠ SIMULATE RECALL` lights up the exposed sites · ask the box a question (grounded, local model) · `✈`
sends the FDA-formatted PDF to Telegram · drag the HUD panels · free-fly with drag-rotate + scroll.
The ask/Telegram buttons call `localhost:8899`, so run the console on the same machine as the relay.

**The swarm (the backend pipeline):**
```bash
python3 -m agent.swarm F-0757-2022         # run the 5-agent swarm on the Dole hero recall
```
Prints the full tool-call transcript (Watcher → Tracer ∥ Risk → Briefer → Comms), the grounded brief,
and the dedup state. Re-run it: the second pass recalls prior `agent_memory` and does **not** re-alert.

On the GB10, one env swap points the model adapter at the local Nemotron (`BC_BACKEND=nemotron
NEMOCLAW_URL=http://localhost:8000/v1`) — everything else is identical, fully offline.

## Status
🏆 **Won Best Use of MongoDB** at the Dell × NVIDIA AI Factory hackathon. Backend **M0–M5 built +
verified** (Mongo load, operator model, recall-response, 5-agent swarm, bridge, Telegram) and the live
demo ran **on the GB10 with a local Nemotron model, offline**. Roadmap (M6–M8): real GB10 NVML
telemetry + pull-the-cable test, per-menu-item allergen matching, multi-operator onboarding.

## Honesty by design
Every payload separates **real** from **modeled**. Real: recalls, violations, distributor history,
buildings. Modeled (labeled in UI + narration): supplier→site links (proprietary in reality — the
FSMA-204 gap itself), the illustrative operator portfolio. An instrument, not an oracle.
