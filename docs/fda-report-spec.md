# BREADCRUMBS — FDA-Aligned Operator Recall Report

*Compliance writer's deliverable: rationale, PDF report template (worked with the Dole F-0757-2022 anchor), SMS/Telegram short-form, and the backend field map.*

---

## 1. Why a formal, FDA-aligned format matters

A recall-response document that an operator can put in front of a health inspector, an insurer, or a plaintiff's attorney has to read like the regulatory record it is derived from — not like an app notification. Three reasons the format is load-bearing:

- **Trust / adoption.** Food-safety managers already work from FDA Enforcement Reports and 21 CFR Part 7 recall communications. Mapping BREADCRUMBS output onto those exact fields (recall number, recalling firm, classification, code/lot info, reason) means the operator recognizes it on sight and doesn't have to reconcile two vocabularies mid-incident.
- **Legal posture.** Under 21 CFR 7.49, a recall communication must let the recipient *identify the product, cease its use, and act*. A dated, on-prem-generated report showing **what the operator knew, when, and what action was directed** is contemporaneous evidence of a good-faith response — the difference between "we acted on the recall the day it posted" and "we can't show when we saw it." FSMA 204 (effective compliance Jan 20, 2026) makes lot-level traceability a legal duty for listed foods, so a lot-code-anchored exposure record is now directly on the compliance path, not a nicety.
- **Honesty as a feature.** The document separates **REAL** (openFDA recall facts, DOHMH violations, distributor recall history) from **MODELED** (the supplier→site links — which is the FSMA-204 traceability gap itself). Labeling the modeled inference *is* the compliance-grade move: it tells the operator exactly which line to verify against their own receiving records before they act.

**What this is, stated plainly:** a recall→action responder. It turns an FDA lot-coded enforcement recall into site-level action in seconds. It is **not** an outbreak detector, and its feed is **FDA-only** — USDA FSIS product (deli meat, poultry, most red meat) is outside the source and is labeled as a coverage boundary, not silently omitted.

---

## 2. PDF REPORT TEMPLATE — "Recall Exposure & Action Report"

> Worked below with the verified demo anchor **Dole F-0757-2022** (iceberg lettuce, *Listeria monocytogenes*, Class I). Fields tagged **[openFDA]** are populated verbatim from the live FDA food enforcement record at generation time; fields tagged **[BREADCRUMBS]** are computed on-box; fields tagged **[MODELED]** are inference, not source data.

---

```
┌──────────────────────────────────────────────────────────────────────┐
│  ██  CLASS I RECALL — SERIOUS HEALTH HAZARD  ██                        │
│  Reasonable probability of serious adverse health consequences or      │
│  death (21 CFR 7.3). ACT ON THIS TODAY.                                │
└──────────────────────────────────────────────────────────────────────┘
```

### RECALL EXPOSURE & ACTION REPORT

| | |
|---|---|
| **Notice ID** | BC-2026-0822-0417  `[BREADCRUMBS]` |
| **Generated** | 2026-08-22 09:14 ET — on-prem (GB10), offline  `[BREADCRUMBS]` |
| **Operator** | [Operator legal name] — 12-site NYC portfolio  `[MODELED portfolio]` |
| **Prepared for** | [Food Safety Manager / person responsible] |
| **Source event** | FDA Food Enforcement Report, recall **F-0757-2022** |
| **Exposure status** | **5 of 12 sites EXPOSED** — action required  `[BREADCRUMBS]` |

---

### A. FDA RECALL FACTS
*Mapped one-to-one to FDA food enforcement-report fields (openFDA `food/enforcement`). These are the regulatory record.*

| FDA field | Value |
|---|---|
| `recall_number` | **F-0757-2022** `[openFDA]` |
| `classification` | **Class I** `[openFDA]` |
| `recalling_firm` | Dole Fresh Vegetables, Inc. `[openFDA]` |
| `product_description` | Iceberg lettuce, packaged / bulk `[openFDA]` |
| `reason_for_recall` | Potential contamination with *Listeria monocytogenes* `[openFDA]` |
| `code_info` (lot / date codes) | [Lot codes and best-by dates as published in the enforcement record] `[openFDA]` |
| `distribution_pattern` | [States / regions of distribution] `[openFDA]` |
| `product_quantity` | [Units / cases recalled] `[openFDA]` |
| `status` | [Ongoing / Completed / Terminated] `[openFDA]` |
| `voluntary_mandated` | Voluntary: Firm Initiated `[openFDA]` |
| `recall_initiation_date` | [YYYY-MM-DD] `[openFDA]` |
| `report_date` | [YYYY-MM-DD — date FDA classified/posted] `[openFDA]` |
| `recalling_firm` location | [City, State] `[openFDA]` |

**Classification key (21 CFR 7.3):** *Class I* — reasonable probability of serious adverse health consequences or death. *Class II* — temporary or medically reversible consequences, or remote probability of serious harm. *Class III* — use not likely to cause adverse health consequences.

---

