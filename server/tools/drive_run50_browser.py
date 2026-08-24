#!/usr/bin/env python3
"""
RUN 50. EVERY VISUAL SURFACE, COUNTED IN A RENDERED DOM.

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
    return f"%PDF-1.4 RUN50BROWSER {tag}\n".encode()


set_extractor_override(StubExtractor({
    hashlib.sha256(doc_bytes(_t)).hexdigest(): (_ty, _ex) for _t, _p, _ty, _ex in DOCS}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R50-BR-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == D)) is None:
        s.add(Project(legacy_id=D, doc={"id": D, "name": "Run 50 browser fixture",
                                        "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R50-BR-PM", "role": "Participant",
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
    "id": D, "name": "Run 50 browser fixture", "sector": _captured_project.get("sector"),
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
        check(base["hasDetail"], "the real detail renderer is loaded")

        print()
        print("=" * 94)
        print("1. THE PROJECT DETAIL PAGE: EVERY SURFACE OPENED, EVERY NODE COUNTED")
        print("=" * 94)
        det = page.evaluate("""async ([id]) => {
            await window.LinDetail.render(id);
            await new Promise(r => setTimeout(r, 3000));
            const root = document.getElementById('detail-root');
            // open every collapsible section so the lazy visuals actually render
            const heads = Array.from(root.querySelectorAll('.collapse-header'));
            for (const h of heads) { try { h.click(); } catch (e) {} }
            await new Promise(r => setTimeout(r, 9000));
            return { opened: heads.length,
                     bodiesOpen: Array.from(root.querySelectorAll('.collapse-body'))
                                   .filter(b => b.style.display !== 'none').length };
        }""", [D])
        print(f"    collapsible section heads clicked: {det['opened']}  bodies open: "
              f"{det['bodiesOpen']}")

        surf = page.evaluate("""() => {
            const root = document.getElementById('detail-root');
            const q = (s) => Array.from(root.querySelectorAll(s));
            const txt = (s) => { const n = root.querySelector(s); return n ? n.textContent.trim() : null; };
            return {
              flowModuleNodes: q('.detail-neural-flow g.lnf-nd[data-kind=module]').length,
              flowCatNodes:    q('.detail-neural-flow g.lnf-nd[data-kind=category]').length,
              flowSummary:     (root.querySelector('.detail-neural-flow .lnf-summary') || {}).textContent || '',
              ledgerCatRows:   q('.detail-ledger .cat-row').length,
              ledgerModRows:   q('.detail-ledger .cat-mod-row').length,
              ledgerCatNums:   q('.detail-ledger .cat-row-num').map(n => n.textContent.trim()),
              ledgerModNums:   q('.detail-ledger .cat-mod-num').map(n => n.textContent.trim()),
              webFootnote:     txt('.sw-footnote'),
              webAxes:         (window.LinDetail && window.LinDetail.__axes) ? window.LinDetail.__axes : null,
              ensEyebrow:      txt('.ens-panel .eyebrow'),
              ensVs:           txt('.ens-panel .sw-vs'),
              projnetEyebrow:  txt('.detail-projnet2d .projnet2d-head .eyebrow'),
              projnetFoot:     txt('.detail-projnet2d .projnet2d-foot'),
              swVs:            txt('.sw-vs'),
              badges: Array.from(root.querySelectorAll('.collapse-badge')).map(n => n.textContent.trim()),
              titles: Array.from(root.querySelectorAll('.collapse-title')).map(n => n.textContent.trim()),
              headText: root.innerText.slice(0, 0),
              allText: root.innerText
            };
        }""")
        for k in ("flowModuleNodes", "flowCatNodes", "ledgerCatRows", "ledgerModRows"):
            print(f"    {k:18s} = {surf[k]}")
        MEASURED.update({k: surf[k] for k in ("flowModuleNodes", "flowCatNodes",
                                              "ledgerCatRows", "ledgerModRows")})
        print(f"    Project Signal Network eyebrow: {surf['projnetEyebrow']}")
        MEASURED["projnetEyebrow"] = surf["projnetEyebrow"]
        print(f"    Signal Flow summary strip, verbatim:\n      {surf['flowSummary'][:400]}")
        print(f"    Signal Web footnote:  {surf['webFootnote']}")
        print(f"    Ensemble eyebrow:     {surf['ensEyebrow']}")
        print(f"    Ensemble sub:         {surf['ensVs']}")
        print(f"    section titles:       {surf['titles']}")
        print(f"    section badges:       {surf['badges']}")
        print(f"    ledger category chips rendered: {surf['ledgerCatNums']}")
        print(f"    ledger module chips rendered (first 12): {surf['ledgerModNums'][:12]}"
              f"  total={len(surf['ledgerModNums'])}")

        check(surf["flowModuleNodes"] == IN_SERVICE,
              f"SIGNAL FLOW draws exactly the population in service ({IN_SERVICE} module nodes)",
              str(surf["flowModuleNodes"]))
        check(surf["ledgerModRows"] == IN_SERVICE,
              f"SIGNAL LEDGER draws exactly the population in service ({IN_SERVICE} module rows)",
              str(surf["ledgerModRows"]))
        check(not re.search(r"\b(96|101|103|100)\s+(registered\s+)?(project\s+)?modules?\b",
                            surf["allText"]),
              "no rendered text on the detail page states a module population of 96, 100, 101 "
              "or 103",
              (re.search(r".{60}\b(96|101|103|100)\s+(registered\s+)?(project\s+)?modules?\b.{60}",
                         surf["allText"]) or [""])[0])
        check(not surf["ledgerModNums"],
              "SIGNAL LEDGER renders NO module identifier chip (guarantee 1)",
              str(surf["ledgerModNums"][:8]))
        check(not surf["ledgerCatNums"],
              "SIGNAL LEDGER renders NO category identifier chip (guarantee 1)",
              str(surf["ledgerCatNums"]))
        _reg = [b for b in surf["badges"] if "registered" in b.lower()]
        check(not _reg,
              "no section badge describes this project's drawn population as 'registered'",
              str(_reg))
        check("registered architecture" not in surf["flowSummary"],
              "the Signal Flow summary strip no longer calls the drawn population the "
              "platform's registered architecture", surf["flowSummary"][:200])

        print()
        print("=" * 94)
        print("1b. THE HANDBOOK PAGE: EVERY SENTENCE STATING A MODULE POPULATION")
        print("=" * 94)
        kn = page.evaluate(r"""async () => {
            const host = document.querySelector('[data-page=handbook]');
            if (host) host.hidden = false;
            const tab = host.querySelector('.hb-tab[data-tab=methods]');
            if (tab) { try { tab.click(); } catch (e) {} }
            if (window.LinKnowledge) { try { await window.LinKnowledge.renderKnowledgePage(); } catch(e) {} }
            await new Promise(r => setTimeout(r, 1500));
            const topics = Array.from(host.querySelectorAll('button[data-topic]'))
                             .map(b => b.getAttribute('data-topic'));
            let text = '';
            const seen = [];
            for (const t of topics) {
              const b = host.querySelector('button[data-topic="' + t + '"]');
              if (!b) continue;
              try { b.click(); } catch (e) { continue; }
              await new Promise(r => setTimeout(r, 120));
              // open every collapsed article section so its prose reaches innerText
              for (let pass = 0; pass < 2; pass++) {
                const hs = Array.from(host.querySelectorAll('.collapse-header'));
                for (const h of hs) {
                  const body = h.parentElement.querySelector('.collapse-body');
                  if (body && body.style.display === 'none') { try { h.click(); } catch (e) {} }
                }
                await new Promise(r => setTimeout(r, 60));
              }
              const dets = Array.from(host.querySelectorAll('details'));
              for (const d of dets) d.open = true;
              await new Promise(r => setTimeout(r, 40));
              seen.push(t);
              text = text + ' ' + host.innerText;
            }
            return { clicked: topics.length, opened: seen.length, text: text,
                     navNums: Array.from(host.querySelectorAll('.kn-nav-cat-num')).map(n => n.textContent.trim()) };
        }""")
        print(f"    handbook topics clicked: {kn['clicked']} (rendered {kn['opened']})   "
              f"text length: {len(kn['text'])}")
        print(f"    handbook nav category chips: {sorted(set(kn['navNums']))}")
        check("why-108-modules" in kn["text"] or kn["opened"] >= 40,
              "the handbook probe really did render its articles, so the sweep below is not "
              "vacuous", str(kn["opened"]))
        check("101 registered modules, of which 63 are in service" in kn["text"],
              "AND THE SWEEP IS PROVED NON-VACUOUS BY A POSITIVE: the handbook sentence that "
              "states the registry and the in-service population together IS in the rendered "
              "text")
        pathlib.Path("handbook_text.txt").write_text(kn["text"], encoding="utf-8")
        for _probe in ("Why 101 registered modules", "96 registered modules",
                       "101 registered modules, of which 63",
                       "No human can run this many analyses"):
            print(f"      probe {_probe!r}: {_probe in kn['text']}")
        _hits = re.findall(r".{90}\b(?:96|100|101|103)\s+(?:registered\s+)?(?:project\s+)?modules?.{90}",
                           kn["text"])
        for h in sorted(set(_hits)):
            print(f"      HIT: ...{h}...")
        _bad = [h for h in set(_hits)
                if re.search(r"\b(?:96|100|103)\s+(?:registered\s+)?(?:project\s+)?modules?", h)]
        check(not _bad,
              "no handbook sentence states a module population of 96, 100 or 103 (101 is the "
              "registry and is correct where the sentence is about what the platform registers)",
              str(_bad)[:400])
        check(not re.search(r"the project(?:'s|\u2019s)\s+\d+\s+registered modules", kn["text"]),
              "no handbook sentence calls a per-project population 'registered modules'",
              (re.search(r".{80}the project(?:.{0,3})s\s+\d+\s+registered modules.{80}",
                         kn["text"]) or [""])[0])

        print()
        print("=" * 94)
        print("2. THE RESEARCH DEEP-DIVE SURFACE: PANELS, BUCKETS AND GROUP HEADERS")
        print("=" * 94)
        # RUN 54: THIS BLOCK IS HISTORICAL AND WILL NOT RUN AGAIN. `research/deepdive.html`
        # was DELETED on the owner's ruling at section 8 of the Run 54 order, and the route
        # that served it went with it. This driver is the EVIDENCE CAPTURE for its own run
        # and is pinned to what that run measured; rewriting it would falsify the record it
        # exists to be. It is annotated, not rewritten, on the same principle every
        # predecessor package record in this repository is kept rather than regenerated.
        dd_page = browser.new_page(viewport={"width": 1680, "height": 2400})
        dd_errors = []
        dd_page.on("pageerror", lambda e: dd_errors.append(str(e)))
        dd_page.goto(BASE + "/research/deepdive.html", wait_until="domcontentloaded")
        dd_page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        dd_page.goto(BASE + "/research/deepdive.html", wait_until="domcontentloaded")
        dd_page.wait_for_timeout(3000)
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
              buckets: panels.map(p => p.getAttribute('data-cat')),
              nums: panels.map(p => p.getAttribute('data-num')),
              groupNames: Array.from(document.querySelectorAll('.dd-cat-name')).map(n => n.textContent),
              groupCounts: Array.from(document.querySelectorAll('.dd-cat-count')).map(n => n.textContent),
              groupKeys: Array.from(document.querySelectorAll('.dd-catgroup')).map(n => n.dataset.cat),
              health: !!document.querySelector('.dd-cat8-health, .dd-health-flyout'),
              healthText: (document.querySelector('.dd-cat8-health, .dd-health-flyout') || {}).textContent || '',
              allText: host ? host.innerText : '',
              controls: host ? host.querySelectorAll('button,input,select,textarea').length : -1
            };
        }""")
        print(f"    deep-dive panels rendered: {dd['count']}")
        MEASURED["ddPanels"] = dd["count"]
        if dd_errors:
            print(f"    dd page errors: {'; '.join(dd_errors)[:400]}")
        if dd["err"]:
            print(f"    deep dive error text: {dd['err']}")
        print("    group headers, verbatim from the DOM:")
        for g, c, k in zip(dd["groupNames"], dd["groupCounts"], dd["groupKeys"]):
            print(f"      [{k}] {g}   ({c})")
        pairs = sorted(set(zip(dd["nums"], dd["buckets"])))
        print(f"    panel key -> bucket, from the DOM:")
        for n, b in pairs:
            print(f"      {n:12s} -> {b}")
        print(f"    Portfolio Health flyout present on this surface: {dd['health']}")
        if dd["health"]:
            print(f"      flyout text: {dd['healthText'][:400]}")
        check(dd["count"] > 0, "the deep-dive panels render", f"count={dd['count']}")
        check(not dd["health"], "PORTFOLIO HEALTH RENDERS NOWHERE on the deep-dive surface",
              dd["healthText"][:200])
        joined = "\n".join(dd["labels"] + dd["groupNames"])
        check(not re.search(r"\bCat\s*\d|\bM\d\d\b|\bD1\.\d|Module\s+\d", joined),
              "no rendered deep-dive label or group header carries an identifier", joined[:300])
        check("&" not in joined and "—" not in joined and "–" not in joined,
              "and none carries an ampersand, an em dash or an en dash", joined[:300])

        print()
        print("    THE FOUR-GROUP MISMATCH, MEASURED: does each group's header name the "
              "category its panels belong to?")
        _headmap = dict(zip(dd["groupKeys"], dd["groupNames"]))
        print(f"    group key -> header: {_headmap}")

        dd_page.close()

        print()
        print("=" * 94)
        print("3. NO UNCAUGHT PAGE ERROR")
        print("=" * 94)
        check(not errors, "no uncaught page error on the detail page", "; ".join(errors)[:400])
        browser.close()
except BaseException:
    import traceback
    traceback.print_exc()
    FAILED += 1
    _fail.append("the driver raised")
    print("  ****  the driver raised; counted as a failure")

print()
print("MEASURED NODE COUNTS: " + json.dumps(MEASURED))
if _fail:
    print("FAILURES:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
raise SystemExit(1 if FAILED else 0)
