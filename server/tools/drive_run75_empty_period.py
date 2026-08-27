#!/usr/bin/env python3
"""
RUN 75. AN EMPTY PERIOD MUST NOT HIDE A REAL ONE.

Five sequential states of ONE project, each measured by query and by browser:

  P1  documents in period 1 only, computed. No row may exist for period 2 or later.
  P2  the detail page opens on period 1 and shows its figures.
  P3  an empty live row for period 2 is INSERTED BY HAND, bypassing compute. The page
      must still show period 1.
  P4  period 2 documents uploaded and computed. The page opens on period 2.
  P5  every period 2 document archived and recalculated. The page falls back to period 1.

Also establishes, by execution and before any fix:
  E1  does `projectcomputeall` create a row for a period holding no documents?
  E2  does `projectcompute` with a client-supplied empty period create one?
  E3  does `projectperiods` report such a row as computed / latest?

argv[1] = label
"""
from __future__ import annotations
import ast, base64, hashlib, io, json, logging, os, pathlib, socket, sys, threading, time

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run75"
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)

from reportlab.lib.pagesizes import LETTER            # noqa: E402
from reportlab.pdfgen import canvas as rl_canvas      # noqa: E402
from fastapi.testclient import TestClient             # noqa: E402
from sqlalchemy import select, func                   # noqa: E402
import app.main as main                               # noqa: E402
from app.documents import set_extractor_override      # noqa: E402
from app.extraction_client import StubExtractor       # noqa: E402
from app.extraction_fields import extraction_fields_for  # noqa: E402
from app.models import Project                        # noqa: E402
from app.research_identity import hash_access_token, new_ulid  # noqa: E402
from app.research_models import Participant, Observation, Document, DocumentUpload, ComputedResult  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
STAMP = int(time.time())
PID = f"PRJ-R75-{STAMP}"
ADMIN = f"run75-admin-{STAMP}"
P1_END, P2_END = "2026-03-31", "2026-04-30"
LOG: list[str] = []
def say(*a):
    line = " ".join(str(x) for x in a)
    LOG.append(line); print(line, flush=True)

def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:400]}"
    return r.json()
def b64(raw): return base64.b64encode(raw).decode()

# ---- VALUES taken verbatim from Run 74's harness so the fixture is the same shape ----------
_src = (HERE / "drive_run74_did_extraction_store.py").read_text(encoding="utf-8")
_tree = ast.parse(_src)
_vnode = next(n for n in _tree.body
              if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "VALUES")
def values_for(period_end: str) -> dict:
    return eval(compile(ast.Expression(_vnode.value), "<values>", "eval"),
                {"PERIOD_END": period_end}, {})

DOCSET = [
    ("D01_contract_award.pdf",       "contract_value"),
    ("D02_pay_application.pdf",      "pay_application"),
    ("D05_schedule_update.pdf",      "schedule_update"),
    ("D06_monthly_report.pdf",       "monthly_report"),
    ("D09_rfi_log.pdf",              "rfi_log"),
    ("D11_submittal_register.pdf",   "submittal_register"),
    ("D15_safety_report.pdf",        "safety_report"),
    ("D21_change_order.pdf",         "change_order"),
]

def make_pdf(filename, doc_type, ex, period):
    buf = io.BytesIO(); c = rl_canvas.Canvas(buf, pagesize=LETTER)
    c.setFont("Helvetica-Bold", 13); c.drawString(72, 720, filename)
    c.setFont("Helvetica", 9); y = 700
    c.drawString(72, y, f"Document type: {doc_type}  Project RUN75 period {period}"); y -= 16
    c.drawString(72, y, f"run stamp {STAMP} period {period}"); y -= 20
    for k, v in ex.items():
        s = json.dumps(v) if isinstance(v, (list, dict)) else str(v)
        for chunk in [s[i:i+90] for i in range(0, max(len(s), 1), 90)]:
            c.drawString(72, y, f"{k}: {chunk}"); y -= 12
            if y < 60: c.showPage(); c.setFont("Helvetica", 9); y = 720
    c.showPage(); c.save(); return buf.getvalue()

OVERRIDE = {}
def build(period, period_end):
    vals = values_for(period_end); out = []
    for fn, dt in DOCSET:
        ex = {f: vals[f] for f in (extraction_fields_for(dt) or []) if f in vals}
        ex.setdefault("document_date", period_end)
        name = f"P{period}_{fn}"
        raw = make_pdf(name, dt, ex, period)
        OVERRIDE[hashlib.sha256(raw).hexdigest()] = (dt, ex, 0.95)
        out.append((name, raw))
    return out

P1_DOCS = build(1, P1_END)
P2_DOCS = build(2, P2_END)
set_extractor_override(StubExtractor(OVERRIDE))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code=f"R75-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 75 reproduction",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R75-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})

