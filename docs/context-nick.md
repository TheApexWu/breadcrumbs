# BREADCRUMBS — branch brief (`nick` lane)

**Status as of Aug 22 2026, ~11:45.** Working notes for the asset/UI lane. Not a spec —
`PRD.JSON`, `docs/premise.md`, `docs/branching.md` and `bridge/CONTRACT.md` remain authoritative.
Structural companion: [`SYSTEM-MAP.md`](SYSTEM-MAP.md).

---

## 1. What's committed on this branch

`docs/SYSTEM-MAP.md` + `mockups/logo-lab.html`, committed and pushed to `origin/nick`. **No PR
opened into `food`** — held pending review.

Two notes from doing it:

- **The branch got renamed.** It was `assets-nick` at 11:38 and `nick` three minutes later; the
  reflog records `Branch: renamed refs/heads/assets-nick to refs/heads/nick`, not initiated from
  this session (desktop-app branch session, most likely). `docs/branching.md` specifies human
  branches as `ui-*` / `assets-*`, so `nick` is off-convention — cosmetic, but the loop's docs
  reference the pattern.
- Fast-forwarded onto `food` first, so this branch now carries `docs/ideas.md`,
  `mockups/vision.html`, and the stray-`scp`-file deletion (`89c2c3f`).

§9 of the system map was updated before commit — it had gone stale within the hour.

---

## 2. The loop has not landed a milestone

All 9 PRD milestones are `completed:false`. `agent/ sim/ db/ bridge/` on `ralph` are the scaffold
only. Every commit on `ralph` since the scaffold is a hand-edit to `PRD.JSON`, not loop output:

| commit | change |
|---|---|
| `02d33de` | Telegram → M5 primary comms channel (real Bot API, token from env) |
| `777ac5c` | allergen radar → M0 tag + M2 match; notification-preference profile → M1 |
| `79e375a` | merge sync `ralph` ← `food` |

The loop is being *tuned*, not *run*. And it is backend-only by design — **it will never emit a
design.** Waiting on it for visual direction is waiting on the wrong process.

---

## 3. The brand-color gate is already cleared — by `vision.html`

`mockups/vision.html` (committed 11:22, `8025a60`) settles the question the logo lab was blocking on:

```
--brand:#3fb6c9    cyan — brand
--amber:#e0a95a    demoted to accent
--nominal:#3fb950  --watch:#d29922  --warn:#e0823d  --critical:#e5484d
--allergen:#c77dff NEW — nothing else in the repo knows about this token
```

Cyan as brand, amber demoted — which is what `docs/design-system.md` recommended and what the
concept page was violating. **Color is decided.** What remains open is the mark, not the palette.

### The actual coherence backlog

The consoles have drifted from the mockups — different token *names* and different *values*:

| | mockups (`vision`, `product-concept`) | consoles (`food3d`, `food`) |
|---|---|---|
| token names | `--abyss --ink --brand --critical` | `--bg --tx --cyan --red` |
| background | `#060a12` | `#05080f` / `#060910` |
| critical | `#e5484d` | `#e2564a` |
| nominal | `#3fb950` | `#5ac26a` |
| primary accent | **cyan** | **amber** (inverted) |

Three blacks, two reds, and the consoles lead with amber where the brand leads with cyan.
Type is bare `ui-monospace` / Menlo everywhere — **no typeface has actually been chosen.**
`docs/onboarding.html` runs a separate light/warm system (accent `#2f7d8c`) — deliberate, it's a
document not a console, but it shares zero tokens.

That table plus the missing `--allergen` purple **is** the design-coherence job. None of it is
blocked on the loop.

---

## 4. The three ideas

### 4.1 Web research as a secondary recall source

The strong version isn't scraping — it's two **structured** sources openFDA genuinely doesn't carry:

1. **USDA FSIS recalls** (meat, poultry, egg products). Different agency, entirely absent from
   openFDA. Structured feed, no extraction needed.
2. **FDA's own recall press releases.** Company announcements are public on day 0; the openFDA
   enforcement record appears only after weekly classification. **That lag is the feature** —
   "we saw it when the company announced it, not when the paperwork cleared."

This argues for a **third provenance tier** alongside real/modeled: `real-press` (announced, not yet
classified). That's a `bridge/CONTRACT.md` shape, not a scraper.

**Firecrawl self-hosted: recommend against for today.** Docker + Redis + a Playwright worker to read
what is, in practice, an RSS feed. Local-first alternatives in reach order:

| tool | use |
|---|---|
| `httpx` + `feedparser` | probably the entire job for FDA/FSIS |
| **`trafilatura`** | pip-only, best-in-class boilerplate removal, handles feeds + sitemaps |
| `crawl4ai` | Playwright-based, if JS-rendered pages ever matter |
| SearXNG (self-hosted) | discovery meta-search — overkill today |
| `monolith` | archive a page to disk for evidence provenance |

Extraction of brand/product/allergen from press-release prose is a job for **Nemotron on the GB10** —
which makes this a local-inference story rather than a cloud-API one.

**Hard constraint:** `hard_rules[4]` — the demo runs with the network unplugged. Fetch once, cache to
disk with a `fetched_at` stamp, render from cache.

### 4.2 Telegram inbound Q&A

Best of the three for the pitch, and cheaper than it looks. M5 already builds the **outbound** adapter
with a real bot token; inbound is the same bot plus a `getUpdates` poller. A judge can text it from
their own phone and the answer round-trips through the GB10 — the local-inference claim *demonstrated*
rather than asserted.

