# bridge/ — data contract (loop-backend → human-frontend)

SCAFFOLD. The ralph loop fills the shapes in as M2–M4 land. The frontend team wires
`globe/food3d.html` against THIS doc — never against backend code. Every field is tagged
`real` or `modeled`; the console must surface that distinction (instrument, not oracle).

The loop serves these over `http://localhost:8899` and/or as static `bridge/out/*.json` (offline).

## GET /operator_sites  → `operator_sites.json`
GeoJSON FeatureCollection of the operator's ~12 sites. TODO(M1): fields — name, boro, `loc`
(GeoJSON Point), `distributor` (modeled), `crit_violations` (real), `class:'modeled-portfolio'`.

## GET /response?recall=<id>  → `response.json`
The M2 Response. TODO(M2): `{recall, exposed_sites[], compounding_count, distributor_risk{class1,total},
origin, recommendation, provenance{real[], modeled[]}}`.

## GET /transcript  → `transcript.json`
The M3 swarm tool-call log. Ordered list, one entry per tool-call:
```json
[{
  "agent": "Watcher|Tracer|Risk|Briefer|Comms",
  "tool": "watch_feed|ingest_recall|trace_forward|score_risk|brief|draft_sms",
  "args": {…},
  "result": {…},
  "ts": "YYYY-MM-DDTHH:MM:SSZ",
  "concurrent": false
}]
```
Canonical order: `watch_feed → ingest_recall → trace_forward → score_risk → brief → draft_sms`
(`trace_forward` and the distributor-risk lookup run concurrently; the canonical
subsequence is preserved). `agent_memory` decisions are NOT in the transcript —
they live in the `agent_memory` Mongo collection (run_id, recall_id, decision,
alert_sent, ts).

## GET /telemetry  → `telemetry.json`
TODO(M4/M6): `{model, tokens_per_sec, unified_gb, watts, agents_concurrent, source:'stub'|'nvml'}`.

## Samples
`bridge/samples/` holds canned payloads (e.g. the Dole-recall response) so the console renders
offline before the live bridge exists.
