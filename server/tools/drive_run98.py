#!/usr/bin/env python3
"""
RUN 97, GOAL ZERO. THE GOVERNANCE DECISION CARD ON THE OWNER'S OWN ROUTE.

NOTHING UNDER TEST IS SUPPLIED. The fixture below seeds DOCUMENTS through the real upload and
compute routes -- which section 1a.4 expressly permits -- and then the browser opens the REAL
project detail page and reads the Governance Decision panel BACK OUT OF THE RENDERED DOM. The
decision brief is NOT composed here, NOT injected here, and NOT handed to any render function
here: it must arrive on the served result and be laid out by the page's own code, or this
driver reports it absent.

Contrast with `drive_run96_card.py`, which composed the card in Python and called
`LinDecisionUI.__cardForTest.renderDecisionBrief(card)` on a blank page. That measured the
renderer; it could not measure whether the card reaches a participant.

Original fixture setup below is drive_run48_browser.py's.

Serves the REAL application from the repository root against a throwaway migrated SQLite
database, builds a MULTI-PERIOD fixture through the REAL routes, drives the real Chromium
headless shell against it, renders the REAL project detail page, and reads back OUT OF THE
RENDERED DOM which period each panel is showing.

WHY MULTI-PERIOD, AND WHY IT COULD NOT BE BEFORE. Run 47's browser fixture had to be
single-period because `primeAndRefresh` read the stored row back with a hard-coded `period: 1`:
a second period existed on the server and no panel on the page would ever have shown it. That
literal is what Run 48 removes, so this fixture is built with two computed periods whose rows
are DIFFERENT IN TEXT THE PAGE PRINTS, and every panel is asked, BY NAME, which of the two it
is showing.

THE TWO PERIODS ARE MADE DISTINGUISHABLE ON PURPOSE. Period 1's figures agree with the
percentages that determine them, so it carries NO disagreement finding at all; period 2's
planned value disagrees with its own document by 25 per cent, so it carries exactly one. A page
still reading period 1 would render no disagreement block, would print period 1's figures in
the ledger, and would fail here rather than pass quietly.

GUARDED FIRST: the DEng\\Demo tell. api.js / boot.js in document.scripts with zero `.page`
sections, against the 7 this application has. Checked before anything else is measured, and the
session's working directory is printed.

THIS DRIVER CHANGES NOTHING in the repository. Production Postgres is never contacted.

Run from a CLEAN directory (never the scratchpad root: a `queue.py` there shadows the standard
library and anyio then fails as an opaque HTTP 500):
    DATABASE_URL=sqlite:///<throwaway> SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python <repo>/server/tools/drive_run48_browser.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import pathlib
import re
import socket
import sys
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)

SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = 0
FAILED = 0


def check(ok, label, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"   [{detail}]" if detail else ""))
    return bool(ok)


def post(payload):
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return r.json()


def b64(raw):
    return base64.b64encode(raw).decode()


# ------------------------------------------------------------------------------ the two periods
#
# Hand-computed, and every figure below is a literal:
#   period 1: 4,000,000 x 25.50 / 100 = 1,020,000, which is exactly the stated planned value,
#             so period 1 carries NO disagreement.
#   period 2: 4,000,000 x 50.00 / 100 = 2,000,000 against a stated 1,500,000. The difference is
#             500,000, and 500,000 / 2,000,000 = 25 per cent, which is above the 2 per cent
#             tolerance, so period 2 carries EXACTLY ONE disagreement.
BAC = 4_000_000
P1 = {"ev": 1_000_000, "ac": 1_050_000, "pv": 1_020_000, "planned_pct": 25.50, "actual_pct": 25.00}
P2 = {"ev": 2_000_000, "ac": 2_100_000, "pv": 1_500_000, "planned_pct": 50.00, "actual_pct": 50.00}
P2_IMPLIED_PV = 2_000_000

END = {1: "2026-03-31", 2: "2026-04-30"}
_STAMP = str(int(time.time()))
ADMIN = "run98-browser-admin-" + _STAMP
D = "PRJ-R98-BROWSER-" + _STAMP

DOCS = [
    ("contract", 1, "contract_value",
     {"original_contract_sum": BAC,
      "project_start_date": "2026-01-01", "project_end_date": "2027-06-30"}),
    ("tps1", 1, "time_phased_schedule",
     {"planned_value_to_date": P1["pv"], "planned_percent_complete": P1["planned_pct"],
      "data_date": END[1], "document_date": END[1]}),
    ("pay1", 1, "pay_application",
     {"amount_paid_to_date": P1["ac"], "completed_to_date": P1["ev"],
      "percent_complete_verified": P1["actual_pct"],
      "application_date": END[1], "document_date": END[1]}),
    ("tps2", 2, "time_phased_schedule",
     {"planned_value_to_date": P2["pv"], "planned_percent_complete": P2["planned_pct"],
      "data_date": END[2], "document_date": END[2]}),
    ("pay2", 2, "pay_application",
     {"amount_paid_to_date": P2["ac"], "completed_to_date": P2["ev"],
      "percent_complete_verified": P2["actual_pct"],
      "application_date": END[2], "document_date": END[2]}),
]


def doc_bytes(tag):
    return f"%PDF-1.4 RUN98BROWSER {_STAMP} {tag}\n".encode()


set_extractor_override(StubExtractor({
    hashlib.sha256(doc_bytes(_t)).hexdigest(): (_ty, _ex) for _t, _p, _ty, _ex in DOCS}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R98-BR-ADMIN-" + _STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == D)) is None:
        s.add(Project(legacy_id=D, doc={"id": D, "name": "Run 98 browser fixture",
                                        "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R98-BR-PM-" + _STAMP, "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": D,
      "participant_id": created["participant_id"], "project_role": "PM"})
for tag, per, _ty, _ex in DOCS:
    r = post({"action": "projectupload", "session_token": PM, "id": D, "period": per,
              "period_end": END[per],
              "documents": [{"filename": f"{tag}.pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(doc_bytes(tag))}]})
    assert r.get("ok") is True, str(r)[:300]
assert post({"action": "projectcomputeall", "session_token": PM, "id": D}).get("ok") is True

# THE DEEP-DIVE SURFACE'S OWN INPUT, WRITTEN THROUGH THE REAL SAVE ROUTE.
#
# research/deepdive.html is the surface that renders the panel labels this run corrects, and it
# is the ONE surface that recomputes in the browser: it reads the LEGACY client-side signals
# blob (`signals.evm`, `signals.cusum`, `signals.mc`, `signals.doc`), not the stored computed
# row, and refuses to draw at all without it. It is written here through `save`, which is the
# write path the client itself uses for that blob. NOTHING STORED BY THE DOCUMENT PIPELINE IS
# TOUCHED: this adds the legacy blob and the period rows are left exactly as computed.
#
# THE BLOB IS THE CAPTURED ONE, NOT AN INVENTED SHAPE. p0-baseline/contracts/get/get.json is a
# recorded response of the real `get` route, and its `signals` block is read from there rather
# than hand-written, so this fixture cannot pass by being shaped to suit the renderer. The file
# is READ ONLY and is not modified.
_capture = json.loads((HERE.parents[1] / "p0-baseline" / "contracts" / "get" / "get.json")
                      .read_text(encoding="utf-8"))
_captured_project = _capture.get("project") or (_capture.get("projects") or [{}])[0]
_proj = post({"action": "get", "session_token": PM, "id": D})
_doc = _proj.get("project") or _proj.get("doc") or {}
_doc.update({
    "id": D, "name": "Run 98 browser fixture", "sector": _captured_project.get("sector"),
    "status": _captured_project.get("status") or "Amber",
    "signals": _captured_project.get("signals"),
    # The captured document's own signalInputs are NOT reused: the live write path validates
    # them and refuses several of that capture's values. Only the `signals` block, which is what
    # the deep-dive surface reads, is taken from the capture.
    "signalInputs": {
        "bac": BAC, "ev": P2["ev"], "ac": P2["ac"], "pv": P2["pv"],
        "docRiskScore": 0.30, "actualPctComplete": P2["actual_pct"],
        "plannedPctComplete": P2["planned_pct"],
    },
})
_sv = post({"action": "save", "session_token": PM, "project": _doc})
assert _sv.get("ok") is True, str(_sv)[:300]

# THE SERVER'S OWN ANSWER, before the browser is asked anything. Both periods are computed and
# the latest one is 2.
_pv = post({"action": "projectperiods", "session_token": PM, "id": D})
assert _pv.get("ok") is True, str(_pv)[:300]

# THE CATEGORY SPECIFICATIONS ARE PRESSED THROUGH THE REAL ROUTE, for both periods.
#
# `documents._result_view` serves `module_results` from the SPECIFICATION PROJECTION, not from
# the Python row, so a project with no stored specification reading serves an EMPTY module list
# and every module renders in its no-current-result STATE. That is Run 79's design, not a
# defect -- but it means the Signal Flow's module -> category branches have no LIVE tier to
# measure until the categories have been called. `projectcategoryapply` is the button a
# participant presses; nothing is written here by hand.
for _per in (1, 2):
    _ap = post({"action": "projectcategoryapply", "session_token": PM, "id": D, "period": _per})
    print(f"category apply period {_per}: ok={_ap.get('ok')} "
          f"readings={len(_ap.get('readings') or [])} servedBy={_ap.get('servedBy')}")

sock = socket.socket()
sock.bind(("127.0.0.1", 0))
PORT = sock.getsockname()[1]
sock.close()
import uvicorn  # noqa: E402

cfg = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical")
server = uvicorn.Server(cfg)
threading.Thread(target=server.run, daemon=True).start()
for _ in range(200):
    try:
        c = socket.create_connection(("127.0.0.1", PORT), 0.2)
        c.close()
        break
    except OSError:
        time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"

print(f"browser session cwd: {os.getcwd()}")
print(f"repository root:     {HERE.parents[1]}")
print(f"DATABASE_URL:        {os.environ.get('DATABASE_URL')}")
print(f"served at:           {BASE}")


MEASURE_WIDTHS = (1280, 1024)

# ---------------------------------------------------------------- GOAL ONE'S PATTERN TEST
#
# WHAT IT LOOKS FOR, and every family is one of the things section 2 names: an issued
# instruction, a prescribed remedy, a named deadline, an assigned authority.
#
# WHAT IT DELIBERATELY DOES NOT LOOK FOR: a bare `\bmust\b` or `\bshould\b`. The composed brief
# prints "the cost efficiency the remaining work must achieve to finish within budget", which is
# the definition of TCPI and not an instruction to anybody. A pattern that fired on that would
# be a pattern the card can only pass by saying less that is true.
IMPERATIVE_PATTERNS = [
    ("assigned authority / named role",
     r"\b(Project Manager|Programme? Manager|Programme? Director|PMO Analyst|PMO Lead|PMO"
     r"|Contracting Officer|Contract Administrator|Document Controller"
     r"|Project Controls Lead|Controls Lead|Contract Administration)\b"),
    ("named deadline",
     r"(\bwithin \d+ (business )?(day|week|month)s?\b"
     r"|\bimmediate(ly)?\b"
     r"|\bnext (reporting cycle|portfolio review|decision point|reporting period)\b"
     r"|\bby (COB|close of business|end of (day|week|month))\b"
     r"|\bresponse timeframe\b|\bfollow-?up date\b)"),
    ("issued instruction (imperative verb opening a sentence or a cell)",
     r"(^|[.;:!?]\s+|\|\s*|\n\s*)(Investigate|Review|Address|Fix|Escalate|Request|Execute"
     r"|Verify|Re-?upload|Locate|Compare|Update|Open|Perform|Implement|Ensure|Notify|Inform"
     r"|Provide|Submit|Correct|Monitor|Proceed|Conduct|Initiate|Assign|Re-?baseline"
     r"|Bring|Raise|Take)\b"),
    ("prescribed remedy",
     r"(\brecommended action\b|\bcorrective action\b|\brecovery[- ]plan\b|\baction plan\b"
     r"|\bremedial\b|\bmitigation plan\b|\bdocumentation required\b|\brouting monitoring\b"
     r"|\broutine monitoring\b|\bclose-?out record\b)"),
    ("prescriptive modality directed at the reader",
     r"(\byou (must|should|shall|will need to)\b|\bis required to\b|\brequired before\b"
     r"|\bshall\b|\bshould be (taken|actioned|escalated|reviewed|provided)\b"
     r"|\bmust be (taken|provided|completed|actioned)\b)"),
]
PRESCRIPTIVE_PROBE = ("Escalate to the Programme Director within 5 business days; "
                      "a recovery-plan review is required before any formal action.")


def scan_imperative(text):
    hits = []
    for name, pat in IMPERATIVE_PATTERNS:
        for m in re.finditer(pat, text or "", re.IGNORECASE):
            frag = (text or "")[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
            hits.append((name, m.group(0).strip(), frag))
    return hits


# THE TEST MUST BE ABLE TO FAIL, and it is proved here BEFORE it is used, against a sentence
# that is exactly what the card must never carry.
_probe = scan_imperative(PRESCRIPTIVE_PROBE)
print()
print("=" * 90)
print("GOAL ONE: THE IMPERATIVE / AUTHORITY PATTERN TEST, PROVED ABLE TO FAIL FIRST")
print("=" * 90)
print(f"  probe sentence: {PRESCRIPTIVE_PROBE}")
for h in _probe:
    print(f"    HIT  [{h[0]}] {h[1]!r}")
check(len({h[0] for h in _probe}) >= 4,
      "the pattern test fires on a prescriptive sentence, on at least four of its five families",
      str(sorted({h[0] for h in _probe})))
check(not scan_imperative(
    "TCPI: 0.998, the cost efficiency the remaining work must achieve to finish within budget. "
    "On the evidence presented, is the absence of an assessment material to the decision now "
    "before you?"),
    "and it does NOT fire on the composed brief's own descriptive prose (no false positive)",
    str(scan_imperative("TCPI: 0.998, the cost efficiency the remaining work must achieve to "
                        "finish within budget.")))

BLOCKS = ["Project posture", "Decision-support finding", "Why this finding was produced",
          "Forecast and baseline comparison", "Material drivers", "Evidence used",
          "Assessment limitations", "Decision question"]
FORBIDDEN_HEADINGS = ["Recommended action", "Conflict", "Authority", "Documentation required",
                      "Documentation Required", "Signal-Traced Action Plan"]
PLACEHOLDERS = ["not established", "Not established"]
EXPECTED_DISPOSITIONS = [
    ("accept", "Accept finding"),
    ("modify", "Modify finding"),
    ("defer", "Defer pending evidence"),
    ("reject", "Override finding"),
    ("no_action_within_current_authority", "Record no action within current authority"),
]

from playwright.sync_api import sync_playwright  # noqa: E402

READ_BACK = {}

try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=SHELL,
                                     args=["--use-gl=swiftshader", "--no-sandbox"])
        for VW in MEASURE_WIDTHS:
            print()
            print("=" * 90)
            print(f"THE OWNER'S ROUTE AT {VW}px -- real server, real page, nothing injected")
            print("=" * 90)
            page = browser.new_page(viewport={"width": VW, "height": 2400})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                            "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
                page.route(pattern, lambda r: r.abort())
            page.goto(BASE + "/", wait_until="domcontentloaded")
            page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
            page.goto(BASE + "/", wait_until="domcontentloaded")
            page.wait_for_timeout(6000)
            out = page.evaluate("""async (id) => {
                // THE OWNER'S OWN NAVIGATION. `LinApp.openDetail` is what the Manage button
                // on the portfolio list calls; it shows the detail page so the section is
                // actually laid out, rather than rendered into a hidden one.
                if (window.LinApp && LinApp.openDetail) LinApp.openDetail(id);
                await new Promise(r => setTimeout(r, 1500));
                await window.LinDetail.render(id);
                // WAIT FOR THE ROW THE CARD READS, then render the card again from it.
                // RUN 98 FINDING: at 1024px the Run 97 driver measured the card BEFORE the
                // served row had arrived and the brief was silently absent. The page's own
                // renderer is called again here with the project the page holds -- nothing is
                // supplied to it; it reads `LinResults.rowFor` exactly as it does on a click.
                let row = null;
                for (let i = 0; i < 200; i++) {
                  row = (window.LinResults && window.LinResults.rowFor)
                      ? window.LinResults.rowFor({id: id}) : null;
                  if (row && row.decision_brief) break;
                  await new Promise(r2 => setTimeout(r2, 250));
                }
                const body = document.querySelector('#body-d-decision');
                if (body) body.style.display = '';
                document.dispatchEvent(new CustomEvent('lin:section-opened',
                                                       {detail: {id: 'd-decision'}}));
                await new Promise(r => setTimeout(r, 2500));
                const panel = document.querySelector('#body-d-decision');
                row = (window.LinResults && window.LinResults.rowFor)
                    ? window.LinResults.rowFor({id: id}) : null;
                const sel = panel ? panel.querySelector('select.disposition') : null;
                return {
                  text: panel ? (panel.innerText || '') : null,
                  headings: panel ? Array.from(panel.querySelectorAll('h2,h3'))
                      .map(n => n.textContent.trim()) : [],
                  groups: panel ? panel.querySelectorAll('.dc-group').length : 0,
                  rowHasBrief: !!(row && row.decision_brief),
                  briefKeys: (row && row.decision_brief)
                      ? Object.keys(row.decision_brief).filter(
                          k => row.decision_brief[k] !== null
                            && row.decision_brief[k] !== undefined
                            && row.decision_brief[k] !== "").sort() : [],
                  rowPeriod: row ? row.period : null,
                  servedDispositions: (row && row.decision_dispositions) || null,
                  selectOptions: sel ? Array.from(sel.options)
                      .map(o => [o.value, o.textContent.trim()]) : null,
                  hasActionPlanTable: !!(panel && panel.querySelector('.ap-table, .dc-action-plan')),
                  hasFairnessGate: !!(panel && panel.querySelector('.fairness-gate')),
                  recordDisabled: (() => { const b = panel && panel.querySelector('.record-btn');
                      return b ? b.disabled : null; })()
                };
            }""", D)
            print(f"  row period on the client: {out['rowPeriod']}")
            print(f"  headings rendered in the panel: {out['headings']}")
            print()
            print("  ---- THE CARD AS THE PAGE RENDERS IT ----")
            for line in (out["text"] or "").splitlines():
                print("  | " + line)
            print("  ---- END ----")
            print()
            print(f"  blocks the composer filled on this row: {out['briefKeys']}")
            KEY_TO_BLOCK = {"posture": "Project posture", "finding": "Decision-support finding",
                            "why": "Why this finding was produced",
                            "forecast": "Forecast and baseline comparison",
                            "drivers": "Material drivers", "evidence": "Evidence used",
                            "limitations": "Assessment limitations",
                            "question": "Decision question"}
            for key, b in KEY_TO_BLOCK.items():
                if key in out["briefKeys"]:
                    check(b in out["headings"], f"[{VW}] block rendered: {b}")
                else:
                    check(b not in out["headings"], f"[{VW}] block absent, not empty: {b}")
            for f in FORBIDDEN_HEADINGS:
                check(f not in out["headings"], f"[{VW}] heading absent: {f}")
            for ph in PLACEHOLDERS:
                check(ph not in (out["text"] or ""), f"[{VW}] placeholder absent: {ph!r}")
            check(out["groups"] >= 6, f"[{VW}] the card renders as separate blocks",
                  str(out["groups"]))

            # ---------------------------------------------------------------- GOAL ONE
            check(out["hasActionPlanTable"] is False,
                  f"[{VW}] NO action-plan table on the card")
            check(out["hasFairnessGate"] is False,
                  f"[{VW}] NO fairness-gate remedy block on the card")
            hits = scan_imperative(out["text"] or "")
            for h in hits:
                print(f"    IMPERATIVE HIT  [{h[0]}] {h[1]!r}  ...{h[2]}...")
            check(not hits,
                  f"[{VW}] no imperative or authority form survives on the rendered card",
                  f"{len(hits)} hits")

            # ---------------------------------------------------------------- GOAL TWO
            print(f"  dispositions served on the row: {out['servedDispositions']}")
            print(f"  options in the card's select:   {out['selectOptions']}")
            served = [(o["code"], o["label"]) for o in (out["servedDispositions"] or [])]
            check(served == EXPECTED_DISPOSITIONS,
                  f"[{VW}] the server serves exactly the five dispositions", str(served))
            opts = [tuple(o) for o in (out["selectOptions"] or [])][1:]  # drop the placeholder
            check(opts == EXPECTED_DISPOSITIONS,
                  f"[{VW}] and the card offers exactly those five", str(opts))
            check(out["recordDisabled"] is True,
                  f"[{VW}] Record decision is disabled until a disposition and a rationale exist")

            # PRESS THE CONTROL. Every one of the five, in turn, INCLUDING accept -- through the
            # page's own button, not by calling the route.
            for code, label in EXPECTED_DISPOSITIONS:
                pressed = page.evaluate("""async (code) => {
                    const panel = document.querySelector('#body-d-decision');
                    const sel = panel.querySelector('select.disposition');
                    const ta  = panel.querySelector('textarea.rationale');
                    const btn = panel.querySelector('.record-btn');
                    const note0 = panel.querySelector('.dc-record-note');
                    if (note0) note0.textContent = '';   // clear the previous press's line
                    ta.value = 'Recorded by the Run 98 driver through the card itself, ' + code;
                    ta.dispatchEvent(new Event('input', {bubbles:true}));
                    sel.value = code;
                    sel.dispatchEvent(new Event('change', {bubbles:true}));
                    if (btn.disabled) return {error: 'button still disabled for ' + code};
                    btn.click();
                    for (let i = 0; i < 120; i++) {
                      const n = panel.querySelector('.dc-record-note');
                      if (n && n.textContent.trim()) return {note: n.textContent.trim()};
                      await new Promise(r => setTimeout(r, 250));
                    }
                    return {error: 'no read-back line appeared for ' + code};
                }""", code)
                print(f"    pressed {code:38s} -> {pressed}")
                check(bool(pressed.get("note", "").startswith("Recorded in the audit record:")),
                      f"[{VW}] {code} recorded and READ BACK from the audit record on the page",
                      str(pressed))
                READ_BACK.setdefault(code, pressed.get("note"))

            check(not errors, f"[{VW}] no page errors", str(errors[:3]))

            # ---------------------------------------------------------------- GOAL THREE
            page.evaluate("(id) => { window.__run98id = id; }", D)
            flow = page.evaluate("""async () => {
                const body = document.querySelector('#body-d-neural');
                if (body) body.style.display = '';
                document.dispatchEvent(new CustomEvent('lin:section-opened',
                                                       {detail: {id: 'd-neural'}}));
                for (let i = 0; i < 80; i++) {
                  if (document.querySelector('#body-d-neural svg')) break;
                  await new Promise(r => setTimeout(r, 250));
                }
                await new Promise(r => setTimeout(r, 1500));
                const svg = document.querySelector('#body-d-neural svg');
                if (!svg) return {error: 'no svg drawn'};
                const rows = (t) => Array.from(svg.querySelectorAll(
                    '[data-edge-type="' + t + '"]')).map(e =>
                    (e.getAttribute('opacity')||'?') + ' @ ' +
                    (e.getAttribute('stroke-width')||'?') + 'px');
                const tally = (a) => a.reduce((m,k)=>(m[k]=(m[k]||0)+1,m),{});
                const term = Array.from(svg.querySelectorAll('[data-edge-terminates]')).map(e=>
                  [e.getAttribute('data-edge-terminates'), e.getAttribute('opacity'),
                   !!e.getAttribute('stroke-dasharray'),
                   !!e.getAttribute('marker-end')].join('|'));
                const ys = (kind) => Array.from(svg.querySelectorAll('[data-kind="'+kind+'"]'))
                    .map(n => { const c = n.querySelector('circle,rect,polygon');
                                if (!c) return NaN;
                                const v = c.getAttribute('cy');
                                if (v !== null) return parseFloat(v);
                                const y = c.getAttribute('y'), h = c.getAttribute('height');
                                return y === null ? NaN
                                       : parseFloat(y) + (h ? parseFloat(h) / 2 : 0); })
                    .filter(v => !isNaN(v));
                const span = (a) => a.length ? {n: a.length, top: Math.round(Math.min(...a)),
                                                bottom: Math.round(Math.max(...a))} : {n: 0};
                const vb = (svg.getAttribute('viewBox')||'').split(/\\s+/).map(Number);
                // RUN 98 GOAL THREE. THE TWO PORTS PER NODE, read from what was DRAWN.
                const ports = (kind) => Array.from(
                    svg.querySelectorAll('[data-kind="'+kind+'"]')).map(g => {
                      const shapes = Array.from(g.querySelectorAll('[data-port]'))
                        .filter(e => e.getAttribute('data-kind') === null
                                  || !/identity/.test(e.getAttribute('data-kind')||''));
                      // RUN 103 GOAL SIX. THE READER IS SHAPE-AWARE. THE CHART IS UNCHANGED.
                      // `config.linStatusShape` draws a port as a CIRCLE for Green, a TRIANGLE
                      // for Yellow, a DIAMOND for Amber and a SQUARE for Red, so a non-Green
                      // category's port is a <polygon> with no `cx` and no `r`, and reading
                      // those attributes gave NaN on three checks per viewport. The chart was
                      // right and the reader was blind. The centre and the radius are now
                      // recovered from whatever was actually drawn -- `cx`/`r` on a circle,
                      // `x`+`width`/2 on a rect, and the bounding box of the `points` list on a
                      // polygon -- so a triangle, a diamond and a square are read at the same
                      // coordinate a circle would have been, which is the coordinate the chart
                      // drew them all from.
                      const geom = (e) => {
                        const cx = e.getAttribute('cx');
                        if (cx !== null) {
                          return {x: parseFloat(cx), r: e.getAttribute('r')};
                        }
                        const pts = e.getAttribute('points');
                        if (pts) {
                          const nums = (pts.match(/-?\d+(\.\d+)?/g) || []).map(Number);
                          const xs = nums.filter((_, i) => i % 2 === 0);
                          const ys = nums.filter((_, i) => i % 2 === 1);
                          if (!xs.length) return {x: NaN, r: null};
                          const lo = Math.min(...xs), hi = Math.max(...xs);
                          const ylo = Math.min(...ys), yhi = Math.max(...ys);
                          // The half-extent, rounded to 3 places, is the polygon's own
                          // equivalent of a circle's r: it is what makes two ports drawn at the
                          // same size compare equal without the chart having to carry an `r`.
                          return {x: (lo + hi) / 2,
                                  r: String(Math.round(Math.max(hi - lo, yhi - ylo) / 2 * 1000)
                                            / 1000)};
                        }
                        const x = e.getAttribute('x'), w = e.getAttribute('width');
                        const h = e.getAttribute('height');
                        if (x !== null) {
                          return {x: parseFloat(x) + (w ? parseFloat(w) / 2 : 0),
                                  r: w ? String(Math.max(parseFloat(w),
                                                         h ? parseFloat(h) : 0) / 2) : null};
                        }
                        return {x: NaN, r: e.getAttribute('r')};
                      };
                      return shapes.map(e => {
                        const g = geom(e);
                        return {
                          port: e.getAttribute('data-port'),
                          x: g.x,
                          r: g.r,
                          fill: e.getAttribute('fill'),
                          op: e.getAttribute('opacity'),
                          tag: e.tagName.toLowerCase()
                        };
                      });
                    });
                const ringPorts = (kind, ident) => Array.from(
                    svg.querySelectorAll('[data-kind="'+ident+'"]')).map(e => [
                      e.getAttribute('data-port'), e.getAttribute('r'),
                      e.getAttribute('stroke-width'), e.getAttribute('opacity')].join('|'));
                // Where the edges actually attach, from the path data.
                const edgeEnds = (t, which) => Array.from(svg.querySelectorAll(
                    '[data-edge-type="'+t+'"]')).map(e => {
                      const d = e.getAttribute('d')||'';
                      const nums = d.match(/-?\\d+(\\.\\d+)?/g)||[];
                      return which === 'start' ? parseFloat(nums[0])
                                               : parseFloat(nums[nums.length-2]);
                    });
                const uniq = (a) => Array.from(new Set(a.map(v => Math.round(v)))).sort((x,y)=>x-y);
                // THE THEME BACKGROUND, computed from the whole stack outward.
                const stack = [];
                let el = svg;
                while (el && el !== document.documentElement) {
                  const cs = getComputedStyle(el);
                  stack.push({tag: el.tagName.toLowerCase(),
                              cls: (el.getAttribute('class')||'').slice(0,40),
                              bg: cs.backgroundColor, bgImage: cs.backgroundImage.slice(0,60),
                              surface: cs.getPropertyValue('--surface').trim(),
                              pageBg: cs.getPropertyValue('--page-bg').trim()});
                  el = el.parentElement;
                }
                const rootCS = getComputedStyle(document.documentElement);
                return {
                  viewBox: vb, dm: tally(rows('DOCUMENT -> MODULE')),
                  mc: tally(rows('MODULE -> CATEGORY')), term: tally(term),
                  doc: span(ys('document')), mod: span(ys('module')), cat: span(ys('category')),
                  modPorts: ports('module')[0] || [],
                  modPortCounts: tally(ports('module').map(a => a.length)),
                  catPorts: ports('category')[0] || [],
                  catPortCounts: tally(ports('category').map(a => a.length)),
                  modRings: tally(ringPorts('module','module-identity')),
                  catRings: tally(ringPorts('category','category-identity')),
                  mcStarts: uniq(edgeEnds('MODULE -> CATEGORY','start')),
                  dmEnds: uniq(edgeEnds('DOCUMENT -> MODULE','end')),
                  csStarts: uniq(edgeEnds('CATEGORY -> PROJECT STATUS','start')),
                  mcEnds: uniq(edgeEnds('MODULE -> CATEGORY','end')),
                  panelRects: Array.from(svg.querySelectorAll(':scope > rect'))
                      .map(r => r.getAttribute('fill')),
                  panelRectsComputed: Array.from(svg.querySelectorAll(':scope > rect'))
                      .map(r => getComputedStyle(r).fill),
                  svgRect: (() => {const r = svg.getBoundingClientRect();
                      return {w: Math.round(r.width), h: Math.round(r.height)};})(),
                  stack: stack,
                  tokens: {pageBg: rootCS.getPropertyValue('--page-bg').trim(),
                           surface: rootCS.getPropertyValue('--surface').trim(),
                           theme: document.documentElement.getAttribute('data-theme')}
                };
            }""")
            print()
            print(f"  ---- SIGNAL FLOW at {VW}px ----")
            if flow.get("error"):
                check(False, f"[{VW}] Signal Flow renders", flow["error"])
            else:
                print(f"    module node ports (first module): {flow['modPorts']}")
                print(f"    ports per module node:            {flow['modPortCounts']}")
                print(f"    category node ports (first):      {flow['catPorts']}")
                print(f"    ports per category node:          {flow['catPortCounts']}")
                print(f"    module identity rings:            {flow['modRings']}")
                print(f"    category identity rings:          {flow['catRings']}")
                print(f"    doc->mod edge END x values:       {flow['dmEnds']}")
                print(f"    mod->cat edge START x values:     {flow['mcStarts']}")
                print(f"    mod->cat edge END x values:       {flow['mcEnds']}")
                print(f"    cat->status edge START x values:  {flow['csStarts']}")
                check(set(str(k) for k in flow["modPortCounts"]) == {"2"},
                      f"[{VW}] every module node carries exactly two dots",
                      str(flow["modPortCounts"]))
                check(set(str(k) for k in flow["catPortCounts"]) == {"2"},
                      f"[{VW}] every category node carries exactly two dots",
                      str(flow["catPortCounts"]))
                mp = flow["modPorts"]
                check(len(mp) == 2 and mp[0]["r"] == mp[1]["r"] and mp[0]["fill"] == mp[1]["fill"]
                      and mp[0]["op"] == mp[1]["op"] and mp[0]["tag"] == mp[1]["tag"],
                      f"[{VW}] a module's two dots are IDENTICAL (size, colour, opacity, shape)",
                      str(mp))
                cp = flow["catPorts"]
                check(len(cp) == 2 and cp[0]["r"] == cp[1]["r"] and cp[0]["fill"] == cp[1]["fill"]
                      and cp[0]["op"] == cp[1]["op"] and cp[0]["tag"] == cp[1]["tag"],
                      f"[{VW}] a category's two dots are IDENTICAL", str(cp))
                check(len(mp) == 2 and mp[0]["x"] < mp[1]["x"] and mp[0]["port"] == "in",
                      f"[{VW}] the module's IN dot is on the left and the OUT dot on the right",
                      str(mp))
                check(len(cp) == 2 and cp[0]["x"] < cp[1]["x"] and cp[0]["port"] == "in",
                      f"[{VW}] the category's IN dot is left, OUT dot right", str(cp))
                if len(mp) == 2:
                    check(all(abs(v - mp[0]["x"]) <= 8 for v in flow["dmEnds"]),
                          f"[{VW}] incoming doc->module branches land on the module's LEFT dot",
                          f"ends {flow['dmEnds']} vs left dot {mp[0]['x']}")
                    check(all(abs(v - mp[1]["x"]) <= 2 for v in flow["mcStarts"]),
                          f"[{VW}] outgoing module->category branches leave the RIGHT dot",
                          f"starts {flow['mcStarts']} vs right dot {mp[1]['x']}")
                if len(cp) == 2:
                    check(all(abs(v - cp[0]["x"]) <= 14 for v in flow["mcEnds"]),
                          f"[{VW}] incoming module->category branches land on the category's LEFT dot",
                          f"ends {flow['mcEnds']} vs left dot {cp[0]['x']}")
                    check(all(abs(v - cp[1]["x"]) <= 2 for v in flow["csStarts"]),
                          f"[{VW}] the outgoing category->status edge leaves the RIGHT dot",
                          f"starts {flow['csStarts']} vs right dot {cp[1]['x']}")
                # THEME
                print(f"    theme tokens on :root:            {flow['tokens']}")
                print(f"    svg panel rect fills (attr):      {flow['panelRects']}")
                print(f"    svg panel rect fills (computed):  {flow['panelRectsComputed']}")
                print(f"    svg laid-out size:                {flow['svgRect']}")
                for s in flow["stack"]:
                    print(f"      stack {s['tag']:8s} .{s['cls']:40s} bg={s['bg']} "
                          f"--surface={s['surface']} --page-bg={s['pageBg']}")
                check(flow["panelRects"] == ["var(--page-bg, #0b0e17)", "var(--surface, #0b0e17)"],
                      f"[{VW}] the Signal Flow ground is painted from the theme's own tokens",
                      str(flow["panelRects"]))
                # LAYERS AND STATES -- RE-MEASURED, NOT ASSUMED
                live_dm = sorted(k for k in flow["dm"] if not k.startswith("0.12"))
                live_mc = sorted(k for k in flow["mc"] if not k.startswith("0.14"))
                print(f"    LIVE doc->mod {live_dm}")
                print(f"    LIVE mod->cat {live_mc}")
                check(live_dm == ["0.45 @ 1.6px", "0.75 @ 1.6px"] and live_mc == live_dm,
                      f"[{VW}] both branch layers are still equal at 0.45/0.75 @ 1.6px",
                      f"dm {live_dm} / mc {live_mc}")
                check(any(k.startswith("0.14") for k in flow["mc"]),
                      f"[{VW}] STATE 0.14 (module with no current result) unchanged")
                check(any(k.startswith("0.12") for k in flow["dm"]),
                      f"[{VW}] STATE 0.12 (document not uploaded) unchanged")
                check(flow["term"] == {"at-centre|0.55|false|true": 1, "short|0.30|true|false": 4},
                      f"[{VW}] the category->status terminations are unchanged",
                      str(flow["term"]))
                H = flow["viewBox"][3] if len(flow["viewBox"]) == 4 else 0
                spans = [flow[n] for n in ("doc", "mod", "cat") if flow[n].get("n")]
                tops = [s["top"] for s in spans]; bots = [s["bottom"] for s in spans]
                print(f"    frame height {H}; column tops {tops}; bottoms {bots}")
                check(max(bots) >= H - 120,
                      f"[{VW}] the columns still reach the bottom of the frame", str(bots))
                check(max(bots) - min(bots) <= 2 and max(tops) - min(tops) <= 2,
                      f"[{VW}] all three columns still span the same vertical extent",
                      f"{tops} {bots}")

            # ---------------------------------------------------------------- GOAL FOUR
            net = page.evaluate("""async () => {
                const body = document.querySelector('#body-d-projnet');
                if (body) body.style.display = '';
                document.dispatchEvent(new CustomEvent('lin:section-opened',
                                                       {detail: {id: 'd-projnet'}}));
                for (let i = 0; i < 80; i++) {
                  if (document.querySelector('#body-d-projnet svg, #body-d-projnet canvas')) break;
                  await new Promise(r => setTimeout(r, 250));
                }
                await new Promise(r => setTimeout(r, 1800));
                const host = document.querySelector('#body-d-projnet');
                if (!host) return {error: 'no #body-d-projnet'};
                const svg = host.querySelector('svg');
                const canvas = host.querySelector('canvas');
                const txt = host.innerText || '';
                const tally = (a) => a.reduce((m,k)=>(m[k]=(m[k]||0)+1,m),{});
                const stack = [];
                let el = svg || canvas || host;
                while (el && el !== document.documentElement) {
                  const cs = getComputedStyle(el);
                  stack.push({tag: el.tagName.toLowerCase(),
                              cls: (el.getAttribute('class')||'').slice(0,40),
                              bg: cs.backgroundColor,
                              surface: cs.getPropertyValue('--surface').trim(),
                              pageBg: cs.getPropertyValue('--page-bg').trim()});
                  el = el.parentElement;
                }
                return {
                  hasSvg: !!svg, hasCanvas: !!canvas,
                  rect: (svg||canvas||host).getBoundingClientRect
                        ? (() => {const r=(svg||canvas||host).getBoundingClientRect();
                                  return {w: Math.round(r.width), h: Math.round(r.height)};})()
                        : null,
                  planets: svg ? svg.querySelectorAll('[data-kind="planet"],[data-node="category"],[data-category]').length : 0,
                  moons: svg ? svg.querySelectorAll('[data-kind="moon"],[data-node="module"],[data-module]').length : 0,
                  states: svg ? tally(Array.from(svg.querySelectorAll('[data-state]'))
                                .map(e=>e.getAttribute('data-state'))) : {},
                  sun: svg ? (() => {const s = svg.querySelector('[data-kind="sun"],[data-node="status"]');
                                     return s ? {lit: s.getAttribute('data-lit'),
                                                 status: s.getAttribute('data-status')} : null;})() : null,
                  text: txt.slice(0, 900),
                  stack: stack,
                  svgRects: svg ? Array.from(svg.querySelectorAll(':scope > rect'))
                      .map(r => r.getAttribute('fill')) : []
                };
            }""")
            print()
            print(f"  ---- SIGNAL NETWORK at {VW}px ----")
            print(f"    {json.dumps({k:v for k,v in net.items() if k != 'text'})[:1200]}")
            for st in (net.get("stack") or []):
                print(f"      netstack {st['tag']:8s} .{st['cls']:30s} bg={st['bg']} "
                      f"--surface={st.get('surface')} --page-bg={st.get('pageBg')}")
            print("    text: " + (net.get("text") or "")[:600].replace("\n", " | "))
            check(bool(net.get("hasSvg") or net.get("hasCanvas")),
                  f"[{VW}] the Signal Network draws something on the owner's own route",
                  str(net)[:200])
            page.close()
        browser.close()
finally:
    pass

print()
print("=" * 90)
print("THE FIVE DISPOSITIONS AS READ BACK FROM THE AUDIT RECORD (through the page)")
print("=" * 90)
for k, v in READ_BACK.items():
    print(f"  {k:38s} {v}")

# THE AUDIT RECORD, READ THROUGH THE REAL ROUTE, ONE MORE TIME AND SERVER-SIDE.
back = post({"action": "projectdecisions", "session_token": PM, "id": D})
print()
print("THE AUDIT RECORD, READ BACK THROUGH `projectdecisions`:")
for r in (back.get("decisions") or []):
    print(f"  {r['recorded_at']}  {r['disposition']:38s} period={r['period']} "
          f"posture={r['posture']} rationale={(r['rationale'] or '')[:60]!r}")
codes = {r["disposition"] for r in (back.get("decisions") or [])}
check(codes == {c for c, _ in EXPECTED_DISPOSITIONS},
      "all five dispositions, accept included, are in the audit record", str(sorted(codes)))
check(all(r["period"] is not None and r["recorded_at"] and r["rationale"]
          for r in (back.get("decisions") or [])),
      "every recorded row carries its period, its timestamp and its rationale")
check(all(("posture" in r) for r in (back.get("decisions") or [])),
      "and the posture it was recorded against")

print()
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
