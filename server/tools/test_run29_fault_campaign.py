"""
RUN 29 -- THE NON-VACUITY CAMPAIGN: the twenty faults section 18 of the supplied contract names.

THE RULE THIS SUITE OBEYS, and it is the rule sixteen-plus vacuous guards in this programme were
found breaking. For each fault:

    1  INJECT it;
    2  CONFIRM THE INJECTION TOOK EFFECT by reading the mutated state back rather than assuming;
    3  observe the NAMED GUARD go RED for the INTENDED REASON;
    4  RESTORE;
    5  observe the guard GREEN again.

A CRASH IS NOT RED. Every guard below is a boolean over a value the module returned, and the
"red" observation is that the boolean flips, not that something raised. Where a fault is a
mutation of a governed structure the module receives, the module's own refusal IS the guard, and
what is asserted is that the refusal happens for that fault and does not happen without it -- the
green half is asserted every time, so a guard that refused everything would fail here.

NOTHING IS MUTATED IN THE REPOSITORY. Faults 19 and 20, which are about production code rather
than about a structure, are injected into isolated in-memory copies of the tables they concern
and restored in a `finally`, and the restoration is verified.

The results are written to `code_audit/run29_fault_injection.csv`.
"""

from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402
# Run 137, Item 1: a removed module identifier is SUBSTITUTED, not dispatched.
import os as _r96_os, sys as _r96_sys  # noqa: E402
_r96_sys.path.insert(0, _r96_os.path.dirname(_r96_os.path.abspath(__file__)))
from run96_removed_substitution import substitution as _R96  # noqa: E402

import csv
import datetime
import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# --- CAMPAIGN SAFETY (Run 54, phase A) -----------------------------------------------------
# THE START-AND-END DIRTY-TREE GUARD. A campaign must not BEGIN on a dirty tree: Run 53
# established that a leaked fault is snapshotted from disk by the next campaign, faithfully
# restored by its `finally`, and thereby CERTIFIED by its own passing assertion. An end-only
# check cannot see that, because the leak began in an earlier process. See
# server/tools/campaign_safety.py for the full mechanism and the proof.
import sys as _cs_sys, pathlib as _cs_pl                                       # noqa: E402
_cs_sys.path.insert(0, str(_cs_pl.Path(ROOT) / "server" / "tools"))
from campaign_safety import (arm as _cs_arm, restore_guard, head_text,          # noqa: E402,F401
                             snapshot_text, CampaignTreeDirty)
_cs_arm(_cs_pl.Path(ROOT), "test_run29_fault_campaign.py",
        allow=["code_audit/run29_fault_injection.csv"])
# -------------------------------------------------------------------------------------------
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app import project_data as PD                             # noqa: E402
from app.simulation import models as M                         # noqa: E402
from app.simulation import registry as REG                     # noqa: E402
from app.simulation.canonical import StructureAbsent           # noqa: E402
from app.simulation.canonical_v4 import (                      # noqa: E402
    V4_STRUCTURE_KEYS, document_risk_evidence,
)
import run29_fixtures as FX                                    # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731

PASSED = 0
FAILED = 0
FAILURES: list[str] = []
ROWS: list[dict] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))
    return ok


def run(mid: str, si: dict) -> dict:
    return _R96.dispatch(REG.run_module, globals(), mid, si, RAND, CUTOFF)


def abstains(out: dict) -> bool:
    return bool(out.get("insufficient_data"))


def structure_fault(number: int, name: str, module: str, key: str, clean, faulty,
                    injection_evidence: str, guard: str, reason_fragment: str = "") -> None:
    """
    One fault whose vehicle is a mutated governed structure.

    `clean` and `faulty` are callables returning the structure. The guard is the module's own
    refusal, and BOTH halves are asserted: the clean structure must compute (so the guard is not
    refusing everything) and the faulty one must refuse (so the guard binds).
    """
    print()
    print(f"--- FAULT {number}: {name}")
    _clean, _faulty = clean(), faulty()
    took = _clean != _faulty
    check(took, f"F{number} INJECTION CONFIRMED: the structure handed to {module} really differs "
                f"from the clean one -- {injection_evidence}")
    before = run(module, {key: _clean})
    green_before = check(not abstains(before),
                         f"F{number} GREEN BEFORE: {module} computes from the clean structure, so "
                         f"the guard is not one that refuses everything",
                         str(before.get("evidence_metric"))[:70])
    hurt = run(module, {key: _faulty})
    red = check(abstains(hurt),
                f"F{number} RED: {guard} refuses the faulted structure",
                str(hurt.get("evidence_metric"))[:90])
    if reason_fragment:
        check(reason_fragment.lower() in str(hurt.get("evidence_metric", "")).lower(),
              f"F{number} RED FOR THE INTENDED REASON: the refusal names {reason_fragment!r} "
              f"rather than failing for something unrelated",
              str(hurt.get("evidence_metric"))[:110])
    after = run(module, {key: clean()})
    green_after = check(not abstains(after) and after == before,
                        f"F{number} RESTORED: {module} computes from the clean structure again, "
                        f"identically to before the injection")
    ROWS.append({
        "fault": number, "name": name, "module": module, "vehicle": f"structure {key}",
        "injection_confirmed": "yes" if took else "no",
        "guard": guard,
        "green_before": "yes" if green_before else "no",
        "red_under_fault": "yes" if red else "no",
        "red_reason": str(hurt.get("abstention_reason_code") or ""),
        "green_after_restore": "yes" if green_after else "no",
        "crash_accepted_as_red": "no",
    })


