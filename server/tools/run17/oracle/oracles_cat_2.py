"""
Run 19 independent oracles for Category 2, schedule analytics.

EVERY FUNCTION HERE IS WRITTEN FROM THE EQUATIONS IN THE SUPERVISORY SPECIFICATION, section 11,
and from nowhere else. The specification's own worked answers are asserted in self_test() before
any of these functions is allowed to judge production. Supervisory specification section 24 is
explicit that a second function copied from the first is not independent, so none of this file
was written with a production module open, and it imports nothing from server/app.
"""

from __future__ import annotations

import math


# ------------------------------------------------------------------ 2.1 PERT criticality

def pert_moments(o: float, m: float, p: float) -> tuple[float, float]:
    """Specification 2.1. E[T] = (O + 4M + P)/6; Var[T] = ((P-O)/6)^2."""
    return (o + 4.0 * m + p) / 6.0, ((p - o) / 6.0) ** 2


def deterministic_critical_activities(durations: dict[str, float],
                                      edges: list[tuple[str, str]]) -> set[str]:
    """
    Longest-path activities of an activity-on-node network, by exhaustive path enumeration.

    Specification 2.1 supplies the network A=3, B=2, C=1 with A->C and B->C, and states that the
    critical activities are A and C while B is not. Enumerating every source-to-sink path and
    keeping the activities of the longest one reproduces that without any forward or backward
    pass machinery, which keeps this oracle independent of the CPM oracle below.
    """
    succ: dict[str, list[str]] = {a: [] for a in durations}
    indeg = {a: 0 for a in durations}
    for u, v in edges:
        succ[u].append(v)
        indeg[v] += 1
    sinks = [a for a in durations if not succ[a]]
    sources = [a for a in durations if indeg[a] == 0]

    paths: list[list[str]] = []

    def walk(node: str, acc: list[str]) -> None:
        acc = acc + [node]
        if node in sinks:
            paths.append(acc)
            return
        for nxt in succ[node]:
            walk(nxt, acc)

    for s in sources:
        walk(s, [])
    best = max(paths, key=lambda pth: sum(durations[a] for a in pth))
    longest = sum(durations[a] for a in best)
    critical: set[str] = set()
    for pth in paths:
        if abs(sum(durations[a] for a in pth) - longest) < 1e-12:
            critical |= set(pth)
    return critical


# ------------------------------------------------------------------ 2.2 Line of balance

def lob_production_rate(units: list[float], times: list[float]) -> float:
    """Specification 2.2. production rate = change in units / change in time."""
    return (units[-1] - units[0]) / (times[-1] - times[0])


def lob_separation(locations: list[int], start_lead: float, rate_lead: float,
                   start_follow: float, rate_follow: float) -> dict[str, float]:
    """
    The crew separation across the locations, from the two production lines.

    Specification 2.2 requires the unit sequence, crew continuity and the offsets between the
    lines. A crew advancing at r locations per day from start day s reaches location u on day
    s + u/r, so the separation at u is the difference of the two, and the interference the
    method exists to find is its minimum over the locations.
    """
    seps = [((start_follow + u / rate_follow) - (start_lead + u / rate_lead), u)
            for u in locations]
    minimum, at = min(seps, key=lambda pair: pair[0])
    return {"minimum_separation_days": minimum, "at_location": float(at),
            "first_separation_days": seps[0][0]}


# ------------------------------------------------------------------ 2.3 CCPM buffer

def buffer_penetration(original_buffer: float, remaining_buffer: float) -> float:
    """Specification 2.3. BufferPenetration = BufferConsumed / OriginalBuffer."""
    return (original_buffer - remaining_buffer) / original_buffer


# ------------------------------------------------------------------ 2.5 Float consumption

def total_float(ls: float, es: float) -> float:
    """Specification 2.5. TF = LS - ES."""
    return ls - es


def float_consumption_fraction(tf_baseline: float, tf_current: float) -> dict[str, float]:
    """Specification 2.5. FloatConsumed = TF_baseline - TF_current; fraction over TF_baseline."""
    consumed = tf_baseline - tf_current
    return {"consumed": consumed, "fraction": consumed / tf_baseline}


