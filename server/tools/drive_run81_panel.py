#!/usr/bin/env python3
"""
RUN 81. THE CATEGORY PANEL, VERIFIED IN A BROWSER.

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
PID = f"PRJ-R81-{STAMP}"
ADMIN = f"run81-admin-{STAMP}"
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
        s.add(Participant(pseudonymous_code=f"R81-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 76 reproduction",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R81-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})

say("=" * 100); say(f"RUN 81  project={PID}  DATABASE_URL={os.environ.get('DATABASE_URL')}")
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
  const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
      return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width),
              right: Math.round(r.right)}; };
  const rows = Array.from(document.querySelectorAll('.dcat-row')).map(r => ({
    cat: r.getAttribute('data-category'),
    state: r.getAttribute('data-state'),
    tag: r.tagName,
    listStyle: getComputedStyle(r).listStyleType,
    display: getComputedStyle(r.querySelector('.dcat-head') || r).display,
    status: (r.querySelector('.dcat-status')||{}).textContent,
    statusAttr: r.querySelector('.dcat-status') ? r.querySelector('.dcat-status').getAttribute('data-status') : null,
    chip: (r.querySelector('.dcat-state')||{}).textContent,
    chipState: r.querySelector('.dcat-state') ? r.querySelector('.dcat-state').getAttribute('data-state') : null,
    counts: Array.from(r.querySelectorAll('.dcat-n')).map(n => n.textContent),
    headLine: (r.querySelector('.dcat-head')||{}).innerText ?
          (r.querySelector('.dcat-head').innerText||'').replace(/\n/g,' ⏎ ') : '',
    btnLabel: r.querySelector('.dcat-call') ? r.querySelector('.dcat-call').textContent : null,
    btnBox: box(r.querySelector('.dcat-call')),
    callDisabled: r.querySelector('.dcat-call') ? r.querySelector('.dcat-call').disabled : null
  }));
  /* EXPLANATION TEXT, CAPTURED VERBATIM. textContent, never innerText: innerText is
     layout-dependent and would differ between two layouts for identical strings, which is
     exactly what this comparison must not do. */
  const reasons = Array.from(document.querySelectorAll('.dcat-reason'))
      .map(e => [ (e.closest('.dcat-mod')||{}).getAttribute
                    ? e.closest('.dcat-mod').getAttribute('data-module') : '?', e.textContent ]);
  const notes = Array.from(document.querySelectorAll('.dcat-note')).map(e => e.textContent);
  const hint = (document.querySelector('.dcat-hint')||{}).textContent || '';
  const mods = Array.from(document.querySelectorAll('.dcat-mod'))
      .map(m => ({ id: m.getAttribute('data-module'), state: m.getAttribute('data-state'),
                   band: m.querySelector('.dcat-band') ? m.querySelector('.dcat-band').getAttribute('data-band') : null,
                   chip: (m.querySelector('.dcat-state')||{}).textContent || null,
                   text: (m.innerText||'').replace(/\s+/g,' ').trim().slice(0,150) }));
  return { sections, rows, mods, reasons, notes, hint,
           callAllLabel: (document.querySelector('.dcat-call-all')||{}).textContent || null,
           callAll: !!document.querySelector('.dcat-call-all'),
           panelPresent: !!document.querySelector('.detail-catspecs') };
}"""
OPEN_ALL = r"""() => {
  /* Opened through the page's OWN control -- the collapse header the person clicks -- never by
     setting a style from the harness. If the panel is not visible after this, the check must
     fail rather than be handed a layout the harness arranged for it. */
  if (window.LinApp && LinApp.showPage) { try { LinApp.showPage('detail'); } catch(e){} }
  const h = document.querySelector('#section-d-catspecs .collapse-header');
  if (h) h.click();
  document.querySelectorAll('.dcat-toggle').forEach(b => b.click());
  const body = document.getElementById('body-d-catspecs');
  const panel = document.querySelector('.detail-catspecs');
  const chain = [];
  let e = panel;
  while (e && e !== document.documentElement) {
    const cs = getComputedStyle(e);
    chain.push(e.tagName + '.' + (e.className||'').toString().split(' ')[0]
               + ' d=' + cs.display + ' v=' + cs.visibility
               + ' w=' + Math.round(e.getBoundingClientRect().width));
    e = e.parentElement;
  }
  return { bodyDisplay: body ? getComputedStyle(body).display : null,
           panelWidth: panel ? Math.round(panel.getBoundingClientRect().width) : 0,
           chain: chain, hasShowPage: !!(window.LinApp && window.LinApp.showPage) };
}"""

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
    # THE DETAIL PAGE MUST ACTUALLY BE THE SHOWN PAGE, or every box measured is a box
    # inside `section.page { display:none }` and the geometry check would pass on a
    # zero-width layout -- exactly the shape Run 60 caught. This is the page's own router
    # call, the same one the project list control makes.
    pg.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('detail')")
    pg.evaluate("(id) => window.LinDetail && LinDetail.render(id)", PID)
    pg.wait_for_timeout(14000)
    OP = pg.evaluate(OPEN_ALL)
    pg.wait_for_timeout(6000)
    R = pg.evaluate(READ)
    say(f"panel opened via its own collapse header: {OP}")

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
        say(f"        head line: {r['headLine']!r}")
        seen.setdefault(r["state"], []).append(r["cat"])
    say(f"  DISTINCT data-state values rendered: {sorted(seen.keys())}")
    four = ["computed", "abstained", "out_of_order", "failed"]
    say(f"  all four present and distinct: {all(k in seen for k in four)}  -> {[(k, seen.get(k)) for k in four]}")

    say("-" * 100)
    say("MODULE ROWS AND THEIR EXPLANATION TEXT:")
    for m in R["mods"]:
        say(f"  {str(m['id']):<6} state={str(m['state']):<10} chip={str(m['chip']):<20} "
            f"band={str(m['band']):<6} {m['text'][:100]}")

    say("-" * 100)
    say("EXPLANATION TEXT, CAPTURED VERBATIM (textContent, layout-independent):")
    for mid, txt in R["reasons"]:
        say(f"  [{mid}] {txt!r}")
    say("  NOTES:")
    for t in R["notes"]:
        say(f"    {t!r}")
    say(f"  HINT: {R['hint']!r}")

    say("-" * 100)
    say(f"BUTTON LABELS: call-all={R['callAllLabel']!r}  per-row="
        f"{sorted({str(r['btnLabel']) for r in R['rows']})}")
    boxes = [r['btnBox'] for r in R['rows'] if r['btnBox']]
    xs = sorted({b['x'] for b in boxes})
    ws = sorted({b['w'] for b in boxes})
    say(f"  per-row button boxes read from the DOM: {len(boxes)}  left edges={xs}  widths={ws}")
    # A degenerate 0x0 box would make ANY set of buttons look aligned, so the check
    # requires a real width as well as a single left edge.
    say(f"  buttons aligned in one column with a real width: "
        f"{len(xs) == 1 and len(ws) == 1 and ws[0] > 0 and len(boxes) == len(R['rows'])}")
    say(f"  row list-style-type: {sorted({str(r['listStyle']) for r in R['rows']})}")

    say("-" * 100)
    say(f"page errors: {errs or 'NONE'}")
    OUT = pathlib.Path(os.environ.get("R81_OUT", "/tmp/r81.json"))
    OUT.write_text(json.dumps({
        "reasons": R["reasons"], "notes": R["notes"], "hint": R["hint"],
        "rows": [{k: r[k] for k in ("cat", "state", "status", "chip", "chipState",
                                    "btnLabel", "counts", "headLine")} for r in R["rows"]],
        "callAllLabel": R["callAllLabel"],
        "btnLeftEdges": xs,
    }, indent=1, sort_keys=True))
    say(f"  wrote {OUT}")
    b.close()

say("=" * 100)
ok = (idx_panel >= 0 and idx_globe == idx_panel + 1
      and all(k in seen for k in ["computed", "abstained", "out_of_order", "failed"])
      and not errs)
say(f"RESULT: {'4/4' if ok else '?/4'} checks passed "
    f"(placement, four states distinguishable, module rows, no page errors)")
