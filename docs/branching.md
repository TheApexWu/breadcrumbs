# BREADCRUMBS — branches & who touches what

Humans and the ralph loop build in parallel. The rule that keeps us from stomping each other is
**file ownership**, not just separate branches. Read this before you push.

## Branches
| Branch | Owner | Purpose |
|---|---|---|
| `main` | — | maritime fallback, frozen. Ignore it. |
| `food` | everyone | shared stable base. Branch off it; merge back via PR when green. |
| `ralph` | the loop | the autonomous backend build. Auto-commits + pushes. **Don't hand-edit it.** |
| `ui-<name>` | you | your frontend / UI playground. Branch off `food`. |
| `assets-<name>` | you | your assets / design playground. Branch off `food`. |

```bash
git checkout food && git pull
git checkout -b ui-<yourname>      # or assets-<yourname>
# ...build, commit as yourself, push...
git push -u origin ui-<yourname>
# open a PR into food when it's ready
```

## File ownership — the no-collision rule
- **The loop (ralph) owns BACKEND ONLY:** `agent/ sim/ db/ scripts/ bridge/` + `PRD.JSON` / `evidence/`.
- **Humans own the FRONTEND + assets:** `globe/*.html`, `globe/assets/`, `mockups/`, `docs/`.
- **They meet only at `bridge/`.** The loop serves Mongo-backed JSON with a documented shape
  (`bridge/CONTRACT.md`); the console *fetches* it. The loop never edits console HTML; you never edit
  backend code. If you need a field that isn't in the contract, ask — don't reach into `agent/`.

## Why
The loop rewrites backend files every few minutes and force-pushes `ralph`. If it and a human touched
the same file, one of you loses work to a merge conflict or an overwrite. Ownership by directory means
that never happens — `food` integrates both sides through PRs, on our schedule, not the loop's.

## Integrating
- Loop backend lands in `food` when a milestone is green (we merge `ralph` → `food`, reviewed).
- Your UI lands in `food` via PR.
- `food` is what we demo from. Keep it runnable at all times.
