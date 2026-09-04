"""
lin-project-radar backend — simulations.py  (Sprint 0 items 25-29)
Python port of the five client-side JS simulation models. Pure functions
over a project's extracted signalInputs; no network, no OpenAI.
"""
import numpy as np


# ---------------------------------------------------------------- abstention
# Run 135B / S3. These models previously read their inputs with `or`, so a real
# zero — spi 0, bac 0, actualPctComplete 0 — was indistinguishable from a missing
# key and was replaced by a favourable stand-in (spi 1.0, bac 1, pct_complete 37).
# `run_all({})` therefore returned a full five-signal Red/Green/Green/Red/Amber
# verdict over inputs nobody supplied.
#
# Now a model that lacks a required input abstains and says what it needs. The
# abstention carries status_color "Indeterminate", which is deliberately NOT one
# of PCEIFGovernanceRouter.CANONICAL_SIGNAL_STATUS: the router will reject it and
# abstain in turn, so the absence propagates instead of being coloured in.
ABSTAIN = "Indeterminate"


def _required(signal_inputs: dict, key: str):
    """Return (value, None) when the input is present and numeric, else (None, reason).

    Presence is `is not None`, never truthiness — a real zero is a value.
    """
    if key not in signal_inputs or signal_inputs[key] is None:
        return None, f"{key} absent"
    try:
        return float(signal_inputs[key]), None
    except (TypeError, ValueError):
        return None, f"{key} is not numeric ({signal_inputs[key]!r})"


def _abstain(method_class: str, needs: list) -> dict:
    return {
        "method_class": method_class,
        "status_color": ABSTAIN,
        "needs": needs,
        "evidence_metric": f"Abstained — {method_class} requires " + "; ".join(needs),
    }


def _sample_triangular(a, m, b):
    if b <= a:  # degenerate guard
        return float(a)
    F = (m - a) / (b - a)
    U = np.random.random()
    if U < F:
        return a + np.sqrt(U * (b - a) * (m - a))
    return b - np.sqrt((1 - U) * (b - a) * (b - m))


def run_pert(signal_inputs: dict) -> dict:
    """PERT Network Criticality — stochastic path analysis."""
    spi, why = _required(signal_inputs, "spi")
    if why:
        return _abstain("PERT_Network_Criticality", [why])
    network = {
        "A": {"a": 12, "m": 15, "b": int(24 / max(spi, 0.5))},
        "B": {"a": 18, "m": 22, "b": int(36 / max(spi, 0.5))},
        "C": {"a": 6,  "m": 9,  "b": int(15 / max(spi, 0.5))},
    }
    iterations = 5000
    p1_critical = 0
    durations = []
    for _ in range(iterations):
        d = {k: _sample_triangular(v["a"], v["m"], v["b"]) for k, v in network.items()}
        p1 = d["A"] + d["B"]
        p2 = d["A"] + d["C"]
        durations.append(max(p1, p2))
        if p1 >= p2:
            p1_critical += 1
    p80 = float(np.percentile(durations, 80))
    criticality = round(p1_critical / iterations * 100, 1)
    status = "Red" if p80 > 45 else ("Amber" if p80 > 35 else "Green")
    return {
        "method_class": "PERT_Network_Criticality", "status_color": status,
        "p80_duration_days": round(p80, 1), "path_criticality_index": criticality,
        "evidence_metric": f"P80 path {round(p80, 1)}d; structural path critical {criticality}% of runs",
    }


def run_lob(signal_inputs: dict) -> dict:
    """Line of Balance — production velocity."""
    spi, why = _required(signal_inputs, "spi")
    if why:
        return _abstain("Line_of_Balance_Velocity", [why])
    grading_rate = 2.2
    paving_rate = 1.6 * max(spi, 0.5)
    buffer = 6.0
    total_units = 40
    min_buffer = float("inf")
    critical_unit = 0
    for u in range(total_units):
        t_grade = u / grading_rate
        t_pave = (u / paving_rate) + buffer
        b = t_pave - t_grade
        if b < min_buffer:
            min_buffer = b
            critical_unit = u
    status = "Red" if min_buffer <= 1.5 else ("Amber" if min_buffer <= 3.0 else "Green")
    return {
        "method_class": "Line_of_Balance_Velocity", "status_color": status,
        "minimum_buffer_days": round(min_buffer, 2), "critical_unit_index": critical_unit,
        "evidence_metric": f"Min crew buffer {round(min_buffer, 1)}d (paving {round(paving_rate, 2)} vs grading {grading_rate} units/day)",
    }


