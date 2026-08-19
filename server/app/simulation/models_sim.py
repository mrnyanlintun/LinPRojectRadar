"""
Models ported from assets/js/sim.js: Monte Carlo EAC (A1.1) and CUSUM (A1.2).

These are the two most recognisable Cat A1 outputs and they do NOT live in simulations.js, so a
port that touched only that file would have produced an analytical layer conspicuously missing
them. They are ported separately here because they carry their own generator and their own status
thresholds.

Both are reseeded from (scenario_id, period). The JavaScript seeds Monte Carlo from a hash of the
input values, which is deterministic but scenario-blind: two different scenarios that happened to
share cpi/spi/bac would draw the identical sample path. Seeding from the period makes the draw a
property of the scenario period, which is what the design intends.

No module here reads the system clock. Where a "now" is needed it is passed in as the period's
data cutoff.
"""

from __future__ import annotations

import math
from typing import Any, Callable

from .rng import clamp, make_rng, pctile

# THE FIFTEEN DEFECTS, defect 9. `DEMO_BAC = 100.0` used to live here, and `bac` was read as
# `float(inputs.get("bac") or 0) or DEMO_BAC`, so a project with a budget of zero, or with a
# budget the extraction model returned as null, was forecast against a budget of one hundred
# units. Every figure downstream of it, the fiftieth and eightieth percentile forecasts and both
# overrun percentages, was then a percentage of a number no document contained. It is removed
# rather than raised, because there is no correct placeholder: a forecast needs the project's own
# budget or it needs to abstain. The same applies to the two indices, which fell back to 1.0 and
# so forecast an on-plan project whenever performance was recorded as zero.


def _normal(rand: Callable[[], float]) -> float:
    """Box-Muller, matching the JavaScript exactly including the reject-zero loops."""
    u = 0.0
    v = 0.0
    while u == 0:
        u = rand()
    while v == 0:
        v = rand()
    return math.sqrt(-2 * math.log(u)) * math.cos(2 * math.pi * v)


def _gamma(k: float, rand: Callable[[], float]) -> float:
    """Marsaglia-Tsang, valid for k >= 1; the Beta-PERT alpha and beta are always >= 1."""
    d = k - 1.0 / 3.0
    c = 1.0 / math.sqrt(9 * d)
    while True:
        while True:
            x = _normal(rand)
            v = 1 + c * x
            if v > 0:
                break
        v = v * v * v
        u = rand()
        if u < 1 - 0.0331 * x * x * x * x:
            return d * v
        if math.log(u) < 0.5 * x * x + d * (1 - v + math.log(v)):
            return d * v


def _beta(alpha: float, beta_param: float, rand: Callable[[], float]) -> float:
    g1 = _gamma(alpha, rand)
    g2 = _gamma(beta_param, rand)
    return g1 / (g1 + g2)


