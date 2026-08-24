#!/usr/bin/env python3
"""
RUN 55, PHASE A. THE SIX ADMIN CONTROLS ON THE PROJECT DETAIL PAGE, MEASURED IN A BROWSER.

Run 54's navigation driver, taken forward rather than rewritten: the fixture, the server, the
browser launch and the DEng\\Demo tell are its code unchanged. What is new is sections 1-4:
the six controls are COUNTED on the detail page of each of three projects, each control's
`data-admin-for` host is read back so that "acts on that project and no other" is measured
rather than argued, and the absence of the controls before the move is pinned to an EXPLICIT
COMMIT HASH -- never to a relative reference, which is the defect Run 54 caught in itself.

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

    def _goto():
        # The environment throttles; a single 30s goto is not a reliable measurement instrument.
        # Three attempts, and the third failure is allowed to raise so the traceback prints.
        for _a in range(3):
            try:
                page.goto(BASE + "/", wait_until="domcontentloaded", timeout=60000)
                return
            except Exception as _e:
                print(f"    [goto retry {_a + 1}: {type(_e).__name__}]")
                time.sleep(2)
        page.goto(BASE + "/", wait_until="domcontentloaded", timeout=90000)

    def portfolio():
        _goto()
        page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        _goto()
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


    RUN55_PRE_MOVE_COMMIT = "d5f4243"     # the tip of run54-phases BEFORE phase A. EXPLICIT.
    SIX = [(".pe-save", "Save info"), (".pe-populate", "Upload documents"),
           (".pe-recompute", "Recompute this project"), (".pe-reset", "Reset signals"),
           (".pe-archive", "Archive"), (".pe-cancel", "Close")]

    print()
    print("=" * 94)
    print("1. NON-VACUITY, PINNED TO AN EXPLICIT COMMIT: the six existed before the move")
    print("=" * 94)
    _ing = subprocess.run(["git", "-C", str(ROOT), "show",
                           RUN55_PRE_MOVE_COMMIT + ":assets/js/ingest.js"], capture_output=True)
    _det = subprocess.run(["git", "-C", str(ROOT), "show",
                           RUN55_PRE_MOVE_COMMIT + ":assets/js/detail.js"], capture_output=True)
    check(_ing.returncode == 0, f"ingest.js reads at {RUN55_PRE_MOVE_COMMIT}")
    for sel, label in SIX:
        cls = sel[1:]
        check(cls.encode() in _ing.stdout and label.encode() in _ing.stdout,
              f"NON-VACUITY at {RUN55_PRE_MOVE_COMMIT}: '{label}' ({sel}) was built by ingest.js")
    check(b"detail-admin-host" not in _det.stdout,
          f"NON-VACUITY at {RUN55_PRE_MOVE_COMMIT}: detail.js had NO admin host -- the six were "
          f"NOT on the detail page before this run")
    _appjs = subprocess.run(["git", "-C", str(ROOT), "show",
                             RUN55_PRE_MOVE_COMMIT + ":assets/js/app.js"], capture_output=True)
    # NOT a bare substring test: Run 54 left an explanatory COMMENT in app.js naming
    # LinIngest.openInlineManage, so "the word is absent" is false and would be the wrong
    # question anyway. The question is whether a CALL SITE existed, so the comment lines are
    # dropped first and what remains is code.
    _code = b"\n".join(l for l in _appjs.stdout.split(b"\n")
                       if not l.strip().startswith(b"//"))
    check(b"LinIngest.openInlineManage(" not in _code,
          f"NON-VACUITY at {RUN55_PRE_MOVE_COMMIT}: app.js carried NO CALL SITE for "
          f"openInlineManage (comment lines excluded) -- the panel was unreachable, which is "
          f"why the move was ordered")
    check(b"function openInlineManage(id) {" in _ing.stdout,
          f"NON-VACUITY at {RUN55_PRE_MOVE_COMMIT}: the builder took ONE argument, so the panel "
          f"could only ever be appended to a portfolio row")

    print()
    print("=" * 94)
    print("2. THE SIX CONTROLS RENDER ON THE DETAIL PAGE -- PER PROJECT, PER SURFACE")
    print("=" * 94)
    portfolio()
    _inv = page.evaluate("""() => {
        const rows = Array.from(document.querySelectorAll('#project-list .list-item'));
        return { hosts: document.querySelectorAll('#project-list').length,
                 ids: rows.map(r => r.getAttribute('data-id')) }; }""")
    print(f"    hosts rendering a project list: {_inv['hosts']}   rows: {_inv['ids']}")
    ROWS = _inv["ids"]
    check(len(ROWS) >= 2, "MORE THAN ONE PROJECT, so 'per project' is a real quantifier",
          str(len(ROWS)))
    check(page.evaluate("() => document.querySelectorAll('#project-list .pr-admin').length") == 0,
          "the portfolio row renders NO admin panel: this is a MOVE, not a duplication")

    PLACEMENT = None
    for rid in ROWS:
        portfolio()
        page.click(f"#project-list .list-item[data-id='{rid}'] .li-manage")
        page.wait_for_timeout(2500)
        got = page.evaluate("""(sels) => {
            const root = document.getElementById('detail-root');
            const host = root && root.querySelector('.detail-admin-host');
            const panel = host && host.querySelector('.pr-admin');
            return {
              visible: Array.from(document.querySelectorAll('.page'))
                         .filter(p => getComputedStyle(p).display !== 'none')
                         .map(p => p.getAttribute('data-page')),
              hostCount: root ? root.querySelectorAll('.detail-admin-host').length : -1,
              hostFor: host ? host.getAttribute('data-admin-for') : null,
              parentClass: host && host.parentElement ? host.parentElement.className : null,
              panelParent: panel && panel.parentElement ? panel.parentElement.className : null,
              idField: panel ? (panel.querySelector('.pe-id') || {}).value : null,
              nameField: panel ? (panel.querySelector('.pe-name') || {}).value : null,
              order: panel ? Array.from(panel.querySelectorAll('.dc-actions button'))
                              .map(b => b.textContent.trim()) : [],
              found: sels.map(s => panel ? panel.querySelectorAll(s).length : 0),
              rowPanels: document.querySelectorAll('#project-list .pr-admin').length,
              headActions: root ? Array.from(
                 root.querySelectorAll('.detail-head-actions button')).map(
                 b => b.textContent.trim()) : []
            }; }""", [s for s, _ in SIX])
        print(f"    {rid}: host parent={got['parentClass']!r} data-admin-for={got['hostFor']!r} "
              f"panel parent={got['panelParent']!r}")
        print(f"    {rid}: control order in the panel = {got['order']}")
        print(f"    {rid}: detail-head-actions (pre-existing, untouched) = {got['headActions']}")
        check("detail" in got["visible"], f"{rid}: the detail page is open", str(got["visible"]))
        check(got["hostCount"] == 1, f"{rid}: exactly ONE admin host on the detail page",
              str(got["hostCount"]))
        for (sel, label), n in zip(SIX, got["found"]):
            # RUN 56, PHASE A. REVISED, NOT DELETED, AND NARROWED RATHER THAN WEAKENED. The
            # owner's Run 56 ruling removed the moved '.pe-populate' ("Upload documents") FROM
            # THE DETAIL PAGE ONLY, because the page already carried '.detail-upload' with the
            # same label calling the same function with the same project id. The expectation is
            # therefore EXACTLY ZERO for that one selector and EXACTLY ONE for the other five --
            # a count that is still asserted exactly, so a reappearance of the duplicate turns
            # this row red just as its disappearance used to.
            want = 0 if sel == ".pe-populate" else 1
            check(n == want,
                  f"{rid}: '{label}' ({sel}) renders exactly {want} time(s) on the detail page",
                  str(n))
        check(got["hostFor"] == rid,
              f"{rid}: the host is stamped with THIS project's id, not another's",
              str(got["hostFor"]))
        check(got["idField"] == rid,
              f"{rid}: ACTS ON THIS PROJECT -- the panel's project-number field reads back {rid}",
              str(got["idField"]))
        check(got["rowPanels"] == 0, f"{rid}: no admin panel remains on any portfolio row",
              str(got["rowPanels"]))
        if PLACEMENT is None:
            PLACEMENT = (got["parentClass"], got["panelParent"], got["order"],
                         got["headActions"])

    print()
    print("=" * 94)
    print("3. EACH CONTROL ACTS ON THE PROJECT BEING VIEWED AND NO OTHER")
    print("=" * 94)
    # Measured, not argued: every one of the six handlers is closed over the id the panel was
    # built with. The panel is rebuilt per navigation, so opening a DIFFERENT project and
    # reading the same fields back is a direct test that no id leaks between pages.
    for rid in ROWS:
        portfolio()
        page.click(f"#project-list .list-item[data-id='{rid}'] .li-manage")
        page.wait_for_timeout(2200)
        seen = page.evaluate("""() => {
            const p = document.querySelector('#detail-root .detail-admin-host .pr-admin');
            return p ? { id: p.querySelector('.pe-id').value,
                         upload: !!p.querySelector('.pe-populate'),
                         recompute: !!p.querySelector('.pe-recompute') } : null; }""")
        check(seen is not None and seen["id"] == rid,
              f"after navigating to {rid}, the panel carries {rid} and no other id",
              str(seen))
    # Upload documents: the control opens the upload dialog PRE-LOCKED to this project.
    portfolio()
    page.click(f"#project-list .list-item[data-id='{ROWS[0]}'] .li-manage")
    page.wait_for_timeout(2200)
    # RUN 56, PHASE A. REVISED, NOT DELETED. '.pe-populate' no longer renders on the detail
    # page; '.detail-upload' is the SURVIVING control of that pair and it is the one this row
    # now drives. The assertion below is unchanged: the dialog must open and must name THIS
    # project. The check got stricter in one respect -- it now exercises the control the owner
    # kept, which nothing previously drove in a browser.
    page.click("#detail-root .detail-head-actions .detail-upload")
    page.wait_for_timeout(1500)
    _up = page.evaluate("""(pid) => {
        const t = document.body.innerText || '';
        return { mentions: t.indexOf(pid) >= 0,
                 modals: document.querySelectorAll(
                     '.modal, .lin-modal, [role=dialog], .lin-modal-card, .modal-card').length,
                 openish: document.querySelectorAll('.pr-upload, .ig-drop, #upload-modal').length
               }; }""", ROWS[0])
    check(_up["modals"] + _up["openish"] >= 1,
          f"'Upload documents' on {ROWS[0]}'s detail page opens the upload dialog",
          str(_up))
    check(_up["mentions"],
          f"and the dialog it opens names {ROWS[0]} -- it is pre-locked to THIS project",
          str(_up))
    page.keyboard.press("Escape")
    page.wait_for_timeout(600)

    print()
    print("=" * 94)
    print("4. CLOSE REMOVES THE PANEL, AND MANAGE BRINGS IT BACK (no new control needed)")
    print("=" * 94)
    portfolio()
    page.click(f"#project-list .list-item[data-id='{ROWS[0]}'] .li-manage")
    page.wait_for_timeout(2200)
    before_close = page.evaluate(
        "() => document.querySelectorAll('#detail-root .pr-admin').length")
    page.click("#detail-root .detail-admin-host .pe-cancel")
    page.wait_for_timeout(800)
    after_close = page.evaluate(
        "() => document.querySelectorAll('#detail-root .pr-admin').length")
    check(before_close == 1 and after_close == 0,
          "Close removes the panel -- the same thing it did on the portfolio row",
          f"{before_close} -> {after_close}")
    portfolio()
    page.click(f"#project-list .list-item[data-id='{ROWS[0]}'] .li-manage")
    page.wait_for_timeout(2200)
    reopened = page.evaluate(
        "() => document.querySelectorAll('#detail-root .detail-admin-host .pr-admin').length")
    check(reopened == 1,
          "and Manage -- an EXISTING control, not a new one -- brings it back",
          str(reopened))

    print()
    print("=" * 94)
    print("5. THE DESTRUCTIVE CONTROLS: WHAT CONFIRMATION EACH CARRIES")
    print("=" * 94)
    # Reported, not changed. Read from the committed bytes at the pinned pre-move commit and
    # from the live file, so 'survived the move unchanged' is a comparison and not a claim.
    _pre = _ing.stdout.decode("utf-8", "replace")
    _now = (ROOT / "assets" / "js" / "ingest.js").read_text(encoding="utf-8")
    for name, sel in (("Archive", ".pe-archive"), ("Reset signals", ".pe-reset")):
        def _handler(text, s):
            i = text.find('box.querySelector("' + s + '").addEventListener')
            return text[i:i + 1400] if i >= 0 else ""
        h_pre, h_now = _handler(_pre, sel), _handler(_now, sel)
        conf_pre = any(k in h_pre for k in ("window.confirm", "confirm(", "LinUI.confirm"))
        conf_now = any(k in h_now for k in ("window.confirm", "confirm(", "LinUI.confirm"))
        print(f"    {name} ({sel}): confirmation before the move = "
              f"{'yes' if conf_pre else 'NONE'};  after = {'yes' if conf_now else 'NONE'}")
        check(bool(h_pre) and bool(h_now), f"{name}: the handler is present before and after")
        check(conf_pre == conf_now,
              f"{name}: the confirmation it carries SURVIVED THE MOVE UNCHANGED "
              f"(before={conf_pre}, after={conf_now})")
        check(h_pre == h_now,
              f"{name}: the handler body is BYTE-IDENTICAL to the pinned pre-move commit -- "
              f"this was a move, not a rewrite")

    print()
    print("=" * 94)
    print("6. NO .li-open RULE SURVIVES, AND THE MOVE ADDED NO CONTROL")
    print("=" * 94)
    _css = (ROOT / "assets" / "css" / "radar.css").read_text(encoding="utf-8")
    import re as _re
    _rules = _re.findall(r"\.li-open\b(?![^\n]*\*/)", _css)
    check(not _rules, "no .li-open selector remains in radar.css", str(len(_rules)))
    _css_pre = subprocess.run(["git", "-C", str(ROOT), "show",
                               RUN55_PRE_MOVE_COMMIT + ":assets/css/radar.css"],
                              capture_output=True).stdout.decode("utf-8", "replace")
    check(len(_re.findall(r"\.li-open\b", _css_pre)) >= 4,
          f"NON-VACUITY at {RUN55_PRE_MOVE_COMMIT}: radar.css DID carry .li-open rules",
          str(len(_re.findall(r"\.li-open\b", _css_pre))))
    portfolio()
    _row_controls = page.evaluate("""() => Array.from(
        document.querySelectorAll('#project-list .list-item')).map(
        r => Array.from(r.querySelectorAll('.li-actions button')).map(b => b.textContent.trim()))""")
    print(f"    portfolio row controls after the move: {_row_controls}")
    check(all(c == ["Manage"] for c in _row_controls),
          "the portfolio row still carries exactly one control, Manage -- unchanged by phase A",
          str(_row_controls))
    if PLACEMENT:
        print()
        print("    PLACEMENT OF RECORD:")
        print(f"      host parent element class : {PLACEMENT[0]}")
        print(f"      panel parent element class: {PLACEMENT[1]}")
        print(f"      control order in the panel : {PLACEMENT[2]}")
        print(f"      pre-existing head actions  : {PLACEMENT[3]}")

    print()
    print("=" * 94)
    print("VERDICT")
    print("=" * 94)
    print(f"  the six admin controls, per project detail page, over {len(ROWS)} projects "
          f"on 1 surface: {[lbl for _s, lbl in SIX]}")
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
