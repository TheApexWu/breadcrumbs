# BREADCRUMBS — product premise (LOCKED 2026-08-22, hackathon day)

Name is a placeholder (decide later). This doc is authoritative; the ralph loop / PRD build
against it, not against the older maritime framing.

## One-liner
When a food recall drops, BREADCRUMBS tells a NYC operator which of *their* locations are exposed
and what to do — on a box in the back office, data never leaving the building.

## What it is
An always-on, **on-prem food-safety & supply-risk agent** for a NYC food operator. It watches
the live FDA recall feed, knows the operator's suppliers and locations, and the instant a recall
lands it answers three questions in seconds: **am I hit, how bad, what do I do.**

Category: on-prem supply-chain risk agent — a "food-safety copilot," not a dashboard.

## Locked decisions (from the Aug 22 premise pass)
- **POV = operator's console.** "MY locations, MY suppliers" is the default. City-scale (all 17K
  NYC establishments) is a secondary toggle for context + visual scale — not the default screen.
- **Hero moment = reactive recall-response.** A real recall drops → trace exposure → brief →
  recommend swap. The continuous supplier scorecard is the ambient backdrop, not the lead.
- **Buyer = generic "NYC food buyer," demoed through a restaurant group** (procurement + safety).
  Grocer/shelf-pull is the adjacent market, not the demo.
- **Provenance = first-class IF the real data holds, one-beat as the floor.** Stretch: origin firm
  location (real, openFDA) + the commodity's typical source countries (real, UN Comtrade). Floor:
  show origin on the recalled lot only; do NOT build the full farm→port→NYC import graph.

## Three pillars — each a VERIFIED real-data asset, not a promise
1. **Exposure** — real openFDA recalls × operator suppliers × operator locations → "am I hit."
2. **Risk grading** — real openFDA distributor recall history (Dole 205 Class-I, Fresh Express 110,
   Sysco 24, Baldor 0) + real DOHMH health grades → which suppliers are slop, which of my exposed
   sites are already fragile.
3. **Action** — hold / pull / swap-supplier, reasoned locally by Nemotron.

## Why it MUST be local (load-bearing, not decorative)
Supplier contracts, margins, sourcing = trade secrets; no operator POSTs that to a cloud LLM.
FSMA 204 makes traceability a legal mandate. Always-on + private = only possible on the GB10.
This is the reason the hackathon's "local business agent" brief is satisfied for real, not as a gimmick.

## Principles
- **Instrument, not oracle.** Reports real state (real recalls, grades, distributor history). The
  modeled parts (supplier→site links) and any simulation are visibly labeled. No black-box prediction.
- **The wow is the operator's own city in 3D** (Sixth Borough heritage — 45K+ real buildings,
  LiDAR heights), risk glowing on the real blocks. Same deck.gl stack, no engine swap.

## Data provenance (what's real vs modeled — keep honest on stage)
- REAL/free/offline: openFDA recalls (29,310; 301 Class-I E.coli; current); DOHMH grades (17,204
  geocoded); NYS food stores (11,224); distributor recall history; Sixth Borough buildings; Comtrade
  origin (partial). All cacheable → runs unplugged.
- MODELED (label it): supplier→restaurant edges (proprietary in reality — the FSMA-204 gap itself),
  the operator's specific portfolio, COVERS/DAY exposure multiplier.

## Demo script — 90 seconds
- **0:00 Idle watch.** 3D NYC. The operator's ~12 restaurants lit among the city. Sentinel
  "● watching · local." Supplier scorecard visible: Baldor clean, Dole/Fresh Express/Sysco hot.
- **0:15 The local claim.** "This runs entirely on the GB10. No cloud. The supplier list never
  leaves the building."
- **0:25 Recall drops.** Real openFDA item hits the feed. Alert. Sentinel: `ingest_recall` →
  "Dole leafy greens · Class I · E. coli" (real product text).
- **0:40 Trace.** `trace_forward` → the operator's exposed restaurants light red on their actual
  blocks. "3 of your 12 sites source this through [distributor]." [links MODELED — say so]
- **0:55 Compounding.** `flag_compounding` → "2 of those already carry a C health grade — top priority."
- **1:05 Brief + act.** "Hold these lots. Swap to Baldor — 0 recalls on record vs Dole's 205 Class-I."
- **1:20 Why care.** "That trace took 4 seconds. Today it takes 3 days of phone calls — and it ran
  on a box you own, offline." End.

## Vision expansion — folded Aug 22 (see mockups/vision.html)
BREADCRUMBS is a **living food-safety system**, not a lookup tool: always-on Watcher → continuous
risk scoring → personalized alerts. Four live risk dimensions, all real data:
1. **Recall exposure** (29,310 recalls) · 2. **Allergen radar** (6,896 undeclared-allergen recalls —
the #2 cause, 15× E. coli) · 3. **Supplier risk** (distributor recall scorecards) · 4. **Establishment
risk** (155,091 critical food-handling violations).
- **Allergen radar** = tag recalls by allergen (real); flag the operator's category exposure (modeled;
  per-menu-item matching needs menu data = roadmap, labeled).
- **Notification preferences** = the operator sets, in plain English OR toggles, what wakes them
  {severity, scope, categories, allergens, channel, quiet-hours} → kills alert fatigue.
- **Channel = Telegram** (real send; I/O not inference, so it's rule-clean) + mock phone fallback offline.
Folded into the loop: M0 tags recalls by allergen; M1 adds the preference profile; M2 emits allergen_match.

## Open before ralph loop (morning)
- Pick the operator's real portfolio (~12 named DOHMH restaurants) → makes "my sites" concrete + real.
- Name decision.
- Realign PRD.JSON milestones to this premise (currently maritime).
- Provenance stretch: wire origin beat (openFDA firm state + Comtrade commodity origin).
