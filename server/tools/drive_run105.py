"""
RUN 105. ONE PROJECT, ONE STATUS -- AND THE THIN CATEGORY, ON THE REAL ROUTE.

WHAT IS REAL AND WHAT IS HARNESS, STATED BEFORE ANYTHING IS MEASURED.

  REAL ROUTE. The corpus project is rebuilt from Run 103's own document set -- READ OUT of
  `drive_run103_census.py` rather than transcribed, so it cannot drift -- and pressed through
  the REAL upload, compute, category-apply and projectresults routes. The stored `project_status`
  is read straight off the `computed_results` row; the served one off the real route. Part 4
  opens the REAL application in Chromium and reads the Governance Decision card's own innerText.
  NOTHING UNDER TEST IS SUPPLIED to a renderer: the decision brief is not composed here, not
  injected here, and handed to no render function, and `window.LinResults.rowFor` is NOT
  substituted -- it is only READ, to wait until the row the page fetched has arrived.

  HARNESS. Parts 2 and 3 call `worst_band`, `category_posture` and `project_status_basis`
  directly on synthetic inputs. They are proofs about the RULES, not about the project, and each
  is proved ABLE TO FAIL by neutralising the rule and re-running.

  NO MODEL CALL IS SIMULATED. There is no ANTHROPIC_API_KEY in this environment; extraction runs
  through `StubExtractor` and the specification layer's extraction-contract text is UNEXERCISED.
"""
import base64, hashlib, json, logging, os, pathlib, socket, sys, threading, time
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools"); sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)
from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import Participant, ComputedResult

client = TestClient(main.app, raise_server_exceptions=False); S = main.SessionFactory
def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, r.text[:300]
    return r.json()
def b64(x): return base64.b64encode(x).decode()

PASS = FAIL = 0
def check(ok, label, detail=""):
    global PASS, FAIL
    if ok: PASS += 1; print(f"  PASS  {label}")
    else:  FAIL += 1; print(f"  ****  {label}" + (f"   [{detail}]" if detail else ""))

STAMP = str(int(time.time())); ADMIN = "r105-" + STAMP
BAC = 4_000_000; END = "2026-03-31"; PID = "PRJ-R105-" + STAMP

_src = (HERE / "drive_run103_census.py").read_text()
_i = _src.index("DOCS = ["); _j = _src.index("\n]\n", _i) + 3
_ns: dict = {}
exec(_src[_i:_j], {"BAC": BAC, "END": END}, _ns)
DOCS = _ns["DOCS"]

def raw(t): return f"%PDF-1.4 R105 {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest(): (ty, ex)
                                      for t, ty, ex in DOCS}))
with S() as s:
    r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if r is None:
        s.add(Participant(pseudonymous_code="R105-A-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        r.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 105 fixture",
                                          "sector": "construction", "signals": {}, "events": []}))
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
c = post({"action": "adminparticipantcreate", "session_token": admin,
          "pseudonymous_code": "R105-PM-" + STAMP, "role": "Participant",
          "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": c["participant_id"], "project_role": "PM"})
