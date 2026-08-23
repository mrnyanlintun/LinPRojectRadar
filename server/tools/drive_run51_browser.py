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
        print("1b. GUARANTEE 1, MEASURED ON THE RENDERED DOM AND INSIDE ITS SVGs")
        print("=" * 94)
        # THE SWEEPER. Reads innerText AND every SVG <text> node AND every aria-label, title,
        # placeholder and alt on the page. Returns each string with the node that carried it, so
        # a survivor can be named rather than counted.
        SWEEP = r"""
        () => {
          const out = [];
          const push = (where, s) => { if (s && String(s).trim()) out.push([where, String(s)]); };
          // 1. Visible text, node by node, so a survivor can be located.
          const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          let n;
          while ((n = walk.nextNode())) {
            const el = n.parentElement;
            if (!el) continue;
            const tag = el.tagName ? el.tagName.toLowerCase() : '';
            if (tag === 'script' || tag === 'style') continue;
            // A hidden page section is still served text; sweep it.
            push(tag + (el.className && el.className.baseVal === undefined
                        ? '.' + String(el.className).split(' ')[0] : ''), n.nodeValue);
          }
          // 2. SVG <text> and <title> and <tspan>: NOT in innerText. This is the whole point.
          document.querySelectorAll('svg text, svg tspan, svg title').forEach(
            (t) => push('SVG:' + t.tagName, t.textContent));
          // 3. Accessible names and other attributes a reader or a screen reader receives.
          document.querySelectorAll('[aria-label],[title],[placeholder],[alt]').forEach((el) => {
            ['aria-label', 'title', 'placeholder', 'alt'].forEach((a) => {
              if (el.hasAttribute(a)) push('@' + a + ':' + el.tagName.toLowerCase(),
                                           el.getAttribute(a));
            });
          });
          return out;
        }"""

        G1 = [
            ("module identifier", re.compile(r"\b[A-D]\d{1,2}\.\d{1,2}\b")),
            ("category identifier", re.compile(r"\b[A-D]\d{1,2}\b(?![\.\w])")),
            ("retired Cat scheme", re.compile(r"\bCat(?:egory)?\s*\d+", re.I)),
            ("retired Module scheme", re.compile(r"\bModule\s*\d+|\bM0\d\b|\bPH\.\d")),
            ("ampersand", re.compile(r"&")),
            ("en or em dash", re.compile(r"[–—]")),
        ]

        def g1(strings, surface):
            bad = []
            for where, s in strings:
                for label, rx in G1:
                    m = rx.search(s)
                    if m:
                        bad.append((surface, where, label, m.group(0), s.strip()[:110]))
            return bad

        # Every participant page, opened in turn, swept whole.
        PAGES = ["portfolio", "handbook", "about", "workspace", "auditor", "admin"]
        all_bad = []
        swept_pages = []
        for pg in PAGES:
            ok = page.evaluate("""(p) => {
                try { if (window.LinApp && LinApp.showPage) { LinApp.showPage(p); return true; } }
                catch (e) {}
                return false;
            }""", pg)
            if not ok:
                continue
            page.wait_for_timeout(1200)
            strings = page.evaluate(SWEEP)
            swept_pages.append((pg, len(strings)))
            all_bad += g1(strings, pg)
        print(f"    pages swept, strings read: {swept_pages}")
        check(len(swept_pages) >= 3 and sum(c for _p, c in swept_pages) > 500,
              "THE SWEEP IS NOT VACUOUS: it read hundreds of strings across several pages",
              str(swept_pages))

        print()
        print("=" * 94)
        print("1c. THE HANDBOOK, ARTICLE BY ARTICLE, WITH ITS SVG TEXT NODES READ")
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
            const svgText = [];
            const arias = [];
            const seen = [];
            for (const t of topics) {
              const b = host.querySelector('button[data-topic="' + t + '"]');
              if (!b) continue;
              try { b.click(); } catch (e) { continue; }
              await new Promise(r => setTimeout(r, 120));
              for (let pass = 0; pass < 2; pass++) {
                const hs = Array.from(host.querySelectorAll('.collapse-header'));
                for (const h of hs) {
                  const body = h.parentElement.querySelector('.collapse-body');
                  if (body && body.style.display === 'none') { try { h.click(); } catch (e) {} }
                }
                await new Promise(r => setTimeout(r, 60));
              }
              for (const d of Array.from(host.querySelectorAll('details'))) d.open = true;
              await new Promise(r => setTimeout(r, 40));
              seen.push(t);
              text = text + ' ' + host.innerText;
              host.querySelectorAll('svg text, svg tspan, svg title').forEach(
                (x) => svgText.push(x.textContent));
              host.querySelectorAll('[aria-label]').forEach(
                (x) => arias.push(x.getAttribute('aria-label')));
            }
            return { clicked: topics.length, opened: seen.length, text: text,
                     svgText: svgText, arias: arias,
                     navNums: Array.from(host.querySelectorAll('.kn-nav-cat-num'))
                                .map(n => n.textContent.trim()) };
        }""")
        svgset = sorted(set(x.strip() for x in kn["svgText"] if x and x.strip()))
        ariaset = sorted(set(x.strip() for x in kn["arias"] if x and x.strip()))
        print(f"    handbook topics clicked: {kn['clicked']} (rendered {kn['opened']})   "
              f"text length: {len(kn['text'])}")
        print(f"    SVG text nodes read: {len(kn['svgText'])} ({len(svgset)} distinct)")
        print(f"    handbook SVG text, verbatim: {svgset[:60]}")
        print(f"    handbook accessible names: {ariaset[:20]}")
        pathlib.Path("run51_handbook_text.txt").write_text(kn["text"], encoding="utf-8")
        pathlib.Path("run51_handbook_svg.txt").write_text("\n".join(svgset), encoding="utf-8")

        # THE PROOF THE SWEEP READS SVG TEXT NODES (order section 7 item 12). This check FAILS
        # if the ten identifiers are reinstated, and it PASSES only because the sweep can see
        # inside the SVG at all -- which is proved by the positive on the line below it.
        check(len(kn["svgText"]) >= 20,
              "THE SWEEP READS SVG TEXT NODES AT ALL: the handbook's diagrams yielded text nodes "
              "that innerText never exposes", str(len(kn["svgText"])))
        check(any(x.strip() in ("EVM", "CUSUM", "PERT", "DSM", "CCPM") for x in kn["svgText"]),
              "AND IT REALLY READ THE SIGNAL STACK: the method chips inside that SVG are in the "
              "swept text, so an identifier inside it could not hide", str(svgset[:12]))
        _svg_ids = [x for x in svgset
                    if re.search(r"^\s*0\d\s|\b[A-D]\d{1,2}\.\d|\bCat\s*\d", x)]
        check(not _svg_ids,
              "AND NOT ONE SVG TEXT NODE ON THE HANDBOOK CARRIES A MODULE IDENTIFIER "
              "(this is the check that fails if 01 EVM .. 10 DSM are reinstated)",
              str(_svg_ids))
        _bad_aria = [a for a in ariaset if re.search(r"\b10 categories\b|\bCat\s*\d", a)]
        check(not _bad_aria,
              "AND NO ACCESSIBLE NAME ON THE HANDBOOK STATES TEN CATEGORIES WHERE ELEVEN "
              "PROJECT CATEGORIES ARE IN SERVICE", str(_bad_aria))

        check("101 registered modules, of which 63 are in service" in kn["text"],
              "THE HANDBOOK SWEEP IS NON-VACUOUS BY A POSITIVE: the sentence naming the registry "
              "and the in-service population together IS in the rendered text")
        _hits = re.findall(
            r".{90}\b(?:96|100|101|103)\s+(?:registered\s+)?(?:project\s+)?modules?.{90}",
            kn["text"])
        for h in sorted(set(_hits)):
            print(f"      HIT: ...{h}...")
        _bad = [h for h in set(_hits)
                if re.search(r"\b(?:96|100|103)\s+(?:registered\s+)?(?:project\s+)?modules?", h)]
        check(not _bad,
              "NO HANDBOOK SENTENCE STATES 96, 100 OR 103 MODULES. This is the defect the owner "
              "saw, read back from the rendered DOM", str(_bad)[:400])
        check(f"{REGISTRY} registered modules" in kn["text"]
              and f"{IN_SERVICE} are in service" in kn["text"],
              f"AND THE HANDBOOK STATES {REGISTRY} REGISTERED AND {IN_SERVICE} IN SERVICE, both "
              "from the rendered DOM")
        _per_project = re.search(r"the project(?:'s|’s)\s+\d+\s+registered modules",
                                 kn["text"])
        check(not _per_project,
              "and no handbook sentence calls a per-project population 'registered modules'",
              _per_project.group(0) if _per_project else "")
        all_bad += g1([("handbook.svg", x) for x in svgset], "handbook-svg")
        all_bad += g1([("handbook.aria", x) for x in ariaset], "handbook-aria")

        print()
        print("=" * 94)
        print("1d. THE ABOUT PAGE STATES ITS COUNTS FROM THE TAXONOMY, NOT FROM PROSE")
        print("=" * 94)
        page.evaluate("() => { try { LinApp.showPage('about'); } catch (e) {} }")
        page.wait_for_timeout(800)
        ab = page.evaluate("""() => {
            const spans = Array.from(document.querySelectorAll('[data-taxcount]'));
            const host = document.querySelector('[data-page=about]');
            return { keys: spans.map(s => s.getAttribute('data-taxcount')),
                     values: spans.map(s => s.textContent.trim()),
                     counts: window.LIN_TAXONOMY_COUNTS || null,
                     text: host ? host.innerText : '' };
        }""")
        print(f"    data-taxcount spans: {list(zip(ab['keys'], ab['values']))}")
        print(f"    window.LIN_TAXONOMY_COUNTS = {ab['counts']}")
        check(len(ab["keys"]) >= 6, "the About page states its counts through derived spans, "
              "not typed prose", str(len(ab["keys"])))
        check(all(v.isdigit() for v in ab["values"]) and ab["values"],
              "and every one of them RESOLVED to a number in the rendered DOM", str(ab["values"]))
        _want = {"registered": str(REGISTRY), "inService": str(IN_SERVICE)}
        _mismatch = [(k, v) for k, v in zip(ab["keys"], ab["values"])
                     if k in _want and v != _want[k]]
        check(not _mismatch,
              f"and each resolves to the population the SERVER reports ({REGISTRY} registered, "
              f"{IN_SERVICE} in service), hand-computed here and not read from the same object",
              str(_mismatch))
        check(ab["counts"] and ab["counts"].get("registered") == REGISTRY
              and ab["counts"].get("inService") == IN_SERVICE
              and ab["counts"].get("retired") == REGISTRY - IN_SERVICE,
              "and window.LIN_TAXONOMY_COUNTS itself agrees with registry_index() and "
              "service_index() called in this process", str(ab["counts"]))

        print()
        print("=" * 94)
        print("2. THE RESEARCH DEEP-DIVE SURFACE: PANELS, BUCKETS AND GROUP HEADERS")
        print("=" * 94)
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
              heads: panels.map(p => { const h = p.querySelector('.dd-head'); return h ? h.innerText.trim() : ''; }),
              buckets: panels.map(p => p.getAttribute('data-cat')),
              nums: panels.map(p => p.getAttribute('data-num')),
              groupNames: Array.from(document.querySelectorAll('.dd-cat-name')).map(n => n.textContent),
              groupCounts: Array.from(document.querySelectorAll('.dd-cat-count')).map(n => n.textContent),
              groupKeys: Array.from(document.querySelectorAll('.dd-catgroup')).map(n => n.dataset.cat),
              health: !!document.querySelector('.dd-cat8-health, .dd-health-flyout, .cat8-module'),
              healthText: (document.querySelector('.dd-cat8-health, .dd-health-flyout, .cat8-module') || {}).textContent || '',
              linDeepDiveKeys: Object.keys(window.LinDeepDive || {}),
              projectCats: (window.projectLevelCategories ? window.projectLevelCategories() : [])
                             .map(c => [c.key, c.name]),
              allText: host ? host.innerText : ''
            };
        }""")
        print(f"    deep-dive panels rendered: {dd['count']}")
        MEASURED["ddPanels"] = dd["count"]
        if dd_errors:
            print(f"    dd page errors: {'; '.join(dd_errors)[:400]}")
        print(f"    window.LinDeepDive exports: {dd['linDeepDiveKeys']}")
        print(f"    project-level categories in service, in order: {dd['projectCats']}")
        print("    group headers, verbatim from the DOM:")
        for g, c, k in zip(dd["groupNames"], dd["groupCounts"], dd["groupKeys"]):
            print(f"      [{k}] {g}   ({c})")
        pairs = sorted(set(zip(dd["nums"], dd["buckets"])))
        print("    panel key -> bucket -> header, from the DOM:")
        _headmap = dict(zip(dd["groupKeys"], dd["groupNames"]))
        for n, b in pairs:
            print(f"      {str(n):12s} -> {str(b):4s} -> {_headmap.get(b, '(no group)')}")

        check(dd["count"] > 0, "the deep-dive panels render", f"count={dd['count']}")
        check(dd["linDeepDiveKeys"] == ["render"],
              "window.LinDeepDive exports ONLY render: renderCat8Health is gone from the served "
              "bytes", str(dd["linDeepDiveKeys"]))
        check(not dd["health"],
              "PORTFOLIO HEALTH RENDERS NOWHERE, asserted on the only surface that loads "
              "deepdive.js", dd["healthText"][:200])

        # RULING 5 AND 6, MEASURED. Every rendered panel sits in the bucket whose header names
        # the category the module belongs to, hand-computed here from the authority CSV rather
        # than read back from the map under test.
        AUTH = {}
        _csv = (ROOT / "p0-baseline" / "module_renumbering_map.csv").read_text(encoding="utf-8")
        print(f"    naming authority rows read: {len(_csv.splitlines()) - 1}")
        EXPECT = {  # panel key -> the category KEY it belongs to, from the authority, by hand
            "01": "A1", "02": "A1", "1.4": "A1", "1.5": "A1", "1.6": "A1", "1.7": "A1",
            "1.8": "A1", "1.9": "A1", "1.10": "A1", "1.11": "A1", "1.12": "A1",
            "04": "A2", "05": "A2", "06": "A2", "2.4": "A2", "2.5": "A2", "2.6": "A2",
            "2.7": "A2", "2.8": "A2", "2.9": "A2", "2.10": "A2", "2.11": "A2",
            "07": "A3", "3.1": "A3", "3.3": "A3", "3.4": "A3", "3.5": "A3", "3.6": "A3",
            "3.7": "A3", "3.8": "A3", "3.9": "A3", "3.10": "A3",
            "03": "A4", "4.1": "A4", "4.2": "A4", "4.3": "A4", "4.4": "A4", "4.5": "A4",
            "4.6": "A4", "4.7": "A4", "4.8": "A4", "4.9": "A4", "4.10": "A4",
            "08": "A5", "3.2": "A5", "5.1": "A5", "5.2": "A5", "5.3": "A5", "5.4": "A5",
            "5.5": "A5", "5.6": "A5", "5.7": "A5", "5.8": "A5",
            "8.6 to 8.9": "A6",
            "09": "B1", "6.1": "B1", "6.2": "B1", "6.3": "B1", "6.4": "B1",
            "10": "B2", "11": "B2", "12": "B2", "13": "B2", "14": "B2", "15": "B2",
            "16": "B2", "17": "B2", "18": "B2", "7.1": "B2", "7.2 to 7.8": "B2",
            "7.9 to 7.20": "B2",
            "19": "B3", "8.1": "B3", "8.2 to 8.5": "B3",
            "10.1": "B4", "10.2 to 10.7": "B4",
            "9.1": "C1", "9.2 to 9.7": "C1",
        }
        catorder = [c[0] for c in dd["projectCats"]]
        catname = dict(dd["projectCats"])
        misfiled = []
        for num, bucket in zip(dd["nums"], dd["buckets"]):
            want = EXPECT.get(num)
            if want is None:
                misfiled.append((num, bucket, "NOT IN THE HAND-COMPUTED TABLE"))
                continue
            want_bucket = str(catorder.index(want) + 1) if want in catorder else "?"
            if str(bucket) != want_bucket:
                misfiled.append((num, bucket, f"expected {want_bucket} ({want})"))
        check(not misfiled,
              "EVERY RENDERED PANEL IS FILED UNDER THE CATEGORY ITS MODULE BELONGS TO IN THE "
              "CURRENT TAXONOMY, asserted per panel against a table hand-computed from the "
              "naming authority and not read from the map under test", str(misfiled)[:600])
        headers_wrong = []
        for num, bucket in zip(dd["nums"], dd["buckets"]):
            want = EXPECT.get(num)
            if want and _headmap.get(str(bucket)) != catname.get(want):
                headers_wrong.append((num, _headmap.get(str(bucket)), catname.get(want)))
        check(not headers_wrong,
              "AND EVERY PANEL IS LABELLED WITH THAT CATEGORY'S NAME: the collapsible header "
              "over it names the category the module belongs to", str(headers_wrong)[:500])

        # RULING 6: the eleventh group.
        _c1_bucket = str(catorder.index("C1") + 1) if "C1" in catorder else "?"
        _c1_panels = [n for n, b in zip(dd["nums"], dd["buckets"]) if str(b) == _c1_bucket]
        print(f"    C1 Data Integrity is project category #{_c1_bucket}; panels in it: "
              f"{_c1_panels}")
        check(_c1_bucket == str(len(catorder)) and len(catorder) == 11,
              "C1 Data Integrity is the ELEVENTH project-level category in service",
              f"{_c1_bucket} of {len(catorder)}")
        check(sorted(_c1_panels) == sorted(["9.1", "9.2 to 9.7"]),
              "THE TWO DATA-QUALITY PANELS RENDER, AND THEY RENDER IN THE ELEVENTH GROUP, which "
              "could not exist before the loop bound was derived from the taxonomy",
              str(_c1_panels))
        check(_headmap.get(_c1_bucket) == catname.get("C1"),
              "and the eleventh group's header names Data Integrity",
              str(_headmap.get(_c1_bucket)))

        # RULING 3: the compliance panel is two panels, each holding only its own category.
        _b3 = str(catorder.index("B3") + 1)
        _a6 = str(catorder.index("A6") + 1)
        _split = [n for n in dd["nums"] if n in ("8.2 to 8.5", "8.6 to 8.9")]
        print(f"    the split compliance panels present: {_split}")
        check("8.2–8.9" not in dd["nums"] and "8.2 to 8.9" not in dd["nums"],
              "THE SINGLE EIGHT-MODULE COMPLIANCE PANEL IS GONE from the rendered surface",
              str([n for n in dd["nums"] if n.startswith("8.")]))
        check(sorted(_split) == ["8.2 to 8.5", "8.6 to 8.9"],
              "AND IT IS TWO PANELS, one per current category", str(_split))
        _split_buckets = {n: b for n, b in zip(dd["nums"], dd["buckets"]) if n in _split}
        check(_split_buckets.get("8.2 to 8.5") == _b3
              and _split_buckets.get("8.6 to 8.9") == _a6,
              "AND EACH HOLDS ONLY THE MODULES OF ITS OWN CATEGORY: the regulatory half sits "
              "under Regulatory and Authority Thresholds and the quality half under Delivery "
              "Quality Performance", str(_split_buckets))

        joined = dd["labels"] + dd["groupNames"] + dd["heads"]
        _dd_bad = g1([("deepdive", x) for x in joined], "deepdive")
        check(not _dd_bad,
              "NO RENDERED DEEP-DIVE LABEL, GROUP HEADER OR PANEL HEADING CARRIES AN IDENTIFIER, "
              "THE RETIRED SCHEME, AN AMPERSAND OR A DASH", str(_dd_bad[:6]))
        dd_svg = dd_page.evaluate("""() => Array.from(
            document.querySelectorAll('svg text, svg tspan, svg title')).map(t => t.textContent)""")
        print(f"    deep-dive SVG text nodes read: {len(dd_svg)}")
        all_bad += g1([("deepdive.svg", x) for x in dd_svg if x], "deepdive-svg")
        dd_page.close()

        print()
        print("=" * 94)
        print("3. GUARANTEE 1: THE VERDICT, AND EVERY SURVIVOR NAMED")
        print("=" * 94)
        # Syntactically significant or demonstrably not participant text. Each is NAMED, with
        # its reason, rather than filtered silently.
        EXCUSED = []

        def excuse(row):
            surface, where, label, hit, sample = row
            if label == "ampersand" and re.search(r"session_token|action=|&amp;", sample):
                return "a query-string separator, syntactically significant"
            return None

        named, survivors = [], []
        for row in all_bad:
            why = excuse(row)
            if why:
                named.append((row, why))
            else:
                survivors.append(row)
        print(f"    candidate hits: {len(all_bad)}   excused with a stated reason: {len(named)}"
              f"   SURVIVORS: {len(survivors)}")
        for row, why in named[:20]:
            print(f"      EXCUSED  [{row[0]}] {row[2]}: {row[3]!r} in {row[4]!r}  -- {why}")
        for row in survivors:
            print(f"      SURVIVOR [{row[0]}] {row[1]} {row[2]}: {row[3]!r} in {row[4]!r}")
        check(not survivors,
              "GUARANTEE 1: NO USER-FACING TEXT ON ANY RENDERED SURFACE, SVG TEXT NODES AND "
              "ACCESSIBLE NAMES INCLUDED, CARRIES A MODULE IDENTIFIER, A CATEGORY IDENTIFIER, "
              "THE RETIRED SCHEME, AN AMPERSAND, AN EM DASH OR AN EN DASH",
              str(survivors[:8]))

        print()
        print("=" * 94)
        print("4. NO UNCAUGHT PAGE ERROR")
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
