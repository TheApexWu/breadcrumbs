#!/usr/bin/env python3
"""BREADCRUMBS local relay — the box's I/O seam.
  POST /alert {text}          -> Telegram sendMessage (the outbox; the only thing that leaves the box)
  POST /ask   {question,context} -> local Nemotron (vLLM), grounded, <think> stripped (the on-box brain)
Reads TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID from ~/.config/breadcrumbs/telegram.env.
vLLM endpoint from BC_VLLM_URL (default http://localhost:8000/v1 — the GB10 itself; set the tailscale URL for off-box)."""
import json, os, re, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

ENV = os.path.expanduser("~/.config/breadcrumbs/telegram.env")
VLLM = os.environ.get("BC_VLLM_URL", "http://localhost:8000/v1")
MODEL = os.environ.get("BC_MODEL", "nvidia/Llama-3.1-Nemotron-Nano-4B-v1.1")

def _cfg():
    c = {}
    try:
        for ln in open(ENV):
            if "=" in ln and not ln.strip().startswith("#"):
                k, v = ln.strip().split("=", 1); c[k] = v
    except OSError: pass
    return c

def _send(text):
    c = _cfg(); tok = c.get("TELEGRAM_BOT_TOKEN"); cid = c.get("TELEGRAM_CHAT_ID")
    if not tok or not cid: return {"ok": False, "error": "token/chat_id unconfigured"}
    body = json.dumps({"chat_id": cid, "text": text, "disable_web_page_preview": True}).encode()
    req = urllib.request.Request("https://api.telegram.org/bot%s/sendMessage" % tok,
                                 data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.load(r); return {"ok": d.get("ok"), "message_id": d.get("result", {}).get("message_id")}

def _ask(question, context):
    """Grounded local inference. The model answers ONLY from the facts we pass (RAG over
    deterministic Mongo output) — it never invents numbers. <think> chain-of-thought stripped."""
    sysmsg = ("detailed thinking off. You are BREADCRUMBS, an on-prem food-safety agent. "
              "Answer the operator ONLY from the FACTS provided, in 1-3 plain sentences. "
              "Do not invent numbers or firms. If the facts don't cover it, say so.")
    user = "FACTS:\n%s\n\nQUESTION: %s" % (context or "(none)", question)
    body = json.dumps({"model": MODEL, "temperature": 0.2, "max_tokens": 200,
                       "messages": [{"role": "system", "content": sysmsg},
                                    {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(VLLM.rstrip("/") + "/chat/completions",
                                 data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        d = json.load(r)
    txt = d["choices"][0]["message"]["content"]
    txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.S).strip()
    return {"ok": True, "answer": txt, "model": MODEL, "local": True}

class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try: b = json.loads(raw or b"{}") or {}
        except ValueError: b = {}
        try:
            if self.path.rstrip("/").endswith("ask"):
                out = _ask(b.get("question", ""), b.get("context", ""))
            else:
                out = _send(b.get("text") or "BREADCRUMBS alert (no body supplied).")
        except Exception as e:
            out = {"ok": False, "error": "%s: %s" % (type(e).__name__, e)}
        self.send_response(200 if out.get("ok") else 502); self._cors()
        self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps(out).encode())
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(os.environ.get("BC_RELAY_PORT", "8899"))
    print("[bc-relay] :%d  ->  Telegram(/alert) + local Nemotron %s (/ask)" % (port, VLLM))
    HTTPServer(("127.0.0.1", port), H).serve_forever()
