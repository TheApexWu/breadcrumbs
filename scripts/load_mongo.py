#!/usr/bin/env python3
"""
PRD M0 — load cached datasets into local MongoDB. Idempotent (drop+reload).
Every doc carries provenance {source, fetched_at, class:'real'}. Geocoded docs
get a GeoJSON 'loc' field + a 2dsphere index so blast-radius/exposure are real
$geoWithin / $near queries.

Collections:
  recalls         <- openFDA food/enforcement (data/recalls.json)
                     + allergens[] + hazard_class derived from reason_for_recall
  establishments  <- nyc-restaurants.json (human-owned, read-only) + crit_violations
                     (count of DOHMH critical_flag='Critical' rows per camis)
  distributors    <- distributor-scorecard.json; NYC hubs geocoded with real loc
  buildings_meta  <- counts only (geometry stays in globe/assets, human-owned)

Critical-violation count is the compounding-risk axis (NOT the letter grade) —
per PRD hard rule. operator_sites is M1; here it is created empty so the exposure
aggregation (db/queries.py) is runnable now and parity-checked against a control.
"""
import json, os, re
from datetime import datetime, timezone
from pymongo import MongoClient, GEOSPHERE

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS = os.path.join(ROOT, "globe", "assets")
DATA = os.path.join(ROOT, "data")
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "breadcrumbs"
FETCH_AT = "2026-08-22"

# Real NYC-area food-distributor hubs (publicly known facility locations).
# Producers (Dole/Fresh Express/Taylor Farms) are recalling firms, not hubs;
# they keep their real recall history but loc=None (no NYC hub).
HUBS = {
    "BALDOR": {"address": "1550 Edgewater St, Bronx, NY 10474", "lat": 40.8125, "lon": -73.8875},
    "RESTAURANT DEPOT": {"address": "66 Wyckoff Ave, Brooklyn, NY 11237", "lat": 40.7053, "lon": -73.9207},
    "JETRO": {"address": "71 Wyckoff Ave, Brooklyn, NY 11237", "lat": 40.7058, "lon": -73.9189},
    "SYSCO": {"address": "Sysco Metro NY, Jersey City, NJ", "lat": 40.7280, "lon": -74.0570},
    "US FOODS": {"address": "500 Oak Point Ave, Bronx, NY 10473", "lat": 40.8170, "lon": -73.8850},
}

ALLERGENS = [
    ("peanut", re.compile(r"\bpeanut\b", re.I)),
    ("tree-nut", re.compile(r"tree nut|almond|walnut|pecan|cashew|pistachio|hazelnut|macadamia|brazil nut|pine nut|\bnut\b", re.I)),
    ("milk", re.compile(r"\bmilk\b|dairy", re.I)),
    ("egg", re.compile(r"\begg\b", re.I)),
    ("soy", re.compile(r"\bsoy\b", re.I)),
    ("wheat", re.compile(r"\bwheat\b|gluten", re.I)),
    ("fish", re.compile(r"\bfish\b", re.I)),
    ("shellfish", re.compile(r"shellfish|crustacean|\bcrab\b|\blobster\b|\bshrimp\b", re.I)),
    ("sesame", re.compile(r"\bsesame\b", re.I)),
]
PATHOGEN_RE = re.compile(
    r"listeria|salmonella|e\.?\s*coli|botulis|norovirus|hepatitis|cyclospora|"
    r"clostridium|campylobacter|vibrio|giardia|cryptosporid", re.I)
FOREIGN_RE = re.compile(r"foreign material|foreign matter|\bmetal\b|\bglass\b|\bplastic\b|\bwood\b|extraneous", re.I)


def provenance(source, cls="real"):
    return {"source": source, "fetched_at": FETCH_AT, "class": cls}


def loc(lon, lat):
    return {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]}


def tag_recall(r):
    reason = (r.get("reason_for_recall") or "")
    low = reason.lower()
    allergens = []
    if "undeclared" in low or ("contains" in low and any(p.search(low) for _, p in ALLERGENS)):
        allergens = [name for name, pat in ALLERGENS if pat.search(low)]
    if allergens:
        hazard = "allergen"
    elif PATHOGEN_RE.search(low):
        hazard = "pathogen"
    elif FOREIGN_RE.search(low):
        hazard = "foreign-material"
    else:
        hazard = "other"
    return allergens, hazard


