# bridge/ — data contract (loop-backend → human-frontend)

The ONLY interface between the loop-backend and the human-built frontend.
The frontend team wires `globe/food3d.html` against THIS doc — never against
backend code. Every field is tagged `real` or `modeled`; the console must
surface that distinction (instrument, not oracle — PRD hard rule).

Served live over `http://127.0.0.1:8899` AND mirrored as static
`bridge/out/*.json` (committed; the console renders fully offline, with the
network unplugged). Stable canned payloads also live in `bridge/samples/`.

The loop NEVER edits `globe/*.html`, `globe/assets/*`, `mockups/`, or `docs/`.

## Endpoints

| Method | Path                          | Static mirror              | Description |
|--------|-------------------------------|----------------------------|-------------|
| GET    | `/operator_sites`             | `operator_sites.json`      | operator portfolio (GeoJSON) |
| GET    | `/response?recall=<id>`       | `response.json`            | live M2 Response (exposure/risk/action) |
| GET    | `/transcript?recall=<id>`     | `transcript.json`          | M3 swarm tool-call log |
| GET    | `/telemetry`                  | `telemetry.json`           | GB10 telemetry (stub off-box; real NVML on-box M6) |
| GET    | `/healthz`                    | —                          | liveness |

`<id>` is the openFDA `recall_number` (e.g. `F-0757-2022`) OR the
`recalling_firm`. Defaults to the Dole hero recall `F-0757-2022`.

---

## GET /operator_sites → `operator_sites.json`

GeoJSON `FeatureCollection` of the operator's ~12 sites. Each Feature is a
REAL geocoded DOHMH establishment; the supplier→site link is MODELED (the
FSMA-204 proprietary gap — labeled everywhere).

```json
{
  "type": "FeatureCollection",
  "count": 12,
  "provenance": { "class": "modeled-portfolio", "note": "..." },
  "features": [{
    "type": "Feature",
    "geometry": { "type": "Point", "coordinates": [lon, lat] },
    "properties": {
      "camis":            "50017041",          // string — DOHMH establishment id
      "name":             "SWEETGREEN",        // string
      "boro":             "Manhattan",         // string
      "cuisine":          "Salads",            // string
      "grade":            "A",                 // string|null — letter grade (composite; NOT the risk axis)
      "crit_violations":  11,                  // int — REAL DOHMH critical food-handling violations (the risk axis)
      "distributor":      "DOLE FRESH VEGETABLES INC",  // string — MODELED supplier link (exposure join key)
      "distributor_rule": "produce-supplier",  // "produce-supplier" | "nearest-hub"
      "primary_hub":      "US FOODS",          // string — MODELED nearest-hub
      "hub_distance_m":   52.3,                // float — meters to nearest hub
      "provenance": {
        "source":      "NYC DOHMH (real establishment) + modeled supplier link",
        "fetched_at":  "2026-08-22",
        "class":       "modeled-portfolio"     // provenance class
      }
    }
  }]
}
```

Provenance: `geometry`, `camis`, `name`, `boro`, `cuisine`, `grade`,
`crit_violations` = **real** (DOHMH). `distributor`, `distributor_rule`,
`primary_hub`, `hub_distance_m` = **modeled** (supplier→site edge).

---

## GET /response?recall=<id> → `response.json`

The M2 recall-response: exposure × risk × action. Numbers come straight from
`sim/respond.respond()` — the bridge never recomputes, so there is no drift
from the backend Response. Deterministic: same recall → identical payload.

