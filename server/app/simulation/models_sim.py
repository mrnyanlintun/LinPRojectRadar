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

DEMO_BAC = 100.0


def hash_seed(value) -> int:
    """
    FNV-1a 32-bit, matching sim.js hashSeed exactly.

    The JavaScript derives the synthesised-series generator from hashSeed("series-" + seed) rather
    than from the seed directly. Skipping that transform produced a different series and therefore
    a different sigma, H and breach index, which is how the first validation attempt failed.
    """
    h = 2166136261 & 0xFFFFFFFF
    for ch in str(value):
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h & 0xFFFFFFFF


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
    """Monte Carlo over a Beta-PERT derived from the project's EVM and risk signals."""
    cpi = float(inputs.get("cpi") or 0) or 1.0
    spi = float(inputs.get("spi") or 0) or 1.0
    bac = float(inputs.get("bac") or 0) or DEMO_BAC
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


def derive_series(metric_value: float, seed: int, n: int = 12) -> list[float]:
    """
    A short deterministic metric series when none was supplied.

    The JavaScript hashes a string to seed this; here the caller supplies the seed derived from
    (scenario_id, period), so the synthesised series is a property of the scenario period.
    """
    # Same derivation as the JavaScript: hash the tagged seed string, do not use the seed directly.
    rand = make_rng(hash_seed("series-" + str(seed)))
    out = []
    for t in range(n):
        frac = t / (n - 1)
        base = 1.0 + (metric_value - 1.0) * frac
        out.append(math.floor((base + (rand() - 0.5) * 0.02) * 1000 + 0.5) / 1000)
    return out


def mc_status(overrun_pct_p80: float) -> str:
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


def run_monte_carlo(si: dict, rand, seed: int) -> dict[str, Any]:
    """A1.1. Abstains when bac, cpi or spi is absent, matching the registry's required list."""
    from .models import insufficient
    if any(si.get(k) is None for k in ("bac", "cpi", "spi")):
        return insufficient("Monte_Carlo")

    mc = monte_carlo_eac(
        {"cpi": si.get("cpi"), "spi": si.get("spi"), "bac": si.get("bac"),
         "docScore": si.get("docRiskScore")},
        seed=seed,
    )
    return {
        "method_class": "Monte_Carlo",
        "status_color": mc_status(mc["overrunPctP80"]),
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
    """A1.2. Uses a supplied spiHistory when present, otherwise a seeded derived series."""
    from .models import insufficient
    if si.get("spi") is None:
        return insufficient("CUSUM")

    series = si.get("spiHistory")
    if not series:
        series = derive_series(float(si["spi"]), seed)
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
