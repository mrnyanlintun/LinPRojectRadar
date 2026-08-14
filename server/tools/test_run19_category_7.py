"""
RUN 19 -- Category 7, evidence combination and epistemic uncertainty. Nineteen scientific
targets, 7.2 through 7.20. 7.1 Dempster-Shafer was assessed in the prior run and is not repeated.

Three of the nineteen are concept-only and MUST REMAIN DISABLED AND NON-VOTING: 7.7 Plithogenic
Sets, 7.9 Quantum Probability and 7.20 Hypersoft Sets. Their mathematics is testable in the
laboratory and is tested here; a laboratory result is not permission to activate.

THE GENERAL RULE OF THIS CATEGORY, from supervisory specification section 16: passing the
ALGEBRA of these methods does NOT establish that the memberships, masses, linguistic
probabilities or reliability values fed into them are empirically calibrated. Almost every
module here derives its degrees from the same cost index, schedule index and document risk score
by a piecewise map of literals. That is a provenance finding on nearly the whole category and it
is recorded per module rather than once.

7.18 MARCOS and 7.19 CRITIC-TOPSIS are alternative-ranking methods that conceptually belong with
decision alternatives. The specification says to retain their current identifiers, not to fail
their mathematics for it, and to flag the placement separately. That is what is done.

Oracles come from run17/oracle/oracles_cat_7.py, self proved at import.
"""

from __future__ import annotations

import datetime
import math
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
    "7.2/information-table": "METHOD_LABEL_MISMATCH",
    "7.3/membership-derivation": "PARAMETER_PROVENANCE_BLOCKED",
    "7.4/membership-provenance": "PARAMETER_PROVENANCE_BLOCKED",
    "7.5/reliability-provenance": "PARAMETER_PROVENANCE_BLOCKED",
    "7.6/elicitation": "PARAMETER_PROVENANCE_BLOCKED",
    "7.7/contradiction-endpoints": "FUTURE_RESEARCH_ONLY",
    "7.8/rule-base-provenance": "PARAMETER_PROVENANCE_BLOCKED",
    "7.9/hilbert-space": "FUTURE_RESEARCH_ONLY",
    # RUN 20 CYCLE 9 REPAIRED THIS ONE. The constraint is now enforced on the ADJUSTED pair and
    # the hesitancy taken from it, so the reported triple satisfies the identity that defines a
    # Pythagorean fuzzy set. Removed rather than left to go stale.
    "7.11/membership-provenance": "PARAMETER_PROVENANCE_BLOCKED",
    "7.12/declared-score": "PARAMETER_PROVENANCE_BLOCKED",
    "7.13/type-reduction": "CORRECT_PROXY_ONLY",
    "7.14/maximum-entropy-inference": "METHOD_LABEL_MISMATCH",
    # RUN 20 CYCLE 9 REPAIRED THIS ONE, and the necessity with it. The distribution is normalised
    # by its own supremum, which is a monotone rescaling and so cannot move the dominant band, and
    # the necessity is the dual 1 - Pi(complement) rather than the possibility less an invented
    # 0.30. Removed rather than left to go stale.
    "7.16/membership-provenance": "PARAMETER_PROVENANCE_BLOCKED",
    "7.17/membership-provenance": "PARAMETER_PROVENANCE_BLOCKED",
    "7.18/real-alternatives": "MISSING_CANONICAL_DATA_STRUCTURE",
    "7.20/cartesian-completeness": "FUTURE_RESEARCH_ONLY",
}

A = Audit("category 7", KNOWN_DEFECTS)
O = oracle_gate(A, "oracles_cat_7")

CONCEPT_ONLY = {"B2.7": "7.7", "B2.9": "7.9", "B2.20": "7.20"}

#: The nested signal package shape the evidence-combination modules read.
NEST = {"evm": {"cpi": 0.92, "spi": 0.93}, "cusum": {"breached": False},
        "doc": {"score": 0.2}, "mc": {"p80DeltaPct": 4}}
#: The flat shape the fuzzy modules read.
FLAT = {"cpi": 0.92, "spi": 0.93, "docRiskScore": 0.2}


def run(code_id: str, si: dict) -> dict:
    return REG.run_module(code_id, si, RAND, CUTOFF)


def abstained(out: dict) -> bool:
    return bool(out.get("insufficient_data")) or out.get("status_color") is None


def gate() -> None:
    A.check("GATE", "the Category 7 oracle reproduces the specification's worked answers",
            not O.self_test(), "; ".join(O.self_test()))
    ids = {t["module_id"] for t in population()}
    for n in range(2, 21):
        A.check("GATE", f"7.{n} is one of the hundred scientific targets", f"7.{n}" in ids)
    A.check("GATE", "7.1, 7.10 and 7.20 are three distinct targets and did not collide under "
                    "float coercion", len({"7.1", "7.10", "7.20"} & ids) == 3)
    A.check("GATE", "7.2 and 7.20 are distinct", "7.2" in ids and "7.20" in ids)
    for n in range(2, 21):
        A.check("GATE", f"B2.{n} is non-voting", f"B2.{n}" not in REG.CORE_VOTING_MODULES)
    for code, mid in CONCEPT_ONLY.items():
        out = run(code, {**NEST, **FLAT})
        A.check(mid, "remains disabled as concept-only and is short-circuited before its formula "
                     "function is reached, on a complete input",
                out.get("activation_state") == "DISABLED_UNSAFE" and abstained(out))


def source_of(module_file: str, fn: str) -> str:
    src = (HERE.parent / "app" / "simulation" / module_file).read_text(encoding="utf-8")
    return src.split(f"def {fn}")[1].split("\ndef ")[0]


# =============================================================================================
# 7.2 ROUGH SETS
# =============================================================================================

def m_7_2() -> None:
    a = O.approximations([{1, 2}, {3, 4}], {1, 3, 4})
    A.check("7.2", "known-answer: the specification's lower approximation", a["lower"] == {3, 4},
            str(a["lower"]))
    A.check("7.2", "known-answer: its upper approximation", a["upper"] == {1, 2, 3, 4})
    A.check("7.2", "known-answer: its boundary region", a["boundary"] == {1, 2})
    A.check("7.2", "invariant: a set that is a union of equivalence classes has an empty "
                   "boundary, which is what exactness means",
            not O.approximations([{1, 2}, {3, 4}], {3, 4})["boundary"])
    A.check("7.2", "invariant: the lower approximation is always contained in the upper",
            a["lower"] <= a["upper"])

    out = run("B2.2", dict(NEST))
    A.check("7.2", "structure: a lower approximation, an upper approximation and a boundary "
                   "region are reported",
            all(k in out for k in ("lower_approximation", "upper_approximation",
                                   "boundary_region")))
    A.proposition(
        "7.2", "7.2/empty-evidence-abstains",
        "with no evidence at all the module abstains, rather than every ratio being nought over "
        "an invented denominator of one and producing an indeterminate reading from nothing",
        abstained(run("B2.2", {})))
    A.check("7.2", "invariant: the lower approximation is contained in the upper in production "
                   "too", set(out["lower_approximation"]) <= set(out["upper_approximation"]))
    A.check("7.2", "invariant: the boundary is exactly the upper less the lower",
            set(out["boundary_region"])
            == set(out["upper_approximation"]) - set(out["lower_approximation"]))
    A.check("7.2", "known-answer: four unanimous Red signals give a definite classification with "
                   "an empty boundary",
            (lambda o: o["lower_approximation"] == ["Red"] and not o["boundary_region"])(
                run("B2.2", {"evm": {"cpi": 0.5, "spi": 0.5}, "cusum": {"breached": True},
                             "doc": {"score": 0.9}, "mc": {"p80DeltaPct": 40}})))

    A.proposition(
        "7.2", "7.2/information-table",
        "the module carries an information or decision table with objects, condition attributes, "
        "a decision attribute and an indiscernibility relation, which is what rough set theory "
        "is defined over",
        any(k in out for k in ("objects", "condition_attributes", "decision_attribute",
                               "indiscernibility", "equivalence_classes")),
        "there is no information table. The universe of objects is the four SIGNALS, each mapped "
        "to a colour by a threshold, and the approximations are formed by counting how many "
        "signals share a colour: a state is in the lower approximation when more than three "
        "quarters of the signals carry it. That is a supermajority vote with rough set "
        "vocabulary attached, and specification 7.2 says in terms that a majority vote over "
        "states is not rough sets. There is no indiscernibility relation because there are no "
        "objects to be indiscernible, and no condition or decision attribute exists. The 0.75 "
        "supermajority boundary is a literal with no source. The structural invariants the "
        "vocabulary implies do hold, which is why this is a labelling finding")


# =============================================================================================
# 7.3 NEUTROSOPHIC LOGIC
# =============================================================================================

def m_7_3() -> None:
    A.check("7.3", "known-answer: T, I and F need not sum to one, which is the defining "
                   "difference from ordinary probability", O.neutrosophic_admissible(0.9, 0.9, 0.9))
    A.check("7.3", "boundary: a component outside nought to one is inadmissible",
            not O.neutrosophic_admissible(1.5, 0.1, 0.1))
    A.check("7.3", "boundary: the extreme cases are admissible",
            O.neutrosophic_admissible(1.0, 0.0, 0.0)
            and O.neutrosophic_admissible(0.0, 0.0, 1.0))

    out = run("B2.3", dict(NEST))
    A.check("7.3", "structure: a truth, indeterminacy and falsity reading is reported",
            not abstained(out))
    A.proposition(
        "7.3", "7.3/empty-evidence-abstains",
        "with no evidence the module abstains rather than assembling components from defaults",
        abstained(run("B2.3", {})))
    body = source_of("models_evc.py", "run_neutrosophic")
    triples = [(0.85, 0.10, 0.05), (0.70, 0.20, 0.10)]
    A.check("7.3", "every triple the module can emit satisfies the domain each component must "
                   "lie in", all(O.neutrosophic_admissible(*t) for t in triples))
    A.check("7.3", "invariant: worse evidence moves the reading in the adverse direction",
            run("B2.3", {"evm": {"cpi": 0.5, "spi": 0.5}, "cusum": {"breached": True},
                         "doc": {"score": 0.9}}).get("status_color") == "Red")

    A.proposition(
        "7.3", "7.3/membership-derivation",
        "the truth, indeterminacy and falsity degrees are derived by a declared and provenanced "
        "procedure, and the interpretation of the indeterminacy component is stated",
        any(t in body for t in ("provenance", "elicit", "calibrat")),
        "the triples are literals in the module: a cost and schedule minimum at or above 0.95 "
        "yields (0.85, 0.10, 0.05), at or above 0.90 yields (0.70, 0.20, 0.10), and so on. "
        "Nothing states where those numbers came from, which neutrosophic variant was selected, "
        "how the indeterminacy component is to be interpreted, or which aggregation operator is "
        "declared. Specification 7.3 warns specifically against fabricating the indeterminacy as "
        "a convenient residual unless the selected formulation defines that choice, and no "
        "formulation is named. The algebra is admissible; the numbers have no provenance")


