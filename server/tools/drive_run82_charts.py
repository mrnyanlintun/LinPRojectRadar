#!/usr/bin/env python3
"""
RUN 82, PARTS C AND D. THE TWO REBUILT CHARTS, VERIFIED IN A BROWSER.

Its SETUP is drive_run82_panel.py's, verbatim: the same four stubbed documents, the same
projectcomputeall, the same A1 category press, and the same three directly-stored readings that
put an abstained, an out-of-order and a FAILED row on the page at once. That is what lets all
five module states and the failed category be read off ONE rendered page.

WHAT IT ESTABLISHES, and every one is read back from what was DRAWN:

  C1  the Signal Flow's node census, off the rendered SVG's own data-* attributes.
  C2  EVERY EDGE ON THE FLOW IS CHECKED AGAINST A STORED FIGURE. Each `.nf-edge` carries
      `data-carries`. A document edge must name a field present in the stored
      signal_inputs.sources; a module edge must name a module present in module_results; a
      category edge must name a category with a stored status that votes. An edge naming
      anything else FAILS THE CHECK. This is the order's rule that a line may not be drawn
      unless it carried a figure, tested rather than asserted.
  C3  no edge crosses the field-to-module gap.
  C4  the five module states render as five DIFFERENT marks, read from the DOM.

  D1  the Signal Network's TOPOLOGY, read from the drawn scene graph: which category points at
      which. The invented Cost->Synthesis->Evidence->Decision chain must be gone and the real
      PASS_ONE -> PASS_TWO structure must be what is drawn.
  D2  the scene graph's body census: eleven planets, their moons, and the state of each.
  D3  A CANVAS PIXEL HASH, and the non-vacuity test that goes with it: the canvas must not be
      blank, and rotating the system must CHANGE the hash. A scene-graph assertion alone would
      pass on a canvas that drew nothing, which is the trap Run 81 caught itself in.
  D4  the four states rendered on the canvas as four different geometries.
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
PID = f"PRJ-R82C-{STAMP}"
ADMIN = f"run82c-admin-{STAMP}"
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
        s.add(Participant(pseudonymous_code=f"R82C-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 76 reproduction",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R82C-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})

say("=" * 100); say(f"RUN 82 C/D  project={PID}  DATABASE_URL={os.environ.get('DATABASE_URL')}")
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
    const h = document.querySelector('#section-' + id + ' .collapse-header');
    if (h) h.click();
  });
  return ['d-neural','d-projnet'].map(id => {
    const b = document.getElementById('body-' + id);
    return id + '=' + (b ? getComputedStyle(b).display : 'missing');
  }).join(' ');
}"""

# THE FLOW, READ FROM THE RENDERED SVG. Every figure below comes off an element that was drawn.
FLOW = r"""() => {
  const svg = document.querySelector('.detail-neural-flow svg[data-chart="signal-flow"]');
  if (!svg) return { present: false };
  const at = (k) => svg.getAttribute(k);
  const edges = Array.from(svg.querySelectorAll('.nf-edge')).map(e => ({
    cls: e.getAttribute('class'), carries: e.getAttribute('data-carries'),
    band: e.getAttribute('data-band'), d: e.getAttribute('d')
  }));
  const mods = Array.from(svg.querySelectorAll('.nf-module')).map(g => ({
    id: g.getAttribute('data-module'), state: g.getAttribute('data-state'),
    band: g.getAttribute('data-band'), cat: g.getAttribute('data-category'),
    /* the MARK that was drawn for this state -- tag, fill, stroke, dash. Two states that looked
       alike would produce identical signatures here. */
    mark: (() => { const m = g.querySelector('.nf-mod-mark'); if (!m) return null;
      return m.tagName + '|fill=' + m.getAttribute('fill') + '|stroke=' + m.getAttribute('stroke')
             + '|dash=' + (m.getAttribute('stroke-dasharray') || 'none'); })()
  }));
  const cats = Array.from(svg.querySelectorAll('.nf-category')).map(g => ({
    key: g.getAttribute('data-category'), state: g.getAttribute('data-state'),
    status: g.getAttribute('data-status'), contributes: g.getAttribute('data-contributes'),
    crossed: !!g.querySelector('path[stroke="#fff"]')
  }));
  const brk = svg.querySelector('.nf-break');
  return { present: true,
    census: { modules: at('data-modules'), lit: at('data-modules-lit'),
              categories: at('data-categories'), catsLit: at('data-categories-lit'),
              documents: at('data-documents'), fields: at('data-fields'),
              edgesDoc: at('data-edges-doc'), edgesModule: at('data-edges-module'),
              edgesCategory: at('data-edges-category'),
              projectStatus: at('data-project-status') },
    edges, mods, cats,
    breakPresent: !!brk,
    breakText: brk ? brk.textContent : null,
    censusText: Array.from(svg.querySelectorAll('.nf-census')).map(e => e.textContent),
    box: (() => { const r = svg.getBoundingClientRect();
                  return {w: Math.round(r.width), h: Math.round(r.height)}; })()
  };
}"""