def monte_carlo_eac(inputs: dict, seed: int, iterations: int = 5000) -> dict[str, Any]:
    """
    Monte Carlo over a Beta-PERT derived from the project's EVM and risk signals.

    Requires a positive budget and positive indices. The caller (run_monte_carlo) refuses before
    reaching here; this assertion exists so that no later caller can reintroduce the fallback by
    passing a falsy budget and receiving a silent substitute.
    """
    cpi = float(inputs.get("cpi") or 0)
    spi = float(inputs.get("spi") or 0)
    bac = float(inputs.get("bac") or 0)
    if not (bac > 0 and cpi > 0 and spi > 0):
        raise ValueError("monte_carlo_eac requires a positive bac, cpi and spi")
    if not (isinstance(iterations, int) and iterations >= 1):
        raise ValueError("monte_carlo_eac requires a positive whole iteration count")
    doc_score = clamp(float(inputs.get("docScore") or 0), 0, 1)

    m_eac = bac / cpi

    cusum_penalty = (
        0.15 if inputs.get("cusumBreached")
        else 0.15 * clamp((float(inputs.get("cusumDrift") or 0))
                          / (float(inputs.get("cusumThreshold") or 0) or 1.0), 0, 1)
    )
    s = clamp(0.5 * (1 - cpi) + 0.3 * (1 - spi) + 0.2 * doc_score + cusum_penalty, 0, 1)

    o = m_eac * (1 - 0.10 * s)
    m = m_eac
    p = m_eac * (1 + 0.40 * s)

    # RUN 10, GATE 1. The three bounds are derived above rather than supplied, so this cannot
    # trip on any input the module accepts. It exists so that a later edit which makes the
    # bounds settable cannot sample a Beta-PERT whose optimistic value exceeds its mode or
    # whose mode exceeds its pessimistic value: that draw would be silently wrong rather than
    # loud, and the shape parameters would come back negative.
    if not (o <= m <= p):
        raise ValueError("monte_carlo_eac requires optimistic <= most likely <= pessimistic")

    rand = make_rng(seed)
    if p - o < 1e-9:
        samples = [m_eac] * iterations
    else:
        alpha = 1 + 4 * (m - o) / (p - o)
        beta_p = 1 + 4 * (p - m) / (p - o)
        samples = [o + _beta(alpha, beta_p, rand) * (p - o) for _ in range(iterations)]

    ordered = sorted(samples)
    p50 = pctile(ordered, 0.50)
    p80 = pctile(ordered, 0.80)
    return {
        "iterations": iterations, "p50": p50, "p80": p80, "o": o, "m": m, "p": p, "s": s,
        "mEAC": m_eac, "baseline": bac,
        "overrunPctP50": (p50 / bac - 1) * 100,
        "overrunPctP80": (p80 / bac - 1) * 100,
    }


def cusum_series(series, target: float = 1.0, sigma=None, h_units: float = 5) -> dict[str, Any]:
    """Standard two-sided tabular CUSUM. Deterministic given the series."""
    x = []
    for v in (series or []):
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if math.isfinite(f):
            x.append(f)

    if sigma is None:
        if len(x) > 1:
            mean = sum(x) / len(x)
            varr = sum((b - mean) ** 2 for b in x) / (len(x) - 1)
            sigma = math.sqrt(varr)
        else:
            sigma = 0.0
    if not (sigma > 0):
        sigma = 0.05  # documented floor so k and H stay meaningful on a short or flat series

    k = 0.5 * sigma
    h = h_units * sigma

    s_hi, s_lo, stat = [], [], []
    hi = lo = 0.0
    breached = False
    breach_index = -1
    for t in range(len(x)):
        hi = max(0.0, hi + (x[t] - target) - k)
        lo = max(0.0, lo + (target - x[t]) - k)
        s_hi.append(hi)
        s_lo.append(lo)
        stat.append(max(hi, lo))
        if not breached and (hi > h or lo > h):
            breached = True
            breach_index = t

    return {"x": x, "target": target, "sigma": sigma, "k": k, "H": h, "hUnits": h_units,
            "sHi": s_hi, "sLo": s_lo, "stat": stat,
            "maxStat": max(stat) if stat else 0.0,
            "breached": breached, "breachIndex": breach_index}


def mc_status(overrun_pct_p80: float) -> str:
    """
    RUN 36, A1.1 CLOSURE, OUTCOME D. HISTORICAL ONLY -- NOT REACHED FROM PRODUCTION.

    This ladder is classified UNSUPPORTED in `parameters.py`: the ten and five per cent
    boundaries are cited to nothing inside or outside this repository, and no calibration set
    exists from which they could be fitted or tested. Until Run 36 it was nevertheless applied,
    and A1.1 was the ONE scientific target in the whole instrument that emitted an authoritative
    status colour from an unresolved parameter on the governed corpus -- measured, not asserted.

    The supervisory specification's own pass ceiling for A1.1 is METHOD_PASS_CALIBRATION_PENDING,
    and rule 2 of `canonical_v3.py` is explicit: where no boundary has been established from
    evidence, "the caller emits the number with calibration pending and asserts no colour".
    A1.1 now does exactly that, which is the same governed treatment A6.1, A6.2 and A6.3 already
    receive. The function is PRESERVED rather than deleted -- this programme does not erase
    scientific history -- and `test_run36_instrument_qualification.py` proves production cannot
    reach it.
    """
    if overrun_pct_p80 >= 10:
        return "red"
    if overrun_pct_p80 >= 5:
        return "amber"
    return "green"


