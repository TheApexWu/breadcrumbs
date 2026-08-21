# Straits — Ralph loop contract (the HOW)

This is the per-iteration contract for the autonomous build loop. `ralph.sh` drives it: one milestone per `opencode` process, on OpenRouter, verifying each with a program the agent cannot edit, committing + pushing per pass. This file is the source of truth for *how* an iteration behaves; `PRD.JSON` is the source of truth for *what* (the milestones, verifications, hard_rules).

## Each iteration you are ONE step of the loop
1. **Read `PRD.JSON` in full first.** `project.full_context` and `hard_rules` are non-negotiable. Work ONLY on the single milestone the driver assigned; trust every milestone already `completed:true` — do not re-touch it.
2. Read `docs-notes/*.md` and `RALPH.md` for what previous iterations left. Leave terse notes for the next one.
3. Complete every task in the milestone, then run EVERY item in its `verifications` and make them pass with a program — not with your own say-so.
4. Only when all verifications pass: set the milestone `completed:true` in `PRD.JSON` and add an `evidence` array (one line per verification, describing the proof: the command + its result).
5. Commit `ralph: milestone <id> complete — <name>` and push.
6. If truly blocked (a credential you cannot get, a source that is down, a contradiction), write `BLOCKED.md` explaining exactly what blocks you and what a human must do — then stop.

## Straits-specific rules (on top of PRD hard_rules)
- **Offline-first, always.** Never make the app depend on a live network at demo time. Build against `fixtures/theater-synth.json` until the real `data/theater.parquet` slice exists (M1), then against the recorded slice. Replay must be deterministic.
- **Cargo only.** Ships = AIS types 70-89; air = freighter operators. Drop passenger traffic.
- **Declared fabulation, never prediction.** Any forward-sim output is a *possible* future carrying its seed + assumptions + blocked chokepoint. Never emit language that claims certainty about what will happen. The sentinel refuses to name one true outcome.
- **The agent ACTS.** The sentinel must make visible, autonomous tool-calls (query_flows / inject_shock / reroute_sim / brief / alert). A render-only build fails the "always-on business agent" brief.
- **Prove the hardware, do not assert it.** Telemetry comes from NVML/sparkview/tegrastats, not `nvidia-smi` memory (under-reports on GB10 UMA). Targets live in PRD hard_rules.
- **Honest coverage.** Mid-ocean AIS gaps are dead-reckoned and *labelled* as fill, never shown as real fixes.
- **NEVER self-certify a `human_gate` milestone** (M6 on-box telemetry, M7 live agent quality, M8 pitch). Prepare the artifact + a canned transcript/stub and STOP; Alex renders the verdict.

## What must be true before firing this loop
- [ ] Data-scout `wgbdis0fw` returned; M1 sources + sizing finalized.
- [ ] Name locked (working name: Straits).
- [ ] Alex's explicit go. The loop spends OpenRouter credit and auto-pushes — do not fire it on assumption.

## Test discipline
Test only what must survive repeated runs: schema validity, deterministic replay, the reroute assertion (Suez block -> Cape path), timeline determinism under a fixed seed, the congestion metric direction. No exhaustive suites; the verification IS the test.