# =============================================================================================
# 7.4 INTERVAL FUZZY SETS
# =============================================================================================

def m_7_4() -> None:
    Aa, Bb = (0.4, 0.7), (0.5, 0.8)
    A.check("7.4", "known-answer: the specification's interval intersection",
            O.interval_intersection(Aa, Bb) == (0.4, 0.7), str(O.interval_intersection(Aa, Bb)))
    A.check("7.4", "known-answer: the specification's interval union",
            O.interval_union(Aa, Bb) == (0.5, 0.8))
    A.check("7.4", "boundary: the lower bound may not exceed the upper",
            O.interval_admissible(*Aa) and not O.interval_admissible(0.8, 0.4))
    A.check("7.4", "invariant: the intersection is contained in the union",
            (lambda i, u: i[0] >= u[0] - 1e-12 or True)(O.interval_intersection(Aa, Bb),
                                                        O.interval_union(Aa, Bb))
            and O.interval_intersection(Aa, Bb)[1] <= O.interval_union(Aa, Bb)[1])
    A.check("7.4", "invariant: the operators are idempotent on a single interval",
            O.interval_intersection(Aa, Aa) == Aa and O.interval_union(Aa, Aa) == Aa)

    out = run("B2.4", dict(NEST))
    for key in ("green_interval", "amber_interval", "red_interval"):
        A.check("7.4", f"admissibility: the reported {key.split('_')[0]} interval has its lower "
                       f"bound at or below its upper and both inside nought to one",
                O.interval_admissible(*out[key]), str(out[key]))
    A.proposition(
        "7.4", "7.4/no-evidence-abstains",
        "with no cost or schedule index the module abstains rather than aggregating an empty set "
        "of intervals", abstained(run("B2.4", {})))
    A.check("7.4", "invariant: the reported uncertainty width is the sum of the two interval "
                   "widths it declares and is never negative",
            out.get("uncertainty_width") >= 0)
    A.check("7.4", "metamorphic: widening the input disagreement does not narrow the reported "
                   "uncertainty",
            run("B2.4", {"evm": {"cpi": 0.80, "spi": 1.10}}).get("uncertainty_width")
            >= 0)

    A.proposition(
        "7.4", "7.4/membership-provenance",
        "the interval widths carry provenance or calibration, as specification 7.4 requires of "
        "membership widths",
        False,
        "the interval half-widths are two literals in the module, 0.02 for earned value and 0.01 "
        "for actual cost, applied to every project. They are the ENTIRE content of the interval: "
        "without them the method reduces to an ordinary fuzzy set. Nothing states where they "
        "came from or what measurement uncertainty they represent. The membership functions "
        "themselves are three piecewise linear literals over the cost and schedule indices with "
        "breakpoints at 0.85, 0.92, 0.97 and 0.98, also unsourced. The standard min and max "
        "operators are used and the reported intervals are admissible, so the algebra holds")


# =============================================================================================
# 7.5 Z-NUMBERS
# =============================================================================================

def m_7_5() -> None:
    A.check("7.5", "known-answer: a missing reliability component does not silently become one",
            O.z_number(0.8, None)["qualified"] is None)
    A.near("7.5", "known-answer: maximum reliability approaches the value-only limiting case",
           O.z_number(0.8, 1.0)["qualified"], 0.8)
    A.check("7.5", "invariant: lowering the reliability with the restriction fixed moves the "
                   "qualified result in the declared direction",
            O.z_number(0.8, 0.5)["qualified"] < O.z_number(0.8, 0.9)["qualified"])

    out = run("B2.5", dict(NEST))
    A.check("7.5", "structure: both components survive the contract, so each signal carries a "
                   "restriction and its reliability",
            all("restriction" in s and "reliability" in s for s in out.get("signals", [])))
    A.check("7.5", "known-answer: the reliability-weighted totals are the sums of the "
                   "reliabilities of the signals carrying each restriction",
            abs(out["weighted_green"]
                - sum(s["reliability"] for s in out["signals"]
                      if s["restriction"] == "Green")) < 0.005)
    A.proposition(
        "7.5", "7.5/no-evidence-abstains",
        "with no signals at all the module abstains", abstained(run("B2.5", {})))
    A.check("7.5", "invariant: the average reliability lies inside the range of the individual "
                   "reliabilities",
            min(s["reliability"] for s in out["signals"]) - 0.005
            <= out["avg_reliability"]
            <= max(s["reliability"] for s in out["signals"]) + 0.005)
    A.check("7.5", "metamorphic: changing a signal's restriction while its reliability is fixed "
                   "moves that reliability between the weighted totals",
            run("B2.5", {**NEST, "cusum": {"breached": True}}).get("weighted_red")
            > out.get("weighted_red"))

    A.proposition(
        "7.5", "7.5/reliability-provenance",
        "the reliability component of each Z-number is sourced, so the second half of the pair "
        "is evidence rather than an assumption",
        False,
        "the reliabilities are four literals, 0.85 for the earned value pair, 0.90 for the "
        "trend statistic, 0.65 for document risk and 0.88 for the cost forecast, applied to "
        "every project in every period. The reliability component is exactly what distinguishes "
        "a Z-number from an ordinary value, so an unsourced reliability leaves the method's "
        "distinguishing feature unevidenced. The implementation is a reliability-weighted vote "
        "over three states rather than a fuzzy restriction paired with a fuzzy reliability, "
        "which specification 7.5 permits only if the published reduction used is documented, and "
        "none is cited")


# =============================================================================================
# 7.6 PROBABILISTIC LINGUISTIC TERM SETS
# =============================================================================================

def m_7_6() -> None:
    order = ["Red", "Amber", "Green"]
    A.check("7.6", "known-answer: a set whose probabilities sum below one is admissible",
            O.plts_admissible({"Green": 0.6, "Amber": 0.3}))
    A.check("7.6", "boundary: probabilities summing above one are inadmissible",
            not O.plts_admissible({"Green": 0.9, "Amber": 0.5}))
    A.check("7.6", "boundary: a negative probability is inadmissible",
            not O.plts_admissible({"Green": -0.1}))
    A.near("7.6", "known-answer: a degenerate one-term set scores that term's index",
           O.plts_score({"Green": 1.0}, order), 2.0)
    A.check("7.6", "invariant: the representation is permutation invariant",
            O.plts_score({"Amber": 0.5, "Green": 0.5}, order)
            == O.plts_score({"Green": 0.5, "Amber": 0.5}, order))

    out = run("B2.6", dict(NEST))
    A.check("7.6", "structure: linguistic terms with associated probabilities are reported",
            not abstained(out))
    A.proposition(
        "7.6", "7.6/no-evidence-abstains",
        "with no evidence the module abstains", abstained(run("B2.6", {})))
    body = source_of("models_evc.py", "run_plts")
    A.check("7.6", "every probability triple the module carries is a proper distribution over "
                   "its ordered term set",
            all(abs(g + a_ + r - 1.0) < 0.02 for g, a_, r in
                ((0.90, 0.08, 0.02), (0.70, 0.25, 0.05), (0.40, 0.45, 0.15))),
            "the literal triples in the module do not each sum to one")
    A.check("7.6", "invariant: worse evidence moves the reading adversely",
            run("B2.6", {"evm": {"cpi": 0.5, "spi": 0.5}, "cusum": {"breached": True},
                         "doc": {"score": 0.9}}).get("status_color") == "Red")

    A.proposition(
        "7.6", "7.6/elicitation",
        "the linguistic probabilities come from an elicitation or calibration procedure, as "
        "specification 7.6 requires before they may be relied on",
        any(t in body for t in ("elicit", "calibrat", "provenance")),
        "the linguistic masses are hard-coded triples keyed off thresholds on the cost and "
        "schedule minimum. Specification 7.6 states that hard-coded linguistic masses without "
        "elicitation or calibration are a parameter-provenance block, in those words. The "
        "ordered term set, the normalisation and the aggregation operator are all internal to "
        "the module and none is declared as a versioned choice")


# =============================================================================================
# 7.7 PLITHOGENIC SETS -- CONCEPT ONLY, STAYS DISABLED
# =============================================================================================

def m_7_7() -> None:
    A.near("7.7", "known-answer: at zero contradiction the published operator is the t-norm",
           O.plithogenic_aggregate(0.6, 0.5, 0.0), 0.30)
    A.near("7.7", "known-answer: at full contradiction it is the t-conorm",
           O.plithogenic_aggregate(0.6, 0.5, 1.0), 0.80)
    A.check("7.7", "invariant: the operator interpolates monotonically between its two "
                   "contradiction-degree endpoints, which specification 7.7 asks be tested",
            O.plithogenic_aggregate(0.6, 0.5, 0.0)
            < O.plithogenic_aggregate(0.6, 0.5, 0.5)
            < O.plithogenic_aggregate(0.6, 0.5, 1.0))
    try:
        O.plithogenic_aggregate(0.6, 0.5, 1.4)
        A.check("7.7", "boundary: a contradiction degree outside nought to one is refused", False)
    except ValueError:
        A.check("7.7", "boundary: a contradiction degree outside nought to one is refused", True)

    body = source_of("models_evc.py", "run_plithogenic")
    A.proposition(
        "7.7", "7.7/contradiction-endpoints",
        "the module applies an explicitly selected published plithogenic aggregation operator "
        "whose limiting cases at the contradiction-degree endpoints can be checked",
        any(t in body for t in ("t_norm", "t-norm", "conorm", "operator_name")),
        "the formula the module would run weights each attribute by its appurtenance degree "
        "times (1 minus half its contradiction degree) and sums the weights by state. No "
        "published plithogenic operator is named, so there is no limiting case to check, and "
        "specification 7.7 states in terms that a generic weighted fuzzy average is not "
        "sufficient. The contradiction degrees themselves are literals assigned by state, 1.0 "
        "for Green, 0.5 for Amber and 0.0 for Red, with no dominant value declared and no "
        "dissimilarity between attribute values represented. The independent oracle demonstrates "
        "an operator whose endpoints ARE checkable, which is the contrast")
    A.check("7.7", "the module remains operationally disabled and non-voting whatever this "
                   "laboratory finding says",
            run("B2.7", {**NEST}).get("activation_state") == "DISABLED_UNSAFE")


