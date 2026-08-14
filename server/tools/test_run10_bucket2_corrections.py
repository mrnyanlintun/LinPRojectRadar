"""
Run 10, Gate 2. The exact sixteen Bucket-2 modules from code_audit/run8_module_classification.csv.

The scope list is derived from the CSV rather than transcribed, so a module cannot quietly leave
or join it. For every module: the Run-8 defect is reproduced against the corrected code and shown
to be gone, correct behaviour is asserted from the module's own stated structure, and missing
data, invalid domains, boundaries and abstention are exercised.
"""
import csv
import itertools
import math
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("SESSION_SECRET", "test-secret-do-not-use-in-prod")

from app.simulation.models import run_pert  # noqa: E402
from app.simulation.models_evm import (  # noqa: E402
    run_arima_forecast, run_earned_schedule,
    # RUN 28: the approved rename ICE Ratio -> Independent EAC Reconciliation Index.
    run_independent_eac_reconciliation as run_ice_ratio,
)
from app.simulation.models_ext import (  # noqa: E402
    run_cost_risk, run_critical_path_index, run_float_consumption, run_resource_loading,
    run_schedule_risk,
)
from app.simulation.models_doc import (  # noqa: E402
    run_contractor_performance, run_discrete_event_sim, run_quality_compliance,
    run_rework_feedback, run_safety_performance, run_spec_conflict_density,
)
from app.simulation.models_fuzzy import run_marcos  # noqa: E402
from app.simulation.rng import make_rng  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
passed = total = 0
failures = []


def check(name, cond):
    global passed, total
    total += 1
    if cond:
        passed += 1
    else:
        failures.append(name)


def abstained(r):
    # RUN 28. A calibration-pending row is NOT an abstention: the canonical method ran and
    # produced a figure, and only the colour is withheld because no boundary for the quantity has
    # been established from evidence. `insufficient_data` still wins, so nothing below is
    # weakened by this.
    if r.get("calibration_pending") and not r.get("insufficient_data"):
        return False
    return bool(r.get("insufficient_data")) or r.get("status_color") is None


def banded(r):
    return r.get("status_color") in ("Green", "Yellow", "Amber", "Red")


def banded_or_pending(r):
    """Computed: either a banded reading, or a canonical figure with calibration pending."""
    return banded(r) or (bool(r.get("calibration_pending"))
                         and not r.get("insufficient_data"))


# ---------------------------------------------------------------- scope derived, not transcribed
rows = list(csv.DictReader((ROOT / "code_audit" / "run8_module_classification.csv").open(encoding="utf-8")))
bucket2 = [r["module_id"] for r in rows if r["final_owner_action_bucket"] == "2"]
check("Bucket 2 holds exactly sixteen modules", len(bucket2) == 16)
COVERED = {"A1.5", "A1.6", "A1.11", "A2.1", "A2.5", "A2.9", "A2.10", "A2.11", "A3.6",
           "A4.10", "A5.5", "A5.8", "A6.1", "A6.2", "A6.4", "B2.18"}
check("every Bucket 2 module is covered by this suite", set(bucket2) == COVERED)
for b in ("3", "4", "5"):
    want = {"3": 7, "4": 2, "5": 2}[b]
    check(f"bucket {b} still holds exactly {want} modules",
          len([r for r in rows if r["final_owner_action_bucket"] == b]) == want)

# ================================================ CLASS 1: open input domains
#
# SUPERSEDED IN PART BY RUN 28, and the seven blocks below were observed red against the v3 build
# before being rewritten (KeyError: 'spi_time' at the first of them). Run 10's finding was that
# eleven Bucket-2 modules had an OPEN INPUT DOMAIN: a reading outside the domain a quantity can
# occupy reached a band. Run 28 replaced the computation of seven of those modules entirely, on
# the owner's supplied contract, so the specific out-of-domain scalars Run 10 drove are no longer
# inputs any of them has. Run 10's PROPERTY is stronger in v3, not weaker, and that is what is
# asserted here: the retired inputs reach no band at all because they reach no computation at
# all, and the canonical structure that replaced them refuses its own out-of-domain readings.
# A2.5, A5.8, A6.1, A6.2, A6.4, B2.18, A4.10 and A5.5 are untouched by Run 28 and keep Run 10's
# original checks below.

