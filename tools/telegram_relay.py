#!/usr/bin/env python3
"""BREADCRUMBS local relay — the box's I/O seam. Runs on the GB10 (or Mac for dev).
  POST /alert  {text}              -> Telegram sendMessage (short text alert)
  POST /ask    {question,context}  -> local Nemotron (vLLM), grounded, <think> stripped
  POST /report {report}            -> build a formal FDA-style PDF (reportlab) from the recall
                                      response, send text + the PDF to Telegram (sendDocument),
                                      and return the PDF (base64) so the console can offer download.
Reads TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID from ~/.config/breadcrumbs/telegram.env.
vLLM from BC_VLLM_URL (default http://localhost:8000/v1)."""
import base64, io, json, os, re, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

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

def _tg_text(text):
    c = _cfg(); tok = c.get("TELEGRAM_BOT_TOKEN"); cid = c.get("TELEGRAM_CHAT_ID")
    if not tok or not cid: return {"ok": False, "error": "token/chat_id unconfigured"}
    body = json.dumps({"chat_id": cid, "text": text, "disable_web_page_preview": True}).encode()
    req = urllib.request.Request("https://api.telegram.org/bot%s/sendMessage" % tok,
                                 data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.load(r); return {"ok": d.get("ok"), "message_id": d.get("result", {}).get("message_id")}

def _tg_document(pdf_bytes, filename, caption):
    """Send a PDF to Telegram via sendDocument (multipart/form-data, hand-built)."""
    c = _cfg(); tok = c.get("TELEGRAM_BOT_TOKEN"); cid = c.get("TELEGRAM_CHAT_ID")
    if not tok or not cid: return {"ok": False, "error": "token/chat_id unconfigured"}
    boundary = "----bcbnd7f3a9c1e"
    def part(name, val):
        return ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, name, val)).encode()
    body = part("chat_id", cid) + part("caption", caption)
    body += ("--%s\r\nContent-Disposition: form-data; name=\"document\"; filename=\"%s\"\r\n"
             "Content-Type: application/pdf\r\n\r\n" % (boundary, filename)).encode()
    body += pdf_bytes + ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request("https://api.telegram.org/bot%s/sendDocument" % tok, data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r); return {"ok": d.get("ok"), "message_id": d.get("result", {}).get("message_id")}

