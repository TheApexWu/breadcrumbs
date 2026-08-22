#!/usr/bin/env python3
"""
SCAFFOLD — PRD M3. The agent swarm via NemoClaw (OpenClaw off-box, one adapter).
The ralph loop implements this.

Roles (tool-calling over db/queries + sim/respond + Mongo):
  Watcher  - subscribes to a Mongo CHANGE STREAM on recalls; a new insert fires the swarm
             (honors the operator alert-preference profile before firing)
  Tracer   - calls exposure()
  Risk     - calls score (distributor class1 + compounding)
  Briefer  - composes the plain-language brief (grounded in the M2 Response, no invented numbers)
  Comms    - drafts the SMS + supplier hold notice (M5)

Model behind ONE adapter: OpenRouter/glm off-box  <->  local Nemotron via NemoClaw on-box.
Every tool-call (name, args, result) is logged to an evidence transcript.
"""


class ModelAdapter:
    """TODO(M3): single swap point OpenRouter(OpenClaw) <-> local Nemotron(NemoClaw)."""
    def complete(self, prompt, tools=None):
        raise NotImplementedError("ralph M3: model adapter")


def run(recall):
    """TODO(M3): Watcher->Tracer->Risk->Briefer->Comms; return the structured brief + transcript."""
    raise NotImplementedError("ralph M3: swarm run")