def _v3_retired(label, fn, cases):
    """Run 10's out-of-domain scalars now reach no computation at all."""
    for si in cases:
        check(f"{label} reaches no band from the retired input contract, so the domain Run 10 "
              f"opened cannot be reached at all", abstained(fn(dict(si), None, None)))


_NET = {"schedule_version": "SCH-1", "status_basis": "2026-06-30 data date"}


def _net(acts):
    return {"scheduleNetwork": dict(_NET, activities=acts)}


CPI_HIST = {"cpiHistory": [0.99, 0.97, 0.96, 0.94, 0.93, 0.91, 0.90, 0.88, 0.87, 0.86]}
check("A1.5 forecasts on a history long enough to identify a model from",
      banded_or_pending(run_arima_forecast(dict(CPI_HIST), None, None)))
for bad in ([0.95, 0.0, 0.91] * 4, [0.95, -0.4, 0.91] * 4, [0.0] * 12):
    check(f"A1.5 refuses a history containing {bad[1]}",
          abstained(run_arima_forecast({"cpiHistory": bad}, None, None)))
check("A1.5 refuses a history shorter than the stated minimum",
      abstained(run_arima_forecast({"cpiHistory": [0.9, 0.9]}, None, None)))
check("A1.5 accepts a history at the edge of the domain",
      banded_or_pending(run_arima_forecast(
          {"cpiHistory": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]},
          None, None)))

_ES_CURVE = {"timePhasedBaseline": {
    "baseline_version": "BL-1", "approval_source": "approved baseline",
    "actual_time_periods": 3,
    "periods": [{"period_index": i, "period": f"P{i}", "cumulative_pv": v}
                for i, v in enumerate([0, 20, 40, 60])]}, "ev": 50}
check("A1.6 computes on the cumulative planned value curve",
      banded_or_pending(run_earned_schedule(dict(_ES_CURVE), None, None)))
check("A1.6 index is the specification's own 2.5 / 3",
      abs(run_earned_schedule(dict(_ES_CURVE), None, None)["spi_time"] - 0.833) < 1e-3)
_v3_retired("A1.6", run_earned_schedule, [
    dict({"actualPctComplete": a, "plannedPctComplete": p})
    for a, p in itertools.product((-1.0, 40.0, 100.1, 250.0), (-1.0, 50.0, 100.1, 250.0))])
check("A1.6 abstains on absent evidence entirely", abstained(run_earned_schedule({}, None, None)))

ICE = {"independentEacPair": {
    "management_eac": {"eac": 100.0, "source": "controls report", "method": "index extrapolation",
                       "assumptions": "performance continues", "model_version": "PC-1",
                       "responsible_party": "project management team"},
    "independent_eac": {"eac": 120.0, "source": "review board", "method": "bottom up re-estimate",
                        "assumptions": "scope re-priced", "model_version": "IRB-1",
                        "responsible_party": "independent review board"}}}
check("A1.11 computes on two provenance-distinct forecasts",
      banded_or_pending(run_ice_ratio(dict(ICE), None, None)))
_v3_retired("A1.11", run_ice_ratio, [
    {"bac": 1_000_000.0, "cpi": c, "ev": 400_000.0, "ac": 444_444.0}
    for c in (0.9, 0.0, -0.5, -2.0)])
for bad in (0.0, -0.5, -2.0):
    r = run_ice_ratio({"independentEacPair": {
        **ICE["independentEacPair"],
        "management_eac": {**ICE["independentEacPair"]["management_eac"], "eac": bad}}},
        None, None)
    check(f"A1.11 refuses a management forecast of {bad}", abstained(r))
    check(f"A1.11 publishes no ratio at a management forecast of {bad}", "ier" not in r)

