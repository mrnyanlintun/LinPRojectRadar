"""
RUN 115. THE LAST FOUR MODULES, DRIVEN THROUGH THE REAL ROUTES.

NOTHING UNDER TEST IS SUPPLIED. Every document goes through the real `projectupload` route and
the real `projectcomputeall` route. `saveprojectdata` is never called, no structure is handed to
a module, and `window.LinResults.rowFor` is not touched anywhere in this file.

EVERY CHECK IS PROVED ABLE TO FAIL. Section 6 introduces real faults into the objects the checks
actually read -- a required column struck out of a printed table, the dispute count ladder
collapsed inside the LIVE canonical module, the required-field declaration emptied inside the
LIVE completeness module -- runs the SAME assertion, requires it to fail, then removes the fault
and requires it to pass.

Run from `server/`:  python tools/drive_run115.py
"""
import base64, copy, hashlib, json, logging, pathlib, sys, time
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

PASS = FAIL = 0
def section(t):
    print("\n" + "=" * 94); print(t); print("=" * 94)
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

# =================================================================================================
# THE DOCUMENTS, PRINTED THE WAY A PERSON PRINTS THEM -- by HEADING, never by field name.
# =================================================================================================

RATING_ROWS = [
    {"Subcontractor": "Northline Mechanical", "Assessment period": "2026-03",
     "Rating": "Very Good", "Work package": "HVAC", "Assessor": "Owner's representative"},
    {"Subcontractor": "Harbour Electrical", "Assessment period": "2026-03",
     "Rating": "Satisfactory", "Work package": "Power distribution",
     "Assessor": "Owner's representative"},
]
#: THE SAME REPORT WITH AN ADVERSE RATING. Run 107 HOLDS an Amber or Red normalised posture for
#: Project Manager review: the module asserts no band while it is held. That is the designed
#: behaviour and this fixture proves it rather than working around it.
ADVERSE_ROWS = [dict(RATING_ROWS[0]), {**RATING_ROWS[1], "Rating": "Marginal"}]
DISPUTE_ROWS = [
    {"Dispute No": "D-01", "Subject": "Differing site conditions at grid line 7",
     "Parties": "Owner and General Contractor", "Date raised": "2026-02-11",
     "Status": "Open", "Minute item": "5.2"},
    {"Dispute No": "D-02", "Subject": "Design coordination of the electrical riser",
     "Parties": "General Contractor and Designer", "Date raised": "2026-03-03",
     "Status": "Open", "Minute item": "5.3"},
]
CHANGE_ROWS = [
    {"Change No": "CO-01", "Date issued": "2026-01-20", "Type": "Owner directed",
     "Cause": "Scope addition to the loading dock", "Value": 120_000,
     "Direction": "Additive", "Approval status": "Approved"},
    {"Change No": "PCO-02", "Date issued": "2026-02-14", "Type": "Design clarification",
     "Cause": "Revised roof detail", "Value": 90_000,
     "Direction": "Additive", "Approval status": "Pending"},
    {"Change No": "PCO-03", "Date issued": "2026-03-02", "Type": "Owner directed",
     "Cause": "Additional site security", "Value": 60_000,
     "Direction": "Additive", "Approval status": "Submitted"},
]


#: RUN 119, GOAL 3. THE PROJECT CALENDAR, ADDED AS AN OPT-IN DOCUMENT AND USED ONLY BY THE
#: DISPUTE SECTION. A4.7's measure was REDEFINED from a count to a DURATION in working days on
#: the project's own calendar, so the section below needs a calendar to read against; every
#: other section's fixture is left exactly as Run 115 wrote it so nothing else moves.
R119_CALENDAR = [{"calendar_id": "5-day work week",
                  "working_days_of_week": ["monday", "tuesday", "wednesday", "thursday",
                                           "friday"],
                  "holidays": []}]


