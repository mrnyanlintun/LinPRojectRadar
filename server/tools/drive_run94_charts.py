#!/usr/bin/env python3
"""
RUN 90. THE TWO CHARTS AND THE INDETERMINATE BRIEF, IN A REAL BROWSER.

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
from app.simulation import registry as _REG95                       # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
STAMP = int(time.time())
PID = f"PRJ-R94-{STAMP}"
ADMIN = f"run94-admin-{STAMP}"
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
        s.add(Participant(pseudonymous_code=f"R94-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 76 reproduction",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R94-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})

say("=" * 100); say(f"RUN 94  project={PID}  DATABASE_URL={os.environ.get('DATABASE_URL')}")
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
  ['d-neural','d-projnet'].forEach(id => {
    const sec = document.querySelector('#section-' + id);
    if (!sec) return;
    if (!sec.classList.contains('open')) {
      const h = sec.querySelector('.collapse-header'); if (h) h.click();
    }
  });
  return Array.from(document.querySelectorAll('.collapse-section')).map(s => s.id).join(',');
}"""

SETTHEME = r"""(t) => { document.body.setAttribute('data-theme', t);
  try { if (window.LIN_STATUS_COLORS && LIN_STATUS_COLORS.refresh) LIN_STATUS_COLORS.refresh(); } catch(e){}
  return document.body.getAttribute('data-theme'); }"""

# ---- THE HEADLINE MEASUREMENT. Every rendered <text> in the Signal Flow SVG, its bounding
# ---- box read from the browser, compared pairwise. Not an inspection of the algorithm.
LABELS = r"""() => {
  const host = document.querySelector('.detail-neural-flow');
  const svg = host ? host.querySelector('svg') : null;
  if (!svg) return { present:false };
  const els = Array.from(svg.querySelectorAll('text'));
  const L = els.map((t,i) => {
    const r = t.getBoundingClientRect();
    return { i, txt:(t.textContent||'').trim(), cls:t.getAttribute('class')||'',
             kind:(t.closest('g[data-kind]')||{getAttribute:()=>null}).getAttribute('data-kind'),
             x:r.x, y:r.y, w:r.width, h:r.height };
  }).filter(o => o.txt.length && o.w > 0 && o.h > 0);
  const pairs = [];
  for (let a=0;a<L.length;a++) for (let b=a+1;b<L.length;b++) {
    const A=L[a],B=L[b];
    const ox = Math.min(A.x+A.w,B.x+B.w) - Math.max(A.x,B.x);
    const oy = Math.min(A.y+A.h,B.y+B.h) - Math.max(A.y,B.y);
    if (ox > 0.5 && oy > 0.5) pairs.push({ a:A.txt, b:B.txt, ka:A.kind, kb:B.kind,
      ox:Math.round(ox*10)/10, oy:Math.round(oy*10)/10 });
  }
  return { present:true, n:L.length, overlaps:pairs.length, sample:pairs.slice(0,25),
           labels:L.map(o=>({t:o.txt,k:o.kind,x:Math.round(o.x),y:Math.round(o.y),
                             w:Math.round(o.w),h:Math.round(o.h)})) };
}"""