def run_ccpm(signal_inputs: dict) -> dict:
    """CCPM Buffer Health Fever Chart."""
    # actualPctComplete is preferred; plannedPctComplete is the stated fallback. A zero in
    # either is a real zero per cent complete, not an absent figure. There is no third default:
    # the 37 that used to sit here was an invented input.
    pct_complete, why_pct = _required(signal_inputs, "actualPctComplete")
    if why_pct is not None:
        pct_complete, why_planned = _required(signal_inputs, "plannedPctComplete")
        why_pct = None if why_planned is None else "actualPctComplete or plannedPctComplete required, neither usable"
    spi, why_spi = _required(signal_inputs, "spi")
    needs = [w for w in (why_pct, why_spi) if w]
    if needs:
        return _abstain("CCPM_Buffer_Health", needs)
    buffer_consumed = max(0, (1 - spi) * 100 * 1.5)
    amber_line = pct_complete
    red_line = pct_complete + (100 - pct_complete) / 3
    status = "Red" if buffer_consumed >= red_line else ("Amber" if buffer_consumed >= amber_line else "Green")
    return {
        "method_class": "CCPM_Buffer_Health", "status_color": status,
        "pct_chain_complete": round(pct_complete, 1), "pct_buffer_consumed": round(buffer_consumed, 1),
        "evidence_metric": f"Buffer {round(buffer_consumed, 1)}% consumed at {round(pct_complete, 1)}% chain complete",
    }


def run_rcf(signal_inputs: dict) -> dict:
    """Reference Class Forecasting — cost prior."""
    bac, why = _required(signal_inputs, "bac")
    if why:
        return _abstain("Reference_Class_Forecasting", [why])
    multipliers = [1.00, 1.04, 1.10, 1.14, 1.15, 1.26, 1.38, 1.45, 1.52]
    p50 = bac * multipliers[len(multipliers) // 2]
    p80 = bac * multipliers[int(len(multipliers) * 0.8)]
    debias = multipliers[int(len(multipliers) * 0.8)]
    pct_over = round((debias - 1) * 100, 1)
    status = "Red" if pct_over > 25 else ("Amber" if pct_over > 10 else "Green")
    return {
        "method_class": "Reference_Class_Forecasting", "status_color": status,
        "rcf_p50_adjusted": round(p50), "rcf_p80_adjusted": round(p80),
        "debiasing_factor": debias,
        "evidence_metric": f"P80 cost prior ${round(p80):,} (+{pct_over}% vs BAC); debias ×{debias}",
    }


def run_dsm(signal_inputs: dict) -> dict:
    """DSM Rework Propagation."""
    dsm = np.array([[0.0, 0.3, 0.1], [0.5, 0.0, 0.2], [0.4, 0.4, 0.0]])
    state = np.array([1.0, 0.0, 0.0])
    cumulative = state.copy()
    for _ in range(4):
        state = dsm @ state
        cumulative += state
    total = float(cumulative.sum())
    status = "Amber" if total > 2.5 else "Green"
    return {
        "method_class": "DSM_Rework_Propagation", "status_color": status,
        "rework_multiplier": round(total, 2),
        "evidence_metric": f"Architectural change → ×{round(total, 2)} cumulative rework across Arch/Struct/MEP (4 propagation passes)",
    }


def run_all(signal_inputs: dict) -> list:
    return [
        run_pert(signal_inputs), run_lob(signal_inputs),
        run_ccpm(signal_inputs), run_rcf(signal_inputs), run_dsm(signal_inputs),
    ]
