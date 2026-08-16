"""
THE v5 CANONICAL METHOD LAYER FOR CATEGORIES 6 AND 7.

WHY THIS FILE EXISTS. Run 27 established that most of the twenty Category-7 modules were not
carrying out the method they are named for. They read the cost and schedule performance indices
and the document risk score -- three crisp numbers -- and manufactured from them a membership, a
mass, a linguistic probability or a possibility degree, none of which the project had ever
supplied. Two of them (Maximum Entropy and Fermatean Fuzzy Sets) were proved informationally to
be functions of `min(cpi, spi)` alone. A crisp index is not a mass function. It is not a
membership pair. It is not a probability distribution over designed states, and an entropy
calculated over a lookup table indexed by an index measures the lookup table.

The supervisory contract supplied for Run 30 states, for each of the four Category-6 targets and
the twenty Category-7 targets, the canonical mathematics, the defining structure that mathematics
is defined on, and hand-checkable known answers. This file supplies the structures and the
canonical arithmetic. It follows the v3/v4 pattern exactly, because the failure it prevents is
the same one.

THE RULES THIS FILE ENFORCES.

1. A canonical method computes ONLY from its defining structure. When the structure is absent the
   caller ABSTAINS -- Not Estimable -- and reports no substitute figure. THERE IS NO PROXY
   FALLBACK ANYWHERE BELOW. In particular nothing in this file reads `cpi`, `spi` or
   `docRiskScore`; no function here can be reached from a crisp key-performance index.
2. NO MEMBERSHIP, MASS, LINGUISTIC PROBABILITY, RULE WEIGHT, POSSIBILITY DEGREE, DISTRIBUTION OR
   BAND BOUNDARY IS INVENTED. Every such quantity arrives on a governed structure carrying its
   own provenance, or the method abstains. Functions here return numbers and structural facts;
   they do not assert traffic-light colours over quantities whose calibration Run 33 owns.
3. NOTHING HERE READS A FILE, A CLOCK OR A DATABASE. Every structure arrives on the caller's
   signal inputs, exactly as every scalar does.
4. NOTHING HERE IS DERIVED FROM THE v2/v14 IMPLEMENTATION. Each function was written from the
   supplied contract; the oracles in `server/tools/test_run30_canonical_oracles.py` carry the
   contract's own numbers, never numbers read back out of this file.
5. PROVENANCE TRAVELS. Run 31 owns the Category-9 qualification gate over these same rows and
   cannot qualify what has no lineage. Run 30 closes no LINEAGE finding.

WHAT IS DELIBERATELY LEFT BLOCKED, and why. Four contracts require an operator that the
supervisory artifacts do not freeze. `research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_
SPECIFICATION_v1.md` cites Karnik-Mendel type reduction by DOI (line 341) and asks only that a
centroid type reduction "if" used be tested against a reference (line 2152); it cites RIMER by
DOI (line 338) and asks for aggregation testing "for the selected ER formulation" (7.8) without
selecting one. A citation is not a formulation. So:

  * B2.13 Type-2 -- the interval type-2 membership and footprint of uncertainty are implemented
    and verified; TYPE REDUCTION AND INFERENCE ARE BLOCKED. Nothing here averages the lower and
    upper membership, because midpoint averaging is precisely the thing the contract forbids
    calling a type-2 inference system.
  * B2.8 Belief Rule Base -- the rule structure, admissibility and the single fully activated
    rule are implemented; MULTI-RULE EVIDENTIAL-REASONING AGGREGATION IS BLOCKED.
  * B2.5 Z-numbers -- representation and provenance are implemented; THE REDUCTION OPERATOR IS
    BLOCKED.
  * B2.7 Plithogenic -- the laboratory structure is implemented; THE OPERATOR IS BLOCKED and the
    method stays disabled/future research.

Blocked means a named refusal, not a default and not a substitute.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

from .canonical import StructureAbsent
from .canonical_v3 import _f, _provenance, _rows

# =================================================================================================
# THE GOVERNED v5 STRUCTURES.
#
# One structure per defining need. `decisionAlternatives` serves BOTH B2.18 and B2.19, which is
# section 10 of the contract: MARCOS and CRITIC-TOPSIS share ONE governed alternatives/criteria
# object and Run 32's Category-10 methods reuse the same one.
# =================================================================================================

#: Module id -> the signal-inputs key carrying its defining v5 structure.
V5_STRUCTURE_KEYS: dict[str, str] = {
    "B1.2": "signalWeightPolicy",
    "B2.1": "evidenceMassFunctions",
    "B2.2": "roughDecisionTable",
    "B2.3": "neutrosophicAssessment",
    "B2.4": "intervalFuzzyAssessment",
    "B2.5": "zNumberAssessment",
    "B2.6": "probabilisticLinguisticAssessment",
    "B2.7": "plithogenicLabStructure",
    "B2.8": "beliefRuleBase",
    "B2.10": "pythagoreanFuzzyAssessment",
    "B2.11": "pictureFuzzyAssessment",
    "B2.12": "hesitantFuzzyAssessment",
    "B2.13": "type2FuzzyAssessment",
    "B2.14": "maximumEntropyProblem",
    "B2.15": "possibilityAssessment",
    "B2.16": "sphericalFuzzyAssessment",
    "B2.17": "fermateanFuzzyAssessment",
    "B2.18": "decisionAlternatives",
    "B2.19": "decisionAlternatives",
    "B2.20": "hypersoftLabStructure",
}

#: The plain words for what each structure IS. These reach a reader in the abstention sentence,
#: so they carry no module id, no key name and no reason code, per the naming rules.
V5_STRUCTURE_WORDS: dict[str, str] = {
    "B1.2": "a weighting policy for the project's governed signals: a weight for each signal, "
            "and the authority that set it",
    "B2.1": "bodies of evidence expressed as mass over the states being distinguished, each "
            "body naming the evidence it was read from",
    "B2.2": "a decision table: the cases observed, the attributes recorded for each, and the "
            "decision recorded against them",
    "B2.3": "an assessment stated as three independent degrees -- how far the statement is "
            "supported, how far it is undetermined, and how far it is contradicted",
    "B2.4": "an assessment stated as a range of membership rather than a single degree",
    "B2.5": "an assessment stated as a restriction together with an explicit statement of how "
            "reliable that restriction is",
    "B2.6": "an assessment stated as named terms with a probability against each",
    "B2.7": "a laboratory structure of attributes, their values, appurtenance and contradiction "
            "degrees",
    "B2.8": "a belief rule base: the antecedent reference states, the rule and attribute "
            "weights, and the belief distribution each rule concludes",
    "B2.10": "an assessment stated as a membership and a non-membership degree whose squares "
             "together do not exceed one",
    "B2.11": "an assessment stated as positive, neutral and negative degrees that together do "
             "not exceed one",
    "B2.12": "an assessment stated as the set of degrees the assessors actually gave",
    "B2.13": "a membership with an explicit lower and upper bound at each point considered",
    "B2.14": "a set of states the project may be in, and the constraints the evidence places on "
             "them",
    "B2.15": "a possibility distribution over the states the project may be in",
    "B2.16": "an assessment stated as membership, non-membership and hesitancy degrees whose "
             "squares together do not exceed one",
    "B2.17": "an assessment stated as a membership and a non-membership degree whose cubes "
             "together do not exceed one",
    "B2.18": "an explicit decision problem: the alternatives being compared, the criteria they "
             "are compared on, and which way each criterion is better",
    "B2.19": "an explicit decision problem: the alternatives being compared, the criteria they "
             "are compared on, and which way each criterion is better",
    "B2.20": "a laboratory structure of attributes, the disjoint value sets of each, and a "
             "mapping for every combination of those values",
}


def v5_structure(si: dict, module_id: str) -> dict:
    """The module's defining structure off the signal inputs, or StructureAbsent."""
    key = V5_STRUCTURE_KEYS[module_id]
    words = V5_STRUCTURE_WORDS[module_id]
    structure = si.get(key)
    if structure is None:
        raise StructureAbsent(
            f"Awaiting {words}. This measure is named for a method that cannot be carried out "
            f"without it, so no reading is reported and no other figure is used in its place.")
    if not isinstance(structure, dict):
        raise StructureAbsent(
            f"The information provided for this project in place of {words} is not in a form "
            f"this measure can read, so no reading is taken from it.")
    return structure


def _unit(container: Any, field: str, words: str) -> float:
    """A number in [0, 1], refused rather than clamped when it is outside.

    NO SILENT CLAMPING AND NO SILENT PROJECTION. Section 20 of the contract makes this the
    defining behaviour of the fuzzy family: a degree outside the unit interval is a defect in the
    evidence, and squeezing it into range hides the defect and reports a number nobody supplied.
    """
    v = _f(container, field, words)
    if not (0.0 <= v <= 1.0):
        raise StructureAbsent(
            f"The {words} provided for this project carries a degree outside the range this "
            f"measure is defined on, so no reading is taken from it and nothing is adjusted to "
            f"bring it into range.")
    return v


# =================================================================================================
# CATEGORY 6 -- SYNTHESIS OVER GOVERNED SIGNALS
#
# Category 6 SYNTHESISES qualified signals. It creates no new project evidence. Every function
# below consumes the same governed-signal list and none of them reads a project metric.
# =================================================================================================

#: Severity order for synthesis, supplied by the contract's section 4. Abstain / Unknown /
#: Insufficient are NOT severity zero and are not in this map at all -- there is no entry to
#: accidentally read them through.
SEVERITY: dict[str, int] = {"Green": 0, "Yellow": 1, "Amber": 2, "Red": 3}

#: The inverse, used only to name a severity a caller has already computed.
SEVERITY_BAND: dict[int, str] = {v: k for k, v in SEVERITY.items()}

#: The states that mean "this signal did not speak", listed so they are recognised and EXCLUDED
#: rather than banded. A signal in one of these states is visible in the result and votes nowhere.
ABSTAINING_STATES = ("Abstain", "Unknown", "Insufficient", "NotEstimable", "Not Estimable")

_ABSTAINING_LOWER = {s.replace(" ", "").lower() for s in ABSTAINING_STATES}


class SignalNotEligible(Exception):
    """A governed signal this layer refuses to synthesise over, carrying the reason."""


