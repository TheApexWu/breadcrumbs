# RALPH.md — loop iteration log

The autonomous loop appends terse notes here each iteration (what it did, what it left for next).
Human scaffolding note below; loop entries follow.

---
## SCAFFOLD (pre-loop, human) — 2026-08-22
Backend skeleton laid on branch `ralph` BEFORE any loop run (per instruction: no loop yet).
Created as empty stubs (raise NotImplementedError / exit 1 — a green result can never be faked):
- `scripts/preflight.sh` (M0), `scripts/load_mongo.py` (M0), `db/queries.py` (M0)
- `sim/operator.py` (M1), `sim/respond.py` (M2)
- `agent/swarm.py` (M3)
- `bridge/server.py` + `bridge/CONTRACT.md` (M4)
- `requirements.txt`, `evidence/`, `bridge/samples/`

Loop owns `agent/ sim/ db/ scripts/ bridge/` only. Do NOT touch `globe/*.html`, `globe/assets/*`,
`mockups/`, `docs/`. Build against `docs/premise.md` + `PRD.JSON`. Start at M0.
