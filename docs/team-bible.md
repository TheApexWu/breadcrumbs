# BREADCRUMBS — Team Bible (AUTHORITATIVE)

> Extracted from `team-bible.pdf`, added 2026-08-22. **This doc supersedes `premise.md`'s
> 90-second script and the earlier drafts in `pitch-script.md` wherever they disagree.**
> Lines marked "say out loud" are verbatim.

---

BREADCRUMBS — Team Pitch, Demo &

Onboarding

One doc. Read it once, then don't fumble the pitch, the demo, or the Q&A. Where a line is marked

as something to say out loud, say it verbatim — the honest framing is our credibility.

1. TL;DR — one-liner + what it is

The mission (lead with this):

"Our food supply is a black box. BREADCRUMBS makes it traceable — it knows where a food

product came from and where it went, so the instant something is wrong, you can follow the

crumbs back to the source and forward to every plate at risk."

The sharp, working proof (what the demo shows):

"The highest-stakes version of traceability is a recall. An FDA recall drops, and in seconds

BREADCRUMBS traces the affected lot to exactly which locations received it and what to do

— on a box in the back office, data never leaving the building."

What it is (2 sentences):

BREADCRUMBS is an always-on food-traceability agent. It watches the FDA recall feed and, the

moment a lot-coded recall drops, maps that product to the sites that received it (via the supplier

links), scores how bad it is, and says what to do — hold the lot, swap the distributor, alert the

manager — running entirely on-prem because supply-chain data (suppliers, volumes, margins) is a

trade secret that can't be POSTed to a cloud model.

Language discipline. Lead with "food traceability" / "trace it back to the source" — that is the

mission. Say "recall responder," never "outbreak detector" — that is the honest scope of what

works today. Go easy on the word "operator" (it reads corporate); prefer "food business," "the

people who move our food," or just name them — a restaurant group, a grocer.

2. Why you should care

Today an operator finds out about a recall from a distributor email, days later, then hunts through

spreadsheets to figure out which locations are hit. That's a phone tree across 12, 50, or 200

kitchens.

BREADCRUMBS did it in four seconds, on a box in the back office, with the supplier list

never leaving the building. That's the difference between a recall and an outbreak.

The stakes are real money. Restaurant per-recall cost runs a median of $0.04M–$1.1M per firm, and

the reputational tail is far larger. For grocers, the FMI/GMA study puts average direct recall cost at

~$10M, with 52% of major recalls exceeding $10M in total impact.

The contrast card: 4 seconds vs. 2 days. Land on it and stop talking.

2b. How this maps to real US outbreaks (know these cold)

Judges will ask "would this have caught [outbreak]?" Here is the honest, verified answer — we are

relevant to the FDA lot-coded ones and we say plainly where we are not:

Real US outbreak

Relevant?

Why

Jif peanut butter, 2022
(Salmonella)

YES

A real FDA Class-I lot-coded recall — exactly our
trigger. Verified: 24 real Class-I Smucker records in

the feed.

McDonald's / Taylor Farms

YES

FDA-regulated produce, lot-coded recall — we map it

onions, 2024 (E. coli)

to the sites that received the lot.

Boar's Head deli meat, 2024

NO — and we

USDA FSIS jurisdiction (meat/poultry), invisible to the

(Listeria — 10 dead, the deadliest
of the year)

say so

openFDA food feed. Our labeled coverage boundary.
v2 adds the FSIS feed.

Chipotle, 2015 (E. coli)

NO

Restaurant cross-contamination; no recall was ever

issued and the ingredient was never identified —

nothing to trigger on.

Yuma romaine, 2018 (E. coli)

PARTIAL

Commodity produce → a public advisory, not a lot-

coded recall — no specific lot to trace.

The honest headline: we cover ~100% of FDA lot-coded enforcement recalls, and a minority of the

full universe of epidemiological outbreaks. We sit downstream of CDC/FDA traceback and act the

instant a recall posts. Say "the fastest path from a recall to action," never "we catch outbreaks

early." Live sanity check on the real cadence: NY-distributed Class-I recalls in 2025–26 = 24 —

roughly 1–2 genuinely high-severity, NY-relevant events per month. A real alert stream, not a

firehose and not zero.

3. What's REAL vs. what's MODELED — our credibility

We separate the two on purpose. This is the credibility backbone: know which bucket everything is

in.

Element

REAL / MODELED

Source

Recall facts

REAL

openFDA food enforcement — e.g. F-0757-2022

Distributor recall history

REAL

openFDA firm-level recall counts

Site critical violations

REAL

NYC DOHMH inspection records
( crit_violations )

Site identities / CAMIS

REAL

DOHMH-geocoded establishments

Extruded buildings

REAL

LiDAR geometry (Sixth Borough engine)

Supplier → site → lot

MODELED

Operator supplier assignments — the FSMA-204 gap

links

Operator 12-site

portfolio

MODELED

(illustrative)

itself

Demo portfolio

Narration sentence

Generated

