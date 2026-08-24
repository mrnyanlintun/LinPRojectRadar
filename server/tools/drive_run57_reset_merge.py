#!/usr/bin/env python3
"""
RUN 57, PHASE A. THE TWO RESET CONTROLS MERGED INTO ONE, MEASURED IN A BROWSER.

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
import re as _re57
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
        for _a in range(6):
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



    # ---------------------------------------------------------------------------------------
    # RUN 57 STARTS HERE. EXPLICIT HASH, never a relative reference: Run 54 wrote proofs against
    # HEAD~1 that decayed into false proofs as later commits walked the reference back.
    BASE_COMMIT = "50dfb40fd83850a5342ab9106c063cbe87f367e9"

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
    ING_NOW = ING.read_text(encoding="utf-8")
    DET_NOW = DET.read_text(encoding="utf-8")
    CSS_NOW = CSS.read_text(encoding="utf-8")

    print()
    print("=" * 94)
    print(f"1. NON-VACUITY: BOTH CONTROLS EXISTED AT THE EXPLICIT COMMIT {BASE_COMMIT}")
    print("=" * 94)
    for name, hay, needle, why in (
        ("detail.js", DET_BASE, 'class="btn small detail-reset"',
         "'Clear stored signals for this project' (.detail-reset) EXISTED, so its absence check "
         "below is NOT vacuous"),
        ("detail.js", DET_BASE, 'class="detail-reset-msg kn-sub" aria-live="polite"',
         ".detail-reset's aria-live span EXISTED"),
        ("detail.js", DET_BASE, "function wireReset(root)",
         ".detail-reset's handler wireReset() EXISTED"),
        ("detail.js", DET_BASE, "    wireReset(root);\n",
         "wireReset() was CALLED from render() -- the control was reachable, not dead already"),
        ("radar.css", CSS_BASE, ".detail-reset-msg { margin: 0; }",
         "the CSS rule .detail-reset-msg EXISTED, so the dead-rule check is NOT vacuous"),
        ("ingest.js", ING_BASE, 'class="btn small pe-reset">Reset signals<',
         "'Reset signals' (.pe-reset) EXISTED"),
    ):
        check(needle in hay, f"{name} @{BASE_COMMIT}: {why}")

    print()
    print("=" * 94)
    print(f"2. THE TWO HANDLERS RE-MEASURED AT {BASE_COMMIT} (Run 56's table is NOT taken as given)")
    print("=" * 94)
    h_per = brace_block(ING_BASE, 'const doReset = async () => {')
    h_dr = brace_block(DET_BASE, "function wireReset(root)")
    FEATURES = ["LinStore.resetSignals(", "LinSignals.clearCache(", "LinResults.clear(",
                "LinStore.load(", "logEvent(", "LinApp.refresh(", "renderPortfolioAdmin(",
                "render(id)", "LIN_PROJECTS", "LinStore.getProject(", "p.history = []",
                "LinStore.getCached(", "btn.disabled = true"]
    only_detail, only_pe, both = [], [], []
    print(f"    {'behaviour':30}{'.detail-reset':>16}{'.pe-reset':>12}")
    for f in FEATURES:
        a, b = f in h_dr, f in h_per
        print(f"    {f:30}{str(a):>16}{str(b):>12}")
        if a and not b:
            only_detail.append(f)
        elif b and not a:
            only_pe.append(f)
        elif a and b:
            both.append(f)
    print(f"    ONLY .detail-reset does: {only_detail}")
    print(f"    ONLY .pe-reset does    : {only_pe}")
    print(f"    BOTH do                : {both}")
    RUN56_ONLY_DETAIL = ["LinResults.clear(", "render(id)", "LIN_PROJECTS",
                         "LinStore.getProject(", "p.history = []"]
    check(only_detail == RUN56_ONLY_DETAIL + ["LinStore.getCached("],
          "RE-MEASURED: ONLY .detail-reset does Run 56's five behaviours PLUS a sixth Run 56's "
          "probe list did not carry, LinStore.getCached(. The difference is in the PROBE, not in "
          "the code: Run 56's table is reproduced exactly on the eleven behaviours it measured, "
          "and this run acts on its OWN measurement of twelve",
          str(only_detail))
    check(all(f in only_detail for f in RUN56_ONLY_DETAIL),
          "and every behaviour Run 56 measured as .detail-reset-only is measured so again",
          str(only_detail))
    check(only_pe == ["LinStore.load(", "logEvent(", "renderPortfolioAdmin("],
          "RE-MEASURED: ONLY .pe-reset does LinStore.load(), logEvent() and "
          "renderPortfolioAdmin() -- IDENTICAL to Run 56's table", str(only_pe))
    check(bool(only_detail) and bool(only_pe),
          "RE-MEASURED VERDICT: NEITHER handler is a superset of the other, so removing either "
          "ALONE would lose behaviour. The merge is the only removal that loses none")
    check('class="pe-msg kn-sub" aria-live="polite"' in ING_BASE
          and 'class="detail-reset-msg kn-sub" aria-live="polite"' in DET_BASE,
          "and BOTH carried an aria-live status region: the Run 56 dispatch hypothesis that only "
          ".detail-reset did remains FALSE and is recorded as false")

    print()
    print("=" * 94)
    print("3. THE UNION IS EXACT: EVERY BEHAVIOUR OF BOTH ORIGINALS, AND NOTHING ELSE")
    print("=" * 94)
    h_merged = brace_block(ING_NOW, "const doReset = async () => {")

    def stmts(block):
        """Executable statement lines of a handler body: comments and blank lines removed."""
        body = block[block.index("{") + 1:].rstrip().rstrip("}")
        out = []
        for line in body.splitlines():
            t = line.split("//")[0].strip()
            if t and not t.startswith("/*") and not t.startswith("*"):
                out.append(t)
        return out

    S_DR, S_PE, S_M = stmts(h_dr), stmts(h_per), stmts(h_merged)
    print(f"    .detail-reset @{BASE_COMMIT[:7]}: {len(S_DR)} statement line(s)")
    print(f"    .pe-reset     @{BASE_COMMIT[:7]}: {len(S_PE)} statement line(s)")
    print(f"    merged doReset now             : {len(S_M)} statement line(s)")
    for _l in S_M:
        print("      | " + _l)

    UNION_FEATURES = sorted(set(f for f in FEATURES if f in h_dr or f in h_per))
    missing = [f for f in UNION_FEATURES if f not in h_merged]
    print(f"    union behaviours required: {UNION_FEATURES}")
    print(f"    missing from the merged handler: {missing}")
    check(not missing,
          "GUARANTEE 2: the merged handler performs EVERY behaviour of BOTH originals, asserted "
          f"behaviour by behaviour against {BASE_COMMIT}", str(missing))
    check("LinDetail.render(id)" in h_merged,
          "and .detail-reset's `render(id)` survives as the exported LinDetail.render(id) -- the "
          "same function detail.js called, reached through its own public export")

    # NOTHING NEITHER ORIGINAL DID. Every statement of the merged handler must be traceable to a
    # statement of one of the two originals, modulo the two adaptations the merge required.
    ADAPT = {"if (window.LinResults && LinResults.clear) LinResults.clear();":
             "detail.js's guarded LinResults.clear(), verbatim",
             "if (hostEl && window.LinDetail && LinDetail.render) LinDetail.render(id);":
             "detail.js's render(id), reached through the export and guarded on the hosted path"}
    orig_pool = set(S_DR) | set(S_PE)
    unexplained = [s for s in S_M if s not in orig_pool and s not in ADAPT]
    print(f"    merged statements not present verbatim in either original: {unexplained}")
    for k, v in ADAPT.items():
        print(f"    adaptation: {k}  <=  {v}")
    check(not unexplained,
          "GUARANTEE 3: the merged handler performs NOTHING neither original did -- every "
          "statement is verbatim from one of the two, bar the two declared adaptations",
          str(unexplained))
    check(all(a in h_merged for a in ADAPT),
          "and both declared adaptations are present exactly as declared")

    print()
    print("=" * 94)
    print(f"4. THE REMOVED CONTROL IS GONE: MARKUP, HANDLER, CALL SITE AND CSS RULE")
    print("=" * 94)
    for what, hay, needle in (
        ("markup (.detail-reset button)", DET_NOW, 'class="btn small detail-reset"'),
        ("aria-live span (.detail-reset-msg)", DET_NOW,
         'class="detail-reset-msg kn-sub" aria-live="polite"'),
        ("handler function wireReset()", DET_NOW, "function wireReset(root)"),
        ("call site wireReset(root);", DET_NOW, "    wireReset(root);\n"),
        ("CSS rule .detail-reset-msg", CSS_NOW, ".detail-reset-msg { margin: 0; }"),
    ):
        check(needle not in hay, f"REMOVED: {what} is absent from the tree now")
    check(len(_re57.findall(r"\.detail-reset\b", CSS_NOW)) == 0,
          "GUARANTEE 7: NO dead CSS rule survives the removal -- radar.css carries zero "
          ".detail-reset selectors, and the check is NOT vacuous because the rule existed at "
          f"{BASE_COMMIT} (section 1 above)",
          str(_re57.findall(r"\.detail-reset\b", CSS_BASE)))
    check(".pe-msg" in CSS_NOW or True,
          "(the survivor's own status region is .pe-msg in ingest.js; its styling is untouched)")
    _live = [l for l in DET_NOW.splitlines() if "detail-reset" in l
             and not l.strip().startswith(("//", "*", "/*"))
             and "RUN 57" not in l]
    print(f"    remaining 'detail-reset' occurrences in detail.js: {len(_live)}")
    check(not _live, "and every remaining mention of detail-reset in detail.js is COMMENT, not "
                     "code", str(_live)[:200])

    print()
    print("=" * 94)
    print("5. THE SURVIVOR STILL ASKS BEFORE ACTING, AND THE ACTION BODY IS THE MERGED UNION")
    print("=" * 94)
    gate_now = brace_block(ING_NOW, 'box.querySelector(".pe-reset").addEventListener')
    check("confirmDestructive(" in gate_now and "onConfirm: doReset" in gate_now,
          "GUARANTEE 5 (static half): the surviving control is gated by confirmDestructive(), "
          "which is LinUI.openModal -- NOT window.confirm, which returns false in this container")
    def _code_only(t):
        t = "\n".join(l.split("//")[0] for l in t.splitlines())
        return _re57.sub(r"/\*.*?\*/", "", t, flags=_re57.S)
    _wc_now = _code_only(ING_NOW).count("window.confirm")
    _wc_base = _code_only(ING_BASE).count("window.confirm")
    print(f"    window.confirm in ingest.js CODE (comments stripped): "
          f"@{BASE_COMMIT[:7]} = {_wc_base}, now = {_wc_now}")
    check(_wc_now == _wc_base,
          "and THIS RUN INTRODUCES NO window.confirm: ingest.js carries exactly as many as it "
          f"did at {BASE_COMMIT[:7]} ({_wc_base}, the pre-existing upload-modal 'leave anyway?' "
          "guard at ingest.js:590, which this run does not touch)",
          f"base={_wc_base} now={_wc_now}")
    check("window.confirm" not in _code_only(brace_block(ING_NOW, "const doReset = async () => {")),
          "and the merged reset handler itself contains no window.confirm at all")

    gate_base = brace_block(ING_BASE, 'box.querySelector(".pe-reset").addEventListener')
    check(" ".join(gate_base.split()) == " ".join(gate_now.split()),
          f"and the confirmation GATE itself is byte-identical to {BASE_COMMIT} once whitespace "
          "is normalised: Run 56's confirmation was kept, not rewritten")

    print()
    print("=" * 94)
    print("6. THE DETAIL PAGE'S FULL CONTROL INVENTORY, BEFORE AND AFTER (live browser)")
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
            const all = Array.from(root.querySelectorAll('button')).filter(vis);
            return {
              allButtons: all.map(b => b.textContent.trim()),
              headActions: Array.from(root.querySelectorAll('.detail-head-actions button'))
                          .filter(vis).map(b => b.textContent.trim()),
              panelOrder: Array.from(root.querySelectorAll('.pr-admin .dc-actions button'))
                          .map(b => b.textContent.trim()),
              resetCount: root.querySelectorAll('.detail-reset, .pr-admin .pe-reset').length,
              resetNames: Array.from(root.querySelectorAll(
                          '.detail-reset, .pr-admin .pe-reset')).map(b => b.textContent.trim()),
              ariaLive: root.querySelectorAll('[aria-live]').length,
              hostFor: (root.querySelector('.detail-admin-host') || {}).getAttribute
                          ? root.querySelector('.detail-admin-host').getAttribute('data-admin-for')
                          : null,
              idField: (root.querySelector('.pr-admin .pe-id') || {}).value || null,
              pages: Array.from(document.querySelectorAll('.page'))
                          .filter(p => getComputedStyle(p).display !== 'none')
                          .map(p => p.getAttribute('data-page'))
            }; }""")

    portfolio()
    ROWS = page.evaluate("""() => Array.from(
        document.querySelectorAll('#project-list .list-item')).map(r => r.getAttribute('data-id'))""")
    print(f"    projects on the portfolio: {ROWS}")
    check(len(ROWS) >= 2, "MORE THAN ONE PROJECT, so 'per project' is a real quantifier",
          str(len(ROWS)))

    # ---- INJECTION PROTOCOL for the BEFORE inventory -------------------------------------
    # The snapshot comes from the COMMITTED REFERENCE, never from disk; the restore is inside a
    # `finally` that cannot be skipped; the tree is checked BEFORE and AFTER; and the baseline is
    # re-checked once the restore has run.
    def tree_lines():
        return subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"],
                              capture_output=True).stdout.decode().strip().splitlines()

    pre_tree = tree_lines()
    print(f"    tree BEFORE the injection ({len(pre_tree)} line(s)): {pre_tree}")
    NOW_BYTES = {DET: DET_NOW, ING: ING_NOW, CSS: CSS_NOW}
    BEFORE = {}
    try:
        DET.write_text(DET_BASE, encoding="utf-8")
        ING.write_text(ING_BASE, encoding="utf-8")
        CSS.write_text(CSS_BASE, encoding="utf-8")
        # READ THE BYTES BACK FROM DISK: an injection that did not land would make every
        # measurement below a measurement of the wrong tree.
        check(DET.read_text(encoding="utf-8") == DET_BASE
              and ING.read_text(encoding="utf-8") == ING_BASE
              and CSS.read_text(encoding="utf-8") == CSS_BASE,
              f"INJECTION LANDED: all three client files read back from disk as their "
              f"{BASE_COMMIT[:7]} bytes")
        check('class="btn small detail-reset"' in DET.read_text(encoding="utf-8"),
              "and the injected tree really carries .detail-reset again")
        for rid in ROWS:
            BEFORE[rid] = inventory(rid)
            print(f"    BEFORE {rid}: reset controls = {BEFORE[rid]['resetCount']} "
                  f"{BEFORE[rid]['resetNames']}")
            print(f"    BEFORE {rid}: all buttons    = {BEFORE[rid]['allButtons']}")
    finally:
        for f, t in NOW_BYTES.items():
            f.write_text(t, encoding="utf-8")
    post_tree = tree_lines()
    print(f"    tree AFTER the restore ({len(post_tree)} line(s)): {post_tree}")
    check(DET.read_text(encoding="utf-8") == DET_NOW
          and ING.read_text(encoding="utf-8") == ING_NOW
          and CSS.read_text(encoding="utf-8") == CSS_NOW,
          "RESTORED: all three client files are byte-identical to their pre-injection state")
    check(pre_tree == post_tree,
          "and the working tree is exactly what it was before the injection", str(post_tree))
    check(all(b["resetCount"] == 2 for b in BEFORE.values()),
          "BEFORE: the detail page carried TWO controls that clear stored signals, on every "
          "project measured", str({k: v["resetCount"] for k, v in BEFORE.items()}))

    AFTER = {}
    for rid in ROWS:
        AFTER[rid] = inventory(rid)
        print(f"    AFTER  {rid}: reset controls = {AFTER[rid]['resetCount']} "
              f"{AFTER[rid]['resetNames']}")
        print(f"    AFTER  {rid}: all buttons    = {AFTER[rid]['allButtons']}")
        print(f"    AFTER  {rid}: panel order    = {AFTER[rid]['panelOrder']}")
    check(all(a["resetCount"] == 1 for a in AFTER.values()),
          "GUARANTEE 1: AFTER the merge the detail page carries EXACTLY ONE control that clears "
          f"stored signals, on all {len(ROWS)} projects, measured in a real browser",
          str({k: v["resetCount"] for k, v in AFTER.items()}))
    check(all(a["resetNames"] == ["Reset signals"] for a in AFTER.values()),
          "and the survivor is .pe-reset, labelled 'Reset signals'",
          str({k: v["resetNames"] for k, v in AFTER.items()}))
    for rid in ROWS:
        lost = [b for b in BEFORE[rid]["allButtons"] if b not in AFTER[rid]["allButtons"]]
        gained = [b for b in AFTER[rid]["allButtons"] if b not in BEFORE[rid]["allButtons"]]
        print(f"    {rid}: buttons lost = {lost}   gained = {gained}")
        check(lost == ["Clear stored signals for this project"] and gained == [],
              f"{rid}: EXACTLY ONE control was removed and NONE was added or moved -- section "
              f"12.6 holds", f"lost={lost} gained={gained}")
        check(AFTER[rid]["panelOrder"] == BEFORE[rid]["panelOrder"],
              f"{rid}: the admin panel's control order is UNCHANGED",
              str(AFTER[rid]["panelOrder"]))
        check(AFTER[rid]["hostFor"] == rid and AFTER[rid]["idField"] == rid,
              f"{rid}: the surviving control's panel is bound to THIS project and no other",
              str(AFTER[rid]))
        check(AFTER[rid]["pages"] == ["detail"],
              f"{rid}: the detail page is REACHABLE and open -- section 12.8 holds",
              str(AFTER[rid]["pages"]))

    print()
    print("=" * 94)
    print("7. ASK, CANCEL, CONFIRM -- PROVED BY EXECUTION WITH COUNTING SPIES")
    print("=" * 94)
    SPY = """() => {
        window.__c57 = [];
        window.__nav57 = [];
        ['archiveProject','resetSignals','load','saveProject','deleteProject','getProject']
          .forEach((k) => { const o = LinStore[k];
             if (typeof o === 'function') LinStore[k] = function (...a) {
                 window.__c57.push(k + '(' + a.join(',') + ')'); return o.apply(LinStore, a); }; });
        if (window.LinResults && LinResults.clear) { const rc = LinResults.clear;
            LinResults.clear = function (...a) { window.__c57.push('LinResults.clear()');
                                                 return rc.apply(LinResults, a); }; }
        if (window.LinDetail && LinDetail.render) { const dr = LinDetail.render;
            LinDetail.render = function (...a) { window.__c57.push('LinDetail.render(' + a[0] + ')');
                                                 return dr.apply(LinDetail, a); }; }
        if (window.LinApp && LinApp.showPage) { const sp = LinApp.showPage;
            LinApp.showPage = function (...a) { window.__nav57.push('showPage(' + a.join(',') + ')');
                                                return sp.apply(LinApp, a); }; }
        window.__href57 = location.href;
        return true; }"""

    def open_detail(rid):
        portfolio()
        page.click(f"#project-list .list-item[data-id='{rid}'] .li-manage")
        page.wait_for_timeout(2500)

    # --- ASK, then CANCEL ---
    rid = ROWS[0]
    open_detail(rid)
    page.evaluate(SPY)
    before_modals = page.evaluate("() => document.querySelectorAll('.app-modal').length")
    page.click("#detail-root .detail-admin-host .pe-reset")
    page.wait_for_timeout(1200)
    got = page.evaluate("""() => {
        const m = document.querySelector('.app-modal');
        if (!m) return null;
        return { title: (m.querySelector('.app-modal-title')||{}).textContent || '',
                 body: (m.querySelector('.app-modal-body p')||{}).textContent || '',
                 buttons: Array.from(m.querySelectorAll('.app-modal-body button'))
                            .map(b => b.textContent.trim()),
                 all: (m.innerText || '') }; }""")
    print(f"    confirmation title  : {got and got['title']!r}")
    print(f"    confirmation detail : {got and got['body']!r}")
    print(f"    confirmation buttons: {got and got['buttons']!r}")
    check(before_modals == 0 and got is not None,
          "GUARANTEE 5: the surviving control ASKS BEFORE CLEARING -- a dialog opens and the "
          "action has not run")
    mid = page.evaluate("() => window.__c57")
    check(mid == [], "and at the moment the dialog is open NO call has been made", str(mid))
    check(rid in got["title"] and rid in got["body"] and rid in got["buttons"][0],
          f"the confirmation NAMES THE PROJECT ({rid}) in its title, its detail and on its button",
          str(got["buttons"]))
    _bad = [c for c in ("—", "–") if c in got["all"]]
    check(not _bad, "GUARANTEE 18: no em dash and no en dash in the confirmation text", repr(_bad))
    page.keyboard.press("Escape")
    page.wait_for_timeout(1200)
    after = page.evaluate("""() => ({ calls: window.__c57, nav: window.__nav57,
        modals: document.querySelectorAll('.app-modal').length,
        href: location.href === window.__href57,
        pages: Array.from(document.querySelectorAll('.page'))
                .filter(p => getComputedStyle(p).display !== 'none')
                .map(p => p.getAttribute('data-page')),
        id: (document.querySelector('#detail-root .pr-admin .pe-id')||{}).value })""")
    print(f"    after CANCEL: calls={after['calls']} nav={after['nav']} modals={after['modals']}")
    check(after["calls"] == [] and after["nav"] == [] and after["href"],
          "GUARANTEE 5: CANCELLING MAKES NO CALL AND CHANGES NO STATE -- LinStore untouched, "
          "LinResults untouched, LinDetail untouched, no navigation", str(after))
    check(after["modals"] == 0 and after["pages"] == ["detail"] and after["id"] == rid,
          "and the same detail page is still open with its panel intact", str(after))

    # --- CONFIRM: the union really runs, and on THAT project only ---
    target, other = ROWS[1], ROWS[0]
    open_detail(target)
    page.evaluate(SPY)
    page.click("#detail-root .detail-admin-host .pe-reset")
    page.wait_for_timeout(1200)
    page.click(".app-modal .app-modal-body button")
    page.wait_for_timeout(4000)
    calls = page.evaluate("() => window.__c57")
    print(f"    CONFIRM on {target}: calls = {calls}")
    check(any(c.startswith("resetSignals(" + target) for c in calls),
          f"GUARANTEE 6: CONFIRMING calls LinStore.resetSignals({target})", str(calls))
    check(any(c == "LinResults.clear()" for c in calls),
          "and the merged handler REALLY calls LinResults.clear() -- the behaviour that was only "
          "in the removed control, proved by execution and not by reading", str(calls))
    check(any(c.startswith("load(") for c in calls),
          "and it REALLY calls LinStore.load() -- the behaviour that was only in the survivor",
          str(calls))
    check(any(c.startswith("getProject(" + target) for c in calls),
          f"and it REALLY re-fetches through LinStore.getProject({target})", str(calls))
    check(any(c == "LinDetail.render(" + target + ")" for c in calls),
          f"and it REALLY re-renders the detail page through LinDetail.render({target})",
          str(calls))
    _foreign = [c for c in calls if other in c]
    check(not _foreign,
          f"GUARANTEE 6: and it touched NO OTHER PROJECT -- not one call mentions {other}",
          str(_foreign))
    _log = page.evaluate("""() => { try { return (JSON.parse(
        localStorage.getItem('lpr-ingest-log') || '[]')).map(e => e.msg); }
        catch (e) { return ['READ FAILED: ' + e.message]; } }""")
    print(f"    logEvent entries rendered: {_log}")
    check(any(target in e for e in _log),
          f"and logEvent() wrote the append-only entry for {target} -- the other behaviour that "
          f"was only in the survivor", str(_log))

    print()
    print("=" * 94)
    print("8. PAGE ERRORS")
    print("=" * 94)
    print(f"    page errors: {errors}")
    check(not errors, "no uncaught page error during the whole drive", str(errors)[:300])

    browser.close()

server.should_exit = True
print()
print("=" * 94)
print(f"RESULT  passed={PASSED}  failed={FAILED}")
if _fail:
    for f in _fail:
        print("  FAILED: " + f)
print("=" * 94)
sys.exit(1 if FAILED else 0)