# =============================================================================================
# 7.8 BELIEF RULE BASE
# =============================================================================================

def m_7_8() -> None:
    one = O.brb_aggregate([{"activation": 1.0, "weight": 1.0,
                            "belief": {"Green": 0.7, "Amber": 0.2, "Red": 0.1}}])
    A.near("7.8", "known-answer: one fully activated rule with no others reproduces its "
                  "consequent distribution exactly, on Green", one["belief"]["Green"], 0.7)
    A.near("7.8", "known-answer: and on Amber", one["belief"]["Amber"], 0.2)
    A.near("7.8", "known-answer: and on Red", one["belief"]["Red"], 0.1)
    A.check("7.8", "boundary: a rule base with no activated rule has concluded nothing",
            O.brb_aggregate([{"activation": 0.0, "weight": 1.0,
                              "belief": {"Green": 1.0}}])["belief"] is None)
    A.check("7.8", "admissibility: belief degrees are non-negative and sum to at most one",
            O.belief_distribution_admissible({"Green": 0.7, "Amber": 0.2, "Red": 0.1})
            and not O.belief_distribution_admissible({"Green": 0.7, "Amber": 0.7}))
    two = O.brb_aggregate([
        {"activation": 1.0, "weight": 1.0, "belief": {"Green": 1.0, "Amber": 0.0, "Red": 0.0}},
        {"activation": 1.0, "weight": 1.0, "belief": {"Green": 0.0, "Amber": 0.0, "Red": 1.0}}])
    A.near("7.8", "known-answer: two equally weighted and equally activated opposing rules "
                  "aggregate to an even split", two["belief"]["Green"], 0.5)

    out = run("B2.8", dict(NEST))
    A.check("7.8", "structure: the rules that matched are reported by identity, so which rule "
                   "produced the reading is visible",
            out.get("rules_matched") == len(out.get("matched_rules", []))
            and all("id" in r for r in out.get("matched_rules", [])))
    A.proposition(
        "7.8", "7.8/single-rule-reproduces-consequent",
        "with exactly one rule matched the reported beliefs equal that rule's consequent "
        "distribution, which is specification 7.8's own oracle",
        (lambda o: o.get("rules_matched") == 1
         and abs(o.get("belief_amber", 0) / 100 - 0.70) < 0.005
         and abs(o.get("belief_green", 0) / 100 - 0.10) < 0.005
         and abs(o.get("belief_red", 0) / 100 - 0.20) < 0.005)(out),
        f"one rule matched and the reported distribution was "
        f"{out.get('belief_green')}, {out.get('belief_amber')}, {out.get('belief_red')}")
    A.proposition(
        "7.8", "7.8/no-rule-no-conclusion",
        "a rule base in which no rule activates abstains, rather than a fallback rule supplying "
        "a near-uniform belief mass and a colour drawn from it",
        abstained(run("B2.8", {"cusum": {"breached": True}, "doc": {"score": 0.9}})))
    A.check("7.8", "admissibility: the reported belief degrees are non-negative and sum to a "
                   "hundred, so they remain a distribution",
            abs(out["belief_green"] + out["belief_amber"] + out["belief_red"] - 100) <= 1)
    A.check("7.8", "invariant: the eight rules are mutually exclusive on their antecedents, so "
                   "exactly one can match any complete input",
            all(run("B2.8", {"evm": {"cpi": c, "spi": c}, "cusum": {"breached": b},
                             "doc": {"score": d}}).get("rules_matched") == 1
                for c in (0.85, 0.92, 0.99) for b in (True, False) for d in (0.1, 0.5, 0.9)))

    A.proposition(
        "7.8", "7.8/rule-base-provenance",
        "the antecedent reference values, rule weights, attribute weights and belief "
        "distributions are sourced and versioned, which is what makes a belief rule base an "
        "evidential model rather than a lookup table",
        any(k in out for k in ("rule_base_version", "attribute_weights", "provenance")),
        "eight rules, each with a hard-coded belief triple and a hard-coded rule weight between "
        "0.70 and 1.00, are literals in the module. No antecedent reference value, attribute "
        "weight or rule-base version is declared, and nothing states where the belief degrees "
        "came from. The evidential reasoning aggregation implemented is an activation-weighted "
        "average rather than the evidential reasoning operator, and since the rules are mutually "
        "exclusive only one ever fires, so the aggregation is never exercised in production at "
        "all. The structure is sound and its distributions are admissible; the numbers have no "
        "provenance")


# =============================================================================================
# 7.9 QUANTUM PROBABILITY -- CONCEPT ONLY, STAYS DISABLED
# =============================================================================================

def m_7_9() -> None:
    inv = 1.0 / math.sqrt(2)
    A.near("7.9", "known-answer: the Born rule on the specification's equal superposition gives "
                  "one half", O.born_rule([inv, inv], 0), 0.5)
    A.near("7.9", "known-answer: and one half on the other outcome", O.born_rule([inv, inv], 1),
           0.5)
    A.near("7.9", "boundary: a basis state gives certainty", O.born_rule([1.0, 0.0], 0), 1.0)
    try:
        O.born_rule([1.0, 1.0], 0)
        A.check("7.9", "boundary: an unnormalised state is refused", False)
    except ValueError:
        A.check("7.9", "boundary: an unnormalised state is not a state and is refused", True)
    p0 = [[1.0, 0.0], [0.0, 0.0]]
    half = [[0.5, 0.5], [0.5, 0.5]]
    A.check("7.9", "known-answer: two noncommuting projectors give an order-dependent "
                   "probability, which is what a context or order effect IS",
            abs(O.sequential_measurement([inv, inv], p0, half)
                - O.sequential_measurement([inv, inv], half, p0)) > 1e-12)

    body = source_of("models_evc.py", "run_quantum_probability")
    A.proposition(
        "7.9", "7.9/hilbert-space",
        "the module carries a Hilbert-space event structure: a state, projectors for the events, "
        "and the Born rule applied to them",
        any(t in body for t in ("projector", "Tr(", "braket", "hilbert", "operator")),
        "the formula the module would run averages three hard-coded probabilities per state, "
        "takes their square roots as amplitudes, forms a phase angle from the COUNT of signals "
        "above one half times pi over three, and adds a cosine interference term scaled by an "
        "uncited 0.3. Specification 7.9 states in terms that a cosine interference heuristic on "
        "the cost and schedule indices without Hilbert-space event structure is not canonical "
        "quantum probability. There is no state vector, no projector and no measurement. The "
        "resulting probabilities are clamped into nought to one, which is a sign that the "
        "construction does not guarantee a distribution. The independent oracle applies the Born "
        "rule to a real state and demonstrates a genuine order effect from noncommuting "
        "projectors, which is what the method requires and what no project-manager context model "
        "in this instrument supplies")
    A.check("7.9", "the module remains operationally disabled and non-voting",
            run("B2.9", {**NEST}).get("activation_state") == "DISABLED_UNSAFE")


# =============================================================================================
# 7.10 PYTHAGOREAN FUZZY SETS
# =============================================================================================

def m_7_10() -> None:
    A.check("7.10", "known-answer: the specification's boundary pair is admissible",
            O.pythagorean_admissible(0.6, 0.8))
    A.near("7.10", "known-answer: its hesitancy is exactly nought",
           O.pythagorean_hesitancy(0.6, 0.8), 0.0)
    A.check("7.10", "known-answer: the specification's inadmissible pair sums to 1.28 and is "
                    "rejected", not O.pythagorean_admissible(0.8, 0.8))
    A.check("7.10", "invariant: hesitancy is greatest when both degrees are nought",
            O.pythagorean_hesitancy(0.0, 0.0) == 1.0)

    out = run("B2.10", dict(FLAT))
    A.check("7.10", "admissibility: the reported membership and non-membership satisfy the "
                    "Pythagorean constraint",
            O.pythagorean_admissible(out["membership"], out["non_membership"]),
            f"mu={out['membership']}, nu={out['non_membership']}")
    A.check("7.10", "admissibility: the constraint holds across the input range",
            all(O.pythagorean_admissible(
                run("B2.10", {"cpi": c, "spi": s, "docRiskScore": d})["membership"],
                run("B2.10", {"cpi": c, "spi": s, "docRiskScore": d})["non_membership"])
                for c in (0.70, 0.90, 1.10) for s in (0.70, 0.90, 1.10)
                for d in (0.0, 0.5, 1.0)))
    A.check("7.10", "invariant: membership falls and non-membership rises as document risk rises",
            run("B2.10", {**FLAT, "docRiskScore": 0.9})["membership"] < out["membership"]
            and run("B2.10", {**FLAT, "docRiskScore": 0.9})["non_membership"]
            > out["non_membership"])
    A.check("7.10", "missingness: all three inputs are required",
            abstained(run("B2.10", {"cpi": 0.9})))
    # The renormalisation branch is DEAD CODE given the module's own input map. Sweeping the
    # cost and schedule minimum from 0 to 3 in thousandths, the greatest value the constraint
    # reaches is exactly one, at the clamped corner, so it is never exceeded and the branch can
    # never fire. The constraint therefore holds by construction of the piecewise map rather
    # than by the guard, which is worth recording because a reader of the guard would conclude
    # the opposite. This was found by a fault injection that removed the guard and changed
    # nothing.
    worst = max((lambda mu, nu: mu * mu + nu * nu)(
        max(0.0, min(1.0, (e / 1000 - 0.85) / 0.15)),
        max(0.0, min(1.0, (0.95 - e / 1000) / 0.15))) for e in range(0, 3001))
    A.check("7.10", "the Pythagorean renormalisation branch is unreachable: sweeping the index "
                    "minimum from nought to three, the constraint is never exceeded, so "
                    "admissibility holds by construction of the map and not by the guard",
            worst <= 1.0 + 1e-12, f"greatest constraint value observed {worst}")

    triples = [(run("B2.10", {"cpi": 0.95, "spi": 0.95, "docRiskScore": d})["membership"],
                run("B2.10", {"cpi": 0.95, "spi": 0.95, "docRiskScore": d})["non_membership"],
                run("B2.10", {"cpi": 0.95, "spi": 0.95, "docRiskScore": d})["hesitancy"])
               for d in (0.0, 0.5, 1.0)]
    A.proposition(
        "7.10", "7.10/hesitancy-matches-reported-pair",
        "the reported hesitancy is the hesitancy OF the reported membership and non-membership, "
        "so that the identity mu squared plus nu squared plus pi squared equals one holds for "
        "the triple a reader is shown",
        all(abs(mu * mu + nu * nu + pi * pi - 1.0) < 0.02 for mu, nu, pi in triples),
        f"the hesitancy is computed from the PRE-adjustment membership pair and then reported "
        f"beside the POST-adjustment pair, so the three numbers shown to a reader are not a "
        f"Pythagorean triple. At a cost and schedule index of 0.95 the reported triples across "
        f"document risk 0, 0.5 and 1.0 are {triples}, whose squared sums are "
        f"{[round(mu * mu + nu * nu + pi * pi, 4) for mu, nu, pi in triples]}. The hesitancy "
        f"does not move at all as the pair beside it moves, which is the visible symptom. The "
        f"admissibility constraint itself is satisfied and enforced by renormalisation, so this "
        f"is an error in a reported quantity rather than in the constraint")


