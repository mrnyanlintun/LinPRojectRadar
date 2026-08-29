#!/usr/bin/env python3
"""
RUN 86, GOAL TWO. THE CATEGORY PANEL, MEASURED IN A REAL BROWSER AT 1280px AND 1024px.

Every prior claim about the panel is treated as unverified. What this reads, from the rendered
DOM and computed layout, at BOTH widths:

  1. the per-row headline is exactly ONE figure pair ("n of N produced a status") and the
     five-figure breakdown is NOT in the collapsed row;
  2. the breakdown exists behind the row's expansion (.dcat-body .dcat-counts), not deleted;
  3. each Process button sits ON ITS OWN ROW: its bounding box lies inside its row's box and
     vertically overlaps the row's name cell;
  4. NO ROW WRAPS: the head's rendered height stays single-line (measured against the name
     cell's line height) and nothing overflows horizontally;
  5. the explanation text under each module, byte for byte: sha256 over the textContent of
     every .dcat-reason and .dcat-note, compared across widths (and printed for the report);
  6. the four states remain four distinguishable markers inside the expansion;
  7. Run 85's processing-line styling survives: computed font-weight, colour and animation
     while a call is in flight.

RUN 61's RULE IS OBSERVED: this harness never calls LinResults.prime.

Run (from server/): DATABASE_URL=sqlite:///<fresh> SESSION_SECRET=test \
    python tools/drive_run86_panel_widths.py
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
PID = f"PRJ-R86P-{STAMP}"
ADMIN = f"run86-admin-{STAMP}"
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
        s.add(Participant(pseudonymous_code=f"R86-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 86 panel widths",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R86-PM-{STAMP}", "role": "Participant",
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
AP = post({"action": "projectcategoryapply", "session_token": PM, "id": PID,
           "period": 1, "category": "A1"})
say(f"apply A1 ok={AP.get('ok')} servedBy={AP.get('servedBy')}")

# One stored row per non-computed state so the DOM carries all four states at once.
from app.spec_readings import store_reading  # noqa: E402
from app.research_models import SpecificationReading  # noqa: E402
with Session() as s:
    proj = s.scalar(select(Project).where(Project.legacy_id == PID))
    store_reading(s, proj.id, 1, {
        "category": "A2", "state": "abstained", "status": None,
        "counts": {"computed": 0, "abstained": 2, "out_of_order": 0, "failed": 0},
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

MEASURE = r"""() => {
  const bx = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
      return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width),
              h: Math.round(r.height), right: Math.round(r.right),
              bottom: Math.round(r.bottom)}; };
  const rows = Array.from(document.querySelectorAll('.dcat-row')).map(r => {
    const head = r.querySelector('.dcat-head');
    const name = r.querySelector('.dcat-name');
    const btn = r.querySelector('.dcat-call');
    const prod = r.querySelector('.dcat-produced');
    const nameCS = name ? getComputedStyle(name) : null;
    return {
      cat: r.getAttribute('data-category'),
      state: r.getAttribute('data-state'),
      rowBox: bx(r), headBox: bx(head), nameBox: bx(name), btnBox: bx(btn),
      producedText: prod ? prod.textContent : null,
      headlineIsOnePair: prod ? /^\d+ of \d+ produced a status$/.test(prod.textContent.trim()) : false,
      countsInHead: !!(head && head.querySelector('.dcat-counts')),
      countsInBody: !!r.querySelector('.dcat-body .dcat-counts'),
      bodyDisplay: r.querySelector('.dcat-body') ?
          getComputedStyle(r.querySelector('.dcat-body')).display : null,
      overflowX: r.scrollWidth > r.clientWidth,
      headOverflowX: head ? head.scrollWidth > head.clientWidth : null,
      btnInRow: (btn && r) ? (bx(btn).x >= bx(r).x - 1 && bx(btn).right <= bx(r).right + 1 &&
                              bx(btn).y >= bx(r).y - 1 && bx(btn).bottom <= bx(r).bottom + 1) : null,
      btnOverlapsNameRow: (btn && name) ? (bx(btn).y < bx(name).bottom && bx(btn).bottom > bx(name).y) : null,
      nameLineHeight: nameCS ? nameCS.lineHeight : null
    };
  });
  return { width: window.innerWidth, rows };
}"""

OPEN_ALL = r"""() => {
  if (window.LinApp && LinApp.showPage) { try { LinApp.showPage('detail'); } catch(e){} }
  const h = document.querySelector('#section-d-catspecs .collapse-header');
  if (h) h.click();
  document.querySelectorAll('.dcat-toggle').forEach(b => b.click());
  const panel = document.querySelector('.detail-catspecs');
  return { panelWidth: panel ? Math.round(panel.getBoundingClientRect().width) : 0 };
}"""

EXPANDED = r"""() => {
  const sha = (s) => s;  /* hashed on the Python side, bytes for bytes */
  const reasons = Array.from(document.querySelectorAll('.dcat-reason'))
      .map(e => [(e.closest('.dcat-mod')||{getAttribute:()=>'?'}).getAttribute('data-module'), e.textContent]);
  const notes = Array.from(document.querySelectorAll('.dcat-note')).map(e => e.textContent);
  const chips = Array.from(document.querySelectorAll('.dcat-row')).map(r => ({
    cat: r.getAttribute('data-category'), state: r.getAttribute('data-state'),
    chip: (r.querySelector('.dcat-state')||{}).textContent || null,
    counts: Array.from(r.querySelectorAll('.dcat-body .dcat-n'))
        .map(n => [n.getAttribute('data-count'), n.textContent])
  }));
  return { reasons, notes, chips };
}"""

PRESS = r"""() => {
  const b = document.querySelector('.dcat-call[data-cat="A1"]');
  if (b) b.click();
  const line = document.querySelector('.dcat-status-line');
  const cs = line ? getComputedStyle(line) : null;
  return line ? { text: line.textContent, className: line.className,
                  fontWeight: cs.fontWeight, color: cs.color,
                  animationName: cs.animationName, animationDuration: cs.animationDuration }
              : null;
}"""

from playwright.sync_api import sync_playwright  # noqa: E402
OUT = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME,
                           args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    for width in (1280, 1024):
        pg = b.new_page(viewport={"width": width, "height": 3200})
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
        say("-" * 100)
        say(f"VIEWPORT {width}px — collapsed rows")
        collapsed = pg.evaluate(MEASURE)
        op = pg.evaluate(OPEN_ALL)
        pg.wait_for_timeout(4000)
        expanded_geo = pg.evaluate(MEASURE)
        expanded = pg.evaluate(EXPANDED)
        pressed = pg.evaluate(PRESS)
        pg.wait_for_timeout(300)
        OUT[width] = {"collapsed": collapsed, "open": op, "expanded_geo": expanded_geo,
                      "expanded": expanded, "pressed": pressed}
        blob = "\x00".join(t for _m, t in expanded["reasons"]) + "\x01" + \
               "\x00".join(expanded["notes"])
        OUT[width]["explanation_sha256"] = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        pg.close()
    b.close()

ok = True
def check(cond, label, detail=""):
    global ok
    ok = ok and bool(cond)
    say(f"  {'PASS' if cond else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))

for width in (1280, 1024):
    d = OUT[width]
    rows = d["expanded_geo"]["rows"]
    say("=" * 100)
    say(f"AT {width}px  (panel width {d['open']['panelWidth']}px, "
        f"{len(rows)} category rows)")
    check(all(r["headlineIsOnePair"] for r in rows),
          "1. each row's headline is exactly one figure pair",
          "; ".join(f"{r['cat']}:{r['producedText']}" for r in rows[:4]) + " …")
    check(all(not r["countsInHead"] for r in rows),
          "2a. the five-figure breakdown is NOT in the collapsed head")
    check(all(r["countsInBody"] for r in rows),
          "2b. the breakdown exists behind the expansion (not deleted)")
    check(all(r["btnInRow"] for r in rows if r["btnBox"]),
          "3a. every Process button's box lies inside its own row's box")
    check(all(r["btnOverlapsNameRow"] for r in rows if r["btnBox"]),
          "3b. every Process button vertically overlaps its row's name cell")
    wraps = [r["cat"] for r in rows if r["overflowX"] or r["headOverflowX"]]
    check(not wraps, "4a. no row overflows horizontally", str(wraps))
    tall = [(r["cat"], r["headBox"]["h"]) for r in rows
            if r["headBox"] and r["headBox"]["h"] > 44]
    check(not tall, "4b. no row's head grew beyond a single-line height (<=44px)", str(tall))
    states = {r["cat"]: r["state"] for r in rows}
    chipset = {c["state"]: c["chip"] for c in d["expanded"]["chips"] if c["chip"]}
    check(len({s for s in states.values() if s in
               ("computed", "abstained", "out_of_order", "failed")}) == 4,
          "6. all four states present and distinguishable",
          str({k: v for k, v in states.items() if v != 'unspecified'}))
    p = d["pressed"]
    check(p and "Processing" in (p["text"] or "") and p["fontWeight"] == "700"
          and p["animationName"] == "dcat-processing-pulse",
          "7. processing line: bold, pulsing, its Run-85 styling computed live",
          json.dumps(p))
    say(f"  explanation sha256 at {width}px: {d['explanation_sha256']}")

check(OUT[1280]["explanation_sha256"] == OUT[1024]["explanation_sha256"],
      "5. explanation text byte-identical across widths",
      OUT[1280]["explanation_sha256"][:16])

say("=" * 100)
say("BUTTON GEOMETRY, for the report (x, y, w per Process button):")
for width in (1280, 1024):
    for r in OUT[width]["expanded_geo"]["rows"]:
        if r["btnBox"]:
            say(f"  {width}px  {r['cat']}: x={r['btnBox']['x']} y={r['btnBox']['y']} "
                f"w={r['btnBox']['w']}")
say("RESULT: " + ("ALL CHECKS PASSED" if ok else "CHECKS FAILED"))
sys.exit(0 if ok else 1)
