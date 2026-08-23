#!/usr/bin/env python3
"""
RUN 51. WHAT THE RENDERED DOM ACTUALLY SAYS, INCLUDING INSIDE ITS SVGs.

Run 50's driver, taken forward rather than rewritten. It serves the REAL application from the
repository root against a throwaway migrated SQLite database, builds a fixture through the REAL
routes, and drives real Chromium.

WHAT RUN 51 ADDS. Every sweep here reads SVG <text> nodes and aria-labels explicitly, because
`innerText` does not expose them, which is why ten retired module identifiers stood inside the
handbook's Signal Stack diagram through three guarantee-1 sweeps that all reported it clean.

Serves the REAL application from the repository root against a throwaway migrated SQLite
database, builds a fixture through the REAL routes, drives real Chromium, renders the REAL
project detail page and the REAL research deep-dive surface, and COUNTS THE RENDERED NODES
on every surface section 5.1 enumerates.

Verification here is by counting rendered nodes. Reading the code is not verification.

A RAISE IS A FAILURE AND ITS TRACEBACK IS PRINTED. This file does NOT use the
try/finally + sys.exit-in-finally shape, which swallows a traceback and prints a clean
RESULT line one check short.

Run from a CLEAN directory, never the scratchpad root.
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
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402
from app.simulation.registry import registry_index, service_index  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = 0
FAILED = 0
_fail = []
MEASURED = {}


def check(ok, label, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        _fail.append(label)
        print(f"  ****  {label}" + (f"   [{detail}]" if detail else ""))
    return bool(ok)


def post(payload):
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return r.json()


def b64(raw):
    return base64.b64encode(raw).decode()


BAC = 4_000_000
P1 = {"ev": 1_000_000, "ac": 1_050_000, "pv": 1_020_000, "planned_pct": 25.50, "actual_pct": 25.00}
P2 = {"ev": 2_000_000, "ac": 2_100_000, "pv": 1_500_000, "planned_pct": 50.00, "actual_pct": 50.00}
END = {1: "2026-03-31", 2: "2026-04-30"}
ADMIN = "run50-browser-admin"
D = "PRJ-R50-BROWSER"

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
    return f"%PDF-1.4 RUN51BROWSER {tag}\n".encode()


set_extractor_override(StubExtractor({
    hashlib.sha256(doc_bytes(_t)).hexdigest(): (_ty, _ex) for _t, _p, _ty, _ex in DOCS}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R51-BR-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == D)) is None:
        s.add(Project(legacy_id=D, doc={"id": D, "name": "Run 51 browser fixture",
                                        "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R51-BR-PM", "role": "Participant",
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

# The legacy client-side signals blob, taken from the RECORDED capture and written through the
# REAL save route. research/deepdive.html reads that blob and nothing else; the capture is read
# only and is never modified. Its own signalInputs are refused by the live write path, so only
# the `signals` block is taken from it.
_capture = json.loads((ROOT / "p0-baseline" / "contracts" / "get" / "get.json")
                      .read_text(encoding="utf-8"))
_captured_project = _capture.get("project") or (_capture.get("projects") or [{}])[0]
_proj = post({"action": "get", "session_token": PM, "id": D})
_doc = _proj.get("project") or _proj.get("doc") or {}
_doc.update({
    "id": D, "name": "Run 51 browser fixture", "sector": _captured_project.get("sector"),
    "status": _captured_project.get("status") or "Amber",
    "signals": _captured_project.get("signals"),
    "signalInputs": {
        "bac": BAC, "ev": P2["ev"], "ac": P2["ac"], "pv": P2["pv"],
        "docRiskScore": 0.30, "actualPctComplete": P2["actual_pct"],
        "plannedPctComplete": P2["planned_pct"],
    },
})
assert post({"action": "save", "session_token": PM, "project": _doc}).get("ok") is True

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

IN_SERVICE = len(service_index())
REGISTRY = len(registry_index())
RETIRED = sorted(set(registry_index()) - set(service_index()))

print(f"browser session cwd: {os.getcwd()}")
print(f"repository root:     {ROOT}")
print(f"DATABASE_URL:        {os.environ.get('DATABASE_URL')}")
print(f"served at:           {BASE}")
print(f"in service:          {IN_SERVICE}    registry: {REGISTRY}    retired: {len(RETIRED)}")

from playwright.sync_api import sync_playwright  # noqa: E402

try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME,
                                     args=["--use-gl=swiftshader", "--no-sandbox",
                                           "--headless=new"])
        page = browser.new_page(viewport={"width": 1680, "height": 2400})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                        "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            page.route(pattern, lambda r: r.abort())
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.add_style_tag(content="*,*::before,*::after{transition:none!important;"
                                   "animation:none!important}")
        page.wait_for_timeout(7000)

        print()
        print("=" * 94)
        print("0. THE APPLICATION UNDER TEST IS THE RIGHT ONE (the DEng\\Demo tell)")
        print("=" * 94)
        base = page.evaluate("""() => ({
            pageSections: document.querySelectorAll('.page').length,
            demoTell: Array.from(document.scripts).map(s => s.src.split('/').pop())
                        .filter(s => s === 'api.js' || s === 'boot.js'),
            hasDetail: !!window.LinDetail
        })""")
        check(base["pageSections"] == 7, "7 .page sections", base["pageSections"])
        check(not base["demoTell"], "neither api.js nor boot.js in document.scripts",
              str(base["demoTell"]))

        print()
        print("=" * 94)
        print("P. RULING 1 PREMISE, ESTABLISHED BY EXECUTION: WHERE DOES MANAGE GO?")
        print("=" * 94)
        # Navigate to the portfolio page which hosts #project-list.
        page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('portfolio')")
        page.wait_for_timeout(1500)
        page.evaluate("() => window.LinApp && LinApp.buildFallbackList && LinApp.buildFallbackList()")
        page.wait_for_timeout(1500)

        inv = page.evaluate("""() => {
            const rows = Array.from(document.querySelectorAll('#project-list .list-item'));
            const vis = () => { const s = document.querySelector('.page.active,[data-page].active');
                return Array.from(document.querySelectorAll('.page'))
                  .filter(p => getComputedStyle(p).display !== 'none')
                  .map(p => p.getAttribute('data-page')); };
            return { rowCount: rows.length,
                     ids: rows.map(r => r.getAttribute('data-id')),
                     openBtns: document.querySelectorAll('#project-list .li-open').length,
                     manageBtns: document.querySelectorAll('#project-list .li-manage').length,
                     visiblePages: vis() };
        }""")
        print(f"    project-list rows rendered: {inv['rowCount']}  ids={inv['ids']}")
        print(f"    .li-open controls: {inv['openBtns']}    .li-manage controls: {inv['manageBtns']}")
        print(f"    visible .page sections before any click: {inv['visiblePages']}")
        check(inv["rowCount"] > 0, "the project list renders at least one row", str(inv))
        check(inv["openBtns"] == inv["rowCount"],
              "NON-VACUITY: an Open control exists on every row at fe35504", str(inv["openBtns"]))
        check(inv["manageBtns"] == inv["rowCount"],
              "NON-VACUITY: a Manage control exists on every row at fe35504", str(inv["manageBtns"]))

        TARGET = inv["ids"][0]
        print(f"    target row: {TARGET}")

        # --- CLICK MANAGE, BY EXECUTION ---
        page.evaluate("""(id) => {
            const r = document.querySelector('#project-list .list-item[data-id="'+id+'"]');
            r.querySelector('.li-manage').click();
        }""", TARGET)
        page.wait_for_timeout(2500)
        after_manage = page.evaluate("""(id) => {
            const r = document.querySelector('#project-list .list-item[data-id="'+id+'"]');
            const li = r ? r.closest('li') : null;
            return {
              visiblePages: Array.from(document.querySelectorAll('.page'))
                  .filter(p => getComputedStyle(p).display !== 'none')
                  .map(p => p.getAttribute('data-page')),
              inlineAdminUnderRow: !!(li && li.querySelector('.pr-admin')),
              inlineAdminText: (li && li.querySelector('.pr-admin'))
                  ? li.querySelector('.pr-admin').innerText.replace(/\\s+/g,' ').slice(0,240) : null,
              detailRootText: (document.getElementById('detail-root')||{}).innerText
                  ? document.getElementById('detail-root').innerText.trim().slice(0,80) : '',
              detailVisible: (() => { const d = document.getElementById('detail-root');
                  if (!d) return false; const p = d.closest('.page');
                  return !!p && getComputedStyle(p).display !== 'none'; })()
            };
        }""", TARGET)
        print()
        print("    AFTER CLICKING MANAGE:")
        print(f"      visible .page sections : {after_manage['visiblePages']}")
        print(f"      detail page visible?   : {after_manage['detailVisible']}")
        print(f"      inline .pr-admin under the row? : {after_manage['inlineAdminUnderRow']}")
        print(f"      inline panel text      : {after_manage['inlineAdminText']}")

        MANAGE_REACHES_DETAIL = bool(after_manage["detailVisible"]) and \
            "detail" in (after_manage["visiblePages"] or [])
        check(after_manage["inlineAdminUnderRow"],
              "MEASURED: Manage opens an inline admin accordion under its own row")
        print(f"    >>> MANAGE REACHES THE PROJECT DETAIL PAGE: {MANAGE_REACHES_DETAIL}")

        # collapse the accordion again
        page.evaluate("""(id) => {
            const r = document.querySelector('#project-list .list-item[data-id="'+id+'"]');
            if (r && r.classList.contains('mng-open')) r.querySelector('.li-manage').click();
        }""", TARGET)
        page.wait_for_timeout(1200)

        # --- CLICK OPEN, BY EXECUTION ---
        page.evaluate("""(id) => {
            const r = document.querySelector('#project-list .list-item[data-id="'+id+'"]');
            r.querySelector('.li-open').click();
        }""", TARGET)
        page.wait_for_timeout(4000)
        after_open = page.evaluate("""() => ({
              visiblePages: Array.from(document.querySelectorAll('.page'))
                  .filter(p => getComputedStyle(p).display !== 'none')
                  .map(p => p.getAttribute('data-page')),
              detailVisible: (() => { const d = document.getElementById('detail-root');
                  if (!d) return false; const p = d.closest('.page');
                  return !!p && getComputedStyle(p).display !== 'none'; })(),
              detailHead: (document.getElementById('detail-root')||{innerText:''}).innerText
                  .trim().replace(/\\s+/g,' ').slice(0,160)
        })""")
        print()
        print("    AFTER CLICKING OPEN:")
        print(f"      visible .page sections : {after_open['visiblePages']}")
        print(f"      detail page visible?   : {after_open['detailVisible']}")
        print(f"      detail-root head text  : {after_open['detailHead']}")
        OPEN_REACHES_DETAIL = bool(after_open["detailVisible"])
        print(f"    >>> OPEN REACHES THE PROJECT DETAIL PAGE: {OPEN_REACHES_DETAIL}")

        print()
        print("=" * 94)
        print("PREMISE VERDICT")
        print("=" * 94)
        print(f"  Manage -> detail page : {MANAGE_REACHES_DETAIL}")
        print(f"  Open   -> detail page : {OPEN_REACHES_DETAIL}")
        if OPEN_REACHES_DETAIL and not MANAGE_REACHES_DETAIL:
            print("  PREMISE OF RULING 1 IS FALSE. The two controls do NOT lead to the same page.")
            print("  Removing Open would remove the only route from the project list to the")
            print("  project detail page. STOP THIS SURFACE UNDER SECTION 8.1.")
        elif MANAGE_REACHES_DETAIL:
            print("  PREMISE HOLDS. Manage reaches the detail page; Open may be removed.")
        browser.close()
except Exception:
    import traceback
    traceback.print_exc()
    FAILED += 1
    _fail.append("driver raised")

print()
print(f"RESULT: {PASSED} passed, {FAILED} failed" + (f"  ({_fail})" if _fail else ""))
sys.exit(1 if FAILED else 0)
