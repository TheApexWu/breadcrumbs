#!/usr/bin/env python3
"""
PRD M0 — one-time cache of the REAL openFDA food/enforcement corpus + the DOHMH
critical-violation count per establishment. Output: data/recalls.json and
data/crit-violations.json (loop-owned cache; globe/assets is human-owned).

openFDA food/enforcement is paginated with a hard skip cap of 25000 per query,
so we slice by classification (each class < 25000) and concatenate. This yields
the full corpus (Class I + II + III), which lets us DERIVE allergen tags from the
real reason_for_recall text rather than fetching only allergen hits.
"""
import json, os, time, urllib.parse, urllib.request

OUT = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "breadcrumbs-hackathon/1.0"}
BASE = "https://api.fda.gov/food/enforcement.json"
FETCH_AT = "2026-08-22"


def get(url, retries=4):
    for i in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(1.5 * (i + 1))


def fetch_class(cls):
    term = urllib.parse.quote('classification:"%s"' % cls)
    out, skip = [], 0
    while True:
        url = "%s?search=%s&limit=1000&skip=%d" % (BASE, term, skip)
        d = get(url)
        res = d.get("results", []) or []
        if not res:
            break
        out.extend(res)
        total = d["meta"]["results"]["total"]
        skip += len(res)
        print("    %s: %d/%d" % (cls, len(out), total))
        if len(res) < 1000 or skip >= total:
            break
        time.sleep(0.1)
    return out


def recalls():
    all_rows = []
    for cls in ("Class I", "Class II", "Class III"):
        all_rows.extend(fetch_class(cls))
    # dedupe by recall_number (openFDA can overlap across paginated slices)
    seen, dedup = set(), []
    for r in all_rows:
        rn = r.get("recall_number")
        if rn and rn not in seen:
            seen.add(rn)
            dedup.append(r)
    p = os.path.join(OUT, "recalls.json")
    with open(p, "w") as f:
        json.dump({"meta": {"source": "openFDA food/enforcement",
                            "fetched_at": FETCH_AT,
                            "count": len(dedup),
                            "note": "full corpus via classification slices (Class I+II+III)"},
                   "results": dedup}, f)
    print("  wrote recalls.json (%d recalls, %d KB)" % (len(dedup), os.path.getsize(p) // 1024))
    return len(dedup)


def crit_violations():
    # DOHMH 43nn-pn8j: count critical_flag='Critical' rows per camis.
    base = "https://data.cityofnewyork.us/resource/43nn-pn8j.json"
    q = ("$select=camis,count(*) as crit_count"
         "&$where=critical_flag='Critical' AND latitude IS NOT NULL"
         "&$group=camis&$limit=50000")
    rows = get(base + "?" + urllib.parse.quote(q, safe="?$=&,()'"))
    counts = {r["camis"]: int(r["crit_count"]) for r in rows if r.get("camis")}
    p = os.path.join(OUT, "crit-violations.json")
    with open(p, "w") as f:
        json.dump({"meta": {"source": "NYC DOHMH 43nn-pn8j, critical_flag='Critical'",
                            "fetched_at": FETCH_AT,
                            "camis_with_critical": len(counts)},
                   "counts": counts}, f)
    print("  wrote crit-violations.json (%d camis, %d KB)" %
          (len(counts), os.path.getsize(p) // 1024))
    return len(counts)


if __name__ == "__main__":
    print("1. openFDA food enforcement corpus…")
    recalls()
    print("2. DOHMH critical-violation counts per camis…")
    crit_violations()
    print("done.")
