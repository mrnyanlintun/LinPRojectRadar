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
    run_arima_forecast, run_earned_schedule, run_ice_ratio,
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
    return bool(r.get("insufficient_data")) or r.get("status_color") is None


def banded(r):
    return r.get("status_color") in ("Green", "Yellow", "Amber", "Red")


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
CPI_HIST = {"cpiHistory": [0.95, 0.93, 0.91]}
check("A1.5 forecasts on a valid history", banded(run_arima_forecast(dict(CPI_HIST), None, None)))
for bad in ([0.95, 0.0, 0.91], [0.95, -0.4, 0.91], [0.0, 0.0, 0.0]):
    check(f"A1.5 refuses a history containing {bad[1]}",
          abstained(run_arima_forecast({"cpiHistory": bad}, None, None)))
check("A1.5 still refuses a short history",
      abstained(run_arima_forecast({"cpiHistory": [0.9, 0.9]}, None, None)))
check("A1.5 accepts a history at the edge of the domain",
      banded(run_arima_forecast({"cpiHistory": [0.01, 0.02, 0.03]}, None, None)))

ES = {"actualPctComplete": 40.0, "plannedPctComplete": 50.0}
check("A1.6 computes without the three figures it never reads",
      banded(run_earned_schedule(dict(ES), None, None)))
check("A1.6 index is progress against plan",
      abs(run_earned_schedule(dict(ES), None, None)["spi_time"] - 0.8) < 1e-9)
for key, bad in itertools.product(("actualPctComplete", "plannedPctComplete"), (-1.0, 100.1, 250.0)):
    check(f"A1.6 refuses {key} of {bad}", abstained(run_earned_schedule(dict(ES, **{key: bad}), None, None)))
check("A1.6 accepts a completion of exactly one hundred",
      banded(run_earned_schedule({"actualPctComplete": 100.0, "plannedPctComplete": 100.0}, None, None)))
check("A1.6 abstains on absent completion", abstained(run_earned_schedule({}, None, None)))

ICE = {"bac": 1_000_000.0, "cpi": 0.9, "ev": 400_000.0, "ac": 444_444.0}
check("A1.11 computes on a positive index", banded(run_ice_ratio(dict(ICE), None, None)))
for bad in (0.0, -0.5, -2.0):
    r = run_ice_ratio(dict(ICE, cpi=bad), None, None)
    check(f"A1.11 refuses an index of {bad}", abstained(r))
    check(f"A1.11 publishes no currency figure at an index of {bad}", "eac_cpi" not in r)

SR = {"spi": 0.9, "baselineStart": "2026-01-01", "baselineEnd": "2026-12-31",
      "actualPctComplete": 40.0}
check("A2.10 computes on a valid state", banded(run_schedule_risk(dict(SR), None, None)))
for bad in (0.0, -0.5):
    check(f"A2.10 refuses an index of {bad} rather than raising",
          abstained(run_schedule_risk(dict(SR, spi=bad), None, None)))
for bad in (-5.0, 130.0):
    check(f"A2.10 refuses a completion of {bad}",
          abstained(run_schedule_risk(dict(SR, actualPctComplete=bad), None, None)))
check("A2.10 reports no favourable delay from an invalid domain",
      not any(run_schedule_risk(dict(SR, spi=b), None, None).get("p80_delay_days", 0) < 0
              for b in (-0.5, -2.0)))

CPI_IDX = {"spi": 0.95, "plannedPctComplete": 50.0, "actualPctComplete": 45.0}
check("A2.11 computes on a valid state", banded(run_critical_path_index(dict(CPI_IDX), None, None)))
for bad in (0.0, -1.0):
    check(f"A2.11 refuses an index of {bad}",
          abstained(run_critical_path_index(dict(CPI_IDX, spi=bad), None, None)))

DES = {"spi": 0.95, "cpi": 0.95, "plannedPctComplete": 50.0, "actualPctComplete": 45.0}
check("A5.8 computes on a valid state", banded(run_discrete_event_sim(dict(DES), None, None)))
for bad in (0.0, -1.0):
    check(f"A5.8 refuses an index of {bad}",
          abstained(run_discrete_event_sim(dict(DES, spi=bad), None, None)))

FLOAT = {"totalFloat": 20.0, "consumedFloat": 8.0, "actualPctComplete": 40.0}
check("A2.5 computes on a valid state", banded(run_float_consumption(dict(FLOAT), None, None)))
for bad in (-1.0, -30.0):
    r = run_float_consumption(dict(FLOAT, consumedFloat=bad), None, None)
    check(f"A2.5 refuses consumed float of {bad}", abstained(r))
    check(f"A2.5 does not read Green on consumed float of {bad}", r.get("status_color") != "Green")
check("A2.5 accepts consumed float of exactly nought",
      banded(run_float_consumption(dict(FLOAT, consumedFloat=0.0), None, None)))

RES = {"plannedLaborHours": 1000.0, "actualLaborHours": 980.0}
check("A2.9 computes on a valid pair", banded(run_resource_loading(dict(RES), None, None)))
for bad in (-1.0, -500.0):
    r = run_resource_loading(dict(RES, actualLaborHours=bad), None, None)
    check(f"A2.9 refuses actual hours of {bad}", abstained(r))
    check(f"A2.9 publishes no ratio at actual hours of {bad}", "load_ratio" not in r)
check("A2.9 accepts actual hours of exactly nought",
      banded(run_resource_loading(dict(RES, actualLaborHours=0.0), None, None)))

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

CR = {"bac": 1_000_000.0, "cpi": 1.4, "ac": 300_000.0, "ev": 420_000.0}
below = run_cost_risk(dict(CR), None, None)
check("A3.6 computes a forecast below budget", banded(below))
check("A3.6 forecast below budget carries a negative delta", below["p80_delta_pct"] < 0)
check("A3.6 does not print a plus in front of a negative figure",
      "(+-" not in below["evidence_metric"] and "+-" not in below["evidence_metric"])
check("A3.6 prints the minus sign it computed", "-" in below["evidence_metric"].split("(")[-1])
above = run_cost_risk(dict(CR, cpi=0.8), None, None)
check("A3.6 still prints a plus in front of an overrun", "(+" in above["evidence_metric"])

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