FLOW = r"""() => {
  const host = document.querySelector('.detail-neural-flow');
  const svg = host ? host.querySelector('svg') : null;
  if (!svg) return { present:false, hostHTML: host ? host.innerHTML.slice(0,300) : null };
  const paths = Array.from(svg.querySelectorAll('path[data-edge-type]')).map(p => ({
    type: p.getAttribute('data-edge-type'), src: p.getAttribute('data-edge-src'),
    dst: p.getAttribute('data-edge-dst'), term: p.getAttribute('data-edge-terminates'),
    marker: p.getAttribute('marker-end') || null
  }));
  const cats = Array.from(svg.querySelectorAll('g[data-kind="category"]')).map(g => {
    const c = g.querySelector('[data-status]'); const t = g.querySelector('text');
    return { label: t ? t.textContent : null, status: c ? c.getAttribute('data-status') : null,
             active: c ? c.getAttribute('data-active') : null };
  });
  const mods = Array.from(svg.querySelectorAll('g[data-kind="module"]')).map(g => {
    const t = g.querySelector('text'); const c = g.querySelector('[data-status]');
    return { name: t ? t.textContent : null, status: c ? c.getAttribute('data-status') : null };
  });
  const docs = Array.from(svg.querySelectorAll('g[data-kind="document"]')).length;
  const prj = svg.querySelector('#lnf-prj');
  const termini = Array.from(svg.querySelectorAll('[data-kind="stream-terminus"]'))
    .map(e => e.getAttribute('data-edge-src'));
  const box = svg.getBoundingClientRect();
  const cs = getComputedStyle(document.body);
  const theme = ['--page-bg','--surface','--line','--text','--muted','--faint','--accent',
                 '--flow-accent','--status-green','--status-red','--status-nodata']
    .reduce((o,k)=>(o[k]=cs.getPropertyValue(k).trim(),o),{});
  return { present:true, paths, cats, mods, docs, termini, theme,
    prjText: prj ? Array.from(prj.querySelectorAll('text')).map(t=>t.textContent) : null,
    headers: Array.from(svg.querySelectorAll('text.lnf-hdr-arch, text.lnf-hdr-activity')).map(t=>t.textContent),
    viewBox: svg.getAttribute('viewBox'),
    bodyOverflowX: document.documentElement.scrollWidth > window.innerWidth + 2,
    box: { w: Math.round(box.width), h: Math.round(box.height) } };
}"""

# ---- RUN 94b. THE THREE MEASUREMENTS THIS RUN IS JUDGED ON, all read from what was DRAWN:
# ---- (1) every module label rendered in full, no ellipsis, inside its own column;
# ---- (2) the identity colours actually painted on the drawn rings, in DRAWN ROW ORDER, and
# ----     the smallest CIE76 dE*ab between any two adjacent ones and between any one and a
# ----     band colour read from the live theme;
# ---- (3) the module names drawn, so a retired name can be caught by its TEXT and not by a grep.
IDENT = r"""() => {
  const host = document.querySelector('.detail-neural-flow');
  const svg = host ? host.querySelector('svg') : null;
  if (!svg) return { present:false };
  const groups = Array.from(svg.querySelectorAll('g[data-kind="module"]'));
  const rows = groups.map(g => {
    const t = g.querySelector('text');
    const ring = g.querySelector('[data-kind="module-identity"]');
    const r = t ? t.getBoundingClientRect() : null;
    return { text: t ? (t.textContent||'') : null,
             id: ring ? ring.getAttribute('data-module') : null,
             color: ring ? ring.getAttribute('data-identity-color') : null,
             x: r ? r.x : null, right: r ? r.x + r.width : null, w: r ? r.width : null,
             y: r ? r.y : null };
  });
  rows.sort((a,b) => (a.y||0) - (b.y||0));
  const cats = Array.from(svg.querySelectorAll('[data-kind="category-identity"]'))
    .map(e => ({ id: e.getAttribute('data-category'), color: e.getAttribute('data-identity-color') }));
  const docs = Array.from(svg.querySelectorAll('[data-kind="document-identity"]'))
    .map(e => ({ id: e.getAttribute('data-document'), color: e.getAttribute('data-identity-color') }));
  // The leftmost rendered CATEGORY label, in the same client coordinates, so "the module
  // column fits its text" is a comparison of two measured boxes and not of two constants.
  let catLeft = Infinity;
  Array.from(svg.querySelectorAll('g[data-kind="category"] text')).forEach(t => {
    const r = t.getBoundingClientRect(); if (r.width > 0) catLeft = Math.min(catLeft, r.x);
  });
  const dE = window.LIN_COLOR_DELTA_E;
  function minAdj(list) {
    let m = null, pair = null;
    for (let i=1;i<list.length;i++) {
      const d = dE(list[i-1].color, list[i].color);
      if (d !== null && (m === null || d < m)) { m = d; pair = [list[i-1].id, list[i].id]; }
    }
    return { min: m, pair };
  }
  function minAny(list) {
    let m = null, pair = null;
    for (let i=0;i<list.length;i++) for (let j=i+1;j<list.length;j++) {
      const d = dE(list[i].color, list[j].color);
      if (d !== null && (m === null || d < m)) { m = d; pair = [list[i].id, list[j].id]; }
    }
    return { min: m, pair };
  }
  const bandNames = Object.keys(window.LIN_STATUS_COLORS || {});
  const bands = bandNames.map(k => ({ id: k, color: window.LIN_STATUS_COLORS[k] }));
  function minBand(list) {
    let m = null, pair = null;
    list.forEach(o => bands.forEach(b => {
      const d = dE(o.color, b.color);
      if (d !== null && (m === null || d < m)) { m = d; pair = [o.id, b.id]; }
    }));
    return { min: m, pair };
  }
  const withColor = rows.filter(r => r.color);
  return { present:true,
    n: rows.length,
    truncated: rows.filter(r => r.text && r.text.indexOf('\u2026') >= 0).map(r => r.text),
    names: rows.map(r => r.text),
    colored: withColor.length,
    maxLabelRight: Math.max(...rows.filter(r=>r.right!=null).map(r => r.right)),
    catLabelLeft: (catLeft === Infinity ? null : catLeft),
    moduleAdj: minAdj(withColor), moduleAny: minAny(withColor), moduleBand: minBand(withColor),
    catAdj: minAdj(cats), catBand: minBand(cats),
    docAdj: minAdj(docs), docBand: minBand(docs),
    bands: bands,
    formula: (window.LinNeuralFlow && window.LinNeuralFlow.lastPalette && window.LinNeuralFlow.lastPalette()
              && window.LinNeuralFlow.lastPalette().module)
              ? window.LinNeuralFlow.lastPalette().module.formula : null };
}"""

