# BREADCRUMBS — Ralph loop contract (the HOW)

Per-iteration contract for the autonomous build loop. `ralph.sh` drives it: one milestone per
`opencode` process, on OpenRouter, verifying each with a program the agent cannot edit, committing +
pushing per pass. This file is the source of truth for *how* an iteration behaves; `PRD.JSON` is the
source of truth for *what* (milestones, verifications, hard_rules).

## Each iteration you are ONE step of the loop
1. **Read `PRD.JSON` in full first.** `project.full_context` and `hard_rules` are non-negotiable.
   Work ONLY on the single milestone the driver assigned; trust every milestone `completed:true`.
2. Read `RALPH.md` and prior notes for what earlier iterations left. Leave terse notes for the next.
3. Complete every task, then run EVERY item in the milestone's `verifications` and make them pass
   with a program — not with your own say-so.
4. Only when all verifications pass: set the milestone `completed:true` and add an `evidence` array
   (one line per verification: the command + its result).
5. Commit `ralph: milestone <id> complete — <name>` and push.
6. If truly blocked (a credential you cannot get, a source down, a contradiction), write `BLOCKED.md`
   explaining exactly what blocks you and what a human must do — then stop.

## BREADCRUMBS-specific rules (on top of PRD hard_rules)
- **You run on branch `ralph`. You own BACKEND ONLY.** Edit only `agent/ sim/ db/ scripts/ bridge/`
  plus `PRD.JSON` / `evidence/`. **NEVER touch `globe/*.html`, `globe/assets/*`, `mockups/`, or
  `docs/*`** — humans build those in parallel on `ui-*` / `assets-*` branches. The console consumes
  your output through `bridge/` (Mongo-backed JSON + a documented contract), never the reverse. If a
  task seems to need a human-owned file, write the contract in `bridge/` and stop there.
- **Local-first, offline.** All data is cached / in local MongoDB; the system runs with the network
  unplugged at demo time. No cloud inference at demo. Vendor deps locally.
- **MongoDB is the substrate, used tastefully** — documents + a 2dsphere geo index + aggregation
  pipelines as the agent's tools + a change stream as the always-on Watcher. Not a flat JSON store.
- **NemoClaw is the agent runtime** (OpenClaw for off-box dev, behind one adapter). Local Nemotron on-box.
- **Real vs MODELED, always labeled.** Real: recalls, DOHMH critical-violation history, distributor
  recall history, buildings. Modeled: supplier→site links, the operator portfolio, covers/day.
- **Risk = critical food-handling violations, NOT the letter grade** (grades are a composite).
- **The agent ACTS** — visible autonomous tool-calls. A render-only build fails the brief.
- **Prove the box, don't assert it** — telemetry from NVML/tegrastats, not nvidia-smi.
- **Instrument, not oracle.** Report real state; label simulation; refuse false certainty.
- **NEVER self-certify a `human_gate` milestone** (M6 on-box, M7 agent quality, M8 pitch). Prepare
  the artifact + a canned transcript/stub and STOP; Alex renders the verdict.

## What must be true before firing this loop
- [x] Premise locked (`docs/premise.md`); name = BREADCRUMBS.
- [x] Real data cached (openFDA / DOHMH / distributors / buildings) in `globe/assets/`.
- [x] Branch `ralph` checked out; humans isolated on their own branches.
- [ ] Local MongoDB reachable (M0 preflight asserts it).
- [ ] Alex's explicit go. The loop spends OpenRouter credit and auto-pushes — do not fire on assumption.

## Test discipline
Test only what must survive repeated runs: Mongo load counts + provenance, the exposure aggregation
== its python control, deterministic Response under a fixed recall, the bridge contract == respond.py
numbers, and the no-human-file-touched path check. The verification IS the test; no exhaustive suites.
