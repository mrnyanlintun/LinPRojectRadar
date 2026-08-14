"""
RUN 19 -- Category 5, system dynamics and complexity. Eight scientific targets.

Controlling theory: the committed supervisory specification, section 14. Oracles come from
run17/oracle/oracles_cat_5.py, self proved at import: the closed-form M/M/1 results with
Little's Law, a hand event schedule for the discrete event case, and an agent model whose state
history is PRODUCED by replaying its behaviour rules rather than supplied.

TEST AND AUDIT ONLY. Production output is never the oracle.
"""

from __future__ import annotations

import datetime
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE / "run17"))
sys.path.insert(0, str(HERE / "run17" / "oracle"))

from audit_harness import (Audit, RESULT_HEADER, write_results,  # noqa: E402
                           oracle_gate)
from population import population                                # noqa: E402
from app.simulation import registry as REG                       # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731

KNOWN_DEFECTS = {
    # RUN 20 CYCLE 9 REPAIRED BOTH 5.2 PROPOSITIONS, so they are removed from the register rather
    # than left to go stale. Only the cost-index driver was ever perturbed; the other two were a
    # halved index deviation and a raw risk share, ranked against it on an uncited scaling. The
    # module now reports the one driver it perturbs and reports the other two as levels.
    "5.3/output-evaluated-at-low-and-high": "METHOD_LABEL_MISMATCH",
    "5.3/presents-5.2-results": "METHOD_LABEL_MISMATCH",
    "5.4/system-conditions-not-action-choice": "OWNER_DECISION_REQUIRED",
    "5.5/stocks-and-flows": "METHOD_LABEL_MISMATCH",
    "5.6/queueing-model": "CORRECT_PROXY_ONLY",
    "5.7/rules-are-executed": "CORRECT_PROXY_ONLY",
    "5.8/event-schedule": "METHOD_LABEL_MISMATCH",
}

A = Audit("category 5", KNOWN_DEFECTS)
O = oracle_gate(A, "oracles_cat_5")

EVM = {"bac": 1000, "ev": 400, "ac": 500, "pv": 500, "cpi": 0.80, "spi": 0.85,
       "docRiskScore": 0.30, "actualPctComplete": 40, "plannedPctComplete": 50}


def run(code_id: str, si: dict) -> dict:
    return REG.run_module(code_id, si, RAND, CUTOFF)


def abstained(out: dict) -> bool:
    return bool(out.get("insufficient_data")) or out.get("status_color") is None


def source_of(fn: str) -> str:
    src = (HERE.parent / "app" / "simulation" / "models_doc.py").read_text(encoding="utf-8")
    return src.split(f"def {fn}")[1].split("\ndef ")[0]


def gate() -> None:
    A.check("GATE", "the Category 5 oracle reproduces the specification's worked answers",
            not O.self_test(), "; ".join(O.self_test()))
    ids = {t["module_id"] for t in population()}
    for mid in ("5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8"):
        A.check("GATE", f"{mid} is one of the hundred scientific targets", mid in ids)
    for code in ("A5.1", "A5.2", "A5.3", "A5.4", "A5.5", "A5.6", "A5.7", "A5.8"):
        A.check("GATE", f"{code} is non-voting", code not in REG.CORE_VOTING_MODULES)


# =============================================================================================
# 5.1 DSM REWORK PROPAGATION -- specification 14, "5.1"
# =============================================================================================

def m_5_1() -> None:
    D = [[0.0, 0.5], [0.0, 0.0]]
    waves = O.dsm_propagate(D, [0.0, 1.0], 2)
    A.check("5.1", "known-answer: the specification's single-edge matrix propagates a half wave "
                   "to the first element", waves[1] == [0.5, 0.0], str(waves[1]))
    A.check("5.1", "known-answer: the wave dies at the second step", waves[2] == [0.0, 0.0])
    A.check("5.1", "boundary: a zero matrix propagates nothing",
            O.dsm_step([[0.0, 0.0], [0.0, 0.0]], [1.0, 1.0]) == [0.0, 0.0])
    A.check("5.1", "boundary: a disconnected graph leaves each element with only its own seed",
            O.dsm_step([[0.0, 0.0], [0.0, 0.0]], [1.0, 2.0]) == [0.0, 0.0])
    A.check("5.1", "invariant: propagation is linear in the seed, so a doubled initiating wave "
                   "doubles what arrives", O.dsm_step(D, [0.0, 2.0]) == [1.0, 0.0])
    A.check("5.1", "invariant: edge strength is monotone, so a stronger dependency carries more",
            O.dsm_step([[0.0, 0.9], [0.0, 0.0]], [0.0, 1.0])[0]
            > O.dsm_step(D, [0.0, 1.0])[0])
    A.check("5.1", "boundary: a cycle propagates around and back, which is why a stopping policy "
                   "must be declared",
            O.dsm_propagate([[0.0, 1.0], [1.0, 0.0]], [1.0, 0.0], 2)[2] == [1.0, 0.0])

    A.proposition(
        "5.1", "5.1/abstains-without-matrix",
        "with no dependency matrix for the project the module abstains, rather than propagating "
        "a wave through coefficients that are this file's literals",
        all(abstained(run("A5.1", si)) for si in ({}, dict(EVM), {"cpi": 0.5, "rfiCount": 40})))
    A.check("5.1", "missingness: the abstention names the dependency matrix as what is absent",
            "dependency matrix" in str(run("A5.1", {}).get("evidence_metric", "")).lower())
    A.check("5.1", "invariant: no project input can move the result while the matrix is absent",
            len({str(run("A5.1", {"cpi": c, "bac": b}))
                 for c in (0.4, 1.0, 1.6) for b in (10, 10 ** 8)}) == 1)


# =============================================================================================
# 5.2 SENSITIVITY ANALYSIS -- specification 14, "5.2"
# =============================================================================================