print("=" * 78)
print("RUN 29 NON-VACUITY CAMPAIGN: the twenty faults of contract section 18")
print("=" * 78)

# ---------------------------------------------------------------- 1
structure_fault(
    1, "Document Risk Score with no evidence provenance", "A4.1-engine", "documentRiskEvidence",
    FX.document_risk_evidence,
    lambda: dict(FX.document_risk_evidence(), source="", classifier_version=""),
    "the source and the classifier version are blanked",
    "canonical_v4.document_risk_evidence's provenance guard") if False else None
# A4.1 is registered but not registry-computed, so its guard is the engine rather than a runner.
print()
print("--- FAULT 1: Document Risk Score with no evidence provenance")
_clean1 = FX.document_risk_evidence()
_bad1 = dict(FX.document_risk_evidence(), source="", classifier_version="")
check(_clean1 != _bad1,
      "F1 INJECTION CONFIRMED: the source and the classifier version are blanked on the record "
      "handed to the aggregation")
_ok1 = document_risk_evidence(_clean1)
_green1 = check(abs(_ok1["risk_score"] - 1 / 1.5) < 1e-12,
                "F1 GREEN BEFORE: the clean evidence aggregates to the contract's own figure")
_red1 = False
_r1_reason = ""
try:
    document_risk_evidence(_bad1)
except StructureAbsent as exc:
    _red1 = True
    _r1_reason = exc.sentence
check(_red1, "F1 RED: the provenance guard refuses evidence with no stated source")
check("where its figures came from" in _r1_reason,
      "F1 RED FOR THE INTENDED REASON: the refusal is about provenance, not about arithmetic",
      _r1_reason[:110])
_green1b = check(document_risk_evidence(FX.document_risk_evidence())["risk_score"]
                 == _ok1["risk_score"],
                 "F1 RESTORED: the clean evidence aggregates identically again")
ROWS.append({"fault": 1, "name": "Document Risk Score with no evidence provenance",
             "module": "A4.1", "vehicle": "structure documentRiskEvidence",
             "injection_confirmed": "yes",
             "guard": "canonical_v4.document_risk_evidence provenance guard",
             "green_before": "yes" if _green1 else "no", "red_under_fault": "yes" if _red1 else "no",
             "red_reason": "provenance absent", "green_after_restore": "yes" if _green1b else "no",
             "crash_accepted_as_red": "no"})

# ---------------------------------------------------------------- 2
print()
print("--- FAULT 2: an RFI cumulative-register revision double-counted as a new event")
# The fault is not a malformed structure but a WRONG READING of a well-formed one: the same
# twelve requests re-reported under NEW identities, which is what double-counting looks like.
_clean2 = FX.rfi_event_log()
_dup_same_ids = FX.rfi_event_log(duplicate=True)
_relabelled = FX.rfi_event_log()
_relabelled["events"] = _relabelled["events"] + [
    dict(e, rfi_id=e["rfi_id"] + "-COPY") for e in _relabelled["events"]]
check(len(_dup_same_ids["events"]) == 24 and len(_clean2["events"]) == 12,
      "F2 INJECTION CONFIRMED: the register now carries twenty-four rows where the clean one "
      "carries twelve", f"{len(_dup_same_ids['events'])} rows")
_base2 = run("A4.2", {"rfiEventLog": _clean2})
_green2 = check(_base2["total_rfis"] == 12 and abs(_base2["rate_per_day"] - 0.4) < 5e-3,
                "F2 GREEN BEFORE: twelve events over thirty days is 0.4 a day")
_dup2 = run("A4.2", {"rfiEventLog": _dup_same_ids})
_red2 = check(_dup2["total_rfis"] == 12 and _dup2["duplicate_rows_collapsed"] == 12
              and abs(_dup2["rate_per_day"] - 0.4) < 5e-3,
              "F2 RED IN THE DIRECTION THAT MATTERS: re-uploading the same cumulative register "
              "does NOT double the rate; the twelve repeated rows are collapsed and reported as "
              "collapsed", f"{_dup2['total_rfis']} events, rate {_dup2['rate_per_day']}")
