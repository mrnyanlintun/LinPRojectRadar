"""
RUN 115, GOAL 4. THE CAVEAT, READ FROM THE DOM OF THE PAGE THE OWNER LOADS.

NOTHING UNDER TEST IS SUPPLIED. The project is built through the real `projectupload` and
`projectcomputeall` routes. The page is loaded in Chromium exactly as a project manager loads
it, and `window.LinResults.rowFor` is READ ONLY to wait for the page's own fetch to land -- it
is never assigned, never stubbed and never handed a value. The assertion itself is made against
`document.querySelector('[data-completeness-caveat]').innerText`, which is DOM text the page
produced from the server's own response.

PROVED ABLE TO FAIL. Section 3 reloads the SAME page with the server-side caveat suppressed in
the LIVE module, requires the DOM node to be absent, then restores it and requires it back.

Run from `server/`:  python tools/drive_run115_dom.py
"""
import base64, hashlib, json, logging, pathlib, socket, sys, threading, time
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools"); sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)
from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import Participant
client = TestClient(main.app, raise_server_exceptions=False); S = main.SessionFactory

PASS = FAIL = 0
def check(cond, what, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  PASS  {what}" + (f"  [{detail}]" if detail else ""))
    else:    FAIL += 1; print(f"  FAIL  {what}" + (f"  [{detail}]" if detail else ""))
    return bool(cond)
def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, r.text[:400]
    return r.json()
def b64(x): return base64.b64encode(x).decode()

STAMP = str(int(time.time())); BAC = 4_000_000; END = "2026-03-31"
PID = "PRJ-R115DOM-" + STAMP; ADMIN = "r115dom-" + STAMP

DOCS = [
    ("contract", "contract_value", {"original_contract_sum": BAC,
                                    "project_start_date": "2026-01-01",
                                    "project_end_date": "2027-06-30"}),
    ("pay", "pay_application", {"amount_paid_to_date": 1_000_000,
                                "completed_to_date": 1_000_000,
                                "percent_complete_verified": 25.0,
                                "application_date": END, "document_date": END,
                                "original_contingency": 400_000,
                                "remaining_contingency": 380_000}),
    ("tps", "time_phased_schedule", {"planned_value_to_date": 1_000_000,
                                     "planned_percent_complete": 25.0, "data_date": END,
                                     "document_date": END, "total_float": 30,
                                     "consumed_float": 2}),
    ("oac", "oac_minutes", {"document_date": END, "document_risk_score": 0.10,
                            "outstanding_action_items": 2, "subcontractor_disputes": 0,
                            "report_period": "2026-03", "disputes_recorded": 1}),
    ("subr", "subcontractor_report", {"compliance_score": 95, "report_period": "2026-03",
                                      "subcontractor_ratings_json": [
                                          {"Subcontractor": "Northline Mechanical",
                                           "Assessment period": "2026-03",
                                           "Rating": "Very Good"}],
                                      "subcontractor_rating_scale": "owner_five_point_label",
                                      "subcontractor_report_date": END,
                                      "subcontractor_report_version": "1"}),
]

def raw(t): return f"%PDF-1.4 R115DOM {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor(
    {hashlib.sha256(raw(t)).hexdigest(): (ty, ex) for t, ty, ex in DOCS}))
with S() as s:
    r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if r is None:
        s.add(Participant(pseudonymous_code="R115DOM-A-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        r.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 115 caveat",
                                          "sector": "construction", "signals": {},
                                          "events": []}))
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
c = post({"action": "adminparticipantcreate", "session_token": admin,
          "pseudonymous_code": "R115DOM-PM-" + STAMP, "role": "Participant",
          "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": c["participant_id"], "project_role": "PM"})
for t, ty, ex in DOCS:
    post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
          "period_end": END,
          "documents": [{"filename": t + ".pdf", "mimeType": "application/pdf",
                         "dataBase64": b64(raw(t))}]})
post({"action": "projectcomputeall", "session_token": PM, "id": PID})

sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn
cfg = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical")
srv = uvicorn.Server(cfg)
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(200):
    try:
        s_ = socket.create_connection(("127.0.0.1", PORT), 0.2); s_.close(); break
    except OSError: time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"


def open_page():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=SHELL,
                                     args=["--use-gl=swiftshader", "--no-sandbox"])
        page = browser.new_page(viewport={"width": 1280, "height": 2400})
        for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                        "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            page.route(pattern, lambda r: r.abort())
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        out = page.evaluate("""async (id) => {
            if (window.LinApp && LinApp.openDetail) LinApp.openDetail(id);
            await new Promise(r => setTimeout(r, 1500));
            await window.LinDetail.render(id);
            // rowFor is READ, never assigned: this only waits for the page's own fetch.
            for (let i = 0; i < 200; i++) {
              const row = (window.LinResults && window.LinResults.rowFor)
                  ? window.LinResults.rowFor({id: id}) : null;
              if (row && row.information_completeness) break;
              await new Promise(r2 => setTimeout(r2, 250));
            }
            const body = document.querySelector('#body-d-brief');
            if (body) body.style.display = '';
            document.dispatchEvent(new CustomEvent('lin:section-opened',
                                                   {detail: {id: 'd-brief'}}));
            await new Promise(r => setTimeout(r, 6000));
            const node = document.querySelector('[data-completeness-caveat]');
            const sec = document.querySelector('[data-brief-completeness]');
            const brief = document.querySelector('#body-d-brief');
            const rec = document.querySelector('.eb-rec');
            return {
              caveat: node ? (node.innerText || '').trim() : null,
              sectionText: sec ? (sec.innerText || '').trim() : null,
              briefText: brief ? (brief.innerText || '').trim() : null,
              recText: rec ? (rec.innerText || '').trim() : null,
              caveatIsLast: !!(sec && brief &&
                  brief.querySelectorAll('.eb-section')[
                      brief.querySelectorAll('.eb-section').length - 1] === sec)
            };
        }""", PID)
        browser.close()
        return out


print("=" * 94)
print("RUN 115, GOAL 4 -- THE CAVEAT ON THE PAGE THE OWNER LOADS, READ FROM THE DOM")
print("=" * 94)
OUT = open_page()
print("\n--- the caveat node's own text, verbatim from the DOM ---")
print(OUT.get("caveat"))
print("--- end ---\n")
print("BRIEFTEXT:", json.dumps(OUT.get("briefText"))[:900])
check(bool(OUT.get("caveat")), "the caveat node exists in the rendered DOM")
check(str(OUT.get("caveat") or "").startswith("This assessment is based on"),
      "and its text is the owner's sentence", str(OUT.get("caveat"))[:60])
check("per cent of the information required" in str(OUT.get("caveat") or ""),
      "and it states a proportion of the information required")
check(OUT.get("caveatIsLast") is True,
      "and it is the LAST section in the brief -- the bottom of the recommendation")
check(bool(OUT.get("recText")),
      "the recommendation itself rendered above it", str(OUT.get("recText"))[:70])

print()
print("=" * 94)
print("FALSIFICATION -- the same page, with the server-side caveat suppressed in the LIVE module")
print("=" * 94)
from app import information_completeness as ICM
_real = ICM.information_completeness
def _suppressed(documents):
    out = dict(_real(documents)); out["caveat"] = None; return out
import app.documents as DOCMOD
DOCMOD.information_completeness = _suppressed
try:
    BROKEN = open_page()
finally:
    DOCMOD.information_completeness = _real
check(BROKEN.get("caveat") is None,
      "FALSIFIED: with the server sending no caveat, the DOM node is absent",
      str(BROKEN.get("caveat")))
AGAIN = open_page()
check(str(AGAIN.get("caveat") or "").startswith("This assessment is based on"),
      "RESTORED: the caveat is back in the DOM once the suppression is removed",
      str(AGAIN.get("caveat"))[:60])

print("\n" + "=" * 94)
print(f"RUN 115 DOM DRIVER: {PASS} passed, {FAIL} failed, {PASS + FAIL} checks")
print("=" * 94)
sys.exit(1 if FAIL else 0)