def m_5_2() -> None:
    def y(v):
        return v["x1"] ** 2 + v["x2"]
    A.near("5.2", "known-answer: the specification's Y = x1 squared plus x2 at (2,1), perturbed "
                  "ten per cent on x1, has a normalised sensitivity of 1.68",
           O.normalised_sensitivity(y, {"x1": 2.0, "x2": 1.0}, "x1", 0.10), 1.68)
    A.near("5.2", "invariant: an input the output does not depend on has no sensitivity, which "
                  "is what makes the elasticity a meaningful ranking key",
           O.normalised_sensitivity(lambda v: v["x1"], {"x1": 2.0, "x2": 1.0}, "x2", 0.10), 0.0)
    A.check("5.2", "invariant: the normalised sensitivity is dimensionless, so rescaling the "
                   "unit of an input leaves it unchanged, which is what makes two different "
                   "inputs comparable",
            abs(O.normalised_sensitivity(y, {"x1": 2.0, "x2": 1.0}, "x2", 0.10)
                - O.normalised_sensitivity(lambda v: v["x1"] ** 2 + v["x2"] / 1000,
                                           {"x1": 2.0, "x2": 1000.0}, "x2", 0.10)) < 1e-9)

    out = run("A5.2", dict(EVM))
    # RUN 20 CYCLE 9. THE EXPECTED STRUCTURE CHANGED BECAUSE THE DEFECT THIS SUITE RECORDED WAS
    # FIXED, and the fix was the one this suite's own finding recommended: report only the driver
    # that is perturbed. Two of the three "drivers" were never perturbed and could not be -- the
    # estimate at completion is bac over the cost index and is not a function of the schedule
    # index or the document risk score at all -- so ranking three was the defect, not the
    # structure. One perturbed driver is ranked and named; the other two quantities are still
    # reported, under their own names, as levels that are not ranked.
    A.check("5.2", "structure: the perturbed driver is ranked and named, and the two quantities "
                   "that are not sensitivities are reported separately as levels",
            len(out.get("drivers", [])) == 1 and out.get("top_driver") == "CPI"
            and [d["name"] for d in out.get("levels_not_perturbed", [])] == ["SPI", "DocRisk"])
    A.proposition(
        "5.2", "5.2/no-absent-driver-reads-zero",
        "an absent document risk score is required rather than read as a sensitivity of exactly "
        "zero, which would be the strongest possible claim that the driver does not move the "
        "estimate and would demote it to the bottom of the ranking",
        abstained(run("A5.2", {k: v for k, v in EVM.items() if k != "docRiskScore"})))
    A.check("5.2", "invalid input: a document risk score outside nought to one is refused",
            abstained(run("A5.2", {**EVM, "docRiskScore": 30})))
    A.check("5.2", "boundary: the cost index values at which the perturbed division would be "
                   "undefined are refused",
            all(abstained(run("A5.2", {**EVM, "cpi": c})) for c in (0, 0.05, -0.05)))
    A.check("5.2", "boundary: a budget of zero leaves no base estimate to normalise against",
            abstained(run("A5.2", {**EVM, "bac": 0})))
    A.check("5.2", "missingness: all seven inputs are required",
            abstained(run("A5.2", {"cpi": 0.8})))

    drivers = {d["name"]: d["sensitivity"] for d in out["drivers"]}
    # RUN 20 CYCLE 9. EVALUATED LIVE RATHER THAN PINNED TO False. The proposition is tested by
    # moving each ranked driver's input and requiring the reported sensitivity to respond, which
    # is what "perturbed and recomputed" means, and by requiring that nothing is ranked which the
    # estimate is not a function of.
    _moved = run("A5.2", {**EVM, "cpi": EVM["cpi"] * 1.1})
    _all_perturbed = (
        len(out["drivers"]) == 1
        and out["drivers"][0]["name"] == "CPI"
        and _moved["drivers"][0]["sensitivity"] != out["drivers"][0]["sensitivity"]
        and "sensitivity" not in {k for lv in out["levels_not_perturbed"] for k in lv})
    A.proposition(
        "5.2", "5.2/all-drivers-perturbed",
        "every driver ranked is perturbed and the estimate recomputed, which is what "
        "specification 5.2 requires before a quantity may be called a sensitivity",
        _all_perturbed,
        f"only ONE of the three is. The cost index driver genuinely perturbs the index by plus "
        f"and minus 0.05 and recomputes the forecast at completion, which is a real local "
        f"sensitivity. The other two are not perturbed at all: the schedule driver is the "
        f"absolute deviation of the schedule index from one, halved, and the document driver is "
        f"the document risk score itself. Specification 5.2 says in terms not to call current "
        f"badness a sensitivity unless an input is actually perturbed and the output recomputed. "
        f"Observed at the standard input: {drivers}")
    # RUN 20 CYCLE 9. ALSO EVALUATED LIVE. A ranking is commensurable when everything in it is
    # the same kind of quantity. With one perturbed driver ranked and the two levels excluded from
    # the ranking, the band is read from a relative spread of the forecast and from nothing else.
    _commensurable = (len({d.get("method", "") for d in out["drivers"]}) == 1
                      and out["top_sensitivity"] == int(round(
                          out["drivers"][0]["sensitivity"] * 100))
                      and all("level" in lv and "sensitivity" not in lv
                              for lv in out["levels_not_perturbed"]))
    A.proposition(
        "5.2", "5.2/commensurable-ranking",
        "the three driver figures are on a common scale, so ranking them and taking the largest "
        "means something",
        _commensurable,
        "the first driver is a dimensionless relative spread of the forecast, the second is half "
        "an index deviation and the third is a raw risk share. They are three different "
        "quantities, and the 0.5 multiplier on the schedule driver is the only thing setting "
        "their relative standing. Both the reported top driver and the band, which reads the "
        "maximum of the three, are therefore determined by an uncited scaling choice rather than "
        "by sensitivity. The oracle's normalised elasticity is dimensionless precisely so that a "
        "ranking across inputs is meaningful, and that property does not hold here")


# =============================================================================================
# 5.3 TORNADO RISK RANKING -- specification 14, "5.3"
# =============================================================================================