def eligible_signals(signals: Any) -> tuple[list[dict], list[dict]]:
    """
    Split a governed signal list into the eligible non-abstaining ones and the abstaining ones.

    THE UNKNOWN LABEL IS REJECTED, NOT BUCKETED. Section 4 of the contract: "Do not silently
    coerce arbitrary strings into valid statuses." A status this layer does not recognise raises
    rather than becoming Green, Amber or an abstention, because an unrecognised string is a
    defect in the supply path and the supply path is what Run 31 has to qualify.

    A signal must carry: an identity, a status, a period and a lineage body. Those are the
    section-4 fields. Reliability and method/version are carried through when present and never
    invented when absent.
    """
    if not isinstance(signals, list) or not signals:
        raise SignalNotEligible(
            "No governed signals were supplied for this project, so there is nothing to "
            "synthesise and no reading is reported.")
    eligible: list[dict] = []
    abstaining: list[dict] = []
    for raw in signals:
        if not isinstance(raw, dict):
            raise SignalNotEligible(
                "One of the governed signals supplied for this project is not in a form this "
                "measure can read, so no synthesis is carried out.")
        identity = str(raw.get("signal_id") or "").strip()
        period = raw.get("period")
        lineage = raw.get("lineage_body")
        if not identity:
            raise SignalNotEligible(
                "A governed signal was supplied without an identity, so it cannot be told apart "
                "from another and no synthesis is carried out.")
        if not str(lineage or "").strip():
            raise SignalNotEligible(
                "A governed signal was supplied without saying what evidence it rests on, so "
                "duplicate evidence could not be told from independent evidence and no "
                "synthesis is carried out.")
        if period is None:
            raise SignalNotEligible(
                "A governed signal was supplied without the reporting period it belongs to, so "
                "no synthesis is carried out.")
        status = str(raw.get("status") or "").strip()
        record = {
            "signal_id": identity,
            "status": status,
            "period": period,
            "lineage_body": str(lineage).strip(),
            "source": raw.get("source"),
            "qualification": raw.get("qualification"),
            "reliability": raw.get("reliability"),
            "method_version": raw.get("method_version"),
            "abstention_reason": raw.get("abstention_reason"),
        }
        if status.replace(" ", "").lower() in _ABSTAINING_LOWER:
            abstaining.append(record)
            continue
        if status not in SEVERITY:
            raise SignalNotEligible(
                f"A governed signal was supplied carrying a state this platform does not "
                f"recognise, so it is refused rather than read as any of the states it is not. "
                f"No synthesis is carried out.")
        record["severity"] = SEVERITY[status]
        eligible.append(record)
    return eligible, abstaining


def independent_signals(eligible: Sequence[dict]) -> tuple[list[dict], list[dict]]:
    """
    Collapse signals resting on the SAME evidence body to one representative each.

    DUPLICATE-LINEAGE NEUTRALITY, which is section 17's whole subject. Two readings of one body
    of evidence are one body of evidence read twice; letting the second one vote, carry weight,
    or occupy a second worst position manufactures corroboration nobody supplied. The
    representative kept is the MOST SEVERE reading of the body -- the conservative direction and
    an idempotent operator, so a third and a fourth reading of the same body change nothing.
    Ties keep the earliest in the caller's own supplied order, which is declared and
    deterministic and is never a choice made by which representative gives the calmer answer.

    THIS IS PAIRWISE OVER A DECLARED BODY, NOT A TRANSITIVE CLOSURE. Dependence is not transitive
    and this programme does not partition by connected component; two signals are the same
    evidence exactly when they name the same body, and nothing here joins two bodies because a
    third overlaps both.
    """
    by_body: dict[str, dict] = {}
    suppressed: list[dict] = []
    for sig in eligible:
        body = sig["lineage_body"]
        held = by_body.get(body)
        if held is None:
            by_body[body] = sig
        elif sig["severity"] > held["severity"]:
            suppressed.append(held)
            by_body[body] = sig
        else:
            suppressed.append(sig)
    return list(by_body.values()), suppressed


def governed_signals_from_project(si: dict, period: Any) -> list[dict]:
    """
    THE PRODUCTION SUPPLY PATH FOR CATEGORY-6 SYNTHESIS, built from evidence the platform
    already holds and manufacturing none.

    The eligible inputs are the FOUR ASSEMBLED ARMS the signal package already carries, each
    given the lineage body `arm_lineage` already declares for it, resolved against this
    project's own evidence. Section 4's fields travel with each: identity, state, period,
    source provenance, evidence-lineage body, qualification state, abstention reason.

    WHAT IS DELIBERATELY EXCLUDED, and this is the substantive v15 change. The v14 ensembles
    ALSO voted every entry of `simulationSignals.signal_array` -- every other module this run
    computed. Those are not further evidence. They are further TRANSFORMATIONS of these same
    four arms, and section 3 of the contract is explicit that a transformation retains the
    lineage of what produced it rather than becoming an independent project fact. Admitting
    them let the count of REGISTERED MODULES decide the answer: Run 27 proved identical adverse
    evidence read Red beside a three-module array and Yellow beside a sixty-three-module array,
    because the adverse fraction was diluted by modules that had learned nothing new. Nothing
    is weighted or discounted to fix that; the arms that are actually distinct bodies are what
    is synthesised.

    QUALIFICATION IS CARRIED, NOT DECIDED. Every signal leaves here marked with the platform's
    own disclosed qualification state. Run 31 owns the gate; this function must not and does not
    become a competing one.
    """
    from .arm_lineage import ARM_LINEAGE_BY_KEY, separate_arms
    from .signal_package import SIGNAL_KEYS, SIGNAL_NAMES, SIGNAL_QUALIFICATION

    assembled = (si or {}).get("signals") or {}
    keys = [k for k in SIGNAL_KEYS if assembled.get(k) is not None]
    if not keys:
        return []
    records = [ARM_LINEAGE_BY_KEY[k] for k in keys]
    bodies = separate_arms(records, si)
    body_of: dict[int, str] = {}
    for group in bodies:
        # The body's name is its members' declared arm ids, joined in the module's own order, so
        # two arms in one body carry ONE body name and cannot be told apart by a later consumer.
        name = "+".join(records[i]["module_id"] for i in sorted(group))
        for i in group:
            body_of[i] = name
    out: list[dict] = []
    for idx, key in enumerate(keys):
        raw = assembled[key]
        status = raw.get("status") if key != "decision" else raw.get("state")
        band = None
        if status is not None:
            from .fusion import normalise_status
            band = normalise_status(status)
        out.append({
            "signal_id": key,
            "status": band if band is not None else "Abstain",
            "period": period,
            "lineage_body": body_of.get(idx, records[idx]["module_id"]),
            "source": SIGNAL_NAMES.get(key, key),
            "qualification": SIGNAL_QUALIFICATION,
            "method_version": raw.get("method_version"),
            "abstention_reason": (
                None if band is not None else
                "this signal did not report a state this platform recognises, so it takes no "
                "part in the synthesis"),
        })
    return out


def conservative_dominance(signals: Any) -> dict[str, Any]:
    """
    6.1 -- the most severe credible eligible non-abstaining signal. S_CD = max severity.

    No parameter, no threshold and no count: a maximum over the bands the signals themselves
    carry. Permutation invariant and idempotent by construction.
    """
    eligible, abstaining = eligible_signals(signals)
    independent, suppressed = independent_signals(eligible)
    if not independent:
        return {
            "estimable": False,
            "reason": "every governed signal for this project abstained, so there is no state "
                      "to take the most severe of and none is reported",
            "abstaining": abstaining,
        }
    worst = max(independent, key=lambda s: s["severity"])
    return {
        "estimable": True,
        "severity": worst["severity"],
        "state": SEVERITY_BAND[worst["severity"]],
        "dominant_signal_id": worst["signal_id"],
        "considered": [s["signal_id"] for s in independent],
        "duplicate_lineage_suppressed": [s["signal_id"] for s in suppressed],
        "abstaining": abstaining,
    }


def weighted_voting(signals: Any, policy: Any) -> dict[str, Any]:
    """
    6.2 -- class-weighted voting. Vote(c) = sum_i w_i * I(s_i = c); winner = argmax_c Vote(c).

    THE WEIGHTS ARE NOT INVENTED HERE AND CANNOT BE. They arrive on a governed weighting policy
    carrying its own authority; there is no default weight anywhere in this function, so a
    project with no policy cannot be given one implicitly. Weights are non-negative and are
    normalised to sum to one over the eligible independent signals actually voting, which is what
    makes the class votes comparable between projects with different signal counts.

    THE TIE POLICY IS DECLARED, NOT RESOLVED. A tie between classes returns no winner and says
    so. Choosing a winner from a tie is a governance decision with a direction (the calmer class
    or the more severe one) and it is not this function's to make.
    """
    eligible, abstaining = eligible_signals(signals)
    independent, suppressed = independent_signals(eligible)
    if not independent:
        return {"estimable": False,
                "reason": "every governed signal for this project abstained, so there is nothing "
                          "to weigh and no vote is reported",
                "abstaining": abstaining}
    if not isinstance(policy, dict):
        raise StructureAbsent(
            "Awaiting a weighting policy for this project's governed signals. A weighted vote "
            "cannot be taken without stated weights, and none is assumed.")
    words = V5_STRUCTURE_WORDS["B1.2"]
    provenance = _provenance(policy, words, "set_by", "authority")
    table = policy.get("weights")
    if not isinstance(table, dict) or not table:
        raise StructureAbsent(
            f"The {words} provided for this project states no weights, so no weighted vote is "
            f"taken and no weight is assumed for any signal.")
    raw: dict[str, float] = {}
    for sig in independent:
        if sig["signal_id"] not in table:
            raise StructureAbsent(
                f"The {words} provided for this project does not state a weight for every "
                f"signal being voted on, so no weighted vote is taken and no weight is assumed "
                f"for the signals it omits.")
        w = _f(table, sig["signal_id"], words)
        if w < 0:
            raise StructureAbsent(
                f"The {words} provided for this project states a negative weight, which a vote "
                f"is not defined on, so no weighted vote is taken.")
        raw[sig["signal_id"]] = w
    total = sum(raw.values())
    if total <= 0:
        return {"estimable": False,
                "reason": "the weighting policy for this project gives every voting signal no "
                          "weight at all, so no winner is reported",
                "abstaining": abstaining}
    weights = {k: v / total for k, v in raw.items()}
    votes = {c: 0.0 for c in SEVERITY}
    for sig in independent:
        votes[sig["status"]] += weights[sig["signal_id"]]
    best = max(votes.values())
    winners = [c for c in SEVERITY if votes[c] == best]
    return {
        "estimable": True,
        "votes": votes,
        "normalised_weights": weights,
        "unique_winner": len(winners) == 1,
        "winner": winners[0] if len(winners) == 1 else None,
        "tied_classes": winners if len(winners) > 1 else [],
        "tie_policy": "a tie between classes returns no winner; the choice between tied classes "
                      "is a governance decision and is not made here",
        "weight_provenance": provenance,
        "duplicate_lineage_suppressed": [s["signal_id"] for s in suppressed],
        "abstaining": abstaining,
    }


