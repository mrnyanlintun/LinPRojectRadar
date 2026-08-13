"""
Run 19 independent oracles for Category 3, cost risk.

Written from the equations in supervisory specification section 12 and from nothing else. The
specification's own worked answers are asserted in self_test() before any function here judges
production. Nothing in server/app is imported and nothing here was written with a production
module open.
"""

from __future__ import annotations

import math


# ------------------------------------------------------------------ 3.1 Reference class

def quantile_of_reference_class(overruns: list[float], p: float) -> float:
    """
    Specification 3.1. U_p = Quantile_p({r_i}) over the realised proportional overruns of a
    governed population of comparable completed projects.

    The convention is frozen here before any result is observed: linear interpolation between
    order statistics, which reproduces the specification's median of .20 on its own five-point
    reference class.
    """
    s = sorted(overruns)
    if not s:
        raise ValueError("a reference class forecast has no reference class")
    k = p * (len(s) - 1)
    lo = int(math.floor(k))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (k - lo) * (s[hi] - s[lo])


def rcf_adjusted_forecast(inside_view: float, uplift: float) -> float:
    """Specification 3.1. AdjustedForecast = InsideViewForecast * (1 + U_p)."""
    return inside_view * (1.0 + uplift)


# ------------------------------------------------------------------ 3.2 Contingency burn

def contingency_consumed_fraction(original: float, remaining: float) -> float:
    """Specification 3.2. C = (Original - Remaining) / Original."""
    return (original - remaining) / original


def normalised_burn(consumed_fraction: float, progress_fraction: float) -> float:
    """Specification 3.2. NormalizedBurn = C / ProgressFraction, for progress above zero."""
    if progress_fraction <= 0:
        raise ValueError("no progress to normalise the burn against")
    return consumed_fraction / progress_fraction


# ------------------------------------------------------------------ 3.3 Labor productivity

def productivity(output: float, labor_hours: float) -> float:
    """Specification 3.3. Productivity is OUTPUT per labour input, not hours per hour."""
    return output / labor_hours


def productivity_index(earned_output: float, actual_hours: float,
                       planned_output: float, planned_hours: float) -> float:
    """Specification 3.3. ProductivityIndex = ActualProductivity / PlannedProductivity."""
    return productivity(earned_output, actual_hours) / productivity(planned_output, planned_hours)


# ------------------------------------------------------------------ 3.5 Overhead absorption

def absorption_rate(overhead: float, allocation_base: float) -> float:
    """Specification 3.5. An absorption RATE is overhead per unit of an explicit base."""
    return overhead / allocation_base


def absorption_rate_variance(planned_oh: float, planned_base: float,
                             actual_oh: float, actual_base: float) -> dict[str, float]:
    """
    Specification 3.5. The comparison is of two RATES on a comparable base, not of two amounts.

    The specification's worked case: plan 100 over a base of 1000 is a rate of .10; actual 120
    over the same base of 1000 is .12; the rate variance is .02 and the relative variance 20%.
    """
    pr = absorption_rate(planned_oh, planned_base)
    ar = absorption_rate(actual_oh, actual_base)
    return {"planned_rate": pr, "actual_rate": ar, "rate_variance": ar - pr,
            "relative_variance": (ar - pr) / pr}


# ------------------------------------------------------------------ 3.6 Cost risk P80

def empirical_quantile_right_continuous(sample: list[float], p: float) -> float:
    """
    The frozen empirical quantile convention for specification 3.6.

    Right continuous: the smallest observed value whose empirical cumulative share reaches p.
    On the specification's two-point distribution, 100 with probability .5 and 120 with
    probability .5, this gives P80 = 120, which is the answer the specification states.
    """
    s = sorted(sample)
    idx = math.ceil(p * len(s)) - 1
    return s[max(0, min(len(s) - 1, idx))]


def bernoulli_cost_model(base: float, prob: float, impact: float,
                         draws: int, seed: int) -> list[float]:
    """
    Specification 3.6. TotalCost = BaseCost + RealizedRiskEvents, one independent Bernoulli.

    A cost-risk model is a distribution, not a scalar uplift, so the oracle produces the sample
    and the quantile is read off it.
    """
    import random
    rng = random.Random(seed)
    return [base + (impact if rng.random() < prob else 0.0) for _ in range(draws)]


# ------------------------------------------------------------------ 3.7 Analogous estimating