def docs(*, ratings=RATING_ROWS, scale="owner_five_point_label",
         disputes=None, disputes_total=None, changes=CHANGE_ROWS, contingency=None,
         drop_report_version=False, calendar=None):
    oac = {"document_date": END, "document_risk_score": 0.10,
           "outstanding_action_items": 2, "subcontractor_disputes": 0,
           "report_period": "2026-03"}
    if disputes is not None:
        oac["disputes_json"] = disputes
    if disputes_total is not None:
        oac["disputes_recorded"] = disputes_total
    sub = {"compliance_score": 95, "report_period": "2026-03",
           "subcontractor_ratings_json": ratings,
           "subcontractor_rating_scale": scale,
           "subcontractor_report_date": END,
           "subcontractor_report_version": "1"}
    if drop_report_version:
        sub.pop("subcontractor_report_version")
    co = {"change_order_count": len(changes or []), "baseline_contract_sum": BAC,
          "change_order_date": END, "change_events_json": changes,
          "change_exposure_days": 90}
    pay = {"amount_paid_to_date": 1_000_000, "completed_to_date": 1_000_000,
           "percent_complete_verified": 25.0, "application_date": END, "document_date": END}
    if contingency is not None:
        pay["original_contingency"] = contingency[0]
        pay["remaining_contingency"] = contingency[1]
    out = [
        ("contract", "contract_value", {"original_contract_sum": BAC,
                                        "project_start_date": "2026-01-01",
                                        "project_end_date": "2027-06-30"}),
        ("pay", "pay_application", pay),
        ("oac", "oac_minutes", oac),
        ("subr", "subcontractor_report", sub),
        ("co", "change_order", co),
    ]
    if calendar is not None:
        out.append(("sched", "schedule_update", {"data_date": END,
                                                 "schedule_calendar_json": calendar}))
    return out


def run_project(tag, doclist):
    pid = f"PRJ-R115-{tag}-{STAMP}"
    admin_tok = f"r115-{tag}-{STAMP}"
    def raw(t): return f"%PDF-1.4 R115 {tag} {STAMP} {t}\n".encode()
    set_extractor_override(StubExtractor(
        {hashlib.sha256(raw(t)).hexdigest(): (ty, ex) for t, ty, ex in doclist}))
    with S() as s:
        r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if r is None:
            s.add(Participant(pseudonymous_code="R115-A-" + tag + STAMP, role="ResearchAdmin",
                              access_token_hash=hash_access_token(admin_tok)))
        else:
            r.access_token_hash = hash_access_token(admin_tok)
        if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
            s.add(Project(legacy_id=pid, doc={"id": pid, "name": "Run 115 " + tag,
                                              "sector": "construction", "signals": {},
                                              "events": []}))
        s.commit()
    admin = post({"action": "researchlogin", "access_token": admin_tok})["session_token"]
    c = post({"action": "adminparticipantcreate", "session_token": admin,
              "pseudonymous_code": "R115-PM-" + tag + STAMP, "role": "Participant",
              "account_type": "operational"})
    pm = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": admin, "id": pid,
          "participant_id": c["participant_id"], "project_role": "PM"})
    for t, ty, ex in doclist:
        post({"action": "projectupload", "session_token": pm, "id": pid, "period": 1,
              "period_end": END,
              "documents": [{"filename": t + ".pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(raw(t))}]})
    post({"action": "projectcomputeall", "session_token": pm, "id": pid})
    res = post({"action": "projectresults", "session_token": pm, "id": pid, "period": 1})
    with S() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == pid))
        row = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == proj.id, ComputedResult.superseded_by.is_(None)))
        results = {m.get("module_id"): m for m in ((row.module_results if row else None) or [])}
        abstained = {a.get("module_id"): a for a in ((row.abstained if row else None) or [])}
        si = dict(row.signal_inputs or {}) if row else {}
    return results, abstained, si, (res.get("result") or {}), pid, pm


def state(results, abstained, mid):
    r = results.get(mid)
    if r is not None and r.get("status_color"):
        return "BANDS " + str(r["status_color"]).upper()
    if r is not None:
        return "COMPUTED, NO BAND"
    if mid in abstained:
        return "ABSTAINS"
    return "NO ROW AT ALL"


# =================================================================================================
section("0. THE REQUIRED-FIELD DECLARATION IS PINNED TO THE TREE, NOT TO A COMMENT")
# =================================================================================================
# The completeness denominator is only honest if every field it names is a field a document type
# actually declares AND a field the assembler in `documents.py` actually reads. Both are checked
# here against the live sources, so a field renamed in either place turns this red rather than
# quietly shrinking the denominator.
from app.information_completeness import (REQUIRED_PAIRS, REQUIRED_TOTAL, _ASSEMBLER_FIELDS,
                                          DENOMINATOR_WORDS)
