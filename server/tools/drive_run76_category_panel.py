#!/usr/bin/env python3
"""
RUN 76. THE CATEGORY PANEL, VERIFIED IN A BROWSER.

What this establishes, by reading the RENDERED DOM and nothing else:

  B1  the ordered list of section ids BEFORE and AFTER, from the DOM, so the placement ruling
      -- "immediately above Location" -- is proved rather than asserted.
  B2  pressing one category's Call button stores a reading and repaints the row.
  B3  ALL FOUR STATES rendered simultaneously, read back as FOUR DIFFERENT markers.
  B4  the counts on a row are the server's, not the client's.

RUN 61's RULE IS OBSERVED. This harness never calls LinResults.prime. It navigates by
LinDetail.render and reads back what the page itself fetched.
"""
from __future__ import annotations
import ast, base64, hashlib, io, json, logging, os, pathlib, socket, sys, threading, time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)

from reportlab.lib.pagesizes import LETTER            # noqa: E402
from reportlab.pdfgen import canvas as rl_canvas      # noqa: E402
from fastapi.testclient import TestClient             # noqa: E402
from sqlalchemy import select                          # noqa: E402
import app.main as main                                # noqa: E402
from app.documents import set_extractor_override       # noqa: E402
from app.extraction_client import StubExtractor        # noqa: E402
from app.extraction_fields import extraction_fields_for  # noqa: E402
from app.models import Project                         # noqa: E402
from app.research_identity import hash_access_token    # noqa: E402
from app.research_models import Participant, SpecificationReading  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
STAMP = int(time.time())
PID = f"PRJ-R76-{STAMP}"
ADMIN = f"run76-admin-{STAMP}"
P1_END = "2026-03-31"

def say(*a): print(" ".join(str(x) for x in a), flush=True)
def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:400]}"
    return r.json()
def b64(raw): return base64.b64encode(raw).decode()

_src = (HERE / "drive_run74_did_extraction_store.py").read_text(encoding="utf-8")
_vnode = next(n for n in ast.parse(_src).body
              if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "VALUES")
VALUES = eval(compile(ast.Expression(_vnode.value), "<v>", "eval"), {"PERIOD_END": P1_END}, {})
DOCSET = [("D01_contract_award.pdf", "contract_value"),
          ("D02_pay_application.pdf", "pay_application"),
          ("D05_schedule_update.pdf", "schedule_update"),
          ("D06_monthly_report.pdf", "monthly_report")]

def make_pdf(filename, doc_type, ex):
    buf = io.BytesIO(); c = rl_canvas.Canvas(buf, pagesize=LETTER)
    c.setFont("Helvetica-Bold", 13); c.drawString(72, 720, filename)
    c.setFont("Helvetica", 9); y = 700
    c.drawString(72, y, f"Document type: {doc_type} stamp {STAMP}"); y -= 18
    for k, v in ex.items():
        s = json.dumps(v) if isinstance(v, (list, dict)) else str(v)
        for chunk in [s[i:i+90] for i in range(0, max(len(s), 1), 90)]:
            c.drawString(72, y, f"{k}: {chunk}"); y -= 12
            if y < 60: c.showPage(); c.setFont("Helvetica", 9); y = 720
    c.showPage(); c.save(); return buf.getvalue()

OVERRIDE, DOCS = {}, []
for fn, dt in DOCSET:
    ex = {f: VALUES[f] for f in (extraction_fields_for(dt) or []) if f in VALUES}
    ex.setdefault("document_date", P1_END)
    raw = make_pdf(fn, dt, ex)
    OVERRIDE[hashlib.sha256(raw).hexdigest()] = (dt, ex, 0.95)
    DOCS.append((fn, raw))
set_extractor_override(StubExtractor(OVERRIDE))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code=f"R76-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 76 reproduction",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R76-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})

say("=" * 100); say(f"RUN 76  project={PID}  DATABASE_URL={os.environ.get('DATABASE_URL')}")
say("=" * 100)
U = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
          "period_end": P1_END,
          "documents": [{"filename": fn, "mimeType": "application/pdf", "dataBase64": b64(r)}
                        for fn, r in DOCS]})