def adapted_analog_estimate(analog_cost: float, factors: list[float]) -> float:
    """
    Specification 3.7. An analogous estimate is a selected analog cost carried through explicit
    normalisation and adaptation factors: 100 * 1.20 * 1.10 = 132.
    """
    out = analog_cost
    for f in factors:
        out *= f
    return out


# ------------------------------------------------------------------ 3.8 Parametric cost

def parametric_cost(intercept: float, coefficients: list[float], drivers: list[float]) -> float:
    """
    Specification 3.8. Cost = beta0 + beta1*x1 + ... + betap*xp, with measurable drivers and
    fitted coefficients. The specification's worked case is 10 + 2*4 + 3*5 = 33.
    """
    if len(coefficients) != len(drivers):
        raise ValueError("the design matrix and the coefficient vector do not conform")
    return intercept + sum(b * x for b, x in zip(coefficients, drivers))


# ------------------------------------------------------------------ 3.9 Inflation adjustment

def escalation_factor(index_current: float, index_base: float) -> float:
    """Specification 3.9. EscalationFactor = Index_current / Index_base."""
    return index_current / index_base


def adjusted_cost(base_cost: float, index_current: float, index_base: float) -> float:
    """Specification 3.9. AdjustedCost = BaseCost * EscalationFactor."""
    return base_cost * escalation_factor(index_current, index_base)


# ------------------------------------------------------------------ self proof

def self_test() -> list[str]:
    fails: list[str] = []

    def eq(label: str, got, want, tol=1e-9) -> None:
        if got is None or abs(float(got) - float(want)) > tol:
            fails.append(f"{label}: got {got!r}, specification says {want!r}")

    # 3.1 -- reference overruns 0, .10, .20, .30, .40 have a median uplift of .20.
    eq("3.1 median uplift of the reference class",
       quantile_of_reference_class([0.0, 0.10, 0.20, 0.30, 0.40], 0.50), 0.20)
    eq("3.1 adjusted forecast at the median uplift", rcf_adjusted_forecast(1000, 0.20), 1200)

    # 3.2 -- original 100, remaining 60, progress .50: consumed .40, normalised burn .80.
    c = contingency_consumed_fraction(100, 60)
    eq("3.2 consumed fraction", c, 0.40)
    eq("3.2 normalised burn", normalised_burn(c, 0.50), 0.80)

    # 3.3 -- planned 10 units per hour against actual 8 is an index of .80.
    eq("3.3 planned productivity", productivity(1000, 100), 10.0)
    eq("3.3 actual productivity", productivity(800, 100), 8.0)
    eq("3.3 productivity index", productivity_index(800, 100, 1000, 100), 0.80)

    # 3.5 -- the specification's overhead rates and variances.
    v = absorption_rate_variance(100, 1000, 120, 1000)
    eq("3.5 planned absorption rate", v["planned_rate"], 0.10)
    eq("3.5 actual absorption rate", v["actual_rate"], 0.12)
    eq("3.5 absorption rate variance", v["rate_variance"], 0.02)
    eq("3.5 relative rate variance", v["relative_variance"], 0.20)

    # 3.6 -- base 100 with a fifty per cent chance of a 20 impact: mean 110, P80 120.
    eq("3.6 P80 of the two-point distribution",
       empirical_quantile_right_continuous([100.0] * 500 + [120.0] * 500, 0.80), 120.0)
    sample = bernoulli_cost_model(100, 0.5, 20, 40000, 20260813)
    eq("3.6 simulated mean converges to the analytic 110",
       sum(sample) / len(sample), 110.0, 0.5)
    eq("3.6 simulated P80 is the upper atom",
       empirical_quantile_right_continuous(sample, 0.80), 120.0)

    # 3.7 -- analog 100 with size 1.20 and location 1.10 adapts to 132.
    eq("3.7 adapted analog estimate", adapted_analog_estimate(100, [1.20, 1.10]), 132.0)

    # 3.8 -- 10 + 2*4 + 3*5 = 33.
    eq("3.8 parametric prediction", parametric_cost(10, [2, 3], [4, 5]), 33.0)
    try:
        parametric_cost(10, [2, 3], [4])
        fails.append("3.8 a nonconforming design matrix must be refused, not predicted from")
    except ValueError:
        pass

    # 3.9 -- index 200 to 220 is a factor of 1.10; 100 becomes 110.
    eq("3.9 escalation factor", escalation_factor(220, 200), 1.10)
    eq("3.9 adjusted cost", adjusted_cost(100, 220, 200), 110.0)

    return fails


_FAILS = self_test()
assert not _FAILS, "Category 3 oracle does not reproduce the specification: " + "; ".join(_FAILS)