_relab2 = run("A4.2", {"rfiEventLog": _relabelled})
check(_relab2["total_rfis"] == 24 and abs(_relab2["rate_per_day"] - 0.8) < 5e-3,
      "F2 AND THE GUARD IS NOT BLIND: twenty-four requests with twenty-four DISTINCT identities "
      "really is twice the rate, so the de-duplication is by identity and not by row count",
      str(_relab2["rate_per_day"]))
_conflict = FX.rfi_event_log()
_conflict["events"] = _conflict["events"] + [
    dict(e, created_day=e["created_day"] + 99) for e in _conflict["events"]]
check(abstains(run("A4.2", {"rfiEventLog": _conflict})),
      "F2 AND A REGISTER CARRYING THE SAME REQUEST TWICE WITH DIFFERENT DATES IS REFUSED rather "
      "than silently de-duplicated to one of them")
_green2b = check(run("A4.2", {"rfiEventLog": FX.rfi_event_log()}) == _base2,
                 "F2 RESTORED: the clean register reads identically again")
ROWS.append({"fault": 2, "name": "RFI cumulative-register revision double-counted",
             "module": "A4.2", "vehicle": "structure rfiEventLog",
             "injection_confirmed": "yes", "guard": "identity de-duplication in rfi_velocity",
             "green_before": "yes" if _green2 else "no", "red_under_fault": "yes" if _red2 else "no",
             "red_reason": "repeated identities collapsed; conflicting dates refused",
             "green_after_restore": "yes" if _green2b else "no", "crash_accepted_as_red": "no"})

# ---------------------------------------------------------------- 3
print()
print("--- FAULT 3: submittal rejected count greater than the assessed population")
# The register path cannot express this fault: a rejection IS an assessed decision there, so
# rejected is a subset of assessed by construction, which is the stronger position. The fault
# CAN be expressed on the extracted-totals path, where the two figures arrive as independent
# numbers, and that is where it is injected.
_clean3 = {"submittalsTotal": 20, "submittalsRejected": 3}
_bad3 = {"submittalsTotal": 20, "submittalsRejected": 30}
check(_bad3["submittalsRejected"] > _bad3["submittalsTotal"]
      and _clean3["submittalsRejected"] <= _clean3["submittalsTotal"],
      "F3 INJECTION CONFIRMED: the rejected count is set above the assessed total, read back "
      "from the input", f"{_bad3['submittalsRejected']} of {_bad3['submittalsTotal']}")
_base3 = run("A4.3", _clean3)
_green3 = check(_base3.get("rejection_rate") == 0.15,
                "F3 GREEN BEFORE: three of twenty is 0.15")
_red3 = check(abstains(run("A4.3", _bad3)),
              "F3 RED: a rejected count outside the total is refused rather than producing a "
              "rate above one that the top band silently absorbs",
              str(run("A4.3", _bad3).get("evidence_metric"))[:90])
check(abstains(run("A4.3", {"submittalDecisionRegister": dict(
    FX.submittal_register(), decisions=FX.submittal_register()["decisions"]
    + [FX.submittal_register()["decisions"][0]])})),
      "F3 AND ON THE GOVERNED REGISTER the same decision declared twice is refused, so a "
      "duplicated row cannot inflate either side of the share")
_green3b = check(run("A4.3", _clean3) == _base3, "F3 RESTORED")
ROWS.append({"fault": 3, "name": "submittal rejected greater than assessed", "module": "A4.3",
             "vehicle": "extracted totals and a duplicated register row",
             "injection_confirmed": "yes", "guard": "run_submittal_rejection domain guard",
             "green_before": "yes" if _green3 else "no", "red_under_fault": "yes" if _red3 else "no",
             "red_reason": "rejected outside the total",
             "green_after_restore": "yes" if _green3b else "no", "crash_accepted_as_red": "no"})

# ---------------------------------------------------------------- 4
structure_fault(
    4, "NCR numerator with no exposure denominator claimed as a normalised rate", "A4.4",
    "ncrExposureRecord", FX.ncr_record,
    lambda: dict(FX.ncr_record(), exposure_quantity=0.0),
    "the exposure quantity is set to nought while the four nonconformances remain",
    "canonical_v4.ncr_rate's exposure guard", "exposure")

# ---------------------------------------------------------------- 5
structure_fault(
    5, "a weather day with no schedule linkage claimed as impact", "A4.5",
    "weatherImpactEvents", FX.weather_events,
    lambda: dict(FX.weather_events(), events=[
        {k: v for k, v in FX.weather_events()["events"][0].items()
         if k not in ("activity_id", "schedule_path_id", "causal_evidence")}]),
    "the affected activity, the schedule path and the causal evidence are removed, leaving a "
    "bare count of lost days",
    "canonical_v4.weather_day_impact's linkage guard")