_SRA = _net([{"activity_id": "A", "predecessors": [], "current_duration": 5,
              "optimistic_duration": 0, "most_likely_duration": 5, "pessimistic_duration": 10}])
check("A2.10 computes on a governed network with duration distributions",
      banded_or_pending(run_schedule_risk(dict(_SRA), make_rng(20260828), None)))
_v3_retired("A2.10", run_schedule_risk, [
    {"spi": s, "baselineStart": "2026-01-01", "baselineEnd": "2026-12-31",
     "actualPctComplete": p}
    for s, p in itertools.product((0.9, 0.0, -0.5), (40.0, -5.0, 130.0))])
check("A2.10 refuses a network whose activities carry no distribution",
      abstained(run_schedule_risk(_net([{"activity_id": "A", "predecessors": [],
                                         "current_duration": 5}]), make_rng(1), None)))

_CPM = _net([{"activity_id": "A", "predecessors": [], "current_duration": 3},
             {"activity_id": "B", "predecessors": [], "current_duration": 4},
             {"activity_id": "C", "predecessors": ["A", "B"], "current_duration": 2}])
check("A2.11 computes on a governed activity network",
      banded_or_pending(run_critical_path_index(dict(_CPM), None, None)))
_v3_retired("A2.11", run_critical_path_index, [
    {"spi": s, "plannedPctComplete": 50.0, "actualPctComplete": 45.0}
    for s in (0.95, 0.0, -1.0)])

DES = {"spi": 0.95, "cpi": 0.95, "plannedPctComplete": 50.0, "actualPctComplete": 45.0}
check("A5.8 computes on a valid state", banded(run_discrete_event_sim(dict(DES), None, None)))
for bad in (0.0, -1.0):
    check(f"A5.8 refuses an index of {bad}",
          abstained(run_discrete_event_sim(dict(DES, spi=bad), None, None)))

_FLOAT_NET = _net([{"activity_id": "A", "predecessors": [], "current_duration": 3,
                    "baseline_total_float": 5},
                   {"activity_id": "B", "predecessors": [], "current_duration": 4,
                    "baseline_total_float": 2},
                   {"activity_id": "C", "predecessors": ["A", "B"], "current_duration": 2,
                    "baseline_total_float": 0}])
check("A2.5 computes on a governed activity network",
      banded_or_pending(run_float_consumption(dict(_FLOAT_NET), None, None)))
_v3_retired("A2.5", run_float_consumption, [
    {"totalFloat": 20.0, "consumedFloat": c, "actualPctComplete": 40.0}
    for c in (8.0, 0.0, -1.0, -30.0)])
check("A2.5 refuses a network in which nothing carries the float it began with",
      abstained(run_float_consumption(_net([{"activity_id": "A", "predecessors": [],
                                             "current_duration": 3}]), None, None)))
check("A2.5 reports an activity that began at zero float as already critical rather than "
      "dividing by nothing",
      run_float_consumption(_net([{"activity_id": "A", "predecessors": [],
                                   "current_duration": 3, "baseline_total_float": 0}]),
                            None, None).get("float_consumption_ratio") is None)

_RESPROF = {"resourceProfile": {"resource_plan_version": "RP-1", "buckets": [
    {"time_bucket": "2026-07", "resource_type": "LABOUR", "demand": 120.0,
     "available_capacity": 100.0}]}}
check("A2.9 computes on a time phased resource profile",
      banded_or_pending(run_resource_loading(dict(_RESPROF), None, None)))
_v3_retired("A2.9", run_resource_loading, [
    {"plannedLaborHours": 1000.0, "actualLaborHours": h}
    for h in (980.0, 0.0, -1.0, -500.0)])
for bad in (-1.0, -500.0):
    r = run_resource_loading({"resourceProfile": {
        "resource_plan_version": "RP-1",
        "buckets": [{"time_bucket": "2026-07", "resource_type": "LABOUR", "demand": bad,
                     "available_capacity": 100.0}]}}, None, None)
    check(f"A2.9 refuses a demand of {bad}", abstained(r))
    check(f"A2.9 publishes no ratio at a demand of {bad}", "peak_load_ratio" not in r)

