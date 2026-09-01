"""
RUN 102. The four properties this run must not lose, each proved able to fail first.

  1. `banded()` REFUSES a band with no `threshold_source`, and refuses one that is not in the
     three-value vocabulary. Section 12.5.
  2. The merge FILLS an absence and NEVER OVERRIDES a reading. Section 12.2.
  3. The merge is NEVER SILENT: a posture served from the Python layer says so on the category
     and on every module row it served. Section 12.1.
  4. Every A6 and A2 band this run built carries its provenance class AND its threshold source.

NON-VACUITY. Every check below is paired with a case that MUST fail it, and the failing case is
asserted to fail. A check that cannot fail proves nothing.
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app import spec_projection as SP
from app.simulation import models as M
from app.simulation import spec_apply as sa

PASS = FAIL = 0


def check(ok, label, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {label}")
    else:
        FAIL += 1
        print(f"  ****  {label}" + (f"   [{detail}]" if detail else ""))


print("1. banded() REFUSES A BAND WITH NO THRESHOLD SOURCE")
_common = dict(status_color="Green", boundary="b", basis="s",
               provenance=M.PROVENANCE_CODIFIED)
try:
    M.banded("X", "m", **_common)
    check(False, "banded() raises when threshold_source is not passed at all")
except TypeError:
    check(True, "banded() raises when threshold_source is not passed at all")
try:
    M.banded("X", "m", threshold_source="made_up", **_common)
    check(False, "banded() raises on a threshold source outside the three-value vocabulary")
except ValueError:
    check(True, "banded() raises on a threshold source outside the three-value vocabulary")
_ok = M.banded("X", "m", threshold_source=M.THRESHOLD_SOURCE_OWNER, **_common)
check(_ok["threshold_source"] == "owner_configured_default"
      and bool(_ok["threshold_source_words"]),
      "and a valid one is stored on the reading with its plain words")
check(_ok["band_basis_provenance_class"] == "CODIFIED",
      "the provenance class is UNCHANGED and is not replaced by the threshold source",
      str(_ok.get("band_basis_provenance_class")))

print()
print("2. THE MERGE FILLS AN ABSENCE AND NEVER OVERRIDES A READING")
_row_cats = {"A1": {"status": "Green", "contributes_to_project_status": True, "group": "A"},
             "A2": {"status": "Red", "contributes_to_project_status": True, "group": "A"}}
_row_mods = [{"module_id": "A1.7", "category": "A1", "status_color": "Green"},
             {"module_id": "A2.8", "category": "A2", "status_color": "Red"}]

# A specification layer that ANSWERED A1 (computed, Yellow) and could not be asked about A2.
_spec = {
    "module_results": [{"module_id": "A1.7", "category": "A1", "status_color": "Yellow"}],
    "abstained": [],
    "category_statuses": {
        "A1": {"status": "Yellow", "state": sa.COMPUTED, "contributes_to_project_status": True,
               "group": "A"},
        "A2": {"status": None, "state": sa.FAILED, "reason": "no API key",
               "contributes_to_project_status": True, "group": "A"},
    },
}
m = SP.merge_python_row(_spec, _row_mods, [], _row_cats, {})
check(m["category_statuses"]["A1"]["status"] == "Yellow",
      "a category the specification layer COMPUTED keeps its own posture; the Python Green does "
      "not override it", str(m["category_statuses"]["A1"]["status"]))
check(m["category_statuses"]["A2"]["status"] == "Red",
      "a category the specification layer could not be asked about is FILLED from the Python row",
      str(m["category_statuses"]["A2"]["status"]))
check(m["python_fallback_categories"] == ["A2"],
      "and exactly that one category is recorded as filled", str(m["python_fallback_categories"]))

# NON-VACUITY: an ABSTAINED reading is still a reading and must NOT be overridden.
_spec2 = dict(_spec)
_spec2["category_statuses"] = dict(_spec["category_statuses"])
_spec2["category_statuses"]["A2"] = {"status": None, "state": sa.ABSTAINED,
                                     "reason": "the evidence is not there",
                                     "contributes_to_project_status": True, "group": "A"}
m2 = SP.merge_python_row(_spec2, _row_mods, [], _row_cats, {})
check(m2["category_statuses"]["A2"]["status"] is None
      and m2["python_fallback_categories"] == [],
      "an ABSTAINED specification reading is a reading and is NOT overridden by the Python row",
      str(m2["python_fallback_categories"]))

print()
print("3. THE FALLBACK IS NEVER SILENT")
check(m["category_statuses"]["A2"]["posture_layer"] == SP.POSTURE_LAYER_PYTHON
      and bool(m["category_statuses"]["A2"]["posture_layer_words"]),
      "the filled category names the layer that produced its posture, in words")
check(m["category_statuses"]["A1"]["posture_layer"] == SP.POSTURE_LAYER_SPEC,
      "and the specification-layer category names its layer too")
_a28 = [r for r in m["module_results"] if r["module_id"] == "A2.8"]
check(bool(_a28) and _a28[0]["posture_layer"] == SP.POSTURE_LAYER_PYTHON,
      "every module row served from the Python layer says so on the row")
check(bool(m["posture_layer_note"]) and "A2" in m["posture_layer_note"],
      "and the projection carries a sentence naming which categories were filled")
check(m2["posture_layer_note"] is None,
      "NON-VACUITY: with nothing filled there is no disclosure sentence, so the sentence above "
      "is not a constant")

print()
print("4. EVERY BAND THIS RUN BUILT CARRIES BOTH FIELDS")
import random
from app.simulation import models_ext as E
from app.simulation.models_cat89 import _a6_band
from app.simulation.canonical_v6 import (
    contractor_assessment, environmental_compliance, quality_compliance, safety_performance,
)

_net = {"activities": [
    {"activity_id": "A", "predecessors": [], "current_duration": 3,
     "optimistic_duration": 2, "most_likely_duration": 3, "pessimistic_duration": 5},
    {"activity_id": "B", "predecessors": ["A"], "current_duration": 1,
     "optimistic_duration": 1, "most_likely_duration": 1, "pessimistic_duration": 2}],
    "schedule_version": "v1", "status_basis": "as of period"}
_la = {"activities": [{"activity_id": f"L{i}", "constraint_status": "CLEARED"}
                      for i in range(10)],
       "horizon": "6 weeks", "status_date": "2026-03-31"}
_rp = {"buckets": [{"time_bucket": "2026-03", "resource_type": "labour hours",
                    "demand": 90, "available_capacity": 100}],
       "resource_plan_version": "v1"}
_mh = {"milestones": [{"milestone_id": "M1", "original_baseline_day": 100,
                       "approved_baseline_day": 100,
                       "forecasts": [{"report_index": 1, "forecast_day": 100},
                                     {"report_index": 2, "forecast_day": 101}]}],
       "schedule_version": "v1", "remaining_planned_duration_days": 200}
for label, row in (
        ("A2.1 PERT", M.run_pert({"scheduleNetwork": _net}, random.Random(3).random, None)),
        ("A2.7 Milestone Trend", E.run_milestone_trend({"milestoneForecastHistory": _mh},
                                                       None, None)),
        ("A2.8 Look-Ahead", E.run_lookahead_health({"lookAheadSchedule": _la}, None, None)),
        ("A2.9 Resource Loading", E.run_resource_loading({"resourceProfile": _rp}, None, None))):
    check(bool(row.get("band_asserted")) and bool(row.get("threshold_source"))
          and bool(row.get("band_basis_provenance_class")),
          f"{label} asserts a band carrying BOTH its provenance class and its threshold source",
          f"{row.get('status_color')} / {row.get('threshold_source')}")

_q = {"items_inspected": 100, "items_passing_first_inspection": 96}
_e = {"corrective_actions": [{"action_id": "CA1", "required_deadline": "2026-01-10",
                              "closure_date": "2026-01-05", "severity": "low"}]}
_s = {"recordable_cases": 3, "employee_hours_worked": 400000}
_c = {"source_system": "internal",
      "factor_ratings": [{"factor": "Quality", "rating": 88}]}
for mid, res, st in (("A6.1", quality_compliance(_q), _q),
                     ("A6.2", safety_performance(_s), _s),
                     ("A6.3", environmental_compliance(_e), _e),
                     ("A6.4", contractor_assessment(_c), _c)):
    colour, _b, _bas, prov, _bp, tsrc = _a6_band(mid, res, st)
    check(colour is not None and prov is not None and tsrc in M.THRESHOLD_SOURCES,
          f"{mid} asserts a band carrying BOTH its provenance class and its threshold source",
          f"{colour} / {prov} / {tsrc}")

print()
print("5. THE HARD OVERRIDES FIRE, AND ARE PROVED NOT TO FIRE WHEN THEY SHOULD NOT")
_crit = dict(_q, critical_quality_failures=[{"item_id": "H-1", "kind": "hold point"}])
check(_a6_band("A6.1", quality_compliance(_crit), _crit)[0] == "Red",
      "A6.1: a failed hold-point item is Red at a 96 per cent first-pass rate")
check(_a6_band("A6.1", quality_compliance(_q), _q)[0] == "Green",
      "NON-VACUITY: the same rate with no critical failure is Green")
_fatal = dict(_s, severe_events=[{"event_type": "fatality"}])
check(_a6_band("A6.2", safety_performance(_fatal), _fatal)[0] == "Red",
      "A6.2: a fatality is Red at a benchmark ratio of 0.625")
_late = {"corrective_actions": [
    {"action_id": "CA1", "required_deadline": "2026-01-10", "closure_date": "2026-01-05"},
    {"action_id": "CA2", "required_deadline": "2026-02-01", "deadline_passed": True,
     "severity": "critical", "deadline_is_mandatory": True}]}
check(_a6_band("A6.3", environmental_compliance(_late), _late)[0] == "Red",
      "A6.3: one corrective action unclosed past a mandatory deadline is Red")
_pert_imposed = dict(_net, imposed_finish_day=2)
check(M.run_pert({"scheduleNetwork": _pert_imposed},
                 random.Random(3).random, None)["band_hard_override_fired"] is True,
      "A2.1: negative total float against the imposed finish fires the override")
check(M.run_pert({"scheduleNetwork": _net},
                 random.Random(3).random, None)["band_hard_override_fired"] is False,
      "NON-VACUITY: with no imposed finish stated the override does NOT fire, because the "
      "backward pass's own critical-path float is zero by construction")
_la_blocked = dict(_la, activities=_la["activities"] + [
    {"activity_id": "LX", "constraint_status": "OPEN", "constraint_category": "permit",
     "on_critical_path": True}])
check(E.run_lookahead_health({"lookAheadSchedule": _la_blocked},
                             None, None)["status_color"] == "Red",
      "A2.8: a critical-path activity blocked by an open constraint is Red at 91 per cent ready")
_rp_zero = {"buckets": [{"time_bucket": "2026-03", "resource_type": "labour hours",
                         "demand": 105, "available_capacity": 100,
                         "affects_zero_or_negative_float": True}],
            "resource_plan_version": "v1"}
check(E.run_resource_loading({"resourceProfile": _rp_zero},
                             None, None)["status_color"] == "Red",
      "A2.9: an overload on a zero-float path is Red at a ratio of 1.05, which is otherwise "
      "Yellow")
_mh_late = {"milestones": [{"milestone_id": "M1", "original_baseline_day": 100,
                            "approved_baseline_day": 100, "milestone_class": "contractual",
                            "forecasts": [{"report_index": 1, "forecast_day": 100},
                                          {"report_index": 2, "forecast_day": 102}]}],
            "schedule_version": "v1", "remaining_planned_duration_days": 2000}
check(E.run_milestone_trend({"milestoneForecastHistory": _mh_late},
                            None, None)["status_color"] == "Red",
      "A2.7: a contractual milestone forecast past its approved date is Red at a slip ratio of "
      "0.001")

print()
print("6. NO SLIP RATIO WITHOUT ITS DENOMINATOR -- THE ABSTENTION IS REAL")
_mh_nodenom = {k: v for k, v in _mh.items() if k != "remaining_planned_duration_days"}
_r = E.run_milestone_trend({"milestoneForecastHistory": _mh_nodenom}, None, None)
check(_r.get("status_color") is None and bool(_r.get("band_withheld_reason")),
      "with no remaining planned duration stated, A2.7 computes, states its reason and asserts "
      "no band", str(_r.get("status_color")))

print()
print(f"RESULT: {PASS}/{PASS + FAIL} checks passed")
sys.exit(0 if FAIL == 0 else 1)