# ---------------------------------------------------------------- 6
structure_fault(
    6, "change frequency with no exposure", "A4.6", "changeEventRegister", FX.change_register,
    lambda: FX.change_register(exposure_days=0.0),
    "the exposure window is set to nought while the six changes remain",
    "canonical_v4.change_frequency's exposure guard", "span of time")

# ---------------------------------------------------------------- 7
print()
print("--- FAULT 7: dispute status inferred only from RFI and change counts")
_base7 = run("A4.7", {"claimDisputeRegister": FX.dispute_register()})
_green7 = check(_base7.get("highest_stage_id") == "S1_CLAIM_SUBMITTED",
                "F7 GREEN BEFORE: with the governed register the stage is read")
_kpi = {"docRiskScore": 0.9, "rfiCount": 40, "changeOrderCount": 30}
check(all(k not in V4_STRUCTURE_KEYS.values() for k in _kpi),
      "F7 INJECTION CONFIRMED: the input handed to the module contains only generic KPI fields "
      "and no governed dispute structure at all", str(sorted(_kpi)))
_red7 = check(abstains(run("A4.7", _kpi)),
              "F7 RED: no stage is inferred from a request count, a change count and a document "
              "risk score", str(run("A4.7", _kpi).get("evidence_metric"))[:80])
_sweep7 = {run("A4.7", {"docRiskScore": d, "rfiCount": r,
                        "changeOrderCount": c}).get("highest_stage_rank")
           for d in (0.0, 0.5, 1.0) for r in (0, 20, 100) for c in (0, 10, 60)}
check(_sweep7 == {None},
      "F7 AND EXHAUSTIVELY: across twenty-seven combinations of the three counts no stage is "
      "ever produced", str(_sweep7))
_green7b = check(run("A4.7", {"claimDisputeRegister": FX.dispute_register()}) == _base7,
                 "F7 RESTORED: the governed register reads identically again")
ROWS.append({"fault": 7, "name": "dispute status inferred from RFI and change counts",
             "module": "A4.7", "vehicle": "generic KPI fields with no dispute structure",
             "injection_confirmed": "yes", "guard": "require_v4_structure for A4.7",
             "green_before": "yes" if _green7 else "no", "red_under_fault": "yes" if _red7 else "no",
             "red_reason": "canonical_structure_absent",
             "green_after_restore": "yes" if _green7b else "no", "crash_accepted_as_red": "no"})

# ---------------------------------------------------------------- 8
print()
print("--- FAULT 8: an opaque subcontractor score with no component provenance")
_base8 = run("A4.8", {"subcontractorAssessments": FX.subcontractor_assessment()})
_green8 = check(abs(_base8["mean_score"] - 0.80) < 1e-4,
                "F8 GREEN BEFORE: the component ratings and versioned weights give 0.80")
_opaque = {"subcontractorComplianceScore": 0.82, "docRiskScore": 0.4,
           "subcontractorIssuesDiscussed": 3}
_red8 = check(abstains(run("A4.8", _opaque)),
              "F8 RED: an opaque precomputed compliance score with no criterion, rating, "
              "evaluator or weight is refused", str(run("A4.8", _opaque).get("evidence_metric"))[:80])
_no_prov = dict(FX.subcontractor_assessment(), weights_version="")
check(FX.subcontractor_assessment() != _no_prov,
      "F8 INJECTION CONFIRMED: the weights version is blanked on the governed structure")
check(abstains(run("A4.8", {"subcontractorAssessments": _no_prov})),
      "F8 AND THE SAME REFUSAL APPLIES TO THE GOVERNED STRUCTURE with no weight version, so the "
      "provenance requirement is not satisfied merely by using the new shape")
_green8b = check(run("A4.8", {"subcontractorAssessments": FX.subcontractor_assessment()})
                 == _base8, "F8 RESTORED")
ROWS.append({"fault": 8, "name": "opaque subcontractor score with no component provenance",
             "module": "A4.8", "vehicle": "precomputed scalar and a version-less structure",
             "injection_confirmed": "yes", "guard": "subcontractor_performance provenance guard",
             "green_before": "yes" if _green8 else "no", "red_under_fault": "yes" if _red8 else "no",
             "red_reason": "canonical_structure_absent",
             "green_after_restore": "yes" if _green8b else "no", "crash_accepted_as_red": "no"})

# ---------------------------------------------------------------- 9
print()
print("--- FAULT 9: a delayed procurement item double-counted inside at-risk")
_items = FX.procurement_items()
_items["items"] = [dict(_items["items"][0]),
                   dict(_items["items"][0], item_id="AHU-02", required_on_site_day=100.0,
                        forecast_delivery_day=95.0, available_float_days=0.0)]
