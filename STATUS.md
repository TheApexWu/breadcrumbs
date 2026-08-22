# BREADCRUMBS — status

On-prem NYC food-safety agent (Dell × NVIDIA hackathon, 2026-08-22). See `docs/premise.md`.

## Branches
- `main` — maritime fallback, frozen.
- `food` — shared stable base (frontend + data + docs live here). Humans PR into it.
- `ralph` — the loop's backend build. Backend-only. Don't hand-edit.
- `ui-*` / `assets-*` — teammate playgrounds off `food`.

Full model + file-ownership rule: `docs/branching.md`.

## Built (scaffolds — allowed pre-work)
- Real data cached in `globe/assets/` (openFDA recalls, DOHMH 17,204 graded, distributor scorecard, buildings).
- Consoles: `globe/food3d.html` (3D), `globe/food.html` (2D).
- Concept: `mockups/product-concept.html`. Onboarding: `docs/onboarding.html`.
- Backend SKELETON on `ralph` (stubs only — not implemented).

## Loop builds (M0–M5, off-box) — NOT STARTED
M0 preflight+Mongo · M1 operator model · M2 recall-response · M3 agent swarm · M4 bridge · M5 SMS.

## Human-gated (M6–M8, on-box + pitch)
M6 Nemotron on GB10 + real telemetry · M7 agent quality · M8 pitch + demo video (18:00 submission).

## Infra
- GB10: `ssh dell@100.113.10.122` (Tailscale) or `dell@promaxgb10-5ca9.local` (LAN). DGX Spark, aarch64.
- Loop runs on the Mac (OpenRouter); GB10 is for M6+.
