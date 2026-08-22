#!/usr/bin/env python3
"""
SCAFFOLD — PRD M2. The recall-response engine: exposure x risk x action.
The ralph loop implements this. Deterministic; grounded in REAL data.

respond(recall) -> Response {
  recall,               # the real openFDA doc (product text, reason, firm state)
  exposed_sites,        # from M1 exposure (via MODELED links — labeled)
  compounding_count,    # exposed sites with crit_violations>0 (REAL)
  distributor_risk,     # the distributor's real class1 count (REAL)
  origin,               # firm state + Comtrade commodity origin (supporting beat)
  recommendation,       # hold + swap to lowest-class1 distributor
  provenance,           # separates 'real' fields from 'modeled'
}
"""


def respond(recall):
    """TODO(M2): compute exposure, risk (distributor class1 + compounding), action."""
    raise NotImplementedError("ralph M2: respond")