SPEC = {"docRiskScore": 0.3, "rfiCount": 16}
check("A4.10 computes on a valid pair", banded(run_spec_conflict_density(dict(SPEC), None, None)))
for bad in (-0.2, 1.4, 12.0):
    check(f"A4.10 refuses a document risk score of {bad}",
          abstained(run_spec_conflict_density(dict(SPEC, docRiskScore=bad), None, None)))
for edge in (0.0, 1.0):
    check(f"A4.10 accepts a document risk score of {edge}",
          banded(run_spec_conflict_density(dict(SPEC, docRiskScore=edge), None, None)))

QC = {"qualityDeficienciesNoted": 3, "qualityAuditScore": 92.0}
check("A6.1 computes on a valid score", banded(run_quality_compliance(dict(QC), None, None)))
for bad in (150.0, 100.1, -10.0):
    r = run_quality_compliance(dict(QC, qualityAuditScore=bad), None, None)
    check(f"A6.1 refuses an audited score of {bad}", abstained(r))
    check(f"A6.1 leaves no out-of-domain figure in the finding", "quality_score" not in r)
for edge in (0.0, 100.0):
    check(f"A6.1 accepts an audited score of {edge}",
          banded(run_quality_compliance(dict(QC, qualityAuditScore=edge), None, None)))

CONTR = {"overallRating": 4.2, "scheduleRating": 3.8, "costRating": 4.0, "qualityRating": 3.2}
check("A6.4 computes on valid ratings", banded(run_contractor_performance(dict(CONTR), None, None)))
check("A6.4 reads the quality rating into the worst",
      abs(run_contractor_performance(dict(CONTR), None, None)["min_rating"] - 3.2) < 1e-9)
for key in ("overallRating", "scheduleRating", "costRating", "qualityRating"):
    for bad in (-2.0, 7.0):
        check(f"A6.4 refuses {key} of {bad}",
              abstained(run_contractor_performance(dict(CONTR, **{key: bad}), None, None)))
for edge in (0.0, 5.0):
    check(f"A6.4 accepts a rating of exactly {edge}",
          banded(run_contractor_performance(dict(CONTR, overallRating=edge), None, None)))

# SUPERSEDED BY RUN 28, observed red against the v3 build (KeyError: 'p80_delta_pct') before
# being rewritten. Run 10's finding here was a PRESENTATION defect: a forecast below budget
# printed a hard-coded plus in front of a negative figure, so the sentence said the opposite of
# the number. Run 28 replaced the whole computation on the owner's supplied contract -- the
# deterministic cost-index uplift is gone and a total-cost distribution is simulated -- so there
# is no delta percentage and no signed sentence for the old check to read. The property Run 10
# established is preserved in the form it now takes: the sentence a reader sees must agree with
# the figures beside it, which is asserted by reading both out of the same result.
def _cr(base, prob, impact):
    return {"costRiskModel": {
        "model_version": "CRM-1", "estimate_source": "approved base estimate",
        "cost_components": [{"component_id": "BASE", "base_amount": base}],
        "risk_events": [{"risk_id": "R1", "probability": prob,
                         "impact_distribution": "POINT", "impact": impact}]}}


_cra = run_cost_risk(_cr(100.0, 0.5, 20.0), make_rng(20260828), None)
check("A3.6 computes a simulated total cost distribution", banded_or_pending(_cra))
check("A3.6 the eightieth percentile is the specification's own 120",
      abs(_cra["p80_total_cost"] - 120.0) < 1e-9)
check("A3.6 the P80 is at or above the P50, which any percentile pair must satisfy",
      _cra["p80_total_cost"] >= _cra["p50_total_cost"])
check("A3.6 the sentence a reader sees carries the same figures the result carries",
      f"{int(round(_cra['p80_total_cost'])):,}" in _cra["evidence_metric"]
      and str(_cra["trials"]) in _cra["evidence_metric"])