def m_5_3() -> None:
    ranked = O.tornado_impacts(lambda v: v["A"] + v["B"] + v["C"],
                               {"A": 90.0, "B": 98.0, "C": 80.0},
                               {"A": (90.0, 120.0), "B": (98.0, 105.0), "C": (80.0, 110.0)})
    impacts = {r[0]: r[1] for r in ranked}
    A.near("5.3", "known-answer: the specification's impact for A", impacts["A"], 30)
    A.near("5.3", "known-answer: the specification's impact for B", impacts["B"], 7)
    A.near("5.3", "known-answer: the specification's impact for C", impacts["C"], 30)
    A.check("5.3", "known-answer: A and C tie above B, and the tie policy is explicit and stable",
            {r[0] for r in ranked[:2]} == {"A", "C"} and ranked[-1][0] == "B",
            str([r[0] for r in ranked]))
    A.check("5.3", "invariant: an input whose low and high give the same output has no impact",
            O.tornado_impacts(lambda v: v["A"], {"A": 1.0}, {"A": (1.0, 1.0)})[0][1] == 0)

    out = run("A5.3", dict(EVM))
    A.check("5.3", "structure: four risks are ranked and the top one is named",
            len(out.get("risks", [])) == 4 and bool(out.get("top_risk")))
    A.proposition(
        "5.3", "5.3/negative-score-refused",
        "a document risk score outside nought to one is refused rather than dragging the "
        "composite down without limit into the one-sided calm end of the band",
        abstained(run("A5.3", {**EVM, "docRiskScore": -30})))
    A.check("5.3", "invalid input: a cost or schedule index at or below zero is refused",
            abstained(run("A5.3", {**EVM, "cpi": 0}))
            and abstained(run("A5.3", {**EVM, "spi": -1})))
    A.check("5.3", "invalid input: progress outside nought to one hundred is refused",
            abstained(run("A5.3", {**EVM, "actualPctComplete": 400}))
            and abstained(run("A5.3", {**EVM, "plannedPctComplete": -20})))
    A.check("5.3", "missingness: all five inputs are required",
            abstained(run("A5.3", {"cpi": 0.8})))
    A.check("5.3", "invariant: the ranking is by absolute impact descending, as the method "
                   "requires", [r["impact"] for r in out["risks"]]
            == sorted([r["impact"] for r in out["risks"]], reverse=True))

    A.proposition(
        "5.3", "5.3/output-evaluated-at-low-and-high",
        "each input's impact is the difference between the OUTPUT evaluated at that input's high "
        "value and at its low value, which is what a tornado impact is",
        False,
        "no output is evaluated at any low or high value. The four impacts are the absolute "
        "deviation of the cost index from one, the same for the schedule index, the document "
        "risk score times a hundred, and the absolute gap between reported and planned progress. "
        "These are current deviations from nominal, not ranges of a response. No range is "
        "declared for any input and no response function exists to evaluate")
    A.proposition(
        "5.3", "5.3/presents-5.2-results",
        "the module presents the sensitivity results of the sensitivity module rather than "
        "creating a second, differently computed ranking from the same evidence",
        False,
        "specification 5.3 states that this should ordinarily present the sensitivity module's "
        "results and that if it independently creates duplicate evidence the lineage and "
        "double-count risk must be flagged. It does exactly that: it recomputes its own impacts "
        "from the same cost index, schedule index and document risk score the sensitivity module "
        "reads, by a different formula, and adds a fourth driver. The two modules therefore "
        "report on one body of evidence twice, by two incompatible definitions, and a reader "
        "seeing both agree is seeing one reading counted twice")


# =============================================================================================
# 5.4 SCENARIO MODELING -- specification 14, "5.4"
# =============================================================================================

def _decision(probs, outcomes, version="synthetic-v0.3", split="DEVELOPMENT"):
    return {"bac": 1000, "scenarioDecisionStructure": {
        "asset_version": version, "split": split, "decision_object_id": "D1",
        "evaluated_project_id": "P1", "reference_member_project_ids": ["P2", "P3"],
        "scenarios": [{"scenario_id": s, "probability": p} for s, p in probs.items()],
        "outcomes": [{"action_id": a, "scenario_id": s, "cost_delta_usd": v}
                     for a, row in outcomes.items() for s, v in row.items()]}}


def m_5_4() -> None:
    sd = O.scenario_expectation({"S1": 0.6, "S2": 0.4},
                                {"hold": {"S1": 0.0, "S2": 100.0},
                                 "act": {"S1": 30.0, "S2": 30.0}})
    A.near("5.4", "known-answer: the probability weighted expectation of holding",
           sd["expectations"]["hold"], 40.0)
    A.near("5.4", "known-answer: the probability weighted expectation of acting",
           sd["expectations"]["act"], 30.0)
    A.check("5.4", "known-answer: the action with the lower expected cost is chosen",
            sd["best"] == "act")
    try:
        O.scenario_expectation({"S1": 0.6, "S2": 0.6}, {"a": {"S1": 1.0, "S2": 1.0}})
        A.check("5.4", "boundary: probabilities that do not sum to one are refused", False)
    except ValueError:
        A.check("5.4", "boundary: probabilities that do not sum to one do not describe one "
                       "distribution and are refused", True)

    good = _decision({"S1": 0.6, "S2": 0.4},
                     {"hold": {"S1": 0.0, "S2": 100.0}, "act": {"S1": 30.0, "S2": 30.0}})
    out = run("A5.4", good)
    A.check("5.4", "known-answer: production chooses the same action as the independent "
                   "expectation", out.get("recommended_action") == "act",
            str(out.get("recommended_action")))
    A.near("5.4", "known-answer: production's expected forecast is the budget plus the chosen "
                  "action's expectation", out.get("expected_eac"), 1030, 1.0)
    A.near("5.4", "known-answer: and its pessimistic forecast is that action's worst scenario",
           out.get("pessimistic_eac"), 1030, 1.0)
    A.check("5.4", "structure: the count of actions and scenarios considered is reported",
            out.get("actions_considered") == 2 and out.get("scenarios_considered") == 2)

    A.proposition(
        "5.4", "5.4/abstains-without-decision-structure",
        "with no decision problem the module abstains rather than reporting a three-divisor "
        "earned-value forecast under this method's name",
        abstained(run("A5.4", dict(EVM))))
    A.proposition(
        "5.4", "5.4/probabilities-must-be-a-distribution",
        "scenario probabilities that do not sum to one are refused",
        abstained(run("A5.4", _decision({"S1": 0.6, "S2": 0.6},
                                        {"a": {"S1": 1.0, "S2": 1.0}}))))
    A.proposition(
        "5.4", "5.4/complete-outcome-matrix",
        "an action with no outcome under every scenario described cannot have an expectation "
        "formed and is refused",
        abstained(run("A5.4", {"bac": 1000, "scenarioDecisionStructure": {
            "asset_version": "v", "split": "DEVELOPMENT", "decision_object_id": "D",
            "scenarios": [{"scenario_id": "S1", "probability": 0.5},
                          {"scenario_id": "S2", "probability": 0.5}],
            "outcomes": [{"action_id": "a", "scenario_id": "S1", "cost_delta_usd": 1}]}})))
    A.proposition(
        "5.4", "5.4/locked-holdout-refused",
        "a decision object from the locked holdout is refused outright, since the point of "
        "locking it is that nothing consults it",
        abstained(run("A5.4", _decision({"S1": 1.0}, {"a": {"S1": 1.0}},
                                        split="LOCKED_HOLDOUT"))))
    A.proposition(
        "5.4", "5.4/no-self-comparison",
        "a decision object whose reference population contains the project being assessed is "
        "refused, since the comparison would be of the project with itself",
        abstained(run("A5.4", {"bac": 1000, "scenarioDecisionStructure": {
            **_decision({"S1": 1.0}, {"a": {"S1": 1.0}})["scenarioDecisionStructure"],
            "evaluated_project_id": "P1", "reference_member_project_ids": ["P1"]}})))
    A.proposition(
        "5.4", "5.4/version-required",
        "a decision object with no asset version is refused, since a reading taken from it could "
        "not be interpreted later",
        abstained(run("A5.4", _decision({"S1": 1.0}, {"a": {"S1": 1.0}}, version=""))))
    A.check("5.4", "invalid input: a scenario probability outside nought to one is refused",
            abstained(run("A5.4", _decision({"S1": 1.4, "S2": -0.4},
                                            {"a": {"S1": 1.0, "S2": 1.0}}))))
    A.check("5.4", "boundary: no positive budget leaves nothing to place the outcomes against",
            abstained(run("A5.4", {**good, "bac": 0})))
    A.check("5.4", "invariant: the chosen action is unchanged when every outcome is shifted by a "
                   "constant, since the expectation shifts with it",
            run("A5.4", _decision({"S1": 0.6, "S2": 0.4},
                                  {"hold": {"S1": 50.0, "S2": 150.0},
                                   "act": {"S1": 80.0, "S2": 80.0}})).get("recommended_action")
            == "act")

    A.proposition(
        "5.4", "5.4/system-conditions-not-action-choice",
        "the module models what happens to the SYSTEM under stated conditions, which is what "
        "specification 5.4 places in this category, rather than comparing which ACTION to take, "
        "which the same specification places in Category 10",
        False,
        "the method implemented is correct and its guards are the strongest in the instrument: "
        "the probabilities must be a distribution, every action must have an outcome under every "
        "scenario, the object must carry a version, a locked holdout is refused outright and the "
        "project may not appear in its own reference population. But what it computes is the "
        "probability weighted expected cost of each ACTION and recommends the cheapest, which is "
        "the action-comparison question specification 5.4 explicitly separates from this "
        "category and assigns to Category 10. This is a category-placement question for the "
        "owner rather than a defect, and it is the same structure Category 10.4 was found not to "
        "produce, so the two findings are connected")


