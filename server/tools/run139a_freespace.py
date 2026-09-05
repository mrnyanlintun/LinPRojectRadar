#!/usr/bin/env python3
"""
RUN 139A. HOW MUCH CANVAS IS ACTUALLY FREE, SAMPLED OVER A WHOLE ORBIT.

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
PID = f"PRJ-R139F-{STAMP}"
ADMIN = f"run139f-admin-{STAMP}"
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
OUT = pathlib.Path(os.environ.get("RUN139A_OUT", "/tmp/run139a")); OUT.mkdir(parents=True, exist_ok=True)

OPEN = r"""() => {
  if (window.LinApp && LinApp.showPage) { try { LinApp.showPage('detail'); } catch(e){} }
  const sec = document.querySelector('#section-d-projnet');
  if (sec && !sec.classList.contains('open')) {
    const h = sec.querySelector('.collapse-header'); if (h) h.click();
  }
  return sec ? sec.className : 'NO SECTION';
}"""

# ONE SAMPLE OF WHAT THE SYSTEM OCCUPIES: every moon disc, every planet disc, the sun, and the
# bounding box of every drawn category label, in CSS pixels of the canvas.
SAMPLE = r"""() => {
  const host = document.querySelector('.detail-projnet2d');
  const cv = host && host.querySelector('canvas.projnet2d-canvas');
  if (!cv) return null;
  const s = (window.LinProjectNet2D && LinProjectNet2D.lastScene) ? LinProjectNet2D.lastScene() : null;
  if (!s) return null;
  const box = cv.getBoundingClientRect();
  const g = cv.getContext('2d');
  const boxes = [];
  s.bodies.forEach(b => {
    // a lit planet paints a corona out to 2.3r and a lit moon a halo out to 2.8r; take the
    // painted extent, not the disc, so "free" means free of ink and not merely of geometry.
    const k = b.kind === 'moon' ? 2.8 : (b.kind === 'planet' ? 2.3 : 1.25);
    const r = b.r * k;
    boxes.push([b.x-r, b.y-r, b.x+r, b.y+r, b.kind]);
  });
  g.save(); g.font = '600 11px system-ui, sans-serif';
  (s.labels||[]).forEach(L => {
    const w = Math.max.apply(null, (L.lines||[L.name]).map(t => g.measureText(t).width));
    const h = 13 * ((L.lines||[1]).length || 1);
    boxes.push([L.x - w/2, L.y - 11, L.x + w/2, L.y + h, 'label']);
  });
  g.restore();
  return { w: Math.round(box.width), h: Math.round(box.height), boxes };
}"""

from playwright.sync_api import sync_playwright  # noqa: E402
VIEWPORTS = [int(v) for v in os.environ.get("RUN139A_VW", "1440,1280,1024,768").split(",")]
NS = int(os.environ.get("RUN139A_SAMPLES", "44"))       # 44 x 0.75s = 33s > one orbit (28.6s)
CELL = 8

def rects_report(W, H, occ):
    """For a set of candidate legend rectangles, how many 8px cells carry ink."""
    def occupied(x0, y0, x1, y1):
        n = bad = 0
        for cy in range(max(0, y0 // CELL), min(H // CELL, y1 // CELL + 1)):
            for cx in range(max(0, x0 // CELL), min(W // CELL, x1 // CELL + 1)):
                n += 1
                if occ[cy][cx]: bad += 1
        return bad, n
    return occupied

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--use-gl=swiftshader", "--no-sandbox"])
    for VW in VIEWPORTS:
        say("=" * 100); say(f"VIEWPORT {VW}px")
        pg = b.new_page(viewport={"width": VW, "height": 2400})
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
        pg.evaluate(OPEN); pg.wait_for_timeout(4000)
        first = pg.evaluate(SAMPLE)
        if not first: say("  PANEL NOT RENDERED"); pg.close(); continue
        W, H = first["w"], first["h"]
        occ = [[0] * (W // CELL + 1) for _ in range(H // CELL + 1)]
        def mark(bx):
            for x0, y0, x1, y1, kind in bx:
                for cy in range(max(0, int(y0) // CELL), min(H // CELL, int(y1) // CELL) + 1):
                    for cx in range(max(0, int(x0) // CELL), min(W // CELL, int(x1) // CELL) + 1):
                        occ[cy][cx] = 1
        mark(first["boxes"])
        for i in range(NS):
            pg.wait_for_timeout(750)
            s = pg.evaluate(SAMPLE)
            if s: mark(s["boxes"])
        say(f"  canvas {W}x{H}; ink sampled over {NS+1} frames spanning ~{(NS)*0.75:.0f}s "
            f"(one orbit is 2*pi/0.22 = 28.6s)")
        # the tallest clean strip against the LEFT edge, and the tallest clean strip along the
        # BOTTOM edge, both reported as the largest clean rectangle anchored at that corner.
        def clean_w_at(y0, y1):
            w = 0
            for cx in range(W // CELL + 1):
                col_clean = all(occ[cy][cx] == 0
                                for cy in range(max(0, y0 // CELL), min(H // CELL, y1 // CELL) + 1))
                if not col_clean: break
                w = (cx + 1) * CELL
            return w
        def clean_h_at(x0, x1):
            h = 0
            for cy in range(H // CELL, -1, -1):
                row_clean = all(occ[cy][cx] == 0
                                for cx in range(max(0, x0 // CELL), min(W // CELL, x1 // CELL) + 1))
                if not row_clean: break
                h = (H // CELL - cy + 1) * CELL
            return h
        say(f"  BOTTOM-LEFT CORNER, clean width for the full canvas height 0..{H}: {clean_w_at(0, H)}px")
        for hh in (140, 200, 260, 320, 440, 480):
            say(f"    clean width of a strip {hh}px tall anchored at the bottom "
                f"(y {H-hh}..{H}): {clean_w_at(H-hh, H)}px")
        for ww in (240, 320, 440, 620, 900, W):
            say(f"    clean height of a strip {ww}px wide anchored bottom-left "
                f"(x 0..{ww}): {clean_h_at(0, ww)}px")
        (OUT / f"freespace_{VW}.json").write_text(json.dumps({"w": W, "h": H, "occ": occ}))
        pg.close()
    b.close()
say("DONE")