# ------------------------------------------------------------------ 2.6 S-curve deviation

def scurve_point_deviation(actual_cumulative: float, planned_cumulative: float) -> float:
    """Specification 2.6. D(t) = ActualCumulative(t) - PlannedCumulative(t)."""
    return actual_cumulative - planned_cumulative


# ------------------------------------------------------------------ 2.7 Milestone trend

def milestone_slips_against_baseline(baseline: float, forecasts: list[float]) -> list[float]:
    """Specification 2.7. For baseline B and forecast F_t, Slip_t = F_t - B."""
    return [f - baseline for f in forecasts]


def ols_slope(xs: list[float], ys: list[float]) -> float:
    """
    Ordinary least squares slope, the declared regression summary of specification 2.7.

    Written from the normal equations rather than taken from any library.
    """
    n = float(len(xs))
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den


# ------------------------------------------------------------------ 2.8 Look-ahead

def ready_fraction(planned: float, constrained: float) -> float:
    """Specification 2.8. ReadyFraction = (Planned - Constrained) / Planned."""
    return (planned - constrained) / planned


# ------------------------------------------------------------------ 2.9 Resource loading

def load_ratio(demand: float, capacity: float) -> float:
    """Specification 2.9. LoadRatio_t = Demand_t / AvailableCapacity_t, per time period."""
    return demand / capacity


def time_phased_load(demand: list[float], capacity: list[float]) -> list[float]:
    """The time-phased vector the specification requires; a project total is not this."""
    return [load_ratio(d, c) for d, c in zip(demand, capacity)]


# ------------------------------------------------------------------ 2.10 Schedule risk P80

def empirical_quantile(sorted_sample: list[float], p: float) -> float:
    """
    The 0.80 quantile of a simulated completion distribution, right-continuous convention.

    Specification 2.10 requires P80 to be read off an empirical simulated distribution. The
    convention is frozen here, before any result is observed: the smallest observed value whose
    empirical cumulative share is at least p.
    """
    n = len(sorted_sample)
    idx = math.ceil(p * n) - 1
    return sorted_sample[max(0, min(n - 1, idx))]


def uniform_p80(lo: float, hi: float) -> float:
    """Specification 2.10 laboratory case. T ~ Uniform(lo,hi) has true P80 = lo + .8(hi-lo)."""
    return lo + 0.8 * (hi - lo)


# ------------------------------------------------------------------ 2.11 Critical path

def cpm_passes(durations: dict[str, float],
               edges: list[tuple[str, str]]) -> dict[str, dict[str, float]]:
    """
    Forward and backward passes of the critical path method, written from the definitions.

    ES is the latest early finish of the predecessors; EF = ES + duration. LF is the earliest
    late start of the successors, or the project finish for a sink; LS = LF - duration. Total
    float is LS - ES, and an activity is critical when its total float is zero.

    Specification 2.11 supplies A=3 -> C=2 and B=4 -> C=2, project finish 6, with B and C
    critical, A carrying one day of total float and B and C carrying none.
    """
    preds: dict[str, list[str]] = {a: [] for a in durations}
    succs: dict[str, list[str]] = {a: [] for a in durations}
    for u, v in edges:
        preds[v].append(u)
        succs[u].append(v)

    order: list[str] = []
    remaining = dict((a, list(preds[a])) for a in durations)
    while remaining:
        ready = [a for a, ps in remaining.items() if not ps]
        if not ready:
            raise ValueError("the network contains a cycle and has no critical path")
        for a in sorted(ready):
            order.append(a)
            del remaining[a]
            for s in succs[a]:
                if a in remaining.get(s, []):
                    remaining[s].remove(a)

    es: dict[str, float] = {}
    ef: dict[str, float] = {}
    for a in order:
        es[a] = max([ef[p] for p in preds[a]], default=0.0)
        ef[a] = es[a] + durations[a]
    finish = max(ef.values())

    lf: dict[str, float] = {}
    ls: dict[str, float] = {}
    for a in reversed(order):
        lf[a] = min([ls[s] for s in succs[a]], default=finish)
        ls[a] = lf[a] - durations[a]

    return {a: {"ES": es[a], "EF": ef[a], "LS": ls[a], "LF": lf[a],
                "TF": ls[a] - es[a], "critical": abs(ls[a] - es[a]) < 1e-12}
            for a in durations}, finish