# =============================================================================================
# 5.5 REWORK FEEDBACK LOOP -- specification 14, "5.5"
# =============================================================================================

def m_5_5() -> None:
    r = O.rework_step(10, 5, 8, 0.25)
    A.near("5.5", "known-answer: the specification's rework generated", r["rework"], 2.0)
    A.near("5.5", "known-answer: the specification's next backlog", r["backlog_next"], 9.0)
    A.near("5.5", "boundary: a zero error rate generates no rework",
           O.rework_step(10, 5, 8, 0.0)["rework"], 0.0)
    A.near("5.5", "boundary: with no work completed nothing is completed and nothing reworked",
           O.rework_step(10, 5, 0, 0.25)["backlog_next"], 15.0)
    A.check("5.5", "invariant: at new work six, completion eight and an error rate of a quarter "
                   "the backlog is in equilibrium and does not move",
            all(abs(v - 10) < 1e-9 for v in O.rework_run(10, 6, 8, 0.25, 5)))
    A.check("5.5", "invariant: a higher error rate amplifies the backlog, which is the feedback "
                   "the method exists to model", O.rework_run(10, 6, 8, 0.60, 5)[-1] > 10)
    A.check("5.5", "invariant: the accounting conserves, so the change in backlog is exactly new "
                   "work plus rework less completion",
            abs((O.rework_step(10, 5, 8, 0.25)["backlog_next"] - 10) - (5 + 2 - 8)) < 1e-9)

    out = run("A5.5", {"cpi": 0.80, "rfiCount": 15, "changeOrderCount": 5})
    A.near("5.5", "structure: the declared index is the weighted sum of three capped terms",
           out.get("rework_index"),
           min(15 / 30, 1) * 0.3 + min(5 / 15, 1) * 0.3 + max(0, 1 - 0.80) * 0.4, 0.005)
    A.check("5.5", "invariant: the index rises monotonically with requests for information",
            [run("A5.5", {"cpi": 0.9, "rfiCount": n,
                          "changeOrderCount": 2}).get("rework_index")
             for n in (0, 10, 20, 40)] == sorted(
                [run("A5.5", {"cpi": 0.9, "rfiCount": n,
                              "changeOrderCount": 2}).get("rework_index")
                 for n in (0, 10, 20, 40)]))
    A.check("5.5", "boundary: the request and change terms are capped, so the index stops rising "
                   "once each cap is reached",
            run("A5.5", {"cpi": 0.9, "rfiCount": 30, "changeOrderCount": 15}).get("rework_index")
            == run("A5.5", {"cpi": 0.9, "rfiCount": 3000,
                            "changeOrderCount": 1500}).get("rework_index"))
    A.proposition(
        "5.5", "5.5/absent-count-is-not-zero",
        "an absent count of requests or change orders is required rather than contributing "
        "exactly zero, which is the same contribution a perfect term makes and would mean "
        "missing evidence buying a better reading",
        abstained(run("A5.5", {"cpi": 0.8, "rfiCount": 15}))
        and abstained(run("A5.5", {"cpi": 0.8, "changeOrderCount": 5}))
        and abstained(run("A5.5", {"rfiCount": 15, "changeOrderCount": 5})))
    A.check("5.5", "invalid input: a negative count is refused",
            abstained(run("A5.5", {"cpi": 0.8, "rfiCount": -1, "changeOrderCount": 5})))

    A.proposition(
        "5.5", "5.5/stocks-and-flows",
        "the module carries time-dependent stocks and flows with feedback, so a backlog, a rate "
        "of rework generation and a completion rate exist and evolve over time",
        any(k in out for k in ("backlog", "rework_generated", "time_step", "stocks", "flows")),
        "the module computes a weighted sum of three capped current quantities: the request "
        "count over thirty, the change order count over fifteen, and one minus the cost index. "
        "Specification 5.5 states in terms that a weighted cost index, request and change score "
        "is not a feedback simulation. There is no stock, no flow, no time step and no feedback: "
        "nothing accumulates and nothing feeds back into anything. The three weights of 0.3, 0.3 "
        "and 0.4 and the caps of thirty and fifteen are literals with no source. The independent "
        "oracle demonstrates what the method requires, including an equilibrium that holds and "
        "an error rate that amplifies the stock, neither of which this module can express")