def majority_rules(signals: Any, *, quorum: int = 2) -> dict[str, Any]:
    """
    6.3 -- one vote per eligible independent qualified signal, plurality winner.

    Missing evidence never defaults Green: an abstaining signal casts no vote and an unrecognised
    label is refused upstream in `eligible_signals`. A tie is a conflict and is reported as one.

    THE QUORUM IS THE ONE STRUCTURAL MINIMUM, NOT A TUNED PARAMETER: a majority over a single
    voter is that voter, which is not a majority rule and is not reported as one.
    """
    eligible, abstaining = eligible_signals(signals)
    independent, suppressed = independent_signals(eligible)
    counts = {c: 0 for c in SEVERITY}
    for sig in independent:
        counts[sig["status"]] += 1
    if not independent:
        return {"estimable": False, "counts": counts,
                "reason": "every governed signal for this project abstained, so no majority is "
                          "reported and no state is assumed in place of one",
                "abstaining": abstaining}
    if len(independent) < quorum:
        return {"estimable": False, "counts": counts, "quorum": quorum,
                "voters": len(independent),
                "reason": "fewer independent signals spoke than a majority rule needs, so no "
                          "majority is reported",
                "abstaining": abstaining}
    best = max(counts.values())
    winners = [c for c in SEVERITY if counts[c] == best]
    return {
        "estimable": True,
        "counts": counts,
        "voters": len(independent),
        "quorum": quorum,
        "unique_winner": len(winners) == 1,
        "winner": winners[0] if len(winners) == 1 else None,
        "tied_classes": winners if len(winners) > 1 else [],
        "conflict": len(winners) > 1,
        "duplicate_lineage_suppressed": [s["signal_id"] for s in suppressed],
        "abstaining": abstaining,
    }


def worst_two_of_m(signals: Any) -> dict[str, Any]:
    """
    6.4 -- the frozen Worst-2 mean statistic. MeanWorst2 = (s1 + s2) / 2 over the two most
    severe eligible independent non-abstaining signals.

    WHY NOT max(worst two): it collapses to Conservative Dominance and the module stops being a
    second regime at all. WHY NOT the v14 rule: it compared a red COUNT against a FRACTION of the
    registered signal array, so registering more modules diluted the adverse fraction and
    identical adverse evidence read Red beside three signals and Yellow beside sixty-three. The
    statistic below has no denominator that grows with the array.

    NO TRAFFIC-LIGHT BOUNDARY IS DRAWN OVER MeanWorst2 HERE. The contract forbids inventing one
    and Run 33 owns the mapping; the number and the two signals it came from are exposed instead.
    A duplicate-lineage reading cannot occupy the second position because the duplicates are
    collapsed before the two are selected.
    """
    eligible, abstaining = eligible_signals(signals)
    independent, suppressed = independent_signals(eligible)
    if len(independent) < 2:
        return {"estimable": False, "m": len(independent),
                "reason": "fewer than two independent signals spoke for this project, so the "
                          "worst two cannot be taken and no reading is reported",
                "abstaining": abstaining,
                "duplicate_lineage_suppressed": [s["signal_id"] for s in suppressed]}
    ordered = sorted(independent, key=lambda s: (-s["severity"], s["signal_id"]))
    s1, s2 = ordered[0], ordered[1]
    return {
        "estimable": True,
        "m": len(independent),
        "mean_worst_2": (s1["severity"] + s2["severity"]) / 2.0,
        "selected": [
            {"signal_id": s1["signal_id"], "status": s1["status"],
             "severity": s1["severity"], "lineage_body": s1["lineage_body"]},
            {"signal_id": s2["signal_id"], "status": s2["status"],
             "severity": s2["severity"], "lineage_body": s2["lineage_body"]},
        ],
        "classification": None,
        "classification_blocked": "the boundaries that would turn this statistic into a state "
                                  "have not been set for this platform, so none is asserted",
        "duplicate_lineage_suppressed": [s["signal_id"] for s in suppressed],
        "abstaining": abstaining,
    }


# =================================================================================================
# 7.1 DEMPSTER-SHAFER
# =================================================================================================

def _frozenset_key(subset: Iterable[str]) -> frozenset:
    return frozenset(str(s) for s in subset)


def read_mass_function(body: Any, frame: Sequence[str], words: str) -> dict[frozenset, float]:
    """
    One body of evidence as m: 2^Theta -> [0,1] with m(empty)=0 and sum m(A)=1.

    Refused rather than normalised when the masses do not sum to one: a body whose masses do not
    sum to one is not a mass function, and scaling it to make it one asserts a distribution the
    evidence did not state.
    """
    if not isinstance(body, dict):
        raise StructureAbsent(
            f"The {words} provided for this project is not in a form this measure can read, so "
            f"no combination is carried out.")
    focal = body.get("masses")
    if not isinstance(focal, list) or not focal:
        raise StructureAbsent(
            f"A body of evidence provided for this project assigns no mass to anything, so no "
            f"combination is carried out.")
    out: dict[frozenset, float] = {}
    for entry in focal:
        if not isinstance(entry, dict):
            raise StructureAbsent(
                f"The {words} provided for this project is not in a form this measure can read.")
        subset = entry.get("subset")
        if not isinstance(subset, list) or not subset:
            raise StructureAbsent(
                "A body of evidence provided for this project assigns mass to the empty set, "
                "which carries no meaning under this method, so no combination is carried out.")
        key = _frozenset_key(subset)
        if not key <= set(frame):
            raise StructureAbsent(
                "A body of evidence provided for this project assigns mass to a state that is "
                "not among the states being distinguished, so no combination is carried out.")
        value = _f(entry, "mass", words)
        if value < 0:
            raise StructureAbsent(
                "A body of evidence provided for this project assigns a negative mass, which "
                "this method is not defined on, so no combination is carried out.")
        out[key] = out.get(key, 0.0) + value
    total = sum(out.values())
    if abs(total - 1.0) > 1e-9:
        raise StructureAbsent(
            "A body of evidence provided for this project does not distribute exactly all of "
            "its mass, so it is refused rather than rescaled, and no combination is carried "
            "out.")
    return out


def belief(mass: dict[frozenset, float], event: Iterable[str]) -> float:
    """Bel(A) = sum over B subset of A of m(B)."""
    a = _frozenset_key(event)
    return sum(v for b, v in mass.items() if b <= a)


def plausibility(mass: dict[frozenset, float], event: Iterable[str]) -> float:
    """Pl(A) = sum over B intersecting A of m(B)."""
    a = _frozenset_key(event)
    return sum(v for b, v in mass.items() if b & a)


def conflict_coefficient(m1: dict[frozenset, float], m2: dict[frozenset, float]) -> float:
    """K = sum over disjoint pairs of m1(B) m2(C).

    IGNORANCE IS NOT CONFLICT. Mass on the full frame intersects every subset, so it contributes
    nothing to K -- that falls out of the definition and is not a special case here, which is
    exactly why the definition is used rather than a count of disagreeing arms.
    """
    return sum(v1 * v2 for b, v1 in m1.items() for c, v2 in m2.items() if not (b & c))


def dempster_combine(m1: dict[frozenset, float], m2: dict[frozenset, float],
                     *, assume_independent: bool) -> dict[str, Any]:
    """
    Dempster's rule of combination, refusing the two cases where it is not defined.

    INDEPENDENCE IS ASSERTED, NEVER ASSUMED. `assume_independent` has no default: Dempster's rule
    normalises by a conflict coefficient defined only for independent bodies, so combining two
    readings of one body is the same evidence counted twice. A caller that has not established
    independence gets a refusal, which is FUSION.1's EXPLICIT UNRESOLVED default carried into
    this layer unchanged.

    TOTAL CONFLICT (K = 1) IS NAMED, NOT DIVIDED BY. No verdict is fabricated for it.
    """
    if not assume_independent:
        return {"combined": False, "state": "DEPENDENCE_UNRESOLVED",
                "reason": "these bodies of evidence have not been established as independent of "
                          "one another, so combining them would count the same evidence twice "
                          "and no combination is carried out"}
    k = conflict_coefficient(m1, m2)
    if k >= 1.0 - 1e-12:
        return {"combined": False, "state": "TOTAL_CONFLICT", "conflict": 1.0,
                "reason": "these two bodies of evidence exclude one another completely, so this "
                          "method returns no combined belief and the disagreement is referred "
                          "for review"}
    out: dict[frozenset, float] = {}
    for b, v1 in m1.items():
        for c, v2 in m2.items():
            inter = b & c
            if not inter:
                continue
            out[inter] = out.get(inter, 0.0) + (v1 * v2) / (1.0 - k)
    return {"combined": True, "state": "COMBINED", "conflict": k, "mass": out}


def discount(mass: dict[frozenset, float], alpha: float,
             frame: Sequence[str]) -> dict[frozenset, float]:
    """Shafer's reliability discount: m'(A) = alpha m(A) for A != Theta, m'(Theta) picks up the
    remainder. alpha is a supplied reliability and is never inferred."""
    if not (0.0 <= alpha <= 1.0):
        raise StructureAbsent(
            "The reliability stated for a body of evidence on this project is outside the range "
            "a discount is defined on, so no discount is applied and no reading is taken.")
    theta = _frozenset_key(frame)
    out: dict[frozenset, float] = {}
    for a, v in mass.items():
        if a == theta:
            continue
        out[a] = alpha * v
    out[theta] = 1.0 - alpha + alpha * mass.get(theta, 0.0)
    return out


