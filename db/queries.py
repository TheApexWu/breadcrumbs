#!/usr/bin/env python3
"""
PRD M0 — the analytical primitives as MongoDB AGGREGATION pipelines.
These are what the agent's tools call (M3). Real Mongo $lookup/$group/$geoNear,
not hand-rolled JS loops (PRD hard rule: Mongo used tastefully).

  exposure(recall)    : operator_sites whose modeled distributor == recall's firm
                        ($match + $lookup recalls<->distributors<->sites)
  scorecard()         : distributor recall history via $group over recalls
  compounding(site_ids): exposed sites with crit_violations>0 ($match)
  near(lon,lat,m)     : establishments within m of a point ($geoNear on 2dsphere)

operator_sites is populated in M1; until then exposure() returns [] and the
pure-python control returns [] too — the M0 parity check holds (both empty).
M1/M2 make the set non-empty and the real exposure assertions land there.
"""
import os
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "breadcrumbs"


def get_db():
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)[DB_NAME]


def exposure(recall, db=None):
    """Exposed operator_sites for a recall: sites whose modeled distributor
    matches the recall's recalling_firm. Enriched with the distributor doc and
    the firm's recall history via $lookup."""
    db = get_db() if db is None else db
    firm = (recall.get("recalling_firm") or "").upper().strip()
    if not firm:
        return []
    pipeline = [
        {"$match": {"distributor": firm}},
        {"$lookup": {"from": "distributors", "localField": "distributor",
                     "foreignField": "firm", "as": "distributor_doc"}},
        {"$lookup": {"from": "recalls", "localField": "distributor",
                     "foreignField": "recalling_firm", "as": "recall_history"}},
    ]
    return list(db.operator_sites.aggregate(pipeline))


def exposure_control(recall, db=None):
    """Pure-python control for exposure(): same join, no aggregation engine.
    Used by M0 verification to prove the aggregation returns the same set."""
    db = get_db() if db is None else db
    firm = (recall.get("recalling_firm") or "").upper().strip()
    if not firm:
        return []
    return [s for s in db.operator_sites.find({"distributor": firm}, {"_id": 0})]


def scorecard(db=None):
    """Distributor recall-history scorecard via $group over the recalls
    collection: {firm, recalls, class1}. Mirrors distributor-scorecard.json but
    derived live from the loaded recall corpus."""
    db = get_db() if db is None else db
    pipeline = [
        {"$group": {"_id": "$recalling_firm",
                    "recalls": {"$sum": 1},
                    "class1": {"$sum": {"$cond": [{"$eq": ["$classification", "Class I"]}, 1, 0]}}}},
        {"$project": {"_id": 0, "firm": "$_id", "recalls": 1, "class1": 1}},
        {"$sort": {"class1": -1}},
    ]
    return list(db.recalls.aggregate(pipeline))


def compounding(site_ids, db=None):
    """Exposed sites with crit_violations>0 — the compounding-risk signal
    (critical food-handling violations, NOT the letter grade)."""
    db = get_db() if db is None else db
    if not site_ids:
        return []
    pipeline = [
        {"$match": {"camis": {"$in": list(site_ids)}, "crit_violations": {"$gt": 0}}},
        {"$project": {"_id": 0, "camis": 1, "name": 1, "crit_violations": 1,
                      "grade": 1, "loc": 1}},
    ]
    return list(db.establishments.aggregate(pipeline))


def near(lon, lat, meters, db=None, limit=200):
    """Establishments within `meters` of (lon,lat) via $geoNear on the 2dsphere
    index. Returns nearest-first."""
    db = get_db() if db is None else db
    pipeline = [
        {"$geoNear": {"near": {"type": "Point", "coordinates": [lon, lat]},
                      "distanceField": "dist_meters", "maxDistance": meters,
                      "spherical": True}},
        {"$limit": limit},
        {"$project": {"_id": 0, "camis": 1, "name": 1, "boro": 1, "dist_meters": 1,
                      "crit_violations": 1, "loc": 1}},
    ]
    return list(db.establishments.aggregate(pipeline))


if __name__ == "__main__":
    db = get_db()
    print("scorecard (top 5):")
    for s in scorecard(db)[:5]:
        print("  %-20s recalls=%-5d class1=%-4d" % (s["firm"], s["recalls"], s["class1"]))
    print("near Baldor hub (1km):")
    for s in near(-73.8875, 40.8125, 1000, db, limit=5):
        print("  %s (%.0fm) crit=%d" % (s.get("name"), s["dist_meters"], s["crit_violations"]))