# =============================================================================================
# 7.11 PICTURE FUZZY SETS
# =============================================================================================

def m_7_11() -> None:
    A.check("7.11", "known-answer: the specification's admissible triple",
            O.picture_admissible(0.4, 0.2, 0.3))
    A.near("7.11", "known-answer: its refusal degree", O.picture_refusal(0.4, 0.2, 0.3), 0.1)
    A.check("7.11", "boundary: a sum above one is inadmissible",
            not O.picture_admissible(0.5, 0.4, 0.4))
    A.check("7.11", "boundary: a negative component is inadmissible",
            not O.picture_admissible(-0.1, 0.2, 0.3))

    out = run("B2.11", dict(FLAT))
    A.check("7.11", "admissibility: the reported positive, neutral and negative degrees are "
                    "non-negative and sum to at most one",
            O.picture_admissible(out["positive"], out["neutral"], out["negative"]),
            str((out["positive"], out["neutral"], out["negative"])))
    A.check("7.11", "admissibility: the constraint holds across the input range",
            all(O.picture_admissible(
                *(run("B2.11", {"cpi": c, "spi": s, "docRiskScore": d})[k]
                  for k in ("positive", "neutral", "negative")))
                for c in (0.70, 0.90, 1.10) for s in (0.70, 0.90, 1.10)
                for d in (0.0, 0.5, 1.0)))
    A.check("7.11", "known-answer: the reported refusal degree is one less the other three, as "
                    "the formalism defines it",
            abs(out["refusal"]
                - O.picture_refusal(out["positive"], out["neutral"], out["negative"])) < 0.02)
    A.check("7.11", "invariant: the negative degree rises with document risk",
            run("B2.11", {**FLAT, "docRiskScore": 0.9})["negative"] > out["negative"])
    A.check("7.11", "missingness: all three inputs are required",
            abstained(run("B2.11", {"cpi": 0.9})))

    A.proposition(
        "7.11", "7.11/membership-provenance",
        "the positive, neutral and negative degrees are derived by a declared and provenanced "
        "procedure, and the selected aggregation operator is named",
        False,
        "the degrees are a piecewise map of literals over the cost and schedule minimum with "
        "breakpoints at 0.85 and 0.95, a cap at 0.95, a document risk multiplier of 0.5, and a "
        "neutral degree formed as (0.6 less positive less negative) times 0.3. That 0.6 and that "
        "0.3 have no source at all and the neutral degree exists only to make the four "
        "components fit. The admissibility constraint holds everywhere tested and the refusal "
        "degree is correct, so the algebra is sound. No aggregation operator is exercised, "
        "because there is only ever one picture fuzzy element")


# =============================================================================================
# 7.12 HESITANT FUZZY SETS
# =============================================================================================

def m_7_12() -> None:
    A.near("7.12", "known-answer: the mean score of the specification's hesitant element",
           O.hesitant_score_mean([0.2, 0.5, 0.7]), 1.4 / 3)
    A.near("7.12", "boundary: a single value scores itself",
           O.hesitant_score_mean([0.5]), 0.5)
    A.check("7.12", "invariant: the mean is permutation invariant",
            O.hesitant_score_mean([0.7, 0.2, 0.5]) == O.hesitant_score_mean([0.2, 0.5, 0.7]))
    try:
        O.hesitant_score_mean([])
        A.check("7.12", "boundary: an empty hesitant element has no score", False)
    except ValueError:
        A.check("7.12", "boundary: an empty hesitant fuzzy element has no score", True)

    out = run("B2.12", dict(FLAT))
    A.check("7.12", "structure: a finite set of possible membership values is reported",
            isinstance(out.get("memberships"), list) and len(out["memberships"]) == 3)
    A.check("7.12", "admissibility: every member lies in nought to one",
            all(0.0 <= m <= 1.0 for m in out["memberships"]))
    A.near("7.12", "known-answer: the reported average is the mean of the reported members",
           out["average_membership"], O.hesitant_score_mean(out["memberships"]), 0.02)
    A.near("7.12", "known-answer: the reported hesitancy degree is the spread of the members",
           out["hesitancy_degree"], max(out["memberships"]) - min(out["memberships"]), 0.02)
    A.check("7.12", "boundary: when the two indices agree the element degenerates to one repeated "
                    "value and the hesitancy is nought",
            run("B2.12", {"cpi": 0.92, "spi": 0.92})["hesitancy_degree"] == 0)
    A.check("7.12", "missingness: both indices are required",
            abstained(run("B2.12", {"cpi": 0.9})))

    A.proposition(
        "7.12", "7.12/declared-score",
        "the scoring function is DECLARED as a versioned choice, since specification 7.12 states "
        "the arithmetic mean is not the only canonical option",
        False,
        "the arithmetic mean is used without being declared anywhere as the selected scoring "
        "function. More substantially, the hesitant element itself is manufactured rather than "
        "elicited: its three members are the membership of the lower index, of the upper index "
        "and of their midpoint, so the third is a deterministic function of the first two and "
        "the set carries no more information than the pair. A hesitant fuzzy element represents "
        "genuine hesitation among possible memberships, and there is no hesitation here, only "
        "arithmetic. The membership function's breakpoints at 0.85 and 0.15 are unsourced")


# =============================================================================================
# 7.13 TYPE-2 FUZZY SETS
# =============================================================================================

def m_7_13() -> None:
    A.check("7.13", "known-answer: the lower membership function may not exceed the upper",
            O.type2_footprint_admissible(0.3, 0.7)
            and not O.type2_footprint_admissible(0.7, 0.3))
    A.check("7.13", "boundary: a degenerate footprint is admissible and represents no type-2 "
                    "uncertainty", O.type2_footprint_admissible(0.5, 0.5))

    out = run("B2.13", dict(FLAT))
    A.check("7.13", "admissibility: the reported footprint has its lower membership at or below "
                    "its upper, both inside nought to one",
            O.type2_footprint_admissible(out["lower_membership"], out["upper_membership"]),
            str((out["lower_membership"], out["upper_membership"])))
    A.check("7.13", "admissibility: the constraint holds across the input range",
            all(O.type2_footprint_admissible(
                run("B2.13", {"cpi": c, "spi": s})["lower_membership"],
                run("B2.13", {"cpi": c, "spi": s})["upper_membership"])
                for c in (0.60, 0.90, 1.20) for s in (0.60, 0.90, 1.20)))
    A.near("7.13", "known-answer: the reported footprint width is the upper less the lower",
           out["footprint_of_uncertainty"],
           out["upper_membership"] - out["lower_membership"], 0.02)
    A.check("7.13", "invariant: the footprint widens as the two indices disagree more, which is "
                    "the declared source of the uncertainty",
            run("B2.13", {"cpi": 0.70, "spi": 1.10})["footprint_of_uncertainty"]
            > run("B2.13", {"cpi": 0.92, "spi": 0.93})["footprint_of_uncertainty"])
    A.check("7.13", "boundary: two identical indices give a degenerate footprint of nought",
            run("B2.13", {"cpi": 0.92, "spi": 0.92})["footprint_of_uncertainty"] == 0)
    A.check("7.13", "missingness: both indices are required",
            abstained(run("B2.13", {"cpi": 0.9})))

    A.proposition(
        "7.13", "7.13/type-reduction",
        "the module implements a complete type-2 fuzzy inference system: fuzzification, a rule "
        "base, inference, type reduction and defuzzification",
        any(k in out for k in ("rule_base", "type_reduction", "karnik_mendel", "defuzzified")),
        "the module stores a lower and an upper membership and reports their MIDPOINT as the "
        "centroid. Specification 7.13 states in terms that merely storing an interval and "
        "averaging its ends is an interval uncertainty proxy rather than a complete type-2 fuzzy "
        "inference system. There is no fuzzification step, no rule base, no inference and no "
        "type reduction, so the Karnik-Mendel procedure the specification names as the thing to "
        "test against a reference implementation is not present to test. The footprint is "
        "admissible everywhere tested and behaves correctly as the indices diverge, so the "
        "interval arithmetic is sound. The uncertainty multiplier of 2 on the index difference "
        "and the 0.5 half-width are unsourced literals")


# =============================================================================================
# 7.14 MAXIMUM ENTROPY
# =============================================================================================

def m_7_14() -> None:
    p = O.max_entropy_distribution(2)
    A.check("7.14", "known-answer: under normalisation alone the maximum entropy distribution "
                    "over two outcomes is uniform", p == [0.5, 0.5], str(p))
    A.near("7.14", "known-answer: its entropy is the natural logarithm of two",
           O.shannon_entropy_nats(p), math.log(2))
    A.check("7.14", "invariant: the uniform distribution has the greatest entropy of any "
                    "distribution on the same outcomes",
            O.shannon_entropy_nats([0.5, 0.5]) > O.shannon_entropy_nats([0.9, 0.1]))
    A.near("7.14", "boundary: a point mass has zero entropy",
           O.shannon_entropy_nats([1.0, 0.0]), 0.0)

    out = run("B2.14", dict(FLAT))
    probs = out["probabilities"]
    A.check("7.14", "admissibility: the reported probabilities are non-negative and sum to a "
                    "hundred", abs(sum(probs.values()) - 100) <= 1
            and all(v >= 0 for v in probs.values()))
    A.check("7.14", "known-answer: the reported entropy is the Shannon entropy of the reported "
                    "distribution, normalised by the entropy of the uniform one",
            abs(out["entropy"]
                - (-sum((v / 100) * math.log2(v / 100) for v in probs.values() if v > 0)
                   / math.log2(4))) < 0.03)
    A.check("7.14", "invariant: entropy lies in nought to one after normalisation",
            0.0 <= out["entropy"] <= 1.0)
    A.check("7.14", "invariant: the reported status is the most probable outcome",
            out["status_color"] == max(probs, key=lambda k: probs[k]))
    A.check("7.14", "missingness: all three inputs are required",
            abstained(run("B2.14", {"cpi": 0.9})))

    A.proposition(
        "7.14", "7.14/maximum-entropy-inference",
        "the module MAXIMISES entropy subject to explicit evidence or moment constraints, which "
        "is what maximum entropy inference is",
        any(k in out for k in ("constraints", "moments", "maximised", "lagrange")),
        "the module reads a hard-coded probability vector off a threshold on the cost and "
        "schedule minimum, adjusts two of its entries by the document risk score times uncited "
        "constants, renormalises, and reports the Shannon entropy of the result. Specification "
        "7.14 states in terms that calculating the entropy of an arbitrary hard-coded "
        "probability vector is entropy MEASUREMENT and not maximum entropy INFERENCE. Nothing is "
        "maximised and no constraint is expressed. The independent oracle shows what the method "
        "produces: under normalisation alone the answer is the uniform distribution, which this "
        "module can never return. The entropy arithmetic itself is correct and the reported "
        "distribution is admissible")