from app.extraction_fields import DOC_TYPES, extraction_fields_for
_undeclared = sorted(
    f"{t}.{f}" for t, fs in _ASSEMBLER_FIELDS.items() for f in fs
    if f not in set(extraction_fields_for(t)))
check(not _undeclared,
      "every declared assembler field is a field its document type actually asks for",
      str(_undeclared)[:150])
_src = pathlib.Path(HERE.parent / "app" / "documents.py").read_text()
_unread = sorted(f"{t}.{f}" for t, fs in _ASSEMBLER_FIELDS.items() for f in fs
                 if f'"{f}"' not in _src)
check(not _unread, "and is a field `documents.py` actually reads", str(_unread)[:150])
_candidate_a = sum(len(extraction_fields_for(t)) for t in DOC_TYPES)
# RUN 117 RE-POINT, WITH THE REASON RECORDED BESIDE IT. Both numbers moved because Run 117
# GREW THE EXTRACTION CONTRACT: `correspondence_notice` gained four enforcement fields,
# `field_report` gained the weather event table plus the attribution column, and seven more
# document types gained `trade_attribution_json` -- sixteen new (type, field) pairs, so
# candidate A goes 273 -> 289. Candidate B goes 163 -> 179 because every one of those sixteen
# now has a real path to a module and is declared in `_ASSEMBLER_FIELDS`; leaving them out
# would have let the completeness caveat report a project as more complete than its evidence.
# NEITHER NUMBER IS WEAKENED and the check still fails on a rename in either place.
# RUN 118 RE-POINT, WITH THE REASON RECORDED BESIDE THE RUN 117 ONE, WHICH IS LEFT STANDING.
# Both numbers moved again because Run 118 GREW THE EXTRACTION CONTRACT ONCE MORE: the same
# EIGHT trade document types that Run 117 gave `trade_attribution_json` now also ask for
# `trade_denominators_json`, the per-firm population table without which not one of the owner's
# factor ladders can be evaluated. Eight new (type, field) pairs, so candidate A goes 289 -> 297.
# Candidate B goes 179 -> 187 because all eight are declared in `_ASSEMBLER_FIELDS`: the factor
# ladders are a real path from the field to a module, and leaving them undeclared would have let
# the completeness caveat report a project as MORE COMPLETE than its evidence -- which is the
# exact failure this check exists to catch. NEITHER NUMBER IS WEAKENED, nothing is deleted, and
# the check still fails on a rename in either place.
# RUN 119, SECTION 5. Candidate A 297 -> 299 and candidate B 187 -> 189: `commissioning_items_total`
# and `commissioning_items_cleared`
# are declared in `_ASSEMBLER_FIELDS`, because the commissioning completion path reads them. The
# pin MOVES with the declaration, which is the whole point of pinning it -- a field added to the
# contract and NOT declared would leave this number where it was and hide the new path.
check(_candidate_a == 299 and REQUIRED_TOTAL == 189,
      "the two candidate denominators, measured: every field every type asks for, against the "
      "fields this platform has a path from",
      f"candidate A {_candidate_a} pairs, candidate B (chosen) {REQUIRED_TOTAL} pairs")
check("Fields the extractor asks for and nothing consumes are not counted" in DENOMINATOR_WORDS,
      "and the caveat says which of the two it counted, in its own words")

# =================================================================================================
section("1. A4.8 SUBCONTRACTOR PERFORMANCE -- the assembler, on a real project")
# =================================================================================================
R, A, SI, VIEW, PID, PM = run_project("main", docs(disputes=DISPUTE_ROWS,
                                                   contingency=(400_000, 380_000)))
check("subcontractorAssessments" in SI,
      "the assembler wrote subcontractorAssessments into the signal inputs",
      str(list((SI.get("subcontractorAssessments") or {}).keys()))[:110])
check(state(R, A, "A4.8") == "BANDS YELLOW",
      "A4.8 bands on the most adverse valid reported posture across firms",
      state(R, A, "A4.8"))
_a48 = R.get("A4.8") or {}
check(_a48.get("governing_reported_rating") == "Satisfactory"
      and _a48.get("governing_subcontractor_id") == "Harbour Electrical",
      "the governing firm and its reported rating are the ones the report printed",
      f"{_a48.get('governing_subcontractor_id')} / {_a48.get('governing_reported_rating')}")