def dempster_shafer(structure: dict) -> dict[str, Any]:
    """The governed B2.1 structure: a frame and the bodies of evidence over it."""
    words = V5_STRUCTURE_WORDS["B2.1"]
    frame = structure.get("frame")
    if not isinstance(frame, list) or len(frame) < 2:
        raise StructureAbsent(
            f"The {words} provided for this project does not say which states are being told "
            f"apart, so no combination is carried out.")
    frame = [str(s) for s in frame]
    bodies = _rows(structure, "bodies", words)
    read = []
    for b in bodies:
        _provenance(b, words, "body_id", "evidence_source")
        read.append({"body_id": str(b["body_id"]).strip(),
                     "evidence_source": str(b["evidence_source"]).strip(),
                     "mass": read_mass_function(b, frame, words)})
    # SAME EVIDENCE SOURCE IS ONE BODY. Two mass functions read off one source are not two
    # independent bodies and Dempster's rule may not be applied across them.
    seen: dict[str, str] = {}
    for r in read:
        prior = seen.get(r["evidence_source"])
        if prior is not None:
            return {"estimable": False, "state": "DEPENDENCE_UNRESOLVED",
                    "reason": "two of the bodies of evidence provided for this project were "
                              "read from the same source, so combining them would count that "
                              "evidence twice and no combination is carried out",
                    "dependent_pair": [prior, r["body_id"]]}
        seen[r["evidence_source"]] = r["body_id"]
    if len(read) == 1:
        m = read[0]["mass"]
        return {"estimable": True, "state": "SINGLE_BODY", "bodies": 1,
                "conflict_estimable": False, "mass": m,
                "belief": {s: belief(m, [s]) for s in frame},
                "plausibility": {s: plausibility(m, [s]) for s in frame}}
    acc = read[0]["mass"]
    conflicts = []
    for r in read[1:]:
        step = dempster_combine(acc, r["mass"], assume_independent=True)
        if not step["combined"]:
            return {"estimable": False, "state": step["state"], "reason": step["reason"],
                    "conflict": step.get("conflict")}
        conflicts.append(step["conflict"])
        acc = step["mass"]
    return {"estimable": True, "state": "COMBINED", "bodies": len(read),
            "conflict_estimable": True, "conflict": conflicts[-1],
            "pairwise_conflict": conflicts, "mass": acc,
            "belief": {s: belief(acc, [s]) for s in frame},
            "plausibility": {s: plausibility(acc, [s]) for s in frame}}


# =================================================================================================
# 7.2 ROUGH SETS
# =================================================================================================

def rough_approximations(structure: dict, *, attributes: Sequence[str] | None = None,
                         target: Any = None) -> dict[str, Any]:
    """
    Indiscernibility over the condition attributes, and the lower/upper approximation of the
    target decision class.

    ONE CURRENT PROJECT ROW IS NOT A DECISION TABLE. The universe must hold more than one case
    and the table must record a decision, or there is nothing to approximate.
    """
    words = V5_STRUCTURE_WORDS["B2.2"]
    rows = _rows(structure, "cases", words)
    cond = attributes if attributes is not None else structure.get("condition_attributes")
    if not isinstance(cond, (list, tuple)) or not cond:
        raise StructureAbsent(
            f"The {words} provided for this project does not say which attributes the cases are "
            f"to be told apart on, so no approximation is carried out.")
    decision_attr = str(structure.get("decision_attribute") or "").strip()
    if not decision_attr:
        raise StructureAbsent(
            f"The {words} provided for this project records no decision against its cases, so "
            f"there is nothing to approximate and no reading is taken.")
    if len(rows) < 2:
        raise StructureAbsent(
            f"The {words} provided for this project holds a single case. One case cannot be "
            f"told apart from another, so no approximation is carried out.")
    universe: list[str] = []
    classes: dict[tuple, list[str]] = {}
    decisions: dict[str, Any] = {}
    for row in rows:
        case_id = str(row.get("case_id") or "").strip()
        if not case_id:
            raise StructureAbsent(
                f"A case in the {words} provided for this project has no identity, so the cases "
                f"cannot be told apart and no approximation is carried out.")
        if case_id in decisions:
            raise StructureAbsent(
                f"The {words} provided for this project lists the same case twice, so no "
                f"approximation is carried out.")
        for a in cond:
            if a not in row:
                raise StructureAbsent(
                    f"A case in the {words} provided for this project does not record every "
                    f"attribute the cases are told apart on, so no approximation is carried "
                    f"out and no value is assumed for the ones it omits.")
        if decision_attr not in row:
            raise StructureAbsent(
                f"A case in the {words} provided for this project records no decision, so no "
                f"approximation is carried out.")
        universe.append(case_id)
        decisions[case_id] = row[decision_attr]
        classes.setdefault(tuple(row[a] for a in cond), []).append(case_id)
    if target is None:
        target = structure.get("target_decision")
    if target is None:
        raise StructureAbsent(
            f"The {words} provided for this project does not say which decision is being "
            f"approximated, so no approximation is carried out.")
    x = {c for c in universe if decisions[c] == target}
    lower: set[str] = set()
    upper: set[str] = set()
    for members in classes.values():
        block = set(members)
        if block <= x:
            lower |= block
        if block & x:
            upper |= block
    return {
        "estimable": True,
        "universe": sorted(universe),
        "equivalence_classes": [sorted(v) for v in classes.values()],
        "target": target,
        "target_set": sorted(x),
        "lower": sorted(lower),
        "upper": sorted(upper),
        "boundary": sorted(upper - lower),
        "accuracy": (len(lower) / len(upper)) if upper else None,
    }


# =================================================================================================
# 7.3 NEUTROSOPHIC LOGIC
# =================================================================================================

def neutrosophic(structure: dict) -> dict[str, Any]:
    """
    A single-valued neutrosophic triple (T, I, F), each independently in [0, 1].

    I IS NOT 1 - T - F. Indeterminacy is an independent quantity in this representation; deriving
    it from the other two collapses three degrees of freedom to two and makes (0.7, 0.2, 0.1) and
    (0.7, 0.8, 0.1) the same object, which they are not. There is no branch below that computes I.
    They need not sum to one and no sum is checked.
    """
    words = V5_STRUCTURE_WORDS["B2.3"]
    _provenance(structure, words, "assessed_by", "source")
    for field in ("truth", "indeterminacy", "falsity"):
        if field not in structure:
            raise StructureAbsent(
                f"The {words} provided for this project does not state all three degrees "
                f"separately, so no reading is taken and none of them is derived from the "
                f"others.")
    t = _unit(structure, "truth", words)
    i = _unit(structure, "indeterminacy", words)
    f = _unit(structure, "falsity", words)
    return {"estimable": True, "truth": t, "indeterminacy": i, "falsity": f,
            "sum": t + i + f,
            "indeterminacy_is_independent": True}


# =================================================================================================
# 7.4 INTERVAL FUZZY SETS
# =================================================================================================

def _interval(container: Any, words: str) -> tuple[float, float]:
    lo = _unit(container, "lower", words)
    up = _unit(container, "upper", words)
    if lo > up:
        raise StructureAbsent(
            f"The {words} provided for this project states a range whose lower degree is above "
            f"its upper degree, which is not a range, so no reading is taken from it.")
    return lo, up


def interval_fuzzy(structure: dict) -> dict[str, Any]:
    """mu(x) = [l, u] with 0 <= l <= u <= 1, and the v15 min/max operators."""
    words = V5_STRUCTURE_WORDS["B2.4"]
    _provenance(structure, words, "assessed_by", "source")
    return {"estimable": True, "membership": list(_interval(structure, words))}