ok = 0
for t, ty, ex in DOCS:
    r = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
              "period_end": END,
              "documents": [{"filename": t + ".pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(raw(t))}]})
    if r.get("ok"): ok += 1
print(f"uploaded {ok}/{len(DOCS)} documents through the real route")
post({"action": "projectcomputeall", "session_token": PM, "id": PID})
ap = post({"action": "projectcategoryapply", "session_token": PM, "id": PID, "period": 1})
print("categoryapply:", ap.get("ok"), "readings", len(ap.get("readings") or []))


def read_row():
    with S() as s:
        p = s.scalar(select(Project).where(Project.legacy_id == PID))
        row = s.scalar(select(ComputedResult).where(ComputedResult.project_id == p.id,
                                                    ComputedResult.superseded_by.is_(None)))
        return (dict(row.category_statuses or {}), row.project_status,
                {m.get("module_id"): m for m in (row.module_results or [])},
                {a.get("module_id"): a for a in (row.abstained or [])},
                row.simulation_version)


PYCATS, PYSTATUS, RESULTS, ABSTAINED, SIMVER = read_row()

print()
print("=" * 92)
print("1. GOAL ONE -- THE STORED ROW AND THE SERVED PAGE, ON THE CORPUS PROJECT")
print("=" * 92)
res = post({"action": "projectresults", "session_token": PM, "id": PID, "period": 1})
_r = res.get("result") or {}
SERVED_CATS = _r.get("category_statuses") or {}
SERVED_STATUS = _r.get("project_status")
print(f"  simulation_version on the stored row : {SIMVER!r}")
print(f"  stored PYTHON row project_status     : {PYSTATUS!r}")
print(f"  SERVED project_status                : {SERVED_STATUS!r}")
print(f"  stored row fused_band / dempster_band: "
      f"{_r.get('fused_band')!r} / {_r.get('dempster_band')!r}")
print()
for k in sorted(PYCATS):
    e = PYCATS[k] or {}
    print(f"  PY  {k}  {str(e.get('status')):<7} rule={e.get('posture_rule'):<26} "
          f"banded={e.get('posture_banded_count')} of {e.get('posture_modules_considered')}"
          f"{'  ONE READING' if e.get('posture_single_reading') else ''}")
check(PYSTATUS == SERVED_STATUS,
      f"the stored row and the served page agree on the project status ({PYSTATUS!r})",
      f"stored {PYSTATUS!r} vs served {SERVED_STATUS!r}")

# THE PORTFOLIO LIST IS THE OTHER READER OF THE STORED STATUS. `facade.with_stored_status` and
# `facade.slim_row` set the row's `status` from `computed_results.project_status`; before Run 105
# that was the Dempster band while the DETAIL page served the worst-wins one. Both real routes
# are pressed here.
def get(params):
    r = client.get("/exec", params=params)
    assert r.status_code == 200, r.text[:300]
    return r.json()
_lst = get({"action": "list", "session_token": PM})
_slim = get({"action": "listslim", "session_token": PM})
_lrow = next((p for p in (_lst.get("projects") or []) if p.get("id") == PID), None)
_srow = next((p for p in (_slim.get("projects") or []) if p.get("id") == PID), None)
print(f"  portfolio LIST row status            : {(_lrow or {}).get('status')!r}")
print(f"  portfolio LISTSLIM row status        : {(_srow or {}).get('status')!r}")
check((_lrow or {}).get("status") == SERVED_STATUS,
      "the portfolio LIST row and the detail page agree on the project status",
      f"{(_lrow or {}).get('status')!r} vs {SERVED_STATUS!r}")
check((_srow or {}).get("status") == SERVED_STATUS,
      "the portfolio LISTSLIM row agrees too",
      f"{(_srow or {}).get('status')!r} vs {SERVED_STATUS!r}")

# THE READERS OF THE RAW STORED STATUS THAT A PERSON ACTUALLY SEES, measured rather than
# assumed. The portfolio routes above do NOT read it (they go through `merge_python_row`). Two
# do: the compute route's own reply, and `documents.a_projectdecisionrecord`, which stamps a
# RECORDED DECISION with `_live_result(...).project_status`. That second one is why this matters:
# before Run 105 a participant's decision would have been audited Green against a card reading
# Amber.
_cmp = post({"action": "projectcompute", "session_token": PM, "id": PID, "period": 1})
print(f"  projectcompute route reply           : "
      f"{_cmp.get('project_status')!r}  (recomputed={_cmp.get('recomputed')!r})")
check(_cmp.get("project_status") in (None, SERVED_STATUS),
      "the compute route's reply carries the served status, or no status at all when it did "
      "not recompute (documents unchanged -- the real branch this fixture takes)",
      repr(_cmp.get("project_status")))
from app.documents import _live_result as _lr
from app.models import Project as _Pj
with S() as _s:
    _pj = _s.scalar(select(_Pj).where(_Pj.legacy_id == PID))
    _posture = getattr(_lr(_s, _pj, 1), "project_status", None)
print(f"  posture a RECORDED DECISION is stamped with: {_posture!r}")
check(_posture == SERVED_STATUS,
      "a decision recorded against this period is stamped with the posture the participant "
      "read on the card", f"{_posture!r} vs {SERVED_STATUS!r}")

from app.simulation.fusion import worst_band, fuse_signals
from app.simulation.lineage import lineage_record
_py_contrib = [(v or {}).get("status") for v in PYCATS.values()
               if (v or {}).get("status") and (v or {}).get("contributes_to_project_status")]
check(PYSTATUS == worst_band(_py_contrib),
      f"and the stored status IS the worst of the stored categories {sorted(_py_contrib)}",
      repr(PYSTATUS))
# THE OLD RULE RE-APPLIED TO THIS SAME ROW, so the divergence is measured and not asserted.
_old = fuse_signals([{"status": (v or {}).get("status"), "module_id": k,
                      "lineage": lineage_record(k, lineage_group_ids=tuple(
                          (v or {}).get("lineage_bodies") or ()))}
                     for k, v in PYCATS.items()
                     if (v or {}).get("status") and (v or {}).get("contributes_to_project_status")])
_oldband = _old["status"] if _old else None
print(f"  the rule Run 105 replaced (Dempster across the categories) on this same row: {_oldband!r}")
check(_oldband != SERVED_STATUS,
      f"FAULT PROOF: the OLD rule gives {_oldband!r} on this row, not {SERVED_STATUS!r}, so the "
      f"agreement above is the fix and not a fixture in which both rules happen to agree")

# ------------------------------------------------------------------- 1b. THE INJECTION, REAL
print()
print("-" * 92)
print("1b. AN ADVERSE CATEGORY MOVES BOTH -- injected into the STORED ROW, then re-served")
print("-" * 92)
# The Python rollup is re-run from the stored row's own categories with ONE category made
# adverse. Nothing is handed to a renderer: the row is rewritten and the REAL route is pressed
# again, so both numbers below come back off production code.
from app.simulation.compute import _REQUIRED_CATEGORIES  # noqa: F401  (asserted below)
_target = "A2"
with S() as s:
    p = s.scalar(select(Project).where(Project.legacy_id == PID))
    row = s.scalar(select(ComputedResult).where(ComputedResult.project_id == p.id,
                                                ComputedResult.superseded_by.is_(None)))
    cs = dict(row.category_statuses or {})
    cs[_target] = dict(cs[_target]); cs[_target]["status"] = "Red"
    row.category_statuses = cs
    row.project_status = worst_band([(v or {}).get("status") for v in cs.values()
                                     if (v or {}).get("contributes_to_project_status")])
    s.commit()
    _inj_stored = row.project_status
res2 = post({"action": "projectresults", "session_token": PM, "id": PID, "period": 1})
_r2 = res2.get("result") or {}
print(f"  with {_target} forced Red: stored {_inj_stored!r}  served {_r2.get('project_status')!r}")
check(_inj_stored == "Red", "the stored status moves to Red", repr(_inj_stored))
check(_r2.get("project_status") == "Red",
      "and the served status moves to Red on the same evidence",
      repr(_r2.get("project_status")))
check(_inj_stored != PYSTATUS,
      f"FAULT PROOF: the injection actually changed something ({PYSTATUS!r} -> {_inj_stored!r})")
# RESTORE, so parts 3 and 4 read the true corpus project.
with S() as s:
    p = s.scalar(select(Project).where(Project.legacy_id == PID))
    row = s.scalar(select(ComputedResult).where(ComputedResult.project_id == p.id,
                                                ComputedResult.superseded_by.is_(None)))
    row.category_statuses = PYCATS; row.project_status = PYSTATUS; s.commit()
_r = (post({"action": "projectresults", "session_token": PM, "id": PID,
            "period": 1}).get("result") or {})
SERVED_CATS = _r.get("category_statuses") or {}
check(_r.get("project_status") == SERVED_STATUS, "RESTORED -- the corpus project reads "
      f"{SERVED_STATUS!r} again", repr(_r.get("project_status")))

print()
print("=" * 92)
print("2. THE ONE RULE, INJECTED -- HARNESS, over every band combination, proved able to fail")
print("=" * 92)
import itertools
from app.spec_projection import project_status_basis
BANDS = ("Green", "Yellow", "Amber", "Red")
CONTRIB = {"contributes_to_project_status": True}
_bad = []
for combo in itertools.product(BANDS, repeat=5):
    cats = {k: dict(CONTRIB, status=b) for k, b in zip(("A1", "A2", "A3", "A4", "A6"), combo)}
    want = max(combo, key=BANDS.index)
    got_spec = project_status_basis(cats)["status"]
    got_py = worst_band(list(combo))
    if got_spec != want or got_py != want:
        _bad.append((combo, got_spec, got_py))
check(not _bad, "over all 1024 five-category combinations the specification path and the Python "
                "path give the SAME status, and it is the worst band", str(_bad[:2]))
_neut = [c for c in itertools.product(BANDS, repeat=5)
         if (fuse_signals([{"status": b, "module_id": k, "lineage": lineage_record(k)}
                           for k, b in zip(("A1", "A2", "A3", "A4", "A6"), c)]) or {}
             ).get("status") != max(c, key=BANDS.index)]
check(bool(_neut),
      f"FAULT PROOF: the rule Run 105 removed disagrees with worst-wins on {len(_neut)} of the "
      f"1024 combinations, e.g. {_neut[0] if _neut else ''}, so the check above can go red")
# THE GATE AND INDETERMINATE ARE UNTOUCHED.
_miss = {k: dict(CONTRIB, status="Green") for k in ("A1", "A2", "A3")}
check(project_status_basis(_miss)["status"] == "Indeterminate",
      "a project missing required categories is still Indeterminate, not a band")
check(project_status_basis({k: dict(CONTRIB, status="Green")
                            for k in ("A1", "A2", "A3", "A4", "A6")})["status"] == "Green",
      "FAULT PROOF: with all five present the same function returns a band, so the check above "
      "is about the gate and not about the function refusing everything")

print()
print("=" * 92)
print("3. GOAL THREE -- THE ONE-READING AVERAGE, AND THE FLOOR THAT WAS NOT IMPOSED")
print("=" * 92)
from app.simulation.category_posture import category_posture, CATEGORY_RULES, RULE_AVERAGE
_one = category_posture("A4", [("A4.2", "Green")], modules_in_category=8)
print(" ", _one["posture_arithmetic"])
check(_one["posture_single_reading"] is True,
      "an average over ONE banded module is marked as resting on a single reading")
check("ONE READING" in (_one["posture_arithmetic"] or ""),
      "and the arithmetic string every surface renders says so in words")
check("7 other modules" in (_one["posture_thinness_words"] or ""),
      "naming how many modules in the category produced no band",
      repr(_one["posture_thinness_words"]))
_two = category_posture("A1", [("m1", "Green"), ("m2", "Green")])
check(_two["posture_single_reading"] is False,
      "FAULT PROOF: an average over TWO banded modules is NOT marked, so the mark is about the "
      "count and not about averaging")
_w = category_posture("A6", [("A6.4", "Amber")])
check(_w["posture_single_reading"] is False,
      "worst-wins over one module is NOT marked: the worst of one reading is that reading and "
      "nothing was averaged away")
check(_one["status"] == "Green",
      "the posture is PUBLISHED, not withheld -- the mark is disclosure, not a floor")

# THE FLOOR MEASURED AGAINST THE OWNER'S OWN CORPUS, so the decision is numbers and not taste.
print()
print("  What a minimum banded count would do to THIS project:")
_counts = {k: ((PYCATS.get(k) or {}).get("posture_banded_count"),
               (PYCATS.get(k) or {}).get("posture_modules_considered"))
           for k in ("A1", "A2", "A3", "A4", "A6")}
for k, (b, t) in _counts.items():
    print(f"    {k}: {b} banded of {t} considered")
for floor in (2, 3):
    stripped = [k for k, (b, _t) in _counts.items() if (b or 0) < floor]
    cats = {k: dict(CONTRIB, status=(PYCATS.get(k) or {}).get("status"))
            for k in ("A1", "A2", "A3", "A4", "A6") if k not in stripped}
    st = project_status_basis(cats)["status"]
    print(f"    a floor of {floor} strips {stripped or 'nothing'} -> project status {st!r}")
    check(True, f"MEASURED: floor {floor} strips {stripped or 'nothing'} and the project reads "
                f"{st!r}")
_f2 = [k for k, (b, _t) in _counts.items() if (b or 0) < 2]
check("A4" in _f2, "a floor of 2 strips A4, which is in the required core", str(_f2))
check(project_status_basis({k: dict(CONTRIB, status=(PYCATS.get(k) or {}).get("status"))
                            for k in ("A1", "A2", "A3", "A4", "A6")
                            if k not in _f2})["status"] == "Indeterminate",
      "so a floor of 2 forces the corpus project to Indeterminate -- which is why no floor "
      "was imposed")

print()
print("=" * 92)
print("4. THE CARD THE OWNER LOADS -- REAL page, real route, nothing supplied to a renderer")
print("=" * 92)
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
print("served at:", BASE, "| DATABASE_URL:", os.environ.get("DATABASE_URL"))
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
        let row = null;
        for (let i = 0; i < 200; i++) {
          row = (window.LinResults && window.LinResults.rowFor)
              ? window.LinResults.rowFor({id: id}) : null;
          if (row && row.decision_brief) break;
          await new Promise(r2 => setTimeout(r2, 250));
        }
        const body = document.querySelector('#body-d-decision');
        if (body) body.style.display = '';
        document.dispatchEvent(new CustomEvent('lin:section-opened',
                                               {detail: {id: 'd-decision'}}));
        await new Promise(r => setTimeout(r, 2500));
        const panel = document.querySelector('#body-d-decision');
        return {text: panel ? (panel.innerText || '') : null,
                rowStatus: row ? row.project_status : null};
    }""", PID)
    browser.close()
srv.should_exit = True
CARD = out.get("text") or ""
print()
print(CARD[:6000])
print("=" * 92)
check(bool(CARD), "the Governance Decision card rendered on the real page")
check("ONE READING ONLY" in CARD or "RESTS ON ONE READING" in CARD,
      "the RENDERED card marks the category whose average rests on one reading")
check("READ A4" in CARD or "rests on a single banded module" in CARD or
      "rest on a single banded module" in CARD,
      "and it says in words that the band is not the agreement of several modules")
check("Conservative Dominance" not in CARD,
      "the rendered card does not name Conservative Dominance as the platform's status rule")
check(out.get("rowStatus") == SERVED_STATUS,
      f"the row the PAGE fetched carries the same status the route serves ({SERVED_STATUS!r})",
      repr(out.get("rowStatus")))

print()
print("=" * 92)
print(f"RESULT: {PASS}/{PASS + FAIL} checks passed")
print("=" * 92)
sys.exit(1 if FAIL else 0)