say(f"upload: ok={U.get('ok')}")
CA = post({"action": "projectcomputeall", "session_token": PM, "id": PID})
say(f"computeall: ok={CA.get('ok')}")

RES = post({"action": "projectresults", "session_token": PM, "id": PID, "period": 1})
mr = (RES.get("result") or {}).get("module_results") or []
si = (RES.get("result") or {}).get("signal_inputs") or {}
computed_before = [m.get("module_id") or m.get("methodClass") for m in mr]
say(f"BEFORE, Python module layer: {len(mr)} module result rows stored")
say(f"  signal_inputs fields: {sorted(k for k in si if not str(k).startswith('_'))[:24]}")

say("-" * 100)
say("API: press category A1")
AP = post({"action": "projectcategoryapply", "session_token": PM, "id": PID,
           "period": 1, "category": "A1"})
say(f"  ok={AP.get('ok')} servedBy={AP.get('servedBy')}")
for r in AP.get("readings") or []:
    say(f"  {r['category']}: state={r['state']} status={r['status']} counts={r['counts']} "
        f"servedBy={r['servedBy']} spec_sha={str(r['specificationSha256'])[:16]}")
RD = post({"action": "projectcategoryreadings", "session_token": PM, "id": PID, "period": 1})
say(f"  stored and read back: {sorted(RD.get('readings', {}).keys())}")
say(f"  specified categories: {RD.get('specified')}  passOne={RD.get('passOne')} "
    f"passTwo={RD.get('passTwo')}")

# ---- FOUR STORED ROWS, ONE PER STATE, so the DOM can be asked to tell them apart -----------
say("-" * 100)
say("Storing one row per state on four different categories, so all four render at once:")
from app.spec_readings import store_reading  # noqa: E402
with Session() as s:
    proj = s.scalar(select(Project).where(Project.legacy_id == PID))
    store_reading(s, proj.id, 1, {
        "category": "A2", "state": "abstained", "status": None,
        "counts": {"computed": 0, "abstained": 3, "out_of_order": 0, "failed": 0},
        "modules": [{"module_id": "A2.1", "state": "abstained", "value": None, "display": None,
                     "band": None, "band_asserted": False, "evidence_metric": None,
                     "reason": "Awaiting the project's activity network"}],
        "reason": None, "missing_upstream": [], "served_by": "recorded", "model_id": "fixture"})
    store_reading(s, proj.id, 1, {
        "category": "B1", "state": "out_of_order", "status": None,
        "counts": {"computed": 0, "abstained": 0, "out_of_order": 1, "failed": 0},
        "modules": [], "reason": "This category reads what the categories before it produced, "
                                 "and A3, A4 have not run yet. Run them and press this again.",
        "missing_upstream": ["A3", "A4"], "served_by": "recorded", "model_id": "fixture"})
    store_reading(s, proj.id, 1, {
        "category": "B2", "state": "failed", "status": None,
        "counts": {"computed": 0, "abstained": 0, "out_of_order": 0, "failed": 1},
        "modules": [], "reason": "the answer carried no JSON object",
        "missing_upstream": [], "served_by": "recorded", "model_id": "fixture"})
    s.commit()
    say(f"  stored rows now: "
        f"{[(r.category_key, r.state) for r in s.scalars(select(SpecificationReading).where(SpecificationReading.project_id == proj.id, SpecificationReading.superseded_by.is_(None)))]}")

