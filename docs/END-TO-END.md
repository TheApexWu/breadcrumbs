# BREADCRUMBS — end to end

**Verified against `origin/ralph` @ `e22220b` and `origin/food` @ `0ce1d32`, Aug 22 2026 ~13:00.**
Traced from the code, not from the milestone notes. Where the loop's self-report and the code
disagree, the code wins and the disagreement is flagged.

Companion docs: [`SYSTEM-MAP.md`](SYSTEM-MAP.md) (structure), [`pitch-script.md`](pitch-script.md)
(what to say), `bridge/CONTRACT.md` (the seam), `PRD.JSON` (the rules).

---

## The shape in one paragraph

A recall number goes in. Mongo aggregations turn it into *which of the operator's 12 sites are
exposed*, *how bad*, and *what to do*. Five tool-calling agent roles walk that computation and
narrate it. A local HTTP server (or a committed static mirror) hands the result to a 3D console.
An alert fires over Telegram, or to a file if the network is gone. **Every number in the brief is
computed by Python and Mongo; the LLM only writes the sentence around them.** That is the whole
system, and it is the honesty claim.

---

## Stage 0 — Acquisition (once, then never again)

Run by hand, off-box, before the demo. Output is committed. After this stage the system never
needs a network again — hard rule 4.

| Script | Source | Output | Volume |
|---|---|---|---|
| `scripts/fetch_recalls.py` | openFDA `food/enforcement` | `data/recalls.json` | **29,309 recalls**, full rows |
| `scripts/fetch_nyc_food.py` | NYC DOHMH Socrata `43nn-pn8j` | `globe/assets/nyc-restaurants.json` | 17,204 latest-graded establishments |
| (same, M0 addition) | DOHMH `critical_flag='Critical'`, grouped by camis | `data/crit-violations.json` | **26,386 camis** with ≥1 critical violation |
| `scripts/fetch_nyc_food.py` | openFDA, 10 distributor name searches | `globe/assets/distributor-scorecard.json` | 10 firms, class1 + total counts |
| `scripts/fetch_food_sources.py` | UN Comtrade | `globe/assets/food-sources.json` | commodity origin, partial |
| (Sixth Borough heritage) | NYC building footprints + LiDAR | `globe/assets/manhattan_buildings.json` | 45,194 polygons, heights to 472 m |

Two acquisition facts that matter downstream:

- **The full corpus takes ~8 minutes** (a single 1,000-row openFDA call is ~16 s). It is cached and
  `fetch_recalls.py` is idempotent. Do not re-fetch on the day.
- **`nyc-restaurants.json` is latest-graded-only** — one `critical_flag` string per site, not a
  count. That is why M0 had to go back to DOHMH separately for the violation *counts*. The letter
  grade in that file is **not** the risk axis (hard rule 6); `crit_violations` is.

---

## Stage 1 — Load (`scripts/load_mongo.py` → local MongoDB `breadcrumbs`)

Four collections, deliberately heterogeneous documents rather than flat tables — hard rule 3.

- **`recalls`** — 29,309 openFDA docs, tagged at load with `hazard_class`
  (`allergen` | `pathogen` | `foreign-material` | `other`) and a parsed `allergens[]`.
- **`establishments`** — 17,204 DOHMH sites, each merged with its `crit_violations:int`.
  **16,656 of 17,204 have `crit_violations > 0`.** `loc` GeoJSON Point + **2dsphere index**.
- **`distributors`** — 10 firms with real openFDA recall history. Five are geocoded real NYC-area
  facilities and carry `is_hub:true` (Baldor, Restaurant Depot, Jetro, Sysco Jersey City, US Foods
  Bronx). The producers (Dole, Fresh Express, Taylor Farms) keep their recall history but
  `loc=null` — they are recalling firms, not hubs.
- **`operator_sites`** — created empty here, **populated by M1**. 2dsphere index.
- **`agent_memory`** — not created here. Springs into existence on the swarm's first write.

> **Trap:** re-running `load_mongo.py` clears `operator_sites` back to empty. `build_portfolio()`
> must be re-run after, or `exposure()` silently returns `[]` and the whole demo reports zero
> exposure with no error.

---

## Stage 2 — The operator (`sim/operator.py`, M1)

`build_portfolio()` picks **12 real DOHMH establishments by camis** and gives each a supplier.
This is *the* modeled edge in the system, and it exists because the real thing is proprietary —
which is precisely the FSMA-204 gap the product is about.

Two link rules, both labeled `modeled-link`:

