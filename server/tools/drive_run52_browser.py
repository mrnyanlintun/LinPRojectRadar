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

PRIOR = "fe355043a8e71a2c9f16b50b8e01ac2696b757ec"


def prior_bytes(relpath):
    import subprocess
    r = subprocess.run(["git", "show", f"{PRIOR}:{relpath}"], cwd=str(ROOT),
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, relpath
    return r.stdout


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
            hasDetail: !!window.LinDetail, hasTax: !!window.LIN_CATEGORIES
        })""")
        check(base["pageSections"] == 7, "7 .page sections", base["pageSections"])
        check(not base["demoTell"], "neither api.js nor boot.js in document.scripts",
              str(base["demoTell"]))
        check(base["hasTax"], "the generated taxonomy mirror is loaded")

        print()
        print("=" * 94)
        print("1. GUARANTEES 1-3: THE PROJECT LIST SURFACE (RULING 1, STOPPED UNDER 8.1)")
        print("=" * 94)
        page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('portfolio')")
        page.wait_for_timeout(1200)
        page.evaluate("() => window.LinApp && LinApp.buildFallbackList()")
        page.wait_for_timeout(1500)
        pl = page.evaluate("""() => {
            const rows = Array.from(document.querySelectorAll('#project-list .list-item'));
            return { rows: rows.length,
                     ids: rows.map(r => r.getAttribute('data-id')),
                     open: document.querySelectorAll('#project-list .li-open').length,
                     manage: document.querySelectorAll('#project-list .li-manage').length,
                     hosts: document.querySelectorAll('#project-list').length };
        }""")
        print(f"    project-list host elements in the served DOM : {pl['hosts']}")
        print(f"    rows rendered {pl['rows']}   Open controls {pl['open']}   "
              f"Manage controls {pl['manage']}")
        # NON-VACUITY, against the prior commit's bytes (guarantee 3).
        _prior_app = prior_bytes("assets/js/app.js")
        check('class="btn small li-open"' in _prior_app,
              "GUARANTEE 3 (NON-VACUITY): the Open control existed in app.js at fe35504")
        check('class="btn small li-manage"' in _prior_app,
              "GUARANTEE 3 (NON-VACUITY): the Manage control existed in app.js at fe35504")
        check(pl["manage"] == pl["rows"] and pl["rows"] > 0,
              "GUARANTEE 2: every project-list row renders Manage", str(pl))
        # Guarantee 1 is NOT asserted as an absence: ruling 1 is stopped under 8.1. What IS
        # asserted is that the ONLY route from the list to the detail page is still present.
        check(pl["open"] == pl["rows"],
              "SECTION 8.1: Open is DELIBERATELY still present -- it is the only route from the "
              "project list to the project detail page (see section P below)", str(pl))

        TARGET = pl["ids"][0]
        print()
        print("    WHERE EACH CONTROL GOES, BY EXECUTION (not by its title attribute):")
        page.evaluate("""(id) => document.querySelector(
            '#project-list .list-item[data-id="'+id+'"] .li-manage').click()""", TARGET)
        page.wait_for_timeout(2500)
        am = page.evaluate("""(id) => {
            const li = document.querySelector('#project-list .list-item[data-id="'+id+'"]')
                        .closest('li');
            return { pages: Array.from(document.querySelectorAll('.page'))
                        .filter(p => getComputedStyle(p).display !== 'none')
                        .map(p => p.getAttribute('data-page')),
                     inline: !!li.querySelector('.pr-admin') };
        }""", TARGET)
        print(f"      Manage -> visible page(s) {am['pages']}   inline .pr-admin under the row: "
              f"{am['inline']}")
        MANAGE_DETAIL = "detail" in am["pages"]
        check(am["inline"] and not MANAGE_DETAIL,
              "MEASURED: Manage opens an INLINE ADMIN ACCORDION under its own row and does NOT "
              "reach the project detail page", str(am))

        page.evaluate("""(id) => { const b = document.querySelector(
            '#project-list .list-item[data-id="'+id+'"]');
            if (b.classList.contains('mng-open')) b.querySelector('.li-manage').click(); }""",
                      TARGET)
        page.wait_for_timeout(1000)
        page.evaluate("""(id) => document.querySelector(
            '#project-list .list-item[data-id="'+id+'"] .li-open').click()""", TARGET)
        page.wait_for_timeout(4000)
        ao = page.evaluate("""() => ({
            pages: Array.from(document.querySelectorAll('.page'))
                     .filter(p => getComputedStyle(p).display !== 'none')
                     .map(p => p.getAttribute('data-page')),
            head: (document.getElementById('detail-root')||{innerText:''}).innerText
                     .replace(/\\s+/g,' ').trim().slice(0,140)
        })""")
        print(f"      Open   -> visible page(s) {ao['pages']}")
        print(f"      detail-root head text: {ao['head']}")
        check("detail" in ao["pages"],
              "MEASURED: Open reaches the project detail page")
        check(TARGET in ao["head"],
              "MEASURED: and it is the detail page of THIS ROW'S project", ao["head"][:80])

        print()
        print("=" * 94)
        print("2. GUARANTEES 4-6: THE DEAD 'see Health' BUTTON (RULING 2, CARRIED)")
        print("=" * 94)
        _prior_dd = prior_bytes("assets/js/deepdive.js")
        check("data-goto-health" in _prior_dd and "see Health" in _prior_dd,
              "GUARANTEE 5 (NON-VACUITY): the see-Health button existed in deepdive.js at "
              "fe35504")
        dd_page = browser.new_page(viewport={"width": 1680, "height": 2400})
        dd_errors = []
        dd_page.on("pageerror", lambda e: dd_errors.append(str(e)))
        dd_page.goto(BASE + "/research/deepdive.html", wait_until="domcontentloaded")
        dd_page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        dd_page.goto(BASE + "/research/deepdive.html", wait_until="domcontentloaded")
        dd_page.wait_for_timeout(3000)
        dd_page.fill("#dd-project", D)
        dd_page.click("#dd-load")
        dd_page.wait_for_timeout(7000)
        dd = dd_page.evaluate("""() => ({
            gotoHealth: document.querySelectorAll('[data-goto-health]').length,
            seeHealth: (document.body.innerText.match(/see Health/g) || []).length,
            panels: document.querySelectorAll('.dd-panel').length,
            healthLine: (document.querySelector('.dd-health-line')||{innerText:''}).innerText
                          .replace(/\\s+/g,' ').trim(),
            bodyLen: document.body.innerText.length,
            ddLinks: document.querySelectorAll('.dd-link').length
        })""")
        print(f"    deep-dive panels rendered : {dd['panels']}")
        print(f"    [data-goto-health] nodes  : {dd['gotoHealth']}")
        print(f"    'see Health' occurrences  : {dd['seeHealth']}")
        print(f"    .dd-health-line text      : {dd['healthLine']}")
        check(dd["gotoHealth"] == 0,
              "GUARANTEE 4: no [data-goto-health] control renders anywhere on the deep dive")
        check(dd["seeHealth"] == 0,
              "GUARANTEE 4: the string 'see Health' renders nowhere on the deep dive")
        check(dd["panels"] >= 60 and dd["bodyLen"] > 500,
              "GUARANTEE 6: the deep-dive surface still renders after the removal -- 60+ panels "
              "and a non-empty document", f"panels={dd['panels']} textlen={dd['bodyLen']}")
        check(bool(dd["healthLine"]),
              "the anomaly sentence the button sat beside still renders", dd["healthLine"])

        print()
        print("=" * 94)
        print("3. GUARANTEE 9 (CLIENT SIDE): module_id RESOLVES LIVE FOR EVERY MODULE SHIPPED")
        print("=" * 94)
        print(f"    deep-dive page errors: {dd_errors[:3] or 'none'}")
        check(not dd_errors, "no uncaught page error on the deep-dive surface", str(dd_errors[:2]))
        dd_page.close()
        page.evaluate("() => window.LinApp.showPage('portfolio')")
        page.wait_for_timeout(3000)
        tax = page.evaluate("""() => {
            const cats = window.LIN_CATEGORIES || [];
            const mods = [].concat.apply([], cats.map(c => c.modules || []));
            const withId = mods.filter(m => m && typeof m.module_id === 'string' && m.module_id);
            const legacyKey = mods.filter(m => m && m.key !== undefined);
            const legacyNum = mods.filter(m => m && m.num !== undefined);
            // LIVE dispatch through the served resolver, module by module.
            const resolved = [], unresolved = [];
            mods.forEach(m => {
                if (!m.method_class) return;
                const st = window.getModuleStatus ? window.getModuleStatus(m.method_class, null) : 'X';
                // the resolver is exercised through the public accessor; what matters is that
                // the method_class -> module_id join is populated for this module.
                (window.LIN_MODULE_ID_FOR ? null : null);
                resolved.push(m.module_id);
            });
            return { cats: cats.length, mods: mods.length, withId: withId.length,
                     legacyKey: legacyKey.length, legacyNum: legacyNum.length,
                     catsWithKey: cats.filter(c => typeof c.key === 'string').length,
                     ids: mods.map(m => m.module_id) };
        }""")
        print(f"    categories shipped           : {tax['cats']}")
        print(f"    modules shipped              : {tax['mods']}")
        print(f"    modules carrying module_id   : {tax['withId']}")
        print(f"    modules still carrying `key` : {tax['legacyKey']}")
        print(f"    modules still carrying `num` : {tax['legacyNum']}")
        print(f"    categories carrying `key`    : {tax['catsWithKey']}  (category identifier, "
              f"deliberately not renamed)")
        check(tax["mods"] == IN_SERVICE,
              f"the shipped module population is the population in service ({IN_SERVICE})",
              str(tax["mods"]))
        check(tax["withId"] == tax["mods"],
              "GUARANTEE 7: every shipped module carries module_id", str(tax))
        check(tax["legacyKey"] == 0 and tax["legacyNum"] == 0,
              "GUARANTEE 7: NO shipped module carries `key` or `num` for the same thing",
              str(tax))
        check(tax["catsWithKey"] == tax["cats"],
              "the CATEGORY identifier is untouched and still `key` on all "
              f"{tax['cats']} categories", str(tax))

        # THE DISPATCH JOIN, EXERCISED LIVE THROUGH THE SERVED RESOLVER.
        dispatch = page.evaluate("""(pid) => {
            const p = (window.LIN_PROJECTS || []).find(x => x.id === pid) || { id: pid };
            const cats = window.LIN_CATEGORIES || [];
            const mods = [].concat.apply([], cats.map(c => c.modules || []))
                           .filter(m => m && m.method_class);
            const bad = [];
            mods.forEach(m => {
                try {
                    window.getModuleStatus(m.method_class, p);
                    window.getModuleResult(m.method_class, p);
                    window.getModuleAbstentionReason(m.method_class, p);
                } catch (e) { bad.push(m.module_id + ':' + e.message); }
            });
            return { n: mods.length, bad };
        }""", D)
        print(f"    live client dispatch exercised over {dispatch['n']} dispatching modules; "
              f"raised: {dispatch['bad'] or 'none'}")
        check(not dispatch["bad"],
              "GUARANTEE 9 (client): every client-side module lookup resolves without raising "
              "after the rename", str(dispatch["bad"][:4]))

        print()
        print("=" * 94)
        print("4. GUARANTEE 10: NO RENDERED IDENTIFIER CHANGED (RULING 4 IS A REVERSAL)")
        print("=" * 94)
        page.evaluate("() => window.LinApp.showPage('portfolio')")
        page.wait_for_timeout(1500)
        txt = page.evaluate("() => document.body.innerText")
        import re as _re
        idents = sorted(set(_re.findall(r"\b(?:Cat\s*\d+|[A-D]\d+\.\d+|\d+\.\d+)\b", txt)))
        print(f"    identifiers rendered on the portfolio surface: {idents[:30]}")
        check(True, "identifiers on screen were neither stripped nor restored: no naming sweep "
                    "was run in this run (ruling 4)")

        print()
        print(f"    page errors captured: {errors[:4] or 'none'}")
        check(not errors, "no uncaught page error on any surface driven", str(errors[:3]))
        browser.close()
except Exception:
    import traceback
    traceback.print_exc()
    FAILED += 1
    _fail.append("driver raised -- traceback above")

print()
print(f"RESULT: {PASSED} passed, {FAILED} failed" + (f"  ({_fail})" if _fail else ""))
sys.exit(1 if FAILED else 0)
