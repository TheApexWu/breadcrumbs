# BREADCRUMBS — pitch script

> ## ⚠️ SUPERSEDED BY [`team-bible.md`](team-bible.md)
>
> The Team Bible (added 2026-08-22) is now the authoritative pitch spec. Where this file and the
> Bible disagree, **the Bible wins.** What changed:
>
> | | This file said | Bible says |
> |---|---|---|
> | **Mission** | recall response leads | **food traceability leads** — "our food supply is a black box"; the recall is the sharpest *proof*, not the headline |
> | **The contrast** | 72h → seconds | **4 seconds vs 2 days** — say it and stop talking |
> | **Problem framing** | 48M sickened (unverified) | the phone tree + **$0.04M–$1.1M** per restaurant firm, **~$10M** per grocer, **52%** of major recalls exceed $10M |
> | **Corpus** | 29,309 | **29,310** |
> | **Swap target** | "a verified record" (I inferred Jetro) | **Jetro, 0-of-1** — confirmed. A *verified low record*, never "clean" |
> | **Risk baseline** | raw violation counts | counts **vs citywide median 4**, range 0–56 |
> | **Coverage** | not addressed | **~100% of FDA lot-coded recalls, a minority of real outbreaks.** USDA FSIS is a labeled blind spot — Boar's Head 2024 would be invisible |
> | **Telegram** | "fires the alert" | **drafted, not auto-dispatched** |
> | **Change stream** | implied always-on | **observes inserts, does not yet auto-trigger `run()`** |
> | **Vocabulary** | "operator" throughout | prefer **food business / restaurant group / grocer**. Say **recall responder**, never *outbreak detector* |
> | **The ask** | 1 group, 30 days | **1 group, their real purchase records, 12 months** |
>
> New material the Bible adds and this file lacks: the **outbreak-coverage table** (Jif ✅ ·
> McDonald's/Taylor Farms ✅ · Yuma ⚠️ · Boar's Head ❌ · Chipotle ❌), the **FDA-aligned Recall
> Exposure & Action Report** format, the **business case** (FSMA 204 mandatory **July 20 2028**,
> ~$30B by 2030, four buyer segments), **8 judge Q&A kill-shots**, **role division**
> (Driver / Narrator / Q&A Lead), and **the six things we never overclaim**.
>
> All of the above is already reflected in the Figma deck.
> Keep this file only for the run-book below — the rest is historical.


**For M8.** Two deliverables with different clocks:

| | Length | Deadline | Owner |
|---|---|---|---|
| **A. Demo video** | 90 s | **18:00 hard wall**, BuilderBase portal | Alex |
| **B. Top-8 pitch** | 5 min | 19:30, live | Alex |

Every number below is traced to `docs/END-TO-END.md`. Anything not verified is marked ⚠.
`docs/premise.md`'s 90-second script is **superseded** — see *Do not say* at the bottom for why.

---

# A. Demo video — 90 seconds

Shot list and voice-over. Screen is `globe/food3d.html`; the telemetry HUD and transcript come
from the bridge if wired by then, otherwise from `bridge/out/*.json` on disk.

### 0:00–0:12 · Idle watch
> **Screen:** 3D NYC, camera slowly orbiting. The operator's 12 sites lit among 17,204. Sentinel
> panel reads `● WATCHING · local`. Supplier scorecard in the corner.

**VO:** "This is a New York restaurant group's back office. Twelve locations, on the real blocks
they occupy. The agent has been watching the FDA recall feed all night — on this box, in this
room."

### 0:12–0:22 · The local claim
> **Screen:** cut to the GB10 itself, or the telemetry HUD. Then the network cable comes out.

**VO:** "It runs entirely on the GB10. No cloud. Their supplier list never leaves the building —
and I'm about to unplug the network to prove it."

*Pull the cable here, on camera. Everything that follows must survive it.*

### 0:22–0:36 · The recall drops
> **Screen:** alert banner. Transcript: `Watcher ▸ watch_feed` → `Watcher ▸ ingest_recall`.

**VO:** "A real recall lands. Dole, Class One. Listeria on the harvest equipment for raw iceberg
lettuce. That's the actual FDA text — recall F-0757-2022."

### 0:36–0:52 · Trace
> **Screen:** `Tracer ▸ trace_forward` and `Risk ▸ score_risk.distributor` fire **side by side**
> — hold on the two concurrent lines. Five sites go red on their actual buildings.

**VO:** "Two agents go at once. One traces forward: five of their twelve sites source this. Those
supplier links are modeled — in the real world they're proprietary, and that gap is the whole
problem. The other pulls Dole's history: two hundred and five Class-One recalls on file."

### 0:52–1:06 · Compounding
> **Screen:** `Risk ▸ score_risk`. The five red columns rank by violation count.