- **8 salad/produce sites** → linked to a *producer* (`DOLE FRESH VEGETABLES INC`,
  `FRESH EXPRESS INCORPORATED`, `TAYLOR FARMS, INC.`) — rule `produce-supplier`
- **4 other-cuisine sites** → linked to their geographically *nearest hub* — rule `nearest-hub`

The exposure join is one string comparison: `operator_sites.distributor == recall.recalling_firm`.
The full firm name is stored so it matches the recalls collection.

`preferences()` returns the alert profile — `min_severity: Class I`, allergen list, produce
categories, supplier scope, `channel: telegram`. `parse_profile(text)` turns plain English into
that dict, which is the "kills alert fatigue" claim on the vision page.

> **Known seam:** `operator_sites` stores full firm names, `distributors` stores short ones
> ("DOLE"). The `$lookup` between them returns `[]`. M2 works around it with a prefix match.

---

## Stage 3 — The response engine (`sim/respond.py`, M2)

`respond(recall)` is the **single source of truth**. Everything downstream reads it; nothing
downstream recomputes. It returns:

| Field | How | Class |
|---|---|---|
| `recall` | the openFDA doc + parsed `hazard_class`, `allergens` | **real** |
| `exposed_sites` | M1 `exposure()` — the `$match` + `$lookup` aggregation | **modeled** (the link is) |
| `compounding_count` | `db.queries.compounding([camis…])` — exposed sites with `crit_violations>0` | **real** |
| `distributor_risk` | prefix-match the recalling firm to a `distributors` doc | **real** |
| `origin` | recall `state` + Comtrade top sources for the inferred category | **real** |
| `allergen_match` | `ALLERGEN_CATEGORIES` dict, category-level only | **modeled** |
| `recommendation` | `hold` + `_swap_target(db)` | **modeled** |

Deterministic by construction: sorted fields, camis-sorted sites. Same recall in, byte-identical
payload out.

### The hero recall, computed

`F-0757-2022` — **DOLE FRESH VEGETABLES INC**, Class I, `hazard_class: pathogen`.
Product: *Marketside 12oz Classic Salad, UPC 6-81131-32894-4, SKU 3107*.
Reason: *harvest equipment used in harvesting raw iceberg lettuce tested positive for Listeria
monocytogenes.*

- **5 of 12 sites exposed** — JUST SALAD ×3, SWEETGREEN ×2, across Manhattan and Brooklyn
- **5 of 5 compounding** — `crit_violations` = 11, 10, 8, 8, 10. Every exposed site is already
  fragile.
- **Distributor risk: Dole = 205 Class-I of 236 recalls on file.** Real, from openFDA.

### The swap target, and the honesty fix that changed it

The original rule was "lowest `class1` hub" → **BALDOR, class1 = 0**. That is an artifact: Baldor
has `recalls = 0`, meaning *openFDA has no name-match for it at all*. Zero recalls is absence of
evidence, not a clean record. Presenting it as "safest" is the exact black-box-certainty failure
hard rule 10 forbids.

`e22220b` rewrote `_swap_target()` to prefer a distributor with a **real record** (`recalls > 0`),
whose low Class-I count is therefore *verified*, and to label a no-record firm
`unverified-nomatch` if it ever has to fall back. `origin/food`'s `ad9f5f6` made the same fix in
the console independently, an hour apart. Both teams caught it.

Among the five `is_hub` distributors: Baldor `0/0` and US Foods `0/0` are unverified; Restaurant
Depot `0/3`, Jetro `0/1` and Sysco `24/137` have records. Sorted by `(class1, firm)`, the new
answer is **JETRO — 0 Class-I of 1 recall on file**.

> ⚠️ **Two consequences nobody has handled yet.**
> 1. `bridge/out/*.json` was generated *before* `e22220b` and still says `swap_to: BALDOR`,
>    `swap_to_class1: 0`. The committed offline payloads no longer match live compute. Fix:
>    `.venv/bin/python bridge/server.py --write-out`.
> 2. **The money line in `docs/premise.md` is now wrong** — *"Swap to Baldor — 0 recalls on record
>    vs Dole's 205 Class-I"* is the artifact that was just removed. See `pitch-script.md` for the
>    replacement.

---

## Stage 4 — The swarm (`agent/swarm.py`, M3)

`run(recall_number, db, adapter)`. Five roles, six canonical tool-calls, one genuine concurrency.

