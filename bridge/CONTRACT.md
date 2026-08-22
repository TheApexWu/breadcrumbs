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
The M3 swarm tool-call log. TODO(M3): ordered `[{agent, tool, args, result, ts}]`.

## GET /telemetry  → `telemetry.json`
TODO(M4/M6): `{model, tokens_per_sec, unified_gb, watts, agents_concurrent, source:'stub'|'nvml'}`.

## Samples
`bridge/samples/` holds canned payloads (e.g. the Dole-recall response) so the console renders
offline before the live bridge exists.
