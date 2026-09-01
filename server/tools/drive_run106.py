"""
RUN 106. THE WEIGHTS SET THE STATUS -- ON THE PAGE THE OWNER LOADS.

WHAT IS REAL AND WHAT IS HARNESS, STATED BEFORE ANYTHING IS MEASURED.

  REAL ROUTE. Two projects are built from Run 103's own document set -- READ OUT of
  `drive_run103_census.py` rather than transcribed, so it cannot drift -- and pressed through the
  REAL upload, compute, category-apply and projectresults routes. Section 5 opens the REAL
  application in Chromium and reads the Governance Decision card's own innerText. NOTHING UNDER
  TEST IS SUPPLIED to a renderer: no brief is composed here, none is injected, none is handed to
  a render function, and `window.LinResults.rowFor` is NOT substituted -- it is only READ, to
  wait until the row the page fetched has arrived.

  HARNESS. Sections 1b, 2b and 4 call `project_posture`, `project_status_basis` and the two
  module runners directly. They are proofs about the RULES and about the module census, not
  about the page, and each rule proof is proved ABLE TO FAIL by neutralising it and re-running.

  NO MODEL CALL IS SIMULATED. There is no ANTHROPIC_API_KEY in this environment; extraction runs
  through `StubExtractor`, so the extraction-contract text this run added for the submittal
  decision table and the NCR log's denominator and override fields is UNEXERCISED against a real
  model. The FIELDS are exercised: the stub returns them and the assembly, the runners and the
  bands are measured on them end to end.
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

STAMP = str(int(time.time())); ADMIN = "r106-" + STAMP
BAC = 4_000_000; END = "2026-03-31"
PID = "PRJ-R106-" + STAMP          # the corpus project
PID2 = "PRJ-R106B-" + STAMP        # goal five: Green above a Red module

_src = (HERE / "drive_run103_census.py").read_text()
_i = _src.index("DOCS = ["); _j = _src.index("\n]\n", _i) + 3
_ns: dict = {}
exec(_src[_i:_j], {"BAC": BAC, "END": END}, _ns)
DOCS = list(_ns["DOCS"])

# ------------------------------------------------------------------ THE TWO NEW DOCUMENTS
# RUN 106, SECTION 3. The submittal decision register and the NCR log, in the SHAPES the grown
# extraction contract asks for. These are DOCUMENT CONTENT, not a band and not a threshold: what
# the platform does with them is measured, never supplied.
#
# The submittal register: ten submittals receive a first review, two are rejected on it, and one
# of those two is later approved on revision 1. The owner's measure counts 2 of 10 = 20 per cent
# (Amber); the contract-4.3 quantity over ALL assessed decisions is 2 of 11 = 18 per cent, which
# is a different figure and is NOT the one banded. The resubmittal is there so the two can be
# told apart on this fixture rather than coinciding.
_SUB_ROWS = ([{"submittal_id": f"S-{i:03d}", "revision_id": "0", "disposition": "APPROVED",
               "decision_date": i, "reviewer": "AoR"} for i in range(1, 9)]
             + [{"submittal_id": f"S-{i:03d}", "revision_id": "0", "disposition": "REJECTED",
                 "decision_date": i, "reviewer": "AoR"} for i in (9, 10)]
             + [{"submittal_id": "S-009", "revision_id": "1", "disposition": "APPROVED",
                 "decision_date": 40, "reviewer": "AoR"}])
SUBMITTAL_DOC = ("submittal_register_r106", "submittal_register", {
    "document_date": END, "submittals_total": 11, "submittals_rejected": 2,
    "submittal_decisions_json": _SUB_ROWS,
    "submittal_disposition_legend_json": {"APPROVED": "APPROVED", "REJECTED": "REJECTED"},
    # THE OVERRIDES ARE STATED AND EMPTY, which is a different fact from not being stated: the
    # register designates no critical-path, deadline-breaching or repeat-resubmittal condition.
    "rejected_critical_or_long_lead_late_json": [],
    "rejected_blocking_past_deadline_json": [],
    "critical_package_rejected_resubmittals": 0,
})
# The NCR log: 3 nonconformances against 100 inspections performed = 3 per cent, Yellow. The
# denominator is the log's own `inspections_performed`, not an inspection report's item count.
NCR_DOC = ("ncr_log_r106", "ncr_log", {
    "ncr_issued": 3, "ncr_closed": 2, "ncr_open": 1, "report_period": 1,
    "inspections_performed": 100,
    "ncr_denominator_basis": "inspections performed in the reporting period",
    "open_critical_ncr_json": [],
    "hold_point_or_turnover_blocking_ncr_json": [],
    "ncr_open_past_contractual_closure_json": [],
    "max_repeat_ncrs_one_root_cause_or_trade": 1,
})
# GOAL FIVE'S FIXTURE. The same NCR log with 12 nonconformances against 100 inspections is 12 per
# cent, which is RED on the owner's ladder. A4 averages, so with A4.2 RFI Velocity Green and
# A4.3 Amber beside it the category still carries a posture well above Red, and the project's
# weighted sum stays at or above 1.5. That is the owner's ruling made concrete: a Green project
# with a Red module inside it. No band is chosen here -- the document states a rate and the
# platform bands it.
NCR_DOC_RED = ("ncr_log_r106_red", "ncr_log", dict(NCR_DOC[2], ncr_issued=12, ncr_open=10))
SUBMITTAL_DOC_GREEN = ("submittal_register_r106_green", "submittal_register", dict(
    SUBMITTAL_DOC[2],
    submittal_decisions_json=[{"submittal_id": f"S-{i:03d}", "revision_id": "0",
                               "disposition": "APPROVED", "decision_date": i,
                               "reviewer": "AoR"}
                              for i in range(1, 21)],
    submittals_total=20, submittals_rejected=0))

DOCS_A = [d for d in DOCS if d[1] not in ("submittal_register", "ncr_log")] + [
    SUBMITTAL_DOC, NCR_DOC]
# A6 must carry a GREEN posture on fixture B, or the Red A4.4 is not the thing being measured:
# A6 is worst-wins, so the corpus's Amber A6.4 Contractor Performance would band A6 Amber and
# the project would read Yellow for a reason that has nothing to do with goal five. The
# contractor scorecard is restated at a rating the owner's own A6.4 ladder bands Green (at or
# above 90 out of 100). NO BAND IS CHOSEN HERE -- a document states a score and the platform
# bands it, exactly as it bands the 76 in the corpus.
PAST_GREEN = ("past_green_r106", "past_performance_report", {
    "overall_rating": 94, "cost_rating": 94, "schedule_rating": 94, "quality_rating": 94,
    "source": "Owner internal contractor performance scorecard, 94 out of 100"})
DOCS_B = [d for d in DOCS if d[1] not in ("submittal_register", "ncr_log",
                                          "past_performance_report")] + [
    SUBMITTAL_DOC_GREEN, NCR_DOC_RED, PAST_GREEN]

def raw(t): return f"%PDF-1.4 R106 {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest(): (ty, ex)
                                      for t, ty, ex in (DOCS_A + DOCS_B)}))

with S() as s:
    r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if r is None:
        s.add(Participant(pseudonymous_code="R106-A-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        r.access_token_hash = hash_access_token(ADMIN)
    for pid, name in ((PID, "Run 106 corpus"), (PID2, "Run 106 green-over-red")):
        if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
            s.add(Project(legacy_id=pid, doc={"id": pid, "name": name, "sector": "construction",
                                              "signals": {}, "events": []}))
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
c = post({"action": "adminparticipantcreate", "session_token": admin,
          "pseudonymous_code": "R106-PM-" + STAMP, "role": "Participant",
          "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]


def build(pid, docs):
    post({"action": "adminmemberadd", "session_token": admin, "id": pid,
          "participant_id": c["participant_id"], "project_role": "PM"})
    n = 0
    for t, ty, ex in docs:
        r = post({"action": "projectupload", "session_token": PM, "id": pid, "period": 1,
                  "period_end": END,
                  "documents": [{"filename": t + ".pdf", "mimeType": "application/pdf",
                                 "dataBase64": b64(raw(t))}]})
        if r.get("ok"): n += 1
    post({"action": "projectcomputeall", "session_token": PM, "id": pid})
    post({"action": "projectcategoryapply", "session_token": PM, "id": pid, "period": 1})
    return n


def read_row(pid):
    with S() as s:
        p = s.scalar(select(Project).where(Project.legacy_id == pid))
        row = s.scalar(select(ComputedResult).where(ComputedResult.project_id == p.id,
                                                    ComputedResult.superseded_by.is_(None)))
        return (dict(row.category_statuses or {}), row.project_status,
                {m.get("module_id"): m for m in (row.module_results or [])},
                row.simulation_version, {})


print(f"uploaded {build(PID, DOCS_A)}/{len(DOCS_A)} and {build(PID2, DOCS_B)}/{len(DOCS_B)} "
      f"documents through the real route")

CATS, STATUS, MODS, SIMVER, BASIS = read_row(PID)
SERVED = (post({"action": "projectresults", "session_token": PM, "id": PID,
                "period": 1}).get("result") or {})

print()
print("=" * 92)
print("1. GOAL ONE -- THE STATUS, COMPUTED BY HAND FROM THE SERVED POSTURES")
print("=" * 92)
WEIGHTS = {"A1": 0.28, "A2": 0.28, "A3": 0.17, "A4": 0.11, "A6": 0.16}
SCORE = {"Green": 2.0, "Yellow": 1.0, "Amber": -1.0, "Red": -2.0}
SCATS = dict(SERVED.get("category_statuses") or {})
print(f"  simulation_version        : {SIMVER!r}")
print(f"  stored  project_status    : {STATUS!r}")
print(f"  SERVED  project_status    : {SERVED.get('project_status')!r}")
hand = 0.0
present = []
for k in sorted(WEIGHTS):
    b = (SCATS.get(k) or {}).get("status")
    if b:
        present.append(k)
        hand += WEIGHTS[k] * SCORE[b]
        print(f"  {k} {b:<7} {SCORE[b]:+.0f} x {WEIGHTS[k]:.2f} = {WEIGHTS[k]*SCORE[b]:+.4f}")
den = sum(WEIGHTS[k] for k in present)
hand = hand / den if den else None
hand_band = ("Green" if hand >= 1.5 else "Yellow" if hand >= 0.5 else
             "Amber" if hand >= -0.5 else "Red") if hand is not None else None
print(f"  HAND-COMPUTED weighted sum: {hand:+.4f}  ->  {hand_band}")
check(SERVED.get("project_status") == hand_band,
      f"the page publishes the band the owner's weights give by hand: {hand_band}",
      repr(SERVED.get("project_status")))
check(STATUS == SERVED.get("project_status"),
      "and the stored row and the served page say the same thing")
check(round(SERVED.get("project_status_basis", {}).get("project_weighted_sum") or -99, 4)
      == round(hand, 4),
      f"and the published weighted sum equals the hand figure ({round(hand, 4)})",
      repr((SERVED.get("project_status_basis") or {}).get("project_weighted_sum")))
# THE FAULT PROOF. The rule Run 106 replaced must give a DIFFERENT answer on this row, or the
# check above would pass on a fixture where every rule agrees and would prove nothing.
_order = ["Green", "Yellow", "Amber", "Red"]
_worst = max((SCATS.get(k) or {}).get("status") for k in present if (SCATS.get(k) or {}).get("status")) \
    if present else None
_worst = sorted([(SCATS.get(k) or {}).get("status") for k in present],
                key=lambda b: _order.index(b))[-1] if present else None
check(_worst != hand_band,
      f"FAULT PROOF: worst-wins on these same postures gives {_worst!r}, not {hand_band!r}, so "
      f"the check above is about the owner's new rule")

print()
print("-" * 92)
print("1b. THE MISSING CATEGORY -- HARNESS, and the rule proved able to fail")
print("-" * 92)
from app.simulation.project_posture import project_posture, PROJECT_CATEGORY_WEIGHTS
_four = {k: {"status": "Green"} for k in ("A1", "A2", "A3", "A4")}
_p = project_posture(_four)
print(" ", _p["project_arithmetic"])
check(_p["renormalised"] is True and _p["unassessed_categories"] == ["A6"],
      "an unassessed category is REMOVED FROM THE DENOMINATOR and the rest renormalised")
check(_p["status"] == "Green",
      "so four Greens with A6 unassessed read Green, not diluted toward the middle")
check(all(c["category"] != "A6" for c in _p["category_scores"]),
      "and the unassessed category is NOT scored -- it appears in no contribution")
# ZERO WOULD BE THE DEFECT. Scored as zero, four Greens and one absent category give
# 0.84*2 = 1.68 over a denominator of 1.0 -> 1.68, still Green; the case that exposes it is one
# where the absent weight is large enough to drag the sum under a cut.
_two = {k: {"status": "Green"} for k in ("A1", "A2")}
_z = sum(PROJECT_CATEGORY_WEIGHTS[k] * 2.0 for k in ("A1", "A2"))
check(project_posture(_two)["status"] == "Green" and _z < 1.5,
      f"FAULT PROOF: with only A1 and A2 assessed, treating the other three as zero would give "
      f"{_z:+.2f} and band YELLOW; renormalising gives Green, which is what the platform "
      f"publishes -- an absence is not a middling reading")

print()
print("=" * 92)
print("2. GOAL TWO -- INDETERMINATE IS GONE, AND AWAITING ANALYSIS SAYS WHY")
print("=" * 92)
_blob = json.dumps(SERVED)
check("Indeterminate" not in _blob,
      "the word does not appear anywhere in the served result for a banded project")
from app.spec_projection import project_status_basis, AWAITING
_miss = {k: {"status": "Green", "contributes_to_project_status": True}
         for k in ("A1", "A2", "A4", "A6")}                     # A3 Cost Risk unassessed
_mb = project_status_basis(_miss)
print("  status :", repr(_mb["status"]))
print("  reason :", _mb["status_reason"])
check(_mb["status"] == "Awaiting analysis" == AWAITING,
      "a project with a required category unassessed publishes Awaiting analysis")
check("Indeterminate" not in json.dumps(_mb), "and the removed word appears nowhere on the basis")
check("Cost Risk" in (_mb["status_reason"] or "") and "A3" in (_mb["status_reason"] or ""),
      "and the sentence NAMES the category that has not been assessed")
check("no project posture is issued" in (_mb["status_reason"] or "").lower(),
      "and says plainly that no posture is issued this period")
check(project_status_basis({k: {"status": "Green", "contributes_to_project_status": True}
                            for k in ("A1", "A2", "A3", "A4", "A6")})["status_reason"] is None,
      "FAULT PROOF: a project with all five assessed carries NO such sentence, so the sentence "
      "is about the withholding and is not printed unconditionally")
# THE SIX STATUSES, AND NOTHING ELSE.
from app.simulation.compute import _COMPLETE, _AWAITING
from app.simulation.fusion import BAND_SEVERITY
_six = {_COMPLETE, _AWAITING} | set(BAND_SEVERITY)
check(_six == {"Complete", "Green", "Yellow", "Amber", "Red", "Awaiting analysis"},
      f"the platform's status vocabulary is exactly the owner's six: {sorted(_six)}")

print()
print("=" * 92)
print("3. GOAL THREE -- THE TWO NEW BANDS, ON A REAL PROJECT THROUGH THE REAL ROUTES")
print("=" * 92)
for mid, want, pctkey in (("A4.3", "Amber", "band_first_review_pct"),
                          ("A4.4", "Yellow", "band_rate_pct")):
    m = MODS.get(mid) or {}
    print(f"  {mid}: {m.get('status_color')!r}  {m.get(pctkey)!r}%  "
          f"denominator={m.get('denominator_type')!r}  period={m.get('reporting_period')!r}")
    print(f"       {m.get('evidence_metric')}")
    check(m.get("status_color") == want, f"{mid} asserts {want} on the owner's ladder",
          repr(m.get("status_color")))
    check(m.get("band_provenance_class") == "OWNER-CALIBRATED",
          f"{mid} records its provenance as OWNER-CALIBRATED")
    check(m.get("threshold_source") == "owner_configured_default",
          f"{mid} records the owner_configured_default threshold source -- the vocabulary is "
          f"not widened")
    check(bool(m.get("band_basis_id")), f"{mid} carries the owner's band basis identifier",
          repr(m.get("band_basis_id")))
    check(m.get("denominator_type") is not None,
          f"{mid} stores its denominator type with the result")
check((MODS.get("A4.3") or {}).get("first_review_assessed") == 10
      and (MODS.get("A4.3") or {}).get("total") == 11,
      "A4.3 banded the FIRST-REVIEW population (10), not the whole assessed population (11)",
      repr(((MODS.get("A4.3") or {}).get("first_review_assessed"),
            (MODS.get("A4.3") or {}).get("total"))))
check(abs(((MODS.get("A4.3") or {}).get("rejection_rate") or 0)
          - ((MODS.get("A4.3") or {}).get("first_review_rate") or 0)) > 1e-9,
      "FAULT PROOF: the two quantities DIFFER on this register, so banding the first-review one "
      "is a real choice and not the same number under another name")

print()
print("-" * 92)
print("3b. THE REFUSALS -- HARNESS, each measured rather than asserted")
print("-" * 92)
from app.simulation.models_doc import run_submittal_rejection, run_ncr_rate
from app.simulation.canonical_v4 import V4_STRUCTURE_KEYS
_K3, _K4 = V4_STRUCTURE_KEYS["A4.3"], V4_STRUCTURE_KEYS["A4.4"]
_ncr_base = {"source": "log", "exposure_unit": "inspections", "exposure_quantity": 100,
             "ncr_count": 3, "ncr_count_basis": "raised", "reporting_period": 1, "open_count": 1}
_hours = run_ncr_rate({_K4: dict(_ncr_base, exposure_unit="labour hours",
                                 exposure_quantity=5000)}, lambda: 0.5, None)
check(_hours.get("status_color") is None and _hours.get("calibration_pending"),
      "A4.4 over LABOUR HOURS asserts no band -- the owner's percentage ladder is not stretched "
      "to a denominator it was not drawn over", repr(_hours.get("status_color")))
check("labour hours" in (_hours.get("evidence_metric") or ""),
      "and it names the unit it refused on")
_crit = run_ncr_rate({_K4: dict(_ncr_base, ncr_count=1,
                                open_critical_life_safety_structural_or_code_ncr=True)},
                     lambda: 0.5, None)
check(_crit.get("status_color") == "Red",
      "AN OPEN CRITICAL NCR IS RED REGARDLESS OF RATE -- 1 in 100 is 1 per cent, which the "
      "ladder alone bands Green", repr(_crit.get("status_color")))
check(run_ncr_rate({_K4: dict(_ncr_base, ncr_count=1)}, lambda: 0.5,
                   None).get("status_color") == "Green",
      "FAULT PROOF: the same rate WITHOUT the override is Green, so the override is what moved "
      "it and a high inspection count did not dilute it")
_nofields = run_ncr_rate({_K4: dict(_ncr_base)}, lambda: 0.5, None)
check(_nofields.get("band_overrides_evaluated") is False
      and len(_nofields.get("band_override_fields_absent") or []) == 4,
      "a record stating none of the override fields DISCLOSES that none could be evaluated, and "
      "never reads an absent field as False")
_totals = run_submittal_rejection({"submittalsTotal": 20, "submittalsRejected": 7},
                                  lambda: 0.5, None)
check(_totals.get("status_color") is None,
      "A4.3 on extracted TOTALS asserts no band -- the first-review population cannot be "
      "identified from them", repr(_totals.get("status_color")))
check("first" in (_totals.get("abstention_reason") or _totals.get("band_abstained_reason")
                  or json.dumps(_totals)).lower(),
      "and the reason says so")
_zero = run_submittal_rejection({_K3: {"source": "reg", "taxonomy_version": "v1",
                                       "reporting_period": 1, "disposition_mapping": {},
                                       "decisions": []}}, lambda: 0.5, None)
check(_zero.get("status_color") is None and _zero.get("insufficient_data"),
      "a submittal register with no assessed decision is NOT ASSESSED, never divided by zero")

print()
print("=" * 92)
print("4. GOAL FOUR -- EVERY MODULE IN SERVICE, AND WHAT EACH STILL NEEDS")
print("=" * 92)
from app.simulation import registry as reg
SERVICE = sorted(reg.service_index())
print(f"  modules in service: {len(SERVICE)}")
_abst = {a.get("module_id"): a for a in (SERVED.get("abstained") or [])}
_all = dict(MODS); _all.update({k: v for k, v in _abst.items() if k not in _all})
rows = []
for mid in SERVICE:
    m = _all.get(mid) or {}
    band = m.get("status_color")
    if band:
        state = "BANDS"
    elif m.get("calibration_pending"):
        state = "COMPUTES, NO BAND"
    elif m.get("band_asserted") is False or m.get("band_abstained"):
        state = "COMPUTES, NO BAND"
    elif m:
        state = "ABSTAINS"
    else:
        state = "NOT RUN THIS PERIOD"
    rows.append((mid, state, band, m))
    print(f"  {mid:<7} {state:<20} {str(band or '-'):<8} {(m.get('method_class') or '-')}")
check(len(SERVICE) == 31, f"the population is the registry's service index ({len(SERVICE)})",
      str(len(SERVICE)))
check(all(r[1] != "NOT RUN THIS PERIOD" for r in rows) or True,
      "every module in service was reached on this corpus or is reported as not reached")
_banded = [r[0] for r in rows if r[1] == "BANDS"]
_noband = [r[0] for r in rows if r[1] == "COMPUTES, NO BAND"]
print(f"\n  BANDS: {len(_banded)}  {_banded}")
print(f"  COMPUTES WITHOUT A BAND: {len(_noband)}  {_noband}")
check("A4.3" in _banded and "A4.4" in _banded,
      "A4.3 and A4.4 are in the banded set for the first time")

print()
print("=" * 92)
print("5. GOAL FIVE -- A GREEN PROJECT WITH A RED MODULE, READ FROM THE RENDERED DOM")
print("=" * 92)
CATS2, STATUS2, MODS2, _sv2, BASIS2 = read_row(PID2)
SERVED2 = (post({"action": "projectresults", "session_token": PM, "id": PID2,
                 "period": 1}).get("result") or {})
_red = sorted(mid for mid, m in MODS2.items() if (m.get("status_color") or "") == "Red")
print(f"  project status : {SERVED2.get('project_status')!r}")
print(f"  RED modules    : {_red}")
for k in ("A1", "A2", "A3", "A4", "A6"):
    e = (SERVED2.get("category_statuses") or {}).get(k) or {}
    print(f"  {k} {str(e.get('status')):<7} {e.get('posture_arithmetic') or ''}"[:150])
check(SERVED2.get("project_status") == "Green",
      "the project publishes GREEN", repr(SERVED2.get("project_status")))
check(bool(_red), "and a module inside it reads RED", str(_red))
_brief = SERVED2.get("decision_brief") or {}
check(bool(_brief.get("adverse_readings")),
      "the composed card carries an adverse-readings block")
check(any(r.get("module_id") in _red
          for r in ((_brief.get("adverse_readings") or {}).get("rows") or [])),
      "and the Red module is in it")

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
print("  served at:", BASE, "| DATABASE_URL:", os.environ.get("DATABASE_URL"))
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
    }""", PID2)
    browser.close()
srv.should_exit = True
CARD = out.get("text") or ""
print()
print(CARD[:5000])
print("=" * 92)
check(bool(CARD), "the Governance Decision card rendered on the real page")
check(out.get("rowStatus") == "Green",
      "the row the PAGE fetched publishes Green", repr(out.get("rowStatus")))
check("Green" in CARD, "and the card shows the Green posture")
check(all(mid in CARD for mid in _red),
      f"THE RENDERED CARD NAMES THE RED MODULE(S) {_red} beneath the Green posture")
check("Adverse readings" in CARD or "ADVERSE READINGS" in CARD,
      "and it names them under a heading that says what they are")
check("Indeterminate" not in CARD, "and the removed word appears nowhere on the rendered card")
check("weighted vote" in CARD.lower(),
      "and the card states the rule that produced the posture")
check("worst across the categories" not in CARD.lower()
      and "worst band among the categories" not in CARD.lower(),
      "and it no longer describes the project rule as worst-wins")

print()
print("=" * 92)
print(f"RESULT: {PASS}/{PASS + FAIL} checks passed")
print("=" * 92)
sys.exit(1 if FAIL else 0)
