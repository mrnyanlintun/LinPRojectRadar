#!/usr/bin/env python3
"""
RUN 139B. THE SIGNAL FLOW PANEL, MEASURED IN A REAL BROWSER.

Reads, from the rendered SVG of `.detail-neural-flow` (neural_flow.js):
  1. every module label's x, text-anchor, rendered advance width (getComputedTextLength)
     and bounding box -- MEASURED, never inferred from character counts;
  2. every module node dot (both ports) cx/cy;
  3. every flow path's two endpoints (getPointAtLength 0 and total), rounded to 3dp,
     so a before/after diff can prove nothing moved;
  4. the legend strip's box and the SVG's box, at each viewport width.

Writes a JSON blob to $RUN139B_OUT for numeric before/after diffing.

Run (from server/): DATABASE_URL=sqlite:///<file> SESSION_SECRET=test \
    RUN139B_OUT=/path/out.json python tools/run139b_measure_flow.py [widths...]
"""
from __future__ import annotations
import ast, base64, hashlib, io, json, logging, os, pathlib, socket, sys, threading, time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas as rl_canvas
from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.extraction_fields import extraction_fields_for
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import Participant

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
STAMP = int(time.time())
PID = f"PRJ-R139B-{STAMP}"
ADMIN = f"run139b-admin-{STAMP}"
P1_END = "2026-03-31"
WIDTHS = [int(a) for a in sys.argv[1:]] or [1280, 380]
OUT_PATH = pathlib.Path(os.environ.get("RUN139B_OUT", "/tmp/run139b_measure.json"))

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
    for k, v in ex.items():
        s = json.dumps(v) if isinstance(v, (list, dict)) else str(v)
        c.drawString(72, y, f"{k}: {s[:90]}"); y -= 12
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
        s.add(Participant(pseudonymous_code=f"R139B-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 139B signal flow",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R139B-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})
U = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
          "period_end": P1_END,
          "documents": [{"filename": fn, "mimeType": "application/pdf", "dataBase64": b64(r)}
                        for fn, r in DOCS]})
say(f"upload ok={U.get('ok')}")
CA = post({"action": "projectcomputeall", "session_token": PM, "id": PID})
say(f"computeall ok={CA.get('ok')}")

sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn
srv = uvicorn.Server(uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(200):
    try:
        c = socket.create_connection(("127.0.0.1", PORT), 0.2); c.close(); break
    except OSError: time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"
CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

MEASURE = r"""() => {
  const root = document.querySelector('.detail-neural-flow');
  if (!root) return {error: 'no .detail-neural-flow'};
  const svg = root.querySelector('svg');
  if (!svg) return {error: 'no svg'};
  const r3 = (n) => Math.round(n * 1000) / 1000;
  const texts = Array.from(svg.querySelectorAll('text')).map((t, i) => {
    let len = null; try { len = r3(t.getComputedTextLength()); } catch(e) {}
    let bb = null; try { const b = t.getBBox();
      bb = {x:r3(b.x), y:r3(b.y), w:r3(b.width), h:r3(b.height)}; } catch(e) {}
    return {i, text: t.textContent, x: t.getAttribute('x'), y: t.getAttribute('y'),
            anchor: t.getAttribute('text-anchor'),
            baseline: t.getAttribute('dominant-baseline'),
            fontSize: t.getAttribute('font-size'),
            cls: t.getAttribute('class'), opacity: t.getAttribute('opacity'),
            len, bb};
  });
  const dots = Array.from(svg.querySelectorAll('[data-module]')).map(e => ({
    module: e.getAttribute('data-module'), kind: e.getAttribute('data-kind'),
    port: e.getAttribute('data-port'), tag: e.tagName,
    cx: e.getAttribute('cx'), cy: e.getAttribute('cy'),
    points: e.getAttribute('points'), d: e.getAttribute('d'),
    x: e.getAttribute('x'), y: e.getAttribute('y')
  }));
  const paths = Array.from(svg.querySelectorAll('path')).map((p, i) => {
    let a = null, b = null, L = null;
    try { L = p.getTotalLength(); const p0 = p.getPointAtLength(0), p1 = p.getPointAtLength(L);
          a = [r3(p0.x), r3(p0.y)]; b = [r3(p1.x), r3(p1.y)]; } catch(e) {}
    return {i, d: p.getAttribute('d'), a, b, L: L === null ? null : r3(L)};
  });
  const circles = Array.from(svg.querySelectorAll('circle')).map((c,i) => ({
    i, cx:c.getAttribute('cx'), cy:c.getAttribute('cy'), r:c.getAttribute('r'),
    kind:c.getAttribute('data-kind'), module:c.getAttribute('data-module'),
    port:c.getAttribute('data-port')}));
  const bx = (e) => { if (!e) return null; const q = e.getBoundingClientRect();
    return {x:r3(q.x), y:r3(q.y), w:r3(q.width), h:r3(q.height),
            bottom:r3(q.bottom), right:r3(q.right)}; };
  const leg = root.querySelector('.lnf-legend');
  return {
    width: window.innerWidth,
    viewBox: svg.getAttribute('viewBox'),
    svgBox: bx(svg), rootBox: bx(root), legendBox: bx(leg),
    legendText: leg ? leg.textContent : null,
    legendChildren: leg ? Array.from(leg.children).map(c => ({t: c.textContent, b: bx(c)})) : null,
    texts, dots, paths, circles,
    nText: texts.length, nPath: paths.length
  };
}"""

from playwright.sync_api import sync_playwright
OUT = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME,
                           args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    for width in WIDTHS:
        pg = b.new_page(viewport={"width": width, "height": 2400})
        for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                    "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            pg.route(pat, lambda r: r.abort())
        pg.goto(BASE + "/", wait_until="domcontentloaded")
        pg.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        pg.goto(BASE + "/", wait_until="domcontentloaded")
        pg.wait_for_timeout(7000)
        pg.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('detail')")
        pg.evaluate("(id) => window.LinDetail && LinDetail.render(id)", PID)
        pg.wait_for_timeout(11000)
        # The section renders on FIRST EXPAND (detail.js lazyInits), so open it.
        pg.evaluate("""() => {
            const body = document.getElementById('body-d-neural');
            const closed = !body || body.style.display === 'none';
            if (closed && typeof window.toggleSection === 'function') window.toggleSection('d-neural');
            else { const h = document.querySelector('#section-d-neural .collapse-header');
                   if (h) h.click(); }
        }""")
        pg.wait_for_timeout(6000)
        m = pg.evaluate(MEASURE)
        OUT[str(width)] = m
        say(f"VIEWPORT {width}: {m.get('nText')} texts, {m.get('nPath')} paths, "
            f"viewBox={m.get('viewBox')} legend={m.get('legendBox')}")
        OUT_PATH.write_text(json.dumps(OUT, indent=1), encoding="utf-8")
        shot = os.environ.get("RUN139B_SHOT")
        if shot:
            # A full-page shot of this page times out (it is thousands of px tall), so the
            # panel is scrolled to the top of the viewport and the VIEWPORT is captured.
            # A screenshot of the whole page times out (thousands of px tall, live canvases),
            # so every OTHER section is detached first and the panel is scrolled to the top.
            pg.evaluate("""() => {
                document.querySelectorAll('.collapse-section, section, .panel').forEach(el => {
                  if (!el.querySelector('.detail-neural-flow') &&
                      !el.closest('#section-d-neural')) {
                    if (!el.contains(document.querySelector('.detail-neural-flow'))) el.remove();
                  }
                });
                const e = document.querySelector('.detail-neural-flow');
                if (e) window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - 8);
            }""")
            pg.wait_for_timeout(700)
            try:
                pg.screenshot(path=f"{shot}_{width}.png", animations="disabled",
                              caret="hide", timeout=90000)
            except Exception as exc:
                say(f"screenshot at {width} failed: {exc}")
        pg.close()
    b.close()
OUT_PATH.write_text(json.dumps(OUT, indent=1), encoding="utf-8")
say(f"wrote {OUT_PATH}")
