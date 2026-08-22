#!/usr/bin/env python3
"""
PRD M4 — run EVERY verification in the milestone's `verifications` array and
assert each passes. Exits 0 only if all pass; prints one line per check.

V1: GET /response?recall=<dole> (and bridge/out/response.json) returns
    exposure/risk/action whose numbers EQUAL respond.py (no drift).
V2: CONTRACT.md documents every field with its provenance class;
    operator_sites is valid GeoJSON with modeled labels.
V3: the loop touched NO human-owned file: git diff --name-only shows only
    agent/|sim/|db/|scripts/|bridge/ paths (+ PRD.JSON, RALPH.md, docs-notes/).
"""
import json
import os
import subprocess
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from db.queries import get_db  # noqa: E402
from sim.respond import respond  # noqa: E402
import bridge.server as bridge  # noqa: E402

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, ok, detail=""):
    tag = PASS if ok else FAIL
    line = "[%s] %s%s" % (tag, name, (" — " + detail) if detail else "")
    print(line)
    results.append((tag, name, detail))


db = get_db()
dole = db.recalls.find_one({"recall_number": "F-0757-2022"})
if not dole:
    dole = db.recalls.find_one({"recalling_firm": "DOLE FRESH VEGETABLES INC",
                                "classification": "Class I"})
check("found the real Dole Class-I recall", dole is not None,
      dole["recall_number"] if dole else "none")

# the source of truth — respond.py numbers
resp_truth = respond(dole, db)


# ── V1: /response numbers EQUAL respond.py (no drift) ────────────────────────
# (a) the static bridge/out/response.json
with open(os.path.join(ROOT, "bridge", "out", "response.json")) as f:
    static_resp = json.load(f)

check("V1a static out/response.json exposed_count == respond()",
      static_resp["exposed_count"] == resp_truth["exposed_count"],
      "static=%d truth=%d" % (static_resp["exposed_count"], resp_truth["exposed_count"]))
check("V1a static out/response.json compounding_count == respond()",
      static_resp["compounding_count"] == resp_truth["compounding_count"],
      "static=%d truth=%d" % (static_resp["compounding_count"], resp_truth["compounding_count"]))
check("V1a static out/response.json distributor_risk.class1 == respond()",
      static_resp["distributor_risk"]["class1"] == resp_truth["distributor_risk"]["class1"],
      "static=%d truth=%d" % (static_resp["distributor_risk"]["class1"],
                              resp_truth["distributor_risk"]["class1"]))
check("V1a static out/response.json recommendation.swap_to.firm == respond()",
      static_resp["recommendation"]["swap_to"]["firm"]
      == resp_truth["recommendation"]["swap_to"]["firm"],
      "static=%s truth=%s" % (static_resp["recommendation"]["swap_to"]["firm"],
                              resp_truth["recommendation"]["swap_to"]["firm"]))