**VO:** "Then the part that matters. All five of those sites already carry critical food-handling
violations — eleven, ten, eight, eight, ten. Not letter grades. Critical violations: wrong holding
temperature, contaminated contact surface, unapproved source. These are the sites most likely to
turn a recalled lot into someone in a hospital."

### 1:06–1:20 · Brief and act
> **Screen:** `Briefer ▸ brief`, then `Comms ▸ draft_sms` → `send`. Telegram alert lands on a
> phone in frame.

**VO:** "The brief is written locally. Hold the lot. Switch sourcing — and it names a distributor
with an actual clean record on file, not one the FDA has simply never heard of. Then it fires the
alert to the affected managers."

### 1:20–1:30 · Why care
> **Screen:** wide on the city, the unplugged cable visible.

**VO:** "That trace took seconds. Today it's three days of phone calls. And every bit of it ran on
a box they own, with the network on the floor."

---

# B. Top-8 pitch — 5 minutes

Six slides. Times are cumulative. Aim to land at 4:50.

---

## Slide 1 — The problem · 0:00–0:40

**Visual:** one number, full bleed. `48,000,000` — then beneath it, small: *1 in 6 Americans, every
year.* ⚠ *CDC estimate — verify the current figure and cite the year on the slide before stage.*

**Script:**
> "Forty-eight million Americans get sick from food every year. When the FDA announces a recall,
> the clock starts — and for the restaurant group that bought that lot, the first question is
> stupidly simple. *Did we get any of it?*
>
> Right now, answering that takes three days of phone calls to distributors. Federal law — FSMA
> Rule 204 — says they have to be able to answer it. The data to answer it doesn't flow. That's
> the gap."

**Beat:** land "three days of phone calls" and stop. Let it sit.

---

## Slide 2 — Why it has to be local · 0:40–1:25

**Visual:** two columns. Left, *What the agent must know*: supplier contracts · unit margins ·
sourcing routes · site violation history. Right, one line: *What no operator will POST to a cloud
LLM.* Draw the arrow between them and cross it out.

**Script:**
> "To answer that question the agent has to know your supplier contracts, your margins, your
> sourcing. That is the most sensitive data a food business owns. No operator is pasting it into
> a cloud model, and they're right not to.
>
> So the choice isn't 'local is nice.' It's local or it doesn't exist. Always-on, watching a live
> feed, holding trade secrets, answering in seconds — that combination is only possible on a box
> they own. That's why this is a GB10 product and not a SaaS dashboard."

**Beat:** this is the strategic claim. Slow down. Everything after is evidence for it.

---

## Slide 3 — The demo · 1:25–3:00

**Visual:** live console, or the 90-second video if live is risky. **Decide by 17:00 and rehearse
whichever you pick — do not improvise this at 19:30.**

Narrate the same six beats as Part A, compressed. The three moments that must land:

1. **The cable comes out** and nothing breaks.
2. **Two agents run concurrently** — point at the two lines on screen.
3. **Five sites, all five already fragile** — the compounding beat is the insight, not the trace.

If the console is not wired to the bridge by then, run the console for the city and the transcript
from `bridge/out/transcript.json` side by side, and **say** they're two windows onto the same
computation. Do not imply the console computed it.

---

## Slide 4 — How it works · 3:00–3:50

**Visual:** the pipeline, left to right, with the concurrent fork drawn as an actual fork:

```
openFDA 29,309 recalls ──┐
DOHMH 17,204 sites ──────┤
26,386 violation records ┼──▶ local MongoDB ──▶  Watcher ──▶ Tracer ┐
distributor history ─────┤     2dsphere +                  └ Risk   ┴──▶ Briefer ──▶ Comms
45,194 buildings ────────┘     aggregations                                          │
                                                                              Telegram / phone
```

**Script:**
> "Everything is cached locally — twenty-nine thousand FDA recalls, seventeen thousand New York
> establishments, twenty-six thousand with critical violation records, and forty-five thousand
> buildings at real LiDAR heights.
>
> Mongo isn't a JSON dump here. Geospatial indexes make blast radius a real query, the agents'
> tools *are* aggregation pipelines, and a change stream on the recalls collection is literally
> the Watcher — a new recall insert fires the swarm.
>
> Five roles: Watcher, Tracer, Risk, Briefer, Comms. Tracer and Risk run genuinely concurrently.
> Nemotron does the reasoning on the box, through NemoClaw."

**If asked about the model:** one adapter, one dispatch branch — the off-box dev path and the
on-box Nemotron path share an interface, so moving on-box was a one-line change.

---

## Slide 5 — Instrument, not oracle · 3:50–4:25

**Visual:** two columns, honestly labeled. **REAL** — FDA recalls, distributor recall history,
DOHMH critical violations, buildings, Comtrade origin. **MODELED** — supplier→site links, this
operator's portfolio, allergen→category exposure.