def interval_intersection(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    """[min(l1,l2), min(u1,u2)] -- the v15 operator named by the contract."""
    return (min(a[0], b[0]), min(a[1], b[1]))


def interval_union(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    """[max(l1,l2), max(u1,u2)] -- the v15 operator named by the contract."""
    return (max(a[0], b[0]), max(a[1], b[1]))


# =================================================================================================
# 7.5 Z-NUMBERS
# =================================================================================================

def z_number(structure: dict) -> dict[str, Any]:
    """
    Z = (A, B): a restriction and an EXPLICIT statement of its reliability.

    A MISSING B IS NOT FULL RELIABILITY. An assessment nobody has vouched for is refused, because
    treating silence as certainty is the single most favourable substitution available here.

    THE REDUCTION OPERATOR IS BLOCKED. No exact reduction from Z to a single restriction is
    frozen in the supervisory artifacts -- they cite Zadeh (2011) by DOI and nothing more -- so
    none is chosen here. Representation and provenance only.
    """
    words = V5_STRUCTURE_WORDS["B2.5"]
    _provenance(structure, words, "assessed_by", "source")
    a = structure.get("restriction")
    b = structure.get("reliability")
    if not isinstance(a, dict) or not str(a.get("term") or "").strip():
        raise StructureAbsent(
            f"The {words} provided for this project does not state what is being asserted, so "
            f"no reading is taken from it.")
    if not isinstance(b, dict) or not str(b.get("term") or "").strip():
        raise StructureAbsent(
            f"The {words} provided for this project does not say how reliable the assertion is. "
            f"A missing statement of reliability is not a statement of full reliability, so no "
            f"reading is taken from it.")
    return {
        "estimable": True,
        "restriction": {"term": str(a["term"]).strip(),
                        "membership": list(_interval(a, words)) if "lower" in a else None},
        "reliability": {"term": str(b["term"]).strip(),
                        "membership": list(_interval(b, words)) if "lower" in b else None},
        "reduction": None,
        "reduction_blocked": "no reduction of a restriction and its reliability to a single "
                             "figure has been set for this platform, so none is carried out",
    }


# =================================================================================================
# 7.6 PROBABILISTIC LINGUISTIC TERM SETS
# =================================================================================================

def plts(structure: dict) -> dict[str, Any]:
    """
    L(p) = {s_k(p_k)} with p_k >= 0 and sum p_k = 1 under this v15 contract.

    A set whose probabilities do not sum to one is refused rather than completed or rescaled.
    """
    words = V5_STRUCTURE_WORDS["B2.6"]
    _provenance(structure, words, "assessed_by", "source")
    rows = _rows(structure, "terms", words)
    terms: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        term = str(row.get("term") or "").strip()
        if not term:
            raise StructureAbsent(
                f"The {words} provided for this project carries a probability against no named "
                f"term, so no reading is taken from it.")
        if term in seen:
            raise StructureAbsent(
                f"The {words} provided for this project names the same term twice, so no "
                f"reading is taken from it.")
        seen.add(term)
        p = _f(row, "probability", words)
        if p < 0:
            raise StructureAbsent(
                f"The {words} provided for this project states a negative probability, which "
                f"this method is not defined on, so no reading is taken from it.")
        terms.append({"term": term, "probability": p})
    total = sum(t["probability"] for t in terms)
    if abs(total - 1.0) > 1e-9:
        raise StructureAbsent(
            f"The {words} provided for this project states probabilities that do not together "
            f"make one, so it is refused rather than rescaled and no reading is taken from it.")
    return {"estimable": True, "terms": terms, "total_probability": total,
            "complete": True, "degenerate": len(terms) == 1}


# =================================================================================================
# 7.7 PLITHOGENIC SETS -- DISABLED / FUTURE RESEARCH
# =================================================================================================

def plithogenic_lab(structure: dict) -> dict[str, Any]:
    """
    The laboratory structure only. NO OPERATIONAL RESULT IS PRODUCED BY THIS FUNCTION.

    The contract requires an explicitly selected operator and the supervisory artifacts freeze
    none, so none is chosen. What is verified is that the structure is complete: attributes, the
    values each may take, the dominant value where one applies, an appurtenance degree and a
    contradiction degree. CONTRADICTION DEGREES ARE NEVER INFERRED from anything.
    """
    words = V5_STRUCTURE_WORDS["B2.7"]
    _provenance(structure, words, "research_origin", "source")
    attrs = _rows(structure, "attributes", words)
    read = []
    for a in attrs:
        name = str(a.get("attribute") or "").strip()
        values = a.get("values")
        if not name or not isinstance(values, list) or not values:
            raise StructureAbsent(
                f"The {words} provided is incomplete, so nothing is read from it.")
        vals = []
        for v in values:
            if not isinstance(v, dict) or not str(v.get("value") or "").strip():
                raise StructureAbsent(
                    f"The {words} provided is incomplete, so nothing is read from it.")
            vals.append({"value": str(v["value"]).strip(),
                         "appurtenance": _unit(v, "appurtenance", words),
                         "contradiction": _unit(v, "contradiction", words)})
        read.append({"attribute": name, "dominant_value": a.get("dominant_value"),
                     "values": vals})
    return {
        "structure_complete": True,
        "attributes": read,
        "operational": False,
        "operator": None,
        "operator_blocked": "the way these degrees would be combined has not been set for this "
                            "platform, so no combination is carried out",
        "disposition": "DISABLED_FUTURE_RESEARCH",
    }


# =================================================================================================
# 7.8 BELIEF RULE BASE
# =================================================================================================

def belief_rule_base(structure: dict) -> dict[str, Any]:
    """
    The rule structure and the single fully activated rule.

    MULTI-RULE EVIDENTIAL-REASONING AGGREGATION IS BLOCKED. The supervisory specification names
    RIMER by DOI and asks for testing "for the selected ER formulation" without selecting one; a
    citation is not a formulation, and choosing an ER variant here would be choosing a theory.
    So: a single fully activated rule returns its own consequent distribution exactly, and two or
    more activated rules return a named refusal.
    """
    words = V5_STRUCTURE_WORDS["B2.8"]
    _provenance(structure, words, "elicited_from", "source")
    consequents = structure.get("consequents")
    if not isinstance(consequents, list) or not consequents:
        raise StructureAbsent(
            f"The {words} provided for this project does not say what its rules conclude about, "
            f"so no inference is carried out.")
    consequents = [str(c) for c in consequents]
    rules = _rows(structure, "rules", words)
    read = []
    for r in rules:
        rid = str(r.get("rule_id") or "").strip()
        if not rid:
            raise StructureAbsent(
                f"A rule in the {words} provided for this project has no identity, so no "
                f"inference is carried out.")
        antecedents = r.get("antecedents")
        if not isinstance(antecedents, dict) or not antecedents:
            raise StructureAbsent(
                f"A rule in the {words} provided for this project states no antecedent "
                f"reference states, so it is not a rule and no inference is carried out.")
        weight = _unit(r, "rule_weight", words)
        beliefs = r.get("beliefs")
        if not isinstance(beliefs, dict) or not beliefs:
            raise StructureAbsent(
                f"A rule in the {words} provided for this project concludes no belief "
                f"distribution, so no inference is carried out.")
        dist: dict[str, float] = {}
        for c in consequents:
            if c in beliefs:
                dist[c] = _unit(beliefs, c, words)
        for c in beliefs:
            if c not in consequents:
                raise StructureAbsent(
                    f"A rule in the {words} provided for this project puts belief on something "
                    f"it does not conclude about, so no inference is carried out.")
        total = sum(dist.values())
        if total > 1.0 + 1e-9:
            raise StructureAbsent(
                f"A rule in the {words} provided for this project distributes more than all of "
                f"its belief, which this method is not defined on, so no inference is carried "
                f"out.")
        activation = _unit(r, "activation", words)
        read.append({"rule_id": rid, "antecedents": dict(antecedents),
                     "rule_weight": weight, "beliefs": dist,
                     "belief_total": total, "incompleteness": 1.0 - total,
                     "activation": activation})
    attr_weights = structure.get("attribute_weights")
    if not isinstance(attr_weights, dict) or not attr_weights:
        raise StructureAbsent(
            f"The {words} provided for this project states no attribute weights, so no "
            f"inference is carried out and no weight is assumed.")
    for k in attr_weights:
        _unit(attr_weights, k, words)
    activated = [r for r in read if r["activation"] > 0]
    if not activated:
        return {"estimable": False, "rules": read,
                "reason": "no rule in this project's rule base is activated by its evidence, so "
                          "no conclusion is drawn"}
    if len(activated) == 1 and abs(activated[0]["activation"] - 1.0) <= 1e-12:
        r = activated[0]
        return {"estimable": True, "rules": read, "activated": [r["rule_id"]],
                "aggregation": "SINGLE_FULLY_ACTIVATED_RULE",
                "belief": dict(r["beliefs"]), "incompleteness": r["incompleteness"],
                "attribute_weights": dict(attr_weights)}
    return {
        "estimable": False,
        "rules": read,
        "activated": [r["rule_id"] for r in activated],
        "state": "AGGREGATION_BLOCKED",
        "reason": "more than one rule speaks to this project at once, and the way this platform "
                  "is to combine what several rules conclude has not been set, so no combined "
                  "conclusion is drawn",
    }


# =================================================================================================
# 7.9 QUANTUM PROBABILITY -- ARCHIVED FUTURE RESEARCH
# =================================================================================================

#: The archive record. Section 16 of the contract: this is scientific history, not a capability.
QUANTUM_ARCHIVE: dict[str, Any] = {
    "identity": "B2.9",
    "canonical_name": "Quantum Probability",
    "historical_implementation": "server/app/simulation/models_gov.py (run_quantum_probability), "
                                 "ported from assets/js/simulations.js",
    "historical_tests": "server/tools/test_run14_disabled_method_functional.py, "
                        "server/tools/test_run15_disabled_root_cause.py",
    "literature_record": "Quantum probability as a probability formalism; PCEIF project-control "
                         "applicability requires an actual context/order-effect model "
                         "(supervisory specification, Category-7 sources).",
    "reason_archived": "the formalism is genuine, but nothing in this platform supplies the "
                       "context or order-effect model that would make a project-control reading "
                       "from it mean anything",
    "missing_restoration_evidence": "a project-control model in which measurement order changes "
                                    "the answer, and evidence that it does",
    "restoration_prerequisites": (
        "an explicit Hilbert-space state space over project-control propositions with governed "
        "provenance; an explicit measurement/projection model; empirical evidence of an order or "
        "context effect in project-control judgement that a classical model does not account "
        "for; owner authorisation; and calibration and empirical validation under Run 33"),
    "operational_activation": False,
    "voting": False,
    "participant_operational_visibility": False,
}


def quantum_lab_born_rule(amplitudes: Sequence[complex]) -> list[float]:
    """
    RESEARCH-HISTORY VERIFICATION ONLY. Not reachable from any operational path and registered
    nowhere; it exists so the archived identity's mathematics stays checkable.

    Born rule: P(i) = |amplitude_i|^2 over a normalised state.
    """
    norm = math.sqrt(sum(abs(a) ** 2 for a in amplitudes))
    if norm <= 0:
        raise ValueError("a state vector of zero length is not a state")
    return [abs(a) ** 2 / (norm ** 2) for a in amplitudes]


# =================================================================================================
# 7.10 - 7.17 THE FUZZY FAMILY
#
# SEVEN SEPARATE DOMAIN ENFORCEMENTS, NOT ONE SHARED VALIDATOR. Section 8 of the contract. Each
# function below states its own defining constraint in its own terms; there is no generic tuple
# validator any of them delegates the constraint to, so one family's admissibility model cannot
# silently become another's.
# =================================================================================================

def pythagorean_fuzzy(structure: dict) -> dict[str, Any]:
    """mu^2 + nu^2 <= 1; hesitancy pi = sqrt(1 - mu^2 - nu^2)."""
    words = V5_STRUCTURE_WORDS["B2.10"]
    _provenance(structure, words, "assessed_by", "source")
    mu = _unit(structure, "membership", words)
    nu = _unit(structure, "non_membership", words)
    total = mu * mu + nu * nu
    if total > 1.0 + 1e-12:
        raise StructureAbsent(
            f"The {words} provided for this project states a pair this representation is not "
            f"defined on, so it is refused rather than scaled back into range and no reading is "
            f"taken from it.")
    return {"estimable": True, "membership": mu, "non_membership": nu,
            "squared_sum": total,
            "hesitancy": math.sqrt(max(0.0, 1.0 - total))}


def picture_fuzzy(structure: dict) -> dict[str, Any]:
    """mu + eta + nu <= 1, each non-negative; refusal r = 1 - mu - eta - nu.

    NEUTRALITY IS NOT MISSINGNESS AND NOT REFUSAL. Three separate fields, three separate
    meanings, and the refusal is what the three leave over rather than a fourth assessment.
    """
    words = V5_STRUCTURE_WORDS["B2.11"]
    _provenance(structure, words, "assessed_by", "source")
    mu = _unit(structure, "positive", words)
    eta = _unit(structure, "neutral", words)
    nu = _unit(structure, "negative", words)
    total = mu + eta + nu
    if total > 1.0 + 1e-12:
        raise StructureAbsent(
            f"The {words} provided for this project states degrees that together exceed what "
            f"this representation allows, so it is refused rather than scaled and no reading is "
            f"taken from it.")
    return {"estimable": True, "positive": mu, "neutral": eta, "negative": nu,
            "sum": total, "refusal": 1.0 - total}


def hesitant_fuzzy(structure: dict) -> dict[str, Any]:
    """
    h(x) subset of [0,1]. The v15 LABORATORY SCORE is the arithmetic mean.

    THIS IS A DECLARED LABORATORY SCORING OPERATOR, not a claim that it is the only hesitant
    fuzzy score. It is permutation invariant, returns a single supplied value unchanged, and is
    not defined on the empty set -- an empty hesitant element is Not Estimable and never a
    favourable one.
    """
    words = V5_STRUCTURE_WORDS["B2.12"]
    _provenance(structure, words, "assessed_by", "source")
    values = structure.get("degrees")
    if not isinstance(values, list):
        raise StructureAbsent(
            f"The {words} provided for this project is not in a form this measure can read, so "
            f"no reading is taken from it.")
    if not values:
        raise StructureAbsent(
            "No assessor gave a degree for this project, so there is nothing to take a hesitant "
            "assessment over and no reading is reported in place of one.")
    degrees = []
    for idx, _v in enumerate(values):
        degrees.append(_unit({"degree": values[idx]}, "degree", words))
    return {"estimable": True, "degrees": degrees, "count": len(degrees),
            "score_operator": "arithmetic mean (declared v15 laboratory scoring operator)",
            "score": sum(degrees) / len(degrees)}


def type2_fuzzy(structure: dict) -> dict[str, Any]:
    """
    A genuine interval type-2 membership: a SEPARATE lower and upper membership at every point
    considered, and the footprint of uncertainty between them.

    TYPE REDUCTION AND INFERENCE ARE BLOCKED and nothing here averages the two bounds. The
    supervisory artifacts cite Karnik-Mendel by DOI and ask that a centroid type reduction "if"
    used be verified; they contain no formulation sufficient to implement or independently
    verify. Midpoint averaging is explicitly forbidden as a substitute, so the footprint is
    preserved and no single figure is produced.

    ZERO FOOTPRINT WIDTH IS A REAL ASSESSMENT, NOT MISSING DATA: lower = upper means the
    assessors were certain at that point.
    """
    words = V5_STRUCTURE_WORDS["B2.13"]
    _provenance(structure, words, "assessed_by", "source")
    rows = _rows(structure, "points", words)
    points = []
    seen: set = set()
    for row in rows:
        if "x" not in row:
            raise StructureAbsent(
                f"The {words} provided for this project does not say which point each membership "
                f"belongs to, so no reading is taken from it.")
        x = row["x"]
        if x in seen:
            raise StructureAbsent(
                f"The {words} provided for this project gives two memberships at the same point, "
                f"so no reading is taken from it.")
        seen.add(x)
        lo, up = _interval(row, words)
        points.append({"x": x, "lower": lo, "upper": up, "fou_width": up - lo})
    return {
        "estimable": True,
        "points": points,
        "max_fou_width": max(p["fou_width"] for p in points),
        "type_reduced": None,
        "type_reduction_blocked": "the way this platform is to reduce a membership that is "
                                  "itself a range to a single figure has not been set, so no "
                                  "single figure is produced and the range is reported as it is",
    }


def spherical_fuzzy(structure: dict) -> dict[str, Any]:
    """mu^2 + nu^2 + pi^2 <= 1, all three components distinct and each in [0, 1]."""
    words = V5_STRUCTURE_WORDS["B2.16"]
    _provenance(structure, words, "assessed_by", "source")
    mu = _unit(structure, "membership", words)
    nu = _unit(structure, "non_membership", words)
    pi = _unit(structure, "hesitancy", words)
    total = mu * mu + nu * nu + pi * pi
    if total > 1.0 + 1e-12:
        raise StructureAbsent(
            f"The {words} provided for this project states degrees this representation is not "
            f"defined on, so it is refused rather than brought into range and no reading is "
            f"taken from it.")
    return {"estimable": True, "membership": mu, "non_membership": nu, "hesitancy": pi,
            "squared_sum": total, "refusal_slack": 1.0 - total}


def fermatean_fuzzy(structure: dict) -> dict[str, Any]:
    """
    mu^3 + nu^3 <= 1.

    NO RENORMALISATION LOOP. The v14 implementation multiplied an inadmissible pair by 0.95 until
    it fitted, which reports a pair nobody assessed; an inadmissible pair is refused here.
    """
    words = V5_STRUCTURE_WORDS["B2.17"]
    _provenance(structure, words, "assessed_by", "source")
    mu = _unit(structure, "membership", words)
    nu = _unit(structure, "non_membership", words)
    total = mu ** 3 + nu ** 3
    if total > 1.0 + 1e-12:
        raise StructureAbsent(
            f"The {words} provided for this project states a pair this representation is not "
            f"defined on, so it is refused rather than shrunk into range and no reading is taken "
            f"from it.")
    return {"estimable": True, "membership": mu, "non_membership": nu, "cubed_sum": total}


# =================================================================================================
# 7.14 MAXIMUM ENTROPY
# =================================================================================================

def maximum_entropy(structure: dict, *, tolerance: float = 1e-12,
                    max_iterations: int = 200) -> dict[str, Any]:
    """
    THE ACTUAL CONSTRAINED OPTIMISATION, not the entropy of a supplied vector.

    maximise H(p) = -sum_i p_i ln p_i subject to p_i >= 0, sum_i p_i = 1 and the supplied moment
    constraints sum_i p_i f_k(x_i) = b_k.

    Solved through the convex dual, which is the standard route and the only one that makes the
    solution provably the maximiser rather than a plausible-looking vector: the maximiser has the
    exponential form p_i = exp(sum_k lambda_k f_k(x_i)) / Z(lambda), and lambda minimises the
    convex potential ln Z(lambda) - sum_k lambda_k b_k, whose gradient is the constraint residual
    and whose Hessian is the covariance of the constraint functions. Newton with a backtracking
    line search on a convex function of a handful of variables.

    WITH NO MOMENT CONSTRAINTS THE MAXIMISER IS UNIFORM and falls out of the same machinery
    rather than being written down: lambda = 0 is stationary, so p is uniform and H = ln n.

    INFEASIBILITY IS NAMED. A required expectation outside the range the state space can produce
    has no solution at all, and no distribution is fabricated for it.
    """
    words = V5_STRUCTURE_WORDS["B2.14"]
    _provenance(structure, words, "defined_by", "source")
    rows = _rows(structure, "states", words)
    labels: list[str] = []
    for row in rows:
        label = str(row.get("state") or "").strip()
        if not label:
            raise StructureAbsent(
                f"A state in the {words} provided for this project has no name, so no "
                f"distribution is inferred.")
        if label in labels:
            raise StructureAbsent(
                f"The {words} provided for this project names the same state twice, so no "
                f"distribution is inferred.")
        labels.append(label)
    if len(labels) < 2:
        raise StructureAbsent(
            f"The {words} provided for this project holds fewer than two states, so there is "
            f"nothing to distribute belief over and no distribution is inferred.")
    n = len(labels)
    raw_constraints = structure.get("constraints")
    if raw_constraints is None:
        raw_constraints = []
    if not isinstance(raw_constraints, list):
        raise StructureAbsent(
            f"The {words} provided for this project states its constraints in a form this "
            f"measure cannot read, so no distribution is inferred.")
    fs: list[list[float]] = []
    bs: list[float] = []
    names: list[str] = []
    for c in raw_constraints:
        if not isinstance(c, dict):
            raise StructureAbsent(
                f"The {words} provided for this project states its constraints in a form this "
                f"measure cannot read, so no distribution is inferred.")
        name = str(c.get("constraint") or "").strip()
        values = c.get("values")
        if not name or not isinstance(values, list) or len(values) != n:
            raise StructureAbsent(
                f"A constraint in the {words} provided for this project does not give a figure "
                f"for every state, so no distribution is inferred.")
        row = [_f({"v": v}, "v", words) for v in values]
        target = _f(c, "expectation", words)
        lo, hi = min(row), max(row)
        if target < lo - 1e-12 or target > hi + 1e-12:
            return {"estimable": False, "state": "INFEASIBLE",
                    "reason": "the evidence for this project requires an average this set of "
                              "states cannot produce, so there is no distribution consistent "
                              "with it and none is reported",
                    "infeasible_constraint": name}
        fs.append(row)
        bs.append(target)
        names.append(name)
    k = len(fs)
    lam = [0.0] * k

    def dist(l: Sequence[float]) -> list[float]:
        expo = [sum(l[j] * fs[j][i] for j in range(k)) for i in range(n)]
        shift = max(expo) if expo else 0.0
        w = [math.exp(e - shift) for e in expo]
        z = sum(w)
        return [x / z for x in w]

    def potential(l: Sequence[float]) -> float:
        expo = [sum(l[j] * fs[j][i] for j in range(k)) for i in range(n)]
        shift = max(expo) if expo else 0.0
        z = shift + math.log(sum(math.exp(e - shift) for e in expo))
        return z - sum(l[j] * bs[j] for j in range(k))

    iterations = 0
    converged = k == 0
    p = dist(lam)
    for iterations in range(1, max_iterations + 1):
        if k == 0:
            break
        p = dist(lam)
        grad = [sum(p[i] * fs[j][i] for i in range(n)) - bs[j] for j in range(k)]
        if max(abs(g) for g in grad) < 1e-11:
            converged = True
            break
        hess = [[sum(p[i] * fs[a][i] * fs[b][i] for i in range(n))
                 - sum(p[i] * fs[a][i] for i in range(n))
                 * sum(p[i] * fs[b][i] for i in range(n))
                 for b in range(k)] for a in range(k)]
        step = _solve_linear(hess, [-g for g in grad])
        if step is None:
            step = [-g for g in grad]
        base = potential(lam)
        t = 1.0
        for _ in range(60):
            trial = [lam[j] + t * step[j] for j in range(k)]
            if potential(trial) <= base - 1e-18:
                break
            t *= 0.5
        else:
            converged = False
            break
        lam = [lam[j] + t * step[j] for j in range(k)]
    if k and not converged:
        p = dist(lam)
        grad = [sum(p[i] * fs[j][i] for i in range(n)) - bs[j] for j in range(k)]
        if max(abs(g) for g in grad) < 1e-9:
            converged = True
    if k and not converged:
        return {"estimable": False, "state": "NOT_SOLVED",
                "reason": "no distribution consistent with the evidence supplied for this "
                          "project could be found, so none is reported"}
    p = dist(lam)
    entropy = -sum(x * math.log(x) for x in p if x > 0)
    return {
        "estimable": True,
        "state": "SOLVED",
        "states": labels,
        "distribution": {labels[i]: p[i] for i in range(n)},
        "entropy": entropy,
        "multipliers": {names[j]: lam[j] for j in range(k)},
        "constraint_expectations": {names[j]: sum(p[i] * fs[j][i] for i in range(n))
                                    for j in range(k)},
        "iterations": iterations if k else 0,
        "solver": "dual Newton with backtracking line search on the convex log-partition "
                  "potential, v15",
        "tolerance": tolerance,
    }


def _solve_linear(a: list[list[float]], b: list[float]) -> list[float] | None:
    """Gaussian elimination with partial pivoting. None when the system is singular."""
    n = len(b)
    if n == 0:
        return []
    m = [list(a[i]) + [b[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-14:
            return None
        m[col], m[pivot] = m[pivot], m[col]
        pv = m[col][col]
        for r in range(n):
            if r == col:
                continue
            factor = m[r][col] / pv
            if factor:
                for c in range(col, n + 1):
                    m[r][c] -= factor * m[col][c]
    return [m[i][n] / m[i][i] for i in range(n)]


# =================================================================================================
# 7.15 POSSIBILITY THEORY
# =================================================================================================

def possibility(structure: dict) -> dict[str, Any]:
    """
    A NORMALISED possibility distribution: pi(x) in [0,1] with sup_x pi(x) = 1.

    NORMALISED MEANS THE SUPREMUM IS ONE, NOT THAT THE DEGREES SUM TO ONE. Possibility is a
    maxitive measure, not an additive one, and requiring the degrees to sum to one would turn it
    into a probability and destroy the distinction the module exists to represent. No sum is
    computed here for any purpose.
    """
    words = V5_STRUCTURE_WORDS["B2.15"]
    _provenance(structure, words, "assessed_by", "source")
    rows = _rows(structure, "states", words)
    pi: dict[str, float] = {}
    for row in rows:
        label = str(row.get("state") or "").strip()
        if not label:
            raise StructureAbsent(
                f"A state in the {words} provided for this project has no name, so no reading "
                f"is taken from it.")
        if label in pi:
            raise StructureAbsent(
                f"The {words} provided for this project names the same state twice, so no "
                f"reading is taken from it.")
        pi[label] = _unit(row, "possibility", words)
    if abs(max(pi.values()) - 1.0) > 1e-12:
        raise StructureAbsent(
            f"The {words} provided for this project holds no state that is fully possible, so "
            f"it is refused rather than rescaled and no reading is taken from it.")
    return {"estimable": True, "distribution": pi, "universe": sorted(pi)}


def possibility_of(pi: dict[str, float], event: Iterable[str]) -> float:
    """Pi(A) = sup over x in A of pi(x). The empty event has possibility zero."""
    members = [pi[x] for x in event if x in pi]
    return max(members) if members else 0.0


def necessity_of(pi: dict[str, float], event: Iterable[str]) -> float:
    """N(A) = 1 - Pi(complement of A)."""
    a = set(event)
    return 1.0 - possibility_of(pi, [x for x in pi if x not in a])


# =================================================================================================
# 7.18 / 7.19 THE SHARED DECISION STRUCTURE
#
# ONE governed alternatives/criteria object for MARCOS and CRITIC-TOPSIS, reusable by Run 32's
# Category-10 methods. Section 10 of the contract.
# =================================================================================================

def decision_problem(structure: dict, *, module_id: str,
                     require_weights: bool) -> dict[str, Any]:
    """Read and validate the shared decision structure. Criteria are never alternatives."""
    words = V5_STRUCTURE_WORDS[module_id]
    _provenance(structure, words, "context_id", "source")
    period = structure.get("period")
    crits = _rows(structure, "criteria", words)
    criteria: list[dict] = []
    seen_c: set[str] = set()
    for c in crits:
        cid = str(c.get("criterion_id") or "").strip()
        orientation = str(c.get("orientation") or "").strip().lower()
        if not cid:
            raise StructureAbsent(
                f"A criterion in the {words} provided for this project has no identity, so no "
                f"ranking is carried out.")
        if cid in seen_c:
            raise StructureAbsent(
                f"The {words} provided for this project names the same criterion twice, so no "
                f"ranking is carried out.")
        if orientation not in ("benefit", "cost"):
            raise StructureAbsent(
                f"A criterion in the {words} provided for this project does not say whether "
                f"more of it is better or worse, so no ranking is carried out and neither is "
                f"assumed.")
        seen_c.add(cid)
        entry = {"criterion_id": cid, "label": str(c.get("label") or cid),
                 "orientation": orientation, "units": c.get("units")}
        if require_weights:
            if "weight" not in c:
                raise StructureAbsent(
                    f"The {words} provided for this project does not state a weight for every "
                    f"criterion, so no ranking is carried out and no weight is assumed.")
            w = _f(c, "weight", words)
            if w < 0:
                raise StructureAbsent(
                    f"The {words} provided for this project states a negative criterion weight, "
                    f"which a ranking is not defined on, so none is carried out.")
            entry["weight"] = w
            entry["weight_provenance"] = str(c.get("weight_source") or "").strip()
            if not entry["weight_provenance"]:
                raise StructureAbsent(
                    f"The {words} provided for this project does not say who set its criterion "
                    f"weights, so a ranking taken from them could not be interpreted later and "
                    f"none is carried out.")
        criteria.append(entry)
    if len(criteria) < 2:
        raise StructureAbsent(
            f"The {words} provided for this project compares on fewer than two criteria, so "
            f"there is no multi-criteria problem to solve and no ranking is carried out.")
    alts = _rows(structure, "alternatives", words)
    alternatives: list[dict] = []
    seen_a: set[str] = set()
    for a in alts:
        aid = str(a.get("alternative_id") or "").strip()
        if not aid:
            raise StructureAbsent(
                f"An alternative in the {words} provided for this project has no identity, so "
                f"no ranking is carried out.")
        if aid in seen_a:
            raise StructureAbsent(
                f"The {words} provided for this project names the same alternative twice, so no "
                f"ranking is carried out.")
        seen_a.add(aid)
        values = a.get("values")
        if not isinstance(values, dict):
            raise StructureAbsent(
                f"An alternative in the {words} provided for this project carries no criterion "
                f"values, so no ranking is carried out.")
        row = {}
        for c in criteria:
            if c["criterion_id"] not in values:
                raise StructureAbsent(
                    f"An alternative in the {words} provided for this project is not scored on "
                    f"every criterion, so no ranking is carried out and no score is assumed for "
                    f"the ones it omits.")
            row[c["criterion_id"]] = _f(values, c["criterion_id"], words)
        alternatives.append({"alternative_id": aid,
                             "label": str(a.get("label") or aid), "values": row})
    if len(alternatives) < 2:
        raise StructureAbsent(
            f"The {words} provided for this project holds fewer than two alternatives. A single "
            f"project state is not a choice between options, so no ranking is carried out.")
    weight_total = sum(c.get("weight", 0.0) for c in criteria) if require_weights else None
    if require_weights and weight_total is not None and weight_total <= 0:
        raise StructureAbsent(
            f"The {words} provided for this project gives every criterion no weight at all, so "
            f"no ranking is carried out.")
    return {"context_id": str(structure["context_id"]).strip(),
            "source": str(structure["source"]).strip(), "period": period,
            "criteria": criteria, "alternatives": alternatives,
            "weight_total": weight_total}


def marcos(structure: dict) -> dict[str, Any]:
    """
    MARCOS over an explicit alternatives x criteria problem, in the published steps.

    Extended matrix: the anti-ideal AAI is the worst value of each criterion and the ideal AI the
    best, taking orientation into account. Normalisation is against the IDEAL: n_ij = x_ij / x_AI
    for a benefit criterion and n_ij = x_AI / x_ij for a cost criterion. S_i is the weighted sum
    of the normalised row. Utility degrees K_i^- = S_i / S_AAI and K_i^+ = S_i / S_AI. Utility
    functions f(K_i^-) = K_i^+ / (K_i^+ + K_i^-) and f(K_i^+) = K_i^- / (K_i^+ + K_i^-). The
    utility function of the alternative is

        f(K_i) = (K_i^+ + K_i^-) / (1 + (1 - f(K_i^+))/f(K_i^+) + (1 - f(K_i^-))/f(K_i^-)).

    Ranked descending on f(K_i). WEIGHTS ARE EXTERNALLY GOVERNED and refused when absent.
    """
    problem = decision_problem(structure, module_id="B2.18", require_weights=True)
    criteria = problem["criteria"]
    alts = problem["alternatives"]
    total_w = problem["weight_total"]
    weights = {c["criterion_id"]: c["weight"] / total_w for c in criteria}
    aai, ai = {}, {}
    for c in criteria:
        cid = c["criterion_id"]
        col = [a["values"][cid] for a in alts]
        if c["orientation"] == "benefit":
            ai[cid], aai[cid] = max(col), min(col)
        else:
            ai[cid], aai[cid] = min(col), max(col)

    def normalise(row: dict) -> dict:
        out = {}
        for c in criteria:
            cid = c["criterion_id"]
            if c["orientation"] == "benefit":
                denom = ai[cid]
                if denom == 0:
                    raise StructureAbsent(
                        "The decision problem provided for this project has a criterion on which "
                        "the best alternative scores nothing, so this ranking is not defined on "
                        "it and none is carried out.")
                out[cid] = row[cid] / denom
            else:
                if row[cid] == 0:
                    raise StructureAbsent(
                        "The decision problem provided for this project has an alternative "
                        "costing nothing on a criterion, so this ranking is not defined on it "
                        "and none is carried out.")
                out[cid] = ai[cid] / row[cid]
        return out

    n_aai, n_ai = normalise(aai), normalise(ai)
    s_aai = sum(weights[c["criterion_id"]] * n_aai[c["criterion_id"]] for c in criteria)
    s_ai = sum(weights[c["criterion_id"]] * n_ai[c["criterion_id"]] for c in criteria)
    if s_aai <= 0 or s_ai <= 0:
        raise StructureAbsent(
            "The decision problem provided for this project gives its reference alternatives no "
            "weighted value, so no ranking is carried out.")
    rows = []
    for a in alts:
        norm = normalise(a["values"])
        s = sum(weights[c["criterion_id"]] * norm[c["criterion_id"]] for c in criteria)
        k_minus = s / s_aai
        k_plus = s / s_ai
        denom = k_plus + k_minus
        f_minus = k_plus / denom
        f_plus = k_minus / denom
        util = denom / (1.0 + (1.0 - f_plus) / f_plus + (1.0 - f_minus) / f_minus)
        rows.append({"alternative_id": a["alternative_id"], "normalised": norm,
                     "weighted_sum": s, "k_minus": k_minus, "k_plus": k_plus,
                     "f_k_minus": f_minus, "f_k_plus": f_plus, "utility": util})
    order = sorted(rows, key=lambda r: (-r["utility"], r["alternative_id"]))
    ranks: dict[str, int] = {}
    rank = 0
    prev = None
    for idx, r in enumerate(order):
        if prev is None or abs(r["utility"] - prev) > 1e-12:
            rank = idx + 1
            prev = r["utility"]
        ranks[r["alternative_id"]] = rank
    return {"estimable": True, "context_id": problem["context_id"],
            "normalised_weights": weights, "ideal": ai, "anti_ideal": aai,
            "s_ideal": s_ai, "s_anti_ideal": s_aai, "rows": rows,
            "ranking": [r["alternative_id"] for r in order], "ranks": ranks,
            "lineage": {"source": problem["source"], "period": problem["period"],
                        "derived_from": "the decision alternatives supplied for this project; "
                                        "this ranking is not a further reading of the project's "
                                        "condition"}}


def critic_topsis(structure: dict) -> dict[str, Any]:
    """
    CRITIC objective weights, then TOPSIS over the same explicit problem.

    CRITIC (Diakoulaki et al.): the matrix is min-max normalised with orientation taken into
    account, sigma_j is the sample standard deviation of the normalised column, r_jk is the
    Pearson correlation between normalised columns, C_j = sigma_j * sum_k (1 - r_jk), and
    w_j = C_j / sum C.

    ZERO VARIANCE DOES NOT SILENTLY DIVIDE. A criterion on which every alternative scores the
    same has no dispersion and no defined correlation with anything, so it is REFUSED rather
    than given a correlation of zero, one, or a nudged denominator.

    TOPSIS: vector normalisation, CRITIC weights applied, positive and negative ideals selected
    by orientation, Euclidean distances, CC_i = D_i^- / (D_i^+ + D_i^-), ranked descending.
    """
    problem = decision_problem(structure, module_id="B2.19", require_weights=False)
    criteria = problem["criteria"]
    alts = problem["alternatives"]
    m = len(alts)
    if m < 3:
        raise StructureAbsent(
            "The decision problem provided for this project holds too few alternatives for the "
            "spread and agreement between criteria to mean anything, so no objective weights "
            "are derived and no ranking is carried out.")
    cols: dict[str, list[float]] = {}
    for c in criteria:
        cid = c["criterion_id"]
        raw = [a["values"][cid] for a in alts]
        lo, hi = min(raw), max(raw)
        if hi - lo <= 0:
            raise StructureAbsent(
                "Every alternative in the decision problem provided for this project scores the "
                "same on one of its criteria. That criterion tells the alternatives nothing "
                "apart, so no objective weight is derived from it and no ranking is carried "
                "out.")
        if c["orientation"] == "benefit":
            cols[cid] = [(v - lo) / (hi - lo) for v in raw]
        else:
            cols[cid] = [(hi - v) / (hi - lo) for v in raw]
    ids = [c["criterion_id"] for c in criteria]
    sigma = {}
    for cid in ids:
        mean = sum(cols[cid]) / m
        sigma[cid] = math.sqrt(sum((v - mean) ** 2 for v in cols[cid]) / (m - 1))
    corr: dict[str, dict[str, float]] = {}
    for j in ids:
        corr[j] = {}
        mj = sum(cols[j]) / m
        for k in ids:
            mk = sum(cols[k]) / m
            num = sum((cols[j][i] - mj) * (cols[k][i] - mk) for i in range(m))
            dj = math.sqrt(sum((cols[j][i] - mj) ** 2 for i in range(m)))
            dk = math.sqrt(sum((cols[k][i] - mk) ** 2 for i in range(m)))
            if dj <= 0 or dk <= 0:
                raise StructureAbsent(
                    "A criterion in the decision problem provided for this project does not vary "
                    "between the alternatives, so its agreement with the others is not defined "
                    "and no ranking is carried out.")
            corr[j][k] = num / (dj * dk)
    info = {j: sigma[j] * sum(1.0 - corr[j][k] for k in ids) for j in ids}
    total_info = sum(info.values())
    if total_info <= 0:
        raise StructureAbsent(
            "The decision problem provided for this project carries no information to weigh its "
            "criteria by, so no ranking is carried out.")
    weights = {j: info[j] / total_info for j in ids}
    norm: dict[str, list[float]] = {}
    for cid in ids:
        raw = [a["values"][cid] for a in alts]
        denom = math.sqrt(sum(v * v for v in raw))
        if denom <= 0:
            raise StructureAbsent(
                "A criterion in the decision problem provided for this project scores every "
                "alternative at nothing, so this ranking is not defined on it and none is "
                "carried out.")
        norm[cid] = [v / denom for v in raw]
    weighted = {cid: [weights[cid] * v for v in norm[cid]] for cid in ids}
    a_plus, a_minus = {}, {}
    for c in criteria:
        cid = c["criterion_id"]
        col = weighted[cid]
        if c["orientation"] == "benefit":
            a_plus[cid], a_minus[cid] = max(col), min(col)
        else:
            a_plus[cid], a_minus[cid] = min(col), max(col)
    rows = []
    for i, a in enumerate(alts):
        d_plus = math.sqrt(sum((weighted[cid][i] - a_plus[cid]) ** 2 for cid in ids))
        d_minus = math.sqrt(sum((weighted[cid][i] - a_minus[cid]) ** 2 for cid in ids))
        denom = d_plus + d_minus
        cc = 0.0 if denom == 0 else d_minus / denom
        rows.append({"alternative_id": a["alternative_id"], "d_plus": d_plus,
                     "d_minus": d_minus, "closeness": cc})
    order = sorted(rows, key=lambda r: (-r["closeness"], r["alternative_id"]))
    ranks: dict[str, int] = {}
    rank = 0
    prev = None
    for idx, r in enumerate(order):
        if prev is None or abs(r["closeness"] - prev) > 1e-12:
            rank = idx + 1
            prev = r["closeness"]
        ranks[r["alternative_id"]] = rank
    return {"estimable": True, "context_id": problem["context_id"],
            "critic_normalised": cols, "sigma": sigma, "correlation": corr,
            "information": info, "weights": weights,
            "topsis_normalised": norm, "weighted": weighted,
            "positive_ideal": a_plus, "negative_ideal": a_minus,
            "rows": rows, "ranking": [r["alternative_id"] for r in order], "ranks": ranks,
            "weights_are_algorithmic": True,
            "lineage": {"source": problem["source"], "period": problem["period"],
                        "derived_from": "the decision alternatives supplied for this project; "
                                        "this ranking is not a further reading of the project's "
                                        "condition"}}


# =================================================================================================
# 7.20 HYPERSOFT SETS -- DISABLED / FUTURE RESEARCH
# =================================================================================================

def hypersoft_lab(structure: dict) -> dict[str, Any]:
    """
    The laboratory structure only. NO OPERATIONAL RESULT IS PRODUCED BY THIS FUNCTION.

    A hypersoft set is defined on the CARTESIAN PRODUCT of disjoint attribute value subspaces,
    with an approximate mapping given for EVERY admissible tuple. A missing tuple makes the
    structure incomplete; the completeness check reports which tuples are missing and abstains.
    NOTHING IS SUPPLIED IN PLACE OF A MISSING TUPLE -- not zero, not neutral, not a default.
    """
    words = V5_STRUCTURE_WORDS["B2.20"]
    _provenance(structure, words, "research_origin", "source")
    attrs = _rows(structure, "attributes", words)
    names: list[str] = []
    spaces: list[list[str]] = []
    for a in attrs:
        name = str(a.get("attribute") or "").strip()
        values = a.get("values")
        if not name or not isinstance(values, list) or not values:
            raise StructureAbsent(
                f"The {words} provided is incomplete, so nothing is read from it.")
        vals = [str(v).strip() for v in values]
        if len(set(vals)) != len(vals):
            raise StructureAbsent(
                f"The {words} provided lists the same value twice for one attribute, so nothing "
                f"is read from it.")
        names.append(name)
        spaces.append(vals)
    if len(names) < 2:
        raise StructureAbsent(
            f"The {words} provided holds fewer than two attributes, so there is no product of "
            f"value sets to define a mapping over and nothing is read from it.")
    if len(set(names)) != len(names):
        raise StructureAbsent(
            f"The {words} provided names the same attribute twice, so nothing is read from it.")
    overlap = set()
    for i in range(len(spaces)):
        for j in range(i + 1, len(spaces)):
            overlap |= set(spaces[i]) & set(spaces[j])
    if overlap:
        raise StructureAbsent(
            f"The {words} provided shares values between attributes whose value sets must be "
            f"kept apart, so nothing is read from it.")
    product: list[tuple] = [()]
    for space in spaces:
        product = [row + (v,) for row in product for v in space]
    mapping = structure.get("mapping")
    if not isinstance(mapping, list):
        raise StructureAbsent(
            f"The {words} provided gives no mapping, so nothing is read from it.")
    given: dict[tuple, Any] = {}
    for entry in mapping:
        if not isinstance(entry, dict):
            raise StructureAbsent(
                f"The {words} provided gives its mapping in a form this measure cannot read.")
        tup = entry.get("tuple")
        if not isinstance(tup, list) or len(tup) != len(names):
            raise StructureAbsent(
                f"The {words} provided gives a mapping against something that is not a "
                f"combination of one value from each attribute, so nothing is read from it.")
        key = tuple(str(v).strip() for v in tup)
        if key not in product:
            raise StructureAbsent(
                f"The {words} provided gives a mapping against a combination its own attributes "
                f"cannot produce, so nothing is read from it.")
        if key in given:
            raise StructureAbsent(
                f"The {words} provided gives two mappings for the same combination, so nothing "
                f"is read from it.")
        if "approximation" not in entry:
            raise StructureAbsent(
                f"The {words} provided names a combination without saying what it maps to, so "
                f"nothing is read from it.")
        given[key] = entry["approximation"]
    missing = [list(t) for t in product if t not in given]
    return {
        "attributes": names,
        "value_spaces": spaces,
        "cartesian_size": len(product),
        "mapped": len(given),
        "missing_tuples": missing,
        "structure_complete": not missing,
        "estimable": False,
        "operational": False,
        "disposition": "DISABLED_FUTURE_RESEARCH",
        "reason": ("this structure is incomplete: some combinations of its attribute values "
                   "carry no mapping, and nothing is supplied in their place")
        if missing else
        ("this representation is held for research only and produces no operational reading"),
    }