def cusum_status(cu: dict) -> str:
    if cu["breached"]:
        return "red"
    if cu["maxStat"] >= 0.6 * cu["H"]:
        return "amber"
    return "green"


# ---------------------------------------------------------------- module wrappers


#: RUN 36 CLOSURE, THE OWNER'S A1.1 RULING. Declared here beside the code it describes, and
#: asserted from the LIVE SOURCE of the gate by `assert_retained_adaptation_not_reachable` below.
RETAINED_ADAPTATION_ROUTE_REACHABLE = False


def assert_retained_adaptation_not_reachable(check) -> None:
    """
    Prove current production cannot reach the retained scalar Monte Carlo adaptation.

    THE OTHER HALF OF PRESERVING IT. The owner's ruling permits the BAC/CPI/SPI/document-risk
    adaptation to remain as scientific and historical code, and forbids it from emitting the
    current operational A1.1 result, from emitting an authoritative status colour, from voting,
    and from silently substituting for the missing driver-distribution model. Preservation without
    a reachability proof is just a fallback that has not fired yet.

    DERIVED FROM THE LIVE SOURCE OF THE GATE, not from a list. A list would still say what it said
    after someone moved the short-circuit. `registry.run_module` is the ONLY production entry point
    -- `run_all` dispatches through it and nothing else calls the module functions -- so its source
    is read here and asserted to short-circuit A1.1 before the dispatch table is consulted.
    """
    import inspect as _inspect

    from . import registry as _reg

    src = _inspect.getsource(_reg.run_module)
    check("DISABLED_CANONICAL_INPUT_NOT_GOVERNED" in src,
          "production's only module entry point short-circuits the canonical-input-not-governed "
          "set", "the gate is present in run_module")
    gate = src.index("DISABLED_CANONICAL_INPUT_NOT_GOVERNED")
    dispatch = src.index("if new_id not in VALIDATED")
    check(gate < dispatch,
          "and it short-circuits BEFORE the dispatch table is consulted, so the retained "
          "adaptation is never entered", f"gate at {gate}, dispatch at {dispatch}")
    check("A1.1" in _reg.DISABLED_CANONICAL_INPUT_NOT_GOVERNED,
          "A1.1 is in that set", str(sorted(_reg.DISABLED_CANONICAL_INPUT_NOT_GOVERNED)))
    check(RETAINED_ADAPTATION_ROUTE_REACHABLE is False,
          "the retained route is declared unreachable",
          str(RETAINED_ADAPTATION_ROUTE_REACHABLE))
    check(callable(run_monte_carlo) and callable(monte_carlo_eac),
          "while the retained adaptation is PRESERVED for historical reconstruction",
          "run_monte_carlo and monte_carlo_eac still exist")
    row = _reg.run_module("A1.1", {"bac": 1_000_000.0, "cpi": 0.909, "spi": 0.889,
                                   "docRiskScore": 0.35}, (lambda: 0.5), None)
    check(row.get("status_color") is None and row.get("insufficient_data") is True
          and not any(k in row for k in ("p50_eac", "p80_eac", "overrun_pct_p80")),
          "and EXECUTED on inputs the adaptation would happily have computed from, A1.1 returns "
          "no figure and no colour", str(sorted(row))[:200])
    check(row.get("abstention_reason_code")
          == "CANONICAL_DRIVER_DISTRIBUTION_MAPPING_NOT_GOVERNED",
          "with the reason code that distinguishes an ungoverned method definition from an "
          "ordinary missing value", str(row.get("abstention_reason_code")))


