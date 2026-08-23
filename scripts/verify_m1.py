#!/usr/bin/env python3
"""
PRD M1 — run EVERY verification in the milestone's `verifications` array and
assert each passes. Exits 0 only if all pass; prints one line per check.
"""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from db.queries import get_db, exposure  # noqa: E402
from sim.operator import build_portfolio, matches, preferences  # noqa: E402

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

# ── V1: operator_sites has exactly 12 real geocoded establishments, each
#      carrying class:'modeled-portfolio' and a modeled distributor link ──────
n = db.operator_sites.count_documents({})
check("V1 operator_sites count == 12", n == 12, "got %d" % n)

geocoded = 0
modeled_portfolio = 0
has_link = 0
for s in db.operator_sites.find({}):
    loc = s.get("loc")
    if isinstance(loc, dict) and loc.get("type") == "Point" and len(loc.get("coordinates", [])) == 2:
        geocoded += 1
    if s.get("provenance", {}).get("class") == "modeled-portfolio":
        modeled_portfolio += 1
    dl = s.get("distributor_link")
    if isinstance(dl, dict) and dl.get("class") == "modeled-link":
        has_link += 1

check("V1 every site is geocoded (GeoJSON Point)", geocoded == 12, "%d/12" % geocoded)
check("V1 every site has provenance.class=='modeled-portfolio'", modeled_portfolio == 12,
      "%d/12" % modeled_portfolio)
check("V1 every site has a modeled distributor link (class:'modeled-link')", has_link == 12,
      "%d/12" % has_link)


# ── V2: exposure() for a Dole-linked recall returns a deterministic, non-empty
#      subset of operator_sites (same input -> identical output across runs) ──
dole_recall = db.recalls.find_one({
    "recalling_firm": "DOLE FRESH VEGETABLES INC",
    "classification": "Class I",
})
check("V2 found a DOLE Class I recall to test", dole_recall is not None,
      dole_recall["recall_number"] if dole_recall else "none")

ex1 = exposure(dole_recall, db)
ex2 = exposure(dole_recall, db)
check("V2 exposure() for DOLE recall is non-empty", len(ex1) > 0,
      "%d sites exposed" % len(ex1))
check("V2 exposure() is deterministic (run1 == run2)",
      json.dumps(ex1, sort_keys=True, default=str) == json.dumps(ex2, sort_keys=True, default=str),
      "len1=%d len2=%d" % (len(ex1), len(ex2)))

# every exposed site's distributor matches the recall's recalling_firm
all_match = all(
    (s.get("distributor") or "").upper() == dole_recall["recalling_firm"].upper()
    for s in ex1
)
check("V2 every exposed site's distributor == recall's recalling_firm", all_match,
      "firms: %s" % sorted(set(s.get("distributor") for s in ex1)))


# ── V3: every modeled doc is tagged class:'modeled-*' — no modeled doc is
#      mislabeled 'real' ──────────────────────────────────────────────────────
n_real = db.operator_sites.count_documents({"provenance.class": "real"})
check("V3 no operator_site is mislabeled 'real'", n_real == 0, "found %d mislabeled" % n_real)

n_modeled = db.operator_sites.count_documents({"provenance.class": {"$regex": "^modeled-"}})
check("V3 all operator_sites tagged class:'modeled-*'", n_modeled == 12,
      "%d/12 modeled" % n_modeled)


# ── V4: matches(recall, profile) filters correctly ─────────────────────────
#   (a) a Class-I allergen recall matching the profile returns True
#   (b) a Class-III recall outside the profile's categories/allergens returns False
profile = preferences()

# (a) find a Class I recall whose allergens intersect the profile's allergens
class1_allergen = db.recalls.find_one({
    "classification": "Class I",
    "allergens": {"$in": profile["allergens"], "$ne": []},
})
check("V4a found a Class I allergen recall matching the profile",
      class1_allergen is not None,
      ("allergens=%s" % class1_allergen["allergens"]) if class1_allergen else "none")
if class1_allergen:
    ok_a = matches(class1_allergen, profile) is True
    check("V4a Class-I allergen recall matching profile -> matches()==True",
          ok_a, "got %r (allergens=%s)" % (matches(class1_allergen, profile), class1_allergen.get("allergens")))

# (b) find a Class III recall with no matching allergens and non-salad product
class3_outside = db.recalls.find_one({
    "classification": "Class III",
    "allergens": {"$nin": profile["allergens"]},
    "hazard_class": {"$ne": "allergen"},
})
check("V4b found a Class III recall outside the profile",
      class3_outside is not None,
      ("recall=%s" % class3_outside["recall_number"]) if class3_outside else "none")
if class3_outside:
    ok_b = matches(class3_outside, profile) is False
    check("V4b Class-III recall outside profile -> matches()==False",
          ok_b, "got %r" % matches(class3_outside, profile))

# ── summary ─────────────────────────────────────────────────────────────────
npass = sum(1 for t, _, _ in results if t == PASS)
nfail = sum(1 for t, _, _ in results if t == FAIL)
print("\n=== M1 verifications: %d pass, %d fail ===" % (npass, nfail))
sys.exit(0 if nfail == 0 else 1)
