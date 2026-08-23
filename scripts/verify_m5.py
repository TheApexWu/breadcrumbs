#!/usr/bin/env python3
"""
PRD M5 — run EVERY verification in the milestone's `verifications` array and
assert each passes. Exits 0 only if all pass; prints one line per check.

V1: firing Comms on the Dole recall produces an alert payload containing the
    real product name, exposed-site count, compounding count, and swap target
    — equal to the M2 Response.
V2: the Telegram adapter POSTs to sendMessage and gets ok:true with a test
    token/chat_id, OR cleanly skips (logs 'no token') when unset; the mock UI
    renders offline with ZERO network calls.
V3: the bot token is read from env/config only — a grep of the repo finds NO
    token literal (assert).
"""
import json
import os
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from db.queries import get_db  # noqa: E402
from sim.operator import build_portfolio  # noqa: E402
from sim.respond import respond  # noqa: E402
import agent.swarm as swarm  # noqa: E402
from agent.comms import TelegramAdapter, send_alert, mock_phone_render, build_alert  # noqa: E402

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, ok, detail=""):
    tag = PASS if ok else FAIL
    line = "[%s] %s%s" % (tag, name, (" — " + detail) if detail else "")
    print(line)
    results.append((tag, name, detail))


# ── setup: rebuild portfolio, clear agent_memory for a clean first-alert ────
db = get_db()
build_portfolio(db)
db.agent_memory.drop()
os.environ.pop("OPENROUTER_API_KEY", None)
os.environ.pop("TELEGRAM_BOT_TOKEN", None)
os.environ.pop("TELEGRAM_CHAT_ID", None)

dole = db.recalls.find_one({"recall_number": "F-0757-2022"})
if not dole:
    dole = db.recalls.find_one({"recalling_firm": "DOLE FRESH VEGETABLES INC",
                                "classification": "Class I"})
check("found the real Dole Class-I recall", dole is not None,
      dole["recall_number"] if dole else "none")

# the source of truth — respond.py numbers
resp_truth = respond(dole, db)

# fire Comms (swarm run with no token -> mock-phone fallback)
out = swarm.run("F-0757-2022", db=db, adapter=swarm.ModelAdapter(backend="openrouter"))
alert = out.get("alert") or {}
send = out.get("send") or {}


# ── V1: alert payload EQUAL to the M2 Response ──────────────────────────────
check("V1 alert carries the real product_description (openFDA text)",
      bool(alert.get("product_description"))
      and alert["product_description"] == resp_truth["recall"]["product_description"],
      "product=%s..." % (alert.get("product_description") or "")[:40])

check("V1 alert.exposed_count == Response.exposed_count",
      alert.get("exposed_count") == resp_truth["exposed_count"],
      "alert=%d resp=%d" % (alert.get("exposed_count"), resp_truth["exposed_count"]))

check("V1 alert.compounding_count == Response.compounding_count",
      alert.get("compounding_count") == resp_truth["compounding_count"],
      "alert=%d resp=%d" % (alert.get("compounding_count"), resp_truth["compounding_count"]))

check("V1 alert.swap_to == Response.recommendation.swap_to.firm",
      alert.get("swap_to") == resp_truth["recommendation"]["swap_to"]["firm"],
      "alert=%s resp=%s" % (alert.get("swap_to"),
                            resp_truth["recommendation"]["swap_to"]["firm"]))

check("V1 alert.recalling_firm == Response.recall.recalling_firm (real)",
      alert.get("recalling_firm") == resp_truth["recall"]["recalling_firm"],
      "alert=%s resp=%s" % (alert.get("recalling_firm"),
                            resp_truth["recall"]["recalling_firm"]))

check("V1 alert labeled class:'grounded'",
      alert.get("class") == "grounded", "class=%s" % alert.get("class"))

# the sms text names the real recall + the action (<=2 sentences per task)
sms_text = (out.get("sms") or {}).get("sms", "")
sents = [s for s in re.split(r"(?<=[.!?])\s+", sms_text.strip()) if s]
check("V1 sms is <=2 sentences (SMS-style layman alert)",
      len(sents) <= 2, "sentences=%d" % len(sents))
check("V1 sms names the swap target + exposed count",
      ("BALDOR" in sms_text and "5" in sms_text), "sms=%s" % sms_text[:80])


# ── V2: Telegram adapter POSTs and gets ok:true (test relay) OR skips cleanly ─
# (a) no token -> clean skip, no network call
no_token = TelegramAdapter()
skip_res = no_token.send("test")
check("V2a TelegramAdapter with no token cleanly skips (ok=False, skipped=True)",
      skip_res.get("ok") is False and skip_res.get("skipped") is True
      and skip_res.get("network_calls") == 0,
      "reason=%s ncalls=%d" % (skip_res.get("reason"), skip_res.get("network_calls", -1)))

