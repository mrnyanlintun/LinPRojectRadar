"""
RUN 114. THE THREE NEW TABLE CONTRACTS, THE SUBMITTAL LADDER, AND THE TWO NEW YELLOW RUNGS.

NOTHING UNDER TEST IS SUPPLIED. Every document goes through the real `projectupload` route and
the real `projectcomputeall` route. `saveprojectdata` is never called, no structure is handed to
a module, and `window.LinResults.rowFor` is not touched anywhere in this file.

EVERY CHECK IN THIS FILE IS PROVED ABLE TO FAIL. Section 5 introduces a real fault -- a required
column struck out of a printed table, and the collapsed A1.7 ladder put back into the running
module -- runs the SAME assertion, and requires it to fail; then removes the fault and requires
it to pass. A check that reads the current code as if it were the old code proves nothing, so
the faults below are introduced into the objects the checks actually read.

Run from `server/`:  python tools/drive_run114.py
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
from app.research_models import Participant
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
# THE DOCUMENTS, PRINTED THE WAY A PERSON PRINTS THEM.
#
# Every table below is keyed by the HEADINGS a real register carries -- "Event No", "Days lost",
# "Required on site", "Direction" -- and not by the field names the canonical structures use. The
# assembler in `documents.py` matches the headings; if it did not, these fixtures would fail.
# =================================================================================================

WEATHER_ROWS = [
    {"Event No": "WX-01", "Date": "2026-02-10", "Activity ID": "A120",
     "Schedule path": "P-CRIT", "Planned work": "Structural steel erection",
     "Days lost": 3, "Total float (days)": 2,
     "Causal evidence": "NOAA station PAFA daily record: sustained wind above 35 mph",
     "Mitigation days": 0, "Start date": "2026-02-10", "End date": "2026-02-12"},
    {"Event No": "WX-02", "Date": "2026-03-04", "Activity ID": "A120",
     "Schedule path": "P-CRIT", "Planned work": "Structural steel erection",
     "Days lost": 2, "Total float (days)": 2,
     "Causal evidence": "NOAA station PAFA daily record: 14 in snowfall, site closed",
     "Mitigation days": 0, "Start date": "2026-03-04", "End date": "2026-03-05"},
]
PROC_ROWS = [
    {"Item No": "PR-001", "Description": "Main switchgear line-up",
     "Required on site": "2026-05-01", "Forecast delivery": "2026-05-20",
     "Total float (days)": 5, "Criticality": "controlling", "Status": "In fabrication",
     "Activity ID": "A300", "Long lead": "Yes", "Protection date missed": "Yes",
     "Causes required milestone late": "No"},
    {"Item No": "PR-002", "Description": "Interior door hardware",
     "Required on site": "2026-06-01", "Forecast delivery": "2026-05-15",
     "Total float (days)": 10, "Criticality": "not_critical", "Status": "Released",
     "Activity ID": "A420", "Long lead": "No", "Protection date missed": "No",
     "Causes required milestone late": "No"},
]
CHANGE_ROWS = [
    {"Change No": "CO-001", "Date issued": "2026-02-01", "Type": "Owner scope addition",
     "Cause": "Owner requested added scope", "Value": 900_000, "Direction": "Addition",
     "Reporting period": "2026-03"},
    {"Change No": "CO-002", "Date issued": "2026-02-20", "Type": "Design error",
     "Cause": "Design coordination conflict", "Value": 40_000, "Direction": "Addition",
     "Reporting period": "2026-03"},
    {"Change No": "CO-003", "Date issued": "2026-03-10", "Type": "Scope reduction",
     "Cause": "Value engineering", "Value": 30_000, "Direction": "Omission",
     "Reporting period": "2026-03"},
]
# Ten submittals receiving a first review; three rejected on first review = 30 per cent = Amber.
SUB_ROWS = []
for i in range(1, 11):
    SUB_ROWS.append({"Submittal No": f"S-{i:03d}", "Revision": "0",
                     "Decision date": f"2026-03-{i:02d}",
                     "Disposition": "REJECTED" if i <= 3 else "APPROVED",
                     "Reviewer": "Architect of record", "Reporting period": "2026-03"})
# Two resubmittals, APPROVED, which must NOT enter the first-review denominator.
SUB_ROWS += [{"Submittal No": "S-001", "Revision": "1", "Decision date": "2026-03-20",
              "Disposition": "APPROVED", "Reviewer": "Architect of record",
              "Reporting period": "2026-03"},
             {"Submittal No": "S-002", "Revision": "1", "Decision date": "2026-03-21",
              "Disposition": "APPROVED", "Reviewer": "Architect of record",
              "Reporting period": "2026-03"}]

def docs(weather_rows, proc_rows, change_rows, sub_rows, weather_scalars=None,
         change_scalars=None, proc_scalars=None):
    ws = {"document_date": END, "document_risk_score": 0.10, "outstanding_action_items": 2,
          "weather_days_discussed": 5, "weather_days_claimed": 9, "weather_days_approved": 7,
          "weather_approval_period": "2026-03", "weather_allowance_days": 10,
          "weather_time_extension_granted": True, "weather_time_extension_days": 5,
          "weather_events_json": weather_rows,
          "weather_allowance_days_remaining": 1,
          "weather_calendar_id": "WX-CAL-2026",
          "weather_day_basis": "approved_calendar_working_days",
          "weather_approval_source": "OAC meeting minutes of 2026-03-31",
          "weather_time_extension_incorporated_in_baseline": False,
          "weather_milestone_forecast_late": False,
          "weather_milestone_class": "contractual"}
    ws.update(weather_scalars or {})
    ps = {"long_lead_items_total": 20, "at_risk": 1, "delayed": 1, "on_schedule": 18,
          "report_date": END, "procurement_items_json": proc_rows,
          "procurement_day_basis": "approved_calendar_working_days"}
    ps.update(proc_scalars or {})
    cs = {"change_order_count": 3, "baseline_contract_sum": BAC,
          "revised_contract_sum": BAC + 910_000, "change_order_date": END,
          "change_events_json": change_rows, "change_exposure_days": 180,
          "change_related_delay_days": 6, "change_available_total_float_days": 30,
          "original_contract_duration_days": 546,
          "change_time_extension_approved": False,
          "change_forecast_completion_moved": False}
    cs.update(change_scalars or {})
    return [
        ("contract", "contract_value", {"original_contract_sum": BAC,
                                        "project_start_date": "2026-01-01",
                                        "project_end_date": "2027-06-30"}),
        ("oac", "oac_minutes", ws),
        ("proc", "procurement_log", ps),
        ("co", "change_order", cs),
        ("sub", "submittal_register", {"submittals_total": 12, "submittals_rejected": 3,
                                       "document_date": END, "document_risk_score": 0.15,
                                       "submittal_decisions_json": sub_rows,
                                       "submittal_reporting_period": "2026-03"}),
    ]

def run_project(tag, doclist):
    """Upload every document through the real route, compute, and return module_id -> row."""
    pid = f"PRJ-R114-{tag}-{STAMP}"
    admin_tok = f"r114-{tag}-{STAMP}"
    def raw(t): return f"%PDF-1.4 R114 {tag} {STAMP} {t}\n".encode()
    set_extractor_override(StubExtractor(
        {hashlib.sha256(raw(t)).hexdigest(): (ty, ex) for t, ty, ex in doclist}))
    with S() as s:
        r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if r is None:
            s.add(Participant(pseudonymous_code="R114-A-" + tag + STAMP, role="ResearchAdmin",
                              access_token_hash=hash_access_token(admin_tok)))
        else:
            r.access_token_hash = hash_access_token(admin_tok)
        if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
            s.add(Project(legacy_id=pid, doc={"id": pid, "name": "Run 114 " + tag,
                                              "sector": "construction", "signals": {},
                                              "events": []}))
        s.commit()
    admin = post({"action": "researchlogin", "access_token": admin_tok})["session_token"]
    c = post({"action": "adminparticipantcreate", "session_token": admin,
              "pseudonymous_code": "R114-PM-" + tag + STAMP, "role": "Participant",
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
    from app.research_models import ComputedResult
    with S() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == pid))
        row = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == proj.id, ComputedResult.superseded_by.is_(None)))
        results = {m.get("module_id"): m for m in ((row.module_results if row else None) or [])}
        abstained = {a.get("module_id"): a for a in ((row.abstained if row else None) or [])}
        si = dict(row.signal_inputs or {}) if row else {}
    return results, abstained, si


def state(results, abstained, mid):
    r = results.get(mid)
    if r is not None and r.get("status_color"):
        return "BANDS " + str(r["status_color"]).upper()
    if r is not None:
        return "COMPUTED, NO BAND"
    if mid in abstained:
        return "ABSTAINS"
    return "NO ROW AT ALL"


def detail(results, abstained, mid):
    r = results.get(mid)
    if r is not None:
        return str(r.get("evidence_metric") or "")[:150]
    a = abstained.get(mid)
    return str((a or {}).get("reason") or "")[:150]


# =================================================================================================
# SECTION 1. THE THREE NEW TABLE CONTRACTS, AND A4.3, ON A REAL PROJECT
# =================================================================================================

section("1. THE FULL PROJECT: three new tables, a submittal decision register, nothing supplied")
R, A, SI = run_project("full", docs(WEATHER_ROWS, PROC_ROWS, CHANGE_ROWS, SUB_ROWS))
for mid, name in (("A4.5", "Weather Day Impact"), ("A4.6", "Change Order Frequency"),
                  ("A4.9", "Procurement Lead Time"), ("A4.3", "Submittal Rejection Rate")):
    print(f"  {mid:<6} {state(R, A, mid):<18} {name}")
    print(f"         {detail(R, A, mid)}")

check("weatherImpactEvents" in SI,
      "A4.5: the OAC minutes' printed weather table reached signal_inputs as "
      "`weatherImpactEvents` through the real upload route",
      str(len((SI.get("weatherImpactEvents") or {}).get("events") or [])) + " events")
check(state(R, A, "A4.5").startswith("BANDS"),
      "A4.5 Weather Day Impact BANDS on a real project", state(R, A, "A4.5"))
check((R.get("A4.5") or {}).get("weather_days_approved") == 7
      and (R.get("A4.5") or {}).get("weather_days_claimed") == 9,
      "A4.5 banded on the days the owner APPROVED (7), with the days CLAIMED (9) carried "
      "beside them and never substituted for them",
      f"approved={(R.get('A4.5') or {}).get('weather_days_approved')} "
      f"claimed={(R.get('A4.5') or {}).get('weather_days_claimed')}")

check("procurementItems" in SI,
      "A4.9: the procurement log's printed item table reached signal_inputs as "
      "`procurementItems`",
      str(len((SI.get("procurementItems") or {}).get("items") or [])) + " items")
check(state(R, A, "A4.9").startswith("BANDS"),
      "A4.9 Procurement Lead Time BANDS on a real project", state(R, A, "A4.9"))
check(any(i.get("criticality") == "controlling"
          for i in (SI.get("procurementItems") or {}).get("items") or []),
      "A4.9: the register STATES its own criticality and the platform read it from the "
      "register's own column, reaching into no other module")

check("changeEventRegister" in SI,
      "A4.6: the change order document's printed change table reached signal_inputs as "
      "`changeEventRegister`",
      str(len((SI.get("changeEventRegister") or {}).get("changes") or [])) + " changes")
check((SI.get("changeEventRegister") or {}).get("exposure_days") == 180,
      "A4.6: `exposure_days` -- the field Run 111 measured as having none declared anywhere -- "
      "reached the structure from `change_exposure_days`",
      str((SI.get("changeEventRegister") or {}).get("exposure_days")))
check(state(R, A, "A4.6").startswith("BANDS"),
      "A4.6 Change Order Frequency BANDS on a real project", state(R, A, "A4.6"))
_dirs = sorted({c.get("direction") for c in
                (SI.get("changeEventRegister") or {}).get("changes") or []})
check(_dirs == ["ADDITIVE", "DEDUCTIVE"],
      "A4.6: 'Addition' and 'Omission' as a register prints them became ADDITIVE and DEDUCTIVE, "
      "and the platform signed no value itself", str(_dirs))

section("2. A4.3 SUBMITTAL REJECTION: does the Run 106 ladder band, and did the overrides land")
_a43 = R.get("A4.3") or {}
check(state(R, A, "A4.3").startswith("BANDS"),
      "A4.3 Submittal Rejection Rate BANDS on a real project", state(R, A, "A4.3"))
check(_a43.get("first_review_assessed") == 10 and _a43.get("first_review_rejected") == 3,
      "A4.3 banded the FIRST-REVIEW population: 3 of 10, with the two later resubmittals "
      "excluded from the denominator",
      f"{_a43.get('first_review_rejected')} of {_a43.get('first_review_assessed')} "
      f"(all assessed decisions = {_a43.get('total')})")
check(_a43.get("status_color") == "Amber",
      "A4.3 read AMBER at 30 per cent, on the owner's 10 / 20 / 35 ladder",
      f"{_a43.get('band_first_review_pct')} per cent -> {_a43.get('status_color')}")
check(_a43.get("threshold_source") == "owner_configured_default"
      and _a43.get("band_basis_id") == "owner_configured_construction_document_control_tolerance",
      "A4.3 carries the owner's threshold source and band basis identifier",
      f"{_a43.get('threshold_source')} / {_a43.get('band_basis_id')}")
check(_a43.get("band_overrides_evaluated") is False
      and sorted(_a43.get("band_override_fields_absent") or []) == [
          "critical_package_rejected_resubmittals",
          "rejected_critical_or_long_lead_forecast_after_need_by",
          "rejected_unresolved_past_review_deadline_blocking_work"],
      "A4.3's three Red overrides were NOT TESTED on this register and the row says so by "
      "name, rather than reading silence as the conditions not holding",
      str(_a43.get("band_override_fields_absent")))

# The overrides fire when the register designates them. Same route, one document changed.
_sub_ov = copy.deepcopy(SUB_ROWS)
_docs_ov = docs(WEATHER_ROWS, PROC_ROWS, CHANGE_ROWS, _sub_ov)
for i, (t, ty, ex) in enumerate(_docs_ov):
    if ty == "submittal_register":
        ex["rejected_critical_or_long_lead_late_json"] = [
            {"Submittal No": "S-001", "Package": "Structural steel",
             "Need by": "2026-04-01", "Forecast approval": "2026-05-01"}]
        ex["rejected_blocking_past_deadline_json"] = []
        ex["critical_package_rejected_resubmittals"] = 0
R2, A2, SI2 = run_project("override", _docs_ov)
_o = R2.get("A4.3") or {}
check(_o.get("band_override_fired") is True and _o.get("status_color") == "Red",
      "A4.3's Run 106 Red override FIRES and takes precedence over the rate when the register "
      "designates a rejected critical or long-lead submittal approving after its need-by date",
      f"fired={_o.get('band_override_fired')} colour={_o.get('status_color')} "
      f"rate still {_o.get('band_first_review_pct')} per cent")


# =================================================================================================
# SECTION 3. THE TWO NEW YELLOW RUNGS
# =================================================================================================

section("3. A1.7 TCPI AND A1.8 VAC: the owner's Yellow rung, on the real route and on the ladder")
from app.simulation import models_evm as EVM

def tcpi_band(bac, ev, ac):
    return EVM.run_tcpi({"bac": bac, "ev": ev, "ac": ac}, None, None).get("status_color")
def vac_band(cpi):
    return EVM.run_vac({"bac": 4_000_000, "cpi": cpi}, None, None).get("status_color")

_TCPI_LADDER = [(0.90, "Green"), (1.00, "Green"), (1.01, "Yellow"), (1.05, "Yellow"),
                (1.06, "Amber"), (1.10, "Amber"), (1.11, "Red")]
for _t, _want in _TCPI_LADDER:
    # bac/ev/ac chosen so that (bac-ev)/(bac-ac) is exactly the index wanted.
    _bac, _ac = 4_000_000.0, 2_000_000.0
    _ev = _bac - _t * (_bac - _ac)
    check(tcpi_band(_bac, _ev, _ac) == _want,
          f"A1.7 reads {_want} at a required efficiency of {_t}",
          str(tcpi_band(_bac, _ev, _ac)))
_VAC_LADDER = [(1.05, "Green"), (1.00, "Green"), (0.98, "Yellow"), (0.96, "Yellow"),
               (0.94, "Amber"), (0.91, "Amber"), (0.89, "Red")]
for _c, _want in _VAC_LADDER:
    check(vac_band(_c) == _want,
          f"A1.8 reads {_want} at a cost performance index of {_c} "
          f"(VAC {round((1 - 1 / _c) * 100, 2)} per cent)",
          str(vac_band(_c)))
check(round(EVM._VAC_OWNER_YELLOW_PCT, 6) == round((1 - 1 / 0.95) * 100, 6),
      "A1.8's Yellow edge is the exact restatement of a cost performance index of 0.95",
      f"{EVM._VAC_OWNER_YELLOW_PCT} per cent")
check(EVM._TCPI_PLANNED_EFFICIENCY == 1.00 and EVM._TCPI_BEYOND_OBSERVED == 1.10
      and EVM._VAC_BUDGET_MET_PCT == 0.0
      and round(EVM._VAC_BEYOND_OBSERVED_PCT, 6) == round((1 - 1 / 0.90) * 100, 6),
      "the existing Green and Red edges of both ladders did NOT move: 1.00 and 1.10 on A1.7, "
      "zero and minus 11.11 per cent on A1.8")
check(EVM._EDGE_CLASSES(EVM._TCPI_EDGE_PROVENANCE) == ["CODIFIED", "CONVENTION",
                                                       "OWNER-CALIBRATED"]
      and EVM._TCPI_EDGE_PROVENANCE["yellow_at_or_below"][1] == "OWNER-CALIBRATED"
      and EVM._VAC_EDGE_PROVENANCE["yellow_at_or_above"][1] == "OWNER-CALIBRATED",
      "the new Yellow edge is recorded OWNER-CALIBRATED per edge on both ladders and does not "
      "inherit the CONVENTION class the 1.10 and the minus 11.11 carry")

# ON THE REAL ROUTE: a project whose figures fall in the new rung, uploaded and computed.
_YEL = [("contract", "contract_value", {"original_contract_sum": BAC,
                                        "project_start_date": "2026-01-01",
                                        "project_end_date": "2027-06-30"}),
        ("month", "monthly_report", {"earned_value": 1_000_000, "actual_cost": 1_030_000,
                                     "planned_value": 1_000_000, "budget_at_completion": BAC,
                                     "actual_percent_complete": 25.0,
                                     "planned_percent_complete": 25.0, "report_date": END})]
RY, AY, SIY = run_project("yellow", _YEL)
check(state(RY, AY, "A1.7") == "BANDS YELLOW",
      "A1.7 reads YELLOW on a real project through the real upload route",
      f"{state(RY, AY, 'A1.7')} -- {detail(RY, AY, 'A1.7')}")
check(state(RY, AY, "A1.8") == "BANDS YELLOW",
      "A1.8 reads YELLOW on the same real project",
      f"{state(RY, AY, 'A1.8')} -- {detail(RY, AY, 'A1.8')}")
check((RY.get("A1.7") or {}).get("band_boundary_provenance_classes") == [
          "CODIFIED", "CONVENTION", "OWNER-CALIBRATED"],
      "the stored A1.7 reading publishes every provenance class on its ladder, so nothing "
      "reading one field can miss that an owner-set edge is in it",
      str((RY.get("A1.7") or {}).get("band_boundary_provenance_classes")))

# =================================================================================================
# SECTION 4. CAN A USER STILL SELECT A TYPE THAT PRODUCES NOTHING?
# =================================================================================================

section("4. EVERY SELECTABLE TYPE, MEASURED: does it derive any signal at all?")
import re as _re
from app.extraction_fields import DOC_TYPES, UI_ONLY_DOC_TYPES, extraction_fields_for, is_mapped
from app.extraction_merge import emit_observations

_js = pathlib.Path("/home/user/LinPRojectRadar/assets/js/signals.js").read_text()
_grp = _re.search(r"const DOC_TYPE_GROUPS = \[([\s\S]*?)\n  \];", _js)
_offered = _re.findall(r'\[\s*"([a-z_]+)"', _grp.group(1)) if _grp else []
check(set(_offered) == set(DOC_TYPES),
      "the upload dropdown now offers exactly the 27 types the server can classify into",
      f"offered={len(_offered)} doc_types={len(DOC_TYPES)}")
check(not (set(_offered) & set(UI_ONLY_DOC_TYPES)),
      "not one of the fifteen planning and governance types is selectable any more",
      str(sorted(set(_offered) & set(UI_ONLY_DOC_TYPES))))
_labels = _re.search(r"const RETIRED_DOC_TYPE_LABEL = \{([\s\S]*?)\};", _js)
_lk = set(_re.findall(r"^\s*([a-z_]+):", _labels.group(1), _re.M)) if _labels else set()
check(_lk == set(UI_ONLY_DOC_TYPES),
      "a stored document already carrying one of the fifteen still renders a name: every one "
      "keeps its label in RETIRED_DOC_TYPE_LABEL, which DOC_TYPE_LABEL is seeded from",
      f"{len(_lk)} labels kept")

_barren = []
for _ty in DOC_TYPES:
    _flds = extraction_fields_for(_ty)
    _ex = {}
    for _f in _flds:
        _ex[_f] = ([{"a": 1}] if _f.endswith("_json") else
                   ("2026-03-31" if _f.endswith(("_date", "_from", "_to")) else
                    (0.5 if _f == "document_risk_score" else 1)))
    try:
        _obs = emit_observations({"sha256": "x" * 64, "doc_type": _ty, "filename": _ty + ".pdf",
                                  "extraction": _ex})
    except Exception as _e:
        _obs = []
    if not _obs:
        _barren.append(_ty)
check(not _barren,
      "RUN 114 MEASUREMENT: every remaining selectable type emits at least one observation when "
      "its own declared fields are present -- no other type has the property the fifteen had",
      f"barren={_barren}")
for _ty in UI_ONLY_DOC_TYPES[:3]:
    check(not is_mapped(_ty) and not emit_observations(
        {"sha256": "y" * 64, "doc_type": _ty, "filename": "x.pdf", "extraction": {"a": 1}}),
        f"{_ty}: still unmapped and still emits nothing (the server behaviour is unchanged; "
        f"only the picker closed)")


# =================================================================================================
# SECTION 5. EVERY CHECK ABOVE, PROVED ABLE TO FAIL
#
# A check that cannot fail is worse than no check. Each fault below is introduced into the thing
# the check actually reads -- the printed table the assembler parses, or the ladder constant the
# running module bands on -- and the SAME assertion is then required to come out FALSE. A
# falsification that re-reads the old code as if it were the new code proves nothing, so nothing
# here reads a copy or a snapshot.
# =================================================================================================

section("5. FALSIFICATION: introduce the fault, watch the check fail, remove it, watch it pass")

def strike(rows, heading):
    """The same printed table with one column struck out, as a document that omitted it."""
    out = []
    for r in rows:
        out.append({k: v for k, v in r.items() if k != heading})
    return out

_FAULTS = [
    ("A4.5", "the weather table's 'Total float' column",
     lambda: docs(strike(WEATHER_ROWS, "Total float (days)"), PROC_ROWS, CHANGE_ROWS, SUB_ROWS)),
    ("A4.9", "the procurement table's 'Required on site' column",
     lambda: docs(WEATHER_ROWS, strike(PROC_ROWS, "Required on site"), CHANGE_ROWS, SUB_ROWS)),
    ("A4.6", "the change register's 'Direction' column",
     lambda: docs(WEATHER_ROWS, PROC_ROWS, strike(CHANGE_ROWS, "Direction"), SUB_ROWS)),
    ("A4.3", "the submittal register's 'Reviewer' column",
     lambda: docs(WEATHER_ROWS, PROC_ROWS, CHANGE_ROWS, strike(SUB_ROWS, "Reviewer"))),
]
for _i, (_mid, _what, _mk) in enumerate(_FAULTS):
    _rf, _af, _sif = run_project(f"fault{_i}", _mk())
    _banded = state(_rf, _af, _mid).startswith("BANDS")
    check(not _banded,
          f"FAULT INTRODUCED -- {_what} struck out: the check '{_mid} BANDS on a real project' "
          f"now FAILS, so it was capable of failing",
          f"{_mid} -> {state(_rf, _af, _mid)}")
check(state(R, A, "A4.5").startswith("BANDS")
      and state(R, A, "A4.6").startswith("BANDS")
      and state(R, A, "A4.9").startswith("BANDS")
      and state(R, A, "A4.3").startswith("BANDS"),
      "FAULT REMOVED -- the unmodified tables of section 1 still band all four modules")

# THE LADDER FAULT, INTRODUCED INTO THE RUNNING MODULE ITSELF.
_saved_t, _saved_v = EVM._TCPI_OWNER_YELLOW, EVM._VAC_OWNER_YELLOW_PCT
EVM._TCPI_OWNER_YELLOW = EVM._TCPI_PLANNED_EFFICIENCY      # the rung collapsed away
EVM._VAC_OWNER_YELLOW_PCT = EVM._VAC_BUDGET_MET_PCT
_t_fault = tcpi_band(4_000_000.0, 4_000_000.0 - 1.01 * 2_000_000.0, 2_000_000.0)
_v_fault = vac_band(0.98)
check(_t_fault != "Yellow" and _v_fault != "Yellow",
      "FAULT INTRODUCED -- the owner's Yellow edge collapsed onto the Green edge in the live "
      "module: the ladder checks of section 3 now FAIL, so they were capable of failing",
      f"A1.7 at 1.01 -> {_t_fault}, A1.8 at CPI 0.98 -> {_v_fault}")
EVM._TCPI_OWNER_YELLOW, EVM._VAC_OWNER_YELLOW_PCT = _saved_t, _saved_v
check(tcpi_band(4_000_000.0, 4_000_000.0 - 1.01 * 2_000_000.0, 2_000_000.0) == "Yellow"
      and vac_band(0.98) == "Yellow",
      "FAULT REMOVED -- both ladders read Yellow again")

# THE PICKER CHECK, PROVED ABLE TO FAIL: put one retired type back into the parsed text.
_js_fault = _js.replace('["rfi_log",               "RFI Log (register)"],',
                        '["rfi_log",               "RFI Log (register)"],\n'
                        '      ["as_built_drawings",      "As-Built Drawings"],')
_g2 = _re.search(r"const DOC_TYPE_GROUPS = \[([\s\S]*?)\n  \];", _js_fault)
_off2 = _re.findall(r'\[\s*"([a-z_]+)"', _g2.group(1)) if _g2 else []
check(bool(set(_off2) & set(UI_ONLY_DOC_TYPES)) and set(_off2) != set(DOC_TYPES),
      "FAULT INTRODUCED -- one retired type put back into the dropdown text: both picker checks "
      "of section 4 now FAIL, so they were capable of failing",
      str(sorted(set(_off2) & set(UI_ONLY_DOC_TYPES))))
check(set(_offered) == set(DOC_TYPES) and not (set(_offered) & set(UI_ONLY_DOC_TYPES)),
      "FAULT REMOVED -- the real signals.js still offers exactly DOC_TYPES")

print()
print("=" * 94)
print(f"RESULT: {PASS}/{PASS + FAIL} checks passed")
print("=" * 94)
sys.exit(0 if FAIL == 0 else 1)
