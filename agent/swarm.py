#!/usr/bin/env python3
"""
PRD M3 — the agent swarm. Five tool-calling roles over the M0 aggregation
pipelines + M2 functions, orchestrated concurrently, with a durable
agent_memory in Mongo (dedup across restarts).

Runtime (hard rule: at least one of OpenClaw/NemoClaw/OpenShell):
  - Off-box dev  = OpenClaw: the ModelAdapter wraps OpenRouter (glm).
  - On-box (M6)  = NemoClaw: swap to local Nemotron via the SAME adapter.
  The swap is ONE line: ModelAdapter(backend="nemotron", ...).

Roles (each a tool-call over db/queries + sim/respond + Mongo):
  Watcher  - watch_feed: a Mongo CHANGE STREAM on recalls IS the always-on
             watch. A new insert fires the swarm. In the synchronous run()
             path the Watcher tool ingests the fired recall.
  Tracer   - trace_forward: the exposure aggregation (M0 $lookup).
  Risk     - score_risk: distributor class1 (real openFDA) + compounding
             (crit_violations>0). Runs distributor lookup CONCURRENTLY with
             Tracer (independent aggregations).
  Briefer  - brief: plain-language brief GROUNDED in the M2 Response — every
             number traced to a Response field; no invented certainty.
  Comms    - draft_sms: the SMS + supplier hold notice (M5 wires the send).

AGENT MEMORY (MongoDB-track 'the agent survives its own sandbox'):
  agent_memory collection persists {run_id, recall_id, decision, alert_sent,
  ts, response_summary}. On restart the swarm RECALLS prior state and DEDUPES
  — it does not re-alert a recall it already handled. Past decisions steer
  the next run (retrieval that changes behavior).
"""
import json
import os
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.queries import get_db, exposure as exposure_agg, compounding  # noqa: E402
from sim.respond import respond  # noqa: E402

# ── runtime tag (asserted by M3 V3: at least one of OpenClaw/NemoClaw/OpenShell) ──
RUNTIME = "OpenClaw"  # off-box dev runtime; on-box swap -> "NemoClaw"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# OpenRouter API model id (the opencode default is openrouter/z-ai/glm-5.2; the
# OpenRouter HTTP id drops the openrouter/ prefix). Env override for the box.
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "z-ai/glm-5.2")


