#!/usr/bin/env python3
"""
Build the food SOURCES + food TYPES layer for STRAITS (food theater). Two outputs:

  food-types.json  — a food-category taxonomy scored by REAL openFDA recall history
                     (which food TYPES are riskiest: leafy greens, dairy, seafood, ...)
  food-sources.json — where each category's imports come from, per-country, from UN
                     Comtrade (real trade values; partner codes resolved to names).

Both free/keyless. Comtrade preview tier returns per-partner values but strips country
names, so we resolve partnerCode via Comtrade's public partnerAreas reference.
"""
import json, urllib.request, urllib.parse, os

OUT = os.path.join(os.path.dirname(__file__), "..", "globe", "assets")
UA = {"User-Agent": "straits-hackathon/1.0"}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)

# food-type taxonomy: label -> (openFDA product_description query, HS chapter for imports)
CATS = [
    ("Leafy greens",  "lettuce OR romaine OR spinach OR kale OR greens OR salad", "07"),
    ("Other produce", "tomato OR onion OR pepper OR cucumber OR carrot OR melon OR sprouts", "07"),
    ("Fruit",         "apple OR berry OR mango OR papaya OR cantaloupe OR grape OR peach", "08"),
    ("Dairy & cheese","cheese OR milk OR cream OR yogurt OR butter OR dairy", "04"),
    ("Meat & poultry","chicken OR beef OR pork OR turkey OR poultry OR sausage OR deli", "02"),
    ("Seafood",       "shrimp OR fish OR seafood OR tuna OR salmon OR oyster OR clam OR crab", "03"),
    ("Nuts & spices", "peanut OR almond OR pistachio OR spice OR sesame OR seed", "09"),
    ("Prepared/bakery","bakery OR bread OR cake OR frozen OR snack OR sauce OR soup", "19"),
]

def food_types():
    base = "https://api.fda.gov/food/enforcement.json"
    out = []
    for label, q, hs in CATS:
        term = urllib.parse.quote("product_description:(%s)" % q)
        total = c1 = 0
        try:
            total = get("%s?search=%s&limit=1" % (base, term))["meta"]["results"]["total"]
        except Exception:
            pass
        try:
            c1 = get("%s?search=%s+AND+classification:%%22Class+I%%22&limit=1" % (base, term))["meta"]["results"]["total"]
        except Exception:
            pass
        out.append({"category": label, "hs": hs, "recalls": total, "class1": c1})
        print("  %-16s recalls=%-5d classI=%-4d" % (label, total, c1))
    out.sort(key=lambda x: -x["class1"])
    save("food-types.json", {"meta": {"source": "openFDA food/enforcement, categorized by product text"}, "cats": out})
    return out

def partner_names():
    # Comtrade public reference: partner area codes -> names
    for url in ["https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json"]:
        try:
            d = get(url)
            rows = d.get("results") or d.get("data") or d
            m = {}
            for r in (rows if isinstance(rows, list) else []):
                cid = str(r.get("id") or r.get("PartnerCode") or r.get("partnerCode"))
                txt = r.get("text") or r.get("PartnerDesc") or r.get("partnerDesc")
                if cid and txt:
                    m[cid] = txt
            if m:
                print("  partner reference: %d codes" % len(m))
                return m
        except Exception as e:
            print("  partner ref failed:", e)
    return {}

def food_sources(cats):
    names = partner_names()
    base = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
    hs_done = {}
    out = {}
    for c in cats:
        hs = c["hs"]
        if hs not in hs_done:
            url = "%s?reporterCode=842&period=2023&cmdCode=%s&flowCode=M" % (base, hs)
            try:
                rows = get(url).get("data", [])
            except Exception:
                rows = []
            parts = []
            for r in rows:
                pc = str(r.get("partnerCode"))
                nm = names.get(pc)
                v = r.get("primaryValue") or 0
                if not nm or nm == "World" or pc in ("0",) or not v:
                    continue
                parts.append({"country": nm, "value": int(v)})
            parts.sort(key=lambda x: -x["value"])
            hs_done[hs] = parts[:8]
            print("  HS%s %-14s top: %s" % (hs, c["category"], ", ".join(p["country"] for p in parts[:4]) or "none"))
        out[c["category"]] = {"hs": hs, "top_sources": hs_done[hs]}
    save("food-sources.json", {"meta": {"source": "UN Comtrade preview, US imports 2023, per partner"}, "byCategory": out})
    return out

def save(name, obj):
    p = os.path.join(OUT, name)
    json.dump(obj, open(p, "w"))
    print("  wrote %s (%d KB)" % (name, os.path.getsize(p) // 1024))

if __name__ == "__main__":
    print("food TYPES (openFDA recall risk by category)…")
    cats = food_types()
    print("food SOURCES (Comtrade imports by country)…")
    food_sources(cats)
    print("done.")
