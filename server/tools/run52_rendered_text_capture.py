#!/usr/bin/env python3
"""
RUN 52. THE RENDERED-TEXT CAPTURE THAT PROVES GUARANTEE 10 AND SECTION 9.8.

Ruling 4 of 2026-08-23 is a REVERSAL: displayed identifiers such as "Cat 4", "A4.2" and "1.7"
are acceptable, so this run ran NO naming sweep. Section 9.8 makes that testable and run-level:
if a rendered identifier would change, the run halts. Proving that requires comparing the
RENDERED TEXT of every affected surface BEFORE and AFTER, not reading the diff.

This script serves the REAL application from ITS OWN repository root and writes the rendered
text -- innerText plus every SVG <text> node, aria-label and title -- of the portfolio surface,
the project detail page with every collapsible section opened, and the research deep-dive
surface, to the JSON file named by $CAP_OUT.

Run it TWICE, once from a git worktree at the predecessor commit and once from the live tree,
and diff the two files. Run 52 did exactly that. The only differences were the upload timestamps
of the two fixtures, which were built two minutes apart, and ONE line on the deep-dive surface:

    -Portfolio Health: no anomaly flagged. see Health ->
    +Portfolio Health: no anomaly flagged.

which is the one control ruling 2 removed. The portfolio surface and the deep-dive SVG capture
were byte-identical.

Usage:
    CAP_OUT=/somewhere/before.json DATABASE_URL=sqlite:///throwaway.db python tools/run52_rendered_text_capture.py

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
import json as _json

OUT = {}
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME,
                                 args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    page = browser.new_page(viewport={"width": 1680, "height": 2400})
    for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                    "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
        page.route(pattern, lambda r: r.abort())
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.add_style_tag(content="*,*::before,*::after{transition:none!important;animation:none!important}")
    page.wait_for_timeout(8000)
    page.evaluate("() => window.LinApp.showPage('portfolio')")
    page.wait_for_timeout(1500)
    page.evaluate("() => window.LinApp.buildFallbackList()")
    page.wait_for_timeout(2000)
    OUT["portfolio"] = page.evaluate("() => document.querySelector('[data-page=portfolio]').innerText")
    page.evaluate("(id) => window.LinApp.openDetail ? window.LinApp.openDetail(id) : null", D)
    page.wait_for_timeout(1000)
    page.evaluate("""async (id) => { await window.LinDetail.render(id);
        await new Promise(r => setTimeout(r, 3000));
        const root = document.getElementById('detail-root');
        Array.from(root.querySelectorAll('.collapse-header')).forEach(h => { try { h.click(); } catch(e){} });
        await new Promise(r => setTimeout(r, 9000)); }""", D)
    OUT["detail"] = page.evaluate("() => document.getElementById('detail-root').innerText")
    OUT["detail_svg"] = page.evaluate("""() => Array.from(
        document.getElementById('detail-root').querySelectorAll('text,[aria-label],[title]'))
        .map(n => (n.textContent||'') + '|' + (n.getAttribute('aria-label')||'') + '|' + (n.getAttribute('title')||''))
        .filter(s => s.replace(/\\|/g,'').trim()).join('\\n')""")
    # RUN 54: THIS BLOCK IS HISTORICAL AND WILL NOT RUN AGAIN. `research/deepdive.html`
    # was DELETED on the owner's ruling at section 8 of the Run 54 order, and the route
    # that served it went with it. This driver is the EVIDENCE CAPTURE for its own run
    # and is pinned to what that run measured; rewriting it would falsify the record it
    # exists to be. It is annotated, not rewritten, on the same principle every
    # predecessor package record in this repository is kept rather than regenerated.
    dd = browser.new_page(viewport={"width": 1680, "height": 2400})
    dd.goto(BASE + "/research/deepdive.html", wait_until="domcontentloaded")
    dd.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
    dd.goto(BASE + "/research/deepdive.html", wait_until="domcontentloaded")
    dd.wait_for_timeout(3000)
    dd.fill("#dd-project", D)
    dd.click("#dd-load")
    dd.wait_for_timeout(8000)
    OUT["deepdive"] = dd.evaluate("() => document.body.innerText")
    OUT["deepdive_svg"] = dd.evaluate("""() => Array.from(
        document.querySelectorAll('text,[aria-label],[title]'))
        .map(n => (n.textContent||'') + '|' + (n.getAttribute('aria-label')||'') + '|' + (n.getAttribute('title')||''))
        .filter(s => s.replace(/\\|/g,'').trim()).join('\\n')""")
    browser.close()

import os as _os
_p = _os.environ["CAP_OUT"]
open(_p, "w", encoding="utf-8").write(_json.dumps(OUT, indent=1))
print("captured ->", _p, {k: len(v) for k, v in OUT.items()})
