#!/usr/bin/env python3
"""
RUN 91. THE INDETERMINATE BRIEF, IN A REAL BROWSER.

Setup is drive_run82_charts.py's, verbatim, because it produces exactly the row this run needs:
A1 pressed for real and A4 stored, with A2, A3 and A6 left unassessed -- which under Run 89's
required-core gate is an INDETERMINATE project status. Everything below is read back from what
was DRAWN: the Signal Network's own scene graph and canvas pixels, the Signal Flow's rendered
SVG nodes and edges, and the Executive Brief's rendered DOM.

Measured at 1280px and at 1024px, as section 9.8 requires.
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
PID = f"PRJ-R91-{STAMP}"
ADMIN = f"run90-admin-{STAMP}"
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
        s.add(Participant(pseudonymous_code=f"R91-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 76 reproduction",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R91-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})

say("=" * 100); say(f"RUN 91  project={PID}  DATABASE_URL={os.environ.get('DATABASE_URL')}")
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
say(f"Python module layer: {len(mr)} module result rows stored")
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
                     "reason": "Awaiting the project's activity network"},
                    {"module_id": "A2.4", "state": "abstained", "value": None, "display": None,
                     "band": None, "band_asserted": False, "evidence_metric": None,
                     "reason": "No Schedule Update has been uploaded for this period, so there "
                               "is no data date and no total float to read. Upload a Schedule "
                               "Update to have this measure taken."}],
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


# ---- ONE MORE STORED ROW, so a SECOND band colour and a DISAGREEING category render ---------
# RUN 81's PRECEDENT, and it is labelled the same way: this writes stored rows DIRECTLY so that
# every state can be made to render on ONE page. It is a RENDERING VERIFICATION, not a
# measurement of what a model returns. There is no ANTHROPIC_API_KEY in this environment.
with Session() as s:
    proj = s.scalar(select(Project).where(Project.legacy_id == PID))
    # A CATEGORY WHOSE MODULES DISAGREE -- the owner's second "what it makes visible": several
    # lit green and one red, which must be visible at a glance on both charts.
    store_reading(s, proj.id, 1, {
        "category": "A4", "state": "computed", "status": "Red",
        "counts": {"computed": 4, "abstained": 6, "out_of_order": 0, "failed": 0},
        "modules": [
            {"module_id": "A4.2", "state": "computed", "value": 0.91, "display": "0.91",
             "band": "Green", "band_asserted": True, "evidence_metric": None, "reason": None},
            {"module_id": "A4.3", "state": "computed", "value": 0.78, "display": "0.78",
             "band": "Green", "band_asserted": True, "evidence_metric": None, "reason": None},
            {"module_id": "A4.6", "state": "computed", "value": 12, "display": "12",
             "band": "Yellow", "band_asserted": True, "evidence_metric": None, "reason": None},
            {"module_id": "A4.7", "state": "computed", "value": 3, "display": "3 open",
             "band": "Red", "band_asserted": True, "evidence_metric": None, "reason": None},
            {"module_id": "A4.10", "state": "abstained", "value": None, "display": None,
             "band": None, "band_asserted": False, "evidence_metric": None,
             "reason": "Awaiting a governed change register for this period."}],
        "reason": None, "missing_upstream": [], "served_by": "recorded", "model_id": "fixture"})
    # THE PROJECT'S SECTOR drives "not relevant". The taxonomy tags A4.4/A4.5/A4.8/A4.9 and
    # A6.2/A6.3 as construction-and-hybrid only, so a DESIGN project makes them NOT RELEVANT --
    # a declaration about the project TYPE, read from the taxonomy, not a reading invented here.
    # RUN 90, SECTION 3.3. THE COMMON CASE: a category whose modules COMPUTED and asserted NO
    # BAND. A5's own specification requires exactly this of every module in it ("All five in
    # service are bandless"), so this is the shape the platform really produces, not an invented
    # state. The category itself still carries NO POSTURE, which is what makes it the pair of
    # states the order asks to be told apart: unlit moons round an unassessed planet.
    store_reading(s, proj.id, 1, {
        "category": "A5", "state": "computed", "status": None,
        "counts": {"computed": 3, "abstained": 2, "out_of_order": 0, "failed": 0},
        "modules": [
            {"module_id": "A5.2", "state": "computed", "value": 0.42, "display": "0.42",
             "band": None, "band_asserted": False, "evidence_metric": None, "reason": None},
            {"module_id": "A5.4", "state": "computed", "value": 3, "display": "3 scenarios",
             "band": None, "band_asserted": False, "evidence_metric": None, "reason": None},
            {"module_id": "A5.6", "state": "computed", "value": 1.8, "display": "1.8",
             "band": None, "band_asserted": False, "evidence_metric": None, "reason": None},
            {"module_id": "A5.7", "state": "abstained", "value": None, "display": None,
             "band": None, "band_asserted": False, "evidence_metric": None,
             "reason": "Awaiting an agent supply chain model."}],
        "reason": None, "missing_upstream": [], "served_by": "recorded", "model_id": "fixture"})
    doc = dict(proj.doc or {}); doc["sector"] = "design"; proj.doc = doc
    s.commit()
    say(f"  project sector set to {doc['sector']!r} so the taxonomy's sector-excluded modules "
        f"render as NOT RELEVANT")

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

OPEN = r"""() => {
  if (window.LinApp && LinApp.showPage) { try { LinApp.showPage('detail'); } catch(e){} }
  ['d-brief'].forEach(id => {
    const h = document.querySelector('#section-' + id + ' .collapse-header');
    if (h) h.click();
  });
  return Array.from(document.querySelectorAll('.collapse-section')).map(s => s.id).join(',');
}"""

# WHAT THE BROWSER ACTUALLY HOLDS. The Run-89 Indeterminate branch is guarded on
# `ev.statusBasis`, which is `row.project_status_basis` off the row LinResults holds. If that
# field is absent in the browser the branch is dead and the generic branch renders instead.
ROW = r"""() => {
  const p = (window.LIN_PROJECTS || []).filter(x => x.id === window.__R91PID)[0]
            || (window.LinApp && LinApp.currentProject && LinApp.currentProject()) || null;
  const row = (window.LinResults && LinResults.rowFor) ? LinResults.rowFor(p || window.__R91PID) : null;
  const ev = (window.LinDetail && LinDetail.__briefForTest && LinDetail.__briefForTest.briefEvidence)
    ? (function(){ try { return LinDetail.__briefForTest.briefEvidence(p || window.__R91PID); }
                   catch(e){ return { error: String(e) }; } })() : null;
  return {
    haveProject: !!p,
    rowKeys: row ? Object.keys(row) : null,
    project_status: row ? row.project_status : null,
    project_status_basis: row ? row.project_status_basis : null,
    evStatusBasis: ev ? ev.statusBasis : null,
    evCategories: ev ? ev.categories : null,
    evModuleCount: ev && ev.modules ? ev.modules.length : null,
    briefTest: (window.LinDetail && LinDetail.__briefForTest) ? Object.keys(LinDetail.__briefForTest) : null
  };
}"""

BRIEF = r"""() => {
  const dec = document.querySelector('#section-d-decision');
  const decInfo = dec ? { present:true,
     heading: (dec.querySelector('.collapse-header') || {}).innerText || null,
     text: (dec.innerText || '').slice(0, 900),
     open: !!dec.querySelector('.collapse-body:not([hidden])'),
     controls: Array.from(dec.querySelectorAll('button, select, input, a[href]'))
       .map(e => ((e.textContent||e.value||e.name||'').trim().slice(0,60))).filter(Boolean).slice(0,25)
   } : { present:false };
  const sec = document.querySelector('#section-d-brief') || document.querySelector('#body-d-brief');
  if (!sec) return { present:false, ids: Array.from(document.querySelectorAll('[id^="section-"]')).map(e=>e.id) };
  const txt = sec.innerText || '';
  return { present:true, text: txt,
    buttons: Array.from(sec.querySelectorAll('button, a[href], [role="button"]')).map(e=>({t:(e.textContent||'').trim().slice(0,80), dis: e.disabled === true})),
    decisionCard: decInfo,
    briefMentionsDecision: /decision|how did you treat/i.test(txt),
    box: (()=>{const r=sec.getBoundingClientRect(); return {w:Math.round(r.width),h:Math.round(r.height)};})()
  };
}"""

# THE ROUTE, EXERCISED. Click whatever control the brief offers to reach the decision card and
# report where the page ended up. A route that leads nowhere is a finding, not a pass.
ROUTE = r"""async () => {
  const sec = document.querySelector('#section-d-brief');
  const btn = sec ? sec.querySelector('[data-brief-to-decision]') : null;
  if (!btn) return { control: null };
  btn.click();
  await new Promise(r => setTimeout(r, 700));
  const dec = document.querySelector('#section-d-decision');
  const body = dec ? dec.querySelector('.collapse-body') : null;
  return {
    control: (btn.textContent || '').trim(),
    decisionOpen: !!(body && getComputedStyle(body).display !== 'none'),
    decisionText: dec ? (dec.innerText || '').slice(0, 900) : null,
    decisionControls: dec ? Array.from(dec.querySelectorAll('button, select, input, textarea, a[href]'))
      .map(e => ((e.textContent||e.value||e.name||'').trim().slice(0,60))).filter(Boolean).slice(0,30) : null,
    scrolledTo: dec ? Math.round(dec.getBoundingClientRect().top) : null
  };
}"""

from playwright.sync_api import sync_playwright  # noqa: E402
OUT = pathlib.Path(os.environ.get("RUN91_OUT", "/tmp/run91"))
OUT.mkdir(parents=True, exist_ok=True)

def dump(tag, obj):
    (OUT / f"{tag}.json").write_text(json.dumps(obj, indent=1, default=str))

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME,
                           args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    for VW in (1280, 1024):
        say("=" * 100); say(f"VIEWPORT {VW}px")
        pg = b.new_page(viewport={"width": VW, "height": 3200})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                    "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            pg.route(pat, lambda r: r.abort())
        pg.goto(BASE + "/", wait_until="domcontentloaded")
        pg.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        pg.goto(BASE + "/", wait_until="domcontentloaded")
        pg.evaluate("(id) => { window.__R91PID = id; }", PID)
        pg.wait_for_timeout(9000)
        pg.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('detail')")
        pg.evaluate("(id) => window.LinDetail && LinDetail.render(id)", PID)
        pg.wait_for_timeout(14000)
        say(f"sections: {pg.evaluate(OPEN)[:400]}")
        pg.wait_for_timeout(5000)

        RES = post({"action": "projectresults", "session_token": PM, "id": PID, "period": 1})
        RR = RES.get("result") or {}
        say(f"SERVED  project_status={RR.get('project_status')!r}")
        say(f"SERVED  project_status_basis={json.dumps(RR.get('project_status_basis'), default=str)}")
        say(f"SERVED  categories with a status: "
            f"{ {k: v.get('status') for k, v in (RR.get('category_statuses') or {}).items()} }")

        R = pg.evaluate(ROW); dump(f"row_{VW}", R)
        say("-" * 100); say("WHAT THE BROWSER HOLDS")
        say(f"  haveProject={R.get('haveProject')}  briefForTest keys={R.get('briefTest')}")
        say(f"  row.project_status={R.get('project_status')!r}")
        say(f"  row.project_status_basis={json.dumps(R.get('project_status_basis'), default=str)}")
        say(f"  ev.statusBasis={json.dumps(R.get('evStatusBasis'), default=str)}")
        say(f"  ev.categories={json.dumps(R.get('evCategories'), default=str)}")

        B = pg.evaluate(BRIEF); dump(f"brief_{VW}", B)
        say("-" * 100); say("THE EXECUTIVE BRIEF, AS RENDERED")
        if not B.get("present"):
            say(f"  NOT FOUND  {B.get('ids')}")
        else:
            say(f"  box={B['box']}")
            say("  ---- RENDERED TEXT ----")
            for line in (B["text"] or "").splitlines():
                if line.strip():
                    say(f"  | {line.strip()}")
            say(f"  ---- controls inside the brief: {B['buttons']}")
            say(f"  ---- the brief's own text mentions a decision: {B.get('briefMentionsDecision')}")
            dc = B.get('decisionCard') or {}
            say(f"  ---- decision card present={dc.get('present')} open={dc.get('open')}")
            say(f"       controls: {dc.get('controls')}")
            for line in (dc.get('text') or '').splitlines():
                if line.strip():
                    say(f"       | {line.strip()}")

        RT = pg.evaluate(ROUTE); dump(f"route_{VW}", RT)
        say("-" * 100); say("THE ROUTE FROM THE BRIEF TO THE DECISION CARD")
        say(f"  control found: {RT.get('control')!r}")
        if RT.get("control"):
            say(f"  decision section open after click: {RT.get('decisionOpen')}")
            say(f"  decision section top after click (px): {RT.get('scrolledTo')}")
            say(f"  decision controls now exposed: {RT.get('decisionControls')}")
            for line in (RT.get('decisionText') or '').splitlines():
                if line.strip():
                    say(f"    | {line.strip()}")

        pg.screenshot(path=str(OUT / f"page_{VW}.png"), full_page=True)
        say(f"  screenshot -> {OUT}/page_{VW}.png")
        say(f"  PAGE ERRORS: {errs}")
        pg.close()
    b.close()
say("=" * 100); say("RUN 91 DRIVE COMPLETE")