Not a competing idea: the team already logged "restaurant allergen + grade lookup" in `docs/ideas.md`.
This is the **channel** for it.

Two honest limits:

- **Per-item precision is out of reach.** "Chicken burrito" needs menu data we don't have; the PRD
  already scopes allergen matching to CATEGORY-level and labels per-item as roadmap. If the bot implies
  it knows what's in the burrito, we've broken the instrument-not-oracle rule the product rests on.
  The honest answer shape: DOHMH grade + critical violations (**real**), category-level recall exposure
  (**modeled**), allergen radar hit (**real** recall text, **modeled** link).
- **Name → CAMIS is a fuzzy match** against 17,204 rows with many rows per chain. Needs
  nearest-by-location disambiguation.

Ownership: M5-adjacent = loop-owned. Cleanest path is a CONTRACT addition
(`GET /place_check?name=&lat=&lon=`) with the bot as a thin client.

### 4.3 NYC map data

Already spec'd in `docs/map-tech-recipe.md` — just aimed at the wrong hemisphere (bbox `25,10,60,42`
is Suez). Swap in NYC, cap `--maxzoom=14`.

Highest visual payoff per unit of risk, and uncontested — `globe/` is human-owned.

- **Do the glyphs + sprite self-host FIRST.** It's the failure that only surfaces when the ethernet is
  actually pulled, at which point it's too late.
- **Land it before the brand pass, not after.** Cyan markers over a dark Protomaps basemap is a
  completely different color problem than cyan dots on black.

---

## 5. Sequencing

Map data (4.3) needs nothing from the loop — natural use of the runway. 4.1 and 4.2 both belong in
`bridge/CONTRACT.md` as shapes for the loop to implement, which is exactly the mechanism SYSTEM-MAP §8
describes for adding a feature without colliding with a force-push.

**Slide deck: hold.** It can cite the map section-by-section now, but §6's real-vs-modeled ledger is
the spine of the pitch and half of it is still `completed:false`.

---

## 6. Open decisions

- **The mark** — `TRAIL` / `TRACE` / `RETICLE ◈` / `SENTINEL` in `mockups/logo-lab.html`. Color is
  answered, so this is the last gate on SVG/favicon export and the `design-system.md` rewrite.
  Recommendation: **TRAIL** — survives the favicon collapse to source-plus-two-crumbs, and it's the
  only one that stays true if the placeholder name changes.
- **Typeface** — nothing chosen; everything is system mono.
- **PR into `food`** — held.

---

## 7. Does the map have a time dimension?

**Today: snapshot, point-in-time.** No date axis anywhere in `globe/food3d.html` or `globe/food.html`.

What looks like time isn't:

- `loop()` runs rAF but only drives `pulse=(Math.sin(now/360)+1)/2` — a glow oscillation on the
  recall highlight.
- `SIMULATE RECALL` fires five `setTimeout(f, i*750)` narration beats — scripted demo choreography in
  wall-clock seconds, not data time.
- `feed()` stamps log lines with `new Date().toLocaleTimeString()` — the wall clock, cosmetic.

What's rendered is latest-state: DOHMH latest grade per establishment, distributor **lifetime**
recall counts.

### The engine already exists, one file over

`globe/index.html` (maritime, frozen on `main`) has a **complete sim clock** that the food fork dropped:

```
DAY0 / STRIKE / simT          sim time base
playing, speed                play-pause
SPEEDS=[120,600,1800,7200]    4 speed multipliers
advance()                     per-frame vessel interpolation + visibility window
triggerStrike()               event fires when simT crosses a timestamp
clock + progress bar          scrub UI
```

It replays real AIS tracks across a 24-hour day and detonates the Key Bridge allision at the right
moment. Porting that pattern to food is a **known-good path, not new invention.**

### The data has dates — but nothing persists a history

| asset | date field | granularity |
|---|---|---|
| `nyc-restaurants.json` | `date` (e.g. `2026-08-18`) | **one** date per establishment — 5,873 in 2025, 11,331 in 2026 |
| `distributor-scorecard.json` | `recent` (e.g. `20240208` DOLE) | **one** date per firm — lifetime counts otherwise undated |
| `food-types.json` | none | categorized text counts |
| raw openFDA recalls | not cached at all | M0's job |

`scripts/fetch_nyc_food.py:31` queries DOHMH `43nn-pn8j` with `$order=inspection_date DESC
&$limit=50000` and then keeps **the latest graded row per establishment** — the history is fetched and
discarded. openFDA enforcement records carry `recall_initiation_date`, `center_classification_date`
and `report_date`; the scorecard build keeps only the max.

So: **dates exist upstream in both real sources; the repo currently persists one date per entity and
no event history.** A timelapse is a data-shape change (keep the rows), not a data-acquisition problem.

### Whether to build it

There's a real tension. The product's hero is **reactive** — a recall drops *now*, who's exposed,
what do I do. A timelapse is **historical/analytical** — a second mode, a different story.

Where it genuinely earns its place: the *establishing* beat. "We've been watching all along" plays far
better as 18 months of recalls blooming across the city than as a static dot field — and the allergen
radar's ~6,896 recalls become a visible rising wave rather than a number on a card. It also makes the
`real-press` vs `real-classified` lag from §4.1 **visible**: two dots, days apart, same recall.

Cheapest honest version: replay `recall_initiation_date` for the cached recall set over a scrubbable
date range, sites lighting as their supplier's recalls land — reusing the `index.html` clock verbatim.
Requires M0 to persist raw recall rows, so it's a CONTRACT ask, not a solo build.