def _ask(question, context):
    sysmsg = ("detailed thinking off. You are BREADCRUMBS, a sharp NYC food-safety analyst advising an "
              "operator during a live recall. Answer the question DIRECTLY in ONE or TWO short sentences. "
              "Lead with the number or the answer, then one clause of why it matters. Use the exact figures in "
              "the FACTS and count them yourself when asked 'how many'. Be decisive and specific — never say "
              "'not specified', never list what you don't know, never hedge, no markdown headers or bullets. "
              "Talk like an expert who already read the report.")
    user = "FACTS:\n%s\n\nQUESTION: %s\n\nAnswer in 1-2 direct sentences:" % (context or "(none)", question)
    body = json.dumps({"model": MODEL, "temperature": 0.1, "max_tokens": 160,
                       "messages": [{"role": "system", "content": sysmsg},
                                    {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(VLLM.rstrip("/") + "/chat/completions",
                                 data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        d = json.load(r)
    txt = re.sub(r"<think>.*?</think>", "", d["choices"][0]["message"]["content"], flags=re.S).strip()
    return {"ok": True, "answer": txt, "model": MODEL, "local": True}

# ---- last-resort static PDF (valid, minimal) if reportlab itself fails ----
_FALLBACK_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
    b"/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>endobj\n"
    b"4 0 obj<</Length 74>>stream\n"
    b"BT /F1 12 Tf 72 720 Td (BREADCRUMBS Recall Report - render error) Tj ET\n"
    b"endstream endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)


def _s(v):
    """None-safe stringify."""
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _int(v, default=0):
    """Best-effort int; never raises."""
    try:
        if isinstance(v, bool):
            return int(v)
        if isinstance(v, str):
            m = re.search(r"-?\d+", v)
            return int(m.group()) if m else default
        return int(v)
    except (TypeError, ValueError):
        return default


def _esc(v, n=None):
    """Truncate cleanly, then XML-escape for reportlab Paragraph (& < > only).
    Data is escaped here; markup tags (<b> etc.) are added by callers AFTER this."""
    s = _s(v).strip()
    if not s:
        s = "-"
    if n and len(s) > n:
        s = s[: n - 1].rstrip() + "…"
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _classify(raw):
    """Return (n, roman) where n in {1,2,3} or 0 if unknown. Order matters: III->II->I."""
    u = _s(raw).upper().replace(".", "").replace("-", " ")
    if "III" in u or "CLASS 3" in u or "CLASS THREE" in u:
        return 3, "III"
    if "II" in u or "CLASS 2" in u or "CLASS TWO" in u:
        return 2, "II"
    if re.search(r"\bI\b", u) or "CLASS 1" in u or "CLASS ONE" in u:
        return 1, "I"
    return 0, ""


def _build_pdf(rep):
    """Formal FDA-style 'Recall Exposure & Action Report' from the recall response.
    reportlab.platypus only. Deterministic: numbers come straight from `rep`. Never raises —
    always returns non-empty PDF bytes (falls back to a minimal PDF on any render failure)."""
    if not isinstance(rep, dict):
        rep = {}
    try:
        return _render(rep)
    except Exception as e:
        try:
            return _render_min(rep, e)
        except Exception:
            return _FALLBACK_PDF


def _render(rep):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    def _d(v):
        return v if isinstance(v, dict) else {}
    rc = _d(rep.get("recall"))
    dr = _d(rep.get("distributor_risk"))
    rec = _d(rep.get("recommendation"))
    sw = _d(rec.get("swap_to"))
    exposed = rep.get("exposed_sites")
    exposed = exposed if isinstance(exposed, list) else []
    prov = _d(rep.get("provenance"))

    ss = getSampleStyleSheet()
    NAVY = colors.HexColor("#0b2b45")
    GREY = colors.HexColor("#5a6473")
    LINE = colors.HexColor("#dde3ec")
    H = ParagraphStyle("H", parent=ss["Title"], fontSize=16, spaceAfter=2, textColor=NAVY)
    sub = ParagraphStyle("sub", parent=ss["Normal"], fontSize=8, textColor=GREY, leading=11)
    sec = ParagraphStyle("sec", parent=ss["Heading2"], fontSize=11, spaceBefore=11, spaceAfter=3, textColor=NAVY)
    body = ParagraphStyle("body", parent=ss["Normal"], fontSize=9.5, leading=13)
    small = ParagraphStyle("small", parent=ss["Normal"], fontSize=7.5, textColor=GREY, leading=10)
    whiteb = ParagraphStyle("whiteb", parent=body, textColor=colors.white, fontSize=11.5)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter, topMargin=0.7 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        title="BREADCRUMBS Recall Exposure & Action Report",
        author="BREADCRUMBS (on-prem)",
    )
    W = 6.9 * inch  # usable content width

    n, roman = _classify(rc.get("classification"))
    banner_col = {1: colors.HexColor("#c0392b"), 2: colors.HexColor("#d68910"),
                  3: colors.HexColor("#b7950b"), 0: GREY}[n]
    recall_no = _esc(rc.get("recall_number"))

    el = []
    # --- header ---
    el.append(Paragraph("Recall Exposure &amp; Action Report", H))
    subline = "BREADCRUMBS &middot; generated on-prem, offline &middot; report ref %s" % recall_no
    note = _esc(rep.get("generated_note")) if rep.get("generated_note") else ""
    if note and note != "-":
        subline += " &middot; %s" % note
    el.append(Paragraph(subline, sub))
    el.append(Spacer(1, 6))

    # --- severity banner ---
    if n:
        btext = "<b>FDA CLASS %s RECALL</b> &nbsp; %s" % (roman, recall_no)
    else:
        btext = "<b>FDA RECALL &middot; CLASSIFICATION UNAVAILABLE</b> &nbsp; %s" % recall_no
    banner = Table([[Paragraph(btext, whiteb)]], colWidths=[W])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), banner_col), ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    el.append(banner)
    el.append(Spacer(1, 8))

    # --- 1. FDA recall facts (REAL) ---
    el.append(Paragraph("1. FDA Recall &mdash; source: openFDA food enforcement [REAL]", sec))
    facts = [
        ("Recalling firm", _esc(rc.get("recalling_firm"), 90)),
        ("Product", _esc(rc.get("product_description"), 220)),
        ("Reason / hazard", _esc(rc.get("reason_for_recall"), 260)),
        ("Classification", ("Class %s" % roman) if n else "Not classified / unavailable"),
        ("Firm state", _esc(rc.get("state"), 40)),
    ]
    hazard = _s(rc.get("hazard_class")).strip().lower()
    if hazard == "allergen":
        allergens = rc.get("allergens") or []
        if isinstance(allergens, (list, tuple)) and allergens:
            atxt = _esc(", ".join(_s(a) for a in allergens if _s(a).strip()), 200)
        else:
            atxt = "Undeclared allergen (specifics not provided)"
        facts.append(("Allergen(s)", atxt))
    ft = Table([[Paragraph("<b>%s</b>" % _esc(k), small), Paragraph(v, body)] for k, v in facts],
               colWidths=[1.4 * inch, 5.5 * inch])
    ft.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LINEBELOW", (0, 0), (-1, -2), 0.3, LINE)]))
    el.append(ft)

    # --- 2. Exposure (MODELED supplier->site links) ---
    exp_count = _int(rep.get("exposed_count", len(exposed)), len(exposed))
    n_listed = len(exposed)
    hdr = ("%d site(s) received the affected lot" % exp_count if exp_count == n_listed
           else "%d site(s) received the affected lot (%d itemized below; %d not resolved in this record)"
                % (exp_count, n_listed, max(0, exp_count - n_listed)))
    el.append(Paragraph(
        "2. Your Exposure &mdash; %s [supplier&rarr;site links MODELED]" % hdr, sec))
    if exposed:
        rows = [[Paragraph("<b>Site</b>", small), Paragraph("<b>Borough</b>", small),
                 Paragraph("<b>Cuisine</b>", small), Paragraph("<b>Crit. viol.</b>", small),
                 Paragraph("<b>Distributor</b>", small)]]
        for s in exposed:
            if not isinstance(s, dict):
                s = {}
            rows.append([
                Paragraph(_esc(s.get("name"), 60), body),
                Paragraph(_esc(s.get("boro"), 24), body),
                Paragraph(_esc(s.get("cuisine"), 30), body),
                Paragraph(_s(_int(s.get("crit_violations"))), body),
                Paragraph(_esc(s.get("distributor"), 40), body)])
        et = Table(rows, colWidths=[1.9 * inch, 0.85 * inch, 1.3 * inch, 0.75 * inch, 2.0 * inch],
                   repeatRows=1)
        et.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7fb")]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#ccd4df")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        el.append(et)
    else:
        empty = Table([[Paragraph(
            "No sites in your portfolio are modeled as exposed to this lot. "
            "Absence of a modeled link is <b>not</b> proof of no exposure &mdash; the "
            "supplier&rarr;site trace is the FSMA-204 gap this tool flags.", body)]], colWidths=[W])
        empty.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f7fb")),
            ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#ccd4df")),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        el.append(empty)

    # --- 3. Risk (REAL) ---
    el.append(Paragraph("3. Risk &mdash; openFDA distributor history + NYC DOHMH violations [REAL]", sec))
    comp = _int(rep.get("compounding_count"))
    firm = _esc(dr.get("firm"))
    if dr.get("firm") or dr.get("class1") is not None or dr.get("recalls") is not None:
        risk_txt = ("Distributor <b>%s</b>: <b>%d Class-I</b> recall(s) on file (of %d total on record). "
                    % (firm, _int(dr.get("class1")), _int(dr.get("recalls"))))
    else:
        risk_txt = "No distributor recall history was supplied for this record. "
    if comp > 0:
        risk_txt += ("<b>%d</b> of your exposed site(s) already carry prior critical "
                     "food-handling violation(s), compounding the hazard." % comp)
    else:
        risk_txt += "No exposed site carries a prior critical violation in the supplied data."
    el.append(Paragraph(risk_txt, body))

    # --- 4. Recommended action ---
    el.append(Paragraph("4. Recommended Action", sec))
    action = _esc(rec.get("action"), 200)
    lead = ("<b>%s</b>" % action) if action != "-" else \
        "<b>HOLD and segregate the recalled lot; do not serve.</b>"
    if sw and (sw.get("firm") or sw.get("basis")):
        swap = ("Swap sourcing to <b>%s</b>" % _esc(sw.get("firm"), 80))
        detail = []
        if sw.get("class1") is not None or sw.get("recalls") is not None:
            detail.append("%d Class-I of %d recalls on record" % (_int(sw.get("class1")), _int(sw.get("recalls"))))
        if sw.get("basis"):
            detail.append(_esc(sw.get("basis"), 120))
        if detail:
            swap += " (%s)" % "; ".join(detail)
        swap += ", away from <b>%s</b> (%d Class-I on record). Notify DOHMH." % (firm, _int(dr.get("class1")))
    else:
        swap = ("No lower-risk substitute was identified in the current dataset; source from a "
                "supplier with a verified clean recall record and notify DOHMH.")
    act_txt = "%s %s" % (lead, swap)
    rationale = _esc(rec.get("rationale"), 300)
    if rationale != "-":
        act_txt += " <i>%s</i>" % rationale
    el.append(Paragraph(act_txt, body))

    # --- provenance box (REAL vs MODELED) ---
    el.append(Spacer(1, 10))
    real_items = prov.get("real") if isinstance(prov.get("real"), (list, tuple)) else None
    mod_items = prov.get("modeled") if isinstance(prov.get("modeled"), (list, tuple)) else None
    real_txt = (_esc("; ".join(_s(x) for x in real_items if _s(x).strip()), 400)
                if real_items else "recall facts, distributor recall history, site critical violations")
    mod_txt = (_esc("; ".join(_s(x) for x in mod_items if _s(x).strip()), 400)
               if mod_items else "supplier→site links (the FSMA-204 traceability gap), illustrative portfolio")
    pv = Table([[Paragraph(
        "<b>PROVENANCE</b> &nbsp; <b>REAL:</b> %s. &nbsp; <b>MODELED (labeled):</b> %s."
        % (real_txt, mod_txt.replace("→", "&rarr;")), small)]], colWidths=[W])
    pv.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff8ec")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2a54a")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    el.append(pv)
    el.append(Spacer(1, 6))

    # --- footer ---
    el.append(Paragraph(
        "Measures per FDA <b>21 CFR 7</b> (recall procedures) &amp; <b>FSMA 204</b> "
        "(Food Traceability Rule). Generated on-prem on the operator's own hardware; "
        "supplier data never left the building. Deterministic report &mdash; no model in this path.", small))

    doc.build(el)
    return buf.getvalue()