Local Nemotron, on-box; the decision logic is

deterministic Mongo

Two rules that never bend:

The modeled supplier→site link is the point, not a hole. FSMA 204 is the FDA rule that's

supposed to make this traceable and doesn't yet. We're modeling the gap the law is trying to

close. When a real operator plugs in their real supplier list, the modeled layer disappears.

A firm with no name match is labeled "unverified," never "clean." We never let an absence

of data read as safety. Jetro's 0-of-1 is a verified low record, not proof of a safer product.

Coverage boundary, stated not hidden: Source is FDA food enforcement only. USDA FSIS-

regulated products — deli meats, poultry, most red meat — are not in this feed. The 2024 Boar's

Head listeria recall (10 dead) would be invisible to this system. We cover ~100% of FDA lot-coded

enforcement recalls and do not claim outbreak detection.

4. The 90-second demo script — beat by beat

Format: [ACTION] = what you do on screen · "SPOKEN" = say verbatim · UPGRADE = only if live

is green. Total budget: 90s. Practice the close.

BEAT 0 — Cold open (0:00–0:12)

[ACTION] deck.gl 3D NYC console already up, idle. Slow free-fly over the operator's 12 extruded

site blocks, calm/green.

"This is a real NYC food operator — 12 sites, their actual buildings. BREADCRUMBS is

watching FDA recalls for them right now, and every byte of this is running on this box. No

internet."

HONEST TAG (say it): "The buildings and inspection data are real; this 12-site portfolio is

an illustrative operator we modeled — I'll show you what's real underneath in a second."

BEAT 1 — The recall drops (0:12–0:25)

[ACTION] Trigger the Dole case. On-screen event pops:  FDA Enforcement — F-0757-2022 .

"A recall just hit the feed. Dole iceberg lettuce. Listeria. Class I — that's the FDA's most

serious, 'reasonable probability of death.' This is a real recall, real number."

PRIMARY PATH (baked, always works): the F-0757-2022 record is loaded from Mongo and

replayed on click — deterministic, never fails.

UPGRADE (only if live is green): "That fired through a live MongoDB change stream — the

moment the record hit the collection, the Watcher agent woke up. Nobody polled anything."

BEAT 2 — Sites light red (0:25–0:38)

[ACTION] 5 of the 12 blocks flash red. Camera auto-pulls to frame them. Supply-flow arcs from the

Dole hub light up to those 5 sites.

"Five of their twelve sites buy Dole lettuce. Those five just turned red. The other seven are

fine — and knowing which is the whole game."

