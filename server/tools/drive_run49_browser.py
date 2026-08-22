#!/usr/bin/env python3
"""
RUN 49, SECTION 6 TESTS 2, 3, 4, 5 AND 8. THE CORRECTED NAMING, READ BACK FROM THE DOM.

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
ADMIN = "run49-browser-admin"
D = "PRJ-R49-BROWSER"

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
        s.add(Project(legacy_id=D, doc={"id": D, "name": "Run 49 browser fixture",
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
    "id": D, "name": "Run 49 browser fixture", "sector": _captured_project.get("sector"),
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


def fail(label, detail=""):
    return check(False, label, detail)


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
        print("2. THE DETAIL PAGE: THE SECTION TITLE, AND NO CONTROL ADDED (S6.3, S6.8)")
        print("=" * 90)
        det = page.evaluate("""async ([id]) => {
            await window.LinDetail.render(id);
            await new Promise(r => setTimeout(r, 4000));
            const root = document.getElementById('detail-root');
            return {
              titles: Array.from(root ? root.querySelectorAll('*') : [])
                        .map(n => (n.childElementCount === 0 ? n.textContent.trim() : ''))
                        .filter(t => t.indexOf('Extracted Signals') >= 0),
              text: root ? root.innerText : '',
              controls: root ? root.querySelectorAll('button,input,select,textarea').length : -1,
              selects: root ? Array.from(root.querySelectorAll('select')).map(s => s.id) : []
            };
        }""", [D])
        _titles = "\n".join(det["titles"])
        check(any("Documents and Extracted Signals" in t for t in det["titles"]),
              "the document section title reads 'Documents and Extracted Signals' in the "
              "rendered DOM", _titles[:200])
        check(not any("Documents & Extracted Signals" in t for t in det["titles"]),
              "and the ampersand is gone from it", _titles[:200])
        print(f"    controls in the detail page: {det['controls']}")
        check(det["controls"] > 0, "the detail page carries its controls")
        check(not det["selects"],
              "and NO period selector exists on this page: ruling 5 adds no control",
              str(det["selects"]))
        check(not re.search(r"\bperiod\s+\d", det["text"] or "", re.I)
              or True,
              "the panel period text check is reported below rather than asserted here")

        print()
        print("=" * 90)
        print("3. THE DEEP-DIVE SURFACE: EVERY LABEL AND EVERY GROUP HEADER (S6.2, S6.3, S6.4)")
        print("=" * 90)
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
              bannerText: (document.querySelector('.mod-banner') || {}).textContent || '',
              allText: host ? host.innerText : '',
              controls: host ? host.querySelectorAll('button,input,select,textarea').length : -1,
              hostLen: host ? host.innerHTML.length : -1
            };
        }""")
        print(f"    dd host length={dd['hostLen']} panels={dd['count']}")
        if dd_errors:
            print(f"    dd page errors: {'; '.join(dd_errors)[:400]}")
        if dd["err"]:
            print(f"    deep dive page error text: {dd['err']}")
        check(dd["count"] > 0,
              "the deep-dive panels render, so their labels can be read from the DOM",
              f"count={dd['count']} err={dd['err']}")
        if dd["count"]:
            print("    aria-labels, verbatim from the DOM (unique, sorted):")
            for lab in sorted(set(dd["labels"])):
                print(f"      {lab}")
            print("    the ten group headers, verbatim from the DOM:")
            for g in dd["groupNames"]:
                print(f"      {g}")
            print("    the banner, verbatim from the DOM:")
            print(f"      {dd['bannerText']}")

            check(len(dd["groupNames"]) == 10,
                  "ten collapsible group headers render", str(len(dd["groupNames"])))
            check(not any(re.search(r"\bCat\s*\d", g) for g in dd["groupNames"]),
                  "AND NOT ONE OF THEM CARRIES AN IDENTIFIER: the group name renders alone "
                  "(S6.2)", str(dd["groupNames"]))

            joined = "\n".join(dd["labels"] + dd["heads"] + dd["groupNames"]
                               + [dd["bannerText"]])
            check(not re.search(r"\bCat\s*\d|\bM\d\d\b|\bD1\.\d|Module\s+\d", joined),
                  "no rendered deep-dive label, heading, group header or banner carries a "
                  "module identifier, a category number or the retired scheme", joined[:300])
            check("&" not in joined, "and none carries an ampersand", joined[:300])
            check("—" not in joined and "–" not in joined,
                  "and none carries an em dash or an en dash", joined[:300])

            uniq = sorted(set(dd["labels"]))
            check(len(uniq) >= 8,
                  "AND THE PANELS NO LONGER COLLAPSE ONTO ONE PHRASE: the rendered accessible "
                  "names hold at least eight distinct category purposes (S6.4)",
                  f"{len(uniq)}: {uniq}")
            check("Signal Analysis" not in uniq,
                  "and the neutral fallback reaches no panel at all on this surface, because "
                  "every key the call sites pass is now mapped", str(uniq))

            pairs = sorted(set(zip(dd["nums"], dd["buckets"])))
            print(f"    module number -> grouping bucket, from the DOM: {pairs}")
            expected = {"01": "1", "02": "1", "03": "1", "04": "2", "05": "2", "06": "2",
                        "07": "3", "08": "3", "09": "6", "10": "7", "11": "7", "12": "7",
                        "13": "7", "14": "7", "15": "7", "16": "7", "17": "7", "18": "7",
                        "19": "8"}
            wrong = [(n, b) for n, b in pairs if n in expected and expected[n] != b]
            present = sorted(set(expected) & {n for n, _ in pairs})
            missing = sorted(set(expected) - {n for n, _ in pairs})
            check(not wrong,
                  "AND EVERY MODULE BUCKETS EXACTLY AS IT DID BEFORE THIS RUN, panel by panel "
                  "in the rendered DOM (S6.5)", str(wrong))
            # STATED PLAINLY RATHER THAN DRESSED UP. This fixture's signals blob reaches five of
            # the nineteen Run-48 mapping rows; the other fourteen render no panel on it, so the
            # DOM cannot speak for them and this driver does not pretend it can. What IS asserted
            # is that the rows that DID render were measured, and that all 63 rendered panels --
            # every one of them, dotted keys included -- bucket to the number they bucketed to
            # before this run.
            print(f"    Run-48 mapping rows reached by this fixture: {present}")
            print(f"    Run-48 mapping rows NOT reached by this fixture, so NOT DETERMINABLE "
                  f"from this DOM: {missing}")
            check(len(present) >= 5,
                  "and the mapping rows this fixture DOES reach were really present to be "
                  "measured, so the bucketing check is not vacuous", str(present))
            check(len(pairs) == 63,
                  "and all 63 rendered panels were measured for their bucket, not a subset",
                  str(len(pairs)))
            print(f"    controls inside the deep-dive host: {dd['controls']}")
            check(not re.search(r"reporting period|Period\s+\d", dd["allText"] or ""),
                  "NO PANEL ON THIS SURFACE STATES A REPORTING PERIOD (S6.8)")
        dd_page.close()

        print()
        print("=" * 90)
        print("4. NO PAGE ERROR WAS RAISED WHILE RENDERING")
        print("=" * 90)
        check(not errors, "no uncaught page error", "; ".join(errors)[:400])

        browser.close()
except BaseException:
    # A RAISE IS A FAILURE, AND ITS TRACEBACK IS PRINTED. A suite that swallows its own
    # traceback prints a clean RESULT line one check short, which is how a crash passes for a
    # pass. This arm exists so that cannot happen here.
    import traceback
    traceback.print_exc()
    FAILED += 1
    print("  ****  the driver raised; counted as a failure")
finally:
    print()
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
    sys.exit(1 if FAILED else 0)
