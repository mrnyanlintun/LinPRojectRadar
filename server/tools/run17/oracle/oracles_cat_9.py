"""
Run 19 independent oracles for Category 9, data integrity and information quality.

Written from supervisory specification section 18 and from nothing else. Self proved against the
specification's worked answers at import. Imports nothing from server/app.
"""

from __future__ import annotations


# ------------------------------------------------------------------ 9.1 Missing data

def missing_fraction(required_applicable: list[str], values: dict) -> float:
    """
    Specification 9.1. MissingFraction = RequiredApplicableMissing / RequiredApplicableCount.

    Two rules the specification states explicitly and this oracle enforces: ZERO IS A VALUE, so a
    field holding zero is present and not missing; and a field that is NOT APPLICABLE is not part
    of the denominator at all, so it can neither be missing nor inflate completeness.
    """
    if not required_applicable:
        raise ValueError("no applicable required fields, so no missing fraction is defined")
    missing = sum(1 for f in required_applicable if values.get(f, None) is None)
    return missing / len(required_applicable)


def applicable_fields(all_required: list[str], not_applicable: set[str]) -> list[str]:
    """Specification 9.1. Not-applicable fields must not be counted missing."""
    return [f for f in all_required if f not in not_applicable]


# ------------------------------------------------------------------ 9.2 Timeliness

def record_age_days(period_cutoff_ordinal: int, effective_ordinal: int) -> int:
    """Specification 9.2. Age = period_cutoff - effective/source date."""
    return period_cutoff_ordinal - effective_ordinal


def timeliness_state(age_days: int, allowed_age_days: int) -> str:
    """
    Specification 9.2, with the three states it requires.

    A record dated AFTER the period cutoff has a negative age. The specification requires that
    future-dated records receive explicit invalid or review handling, so this oracle returns
    INVALID_FUTURE_DATED rather than letting a negative age fall through as maximally fresh.
    The freshness requirement is a parameter of the SOURCE CLASS, not one universal age.
    """
    if age_days < 0:
        return "INVALID_FUTURE_DATED"
    return "TIMELY" if age_days <= allowed_age_days else "STALE"


# ------------------------------------------------------------------ 9.3 Source reliability

def reliability(components: dict[str, float], weights: dict[str, float]) -> float:
    """
    Specification 9.3. A weighted model over declared evidence characteristics.

    Every component weight must be versioned and provenanced; this oracle only establishes the
    algebra and the monotonicity property, never the provenance.
    """
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError("the reliability weights do not sum to one")
    return sum(components[k] * weights[k] for k in weights)


# ------------------------------------------------------------------ 9.4 Audit trail

def audit_completeness(record: dict, critical: list[str], optional: list[str]) -> dict:
    """
    Specification 9.4. Critical fields are NONCOMPENSATORY.

    A missing method version, evidence identity, judgment identity or required timestamp may not
    be averaged away by any number of present optional fields, so this returns the critical
    verdict separately from the optional coverage and never combines them into one number.
    """
    missing_critical = [f for f in critical if record.get(f) in (None, "")]
    present_optional = sum(1 for f in optional if record.get(f) not in (None, ""))
    return {
        "critical_satisfied": not missing_critical,
        "missing_critical": missing_critical,
        "optional_coverage": present_optional / len(optional) if optional else 1.0,
    }


def chronology_intact(events: list[tuple[str, int]]) -> bool:
    """Specification 9.4. A required event sequence must not run backwards in time."""
    times = [t for _, t in events]
    return all(times[i] <= times[i + 1] for i in range(len(times) - 1))


# ------------------------------------------------------------------ 9.5 Package coverage

def package_coverage(components_applicable: int, components_present: int) -> float:
    """
    Specification 9.5. How much of the applicable overall evidence package is present.

    The specification's worked case: six of eight applicable evidence components present is a
    coverage of .75. This is a question about COMPONENTS OF AN EVIDENCE PACKAGE, deliberately
    distinct from 9.1's question about mandatory FIELDS.
    """
    if components_applicable <= 0:
        raise ValueError("no applicable evidence components, so no coverage is defined")
    return components_present / components_applicable


# ------------------------------------------------------------------ 9.6 Cross-document

def cross_source_agreement(value_a: float, value_b: float, tolerance_fraction: float) -> str:
    """
    Specification 9.6. Compare the SAME governed fact across REAL SOURCE RECORDS.

    The specification's cases: 100.0 from source A and 100.0 from source B agree; 100 against 110
    with an allowed tolerance of two per cent is a material conflict. A conflict is reported as a
    conflict and never averaged away.
    """
    if value_a == 0:
        raise ValueError("no basis to express a relative tolerance against")
    if abs(value_b - value_a) / abs(value_a) <= tolerance_fraction:
        return "CONSISTENT"
    return "MATERIAL_CONFLICT"


def never_average(values: list[float]) -> None:
    """Specification 9.6 forbids resolving a conflict by averaging the conflicting sources."""
    raise AssertionError("conflicting sources must not be averaged into agreement")


# ------------------------------------------------------------------ 9.7 Cadence