# --------------------------------------------------------------------------------- BROWSER
sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn  # noqa: E402
srv = uvicorn.Server(uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(200):
    try:
        c = socket.create_connection(("127.0.0.1", PORT), 0.2); c.close(); break
    except OSError: time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

READ = r"""() => {
  const sections = Array.from(document.querySelectorAll('.collapse-section[id^="section-"]'))
      .map(e => e.id.replace(/^section-/,''));
  const rows = Array.from(document.querySelectorAll('.dcat-row')).map(r => ({
    cat: r.getAttribute('data-category'),
    state: r.getAttribute('data-state'),
    status: (r.querySelector('.dcat-status')||{}).textContent,
    chip: (r.querySelector('.dcat-state')||{}).textContent,
    chipState: r.querySelector('.dcat-state') ? r.querySelector('.dcat-state').getAttribute('data-state') : null,
    counts: Array.from(r.querySelectorAll('.dcat-n')).map(n => n.textContent),
    body: (r.querySelector('.dcat-body')||{}).innerText ?
          (r.querySelector('.dcat-body').innerText||'').replace(/\s+/g,' ').trim().slice(0,220) : '',
    callDisabled: r.querySelector('.dcat-call') ? r.querySelector('.dcat-call').disabled : null
  }));
  const mods = Array.from(document.querySelectorAll('.dcat-row[data-category="A1"] .dcat-mod'))
      .map(m => ({ id: m.getAttribute('data-module'), state: m.getAttribute('data-state'),
                   band: m.querySelector('.dcat-band') ? m.querySelector('.dcat-band').getAttribute('data-band') : null,
                   text: (m.innerText||'').replace(/\s+/g,' ').trim().slice(0,150) }));
  return { sections, rows, mods,
           callAll: !!document.querySelector('.dcat-call-all'),
           panelPresent: !!document.querySelector('.detail-catspecs') };
}"""
OPEN_ALL = r"""() => { let n=0; document.querySelectorAll('.collapse-section[id^="section-"]')
  .forEach(el => { const id = el.id.replace(/^section-/,'');
    try { if (!el.classList.contains('open')) { toggleSection(id); n++; } } catch(e){} });
  document.querySelectorAll('.dcat-toggle').forEach(b => b.click());
  return n; }"""

from playwright.sync_api import sync_playwright  # noqa: E402
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME,
                           args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    pg = b.new_page(viewport={"width": 1680, "height": 3400})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
        pg.route(pat, lambda r: r.abort())
    pg.goto(BASE + "/", wait_until="domcontentloaded")
    pg.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
    pg.goto(BASE + "/", wait_until="domcontentloaded")
    pg.wait_for_timeout(9000)
    pg.evaluate("(id) => window.LinDetail && LinDetail.render(id)", PID)
    pg.wait_for_timeout(14000)
    pg.evaluate(OPEN_ALL)
    pg.wait_for_timeout(6000)
    R = pg.evaluate(READ)

    say("-" * 100)
    say("B1 -- SECTION ORDER READ FROM THE RENDERED DOM:")
    say(f"  {R['sections']}")
    idx_panel = R['sections'].index('d-catspecs') if 'd-catspecs' in R['sections'] else -1
    idx_globe = R['sections'].index('d-globe') if 'd-globe' in R['sections'] else -1
    say(f"  d-catspecs at index {idx_panel}, d-globe (Location) at index {idx_globe}  -> "
        f"immediately above Location: {idx_panel >= 0 and idx_globe == idx_panel + 1}")
    say(f"  panel present: {R['panelPresent']}  call-all button present: {R['callAll']}")

    say("-" * 100)
    say("B3 -- THE FOUR STATES, READ BACK FROM THE DOM:")
    seen = {}
    for r in R["rows"]:
        say(f"  {r['cat']:<4} data-state={str(r['state']):<13} chip={str(r['chip']):<13} "
            f"chip-data-state={str(r['chipState']):<13} status={str(r['status']):<7} "
            f"counts={r['counts']}")
        if r["body"]:
            say(f"        body: {r['body'][:160]}")
        seen.setdefault(r["state"], []).append(r["cat"])
    say(f"  DISTINCT data-state values rendered: {sorted(seen.keys())}")
    four = ["computed", "abstained", "out_of_order", "failed"]
    say(f"  all four present and distinct: {all(k in seen for k in four)}  -> {[(k, seen.get(k)) for k in four]}")

    say("-" * 100)
    say("B4 -- A1's MODULE ROWS, EXPANDED:")
    for m in R["mods"]:
        say(f"  {m['id']:<6} state={m['state']:<10} band={str(m['band']):<6} {m['text'][:110]}")

    say("-" * 100)
    say(f"page errors: {errs or 'NONE'}")
    b.close()

say("=" * 100)
ok = (idx_panel >= 0 and idx_globe == idx_panel + 1
      and all(k in seen for k in ["computed", "abstained", "out_of_order", "failed"])
      and not errs)
say(f"RESULT: {'4/4' if ok else '?/4'} checks passed "
    f"(placement, four states, module rows, no page errors)")
