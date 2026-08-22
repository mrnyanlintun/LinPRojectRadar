#!/usr/bin/env python3
"""
RUN 47, SECTION 7. BROWSER VERIFICATION OF THE DISAGREEMENT TEXT, READ BACK FROM THE DOM.

Serves the REAL application from the repository root against a throwaway migrated SQLite
database, builds the Run 47 fixture through the REAL routes, drives the real Chromium headless
shell against it, renders the REAL Executive Brief and the REAL courses-of-action card, and
reads the disagreement text OUT OF THE RENDERED DOM rather than out of the source.

GUARDED FIRST: the DEng\\Demo tell. api.js / boot.js in document.scripts with zero `.page`
sections, against the 7 this application has. Checked before anything else is measured, and the
session's working directory is printed.

THIS DRIVER CHANGES NOTHING in the repository. Production Postgres is never contacted.

Run from a CLEAN directory (never the scratchpad root: a `queue.py` there shadows the standard
library and anyio then fails as an opaque HTTP 500):
    DATABASE_URL=sqlite:///<throwaway> SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python <repo>/server/tools/drive_run47_browser.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import pathlib
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


BAC = 5_874_620
PV_STATED = 824_370
PLANNED_PCT = 18.47
EV_STATED = 1_046_735
ACTUAL_PCT = 18.16
AC_STATED = 857_930
#: ONE PERIOD. Every document belongs to period 1, because `primeAndRefresh` (detail.js) reads
#: back `projectresults` for period 1 and that is the row every panel on the page then holds. A
#: fixture whose disagreement sat in a period the page never reads back would have proved
#: nothing about the page.
END = {1: "2026-03-31"}
ADMIN = "run47-browser-token"
D = "PRJ-R47-BROWSER"

DOCS = [
    ("contract", 1, "contract_value",
     {"original_contract_sum": BAC, "project_start_date": "2026-01-01",
      "project_end_date": "2027-06-30"}),
    ("tps1", 1, "time_phased_schedule",
     {"planned_value_to_date": PV_STATED, "planned_percent_complete": PLANNED_PCT,
      "data_date": END[1], "document_date": END[1]}),
    ("payapp1", 1, "pay_application",
     {"amount_paid_to_date": AC_STATED, "completed_to_date": EV_STATED,
      "percent_complete_verified": ACTUAL_PCT,
      "application_date": END[1], "document_date": END[1]}),
]


def doc_bytes(tag):
    return f"%PDF-1.4 RUN47BR {tag}\n".encode()


set_extractor_override(StubExtractor({
    hashlib.sha256(doc_bytes(t)).hexdigest(): (ty, ex) for t, _p, ty, ex in DOCS}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R47-BR-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == D)) is None:
        s.add(Project(legacy_id=D, doc={"id": D, "name": "Run 47 browser fixture",
                                        "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R47-BR-PM", "role": "Participant",
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

from playwright.sync_api import sync_playwright  # noqa: E402

try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=SHELL,
                                     args=["--use-gl=swiftshader", "--no-sandbox"])
        page = browser.new_page(viewport={"width": 1680, "height": 1600})
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
        print("=" * 90)
        print("0. THE APPLICATION UNDER TEST IS THE RIGHT ONE")
        print("=" * 90)
        base = page.evaluate("""() => ({
            pageSections: document.querySelectorAll('.page').length,
            demoTell: Array.from(document.scripts).map(s => s.src.split('/').pop())
                        .filter(s => s === 'api.js' || s === 'boot.js'),
            hasDetail: !!window.LinDetail, hasRecOptions: !!window.LinRecOptions
        })""")
        check(base["pageSections"] == 7,
              "the DOM carries 7 .page sections, which is what this application has",
              base["pageSections"])
        check(not base["demoTell"],
              "neither api.js nor boot.js is in document.scripts, so DEng\\Demo is not what is "
              "being served", str(base["demoTell"]))
        check(base["hasDetail"] and base["hasRecOptions"],
              "the real detail renderer and the real courses-of-action renderer are loaded")

        print()
        print("=" * 90)
        print("1. THE EXECUTIVE BRIEF, RENDERED BY THE REAL PAGE AND READ BACK FROM THE DOM")
        print("=" * 90)
        brief = page.evaluate("""async (id) => {
            await window.LinDetail.render(id);
            for (let i = 0; i < 60; i++) {
              const n = document.querySelector('.eb-consistency');
              if (n) break;
              await new Promise(r => setTimeout(r, 250));
            }
            const panel = document.querySelector('.eb-panel');
            const block = document.querySelector('.eb-consistency');
            return {
              panelPresent: !!panel,
              blockPresent: !!block,
              head: block ? (block.querySelector('.eb-consistency-head') || {}).textContent : null,
              items: block ? Array.from(block.querySelectorAll('.eb-consistency-item'))
                                  .map(n => n.textContent) : [],
              controlsInBlock: block ? block.querySelectorAll(
                  'button,input,select,textarea,a,[role=button]').length : -1,
              panelControls: panel ? panel.querySelectorAll('button,input,select,textarea').length : -1
            };
        }""", D)
        check(brief["panelPresent"], "the executive brief panel is in the DOM")
        check(brief["blockPresent"], "the disagreement block is in the rendered DOM")
        print("    HEAD, verbatim from the DOM:")
        print(f"      {brief['head']}")
        print("    ITEMS, verbatim from the DOM:")
        for it in brief["items"]:
            print(f"      {it}")
        check(len(brief["items"]) == 1,
              "exactly one disagreement is rendered, the planned value", str(len(brief["items"])))
        check(brief["controlsInBlock"] == 0,
              "the block contains NO user-facing control of any kind: it is text",
              str(brief["controlsInBlock"]))
        check(brief["panelControls"] == 1,
              "the brief panel still carries exactly the one control it carried before, the "
              "regenerate button: none added, none moved, none removed",
              str(brief["panelControls"]))

        print()
        print("=" * 90)
        print("2. THE RECOMMENDATION, RENDERED BY ITS OWN RENDERER FROM THE SERVED ROW")
        print("=" * 90)
        rec = page.evaluate("""async ([id, token, base]) => {
            const r = await fetch(base + '/exec', {method: 'POST',
              headers: {'Content-Type': 'text/plain'},
              body: JSON.stringify({action: 'projectresults', session_token: token,
                                    id: id, period: 1})});
            const j = await r.json();
            const spec = window.LinRecOptions.build(j.result);
            const host = document.createElement('div');
            host.id = 'r47-rec-host';
            document.body.appendChild(host);
            host.innerHTML = window.LinRecOptions.html(spec);
            const block = host.querySelector('#ro-consistency');
            const out = {
              served: (j.result && j.result.consistency_findings) || [],
              available: spec.available,
              blockPresent: !!block,
              heading: block ? (block.querySelector('.ro-option-title') || {}).textContent : null,
              lede: block ? (block.querySelector('.ro-what') || {}).textContent : null,
              items: block ? Array.from(block.querySelectorAll('.ro-consistency-item'))
                                  .map(n => n.textContent) : [],
              controlsInBlock: block ? block.querySelectorAll(
                  'button,input,select,textarea,a,[role=button]').length : -1
            };
            host.remove();
            return out;
        }""", [D, PM, BASE])
        check(len(rec["served"]) == 1,
              "the served row carries exactly one disagreement", str(len(rec["served"])))
        check(rec["blockPresent"],
              f"the disagreement block is in the rendered card (available={rec['available']})")
        print("    HEADING, verbatim from the DOM:")
        print(f"      {rec['heading']}")
        print("    LEDE, verbatim from the DOM:")
        print(f"      {rec['lede']}")
        print("    ITEMS, verbatim from the DOM:")
        for it in rec["items"]:
            print(f"      {it}")
        check(rec["controlsInBlock"] == 0,
              "the block contains NO user-facing control of any kind: it is text",
              str(rec["controlsInBlock"]))

        print()
        print("=" * 90)
        print("3. THE WORDING, MEASURED ON THE TEXT THAT WAS ACTUALLY RENDERED")
        print("=" * 90)
        import re
        rendered = [t for t in ([brief["head"]] + brief["items"]
                                + [rec["heading"], rec["lede"]] + rec["items"]) if t]
        check(len(rendered) >= 5, "there is rendered text to measure", str(len(rendered)))
        bad_id = re.compile(r"\bCat\s*\d|\b[A-D]\d\.\d|\bPH\.\d")
        joined = "\n".join(rendered)
        check(not bad_id.search(joined), "no module identifier and no number-scheme label")
        check("—" not in joined and "–" not in joined,
              "no em dash and no en dash in any rendered line")
        check("In period 1" in joined, "the rendered text carries the period")
        check("824,370" in joined and "1,085,042" in joined and "24.0 percent" in joined
              and "5,874,620" in joined and "18.47" in joined,
              "the rendered text names the stated figure, the implied figure, the difference, "
              "the budget at completion and the percentage")
        check("Time-phased Schedule" in joined,
              "and it names the document that stated both figures")
        check("1,066,830" not in joined and "1,046,735" not in joined,
              "the earned-value pair is NOT reported: it is inside tolerance",
              joined[:120])

        print()
        print("=" * 90)
        print("4. NO PAGE ERROR WAS RAISED WHILE RENDERING")
        print("=" * 90)
        check(not errors, "no uncaught page error", "; ".join(errors)[:300])

        browser.close()
finally:
    print()
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
    sys.exit(1 if FAILED else 0)
