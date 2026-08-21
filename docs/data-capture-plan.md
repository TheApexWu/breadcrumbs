# Straits — data-capture plan (verified Aug 20 2026)

Source: deep-research scout `wgbdis0fw` (105 agents, adversarially verified) + a direct searoute-py check. Provenance: **verified** against cited sources; items marked *(recalled)* need a live confirm before the day.

## The load-bearing honest gap (verified, high confidence)
**No FREE AIS source covers open ocean.** All free AIS is terrestrial VHF line-of-sight — ~15–20 nm at a 15 m antenna, 40–60 nm from tall base stations. NOAA states coverage is "unavailable > 40–50 miles from coast"; satellite AIS is paid (Spire/Kpler/exactEarth) and legally non-redistributable. **Consequence, which we lean into:** scope to ONE chokepoint theater where terrestrial receivers cluster densely; dead-reckon + LABEL mid-ocean gaps, never fake them.

## Ships — PRESENT (live capture): AISStream.io ✅
- **Endpoint:** `wss://stream.aisstream.io/v0/stream`. Free. Auth = an API key placed in the `APIKey` field of the JSON subscription, sent within 3 s of connect (not a header, not OAuth). Sign up at aisstream.io.
- **Scope:** `BoundingBoxes` (required) — overlapping boxes allowed on ONE connection ("no duplication"). Free tier = **one concurrent connection** — no parallel captures.
- **Cargo filter is CLIENT-SIDE:** there is NO server-side ship-type filter. Subscribe to `ShipStaticData` + `PositionReport`, read ship type, keep **types 70–89** (cargo/tanker) in your own code.
- **Reliability:** known issues — SSL cert expiries (#216/#231), silent zero-message delivery (#15). **Record with reconnect/retry and verify messages are actually flowing** — a silent zero looks identical to a quiet theater.
- **Offline replay:** dump the live JSON stream to a local file over the theater bbox for hours → replay from file with zero network calls.

## Ships — PAST (baseline): theater-dependent
- **Self-record (works for ANY theater):** start the AISStream dump THIS WEEK; earlier days become your "past." Strengthens the capsule story — *we* are the archive.
- **Danish DMA** — free historical AIS, zipped CSV, rolling ~2 yr, `aisdata.ais.dk` *(confirm host live)* — **Danish/Baltic only.**
- **NOAA MarineCadastre** — free zipped CSV, **US EEZ only, 145–165 day lag.**
- **BarentsWatch/Kystverket** — Norwegian only.
> National feeds do NOT cover Suez/Malacca. For an iconic theater, the past = self-recorded.

## Air-freight — PRESENT: OpenSky ✅
- `/states/all`, **OAuth2 client-credentials only** (basic auth removed ~Mar 18 2026 — old tutorials are dead). Create an API client for `client_id`/`client_secret`; tokens from `auth.opensky-network.org` expire in 30 min — **refresh during a multi-hour record.**
- Quotas: anonymous 400 credits/day (latest state, 10 s res); **authenticated 4,000/day** (up to 1 h back, 5 s res); feeder 8,000.
- **Freighter separation = callsign/operator prefix** (FDX, UPS, GTI, CLX, …). The aircraft category field is weight-class only, not cargo-vs-passenger.

## Reroute sim — searoute-py ✅ (verified, native)
- `searoute(origin, dest, restrictions=[...])` where restrictions ∈ `{suez, panama, malacca, ormuz, babalmandab, bosporus, gibraltar, sunda, northwest, chili, south_africa}`. Returns geojson **waypoints + transit hours** (given speed). **"Close Suez → Cape reroute" is one argument** — no graph surgery. (Library is for *realistic-looking* routes, not real navigation — matches the refuse-to-oracle ethos.)

## Reference + metadata
- **Chokepoint coords:** hardcode (Suez ≈30.0 N 32.5 E, Bab-el-Mandeb ≈12.6 N 43.4 E, Hormuz ≈26.6 N 56.3 E, Malacca ≈2.5 N 101.3 E, Panama ≈9.1 N 79.7 W). *(recalled — trivial to confirm.)*
- **Vessel metadata:** AIS `ShipStaticData` gives type/name/dimensions live — sufficient for the MVP. Deadweight/flag enrichment (ITU/registries) = out of scope.
- **Volume:** DMA's ~10 M records / ~2 GB per day is ALL Danish traffic — a loose upper bound. One chokepoint bbox over a few hours is far smaller (hundreds–thousands of cargo vessels, a few hundred MB). Fits the box easily.

## The plan (executable this week)
1. **Theater = Suez + Bab-el-Mandeb** (iconic, searoute-native, the Ever-Given everyone remembers).
2. **Start the AISStream capture NOW** on the Mini (always-on, detached) → accumulate the PAST baseline by Saturday.
3. Record a fresh PRESENT window pre-event; snapshot OpenSky freighters over the same bbox.
4. Seal to `data/theater.parquet` (provenance-stamped) → replay fully offline.
