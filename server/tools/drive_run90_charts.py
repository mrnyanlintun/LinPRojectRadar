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

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
STAMP = int(time.time())
PID = f"PRJ-R90-{STAMP}"
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
        s.add(Participant(pseudonymous_code=f"R90-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 76 reproduction",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R90-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})

say("=" * 100); say(f"RUN 90  project={PID}  DATABASE_URL={os.environ.get('DATABASE_URL')}")
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
  ['d-neural','d-projnet','d-brief'].forEach(id => {
    const h = document.querySelector('#section-' + id + ' .collapse-header');
    if (h) h.click();
  });
  return Array.from(document.querySelectorAll('.collapse-section')).map(s => s.id).join(',');
}"""

# ---------------------------------------------------------------- GOAL ONE: THE SOLAR SYSTEM
NET = r"""async () => {
  const host = document.querySelector('.detail-projnet2d');
  const cv = host ? host.querySelector('canvas.projnet2d-canvas') : null;
  if (!host || !cv) return { present: false };
  const hash = (c) => {
    const g = c.getContext('2d');
    const d = g.getImageData(0, 0, c.width, c.height).data;
    let h = 2166136261 >>> 0, nonblank = 0;
    const bg = [d[0], d[1], d[2]];
    for (let i = 0; i < d.length; i += 4) {
      if (Math.abs(d[i]-bg[0]) + Math.abs(d[i+1]-bg[1]) + Math.abs(d[i+2]-bg[2]) > 12) nonblank++;
      h ^= d[i]; h = Math.imul(h,16777619)>>>0; h ^= d[i+1]; h = Math.imul(h,16777619)>>>0;
      h ^= d[i+2]; h = Math.imul(h,16777619)>>>0;
    }
    return { hash: ('00000000'+h.toString(16)).slice(-8), ink: nonblank, w:c.width, h:c.height };
  };
  const before = hash(cv);
  const r0 = cv.getBoundingClientRect();
  cv.dispatchEvent(new MouseEvent('mousedown', {clientX:r0.x+100, clientY:r0.y+100, bubbles:true}));
  window.dispatchEvent(new MouseEvent('mousemove', {clientX:r0.x+260, clientY:r0.y+160, bubbles:true}));
  window.dispatchEvent(new MouseEvent('mouseup', {bubbles:true}));
  await new Promise(r => setTimeout(r, 300));
  const after = hash(cv);
  const scene = (window.LinProjectNet2D && LinProjectNet2D.lastScene) ? LinProjectNet2D.lastScene() : null;
  return { present:true, before, after, scene,
    note: (host.querySelector('.projnet2d-note')||{}).textContent || null,
    attrs: ['modules','modules-lit','modules-unbanded','modules-dark','modules-na',
            'modules-notcalled','categories','categories-lit','edges','health',
            'scene-bodies','scene-edges']
           .reduce((o,k)=>(o[k]=host.getAttribute('data-'+k),o),{}),
    box: (()=>{const r=cv.getBoundingClientRect(); return {w:Math.round(r.width),h:Math.round(r.height)};})()
  };
}"""

# ---------------------------------------------------------------- GOAL TWO: THE CONVERGENCE
FLOW = r"""() => {
  const host = document.querySelector('.detail-neural-flow');
  const svg = host ? host.querySelector('svg') : null;
  if (!svg) return { present:false, hostHTML: host ? host.innerHTML.slice(0,300) : null };
  const paths = Array.from(svg.querySelectorAll('path[data-edge-type]')).map(p => ({
    type: p.getAttribute('data-edge-type'), src: p.getAttribute('data-edge-src'),
    dst: p.getAttribute('data-edge-dst'), term: p.getAttribute('data-edge-terminates'),
    marker: p.getAttribute('marker-end') || null, d: p.getAttribute('d')
  }));
  const cats = Array.from(svg.querySelectorAll('g[data-kind="category"]')).map(g => {
    const c = g.querySelector('[data-status]');
    const t = g.querySelector('text');
    return { label: t ? t.textContent : null, status: c ? c.getAttribute('data-status') : null,
             active: c ? c.getAttribute('data-active') : null };
  });
  const mods = Array.from(svg.querySelectorAll('g[data-kind="module"]')).map(g => {
    const t = g.querySelector('text');
    const c = g.querySelector('[data-status]');
    return { name: t ? t.textContent : null, status: c ? c.getAttribute('data-status') : null };
  });
  const docs = Array.from(svg.querySelectorAll('g[data-kind="document"]')).length;
  const prj = svg.querySelector('#lnf-prj');
  const termini = Array.from(svg.querySelectorAll('[data-kind="stream-terminus"]'))
    .map(e => e.getAttribute('data-edge-src'));
  const box = svg.getBoundingClientRect();
  return { present:true, paths, cats, mods, docs, termini,
    prjText: prj ? Array.from(prj.querySelectorAll('text')).map(t=>t.textContent) : null,
    headers: Array.from(svg.querySelectorAll('text.lnf-hdr-arch, text.lnf-hdr-activity')).map(t=>t.textContent),
    viewBox: svg.getAttribute('viewBox'),
    box: { w: Math.round(box.width), h: Math.round(box.height) }
  };
}"""

# ------------------------------------------------------- GOAL FOUR: THE INDETERMINATE BRIEF
BRIEF = r"""() => {
  const dec = document.querySelector('#section-d-decision');
  const decInfo = dec ? { present:true,
     heading: (dec.querySelector('.collapse-header') || {}).innerText || null,
     text: (dec.innerText || '').slice(0, 700),
     controls: Array.from(dec.querySelectorAll('button, select, input, a[href]'))
       .map(e => ((e.textContent||e.value||e.name||'').trim().slice(0,60))).filter(Boolean).slice(0,25)
   } : { present:false };
  const sec = document.querySelector('#section-d-brief') || document.querySelector('#body-d-brief');
  if (!sec) return { present:false, ids: Array.from(document.querySelectorAll('[id^="section-"]')).map(e=>e.id) };
  const txt = sec.innerText || '';
  return { present:true, text: txt,
    headings: Array.from(sec.querySelectorAll('h1,h2,h3,h4,strong,b')).map(e=>e.textContent.trim()).filter(Boolean).slice(0,40),
    lists: Array.from(sec.querySelectorAll('li')).map(e=>e.textContent.trim()).slice(0,40),
    buttons: Array.from(sec.querySelectorAll('button, a[href], [role="button"]')).map(e=>({t:(e.textContent||'').trim().slice(0,80), dis: e.disabled === true})),
    decisionCard: decInfo,
    briefMentionsDecision: /decision|recommendation card|how did you treat/i.test(txt),
    box: (()=>{const r=sec.getBoundingClientRect(); return {w:Math.round(r.width),h:Math.round(r.height)};})()
  };
}"""

from playwright.sync_api import sync_playwright  # noqa: E402
OUT = pathlib.Path(os.environ.get("RUN90_OUT", "/tmp/run90"))
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
        pg.wait_for_timeout(9000)
        pg.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('detail')")
        pg.evaluate("(id) => window.LinDetail && LinDetail.render(id)", PID)
        pg.wait_for_timeout(14000)
        say(f"sections: {pg.evaluate(OPEN)[:400]}")
        pg.wait_for_timeout(6000)

        RES = post({"action": "projectresults", "session_token": PM, "id": PID, "period": 1})
        RR = RES.get("result") or {}
        STORED_CATS = RR.get("category_statuses") or {}
        say(f"STORED  project_status={RR.get('project_status')!r}  "
            f"basis={json.dumps(RR.get('project_status_basis'), default=str)[:400]}")
        say(f"STORED  categories with a status: "
            f"{ {k: v.get('status') for k, v in STORED_CATS.items()} }")

        N = pg.evaluate(NET); dump(f"net_{VW}", N)
        say("-" * 100); say("GOAL ONE -- SIGNAL NETWORK, read from the scene graph it drew")
        if not N.get("present"):
            say("  NOT RENDERED")
        else:
            sc = N["scene"] or {}
            bodies = sc.get("bodies") or []
            planets = [x for x in bodies if x["kind"] == "planet"]
            moons = [x for x in bodies if x["kind"] == "moon"]
            sun = [x for x in bodies if x["kind"] == "health"]
            say(f"  canvas box {N['box']}  ink pixels {N['before']['ink']}  "
                f"hash before {N['before']['hash']} after drag {N['after']['hash']}  "
                f"CHANGED={N['before']['hash'] != N['after']['hash']}")
            say(f"  attrs: {N['attrs']}")
            say(f"  note: {N['note']}")
            say(f"  PLANETS DRAWN ({len(planets)}): "
                f"{[(p['key'], p['state'], p['status'], str(p['lit'])+'/'+str(p['total'])) for p in planets]}")
            say(f"  MODEL planet radii, before the perspective divide -- SIZE ENCODES NOTHING: "
                f"{sorted(set(p['baseR'] for p in planets))}  (one value = nothing encoded)")
            say(f"  drawn radii, which differ by DEPTH only: {sorted(set(p['r'] for p in planets))}")
            say(f"  MODEL moon orbit radii -- RADIUS ENCODES NOTHING: "
                f"{sorted(set(round(m['orbitR'],3) for m in moons))}")
            say(f"  moon orbital rates -- SPEED ENCODES NOTHING: "
                f"{sorted(set(round(m['orbitRate'],4) for m in moons))}")
            say(f"  SUN: {sun}")
            st = {}
            for m in moons:
                st[m["state"]] = st.get(m["state"], 0) + 1
            say(f"  MOONS DRAWN ({len(moons)}) by state: {st}")
            say(f"  moon categories drawn: {sorted(set(m['category'] for m in moons))}")
            RETIRED = {"A5.1", "A5.5", "B4.4"}
            drawn_ids = set(m["key"] for m in moons)
            say(f"  RETIRED MODULES DRAWN: {sorted(drawn_ids & RETIRED)}  (must be empty)")
            say(f"  edges drawn: {sc.get('edges')}")
        say(f"  page errors so far: {errs}")

        F = pg.evaluate(FLOW); dump(f"flow_{VW}", F)
        say("-" * 100); say("GOAL TWO -- SIGNAL FLOW, read from the rendered SVG")
        if not F.get("present"):
            say(f"  NOT RENDERED  host={F.get('hostHTML')}")
        else:
            say(f"  svg viewBox={F['viewBox']} box={F['box']}")
            say(f"  headers: {F['headers']}")
            say(f"  categories drawn ({len(F['cats'])}): "
                f"{[(c['label'], c['status'], c['active']) for c in F['cats']]}")
            say(f"  modules drawn: {len(F['mods'])}")
            say(f"  document rows drawn: {F['docs']}")
            catp = [p for p in F["paths"] if p["type"] == "CATEGORY -> PROJECT STATUS"]
            say(f"  CATEGORY -> PROJECT STATUS streams ({len(catp)}):")
            for p in catp:
                say(f"    {p['src']:<40} terminates={p['term']:<10} arrowhead={'yes' if p['marker'] else 'no'}")
            say(f"  drawn stream termini (blunt ends): {F['termini']}")
            say(f"  centre node text: {F['prjText']}")
            RETNAMES = {"DSM Rework Propagation", "Rework Feedback Loop", "What-If Scenario Matrix"}
            drawn = set(m["name"] for m in F["mods"] if m["name"])
            say(f"  RETIRED MODULE LABELS DRAWN: {sorted(n for n in drawn if n in RETNAMES)}  (must be empty)")
        say(f"  page errors so far: {errs}")

        B = pg.evaluate(BRIEF); dump(f"brief_{VW}", B)
        say("-" * 100); say("GOAL FOUR -- THE EXECUTIVE BRIEF, rendered")
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
            say(f"  ---- THE DECISION CARD, is it on the page at all: {(B.get('decisionCard') or {}).get('present')}")
            dc = B.get('decisionCard') or {}
            if dc.get('present'):
                say(f"       heading: {dc.get('heading')!r}")
                say(f"       controls: {dc.get('controls')}")
                for line in (dc.get('text') or '').splitlines():
                    if line.strip():
                        say(f"       | {line.strip()}")

        pg.screenshot(path=str(OUT / f"page_{VW}.png"), full_page=True)
        say(f"  screenshot -> {OUT}/page_{VW}.png")
        say(f"  PAGE ERRORS: {errs}")
        pg.close()
    b.close()
say("=" * 100); say("RUN 90 DRIVE COMPLETE")
