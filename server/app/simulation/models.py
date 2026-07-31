"""
Ported analytical models.

Ported from assets/js/simulations.js, the implementation the instrument has always run, and
validated numerically against it with a shared seeded generator. See VALIDATION.md for the
per-module comparison.

NOT ported from backend/simulations.py. That spike covers 5 of 91 and diverges from the JavaScript
in every one of them: different network topology and thresholds in PERT, different rates and unit
counts in LOB, a different default completion in CCPM, a different percentile rule in RCF, and a
different coefficient in the DSM matrix. Porting it would have moved a second, undocumented model
set into the study under the same names.

Every function is pure: signalInputs in, a result dict out. The only randomness is the `rand`
callable the caller supplies, seeded from (scenario_id, period).

Every model takes `period_cutoff`, the reporting period's data cutoff date. Most ignore it.
It exists so that NO module ever reads the system clock: a module needing a notion of "now"
receives the cutoff instead. A wall-clock read would make the same documents produce different
results on different days, which is the exact confound the frozen-extraction design removes.
"""

from __future__ import annotations

import math
from typing import Any, Callable

from .rng import as_percent, clamp, num, pctile, round1, round2

# Stamped on every result set, so a later change to this layer is detectable in already-collected
# data rather than being invisible in the analysis.
SIMULATION_VERSION = "sim-2026.07-v1"


def insufficient(method_class: str, message: str | None = None) -> dict[str, Any]:
    """
    The abstention contract, matching the JavaScript helper exactly.

    A module with missing inputs abstains. It does not fall back to a neutral value: a fabricated
    Green is indistinguishable from a measured one once it reaches fusion.
    """
    return {
        "method_class": method_class,
        "status_color": None,
        "insufficient_data": True,
        "evidence_metric": message or "Insufficient data: upload required documents",
    }


def check_inputs(si: dict, required: tuple[str, ...]) -> bool:
    return all(si.get(k) is not None for k in required)


def _sample_triangular(a: float, m: float, b: float, rand: Callable[[], float]) -> float:
    """Exact inverse-CDF triangular sampler, matching the JavaScript reference."""
    f = (m - a) / (b - a)
    u = rand()
    if u < f:
        return a + math.sqrt(u * (b - a) * (m - a))
    return b - math.sqrt((1 - u) * (b - a) * (b - m))


# ---------------------------------------------------------------- A2.1 PERT