```
Watcher   watch_feed          ─── the Mongo change stream fired (or the demo button did)
Watcher   ingest_recall       ─── load the recall doc
          │
          ├── Tracer  trace_forward           ┐ ThreadPoolExecutor(max_workers=2)
          └── Risk    score_risk.distributor  ┘ independent aggregations, truly parallel
          │
Risk      score_risk          ─── compounding; depends on the exposed camis list
Briefer   brief               ─── LLM writes ONE sentence around fixed numbers
Comms     draft_sms           ─── alert text + hold notice
Comms     send                ─── M5 dispatch
```

Three things in this stage are load-bearing for the pitch:

**1. The drift assertions.** Before briefing, `run()` calls `respond(recall)` and asserts the
swarm's own concurrent results match it:

```python
assert risk["compounding_count"] == response["compounding_count"], "swarm risk drift vs Response"
assert len(exposed_sites) == response["exposed_count"],            "swarm exposure drift vs Response"
assert risk["distributor_risk"]["class1"] == response["distributor_risk"]["class1"]
```

The agent cannot report a number the deterministic engine didn't produce. It would crash first.

**2. `ModelAdapter` is one swap point.** `backend="openrouter"` (off-box dev, OpenClaw runtime,
`z-ai/glm-5.2`) ↔ `backend="nemotron"` (on-box, NemoClaw). Same `complete(prompt, system)`
signature, one dispatch branch. **M6 is a one-line change.** The adapter also falls back to
`reasoning` when GLM returns `content: null`, and falls back to a deterministic template if the
model returns a reasoning dump — so the brief always renders.

**3. `agent_memory` changes behaviour, it isn't decoration.** First run on a recall → alert sent,
`record_run(alert_sent=True)`. Second run on the *same* recall → prior state recalled,
`deduped=True`, brief still produced, **no second alert**, `alert_count` stays 1. A *different*
recall still alerts. This is "survives its sandbox" — the state outlives the process.

> **Demo trap:** `db.agent_memory.drop()` before demoing, or the second press of the button
> silently declines to alert and it looks broken.

> **Change-stream caveat:** the always-on Watcher needs a Mongo replica set. On a standalone
> `mongod` it prints a message and returns. The demo path is the synchronous `run()`.

---

## Stage 5 — The bridge (`bridge/server.py`, M4) — the only seam

`ThreadingHTTPServer` on `127.0.0.1:8899`, stdlib only, CORS `*` so a `file://` console can fetch.

| Endpoint | Backed by | Static mirror |
|---|---|---|
| `GET /operator_sites` | M1 portfolio as GeoJSON, 12 features | `bridge/out/operator_sites.json` |
| `GET /response?recall=<id>` | **calls `respond()` directly** | `bridge/out/response.json` |
| `GET /transcript?recall=<id>` | **runs the swarm live** | `bridge/out/transcript.json` |
| `GET /alert?recall=<id>` | M5 alert payload | `bridge/out/alert.json` |
| `GET /telemetry` | stub off-box; NVML/tegrastats at M6 | `bridge/out/telemetry.json` |
| `GET /healthz` | liveness | — |

`<id>` accepts a `recall_number` or a `recalling_firm`; it defaults to the Dole hero recall.