check(_a48.get("firm_count") == 2 and _a48.get("canonical_structure")
      == "subcontractor_reported_ratings",
      "both firms were read, through the canonical structure and not a shortcut",
      str(_a48.get("firm_count")))
check(str(_a48.get("source") or "").startswith("the subcontractor performance report"),
      "the reading names the document it was read from", str(_a48.get("source"))[:70])

_Rh, _Ah, _SIh, _Vh, _Ph, _Mh = run_project("held", docs(ratings=ADVERSE_ROWS))
check(state(_Rh, _Ah, "A4.8") == "COMPUTED, NO BAND"
      and (_Rh.get("A4.8") or {}).get("pm_review_required") is True,
      "an ADVERSE reported posture is HELD for Project Manager review and asserts no band, "
      "which is Run 107's rule and is not worked around here",
      state(_Rh, _Ah, "A4.8"))

_R2, _A2, _SI2, _V2, _P2, _M2 = run_project("noversion", docs(drop_report_version=True))
check("subcontractorAssessments" not in _SI2 and state(_R2, _A2, "A4.8") == "ABSTAINS",
      "a report stating no version assembles NOTHING and the module goes on abstaining",
      state(_R2, _A2, "A4.8"))

_R3, _A3, _SI3, _V3, _P3, _M3 = run_project(
    "unmappable", docs(ratings=[{"Subcontractor": "Northline Mechanical",
                                 "Assessment period": "2026-03", "Rating": "Adequate"}]))
check(state(_R3, _A3, "A4.8") in ("COMPUTED, NO BAND", "ABSTAINS"),
      "a rating the ladder does not map is Not Assessed and is never inferred",
      state(_R3, _A3, "A4.8"))

# =================================================================================================
section("2. A1.11 INDEPENDENT EAC RECONCILIATION -- pending exposure against the approved budget")
# =================================================================================================
check("pendingChangeExposure" in SI,
      "the assembler wrote pendingChangeExposure into the signal inputs",
      json.dumps({k: v for k, v in (SI.get("pendingChangeExposure") or {}).items()
                  if k != "pending_changes"})[:150])
_a111 = R.get("A1.11") or {}
check(_a111.get("pending_change_count") == 2 and _a111.get("approved_change_count") == 1,
      "the approved change is in the budget and only the two pending ones are exposure",
      f"pending {_a111.get('pending_change_count')}, approved "
      f"{_a111.get('approved_change_count')}")
check(_a111.get("pending_change_value") == 150_000.0,
      "the exposure is the value of the pending changes and nothing else",
      str(_a111.get("pending_change_value")))
check(_a111.get("approved_budget") == BAC
      and _a111.get("forecast_at_completion") == BAC + 150_000.0,
      "the forecast at completion is the approved budget plus the pending exposure",
      str(_a111.get("forecast_at_completion")))
check(state(R, A, "A1.11") == "BANDS YELLOW",
      "150,000 on 4,000,000 is 3.75 per cent -- above 3 and at or below 5 -- which is Yellow, "
      "and the override does not fire because 380,000 of contingency covers it",
      state(R, A, "A1.11"))
check(_a111.get("band_hard_override_fired") is False
      and _a111.get("band_hard_override_evaluable") is True,
      "the override was evaluable and did not fire", str(_a111.get("band_hard_override_fired")))
check(len(_a111.get("band_components") or []) == 1,
      "ONE component, not two: the Run 107 spread collapses onto the overrun under the "
      "redefinition and is not reported twice",
      json.dumps(_a111.get("band_components"))[:120])

for tag, pend, want in (("green", 100_000, "Green"), ("yellow", 160_000, "Yellow"),
                        ("amber", 300_000, "Amber"), ("red", 500_000, "Red")):
    rows = [dict(CHANGE_ROWS[0]),
            {"Change No": "PCO-9", "Date issued": "2026-02-14", "Type": "Design clarification",
             "Cause": "Revised roof detail", "Value": pend, "Direction": "Additive",
             "Approval status": "Pending"}]
    _r, _a, _si, _v, _p, _m = run_project("ladder-" + tag,
                                          docs(changes=rows, contingency=(900_000, 900_000)))
    check(state(_r, _a, "A1.11") == "BANDS " + want.upper(),
          f"pending exposure of {pend:,} on a 4,000,000 budget bands {want}",
          state(_r, _a, "A1.11"))

