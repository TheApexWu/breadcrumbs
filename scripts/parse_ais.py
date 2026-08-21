#!/usr/bin/env python3
"""
Parse a MarineCadastre 2024 daily GeoParquet slice into compact per-MMSI tracks
for the STRAITS console. Filters to a bbox (default: Chesapeake / Baltimore
approaches) and cargo+tanker vessel types (70-89), then downsamples each track.

Usage:
  python3 parse_ais.py IN.parquet OUT.json [--bbox latmin lonmin latmax lonmax]
                                           [--types 70-89] [--every 5] [--schema]

The daily file is GeoParquet 1.0.0: geometry is a WKB Point. Columns vary; this
script auto-detects LAT/LON columns if present, else decodes the WKB geometry.
"""
import sys, json, argparse, struct
import pyarrow.parquet as pq

# Baltimore/Patapsco + full Chesapeake approach up to the bay mouth.
DEFAULT_BBOX = (37.0, -77.1, 39.6, -75.7)  # latmin, lonmin, latmax, lonmax

def wkb_point_lonlat(b):
    """Decode a little/big-endian WKB Point -> (lon, lat). Returns None on miss."""
    if b is None or len(b) < 21:
        return None
    endian = b[0]
    fmt = "<" if endian == 1 else ">"
    gtype = struct.unpack(fmt + "I", b[1:5])[0]
    if gtype & 0xFF != 1:  # not a Point (ignore Z/M high bits)
        return None
    lon, lat = struct.unpack(fmt + "dd", b[5:21])
    return lon, lat

def find_col(names, *cands):
    low = {n.lower(): n for n in names}
    for c in cands:
        if c.lower() in low:
            return low[c.lower()]
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile"); ap.add_argument("outfile", nargs="?")
    ap.add_argument("--bbox", nargs=4, type=float, default=DEFAULT_BBOX)
    ap.add_argument("--types", default="70-89")
    ap.add_argument("--every", type=int, default=5, help="keep 1 in N points per track")
    ap.add_argument("--schema", action="store_true", help="print schema+sample and exit")
    a = ap.parse_args()

    pf = pq.ParquetFile(a.infile)
    names = pf.schema_arrow.names
    if a.schema:
        print("ROWS:", pf.metadata.num_rows)
        print("COLUMNS:")
        for f in pf.schema_arrow:
            print(f"  {f.name}: {f.type}")
        tbl = pf.read_row_group(0).slice(0, 3).to_pylist()
        print("SAMPLE:", json.dumps(tbl, default=str)[:1500])
        return

    tlo, thi = (int(x) for x in a.types.split("-"))
    latmin, lonmin, latmax, lonmax = a.bbox

    c_mmsi = find_col(names, "MMSI")
    c_time = find_col(names, "BaseDateTime", "base_date_time", "datetime", "time", "timestamp")
    c_lat  = find_col(names, "LAT", "lat", "latitude", "y")
    c_lon  = find_col(names, "LON", "lon", "longitude", "x")
    c_geom = find_col(names, "geometry", "geom")
    c_type = find_col(names, "VesselType", "vessel_type", "ShipType")
    c_name = find_col(names, "VesselName", "vessel_name", "name", "ShipName")
    c_sog  = find_col(names, "SOG", "sog", "speed")
    c_cog  = find_col(names, "COG", "cog", "course")
    c_flag = find_col(names, "Flag", "flag")

    want = [c for c in (c_mmsi, c_time, c_lat, c_lon, c_geom, c_type,
                        c_name, c_sog, c_cog, c_flag) if c]
    tracks = {}  # mmsi -> {"type","name","pts":[[t,lat,lon,sog,cog]]}
    seen_types = {}
    n_rows = 0

    for batch in pf.iter_batches(columns=want, batch_size=200_000):
        d = batch.to_pydict()
        rows = len(d[c_mmsi])
        for i in range(rows):
            n_rows += 1
            vt = d[c_type][i] if c_type else None
            try:
                vt = int(vt) if vt is not None else None
            except (TypeError, ValueError):
                vt = None
            if vt is not None:
                seen_types[vt] = seen_types.get(vt, 0) + 1
            if vt is None or not (tlo <= vt <= thi):
                continue
            if c_lat and c_lon:
                lat = d[c_lat][i]; lon = d[c_lon][i]
            elif c_geom:
                p = wkb_point_lonlat(d[c_geom][i])
                if not p:
                    continue
                lon, lat = p
            else:
                continue
            if lat is None or lon is None:
                continue
            if not (latmin <= lat <= latmax and lonmin <= lon <= lonmax):
                continue
            mmsi = d[c_mmsi][i]
            t = d[c_time][i] if c_time else None
            rec = tracks.get(mmsi)
            if rec is None:
                rec = {"type": vt,
                       "name": (d[c_name][i] if c_name else None),
                       "pts": []}
                tracks[mmsi] = rec
            rec["pts"].append([
                str(t) if t is not None else None,
                round(float(lat), 5), round(float(lon), 5),
                (round(float(d[c_sog][i]), 1) if c_sog and d[c_sog][i] is not None else None),
                (round(float(d[c_cog][i]), 1) if c_cog and d[c_cog][i] is not None else None),
            ])

    # sort each track by time, downsample
    out = {}
    for mmsi, rec in tracks.items():
        pts = sorted((p for p in rec["pts"] if p[0]), key=lambda p: p[0])
        if len(pts) < 2:
            continue
        if a.every > 1:
            kept = pts[::a.every]
            if kept[-1] is not pts[-1]:
                kept.append(pts[-1])
            pts = kept
        out[str(mmsi)] = {"type": rec["type"], "name": rec["name"], "pts": pts}

    summary = {
        "rows_scanned": n_rows,
        "cargo_tanker_vessels": len(out),
        "bbox": a.bbox, "types": a.types,
        "top_types": sorted(seen_types.items(), key=lambda kv: -kv[1])[:12],
    }
    print(json.dumps(summary, indent=2))
    if a.outfile:
        with open(a.outfile, "w") as f:
            json.dump({"meta": summary, "tracks": out}, f)
        print("wrote", a.outfile)

if __name__ == "__main__":
    main()
