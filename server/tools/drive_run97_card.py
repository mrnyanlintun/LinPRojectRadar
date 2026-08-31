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
ADMIN = "run97-browser-admin-" + _STAMP
D = "PRJ-R97-BROWSER-" + _STAMP

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
    return f"%PDF-1.4 RUN97BROWSER {_STAMP} {tag}\n".encode()


set_extractor_override(StubExtractor({
    hashlib.sha256(doc_bytes(_t)).hexdigest(): (_ty, _ex) for _t, _p, _ty, _ex in DOCS}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R97-BR-ADMIN-" + _STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == D)) is None:
        s.add(Project(legacy_id=D, doc={"id": D, "name": "Run 97 browser fixture",
                                        "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R97-BR-PM-" + _STAMP, "role": "Participant",
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
    "id": D, "name": "Run 97 browser fixture", "sector": _captured_project.get("sector"),
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
BLOCKS = ["Project posture", "Decision-support finding", "Why this finding was produced",
          "Forecast and baseline comparison", "Material drivers", "Evidence used",
          "Assessment limitations", "Decision question"]
FORBIDDEN_HEADINGS = ["Recommended action", "Conflict", "Authority", "Documentation required",
                      "Documentation Required"]
PLACEHOLDERS = ["not established", "Not established", "not available", "Not available"]

from playwright.sync_api import sync_playwright  # noqa: E402
from app.theme import THEMES  # noqa: E402

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
                // THE OWNER'S OWN SEQUENCE. The page is opened, the served result is allowed to
                // arrive, and only then is the Governance Decision section expanded -- which is
                // what a person does. Expanding it before the fetch returns measures the first
                // render against a row the server has not answered for yet.
                await window.LinDetail.render(id);
                for (let i = 0; i < 160; i++) {
                  const r = (window.LinResults && window.LinResults.rowFor)
                      ? window.LinResults.rowFor({id: id}) : null;
                  if (r && r.decision_brief) break;
                  await new Promise(r2 => setTimeout(r2, 250));
                }
                const body = document.querySelector('#body-d-decision');
                if (body) body.style.display = '';
                document.dispatchEvent(new CustomEvent('lin:section-opened',
                                                       {detail: {id: 'd-decision'}}));
                await new Promise(r => setTimeout(r, 2000));
                const panel = document.querySelector('#body-d-decision');
                const row = (window.LinResults && window.LinResults.rowFor)
                    ? window.LinResults.rowFor({id: id}) : null;
                return {
                  text: panel ? (panel.innerText || '') : null,
                  headings: panel ? Array.from(panel.querySelectorAll('h2,h3'))
                      .map(n => n.textContent.trim()) : [],
                  groups: panel ? Array.from(panel.querySelectorAll('.dc-group')).map(g => {
                      const h = g.querySelector('h3'); const r = g.getBoundingClientRect();
                      return {title: h ? h.textContent.trim() : '',
                              text: g.textContent.replace(h ? h.textContent : '', '').trim(),
                              w: Math.round(r.width), h: Math.round(r.height)};
                  }) : [],
                  rowHasBrief: !!(row && row.decision_brief),
                  briefKeys: (row && row.decision_brief)
                      ? Object.keys(row.decision_brief).filter(
                          k => row.decision_brief[k] !== null
                            && row.decision_brief[k] !== undefined
                            && row.decision_brief[k] !== "").sort() : [],
                  panelRect: panel ? (() => { const r = panel.getBoundingClientRect();
                      return {w: Math.round(r.width), h: Math.round(r.height)}; })() : null,
                  rowPeriod: row ? row.period : null
                };
            }""", D)
            print(f"  row period on the client: {out['rowPeriod']}")
            print(f"  rowFor(p).decision_brief present on the client: {out['rowHasBrief']}")
            print(f"  headings rendered in the panel: {out['headings']}")
            print()
            print("  ---- THE CARD AS THE PAGE RENDERS IT ----")
            for line in (out["text"] or "").splitlines():
                print("  | " + line)
            print("  ---- END ----")
            print()
            print(f"  blocks the composer filled on this row: {out['briefKeys']}")
            print(f"  panel rect: {out['panelRect']}")
            # THE BLOCK SET IS ASSERTED AGAINST WHAT THE COMPOSER FILLED, NOT AGAINST A LIST
            # WRITTEN HERE. `renderDecisionBrief` omits a block whose payload the composer
            # could not fill, so a fixed list of eight would fail on any honest row that has
            # nothing to say in one of them. What must be true is that EVERY block the composer
            # filled is on the page, which is the proposition that can actually fail.
            KEY_TO_BLOCK = {"posture": "Project posture",
                            "finding": "Decision-support finding",
                            "why": "Why this finding was produced",
                            "forecast": "Forecast and baseline comparison",
                            "drivers": "Material drivers",
                            "evidence": "Evidence used",
                            "limitations": "Assessment limitations",
                            "question": "Decision question"}
            for key, b in KEY_TO_BLOCK.items():
                if key in out["briefKeys"]:
                    check(b in out["headings"],
                          f"block the composer filled is rendered on the real page: {b}")
                else:
                    check(b not in out["headings"],
                          f"block the composer could not fill is absent, not empty: {b}")
            for f in FORBIDDEN_HEADINGS:
                check(f not in out["headings"], f"heading absent from the real page: {f}")
            for ph in PLACEHOLDERS:
                check(ph not in (out["text"] or ""), f"placeholder text absent: {ph!r}")
            check(len(out["groups"]) >= 6,
                  "the card renders as separate .dc-group blocks, not one run of flat text",
                  str(len(out["groups"])))
            check(not errors, "no page errors", str(errors[:3]))
            page.close()
        browser.close()
finally:
    pass

print()
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