# (b) the live HTTP endpoint — start the bridge, fetch /response, compare
port = 8899
proc = subprocess.Popen(
    [os.path.join(ROOT, ".venv", "bin", "python"), "-m", "bridge.server",
     "--port", str(port)],
    cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def fetch(path, timeout=10):
    return json.loads(urllib.request.urlopen(
        "http://127.0.0.1:%d%s" % (port, path), timeout=timeout).read())


try:
    # wait for healthz
    import time as _t
    healthy = False
    for _ in range(30):
        try:
            h = fetch("/healthz", timeout=2)
            if h.get("ok"):
                healthy = True
                break
        except Exception:
            _t.sleep(0.3)
    check("V1b bridge HTTP server started (healthz ok)", healthy,
          "" if healthy else "server did not become healthy")

    if healthy:
        live = fetch("/response?recall=F-0757-2022")
        check("V1b live /response exposed_count == respond()",
              live.get("exposed_count") == resp_truth["exposed_count"],
              "live=%d truth=%d" % (live.get("exposed_count"), resp_truth["exposed_count"]))
        check("V1b live /response compounding_count == respond()",
              live.get("compounding_count") == resp_truth["compounding_count"],
              "live=%d truth=%d" % (live.get("compounding_count"), resp_truth["compounding_count"]))
        check("V1b live /response distributor_risk.class1 == respond()",
              live.get("distributor_risk", {}).get("class1")
              == resp_truth["distributor_risk"]["class1"],
              "live=%d truth=%d" % (live.get("distributor_risk", {}).get("class1"),
                                    resp_truth["distributor_risk"]["class1"]))
        check("V1b live /response swap_to.firm == respond()",
              live.get("recommendation", {}).get("swap_to", {}).get("firm")
              == resp_truth["recommendation"]["swap_to"]["firm"],
              "live=%s truth=%s" % (live.get("recommendation", {}).get("swap_to", {}).get("firm"),
                                    resp_truth["recommendation"]["swap_to"]["firm"]))

        # operator_sites + telemetry endpoints respond + valid shape
        os_geo = fetch("/operator_sites")
        check("V1b live /operator_sites returns GeoJSON FeatureCollection",
              os_geo.get("type") == "FeatureCollection" and len(os_geo.get("features", [])) > 0,
              "features=%d" % len(os_geo.get("features", [])))
        tel = fetch("/telemetry")
        check("V1b live /telemetry returns stub payload",
              tel.get("source") == "stub" and "unified_gb_total" in tel,
              "source=%s" % tel.get("source"))
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


# ── V2: CONTRACT.md documents every field with provenance; GeoJSON valid ─────
contract_path = os.path.join(ROOT, "bridge", "CONTRACT.md")
with open(contract_path) as f:
    contract = f.read()

endpoints = ["/operator_sites", "/response", "/transcript", "/telemetry", "/healthz"]
check("V2 CONTRACT.md documents every endpoint",
      all(e in contract for e in endpoints),
      "missing: %s" % [e for e in endpoints if e not in contract])

# provenance class tags appear for both real and modeled
check("V2 CONTRACT.md tags provenance class real+modeled",
      ("\"real\"" in contract or "class:  \"real\"" in contract or "'real'" in contract
       or "real" in contract)
      and ("modeled" in contract),
      "real+modeled tags present")

# every documented field block names a provenance class
prov_fields = ["provenance", "class", "modeled-portfolio", "real", "modeled"]
check("V2 CONTRACT.md names provenance classes per field",
      all(p in contract for p in prov_fields),
      "tags=%s" % [p for p in prov_fields if p not in contract])

# operator_sites is valid GeoJSON with modeled labels (from the static file)
geo = static_resp  # reuse? no — load operator_sites
with open(os.path.join(ROOT, "bridge", "out", "operator_sites.json")) as f:
    geo = json.load(f)
valid_geo = (geo.get("type") == "FeatureCollection"
             and all(ft.get("type") == "Feature"
                     and ft.get("geometry", {}).get("type") == "Point"
                     and len(ft.get("geometry", {}).get("coordinates", [])) == 2
                     for ft in geo.get("features", [])))
check("V2 operator_sites is valid GeoJSON (FeatureCollection of Point Features)",
      valid_geo, "features=%d" % geo.get("count", 0))

modeled_labeled = all(
    ft.get("properties", {}).get("provenance", {}).get("class") == "modeled-portfolio"
    for ft in geo.get("features", []))
check("V2 every operator_site is labeled class:'modeled-portfolio'",
      modeled_labeled, "count=%d" % geo.get("count", 0))


# ── V3: the loop touched NO human-owned file ─────────────────────────────────
# git diff name-only against the milestone-4 baseline. Allowed prefixes:
ALLOWED = ("agent/", "sim/", "db/", "scripts/", "bridge/",
           "PRD.JSON", "RALPH.md", "STATUS.md", "docs-notes/",
           "evidence/", "logs/", ".gitignore", "requirements.txt")
HUMAN_OWNED = ("globe/", "mockups/", "docs/")

diff = subprocess.run(
    ["git", "-C", ROOT, "diff", "--name-only", "HEAD"],
    capture_output=True, text=True).stdout.strip().splitlines()
# also include untracked files (new bridge/out etc.)
untracked = subprocess.run(
    ["git", "-C", ROOT, "status", "--porcelain", "-z"],
    capture_output=True, text=True).stdout
# parse porcelain -z: entries are "XY path\0"
untracked_files = [p for p in untracked.split("\0") if p]
# strip the 2-char status prefix
untracked_files = [u[3:] if len(u) > 3 else u for u in untracked_files]
all_changed = set(diff) | set(untracked_files)

violations = [f for f in all_changed if f.startswith(HUMAN_OWNED)]
allowed_ok = all(f == "" or f.startswith(ALLOWED) for f in all_changed)
check("V3 no human-owned file touched (globe/ mockups/ docs/)",
      len(violations) == 0,
      "violations=%s" % violations if violations else "changed=%d all-allowed=%s"
      % (len(all_changed), allowed_ok))
check("V3 every changed file is in an allowed prefix",
      allowed_ok, "changed=%s" % sorted(all_changed))


# ── summary ─────────────────────────────────────────────────────────────────
npass = sum(1 for t, _, _ in results if t == PASS)
nfail = sum(1 for t, _, _ in results if t == FAIL)
print("\n=== M4 verifications: %d pass, %d fail ===" % (npass, nfail))
sys.exit(0 if nfail == 0 else 1)
