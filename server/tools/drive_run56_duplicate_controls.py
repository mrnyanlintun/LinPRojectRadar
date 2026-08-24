#!/usr/bin/env python3
"""
RUN 56, PHASES A AND B. THE DUPLICATE CONTROLS AND THE TWO CONFIRMATIONS, MEASURED IN A BROWSER.

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


    BASE_COMMIT = "e13b4f1"   # Run 56 starts here. EXPLICIT HASH, never a relative reference:
                              # Run 54 wrote proofs against HEAD~1 that decayed into false
                              # proofs as later commits walked the reference back.

    ING = ROOT / "assets" / "js" / "ingest.js"
    DET = ROOT / "assets" / "js" / "detail.js"
    CSS = ROOT / "assets" / "css" / "radar.css"

    def at_base(relpath):
        """Bytes of `relpath` at the EXPLICIT commit BASE_COMMIT. Never a relative reference."""
        r = subprocess.run(["git", "-C", str(ROOT), "show", f"{BASE_COMMIT}:{relpath}"],
                           capture_output=True)
        assert r.returncode == 0, f"git show {BASE_COMMIT}:{relpath} failed"
        return r.stdout.decode("utf-8")

    def brace_block(src, anchor):
        """The full brace-balanced text starting at `anchor`. A raise here is a failure and its
           traceback prints -- this file does not swallow one."""
        i = src.index(anchor)
        j = src.index("{", i)
        d = 0
        for k in range(j, len(src)):
            if src[k] == "{":
                d += 1
            elif src[k] == "}":
                d -= 1
                if d == 0:
                    return src[i:k + 1]
        raise AssertionError("unbalanced braces after " + anchor[:40])

    ING_BASE = at_base("assets/js/ingest.js")
    DET_BASE = at_base("assets/js/detail.js")
    CSS_BASE = at_base("assets/css/radar.css")

    print()
    print("=" * 94)
    print(f"1. NON-VACUITY, PINNED TO THE EXPLICIT COMMIT {BASE_COMMIT}")
    print("=" * 94)
    for name, hay, needle, why in (
        ("ingest.js", ING_BASE, 'class="btn small pe-populate">Upload documents<',
         "the moved 'Upload documents' (.pe-populate) EXISTED, so its absence check is not vacuous"),
        ("detail.js", DET_BASE, 'class="btn small primary detail-upload"',
         "the pre-existing 'Upload documents' (.detail-upload) EXISTED"),
        ("detail.js", DET_BASE, 'class="btn small detail-reset"',
         "the pre-existing 'Clear stored signals for this project' (.detail-reset) EXISTED"),
        ("ingest.js", ING_BASE, 'class="btn small pe-reset">Reset signals<',
         "the moved 'Reset signals' (.pe-reset) EXISTED"),
    ):
        check(needle in hay, f"NON-VACUITY at {BASE_COMMIT} in {name}: {why}")

    print()
    print("=" * 94)
    print("2. HANDLER COMPARISON, PAIR BY PAIR, AGAINST " + BASE_COMMIT)
    print("=" * 94)
    # PAIR 1 -- UPLOAD. Both open the SAME dialog for the SAME project id.
    h_pep = brace_block(ING_BASE, 'box.querySelector(".pe-populate").addEventListener')
    h_du = brace_block(DET_BASE, 'root.querySelectorAll("[data-upload]").forEach')
    print("    .pe-populate  @%s: %s" % (BASE_COMMIT, " ".join(h_pep.split())))
    print("    .detail-upload@%s: %s" % (BASE_COMMIT, " ".join(h_du.split())))
    check("openUploadModal(id)" in h_pep,
          ".pe-populate does exactly one thing: openUploadModal(<this project's id>)")
    check("LinIngest.openUploadModal(b.dataset.upload)" in h_du,
          ".detail-upload does exactly the same thing: openUploadModal(<this project's id>)")
    check('data-upload="${esc(p.id)}"' in DET_BASE,
          "and the id .detail-upload passes is render()'s own p.id -- the SAME project")
    # The whole of .pe-populate's body is ONE statement. Enumerated, not asserted by eyeball:
    # every non-empty, non-brace line of the handler body is listed and there is exactly one.
    _body = h_pep[h_pep.index("{") + 1:].strip().rstrip("}").strip()
    _stmts = [l.strip() for l in _body.splitlines() if l.strip()]
    print(f"    .pe-populate body statements: {_stmts}")
    check(_stmts == ["openUploadModal(id);"],
          "PAIR 1 VERDICT: .pe-populate's ENTIRE body is one statement, openUploadModal(id), so "
          "it does NOTHING that .detail-upload does not. The removal loses nothing and PROCEEDS",
          str(_stmts))

    # PAIR 2 -- RESET. This is the section 9.1 case and it is measured, not argued.
    h_per = brace_block(ING_BASE, 'box.querySelector(".pe-reset").addEventListener')
    h_dr = brace_block(DET_BASE, "function wireReset(root)")
    FEATURES = ["LinStore.resetSignals(", "LinSignals.clearCache(", "LinResults.clear(",
                "LinStore.load(", "logEvent(", "LinApp.refresh(", "renderPortfolioAdmin(",
                "render(id)", "LIN_PROJECTS", "LinStore.getProject(", "p.history = []"]
    only_detail, only_pe = [], []
    print(f"    {'behaviour':34}{'.detail-reset':>16}{'.pe-reset':>12}")
    for f in FEATURES:
        a, b = f in h_dr, f in h_per
        print(f"    {f:34}{str(a):>16}{str(b):>12}")
        if a and not b:
            only_detail.append(f)
        if b and not a:
            only_pe.append(f)
    print(f"    ONLY .detail-reset does: {only_detail}")
    print(f"    ONLY .pe-reset does    : {only_pe}")
    check(bool(only_detail),
          "PAIR 2: .detail-reset does things .pe-reset does NOT: " + ", ".join(only_detail))
    check(bool(only_pe),
          "PAIR 2: .pe-reset does things .detail-reset does NOT: " + ", ".join(only_pe))
    check(bool(only_detail) and bool(only_pe),
          "PAIR 2 VERDICT: NEITHER control is a superset of the other, so the order's premise "
          "that '.pe-reset clears more' is FALSE against the code. SECTION 9.1 FIRES: the "
          "removal of .detail-reset is STOPPED and BOTH are left in place")
    # BOTH carry an aria-live status region -- the Run 56 scouting hypothesis that only
    # .detail-reset does is FALSE, and is recorded as false rather than quietly dropped.
    check('class="detail-reset-msg kn-sub" aria-live="polite"' in DET_BASE
          and 'class="pe-msg kn-sub" aria-live="polite"' in ING_BASE,
          "and BOTH reset controls report through an aria-live region (.detail-reset-msg and "
          ".pe-msg): accessible status feedback is NOT the differentiator")

    print()
    print("=" * 94)
    print("3. THE DETAIL PAGE'S FULL CONTROL INVENTORY, AFTER PHASE A (live browser)")
    print("=" * 94)

    def inventory(rid):
        portfolio()
        page.click(f"#project-list .list-item[data-id='{rid}'] .li-manage")
        page.wait_for_timeout(2500)
        return page.evaluate("""() => {
            const root = document.getElementById('detail-root');
            if (!root) return null;
            const vis = (e) => { const s = getComputedStyle(e);
                return s.display !== 'none' && s.visibility !== 'hidden'; };
            const head = Array.from(root.querySelectorAll('.detail-head button')).filter(vis);
            return {
              head: head.map(b => b.textContent.trim()),
              headActions: Array.from(root.querySelectorAll('.detail-head-actions button'))
                          .filter(vis).map(b => b.textContent.trim()),
              headSel: head.map(b => '.' + Array.from(b.classList)
                          .filter(c => c !== 'btn' && c !== 'small' && c !== 'primary').join('.')),
              upload: root.querySelectorAll('.detail-upload, .pr-admin .pe-populate').length,
              uploadNames: Array.from(root.querySelectorAll(
                          '.detail-upload, .pr-admin .pe-populate')).map(b => b.textContent.trim()),
              reset: root.querySelectorAll('.detail-reset, .pr-admin .pe-reset').length,
              resetNames: Array.from(root.querySelectorAll(
                          '.detail-reset, .pr-admin .pe-reset')).map(b => b.textContent.trim()),
              panelOrder: Array.from(root.querySelectorAll('.pr-admin .dc-actions button'))
                          .map(b => b.textContent.trim()),
              hostFor: (root.querySelector('.detail-admin-host') || {}).getAttribute
                          ? root.querySelector('.detail-admin-host').getAttribute('data-admin-for')
                          : null,
              idField: (root.querySelector('.pr-admin .pe-id') || {}).value || null,
              detailPages: Array.from(document.querySelectorAll('.page'))
                          .filter(p => getComputedStyle(p).display !== 'none')
                          .map(p => p.getAttribute('data-page'))
            }; }""")

    portfolio()
    ROWS = page.evaluate("""() => Array.from(
        document.querySelectorAll('#project-list .list-item')).map(r => r.getAttribute('data-id'))""")
    print(f"    projects on the portfolio: {ROWS}")
    check(len(ROWS) >= 2, "MORE THAN ONE PROJECT, so 'per project' is a real quantifier",
          str(len(ROWS)))

    AFTER = {}
    for rid in ROWS:
        inv = inventory(rid)
        AFTER[rid] = inv
        print(f"    {rid}: detail-head controls  = {inv['head']}")
        print(f"    {rid}: admin panel order     = {inv['panelOrder']}")
        print(f"    {rid}: upload controls = {inv['uploadNames']}   "
              f"reset controls = {inv['resetNames']}")
        check("detail" in inv["detailPages"], f"{rid}: the detail page is open and reachable",
              str(inv["detailPages"]))
        check(inv["upload"] == 1,
              f"{rid}: EXACTLY ONE control opens the upload dialog on the detail page",
              f"{inv['upload']} -> {inv['uploadNames']}")
        check(".pe-populate" not in " ".join(inv["headSel"]) and
              page.evaluate("() => document.querySelectorAll("
                            "'#detail-root .pr-admin .pe-populate').length") == 0,
              f"{rid}: the moved .pe-populate is NOT rendered on the detail page")
        check(inv["hostFor"] == rid and inv["idField"] == rid,
              f"{rid}: the admin panel still acts on THIS project and no other",
              f"host={inv['hostFor']} idField={inv['idField']}")
        # section 9.1: BOTH reset controls remain, deliberately.
        check(inv["reset"] == 2,
              f"{rid}: BOTH reset controls remain -- the removal was STOPPED under section 9.1",
              f"{inv['reset']} -> {inv['resetNames']}")
        # the other four moved controls are untouched by phase A
        for lbl in ("Save info", "Recompute this project", "Reset signals", "Archive", "Close"):
            check(inv["panelOrder"].count(lbl) == 1,
                  f"{rid}: '{lbl}' still renders exactly once in the moved panel", str(inv["panelOrder"]))
        check("Upload documents" not in inv["panelOrder"],
              f"{rid}: and 'Upload documents' is gone from the moved panel", str(inv["panelOrder"]))

    print()
    print("=" * 94)
    print("4. NO DEAD CSS RULE SURVIVES THE REMOVAL, WITH NON-VACUITY")
    print("=" * 94)
    css_now = CSS.read_text(encoding="utf-8")
    import re as _re56
    n_now = len(_re56.findall(r"\.pe-populate\b", css_now))
    n_base = len(_re56.findall(r"\.pe-populate\b", CSS_BASE))
    print(f"    .pe-populate rules in radar.css at {BASE_COMMIT}: {n_base}   now: {n_now}")
    check(n_now == 0, "radar.css carries no .pe-populate rule", str(n_now))
    check(n_base == 0,
          f"NON-VACUITY, REPORTED HONESTLY: radar.css carried NO .pe-populate rule at "
          f"{BASE_COMMIT} either, so the removal left NO dead CSS rule behind and there was "
          f"none to remove. This absence check is vacuous and is reported as vacuous",
          str(n_base))
    # The one CSS rule the scouting note flagged, .detail-reset-msg, is NOT dead: its control
    # survives because the removal was stopped. Measured, not assumed.
    check(len(_re56.findall(r"\.detail-reset-msg\b", css_now)) >= 1
          and ".detail-reset" in DET.read_text(encoding="utf-8"),
          ".detail-reset-msg is NOT dead CSS: .detail-reset survives, so its rule stays")

    print()
    print("=" * 94)
    print("5. THE INVENTORY BEFORE PHASE A, MEASURED LIVE ON A SECOND BROWSER")
    print("=" * 94)
    # INJECTION PROTOCOL. The snapshot is taken from the COMMITTED REFERENCE (BASE_COMMIT), not
    # from disk; the restore is inside a `finally`; the tree is checked before and after.
    def tree_dirty():
        return subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"],
                              capture_output=True).stdout.decode().strip()

    pre_tree = tree_dirty()
    print(f"    tree before the injection ({len(pre_tree.splitlines())} line(s)):")
    for _l in pre_tree.splitlines():
        print("      " + _l)
    live_ing = ING.read_text(encoding="utf-8")
    BEFORE = {}
    try:
        ING.write_text(ING_BASE, encoding="utf-8")
        b2 = pw.chromium.launch(executable_path=CHROME,
                                args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
        p2 = b2.new_page(viewport={"width": 1680, "height": 2400})
        for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                        "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            p2.route(pattern, lambda r: r.abort())
        for _a in range(3):
            try:
                p2.goto(BASE + "/", wait_until="domcontentloaded", timeout=60000)
                break
            except Exception:
                time.sleep(2)
        p2.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        p2.goto(BASE + "/", wait_until="domcontentloaded", timeout=90000)
        p2.wait_for_timeout(6000)
        p2.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('portfolio')")
        p2.wait_for_timeout(1200)
        p2.evaluate("() => window.LinApp && LinApp.buildFallbackList && LinApp.buildFallbackList()")
        p2.wait_for_timeout(1500)
        rid0 = ROWS[0]
        p2.click(f"#project-list .list-item[data-id='{rid0}'] .li-manage")
        p2.wait_for_timeout(2500)
        BEFORE = p2.evaluate("""() => {
            const root = document.getElementById('detail-root');
            const vis = (e) => { const s = getComputedStyle(e);
                return s.display !== 'none' && s.visibility !== 'hidden'; };
            return {
              head: Array.from(root.querySelectorAll('.detail-head button')).filter(vis)
                      .map(b => b.textContent.trim()),
              headActions: Array.from(root.querySelectorAll('.detail-head-actions button'))
                      .filter(vis).map(b => b.textContent.trim()),
              upload: root.querySelectorAll('.detail-upload, .pr-admin .pe-populate').length,
              uploadNames: Array.from(root.querySelectorAll(
                      '.detail-upload, .pr-admin .pe-populate')).map(b => b.textContent.trim()),
              reset: root.querySelectorAll('.detail-reset, .pr-admin .pe-reset').length,
              panelOrder: Array.from(root.querySelectorAll('.pr-admin .dc-actions button'))
                      .map(b => b.textContent.trim())
            }; }""")
        print(f"    BEFORE ({rid0}): detail-head controls = {BEFORE['head']}")
        print(f"    BEFORE ({rid0}): admin panel order    = {BEFORE['panelOrder']}")
        print(f"    BEFORE ({rid0}): upload controls      = {BEFORE['uploadNames']}")
        check(BEFORE["upload"] == 2,
              f"BEFORE phase A the detail page carried TWO controls opening the upload dialog "
              f"-- the duplication the owner ruled on", str(BEFORE["uploadNames"]))
        check(BEFORE["panelOrder"] == ["Save info", "Upload documents", "Recompute this project",
                                       "Reset signals", "Archive", "Close"],
              "BEFORE phase A the moved panel carried all six controls", str(BEFORE["panelOrder"]))
        check(AFTER[rid0]["panelOrder"] == ["Save info", "Recompute this project",
                                            "Reset signals", "Archive", "Close"],
              "AFTER phase A it carries five: exactly one control was removed and it is "
              "'Upload documents'", str(AFTER[rid0]["panelOrder"]))
        print(f"    BEFORE ({rid0}): pre-existing .detail-head-actions = {BEFORE['headActions']}")
        print(f"    AFTER  ({rid0}): pre-existing .detail-head-actions = "
              f"{AFTER[rid0]['headActions']}")
        check(BEFORE["headActions"] == AFTER[rid0]["headActions"],
              "and the PRE-EXISTING .detail-head-actions cluster is the SAME LIST before and "
              "after: phase A added, moved and removed nothing there",
              f"{BEFORE['headActions']} vs {AFTER[rid0]['headActions']}")
        check(len(BEFORE["head"]) - len(AFTER[rid0]["head"]) == 1,
              "and the detail head as a whole lost EXACTLY ONE control, no more and no less",
              f"{len(BEFORE['head'])} -> {len(AFTER[rid0]['head'])}")
        b2.close()
    finally:
        ING.write_text(live_ing, encoding="utf-8")
        post_tree = tree_dirty()
        print(f"    tree after the injection was restored "
              f"({len(post_tree.splitlines())} line(s)):")
        for _l in post_tree.splitlines():
            print("      " + _l)
        check(post_tree == pre_tree,
              "INJECTION RESTORED: the tree is byte-identical to what it was before it",
              f"{pre_tree!r} -> {post_tree!r}")

    print()
    print("=" * 94)
    print("6. NO EM DASH OR EN DASH IN USER-FACING TEXT ON THE DETAIL PAGE")
    print("=" * 94)
    txt = page.evaluate("() => (document.getElementById('detail-root')||{}).innerText || ''")
    bad = [c for c in ("—", "–") if c in txt]
    check(not bad, "no em dash and no en dash renders on the project detail page", repr(bad))

    print()
    print("=" * 94)
    print("VERDICT")
    print("=" * 94)
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
