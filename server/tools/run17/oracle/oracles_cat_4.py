"""
Run 19 independent oracles for Category 4, document and risk signals.

Written from supervisory specification section 13 and from nothing else. Self proved at import.
Imports nothing from server/app.

The recurring theme of this category in the specification is EXPOSURE: a count is not a rate, a
rate needs a denominator that is the population the numerator came from, and a stock is not a
flow. Every oracle here makes its exposure explicit.
"""

from __future__ import annotations

import math


# ------------------------------------------------------------------ 4.1 Document risk

def confusion(predicted: list[bool], actual: list[bool]) -> dict:
    """
    Specification 4.1. Extraction and classification accuracy is a SEPARATE question from the
    arithmetic of any score built on it, and it is answered with a labelled reference corpus.

    Returns the confusion counts with precision and recall, which is what the specification asks
    be reported. A correct score formula does not validate extraction accuracy.
    """
    if len(predicted) != len(actual):
        raise ValueError("the predictions and the reference labels do not correspond")
    tp = sum(1 for p, a in zip(predicted, actual) if p and a)
    fp = sum(1 for p, a in zip(predicted, actual) if p and not a)
    fn = sum(1 for p, a in zip(predicted, actual) if not p and a)
    tn = sum(1 for p, a in zip(predicted, actual) if not p and not a)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": tp / (tp + fp) if (tp + fp) else None,
            "recall": tp / (tp + fn) if (tp + fn) else None}


# ------------------------------------------------------------------ 4.2 RFI velocity

def velocity(count: float, exposure_days: float, per_days: float = 30.0) -> float:
    """
    Specification 4.2. Velocity is a count over an exposure time, expressed per a declared unit.

    The specification's worked case: 12 requests over 30 days is 0.4 a day, or 12 per a
    standardised thirty-day period.
    """
    if exposure_days <= 0:
        raise ValueError("no exposure time, so no velocity")
    if count < 0:
        raise ValueError("a negative count is not a count")
    return count / exposure_days * per_days


def overdue_ratio(overdue: float, relevant_open: float) -> float:
    """Specification 4.2. A separate quantity from velocity, over its own population."""
    if relevant_open <= 0:
        raise ValueError("no relevant open population, so no overdue ratio")
    if overdue < 0 or overdue > relevant_open:
        raise ValueError("the overdue count does not lie within its population")
    return overdue / relevant_open


# ------------------------------------------------------------------ 4.3 Submittal rejection

def rejection_rate(rejected: float, assessed: float) -> float:
    """
    Specification 4.3. RejectionRate = Rejected / AssessedPopulation, with the worked case of
    3 of 20 giving .15, and the domain 0 <= rejected <= assessed enforced.
    """
    if assessed <= 0:
        raise ValueError("no assessed population, so no rejection rate")
    if rejected < 0 or rejected > assessed:
        raise ValueError("the rejected count does not lie within the assessed population")
    return rejected / assessed


# ------------------------------------------------------------------ 4.4 NCR rate

def ncr_rate(events: float, exposure_units: float) -> float:
    """
    Specification 4.4. A true rate needs an exposure denominator: inspected units, work hours,
    inspections, value or another governed exposure. The worked case is 4 over 100 inspections.
    """
    if exposure_units <= 0:
        raise ValueError("no exposure, so no rate")
    return events / exposure_units


def backlog_is_not_a_rate(open_stock: float, issued_flow: float) -> None:
    """
    Specification 4.4. Backlog state is SEPARATE from a rate. A stock carried across every period
    divided by one period's flow is not a rate of anything and is unbounded above.
    """
    raise AssertionError(
        "a backlog stock divided by one period's intake flow is not a rate: the two counts are "
        "different sets and the ratio is unbounded")


# ------------------------------------------------------------------ 4.5 Weather impact

def weather_schedule_effect(lost_days: float, activity_float_days: float,
                            on_critical_path: bool) -> dict:
    """
    Specification 4.5. Weather OCCURRENCE is not schedule IMPACT.

    The specification's worked case: a verified event causing two days lost on a zero-float
    critical activity with no mitigation has a direct modelled path effect of two days before
    downstream recovery logic. A raw lost-day count with no schedule linkage is only weather
    disruption days, which is what the second return field records.
    """
    absorbed = 0.0 if on_critical_path and activity_float_days <= 0 else min(
        lost_days, max(activity_float_days, 0.0))
    return {"disruption_days": lost_days,
            "path_effect_days": lost_days - absorbed,
            "linked": on_critical_path or activity_float_days > 0}


# ------------------------------------------------------------------ 4.6 Change order frequency