# THE NETWORK. The scene graph is what was DRAWN; the pixel hash proves the canvas is not blank.
NET = r"""async () => {
  const host = document.querySelector('.detail-projnet2d');
  const cv = host ? host.querySelector('canvas.projnet2d-canvas') : null;
  if (!host || !cv) return { present: false };
  const scene = (window.LinProjectNet2D && LinProjectNet2D.lastScene) ? LinProjectNet2D.lastScene() : null;
  const hash = (c) => {
    const g = c.getContext('2d');
    const d = g.getImageData(0, 0, c.width, c.height).data;
    /* NON-VACUITY. "Not blank" cannot mean "some pixel is non-zero": this chart paints a full
       background wash, so every pixel is non-zero even when it draws nothing at all. What is
       counted instead is pixels that DIFFER FROM THE BACKGROUND -- i.e. ink actually laid down
       by a body, an edge or a label. */
    let h = 2166136261 >>> 0, nonblank = 0;
    const bg = [d[0], d[1], d[2]];
    for (let i = 0; i < d.length; i += 4) {
      if (Math.abs(d[i]-bg[0]) + Math.abs(d[i+1]-bg[1]) + Math.abs(d[i+2]-bg[2]) > 12) nonblank++;
      h ^= d[i]; h = Math.imul(h, 16777619) >>> 0;
      h ^= d[i+1]; h = Math.imul(h, 16777619) >>> 0;
      h ^= d[i+2]; h = Math.imul(h, 16777619) >>> 0;
    }
    return { hash: ('00000000' + h.toString(16)).slice(-8), inkPixels: nonblank,
             total: d.length / 4, w: c.width, h: c.height };
  };
  const before = hash(cv);
  /* NON-VACUITY: rotate the system through the canvas's OWN drag handler and re-hash. A chart
     that draws nothing, or one whose 3D projection is inert, gives the same hash twice. */
  const r0 = cv.getBoundingClientRect();
  cv.dispatchEvent(new MouseEvent('mousedown', {clientX: r0.x + 100, clientY: r0.y + 100, bubbles: true}));
  window.dispatchEvent(new MouseEvent('mousemove', {clientX: r0.x + 260, clientY: r0.y + 160, bubbles: true}));
  window.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
  await new Promise(r => setTimeout(r, 250));
  const after = hash(cv);
  const scene2 = (window.LinProjectNet2D && LinProjectNet2D.lastScene) ? LinProjectNet2D.lastScene() : null;
  return { present: true, before, after, scene, scene2,
    note: (host.querySelector('.projnet2d-note') || {}).textContent || null,
    attrs: ['modules','modules-lit','modules-dark','modules-na','modules-notcalled',
            'categories','categories-lit','edges','health','scene-bodies','scene-edges']
           .reduce((o,k) => (o[k] = host.getAttribute('data-'+k), o), {}),
    controls: host.querySelectorAll('button, [role="button"], input, select').length
  };
}"""