# =============================================================================================
# 5.6 QUEUEING THEORY BOTTLENECK -- specification 14, "5.6"
# =============================================================================================

def _queue(servers, horizon, service, entities, waits):
    return {"queueStructure": {"queues": [
        {"queue_id": "Q1", "servers": servers, "horizon_days": horizon,
         "total_service_days": service, "entities": entities, "wait_times_days": waits}]}}


def m_5_6() -> None:
    q = O.mm1(2, 3)
    A.near("5.6", "known-answer: the specification's M/M/1 utilisation", q["rho"], 2 / 3)
    A.near("5.6", "known-answer: the number in the system", q["L"], 2.0)
    A.near("5.6", "known-answer: the time in the system", q["W"], 1.0)
    A.near("5.6", "known-answer: the number in the queue", q["Lq"], 4 / 3)
    A.near("5.6", "known-answer: the time in the queue", q["Wq"], 2 / 3)
    A.check("5.6", "invariant: Little's Law holds, both for the system and for the queue",
            O.littles_law_holds(2, 3))
    A.check("5.6", "boundary: at an arrival rate equal to the service rate there is no steady "
                   "state and no reassuring solution is returned, which is the defect "
                   "specification 5.6 names",
            not O.mm1(3, 3)["stable"] and O.mm1(3, 3)["L"] is None)
    A.check("5.6", "boundary: an arrival rate above the service rate likewise has no solution",
            O.mm1(4, 3)["L"] is None)
    A.check("5.6", "invariant: waiting grows without bound as utilisation approaches one",
            O.mm1(2.99, 3)["W"] > O.mm1(2, 3)["W"] > O.mm1(1, 3)["W"])

    out = run("A5.6", _queue(2, 30, 30, 4, [1.0, 2.0, 3.0, 4.0]))
    A.near("5.6", "known-answer: utilisation is server time used over server time available",
           out.get("utilisation"), 0.5, 0.005)
    A.near("5.6", "known-answer: the arrival rate is entities over the observation window",
           out.get("arrival_rate_per_day"), 4 / 30, 0.005)
    A.near("5.6", "known-answer: the mean observed wait", out.get("mean_wait_days"), 2.5, 0.06)
    A.proposition(
        "5.6", "5.6/no-steady-state-when-saturated",
        "a queue at or above full utilisation does not emit a reassuring reading",
        run("A5.6", _queue(1, 30, 30, 4, [1.0, 2.0, 3.0, 4.0])).get("status_color") == "Red")
    A.check("5.6", "invariant: utilisation rises as the same service is done by fewer servers",
            run("A5.6", _queue(1, 30, 15, 4, [1.0] * 4)).get("utilisation")
            > run("A5.6", _queue(2, 30, 15, 4, [1.0] * 4)).get("utilisation"))
    A.proposition(
        "5.6", "5.6/abstains-without-queue",
        "with no queue structure the module abstains and does not fall back to a share of "
        "constrained activities in a look-ahead window",
        abstained(run("A5.6", {"activitiesPlanned": 10, "activitiesConstrained": 3, **EVM})))
    A.check("5.6", "boundary: no servers or no observation window is refused",
            abstained(run("A5.6", _queue(0, 30, 10, 2, [1.0, 2.0])))
            and abstained(run("A5.6", _queue(2, 0, 10, 2, [1.0, 2.0]))))
    A.check("5.6", "invalid input: a queue that does not carry a waiting time for each entity "
                   "that arrived is incomplete and is refused",
            abstained(run("A5.6", _queue(2, 30, 10, 4, [1.0, 2.0]))))
    A.check("5.6", "only one boundary is applied and it is the definitional stability condition, "
                   "so no uncited warning level is invented: the module reports two levels",
            {run("A5.6", _queue(2, 30, s, 4, [1.0] * 4)).get("status_color")
             for s in (6, 30, 45, 60, 120)} == {"Green", "Red"})

    A.proposition(
        "5.6", "5.6/queueing-model",
        "the module carries an arrival process and a service process with their rates, a queue "
        "discipline and the waiting measures the theory defines, so the number and time in "
        "system and in queue can be derived",
        any(k in out for k in ("service_rate", "L", "Lq", "W", "Wq", "discipline",
                               "queue_discipline")),
        "the module measures the EMPIRICAL utilisation of an observed queue, service time used "
        "over server time available, and reports the observed mean and ninetieth percentile "
        "waits. That is a sound and honest measurement and it correctly refuses to emit a "
        "steady-state solution at saturation, which is the specific failure specification 5.6 "
        "warns about. But no service rate, no queue discipline and none of the theory's derived "
        "measures exist, so it is queue measurement rather than queueing theory, and Little's "
        "Law cannot be checked against it because neither side of the identity is computed")


# =============================================================================================
# 5.7 AGENT-BASED SUPPLY CHAIN -- specification 14, "5.7"
# =============================================================================================

def _abm(agents, states):
    return {"abmStructure": {
        "agents": [{"agent_id": a, "decision_rule_id": f"R{a}", "network_group": "G1"}
                   for a in agents],
        "states": [{"agent_id": a, "time_step": t, "state": s} for a, t, s in states]}}


