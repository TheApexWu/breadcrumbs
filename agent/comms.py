#!/usr/bin/env python3
"""
PRD M5 — the Comms action. Two channels, picked by the operator alert-preference
profile (M1):

  PRIMARY  = Telegram Bot API. A real message lands on a real phone. Sending
             is I/O, not inference — does not violate the local-inference rule.
             The bot token + chat_id are read from env/config ONLY (never
             committed; PRD hard rule + V3 grep assertion).
  FALLBACK = mock phone UI. Fully offline, ZERO network calls — for the
             pull-the-cable moment or flaky venue wifi. Renders the alert
             payload to bridge/out/alert.json (a static file the human-built
             console reads from the local filesystem, no HTTP).

The alert text is GROUNDED in the M2 Response: real product name, exposed-site
count, compounding count, swap target. No invented numbers (instrument-not-oracle).
"""
import json
import os
import sys

import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

TELEGRAM_BASE = "https://api.telegram.org"

# env keys — the ONLY place the token is read. Never committed.
ENV_TOKEN = "TELEGRAM_BOT_TOKEN"
ENV_CHAT = "TELEGRAM_CHAT_ID"
ENV_BASE = "TELEGRAM_BASE_URL"  # optional override (test/local relay)


class TelegramAdapter:
    """Send text to a Telegram chat via the Bot API sendMessage.

    Token + chat_id come from env (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID) or
    ctor args (tests pass a fake token + point base_url at a local relay).
    Never raises on missing creds — cleanly skips and reports `reason`.
    """

    def __init__(self, token=None, chat_id=None, base_url=None):
        self.token = token if token is not None else os.environ.get(ENV_TOKEN)
        self.chat_id = chat_id if chat_id is not None else os.environ.get(ENV_CHAT)
        self.base_url = (
            base_url
            or os.environ.get(ENV_BASE)
            or TELEGRAM_BASE
        ).rstrip("/")

    def configured(self):
        return bool(self.token and self.chat_id)

    def send(self, text, chat_id=None):
        """POST /bot<token>/sendMessage with {chat_id, text}. Returns a result
        dict: {ok, skipped, status_code, response, network_calls}."""
        if not self.token:
            return {"ok": False, "skipped": True, "reason": "no token",
                    "network_calls": 0}
        cid = chat_id if chat_id is not None else self.chat_id
        if not cid:
            return {"ok": False, "skipped": True, "reason": "no chat_id",
                    "network_calls": 0}
        url = "%s/bot%s/sendMessage" % (self.base_url, self.token)
        try:
            r = requests.post(url, json={"chat_id": cid, "text": text}, timeout=15)
        except requests.RequestException as e:
            return {"ok": False, "skipped": False, "reason": "network error: %s" % e,
                    "network_calls": 1}
        try:
            data = r.json()
        except ValueError:
            data = {"raw": r.text}
        return {"ok": bool(data.get("ok", False)), "skipped": False,
                "status_code": r.status_code, "response": data,
                "network_calls": 1}


def mock_phone_render(alert_payload, out_dir=None):
    """Render the alert to a static JSON file the console reads offline.
    ZERO network calls — the mock phone's whole point (pull-the-cable safe)."""
    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(__file__), "..", "bridge", "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "alert.json")
    with open(path, "w") as f:
        json.dump(alert_payload, f, indent=2, default=str, sort_keys=True)
    return {"ok": True, "skipped": False, "channel": "mock-phone",
            "path": path, "network_calls": 0}


def build_alert(response, brief, sms_payload):
    """The alert payload, GROUNDED in the M2 Response. Every number traced to a
    Response field; the real product name comes from openFDA text."""
    r = response["recall"]
    return {
        "recall_number": r.get("recall_number"),
        "recalling_firm": r.get("recalling_firm"),
        "product_description": r.get("product_description"),
        "classification": r.get("classification"),
        "reason_for_recall": r.get("reason_for_recall"),
        "exposed_count": response["exposed_count"],
        "compounding_count": response["compounding_count"],
        "swap_to": brief.get("swap_to"),
        "sms": sms_payload.get("sms"),
        "hold_notice": sms_payload.get("hold_notice"),
        "class": "grounded",
        "grounded_in": "M2 Response (sim.respond)",
    }


def send_alert(response, brief, sms_payload, profile=None, adapter=None,
                out_dir=None):
    """Pick the channel from the operator alert-preference profile (M1) and
    dispatch. PRIMARY=telegram (real send); FALLBACK=mock phone (offline).
    On any Telegram failure or missing creds, falls back to mock phone so the
    alert always lands somewhere. Returns a result dict with the channel used."""
    profile = profile or {}
    channel = profile.get("channel", "telegram")
    alert = build_alert(response, brief, sms_payload)
    result = {"channel_attempted": channel, "alert": alert, "ok": False}

    if channel == "telegram":
        adapter = adapter if adapter is not None else TelegramAdapter()
        if adapter.configured():
            send_res = adapter.send(alert["sms"])
            result["telegram"] = send_res
            if send_res.get("ok"):
                result["sent_via"] = "telegram"
                result["ok"] = True
                return result
            result["fallback_reason"] = "telegram send failed: %s" % send_res.get("reason", send_res.get("status_code"))
        else:
            result["fallback_reason"] = "telegram unconfigured (no token/chat_id)"
    else:
        result["fallback_reason"] = "profile.channel=%s -> mock phone" % channel

    # FALLBACK: mock phone (offline, zero network)
    mock = mock_phone_render(alert, out_dir)
    result["mock_phone"] = mock
    result["sent_via"] = "mock-phone"
    result["ok"] = mock["ok"]
    return result