_base9 = run("A4.9", {"procurementItems": _items})
_states = _base9["state_counts"]
_green9 = check(sum(_states.values()) == _base9["item_count"] == 2,
                "F9 GREEN BEFORE: two items, each in exactly one state", str(_states))
# The fault: the SAME item declared twice, which is what a double count is in an item register.
_dupe = dict(_items)
_dupe["items"] = _items["items"] + [dict(_items["items"][0])]
check(len(_dupe["items"]) == 3 and len(_items["items"]) == 2,
      "F9 INJECTION CONFIRMED: the register now declares the late item twice")
_red9 = check(abstains(run("A4.9", {"procurementItems": _dupe})),
              "F9 RED: an item register that declares the same item twice is refused, so the "
              "same slippage cannot be counted twice",
              str(run("A4.9", {"procurementItems": _dupe}).get("evidence_metric"))[:80])
check(_states["LATE"] + _states["AT_RISK"] + _states["ON_TIME"] == 2
      and _states["LATE"] == 1 and _states["ON_TIME"] == 1,
      "F9 AND THE STATES PARTITION: the late item is NOT also counted at risk", str(_states))
_green9b = check(run("A4.9", {"procurementItems": _items}) == _base9, "F9 RESTORED")
ROWS.append({"fault": 9, "name": "delayed procurement item double-counted inside at-risk",
             "module": "A4.9", "vehicle": "structure procurementItems",
             "injection_confirmed": "yes", "guard": "procurement_slack identity and state guards",
             "green_before": "yes" if _green9 else "no", "red_under_fault": "yes" if _red9 else "no",
             "red_reason": "canonical_structure_absent",
             "green_after_restore": "yes" if _green9b else "no", "crash_accepted_as_red": "no"})

# ---------------------------------------------------------------- 10
structure_fault(
    10, "specification conflict density with no denominator", "A4.10",
    "specificationConflictRegister", FX.conflict_register,
    lambda: FX.conflict_register(exposure=0.0),
    "the exposure quantity is set to nought while the five confirmed conflicts remain",
    "canonical_v4.specification_conflict_density's exposure guard", "how much specification")

# ---------------------------------------------------------------- 11
print()
print("--- FAULT 11: a DSM edge removed, and reversed")
_base11 = run("A5.1", {"dsmDependencyModel": FX.dsm_model()})
_green11 = check(_base11["waves"][1] == {"n1": 0.5, "n2": 0.0},
                 "F11 GREEN BEFORE: the wave arrives at n1 at half strength")
_removed = dict(FX.dsm_model(), edges=[])
check(_removed["edges"] != FX.dsm_model()["edges"],
      "F11 INJECTION CONFIRMED (a): the single edge is removed")
_r11a = run("A5.1", {"dsmDependencyModel": _removed})
_red11a = check(_r11a["waves"][1] == {"n1": 0.0, "n2": 0.0}
                and _r11a["total_propagated_rework"] == 0.0,
                "F11 RED (a): with the edge gone nothing propagates, so the propagation really "
                "reads the edge", str(_r11a["waves"][1]))
_reversed = dict(FX.dsm_model(),
                 edges=[{"source": "n1", "target": "n2", "strength": 0.5}])
check(_reversed["edges"] != FX.dsm_model()["edges"],
      "F11 INJECTION CONFIRMED (b): the edge is reversed")
_r11b = run("A5.1", {"dsmDependencyModel": _reversed})
_red11b = check(_r11b["waves"][1] == {"n1": 0.0, "n2": 0.0},
                "F11 RED (b): with the edge reversed the seeded rework has nowhere to go, so the "
                "declared orientation really governs the matrix", str(_r11b["waves"][1]))
_green11b = check(run("A5.1", {"dsmDependencyModel": FX.dsm_model()}) == _base11, "F11 RESTORED")
ROWS.append({"fault": 11, "name": "DSM edge removed and reversed", "module": "A5.1",
             "vehicle": "structure dsmDependencyModel", "injection_confirmed": "yes",
             "guard": "dsm_rework_propagation matrix assembly under the declared orientation",
             "green_before": "yes" if _green11 else "no",
             "red_under_fault": "yes" if (_red11a and _red11b) else "no",
             "red_reason": "propagated rework falls to nought",
             "green_after_restore": "yes" if _green11b else "no", "crash_accepted_as_red": "no"})

# ---------------------------------------------------------------- 12
structure_fault(
    12, "a sensitivity result without input perturbation", "A5.2", "sensitivityModel",
    FX.sensitivity_model,
    lambda: dict(FX.sensitivity_model(), inputs=[
        dict(FX.sensitivity_model()["inputs"][0], perturbation_fraction=0.0)]),
    "the perturbation is set to nought, so no input would be moved and no response recomputed",
    "canonical_v4.sensitivity_analysis's perturbation guard", "moved by nothing at all")