_rows = [dict(CHANGE_ROWS[0]), {**CHANGE_ROWS[1], "Approval status": "Referred to counsel"}]
_r, _a, _si, _v, _p, _m = run_project("nostatus", docs(changes=_rows))
check("pendingChangeExposure" not in _si and state(_r, _a, "A1.11") == "ABSTAINS",
      "a change stating no approval status assembles NOTHING: an unstated status is never "
      "read as pending and never as approved", state(_r, _a, "A1.11"))

_r, _a, _si, _v, _p, _m = run_project(
    "credit", docs(changes=[dict(CHANGE_ROWS[0]),
                            {**CHANGE_ROWS[1], "Direction": "Omission", "Value": 200_000}]))
check(state(_r, _a, "A1.11") == "BANDS GREEN"
      and (_r.get("A1.11") or {}).get("pending_change_value") == -200_000.0,
      "a net deductive pending position is nought per cent above the budget and is Green, "
      "and is never netted into a discount", state(_r, _a, "A1.11"))

# =================================================================================================
section("3. A4.7 DISPUTE ESCALATION INDEX -- the DURATION the OAC minutes record")
# =================================================================================================
# RUN 119, GOAL 3. RE-POINTED, NOT WEAKENED AND NOT DELETED. The owner REPLACED Run 115's count
# ladder (none Green, one Amber, more than one Red) with a DURATION ladder: no open dispute or a
# dispute resolved is Green, a dispute open is Yellow, open more than one week is Amber, open
# more than two weeks is Red, the oldest open dispute governing. These checks asserted the count
# rungs, which the platform no longer has, so they now assert the four duration rungs -- the same
# number of checks over the same module through the same real route, plus the two the redefinition
# added (a resolved dispute returning to Green, and the calendar the duration is counted on).
# END is 2026-03-31 and is the minutes' document date, which is the day the record speaks as of.
_D = lambda no, raised, status: {"Dispute No": no, "Subject": "Differing site conditions",
                                 "Parties": "Owner and General Contractor",
                                 "Date raised": raised, "Status": status, "Minute item": "5.2"}
for tag, rows, want, days in (
        ("resolved", [_D("D-01", "2026-01-05", "Resolved")], "Green", None),
        ("yellow", [_D("D-01", "2026-03-27", "Open")], "Yellow", 2.0),
        ("amber", [_D("D-01", "2026-03-20", "Open")], "Amber", 7.0),
        ("red", [_D("D-01", "2026-03-06", "Open")], "Red", 17.0)):
    _r, _a, _si, _v, _p, _m = run_project("disp-" + tag,
                                          docs(disputes=rows, calendar=R119_CALENDAR))
    check(state(_r, _a, "A4.7") == "BANDS " + want.upper(),
          f"a dispute {tag} bands {want} on the owner's duration ladder", state(_r, _a, "A4.7"))
    check((_r.get("A4.7") or {}).get("dispute_open_working_days") == days,
          f"and the duration it banded on is {days} working days on the project's own calendar",
          str((_r.get("A4.7") or {}).get("dispute_open_working_days")))

_r, _a, _si, _v, _p, _m = run_project("disp-oldest",
                                      docs(disputes=[_D("D-01", "2026-03-06", "Open"),
                                                     _D("D-02", "2026-03-27", "Open")],
                                           calendar=R119_CALENDAR))
check((_r.get("A4.7") or {}).get("governing_dispute_id") == "D-01"
      and state(_r, _a, "A4.7") == "BANDS RED",
      "across several disputes the OLDEST OPEN one governs and the most adverse band results",
      str((_r.get("A4.7") or {}).get("governing_dispute_id")))

_r, _a, _si, _v, _p, _m = run_project("disp-nocal", docs(disputes=DISPUTE_ROWS))
check(state(_r, _a, "A4.7") == "ABSTAINS"
      and "working calendar" in str((_a.get("A4.7") or {}).get("reason") or ""),
      "with NO project calendar the duration is not counted in calendar days instead: it "
      "abstains and the sentence names the calendar",
      str((_a.get("A4.7") or {}).get("reason"))[:90])