### B. EXPOSURE — which of your sites received this lot
**`[MODELED]` — supplier→site links are inferred, not sourced.** This is the FSMA-204 traceability gap: absent a shared lot-level ledger, BREADCRUMBS models which sites a recalled lot reached from the operator's supplier assignments. **Verify each row against your own receiving / invoice records before disposition.** Under FSMA 204, the authoritative answer lives in your Critical Tracking Event records (Receiving KDEs: traceability lot code, product description, quantity, date, location) — this table is the prompt to pull them.

| Site | CAMIS | Supplier link → this lot | Received (modeled) | Verify against |
|---|---|---|---|---|
| Site 03 — Midtown | 41xxxxxx | Dole → iceberg, lot in `code_info` | Yes | Receiving log / invoice |
| Site 05 — LES | 50xxxxxx | Dole → iceberg | Yes | Receiving log / invoice |
| Site 07 — Williamsburg | 41xxxxxx | Dole → iceberg | Yes | Receiving log / invoice |
| Site 09 — LIC | 50xxxxxx | Dole → iceberg | Yes | Receiving log / invoice |
| Site 11 — Harlem | 41xxxxxx | Dole → iceberg | Yes | Receiving log / invoice |

*7 of 12 sites: no modeled receipt of this lot — no action, but retain this notice.*

---

### C. RISK — how bad, per exposed site
*Two independent, REAL signals. Distributor history is openFDA firm-level recall counts; site risk is the count of CRITICAL food-handling violations from NYC DOHMH inspection records (`crit_violations`, range 0–56, citywide median 4) — the operational-hygiene metric, NOT the letter grade.*

**Distributor recall history (REAL — openFDA firm counts):**

| Firm | Class-I recall records | Read |
|---|---|---|
| **Dole** (recalling firm) | **205** | Extensive Class-I recall history |
| Fresh Express | 110 | High |
| Sysco | 24 | Moderate |
| **Jetro** (proposed swap) | **0 of 1** | Low record — verified, not "clean" |

**Exposed-site hygiene risk (REAL — DOHMH `crit_violations`):**

| Site | CAMIS | crit_violations | vs. median (4) | Handling-risk read |
|---|---|---|---|---|
| Site 05 — LES | 50xxxxxx | 14 | +10 | Elevated — prioritize hold |
| Site 11 — Harlem | 41xxxxxx | 9 | +5 | Above median |
| Site 03 — Midtown | 41xxxxxx | 6 | +2 | Slightly above |
| Site 07 — Williamsburg | 41xxxxxx | 4 | 0 | At median |
| Site 09 — LIC | 50xxxxxx | 2 | −2 | Below median |

*Site risk compounds product risk: a Class-I Listeria lot at a site with 14 critical handling violations is the operator's highest-priority hold, because cross-contamination controls there are already the weakest.*

---

### D. RECOMMENDED ACTION
*Deterministic. The numbers above are computed by MongoDB aggregation on-box, not by a model — that is why this can run offline in your back office. The local Nemotron model writes only the plain-language narration line, never the decision.*

1. **HOLD & SEGREGATE.** At all 5 exposed sites, immediately quarantine iceberg lettuce matching the F-0757-2022 lot/date codes in `code_info`. Do not use, serve, or further distribute. (21 CFR 7.49 — cease use of recalled product.) Prioritize **Site 05 (LES, 14 crit violations)** and **Site 11 (Harlem, 9)**.
2. **VERIFY.** Match on-hand lot codes to the recall's `code_info`. Pull each site's Receiving records (FSMA-204 KDEs) to confirm or clear the modeled exposure.
3. **DISPOSITION.** Destroy or return per the recalling firm's instructions in the enforcement notice; document lot, quantity, site, and date.
4. **SWAP — sourcing recommendation:** move iceberg sourcing from **Dole (205 Class-I recall records)** to **Jetro (0 of 1 record)**.
   - *Honest rationale:* Jetro's low count is a **verified low record**, not proof of a safer product — it reflects few matched openFDA recall records for that firm, which can also mean lower recall visibility. Treat this as a lower-recall-history alternative to reduce repeat exposure, and confirm Jetro's own lot-traceability before switching. This is a risk-history swap, not a safety guarantee.
5. **LOG.** This notice, timestamped, is your contemporaneous record that the recall was received and acted on.

> **Narration (local Nemotron, GB10):** *"Five of your twelve sites received Dole iceberg lettuce matching this Class I Listeria recall. Hold and segregate now, starting with your Lower East Side location, which carries the most critical handling violations. Consider shifting iceberg sourcing to Jetro, which has a far lighter recall record than Dole."*

---

### E. REAL vs. MODELED — provenance
*Every claim in this report, sourced.*

| Element | REAL / MODELED | Source |
|---|---|---|
| Recall facts (§A) | **REAL** | openFDA food enforcement — F-0757-2022 |
| Distributor recall history (§C) | **REAL** | openFDA firm-level recall counts |
| Site critical violations (§C) | **REAL** | NYC DOHMH inspection records (`crit_violations`) |
| Site identities / CAMIS | **REAL** | DOHMH-geocoded establishments |
| **Supplier → site → lot links (§B)** | **MODELED** | Operator supplier assignments — the FSMA-204 gap |
| Operator 12-site portfolio | **MODELED (illustrative)** | Demo portfolio |
| Narration sentence (§D) | Generated | Local Nemotron, on-box; decision logic is deterministic Mongo |

