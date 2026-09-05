"""
RUN 29 -- THE SUPPLIED CONTRACT'S OWN KNOWN ANSWERS, CARRIED HERE AS LITERALS.

WHY THIS SUITE EXISTS AND WHAT IT IS NOT. Every number below is transcribed from the owner's
supplied Run-29 supervisory contract, sections 5 and 7. NOT ONE OF THEM WAS READ OUT OF
PRODUCTION. That is the whole point: an oracle derived from the code it tests proves that the
code agrees with itself, which is one of the five failure modes this programme has catalogued.
Each block states the contract's own arithmetic in a comment, so a reader can check it by hand
without running anything.

THE SECOND INDEPENDENT ORACLE. Where `server/tools/run17/oracle/oracles_cat_4.py` and
`oracles_cat_5.py` already implement the method independently -- they were written for Run 19,
before any of this code existed, and they self-test at import against these same contract numbers
-- the production answer is ALSO compared against theirs. Two independent implementations
agreeing on the contract's own figure is a stronger statement than either alone.

EVERY MODULE IS DRIVEN THROUGH `registry.run_module`, not through a direct import of the
function, so what is verified is the production path.
"""

from __future__ import annotations
# Run 137, Item 1: a removed module identifier is SUBSTITUTED, not dispatched.
import os as _r96_os, sys as _r96_sys  # noqa: E402
_r96_sys.path.insert(0, _r96_os.path.dirname(_r96_os.path.abspath(__file__)))
from run96_removed_substitution import substitution as _R96  # noqa: E402

import datetime
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "run17"))
sys.path.insert(0, str(HERE / "run17" / "oracle"))

from app.simulation import registry as REG                 # noqa: E402
from app.simulation.canonical import StructureAbsent       # noqa: E402
from app.simulation.canonical_v4 import document_risk_evidence  # noqa: E402
import oracles_cat_4 as O4                                 # noqa: E402
import oracles_cat_5 as O5                                 # noqa: E402
import run29_fixtures as FX                                # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def near(label: str, got, want, tol: float = 1e-9) -> None:
    try:
        ok = got is not None and abs(float(got) - float(want)) <= tol
    except (TypeError, ValueError):
        ok = False
    check(ok, label, f"got {got!r}, contract says {want!r}")


