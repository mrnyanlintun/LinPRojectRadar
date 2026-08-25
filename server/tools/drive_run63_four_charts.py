#!/usr/bin/env python3
"""
RUN 63. THE FOUR CHARTS, MEASURED BEFORE ANYTHING IS CHANGED.

Section 5.1 of the Run 63 order: establish, BY EXECUTION, what each of the four surfaces
builds from, which period's row it reads, and every count it renders beside the value in the
stored row that count claims to describe.

THE VERIFICATION RULE (Run 61) IS FOLLOWED HERE. The project is LOADED FROM THE SERVER,
there is NO PRE-PRIMING -- this file never calls LinResults.prime -- the fixture's current
period is not 1, and the page is driven through LinDetail.render on the real load path.

THE FIXTURE REPRODUCES PRJ-001's SHAPE, which is what makes the document-count defect
appear at all: many documents uploaded across two periods, then `resetsignals` (which
supersedes every live row and appends `signals_reset` but DELETES NO DOCUMENT), then
`projectcomputeall` again -- which re-reads the retained documents and writes a fresh live
row WITHOUT appending any new `signals_extracted` event. A project in that state has
documents on file, a live computed row, and zero extraction events since the reset.

THE WebGL PANELS ARE OPENED ONE AT A TIME. Run 61 lost a session to three at once.

argv[1] = label   argv[2] = path to write the captured JSON to
"""
from __future__ import annotations
import base64, hashlib, json, logging, os, pathlib, socket, sys, threading, time

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run63"
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("run63_capture.json")
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
from app.research_models import Participant, ComputedResult  # noqa: E402
from app.simulation.registry import registry_index, service_index, CORE_VOTING_MODULES  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:300]}"
    return r.json()

def b64(raw): return base64.b64encode(raw).decode()

D = "PRJ-R63"
ADMIN = "run63-admin-token"
BAC = 4_000_000
END = {1: "2026-03-31", 2: "2026-04-30"}
P1 = {"ev": 1_000_000, "ac": 1_050_000, "pv": 1_020_000, "planned_pct": 25.50, "actual_pct": 25.00}
P2 = {"ev": 2_000_000, "ac": 2_100_000, "pv": 1_500_000, "planned_pct": 50.00, "actual_pct": 50.00}

# A DOCUMENT SET BIG ENOUGH TO TEST A DOCUMENT COUNT. The order is explicit that a fixture
# with a handful of documents cannot reproduce a document-count defect.
FILLER_TYPES = ["field_report", "inspection_report", "oac_minutes", "monthly_report",
                "change_order", "rfi_log", "submittal_register", "safety_report",
                "procurement_log", "ncr_log"]