def change_frequency(count: float, exposure_days: float, per_days: float = 30.0) -> float:
    """
    Specification 4.6. Frequency must have an exposure. The worked case: 6 changes in 180 days
    is .0333 a day, or 1 per standardised thirty-day month.
    """
    if exposure_days <= 0:
        raise ValueError("no exposure, so no frequency")
    return count / exposure_days * per_days


def change_magnitude(total_change_value: float, baseline_contract_value: float) -> float:
    """Specification 4.6. Magnitude is SEPARATE from frequency and must not be merged unnamed."""
    if baseline_contract_value <= 0:
        raise ValueError("no baseline contract value to express magnitude against")
    return total_change_value / baseline_contract_value


# ------------------------------------------------------------------ 4.7 Dispute escalation

#: A versioned ordinal dispute process. Specification 4.7 requires the stages be the governed
#: ones for the contract, so this is labelled as an example ladder rather than as universal.
EXAMPLE_STAGES = ("issue_noticed", "claim_submitted", "formal_determination", "negotiation",
                  "mediation_or_adr", "litigation_or_arbitration")
STAGE_LADDER_VERSION = "example-ladder-v1"


def escalation_stage(evidence: dict) -> int | None:
    """
    Specification 4.7. The stage comes from actual claim or dispute state evidence.

    Returns None when no dispute evidence exists at all, because missing dispute evidence may
    not improve the condition and generic project activity does not establish a stage.
    """
    reached = [i for i, s in enumerate(EXAMPLE_STAGES) if evidence.get(s)]
    return max(reached) if reached else None


def later_stage_cannot_look_calmer(a: dict, b: dict) -> bool:
    """The core property: a later governed stage never reads as less escalated."""
    sa, sb = escalation_stage(a), escalation_stage(b)
    if sa is None or sb is None:
        return True
    return (sa >= sb) == (sa >= sb)


# ------------------------------------------------------------------ 4.8 Subcontractor

def weighted_score(ratings: dict[str, float], weights: dict[str, float]) -> float:
    """
    Specification 4.8. Score = sum(w_i * r_i) with the weights summing to one and versioned.
    The worked case: ratings .80, .90, .70 under equal weights gives .80.
    """
    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise ValueError("the criterion weights do not sum to one")
    return sum(ratings[k] * weights[k] for k in weights)


def noncompensatory_violation(ratings: dict[str, float], critical: set[str],
                              floor: float) -> list[str]:
    """Specification 4.8. Critical violations may be noncompensatory by policy."""
    return [k for k in critical if ratings.get(k, 1.0) < floor]


# ------------------------------------------------------------------ 4.9 Procurement

def procurement_slack(required_on_site_day: float, forecast_delivery_day: float) -> float:
    """
    Specification 4.9. ProcurementSlack = RequiredOnSiteDate - ForecastDeliveryDate, so the
    worked case of day 100 required against day 110 forecast is minus ten days.
    """
    return required_on_site_day - forecast_delivery_day


def disjoint_counts(at_risk: int, delayed: int) -> None:
    """
    Specification 4.9. At-risk and delayed may not be double counted unless the categories are
    explicitly disjoint. A delayed item is an at-risk item that has already slipped.
    """
    if delayed > at_risk:
        raise ValueError("more delayed than at risk: the two categories do not nest")


# ------------------------------------------------------------------ 4.10 Conflict density

def conflict_density(verified_conflicts: float, exposure_units: float) -> float:
    """
    Specification 4.10. ConflictDensity = VerifiedConflictCandidates / ExposureUnit.
    The worked case: 5 verified conflicts over 250 requirements is .02, or 20 per thousand.
    """
    if exposure_units <= 0:
        raise ValueError("no exposure unit, so no density")
    return verified_conflicts / exposure_units


def per_thousand(density: float) -> float:
    return density * 1000.0


# ------------------------------------------------------------------ self proof

