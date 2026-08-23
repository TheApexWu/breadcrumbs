#!/usr/bin/env python3
"""
PRD M1 — the operator model: a ~12-site real portfolio + MODELED supplier links
+ an alert-preference profile. Persisted to Mongo operator_sites.

Hard rules:
  - portfolio = 12 REAL geocoded DOHMH establishments (provenance class:'modeled-portfolio')
  - each site gets a MODELED primary distributor (nearest-hub rule over the 5 real
    NYC hubs; class:'modeled-link') — the proprietary supplier→site edge
  - produce/salad sites also carry a MODELED produce-supplier link (the recalling
    firm whose products they carry, e.g. DOLE FRESH VEGETABLES INC) — this IS the
    exposure join key and IS the FSMA-204 gap (proprietary in reality, labeled modeled)
  - alert-preference profile: {min_severity, scope, categories, allergens, channel, quiet_hours}
  - matches(recall, profile) -> bool decides whether a recall alerts
  - exposure(recall) -> operator_sites whose distributor matches the recall's
    recalling_firm; deterministic and pure (sorted by camis for stable ordering)
"""
import math, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pymongo import GEOSPHERE
from db.queries import get_db, exposure as _exposure

MONGO_URI = None  # inherited from db.queries
FETCH_AT = "2026-08-22"

# The 5 real NYC-area food-distributor hubs (publicly known facility locations).
HUBS = {
    "BALDOR": {"lat": 40.8125, "lon": -73.8875},
    "RESTAURANT DEPOT": {"lat": 40.7053, "lon": -73.9207},
    "JETRO": {"lat": 40.7058, "lon": -73.9189},
    "SYSCO": {"lat": 40.7280, "lon": -74.0570},
    "US FOODS": {"lat": 40.8170, "lon": -73.8850},
}

# The portfolio: 12 real DOHMH establishments selected by camis. A mix of salad
# restaurants (modeled to source produce from DOLE / Fresh Express / Taylor Farms —
# the suppliers whose recalls flow through the hub to the site) and other
# restaurants (modeled to source from their nearest hub directly).
PORTFOLIO = [
    # — Salads → DOLE FRESH VEGETABLES INC (hero recall supplier) —
    {"camis": "50017041", "supplier": "DOLE FRESH VEGETABLES INC"},
    {"camis": "50035721", "supplier": "DOLE FRESH VEGETABLES INC"},
    {"camis": "50088095", "supplier": "DOLE FRESH VEGETABLES INC"},
    {"camis": "50161809", "supplier": "DOLE FRESH VEGETABLES INC"},
    {"camis": "50125151", "supplier": "DOLE FRESH VEGETABLES INC"},
    # — Salads → FRESH EXPRESS INCORPORATED —
    {"camis": "50008140", "supplier": "FRESH EXPRESS INCORPORATED"},
    {"camis": "41315226", "supplier": "FRESH EXPRESS INCORPORATED"},
    # — Salads → TAYLOR FARMS, INC. —
    {"camis": "50179229", "supplier": "TAYLOR FARMS, INC."},
    # — Other cuisines → nearest hub (the modeled primary distributor) —
    {"camis": "50124505", "supplier": None},
    {"camis": "41016607", "supplier": None},
    {"camis": "50011908", "supplier": None},
    {"camis": "50129823", "supplier": None},
]

# The default alert-preference profile. Settable in plain English via
# parse_profile() OR as toggles fields directly.
DEFAULT_PROFILE = {
    "min_severity": "Class I",
    "scope": {
        "suppliers": [
            "DOLE FRESH VEGETABLES INC",
            "FRESH EXPRESS INCORPORATED",
            "TAYLOR FARMS, INC.",
        ],
        "radius_m": None,
    },
    "categories": ["salad", "produce", "leafy", "lettuce", "spinach", "greens"],
    "allergens": [
        "peanut", "tree-nut", "milk", "egg", "soy",
        "wheat", "sesame", "fish", "shellfish",
    ],
    "channel": "telegram",
    "quiet_hours": {"start": "23:00", "end": "06:00"},
}

SEVERITY = {"Class I": 1, "Class II": 2, "Class III": 3}