DOCS = [
    ("contract", 1, "contract_value",
     {"original_contract_sum": BAC, "project_start_date": "2026-01-01",
      "project_end_date": "2027-06-30"}),
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
for i in range(30):
    per = 1 if i < 15 else 2
    DOCS.append((f"filler{i}", per, FILLER_TYPES[i % len(FILLER_TYPES)],
                 {"document_date": END[per]}))

def doc_bytes(tag): return f"%PDF-1.4 RUN63 {tag}\n".encode()

set_extractor_override(StubExtractor({
    hashlib.sha256(doc_bytes(t)).hexdigest(): (ty, ex) for t, _p, ty, ex in DOCS}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R63-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == D)) is None:
        s.add(Project(legacy_id=D, doc={"id": D, "name": "Run 63 four-charts fixture",
                                        "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R63-PM", "role": "Participant",
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

FIX = {"uploads": len(DOCS)}
_p = post({"action": "get", "session_token": PM, "id": D})
_doc = _p.get("project") or _p.get("doc") or {}
FIX["events_before_reset"] = len([e for e in (_doc.get("events") or [])
                                  if (e.get("event") or e.get("type")) == "signals_extracted"])

# THE RESET, then a RECOMPUTE. This is PRJ-001's shape.
rr = post({"action": "resetsignals", "session_token": PM, "id": D})
assert rr.get("ok") is True, str(rr)[:300]
assert post({"action": "projectcomputeall", "session_token": PM, "id": D}).get("ok") is True

_p = post({"action": "get", "session_token": PM, "id": D})
_doc = _p.get("project") or _p.get("doc") or {}
_evs = _doc.get("events") or []
_ridx = max([i for i, e in enumerate(_evs)
             if (e.get("event") or e.get("type")) == "signals_reset"], default=-1)
FIX["events_total"] = len(_evs)
FIX["extracted_total"] = len([e for e in _evs if (e.get("event") or e.get("type")) == "signals_extracted"])
FIX["extracted_since_reset"] = len([e for e in _evs[_ridx + 1:]
                                    if (e.get("event") or e.get("type")) == "signals_extracted"])
FIX["reset_index"] = _ridx

per = post({"action": "projectperiods", "session_token": PM, "id": D})
FIX["latest_computed_period"] = per.get("latest_computed_period")
res = post({"action": "projectresults", "session_token": PM, "id": D,
            "period": FIX["latest_computed_period"]})
ROW = res.get("result") or {}
sd = ROW.get("source_documents") or []
FIX["row_period"] = ROW.get("period")
FIX["row_source_documents"] = len(sd)
FIX["row_source_doc_types"] = sorted({d.get("doc_type") for d in sd if d.get("doc_type")})
FIX["row_signal_input_fields"] = len([k for k, v in (ROW.get("signal_inputs") or {}).items()
                                      if k not in ("sources", "events") and v not in (None, "")])
_mr = ROW.get("module_results") or []
FIX["row_module_results"] = len(_mr)
FIX["row_module_colors"] = {}
for m in _mr:
    c = m.get("status_color")
    FIX["row_module_colors"][c] = FIX["row_module_colors"].get(c, 0) + 1
_cs = ROW.get("category_statuses") or {}
FIX["row_category_statuses"] = {k: (v or {}).get("status") for k, v in _cs.items()}
FIX["row_categories_with_status"] = len([k for k, v in _cs.items() if (v or {}).get("status")])
FIX["row_project_status"] = ROW.get("project_status")

print("=" * 96)
print(f"LABEL: {LABEL}")
print(f"cwd:              {os.getcwd()}")
print(f"repository root:  {ROOT}")
print(f"DATABASE_URL:     {os.environ.get('DATABASE_URL')}")
print(f"registry: {len(registry_index())}  in service: {len(service_index())}  "
      f"core voting: {sorted(CORE_VOTING_MODULES)}")
print("-" * 96)
print("THE FIXTURE, AND THE STORED ROW IT PRODUCED (the authority for every count below):")
for k, v in FIX.items():
    print(f"  {k:32} {v}")
print("=" * 96)

sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn  # noqa: E402
cfg = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical")
server = uvicorn.Server(cfg)
threading.Thread(target=server.run, daemon=True).start()
for _ in range(200):
    try:
        c = socket.create_connection(("127.0.0.1", PORT), 0.2); c.close(); break
    except OSError:
        time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"

from playwright.sync_api import sync_playwright  # noqa: E402

CAP = {"label": LABEL, "fixture": FIX, "registry": len(registry_index()),
       "in_service": len(service_index())}

READ_JS = r"""() => {
  const q = (s) => document.querySelector(s);
  const txt = (s) => { const e = q(s); return e ? (e.innerText || '').trim() : null; };
  const badge = (sec) => { const e = q('#section-' + sec + ' .collapse-badge');
                           return e ? (e.textContent || '').trim() : null; };
  const svgText = (root) => root ? Array.from(root.querySelectorAll('text'))
                                     .map(t => (t.textContent||'').trim()).filter(Boolean) : [];
  const flow = q('.detail-neural-flow');
  return {
    badges: { neural: badge('d-neural'), projnet: badge('d-projnet'), web: badge('d-web'),
              ensemble: badge('d-ensemble'), docsignals: badge('d-docsignals') },
    flow_svg_text: svgText(flow),
    flow_text: flow ? (flow.innerText || '').trim() : null,
    projnet_text: txt('.projnet2d-panel'),
    projnet_svg_text: svgText(q('.projnet2d-panel')),
    web_sub: txt('.signal-web-panel .sw-vs'),
    web_footnote: txt('.signal-web-panel .sw-footnote'),
    web_eyebrow: txt('.signal-web-panel .eyebrow'),
    ens_eyebrow: txt('.ens-panel .eyebrow'),
    ens_sub: txt('.ens-panel .sw-vs'),
    docs_eyebrow: txt('.detail-uploads .eyebrow'),
    docs_rows: document.querySelectorAll('.detail-uploads .up-row').length
  };
}"""

ROW_JS = r"""(id) => {
  const p = (window.LIN_PROJECTS || []).filter(x => x.id === id)[0] || null;
  let row = null;
  try { row = (window.LinResults && LinResults.rowFor(p)) || null; } catch (e) {}
  const cs = (row && row.category_statuses) || {};
  return {
    page_holds_period: p && p.storedResult ? p.storedResult.period : null,
    row_period: row ? row.period : null,
    row_present: !!row,
    row_source_documents: row && row.source_documents ? row.source_documents.length : null,
    row_source_doc_types: row && row.source_documents
      ? Array.from(new Set(row.source_documents.map(d => d.doc_type).filter(Boolean))).sort() : null,
    row_module_results: row && row.module_results ? row.module_results.length : null,
    row_cats_with_status: Object.keys(cs).filter(k => cs[k] && cs[k].status).length,
    row_cat_statuses: Object.keys(cs).reduce((a,k)=>{a[k]=cs[k]&&cs[k].status;return a;},{}),
    project_events_total: p && p.events ? p.events.length : null,
    project_extracted_events: p && p.events
      ? p.events.filter(e => (e.type||e.event||e.kind) === 'signals_extracted').length : null,
    project_signalInputs_present: !!(p && p.signalInputs),
    project_simulationSignals_present: !!(p && p.simulationSignals),
    // Every module status, through the shared resolver, straight from the row.
    module_status_tally: (function () {
      const t = {};
      (window.projectLevelCategories ? projectLevelCategories() : []).forEach(c =>
        (c.modules||[]).forEach(m => {
          let s = null;
          try { s = window.getModuleStatus ? getModuleStatus(m.method_class, p) : null; } catch(e){}
          t[String(s)] = (t[String(s)]||0)+1;
        }));
      return t;
    })(),
    cat_status_via_resolver: (function () {
      const o = {};
      (window.projectLevelCategories ? projectLevelCategories() : []).forEach(c => {
        let s = null;
        try { s = window.getCategoryStatus ? getCategoryStatus(c.id, p) : null; } catch(e){}
        o[c.id] = s;
      });
      return o;
    })(),
    project_level_categories: (window.projectLevelCategories ? projectLevelCategories().length : null),
    project_module_total: (window.projectLevelCategories
      ? projectLevelCategories().reduce((n,c)=>n+((c.modules||[]).length),0) : null)
  };
}"""

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME,
                                 args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    page = browser.new_page(viewport={"width": 1680, "height": 3200})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
        page.route(pat, lambda r: r.abort())
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.add_style_tag(content="*,*::before,*::after{transition:none!important;animation:none!important}")
    page.wait_for_timeout(9000)

    base = page.evaluate("""() => ({
        pageSections: document.querySelectorAll('.page').length,
        demoTell: Array.from(document.scripts).map(s => s.src.split('/').pop())
                    .filter(s => s === 'api.js' || s === 'boot.js'),
        hasDetail: !!window.LinDetail })""")
    CAP["app_under_test"] = base
    print(f"DEng\\Demo tell -> .page sections: {base['pageSections']} (expected 7)   "
          f"api.js/boot.js in document.scripts: {base['demoTell']} (expected [])")

    page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('workspace')")
    page.wait_for_timeout(3000)
    page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('portfolio')")
    page.wait_for_timeout(1500)
    try:
        page.evaluate("() => window.LinApp && LinApp.buildFallbackList && LinApp.buildFallbackList()")
    except Exception:
        pass
    page.wait_for_timeout(1500)

    # ---- FIRST RENDER. No pre-priming by this harness. ----------------------------------
    page.evaluate("(id) => window.LinDetail && LinDetail.render(id)", D)
    page.wait_for_timeout(500)
    CAP["first_render"] = page.evaluate(READ_JS)
    page.wait_for_timeout(12000)
    CAP["settled"] = page.evaluate(READ_JS)
    CAP["row_state"] = page.evaluate(ROW_JS, D)

    # ---- ONE PANEL AT A TIME. -----------------------------------------------------------
    ORDER = ["d-docsignals", "d-projnet", "d-neural", "d-web", "d-ensemble"]
    CAP["panels"] = {}
    for sec in ORDER:
        page.evaluate("""(id) => { const b = document.getElementById('body-' + id);
            if (b && b.style.display === 'none' && window.toggleSection) toggleSection(id); }""", sec)
        page.wait_for_timeout(6000)
        CAP["panels"][sec] = page.evaluate(READ_JS)
        print(f"  opened {sec}")

    # ---- SECOND RENDER, Run 61's guard. -------------------------------------------------
    page.evaluate("(id) => window.LinDetail && LinDetail.render(id)", D)
    page.wait_for_timeout(9000)
    for sec in ORDER:
        page.evaluate("""(id) => { const b = document.getElementById('body-' + id);
            if (b && b.style.display === 'none' && window.toggleSection) toggleSection(id); }""", sec)
        page.wait_for_timeout(4000)
    CAP["second_render"] = page.evaluate(READ_JS)
    CAP["second_row_state"] = page.evaluate(ROW_JS, D)
    CAP["page_errors"] = errors
    browser.close()

server.should_exit = True
OUT.write_text(json.dumps(CAP, indent=2), encoding="utf-8")

FINAL = CAP["panels"]["d-ensemble"]
print()
print("=" * 96)
print("WHAT THE FOUR SURFACES RENDER, WITH EVERY WebGL PANEL OPEN (one at a time):")
print("=" * 96)
for k in ("badges", "flow_svg_text", "flow_text", "projnet_text", "projnet_svg_text",
          "web_eyebrow", "web_sub", "web_footnote", "ens_eyebrow", "ens_sub",
          "docs_eyebrow", "docs_rows"):
    print(f"  {k}:")
    print(f"      {FINAL.get(k)}")
print("=" * 96)
print("THE ROW EACH SURFACE IS DESCRIBING, read through LinResults on the same page:")
for k, v in CAP["row_state"].items():
    print(f"  {k:32} {v}")
print("=" * 96)
print(f"page errors: {errors}")
print(f"capture written to {OUT}")