def live_rows():
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PID))
        out = []
        for r in s.scalars(select(ComputedResult).where(
                ComputedResult.project_id == proj.id,
                ComputedResult.superseded_by.is_(None)).order_by(ComputedResult.period)):
            out.append({"period": r.period, "status": r.project_status,
                        "modules": len(r.module_results or []),
                        "docs": len(r.source_documents or [])})
        return out
def show_rows(tag):
    rs = live_rows()
    say(f"  [{tag}] live computed rows: " + (", ".join(
        f"p{r['period']} status={r['status']!r} modules={r['modules']} docs={r['docs']}"
        for r in rs) or "NONE"))
    return rs

say("=" * 100)
say(f"RUN 75  label={LABEL}  project={PID}  DATABASE_URL={os.environ.get('DATABASE_URL')}")
say("=" * 100)

# ------------------------------------------------------------------ STATE 1: period 1 only
U1 = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
           "period_end": P1_END,
           "documents": [{"filename": fn, "mimeType": "application/pdf", "dataBase64": b64(raw)}
                         for fn, raw in P1_DOCS]})
say(f"S1 upload period 1: ok={U1.get('ok')} summary={U1.get('summary')}")
CA = post({"action": "projectcomputeall", "session_token": PM, "id": PID})
say(f"S1 projectcomputeall: ok={CA.get('ok')} keys={sorted(CA.keys())}")
show_rows("after computeall")

# ---- E1/E2: THE ESTABLISHMENT. compute an empty period by client-supplied number.
say("-" * 100)
say("ESTABLISH -- projectcompute with a client-supplied period 2 that holds NO document:")
C2 = post({"action": "projectcompute", "session_token": PM, "id": PID, "period": 2})
say(f"  response ok={C2.get('ok')} error={C2.get('error')!r} "
    f"result_id={C2.get('result_id')} project_status={C2.get('project_status')!r} "
    f"documents={C2.get('documents')}")
rows_after_e2 = show_rows("after projectcompute period 2")
PP = post({"action": "projectperiods", "session_token": PM, "id": PID})
say(f"  projectperiods -> computed_periods={PP.get('computed_periods')} "
    f"latest_computed_period={PP.get('latest_computed_period')} next_period={PP.get('next_period')}")
E_ROW_CREATED = any(r["period"] == 2 for r in rows_after_e2)
say(f"  EMPTY ROW CREATED FOR PERIOD 2: {E_ROW_CREATED}")
say(f"  PAGE WOULD OPEN ON: period {PP.get('latest_computed_period')}")

# clean the establishment row so the proofs start from the stated state
with Session() as s:
    proj = s.scalar(select(Project).where(Project.legacy_id == PID))
    for r in s.scalars(select(ComputedResult).where(
            ComputedResult.project_id == proj.id, ComputedResult.period == 2)):
        s.delete(r)
    s.commit()
say("-" * 100)
say("PROOF 1 -- period 1 only, computed. Rows that exist:")
P1_ROWS = show_rows("proof 1")
say(f"  rows for period >= 2: {[r for r in P1_ROWS if r['period'] >= 2] or 'NONE'}")
PP1 = post({"action": "projectperiods", "session_token": PM, "id": PID})
say(f"  projectperiods computed_periods={PP1.get('computed_periods')} "
    f"latest={PP1.get('latest_computed_period')}")

# ------------------------------------------------------------------------------- BROWSER
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

# The harness NEVER primes LinResults (Run 61's machine-enforced rule). It navigates by
# LinDetail.render and reads back what the page itself fetched.
READ = r"""(pid) => {
  const R = window.LinResults;
  const txt = id => { const e = document.getElementById('section-'+id);
                      return e ? (e.innerText||'').replace(/\s+/g,' ').trim() : null; };
  const proj = { project_id: pid, id: pid };
  const primed = R && R.primedPeriods ? R.primedPeriods(proj) : [];
  const row = R && R.rowFor ? R.rowFor(proj) : null;
  return {
    primed_periods: primed,
    row_period: row ? row.period : null,
    row_status: row ? row.project_status : null,
    row_modules: row && row.module_results ? row.module_results.length : 0,
    ledger_rows: document.querySelectorAll('#section-d-ledger tr').length,
    brief: (txt('d-brief')||'').slice(0, 240),
    ledger: (txt('d-ledger')||'').slice(0, 200),
    canvases_drawn: Array.from(document.querySelectorAll('canvas'))
        .filter(c => c.width>0 && c.height>0).length,
  };
}"""
OPEN_ALL = r"""() => { let n=0; document.querySelectorAll('.collapse-section[id^="section-"]')
  .forEach(el => { const id = el.id.replace(/^section-/,'');
    try { if (!el.classList.contains('open')) { toggleSection(id); n++; } } catch(e){} });
  return n; }"""

