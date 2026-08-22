#!/usr/bin/env python3
"""
SCAFFOLD — PRD M0. The analytical primitives as MongoDB AGGREGATION pipelines.
These are what the agent's tools call. The ralph loop implements them.

Design (PRD hard-rule: Mongo used tastefully):
  - exposure(recall)   : $match + $lookup recalls<->distributors<->operator_sites
  - scorecard()        : $group distributor recall history (class1 / total)
  - compounding(sites) : $match crit_violations>0 among exposed sites
  - near(point, meters): $geoNear / $near on the 2dsphere index
"""


def exposure(recall):
    """TODO(M0/M2): operator_sites whose modeled distributor == recall's distributor."""
    raise NotImplementedError("ralph M0: exposure aggregation")


def scorecard():
    """TODO(M0): distributor risk table via $group."""
    raise NotImplementedError("ralph M0: scorecard aggregation")


def compounding(site_ids):
    """TODO(M0/M2): exposed sites with crit_violations>0 (the compounding signal)."""
    raise NotImplementedError("ralph M0: compounding aggregation")


def near(lon, lat, meters):
    """TODO(M0): establishments within `meters` of a point via 2dsphere index."""
    raise NotImplementedError("ralph M0: geospatial $near")
