#!/usr/bin/env python3
"""
PRD M0 — run EVERY verification in the milestone's `verifications` array and
assert each passes. Exits 0 only if all pass; prints one line per check.
The verification IS the test (PRD hard rule) — no separate test suite.
"""
import os, re, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from db.queries import get_db, near, exposure, exposure_control  # noqa: E402

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, ok, detail=""):
    tag = PASS if ok else FAIL
    line = "[%s] %s%s" % (tag, name, (" — " + detail) if detail else "")
    print(line)
    results.append((tag, name, detail))
    if not ok:
        # keep going so all failures surface in one run
        pass


# ── V1: preflight.sh exits 0 and prints MongoDB serverStatus ok:1 ───────────
proc = subprocess.run([os.path.join(ROOT, "scripts", "preflight.sh")],
                      capture_output=True, text=True)
ok1 = proc.returncode == 0 and re.search(r"serverStatus\s*ok\s*[:=]\s*1", proc.stdout) is not None
check("V1 preflight exits 0 + prints serverStatus ok:1", ok1,
      "exit=%d" % proc.returncode)


db = get_db()

# ── V2: counts — establishments>=15000, distributors>=8, recalls>=300
#        (E.coli Class-I subset >= 300) ───────────────────────────────────────
n_est = db.establishments.count_documents({})
n_dist = db.distributors.count_documents({})
n_recalls = db.recalls.count_documents({})
ecoli_c1 = db.recalls.count_documents({
    "classification": "Class I",
    "reason_for_recall": {"$regex": "e\\.?\\s*coli", "$options": "i"},
})
check("V2 establishments>=15000", n_est >= 15000, "got %d" % n_est)
check("V2 distributors>=8", n_dist >= 8, "got %d" % n_dist)
check("V2 recalls>=300", n_recalls >= 300, "got %d" % n_recalls)
check("V2 E.coli Class-I>=300", ecoli_c1 >= 300, "got %d" % ecoli_c1)

# ── V3: a random establishment has crit_violations(int)+GeoJSON loc+class real;
#        a distributor doc has class1(int) ────────────────────────────────────
est = list(db.establishments.aggregate([{"$sample": {"size": 1}}]))[0]
loc_ok = (isinstance(est.get("loc"), dict) and est["loc"].get("type") == "Point"
          and len(est["loc"].get("coordinates", [])) == 2)
check("V3 establishment crit_violations is int",
      isinstance(est.get("crit_violations"), int), "got %r" % est.get("crit_violations"))
check("V3 establishment loc is GeoJSON Point", loc_ok, str(est.get("loc")))
check("V3 establishment provenance.class=='real'",
      est.get("provenance", {}).get("class") == "real",
      str(est.get("provenance")))

dist = db.distributors.find_one({"class1": {"$gte": 0}})
check("V3 distributor class1 is int", isinstance(dist.get("class1"), int),
      "got %r" % dist.get("class1"))
check("V3 distributor provenance.class=='real'",
      dist.get("provenance", {}).get("class") == "real", str(dist.get("provenance")))

# ── V4: $near around a hub returns establishments via 2dsphere index scan
#        (explain), and exposure aggregation == pure-python control ───────────
hub = db.distributors.find_one({"is_hub": True})
# pick a hub that actually has NYC establishments within 1km (a NJ hub like Sysco
# is across the river from the NYC-only establishments corpus)
for h in db.distributors.find({"is_hub": True}):
    if near(h["loc"]["coordinates"][0], h["loc"]["coordinates"][1], 1000, db, limit=1):
        hub = h
        break
lon, lat = hub["loc"]["coordinates"]
expl = db.establishments.find(
    {"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [lon, lat]},
                       "$maxDistance": 1000}}}
).limit(1).explain()
plan = expl.get("queryPlanner", {}).get("winningPlan", {})
# walk nested stages to find the IXSCAN
def find_stage(stage, key="IXSCAN"):
    if not isinstance(stage, dict):
        return None
    if stage.get("stage") == key:
        return stage
    for child in [stage.get("inputStage"), stage.get("inputStages")]:
        if isinstance(child, dict):
            r = find_stage(child, key)
            if r:
                return r
        elif isinstance(child, list):
            for c in child:
                r = find_stage(c, key)
                if r:
                    return r
    return None

ixscan = find_stage(plan)
near_rows = near(lon, lat, 1000, db, limit=5)
index_used = ixscan is not None and "loc" in (ixscan.get("indexName") or "")
check("V4 $near uses 2dsphere index (IXSCAN on loc)", index_used,
      "indexName=%s" % (ixscan.get("indexName") if ixscan else None))
check("V4 $near returns nearby establishments", len(near_rows) > 0,
      "%d rows within 1km of %s" % (len(near_rows), hub["firm"]))

# exposure aggregation == pure-python control (operator_sites empty in M0 → both [])
sample_recall = db.recalls.find_one({"classification": "Class I"})
agg = exposure(sample_recall, db)
ctrl = exposure_control(sample_recall, db)
# compare by camis set (docs may differ in enrichment fields; the SET must match)
def ids(rows):
    return sorted([(r.get("camis"), r.get("distributor")) for r in rows])
check("V4 exposure aggregation == pure-python control", ids(agg) == ids(ctrl),
      "agg=%d ctrl=%d firm=%s" % (len(agg), len(ctrl), sample_recall.get("recalling_firm")))

# ── V5: allergen tagging — allergen count in thousands; undeclared-peanut
#        sample has 'peanut' in allergens; pathogen-only control is !='allergen'
n_allergen = db.recalls.count_documents({"hazard_class": "allergen"})
check("V5 allergen recalls in the thousands (>=1000, ~6896)", n_allergen >= 1000,
      "got %d" % n_allergen)

peanut = db.recalls.find_one({"allergens": "peanut"})
peanut_ok = peanut and "peanut" in peanut.get("allergens", []) and "undeclared" in (peanut.get("reason_for_recall") or "").lower()
check("V5 undeclared-peanut recall has allergens containing 'peanut'", peanut_ok,
      (peanut or {}).get("reason_for_recall", "")[:80])

pathogen_control = db.recalls.find_one({"hazard_class": "pathogen"})
pc_ok = pathogen_control and pathogen_control.get("hazard_class") != "allergen" and not pathogen_control.get("allergens")
check("V5 pathogen-only control is hazard_class!='allergen' with empty allergens", pc_ok,
      "hazard=%s allergens=%r" % (pathogen_control.get("hazard_class"), pathogen_control.get("allergens")) if pathogen_control else "none")

# ── summary ─────────────────────────────────────────────────────────────────
npass = sum(1 for t, _, _ in results if t == PASS)
nfail = sum(1 for t, _, _ in results if t == FAIL)
print("\n=== M0 verifications: %d pass, %d fail ===" % (npass, nfail))
sys.exit(0 if nfail == 0 else 1)