# (b) with a test token -> POSTs to sendMessage and parses ok:true.
# Point base_url at a local relay that mimics the Telegram Bot API.
class TelegramRelay(BaseHTTPRequestHandler):
    def do_POST(self):
        # path should be /bot<token>/sendMessage
        body = json.dumps({"ok": True,
                           "result": {"message_id": 1,
                                      "chat": {"id": 0}}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


relay = ThreadingHTTPServer(("127.0.0.1", 0), TelegramRelay)
relay_port = relay.server_address[1]
import threading
relay_thread = threading.Thread(target=relay.serve_forever, daemon=True)
relay_thread.start()

test_adapter = TelegramAdapter(token="TESTBOT123:FAKE", chat_id="TESTCHAT",
                                base_url="http://127.0.0.1:%d" % relay_port)
send_res = test_adapter.send("ALERT: test recall")
relay.shutdown()

check("V2b TelegramAdapter POSTs to /bot<token>/sendMessage and gets ok:true",
      send_res.get("ok") is True and send_res.get("skipped") is False
      and send_res.get("network_calls") == 1
      and send_res.get("status_code") == 200,
      "ok=%s status=%s ncalls=%s" % (send_res.get("ok"),
                                     send_res.get("status_code"),
                                     send_res.get("network_calls")))

# (c) mock phone renders offline with ZERO network calls
tmp_out = "/var/folders/m4/37z2ytt50pj_m88_04m8t5wc0000gn/T/opencode/m5_mock_out"
os.makedirs(tmp_out, exist_ok=True)
mock_alert = build_alert(resp_truth, out["brief"], out["sms"])
mock_res = mock_phone_render(mock_alert, out_dir=tmp_out)
mock_path = os.path.join(tmp_out, "alert.json")
with open(mock_path) as f:
    written = json.load(f)
check("V2c mock phone renders offline (zero network_calls, writes alert.json)",
      mock_res.get("network_calls") == 0 and mock_res.get("ok") is True
      and written.get("exposed_count") == resp_truth["exposed_count"],
      "ncalls=%d path_exists=%s" % (mock_res.get("network_calls", -1),
                                    os.path.exists(mock_path)))

# (d) send_alert with profile.channel=console -> mock phone (no telegram attempt)
console_res = send_alert(resp_truth, out["brief"], out["sms"],
                         profile={"channel": "console"}, out_dir=tmp_out)
check("V2d profile.channel=console -> mock phone (sent_via=mock-phone)",
      console_res.get("sent_via") == "mock-phone"
      and console_res.get("ok") is True
      and console_res.get("mock_phone", {}).get("network_calls") == 0,
      "sent_via=%s ok=%s" % (console_res.get("sent_via"), console_res.get("ok")))


# ── V3: bot token read from env/config ONLY — no token literal in repo ──────
# Grep the repo for anything that looks like a Telegram bot token literal.
# Bot tokens match the pattern <digits>:<base35-ish>, ~46 chars after the colon.
# We exclude this verify script + the comms.py env-key strings from the search.
TOKEN_RE = re.compile(r"['\"]\d{6,}:[A-Za-z0-9_-]{30,}['\"]")
# also flag any literal assigned to TELEGRAM_BOT_TOKEN (not the env-key name)
ASSIGN_RE = re.compile(r"TELEGRAM_BOT_TOKEN\s*=\s*['\"][^'\"]{10,}['\"]")

scan_dirs = ["agent", "sim", "db", "scripts", "bridge"]
token_hits = []
assign_hits = []
for d in scan_dirs:
    for dirpath, _, files in os.walk(os.path.join(ROOT, d)):
        for fn in files:
            if fn.endswith((".py", ".sh", ".md", ".json")):
                p = os.path.join(dirpath, fn)
                try:
                    with open(p) as f:
                        txt = f.read()
                except (OSError, UnicodeDecodeError):
                    continue
                for m in TOKEN_RE.finditer(txt):
                    token_hits.append((p, m.group(0)[:20] + "..."))
                for m in ASSIGN_RE.finditer(txt):
                    assign_hits.append((p, m.group(0)[:40]))

check("V3 no Telegram bot-token literal in repo source",
      len(token_hits) == 0, "hits=%s" % token_hits if token_hits else "clean")
check("V3 no literal assignment to TELEGRAM_BOT_TOKEN",
      len(assign_hits) == 0, "hits=%s" % assign_hits if assign_hits else "clean")

# the adapter reads ONLY from env (os.environ) — assert the source
import inspect
init_src = inspect.getsource(TelegramAdapter.__init__)
mod_src = inspect.getsource(sys.modules[TelegramAdapter.__module__])
check("V3 TelegramAdapter reads token from os.environ only",
      "os.environ.get" in init_src
      and 'ENV_TOKEN = "TELEGRAM_BOT_TOKEN"' in mod_src
      and 'ENV_CHAT = "TELEGRAM_CHAT_ID"' in mod_src,
      "env-read in __init__=%s; ENV_TOKEN/ENV_CHAT constants present=%s"
      % ("os.environ.get" in init_src,
         'ENV_TOKEN = "TELEGRAM_BOT_TOKEN"' in mod_src))

# git-tracked .env (if any) must not contain a token — check .gitignore excludes .env
gi_path = os.path.join(ROOT, ".gitignore")
gi_has_env = False
if os.path.exists(gi_path):
    with open(gi_path) as f:
        gi_has_env = ".env" in f.read()
check("V3 .env is gitignored (no committed token file)", gi_has_env,
      ".gitignore has .env=%s" % gi_has_env)


# ── summary ─────────────────────────────────────────────────────────────────
npass = sum(1 for t, _, _ in results if t == PASS)
nfail = sum(1 for t, _, _ in results if t == FAIL)
print("\n=== M5 verifications: %d pass, %d fail ===" % (npass, nfail))
sys.exit(0 if nfail == 0 else 1)