```json
{
  "recall": {
    "recall_number":       "F-0757-2022",      // string — openFDA id
    "recalling_firm":      "DOLE FRESH VEGETABLES INC",  // string
    "classification":      "Class I",          // string — Class I|II|III
    "product_description": "...",              // string — REAL openFDA text
    "reason_for_recall":   "...",              // string — REAL openFDA text
    "state":               "NE",               // string — firm state (origin beat)
    "hazard_class":        "pathogen",         // allergen|pathogen|foreign-material|other
    "allergens":           []                  // string[] — parsed from reason_for_recall
  },
  "exposed_sites": [{                          // MODELED — via M1 supplier links
    "camis":           "50017041",
    "name":            "SWEETGREEN",
    "boro":            "Manhattan",
    "cuisine":         "Salads",
    "crit_violations": 11,                     // int — REAL (compounding signal)
    "distributor":     "DOLE FRESH VEGETABLES INC",
    "class":           "modeled"
  }],
  "exposed_count":      5,                     // int — len(exposed_sites)
  "compounding_count":  5,                     // int — REAL: # exposed with crit_violations>0
  "distributor_risk": {                        // REAL — distributor's openFDA class1 history
    "firm":    "DOLE",
    "class1":  205,                            // int — Class I recall count
    "recalls": 236,                            // int — total recall count
    "class":   "real"
  },
  "origin": {                                  // REAL — firm state + Comtrade commodity origin
    "firm_state":          "NE",
    "commodity_category":  "Leafy greens",     // inferred from product text (modeled inference)
    "commodity_origin":    [],                 // top source countries (real Comtrade)
    "class":               "real",
    "note":                "..."
  },
  "allergen_match": null,                      // MODELED — non-null only for hazard_class='allergen'
  /* allergen_match shape when present:
  {
    "allergens":           ["milk"],
    "category_exposure":   { "milk": ["Dairy & cheese", "Prepared/bakery"] },
    "class":               "modeled",
    "roadmap":             "per-menu-item matching needs menu data not available"
  } */
  "recommendation": {                          // MODELED
    "action":    "hold",
    "swap_to":   { "firm": "BALDOR", "class1": 0, "recalls": 0, "class": "real" },
    "rationale": "hold the recalled lot; swap sourcing to the lowest-class1 distributor...",
    "class":     "modeled"
  },
  "provenance": {
    "real":    ["recall", "compounding_count", "distributor_risk", "origin"],
    "modeled": ["exposed_sites", "allergen_match", "recommendation"]
  }
}
```

---

## GET /transcript?recall=<id> → `transcript.json`

The M3 swarm tool-call log — proof the agent ACTS (visible autonomous
tool-calls). Ordered list, one entry per tool-call. Running this endpoint
executes the swarm (which persists to `agent_memory` and dedupes re-runs).

```json
{
  "recall_number":    "F-0757-2022",
  "deduped":          false,                   // bool — true if prior alert recalled (no re-alert)
  "alert_count":      1,                       // int — total alerts sent for this recall (stays 1 across re-runs)
  "canonical_order":  ["watch_feed", "ingest_recall", "trace_forward",
                       "score_risk", "brief", "draft_sms"],
  "entries": [{
    "agent":      "Watcher|Tracer|Risk|Briefer|Comms",
    "tool":       "watch_feed|ingest_recall|trace_forward|score_risk|brief|draft_sms",
    "args":       { "...": "..." },
    "result":     { "...": "..." },
    "ts":         "2026-08-22T16:12:00Z",
    "concurrent": false                        // bool — true for Tracer + distributor-risk (parallel)
  }],
  "provenance": { "class": "real", "source": "agent.swarm transcript log" }
}
```

Canonical subsequence: `watch_feed → ingest_recall → trace_forward →
score_risk → brief → draft_sms` (`trace_forward` and the distributor-risk
lookup run concurrently; the canonical subsequence is preserved).
`agent_memory` decisions are NOT in the transcript — they live in the
`agent_memory` Mongo collection (`run_id`, `recall_id`, `decision`,
`alert_sent`, `ts`, `response_summary`).

---

## GET /telemetry → `telemetry.json`

GB10 telemetry HUD. **Stub off-box** (M4); M6 wires real NVML/tegrastats on
the GB10. `nvidia-smi` under-reports on GB10 unified memory — M6 reads
`tegrastats`.

```json
{
  "model":               "openrouter/glm (off-box stub; on-box swap -> Nemotron/NemoClaw)",
  "tokens_per_sec":      null,                 // float|null — M6 real
  "unified_gb":          null,                 // float|null — M6 real (of 128)
  "unified_gb_total":    128,                  // int — GB10 unified memory total
  "watts":               null,                 // float|null — SoC watts (~140), M6 real
  "agents_concurrent":   0,                    // int — M6 real (multiple agents flex the HW)
  "source":              "stub",               // "stub" (M4) | "nvml" (M6)
  "note":                "off-box dev stub; M6 wires real NVML/tegrastats on the GB10",
  "ts":                  "2026-08-22T16:12:00Z"
}
```

---

## Samples & offline mirror

- `bridge/samples/` — committed canned payloads (`operator_sites.json`,
  `response.json`, `transcript.json`, `telemetry.json`) so the console
  renders offline before the live bridge exists.
- `bridge/out/` — regenerated mirror (`server.py --write-out`) for the
  pull-the-cable demo. `brief.json` and `sms.json` are also written here for
  the Comms (M5) UI.

Regenerate: `.venv/bin/python bridge/server.py --write-out`
