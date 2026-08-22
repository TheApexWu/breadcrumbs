#!/usr/bin/env bash
# SCAFFOLD — PRD M0. Preflight for the loop. The ralph loop fills this in.
# Assert: python3>=3.10, a LOCAL venv (never system installs), MongoDB reachable, deps present.
set -euo pipefail

echo "[preflight] SCAFFOLD — not implemented yet (ralph M0)"
echo "[preflight] TODO: python3 --version >= 3.10"
echo "[preflight] TODO: mongosh --eval 'db.serverStatus().ok' -> 1  (mongodb://localhost:27017)"
echo "[preflight] TODO: pip install into ./ .venv (pymongo, requests); assert import"
exit 1   # fail until implemented, so a green preflight is never faked