def _haversine(lon1, lat1, lon2, lat2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_hub(lon, lat):
    """Nearest of the 5 real NYC hubs to (lon, lat). Returns (hub_name, distance_m)."""
    best_name, best_d = None, float("inf")
    for name, h in HUBS.items():
        d = _haversine(lon, lat, h["lon"], h["lat"])
        if d < best_d:
            best_name, best_d = name, d
    return best_name, round(best_d, 1)


def assign_distributor(site):
    """MODELED primary distributor for a site: nearest-hub rule over the 5 real
    NYC hubs. If the site carries a produce supplier (the proprietary supplier→site
    edge), that supplier is the exposure-join key. The hub is always stored as the
    primary distribution route. Returns a dict tagged class:'modeled-link'."""
    lon, lat = site["loc"]["coordinates"]
    hub, dist = nearest_hub(lon, lat)
    return {
        "primary_hub": hub,
        "hub_distance_m": dist,
        "hub_rule": "nearest-hub",
        "distributor_link": {"class": "modeled-link", "rule": "nearest-hub"},
    }


def build_portfolio(db=None):
    """Pick 12 real DOHMH establishments, assign each a MODELED distributor
    (nearest-hub + produce-supplier link where applicable), persist to
    operator_sites. Idempotent (drop+reload)."""
    db = get_db() if db is None else db
    db.operator_sites.drop()

    rows = []
    for spec in PORTFOLIO:
        est = db.establishments.find_one({"camis": spec["camis"]})
        if not est:
            raise ValueError("establishment camis=%s not found in DB" % spec["camis"])

        hub = assign_distributor(est)
        supplier = spec["supplier"] or hub["primary_hub"]

        doc = {
            "camis": est["camis"],
            "name": est.get("name"),
            "boro": est.get("boro"),
            "cuisine": est.get("cuisine"),
            "grade": est.get("grade"),
            "crit_violations": est.get("crit_violations", 0),
            "loc": est["loc"],
            "distributor": supplier,
            "distributor_rule": "produce-supplier" if spec["supplier"] else "nearest-hub",
            "primary_hub": hub["primary_hub"],
            "hub_distance_m": hub["hub_distance_m"],
            "hub_rule": hub["hub_rule"],
            "distributor_link": hub["distributor_link"],
            "provenance": {
                "source": "NYC DOHMH (real establishment) + modeled supplier link",
                "fetched_at": FETCH_AT,
                "class": "modeled-portfolio",
            },
        }
        rows.append(doc)

    db.operator_sites.insert_many(rows)
    db.operator_sites.create_index([("loc", GEOSPHERE)])
    db.operator_sites.create_index("distributor")
    db.operator_sites.create_index("camis")

    return rows


def preferences():
    """The operator's default alert-preference profile."""
    return dict(DEFAULT_PROFILE)


def matches(recall, profile):
    """Decide whether a recall alerts based on the alert-preference profile.
    Returns True only if the recall passes severity AND matches at least one
    specified relevance criterion (supplier, category, or allergen). A filter
    that lets everything through fails — each gate is discriminating."""
    rc = recall.get("classification", "Class III")
    if SEVERITY.get(rc, 3) > SEVERITY.get(profile.get("min_severity", "Class III"), 3):
        return False

    has_criteria = False
    matched = False

    suppliers = (profile.get("scope") or {}).get("suppliers") or []
    if suppliers:
        has_criteria = True
        firm = (recall.get("recalling_firm") or "").upper().strip()
        if firm in [s.upper().strip() for s in suppliers]:
            matched = True

    profile_allergens = profile.get("allergens") or []
    if profile_allergens:
        has_criteria = True
        if set(recall.get("allergens") or []) & set(profile_allergens):
            matched = True

    cats = profile.get("categories") or []
    if cats:
        has_criteria = True
        text = " ".join([
            (recall.get("product_description") or ""),
            (recall.get("reason_for_recall") or ""),
        ]).lower()
        if any(c.lower() in text for c in cats):
            matched = True

    if has_criteria and not matched:
        return False
    return True


def exposure(recall, db=None):
    """Operator sites exposed to a recall: sites whose MODELED distributor
    matches the recall's recalling_firm. Deterministic and pure — output is
    sorted by camis for byte-identical results across runs."""
    rows = _exposure(recall, db)
    return sorted(rows, key=lambda r: str(r.get("camis", "")))


def parse_profile(text):
    """Parse a plain-English alert-preference description into a profile dict.
    e.g. 'Alert on Class I recalls for peanut and milk from Dole' ->
         {min_severity: 'Class I', allergens: ['peanut', 'milk'],
          scope: {suppliers: ['DOLE FRESH VEGETABLES INC'], ...}, ...}
    """
    import re
    p = dict(DEFAULT_PROFILE)
    low = text.lower()

    for cls in ["class i", "class ii", "class iii"]:
        if cls in low:
            p["min_severity"] = cls.title()
            break

    all_allergens = ["peanut", "tree-nut", "milk", "egg", "soy", "wheat",
                     "fish", "shellfish", "sesame"]
    found = [a for a in all_allergens if a in low]
    if found:
        p["allergens"] = found

    if "dole" in low:
        p["scope"] = dict(p["scope"])
        p["scope"]["suppliers"] = ["DOLE FRESH VEGETABLES INC"]
    if "telegram" in low:
        p["channel"] = "telegram"
    elif "digest" in low:
        p["channel"] = "digest"
    elif "console" in low:
        p["channel"] = "console"

    return p


if __name__ == "__main__":
    db = get_db()
    rows = build_portfolio(db)
    print("operator_sites: %d sites loaded" % len(rows))
    for r in rows:
        print("  %-28s %-12s dist=%-8s supplier=%s" % (
            r["name"], r["boro"], r.get("cuisine", ""),
            r["distributor"]))
