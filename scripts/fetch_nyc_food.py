#!/usr/bin/env python3
"""
Fetch + cache the REAL NYC food-supply datasets for STRAITS (food theater).
All sources are free/keyless. Output goes to globe/assets/ as compact JSON so the
console runs fully offline once cached.

Layers:
  1. nyc-restaurants.json  — DOHMH inspections, latest graded+geocoded row per establishment
  2. nyc-stores.json       — NYS Retail Food Stores in the five boroughs, geocoded
  3. distributor-scorecard.json — openFDA recall history per named distributor (real risk)

Run: python3 scripts/fetch_nyc_food.py
"""
import json, urllib.request, urllib.parse, os, sys

OUT = os.path.join(os.path.dirname(__file__), "..", "globe", "assets")
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "straits-hackathon/1.0"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

# ── 1. NYC restaurants (DOHMH) ─────────────────────────────────────────────
def restaurants():
    base = "https://data.cityofnewyork.us/resource/43nn-pn8j.json"
    q = ("?$select=camis,dba,boro,cuisine_description,inspection_date,grade,"
         "critical_flag,score,latitude,longitude,street,zipcode"
         "&$where=latitude IS NOT NULL AND grade IS NOT NULL"
         "&$order=inspection_date DESC&$limit=50000")
    rows = get(base + urllib.parse.quote(q, safe="?$=&,"))
    latest = {}
    for r in rows:                       # rows are newest-first → first seen = latest
        c = r.get("camis")
        if not c or c in latest:
            continue
        try:
            lat = float(r["latitude"]); lon = float(r["longitude"])
        except (KeyError, ValueError, TypeError):
            continue
        if not (40.4 < lat < 41.0 and -74.3 < lon < -73.6):   # NYC bbox sanity
            continue
        latest[c] = {
            "id": c, "name": r.get("dba", "").strip() or "UNKNOWN",
            "boro": r.get("boro"), "cuisine": r.get("cuisine_description"),
            "grade": r.get("grade"), "score": r.get("score"),
            "critical": r.get("critical_flag"),
            "date": (r.get("inspection_date") or "")[:10],
            "lat": round(lat, 5), "lon": round(lon, 5),
        }
    out = list(latest.values())
    grades = {}
    for v in out:
        grades[v["grade"]] = grades.get(v["grade"], 0) + 1
    save("nyc-restaurants.json", {"meta": {"count": len(out), "grades": grades,
         "source": "NYC DOHMH 43nn-pn8j"}, "rows": out})
    return len(out), grades

# ── 2. NYC supermarkets / food stores (NYS Ag & Markets) ────────────────────
def stores():
    base = "https://data.ny.gov/resource/9a8c-vfzj.json"
    counties = ["NEW YORK", "KINGS", "QUEENS", "BRONX", "RICHMOND"]
    inlist = ",".join("'%s'" % c for c in counties)
    q = ("?$where=county in(%s) AND georeference IS NOT NULL&$limit=50000" % inlist)
    rows = get(base + urllib.parse.quote(q, safe="?$=&,()'"))
    out = []
    for r in rows:
        g = r.get("georeference") or {}
        coords = g.get("coordinates")
        if not coords:
            continue
        lon, lat = coords[0], coords[1]
        out.append({
            "name": (r.get("dba_name") or r.get("entity_name") or "").strip(),
            "type": r.get("estab_type"), "county": r.get("county"),
            "city": r.get("city"), "sqft": r.get("square_footage"),
            "lat": round(lat, 5), "lon": round(lon, 5),
        })
    save("nyc-stores.json", {"meta": {"count": len(out), "source": "NYS 9a8c-vfzj"}, "rows": out})
    return len(out)

# ── 3. distributor scorecard (openFDA recall history — REAL risk) ───────────
DISTRIBUTORS = ["SYSCO", "US FOODS", "PERFORMANCE FOOD", "GORDON FOOD",
                "BALDOR", "DOLE", "TAYLOR FARMS", "FRESH EXPRESS",
                "RESTAURANT DEPOT", "JETRO"]
def scorecard():
    base = "https://api.fda.gov/food/enforcement.json"
    cards = []
    for name in DISTRIBUTORS:
        term = urllib.parse.quote('recalling_firm:"%s"' % name)
        url = "%s?search=%s&sort=recall_initiation_date:desc&limit=1000" % (base, term)
        try:
            d = get(url)
        except Exception:
            cards.append({"firm": name, "recalls": 0, "class1": 0, "recent": None, "note": "no matches"})
            continue
        res = d.get("results", [])
        # client-side exact-ish filter: firm string must contain the token (openFDA is fuzzy)
        hits = [r for r in res if name.replace(" ", "") in (r.get("recalling_firm", "").upper().replace(" ", ""))]
        c1 = sum(1 for r in hits if r.get("classification") == "Class I")
        recent = hits[0] if hits else None
        cards.append({
            "firm": name, "recalls": len(hits), "class1": c1,
            "capped": len(res) >= 1000,
            "recent": (recent.get("recall_initiation_date") if recent else None),
            "recent_product": ((recent.get("product_description") or "")[:70] if recent else None),
            "recent_reason": ((recent.get("reason_for_recall") or "")[:90] if recent else None),
        })
    cards.sort(key=lambda c: -c["class1"])
    save("distributor-scorecard.json", {"meta": {"source": "openFDA food/enforcement",
         "note": "counts are client-filtered on recalling_firm; capped=hit the 1000 page limit"},
         "cards": cards})
    return cards

def save(name, obj):
    p = os.path.join(OUT, name)
    with open(p, "w") as f:
        json.dump(obj, f)
    print("  wrote %s (%d KB)" % (name, os.path.getsize(p) // 1024))

if __name__ == "__main__":
    print("1. NYC restaurants (DOHMH)…")
    n, g = restaurants(); print("   %d geocoded+graded; grades=%s" % (n, g))
    print("2. NYC food stores (NYS)…")
    print("   %d geocoded stores" % stores())
    print("3. distributor scorecard (openFDA)…")
    for c in scorecard():
        print("   %-16s recalls=%-4d classI=%-3d recent=%s%s" %
              (c["firm"], c["recalls"], c["class1"], c["recent"], " [CAPPED]" if c.get("capped") else ""))
    print("done.")