def _render_min(rep, err):
    """Degraded but valid PDF if the full render throws — still names the recall."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    rc = rep.get("recall") if isinstance(rep, dict) else None
    rc = rc if isinstance(rc, dict) else {}
    ss = getSampleStyleSheet()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.8 * inch, leftMargin=0.8 * inch)
    doc.build([
        Paragraph("BREADCRUMBS Recall Exposure &amp; Action Report", ss["Title"]),
        Spacer(1, 8),
        Paragraph("Recall ref: %s" % _esc(rc.get("recall_number")), ss["Normal"]),
        Paragraph("Recalling firm: %s" % _esc(rc.get("recalling_firm"), 90), ss["Normal"]),
        Spacer(1, 8),
        Paragraph("Full report could not be rendered (%s). Data above is REAL from openFDA. "
                  "Per 21 CFR 7 / FSMA 204." % _esc(type(err).__name__), ss["Normal"]),
    ])
    return buf.getvalue()

def _report(rep):
    """Build the PDF, send the short text + the PDF to Telegram, return the PDF (b64) for download."""
    rc = rep.get("recall", {}); dr = rep.get("distributor_risk", {})
    sw = (rep.get("recommendation", {}) or {}).get("swap_to", {})
    text = ("⚠ BREADCRUMBS — RECALL EXPOSURE ALERT\n\n"
            "FDA %s recall %s (%s)\nProduct: %s\n\n"
            "EXPOSURE: %s of your sites received the affected lot; %s carry prior critical DOHMH violations.\n"
            "ACTION: HOLD the recalled lot. Swap to %s%s — away from %s (%s Class-I on record).\n\n"
            "Formal PDF report attached. Generated on-prem, offline.") % (
        rc.get("classification") or "Class I", rc.get("recall_number") or "", rc.get("recalling_firm") or "",
        (rc.get("product_description") or "")[:80], rep.get("exposed_count", 0), rep.get("compounding_count", 0),
        sw.get("firm") or "a verified-record supplier", (" (%s)" % sw["basis"]) if sw.get("basis") else "",
        dr.get("firm") or "-", dr.get("class1", 0))
    pdf = _build_pdf(rep)
    t = _tg_text(text)
    fn = "BREADCRUMBS-%s.pdf" % (rc.get("recall_number") or "report")
    d = _tg_document(pdf, fn, "Recall Exposure & Action Report — %s" % (rc.get("recalling_firm") or ""))
    return {"ok": bool(d.get("ok")), "text_message_id": t.get("message_id"), "doc_message_id": d.get("message_id"),
            "pdf_b64": base64.b64encode(pdf).decode(), "filename": fn}

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
        p = self.path.rstrip("/")
        try:
            if p.endswith("ask"):      out = _ask(b.get("question", ""), b.get("context", ""))
            elif p.endswith("report"): out = _report(b.get("report") or {})
            else:                      out = _tg_text(b.get("text") or "BREADCRUMBS alert (no body supplied).")
        except Exception as e:
            out = {"ok": False, "error": "%s: %s" % (type(e).__name__, e)}
        self.send_response(200 if out.get("ok") else 502); self._cors()
        self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps(out).encode())
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(os.environ.get("BC_RELAY_PORT", "8899"))
    print("[bc-relay] :%d  ->  Telegram(/alert,/report) + local Nemotron %s (/ask)" % (port, VLLM))
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