NET = r"""async () => {
  const host = document.querySelector('.detail-projnet2d');
  const cv = host ? host.querySelector('canvas.projnet2d-canvas') : null;
  if (!host || !cv) return { present: false };
  const hash = (c) => {
    const g = c.getContext('2d');
    const d = g.getImageData(0, 0, c.width, c.height).data;
    let h = 2166136261 >>> 0, nonblank = 0; const seen = new Set();
    const bg = [d[0], d[1], d[2]];
    for (let i = 0; i < d.length; i += 4) {
      if (Math.abs(d[i]-bg[0]) + Math.abs(d[i+1]-bg[1]) + Math.abs(d[i+2]-bg[2]) > 12) nonblank++;
      if (seen.size < 4000) seen.add(d[i]+','+d[i+1]+','+d[i+2]);
      h ^= d[i]; h = Math.imul(h,16777619)>>>0; h ^= d[i+1]; h = Math.imul(h,16777619)>>>0;
      h ^= d[i+2]; h = Math.imul(h,16777619)>>>0;
    }
    return { hash: ('00000000'+h.toString(16)).slice(-8), ink: nonblank, distinct: seen.size,
             bg: bg.join(','), w:c.width, h:c.height };
  };
  await new Promise(r => setTimeout(r, 250));
  const shot = hash(cv);
  const scene = (window.LinProjectNet2D && LinProjectNet2D.lastScene) ? LinProjectNet2D.lastScene() : null;
  return { present:true, shot, scene,
    note: (host.querySelector('.projnet2d-note')||{}).textContent || null,
    attrs: ['modules','modules-lit','categories','categories-lit','edges','health','scene-bodies']
           .reduce((o,k)=>(o[k]=host.getAttribute('data-'+k),o),{}) };
}"""

from playwright.sync_api import sync_playwright  # noqa: E402
OUT = pathlib.Path(os.environ.get("RUN94_OUT", "/tmp/run94"))
OUT.mkdir(parents=True, exist_ok=True)
def dump(tag, obj): (OUT / f"{tag}.json").write_text(json.dumps(obj, indent=1, default=str))

from app.theme import THEMES  # noqa: E402
EXTRA = ("dark",)   # archived in theme.py; still renders if forced
ALL_THEMES = list(THEMES) + list(EXTRA)
say(f"THEME AUTHORITY server/app/theme.py THEMES = {THEMES}; archived-but-renderable: {EXTRA}")

