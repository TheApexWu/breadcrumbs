#!/usr/bin/env python3
"""
PRD M2 — run EVERY verification in the milestone's `verifications` array and
assert each passes. Exits 0 only if all pass; prints one line per check.
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from db.queries import get_db, compounding  # noqa: E402
from sim.operator import build_portfolio  # noqa: E402
from sim.respond import respond  # noqa: E402

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, ok, detail=""):
    tag = PASS if ok else FAIL
    line = "[%s] %s%s" % (tag, name, (" — " + detail) if detail else "")
    print(line)
    results.append((tag, name, detail))


# ── rebuild the portfolio (idempotent) so the verification is self-contained ──
db = get_db()
build_portfolio(db)

# ── locate the hero Dole recall (Class I, leafy greens) ──────────────────────
dole = db.recalls.find_one({"recall_number": "F-0757-2022"})
if not dole:
    dole = db.recalls.find_one({
        "recalling_firm": "DOLE FRESH VEGETABLES INC",
        "classification": "Class I",
    })
check("found the real Dole Class-I recall", dole is not None,
      dole["recall_number"] if dole else "none")

# ── V1: Dole recall -> exposed_sites>0, compounding_count == # crit>0,
#      distributor_risk.class1 == real openFDA count, swap names 0-class1 dist ──
resp = respond(dole, db)

check("V1 exposed_sites > 0", resp["exposed_count"] > 0,
      "exposed_count=%d" % resp["exposed_count"])

# compounding_count == number of exposed sites with crit_violations>0
exposed_camis = [s["camis"] for s in resp["exposed_sites"]]
pure_comp = compounding(exposed_camis, db)
check("V1 compounding_count == # exposed with crit_violations>0",
      resp["compounding_count"] == len(pure_comp),
      "respond=%d pure=%d" % (resp["compounding_count"], len(pure_comp)))

# every compounding site has crit_violations>0
all_crit = all(s["crit_violations"] > 0 for s in resp["exposed_sites"])
check("V1 compounding sites all have crit_violations>0", all_crit,
      "crit values: %s" % [s["crit_violations"] for s in resp["exposed_sites"]])

# distributor_risk.class1 == real openFDA count (distributors doc, short-name)
dist_doc = db.distributors.find_one({"firm": "DOLE"})
check("V1 distributor_risk.class1 == real openFDA count (DOLE=205)",
      resp["distributor_risk"]["class1"] == dist_doc["class1"],
      "respond=%d db=%d" % (resp["distributor_risk"]["class1"], dist_doc["class1"]))

# swap recommendation names a 0-class1 distributor
swap = resp["recommendation"]["swap_to"]
check("V1 swap recommendation names a 0-class1 distributor",
      swap["class1"] == 0, "swap_to=%s class1=%d" % (swap["firm"], swap["class1"]))


# ── V2: deterministic — same recall doc -> byte-identical Response ──────────
r1 = respond(dole, db)
r2 = respond(dole, db)
j1 = json.dumps(r1, sort_keys=True, default=str)
j2 = json.dumps(r2, sort_keys=True, default=str)
check("V2 deterministic: same recall -> byte-identical Response", j1 == j2,
      "len1=%d len2=%d" % (len(j1), len(j2)))


# ── V3: provenance separates 'real' from 'modeled' — modeled flag present ────
prov = resp.get("provenance", {})
check("V3 Response carries provenance with 'real' + 'modeled' keys",
      "real" in prov and "modeled" in prov, "keys=%s" % list(prov.keys()))

# exposure is via modeled links — assert the modeled flag is present on sites
sites_modeled = all(s.get("class") == "modeled" for s in resp["exposed_sites"])
check("V3 exposed_sites are tagged class:'modeled'", sites_modeled,
      "%d/%d modeled" % (
          sum(1 for s in resp["exposed_sites"] if s.get("class") == "modeled"),
          len(resp["exposed_sites"])))

# distributor_risk + origin are tagged 'real'
check("V3 distributor_risk tagged class:'real'",
      resp["distributor_risk"].get("class") == "real",
      "class=%s" % resp["distributor_risk"].get("class"))
check("V3 origin tagged class:'real'",
      resp["origin"].get("class") == "real",
      "class=%s" % resp["origin"].get("class"))

# no real field is mislabeled modeled and vice-versa
real_fields = set(prov.get("real", []))
modeled_fields = set(prov.get("modeled", []))
check("V3 real and modeled provenance sets are disjoint",
      real_fields.isdisjoint(modeled_fields),
      "overlap=%s" % (real_fields & modeled_fields))


# ── V4: allergen recall -> allergen_match names allergen(s) + category
#      exposure labeled MODELED; pathogen-only -> null (control) ──────────────

# (a) undeclared-allergen recall — find one that also has operator exposure
#     (DOLE FRESH VEGETABLES INC undeclared egg, F-0227-2021) so the full
#     Response is exercised, but any allergen recall works for the match check.
allergen_recall = db.recalls.find_one({
    "hazard_class": "allergen",
    "allergens": {"$ne": []},
    "classification": "Class I",
})
check("V4a found an undeclared-allergen recall", allergen_recall is not None,
      allergen_recall["recall_number"] if allergen_recall else "none")

if allergen_recall:
    resp_a = respond(allergen_recall, db)
    am = resp_a["allergen_match"]
    check("V4a allergen_match is non-null for an allergen recall", am is not None,
          "allergen_match=%s" % am)
    if am:
        check("V4a allergen_match names the allergen(s)",
              len(am.get("allergens", [])) > 0,
              "allergens=%s" % am.get("allergens"))
        check("V4a allergen_match flags category exposure labeled MODELED",
              am.get("class") == "modeled",
              "class=%s" % am.get("class"))
        check("V4a category_exposure is a non-empty dict",
              isinstance(am.get("category_exposure"), dict)
              and len(am.get("category_exposure", {})) > 0,
              "keys=%s" % list(am.get("category_exposure", {}).keys()))

# (b) pathogen-only control — Dole is pathogen, allergen_match must be null
resp_d = respond(dole, db)
check("V4b pathogen-only recall -> allergen_match is null",
      resp_d["allergen_match"] is None,
      "allergen_match=%s" % resp_d["allergen_match"])

# second control: foreign-material hazard -> also null
fm = db.recalls.find_one({"hazard_class": {"$nin": ["allergen", "pathogen"]}})
if fm:
    resp_fm = respond(fm, db)
    check("V4b non-allergen control (foreign-material) -> allergen_match null",
          resp_fm["allergen_match"] is None,
          "hazard_class=%s allergen_match=%s"
          % (fm.get("hazard_class"), resp_fm["allergen_match"]))

# ── summary ─────────────────────────────────────────────────────────────────
npass = sum(1 for t, _, _ in results if t == PASS)
nfail = sum(1 for t, _, _ in results if t == FAIL)
print("\n=== M2 verifications: %d pass, %d fail ===" % (npass, nfail))
sys.exit(0 if nfail == 0 else 1)