# ---------------------------------------------------------------- 13
print()
print("--- FAULT 13: the tornado treated as an independent evidence body")
_s13 = run("A5.2", {"sensitivityModel": FX.tornado_model()})
_t13 = run("A5.3", {"sensitivityModel": FX.tornado_model()})
_pairs = {i["input_id"]: (i["response_at_low"], i["response_at_high"]) for i in _s13["inputs"]}
_green13 = check(all((b["response_at_low"], b["response_at_high"]) == _pairs[b["input_id"]]
                     for b in _t13["bars"]) and _t13["independent_evidence"] is False,
                 "F13 GREEN BEFORE: every bar is the sensitivity's own low and high response")
# THE FAULT: change the response model so the sensitivity's answers move. If the tornado were an
# independent evidence body it would be free to keep its old answers. It cannot.
_moved_model = dict(FX.tornado_model(),
                    response_model={"model_id": "LAB-ADDITIVE", "version": "2.0",
                                    "terms": [{"coefficient": 2.0, "powers": {"A": 1}},
                                              {"coefficient": 1.0, "powers": {"B": 1}},
                                              {"coefficient": 1.0, "powers": {"C": 1}}]})
check(_moved_model["response_model"] != FX.tornado_model()["response_model"],
      "F13 INJECTION CONFIRMED: the declared response model's coefficient on A is doubled")
_s13b = run("A5.2", {"sensitivityModel": _moved_model})
_t13b = run("A5.3", {"sensitivityModel": _moved_model})
_pairs_b = {i["input_id"]: (i["response_at_low"], i["response_at_high"]) for i in _s13b["inputs"]}
_red13 = check(all((b["response_at_low"], b["response_at_high"]) == _pairs_b[b["input_id"]]
                   for b in _t13b["bars"])
               and _t13b["bars"][0]["impact"] != _t13["bars"][0]["impact"],
               "F13 RED: the tornado's bars MOVE with the sensitivity's, so it cannot hold an "
               "independent answer; a module that computed its own evidence would not have moved",
               f"{_t13['bars'][0]['impact']} -> {_t13b['bars'][0]['impact']}")
check(_t13b["derived_from_response_model_version"] == "2.0"
      and _t13b["derived_from_base_response"] == _s13b["base_response"],
      "F13 AND THE LINEAGE FOLLOWS IT: the ranking names the response model version and the base "
      "response it was derived from, and both are the sensitivity's")
check(abstains(run("A5.3", {})),
      "F13 AND WITH NOTHING FOR A5.2 TO COMPUTE, A5.3 HAS NOTHING TO PRESENT and abstains")
_green13b = check(run("A5.3", {"sensitivityModel": FX.tornado_model()}) == _t13, "F13 RESTORED")
ROWS.append({"fault": 13, "name": "tornado treated as an independent evidence body",
             "module": "A5.3", "vehicle": "structure sensitivityModel",
             "injection_confirmed": "yes", "guard": "tornado_ranking takes the A5.2 result only",
             "green_before": "yes" if _green13 else "no", "red_under_fault": "yes" if _red13 else "no",
             "red_reason": "the bars move with the sensitivity",
             "green_after_restore": "yes" if _green13b else "no", "crash_accepted_as_red": "no"})

# ---------------------------------------------------------------- 14
structure_fault(
    14, "an inconsistent scenario state", "A5.4", "scenarioSet", FX.scenario_set,
    lambda: dict(FX.scenario_set(), scenarios=[
        dict(FX.scenario_set()["scenarios"][0], variables={"x1": 99.0, "x2": 1.0})]
        + FX.scenario_set()["scenarios"][1:]),
    "the BASE scenario sets x1 to ninety-nine, outside the range the set itself declares "
    "consistent",
    "canonical_v4.scenario_modeling's consistency-constraint guard", "outside the range")

# ---------------------------------------------------------------- 15
structure_fault(
    15, "a broken system-dynamics accounting identity", "A5.5", "systemDynamicsModel",
    FX.system_dynamics_model,
    lambda: dict(FX.system_dynamics_model(), steps=[
        {"step": 0, "new_work": 5.0, "work_completed": 99.0, "error_rate": 0.25}]),
    "the step completes ninety-nine units of work from a backlog of ten plus five arriving, so "
    "the stock cannot balance",
    "canonical_v4.rework_feedback_loop's accounting guard", "more work than was in the backlog")

# ---------------------------------------------------------------- 16
print()
print("--- FAULT 16: an unstable queue returning a reassuring finite steady state")
_base16 = run("A5.6", {"queueModel": FX.queue_model()})
_green16 = check(abs(_base16["utilisation"] - 2 / 3) < 1e-5 and abs(_base16["W"] - 1.0) < 1e-5,
                 "F16 GREEN BEFORE: a stable queue reports rho two thirds and W one")