HONEST TAG (say it, don't wait to be asked): "The supplier-to-site link is the one modeled

layer — and that's the point: FSMA 204 is the FDA rule that's supposed to make this

traceable and doesn't yet. We're modeling the gap the law is trying to close. The 5 sites

are real CAMIS locations; the buy-relationship is illustrative."

BEAT 3 — Risk scoring (0:38–0:52)

[ACTION] Click one red site. Side panel: distributor recall history (Dole: 205 Class-I) + that site's

critical food-handling violations from DOHMH.

"Now it scores the exposure with two real signals. Dole's own recall history — 205 Class-I

records, that's real openFDA. And this specific site's critical violations from NYC health

inspections — the handling failures, not the letter grade in the window."

HONEST TAG: "Both of those are real, verified data. The letter grade is theater; critical

violations are what actually predict a handling failure."

BEAT 4 — Brief + the swap (0:52–1:05)

[ACTION] Briefer panel writes the recommendation. Highlight: swap Dole → Jetro.

"It writes the manager a brief and makes a call: stop buying from Dole for this SKU, move to

Jetro — zero-for-one on recall record versus Dole's 205. That's a decision, not a dashboard."

HONEST TAG on inference: "The numbers you're seeing — the 205, the swap logic — are

deterministic MongoDB aggregation, not a language model guessing. The local

Nemotron model writes the one plain-English sentence the manager reads. That split is

deliberate: the math can't hallucinate, and it runs offline."

Firms with no name match are labeled "unverified," never "clean" — say this if pushed on

Jetro's 0-of-1.

BEAT 5 — Report + alert (1:05–1:18)

[ACTION] "Generate report" → formal PDF/report renders. Then "Draft alert" → Telegram message

composed to the site manager.

"A formal incident report — for the file, for the health department. And a draft alert to the site

manager's phone, over Telegram. Draft, not auto-sent — a human still hits go."

PRIMARY PATH: report + Telegram draft are baked and render every time.

UPGRADE (if live): "That alert can actually send — the Comms agent is wired to Telegram on

this box."

BEAT 6 — Why-care close (1:18–1:30)

[ACTION] Full-screen the timer/contrast card: 4 seconds vs. 2 days.

"Today an operator finds out about a recall from a distributor email, days later, then hunts

through spreadsheets to figure out which locations are hit. BREADCRUMBS did it in four

seconds, on a box in the back office, with the supplier list never leaving the building. That's

the difference between a recall and an outbreak."

Land on "back office" and stop. Don't add a sentence.

4b. The agents — 5 roles, in plain English

BREADCRUMBS runs a small team of 5 software agents. Each is a focused role that does its job

and hands to the next, and every step is written to an inspectable transcript, so you can prove on

stage what actually happened. The honest version, no marketing:

#

Agent

What it does, in plain words

Real math, or the AI model?

1 Watcher

Sits and watches the FDA recall feed. The

Real — a live MongoDB change stream;

moment a new recall lands in the database, it

the database pushes it the new record,

wakes the team and loads the recall's details.

nothing polls.

2

Tracer

Answers "am I hit?" — cross-references the

Real query. The supplier→site link is the

recalled product against the suppliers and
locations to find which sites received the

affected lot.

one modeled piece (labeled everywhere).

3

Risk

Answers "how bad?" — pulls the distributor's

Real — openFDA + NYC DOHMH. Runs

real recall history (Dole: 205 Class-I) and

at the same time as the Tracer.

counts how many exposed sites already carry

real critical health-code violations.

4

Briefer

Writes the one-line, plain-English summary of

The only step that uses the AI model

what's happening and what to do.

(local Nemotron). It writes ONE sentence;

every number comes from the database,

never the model.

5

Comms

Drafts the alert + a formal hold notice and

Real send (messaging, not AI); works

sends it to the manager's phone over
Telegram.

offline with a mock-phone fallback.

The one thing to understand about the AI: only the Briefer talks to the language model, and only

to phrase a sentence. Every number — sites exposed, violations, the swap target — is computed by

deterministic database queries. That split is deliberate and it's our best answer to a judge: the

math can't hallucinate, and because the model only writes prose, the whole thing runs offline on the

box. Unplug the model and the decisions are identical — you just lose the nice sentence. (We are

also adding a live "ask the agent" box where local Nemotron answers grounded questions over the

same real data — that is the model doing visible, on-box work.)

5. Know your stack — capability / potency / if-a-judge-pushes

Every teammate should be able to speak any one of these six blocks cold. The rule: say what the

layer really does in this build, then the one honest line if a judge probes. Confidence comes

from not overclaiming.

5.1 — Local Nemotron on the GB10 (via vLLM)

nvidia/Llama-3.1-Nemotron-Nano-4B , served on the box at  localhost:8000  (OpenAI-

compatible), confirmed returning real completions.

CAPABILITY: A 4B instruct model running entirely on-prem, generating the human-readable

briefing sentence a Comms agent hands to the operator.

POTENCY: Zero network egress — the operator's supplier list never leaves the building —

which is the whole reason a food business could actually deploy this.

IF A JUDGE PUSHES ("is the AI making the decision?"): "No — and that's deliberate. The

decisions are deterministic MongoDB aggregation; the model only narrates the result into plain

English. We keep judgment in code you can audit, and use the LLM for the one thing it's good at

offline: writing the sentence. Right now the inference is thin — narration, not reasoning — and

we'd own that in the roadmap."

5.2 — MongoDB (four uses)

The system of record and the compute engine. Decisions live here, not in the model.

CAPABILITY: One store doing geo, joins, streaming, and persistent agent state: (a) 2dsphere
$near  to find operator sites near a risk; (b) aggregation  $lookup / $group  to join recalls →

suppliers → sites and roll up exposure; (c) change-stream Watcher that fires when a new recall

document lands; (d)  agent_memory  that survives restart and dedupes repeat alerts.

POTENCY: The exposure math (which sites turn red, the swap recommendation) is a real

deterministic aggregation over real recall + real site data — reproducible, no model in the loop.

IF A JUDGE PUSHES ("which of the four are actually live?"): "Geo  $near , the  $lookup

aggregation, and  agent_memory  (restart-persistent, deduped) are live and drive the demo. The

change-stream Watcher is built and observes inserts, but it isn't yet wired to auto-trigger the full

run()  pipeline — today we trigger the run explicitly. That's the honest edge."

5.3 — The Agent Swarm: Watcher → Tracer → Risk → Briefer → Comms

Five deterministic stages; the LLM only touches the last.

CAPABILITY: Each agent computes one concrete thing:

Watcher — detects a new recall document (openFDA enforcement record).

Tracer — resolves that recall's firm/product to the operator's suppliers and the specific sites fed
by them (this is where the labeled modeled supplier→site link is applied).

Risk — scores exposed sites using real DOHMH critical food-handling violation counts

( crit_violations , 0–56, median 4) — not the letter grade — plus the distributor's real recall

history.

Briefer — assembles the site list, the action, and the supplier-swap recommendation.

Comms — turns that into the operator-facing message (Nemotron narration).

POTENCY: Four of the five stages are pure deterministic computation over real data; the swarm

is an orchestration of auditable steps, not a chain of LLM guesses.

IF A JUDGE PUSHES ("how much is the LLM doing?"): "Exactly one stage — Comms — and

only for wording. Everything upstream is Mongo aggregation and scoring. The one modeled
input is the supplier→site link inside Tracer, and we label it modeled because it's the FSMA-204

traceability gap itself — the problem we exist to close, not a number we invented and hid."

5.4 — deck.gl 9 3D Console

The operator's back-office view; the real-data layers are the point, not the eye-candy.

CAPABILITY: A 3D NYC console rendering: extruded LiDAR buildings, a risk ground-heat layer,
supplier hubs, supply-flow arcs from distributor → site, cuisine search-spotlight, and free-fly

camera.

POTENCY: The buildings are real LiDAR geometry and the site positions are real geocoded

CAMIS locations — when a recall drops, the five genuinely-exposed sites turn red on their actual

footprints.

IF A JUDGE PUSHES ("is this just a pretty map?"): "The geometry and site coordinates are
real; the supplier→site arcs are the modeled link, same labeled caveat as everywhere else. It's a

decision surface — the red sites and the swap arc are the output of the Mongo aggregation,

drawn — not a decorative globe."

5.5 — Data Assets + Real-vs-Modeled Discipline

Know these numbers cold.

CAPABILITY: All-free, offline-cacheable, verified-this-build feeds — openFDA food enforcement

(29,310 recalls; 6,896 undeclared-allergen, the #2 cause; 301 Class-I E. coli), NYC DOHMH

(17,204 geocoded restaurants, risk = per-site critical violations), and distributor recall history

from real openFDA firm counts (Dole 205 Class-I, Fresh Express 110, Sysco 24, Jetro 0-of-1).

POTENCY: The demo anchor is a real recall — Dole F-0757-2022, iceberg lettuce, Listeria,

Class I → 5 real exposed sites (real CAMIS) turn red, swap → Jetro (0-of-1) away from Dole

(205) — with a verified real twin, Jif 2022 (Smucker/Salmonella, 24 real Class-I records), to

prove it's not cherry-picked.

IF A JUDGE PUSHES ("what's real vs. made up?"): "Real: recalls, DOHMH critical violations,

distributor recall history, buildings. Modeled and labeled as such: the supplier→site links and

the illustrative 12-site portfolio. A firm with no name match is labeled unverified, never clean."

5.6 — Why Local Is Load-Bearing / FSMA 204

CAPABILITY: The entire pipeline — Mongo, the swarm, Nemotron narration, the console —

runs on the GB10 with no data egress.

POTENCY: An operator's supplier list, volumes, and margins are trade secrets that can't be

POSTed to a cloud LLM; FSMA 204 makes lot-level traceability a legal mandate. Always-on +

private is only achievable on a local box — this is why the hackathon's "local business agent"

brief is met for real.

IF A JUDGE PUSHES ("couldn't you just call GPT for this?"): "Not for a real operator. The

moment you send the supplier graph to a cloud model you've leaked the trade secret the

business most wants to protect — and you can't run always-on inside the four walls. Local isn't a

constraint we accepted; it's the feature."

6. Judge Q&A — the honest kill-shot answers

Q1. "Unset the API key / pull the Nemotron model — what actually changes?"

"The narration sentence goes generic or templated. Nothing else. Every red site, every risk

score, the swap, the report — all deterministic Mongo aggregation. The LLM writes prose; it

doesn't make the decision. That's why we're comfortable running it offline — the load-bearing

logic can't hallucinate."

Q2. "Show me the change stream fire live."

If green: "Watch the event log —" drop a record into the collection, Watcher wakes, sites light.

If not wired live: "The demo replays a captured recall deterministically so it never fails on

stage; the change-stream Watcher is built against MongoDB's  watch()  — I can show

you the code path and the agent_memory that survives a restart and dedupes replays."

Never fake a live fire you can't guarantee.

Q3. "The supplier→site link is modeled — so what's actually real?"

"Real: the recalls (29,310 openFDA enforcement records), the inspection data (17,204

geocoded NYC restaurants with critical-violation counts), the distributor recall histories (Dole

205, Fresh Express 110, Sysco 24), and the buildings. Modeled and labeled as such: which

supplier feeds which site, and this illustrative 12-site operator. The modeled layer is exactly the

FSMA-204 traceability gap — the data the law is forcing into existence. When a real operator

plugs in their real supplier list, the model layer disappears."

Q4. "What about Boar's Head — the deadliest recent one? USDA meat recalls?"

"Blind spot, and we label it. Boar's Head 2024 was USDA FSIS — deli meat, poultry, red meat

— and it's invisible to openFDA, which is our feed. We cover ~100% of FDA lot-coded

enforcement recalls and none of USDA's. FSIS publishes a parallel recall feed in the same

shape; it's a connector, not a redesign. We'd rather tell you the boundary than get caught at it."

Q5. "Does this catch outbreaks early?"

"No — and we won't claim it. It's a recall responder, not an outbreak detector. It fires when the

FDA issues a lot-coded recall. It covers 100% of that feed and a minority of real

epidemiological outbreaks. What it does, it does in seconds: recall to site-level action.

Overclaiming outbreak detection is how these demos lose credibility."

Q6. "Why not just a spreadsheet? Why MongoDB?"

"Three things a spreadsheet can't do. Geospatial — 2dsphere  $near  to match recalls to sites

by location. The join at query time —  $lookup / $group  across recalls, suppliers, sites,

violations in one aggregation. And the change stream — the DB itself wakes the agent the

instant a record lands, so it's always-on, not a person refreshing a sheet. A spreadsheet is a

snapshot; this is a watcher."

Q7. "Why does it need to be local? Feels like a constraint you're rationalizing."

"An operator's supplier list, purchase volumes, and margins are trade secrets. No operator will

POST that to a cloud LLM to get a recall alert — the alert isn't worth the leak. FSMA 204

makes lot-level traceability a legal mandate, so this data is about to exist in every operator's

back office whether they like it or not. Always-on plus private is only possible on a box like the

GB10. Local isn't a constraint we're excusing — it's the only shape the customer will accept."

Q8. "What's the business past a demo?"

"FSMA 204 compliance is a mandate with a deadline, and mid-size operators — regional

chains, ghost-kitchen groups, distributors — have no tooling for it. This is an on-prem

appliance: one box, their data stays theirs, priced per site or per location. The wedge is recall

response; the moat is that once their real supplier graph lives in it, it becomes the traceability

system of record the law requires. The USDA connector and a distributor-portal ingest are the

next two features, not the next two pivots."

7. Business potential — from recall-responder to food-traceability

platform

The wedge → platform arc

Today (real, narrow, working): an on-prem responder. An FDA lot-coded recall drops,

BREADCRUMBS tells a NYC operator which of their sites touched the lot and what to do, in

seconds, on a box in the back office. Demo anchor: Dole F-0757-2022 lights up 5 real exposed sites

and recommends swapping distributor away from Dole (205 Class-I records) toward Jetro (0-of-1).

This is a complete product. It covers ~100% of its actual feed.

The hinge is a regulation, and it writes our data for us. The supplier→site links are modeled

today — that gap is the FSMA-204 problem itself. FSMA 204 (the FDA Food Traceability Rule)

makes lot-level traceability a legal recordkeeping mandate for anyone who manufactures,

processes, packs, or holds foods on the Food Traceability List. Mandatory compliance is July 20,

2028 (extended from January 2026 by the Continuing Appropriations Act of 2026). To comply, the

operator must generate traceability lot codes and key data elements at each critical tracking event.

Those records are exactly the missing edges.

Tomorrow (the platform): feed the operator's own FSMA-204 lot/supplier records into the same

MongoDB engine, and the modeled supplier→site links become real provenance graphs. No new

algorithm — the same  $lookup / $group  aggregation, now running on real edges. The regulation

manufactures our ground truth, on hardware the operator already owns. That single substitution

opens three adjacent products off the same engine:

Continuous supplier scorecarding — we already carry real openFDA firm recall histories

(Dole 205, Fresh Express 110, Sysco 24). Turn the one-time swap into a live score per supplier.

Provenance / origin — "farm or port → your kitchen," lot-traced, once the real KDEs are

flowing.

General food-awareness — allergen radar across the 6,896 undeclared-allergen recalls (the #2

recall cause, ~15x E. coli volume) and origin-country risk via UN Comtrade import data.

Honest boundary, up front: this is FDA-only. USDA FSIS (deli meat, poultry, most red meat — Boar's

Head 2024, 10 dead) is a labeled blind spot on the feed, not something the roadmap quietly claims

to solve.

Who pays, and why

Lead — multi-site restaurant groups. A recall drops and they don't know which of their 12, 50,

or 200 kitchens received the lot; today that's a phone tree. They pay for site-level action in

seconds — and they take it on-prem because, in the ops manager's own words, "my sourcing

and my margins never upload anywhere." Restaurant per-recall cost runs a median of

$0.04M–$1.1M per firm.

Grocers / retail — shelf-pull defense. The pain is over-broad recalls: pulling a SKU nationwide

when 3 lots at 8 stores were affected. Lot-level provenance narrows the pull. FMI/GMA puts

average direct recall cost at ~$10M, 52% of major recalls exceeding $10M.

Distributors / wholesalers (Baldor, US Foods, Jetro). Under FSMA 204 they sit on the node

with the most critical tracking events, so the mandate lands hardest here. They pay for turnkey

KDE capture plus an instant downstream-exposure map.

Ghost / cloud kitchens. Thin margins, many virtual brands, high supplier churn, no food-safety

staff. They pay for an always-on watch they don't have to staff.

Why on-prem is the moat, not a constraint

Two forces point at the same box: FSMA 204 makes the records a legal artifact the operator must

keep anyway (by July 2028); and the sourcing list, volumes, and margins in those records are trade

secrets. A cloud SaaS asks the operator to upload precisely the data that is the trade secret. On-

prem resolves the contradiction — the GB10 runs always-on local inference (Nemotron via vLLM)

plus MongoDB geo/aggregation entirely offline. The decision logic is deterministic Mongo, not a

cloud model; the local LLM only narrates. That's the hackathon's "local business agent" brief

satisfied for real.

TAM one-liner + the 12-month "so what"

TAM one-liner: the food-traceability technology market is forecast at roughly $30B by 2030 (Grand

View, 8.8% CAGR; other houses put 2030 anywhere from ~$10B to ~$44B). The reachable slice is

narrower: every US multi-site food operator and distributor facing a hard FSMA-204 deadline

in July 2028 — a regulator-created buying window.

The next real milestone (12 months): ingest one operator's actual purchase records. Replace

the illustrative 12-site portfolio with a real operator's real sites and real supplier POs / invoices. That

one step converts the modeled edges into real provenance and proves the platform hinge on live

data. No hockey stick: one operator, their real records, on their own box. Same engine the whole

way up.

8. The formal FDA-aligned report + alert — what the system outputs

Why a formal, FDA-aligned format matters

A recall-response document an operator can put in front of a health inspector, an insurer, or a

plaintiff's attorney has to read like the regulatory record it's derived from.

Trust / adoption. Food-safety managers already work from FDA Enforcement Reports and 21

CFR Part 7 recall communications. Mapping our output onto those exact fields means the

operator recognizes it on sight.

Legal posture. Under 21 CFR 7.49, a recall communication must let the recipient identify the

product, cease its use, and act. A dated, on-prem-generated report showing what the operator

knew, when, and what action was directed is contemporaneous evidence of a good-faith

response. FSMA 204 makes lot-level traceability a legal duty, so a lot-code-anchored exposure

record is on the compliance path.

Honesty as a feature. The document separates REAL (openFDA recall facts, DOHMH

violations, distributor recall history) from MODELED (the supplier→site links — the FSMA-204

gap itself). Labeling the modeled inference tells the operator exactly which line to verify against

their own receiving records before they act.

PDF report template — "Recall Exposure & Action Report"

Worked with the verified demo anchor Dole F-0757-2022. Fields tagged  [openFDA]  are populated

verbatim from the live FDA food enforcement record;  [BREADCRUMBS]  are computed on-box;

[MODELED]  are inference, not source data.

┌──────────────────────────────────────────────────────────────────────┐

│  ██  CLASS I RECALL — SERIOUS HEALTH HAZARD  ██                        │

│  Reasonable probability of serious adverse health consequences or      │

│  death (21 CFR 7.3). ACT ON THIS TODAY.                                │

└──────────────────────────────────────────────────────────────────────┘

RECALL EXPOSURE & ACTION REPORT

Notice ID

BC-2026-0822-0417  [BREADCRUMBS]

Generated

2026-08-22 09:14 ET — on-prem (GB10), offline  [BREADCRUMBS]

Operator

[Operator legal name] — 12-site NYC portfolio  [MODELED portfolio]

Prepared for

[Food Safety Manager / person responsible]

Source event

FDA Food Enforcement Report, recall F-0757-2022

Exposure status

5 of 12 sites EXPOSED — action required  [BREADCRUMBS]

A. FDA RECALL FACTS (mapped one-to-one to openFDA  food/enforcement  fields — the

regulatory record)

FDA field

Value

recall_number

F-0757-2022  [openFDA]

classification

Class I  [openFDA]

recalling_firm

Dole Fresh Vegetables, Inc.  [openFDA]

product_description

Iceberg lettuce, packaged / bulk  [openFDA]

reason_for_recall

Potential contamination with Listeria monocytogenes  [openFDA]

code_info  (lot / date codes)

[Lot codes and best-by dates as published]  [openFDA]

distribution_pattern

[States / regions of distribution]  [openFDA]

product_quantity

[Units / cases recalled]  [openFDA]

status

[Ongoing / Completed / Terminated]  [openFDA]

voluntary_mandated

Voluntary: Firm Initiated  [openFDA]

recall_initiation_date

[YYYY-MM-DD]  [openFDA]

report_date

[YYYY-MM-DD]  [openFDA]

recalling_firm  location

[City, State]  [openFDA]

Classification key (21 CFR 7.3): Class I — reasonable probability of serious adverse health

consequences or death. Class II — temporary or medically reversible consequences, or remote

probability of serious harm. Class III — use not likely to cause adverse health consequences.

B. EXPOSURE — which of your sites received this lot

[MODELED]  — supplier→site links are inferred, not sourced. This is the FSMA-204 traceability gap:

absent a shared lot-level ledger, BREADCRUMBS models which sites a recalled lot reached from

the operator's supplier assignments. Verify each row against your own receiving / invoice

records before disposition. Under FSMA 204 the authoritative answer lives in your Receiving

KDEs (traceability lot code, product description, quantity, date, location) — this table is the prompt to

pull them.

Site

CAMIS

Supplier link → this lot

Site 03 — Midtown

41xxxxxx

Dole → iceberg, lot in

code_info

Site 05 — LES

50xxxxxx

Dole → iceberg

Received

(modeled)

Yes

Yes

Verify against

Receiving log /

invoice

Receiving log /
invoice

Site

CAMIS

Supplier link → this lot

Site 07 —
Williamsburg

41xxxxxx

Dole → iceberg

Site 09 — LIC

50xxxxxx

Dole → iceberg

Site 11 — Harlem

41xxxxxx

Dole → iceberg

Received

(modeled)

Yes

Yes

Yes

Verify against

Receiving log /
invoice

Receiving log /

invoice

Receiving log /

invoice

7 of 12 sites: no modeled receipt of this lot — no action, but retain this notice.

C. RISK — how bad, per exposed site (two independent, REAL signals)

Distributor recall history (REAL — openFDA firm counts):

Firm

Class-I recall records

Read

Dole (recalling firm)

Fresh Express

Sysco

205

110

24

Extensive Class-I recall history

High

Moderate

Jetro (proposed swap)

0 of 1

Low record — verified, not "clean"

Exposed-site hygiene risk (REAL — DOHMH  crit_violations , range 0–56, citywide median 4;

the operational-hygiene metric, NOT the letter grade):

Site

CAMIS

crit_violations

vs. median (4)

Handling-risk read

Site 05 — LES

50xxxxxx

14

+10

Elevated — prioritize hold

Site 11 — Harlem

41xxxxxx

Site 03 — Midtown

41xxxxxx

Site 07 — Williamsburg

41xxxxxx

Site 09 — LIC

50xxxxxx

9

6

4

2

+5

+2

0

−2

Above median

Slightly above

At median

Below median

Site risk compounds product risk: a Class-I Listeria lot at a site with 14 critical handling violations is

the highest-priority hold, because cross-contamination controls there are already the weakest.

D. RECOMMENDED ACTION (deterministic — computed by MongoDB aggregation on-box, not by

a model; the local Nemotron writes only the narration line, never the decision)

1. HOLD & SEGREGATE. At all 5 exposed sites, immediately quarantine iceberg lettuce matching

the F-0757-2022 lot/date codes in  code_info . Do not use, serve, or further distribute (21 CFR

7.49). Prioritize Site 05 (LES, 14 crit violations) and Site 11 (Harlem, 9).

2. VERIFY. Match on-hand lot codes to the recall's  code_info . Pull each site's Receiving records

(FSMA-204 KDEs) to confirm or clear the modeled exposure.

3. DISPOSITION. Destroy or return per the recalling firm's instructions; document lot, quantity, site,

and date.

4. SWAP — sourcing recommendation: move iceberg sourcing from Dole (205 Class-I recall

records) to Jetro (0 of 1 record).

Honest rationale: Jetro's low count is a verified low record, not proof of a safer product — it

reflects few matched openFDA recall records for that firm, which can also mean lower recall

visibility. Treat this as a lower-recall-history alternative and confirm Jetro's own lot-traceability

before switching. A risk-history swap, not a safety guarantee.

1. LOG. This notice, timestamped, is your contemporaneous record that the recall was received

and acted on.

Narration (local Nemotron, GB10): "Five of your twelve sites received Dole iceberg lettuce

matching this Class I Listeria recall. Hold and segregate now, starting with your Lower East

Side location, which carries the most critical handling violations. Consider shifting iceberg

sourcing to Jetro, which has a far lighter recall record than Dole."

E. REAL vs. MODELED — provenance (see the full honesty table in §3; report-specific rows

below)

Element

REAL / MODELED

Source

Recall facts (§A)

Distributor recall history
(§C)

REAL

REAL

openFDA food enforcement — F-0757-2022

openFDA firm-level recall counts

Site critical violations (§C)

REAL

NYC DOHMH inspection records

( crit_violations )

Site identities / CAMIS

REAL

DOHMH-geocoded establishments

Supplier → site → lot
links (§B)

MODELED

Operator supplier assignments — the FSMA-204
gap

Operator 12-site portfolio

MODELED

Demo portfolio

(illustrative)

Narration sentence (§D)

Generated

Local Nemotron, on-box; decision logic is

deterministic Mongo

Coverage boundary (stated, not hidden): Source is FDA food enforcement only. USDA FSIS

products — deli meats, poultry, most red meat — are not in this feed (the 2024 Boar's Head listeria

recall would be invisible). This report covers ~100% of FDA lot-coded enforcement recalls and does

not claim outbreak detection.

────────────────────────────────────────────────────────────────────────

Source: U.S. FDA Food Enforcement Report (openFDA), recall F-0757-2022.

FDA classification per 21 CFR 7.3; recall-communication elements per

21 CFR 7.49; traceability framing per FSMA §204 Food Traceability Rule.

Generated on-prem on the operator's GB10 — supplier lists, volumes, and

site data never left the building. This document is a response record,

not a substitute for the recalling firm's official instructions.

BREADCRUMBS · Notice BC-2026-0822-0417 · 2026-08-22 09:14 ET

────────────────────────────────────────────────────────────────────────

SMS / Telegram short-form (outbox format)

Formal, plain, no hype — what / where / how bad / do this / ref. Two to four lines.

Primary (Class I, exposed):

FDA CLASS I RECALL — action needed today.

Dole iceberg lettuce (Listeria), recall F-0757-2022. 5 of your 12

sites received matching lots: Midtown, LES, Williamsburg, LIC, Harlem.

DO: hold & segregate now; verify lot codes; do not serve.

Full report + swap recommendation: BC-2026-0822-0417 (PDF).

Compressed 2-line variant (SMS length):

FDA CLASS I: Dole iceberg lettuce, Listeria (recall F-0757-2022).

5 of 12 sites exposed — HOLD & segregate now. Full report: BC-2026-0822-0417.

All-clear variant (no exposure):

FDA CLASS I recall posted: Dole iceberg lettuce, Listeria (F-0757-2022).

No modeled exposure across your 12 sites. No action; notice retained on file.

Backend field map — wireable, not aspirational

Every field resolves to data the pipeline already holds:

1. §A FDA facts →  recall_number ,  classification ,  recalling_firm ,

product_description ,  reason_for_recall ,  code_info ,  distribution_pattern  —

verbatim from the openFDA  food/enforcement  document already in Mongo.

2. §B Exposure table →  exposed_sites[]  with  {camis, name, supplier_link} ; the "5 of 12"

banner is  len(exposed_sites)  over the operator portfolio.

3. §C Site risk →  exposed_sites[].crit_violations  (DOHMH), sorted desc to drive hold

priority.

4. §C Distributor history →  distributor_risk.class1  (Dole=205) and the swap target's

distributor_risk.class1  (Jetro=0-of-1).

5. §D Swap + narration →  recommendation.swap_to  (Jetro) drives the sourcing line; the

Nemotron call fills only the narration string, so the deterministic action survives with or without

the model.

Uncertain / not independently verified in this build: the exact  code_info ,  distribution_pattern ,

product_quantity , and dates for F-0757-2022 are shown as live  [openFDA]  fill-ins rather than
hard-coded; the operator's 12-site portfolio and all supplier→site links are labeled MODELED.

9. Division of labor + the six things we NEVER overclaim

Division of labor (2–3 presenters)

DRIVER (hands on keyboard, talks least). Owns the console. Executes Beats 0–5 cleanly —

camera framing, the trigger click, report + Telegram. Speaks only the short action lines if solo;

otherwise silent and precise. Rule: never narrate and drive at once — if something lags, keep

clicking, let the Narrator cover. Pre-loads the Dole case and confirms Mongo is up before you're

called.

NARRATOR (the voice, faces judges). Delivers every "SPOKEN" line and every HONEST TAG.

Owns pacing and the Beat-6 close — has to land "4 seconds vs. 2 days" and stop talking. Practices

the honest tags until they sound like confidence, not apology. If a beat glitches, bridges verbally

("while that renders —") and never says "it's broken."

Q&A LEAD (the credibility; same as Narrator if only 2). Fields the 8 questions. Owns the honest

framing cold — especially Q4 (Boar's Head), Q5 (not an outbreak detector), Q1 (pull the key).

Discipline: answer the question asked, give the real boundary, stop. Never fill silence with an

overclaim. Knows the real numbers by heart: 29,310 / 6,896 / 205 / 110 / 24 / 0-of-1.

If 2 people: Driver + (Narrator = Q&A Lead).

If 3: split all three; Narrator and Q&A Lead pre-agree a handoff cue so judge questions don't

collide.

Shared pre-flight (all present, 60 sec before stage): Mongo up · console renders 12 blocks · Dole

trigger fires red · report generates · Telegram draft composes · timer card loads. If any live upgrade

is red, agree now to run baked-only and cut the UPGRADE asides — decided before you walk up,

never mid-demo.

The six lines we NEVER overclaim

1. Recall responder, not outbreak detector. Say "turns an FDA recall into site-level action in

seconds." Never "catches outbreaks early" — we cover ~100% of our feed (FDA lot-coded

recalls) and only a minority of real epidemiological outbreaks.

2. FSIS is a labeled blind spot. We're FDA-only. USDA FSIS (deli meat, poultry, most red meat) is

invisible to us — Boar's Head 2024 (10 dead) wouldn't appear. Pre-empt it; don't get caught.

3. Local inference is currently thin. The LLM writes one narration sentence; deterministic Mongo

makes every decision. Frame as strength, don't hide it.

4. Change-stream isn't wired to  run()  yet. The Watcher observes inserts; it does not yet auto-

trigger the full pipeline. We trigger runs explicitly today.

5. Supplier→site links are modeled. They're the FSMA-204 gap we exist to close, labeled

modeled — not real traceability data we're passing off as ground truth.

6. Telegram is draft-not-send. The Comms output is prepared, not auto-dispatched to a live

operator channel.