**No drift by construction:** `/response` never recomputes, it calls `respond()`. The static
mirror is generated by the same function via `--write-out`, so live and offline agree —
*when the mirror has been regenerated* (see the M2 warning above; right now it hasn't).

**This is the seam the loop is forbidden to cross.** Hard rule 7: the loop touches only
`agent/ sim/ db/ scripts/ bridge/`. It may never edit `globe/`, `mockups/`, or `docs/`. If a task
seems to need a console edit, it writes a shape into `CONTRACT.md` instead.

---

## Stage 6 — Comms (`agent/comms.py`, M5)

Channel chosen from `profile.channel`:

- **Primary — Telegram.** Bot API `sendMessage`. Token and chat id from `TELEGRAM_BOT_TOKEN` /
  `TELEGRAM_CHAT_ID` **only**; a verification greps the tree to assert no literal is committed.
  `TELEGRAM_BASE_URL` can point at a local relay so `ok:true` is provable without a real send.
  Sending is I/O, not inference — so it does not violate the local-inference rule.
- **Fallback — mock phone.** `mock_phone_render()` writes `bridge/out/alert.json`. **Zero network
  calls.** The console reads it off the local filesystem. This is what makes the pull-the-cable
  demo survive.

`send_alert()` tries Telegram, falls back to the file. **It always lands.**

The alert text, grounded end to end:

> ALERT: Marketside 12oz Classic Salad UPC:6-81131-32894-4 SKU: 3107 recalled (Class I, harvest
> equipment used in harvesting raw iceberg lettuce was) — 5 of your sites exposed (5 with prior
> critical violations). HOLD lot and swap sourcing to BALDOR.

*(That trailing `BALDOR` is the stale-mirror bug. Regenerate.)*

---

## Stage 7 — The console (`globe/food3d.html`, human lane) — **and the gap**

The 3D console is a single 257-line file: deck.gl 9.0.38, `MapView`, **no basemap** — the city is
45,194 extruded real building footprints lit by a `SunLight`, over a `#070b12` void. A
`HeatmapLayer` ground-heat of all 17,204 establishments, restaurants appearing as pickable dots
above zoom 12.6, five lazy borough toggles, search-to-glow, free camera to 85° pitch, draggable
HUD panels, animated particles flowing along the supply arcs.

It is good. **It is also not connected to any of stages 1–6.**

```
$ grep -n '8899\|bridge/\|operator_sites\|transcript\|telemetry' globe/food3d.html
(no matches)
```

What the console does instead:

- fetches three **static JSON files** from `globe/assets/`
- invents the supply chain in-browser with `nearestHub()` — nearest of 5 hardcoded coordinates,
  by squared degrees. Not procurement, geometry.
- `SIMULATE RECALL` picks the highest-`class1` hub and fires **five `setTimeout` template
  strings** at 750 ms intervals, labelled `SENTINEL ▸ ingest_recall` … `brief`. **No LLM, no
  Mongo, no swarm.** It is a hand-drawn mock of the backend that now exists for real.

So the state of play: **the backend computes the true answer and the frontend performs a
lookalike of it, and they have never met.** Closing that is a contract-shaped job — replace the
`setTimeout` array with a `fetch` of `/transcript`, replace `nearestHub()` with
`/operator_sites`, replace the invented counts with `/response` — and it is the highest-value
unclaimed work in the repo.

---

## What runs where

| | Off-box (Alex's Mac) | On-box (GB10) |
|---|---|---|
| Data fetch | ✅ once, cached | never |
| MongoDB | ✅ `localhost:27017` | ✅ local |
| Swarm inference | OpenRouter `z-ai/glm-5.2` via OpenClaw | **Nemotron via NemoClaw** |
| Bridge | ✅ `:8899` | ✅ `:8899` |
| Console | `file://` | `file://` |
| Telemetry | stub, all `null` | NVML / **tegrastats** |

GB10: `ssh dell@100.113.10.122` (Tailscale) or `dell@promaxgb10-5ca9.local`. DGX Spark, aarch64,
128 GB unified, ~140 W. **`nvidia-smi` under-reports unified memory on GB10 — use `tegrastats`.**

---

## Real vs modeled — the ledger to say out loud

**Real:** openFDA recalls (29,309) · DOHMH critical-violation history (26,386 sites with ≥1) ·
distributor recall history · NYC building footprints and LiDAR heights (45,194) · Comtrade
commodity origin (partial — only Dairy & cheese, Nuts & spices, Fruit resolve; leafy greens
returns empty, and the code says so rather than inventing).

**Modeled, and labeled everywhere:** supplier→site links · the 12-site operator portfolio ·
allergen→category exposure (per-menu-item needs menu data — roadmap) · the covers/day multiplier
in the console.

The one that will get asked about: **the supplier links are modeled because in reality they are
proprietary — that gap is the product.** FSMA 204 makes traceability a legal mandate and the data
still doesn't flow. Say it that way and the weakness becomes the thesis.

---

## Open breaks, ranked

1. **Console ↔ bridge unwired.** Stage 7. Everything real is invisible.
2. **deck.gl loads from `unpkg.com`** (`globe/food3d.html:73`). Violates hard rule 4 — the
   unplugged demo dies on a white screen. Vendor it locally.
3. **`bridge/out/*.json` is stale** vs `sim/respond.py` after `e22220b`. Offline payloads still
   say `BALDOR`. One command fixes it.
4. **`docs/premise.md`'s 90-second script is stale** on two counts: the Baldor line, and "2 of
   those already carry a C health grade" — hard rule 6 forbids claiming the letter grade measures
   ingredient safety, and the built system uses `crit_violations` instead. Corrected in
   `pitch-script.md`.
5. **`amadeus@100.106.203.57ure.py`** still in the tree on `ralph` (cleaned on `food`).
6. **M6–M8 are human-gated and untouched** — local Nemotron, real telemetry, agent-quality
   verdict, pitch. Hard wall 18:00.