**Coverage boundary (stated, not hidden):** Source is **FDA food enforcement only**. USDA FSIS-regulated products — deli meats, poultry, most red meat — are **not** in this feed and will not appear here (e.g. the 2024 Boar's Head listeria recall would be invisible to this system). This report covers ~100% of FDA lot-coded enforcement recalls and does not claim outbreak detection.

---

```
────────────────────────────────────────────────────────────────────────
Source: U.S. FDA Food Enforcement Report (openFDA), recall F-0757-2022.
FDA classification per 21 CFR 7.3; recall-communication elements per
21 CFR 7.49; traceability framing per FSMA §204 Food Traceability Rule.
Generated on-prem on the operator's GB10 — supplier lists, volumes, and
site data never left the building. This document is a response record,
not a substitute for the recalling firm's official instructions.
BREADCRUMBS · Notice BC-2026-0822-0417 · 2026-08-22 09:14 ET
────────────────────────────────────────────────────────────────────────
```

---

## 3. SMS / TELEGRAM SHORT-FORM (outbox format)

Formal, plain, no hype — what / where / how bad / do this / ref. Two to four lines.

**Primary (Class I, exposed):**

```
FDA CLASS I RECALL — action needed today.
Dole iceberg lettuce (Listeria), recall F-0757-2022. 5 of your 12
sites received matching lots: Midtown, LES, Williamsburg, LIC, Harlem.
DO: hold & segregate now; verify lot codes; do not serve.
Full report + swap recommendation: BC-2026-0822-0417 (PDF).
```

**Compressed 2-line variant (SMS length):**

```
FDA CLASS I: Dole iceberg lettuce, Listeria (recall F-0757-2022).
5 of 12 sites exposed — HOLD & segregate now. Full report: BC-2026-0822-0417.
```

**All-clear variant (no exposure):**

```
FDA CLASS I recall posted: Dole iceberg lettuce, Listeria (F-0757-2022).
No modeled exposure across your 12 sites. No action; notice retained on file.
```

---

## 4. Backend field map — this is wireable, not aspirational

Every field in the template resolves to data the pipeline already holds:

1. **§A FDA facts** → `recall_number`, `classification`, `recalling_firm`, `product_description`, `reason_for_recall`, `code_info`, `distribution_pattern` — verbatim from the openFDA `food/enforcement` document already in Mongo.
2. **§B Exposure table** → `exposed_sites[]` with `{camis, name, supplier_link}`; the "5 of 12" banner is `len(exposed_sites)` over the operator portfolio.
3. **§C Site risk** → `exposed_sites[].crit_violations` (DOHMH), sorted desc to drive the hold priority order.
4. **§C Distributor history** → `distributor_risk.class1` (Dole=205) and the swap target's `distributor_risk.class1` (Jetro=0-of-1).
5. **§D Swap + narration** → `recommendation.swap_to` (Jetro) drives the sourcing line; the Nemotron call fills only the narration string, so the deterministic action survives with or without the model.

---

### Regulatory basis (cited)

- FDA recall classes I/II/III and definitions — [Recalls Background and Definitions, FDA](https://www.fda.gov/safety/industry-guidance-recalls/recalls-background-and-definitions); [FDA 101: Product Recalls](https://www.fda.gov/consumers/consumer-updates/fda-101-product-recalls); Class-I examples incl. undeclared allergens and *Listeria*/*Salmonella* in RTE foods — [LA County DPH, Food Recall Classes](http://www.publichealth.lacounty.gov/eh/safety/food-recalls/ref/recall-classes.htm).
- Enforcement-report / recall record fields (exact names) — [openFDA Food Enforcement API](https://open.fda.gov/apis/food/enforcement/) and its [searchable-fields reference](https://open.fda.gov/apis/food/enforcement/searchable-fields/); [FDA Enforcement Reports](https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/enforcement-reports).
- Recall communication required content (identify product/size/lot/code, reason & hazard, cease use, instructions, means to respond) — [21 CFR 7.49, eCFR](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-7/subpart-C/section-7.49); [Public Warning & Notification of Recalls guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/public-warning-notification-recalls-under-21-cfr-part-7-subpart-c).
- FSMA 204 CTEs (harvesting, cooling, initial packing, first land-based receiving, shipping, receiving, transformation) and KDEs (traceability lot code + product description, quantity, location, date, reference document; 24-month retention; 24-hour availability; Jan 20, 2026 compliance) — [FSMA Final Rule on Additional Traceability Records, FDA](https://www.fda.gov/food/food-safety-modernization-act-fsma/fsma-final-rule-requirements-additional-traceability-records-certain-foods).

*Uncertain / not independently verified in this build: the exact `code_info`, `distribution_pattern`, `product_quantity`, and dates for F-0757-2022 are shown as live `[openFDA]` fill-ins rather than hard-coded, because I did not re-pull that specific record here; the operator's 12-site portfolio and all supplier→site links are labeled MODELED.*