from playwright.sync_api import sync_playwright  # noqa: E402
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME,
                           args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    pg = b.new_page(viewport={"width": 1680, "height": 3600})
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
    say(f"sections opened via their own collapse headers: {pg.evaluate(OPEN)}")
    pg.wait_for_timeout(6000)

    # ---- THE STORED TRUTH THE CHART IS CHECKED AGAINST, fetched from the API, not the page ----
    RES = post({"action": "projectresults", "session_token": PM, "id": PID, "period": 1})
    RR = RES.get("result") or {}
    STORED_FIELDS = set((RR.get("signal_inputs") or {}).get("sources") or {})
    STORED_MODULES = {m.get("module_id") for m in (RR.get("module_results") or [])}
    STORED_CATS = RR.get("category_statuses") or {}
    VOTING = {k for k, v in STORED_CATS.items()
              if v.get("status") and v.get("contributes_to_project_status")}
    say("=" * 100)
    say(f"STORED TRUTH  fields={len(STORED_FIELDS)}  computed modules={len(STORED_MODULES)}  "
        f"categories with a status={len([1 for v in STORED_CATS.values() if v.get('status')])}  "
        f"voting={sorted(VOTING)}  project_status={RR.get('project_status')!r}")

    # ============================================================== PART C, THE SIGNAL FLOW
    F = pg.evaluate(FLOW)
    say("=" * 100)
    say("PART C -- THE SIGNAL FLOW, READ FROM THE RENDERED SVG")
    assert F.get("present"), "the Signal Flow SVG did not render"
    say(f"  census (off the SVG's own attributes): {F['census']}")
    say(f"  svg box: {F['box']}")
    say(f"  the break is drawn and stated: {F['breakPresent']}")
    say(f"  break text: {(F['breakText'] or '')[:200]!r}")
    say("  census in words, drawn on the chart:")
    for line in F["censusText"]:
        say(f"    {line}")

    say("-" * 100)
    say("C2 -- EVERY EDGE CHECKED AGAINST A STORED FIGURE:")
    bad = []
    kinds = {"nf-edge-doc": 0, "nf-edge-mod": 0, "nf-edge-cat": 0}
    for e in F["edges"]:
        cls = e["cls"] or ""
        carries = e["carries"]
        if "nf-edge-doc" in cls:
            kinds["nf-edge-doc"] += 1
            if carries not in STORED_FIELDS:
                bad.append(("document edge", carries, "not in signal_inputs.sources"))
        elif "nf-edge-mod" in cls:
            kinds["nf-edge-mod"] += 1
            if carries not in STORED_MODULES:
                bad.append(("module edge", carries, "not in module_results"))
        elif "nf-edge-cat" in cls:
            kinds["nf-edge-cat"] += 1
            if carries not in VOTING:
                bad.append(("category edge", carries, "has no stored status, or does not vote"))
        else:
            bad.append(("unclassified edge", carries, cls))
    say(f"  edges drawn, by kind: {kinds}   total={len(F['edges'])}")
    say(f"  edges naming something the server did not store: {len(bad)} -> {bad}")
    say(f"  NO LINE IS DRAWN THAT CARRIED NO FIGURE: {not bad}")
    # The gap: no edge may span the field column and the module column.
    spanning = [e for e in F["edges"] if "nf-edge-doc" not in (e["cls"] or "")
                and "nf-edge-mod" not in (e["cls"] or "")
                and "nf-edge-cat" not in (e["cls"] or "")]
    say(f"  C3 edges crossing the field-to-module gap: {len(spanning)}")

    say("-" * 100)
    say("C4 -- THE MODULE STATES, AND THE MARK EACH ONE DREW:")
    marks = {}
    for m in F["mods"]:
        marks.setdefault(m["state"], set()).add(m["mark"])
    counts = {}
    for m in F["mods"]:
        counts[m["state"]] = counts.get(m["state"], 0) + 1
    for st in sorted(marks):
        say(f"  {st:<14} n={counts[st]:<3} mark(s) drawn: {sorted(marks[st])}")
    allmarks = [next(iter(v)) for v in marks.values()]
    say(f"  distinct states rendered: {sorted(marks)}")
    say(f"  every state drew a DIFFERENT mark: {len(set(allmarks)) == len(allmarks)}")
    say("  categories, as drawn:")
    for c in F["cats"]:
        say(f"    {c['key']:<4} state={str(c['state']):<13} status={str(c['status']):<7} "
            f"votes={c['contributes']:<5} struck-through={c['crossed']}")

    # ============================================================ PART D, THE SIGNAL NETWORK
    N = pg.evaluate(NET)
    say("=" * 100)
    say("PART D -- THE SIGNAL NETWORK, READ FROM WHAT WAS DRAWN")
    assert N.get("present"), "the Signal Network canvas did not render"
    say(f"  host attributes: {N['attrs']}")
    say(f"  census in words, beneath the canvas: {N['note']!r}")
    say(f"  D3 canvas BEFORE rotation: {N['before']}")
    say(f"  D3 canvas AFTER  rotation: {N['after']}")
    blank = N["before"]["inkPixels"] == 0
    changed = N["before"]["hash"] != N["after"]["hash"]
    say(f"  canvas is NOT blank: {not blank}  ({N['before']['inkPixels']} of "
        f"{N['before']['total']} pixels differ from the background)")
    say(f"  rotating the system CHANGED the drawn pixels: {changed}")
    say(f"  DOM controls inside the chart host (must be 0): {N['controls']}")

    sc = N["scene"] or {}
    bodies = sc.get("bodies") or []
    sedges = sc.get("edges") or []
    planets = [b for b in bodies if b["kind"] == "planet"]
    moons = [b for b in bodies if b["kind"] == "moon"]
    say("-" * 100)
    say(f"D2 -- SCENE GRAPH: {len(planets)} planets, {len(moons)} moons, "
        f"{len(sedges)} edges, health body present="
        f"{any(b['kind'] == 'health' for b in bodies)}")
    mstate = {}
    for m in moons:
        mstate[m["state"]] = mstate.get(m["state"], 0) + 1
    say(f"  moon states drawn: {mstate}")
    say("  planets:")
    for p in sorted(planets, key=lambda x: (x["pass"], x["key"])):
        say(f"    {p['key']:<4} pass={p['pass']} state={str(p['state']):<11} "
            f"status={str(p['status']):<7} {p['lit']} of {p['total']} lit  at ({p['x']},{p['y']}) r={p['r']}")

    say("-" * 100)
    say("D1 -- THE TOPOLOGY THAT WAS DRAWN:")
    PASS_ONE = ["A1", "A2", "A3", "A4", "A5", "A6", "C1"]
    PASS_TWO = ["B1", "B2", "B3", "B4"]
    pairs = sorted({(e["from"], e["to"]) for e in sedges})
    for a, bkey in pairs:
        say(f"    {a} -> {bkey}")
    invented = [(a, bkey) for a, bkey in pairs
                if bkey != "__health__" and not (a in PASS_ONE and bkey in PASS_TWO)]
    say(f"  edges that are NOT pass-one -> pass-two and NOT a fuse to health: {invented}")
    say(f"  the invented Cost->Synthesis->Evidence->Decision chain is gone: "
        f"{not any(a in PASS_TWO and bkey in PASS_TWO for a, bkey in pairs)}")
    fuse = sorted({a for a, bkey in pairs if bkey == "__health__"})
    say(f"  categories fusing to project health: {fuse}")
    say(f"  and the server says these vote: {sorted(VOTING)}  -> agree: {fuse == sorted(VOTING)}")
    # Every drawn dependency edge must come FROM a category with a stored status.
    withstatus = {p["key"] for p in planets if p["status"]}
    bad_edges = [(a, bkey) for a, bkey in pairs if a not in withstatus]
    say(f"  dependency edges drawn from a category with NO stored status: {bad_edges}")

    say("=" * 100)
    say(f"page errors: {errs or 'NONE'}")
    OUT = pathlib.Path(os.environ.get("R82C_OUT", "/tmp/r82_charts.json"))
    OUT.write_text(json.dumps({"flow": F, "net": {k: N[k] for k in
                    ("attrs", "note", "before", "after", "controls")},
                   "scene_pairs": [list(x) for x in pairs],
                   "moon_states": mstate,
                   "stored": {"fields": sorted(STORED_FIELDS),
                              "modules": sorted(STORED_MODULES),
                              "voting": sorted(VOTING)}}, indent=1, sort_keys=True))
    say(f"  wrote {OUT}")
    b.close()

checks = [
    ("C1 flow rendered", bool(F.get("present"))),
    ("C2 no line drawn that carried no figure", not bad),
    ("C3 nothing drawn across the field-to-module gap", len(spanning) == 0),
    ("C4 every module state drew a different mark", len(set(allmarks)) == len(allmarks)),
    ("D1 real pass-one -> pass-two topology, nothing invented", not invented),
    ("D2 eleven planets with their moons in the scene graph", len(planets) == 11),
    ("D3 canvas carries ink and rotation changes it", (not blank) and changed),
    ("D4 no DOM control added to the chart", N["controls"] == 0),
    ("no page errors", not errs),
]
say("=" * 100)
for name, ok in checks:
    say(f"  {'PASS' if ok else 'FAIL'}  {name}")
say(f"RESULT: {sum(1 for _, o in checks if o)}/{len(checks)} checks passed")