def cadence_report(event_days: list[int], expected_interval: int,
                   period_cutoff_day: int) -> dict:
    """
    Specification 9.7. Compare ACTUAL reporting intervals to a GOVERNED expected schedule.

    Two things the specification separates and this oracle keeps separate: cadence is not
    freshness, and CESSATION must be detectable. So the gap from the last report to the period
    cutoff is measured alongside the observed intervals: a project that reported four times
    weekly and then stopped for a year has an excellent mean interval and has ceased reporting.
    """
    if len(event_days) < 2:
        raise ValueError("one report establishes no interval")
    days = sorted(event_days)
    intervals = [days[i] - days[i - 1] for i in range(1, len(days))]
    expected_count = max(0, (period_cutoff_day - days[0]) // expected_interval)
    return {
        "mean_interval": sum(intervals) / len(intervals),
        "intervals": intervals,
        "missed": max(0, expected_count - (len(days) - 1)),
        "gap_since_last_report": period_cutoff_day - days[-1],
        "ceased": (period_cutoff_day - days[-1]) > 2 * expected_interval,
        "duplicates": len(days) - len(set(days)),
    }


# ------------------------------------------------------------------ self proof

def self_test() -> list[str]:
    fails: list[str] = []

    def eq(label: str, got, want, tol=1e-9) -> None:
        if got is None or abs(float(got) - float(want)) > tol:
            fails.append(f"{label}: got {got!r}, specification says {want!r}")

    # 9.1 -- ten applicable required fields with two missing is an index of .20.
    ten = [f"f{i}" for i in range(10)]
    vals = {f: 1 for f in ten}
    del vals["f0"], vals["f1"]
    eq("9.1 missing fraction", missing_fraction(ten, vals), 0.20)
    # Zero is a value.
    eq("9.1 a field holding zero is present, not missing",
       missing_fraction(ten, {f: 0 for f in ten}), 0.0)
    # A not-applicable field is out of the denominator entirely.
    app = applicable_fields(ten, {"f0", "f1"})
    if len(app) != 8:
        fails.append("9.1 not-applicable fields must leave the denominator")
    eq("9.1 the two not-applicable fields are not counted missing",
       missing_fraction(app, {f: 1 for f in app}), 0.0)

    # 9.2 -- allowed age 30: an age of 20 is timely, 40 is stale, a future date is invalid.
    if timeliness_state(20, 30) != "TIMELY":
        fails.append("9.2 an age of 20 against an allowance of 30 is timely")
    if timeliness_state(40, 30) != "STALE":
        fails.append("9.2 an age of 40 against an allowance of 30 is stale")
    if timeliness_state(-5, 30) != "INVALID_FUTURE_DATED":
        fails.append("9.2 a future-dated record requires explicit invalid handling")
    eq("9.2 age is the cutoff less the effective date", record_age_days(100, 80), 20)

    # 9.3 -- algebra and the monotonicity the specification requires.
    w = {"authority": 0.5, "verification": 0.3, "freshness": 0.2}
    base = reliability({"authority": 0.8, "verification": 0.5, "freshness": 0.9}, w)
    better = reliability({"authority": 0.8, "verification": 0.9, "freshness": 0.9}, w)
    eq("9.3 weighted reliability", base, 0.8 * 0.5 + 0.5 * 0.3 + 0.9 * 0.2)
    if not better > base:
        fails.append("9.3 improving verification with all else held constant must not lower "
                     "reliability")
    try:
        reliability({"a": 1.0}, {"a": 0.5})
        fails.append("9.3 weights that do not sum to one must be refused")
    except ValueError:
        pass

    # 9.4 -- critical fields are noncompensatory.
    crit = ["method_version", "evidence_id", "judgment_id", "timestamp"]
    opt = [f"o{i}" for i in range(20)]
    full = {**{c: "x" for c in crit}, **{o: "x" for o in opt}}
    a = audit_completeness(full, crit, opt)
    if not a["critical_satisfied"]:
        fails.append("9.4 a complete record satisfies its critical fields")
    missing_one = dict(full)
    missing_one["method_version"] = None
    b = audit_completeness(missing_one, crit, opt)
    if b["critical_satisfied"] or b["optional_coverage"] != 1.0:
        fails.append("9.4 twenty present optional fields must not repair one missing critical "
                     "field, and the two verdicts must stay separate")
    if not chronology_intact([("created", 1), ("extracted", 2)]):
        fails.append("9.4 an ordered event sequence is intact")
    if chronology_intact([("created", 5), ("extracted", 2)]):
        fails.append("9.4 an event sequence running backwards must be detected")

    # 9.5 -- six of eight applicable components is a coverage of .75.
    eq("9.5 package coverage", package_coverage(8, 6), 0.75)

    # 9.6 -- the specification's two cases.
    if cross_source_agreement(100.0, 100.0, 0.02) != "CONSISTENT":
        fails.append("9.6 two sources reporting 100.0 agree")
    if cross_source_agreement(100.0, 110.0, 0.02) != "MATERIAL_CONFLICT":
        fails.append("9.6 100 against 110 within a two per cent tolerance is a material conflict")

    # 9.7 -- cadence, and cessation, which mean-interval alone cannot see.
    perfect = cadence_report([0, 30, 60, 90], 30, 90)
    eq("9.7 a perfect monthly cadence has a mean interval of thirty",
       perfect["mean_interval"], 30)
    if perfect["missed"] or perfect["ceased"]:
        fails.append("9.7 a perfect cadence has missed nothing and has not ceased")
    stopped = cadence_report([0, 10], 30, 400)
    eq("9.7 a project that stopped still shows a short mean interval",
       stopped["mean_interval"], 10)
    if not stopped["ceased"]:
        fails.append("9.7 a project whose last report is far behind the cutoff has ceased "
                     "reporting, and the mean interval cannot show it")
    if cadence_report([0, 30, 30, 60], 30, 60)["duplicates"] != 1:
        fails.append("9.7 a duplicate report must be detected")

    return fails


_FAILS = self_test()
assert not _FAILS, "Category 9 oracle does not reproduce the specification: " + "; ".join(_FAILS)
