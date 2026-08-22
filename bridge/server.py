#!/usr/bin/env python3
"""
SCAFFOLD — PRD M4. The bridge: the ONLY interface between loop-backend and human-frontend.
Serves Mongo-backed JSON the console fetches. The ralph loop implements this.

Endpoints (see bridge/CONTRACT.md for the shapes):
  GET /operator_sites   -> the operator portfolio as GeoJSON (modeled-portfolio labeled)
  GET /response?recall= -> the live M2 Response (exposure/risk/action)
  GET /transcript       -> the M3 swarm tool-call log
  GET /telemetry        -> GB10 telemetry (stub off-box, real NVML on-box in M6)

The loop NEVER edits globe/*.html — the frontend team wires the console from CONTRACT.md.
May also emit static bridge/out/*.json for a fully-offline console.
"""

PORT = 8899


def serve():
    """TODO(M4): tiny local HTTP service reading from Mongo; also write bridge/out/*.json."""
    raise NotImplementedError("ralph M4: bridge server")


if __name__ == "__main__":
    serve()
