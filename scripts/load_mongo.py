#!/usr/bin/env python3
"""
SCAFFOLD — PRD M0. Load the cached datasets in globe/assets/ into local MongoDB.
The ralph loop implements this; it is a skeleton now (no logic).

Collections (target):
  recalls          <- openFDA food enforcement (from a cached pull)
  establishments   <- nyc-restaurants.json  (+ crit_violations from DOHMH critical_flag='Critical')
  distributors     <- distributor-scorecard.json
  buildings_meta   <- counts only (geometry stays in globe/assets, human-owned)

Requirements (see PRD M0):
  - every doc carries provenance: {source, fetched_at, class:'real'}
  - geocoded docs get a GeoJSON 'loc' field + a 2dsphere index
  - establishments get crit_violations:int (critical food-handling violations, NOT the letter grade)
"""
import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "breadcrumbs"
ASSETS = os.path.join(os.path.dirname(__file__), "..", "globe", "assets")


def load():
    """TODO(M0): drop+reload collections, add 2dsphere indexes, stamp provenance."""
    raise NotImplementedError("ralph M0: implement Mongo load + geo index + crit_violations")


if __name__ == "__main__":
    load()