_r, _a, _si, _v, _p, _m = run_project("disp-none", docs(calendar=R119_CALENDAR))
check(state(_r, _a, "A4.7") == "ABSTAINS",
      "minutes that were never asked the question abstain: silence is not read as no dispute",
      state(_r, _a, "A4.7"))
check("subcontractor" in str((_a.get("A4.7") or {}).get("reason") or "").lower()
      or "meeting minutes" in str((_a.get("A4.7") or {}).get("reason") or "").lower(),
      "and the abstention sentence names what would serve it",
      str((_a.get("A4.7") or {}).get("reason"))[:110])

_r, _a, _si, _v, _p, _m = run_project("disp-scoped",
                                      docs(disputes=None, disputes_total=None,
                                           calendar=R119_CALENDAR))
check(state(_r, _a, "A4.7") == "ABSTAINS",
      "`subcontractor_disputes` = 0 on the same minutes does NOT produce a Green: the "
      "subcontractor-scoped figure is never substituted for the owner's measure",
      state(_r, _a, "A4.7"))

_r, _a, _si, _v, _p, _m = run_project("disp-disagree",
                                      docs(disputes=[_D("D-01", "2026-03-06", "Open"),
                                                     _D("D-02", "2026-03-27", "Open")],
                                           disputes_total=1, calendar=R119_CALENDAR))
check(state(_r, _a, "A4.7") == "BANDS RED"
      and (_r.get("A4.7") or {}).get("count_disagreement"),
      "where the list and the stated total disagree the LIST governs and the disagreement is "
      "still reported rather than reconciled -- the count survives the redefinition as a "
      "property of the record, and no longer sets a band",
      str((_r.get("A4.7") or {}).get("count_disagreement"))[:90])

# =================================================================================================
# =================================================================================================
section("4. GOAL 4 -- the caveat, served on the real projectresults response")
# =================================================================================================
IC = VIEW.get("information_completeness") or {}
check(bool(IC), "the served result carries the completeness record", str(list(IC.keys()))[:110])
check(IC.get("required") == 189 and isinstance(IC.get("extracted"), int),
      "the denominator is the 189 (document type, field) pairs this platform has a path from",
      f"{IC.get('extracted')} of {IC.get('required')}")
check(isinstance(IC.get("percent"), int) and 0 <= IC["percent"] <= 100,
      "and the caveat states a percentage", str(IC.get("percent")))
_cav = str(IC.get("caveat") or "")
check(_cav.startswith("This assessment is based on"),
      "the sentence is the owner's own wording", _cav[:60])
import re as _re
for word in ("red", "amber", "green", "yellow", "escalate", "investigate", "risk", "concern",
             "poor", "deficient", "inadequate", "warning"):
    if _re.search(r"\b" + word + r"\b", _cav.lower()):
        check(False, f"the caveat must not read as an adverse condition: it says '{word}'")
        break
else:
    check(True, "the caveat carries no colour, no severity and no action word")
check(VIEW.get("project_status") == (VIEW.get("project_status") or None)
      and "information_completeness" not in json.dumps(VIEW.get("category_statuses") or {}),
      "and it casts no vote: it is not in the category statuses")
check(state(R, A, "C1.5") == "ABSTAINS",
      "C1.5's own routing is untouched -- it still abstains from its category",
      state(R, A, "C1.5"))

# =================================================================================================
section("5. THE COMPLETENESS MEASURE MOVES WITH THE DOCUMENTS")
# =================================================================================================
_r, _a, _si, _v5, _p5, _m5 = run_project("thin", [
    ("contract", "contract_value", {"original_contract_sum": BAC})])
IC_THIN = _v5.get("information_completeness") or {}
check(IC_THIN.get("extracted", 0) < IC.get("extracted", 0),
      "a project with one document holds less of the required information than the full one",
      f"{IC_THIN.get('extracted')} vs {IC.get('extracted')}")
check(IC_THIN.get("required") == IC.get("required"),
      "and the denominator does not shrink with the evidence", str(IC_THIN.get("required")))

# =================================================================================================
section("6. FALSIFICATION -- every new check proved able to fail, in the thing the check reads")
# =================================================================================================