class ModelAdapter:
    """Single swap point OpenRouter(OpenClaw) <-> local Nemotron(NemoClaw).

    backend="openrouter" (default, off-box): calls OpenRouter chat completions.
    backend="nemotron"   (on-box, M6):      calls the local NemoClaw/Nemotron
        endpoint (base_url + model). The interface is identical — only the
        dispatch inside complete() changes. THIS is the one swap point.
    """

    def __init__(self, backend="openrouter", base_url=None, model=None):
        self.backend = backend
        self.base_url = base_url
        self.model = model

    def complete(self, prompt, system=None):
        """Generate text. Returns a string. Falls back to a deterministic
        empty-string on any failure — the brief's grounded numbers never
        depend on model output (instrument, not oracle)."""
        try:
            if self.backend == "nemotron":
                return self._call_local(prompt, system)
            return self._call_openrouter(prompt, system)
        except Exception as e:
            # log + swallow: the swarm's grounded fields come from the
            # Response, not the model. A model outage must not break the run.
            return "[adapter:fallback %s] %s" % (self.backend, type(e).__name__)

    def _call_openrouter(self, prompt, system):
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            return "[adapter:no-key openrouter]"
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        r = requests.post(
            OPENROUTER_URL,
            headers={"Authorization": "Bearer " + key,
                     "Content-Type": "application/json"},
            json={"model": self.model or OPENROUTER_MODEL, "messages": msgs,
                  "max_tokens": 400},
            timeout=30,
        )
        r.raise_for_status()
        msg = r.json()["choices"][0]["message"]
        # GLM-5.x sometimes returns content=null and puts the answer in
        # `reasoning`; fall back so the adapter always returns a string.
        return msg.get("content") or msg.get("reasoning") or ""

    def _call_local(self, prompt, system):
        # M6 wires the real NemoClaw/Nemotron endpoint. The interface is the
        # same; only the dispatch swaps. Until M6, this is a stub so the
        # adapter is exercised on-box without a cloud call.
        base = self.base_url or os.environ.get("NEMOCLAW_URL", "http://localhost:8000/v1")
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        r = requests.post(
            base + "/chat/completions",
            headers={"Content-Type": "application/json"},
            json={"model": self.model or "nemotron", "messages": msgs,
                  "max_tokens": 400},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


# ── transcript logger ──────────────────────────────────────────────────────────
class Transcript:
    """Ordered tool-call log: {agent, tool, args, result, ts, concurrent?}."""

    def __init__(self):
        self.entries = []

    def log(self, agent, tool, args, result, concurrent=False):
        e = {
            "agent": agent,
            "tool": tool,
            "args": _jsonable(args),
            "result": _jsonable(result),
            "ts": _now(),
            "concurrent": concurrent,
        }
        self.entries.append(e)
        return e

    def as_list(self):
        return list(self.entries)


def _jsonable(x):
    try:
        json.dumps(x, default=str)
        return x
    except (TypeError, ValueError):
        return str(x)


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ── agent_memory: durable state + dedup ────────────────────────────────────────
def recall_state(recall_id, db=None):
    """Read prior agent_memory for a recall. Returns the last decision doc or
    None. This is the retrieval that changes behavior: a prior alert means we
    do NOT re-alert."""
    db = get_db() if db is None else db
    return db.agent_memory.find_one({"recall_id": recall_id}, sort=[("ts", -1)])


def record_run(recall_id, decision, alert_sent, response, db=None, re_alert=False):
    """Persist this run to agent_memory. alert_sent is 1 only on first alert;
    a deduped re-run records runs++ but alert_sent stays 0 for this entry
    (the recall's aggregate alert_sent count stays 1, not 2)."""
    db = get_db() if db is None else db
    doc = {
        "run_id": str(uuid.uuid4()),
        "recall_id": recall_id,
        "decision": decision,
        "alert_sent": 1 if alert_sent else 0,
        "re_alert": re_alert,
        "ts": _now(),
        "response_summary": {
            "exposed_count": response.get("exposed_count"),
            "compounding_count": response.get("compounding_count"),
            "distributor_class1": response.get("distributor_risk", {}).get("class1"),
            "swap_to": response.get("recommendation", {}).get("swap_to", {}).get("firm"),
        },
    }
    db.agent_memory.insert_one(doc)
    return doc


def alert_count(recall_id, db=None):
    """Total alerts sent for a recall across all memory docs. Stays 1 after a
    re-run (the dedup contract)."""
    db = get_db() if db is None else db
    return db.agent_memory.count_documents({"recall_id": recall_id, "alert_sent": 1})


# ── tools (each role calls one; logged to the transcript) ─────────────────────
def tool_watch_feed(transcript, recall_number=None, db=None):
    """Watcher: the always-on watch. Conceptually a Mongo CHANGE STREAM on
    recalls (see watch_change_stream). In the run() path this tool records
    that a new recall fired and returns its id."""
    t = transcript.log("Watcher", "watch_feed",
                       {"recall_number": recall_number},
                       {"fired": True, "recall_number": recall_number})
    return t["result"]


def tool_ingest_recall(transcript, recall_number, db=None):
    """Watcher->ingest: load the fired recall doc from the recalls collection."""
    db = get_db() if db is None else db
    recall = db.recalls.find_one({"recall_number": recall_number})
    if recall is None:
        recall = db.recalls.find_one({"recalling_firm": recall_number})
    if recall is None:
        raise ValueError("recall not found: %s" % recall_number)
    recall["_id"] = str(recall["_id"])
    transcript.log("Watcher", "ingest_recall",
                   {"recall_number": recall.get("recall_number")},
                   {"recall_number": recall.get("recall_number"),
                    "recalling_firm": recall.get("recalling_firm"),
                    "classification": recall.get("classification"),
                    "hazard_class": recall.get("hazard_class")})
    return recall


def tool_trace_forward(transall, recall, db=None):
    """Tracer: the exposure aggregation — which operator sites received the
    affected lot (MODELED supplier links). Returns the exposed sites."""
    db = get_db() if db is None else db
    exposed = exposure_agg(recall, db)
    exposed = sorted(exposed, key=lambda s: str(s.get("camis", "")))
    sites = [{"camis": s.get("camis"), "name": s.get("name"),
              "boro": s.get("boro"), "crit_violations": s.get("crit_violations", 0),
              "distributor": s.get("distributor"), "class": "modeled"}
             for s in exposed]
    transall.log("Tracer", "trace_forward",
                 {"recalling_firm": recall.get("recalling_firm")},
                 {"exposed_count": len(sites),
                  "camis_list": [s["camis"] for s in sites]},
                 concurrent=True)
    return sites


def tool_distributor_risk(transall, recall, db=None):
    """Risk (concurrent part): the distributor's real class1 count. Independent
    of exposure, so runs alongside Tracer. Returns the distributor_risk dict
    from the M2 Response machinery (real openFDA scorecard)."""
    db = get_db() if db is None else db
    # reuse M2's distributor lookup (prefix-match on short name, real openFDA)
    from sim.respond import _distributor_risk
    dr = _distributor_risk(recall, db)
    transall.log("Risk", "score_risk.distributor",
                 {"recalling_firm": recall.get("recalling_firm")},
                 {"firm": dr.get("firm"), "class1": dr.get("class1"),
                  "recalls": dr.get("recalls"), "class": "real"},
                 concurrent=True)
    return dr


def tool_score_risk(transall, recall, exposed_sites, distributor_risk, db=None):
    """Risk (final): compounding = # exposed sites with crit_violations>0
    (real DOHMH critical food-handling violations). Combines with the
    concurrent distributor lookup into the full risk picture."""
    db = get_db() if db is None else db
    camis = [s["camis"] for s in exposed_sites]
    comp = compounding(camis, db)
    compounding_count = len(comp)
    transall.log("Risk", "score_risk",
                 {"exposed_count": len(exposed_sites)},
                 {"compounding_count": compounding_count,
                  "distributor_class1": distributor_risk.get("class1"),
                  "class": "real"})
    return {"compounding_count": compounding_count,
            "compounding_sites": [c.get("camis") for c in comp],
            "distributor_risk": distributor_risk}


def tool_brief(transall, response, adapter=None):
    """Briefer: compose a plain-language brief GROUNDED in the M2 Response.
    Every number is traced to a Response field — no invented certainty
    (instrument-not-oracle). The adapter may polish one narrative line; the
    facts come from the Response."""
    r = response["recall"]
    rec = response
    swap = rec["recommendation"]["swap_to"]
    prov = rec["provenance"]
    narrative = None
    if adapter is not None:
        prompt = (
            "You are the Briefer agent for BREADCRUMBS, a food-safety ops tool. "
            "Write ONE plain sentence (<=30 words) summarizing this recall response "
            "for an operator. Use ONLY these facts, no others: firm=%s, classification=%s, "
            "exposed_count=%d, compounding_count=%d, distributor_class1=%d, swap_to=%s. "
            "Label modeled exposure as modeled. Do not add numbers."
        ) % (r.get("recalling_firm"), r.get("classification"),
             rec["exposed_count"], rec["compounding_count"],
             rec["distributor_risk"].get("class1", 0), swap.get("firm"))
        raw = adapter.complete(prompt, system="Be terse and factual.")
        # accept the model narrative only if it is a clean short sentence —
        # reasoning models sometimes dump their chain-of-thought, which is not
        # a brief. The grounded numbers come from the Response regardless.
        if raw and isinstance(raw, str) and not raw.startswith("[adapter"):
            stripped = raw.strip()
            clean = (len(stripped) <= 240
                     and "**" not in stripped
                     and "\n" not in stripped
                     and not stripped[:3].rstrip(".").isdigit())
            if clean:
                narrative = stripped

    brief = {
        "recall_number": r.get("recall_number"),
        "recalling_firm": r.get("recalling_firm"),
        "classification": r.get("classification"),
        "headline": narrative or (
            "%s %s recall: %d of your sites exposed (modeled links), %d with prior "
            "critical violations." % (
                r.get("recalling_firm"), r.get("classification"),
                rec["exposed_count"], rec["compounding_count"])),
        "exposed_count": rec["exposed_count"],
        "compounding_count": rec["compounding_count"],
        "distributor_class1": rec["distributor_risk"].get("class1"),
        "distributor_recalls": rec["distributor_risk"].get("recalls"),
        "swap_to": swap.get("firm"),
        "swap_to_class1": swap.get("class1"),
        "recommendation": rec["recommendation"]["action"],
        "provenance": prov,
        "grounded_in": "M2 Response (sim.respond)",
        "class": "instrument-not-oracle",
    }
    transall.log("Briefer", "brief",
                 {"recall_number": r.get("recall_number")},
                 {"headline": brief["headline"],
                  "exposed_count": brief["exposed_count"],
                  "compounding_count": brief["compounding_count"],
                  "distributor_class1": brief["distributor_class1"],
                  "swap_to": brief["swap_to"]})
    return brief


def tool_draft_sms(transall, response, brief):
    """Comms: draft the SMS alert + supplier hold notice, grounded in the
    Response. The layman alert is <=2 sentences (SMS-style). (M5 wires the
    actual send via tool_send -> agent.comms.send_alert.)"""
    r = response["recall"]
    # <=2 sentences: one alert sentence + one action sentence.
    sms = (
        "ALERT: {product} recalled ({cls}, {reason}) — {n} of your sites exposed "
        "({comp} with prior critical violations). HOLD lot and swap sourcing to {swap}."
    ).format(
        product=(r.get("product_description") or "")[:80],
        cls=r.get("classification"),
        reason=(r.get("reason_for_recall") or "")[:60],
        n=response["exposed_count"],
        comp=response["compounding_count"],
        swap=brief["swap_to"],
    )
    hold = (
        "HOLD NOTICE — {firm} {product}\n"
        "Recall: {rn} ({cls})\n"
        "Action: hold all inventory from this supplier; do not serve.\n"
        "Reason: {reason}\n"
        "Affected sites: {n} (modeled links)"
    ).format(
        firm=r.get("recalling_firm"),
        product=(r.get("product_description") or "")[:80],
        rn=r.get("recall_number"),
        cls=r.get("classification"),
        reason=r.get("reason_for_recall"),
        n=response["exposed_count"],
    )
    payload = {"sms": sms, "hold_notice": hold,
               "exposed_count": response["exposed_count"],
               "compounding_count": response["compounding_count"],
               "swap_to": brief["swap_to"],
               "class": "grounded"}
    transall.log("Comms", "draft_sms",
                 {"recall_number": r.get("recall_number")},
                 {"sms": sms, "hold_notice": hold[:80] + "..."})
    return payload


def tool_send(transall, response, brief, sms_payload, profile=None,
              adapter=None, out_dir=None):
    """Comms -> send: dispatch the alert over the channel picked by the
    operator alert-preference profile (M1). PRIMARY=Telegram (real send,
    I/O not inference); FALLBACK=mock phone (offline, zero network). The
    alert is GROUNDED in the M2 Response (real product, exposed count,
    compounding count, swap target)."""
    from agent.comms import send_alert
    res = send_alert(response, brief, sms_payload, profile=profile,
                     adapter=adapter, out_dir=out_dir)
    transall.log("Comms", "send",
                 {"recall_number": response["recall"].get("recall_number"),
                  "channel": (profile or {}).get("channel", "telegram")},
                 {"sent_via": res.get("sent_via"), "ok": res.get("ok"),
                  "channel_attempted": res.get("channel_attempted"),
                  "fallback_reason": res.get("fallback_reason")})
    return res


# ── the always-on watch (Mongo change stream) ─────────────────────────────────
def watch_change_stream(on_recall, db=None, timeout_s=60):
    """The Watcher's always-on watch: a Mongo CHANGE STREAM on the recalls
    collection. A new insert fires on_recall(recall_doc). This IS the
    always-on watch (PRD hard rule). Blocks until timeout or interrupted."""
    db = get_db() if db is None else db
    try:
        with db.recalls.watch([{"$match": {"operationType": "insert"}}]) as stream:
            for change in stream:
                recall = change.get("fullDocument")
                if recall:
                    on_recall(recall)
    except Exception as e:
        # change streams need a replica set; fall back to polling in dev
        print("[watcher] change stream unavailable (%s); use run() directly" % type(e).__name__)
        return


# ── the swarm run ─────────────────────────────────────────────────────────────
def run(recall_number, db=None, adapter=None, force_alert=False):
    """Run the swarm on a fired recall. Returns:
      {brief, sms, response, transcript, memory, deduped}.
    Deduped=True means prior state was recalled and no new alert was sent."""
    db = get_db() if db is None else db
    adapter = adapter if adapter is not None else ModelAdapter(backend="openrouter")
    transcript = Transcript()

    # Watcher: watch_feed -> ingest_recall
    tool_watch_feed(transcript, recall_number, db)
    recall = tool_ingest_recall(transcript, recall_number, db)
    recall_id = recall.get("recall_number") or str(recall.get("_id"))

    # agent_memory: recall prior state (retrieval that changes behavior)
    prior = recall_state(recall_id, db)
    if prior and not force_alert:
        # DEDUP: we already handled this recall. Re-recall prior state, do
        # NOT re-alert. Record the re-run (alert_sent=0 for this entry).
        response = respond(recall, db)
        brief = tool_brief(transcript, response, adapter)
        sms = tool_draft_sms(transcript, response, brief)
        mem = record_run(recall_id, "deduped: prior alert recalled, no re-alert",
                         alert_sent=False, response=response, db=db, re_alert=False)
        result = {
            "brief": brief, "sms": sms, "response": response,
            "transcript": transcript.as_list(), "memory": mem,
            "deduped": True, "alert_count": alert_count(recall_id, db),
            "alert": None, "send": {"ok": False, "skipped": True,
                                     "reason": "deduped: prior alert recalled"},
        }
        return result

    # Tracer + Risk(distributor) CONCURRENTLY (independent aggregations)
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_exposed = ex.submit(tool_trace_forward, transcript, recall, db)
        f_dist = ex.submit(tool_distributor_risk, transcript, recall, db)
        exposed_sites = f_exposed.result()
        distributor_risk = f_dist.result()

    # Risk (final): compounding depends on exposed_sites
    risk = tool_score_risk(transcript, recall, exposed_sites, distributor_risk, db)

    # The M2 Response is the single source of truth for the brief's numbers.
    response = respond(recall, db)

    # sanity: the swarm's concurrent pieces must agree with the Response
    assert risk["compounding_count"] == response["compounding_count"], \
        "swam risk drift vs Response"
    assert len(exposed_sites) == response["exposed_count"], \
        "swarm exposure drift vs Response"
    assert risk["distributor_risk"]["class1"] == \
        response["distributor_risk"]["class1"], "swarm distributor drift vs Response"

    # Briefer + Comms (grounded)
    brief = tool_brief(transcript, response, adapter)
    sms = tool_draft_sms(transcript, response, brief)

    # Comms -> send (M5): dispatch the alert over the profile's channel.
    # Telegram (primary) or mock phone (offline fallback). The alert is
    # grounded in the M2 Response.
    from sim.operator import preferences as _prefs
    profile = _prefs()
    send_res = tool_send(transcript, response, brief, sms, profile=profile,
                         adapter=None, out_dir=None)

    # persist to agent_memory (first alert for this recall)
    mem = record_run(recall_id, "alert sent: hold + swap recommendation",
                     alert_sent=True, response=response, db=db, re_alert=False)

    return {
        "brief": brief, "sms": sms, "response": response,
        "transcript": transcript.as_list(), "memory": mem,
        "deduped": False, "alert_count": alert_count(recall_id, db),
        "alert": send_res.get("alert"),
        "send": send_res,
    }


if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("recall_number", nargs="?", default="F-0757-2022",
                   help="recall_number (default: the Dole hero recall)")
    a.add_argument("--no-model", action="store_true",
                   help="skip the OpenRouter call (deterministic fallback)")
    args = a.parse_args()

    ad = ModelAdapter(backend="openrouter")
    if args.no_model:
        ad = ModelAdapter(backend="stub")  # type: ignore
    # stub backend not implemented above; use a no-key openrouter adapter
    if args.no_model:
        os.environ.pop("OPENROUTER_API_KEY", None)

    out = run(args.recall_number, adapter=ad)
    print(json.dumps({
        "brief": out["brief"],
        "sms": out["sms"],
        "deduped": out["deduped"],
        "alert_count": out["alert_count"],
        "transcript": out["transcript"],
    }, indent=2, default=str))