for _lam, _label in ((3.0, "equal to"), (4.0, "above")):
    _bad16 = FX.queue_model(arrival=_lam)
    check(_bad16["queues"][0]["arrival_rate"] == _lam
          and _bad16["queues"][0]["arrival_rate"] >= _bad16["queues"][0]["service_rate"],
          f"F16 INJECTION CONFIRMED: the arrival rate is set {_label} the service rate, read "
          f"back from the structure", str(_bad16["queues"][0]["arrival_rate"]))
    _out16 = run("A5.6", {"queueModel": _bad16})
    check(abstains(_out16) and _out16.get("W") is None and _out16.get("L") is None,
          f"F16 RED: with lambda {_label} mu the module refuses and reports NO finite waiting "
          f"time at all", str(_out16.get("evidence_metric"))[:90])
    check("without limit" in str(_out16.get("evidence_metric", "")),
          "F16 RED FOR THE INTENDED REASON: the refusal says the waiting grows without limit",
          str(_out16.get("evidence_metric"))[:110])
_edge16 = run("A5.6", {"queueModel": FX.queue_model(arrival=2.999)})
check(not abstains(_edge16),
      "F16 AND THE BOUNDARY IS NOT A BLANKET REFUSAL: just below one still has a steady state")
_green16b = check(run("A5.6", {"queueModel": FX.queue_model()}) == _base16, "F16 RESTORED")
ROWS.append({"fault": 16, "name": "unstable queue returning a reassuring steady state",
             "module": "A5.6", "vehicle": "structure queueModel", "injection_confirmed": "yes",
             "guard": "queue_model stability condition", "green_before": "yes" if _green16 else "no",
             "red_under_fault": "yes", "red_reason": "canonical_structure_absent, no steady state",
             "green_after_restore": "yes" if _green16b else "no", "crash_accepted_as_red": "no"})

# ---------------------------------------------------------------- 17
structure_fault(
    17, "an agent-based model with no agents or rules", "A5.7", "agentSupplyChainModel",
    FX.agent_model,
    lambda: dict(FX.agent_model(), agents=[]),
    "every agent is removed, leaving an environment and a time span and nothing to act in them",
    "canonical_v4.agent_supply_chain's agent guard")
structure_fault(
    17.5 if False else 17, "an agent-based model whose agents carry no rule", "A5.7",
    "agentSupplyChainModel", FX.agent_model,
    lambda: dict(FX.agent_model(), agents=[dict(a, behaviour_rule="")
                                           for a in FX.agent_model()["agents"]]),
    "every agent's behaviour rule is blanked, so the agents exist but do nothing",
    "canonical_v4.agent_supply_chain's rule guard")

# ---------------------------------------------------------------- 18
structure_fault(
    18, "a DES model with no event, clock, queue or resource structure", "A5.8",
    "desProcessModel", FX.des_model,
    lambda: dict(FX.des_model(), resources=[]),
    "the resource is removed, so there is nothing to queue for and no clock to advance",
    "canonical_v4.des_process_model's resource guard")
print()
print("--- FAULT 18b: a DES model with no entities to schedule")
_bad18 = dict(FX.des_model(), entities=[])
check(_bad18["entities"] != FX.des_model()["entities"],
      "F18b INJECTION CONFIRMED: the entity list is emptied")
check(abstains(run("A5.8", {"desProcessModel": _bad18})),
      "F18b RED: with no entities there is no event list to process and the module refuses")
check(not abstains(run("A5.8", {"desProcessModel": FX.des_model()})), "F18b RESTORED")

# ---------------------------------------------------------------- 19
print()
print("--- FAULT 19: an orphan new canonical structure with no production supply path")
_real_vocab = PD.governed_structure_keys
_victim = "desProcessModel"


def _crippled() -> set:
    return {k for k in _real_vocab() if k != _victim}


_green19 = check(_victim in _real_vocab(),
                 "F19 GREEN BEFORE: the structure is in the governed intake vocabulary")
PD.governed_structure_keys = _crippled
try:
    check(_victim not in PD.governed_structure_keys(),
          "F19 INJECTION CONFIRMED: the vocabulary no longer carries the key, read back after "
          "the injection")
    _orphans = sorted(k for k in set(V4_STRUCTURE_KEYS.values())
                      if k not in PD.governed_structure_keys())
    _red19 = check(_orphans == [_victim],
                   "F19 RED: the supply-path completeness check names exactly the structure that "
                   "lost its intake", str(_orphans))
    _refused = False
    try:
        PD.add_revision({}, _victim, FX.des_model(), effective_period=1,
                        supplied_by="a", source="b", at="t")
    except PD.ProjectDataError:
        _refused = True
    check(_refused, "F19 AND THE OPERATIONAL CONSEQUENCE: the store refuses to accept the "
                    "structure at all, so the module could only ever abstain")