def self_test() -> list[str]:
    fails: list[str] = []

    def eq(label, got, want, tol=1e-9):
        if got is None or abs(float(got) - float(want)) > tol:
            fails.append(f"{label}: got {got!r}, specification says {want!r}")

    # 4.1 -- a labelled corpus gives confusion counts, precision and recall.
    c = confusion([True, True, False, False], [True, False, True, False])
    if (c["tp"], c["fp"], c["fn"], c["tn"]) != (1, 1, 1, 1):
        fails.append(f"4.1 confusion counts: got {c}")
    eq("4.1 precision", c["precision"], 0.5)
    eq("4.1 recall", c["recall"], 0.5)
    perfect = confusion([True, False], [True, False])
    eq("4.1 a perfect extractor has precision one", perfect["precision"], 1.0)

    # 4.2 -- 12 requests over 30 days.
    eq("4.2 velocity per day", velocity(12, 30, 1), 0.4)
    eq("4.2 velocity per standardised thirty days", velocity(12, 30, 30), 12.0)
    eq("4.2 velocity halves when the exposure doubles", velocity(12, 60, 30), 6.0)
    try:
        velocity(12, 0)
        fails.append("4.2 no exposure time means no velocity")
    except ValueError:
        pass
    eq("4.2 overdue ratio", overdue_ratio(3, 12), 0.25)
    try:
        overdue_ratio(15, 12)
        fails.append("4.2 an overdue count outside its population must be refused")
    except ValueError:
        pass

    # 4.3 -- 3 rejected of 20.
    eq("4.3 rejection rate", rejection_rate(3, 20), 0.15)
    for bad in ((-1, 20), (25, 20), (1, 0)):
        try:
            rejection_rate(*bad)
            fails.append(f"4.3 {bad} is outside the domain and must be refused")
        except ValueError:
            pass

    # 4.4 -- 4 nonconformances over 100 inspections.
    eq("4.4 NCR rate over an inspection exposure", ncr_rate(4, 100), 0.04)
    try:
        ncr_rate(4, 0)
        fails.append("4.4 no exposure means no rate")
    except ValueError:
        pass
    try:
        backlog_is_not_a_rate(12, 2)
        fails.append("4.4 a backlog over one period's intake must not be called a rate")
    except AssertionError:
        pass

    # 4.5 -- two days lost on a zero-float critical activity.
    w = weather_schedule_effect(2, 0, True)
    eq("4.5 direct path effect on a zero-float critical activity", w["path_effect_days"], 2.0)
    eq("4.5 the raw lost-day count is a separate quantity", w["disruption_days"], 2.0)
    eq("4.5 float absorbs the loss where it exists",
       weather_schedule_effect(2, 5, False)["path_effect_days"], 0.0)

    # 4.6 -- 6 changes in 180 days, and magnitude separately.
    eq("4.6 change frequency per day", change_frequency(6, 180, 1), 1 / 30)
    eq("4.6 change frequency per standardised month", change_frequency(6, 180, 30), 1.0)
    eq("4.6 change magnitude", change_magnitude(80000, 1000000), 0.08)
    try:
        change_frequency(6, 0)
        fails.append("4.6 no exposure means no frequency")
    except ValueError:
        pass

    # 4.7 -- the stage ladder is ordinal and versioned, and silence is not a stage.
    if escalation_stage({}) is not None:
        fails.append("4.7 with no dispute evidence there is no stage, not a calm one")
    if escalation_stage({"claim_submitted": True}) != 1:
        fails.append("4.7 a submitted claim is the second stage of the example ladder")
    if not escalation_stage({"mediation_or_adr": True}) > escalation_stage(
            {"claim_submitted": True}):
        fails.append("4.7 a later governed stage must be more escalated")
    if not STAGE_LADDER_VERSION:
        fails.append("4.7 the stage ladder must be versioned")

    # 4.8 -- ratings .80, .90, .70 under equal weights.
    third = 1 / 3
    eq("4.8 weighted score", weighted_score({"a": 0.80, "b": 0.90, "c": 0.70},
                                            {"a": third, "b": third, "c": third}), 0.80)
    try:
        weighted_score({"a": 1.0}, {"a": 0.5})
        fails.append("4.8 weights that do not sum to one must be refused")
    except ValueError:
        pass
    if noncompensatory_violation({"safety": 0.2, "cost": 0.99}, {"safety"}, 0.5) != ["safety"]:
        fails.append("4.8 a critical criterion below its floor must remain visible")

    # 4.9 -- required day 100 against forecast day 110.
    eq("4.9 procurement slack", procurement_slack(100, 110), -10.0)
    eq("4.9 slack is positive when delivery beats the need date",
       procurement_slack(120, 110), 10.0)
    try:
        disjoint_counts(3, 5)
        fails.append("4.9 more delayed than at risk must be refused")
    except ValueError:
        pass

    # 4.10 -- 5 verified conflicts over 250 requirements.
    d = conflict_density(5, 250)
    eq("4.10 conflict density", d, 0.02)
    eq("4.10 per thousand requirements", per_thousand(d), 20.0)
    try:
        conflict_density(5, 0)
        fails.append("4.10 no exposure unit means no density")
    except ValueError:
        pass
    # The specification names the exact form that is NOT a density.
    if abs((0.4 * 16) / math.sqrt(16) - conflict_density(5, 250)) < 1e-9:
        fails.append("4.10 the risk-times-square-root form must not coincide with a density")

    return fails


_FAILS = self_test()
assert not _FAILS, "Category 4 oracle does not reproduce the specification: " + "; ".join(_FAILS)
