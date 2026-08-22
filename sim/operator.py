#!/usr/bin/env python3
"""
SCAFFOLD — PRD M1. The operator model: a ~12-site real portfolio + MODELED supplier links.
The ralph loop implements this.

Hard rules:
  - portfolio = ~12 REAL geocoded DOHMH establishments (class:'modeled-portfolio')
  - each site gets a MODELED primary distributor (nearest-hub rule; class:'modeled-link')
  - alert preferences profile on the operator (severity / scope / category / channel)
  - exposure(recall) is deterministic and pure
"""


def build_portfolio():
    """TODO(M1): pick ~12 real establishments, persist to operator_sites (labeled modeled)."""
    raise NotImplementedError("ralph M1: build_portfolio")


def assign_distributor(site):
    """TODO(M1): nearest-hub modeled link; store rule + class:'modeled-link'."""
    raise NotImplementedError("ralph M1: assign_distributor")


def preferences():
    """TODO(M1): operator alert-preference profile {min_severity, scope, categories, channel}."""
    raise NotImplementedError("ralph M1: preferences profile")


def exposure(recall):
    """TODO(M1): operator_sites whose modeled distributor matches the recall's distributor."""
    raise NotImplementedError("ralph M1: exposure")