def run_pert(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    PERT stochastic network criticality. A then (B parallel C); finish = A + max(B, C).

    The only stochastic model in the ported set. The caller seeds from (scenario_id, period), so
    every participant on that scenario and period draws the identical sample path.
    """
    spi = num(si.get("spi"), 1.0)
    pess = 1 + max(0.0, 1 - spi) * 0.8
    a_act = (8.0, 10.0, 14.0)
    b_act = (12.0, 15.0, 22.0 * pess)
    c_act = (10.0, 13.0, 18.0 * pess)

    n = 2000
    totals = []
    b_critical = 0
    for _ in range(n):
        a = _sample_triangular(*a_act, rand)
        b = _sample_triangular(*b_act, rand)
        c = _sample_triangular(*c_act, rand)
        totals.append(a + max(b, c))
        if b >= c:
            b_critical += 1

    totals.sort()
    p50 = pctile(totals, 0.50)
    p80 = pctile(totals, 0.80)
    crit = b_critical / n
    baseline = a_act[1] + max(b_act[1], c_act[1])
    ratio = p80 / baseline
    color = "Red" if ratio > 1.30 else ("Amber" if ratio > 1.15 else "Green")

    return {
        "method_class": "PERT_Network_Criticality",
        "status_color": color,
        "p50_duration_days": round1(p50),
        "p80_duration_days": round1(p80),
        "baseline_days": round1(baseline),
        "path_criticality_index": round2(crit),
        "evidence_metric": (
            f"P80 path {round1(p80)}d vs baseline {round1(baseline)}d; "
            f"structural path critical {int(math.floor(crit * 100 + 0.5))}% of runs"
        ),
    }


# ---------------------------------------------------------------- A2.2 LOB


def run_lob(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """Line of balance: leader (grading) against follower (paving), buffer eroding per unit."""
    spi = num(si.get("spi"), 1.0)
    units = 20
    grading_rate = 2.0
    paving_rate = 1.8 * clamp(spi, 0.3, 1.2)
    initial_buffer = 5.0
    lag = max(0.0, (1 / paving_rate) - (1 / grading_rate))

    min_buffer = initial_buffer
    crit_unit = units
    flagged = False
    for u in range(1, units + 1):
        buf = initial_buffer - u * lag
        if buf < min_buffer:
            min_buffer = buf
        if not flagged and buf <= 1.5:
            crit_unit = u
            flagged = True

    color = "Red" if min_buffer <= 1.5 else ("Amber" if min_buffer <= 3.0 else "Green")
    return {
        "method_class": "Line_of_Balance_Velocity",
        "status_color": color,
        "minimum_buffer_days": round1(min_buffer),
        "critical_unit_index": crit_unit,
        "grading_rate": grading_rate,
        "paving_rate": round2(paving_rate),
        "initial_buffer_days": initial_buffer,
        "units": units,
        "evidence_metric": (
            f"Min crew buffer {round1(min_buffer)}d (paving {round2(paving_rate)} "
            f"vs grading {grading_rate} units/day)"
        ),
    }


# ---------------------------------------------------------------- A2.3 CCPM


def run_ccpm(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """CCPM buffer-health fever chart: buffer consumption against chain completion."""
    raw = si.get("actualPctComplete")
    if raw is None:
        raw = si.get("plannedPctComplete")
    pct_chain = as_percent(raw, 0.0)
    spi = num(si.get("spi"), 1.0)
    pct_buffer = clamp((1 - spi) * 100 * 1.5, 0, 100)
    amber = pct_chain
    red = pct_chain + (100 - pct_chain) / 3
    color = "Red" if pct_buffer >= red else ("Amber" if pct_buffer >= amber else "Green")

    return {
        "method_class": "CCPM_Buffer_Health",
        "status_color": color,
        "pct_chain_complete": round1(pct_chain),
        "pct_buffer_consumed": round1(pct_buffer),
        "zone": color,
        "amber_threshold": round1(amber),
        "red_threshold": round1(red),
        "evidence_metric": (
            f"Buffer {round1(pct_buffer)}% consumed at {round1(pct_chain)}% chain complete"
        ),
    }


# ---------------------------------------------------------------- A3.1 RCF


def run_rcf(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """Reference class forecasting: empirical overrun multipliers as a cost prior."""
    bac = num(si.get("bac"), 0.0)
    ordered = sorted([1.00, 1.04, 1.10, 1.14, 1.15, 1.26, 1.38, 1.45, 1.52])
    p50 = pctile(ordered, 0.50)
    p80 = pctile(ordered, 0.80)
    p50_adj = bac * p50
    p80_adj = bac * p80
    over = (p80 - 1) * 100
    color = "Green" if over <= 10 else ("Amber" if over <= 25 else "Red")

    if bac > 0:
        evidence = (f"P80 cost prior ${int(math.floor(p80_adj + 0.5)):,} "
                    f"(+{round1(over)}% vs BAC); debias x{round2(p80)}")
    else:
        evidence = f"Debias x{round2(p80)} (+{round1(over)}% P80 prior; BAC not yet extracted)"

    return {
        "method_class": "Reference_Class_Forecasting",
        "status_color": color,
        "rcf_p50_adjusted": int(math.floor(p50_adj + 0.5)),
        "rcf_p80_adjusted": int(math.floor(p80_adj + 0.5)),
        "debiasing_factor": round2(p80),
        "vs_bac_pct": round1(over),
        "p50_multiplier": round2(p50),
        "p80_multiplier": round2(p80),
        "multipliers": list(ordered),
        "bac": bac,
        "evidence_metric": evidence,
    }


# ---------------------------------------------------------------- A5.1 DSM


def run_dsm(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Design structure matrix rework propagation across Arch, Structural and MEP.

    The 3x3 multiply is written out rather than taken from numpy: the service has been bitten
    twice by compiled-wheel availability and does not need the dependency for nine multiplies.
    The discarded spike also had 0.40 where the instrument has 0.30 at [2][1].
    """
    matrix = [
        [0.0, 0.30, 0.10],
        [0.50, 0.0, 0.20],
        [0.40, 0.30, 0.0],
    ]
    wave = [1.0, 0.0, 0.0]
    cumulative = list(wave)
    for _ in range(4):
        nxt = [0.0, 0.0, 0.0]
        for i in range(3):
            for j in range(3):
                nxt[i] += matrix[i][j] * wave[j]
        for k in range(3):
            cumulative[k] += nxt[k]
        wave = nxt

    total = cumulative[0] + cumulative[1] + cumulative[2]
    color = "Amber" if total > 2.5 else "Green"
    return {
        "method_class": "DSM_Rework_Cat5",
        "status_color": color,
        "rework_multiplier": round2(total),
        "matrix": [list(r) for r in matrix],
        "arch_impact": round2(cumulative[0]),
        "structural_impact": round2(cumulative[1]),
        "mep_impact": round2(cumulative[2]),
        "evidence_metric": (
            f"Architectural change -> x{round2(total)} cumulative rework across "
            f"Arch/Struct/MEP (4 propagation passes)"
        ),
    }


# Validated against the JavaScript. Keyed by the registry's new id.
#
# A1.1 and A1.2 come from sim.js and need the seed itself, not just a generator, because they
# derive their own streams from it. They are adapted here so the registry can call every module
# through one signature.
SEED_HOLDER: dict = {}


def run_monte_carlo_module(si, rand, period_cutoff):
    from .models_sim import run_monte_carlo
    return run_monte_carlo(si, rand, SEED_HOLDER.get("seed", 0))


def run_cusum_module(si, rand, period_cutoff):
    from .models_sim import run_cusum
    return run_cusum(si, rand, SEED_HOLDER.get("seed", 0))


VALIDATED: dict[str, tuple[str, Callable[[dict, Callable[[], float], object], dict]]] = {
    "A1.1": ("Monte_Carlo", run_monte_carlo_module),
    "A1.2": ("CUSUM", run_cusum_module),
    "A2.1": ("PERT_Network_Criticality", run_pert),
    "A2.2": ("Line_of_Balance_Velocity", run_lob),
    "A2.3": ("CCPM_Buffer_Health", run_ccpm),
    "A3.1": ("Reference_Class_Forecasting", run_rcf),
    "A5.1": ("DSM_Rework_Cat5", run_dsm),
}


def _register_extensions() -> None:
    # Imported late: models_ext imports helpers from this module.
    from .models_doc import A4_EXTENSIONS, A5_EXTENSIONS
    from .models_evm import A1_EXTENSIONS
    from .models_ext import A2_EXTENSIONS, A3_EXTENSIONS
    VALIDATED.update(A1_EXTENSIONS)
    VALIDATED.update(A2_EXTENSIONS)
    VALIDATED.update(A3_EXTENSIONS)
    VALIDATED.update(A4_EXTENSIONS)
    VALIDATED.update(A5_EXTENSIONS)


_register_extensions()

# Stochastic models, for the seed record on the result set.
STOCHASTIC: frozenset[str] = frozenset({"A1.1", "A1.2", "A2.1"})
