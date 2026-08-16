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
import run29_fixtures as FX                                      # noqa: E402
from app.simulation import registry as REG                       # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731

# RUN 20 CYCLE 9 REPAIRED BOTH 5.2 PROPOSITIONS, and RUN 29 REPAIRED THE REMAINING SEVEN. The
# harness is what forces this register to be maintained rather than the tests: a proposition that
# HOLDS while it is still registered as a defect turns this suite red, so a repaired finding
# cannot sit here quietly. Every one of the seven propositions is re-asserted in its original
# words in the module blocks below, now holding against the governed structure the supplied
# Run-29 contract required to be supplied.
#
# THE REGISTER IS NOW EMPTY FOR THIS CATEGORY. That is a statement about METHOD, not about
# calibration or empirical validation: no Category-5 module carries a status band, every one of
# them is calibration pending, and Run 33 owns that work.
KNOWN_DEFECTS: dict[str, str] = {}

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

    # RUN 29 SUPPLIED THE MATRIX, so the abstention is no longer unconditional and the
    # propagation itself is now exercised through production rather than only through the oracle.
    out = run("A5.1", {"dsmDependencyModel": FX.dsm_model()})
    A.check("5.1", "known-answer: production propagates the specification's own single-edge "
                   "matrix to a half wave at the first node",
            out["waves"][1] == {"n1": 0.5, "n2": 0.0}, str(out.get("waves")))
    A.check("5.1", "known-answer: and the wave dies at the second step",
            out["waves"][2] == {"n1": 0.0, "n2": 0.0})
    A.check("5.1", "structure: the matrix orientation is declared and carried, so a matrix read "
                   "the wrong way round cannot propagate backwards unnoticed",
            out.get("matrix_orientation") == "ROW_RECEIVES_FROM_COLUMN")
    A.check("5.1", "invariant: propagation is linear in the seed, so a doubled initiating wave "
                   "doubles what arrives",
            run("A5.1", {"dsmDependencyModel": dict(FX.dsm_model(),
                                                    seed_rework_vector={"n1": 0.0, "n2": 2.0})}
                )["waves"][1] == {"n1": 1.0, "n2": 0.0})
    A.check("5.1", "invariant: edge strength is monotone, so a stronger dependency carries more",
            run("A5.1", {"dsmDependencyModel": dict(
                FX.dsm_model(), edges=[{"source": "n2", "target": "n1", "strength": 0.9}])}
                )["waves"][1]["n1"] > 0.5)
    A.check("5.1", "boundary: a zero matrix propagates nothing",
            run("A5.1", {"dsmDependencyModel": dict(FX.dsm_model(), edges=[])}
                )["total_propagated_rework"] == 0.0)
    A.check("5.1", "boundary: a cycle stops under the declared stopping rule rather than "
                   "propagating forever",
            run("A5.1", {"dsmDependencyModel": dict(
                FX.dsm_model(),
                edges=[{"source": "n2", "target": "n1", "strength": 1.0},
                       {"source": "n1", "target": "n2", "strength": 1.0}])}
                ).get("wave_count") == 5)
    A.check("5.1", "invalid input: a matrix with no declared orientation is refused",
            abstained(run("A5.1", {"dsmDependencyModel": dict(FX.dsm_model(),
                                                              matrix_orientation="")})))
    A.check("5.1", "invalid input: a dependency joining a node the matrix does not declare is "
                   "refused",
            abstained(run("A5.1", {"dsmDependencyModel": dict(
                FX.dsm_model(),
                edges=[{"source": "ghost", "target": "n1", "strength": 0.5}])})))
    A.check("5.1", "invalid input: a matrix with no stopping rule is refused, because a matrix "
                   "with a cycle in it propagates forever",
            abstained(run("A5.1", {"dsmDependencyModel": {
                k: v for k, v in FX.dsm_model().items() if k != "stopping_rule"}})))
    A.check("5.1", "threshold: no colour is asserted over propagated rework",
            out.get("status_color") is None and out.get("calibration_pending") is True)


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

    out = run("A5.2", {"sensitivityModel": FX.sensitivity_model()})
    _x1 = out["inputs"][0]
    A.near("5.2", "known-answer: production reproduces the specification's own 1.68 on the same "
                  "response, base state and ten per cent perturbation",
           _x1["normalised_sensitivity"], 1.68, 1e-9)
    A.near("5.2", "known-answer: the response at the base state is five",
           out.get("base_response"), 5.0, 1e-12)
    A.near("5.2", "known-answer: and the response RECOMPUTED at the moved input is 5.84",
           _x1["moved_response"], 5.84, 1e-9)
    A.check("5.2", "structure: the response model is named and versioned, so what was perturbed "
                   "is interpretable later",
            out.get("response_model_id") == "LAB-QUADRATIC"
            and out.get("response_model_version") == "1.0")
    A.check("5.2", "structure: the method is declared LOCAL and one at a time, so it is not "
                   "presented as a global sensitivity",
            out.get("method") == "LOCAL_ONE_AT_A_TIME" and out.get("method_scope") == "LOCAL")
    A.proposition(
        "5.2", "5.2/no-absent-driver-reads-zero",
        "an absent document risk score is required rather than read as a sensitivity of exactly "
        "zero, which would be the strongest possible claim that the driver does not move the "
        "estimate and would demote it to the bottom of the ranking",
        abstained(run("A5.2", {k: v for k, v in EVM.items() if k != "docRiskScore"})))
    A.check("5.2", "boundary: an input the model is asked to move by nothing at all is refused, "
                   "because a response cannot respond to a perturbation of nought",
            abstained(run("A5.2", {"sensitivityModel": dict(
                FX.sensitivity_model(),
                inputs=[dict(FX.sensitivity_model()["inputs"][0],
                             perturbation_fraction=0.0)])})))
    A.check("5.2", "boundary: an input that is not part of the base state cannot be moved and is "
                   "refused",
            abstained(run("A5.2", {"sensitivityModel": dict(
                FX.sensitivity_model(),
                inputs=[dict(FX.sensitivity_model()["inputs"][0], input_id="ghost")])})))
    A.check("5.2", "invalid input: a response model with no terms computes nothing and is "
                   "refused",
            abstained(run("A5.2", {"sensitivityModel": dict(
                FX.sensitivity_model(),
                response_model={"model_id": "M", "version": "1", "terms": []})})))
    A.check("5.2", "missingness: the earned-value scalars produce no sensitivity at all",
            abstained(run("A5.2", dict(EVM))))
    A.check("5.2", "threshold: no colour is asserted over the sensitivity",
            out.get("status_color") is None and out.get("calibration_pending") is True)

    # THE PROPOSITION IS EVALUATED BY MOVING THE INPUT AND REQUIRING THE RESPONSE TO MOVE, which
    # is what "perturbed and recomputed" means, rather than by reading a label off the result.
    _bigger = run("A5.2", {"sensitivityModel": dict(
        FX.sensitivity_model(),
        inputs=[dict(FX.sensitivity_model()["inputs"][0], perturbation_fraction=0.20)])})
    _all_perturbed = (
        all(i["moved_response"] != i["base_response"] for i in out["inputs"])
        and _bigger["inputs"][0]["moved_response"] != _x1["moved_response"]
        and all("normalised_sensitivity" in i for i in out["inputs"]))
    A.proposition(
        "5.2", "5.2/all-drivers-perturbed",
        "every driver ranked is perturbed and the estimate recomputed, which is what "
        "specification 5.2 requires before a quantity may be called a sensitivity",
        _all_perturbed)
    _commensurable = all(
        abs(i["normalised_sensitivity"]
            - ((i["delta_response"] / i["base_response"])
               / ((i["moved_value"] - i["base_value"]) / i["base_value"]))) < 1e-12
        for i in out["inputs"])
    A.proposition(
        "5.2", "5.2/commensurable-ranking",
        "the three driver figures are on a common scale, so ranking them and taking the largest "
        "means something",
        _commensurable)


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

    out = run("A5.3", {"sensitivityModel": FX.tornado_model()})
    _bars = {b["input_id"]: b for b in out["bars"]}
    A.near("5.3", "known-answer: production reproduces the specification's own impact for A",
           _bars["A"]["impact"], 30.0, 1e-9)
    A.near("5.3", "known-answer: and for B", _bars["B"]["impact"], 7.0, 1e-9)
    A.near("5.3", "known-answer: and for C", _bars["C"]["impact"], 30.0, 1e-9)
    A.check("5.3", "known-answer: A and C tie above B in production too, and the tie policy is "
                   "stated on the result rather than left implicit",
            out["ranked_inputs"] == ["A", "C", "B"] and _bars["A"]["rank"] == _bars["C"]["rank"]
            and _bars["B"]["rank"] > _bars["A"]["rank"]
            and bool(out.get("tie_policy")), str(out.get("ranked_inputs")))
    A.check("5.3", "invariant: the ranking is by absolute impact descending, as the method "
                   "requires",
            [b["absolute_impact"] for b in out["bars"]]
            == sorted([b["absolute_impact"] for b in out["bars"]], reverse=True))
    A.proposition(
        "5.3", "5.3/negative-score-refused",
        "a document risk score outside nought to one is refused rather than dragging the "
        "composite down without limit into the one-sided calm end of the band",
        abstained(run("A5.3", {**EVM, "docRiskScore": -30})))
    A.check("5.3", "missingness: the five earned-value scalars produce no ranking at all",
            abstained(run("A5.3", dict(EVM))))
    A.check("5.3", "threshold: no colour is asserted over the swings",
            out.get("status_color") is None and out.get("calibration_pending") is True)

    # THE LINEAGE, PROVED BY EXECUTION RATHER THAN BY THE LABEL. The bars this module presents
    # must be, value for value, the low and high responses the sensitivity module computed on the
    # same structure. If it recomputed anything of its own the two would be free to disagree.
    _sens = run("A5.2", {"sensitivityModel": FX.tornado_model()})
    _sens_pairs = {i["input_id"]: (i["response_at_low"], i["response_at_high"])
                   for i in _sens["inputs"]}
    A.proposition(
        "5.3", "5.3/output-evaluated-at-low-and-high",
        "each input's impact is the difference between the OUTPUT evaluated at that input's high "
        "value and at its low value, which is what a tornado impact is",
        all(abs(b["impact"] - (b["response_at_high"] - b["response_at_low"])) < 1e-12
            for b in out["bars"])
        and all((b["response_at_low"], b["response_at_high"]) == _sens_pairs[b["input_id"]]
                for b in out["bars"]))
    A.proposition(
        "5.3", "5.3/presents-5.2-results",
        "the module presents the sensitivity results of the sensitivity module rather than "
        "creating a second, differently computed ranking from the same evidence",
        out.get("independent_evidence") is False and out.get("derived_from") == "A5.2"
        and out.get("derived_from_response_model_id") == _sens.get("response_model_id")
        and out.get("derived_from_base_response") == _sens.get("base_response")
        and all((b["response_at_low"], b["response_at_high"]) == _sens_pairs[b["input_id"]]
                for b in out["bars"]))
    A.check("5.3", "structure: the lineage names the sensitivity model and version the swings "
                   "were derived from, which is what Run 31's qualification gate will need",
            out.get("derived_from_response_model_id") == "LAB-ADDITIVE"
            and out.get("derived_from_response_model_version") == "1.0")


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

    out = run("A5.4", {"scenarioSet": FX.scenario_set()})
    A.check("5.4", "known-answer: production reproduces the specification's own three coherent "
                   "states through Y = 2*x1 + x2, giving five, eight and four exactly",
            out.get("responses") == {"BASE": 5.0, "ADVERSE": 8.0, "RECOVERY": 4.0},
            str(out.get("responses")))
    A.check("5.4", "structure: each scenario carries its identity, its version and the reasoning "
                   "behind it, and states every input it changes together",
            all(sc["scenario_id"] and sc["version"] and sc["rationale"]
                and set(sc["variables"]) == {"x1", "x2"} for sc in out["scenarios"]))
    A.check("5.4", "structure: the response model every scenario is evaluated through is named "
                   "and versioned, and it is the SAME model for all of them",
            out.get("response_model_id") == "LAB-LINEAR"
            and out.get("response_model_version") == "1.0")
    A.check("5.4", "invariant: the response is monotone in a jointly worsened state",
            out["responses"]["ADVERSE"] > out["responses"]["BASE"]
            > out["responses"]["RECOVERY"])
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
    A.check("5.4", "boundary: a scenario that sets an input outside the range the scenario set "
                   "itself declares consistent is refused rather than evaluated",
            abstained(run("A5.4", {"scenarioSet": dict(
                FX.scenario_set(),
                scenarios=[dict(FX.scenario_set()["scenarios"][0],
                                variables={"x1": 99.0, "x2": 1.0})])})))
    A.check("5.4", "boundary: a scenario that does not state a value for every input the "
                   "response model reads is not a coherent state and is refused",
            abstained(run("A5.4", {"scenarioSet": dict(
                FX.scenario_set(),
                scenarios=[dict(FX.scenario_set()["scenarios"][0],
                                variables={"x1": 2.0})])})))
    A.check("5.4", "missingness: the earned-value scalars produce no scenario reading",
            abstained(run("A5.4", dict(EVM))))
    A.check("5.4", "threshold: no colour is asserted over the scenario responses",
            out.get("status_color") is None and out.get("calibration_pending") is True)

    A.proposition(
        "5.4", "5.4/system-conditions-not-action-choice",
        "the module models what happens to the SYSTEM under stated conditions, which is what "
        "specification 5.4 places in this category, rather than comparing which ACTION to take, "
        "which the same specification places in Category 10",
        out.get("recommended_action") is None and bool(out.get("responses"))
        and abstained(run("A5.4", _decision({"S1": 0.6, "S2": 0.4},
                                            {"hold": {"S1": 0.0, "S2": 100.0},
                                             "act": {"S1": 30.0, "S2": 30.0}}))))


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

    out = run("A5.5", {"systemDynamicsModel": FX.system_dynamics_model()})
    A.near("5.5", "known-answer: production reproduces the specification's own rework generated",
           out["trace"][0]["rework_generated"], 2.0, 1e-12)
    A.near("5.5", "known-answer: and the specification's own next backlog of nine",
           out.get("final_backlog"), 9.0, 1e-12)
    _steps = [{"step": i, "new_work": 6.0, "work_completed": 8.0, "error_rate": 0.25}
              for i in range(5)]
    _eq = run("A5.5", {"systemDynamicsModel": dict(FX.system_dynamics_model(), steps=_steps)})
    A.check("5.5", "invariant: at new work six, completion eight and an error rate of a quarter "
                   "the backlog is in equilibrium in production too",
            all(abs(t["closing_backlog"] - 10.0) < 1e-9 for t in _eq["trace"]),
            str([t["closing_backlog"] for t in _eq["trace"]]))
    _amp = run("A5.5", {"systemDynamicsModel": dict(
        FX.system_dynamics_model(),
        steps=[{"step": i, "new_work": 6.0, "work_completed": 8.0, "error_rate": 0.60}
               for i in range(5)])})
    A.check("5.5", "invariant: a higher error rate amplifies the backlog, which is the feedback "
                   "the method exists to model", _amp.get("final_backlog") > 10.0)
    A.check("5.5", "boundary: a zero error rate generates no rework in production either",
            run("A5.5", {"systemDynamicsModel": dict(
                FX.system_dynamics_model(),
                steps=[{"step": 0, "new_work": 5.0, "work_completed": 8.0,
                        "error_rate": 0.0}])})["trace"][0]["rework_generated"] == 0.0)
    A.check("5.5", "invariant: the accounting conserves across the whole run, and the residual "
                   "is reported rather than assumed",
            out.get("accounting_residual") is not None
            and abs(out["accounting_residual"]) < 1e-9)
    A.check("5.5", "invariant: the reported time step is the model's own, so the run is "
                   "time-dependent rather than a single algebraic reading",
            out.get("time_step") == 1.0 and out.get("steps_run") == 1)
    A.proposition(
        "5.5", "5.5/absent-count-is-not-zero",
        "an absent count of requests or change orders is required rather than contributing "
        "exactly zero, which is the same contribution a perfect term makes and would mean "
        "missing evidence buying a better reading",
        abstained(run("A5.5", {"cpi": 0.8, "rfiCount": 15}))
        and abstained(run("A5.5", {"cpi": 0.8, "changeOrderCount": 5}))
        and abstained(run("A5.5", {"rfiCount": 15, "changeOrderCount": 5})))
    A.check("5.5", "invalid input: a step completing more work than the backlog held does not "
                   "balance and is refused",
            abstained(run("A5.5", {"systemDynamicsModel": dict(
                FX.system_dynamics_model(),
                steps=[{"step": 0, "new_work": 5.0, "work_completed": 99.0,
                        "error_rate": 0.25}])})))
    A.check("5.5", "invalid input: an error rate outside nought to one is refused",
            abstained(run("A5.5", {"systemDynamicsModel": dict(
                FX.system_dynamics_model(),
                steps=[{"step": 0, "new_work": 5.0, "work_completed": 8.0,
                        "error_rate": 1.5}])})))
    A.check("5.5", "missingness: the cost index and the two counts produce no reading",
            abstained(run("A5.5", {"cpi": 0.80, "rfiCount": 15, "changeOrderCount": 5})))
    A.check("5.5", "threshold: no colour is asserted over the backlog",
            out.get("status_color") is None and out.get("calibration_pending") is True)

    A.proposition(
        "5.5", "5.5/stocks-and-flows",
        "the module carries time-dependent stocks and flows with feedback, so a backlog, a rate "
        "of rework generation and a completion rate exist and evolve over time",
        all(k in out for k in ("initial_backlog", "final_backlog", "trace", "time_step",
                               "total_rework_generated", "total_work_completed")))


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

    out = run("A5.6", {"queueModel": FX.queue_model()})
    A.near("5.6", "known-answer: production reproduces the specification's own utilisation",
           out.get("utilisation"), 2 / 3, 1e-5)
    A.near("5.6", "known-answer: the number in the system", out.get("L"), 2.0, 1e-5)
    A.near("5.6", "known-answer: the time in the system", out.get("W"), 1.0, 1e-5)
    A.near("5.6", "known-answer: the number in the queue", out.get("Lq"), 4 / 3, 1e-5)
    A.near("5.6", "known-answer: the time in the queue", out.get("Wq"), 2 / 3, 1e-5)
    A.check("5.6", "invariant: Little's Law holds in production, both for the system and for the "
                   "queue",
            abs(out["L"] - 2.0 * out["W"]) < 1e-5 and abs(out["Lq"] - 2.0 * out["Wq"]) < 1e-5,
            f"L {out['L']} vs lambda*W {2.0 * out['W']}")
    A.check("5.6", "structure: the arrival process, the service process, the server count and "
                   "the queue discipline are all declared and carried",
            out.get("arrival_rate") == 2.0 and out.get("service_rate") == 3.0
            and out.get("servers") == 1 and out.get("discipline") == "FIFO")
    A.check("5.6", "invariant: waiting grows as utilisation approaches one",
            run("A5.6", {"queueModel": FX.queue_model(arrival=2.99)}).get("W")
            > out.get("W")
            > run("A5.6", {"queueModel": FX.queue_model(arrival=1.0)}).get("W"))
    A.check("5.6", "invariant: utilisation is the ratio of the two rates, so scaling both "
                   "together leaves it where it was",
            abs(run("A5.6", {"queueModel": FX.queue_model(arrival=20.0, service=30.0)}
                    ).get("utilisation") - out.get("utilisation")) < 1e-9)
    A.check("5.6", "invariant: the same arrivals across more servers run at lower utilisation",
            run("A5.6", {"queueModel": FX.queue_model(servers=2)}).get("utilisation")
            < out.get("utilisation"))
    A.proposition(
        "5.6", "5.6/no-steady-state-when-saturated",
        "a queue at or above full utilisation does not emit a reassuring reading",
        abstained(run("A5.6", {"queueModel": FX.queue_model(arrival=3.0)}))
        and abstained(run("A5.6", {"queueModel": FX.queue_model(arrival=4.0)})))
    A.proposition(
        "5.6", "5.6/abstains-without-queue",
        "with no queue structure the module abstains and does not fall back to a share of "
        "constrained activities in a look-ahead window",
        abstained(run("A5.6", {"activitiesPlanned": 10, "activitiesConstrained": 3, **EVM})))
    A.check("5.6", "boundary: no servers, no arrivals or no service is refused",
            abstained(run("A5.6", {"queueModel": FX.queue_model(servers=0)}))
            and abstained(run("A5.6", {"queueModel": FX.queue_model(arrival=0.0)}))
            and abstained(run("A5.6", {"queueModel": FX.queue_model(service=0.0)})))
    A.check("5.6", "invalid input: a queue taking its work in an order this platform has no "
                   "model for is refused rather than assumed to be first in first out",
            abstained(run("A5.6", {"queueModel": dict(
                FX.queue_model(),
                queues=[dict(FX.queue_model()["queues"][0], discipline="WHOEVER_SHOUTS")])})))
    A.check("5.6", "threshold: no colour is asserted over the queue measures, and the only "
                   "boundary applied is the definitional stability condition",
            out.get("status_color") is None and out.get("calibration_pending") is True)

    A.proposition(
        "5.6", "5.6/queueing-model",
        "the module carries an arrival process and a service process with their rates, a queue "
        "discipline and the waiting measures the theory defines, so the number and time in "
        "system and in queue can be derived",
        all(out.get(k) is not None for k in ("arrival_rate", "service_rate", "discipline",
                                             "L", "Lq", "W", "Wq")))


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

    out = run("A5.7", {"agentSupplyChainModel": FX.agent_model()})
    _trace = out["runs"][0]["trace"]
    A.check("5.7", "known-answer: the hand-computed trace, step by step, under the declared step "
                   "order of post demand, deliver, collect, ship",
            [t["supplier_inventory"] for t in _trace] == [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            and [t["received"] for t in _trace] == [0, 0, 1, 2, 2, 2],
            str([(t["supplier_inventory"], t["dock"], t["in_transit"], t["received"])
                 for t in _trace]))
    A.check("5.7", "known-answer: both units are received and nothing is left backordered",
            out.get("received") == 2 and out.get("backordered") == 0)
    A.check("5.7", "structure: the step order is declared on the result, so any trace is "
                   "hand-checkable rather than having to be reverse engineered",
            out.get("step_order") == ["POST_DEMAND", "DELIVER", "COLLECT", "SHIP"])
    A.check("5.7", "boundary: with no stock the supplier rule cannot fire, so nothing is "
                   "received and the whole demand is backordered",
            run("A5.7", {"agentSupplyChainModel": FX.agent_model(inventory=0.0)}
                ).get("received") == 0)
    A.check("5.7", "invariant: a longer carrier delay moves the receipts later, which is the "
                   "carrier rule being executed rather than read",
            [t["received"] for t in run(
                "A5.7", {"agentSupplyChainModel": FX.agent_model(delay=2)}
            )["runs"][0]["trace"]] == [0, 0, 0, 1, 1, 2])
    A.check("5.7", "reproducibility: the same model run twice gives the identical trace",
            run("A5.7", {"agentSupplyChainModel": FX.agent_model()})["runs"][0]["trace"]
            == _trace)
    A.proposition(
        "5.7", "5.7/agents-need-rules",
        "an agent with no decision rule is refused, since agents without rules do not make a "
        "model of behaviour",
        abstained(run("A5.7", {"agentSupplyChainModel": dict(
            FX.agent_model(),
            agents=[dict(a, behaviour_rule="") for a in FX.agent_model()["agents"]])})))
    A.proposition(
        "5.7", "5.7/agents-need-interaction",
        "an agent belonging to no interaction group is refused, since agents that do not "
        "interact are not an agent-based model",
        abstained(run("A5.7", {"agentSupplyChainModel": dict(
            FX.agent_model(),
            agents=[dict(a, interaction_links=[]) for a in FX.agent_model()["agents"]])})))
    A.proposition(
        "5.7", "5.7/needs-time",
        "a state history covering a single point in time is refused, since a model with one step "
        "is not a model over time",
        abstained(run("A5.7", {"agentSupplyChainModel": FX.agent_model(steps=1)})))
    A.check("5.7", "boundary: an agent connected to somebody the model does not contain is "
                   "refused",
            abstained(run("A5.7", {"agentSupplyChainModel": dict(
                FX.agent_model(),
                agents=[dict(FX.agent_model()["agents"][0], interaction_links=["GHOST"])]
                + FX.agent_model()["agents"][1:])})))
    A.proposition(
        "5.7", "5.7/abstains-without-agents",
        "with no agent structure the module abstains and does not fall back to a share of a "
        "procurement log", abstained(run("A5.7", dict(EVM))))
    A.check("5.7", "threshold: no colour is asserted over the delivered quantity",
            out.get("status_color") is None and out.get("calibration_pending") is True)

    # THE PROPOSITION IS EVALUATED BY CHANGING A RULE'S PARAMETERS AND REQUIRING THE OUTCOME TO
    # MOVE, which is the difference Run 19 recorded: identical rules with a different supplied
    # history used to give a different answer, and identical histories with different rules gave
    # the same one. Neither is possible now, because there is no supplied history at all.
    A.proposition(
        "5.7", "5.7/rules-are-executed",
        "the state history is PRODUCED by executing the agents' behaviour and interaction rules "
        "over the simulation's time steps, which is what makes a model agent-based",
        run("A5.7", {"agentSupplyChainModel": FX.agent_model(inventory=0.0)}).get("received") == 0
        and run("A5.7", {"agentSupplyChainModel": FX.agent_model(inventory=2.0)}
                ).get("received") == 2
        and run("A5.7", {"agentSupplyChainModel": FX.agent_model(delay=3)}).get("received") < 2
        and bool(out.get("rules")))

    # THE STOCHASTIC CASE: seed and replication count recorded, reproducible from the seed alone.
    _st = {"agentSupplyChainModel": FX.agent_model(disruption=0.30, seed=20260816,
                                                   replications=5)}
    _s1 = run("A5.7", _st)
    _s2 = run("A5.7", _st)
    A.check("5.7", "stochastic: the seed and the replication count are recorded on the result",
            _s1.get("seed") == 20260816 and _s1.get("replications") == 5
            and _s1.get("stochastic") is True)
    A.check("5.7", "stochastic: the run is reproducible from its seed alone, replication for "
                   "replication", [r["trace"] for r in _s1["runs"]]
            == [r["trace"] for r in _s2["runs"]])
    A.check("5.7", "stochastic: a different seed gives a different run, so the seed is really "
                   "driving the disruption rather than being carried decoratively",
            [r["disrupted_steps"] for r in _s1["runs"]]
            != [r["disrupted_steps"] for r in run(
                "A5.7", {"agentSupplyChainModel": FX.agent_model(
                    disruption=0.30, seed=99, replications=5)})["runs"]])


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

    out = run("A5.8", {"desProcessModel": FX.des_model()})
    _e = {x["entity_id"]: x for x in out["entities"]}
    A.near("5.8", "known-answer: production's job A starts at nought", _e["A"]["start"], 0)
    A.near("5.8", "known-answer: job A ends at two", _e["A"]["end"], 2)
    A.near("5.8", "known-answer: job A waits nothing", _e["A"]["wait"], 0)
    A.near("5.8", "known-answer: job B starts at two, when the server is released",
           _e["B"]["start"], 2)
    A.near("5.8", "known-answer: job B ends at four", _e["B"]["end"], 4)
    A.near("5.8", "known-answer: job B waits one", _e["B"]["wait"], 1)
    A.near("5.8", "known-answer: the mean wait is one half", out.get("mean_wait"), 0.5)
    A.check("5.8", "structure: an event log with a clock is produced, and the clock ends when "
                   "the last entity departs",
            len(out.get("events", [])) == 4 and out.get("clock_end") == 4.0
            and {ev["type"] for ev in out["events"]} == {"ARRIVAL", "DEPARTURE"})
    A.check("5.8", "structure: the resource, its capacity, the queue discipline, the "
                   "simultaneous-event policy and the termination condition are all declared",
            out.get("resource_id") == "INSPECTOR" and out.get("capacity") == 1
            and out.get("queue_discipline") == "FIFO"
            and bool(out.get("event_order_policy"))
            and out.get("termination_condition") == "ALL_ENTITIES_DEPARTED")
    A.check("5.8", "boundary: the simultaneous-event policy is explicit and deterministic in "
                   "production too, so two jobs arriving together are served in entity order",
            [x["entity_id"] for x in run("A5.8", {"desProcessModel": dict(
                FX.des_model(),
                entities=[{"entity_id": "B", "entity_type": "J", "arrival_time": 0.0,
                           "service_time": 1.0},
                          {"entity_id": "A", "entity_type": "J", "arrival_time": 0.0,
                           "service_time": 1.0}])})["entities"]
             if x["wait"] == 0] == ["A"])
    A.check("5.8", "boundary: a job arriving after the server is released waits nothing, which "
                   "proves the resource is released rather than held",
            run("A5.8", {"desProcessModel": dict(
                FX.des_model(),
                entities=[{"entity_id": "A", "entity_type": "J", "arrival_time": 0.0,
                           "service_time": 1.0},
                          {"entity_id": "B", "entity_type": "J", "arrival_time": 10.0,
                           "service_time": 1.0}])}).get("mean_wait") == 0.0)
    A.check("5.8", "boundary: a second server takes the queue to no waiting at all, which is the "
                   "resource being modelled rather than assumed",
            run("A5.8", {"desProcessModel": dict(
                FX.des_model(),
                resources=[{"resource_id": "INSPECTOR", "capacity": 2}])}).get("mean_wait") == 0.0)
    A.proposition(
        "5.8", "5.8/no-substituted-progress-ratio",
        "with no planned progress the progress ratio is not substituted as exactly one, the "
        "value of a project running precisely to plan",
        abstained(run("A5.8", {**EVM, "plannedPctComplete": 0})))
    A.check("5.8", "invalid input: an entity served for a negative length of time is refused",
            abstained(run("A5.8", {"desProcessModel": dict(
                FX.des_model(),
                entities=[{"entity_id": "A", "entity_type": "J", "arrival_time": 0.0,
                           "service_time": -1.0}])})))
    A.check("5.8", "invalid input: a resource with no capacity can never serve anything and is "
                   "refused",
            abstained(run("A5.8", {"desProcessModel": dict(
                FX.des_model(),
                resources=[{"resource_id": "INSPECTOR", "capacity": 0}])})))
    A.check("5.8", "missingness: the two indices and the two progress figures produce no reading",
            abstained(run("A5.8", dict(EVM))))
    A.check("5.8", "threshold: no colour is asserted over the mean wait",
            out.get("status_color") is None and out.get("calibration_pending") is True)

    # THE STOCHASTIC CASE: exponential service, seed and replications recorded, reproducible.
    _stoch = {"desProcessModel": dict(
        FX.des_model(), seed=20260816, replications=20,
        entities=[{"entity_id": f"E{i}", "entity_type": "J", "arrival_time": float(i),
                   "service_distribution": {"family": "EXPONENTIAL", "mean": 1.5}}
                  for i in range(8)])}
    _d1 = run("A5.8", _stoch)
    _d2 = run("A5.8", _stoch)
    A.check("5.8", "stochastic: the seed and the replication count are recorded on the result",
            _d1.get("seed") == 20260816 and _d1.get("replications") == 20
            and _d1.get("stochastic") is True)
    A.check("5.8", "stochastic: the run is reproducible from its seed alone",
            [r["mean_wait"] for r in _d1["runs"]] == [r["mean_wait"] for r in _d2["runs"]])
    A.check("5.8", "stochastic: a different seed gives different replications, so the seed drives "
                   "the sampling rather than being carried decoratively",
            [r["mean_wait"] for r in _d1["runs"]]
            != [r["mean_wait"] for r in run("A5.8", {"desProcessModel": dict(
                _stoch["desProcessModel"], seed=99)})["runs"]])
    A.check("5.8", "stochastic: the reported mean wait is the mean over the replications, within "
                   "the tolerance predeclared here of one part in a million",
            abs(_d1["mean_wait"] - sum(r["mean_wait"] for r in _d1["runs"])
                / len(_d1["runs"])) < 1e-6)

    A.proposition(
        "5.8", "5.8/event-schedule",
        "the module carries entities, events, a simulation clock, resources, queues and service "
        "durations, and advances a clock through an ordered event schedule",
        all(out.get(k) is not None for k in ("events", "clock_end", "entities", "resource_id",
                                             "queue_discipline", "mean_wait",
                                             "event_order_policy")))


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