def m_5_7() -> None:
    h = O.replay_supply_chain(3)
    A.check("5.7", "known-answer: the project starts backordered",
            h[0]["project"]["state"] == "backordered")
    A.check("5.7", "known-answer: at the first step the supplier has shipped and the carrier is "
                   "carrying, which is the supplier rule firing",
            h[1]["supplier"]["inventory"] == 0 and h[1]["carrier"]["state"] == "busy")
    A.check("5.7", "known-answer: at the second step the declared travel delay has elapsed and "
                   "the project has received the unit", h[2]["project"]["state"] == "received")
    A.check("5.7", "reproducibility: replaying the rules gives the identical state history",
            O.replay_supply_chain(3) == h)
    A.check("5.7", "boundary: with no stock the supplier rule cannot fire, so the state history "
                   "produced by the rules is different, which is what makes them rules",
            O.replay_supply_chain(1)[0]["supplier"]["inventory"] == 1)

    out = run("A5.7", _abm(["a", "b", "c", "d"],
                           [(a, t, "NORMAL") for a in "abcd" for t in (0, 1)][:7]
                           + [("d", 1, "DISRUPTED")]))
    A.near("5.7", "known-answer: one disrupted agent of four at the last step is a quarter",
           out.get("at_risk_ratio"), 0.25, 0.005)
    A.check("5.7", "structure: the agent count and the number of time steps are reported",
            out.get("agents") == 4 and out.get("time_steps") == 2)
    A.proposition(
        "5.7", "5.7/agents-need-rules",
        "an agent with no decision rule is refused, since agents without rules do not make a "
        "model of behaviour",
        abstained(run("A5.7", {"abmStructure": {
            "agents": [{"agent_id": "a", "network_group": "G1"}],
            "states": [{"agent_id": "a", "time_step": 0, "state": "NORMAL"},
                       {"agent_id": "a", "time_step": 1, "state": "NORMAL"}]}})))
    A.proposition(
        "5.7", "5.7/agents-need-interaction",
        "an agent belonging to no interaction group is refused, since agents that do not "
        "interact are not an agent-based model",
        abstained(run("A5.7", {"abmStructure": {
            "agents": [{"agent_id": "a", "decision_rule_id": "R1"}],
            "states": [{"agent_id": "a", "time_step": 0, "state": "NORMAL"},
                       {"agent_id": "a", "time_step": 1, "state": "NORMAL"}]}})))
    A.proposition(
        "5.7", "5.7/needs-time",
        "a state history covering a single point in time is refused, since a model with one step "
        "is not a model over time",
        abstained(run("A5.7", _abm(["a"], [("a", 0, "NORMAL")]))))
    A.check("5.7", "boundary: a history that does not cover every agent at the last time step is "
                   "refused rather than forming a share from a partial cohort",
            abstained(run("A5.7", _abm(["a", "b"], [("a", 0, "NORMAL"), ("a", 1, "NORMAL"),
                                                    ("b", 0, "NORMAL")]))))
    A.proposition(
        "5.7", "5.7/abstains-without-agents",
        "with no agent structure the module abstains and does not fall back to a share of a "
        "procurement log", abstained(run("A5.7", dict(EVM))))

    A.proposition(
        "5.7", "5.7/rules-are-executed",
        "the state history is PRODUCED by executing the agents' behaviour and interaction rules "
        "over the simulation's time steps, which is what makes a model agent-based",
        False,
        "the decision rule and the interaction group are REQUIRED to be present and are then "
        "never executed. The state history is supplied by the caller and the module reads the "
        "share of agents not in a normal state at the last time step. That structural discipline "
        "is real and worth keeping, and it is a large improvement on the procurement-log share "
        "it replaced, but no behaviour is simulated: identical agent rules with a different "
        "supplied history give a different answer, and identical histories with different rules "
        "give the same one. The independent oracle replays the specification's minimum model by "
        "actually firing the rules, which is the difference")


# =============================================================================================
# 5.8 DISCRETE EVENT SIMULATION -- specification 14, "5.8"
# =============================================================================================

def m_5_8() -> None:
    d = O.des_single_server([("A", 0.0, 2.0), ("B", 1.0, 2.0)])
    rows = {r["job"]: r for r in d["log"]}
    A.near("5.8", "known-answer: the specification's job A starts at nought", rows["A"]["start"], 0)
    A.near("5.8", "known-answer: job A ends at two", rows["A"]["end"], 2)
    A.near("5.8", "known-answer: job A waits nothing", rows["A"]["wait"], 0)
    A.near("5.8", "known-answer: job B starts at two, when the server is released",
           rows["B"]["start"], 2)
    A.near("5.8", "known-answer: job B ends at four", rows["B"]["end"], 4)
    A.near("5.8", "known-answer: job B waits one", rows["B"]["wait"], 1)
    A.near("5.8", "known-answer: the mean wait is one half", d["mean_wait"], 0.5)
    A.check("5.8", "boundary: the simultaneous-event policy is explicit and deterministic",
            [r["job"] for r in O.des_single_server([("B", 0.0, 1.0),
                                                    ("A", 0.0, 1.0)])["log"]] == ["A", "B"])
    A.near("5.8", "boundary: a job arriving after the server is released waits nothing, which "
                  "proves the resource is released rather than held",
           O.des_single_server([("A", 0.0, 1.0), ("B", 10.0, 1.0)])["mean_wait"], 0.0)

    out = run("A5.8", dict(EVM))
    A.check("5.8", "structure: a throughput index and an interruption rate are reported",
            out.get("throughput_index") is not None
            and out.get("interruption_rate") is not None)
    A.check("5.8", "invariant: throughput falls as the schedule index falls",
            [run("A5.8", {**EVM, "spi": s}).get("throughput_index")
             for s in (1.2, 1.0, 0.8, 0.5)] == sorted(
                [run("A5.8", {**EVM, "spi": s}).get("throughput_index")
                 for s in (1.2, 1.0, 0.8, 0.5)], reverse=True))
    A.check("5.8", "invariant: the index lies in nought to one, since it is one over one plus a "
                   "non-negative interruption",
            all(0 < run("A5.8", {**EVM, "spi": s, "actualPctComplete": a}
                        ).get("throughput_index") <= 1.0
                for s in (0.3, 1.0, 1.5) for a in (10, 50, 90)))
    A.proposition(
        "5.8", "5.8/no-substituted-progress-ratio",
        "with no planned progress the progress ratio is not substituted as exactly one, the "
        "value of a project running precisely to plan",
        abstained(run("A5.8", {**EVM, "plannedPctComplete": 0})))
    A.check("5.8", "invalid input: a reported progress of ten thousand per cent is refused",
            abstained(run("A5.8", {**EVM, "actualPctComplete": 10000})))
    A.check("5.8", "boundary: a schedule index at or below zero is refused",
            abstained(run("A5.8", {**EVM, "spi": 0})))
    A.check("5.8", "missingness: all four inputs are required",
            abstained(run("A5.8", {"spi": 0.8})))

    A.proposition(
        "5.8", "5.8/event-schedule",
        "the module carries entities, events, a simulation clock, resources, queues and service "
        "durations, and advances a clock through an ordered event schedule",
        any(k in out for k in ("events", "clock", "entities", "queue", "resources",
                               "mean_wait")),
        "the module computes one over one plus an interruption term, where the interruption is "
        "the shortfall of the progress ratio below one plus half the shortfall of the schedule "
        "index below one. Specification 5.8 states in terms that a closed-form progress ratio is "
        "not discrete event simulation. There is no entity, event, clock, resource, queue, "
        "service duration or termination condition anywhere, and nothing is simulated: the "
        "result is a deterministic function of two earned-value indices. The 0.5 weight is a "
        "literal with no source. The independent oracle reproduces the specification's own "
        "two-job schedule exactly, including the simultaneous-event policy and resource release, "
        "which is what the method would have to do")