check("A3.6 a risk that cannot occur leaves the total at the base cost, so no uplift is "
      "manufactured", run_cost_risk(_cr(100.0, 0.0, 20.0),
                                    make_rng(1), None)["p80_total_cost"] == 100.0)
_v3_retired("A3.6", run_cost_risk, [
    {"bac": 1_000_000.0, "cpi": c, "ac": 300_000.0, "ev": 420_000.0}
    for c in (1.4, 0.8, 0.0, -0.5)])

# ================================================ CLASS 2: absence of evidence must not help
FULL = {"cpi": 0.95, "rfiCount": 10, "changeOrderCount": 4}
full_r = run_rework_feedback(dict(FULL), None, None)
check("A5.5 computes on the complete evidence set", banded(full_r))
required = ("rfiCount", "changeOrderCount")
# EXHAUSTIVE over every strict subset of the required evidence, not a sample of them.
subsets = 0
for k in range(len(required)):
    for keep in itertools.combinations(required, k):
        si = {"cpi": 0.95}
        si.update({key: FULL[key] for key in keep})
        r = run_rework_feedback(si, None, None)
        subsets += 1
        check(f"A5.5 abstains on the evidence subset {keep}", abstained(r))
        check(f"A5.5 returns no index on the subset {keep}", "rework_index" not in r)
check("A5.5 exhausted every strict subset of the required evidence", subsets == 3)
check("A5.5 refuses a negative request count",
      abstained(run_rework_feedback(dict(FULL, rfiCount=-1), None, None)))
check("A5.5 refuses a negative change order count",
      abstained(run_rework_feedback(dict(FULL, changeOrderCount=-3), None, None)))
zero_counts = run_rework_feedback({"cpi": 0.95, "rfiCount": 0, "changeOrderCount": 0}, None, None)
check("A5.5 reads a reported nought as a measurement", banded(zero_counts))
check("A5.5 does not renormalise away the missing high-risk terms",
      zero_counts["rework_index"] <= full_r["rework_index"])

SAFE_REPORTED = {"safetyIncidentsDiscussed": 0, "oshaIncidentRate": 0.0}
r = run_safety_performance(dict(SAFE_REPORTED), None, None)
check("A6.2 bands a documented zero incident rate", banded(r))
check("A6.2 gives a documented zero the best index the formula produces", r["safety_index"] == 2)
DERIVED_SRC = {"sources": {"safetyIncidentsDiscussed": {"docType": "derived"}}}
silence = run_safety_performance(dict({"safetyIncidentsDiscussed": 0}, **DERIVED_SRC), None, None)
check("A6.2 abstains on meeting silence", abstained(silence))
check("A6.2 gives meeting silence no safety index", "safety_index" not in silence)
check("A6.2 names silence rather than reporting no incidents",
      "silence" in silence.get("evidence_metric", "").lower())
check("A6.2 abstains on no safety field at all", abstained(run_safety_performance({}, None, None)))
check("A6.2 refuses a negative rate",
      abstained(run_safety_performance({"safetyIncidentsDiscussed": 1,
                                        "oshaIncidentRate": -2.0}, None, None)))
mentioned = run_safety_performance(dict({"safetyIncidentsDiscussed": 2}, **DERIVED_SRC), None, None)
# RUN 20, P0B. This check previously asserted that a derived count ABOVE nought still bands, and
# in doing so it fixed the defect in place as expected behaviour: two mentions of safety in
# meeting minutes were multiplied by ten into an incident rate of 20.0 and the project banded Red
# on it. Run 10 closed the zero case and read the non-zero case as the counterpart that should
# keep computing. Specification 8.7 forbids using incidents discussed in meeting minutes as an
# OSHA incidence-rate substitute in those terms, so the assertion was wrong rather than the fix,
# and it is inverted here rather than deleted, so the defect it protected cannot come back
# unnoticed.
check("A6.2 does not turn a derived count above nought into an incidence rate either",
      abstained(mentioned) and "safety_index" not in mentioned)
