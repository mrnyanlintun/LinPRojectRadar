#!/usr/bin/env python3
"""
RUN 139A. THE PROJECT SIGNAL NETWORK ORRERY LEGEND -- MEASURED, NOT ASSUMED.

The project build is drive_run94_charts.py's, unchanged in substance: a real
`projectupload` and a real `projectcomputeall`, then every performance category pressed
through `projectcategoryapply`, so the canvas draws what the platform actually produces.
Nothing under test is supplied.

WHAT THIS MEASURES, all in a real Chromium, all read back from the rendered page:
  1. the canvas's CSS box at every viewport width the panel renders at;
  2. `ctx.measureText` for every module name and every category name at candidate fonts, on
     the panel's own 2D context, so the legend's footprint is a measurement not an estimate;
  3. the module population the panel draws (`data-modules` and its siblings);
  4. the moon order the painter produced, read from `LinProjectNet2D.lastScene()`;
  5. a PNG of the canvas per theme, for pixel-sampled contrast afterwards.

Run from server/:
  DATABASE_URL=sqlite:///<throwaway> RUN139A_OUT=<dir> python tools/run139a_measure.py
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
from app.research_models import Participant            # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
STAMP = int(time.time())
PID = f"PRJ-R139A-{STAMP}"
ADMIN = f"run139a-admin-{STAMP}"
P1_END = "2026-03-31"
SECTOR = os.environ.get("RUN139A_SECTOR", "construction")

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
        s.add(Participant(pseudonymous_code=f"R139A-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 139A orrery legend",
                                          "sector": SECTOR, "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R139A-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})

say("=" * 100); say(f"RUN 139A  project={PID}  sector={SECTOR}  DATABASE_URL={os.environ.get('DATABASE_URL')}")
say("=" * 100)
U = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
          "period_end": P1_END,
          "documents": [{"filename": fn, "mimeType": "application/pdf", "dataBase64": b64(r)}
                        for fn, r in DOCS]})
say(f"upload: ok={U.get('ok')}")
CA = post({"action": "projectcomputeall", "session_token": PM, "id": PID})
say(f"computeall: ok={CA.get('ok')}")
for cat in ("A1", "A2", "A3", "A4", "A6"):
    r = post({"action": "projectcategoryapply", "session_token": PM, "id": PID,
              "period": 1, "category": cat})
    say(f"  apply {cat}: ok={r.get('ok')}")

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
CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
OUT = pathlib.Path(os.environ.get("RUN139A_OUT", "/tmp/run139a"))
OUT.mkdir(parents=True, exist_ok=True)
TAG = os.environ.get("RUN139A_TAG", "before")

OPEN = r"""() => {
  if (window.LinApp && LinApp.showPage) { try { LinApp.showPage('detail'); } catch(e){} }
  const sec = document.querySelector('#section-d-projnet');
  if (sec && !sec.classList.contains('open')) {
    const h = sec.querySelector('.collapse-header'); if (h) h.click();
  }
  return sec ? sec.className : 'NO SECTION';
}"""
SETTHEME = r"""(t) => { document.body.setAttribute('data-theme', t);
  document.documentElement.setAttribute('data-theme', t);
  return document.body.getAttribute('data-theme'); }"""

MEASURE = r"""() => {
  const host = document.querySelector('.detail-projnet2d');
  const cv = host ? host.querySelector('canvas.projnet2d-canvas') : null;
  if (!host || !cv) return { present:false };
  const box = cv.getBoundingClientRect();
  const cats = (window.performanceCategories ? window.performanceCategories() : []) || [];
  const g = cv.getContext('2d');
  const fonts = ['500 10.5px system-ui, sans-serif', '500 9.5px system-ui, sans-serif',
                 '600 9.5px system-ui, sans-serif'];
  const widths = {};
  fonts.forEach(f => {
    g.save(); g.font = f;
    let maxMod = 0, maxCat = 0; const names = [];
    cats.forEach(c => {
      maxCat = Math.max(maxCat, g.measureText(c.key + ' ' + c.name).width);
      (c.modules||[]).forEach(m => {
        const w = g.measureText(m.name).width;
        names.push([m.module_id, m.name, Math.round(w*10)/10]);
        maxMod = Math.max(maxMod, w);
      });
    });
    names.sort((a,b)=>b[2]-a[2]);
    widths[f] = { maxModule: Math.round(maxMod*10)/10, maxCategory: Math.round(maxCat*10)/10,
                  widest: names.slice(0,4) };
    g.restore();
  });
  g.save(); g.font = '500 10.5px system-ui, sans-serif';
  const keyRows = ['Green','Yellow','Amber','Red','Complete','Computed, no band asserted',
                   'Nothing to report','Not relevant to this project','Not called'];
  const keyW = Math.max.apply(null, keyRows.map(t => g.measureText(t).width));
  g.restore();
  const attrs = {};
  ['modules','modules-lit','modules-unbanded','modules-dark','modules-na','modules-notcalled',
   'categories','categories-lit','health','scene-bodies','legend-entries','legend-box']
    .forEach(k => attrs[k]=host.getAttribute('data-'+k));
  const scene = (window.LinProjectNet2D && LinProjectNet2D.lastScene) ? LinProjectNet2D.lastScene() : null;
  const moons = scene ? scene.bodies.filter(b=>b.kind==='moon').map(b=>({key:b.key,cat:b.category,
                        state:b.state, ic:b.identityColor, x:b.x, y:b.y, r:b.r})) : [];
  const roster = cats.map(c => ({key:c.key, name:c.name,
                        modules:(c.modules||[]).map(m=>[m.module_id,m.name])}));
  const legend = (window.LinProjectNet2D && LinProjectNet2D.lastLegend)
                 ? LinProjectNet2D.lastLegend() : null;
  return { present:true, css:{w:Math.round(box.width),h:Math.round(box.height)},
           dpr: window.devicePixelRatio, raw:{w:cv.width,h:cv.height},
           widths, keyW: Math.round(keyW*10)/10, attrs, roster, moons, legend,
           note: (host.querySelector('.projnet2d-note')||{}).textContent||null };
}"""

from playwright.sync_api import sync_playwright  # noqa: E402
from app.theme import THEMES  # noqa: E402
ALL_THEMES = list(THEMES) + ["dark"]
say(f"THEME AUTHORITY server/app/theme.py THEMES = {THEMES}; plus archived-but-renderable 'dark'")

VIEWPORTS = [int(v) for v in os.environ.get("RUN139A_VW", "1440,1280,1024,768").split(",")]
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME,
                           args=["--use-gl=swiftshader", "--no-sandbox"])
    for VW in VIEWPORTS:
        say("=" * 100); say(f"VIEWPORT {VW}px")
        pg = b.new_page(viewport={"width": VW, "height": 2400})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                    "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            pg.route(pat, lambda r: r.abort())
        pg.goto(BASE + "/", wait_until="domcontentloaded")
        pg.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        pg.goto(BASE + "/", wait_until="domcontentloaded")
        pg.wait_for_timeout(8000)
        pg.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('detail')")
        pg.evaluate("(id) => window.LinDetail && LinDetail.render(id)", PID)
        pg.wait_for_timeout(12000)
        say(f"  section: {pg.evaluate(OPEN)}")
        pg.wait_for_timeout(4000)
        themes = ALL_THEMES if VW == 1280 else ["plain"]
        for TH in themes:
            pg.evaluate(SETTHEME, TH)
            pg.evaluate("(id) => window.LinDetail && LinDetail.render(id)", PID)
            pg.wait_for_timeout(3000); pg.evaluate(OPEN); pg.wait_for_timeout(2500)
            M = pg.evaluate(MEASURE)
            (OUT / f"{TAG}_measure_{VW}_{TH}.json").write_text(json.dumps(M, indent=1))
            if not M.get("present"):
                say(f"  THEME {TH}: PANEL NOT RENDERED"); continue
            say(f"  THEME {TH}: canvas css={M['css']} dpr={M['dpr']} raw={M['raw']}")
            say(f"    attrs={M['attrs']}")
            if TH == themes[0]:
                for f, w in M["widths"].items():
                    say(f"    font {f!r}: widest module name={w['maxModule']}px  "
                        f"widest 'KEY name' line={w['maxCategory']}px")
                    say(f"      widest four: {w['widest']}")
                say(f"    colour-key widest row at 10.5px: {M['keyW']}px")
                say(f"    roster: {[(c['key'], len(c['modules'])) for c in M['roster']]}  "
                    f"total={sum(len(c['modules']) for c in M['roster'])}")
                say(f"    moons in scene: {len(M['moons'])}")
                say(f"    moon key order in scene: {[m['key'] for m in M['moons']]}")
                if M.get("legend"):
                    say(f"    LEGEND reported by the painter: {json.dumps(M['legend'])[:2000]}")
                say(f"    note: {M['note']}")
            # THE PAINTED PIXELS THEMSELVES. An element screenshot never settles on an
            # animating canvas (Playwright waits for stability and times out), and a page
            # screenshot would re-composite the page. `toDataURL` hands back exactly the
            # bitmap the 2D context painted, which is what a contrast measurement must read.
            data = pg.evaluate("""() => {
              const cv = document.querySelector('.detail-projnet2d canvas.projnet2d-canvas');
              return cv ? cv.toDataURL('image/png') : null; }""")
            if data:
                (OUT / f"{TAG}_{VW}_{TH}.png").write_bytes(
                    base64.b64decode(data.split(",", 1)[1]))
        say(f"  page errors: {errs[:3]}")
        pg.close()
    b.close()
say("DONE")