# =============================================================================================
# RESULT ROWS
# =============================================================================================

def _row(mid, name, basis, source, sreq, spres, impl, thresh, lineage, disp, finding, nxt):
    return {
        "module_id": mid, "module_name": name, "category": "5", "basis_class": basis,
        "operational_activation": "ADVISORY_ONLY", "voting_status": "non-voting",
        "primary_method_source": source, "canonical_structure_required": sreq,
        "canonical_structure_present": spres, "implementation_verified": impl,
        "known_answer_pass": "yes", "boundary_pass": "yes", "missingness_pass": "yes",
        "invariant_pass": "yes", "stochastic_diagnostics_pass": "n/a",
        "reproducibility_pass": "yes", "parameter_provenance_status": "NOT_SOURCED",
        "calibration_status": "NOT_CALIBRATED", "threshold_status": thresh,
        "empirical_validation_status": "NOT_DONE", "regulatory_snapshot": "n/a",
        "cat9_qualification_status": "RAW_UNQUALIFIED_INPUT", "lineage_status": lineage,
        "scientific_disposition": disp, "production_change_made": "no",
        "finding_summary": finding, "required_next_action": nxt,
        "test_names": "; ".join(A.coverage.get(mid, []))[:1800],
        "evidence_paths": ("server/tools/test_run19_category_5.py; "
                           "server/tools/run17/oracle/oracles_cat_5.py; "
                           "server/tools/run17/categories/category_5_faults.csv"),
    }