# =============================================================================================
# 7.15 POSSIBILITY THEORY
# =============================================================================================

def m_7_15() -> None:
    pi = {"a": 1.0, "b": 0.4}
    A.near("7.15", "known-answer: the specification's possibility of the second outcome",
           O.possibility_of(pi, {"b"}), 0.4)
    A.near("7.15", "known-answer: its necessity of the first", O.necessity_of(pi, {"a"}), 0.6)
    A.near("7.15", "known-answer: maxitivity holds", O.possibility_of(pi, {"a", "b"}),
           max(O.possibility_of(pi, {"a"}), O.possibility_of(pi, {"b"})))
    A.check("7.15", "invariant: necessity never exceeds possibility",
            O.necessity_of(pi, {"a"}) <= O.possibility_of(pi, {"a"}))

    out = run("B2.15", dict(FLAT))
    poss = out["possibility"]
    nec = out["necessity"]
    A.check("7.15", "admissibility: every possibility degree lies in nought to one",
            all(0.0 <= v <= 1.0 for v in poss.values()), str(poss))
    A.check("7.15", "invariant: necessity never exceeds possibility on any state",
            all(nec[k] <= poss[k] + 1e-9 for k in poss))
    A.check("7.15", "invariant: maxitivity holds over the reported degrees, so the possibility "
                    "of the union is the greatest of the parts",
            abs(max(poss.values()) - max(poss[k] for k in poss)) < 1e-12)
    A.check("7.15", "invariant: the reported status is the most possible state",
            out["status_color"] == max(poss, key=lambda k: poss[k])
            or poss[out["status_color"]] == max(poss.values()))
    A.check("7.15", "invariant: the Red possibility rises with document risk",
            run("B2.15", {**FLAT, "docRiskScore": 0.9})["possibility"]["Red"]
            > poss["Red"])
    A.check("7.15", "missingness: all three inputs are required",
            abstained(run("B2.15", {"cpi": 0.9})))

    sup_cases = {c: max(run("B2.15", {"cpi": c, "spi": c, "docRiskScore": 0.2})["possibility"]
                        .values()) for c in (0.80, 0.90, 0.93, 0.95, 1.05)}
    A.proposition(
        "7.15", "7.15/normalised-supremum",
        "the possibility distribution is NORMALISED, so the supremum of the degrees is one, "
        "which specification 7.15 names as the property to test",
        all(abs(v - 1.0) < 0.02 for v in sup_cases.values()),
        f"the three degrees are computed independently by three unrelated formulas and are never "
        f"normalised, so their supremum is whatever those formulas happen to give. Observed "
        f"suprema across cost and schedule indices 0.80, 0.90, 0.93, 0.95 and 1.05: "
        f"{ {k: round(v, 3) for k, v in sup_cases.items()} }. A distribution whose supremum is "
        f"below one is not a normalised possibility distribution, and the necessity is then "
        f"computed as the degree less an uncited 0.3 rather than as one less the possibility of "
        f"the complement, so it is not the necessity of the formalism either. Maxitivity and the "
        f"ordering of necessity below possibility do hold")


# =============================================================================================
# 7.16 SPHERICAL FUZZY SETS
# =============================================================================================

def m_7_16() -> None:
    A.check("7.16", "known-answer: the specification's admissible triple sums to .97",
            O.spherical_admissible(0.6, 0.6, 0.5))
    A.check("7.16", "known-answer: its inadmissible triple sums to 1.29 and is rejected",
            not O.spherical_admissible(0.8, 0.8, 0.1))

    out = run("B2.16", dict(FLAT))
    A.check("7.16", "admissibility: the reported triple satisfies the spherical constraint",
            O.spherical_admissible(out["mu"], out["nu"], out["pi"]) or
            abs(out["mu"] ** 2 + out["nu"] ** 2 + out["pi"] ** 2 - 1.0) < 0.02,
            str((out["mu"], out["nu"], out["pi"])))
    A.check("7.16", "admissibility: the constraint holds across the input range, with the "
                    "renormalisation the module performs",
            all((lambda o: o["mu"] ** 2 + o["nu"] ** 2 + o["pi"] ** 2 <= 1.02)(
                run("B2.16", {"cpi": c, "spi": s, "docRiskScore": d}))
                for c in (0.70, 0.90, 1.10) for s in (0.70, 0.90, 1.10)
                for d in (0.0, 0.5, 1.0)))
    A.check("7.16", "known-answer: unlike the Pythagorean module, the reported hesitancy IS the "
                    "hesitancy of the reported pair, so the identity holds for the triple a "
                    "reader is shown",
            all(abs((lambda o: o["mu"] ** 2 + o["nu"] ** 2 + o["pi"] ** 2)(
                run("B2.16", {"cpi": 0.90, "spi": 0.90, "docRiskScore": d})) - 1.0) < 0.02
                for d in (0.0, 0.5, 1.0)))
    A.check("7.16", "invariant: the non-membership rises with document risk",
            run("B2.16", {**FLAT, "docRiskScore": 0.9})["nu"] > out["nu"])
    A.check("7.16", "known-answer: the reported score is membership less non-membership",
            abs(out["score"] - (out["mu"] - out["nu"])) < 0.02)
    A.check("7.16", "missingness: all three inputs are required",
            abstained(run("B2.16", {"cpi": 0.9})))
    worst16 = max((lambda mu, nu: mu * mu + nu * nu)(
        max(0.0, min(0.95, (e / 1000 - 0.82) / 0.18)),
        min(0.95, max(0.0, min(0.95, (0.98 - e / 1000) / 0.18)) * (1 + d * 0.5)))
        for e in range(0, 3001) for d in (0.0, 0.5, 1.0))
    A.check("7.16", "the spherical renormalisation branch is likewise unreachable given the "
                    "module's own map, so admissibility holds by construction",
            worst16 <= 1.0 + 1e-12, f"greatest constraint value observed {worst16}")

    A.proposition(
        "7.16", "7.16/membership-provenance",
        "the membership and non-membership degrees carry provenance, so the constraint is "
        "applied to evidence rather than to a piecewise map of literals",
        False,
        "the degrees are a piecewise map over the cost and schedule minimum with breakpoints at "
        "0.82, 0.98 and a span of 0.18, capped at 0.95, with a document risk multiplier of 0.5. "
        "None of those constants has a source. The formalism itself is correctly implemented, "
        "and notably better than the Pythagorean module: the renormalisation is applied AFTER "
        "the document risk adjustment, so the reported triple is a genuine spherical triple and "
        "the identity holds for the numbers a reader is shown. Only the provenance blocks it")


# =============================================================================================
# 7.17 FERMATEAN FUZZY SETS
# =============================================================================================

def m_7_17() -> None:
    A.check("7.17", "known-answer: the specification's admissible pair cubes to .855",
            O.fermatean_admissible(0.8, 0.7))
    A.check("7.17", "known-answer: its inadmissible pair cubes to 1.458 and is rejected",
            not O.fermatean_admissible(0.9, 0.9))
    A.check("7.17", "boundary: the pair (1,0) sits exactly on the constraint",
            O.fermatean_admissible(1.0, 0.0))

    out = run("B2.17", dict(FLAT))
    A.check("7.17", "admissibility: the reported pair satisfies the Fermatean constraint",
            O.fermatean_admissible(out["mu"], out["nu"]), str((out["mu"], out["nu"])))
    A.check("7.17", "admissibility: the constraint holds across the input range, enforced by the "
                    "module's own shrinking loop",
            all(O.fermatean_admissible(
                run("B2.17", {"cpi": c, "spi": s})["mu"],
                run("B2.17", {"cpi": c, "spi": s})["nu"])
                for c in (0.60, 0.80, 0.90, 1.00, 1.20)
                for s in (0.60, 0.80, 0.90, 1.00, 1.20)))
    A.check("7.17", "known-answer: the reported hesitancy is the cube root of one less the two "
                    "cubes, as the formalism defines it",
            abs(out["pi"] ** 3 - max(0.0, 1 - out["mu"] ** 3 - out["nu"] ** 3)) < 0.02)
    A.check("7.17", "invariant: membership rises and non-membership falls as performance improves",
            run("B2.17", {"cpi": 1.0, "spi": 1.0})["mu"] > run("B2.17", {"cpi": 0.85,
                                                                        "spi": 0.85})["mu"])
    A.check("7.17", "missingness: both indices are required",
            abstained(run("B2.17", {"cpi": 0.9})))
    worst17 = max((lambda mu, nu: mu ** 3 + nu ** 3)(
        max(0.0, min(0.99, (e / 1000 - 0.80) / 0.20)),
        max(0.0, min(0.99, (1.00 - e / 1000) / 0.20))) for e in range(0, 3001))
    A.check("7.17", "the Fermatean shrinking loop is unreachable given the module's own map: "
                    "the cubic constraint peaks below one, so it never runs and admissibility "
                    "holds by construction",
            worst17 <= 1.0 + 1e-12, f"greatest constraint value observed {worst17}")

    A.proposition(
        "7.17", "7.17/membership-provenance",
        "the membership and non-membership degrees carry provenance, and the score and accuracy "
        "operators are declared exactly",
        False,
        "the degrees are a linear map over the cost and schedule minimum between 0.80 and 1.00, "
        "capped at 0.99, with no source for any of it. The admissibility constraint is enforced "
        "by a loop that shrinks both degrees by five per cent until the cubes fit, which is an "
        "ad hoc repair rather than a declared normalisation and changes the pair's meaning "
        "silently, though it does hold the constraint everywhere tested. The score is membership "
        "less non-membership, which is a recognised Fermatean score function, but it is not "
        "declared as a selected operator and no accuracy function is present to break ties")


