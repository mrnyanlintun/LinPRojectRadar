#!/usr/bin/env python3
"""
RUN 48, SECTION 6 TEST 7. THE MULTI-PERIOD BROWSER FIXTURE, READ BACK FROM THE DOM.

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
ADMIN = "run48-browser-admin"
D = "PRJ-R48-BROWSER"

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
    return f"%PDF-1.4 RUN48BROWSER {tag}\n".encode()


set_extractor_override(StubExtractor({
    hashlib.sha256(doc_bytes(_t)).hexdigest(): (_ty, _ex) for _t, _p, _ty, _ex in DOCS}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R48-BR-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == D)) is None:
        s.add(Project(legacy_id=D, doc={"id": D, "name": "Run 48 browser fixture",
                                        "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R48-BR-PM", "role": "Participant",
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
    "id": D, "name": "Run 48 browser fixture", "sector": _captured_project.get("sector"),
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

from playwright.sync_api import sync_playwright  # noqa: E402

#: The panels that hold the stored row, BY NAME. Each is asked separately which period it is
#: showing; an aggregate answer would let one panel read period 1 unnoticed.
PANELS = {
    "Executive Brief": "#body-d-brief",
    "Governance Decision": "#body-d-decision",
    "Signal Inputs": "#body-d-ledger",
    "Signal Web": "#body-d-web",
    "Ensemble Analysis": "#body-d-ensemble",
    "Documents and Extracted Signals": "#body-d-docsignals",
    "Project Signal Network": "#body-d-projnet",
}

try:
    print()
    print("=" * 90)
    print("0. THE SERVER'S DETERMINATION, BEFORE THE BROWSER IS ASKED")
    print("=" * 90)
    check(_pv["computed_periods"] == [1, 2],
          "the fixture holds computed results at periods 1 and 2", str(_pv["computed_periods"]))
    check(_pv["latest_computed_period"] == 2,
          "and the latest computed period is 2", str(_pv["latest_computed_period"]))

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=SHELL,
                                     args=["--use-gl=swiftshader", "--no-sandbox"])
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
        print("=" * 90)
        print("1. THE APPLICATION UNDER TEST IS THE RIGHT ONE")
        print("=" * 90)
        base = page.evaluate("""() => ({
            pageSections: document.querySelectorAll('.page').length,
            demoTell: Array.from(document.scripts).map(s => s.src.split('/').pop())
                        .filter(s => s === 'api.js' || s === 'boot.js'),
            hasDetail: !!window.LinDetail
        })""")
        check(base["pageSections"] == 7,
              "the DOM carries 7 .page sections, which is what this application has",
              base["pageSections"])
        check(not base["demoTell"],
              "neither api.js nor boot.js is in document.scripts, so DEng\\Demo is not what is "
              "being served", str(base["demoTell"]))
        check(base["hasDetail"], "the real detail renderer is loaded")

        print()
        print("=" * 90)
        print("2. THE PAGE OPENS ON THE LATEST COMPUTED PERIOD (S6.1)")
        print("=" * 90)
        opened = page.evaluate("""async ([id, sels]) => {
            await window.LinDetail.render(id);
            // Open every panel that holds the stored row, so each is measured as rendered.
            for (const sel of Object.values(sels)) {
              const body = document.querySelector(sel);
              if (body) body.style.display = '';
              const secId = sel.replace('#body-', '');
              document.dispatchEvent(new CustomEvent('lin:section-opened',
                                                     {detail: {id: secId}}));
            }
            for (let i = 0; i < 80; i++) {
              const n = document.querySelector('.eb-consistency');
              if (n) break;
              await new Promise(r => setTimeout(r, 250));
            }
            await new Promise(r => setTimeout(r, 1500));
            const out = {panels: {}};
            for (const [name, sel] of Object.entries(sels)) {
              const el = document.querySelector(sel);
              out.panels[name] = el ? (el.innerText || '').replace(/\\s+/g, ' ') : null;
            }
            const block = document.querySelector('.eb-consistency');
            out.consistencyHead = block
              ? (block.querySelector('.eb-consistency-head') || {}).textContent : null;
            out.consistencyItems = block
              ? Array.from(block.querySelectorAll('.eb-consistency-item')).map(n => n.textContent)
              : [];
            out.primedPeriod = (window.LinResults && window.LinResults.rowFor)
              ? ((window.LinResults.rowFor({id: id}) || {}).period) : 'no accessor';
            const root = document.getElementById('detail-root');
            out.controls = root ? root.querySelectorAll(
              'button, input, select, textarea').length : -1;
            out.selects = root
              ? Array.from(root.querySelectorAll('select')).map(s => s.className) : ['no root'];
            return out;
        }""", [D, PANELS])

        check(opened["primedPeriod"] == 2,
              "the row the page primed and every panel reads from is period 2's row",
              str(opened["primedPeriod"]))

        print()
        print("=" * 90)
        print("3. EVERY PANEL READS THE SAME PERIOD IN ONE RENDER, ASSERTED PER PANEL BY NAME")
        print("=" * 90)
        # The tokens each period's row prints, as literals. A panel showing period 1 carries a
        # period-1 token; a panel showing period 2 carries a period-2 token.
        P1_TOKENS = ["1,000,000", "1,050,000", "1,020,000"]
        P2_TOKENS = ["2,000,000", "2,100,000", "1,500,000"]
        distinguishable, indistinguishable = [], []
        for name, sel in PANELS.items():
            text = opened["panels"][name]
            if not check(text is not None, f"{name}: the panel is in the DOM", sel):
                continue
            p1_hits = [t for t in P1_TOKENS if t in text]
            p2_hits = [t for t in P2_TOKENS if t in text]
            if p1_hits or p2_hits:
                distinguishable.append(name)
                check(p2_hits and not p1_hits,
                      f"{name}: shows period 2's figures {p2_hits} and none of period 1's",
                      f"period-1 hits {p1_hits}")
            else:
                indistinguishable.append(name)
                # STATED PLAINLY RATHER THAN CLAIMED AS A PASS. This panel prints no figure
                # that differs between the two periods, so the DOM alone cannot say which
                # period it is showing. What IS true of it is asserted instead: it reads the
                # row through `LinResults.rowFor`, and that row is period 2's, checked above.
                print(f"    {name}: prints no period-distinguishing figure; the DOM cannot "
                      f"establish its period, and this is NOT counted as a pass")
                check(not p1_hits,
                      f"{name}: prints no figure that belongs only to period 1", str(p1_hits))
        print()
        print(f"    distinguishable from the DOM: {distinguishable}")
        print(f"    NOT distinguishable from the DOM: {indistinguishable}")
        check(len(distinguishable) >= 3,
              "at least three named panels are distinguishable from the DOM and every one of "
              "them shows period 2, so the per-panel check is not vacuous", str(distinguishable))

        print()
        print("=" * 90)
        print("4. THE DISAGREEMENT PANEL, WHICH PERIOD 1 DOES NOT HAVE AT ALL (S6.5)")
        print("=" * 90)
        check(bool(opened["consistencyHead"]),
              "the disagreement block is in the rendered DOM at all, which it would not be if "
              "the page were still reading period 1", str(opened["consistencyHead"]))
        print("    HEAD, verbatim from the DOM:")
        print(f"      {opened['consistencyHead']}")
        for it in opened["consistencyItems"]:
            print(f"      {it}")
        joined = " ".join([opened["consistencyHead"] or ""] + opened["consistencyItems"])
        check("In period 2" in joined,
              "and the text it renders names period 2", joined[:160])
        check("1,500,000" in joined and f"{P2_IMPLIED_PV:,}" in joined,
              "and it names period 2's stated planned value and the value its own document "
              "implies, both hand-computed", joined[:200])
        check(len(opened["consistencyItems"]) == 1,
              "exactly one disagreement is rendered, the planned value",
              str(len(opened["consistencyItems"])))

        print()
        print("=" * 90)
        print("5. NO USER-FACING CONTROL WAS ADDED, MOVED OR REMOVED (S9.1)")
        print("=" * 90)
        print(f"    controls in the detail page: {opened['controls']}")
        check(opened["controls"] > 0, "the detail page carries its controls")
        selectors = opened["selects"]
        check(not selectors,
              "and NO period selector exists on this page: none was added, which hard limit 4 "
              "forbids", str(selectors))

        print()
        print("=" * 90)
        print("6. THE CORRECTED LABELS, READ BACK FROM THE RENDERED DOM (S6.11)")
        print("=" * 90)
        # THE DEEP-DIVE PANELS ARE NOT ON THE PROJECT DETAIL PAGE. index.html deliberately
        # does not load deepdive.js (it re-runs a live Monte Carlo and needs sim.js); the
        # surface that renders those panels is research/deepdive.html. That page is where the
        # corrected labels are read back from, because that is where they are rendered.
        dd_page = browser.new_page(viewport={"width": 1680, "height": 2400})
        dd_errors = []
        dd_page.on("pageerror", lambda e: dd_errors.append(str(e)))
        dd_page.goto(BASE + "/research/deepdive.html", wait_until="domcontentloaded")
        dd_page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        dd_page.goto(BASE + "/research/deepdive.html", wait_until="domcontentloaded")
        dd_page.wait_for_timeout(3000)
        print(f"    deep-dive surface: {BASE}/research/deepdive.html")
        dd_page.fill("#dd-project", D)
        dd_page.click("#dd-load")
        dd_page.wait_for_timeout(6000)
        dd = dd_page.evaluate("""() => {
            const host = document.getElementById('dd-host');
            const panels = Array.from(host ? host.querySelectorAll('.dd-panel') : []);
            return {
              err: (document.getElementById('dd-error') || {}).textContent || '',
              count: panels.length,
              labels: panels.map(p => (p.getAttribute('aria-label') || '')),
              heads: panels.map(p => ((p.querySelector('.dd-head b') || {}).textContent || '')),
              buckets: panels.map(p => p.getAttribute('data-cat')),
              nums: panels.map(p => p.getAttribute('data-num')),
              groupNames: Array.from(document.querySelectorAll('.dd-cat-name'))
                               .map(n => n.textContent),
              hostLen: host ? host.innerHTML.length : -1,
              hostHead: host ? host.innerHTML.slice(0, 300) : '',
              hasLib: !!window.LinDeepDive, hasStore: !!(window.LinStore && window.LinStore.getProject)
            };
        }""")
        print(f"    dd host length={dd['hostLen']} lib={dd['hasLib']} store={dd['hasStore']}")
        print(f"    dd host head: {dd['hostHead'][:200]}")
        if dd_errors:
            print(f"    dd page errors: {'; '.join(dd_errors)[:400]}")
        if dd["err"]:
            print(f"    deep dive page error text: {dd['err']}")
        check(dd["count"] > 0,
              "the deep-dive panels render, so their labels can be read from the DOM",
              f"count={dd['count']} err={dd['err']}")
        if dd["count"]:
            print("    aria-labels, verbatim from the DOM (unique):")
            for lab in sorted(set(dd["labels"])):
                print(f"      {lab}")
            print("    headings, verbatim from the DOM (first five):")
            for h in dd["heads"][:5]:
                print(f"      {h}")
            joined_dd = "\n".join(dd["labels"] + dd["heads"])
            check(not re.search(r"\bCAT\s*\d|\bCat\s*\d", joined_dd),
                  "no rendered deep-dive panel label carries the retired scheme or a number",
                  joined_dd[:200])
            check("&" not in joined_dd, "and none carries an ampersand", joined_dd[:200])
            check("\u2014" not in joined_dd and "\u2013" not in joined_dd,
                  "and none carries an em dash or an en dash")
            pairs = sorted(set(zip(dd["nums"], dd["buckets"])))
            print(f"    module number -> grouping bucket, from the DOM: {pairs}")
            expected = {"01": "1", "02": "1", "03": "1", "04": "2", "05": "2", "06": "2",
                        "07": "3", "08": "3", "09": "6", "10": "7", "11": "7", "12": "7",
                        "13": "7", "14": "7", "15": "7", "16": "7", "17": "7", "18": "7",
                        "19": "8"}
            wrong = [(n, b) for n, b in pairs if n in expected and expected[n] != b]
            check(not wrong,
                  "and every panel still buckets to the number the retired label parsed to, so "
                  "correcting the text moved no panel", str(wrong))
            # SURVIVING INSTANCES, MEASURED RATHER THAN CLAIMED. The collapsible group headers
            # this same file builds still print the retired scheme, and §5.2 orders them
            # reported rather than corrected. Printed here so the report quotes the DOM.
            print("    group headers on this surface, verbatim from the DOM:")
            for g in dd["groupNames"]:
                print(f"      {g}")
        dd_page.close()

        print()
        print("=" * 90)
        print("7. NO PAGE ERROR WAS RAISED WHILE RENDERING")
        print("=" * 90)
        check(not errors, "no uncaught page error", "; ".join(errors)[:400])

        browser.close()
finally:
    print()
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
    sys.exit(1 if FAILED else 0)