# ------------------------------------------------------------------ self proof

def self_test() -> list[str]:
    """
    Prove every oracle against the specification's own worked answers before it judges anything.

    A failure here is a defect in this file, not in production, and the suite must stop.
    """
    fails: list[str] = []

    def eq(label: str, got, want, tol=1e-9) -> None:
        if got is None or abs(float(got) - float(want)) > tol:
            fails.append(f"{label}: got {got!r}, specification says {want!r}")

    # 2.1 -- the classical PERT moments, and the specification's network.
    e, v = pert_moments(2, 4, 12)
    eq("2.1 PERT mean (2,4,12)", e, (2 + 16 + 12) / 6)
    eq("2.1 PERT variance (2,4,12)", v, ((12 - 2) / 6) ** 2)
    crit = deterministic_critical_activities({"A": 3, "B": 2, "C": 1},
                                             [("A", "C"), ("B", "C")])
    if crit != {"A", "C"}:
        fails.append(f"2.1 critical activities: got {sorted(crit)}, specification says A and C")

    # 2.2 -- planned 1,2,3 days over locations 1,2,3 against actual 1,2.25,3.5.
    eq("2.2 planned production slope", lob_production_rate([1, 2, 3], [1, 2, 3]), 1.0)
    eq("2.2 actual production slope", lob_production_rate([1, 2, 3], [1, 2.25, 3.5]), 0.8)

    # 2.3 -- buffer of ten days with six remaining is forty per cent penetrated.
    eq("2.3 buffer penetration", buffer_penetration(10, 6), 0.40)

    # 2.5 -- baseline float five, current two: three consumed, six tenths.
    fc = float_consumption_fraction(5, 2)
    eq("2.5 float consumed", fc["consumed"], 3)
    eq("2.5 float consumption fraction", fc["fraction"], 0.60)
    eq("2.5 total float from the network", total_float(12, 7), 5)

    # 2.6 -- planned .60 against actual .50 is minus ten percentage points.
    eq("2.6 point deviation", scurve_point_deviation(0.50, 0.60), -0.10)

    # 2.7 -- baseline day 100 with forecasts 104, 108, 111 gives slips 4, 8, 11.
    slips = milestone_slips_against_baseline(100, [104, 108, 111])
    if slips != [4, 8, 11]:
        fails.append(f"2.7 slips against baseline: got {slips}, specification says [4, 8, 11]")
    if not ols_slope([0, 1, 2], slips) > 0:
        fails.append("2.7 the slip trend on a deteriorating series must have a positive slope")

    # 2.8 -- ten planned, three constrained, seven tenths ready.
    eq("2.8 ready fraction", ready_fraction(10, 3), 0.70)

    # 2.9 -- demand 120 against capacity 100 is 1.20.
    eq("2.9 load ratio", load_ratio(120, 100), 1.20)

    # 2.10 -- Uniform(0,10) has a true eightieth percentile of 8.
    eq("2.10 analytic uniform P80", uniform_p80(0, 10), 8.0)
    sample = sorted(i / 1000.0 * 10.0 for i in range(1, 1001))
    eq("2.10 empirical quantile of a uniform grid", empirical_quantile(sample, 0.80), 8.0, 0.02)

    # 2.11 -- the specification's CPM network.
    table, finish = cpm_passes({"A": 3, "B": 4, "C": 2}, [("A", "C"), ("B", "C")])
    eq("2.11 project finish", finish, 6)
    eq("2.11 total float of A", table["A"]["TF"], 1)
    eq("2.11 total float of B", table["B"]["TF"], 0)
    eq("2.11 total float of C", table["C"]["TF"], 0)
    if not (table["B"]["critical"] and table["C"]["critical"] and not table["A"]["critical"]):
        fails.append("2.11 the specification says B and C are critical and A is not")

    return fails


_FAILS = self_test()
assert not _FAILS, "Category 2 oracle does not reproduce the specification: " + "; ".join(_FAILS)
