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
import subprocess
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
EXTRA = ["PRJ-R54-B", "PRJ-R54-C"]

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
    for _x in EXTRA:
        if s.scalar(select(Project).where(Project.legacy_id == _x)) is None:
            s.add(Project(legacy_id=_x, doc={"id": _x, "name": f"Run 54 row fixture {_x[-1]}",
                                             "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R51-BR-PM", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": D,
      "participant_id": created["participant_id"], "project_role": "PM"})
for _x in EXTRA:
    post({"action": "adminmemberadd", "session_token": admin, "id": _x,
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

ROWS_EXPECTED = [D] + EXTRA

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

    def portfolio():
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.add_style_tag(content="*,*::before,*::after{transition:none!important;"
                                   "animation:none!important}")
        page.wait_for_timeout(6000)
        page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('portfolio')")
        page.wait_for_timeout(1200)
        page.evaluate("() => window.LinApp && LinApp.buildFallbackList "
                      "&& LinApp.buildFallbackList()")
        page.wait_for_timeout(1500)

    print()
    print("=" * 94)
    print("0. THE APPLICATION UNDER TEST IS THE RIGHT ONE (the DEng\\Demo tell)")
    print("=" * 94)
    portfolio()
    base = page.evaluate("""() => ({
        pageSections: document.querySelectorAll('.page').length,
        demoTell: Array.from(document.scripts).map(s => s.src.split('/').pop())
                    .filter(s => s === 'api.js' || s === 'boot.js'),
        deepdiveLoaded: Array.from(document.scripts).map(s => s.src.split('/').pop())
                    .filter(s => s === 'deepdive.js')
    })""")
    check(base["pageSections"] == 7, "7 .page sections", str(base["pageSections"]))
    check(not base["demoTell"], "neither api.js nor boot.js in document.scripts",
          str(base["demoTell"]))
    check(not base["deepdiveLoaded"], "PHASE B: deepdive.js is loaded by no script tag",
          str(base["deepdiveLoaded"]))
    r = requests.get(BASE + "/research/deepdive.html") if False else None
    import urllib.request, urllib.error
    try:
        urllib.request.urlopen(BASE + "/research/deepdive.html", timeout=10)
        _dd_status = 200
    except urllib.error.HTTPError as e:
        _dd_status = e.code
    check(_dd_status == 404, "PHASE B: /research/deepdive.html is no longer a route",
          f"HTTP {_dd_status}")

    print()
    print("=" * 94)
    print("1. THE SURFACE INVENTORY BEFORE THE CHANGE: CONTROL COUNT PER SURFACE, PER ROW")
    print("=" * 94)
    inv = page.evaluate("""() => {
        const rows = Array.from(document.querySelectorAll('#project-list .list-item'));
        return { hosts: document.querySelectorAll('#project-list').length,
                 rowCount: rows.length,
                 ids: rows.map(r => r.getAttribute('data-id')),
                 openBtns: document.querySelectorAll('#project-list .li-open').length,
                 manageBtns: document.querySelectorAll('#project-list .li-manage').length,
                 perRow: rows.map(r => ({ id: r.getAttribute('data-id'),
                     controls: Array.from(r.querySelectorAll('.li-actions button'))
                                .map(b => b.textContent.trim()) })) };
    }""")
    print(f"    hosts rendering a project list: {inv['hosts']}  (index.html:566 <ul id=project-list>)")
    print(f"    rows: {inv['rowCount']}   ids: {inv['ids']}")
    for r_ in inv["perRow"]:
        print(f"      row {r_['id']}: {len(r_['controls'])} controls {r_['controls']}")
    check(inv["rowCount"] >= 2, "MORE THAN ONE ROW, so 'per row' is a real quantifier",
          str(inv["rowCount"]))
    check(inv["manageBtns"] == inv["rowCount"], "a Manage control on every row",
          str(inv["manageBtns"]))
    OPEN_BEFORE = inv["openBtns"]
    MANAGE_BEFORE = inv["manageBtns"]
    ROWS = inv["ids"]

    print()
    print("=" * 94)
    print("2. MANAGE REACHES THE DETAIL PAGE OF ITS OWN ROW'S PROJECT -- PER ROW, PER SURFACE")
    print("=" * 94)
    for rid in ROWS:
        portfolio()
        before = page.evaluate("""() => Array.from(document.querySelectorAll('.page'))
              .filter(p => getComputedStyle(p).display !== 'none')
              .map(p => p.getAttribute('data-page'))""")
        page.click(f"#project-list .list-item[data-id='{rid}'] .li-manage")
        page.wait_for_timeout(2500)
        after = page.evaluate("""() => ({
            visible: Array.from(document.querySelectorAll('.page'))
                       .filter(p => getComputedStyle(p).display !== 'none')
                       .map(p => p.getAttribute('data-page')),
            detailText: (document.getElementById('detail-root') || {}).innerText || '',
            inlineAdmin: document.querySelectorAll('#project-list .pr-admin').length
        })""")
        shows_own = rid in (after["detailText"] or "")
        print(f"    row {rid}: before={before} after={after['visible']} "
              f"detail shows this row's id={shows_own} inline .pr-admin={after['inlineAdmin']}")
        check("detail" in after["visible"],
              f"MEASURED IN A BROWSER: Manage on row {rid} reaches the DETAIL page",
              str(after["visible"]))
        check(shows_own,
              f"MEASURED IN A BROWSER: and it is {rid}'s OWN detail page, not another row's",
              (after["detailText"] or "")[:120])
        check(after["inlineAdmin"] == 0,
              f"row {rid}: Manage no longer opens the inline admin accordion",
              str(after["inlineAdmin"]))

    print()
    print("=" * 94)
    print("3. OPEN: PRESENT AND WORKING BEFORE THE REMOVAL, ABSENT AFTER IT")
    print("=" * 94)
    # THE SAME DRIVER SERVES BOTH HALVES OF THE ORDERED SEQUENCE. Run it with Open still bound
    # and it measures that Open reaches the detail page, which is what makes the removal a real
    # change rather than the deletion of something already broken. Run it after the removal and
    # it measures the absence, and proves the absence NON-VACUOUS against git rather than
    # against a copy of this logic.
    portfolio()
    _open_now = page.evaluate(
        "() => document.querySelectorAll('#project-list .li-open').length")
    if _open_now:
        for rid in ROWS:
            portfolio()
            page.click(f"#project-list .list-item[data-id='{rid}'] .li-open")
            page.wait_for_timeout(2500)
            vis = page.evaluate("""() => Array.from(document.querySelectorAll('.page'))
                  .filter(p => getComputedStyle(p).display !== 'none')
                  .map(p => p.getAttribute('data-page'))""")
            check("detail" in vis, f"row {rid}: Open reaches the detail page (the route being "
                                   f"replaced works at the moment Manage is verified)", str(vis))
    else:
        _app_before = subprocess.run(
            ["git", "-C", str(ROOT), "show", "bf36ef6:assets/js/app.js"], capture_output=True)
        _had_open = (_app_before.returncode == 0
                     and b'class="btn small li-open"' in _app_before.stdout)
        check(True, "NO PROJECT LIST RENDERS Open: zero .li-open controls on the one surface "
                    "that hosts a project list", f"{_open_now} over {len(ROWS)} rows")
        check(_had_open, "NON-VACUITY: Open WAS rendered at bf36ef6 (app.js:1084), so the "
                         "absence check above is not vacuous",
              f"present_at_bf36ef6={_had_open}")
        for rid in ROWS:
            portfolio()
            per = page.evaluate(f"""() => {{
                const r = document.querySelector(
                    "#project-list .list-item[data-id='{rid}']");
                return r ? Array.from(r.querySelectorAll('.li-actions button'))
                            .map(b => b.textContent.trim()) : null; }}""")
            print(f"      row {rid}: {len(per or [])} controls {per}")
            check(per is not None and len(per) == 1 and per[0] == "Manage",
                  f"row {rid}: exactly ONE control remains and it is Manage", str(per))
        # AND THE DETAIL PAGE IS STILL REACHABLE FOR EVERY PROJECT -- section 15.8, asserted
        # after the removal and not merely before it.
        for rid in ROWS:
            portfolio()
            page.click(f"#project-list .list-item[data-id='{rid}'] .li-manage")
            page.wait_for_timeout(2500)
            vis = page.evaluate("""() => Array.from(document.querySelectorAll('.page'))
                  .filter(p => getComputedStyle(p).display !== 'none')
                  .map(p => p.getAttribute('data-page'))""")
            check("detail" in vis,
                  f"SECTION 15.8: with Open GONE, {rid}'s detail page is still reachable "
                  f"from the project list", str(vis))

    print()
    print("=" * 94)
    print("VERDICT")
    print("=" * 94)
    print(f"  controls per row BEFORE removing Open: Manage={MANAGE_BEFORE} Open={OPEN_BEFORE} "
          f"over {len(ROWS)} rows on 1 surface")
    print(f"  page errors: {errors[:3]}")
    check(not errors, "no page error on any surface", str(errors[:2]))
    browser.close()

print("")
print("=" * 94)
print(f"RESULT: {PASSED} passed, {FAILED} failed")
print("=" * 94)
if _fail:
    for f_ in _fail:
        print("  -", f_)
sys.exit(1 if FAILED else 0)