TOTAL_OVERLAPS = {}
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
        pg.wait_for_timeout(9000)
        pg.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('detail')")
        pg.evaluate("(id) => window.LinDetail && LinDetail.render(id)", PID)
        pg.wait_for_timeout(14000)
        say(f"sections: {pg.evaluate(OPEN)[:200]}")
        pg.wait_for_timeout(6000)

        for TH in ALL_THEMES:
            say("-" * 100)
            say(f"THEME {TH}  (set: {pg.evaluate(SETTHEME, TH)})")
            pg.evaluate("(id) => window.LinDetail && LinDetail.render(id)", PID)
            pg.wait_for_timeout(4000)
            pg.evaluate(OPEN)
            pg.wait_for_timeout(3500)

            L = pg.evaluate(LABELS); dump(f"labels_{VW}_{TH}", L)
            if not L.get("present"):
                say("  SIGNAL FLOW NOT RENDERED"); continue
            TOTAL_OVERLAPS[(VW, TH)] = L["overlaps"]
            say(f"  SIGNAL FLOW labels rendered: {L['n']}   OVERLAPPING LABEL PAIRS: {L['overlaps']}")
            for p in L["sample"]:
                say(f"    OVERLAP {p['ka']}:{p['a'][:34]!r} x {p['kb']}:{p['b'][:34]!r} "
                    f"ox={p['ox']} oy={p['oy']}")

            F = pg.evaluate(FLOW); dump(f"flow_{VW}_{TH}", F)
            if F.get("present"):
                say(f"  viewBox={F['viewBox']} box={F['box']} pageOverflowX={F['bodyOverflowX']}")
                say(f"  docs={F['docs']} modules={len(F['mods'])} categories={len(F['cats'])}")
                say(f"  headers: {F['headers']}")
                say(f"  category labels: {[c['label'] for c in F['cats']]}")
                catp = [p for p in F["paths"] if p["type"] == "CATEGORY -> PROJECT STATUS"]
                for p in catp:
                    say(f"    STREAM {p['src']:<42} terminates={p['term']:<10} "
                        f"arrowhead={'yes' if p['marker'] else 'no'}")
                say(f"  drawn blunt termini: {F['termini']}")
                say(f"  centre node text: {F['prjText']}")
                say(f"  THEME VALUES READ AT RUNTIME: {F['theme']}")
                RETNAMES = {"DSM Rework Propagation", "Rework Feedback Loop", "What-If Scenario Matrix"}
                drawn = set(m["name"] for m in F["mods"] if m["name"])
                say(f"  RETIRED MODULE LABELS DRAWN: {sorted(n for n in drawn if n in RETNAMES)} (must be empty)")

            I = pg.evaluate(IDENT); dump(f"ident_{VW}_{TH}", I)
            if I.get("present"):
                say(f"  MODULE LABELS DRAWN: {I['n']}  with an identity ring: {I['colored']}")
                say(f"  TRUNCATED LABELS (must be empty): {I['truncated']}")
                say(f"  longest module label right edge={I['maxLabelRight']:.1f}px  "
                    f"category label left edge={I['catLabelLeft']}  "
                    f"fits={'YES' if I['catLabelLeft'] and I['maxLabelRight'] < I['catLabelLeft'] else 'NO'}")
                say(f"  COLOUR FORMULA: {I['formula']}")
                for nm, k in (("module", "moduleAdj"), ("category", "catAdj"), ("document", "docAdj")):
                    o = I[k]
                    say(f"  smallest dE between ADJACENT {nm} colours: "
                        f"{'n/a' if o['min'] is None else round(o['min'],2)}  {o['pair']}")
                say(f"  smallest dE between ANY TWO module colours: "
                    f"{round(I['moduleAny']['min'],2) if I['moduleAny']['min'] is not None else 'n/a'} "
                    f"{I['moduleAny']['pair']}")
                for nm, k in (("module", "moduleBand"), ("category", "catBand"), ("document", "docBand")):
                    o = I[k]
                    say(f"  smallest dE between a {nm} colour and a BAND colour: "
                        f"{'n/a' if o['min'] is None else round(o['min'],2)}  {o['pair']}")
                say(f"  band colours read from the live theme: "
                    f"{ {b['id']: b['color'] for b in I['bands']} }")

            SHOT = r"""() => { const c=document.querySelector('canvas.projnet2d-canvas');
                    return c ? c.toDataURL('image/png') : null; }"""
            try:
                du = pg.evaluate(SHOT)
                if du:
                    (OUT / f"net_{VW}_{TH}.png").write_bytes(base64.b64decode(du.split(",",1)[1]))
            except Exception as _e: say(f"  canvas grab failed: {_e}")
            try:
                el = pg.query_selector(".detail-neural-flow svg")
                if el: el.screenshot(path=str(OUT / f"flow_{VW}_{TH}.png"), timeout=15000)
            except Exception as _e: say(f"  flow shot failed: {_e}")
            N = pg.evaluate(NET); dump(f"net_{VW}_{TH}", N)
            if not N.get("present"):
                say("  SIGNAL NETWORK NOT RENDERED")
            else:
                sc = N["scene"] or {}
                bodies = sc.get("bodies") or []
                planets = [x for x in bodies if x["kind"] == "planet"]
                moons = [x for x in bodies if x["kind"] == "moon"]
                sun = [x for x in bodies if x["kind"] == "health"]
                st = {}
                for m in moons: st[m["state"]] = st.get(m["state"], 0) + 1
                say(f"  SIGNAL NETWORK canvas bg={N['shot']['bg']} ink={N['shot']['ink']} "
                    f"distinct-colours={N['shot']['distinct']} hash={N['shot']['hash']}")
                say(f"  planets={len(planets)} moons={len(moons)} sun={sun}")
                say(f"  MODEL planet radii (size encodes nothing): {sorted(set(p['baseR'] for p in planets))}")
                say(f"  MODEL moon orbit radii (radius encodes nothing): {sorted(set(round(m['orbitR'],3) for m in moons))}")
                say(f"  moon orbital rates (speed encodes nothing): {sorted(set(round(m['orbitRate'],4) for m in moons))}")
                say(f"  planet states: {[(p['key'],p['state'],p['status']) for p in planets]}")
                say(f"  moon states: {st}")
                # RUN 95. THE RETIRED SET IS READ FROM THE REGISTRY, NOT TYPED.
                # It said {'A5.1','A5.5','B4.4'} -- Run 89's three. Run 95 retired fifteen more
                # and a typed set would have gone on passing while drawing every one of them,
                # which is precisely the vacuity this driver exists to defeat. The oracle is
                # `registry.retired_modules()`, and the assertion is over DRAWN moon keys.
                _RETIRED = set(_REG95.retired_modules())
                say(f"  RETIRED MODULES THE REGISTRY DECLARES: {len(_RETIRED)}")
                say(f"  RETIRED MOONS DRAWN: {sorted(set(m['key'] for m in moons) & _RETIRED)} (must be empty)")
                # RUN 95, SECTION 4.1. EVERY PLANET CARRIES ITS CATEGORY'S NAME, read back from
                # the scene graph's own record of the text that was drawn -- not from the source
                # file, and not from the taxonomy the chart was given.
                _labels = sc.get("labels") or []
                say(f"  PLANET NAME LABELS DRAWN: {len(_labels)} for {len(planets)} planets")
                for _l in _labels:
                    say(f"    PLANET {_l['key']:4s} labelled {_l['lines']!r}"
                        f"  (name={_l['name']!r})")
                _unlabelled = [p['key'] for p in planets
                               if not any(l['key'] == p['key'] and l['name'] for l in _labels)]
                say(f"  PLANETS WITH NO NAME LABEL (must be empty): {_unlabelled}")
                _joined = {l['key']: " ".join(l['lines']) for l in _labels}
                say(f"  LABEL TEXT EQUALS THE CATEGORY NAME (must be empty if all agree): "
                    f"{[k for k, v in _joined.items() if v != dict((l['key'], l['name']) for l in _labels)[k]]}")
                say(f"  'Systems' OR 'Dynamics' DRAWN ANYWHERE ON THIS CHART (must be empty): "
                    f"{[k for k, v in _joined.items() if 'Systems' in v or 'Dynamics' in v]}")
                say(f"  MOONS CARRYING AN IDENTITY COLOUR: "
                    f"{sum(1 for m in moons if m.get('identityColor'))} of {len(moons)}; "
                    f"distinct rim colours drawn: {len(set(m.get('identityColor') for m in moons))}")
                say(f"  attrs: {N['attrs']}")
                say(f"  note: {N['note']}")
        # ---------------------------------------------------- RUN 96, GOAL THREE
        # THE TWO BRANCH LAYERS, READ BACK OUT OF THE RENDERED SVG ATTRIBUTES.
        # Not asserted from the source file: these are the attributes the browser holds after
        # the chart drew itself, at this viewport.
        BRANCHES = r"""() => {
          const grab = (t) => Array.from(document.querySelectorAll(
              '[data-edge-type="' + t + '"]')).map(e => ({
            op: e.getAttribute('opacity'),
            w: e.getAttribute('stroke-width'),
            cls: e.getAttribute('class') || '',
            term: e.getAttribute('data-edge-terminates')
          }));
          const cat = Array.from(document.querySelectorAll('[data-edge-terminates]')).map(e => ({
            term: e.getAttribute('data-edge-terminates'),
            op: e.getAttribute('opacity'),
            dash: e.getAttribute('stroke-dasharray'),
            marker: e.getAttribute('marker-end') || ''
          }));
          const tally = (rows) => {
            const m = {};
            rows.forEach(r => { const k = r.op + ' @ ' + r.w + 'px'; m[k] = (m[k]||0)+1; });
            return m;
          };
          return { docMod: tally(grab('DOCUMENT -> MODULE')),
                   modCat: tally(grab('MODULE -> CATEGORY')),
                   nDocMod: grab('DOCUMENT -> MODULE').length,
                   nModCat: grab('MODULE -> CATEGORY').length,
                   catStatus: cat };
        }"""
        try:
            _b = pg.evaluate(BRANCHES)
            say("  " + "=" * 70)
            say(f"  RUN 96 GOAL THREE, RENDERED BRANCH ATTRIBUTES AT {VW}px")
            say(f"    DOCUMENT -> MODULE  n={_b['nDocMod']}  opacity@width: {_b['docMod']}")
            say(f"    MODULE   -> CATEGORY n={_b['nModCat']} opacity@width: {_b['modCat']}")
            _dm = set(_b['docMod']); _mc = set(_b['modCat'])
            say(f"    THE TWO LAYERS USE THE SAME OPACITY/STROKE TREATMENT: "
                f"{_dm == _mc}   (doc->mod {sorted(_dm)} / mod->cat {sorted(_mc)})")
            _terms = {}
            for _c in _b['catStatus']:
                _k = (_c['term'], _c['op'], bool(_c['dash']), bool(_c['marker']))
                _terms[_k] = _terms.get(_k, 0) + 1
            say(f"    CATEGORY -> STATUS terminations (must be unchanged: "
                f"'at-centre' with a marker, 'short' dashed without one): {_terms}")
            say(f"    STATE OPACITY 0.14 STILL PRESENT ON AN UNESTIMABLE mod->cat LINE: "
                f"{any('0.14' in k for k in _b['modCat'])}")
        except Exception as _e:                                        # noqa: BLE001
            say(f"  RUN 96 BRANCH MEASUREMENT FAILED: {_e}")
        say(f"  PAGE ERRORS: {errs}")
        pg.close()
    b.close()
say("=" * 100)
say("OVERLAP SUMMARY (viewport, theme) -> overlapping label pairs:")
for k in sorted(TOTAL_OVERLAPS): say(f"  {k}: {TOTAL_OVERLAPS[k]}")
say(f"MAX OVERLAPS ACROSS ALL RENDERS: {max(TOTAL_OVERLAPS.values()) if TOTAL_OVERLAPS else 'n/a'}")
say("RUN 94 DRIVE COMPLETE")