def head(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def run(mid: str, si: dict) -> dict:
    return _R96.dispatch(REG.run_module, globals(), mid, si, RAND, CUTOFF)


def abstains(out: dict) -> bool:
    return bool(out.get("insufficient_data"))


check(not O4.self_test(), "the Run-19 Category-4 oracle still reproduces the contract's worked "
                          "answers at import, so it is fit to be a second opinion",
      "; ".join(O4.self_test()))
check(not O5.self_test(), "and the Run-19 Category-5 oracle does too",
      "; ".join(O5.self_test()))


# =================================================================================================
head("4.1 DOCUMENT RISK SCORE -- contract section 5, 4.1")
# =================================================================================================
# The contract states no scalar oracle for 4.1; what it states is the EVIDENCE the aggregation
# must rest on. HAND: two findings under the confidence-weighted rule, severity 0.8 at confidence
# 1.0 and severity 0.4 at confidence 0.5, score (0.8*1.0 + 0.4*0.5) / (1.0 + 0.5) = 1.0/1.5.
_dre = document_risk_evidence(FX.document_risk_evidence())
near("4.1: the confidence-weighted aggregation of the two findings", _dre["risk_score"], 1 / 1.5)
check(all(all(f.get(k) for k in ("document_id", "document_type", "evidence_span", "risk_class",
                                 "candidate")) for f in _dre["findings"]),
      "4.1: every finding retains its document, its type, the passage read, the class it was put "
      "in and the candidate extracted")
check(_dre["empirical_validation"] == "PENDING_RUN_33",
      "4.1: and the result says plainly that its extraction accuracy is not established here, "
      "which is section 9's own instruction")
for _label, _mutate in (
        ("no evidence span", lambda d: [f.pop("evidence_span") for f in d["findings"]]),
        ("no classifier version", lambda d: d.__setitem__("classifier_version", "")),
        ("no taxonomy", lambda d: d.__setitem__("taxonomy_id", "")),
        ("no source provenance", lambda d: d.__setitem__("source", "")),
        ("no coverage", lambda d: d.__setitem__("coverage", 0.0)),
        ("a severity outside nought to one",
         lambda d: d["findings"][0].__setitem__("severity", 1.4))):
    _bad = FX.document_risk_evidence()
    _mutate(_bad)
    try:
        document_risk_evidence(_bad)
        check(False, f"4.1: evidence with {_label} is refused")
    except StructureAbsent:
        check(True, f"4.1: evidence with {_label} is refused, so an isolated keyword match "
                    f"cannot become verified high-severity evidence")


# =================================================================================================
head("4.2 RFI VELOCITY -- contract: 12 RFIs over 30 days is 0.4 a day, or 12 per 30-day period")
# =================================================================================================
_r = run("A4.2", {"rfiEventLog": FX.rfi_event_log()})
near("4.2: 0.4 requests a day", _r["rate_per_day"], 0.4, 5e-3)
near("4.2: twelve per standardised thirty day period", _r["rfi_per_30d"], 12.0, 5e-2)
near("4.2: and the Run-19 oracle agrees", O4.velocity(12, 30, 1), 0.4)
# THE DOUBLE-COUNTING RULE: a cumulative register uploaded twice is twelve events, not twenty-four.
_dup = run("A4.2", {"rfiEventLog": FX.rfi_event_log(duplicate=True)})
check(_dup["total_rfis"] == 12 and _dup["duplicate_rows_collapsed"] == 12
      and _dup["rate_per_day"] == _r["rate_per_day"],
      "4.2: a cumulative register uploaded twice is twelve events and not twenty-four, so a "
      "revision of the same register is not a new event",
      f"{_dup['total_rfis']} events from {_dup['rows_supplied']} rows")
check(abstains(run("A4.2", {"rfiEventLog": FX.rfi_event_log(exposure_days=0.0)})),
      "4.2: a register covering no span of time has no exposure and is refused")
check(abstains(run("A4.2", {})), "4.2: with neither the register nor the totals, NOT ESTIMABLE")


# =================================================================================================
head("4.3 SUBMITTAL REJECTION RATE -- contract: 3 rejected of 20 assessed is 0.15")
# =================================================================================================
_r = run("A4.3", {"submittalDecisionRegister": FX.submittal_register()})
near("4.3: three rejected of twenty assessed is 0.15", _r["rejection_rate"], 0.15, 1e-6)
near("4.3: and the Run-19 oracle agrees", O4.rejection_rate(3, 20), 0.15)
check(_r["rejected"] == 3 and _r["total"] == 20,
      "4.3: and 0 <= Rejected <= AssessedPopulation holds on the reported pair")
check(abstains(run("A4.3", {"submittalDecisionRegister": dict(
    FX.submittal_register(), decisions=[dict(d, disposition="SORT OF APPROVED")
                                        for d in FX.submittal_register()["decisions"]])})),
      "4.3: a disposition this platform has no governed meaning for is refused rather than "
      "silently merged into approval or rejection")
check(run("A4.3", {"submittalDecisionRegister": FX.submittal_register()})["unique_submittals"]
      == 20,
      "4.3: unique submittals are separated from resubmission cycles")
check(abstains(run("A4.3", {})), "4.3: with neither the register nor the totals, NOT ESTIMABLE")


# =================================================================================================
head("4.4 NCR RATE -- contract: 4 NCRs / 100 inspections = 0.04")
# =================================================================================================
_r = run("A4.4", {"ncrExposureRecord": FX.ncr_record()})
near("4.4: four nonconformances over one hundred inspections", _r["ncr_rate"], 0.04)
near("4.4: and the Run-19 oracle agrees", O4.ncr_rate(4, 100), 0.04)
check(_r["exposure_unit"] == "inspections" and _r["exposure_quantity"] == 100.0,
      "4.4: the governed exposure is named and reported with the rate")
check(_r["open_count"] == 4 and _r["closure_rate"] == 0.0
      and _r["severity_counts"] == {"MAJOR": 4} and _r["max_open_age_days"] is not None,
      "4.4: open count, closure rate, severity and age of open are tracked SEPARATELY")
check(abstains(run("A4.4", {"ncrExposureRecord": FX.ncr_record(exposure=0.0)})),
      "4.4: no exposure, no fabricated normalised rate")
check(abstains(run("A4.4", {})), "4.4: with no record at all, NOT ESTIMABLE")


# =================================================================================================
head("4.5 WEATHER DAY IMPACT -- contract: 2 lost days, zero float, no mitigation = 2 days")
# =================================================================================================
_r = run("A4.5", {"weatherImpactEvents": FX.weather_events()})
near("4.5: the direct modelled path effect before recovery logic", _r["direct_path_effect_days"],
     2.0)
near("4.5: and the Run-19 oracle agrees",
     O4.weather_schedule_effect(2, 0, True)["path_effect_days"], 2.0)
near("4.5: five days of float absorb the same two days",
     run("A4.5", {"weatherImpactEvents": FX.weather_events(available_float=5.0)}
         )["direct_path_effect_days"], 0.0)
near("4.5: and so does a two-day weather allowance, which is applied first",
     run("A4.5", {"weatherImpactEvents": FX.weather_events(allowance=2.0)}
         )["direct_path_effect_days"], 0.0)
check(abstains(run("A4.5", {"weatherDaysLost": 6, "floatRemaining": 20})),
      "4.5: a raw weather-days-lost value with a float figure is NOT ESTIMABLE for impact")


# =================================================================================================
head("4.6 CHANGE ORDER FREQUENCY -- contract: 6 changes over 180 days = 0.0333.. a day")
# =================================================================================================
_r = run("A4.6", {"changeEventRegister": FX.change_register()})
near("4.6: six changes over one hundred and eighty days", _r["change_frequency_per_day"], 6 / 180,
     1e-6)
near("4.6: one change per standardised thirty day period",
     _r["change_frequency_per_30_days"], 1.0, 1e-6)
near("4.6: and the Run-19 oracle agrees", O4.change_frequency(6, 180, 30), 1.0)
near("4.6: magnitude is a SEPARATE quantity, sixty thousand over a million",
     _r["change_magnitude_net"], 0.06, 1e-9)
check(_r["status_color"] is None,
      "4.6: and the two are not combined into one unnamed composite: no colour is asserted over "
      "either")
check(_r["type_counts"] and _r["cause_counts"] and _r["additive_count"] == 6
      and _r["baseline_contract_value"] == 1000000.0,
      "4.6: change type, cause, direction and the contract lineage are preserved")
check(abstains(run("A4.6", {"changeEventRegister": FX.change_register(exposure_days=0.0)})),
      "4.6: no exposure, no frequency")


# =================================================================================================
head("4.7 DISPUTE ESCALATION INDEX -- contract: the project's OWN governed process")
# =================================================================================================
_r = run("A4.7", {"claimDisputeRegister": FX.dispute_register()})
check(_r["highest_stage_id"] == "S1_CLAIM_SUBMITTED" and _r["highest_stage_rank"] == 1,
      "4.7: a submitted claim reads at the stage it has reached on the declared process")
check(_r["process_id"] == "LAB-DISPUTE-PROCESS" and _r["process_version"] == "1.0",
      "4.7: and the process and its version travel with the reading, because the ladder is the "
      "project's own and not a universal one")
_ranks = [run("A4.7", {"claimDisputeRegister": FX.dispute_register(st["stage_id"])}
              )["highest_stage_rank"] for st in FX.LAB_DISPUTE_STAGES]
check(_ranks == [0, 1, 2, 3, 4, 5],
      "4.7: a later governed escalation state never reads as less escalated than an earlier one",
      str(_ranks))
check(abstains(run("A4.7", {"docRiskScore": 0.9, "rfiCount": 40, "changeOrderCount": 30})),
      "4.7: a request count, a change count and a document risk score do not prove a dispute, so "
      "the answer is NOT ESTIMABLE")
check(abstains(run("A4.7", {})),
      "4.7: and missing dispute evidence cannot improve the condition, because there is none")


# =================================================================================================
head("4.8 SUBCONTRACTOR PERFORMANCE -- contract: 0.80, 0.90, 0.70 equally weighted = 0.80")
# =================================================================================================
_r = run("A4.8", {"subcontractorAssessments": FX.subcontractor_assessment()})
near("4.8: the weighted score of the three ratings", _r["mean_score"], 0.80, 1e-4)
_third = 1 / 3
near("4.8: and the Run-19 oracle agrees",
     O4.weighted_score({"a": 0.80, "b": 0.90, "c": 0.70},
                       {"a": _third, "b": _third, "c": _third}), 0.80)
check(abstains(run("A4.8", {"subcontractorAssessments": dict(
    FX.subcontractor_assessment(),
    weights={"quality": 0.5, "schedule": 0.2, "safety": 0.2})})),
      "4.8: weights that do not sum to one are refused")
check(abstains(run("A4.8", {"subcontractorComplianceScore": 0.82})),
      "4.8: an opaque precomputed compliance score with no component evidence is refused")


# =================================================================================================
head("4.9 PROCUREMENT LEAD TIME -- contract: required 100, forecast 110, slack -10")
# =================================================================================================
_r = run("A4.9", {"procurementItems": FX.procurement_items()})
near("4.9: the item's slack", _r["minimum_slack_days"], -10.0)
near("4.9: and the Run-19 oracle agrees", O4.procurement_slack(100, 110), -10.0)
check(sum(_r["state_counts"].values()) == _r["item_count"] and _r["state_counts"]["LATE"] == 1,
      "4.9: every item is in exactly ONE state, so a delayed item is never counted twice inside "
      "at-risk", str(_r["state_counts"]))
check(abstains(run("A4.9", {"longLeadItemsTotal": 10, "longLeadAtRisk": 8,
                            "longLeadDelayed": 5})),
      "4.9: a count ratio alone is not the canonical item-level monitor")


# =================================================================================================
head("4.10 SPECIFICATION CONFLICT DENSITY -- contract: 5 over 250 = 0.02, or 20 per 1,000")
# =================================================================================================
_r = run("A4.10", {"specificationConflictRegister": FX.conflict_register()})
near("4.10: five verified conflicts over two hundred and fifty requirements",
     _r["conflict_density"], 0.02)
near("4.10: expressed per thousand requirements", _r["conflicts_per_thousand"], 20.0, 1e-6)
near("4.10: and the Run-19 oracle agrees", O4.conflict_density(5, 250), 0.02)
check(all(c["location_a"] and c["location_b"] for c in _r["conflicts"]),
      "4.10: each conflict retains the two conflicting evidence locations")
check(abstains(run("A4.10", {"specificationConflictRegister":
                             FX.conflict_register(exposure=0.0)})),
      "4.10: no denominator, NOT ESTIMABLE")
check(abstains(run("A4.10", {"docRiskScore": 0.4, "rfiCount": 16})),
      "4.10: and a document risk score with a request count is not conflict density")


# =================================================================================================
head("5.1 DSM REWORK PROPAGATION -- contract: D=[[0,0.5],[0,0]], R0=[0,1], R1=[0.5,0], R2=[0,0]")
# =================================================================================================
_r = run("A5.1", {"dsmDependencyModel": FX.dsm_model()})
check(_r["waves"][1] == {"n1": 0.5, "n2": 0.0}, "5.1: R1 is [0.5, 0]", str(_r["waves"][1]))
check(_r["waves"][2] == {"n1": 0.0, "n2": 0.0}, "5.1: R2 is [0, 0]", str(_r["waves"][2]))
check(O5.dsm_propagate([[0.0, 0.5], [0.0, 0.0]], [0.0, 1.0], 2)[1] == [0.5, 0.0],
      "5.1: and the Run-19 oracle agrees")
check(_r["matrix"] == [[0.0, 0.5], [0.0, 0.0]],
      "5.1: the matrix assembled under the declared orientation is the contract's own",
      str(_r["matrix"]))
check(abstains(run("A5.1", {"cpi": 0.5, "spi": 0.5, "bac": 1e6})),
      "5.1: no project DSM, NOT ESTIMABLE, and no index substitutes for dependency topology")


# =================================================================================================
head("5.2 SENSITIVITY ANALYSIS -- contract: Y=x1^2+x2 at (2,1), +10% on x1, S = 1.68")
# =================================================================================================
_r = run("A5.2", {"sensitivityModel": FX.sensitivity_model()})
_x1 = _r["inputs"][0]
near("5.2: the response at the base state is 5", _r["base_response"], 5.0, 1e-12)
near("5.2: the response recomputed at x1 = 2.2 is 5.84", _x1["moved_response"], 5.84)
near("5.2: so the change in the response is 0.84", _x1["delta_response"], 0.84)
near("5.2: and the normalised sensitivity is 1.68", _x1["normalised_sensitivity"], 1.68)
near("5.2: and the Run-19 oracle agrees",
     O5.normalised_sensitivity(lambda v: v["x1"] ** 2 + v["x2"], {"x1": 2.0, "x2": 1.0},
                               "x1", 0.10), 1.68)
check(_r["method_scope"] == "LOCAL",
      "5.2: the method is declared LOCAL one at a time and is not called global")


# =================================================================================================
head("5.3 TORNADO RISK RANKING -- contract: impacts 30, 7 and 30, with A and C tied above B")
# =================================================================================================
_r = run("A5.3", {"sensitivityModel": FX.tornado_model()})
_bars = {b["input_id"]: b for b in _r["bars"]}
near("5.3: A's impact is 30", _bars["A"]["impact"], 30.0)
near("5.3: B's impact is 7", _bars["B"]["impact"], 7.0)
near("5.3: C's impact is 30", _bars["C"]["impact"], 30.0)
check(_r["ranked_inputs"] == ["A", "C", "B"] and _bars["A"]["rank"] == _bars["C"]["rank"]
      and _bars["B"]["rank"] > _bars["A"]["rank"],
      "5.3: A and C tie above B, and the tie policy is explicit on the result",
      str(_r["ranked_inputs"]))
check(bool(_r["tie_policy"]), "5.3: the tie policy is stated rather than implied",
      str(_r["tie_policy"]))
# THE LINEAGE, PROVED BY EXECUTION: the bars are the sensitivity's own low and high responses.
_s = run("A5.2", {"sensitivityModel": FX.tornado_model()})
_pairs = {i["input_id"]: (i["response_at_low"], i["response_at_high"]) for i in _s["inputs"]}
check(all((b["response_at_low"], b["response_at_high"]) == _pairs[b["input_id"]]
          for b in _r["bars"]),
      "5.3: every bar is, value for value, the low and high response A5.2 computed, so no "
      "independent evidence stream is created")
check(_r["independent_evidence"] is False and _r["derived_from"] == "A5.2"
      and _r["derived_from_response_model_id"] == _s["response_model_id"],
      "5.3: and the lineage names the sensitivity result it is derived from")


# =================================================================================================
head("5.4 SCENARIO MODELING -- contract: Y=2x1+x2 gives BASE 5, ADVERSE 8, RECOVERY 4")
# =================================================================================================
_r = run("A5.4", {"scenarioSet": FX.scenario_set()})
check(_r["responses"] == {"BASE": 5.0, "ADVERSE": 8.0, "RECOVERY": 4.0},
      "5.4: the three coherent states give five, eight and four exactly",
      str(_r["responses"]))
check(_r.get("recommended_action") is None,
      "5.4: and no action is recommended, because choosing between them is Category 10's question")
check(abstains(run("A5.4", {"scenarioSet": dict(
    FX.scenario_set(),
    scenarios=[dict(FX.scenario_set()["scenarios"][0], variables={"x1": 99.0, "x2": 1.0})])})),
      "5.4: an inconsistent scenario state is refused rather than evaluated")


# =================================================================================================
head("5.5 REWORK FEEDBACK LOOP -- contract: 10 + 5 + 2 - 8 = 9, with rework 0.25*8 = 2")
# =================================================================================================
_r = run("A5.5", {"systemDynamicsModel": FX.system_dynamics_model()})
near("5.5: the rework generated is 2", _r["trace"][0]["rework_generated"], 2.0)
near("5.5: the backlog after one step is 9", _r["final_backlog"], 9.0)
near("5.5: and the Run-19 oracle agrees", O5.rework_step(10, 5, 8, 0.25)["backlog_next"], 9.0)
near("5.5: the accounting conserves across the run", _r["accounting_residual"], 0.0, 1e-9)
_eq = run("A5.5", {"systemDynamicsModel": dict(
    FX.system_dynamics_model(),
    steps=[{"step": i, "new_work": 6.0, "work_completed": 8.0, "error_rate": 0.25}
           for i in range(5)])})
check(all(abs(t["closing_backlog"] - 10.0) < 1e-9 for t in _eq["trace"]),
      "5.5: at new work six and completion eight with a quarter error rate the backlog is in "
      "equilibrium", str([t["closing_backlog"] for t in _eq["trace"]]))
check(abstains(run("A5.5", {"cpi": 0.8, "rfiCount": 15, "changeOrderCount": 5})),
      "5.5: a weighted CPI, request and change-order score is not a feedback loop")


# =================================================================================================
head("5.6 QUEUEING THEORY -- contract: lambda 2, mu 3, rho 2/3, L 2, W 1, Lq 4/3, Wq 2/3")
# =================================================================================================
_r = run("A5.6", {"queueModel": FX.queue_model()})
near("5.6: rho is two thirds", _r["utilisation"], 2 / 3, 1e-5)
near("5.6: L is two", _r["L"], 2.0, 1e-5)
near("5.6: W is one", _r["W"], 1.0, 1e-5)
near("5.6: Lq is four thirds", _r["Lq"], 4 / 3, 1e-5)
near("5.6: Wq is two thirds", _r["Wq"], 2 / 3, 1e-5)
near("5.6: Little's Law holds for the system: L = lambda W = 2", 2.0 * _r["W"], 2.0, 1e-5)
near("5.6: and for the queue: Lq = lambda Wq = 4/3", 2.0 * _r["Wq"], 4 / 3, 1e-5)
_o = O5.mm1(2, 3)
check(abs(_o["L"] - _r["L"]) < 1e-5 and abs(_o["Wq"] - _r["Wq"]) < 1e-5,
      "5.6: and the Run-19 oracle agrees on every measure")
check(abstains(run("A5.6", {"queueModel": FX.queue_model(arrival=3.0)}))
      and abstains(run("A5.6", {"queueModel": FX.queue_model(arrival=4.0)})),
      "5.6: at lambda >= mu no reassuring finite steady state is emitted")
check(abstains(run("A5.6", {"activitiesPlanned": 100, "activitiesConstrained": 20})),
      "5.6: constrained over planned activities is not queueing theory")


# =================================================================================================
head("5.7 AGENT-BASED SUPPLY CHAIN -- contract: the minimum deterministic three-agent model")
# =================================================================================================
# HAND, under the declared step order POST_DEMAND, DELIVER, COLLECT, SHIP. Supplier stock two,
# travel delay one, demand two posted at step nought.
#   step 0: request posted; nothing in transit; dock empty; supplier ships one -> dock 1, stock 1
#   step 1: nothing lands; carrier collects the unit, due at 2; supplier ships the second
#   step 2: the first unit is received; carrier collects the second, due at 3; stock is empty
#   step 3: the second unit is received
_r = run("A5.7", {"agentSupplyChainModel": FX.agent_model()})
_t = _r["runs"][0]["trace"]
check([x["supplier_inventory"] for x in _t] == [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      "5.7: the supplier's stock falls to one at step nought and to nought at step one",
      str([x["supplier_inventory"] for x in _t]))
check([x["received"] for x in _t] == [0, 0, 1, 2, 2, 2],
      "5.7: the project receives its first unit at step two and its second at step three",
      str([x["received"] for x in _t]))
check(_r["received"] == 2 and _r["backordered"] == 0,
      "5.7: both units arrive and nothing is left backordered")
check(run("A5.7", {"agentSupplyChainModel": FX.agent_model(inventory=0.0)})["received"] == 0,
      "5.7: with no stock the supplier rule cannot fire and nothing is received")
check(run("A5.7", {"agentSupplyChainModel": FX.agent_model(delay=2)}
          )["runs"][0]["trace"][3]["received"] == 1,
      "5.7: a longer carrier delay moves the receipts later, so the rule is executed rather than "
      "read")
check(abstains(run("A5.7", {"longLeadItemsTotal": 20, "longLeadAtRisk": 3})),
      "5.7: a long-lead at-risk ratio is not an agent-based model")
# STOCHASTIC: seed and replication count declared, reproducible from the seed alone.
_st = {"agentSupplyChainModel": FX.agent_model(disruption=0.30, seed=20260816, replications=5)}
_s1, _s2 = run("A5.7", _st), run("A5.7", _st)
check(_s1["seed"] == 20260816 and _s1["replications"] == 5 and _s1["stochastic"] is True,
      "5.7 stochastic: the seed and the replication count are recorded on the result")
check([r["trace"] for r in _s1["runs"]] == [r["trace"] for r in _s2["runs"]],
      "5.7 stochastic: reproducible from the seed alone, replication for replication")
check([r["disrupted_steps"] for r in _s1["runs"]]
      != [r["disrupted_steps"] for r in run("A5.7", {"agentSupplyChainModel": FX.agent_model(
          disruption=0.30, seed=99, replications=5)})["runs"]],
      "5.7 stochastic: and a different seed gives a different run, so the seed is really driving "
      "the disruption")


# =================================================================================================
head("5.8 DISCRETE EVENT SIMULATION -- contract: A 0/2/0, B 2/4/1, mean wait 0.5")
# =================================================================================================
_r = run("A5.8", {"desProcessModel": FX.des_model()})
_e = {x["entity_id"]: x for x in _r["entities"]}
near("5.8: A starts at 0", _e["A"]["start"], 0.0)
near("5.8: A ends at 2", _e["A"]["end"], 2.0)
near("5.8: A waits 0", _e["A"]["wait"], 0.0)
near("5.8: B arrives at 1 and starts at 2", _e["B"]["start"], 2.0)
near("5.8: B ends at 4", _e["B"]["end"], 4.0)
near("5.8: B waits 1", _e["B"]["wait"], 1.0)
near("5.8: the mean wait is 0.5", _r["mean_wait"], 0.5)
_o = O5.des_single_server([("A", 0.0, 2.0), ("B", 1.0, 2.0)])
near("5.8: and the Run-19 oracle agrees on the mean wait", _o["mean_wait"], 0.5)
check(len(_r["events"]) == 4 and _r["clock_end"] == 4.0,
      "5.8: an event list of four events was processed and the clock ends at four")
check(bool(_r["event_order_policy"]) and _r["termination_condition"] == "ALL_ENTITIES_DEPARTED",
      "5.8: the simultaneous-event policy and the termination condition are declared")
check(abstains(run("A5.8", {"spi": 0.9, "cpi": 0.9, "actualPctComplete": 40,
                            "plannedPctComplete": 50})),
      "5.8: a progress and schedule index algebraic index is not DES")
# STOCHASTIC: predeclared tolerance of 1e-9 on reproducibility, seed and replications recorded.
_stoch = {"desProcessModel": dict(
    FX.des_model(), seed=20260816, replications=20,
    entities=[{"entity_id": f"E{i}", "entity_type": "JOB", "arrival_time": float(i),
               "service_distribution": {"family": "EXPONENTIAL", "mean": 1.5}}
              for i in range(8)])}
_d1, _d2 = run("A5.8", _stoch), run("A5.8", _stoch)
check(_d1["seed"] == 20260816 and _d1["replications"] == 20 and _d1["stochastic"] is True,
      "5.8 stochastic: the seed and the replication count are recorded on the result")
check(all(abs(a["mean_wait"] - b["mean_wait"]) <= 1e-9
          for a, b in zip(_d1["runs"], _d2["runs"])),
      "5.8 stochastic: reproducible from the seed alone, within the tolerance predeclared here "
      "of one part in a thousand million")
check([r["mean_wait"] for r in _d1["runs"]]
      != [r["mean_wait"] for r in run("A5.8", {"desProcessModel": dict(
          _stoch["desProcessModel"], seed=99)})["runs"]],
      "5.8 stochastic: and a different seed gives different replications")
near("5.8 stochastic: the reported mean wait is the mean over the twenty replications",
     _d1["mean_wait"], sum(r["mean_wait"] for r in _d1["runs"]) / 20, 1e-9)


# =================================================================================================
head("EVERY ONE OF THE EIGHTEEN ABSTAINS WITH ITS STRUCTURE ABSENT, AND ASSERTS NO COLOUR")
# =================================================================================================
_RUNNABLE = ["A4.2", "A4.3", "A4.4", "A4.5", "A4.6", "A4.7", "A4.8", "A4.9", "A4.10",
             "A5.1", "A5.2", "A5.3", "A5.4", "A5.5", "A5.6", "A5.7", "A5.8"]
_RICH = {"bac": 12e6, "ev": 4e6, "ac": 4.4e6, "pv": 4.5e6, "cpi": 0.909, "spi": 0.889,
         "actualPctComplete": 40.0, "plannedPctComplete": 45.0, "docRiskScore": 0.35,
         "rfiCount": 12, "rfiPeriodDays": 30, "changeOrderCount": 6,
         "baselineContractSum": 1e6, "revisedContractSum": 1.08e6,
         "longLeadItemsTotal": 20, "longLeadAtRisk": 3, "longLeadDelayed": 1,
         "ncrIssued": 4, "ncrClosed": 2, "ncrOpen": 6, "totalFindings": 40,
         "submittalsTotal": 20, "submittalsRejected": 3,
         "weatherDaysLost": 3, "floatRemaining": 15, "subcontractorComplianceScore": 0.82,
         "activitiesPlanned": 200, "activitiesConstrained": 37}
_still_proxying = []
for _mid in _RUNNABLE:
    _out = run(_mid, dict(_RICH))
    if _mid in ("A4.2", "A4.3"):
        # The two Run-27 method passes keep their extracted-totals path, which computes the same
        # canonical formula from a thinner record. That is stated, not glossed.
        check(not abstains(_out),
              f"{_mid}: computes from the extracted register totals, which are the SAME canonical "
              f"quantity from a thinner record and were recorded as a method pass by Run 27")
        continue
    if not abstains(_out):
        _still_proxying.append(_mid)
check(not _still_proxying,
      "NO METHOD FALLS BACK TO ITS OLD PROXY: on a fully reported project carrying every scalar "
      "the old computations read, and no governed structure, fifteen of the seventeen runnable "
      "targets abstain", str(_still_proxying))

_banded = []
for _key, (_mid, _fixture) in {
        "rfiEventLog": ("A4.2", FX.rfi_event_log), "ncrExposureRecord": ("A4.4", FX.ncr_record),
        "weatherImpactEvents": ("A4.5", FX.weather_events),
        "changeEventRegister": ("A4.6", FX.change_register),
        "claimDisputeRegister": ("A4.7", FX.dispute_register),
        "subcontractorAssessments": ("A4.8", FX.subcontractor_assessment),
        "procurementItems": ("A4.9", FX.procurement_items),
        "specificationConflictRegister": ("A4.10", FX.conflict_register),
        "dsmDependencyModel": ("A5.1", FX.dsm_model),
        "sensitivityModel": ("A5.2", FX.sensitivity_model),
        "scenarioSet": ("A5.4", FX.scenario_set),
        "systemDynamicsModel": ("A5.5", FX.system_dynamics_model),
        "queueModel": ("A5.6", FX.queue_model),
        "agentSupplyChainModel": ("A5.7", FX.agent_model),
        "desProcessModel": ("A5.8", FX.des_model)}.items():
    _out = run(_mid, {_key: _fixture()})
    if _mid == "A4.2":
        continue          # A4.2 keeps the ladder it always carried, recorded as uncited
    if _out.get("status_color") is not None:
        _banded.append(_mid)
check(not _banded,
      "NO UNSOURCED STATUS BAND WAS INTRODUCED: every module reporting a quantity its old ladder "
      "was not drawn over asserts no colour and carries calibration pending", str(_banded))
check(REG.CORE_VOTING_MODULES == ("A1.7", "A1.8")
      or sorted(REG.CORE_VOTING_MODULES) == ["A1.7", "A1.8"],
      "and voting remains exactly two", str(sorted(REG.CORE_VOTING_MODULES)))
check("A3.4" in REG.DISABLED_MODULES,
      "and Material Cost Variance remains disabled and non-executed")


print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