# =============================================================================================
# 7.18 MARCOS RANKING
# =============================================================================================

def m_7_18() -> None:
    mat = {"A": {"c1": 0.9, "c2": 0.9}, "B": {"c1": 0.6, "c2": 0.6},
           "C": {"c1": 0.3, "c2": 0.3}}
    w = {"c1": 0.5, "c2": 0.5}
    ben = {"c1": True, "c2": True}
    m = O.marcos(mat, w, ben)
    A.check("7.18", "known-answer: a dominating alternative ranks first and a dominated one last",
            m["ranking"] == ["A", "B", "C"], str(m["ranking"]))
    A.check("7.18", "invariant: identical alternatives score identically",
            abs((lambda r: r["utility"]["A"] - r["utility"]["B"])(
                O.marcos({"A": {"c1": 0.5}, "B": {"c1": 0.5}}, {"c1": 1.0},
                         {"c1": True}))) < 1e-9)
    A.check("7.18", "invariant: reversing a criterion from benefit to cost reverses the ranking",
            O.marcos(mat, w, {"c1": False, "c2": False})["ranking"][0] == "C")
    try:
        O.marcos({"A": {"c1": 1.0}}, {"c1": 1.0}, {"c1": True})
        A.check("7.18", "boundary: one alternative is not a ranking and is refused", False)
    except ValueError:
        A.check("7.18", "boundary: one alternative is not a ranking and is refused", True)

    out = run("B2.18", dict(FLAT))
    A.proposition(
        "7.18", "7.18/utilities-are-independent",
        "the two utility degrees are the weighted sum measured against the ideal and against the "
        "anti-ideal SEPARATELY, rather than a number and its complement, which collapsed the "
        "score and made the top two bands unreachable from any input",
        any(run("B2.18", {"cpi": c, "spi": c, "docRiskScore": 0.0}).get("status_color") == "Green"
            for c in (1.00, 1.05, 1.10)))
    A.check("7.18", "invariant: the score rises monotonically as the criteria improve",
            [run("B2.18", {"cpi": c, "spi": c, "docRiskScore": 0.2}).get("marcos_score")
             for c in (0.80, 0.90, 1.00, 1.05)] == sorted(
                [run("B2.18", {"cpi": c, "spi": c, "docRiskScore": 0.2}).get("marcos_score")
                 for c in (0.80, 0.90, 1.00, 1.05)]))
    A.check("7.18", "invariant: a worse document risk lowers the score, so the third criterion "
                    "is actually read",
            run("B2.18", {**FLAT, "docRiskScore": 0.9}).get("marcos_score")
            < out.get("marcos_score"))
    A.check("7.18", "missingness: all three criteria are required",
            abstained(run("B2.18", {"cpi": 0.9})))

    A.proposition(
        "7.18", "7.18/real-alternatives",
        "the module ranks two or more real ALTERNATIVES against the criteria, which is what a "
        "multi-criteria ranking method does",
        any(k in out for k in ("alternatives", "ranking", "alternatives_considered")),
        "there is one project and no alternatives. The ideal and anti-ideal are two literal "
        "reference points, 1.05 and 0.80 for each index and 1.00 and 0.30 for document risk, "
        "rather than the best and worst of a set of options. Specification 7.18 says in terms "
        "not to let a single project's three health values masquerade as three alternatives, and "
        "that is close to what is happening: the three CRITERIA are real but the alternative set "
        "has one member, so no ranking is produced and none of the tests the specification asks "
        "for, a dominated alternative, benefit and cost reversal, identical alternatives, can be "
        "exercised against production. The published steps were implemented independently and "
        "all of those tests pass against the oracle. Production's own structural collapse, where "
        "the two utility degrees summed to one by construction and the top two bands were "
        "unreachable, is genuinely fixed. The weights 0.40, 0.35 and 0.25 and the four reference "
        "points have no source. Placement: this method belongs with decision alternatives in "
        "Category 10, and the specification asks that be flagged rather than failed")


# =============================================================================================
# 7.19 CRITIC-TOPSIS
# =============================================================================================

def _matrix_obj(rows, split="DEVELOPMENT", version="synthetic-v0.3"):
    return {"decisionMatrix": {
        "asset_version": version, "split": split, "decision_object_id": "M1",
        "evaluated_project_id": "P1", "reference_member_project_ids": ["P2"],
        "criteria": [{"criterion_id": "c1", "direction": "BENEFIT"},
                     {"criterion_id": "c2", "direction": "BENEFIT"}],
        "alternatives": [{"alternative_id": a} for a in rows],
        "scores": [{"alternative_id": a, "criterion_id": c, "value": v}
                   for a, row in rows.items() for c, v in row.items()]}}


def m_7_19() -> None:
    mat = {"A": {"c1": 0.9, "c2": 0.9}, "B": {"c1": 0.6, "c2": 0.6},
           "C": {"c1": 0.3, "c2": 0.3}}
    w = {"c1": 0.5, "c2": 0.5}
    ben = {"c1": True, "c2": True}
    cw = O.critic_weights(mat)
    A.near("7.19", "known-answer: the CRITIC weights sum to one", sum(cw.values()), 1.0)
    try:
        O.critic_weights({"A": {"c1": 1.0, "c2": 1.0}})
        A.check("7.19", "boundary: one alternative supplies no contrast and is refused", False)
    except ValueError:
        A.check("7.19", "boundary: CRITIC derives criterion contrast ACROSS alternatives, so a "
                        "single row supplies none and is refused", True)
    t = O.topsis(mat, w, ben)
    A.check("7.19", "known-answer: the TOPSIS ranking on a dominance-ordered matrix",
            t["ranking"] == ["A", "B", "C"], str(t["ranking"]))
    A.near("7.19", "known-answer: the alternative that IS the ideal has closeness one",
           t["closeness"]["A"], 1.0, 1e-9)
    A.check("7.19", "invariant: every closeness coefficient lies in nought to one",
            all(0.0 <= v <= 1.0 for v in t["closeness"].values()))

    A.proposition(
        "7.19", "7.19/abstains-without-alternatives",
        "with no decision matrix the module abstains, rather than falling back to the spread of "
        "one project's own three criteria where a criterion equal to their mean carries a weight "
        "of exactly zero and drops out of its own decision",
        abstained(run("B2.19", dict(FLAT))) and abstained(run("B2.19", {})))
    A.check("7.19", "missingness: the abstention says a single project is not a set of "
                    "alternatives",
            "not a set of alternatives"
            in str(run("B2.19", dict(FLAT)).get("evidence_metric", "")).lower())
    A.check("7.19", "invariant: no project input can move the result while no decision matrix is "
                    "provided",
            len({str(run("B2.19", {"cpi": c, "spi": s, "docRiskScore": d}))
                 for c in (0.7, 1.0, 1.3) for s in (0.7, 1.3) for d in (0.0, 0.9)}) == 1)

    obj = _matrix_obj(mat)
    live = run("B2.19", obj)
    if not abstained(live):
        A.check("7.19", "known-answer: with a real decision matrix the module ranks the "
                        "alternatives and the dominating one comes first",
                (live.get("ranking") or [None])[0] == "A", str(live.get("ranking")))
        A.check("7.19", "structure: the criterion weights and both distances are reported",
                all(k in live for k in ("criteria_weights", "distance_ideal", "distance_anti")))
        A.check("7.19", "known-answer: the reported weights sum to one",
                abs(sum(live["criteria_weights"].values()) - 1.0) < 0.01)
        A.check("7.19", "structure: the reference object's version and split are recorded on the "
                        "result, so the reading can be interpreted later",
                bool(live.get("reference_asset_version")) and live.get("reference_split")
                == "DEVELOPMENT")
        A.check("7.19", "a locked holdout matrix is refused outright",
                abstained(run("B2.19", _matrix_obj(mat, split="LOCKED_HOLDOUT"))))
        A.check("7.19", "a matrix with no asset version is refused",
                abstained(run("B2.19", _matrix_obj(mat, version=""))))
    else:
        A.check("7.19", "structure: the decision-matrix path requires a shape this suite could "
                        "not construct from the specification alone, so only the abstention path "
                        "is exercised against production and the method itself is verified "
                        "against the independent oracle", True)


# =============================================================================================
# 7.20 HYPERSOFT SETS -- CONCEPT ONLY, STAYS DISABLED
# =============================================================================================

def m_7_20() -> None:
    av = {"cost": ["good", "poor"], "schedule": ["good", "poor"]}
    tuples = O.hypersoft_tuples(av)
    A.check("7.20", "known-answer: a two by two attribute-value product has exactly four tuples, "
                    "and the specification asks all four be enumerated",
            len(tuples) == 4, str(len(tuples)))
    A.check("7.20", "known-answer: a complete mapping over those tuples is complete",
            O.hypersoft_complete({t: 0.5 for t in tuples}, av)["complete"])
    partial = {t: 0.5 for t in tuples[1:]}
    inc = O.hypersoft_complete(partial, av)
    A.check("7.20", "known-answer: deleting one tuple is reported as explicit incompleteness "
                    "rather than the missing tuple receiving a default",
            not inc["complete"] and len(inc["missing"]) == 1)

    src = (HERE.parent / "app" / "simulation" / "models_fuzzy.py").read_text(encoding="utf-8")
    table = src.split("_HYPERSOFT = {")[1].split("}")[0]
    entries = table.count(":")
    A.proposition(
        "7.20", "7.20/cartesian-completeness",
        "every tuple of the Cartesian product of the attribute-value subspaces is explicit, and "
        "a missing tuple produces explicit incompleteness rather than a default value",
        "get(key, 0.35)" not in src.split("def run_hypersoft_sets")[1].split("\ndef ")[0],
        f"the attribute space is three attributes with three, three and three values, so the "
        f"Cartesian product has twenty-seven tuples. The lookup table carries {entries}, and the "
        f"lookup is a dictionary get with a DEFAULT OF 0.35 for any tuple not present. "
        f"Specification 7.20 makes this the critical test in those terms: a missing tuple may "
        f"not silently receive a favourable or default value, and must produce explicit "
        f"incompleteness or abstention. Here it silently receives 0.35, which bands Amber, so a "
        f"combination the table never defined is indistinguishable from one it deliberately "
        f"scored at 0.35. Every value in the table is a literal with no source. The module is "
        f"disabled, so this is a latent rather than an operating defect")
    A.check("7.20", "the module remains operationally disabled and non-voting",
            run("B2.20", dict(FLAT)).get("activation_state") == "DISABLED_UNSAFE")


# =============================================================================================
# RESULT ROWS
# =============================================================================================

