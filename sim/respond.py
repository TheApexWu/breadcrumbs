#!/usr/bin/env python3
"""
PRD M2 — the recall-response engine: exposure x risk x action.

Given a real openFDA recall doc, compute:
  EXPOSURE  — which operator sites received the affected lot (via M1 modeled links)
  RISK      — the distributor's real class1 recall count + how many exposed sites
              have crit_violations>0 (the compounding signal — critical
              food-handling violations, NOT the letter grade)
  ACTION    — hold the recalled lot + swap to the lowest-class1 distributor

Deterministic: same recall doc -> byte-identical Response (sorted fields).
Grounded in REAL data; modeled parts are labeled (PRD hard rule: real vs modeled).

respond(recall) -> Response {
  recall,               # the real openFDA doc (product text, reason, firm state)
  exposed_sites,        # via M1 exposure (MODELED supplier links — labeled)
  compounding_count,    # exposed sites with crit_violations>0 (REAL)
  distributor_risk,     # the distributor's real class1 count (REAL)
  origin,               # firm state + Comtrade commodity origin (supporting beat)
  allergen_match,       # allergen(s) + category exposure (MODELED, category-level)
  recommendation,       # hold + swap to lowest-class1 distributor
  provenance,           # separates 'real' fields from 'modeled'
}
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.queries import get_db, scorecard, compounding
from sim.operator import exposure

FETCH_AT = "2026-08-22"

# MODELED: allergen -> food categories that typically carry that allergen.
# Category-level (not per-menu-item — menu data is not available; label roadmap).
# This is the modeled allergen-risk overlay the PRD requires.
ALLERGEN_CATEGORIES = {
    "milk":      ["Dairy & cheese", "Prepared/bakery"],
    "peanut":    ["Nuts & spices", "Prepared/bakery"],
    "tree-nut":  ["Nuts & spices", "Prepared/bakery"],
    "egg":       ["Dairy & cheese", "Prepared/bakery"],
    "soy":       ["Prepared/bakery", "Meat & poultry"],
    "wheat":     ["Prepared/bakery", "Meat & poultry"],
    "fish":      ["Seafood"],
    "shellfish": ["Seafood"],
    "sesame":    ["Prepared/bakery", "Nuts & spices"],
}

# Keyword -> food category for inferring the recall's commodity category from
# product text (used for the Comtrade origin beat). The Comtrade data itself is
# real; the product->category inference is modeled (labeled).
CATEGORY_KEYWORDS = [
    ("salad", "Leafy greens"), ("lettuce", "Leafy greens"),
    ("spinach", "Leafy greens"), ("kale", "Leafy greens"),
    ("greens", "Leafy greens"), ("cabbage", "Leafy greens"),
    ("cheese", "Dairy & cheese"), ("dairy", "Dairy & cheese"),
    ("milk", "Dairy & cheese"), ("cream", "Dairy & cheese"),
    ("yogurt", "Dairy & cheese"),
    ("nut", "Nuts & spices"), ("peanut", "Nuts & spices"),
    ("almond", "Nuts & spices"), ("walnut", "Nuts & spices"),
    ("cashew", "Nuts & spices"), ("pecan", "Nuts & spices"),
    ("spice", "Nuts & spices"), ("seed", "Nuts & spices"),
    ("meat", "Meat & poultry"), ("chicken", "Meat & poultry"),
    ("beef", "Meat & poultry"), ("pork", "Meat & poultry"),
    ("poultry", "Meat & poultry"), ("turkey", "Meat & poultry"),
    ("sausage", "Meat & poultry"),
    ("fish", "Seafood"), ("salmon", "Seafood"), ("tuna", "Seafood"),
    ("shrimp", "Seafood"), ("crab", "Seafood"), ("lobster", "Seafood"),
    ("seafood", "Seafood"),
    ("fruit", "Fruit"), ("apple", "Fruit"), ("banana", "Fruit"),
    ("orange", "Fruit"), ("berry", "Fruit"), ("strawberry", "Fruit"),
    ("mango", "Fruit"), ("grape", "Fruit"),
]


def _infer_category(recall):
    """Infer the food category from the recall's product text. Returns
    (category, hs) or (None, None) if no keyword matches."""
    text = " ".join([
        recall.get("product_description") or "",
        recall.get("reason_for_recall") or "",
    ]).lower()
    for kw, cat in CATEGORY_KEYWORDS:
        if kw in text:
            return cat
    return None


def _commodity_origin(recall, db):
    """The origin beat: firm state (REAL, from openFDA) + Comtrade commodity
    origin (REAL Comtrade data). The product->category inference is modeled."""
    category = _infer_category(recall)
    origin = {
        "firm_state": recall.get("state"),
        "commodity_category": category,
        "commodity_origin": [],
        "class": "real",
        "note": "firm state from openFDA; commodity category inferred from product text; "
                "origin from UN Comtrade US-imports preview",
    }
    if category:
        sources_path = os.path.join(
            os.path.dirname(__file__), "..", "globe", "assets", "food-sources.json"
        )
        try:
            with open(sources_path) as f:
                sources = json.load(f)
            entry = sources.get("byCategory", {}).get(category, {})
            origin["commodity_origin"] = entry.get("top_sources", [])
        except (OSError, ValueError):
            pass
    return origin


def _distributor_risk(recall, db):
    """The distributor's real class1 recall count. Matched by short name
    (distributors collection stores short names; recalls use full firm names).
    Falls back to the scorecard aggregation by full recalling_firm."""
    firm_full = (recall.get("recalling_firm") or "").upper().strip()
    if not firm_full:
        return {"firm": None, "class1": 0, "recalls": 0, "class": "real"}

    # Prefer the distributors doc (real scorecard, aggregated by short name).
    # Match: the distributor whose short firm-name is a prefix of the full
    # recalling_firm (e.g. "DOLE" prefix of "DOLE FRESH VEGETABLES INC").
    best = None
    for d in db.distributors.find({}):
        short = (d.get("firm") or "").upper().strip()
        if short and firm_full.startswith(short):
            if best is None or len(short) > len(best.get("firm", "")):
                best = d
    if best:
        return {
            "firm": best.get("firm"),
            "class1": int(best.get("class1", 0)),
            "recalls": int(best.get("recalls", 0)),
            "class": "real",
        }

    # Fallback: scorecard aggregation by full recalling_firm.
    for row in scorecard(db):
        if (row.get("firm") or "").upper() == firm_full:
            return {
                "firm": row["firm"],
                "class1": int(row.get("class1", 0)),
                "recalls": int(row.get("recalls", 0)),
                "class": "real",
            }
    return {"firm": recall.get("recalling_firm"), "class1": 0, "recalls": 0, "class": "real"}


def _swap_target(db):
    """The lowest-class1 distributor to swap to. Among 0-class1 hubs, pick
    deterministically (alphabetical by firm). Baldor (0, hub) wins."""
    candidates = []
    for d in db.distributors.find({"is_hub": True}):
        candidates.append({
            "firm": d.get("firm"),
            "class1": int(d.get("class1", 0)),
            "recalls": int(d.get("recalls", 0)),
            "class": "real",
        })
    candidates.sort(key=lambda c: (c["class1"], c["firm"]))
    return candidates[0] if candidates else {"firm": None, "class1": 0, "class": "real"}


def _allergen_match(recall):
    """For an allergen recall (hazard_class='allergen'), name the allergen(s)
    + which food categories carry that allergen risk (CATEGORY-level, MODELED).
    Returns None for non-allergen recalls (pathogen/foreign-material/other)."""
    if recall.get("hazard_class") != "allergen":
        return None
    allergens = recall.get("allergens") or []
    if not allergens:
        return None
    category_exposure = {}
    for a in allergens:
        cats = ALLERGEN_CATEGORIES.get(a, [])
        if cats:
            category_exposure[a] = sorted(cats)
    return {
        "allergens": sorted(allergens),
        "category_exposure": category_exposure,
        "class": "modeled",
        "roadmap": "per-menu-item allergen matching needs menu data not available",
    }


def _exposed_sites(recall, db):
    """The exposed operator sites (via M1 modeled supplier links). Stripped to
    stable fields + sorted by camis for determinism."""
    rows = exposure(recall, db)
    out = []
    for s in rows:
        out.append({
            "camis": s.get("camis"),
            "name": s.get("name"),
            "boro": s.get("boro"),
            "cuisine": s.get("cuisine"),
            "crit_violations": int(s.get("crit_violations", 0)),
            "distributor": s.get("distributor"),
            "class": "modeled",
        })
    out.sort(key=lambda s: str(s.get("camis", "")))
    return out


def respond(recall, db=None):
    """Compute the full recall-response: exposure x risk x action.
    Returns a structured Response object. Deterministic: same recall ->
    byte-identical Response."""
    db = get_db() if db is None else db

    exposed = _exposed_sites(recall, db)
    exposed_camis = [s["camis"] for s in exposed]
    comp = compounding(exposed_camis, db)
    compounding_count = len(comp)

    dist_risk = _distributor_risk(recall, db)
    origin = _commodity_origin(recall, db)
    allergen = _allergen_match(recall)
    swap = _swap_target(db)

    response = {
        "recall": {
            "recall_number": recall.get("recall_number"),
            "recalling_firm": recall.get("recalling_firm"),
            "classification": recall.get("classification"),
            "product_description": recall.get("product_description"),
            "reason_for_recall": recall.get("reason_for_recall"),
            "state": recall.get("state"),
            "hazard_class": recall.get("hazard_class"),
            "allergens": sorted(recall.get("allergens") or []),
        },
        "exposed_sites": exposed,
        "exposed_count": len(exposed),
        "compounding_count": compounding_count,
        "distributor_risk": dist_risk,
        "origin": origin,
        "allergen_match": allergen,
        "recommendation": {
            "action": "hold",
            "swap_to": swap,
            "rationale": "hold the recalled lot; swap sourcing to the lowest-class1 "
                        "distributor to minimize repeat-recall risk",
            "class": "modeled",
        },
        "provenance": {
            "real": ["recall", "compounding_count", "distributor_risk", "origin"],
            "modeled": ["exposed_sites", "allergen_match", "recommendation"],
        },
    }
    return response


def respond_json(recall, db=None):
    """JSON-serializable Response (sorted keys) for deterministic comparison."""
    return json.dumps(respond(recall, db), sort_keys=True, default=str)


if __name__ == "__main__":
    db = get_db()
    dole = db.recalls.find_one({"recall_number": "F-0757-2022"})
    if not dole:
        dole = db.recalls.find_one({
            "recalling_firm": "DOLE FRESH VEGETABLES INC",
            "classification": "Class I",
        })
    resp = respond(dole, db)
    print(json.dumps(resp, indent=2, default=str))