def run_monte_carlo(si: dict, rand, seed: int) -> dict[str, Any]:
    """
    A1.1. Abstains when bac, cpi or spi is absent, matching the registry's required list, and
    now also when any of them is present but not positive.

    THE FIFTEEN DEFECTS, defect 9. The absence check was `is not None`, which a budget of zero
    passes: the forecast then ran against the hundred-unit placeholder above, and a zero index
    against a substituted 1.0. A budget of zero is not a budget and a cost or schedule index of
    zero is not performance, so all three refuse rather than being replaced.
    """
    from .models import insufficient
    if any(si.get(k) is None for k in ("bac", "cpi", "spi")):
        return insufficient("Monte_Carlo")
    if not si["bac"] > 0:
        return insufficient(
            "Monte_Carlo",
            "No positive budget at completion is recorded to forecast against")
    if not (si["cpi"] > 0 and si["spi"] > 0):
        return insufficient(
            "Monte_Carlo",
            "Cost or schedule performance is recorded as zero or below, which no forecast "
            "can be scaled by")

    mc = monte_carlo_eac(
        {"cpi": si.get("cpi"), "spi": si.get("spi"), "bac": si.get("bac"),
         "docScore": si.get("docRiskScore")},
        seed=seed,
    )
    return {
        "method_class": "Monte_Carlo",
        # RUN 36, A1.1 CLOSURE, OUTCOME D. No colour is asserted over an uncalibrated quantity.
        # The figure still reaches the ledger, the interface and the export, because
        # `registry.record` routes a calibration-pending row to `computed` rather than to the
        # abstentions; only the band is withheld. Fusion is unaffected: it reads the two voting
        # modules and A1.1 is not one of them.
        "status_color": None,
        "band_asserted": False,
        "calibration_pending": True,
        "calibration_pending_reason": (
            "The forecast is reported as a figure without a colour. The boundaries that would "
            "turn a percentage overrun into a status are not established from evidence held "
            "here, so no status is claimed."),
        "p50_eac": mc["p50"],
        "p80_eac": mc["p80"],
        "overrun_pct_p50": mc["overrunPctP50"],
        "overrun_pct_p80": mc["overrunPctP80"],
        "spread_driver": mc["s"],
        "iterations": mc["iterations"],
        "evidence_metric": (
            f"P80 EAC {mc['p80']:.0f} vs BAC {mc['baseline']:.0f} "
            f"(+{mc['overrunPctP80']:.1f}%); {mc['iterations']} iterations"
        ),
    }


def run_cusum(si: dict, rand, seed: int) -> dict[str, Any]:
    """
    A1.2. Runs on the project's real SPI history and abstains without one.

    D1. This module used to synthesise a twelve-point series from the current SPI whenever no
    history was supplied, which server-side was every project: the browser's blob carried
    spiHistory and the server's assembly never did. A control chart drawn over invented
    observations reported a breach or a clean run about a project nothing had measured over
    time. `spiHistory` is now assembled from the project's earlier periods (documents.py) and
    absence abstains, matching Kalman, ARIMA and Regression to Mean, which read the same series.
    """
    from .models import insufficient
    if si.get("spi") is None:
        return insufficient("CUSUM")

    series = si.get("spiHistory")
    if not isinstance(series, list) or len(series) < 2:
        return insufficient("CUSUM", "Awaiting history (2 periods needed)")
    cu = cusum_series(series)
    return {
        "method_class": "CUSUM",
        "status_color": cusum_status(cu),
        "sigma": cu["sigma"],
        "k": cu["k"],
        "H": cu["H"],
        "max_stat": cu["maxStat"],
        "breached": cu["breached"],
        "breach_index": cu["breachIndex"],
        "periods": len(cu["x"]),
        "evidence_metric": (
            f"CUSUM max {cu['maxStat']:.3f} against H {cu['H']:.3f} over {len(cu['x'])} periods"
            + ("; breached" if cu["breached"] else "; no breach")
        ),
    }