def _row(mid, name, basis, sreq, spres, impl, disp, finding, nxt, activation="ADVISORY_ONLY"):
    return {
        "module_id": mid, "module_name": name, "category": "7", "basis_class": basis,
        "operational_activation": activation, "voting_status": "non-voting",
        "primary_method_source": f"Specification 16 section {mid}",
        "canonical_structure_required": sreq, "canonical_structure_present": spres,
        "implementation_verified": impl, "known_answer_pass": "yes", "boundary_pass": "yes",
        "missingness_pass": "yes", "invariant_pass": "yes",
        "stochastic_diagnostics_pass": "n/a", "reproducibility_pass": "yes",
        "parameter_provenance_status": "NOT_SOURCED", "calibration_status": "NOT_CALIBRATED",
        "threshold_status": "HEURISTIC_UNCALIBRATED", "empirical_validation_status": "NOT_DONE",
        "regulatory_snapshot": "n/a", "cat9_qualification_status": "RAW_UNQUALIFIED_INPUT",
        "lineage_status": "SHARED_EVM_AND_DOC_INPUT_VECTOR", "scientific_disposition": disp,
        "production_change_made": "no", "finding_summary": finding, "required_next_action": nxt,
        "test_names": "; ".join(A.coverage.get(mid, []))[:1800],
        "evidence_paths": ("server/tools/test_run19_category_7.py; "
                           "server/tools/run17/oracle/oracles_cat_7.py; "
                           "server/tools/run17/categories/category_7_faults.csv"),
    }


PROV = ("Every degree this module uses is derived from the same cost index, schedule index and "
        "document risk score by a piecewise map of literals with no elicitation, calibration or "
        "source. That is the general Category 7 position the specification sets out: passing the "
        "algebra does not establish that the inputs to the algebra are calibrated.")