def load_recalls(db):
    path = os.path.join(DATA, "recalls.json")
    with open(path) as f:
        doc = json.load(f)
    src = doc["meta"]["source"]
    rows = []
    for r in doc["results"]:
        allergens, hazard = tag_recall(r)
        rows.append({
            "recall_number": r.get("recall_number"),
            "event_id": r.get("event_id"),
            "recalling_firm": (r.get("recalling_firm") or "").upper().strip(),
            "classification": r.get("classification"),
            "product_description": r.get("product_description"),
            "reason_for_recall": r.get("reason_for_recall"),
            "recall_initiation_date": r.get("recall_initiation_date"),
            "state": r.get("state"),
            "city": r.get("city"),
            "distribution_pattern": r.get("distribution_pattern"),
            "allergens": allergens,
            "hazard_class": hazard,
            "provenance": provenance(src),
        })
    db.recalls.insert_many(rows)
    db.recalls.create_index("recalling_firm")
    db.recalls.create_index("hazard_class")
    db.recalls.create_index("classification")
    print("  recalls: %d (allergen=%d, pathogen=%d, foreign=%d, other=%d)" %
          (len(rows),
           sum(1 for r in rows if r["hazard_class"] == "allergen"),
           sum(1 for r in rows if r["hazard_class"] == "pathogen"),
           sum(1 for r in rows if r["hazard_class"] == "foreign-material"),
           sum(1 for r in rows if r["hazard_class"] == "other")))


def load_establishments(db):
    with open(os.path.join(ASSETS, "nyc-restaurants.json")) as f:
        rest = json.load(f)
    with open(os.path.join(DATA, "crit-violations.json")) as f:
        crit = json.load(f)["counts"]
    src = rest["meta"]["source"]
    rows = []
    for e in rest["rows"]:
        try:
            lat = float(e["lat"]); lon = float(e["lon"])
        except (KeyError, ValueError, TypeError):
            continue
        camis = e.get("id")
        rows.append({
            "camis": camis,
            "name": e.get("name"),
            "boro": e.get("boro"),
            "cuisine": e.get("cuisine"),
            "grade": e.get("grade"),
            "score": e.get("score"),
            "critical_flag": e.get("critical"),
            "inspection_date": e.get("date"),
            "crit_violations": int(crit.get(camis, 0)),
            "loc": loc(lon, lat),
            "provenance": provenance(src),
        })
    db.establishments.insert_many(rows)
    db.establishments.create_index([("loc", GEOSPHERE)])
    db.establishments.create_index("camis")
    db.establishments.create_index("crit_violations")
    nonzero = sum(1 for r in rows if r["crit_violations"] > 0)
    print("  establishments: %d (crit_violations>0: %d)" % (len(rows), nonzero))


def load_distributors(db):
    with open(os.path.join(ASSETS, "distributor-scorecard.json")) as f:
        sc = json.load(f)
    src = sc["meta"]["source"]
    rows = []
    for c in sc["cards"]:
        firm = c["firm"].upper().strip()
        hub = HUBS.get(firm)
        d = {
            "firm": firm,
            "recalls": int(c.get("recalls", 0)),
            "class1": int(c.get("class1", 0)),
            "capped": bool(c.get("capped", False)),
            "recent": c.get("recent"),
            "recent_product": c.get("recent_product"),
            "recent_reason": c.get("recent_reason"),
            "is_hub": hub is not None,
            "loc": loc(hub["lon"], hub["lat"]) if hub else None,
            "address": hub["address"] if hub else None,
            "provenance": provenance(src),
        }
        rows.append(d)
    db.distributors.insert_many(rows)
    db.distributors.create_index([("loc", GEOSPHERE)])
    db.distributors.create_index("firm")
    hubs = sum(1 for r in rows if r["is_hub"])
    print("  distributors: %d (geocoded hubs: %d)" % (len(rows), hubs))


def load_buildings_meta(db):
    with open(os.path.join(ASSETS, "manhattan_buildings.json")) as f:
        b = json.load(f)
    db.buildings_meta.delete_many({})
    db.buildings_meta.insert_one({
        "count": len(b),
        "source": "Sixth Borough LiDAR buildings (manhattan_buildings.json)",
        "note": "counts only; geometry stays in globe/assets (human-owned)",
        "provenance": provenance("Sixth Borough buildings"),
    })
    print("  buildings_meta: count=%d" % len(b))


def load():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[DB_NAME]
    for name in ("recalls", "establishments", "distributors", "buildings_meta", "operator_sites"):
        db[name].drop()
    print("loading into db '%s' (dropped+reload):" % DB_NAME)
    load_recalls(db)
    load_establishments(db)
    load_distributors(db)
    load_buildings_meta(db)
    # operator_sites is M1's deliverable; create the collection + geo index now so
    # the exposure aggregation (db/queries.py) is runnable + parity-checked in M0.
    db.operator_sites.create_index([("loc", GEOSPHERE)])
    db.operator_sites.create_index("distributor")
    print("  operator_sites: created empty (M1 populates) + 2dsphere index")
    print("done. counts: recalls=%d establishments=%d distributors=%d" %
          (db.recalls.count_documents({}), db.establishments.count_documents({}),
           db.distributors.count_documents({})))


if __name__ == "__main__":
    load()