check("A6.2 never gives the best index to an absent record",
      run_safety_performance({}, None, None).get("safety_index") is None
      and silence.get("safety_index") is None)

# ================================================ CLASS 3: structurally unreachable dispositions
perfect = run_marcos({"cpi": 1.05, "spi": 1.05, "docRiskScore": 0.0}, None, None)
# Known answers derived by hand from the published ranking method before production was run:
# each criterion normalised against its own ideal, three weighted sums (project, ideal reference,
# anti-ideal reference), the two utility degrees as separate ratios, then the method's own score.
# Anti-ideal weighted sum = 0.40*(0.80/1.05) + 0.35*(0.80/1.05) + 0.25*(0.30/1.00) = 0.6464286.
check("B2.18 known answer at every ideal", abs(perfect["marcos_score"] - 0.798) < 5e-4)
mid = run_marcos({"cpi": 0.9, "spi": 0.9, "docRiskScore": 0.3}, None, None)
check("B2.18 known answer at a mid state", abs(mid["marcos_score"] - 0.652) < 5e-4)
check("B2.18 gives a project at every ideal a healthy reading", perfect["status_color"] == "Green")
check("B2.18 no longer scores a perfect project at nothing", perfect["marcos_score"] > 0.65)
seen = set()
grid = []
for cpi in [0.5, 0.7, 0.8, 0.9, 1.0, 1.05, 1.2]:
    for spi in [0.5, 0.7, 0.8, 0.9, 1.0, 1.05, 1.2]:
        for d in [0.0, 0.2, 0.5, 0.7, 1.0]:
            out = run_marcos({"cpi": cpi, "spi": spi, "docRiskScore": d}, None, None)
            seen.add(out["status_color"])
            grid.append(((cpi, spi, d), out["marcos_score"]))
check("B2.18 reaches all four dispositions over the exhausted grid",
      seen == {"Green", "Yellow", "Amber", "Red"})
check("B2.18 is not symmetric about the middle of its own scale",
      len({round(s, 3) for _, s in grid}) > 10)
base = run_marcos({"cpi": 0.9, "spi": 0.9, "docRiskScore": 0.3}, None, None)["marcos_score"]
check("B2.18 improves when cost performance improves",
      run_marcos({"cpi": 1.0, "spi": 0.9, "docRiskScore": 0.3}, None, None)["marcos_score"] > base)
check("B2.18 improves when schedule performance improves",
      run_marcos({"cpi": 0.9, "spi": 1.0, "docRiskScore": 0.3}, None, None)["marcos_score"] > base)
check("B2.18 improves when document risk falls",
      run_marcos({"cpi": 0.9, "spi": 0.9, "docRiskScore": 0.1}, None, None)["marcos_score"] > base)
check("B2.18 abstains on absent inputs", abstained(run_marcos({"cpi": 0.9}, None, None)))
check("B2.18 keeps its score inside the unit interval",
      all(0 <= s <= 1 for _, s in grid))

pert = run_pert({"spi": 1.0}, lambda: 0.5, None)
check("A2.1 abstains without a project network", abstained(pert))
check("A2.1 names the structure it needs",
      "activity network" in pert.get("evidence_metric", "").lower())
check("A2.1 reports the absent-structure reason code",
      pert.get("abstention_reason_code") == "canonical_structure_absent")
check("A2.1 publishes no criticality index without a network",
      "path_criticality_index" not in pert)
for spi in (0.5, 0.8, 1.0, 1.2):
    check(f"A2.1 abstains at a schedule index of {spi}",
          abstained(run_pert({"spi": spi}, lambda: 0.5, None)))
for shape in (None, {}, {"activities": []}, [], "network"):
    check(f"A2.1 refuses a network object of shape {type(shape).__name__}",
          abstained(run_pert({"spi": 1.0, "activityNetwork": shape}, lambda: 0.5, None)))

for f in failures:
    print("FAILED:", f)
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