**Script:**
> "One thing we won't do, which is claim more than we have.
>
> The recalls are real. The violation histories are real. The buildings are real. The supplier
> links are modeled — and I want to be precise about why. In the real world those links are
> proprietary; the operator has them, we don't. That's not a shortcut in our demo, **that's the
> FSMA-204 gap itself.** Give the agent the real links and the modeled label goes away.
>
> And it refuses to overclaim in a way you can check. We had a bug where it recommended switching
> to a distributor with zero recalls — except zero meant the FDA had never heard of them. Absence
> of evidence, not a clean record. We fixed it to prefer a supplier with an actual record on file,
> and to say 'unverified' when it can't tell. The agent labels what it doesn't know."

**Beat:** the bug story is the strongest thirty seconds in the pitch. It proves the honesty claim
instead of asserting it. Do not cut it for time — cut Slide 4 instead.

---

## Slide 6 — The ask · 4:25–4:50

**Visual:** the product line, then one ask.

**Script:**
> "BREADCRUMBS is an always-on food-safety agent that runs in the back office and answers *am I
> hit, how bad, what do I do* in seconds, offline.
>
> Next is the pilot: one restaurant group, their real supplier list, thirty days. The modeled edge
> becomes real on day one — and then we find out how many recalls a year they've been absorbing
> without ever knowing they were exposed."

---

# Demo run-book — do this before recording, and again before 19:30

1. `db.agent_memory.drop()` — **otherwise the second run dedups and silently sends no alert.**
2. `build_portfolio()` if `load_mongo.py` has been re-run since — otherwise exposure returns `[]`
   and the demo reports zero hits with no error.
3. `.venv/bin/python bridge/server.py --write-out` — the committed `bridge/out/*.json` predates
   the swap-target fix and still says `BALDOR`.
4. **Vendor deck.gl locally.** `globe/food3d.html:73` loads from `unpkg.com`; the pull-the-cable
   moment is a white screen otherwise. This is the single highest-risk item in the demo.
5. Confirm `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` are in env and the phone in frame is on that
   chat. If the send is at all uncertain, use the mock-phone fallback — it writes
   `bridge/out/alert.json` with zero network and looks identical on camera.
6. Run the whole thing once with the cable actually out.

---

# Do not say

| ❌ Don't | ✅ Instead | Why |
|---|---|---|
| "Swap to Baldor — zero recalls versus Dole's 205" | "Swap to a distributor with a verified record on file" | Baldor's zero is *no openFDA name match*, not a clean record. This is the artifact `e22220b` and `ad9f5f6` both removed. It is now the honesty story — don't reintroduce the bug as a talking point. |
| "Two of those already carry a C health grade" | "All five already carry critical food-handling violations — 11, 10, 8, 8, 10" | Hard rule 6. Letter grades are a composite of vermin, facility, paperwork and temperature. Claiming a grade measures ingredient safety is the exact overclaim we say we don't make. |
| "Three of your twelve sites" | "Five of twelve" | The premise doc predates the built backend. The computed answer is 5. |
| "The agent decided…" | "The agent computed… and wrote the brief around it" | Every number comes from `respond()`; the LLM only writes the sentence. Assertions in `swarm.run()` crash if they disagree. That's a strength — say it. |
| "It predicts which sites will have an outbreak" | "It reports which sites are exposed and which are already fragile" | Instrument, not oracle. No prediction anywhere in the system. |
| Quoting a live tokens/sec number | Read it off the HUD, or don't cite it | ⚠ Telemetry is a stub off-box (all `null`). Real NVML/tegrastats numbers land at M6. Don't rehearse a number you haven't seen on the box. |

---

# Numbers, verified

| Claim | Value | Source |
|---|---|---|
| openFDA recalls cached | **29,309** | `data/recalls.json`, M0 |
| Undeclared-allergen recalls | 6,896 | `docs/premise.md` ⚠ re-verify against the cache |
| DOHMH establishments | **17,204** | `nyc-restaurants.json` |
| Sites with ≥1 critical violation | **26,386 camis** / 16,656 of the 17,204 loaded | `data/crit-violations.json`, M0 |
| Buildings rendered | **45,194**, heights to 472 m | `manhattan_buildings.json` |
| Operator portfolio | **12 sites**, 8 produce-linked + 4 nearest-hub | M1 |
| Hero recall | **F-0757-2022**, Dole, Class I, Listeria | `bridge/out/response.json` |
| Exposed | **5 of 12** — JUST SALAD ×3, SWEETGREEN ×2 | `respond()` |
| Compounding | **5 of 5**, crit_violations 11/10/8/8/10 | `respond()` |
| Dole history | **205 Class-I of 236 recalls** | openFDA scorecard |
| GB10 | 128 GB unified, ~140 W, DGX Spark aarch64 | `STATUS.md` |
| 48M foodborne illnesses/yr | ⚠ **CDC — verify + cite the year on the slide** | external |