ROWS = lambda: [  # noqa: E731
    _row("5.1", "DSM Rework Propagation", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 14 section 5.1; Zhao et al. (2010); Tuholski and Tommelein (2010)",
         "yes", "no", "n/a", "n/a", "NO_EVIDENCE_EMITTED", "CORRECT_ABSTENTION",
         "The method is defined by its dependency matrix and no such matrix exists for any "
         "project. The module abstains unconditionally, names the dependency matrix as what is "
         "absent, and its result is byte-identical across every combination of cost index and "
         "budget tested, so the literal nine coefficients and literal initiating wave it once "
         "carried are genuinely gone rather than gated. The propagation itself was verified "
         "independently against the specification's own matrix and seed, including the zero "
         "matrix, the disconnected graph, linearity in the seed, edge-strength monotonicity and "
         "the cycle case that makes a stopping policy necessary. Abstention is the "
         "scientifically correct result.",
         "Build the dependency matrix corpus if rework propagation is wanted, or leave the "
         "module abstaining."),
    _row("5.2", "Sensitivity Analysis", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 14 section 5.2; Kermanshachi and Pamidimukkala (2023)",
         "yes", "partial", "no", "HEURISTIC_UNCALIBRATED", "SHARED_EVM_INPUT_VECTOR",
         "IMPLEMENTATION_DEFECT",
         "One of the three drivers is a genuine local sensitivity: the cost index is perturbed by "
         "plus and minus 0.05 and the forecast at completion recomputed, normalised by the base "
         "forecast. That is real and should be said. The other two are not perturbed at all: the "
         "schedule driver is the absolute deviation of the schedule index from one, halved, and "
         "the document driver is the risk score itself. Specification 5.2 says in terms not to "
         "call current badness a sensitivity unless an input is perturbed and the output "
         "recomputed. Worse than the labelling, the three figures are on three different scales, "
         "and the 0.5 multiplier on the schedule driver is the only thing setting their relative "
         "standing, so both the reported top driver and the band, which reads the maximum, are "
         "determined by an uncited scaling choice rather than by sensitivity. The oracle's "
         "elasticity is dimensionless precisely so a cross-input ranking means something. The "
         "guards are sound: an absent document risk score is required rather than read as zero, "
         "which would demote the driver, and the undefined division points are refused.",
         "P1. Perturb all three inputs and recompute, or report only the driver that is "
         "perturbed. Until then the top driver and the band are not sensitivity results."),
    _row("5.3", "Tornado Risk Ranking", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 14 section 5.3",
         "yes", "no", "no", "HEURISTIC_UNCALIBRATED", "DUPLICATE_OF_5.2_EVIDENCE",
         "METHOD_LABEL_MISMATCH",
         "The domain guards are complete and all hold: a document risk score outside nought to "
         "one no longer drags the composite into the one-sided calm end of the band, indices at "
         "or below zero are refused, and progress outside nought to one hundred is refused. The "
         "ranking is correctly by absolute impact descending. But no output is evaluated at any "
         "input's low or high value, which is what a tornado impact IS. The four impacts are "
         "current deviations from nominal, no range is declared for any input, and no response "
         "function exists to evaluate. Separately, specification 5.3 states this should "
         "ordinarily present the sensitivity module's results and that independently created "
         "duplicate evidence must be flagged for lineage: it recomputes its own impacts from the "
         "same cost index, schedule index and document risk score by a different formula, so the "
         "two modules report one body of evidence twice under two incompatible definitions and a "
         "reader seeing them agree is seeing one reading counted twice.",
         "P1 with the sensitivity module. Declare input ranges, evaluate the response at each "
         "low and high, and present the sensitivity module's results rather than recomputing. "
         "P0D on the lineage disclosure."),
    _row("5.4", "Scenario Modeling", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 14 section 5.4; Collier et al. (2018)",
         "yes", "yes", "yes", "OWNER_POLICY", "GOVERNED_DECISION_OBJECT",
         "OWNER_DECISION_REQUIRED",
         "The method implemented is correct and independently reproduced: the probability "
         "weighted expectation of each action, the cheapest by expectation, and that action's "
         "worst scenario. Its guards are the strongest in the instrument and every one was "
         "verified. The probabilities must sum to one or no expectation is formed. Every action "
         "must have an outcome under every scenario described. The decision object must carry an "
         "asset version or a reading taken from it could not be interpreted later. A locked "
         "holdout is refused outright, because the point of locking it is that nothing consults "
         "it. And the project may not appear in the reference population it is assessed against. "
         "With no decision problem it abstains rather than reporting the three-divisor "
         "earned-value forecast it used to fall back on. The open question is placement: what it "
         "computes is which ACTION to take, and specification 5.4 separates that from this "
         "category and assigns it to Category 10. Note the connection: Category 10.4 was found "
         "not to produce the action-by-scenario matrix, and this module consumes exactly one.",
         "OWNER DECISION on category placement. No arithmetic change is required. Consider "
         "whether this module and Category 10.4 and 10.7 should share one decision object."),
    _row("5.5", "Rework Feedback Loop", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 14 section 5.5; Love et al. (2011); Li and Taylor (2014)",
         "yes", "no", "no", "HEURISTIC_UNCALIBRATED", "SHARED_EVM_AND_DOCUMENT_COUNTS",
         "METHOD_LABEL_MISMATCH",
         "The best property here is a corrected one and it holds: an absent request or change "
         "order count is required rather than contributing exactly zero, which is the same "
         "contribution a perfect term makes, so missing evidence can no longer buy a better "
         "reading, and renormalising over the present terms was correctly refused as the fix. "
         "Negative counts are refused and the caps behave as declared. But the quantity is a "
         "weighted sum of three capped current values and specification 5.5 states in terms that "
         "a weighted cost index, request and change score is not a feedback simulation. No "
         "stock, flow, time step or feedback exists: nothing accumulates and nothing feeds back. "
         "The weights of 0.3, 0.3 and 0.4 and the caps of thirty and fifteen have no source. The "
         "oracle demonstrates the accounting the method requires, including an equilibrium that "
         "holds exactly and an error rate that amplifies the stock, neither of which this module "
         "can express.",
         "P1. Either build the stock and flow accounting or rename the module for the composite "
         "rework-pressure index it computes. Source the weights and caps either way."),
    _row("5.6", "Queueing Theory Bottleneck", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 14 section 5.6; Carmichael (1986); Farid and Koning (1994)",
         "yes", "partial", "yes", "LITERATURE_EXACT", "OWN_STRUCTURE_ONLY",
         "CORRECT_PROXY_ONLY",
         "This module does the single most important thing specification 5.6 asks: at full "
         "utilisation it does NOT emit a reassuring steady-state solution, it reports the worst "
         "band. And it applies exactly one boundary, the definitional stability condition, "
         "inventing no uncited warning level, so it reports two levels rather than four. That is "
         "the correct scientific posture and it is rare in this instrument. It abstains without "
         "a queue rather than falling back on a share of constrained look-ahead activities, "
         "refuses a queue with no servers or window, and refuses one that does not carry a "
         "waiting time for every entity that arrived. What it computes is EMPIRICAL utilisation, "
         "service time used over server time available, with the observed mean and ninetieth "
         "percentile waits. No service rate, queue discipline or derived measure of the theory "
         "exists, so Little's Law cannot be checked against it because neither side is computed. "
         "It is queue measurement, honestly done, rather than queueing theory.",
         "P3. Either carry arrival and service rates so the theory's measures can be derived, or "
         "name the module for the queue utilisation measurement it performs."),
    _row("5.7", "Agent-Based Supply Chain", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 14 section 5.7; Min and Bjornsson (2008)",
         "yes", "partial", "yes", "HEURISTIC_UNCALIBRATED", "OWN_STRUCTURE_ONLY",
         "CORRECT_PROXY_ONLY",
         "The structural discipline is real and every guard was verified: an agent with no "
         "decision rule is refused because agents without rules do not make a model of "
         "behaviour, an agent in no interaction group is refused because agents that do not "
         "interact are not an agent-based model, a single time step is refused because a model "
         "with one step is not a model over time, and a history not covering every agent at the "
         "last step is refused rather than forming a share from a partial cohort. This is a "
         "large improvement on the procurement-log share it replaced. But the decision rule and "
         "the interaction group are required to be present and are then NEVER EXECUTED. The "
         "state history is supplied by the caller and the module reads the share of agents not "
         "in a normal state at the last step. Identical rules with a different supplied history "
         "give a different answer, and identical histories with different rules give the same "
         "one. The oracle replays the specification's minimum model by actually firing the "
         "rules, which is the difference. The band boundaries have no source.",
         "P2. Execute the behaviour and interaction rules to produce the state history, or name "
         "the module for the agent-state share it reads."),
    _row("5.8", "Discrete Event Simulation", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 14 section 5.8; Martinez (2010); Martinez and Ioannou (1999)",
         "yes", "no", "no", "HEURISTIC_UNCALIBRATED", "SHARED_EVM_INPUT_VECTOR",
         "METHOD_LABEL_MISMATCH",
         "The refusal behaviour is correct: with no planned progress the progress ratio is not "
         "substituted as exactly one, the value of a project running precisely to plan, a "
         "reported progress of ten thousand per cent is refused, and a schedule index at or "
         "below zero is refused. The index is bounded in nought to one and monotone. But nothing "
         "is simulated. The module computes one over one plus an interruption term built from "
         "two earned-value indices, and specification 5.8 states in terms that a closed-form "
         "progress ratio is not discrete event simulation. There is no entity, event, simulation "
         "clock, resource, queue, service duration or termination condition anywhere. The 0.5 "
         "weight is a literal with no source. The independent oracle reproduces the "
         "specification's own two-job schedule exactly, including the simultaneous-event policy "
         "and the proof that the resource is released, which is what the method would require.",
         "P1. Either build the event schedule or rename the module for the throughput index it "
         "computes from the two indices."),
]


def main() -> int:
    gate()
    m_5_1(); m_5_2(); m_5_3(); m_5_4(); m_5_5(); m_5_6(); m_5_7(); m_5_8()
    rows = ROWS()
    write_results(HERE / "run17" / "categories" / "category_5_results.csv", RESULT_HEADER, rows)
    A.check("ROWS", "eight Category 5 result rows were written", len(rows) == 8)
    A.check("ROWS", "no production change is recorded on any row",
            all(r["production_change_made"] == "no" for r in rows))
    return A.finish()


if __name__ == "__main__":
    sys.exit(main())