from playwright.sync_api import sync_playwright  # noqa: E402
CAP = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME,
                           args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    pg = b.new_page(viewport={"width": 1680, "height": 3200})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
        pg.route(pat, lambda r: r.abort())

    def visit(tag):
        pg.goto(BASE + "/", wait_until="domcontentloaded")
        pg.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        pg.goto(BASE + "/", wait_until="domcontentloaded")
        pg.add_style_tag(content="*,*::before,*::after{transition:none!important;animation:none!important}")
        pg.wait_for_timeout(9000)
        pg.evaluate("(id) => window.LinDetail && LinDetail.render(id)", PID)
        pg.wait_for_timeout(12000)
        pg.evaluate(OPEN_ALL)
        pg.wait_for_timeout(7000)
        r = pg.evaluate(READ, PID)
        CAP[tag] = r
        say(f"  [{tag}] page opened on period {r['row_period']} status={r['row_status']!r} "
            f"modules={r['row_modules']} primed={r['primed_periods']} "
            f"ledger_rows={r['ledger_rows']} canvases={r['canvases_drawn']}")
        say(f"      brief: {r['brief'][:170]}")
        return r

    say("-" * 100)
    say("PROOF 2 -- the detail page opens on period 1 and shows its figures:")
    visit("proof2")

    # ---------------------------------------------------- PROOF 3: HAND-INSERTED EMPTY ROW
    say("-" * 100)
    say("PROOF 3 -- an empty live row for period 2 INSERTED BY HAND, bypassing compute:")
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PID))
        p1 = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == proj.id, ComputedResult.period == 1,
            ComputedResult.superseded_by.is_(None)))
        s.add(ComputedResult(
            result_id=new_ulid(), project_id=proj.id, period=2,
            signal_inputs={}, module_results=[], category_statuses={},
            project_status=None, portfolio_snapshot=None,
            simulation_version=p1.simulation_version, seed=p1.seed,
            period_cutoff=p1.period_cutoff, source_documents=[], abstained=None))
        s.commit()
    show_rows("proof 3, after hand insert")
    PP3 = post({"action": "projectperiods", "session_token": PM, "id": PID})
    say(f"  projectperiods computed_periods={PP3.get('computed_periods')} "
        f"latest={PP3.get('latest_computed_period')}")
    visit("proof3")

    with Session() as s:  # remove the hand-inserted row before proof 4
        proj = s.scalar(select(Project).where(Project.legacy_id == PID))
        for r in s.scalars(select(ComputedResult).where(
                ComputedResult.project_id == proj.id, ComputedResult.period == 2)):
            s.delete(r)
        s.commit()

    # ------------------------------------------------------------- PROOF 4: real period 2
    say("-" * 100)
    say("PROOF 4 -- period 2 documents uploaded and computed:")
    U2 = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 2,
               "period_end": P2_END,
               "documents": [{"filename": fn, "mimeType": "application/pdf",
                              "dataBase64": b64(raw)} for fn, raw in P2_DOCS]})
    say(f"  upload ok={U2.get('ok')} summary={U2.get('summary')}")
    C4 = post({"action": "projectcompute", "session_token": PM, "id": PID, "period": 2})
    say(f"  projectcompute period 2: ok={C4.get('ok')} status={C4.get('project_status')!r} "
        f"documents={C4.get('documents')} error={C4.get('error')!r}")
    show_rows("proof 4")
    PP4 = post({"action": "projectperiods", "session_token": PM, "id": PID})
    say(f"  projectperiods computed_periods={PP4.get('computed_periods')} "
        f"latest={PP4.get('latest_computed_period')}")
    visit("proof4")

    # ----------------------------------------------- PROOF 5: archive period 2, recalculate
    say("-" * 100)
    say("PROOF 5 -- every period 2 document archived, then recalculated:")
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PID))
        ids = [d for d in s.scalars(select(DocumentUpload.document_id).where(
            DocumentUpload.project_id == proj.id, DocumentUpload.period == 2))]
    AR = post({"action": "projectdocumentarchive", "session_token": PM, "id": PID, "period": 2,
               "document_ids": ids, "reason": "Run 75 proof 5",
               "confirmation": "Withdraw these documents from period 2"})
    say(f"  archive ok={AR.get('ok')} archived={AR.get('archived')} error={AR.get('error')!r}")
    C5 = post({"action": "projectcompute", "session_token": PM, "id": PID, "period": 2})
    say(f"  recalculate period 2: ok={C5.get('ok')} recomputed={C5.get('recomputed')} "
        f"status={C5.get('project_status')!r} documents={C5.get('documents')} "
        f"note={C5.get('note')!r} error={C5.get('error')!r}")
    show_rows("proof 5")
    PP5 = post({"action": "projectperiods", "session_token": PM, "id": PID})
    say(f"  projectperiods computed_periods={PP5.get('computed_periods')} "
        f"latest={PP5.get('latest_computed_period')}")
    visit("proof5")

    say("-" * 100)
    say(f"page errors: {errs[:6]}")
    b.close()

say("=" * 100)
pathlib.Path(HERE / f"run75_capture_{LABEL}.json").write_text(
    json.dumps({"label": LABEL, "project": PID, "capture": CAP, "log": LOG},
               indent=2, default=str), encoding="utf-8")
say(f"capture -> tools/run75_capture_{LABEL}.json")