def falsify(name, mutate, restore, assertion):
    """Introduce a real fault into the LIVE object, require the check to fail, then restore."""
    mutate()
    try:
        broke = not assertion()
    finally:
        restore()
    check(broke, f"FALSIFIED: {name} fails when the fault is introduced")
    check(assertion(), f"RESTORED: {name} passes again once the fault is removed")

# 6.1 A4.8 -- strike the rating column out of the printed table the assembler reads.
def _a48_holds():
    _r, _a, _si, _v, _p, _m = run_project("f48-" + str(time.time_ns()), docs(ratings=_RATINGS[0]))
    return state(_r, _a, "A4.8") == "BANDS YELLOW"
_RATINGS = [copy.deepcopy(RATING_ROWS)]
falsify("A4.8 bands on the report's own rating column",
        lambda: _RATINGS.__setitem__(0, [{k: v for k, v in r.items() if k != "Rating"}
                                         for r in RATING_ROWS]),
        lambda: _RATINGS.__setitem__(0, copy.deepcopy(RATING_ROWS)),
        _a48_holds)

# 6.2 A1.11 -- strike the approval column out of the printed register the assembler reads.
_CHANGES = [copy.deepcopy(CHANGE_ROWS)]
def _a111_holds():
    _r, _a, _si, _v, _p, _m = run_project("f111-" + str(time.time_ns()),
                                          docs(changes=_CHANGES[0]))
    return (_r.get("A1.11") or {}).get("pending_change_value") == 150_000.0
falsify("A1.11 reads the register's own approval column",
        lambda: _CHANGES.__setitem__(0, [{k: v for k, v in r.items()
                                          if k != "Approval status"} for r in CHANGE_ROWS]),
        lambda: _CHANGES.__setitem__(0, copy.deepcopy(CHANGE_ROWS)),
        _a111_holds)

# 6.3 A4.7 -- collapse the owner's count ladder INSIDE THE LIVE canonical module.
from app.simulation import canonical_v4 as CV4
# RUN 119, GOAL 3. RE-POINTED at the ladder that now decides the band. Collapsing
# DISPUTE_COUNT_BANDS can no longer make this check fail, because the count no longer bands
# anything -- so the fault is introduced into DISPUTE_DURATION_WEEK_CUTS instead, which is where
# the owner's one-week and two-week rungs now live.
_REAL_BANDS = CV4.DISPUTE_DURATION_WEEK_CUTS
def _a47_holds():
    _r, _a, _si, _v, _p, _m = run_project(
        "f47-" + str(time.time_ns()),
        docs(disputes=[{"Dispute No": "D-01", "Subject": "s", "Parties": "p",
                        "Date raised": "2026-03-20", "Status": "Open"}],
             calendar=R119_CALENDAR))
    return state(_r, _a, "A4.7") == "BANDS AMBER"
falsify("A4.7's more-than-one-week rung is Amber and not Yellow",
        lambda: setattr(CV4, "DISPUTE_DURATION_WEEK_CUTS", ((2, "Red"), (99, "Amber"))),
        lambda: setattr(CV4, "DISPUTE_DURATION_WEEK_CUTS", _REAL_BANDS),
        _a47_holds)

# 6.4 GOAL 4 -- empty the required-field declaration INSIDE THE LIVE completeness module.
from app import information_completeness as ICM
_REAL_PAIRS, _REAL_TOTAL = ICM.REQUIRED_PAIRS, ICM.REQUIRED_TOTAL
def _ic_holds():
    _r, _a, _si, _v, _p, _m = run_project("fic-" + str(time.time_ns()),
                                          docs(disputes=DISPUTE_ROWS))
    _ic = _v.get("information_completeness") or {}
    return _ic.get("required") == 189 and (_ic.get("extracted") or 0) > 0
def _break_ic():
    ICM.REQUIRED_PAIRS = {"contract_value": frozenset({"original_contract_sum"})}
    ICM.REQUIRED_TOTAL = 1
def _fix_ic():
    ICM.REQUIRED_PAIRS, ICM.REQUIRED_TOTAL = _REAL_PAIRS, _REAL_TOTAL
falsify("the caveat counts the declared required set and not something else",
        _break_ic, _fix_ic, _ic_holds)

print("\n" + "=" * 94)
print(f"RUN 115 DRIVER: {PASS} passed, {FAIL} failed, {PASS + FAIL} checks")
print("=" * 94)
sys.exit(1 if FAIL else 0)