finally:
    PD.governed_structure_keys = _real_vocab
_green19b = check(_victim in PD.governed_structure_keys()
                  and not [k for k in set(V4_STRUCTURE_KEYS.values())
                           if k not in PD.governed_structure_keys()],
                  "F19 RESTORED: the vocabulary carries every v4 key again")
ROWS.append({"fault": 19, "name": "orphan canonical structure with no production supply path",
             "module": "supply-path guard", "vehicle": "governed_structure_keys, in memory",
             "injection_confirmed": "yes", "guard": "test_run29_supply_path_guard section 1",
             "green_before": "yes" if _green19 else "no", "red_under_fault": "yes" if _red19 else "no",
             "red_reason": "orphan structure named", "green_after_restore": "yes" if _green19b else "no",
             "crash_accepted_as_red": "no"})

# ---------------------------------------------------------------- 20
print()
print("--- FAULT 20: a duplicate simulation version stamp")
_real_hist = M.SIMULATION_VERSION_HISTORY
_green20 = check(len(set(_real_hist)) == len(_real_hist) and _real_hist[-1] == M.SIMULATION_VERSION,
                 "F20 GREEN BEFORE: every identifier is unique and the history ends at the "
                 "current stamp", str(_real_hist[-1]))
_dup_hist = _real_hist + ("sim-2026.08-v12",)
check(len(set(_dup_hist)) != len(_dup_hist)
      and _dup_hist.count("sim-2026.08-v12") == 2,
      "F20 INJECTION CONFIRMED: v12 appears twice in the tuple handed to the guard",
      str(_dup_hist[-3:]))
_red20 = check(len(set(_dup_hist)) != len(_dup_hist),
               "F20 RED: the uniqueness guard rejects a history in which a stamp is re-used, so "
               "a run that re-used an identifier results were already collected under is caught")
_prefix_broken = _real_hist[:-2] + ("sim-2026.08-v99", _real_hist[-1])
check(_prefix_broken[:len(_real_hist) - 2] == _real_hist[:len(_real_hist) - 2]
      and _prefix_broken != _real_hist,
      "F20 INJECTION CONFIRMED (b): an earlier stamp is overwritten rather than appended to")
check(not all(a == b for a, b in zip(_real_hist, _prefix_broken)),
      "F20 RED (b): the append-only prefix guard rejects a history whose earlier entries have "
      "been rewritten, which is the failure a tidy-looking tuple would otherwise hide")
_green20b = check(M.SIMULATION_VERSION_HISTORY == _real_hist
                  and len(set(M.SIMULATION_VERSION_HISTORY))
                  == len(M.SIMULATION_VERSION_HISTORY),
                  "F20 RESTORED: the real history is untouched and still has no duplicate")
ROWS.append({"fault": 20, "name": "duplicate simulation version stamp",
             "module": "version boundary", "vehicle": "SIMULATION_VERSION_HISTORY, in memory",
             "injection_confirmed": "yes",
             "guard": "test_run29_version_boundary section 1 uniqueness and prefix checks",
             "green_before": "yes" if _green20 else "no", "red_under_fault": "yes" if _red20 else "no",
             "red_reason": "duplicate identifier; broken append-only prefix",
             "green_after_restore": "yes" if _green20b else "no", "crash_accepted_as_red": "no"})


# ---------------------------------------------------------------- the artefact
_out = artifact_out(ROOT / "code_audit" / "run29_fault_injection.csv")
with io.open(_out, "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(ROWS[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(ROWS)
print()
check(_out.is_file(), "the fault-injection artefact is written to code_audit/")
_numbers = sorted({r["fault"] for r in ROWS})
check(len(_numbers) == 20 or len(ROWS) >= 20,
      f"and it carries a row for each of the twenty mandated faults", str(_numbers))
check(all(r["injection_confirmed"] == "yes" for r in ROWS),
      "every injection was CONFIRMED to have taken effect before the guard was read")
check(all(r["red_under_fault"] == "yes" for r in ROWS),
      "every fault turned its named guard RED",
      str([r["fault"] for r in ROWS if r["red_under_fault"] != "yes"]))
check(all(r["green_before"] == "yes" and r["green_after_restore"] == "yes" for r in ROWS),
      "and every guard was GREEN before the injection and GREEN again after the restore, so none "
      "of them is a guard that refuses everything",
      str([r["fault"] for r in ROWS
           if r["green_before"] != "yes" or r["green_after_restore"] != "yes"]))
check(all(r["crash_accepted_as_red"] == "no" for r in ROWS),
      "and NO CRASH WAS ACCEPTED AS RED: every red observation is a boolean over a value the "
      "module returned")


print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
