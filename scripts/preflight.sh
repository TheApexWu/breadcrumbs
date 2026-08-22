#!/usr/bin/env bash
# PRD M0 preflight. Assert: node>=18, python3>=3.10 (in a LOCAL venv), local
# MongoDB reachable, backend deps importable. Never system-installs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail() { echo "[preflight] FAIL: $*" >&2; exit 1; }

# 1. node >= 18
if command -v node >/dev/null 2>&1; then
  NODE_MAJ="$(node -p 'process.versions.node.split(".")[0]')"
  [ "$NODE_MAJ" -ge 18 ] || fail "node $NODE_MAJ < 18"
  echo "[preflight] node $(node -v) ok"
else
  fail "node not found"
fi

# 2. python3 >= 3.10 in a LOCAL venv (never system). Create .venv if missing.
PY="$ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
  BASE_PY=""
  for cand in /opt/homebrew/bin/python3.14 /opt/homebrew/bin/python3.13 \
              /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11 \
              /opt/homebrew/bin/python3.10 python3; do
    if command -v "$cand" >/dev/null 2>&1; then
      BASE_PY="$cand"; break
    fi
  done
  [ -n "$BASE_PY" ] || fail "no python3 >= 3.10 found to bootstrap venv"
  PY_MAJ_MIN="$("$BASE_PY" -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
  echo "[preflight] bootstrapping .venv with $BASE_PY ($PY_MAJ_MIN)"
  "$BASE_PY" -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/pip" install -q --upgrade pip
  "$ROOT/.venv/bin/pip" install -q -r "$ROOT/requirements.txt"
  PY="$ROOT/.venv/bin/python"
fi

PY_VER="$("$PY" -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
PY_MAJ="${PY_VER%%.*}"
PY_MIN="${PY_VER#*.}"
{ [ "$PY_MAJ" -ge 3 ] && [ "$PY_MIN" -ge 10 ]; } || fail "python $PY_VER < 3.10"
echo "[preflight] python $PY_VER (.venv) ok"

# 3. backend deps import in the venv
"$PY" -c 'import pymongo, requests, json, os; print("[preflight] pymongo", pymongo.__version__)' \
  || fail "venv deps missing (run: .venv/bin/pip install -r requirements.txt)"

# 4. local MongoDB reachable + serverStatus ok:1
MONGO_URI="${MONGO_URI:-mongodb://localhost:27017}"
if ! command -v mongosh >/dev/null 2>&1; then
  # fall back to the python driver if mongosh is absent
  "$PY" - "$MONGO_URI" <<'PY' || fail "MongoDB not reachable at $MONGO_URI"
import sys
from pymongo import MongoClient
c = MongoClient(sys.argv[1], serverSelectionTimeoutMS=3000)
ok = c.admin.command("serverStatus")["ok"]
assert ok == 1, "serverStatus.ok=%s" % ok
print("[preflight] MongoDB serverStatus ok:%s" % ok)
PY
else
  OK="$(mongosh --quiet --eval 'db.serverStatus().ok' "$MONGO_URI" 2>/dev/null | tr -d '[:space:]')"
  [ "$OK" = "1" ] || fail "MongoDB serverStatus.ok=$OK (expected 1) at $MONGO_URI"
  echo "[preflight] MongoDB serverStatus ok:1 ($MONGO_URI)"
fi

echo "[preflight] PASS"
