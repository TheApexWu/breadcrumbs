# BREADCRUMBS — team idea log

Suggestions that aren't in the loop's PRD yet. Not commitments — a place so nothing's lost.

## Restaurant allergen + grade lookup (teammate, Aug 22)
Query a restaurant → its DOHMH grade + critical-violation risk + allergen exposure.
- **Real / mostly done:** grade + crit_violations already in the console detail panel (M0 loads them;
  bridge serves them). A `ui-*` teammate can enrich the detail panel — no loop task needed.
- **Derived (label it):** allergen exposure = the restaurant's category/supplier allergen-recall
  history (from M0's allergen tags + the modeled supplier links).
- **Roadmap:** per-menu-item allergen precision needs menu data we don't have.
