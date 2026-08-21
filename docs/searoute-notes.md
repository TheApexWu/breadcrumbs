# searoute reroute — verified incantation (Aug 20 2026)

**Bug found in testing:** `searoute(O,D,restrictions=['suez'])` does NOT route around the Cape.
searoute-py's `restrictions` arg **replaces** its default (`['northwest']`), so blocking Suez
alone *opens the Arctic* → it returns a shorter northern route (max lat 78°). Adding just
`northwest` back escapes *east via Panama* (min lat 6.9°). Both look plausible and are WRONG.

**Correct usage — block the target AND every bypass:**
```python
sr.searoute(O, D, units="km", restrictions=['suez','panama','northwest'])
# Shanghai->Rotterdam: 25,729 km, min_lat -35.0 -> ROUNDS THE CAPE ✅ (1.31x the Suez route)
```
Restriction keys: babalmandab, bosporus, gibraltar, suez, panama, ormuz, northwest,
malacca, sunda, chili, south_africa. Default = ['northwest'] (keep it in every block-set).

**Design rule for M3/M4:** the reroute engine keeps a per-scenario BLOCK-SET. To force a
specific detour, block the chokepoint + all alternatives that would otherwise let a vessel
escape a different way. Verify a reroute by geometry (min_lat rounds the Cape), never by
"the route got longer" — a wrong route can be shorter.
