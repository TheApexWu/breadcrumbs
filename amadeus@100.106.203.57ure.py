#!/usr/bin/env python3
"""Skein AIS recorder — dumps AISStream messages for a chokepoint theater to jsonl.
Reconnects on failure; logs message count so a silent-zero is caught (AISStream #15).
Usage: capture.py --out FILE [--seconds N (0=forever)] [--bbox 'lat1,lon1,lat2,lon2']
Key from $AISSTREAM_API_KEY (source ~/.config/aisstream/key.env)."""
import asyncio, json, os, sys, time, argparse
import websockets

def parse():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="data/aisstream_suez.jsonl")
    a.add_argument("--seconds", type=int, default=0)      # 0 = forever
    a.add_argument("--bbox", default="11,32,32,44")        # Red Sea/Suez/Bab-el-Mandeb: lat1,lon1,lat2,lon2
    return a.parse_args()

async def run(args):
    key = os.environ["AISSTREAM_API_KEY"]
    la1, lo1, la2, lo2 = [float(x) for x in args.bbox.split(",")]
    sub = {"APIKey": key,
           "BoundingBoxes": [[[la1, lo1], [la2, lo2]]],
           "FilterMessageTypes": ["PositionReport", "ShipStaticData"]}
    t0 = time.time(); count = 0; static = 0; fails = 0
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    while True:
        try:
            async with websockets.connect("wss://stream.aisstream.io/v0/stream",
                                           ping_interval=20, max_size=None) as ws:
                await ws.send(json.dumps(sub))
                print(f"[{time.strftime('%H:%M:%S')}] connected, subscribed bbox={args.bbox}", flush=True); fails = 0
                with open(args.out, "a") as f:
                    async for raw in ws:
                        s = raw if isinstance(raw, str) else raw.decode()
                        f.write(s + "\n"); f.flush(); count += 1
                        if '"ShipStaticData"' in s: static += 1
                        if count % 200 == 0:
                            print(f"[{time.strftime('%H:%M:%S')}] {count} msgs ({static} static)", flush=True)
                        if args.seconds and time.time() - t0 > args.seconds:
                            print(f"DONE: {count} msgs, {static} static in {int(time.time()-t0)}s -> {args.out}", flush=True)
                            return
        except Exception as e:
            fails += 1
            is429 = "429" in str(e)
            backoff = min(120, (30 if is429 else 5) * (2 ** min(fails-1, 4)))
            print(f"[reconnect #{fails}{' 429' if is429 else ''}] {type(e).__name__}: {str(e)[:120]} -> sleep {backoff}s", flush=True)
            if args.seconds and time.time() - t0 > args.seconds: return
            await asyncio.sleep(backoff)
            continue

if __name__ == "__main__":
    asyncio.run(run(parse()))