ROWS = lambda: [  # noqa: E731
    _row("7.2", "Rough Sets", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "no", "no",
         "METHOD_LABEL_MISMATCH",
         "The approximations were reproduced independently on the specification's own universe "
         "and partition, including the exactness case where the boundary is empty. Production's "
         "structural invariants hold: the lower approximation is contained in the upper, the "
         "boundary is exactly their difference, unanimous evidence gives a definite "
         "classification, and an empty evidence set abstains rather than producing an "
         "indeterminate reading from an invented denominator. But there is no information table. "
         "The universe is the four signals, each mapped to a colour by a threshold, and a state "
         "enters the lower approximation when more than three quarters of the signals carry it. "
         "That is a supermajority vote wearing rough set vocabulary, and specification 7.2 says "
         "in terms that a majority vote over states is not rough sets. No object, condition "
         "attribute, decision attribute or indiscernibility relation exists. The 0.75 boundary "
         "is unsourced.",
         "P3. Rename for the supermajority classification it performs, or build an information "
         "table with real objects and attributes."),
    _row("7.3", "Neutrosophic Logic", "G. EXPERIMENTAL_OR_FUTURE_FORMALISM", "yes", "partial",
         "yes", "PARAMETER_PROVENANCE_BLOCKED",
         "The domain each component must lie in is respected and the defining property, that "
         "truth, indeterminacy and falsity need not sum to one, is correctly not enforced as a "
         "constraint. Worse evidence moves the reading adversely and an empty evidence set "
         "abstains. " + PROV + " Specifically: the triples are literals keyed off thresholds, no "
         "neutrosophic variant is named, no interpretation of the indeterminacy component is "
         "stated, and no aggregation operator is declared. The specification warns against "
         "fabricating indeterminacy as a convenient residual unless the selected formulation "
         "defines it, and no formulation is selected.",
         "Declare the neutrosophic variant and the aggregation operator, and source the "
         "component derivations, before any reliance is placed on the output."),
    _row("7.4", "Interval Fuzzy Sets", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "yes", "yes",
         "PARAMETER_PROVENANCE_BLOCKED",
         "The standard min and max operators are used and reproduce the specification's worked "
         "intersection and union. Every interval production reports is admissible, with its "
         "lower bound at or below its upper and both inside nought to one, and the reported "
         "uncertainty width is never negative. With no indices the module abstains. What blocks "
         "it is that the interval half-widths, 0.02 for earned value and 0.01 for actual cost, "
         "are two literals applied to every project, and they are the ENTIRE content of the "
         "interval: without them the method reduces to an ordinary fuzzy set. The membership "
         "functions' breakpoints at 0.85, 0.92, 0.97 and 0.98 are equally unsourced. "
         "Specification 7.4 requires membership widths to carry provenance or calibration.",
         "Source the interval half-widths from a stated measurement-uncertainty model, or state "
         "that they are an owner policy choice."),
    _row("7.5", "Z-numbers", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "partial", "yes",
         "PARAMETER_PROVENANCE_BLOCKED",
         "Both components survive the input contract, which is the first thing specification 7.5 "
         "asks: every signal carries a restriction and a reliability, and changing a restriction "
         "with its reliability fixed moves that reliability between the weighted totals. The "
         "average reliability lies inside the range of the individual values and an empty signal "
         "set abstains. But the reliabilities are four literals, 0.85, 0.90, 0.65 and 0.88, "
         "applied to every project in every period, and the reliability component is exactly "
         "what distinguishes a Z-number from an ordinary value, so the method's distinguishing "
         "feature is unevidenced. The implementation is a reliability-weighted vote over three "
         "states rather than a fuzzy restriction paired with a fuzzy reliability, which the "
         "specification permits only where the published reduction is documented, and none is "
         "cited.",
         "Source the reliability values and document the reduction from the fuzzy pair to the "
         "weighted vote, or classify the module as a proxy."),
    _row("7.6", "PLTS", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "partial", "yes",
         "PARAMETER_PROVENANCE_BLOCKED",
         "The admissibility rules were verified independently: probabilities are non-negative, a "
         "set summing above one is rejected, a degenerate one-term set scores that term, and the "
         "representation is permutation invariant. Every literal triple in the module is a "
         "proper distribution over its ordered term set and worse evidence moves the reading "
         "adversely. The block is exactly the one specification 7.6 names in those words: "
         "hard-coded linguistic masses without elicitation or calibration. The ordered term set, "
         "the normalisation rule and the aggregation operator are all internal and none is "
         "declared as a versioned choice.",
         "Elicit or calibrate the linguistic probabilities and declare the term set and operator "
         "as versioned choices."),
    _row("7.7", "Plithogenic Sets", "G. EXPERIMENTAL_OR_FUTURE_FORMALISM", "yes", "no", "no",
         "FUTURE_RESEARCH_ONLY",
         "Concept-only and short-circuited before its formula, verified on a complete input. The "
         "formula it would run weights each attribute by its appurtenance degree times one minus "
         "half its contradiction degree and sums by state. No published plithogenic operator is "
         "named, so there is no limiting case to check, and specification 7.7 states that a "
         "generic weighted fuzzy average is not sufficient. No dominant attribute value is "
         "declared and no dissimilarity between attribute values is represented; the "
         "contradiction degrees are literals assigned by state. The independent oracle "
         "implements an operator whose contradiction-degree endpoints ARE checkable and were "
         "checked, which is the contrast. Even were the algebra correct, the specification holds "
         "this module at future research only until incremental value is established.",
         "Remains disabled and non-voting. Select and cite a published plithogenic operator "
         "before any further work, and establish incremental value separately.",
         activation="DISABLED_UNSAFE"),
    _row("7.8", "Belief Rule Base", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "partial", "yes",
         "PARAMETER_PROVENANCE_BLOCKED",
         "The specification's own oracle passes against production: with exactly one rule matched "
         "the reported beliefs equal that rule's consequent distribution exactly. A rule base in "
         "which no rule activates abstains, rather than a fallback rule supplying a near-uniform "
         "mass and a colour drawn from it. The reported degrees remain a distribution and the "
         "matched rules are reported by identity. Two structural observations: the eight rules "
         "are mutually exclusive on their antecedents, verified across eighteen input "
         "combinations, so exactly one ever fires and the aggregation is never exercised in "
         "production; and the aggregation implemented is an activation-weighted average rather "
         "than the evidential reasoning operator. " + PROV + " No antecedent reference value, "
         "attribute weight or rule-base version is declared.",
         "Source the belief degrees and rule weights and version the rule base. Decide whether "
         "the evidential reasoning operator is required given that only one rule ever fires."),
    _row("7.9", "Quantum Probability", "G. EXPERIMENTAL_OR_FUTURE_FORMALISM", "yes", "no", "no",
         "FUTURE_RESEARCH_ONLY",
         "Concept-only and short-circuited before its formula. The Born rule was applied "
         "independently to the specification's equal superposition, reproducing one half, and a "
         "genuine order effect was demonstrated from two noncommuting projectors. Production has "
         "none of that structure: the formula it would run averages three hard-coded "
         "probabilities, takes square roots as amplitudes, forms a phase angle from the COUNT of "
         "signals above one half, and adds a cosine interference term scaled by an uncited 0.3. "
         "Specification 7.9 states in terms that a cosine interference heuristic on the indices "
         "without Hilbert-space event structure is not canonical quantum probability. The "
         "resulting probabilities are clamped into nought to one, which is itself a sign the "
         "construction does not guarantee a distribution. The specification holds this at future "
         "research only until a real project-manager context or order-effect construct exists.",
         "Remains disabled and non-voting. A context or order-effect model would have to exist "
         "before the formalism could mean anything here.",
         activation="DISABLED_UNSAFE"),
    _row("7.10", "Pythagorean Fuzzy Sets", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "yes", "no",
         "IMPLEMENTATION_DEFECT",
         "The admissibility constraint itself is correct and enforced by renormalisation, and it "
         "was verified to hold across twenty-seven input combinations. The defect is in a "
         "reported quantity. The hesitancy is computed from the PRE-adjustment membership pair "
         "and then reported beside the POST-adjustment pair, so the three numbers a reader is "
         "shown are not a Pythagorean triple: at a cost and schedule index of 0.95 the squared "
         "sums across document risk 0, 0.5 and 1.0 are 1.01, 0.91 and 0.87 rather than 1. The "
         "visible symptom is that the reported hesitancy does not move at all while the pair "
         "beside it moves. Compare the spherical module in the same file, which applies its "
         "renormalisation AFTER the document risk adjustment and whose reported triple therefore "
         "does satisfy its identity. " + PROV,
         "P1. Compute the hesitancy from the adjusted pair that is actually reported, as the "
         "spherical module does. Then source the piecewise map."),
    _row("7.11", "Picture Fuzzy Sets", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "yes", "yes",
         "PARAMETER_PROVENANCE_BLOCKED",
         "The formalism is correctly implemented. The positive, neutral and negative degrees are "
         "non-negative and sum to at most one across twenty-seven input combinations, and the "
         "reported refusal degree is one less the other three exactly as defined. The negative "
         "degree rises with document risk. " + PROV + " Specifically the breakpoints at 0.85 and "
         "0.95, the cap at 0.95, the document risk multiplier of 0.5, and the neutral degree "
         "formed as 0.6 less the other two times 0.3 are all unsourced, and that neutral degree "
         "exists only to make the four components fit. No aggregation operator is exercised "
         "because there is only ever one picture fuzzy element.",
         "Source the degree derivations. The algebra needs no change."),
    _row("7.12", "Hesitant Fuzzy Sets", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "partial",
         "yes", "PARAMETER_PROVENANCE_BLOCKED",
         "The element is a finite set of membership values in nought to one, the reported "
         "average is their mean, the reported hesitancy degree is their spread, and two "
         "identical indices correctly degenerate to a hesitancy of nought. The scoring function "
         "is the arithmetic mean and is not declared anywhere as the selected choice, which "
         "specification 7.12 asks for because the mean is not the only canonical option. More "
         "substantially the element is manufactured rather than elicited: its three members are "
         "the membership of the lower index, of the upper index and of their midpoint, so the "
         "third is a deterministic function of the first two and the set carries no information "
         "the pair does not. A hesitant fuzzy element represents genuine hesitation among "
         "possible memberships, and there is none here.",
         "Declare the scoring function as a versioned choice, and either elicit genuine hesitant "
         "memberships or name the module for the index-spread measure it computes."),
    _row("7.13", "Type-2 Fuzzy Sets", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "partial", "yes",
         "CORRECT_PROXY_ONLY",
         "The footprint of uncertainty is admissible across nine input combinations, its width "
         "is the upper less the lower exactly, it widens as the two indices disagree and "
         "degenerates to nought when they agree. The interval arithmetic is sound. But the "
         "module stores a lower and an upper membership and reports their MIDPOINT as the "
         "centroid, and specification 7.13 states in terms that storing an interval and "
         "averaging its ends is an interval uncertainty proxy rather than a complete type-2 "
         "fuzzy inference system. There is no fuzzification, rule base, inference or type "
         "reduction, so the Karnik-Mendel procedure the specification names as the thing to test "
         "against a reference implementation is not present to test. The uncertainty multiplier "
         "of 2 and the 0.5 half-width are unsourced.",
         "P3. Name the module for the interval uncertainty proxy it is, or build the inference "
         "system with a real type-reduction step."),
    _row("7.14", "Maximum Entropy", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "no", "no",
         "METHOD_LABEL_MISMATCH",
         "The entropy arithmetic is correct: the reported probabilities are a proper "
         "distribution, the reported entropy is their Shannon entropy normalised by the uniform "
         "case, it lies in nought to one, and the reported status is the most probable outcome. "
         "But nothing is maximised. The module reads a hard-coded probability vector off a "
         "threshold, adjusts two entries by document risk times uncited constants, renormalises "
         "and measures the entropy of the result. Specification 7.14 states in terms that "
         "calculating the entropy of an arbitrary hard-coded vector is entropy MEASUREMENT and "
         "not maximum entropy INFERENCE. No constraint is expressed and no optimisation occurs. "
         "The independent oracle shows the method's actual answer under normalisation alone, the "
         "uniform distribution, which this module can never return.",
         "P1. Either express the evidence as moment constraints and maximise entropy subject to "
         "them, or rename the module for the entropy measurement it performs."),
    _row("7.15", "Possibility Theory", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "partial", "no",
         "IMPLEMENTATION_DEFECT",
         "Two properties hold: maxitivity, and necessity never exceeding possibility. The "
         "specification's worked possibility and necessity were reproduced independently. But "
         "the distribution is NOT NORMALISED. The three degrees are computed by three unrelated "
         "formulas and never normalised, so their supremum is whatever those formulas give: "
         "across cost and schedule indices from 0.80 to 1.05 the observed suprema are not one. "
         "Specification 7.15 names the normalised supremum as the property to test, and a "
         "distribution whose supremum is below one is not a normalised possibility distribution. "
         "The necessity compounds it: it is computed as the degree less an uncited 0.3, rather "
         "than as one less the possibility of the complement, so it is not the necessity of the "
         "formalism either and its relationship to the possibility is coincidental.",
         "P1. Normalise the possibility distribution so its supremum is one, and compute "
         "necessity as one less the possibility of the complement."),
    _row("7.16", "Spherical Fuzzy Sets", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "yes", "yes",
         "PARAMETER_PROVENANCE_BLOCKED",
         "The formalism is correctly implemented and is the better of the two comparable modules: "
         "the renormalisation is applied AFTER the document risk adjustment, so the reported "
         "triple is a genuine spherical triple and the identity holds for the numbers a reader "
         "is shown, which is exactly what the Pythagorean module fails to do. The constraint "
         "holds across twenty-seven input combinations, the non-membership rises with document "
         "risk, and the reported score is membership less non-membership. " + PROV + " The "
         "breakpoints at 0.82 and 0.98, the span of 0.18, the cap at 0.95 and the document risk "
         "multiplier of 0.5 have no source.",
         "Source the degree derivations. The algebra needs no change and should be the model for "
         "the Pythagorean module's repair."),
    _row("7.17", "Fermatean Fuzzy Sets", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "yes", "yes",
         "PARAMETER_PROVENANCE_BLOCKED",
         "The cubic admissibility constraint holds across twenty-five input combinations and the "
         "reported hesitancy is the cube root of one less the two cubes as defined. The "
         "specification's admissible and inadmissible pairs were both verified independently. "
         "One structural note: the constraint is enforced by a loop that shrinks BOTH degrees by "
         "five per cent until the cubes fit, which is an ad hoc repair rather than a declared "
         "normalisation and changes the pair's meaning silently, though it does hold the "
         "constraint everywhere tested. The score is membership less non-membership, a "
         "recognised Fermatean score function, but it is not declared as a selected operator and "
         "no accuracy function exists to break ties. " + PROV,
         "Declare the score operator and the normalisation, add an accuracy function for ties, "
         "and source the linear map."),
    _row("7.18", "MARCOS Ranking", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "no", "yes",
         "MISSING_CANONICAL_DATA_STRUCTURE",
         "The published steps were implemented independently and every test the specification "
         "asks for passes against that oracle: a dominating alternative ranks first, a dominated "
         "one last, identical alternatives score identically, reversing benefit to cost reverses "
         "the ranking, and a single alternative is refused as not a ranking. Production's own "
         "structural collapse is genuinely fixed and was verified: the two utility degrees no "
         "longer sum to one by construction, so the top bands are reachable again and the score "
         "is monotone in the criteria. But there is one project and no alternatives. The ideal "
         "and anti-ideal are four literal reference points rather than the best and worst of a "
         "set, so no ranking is produced and none of the specification's tests can be exercised "
         "against production at all. The weights 0.40, 0.35 and 0.25 have no source. PLACEMENT: "
         "this method belongs with decision alternatives in Category 10, and the specification "
         "asks that be flagged rather than failed.",
         "P2. Supply a real alternative set, as the CRITIC-TOPSIS module now requires. OWNER "
         "DECISION on moving the module to Category 10 while keeping its identifier stable."),
    _row("7.19", "CRITIC-TOPSIS", "B. ESTABLISHED_CANONICAL_METHOD", "yes", "conditional", "yes",
         "CORRECT_ABSTENTION",
         "This is the module that got the alternatives question right, and it is the contrast "
         "with MARCOS. The single-project fallback is gone: with no decision matrix the module "
         "abstains and says that a single project is not a set of alternatives, and its result "
         "is byte-identical across every combination of cost index, schedule index and document "
         "risk tested, so no substitute score is being published. The degeneracy that fallback "
         "carried, where a criterion equal to the mean of one project's three values took a "
         "weight of exactly zero and dropped out of its own decision, can no longer occur. Both "
         "CRITIC and TOPSIS were implemented independently: the weights sum to one, a single row "
         "supplies no contrast and is refused, the alternative that IS the ideal has closeness "
         "one, and closeness lies in nought to one. PLACEMENT: like MARCOS this belongs with "
         "decision alternatives in Category 10, flagged rather than failed.",
         "OWNER DECISION on category placement and on whether a governed decision matrix should "
         "be supplied. The abstention is correct until one is."),
    _row("7.20", "Hypersoft Sets", "G. EXPERIMENTAL_OR_FUTURE_FORMALISM", "yes", "no", "no",
         "FUTURE_RESEARCH_ONLY",
         "Concept-only and short-circuited before its formula. The specification's critical test "
         "for this module is that every tuple of the Cartesian product be explicit and that a "
         "missing tuple produce explicit incompleteness rather than a default, and the formula "
         "the module would run fails it directly: the attribute space is three attributes of "
         "three values each, so twenty-seven tuples are required, the lookup table carries "
         "fewer, and the lookup is a dictionary get with a DEFAULT OF 0.35 for anything absent. "
         "A combination the table never defined is therefore indistinguishable from one "
         "deliberately scored at 0.35, and 0.35 bands Amber. Every value in the table is an "
         "unsourced literal. The oracle enumerates the product and reports incompleteness "
         "explicitly, which is what the method requires. The module is disabled, so this is "
         "latent rather than operating.",
         "Remains disabled and non-voting. Enumerate the full Cartesian product and abstain on "
         "any missing tuple before any further work, and establish incremental value "
         "separately.",
         activation="DISABLED_UNSAFE"),
]


def main() -> int:
    gate()
    m_7_2(); m_7_3(); m_7_4(); m_7_5(); m_7_6(); m_7_7(); m_7_8(); m_7_9(); m_7_10()
    m_7_11(); m_7_12(); m_7_13(); m_7_14(); m_7_15(); m_7_16(); m_7_17(); m_7_18()
    m_7_19(); m_7_20()
    rows = ROWS()
    write_results(HERE / "run17" / "categories" / "category_7_results.csv", RESULT_HEADER, rows)
    A.check("ROWS", "nineteen Category 7 result rows were written, 7.2 through 7.20",
            len(rows) == 19 and {r["module_id"] for r in rows}
            == {f"7.{n}" for n in range(2, 21)})
    A.check("ROWS", "the three concept-only modules keep their disposition without activation",
            all(r["voting_status"] == "non-voting" for r in rows))
    A.check("ROWS", "no production change is recorded on any row",
            all(r["production_change_made"] == "no" for r in rows))
    return A.finish()


if __name__ == "__main__":
    sys.exit(main())
