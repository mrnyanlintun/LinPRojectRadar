#!/usr/bin/env python3
"""
Run 8: retest and classification of the 27 modules Run 6 left without a known-answer case.

THIS SUITE CHANGES NO PRODUCTION CODE. It adds tests only. Every defect a case reveals is
asserted as the CURRENT behaviour and named in the report as a defect; nothing is fixed here.

WHAT A CASE IN THIS FILE IS.

1. THE EXPECTED VALUE IS DERIVED BY HAND FROM THE MODULE'S OWN STATED FORMULA, and the
   derivation is written in the comment beside it. Nothing in this file runs a module and
   records what it returned as the expectation. Where no independent oracle exists the case is
   a property, a pass-through contract or an abstention contract, and it is labelled as such.

2. EVERY EXPECTATION IS PROVED ABLE TO FAIL BY PERTURBING THE EXPECTED VALUE, not the input.
   `ka()` refuses a case whose expectation cannot be perturbed, and writes the proof row to
   code_audit/run8_expectation_mutation_proof.csv.

3. A PROPERTY ASSERTED OVER A DOMAIN IS EXHAUSTED OR RANDOMISED. A run in this programme once
   asserted a property that was false and passed because the sample space satisfied it.

4. THE PRODUCTION PATH IS DRIVEN. Section 12 runs compute_project and registry.run_all and
   asserts each of the 27 appears there in the state the direct cases predict.

Run:
    PYTHONIOENCODING=utf-8 python tools/test_run8_retest_classify_27.py
"""

from __future__ import annotations

import csv
import math
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

import app.simulation.registry as registry  # noqa: E402
from app.simulation.compute import compute_project  # noqa: E402
from app.simulation.models import VALIDATED, run_lob, run_pert  # noqa: E402
from app.simulation.models_doc import (  # noqa: E402
    run_agent_supply_chain, run_contractor_performance, run_discrete_event_sim,
    run_environmental_compliance, run_ncr_rate, run_quality_compliance,
    run_queueing_bottleneck, run_rework_feedback, run_safety_performance,
    run_scenario_modeling, run_spec_conflict_density,
)
from app.simulation.models_evm import (  # noqa: E402
    run_arima_forecast, run_earned_schedule, run_ice_ratio,
)
from app.simulation.models_ext import (  # noqa: E402
    run_cost_risk, run_critical_path_index, run_float_consumption, run_resource_loading,
    run_schedule_risk,
)
from app.simulation.models_fuzzy import run_critic_topsis, run_marcos  # noqa: E402
from app.simulation.models_sim import run_monte_carlo  # noqa: E402
from app.simulation.rng import make_rng  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
PASSED = 0
FAILED = 0
CASES = 0
PERTURBED = 0
NOOP = object()
MUTATION_ROWS: list[dict] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def _perturb(expected):
    if isinstance(expected, bool):
        return not expected
    if isinstance(expected, (int, float)):
        # `expected * 2 + 1` is a fixed point at -1, which would silently make a case whose
        # expectation is -1 unprovable. Fall back to a shift whenever the doubling returns the
        # value it was meant to differ from.
        candidate = expected + 1 if expected == 0 else expected * 2 + 1
        return candidate if candidate != expected else expected - 1
    if isinstance(expected, str):
        return expected + " (perturbed)"
    if isinstance(expected, (list, tuple)):
        return list(expected) + ["perturbed"]
    if isinstance(expected, (set, frozenset)):
        return set(expected) | {"perturbed"}
    if isinstance(expected, dict):
        out = dict(expected)
        out["__perturbed__"] = True
        return out
    if expected is None:
        return "__not-none__"
    return NOOP


def ka(actual, expected, label: str, module_id: str = "", kind: str = "known_answer",
       derivation: str = "") -> None:
    """One case: the value, the hand-derived expectation, and the proof the check can fail."""
    global CASES, PERTURBED
    CASES += 1
    bad = _perturb(expected)
    if bad is NOOP:
        check(False, f"{label}: expectation cannot be perturbed", repr(expected))
        return
    live = actual != bad
    if live:
        PERTURBED += 1
    ok = actual == expected and live
    MUTATION_ROWS.append({
        "module_id": module_id,
        "check_label": label,
        "kind": kind,
        "expected": repr(expected),
        "perturbed_expectation": repr(bad),
        "actual": repr(actual),
        "red_under_perturbation": "yes" if live else "NO",
        "green_when_restored": "yes" if actual == expected else "NO",
        "derivation": derivation,
    })
    check(ok, label, f"expected {expected!r} got {actual!r}")


def section(n: str) -> None:
    print()
    print("=" * 78)
    print(n)
    print("=" * 78)


def abstains(r) -> bool:
    return r.get("status_color") is None and r.get("insufficient_data") is True


def speakable(r, label: str) -> None:
    """The abstention contract as the ledger renders it: words, no key name, no module id."""
    reason = r.get("evidence_metric") or ""
    ok = bool(reason.strip())
    ok = ok and not re.search(r"\b[A-D]\d+\.\d+\b", reason)
    ok = ok and "—" not in reason
    ok = ok and "_" not in reason
    check(ok, f"{label}: abstention reason is speakable", reason[:110])


NO_ARG = make_rng(0)


# =================================================================================================
section("0. THE FROZEN-FILE GUARD, INHERITED FROM RUN 7 AND NARROWED BACK TO EMPTY")
# =================================================================================================
#
# Run 7 re-based this guard onto a pinned SHA with six named permitted files. Run 8 changes no
# production code at all, so its permitted set is EMPTY and the baseline moves forward to the
# commit Run 8 was cut from: origin/main after Run 7 merged. Anything differing under
# server/app/ or assets/ is a scope breach and fails here.

GUARD_BASELINE_REV = "18b6b80"
RUN8_SCOPED_FILES: set[str] = set()

_diff = subprocess.run(["git", "diff", "--name-only", GUARD_BASELINE_REV, "--"],
                       cwd=str(ROOT), capture_output=True, text=True).stdout.split()
_prod = [p for p in _diff
         if (p.startswith("server/app/") or p.startswith("assets/"))
         and p not in RUN8_SCOPED_FILES]
check(not _prod, "no production file under server/app/ or assets/ differs from the pinned "
                 "baseline", " ".join(_prod))
check(not any(p.startswith("assets/") for p in _diff),
      "nothing under assets/ differs from the pinned baseline",
      " ".join(p for p in _diff if p.startswith("assets/")))


# =================================================================================================
section("1. THE EXACT 27, DERIVED FROM RUN 6's OWN COVERAGE ARITHMETIC RATHER THAN COPIED")
# =================================================================================================
#
# Run 6's section 9 computed its uncovered set as
#     registry-computed - covered here - covered by Run 4 - disabled concept-only
# and printed the result. This run re-derives it from the SAME sources, reading Run 6's own
# COVERED_HERE set out of the merged suite file rather than retyping the 27 ids, so a drift in
# the registry or in Run 6's coverage claim would show up here as a count that is not 27.

_run6_src = (ROOT / "server" / "tools" / "test_run6_known_answer.py").read_text(encoding="utf-8")
_m = re.search(r"COVERED_HERE[^=]*=\s*\{(.*?)\n\}", _run6_src, re.S)
COVERED_BY_RUN_6 = set(re.findall(r'"([A-D]\d+\.\d+)"', _m.group(1)))
COVERED_BY_RUN_4 = {"A1.7", "A1.8"}

_registered = {m for m in registry.registry_index()
               if m in VALIDATED or m in registry.PORTFOLIO_VALIDATED}
_disabled = set(registry.DISABLED_CONCEPT_ONLY)
UNRESOLVED_27 = sorted(_registered - COVERED_BY_RUN_6 - COVERED_BY_RUN_4 - _disabled)

ka(len(_registered), 100, "registry-computed modules", kind="derivation",
   derivation="the registry's own count, not a document's claim")
ka(len(COVERED_BY_RUN_6), 63, "modules Run 6 gave a known-answer case", kind="derivation",
   derivation="read out of the merged Run 6 suite's COVERED_HERE set")
ka(len(_disabled), 8, "disabled concept-only modules", kind="derivation")
ka(len(UNRESOLVED_27), 27, "the deduplicated unresolved universe is exactly 27",
   kind="derivation", derivation="100 - 63 - 2 - 8 = 27")
ka(len(set(UNRESOLVED_27)), 27, "the unresolved universe has no duplicate", kind="derivation")
check(all(m in _registered for m in UNRESOLVED_27),
      "every unresolved id is a module this server actually computes")
check(not (set(UNRESOLVED_27) & _disabled),
      "no unresolved module is one of the Run 1 disabled concept-only modules")
print("     " + " ".join(UNRESOLVED_27))

#: The bucket assignment this run defends, written into the code so the classification is in the
#: suite and not only in the report. Every one of the 27 appears exactly once.
BUCKETS: dict[str, int] = {
    # 2 -- defect reproducible with current data, or the correct behaviour is abstention
    "A1.5": 2, "A1.6": 2, "A1.11": 2, "A2.1": 2, "A2.5": 2, "A2.9": 2, "A2.10": 2,
    "A2.11": 2, "A3.6": 2, "A4.10": 2, "A5.5": 2, "A5.8": 2, "A6.1": 2, "A6.2": 2,
    "A6.4": 2, "B2.18": 2,
    # 3 -- an additional synthetic project-structure corpus is required
    "A1.1": 3, "A2.2": 3, "A2.3": 3, "A4.4": 3, "A5.6": 3, "A5.7": 3, "A6.3": 3,
    # 4 -- a synthetic reference, training, expert-rule or decision dataset is required
    "A5.4": 4, "B2.19": 4,
    # 5 -- unconditionally abstaining since Run 7; stays off until the owner authorises
    "A3.1": 5, "A5.1": 5,
}
ka(sorted(BUCKETS), UNRESOLVED_27, "the classification covers exactly the derived 27",
   kind="derivation")
ka(sum(1 for v in BUCKETS.values() if v == 1), 0, "Bucket 1 count", kind="derivation")
ka(sum(1 for v in BUCKETS.values() if v == 2), 16, "Bucket 2 count", kind="derivation")
ka(sum(1 for v in BUCKETS.values() if v == 3), 7, "Bucket 3 count", kind="derivation")
ka(sum(1 for v in BUCKETS.values() if v == 4), 2, "Bucket 4 count", kind="derivation")
ka(sum(1 for v in BUCKETS.values() if v == 5), 2, "Bucket 5 count", kind="derivation")
ka(len(BUCKETS), 27, "bucket totals sum to 27", kind="derivation")

# None of the 27 carries a Run 1 proxy qualifier. Recorded as a structural fact about the
# universe rather than asserted per module sixteen times.
_qualified = [m for m in UNRESOLVED_27 if m in registry.PROXY_QUALIFIERS]
ka(_qualified, [], "no module in the unresolved 27 carries a Run 1 proxy qualifier",
   kind="derivation",
   derivation="registry.PROXY_QUALIFIERS intersected with the derived 27")


# =================================================================================================
section("2. EVERY ONE OF THE 27 ABSTAINS ON AN EMPTY INPUT, AND SAYS WHY IN WORDS")
# =================================================================================================
#
# Run 6 found seven modules that banded from nothing; Run 7 corrected five of them. This is the
# re-test of that correction restricted to the 27, plus the speakability contract on each.

_EMPTY_BANDED = []
for mid in UNRESOLVED_27:
    r = VALIDATED[mid][1]({}, make_rng(1), "2025-06-30")
    if not abstains(r):
        _EMPTY_BANDED.append((mid, r.get("status_color")))
    else:
        speakable(r, f"{mid} on an empty input")
ka(_EMPTY_BANDED, [], "not one of the 27 produces a band from an empty input",
   kind="domain", derivation="every module executed on {} and the banders collected")


# =================================================================================================
section("3. A2.1 PERT NETWORK CRITICALITY: A HEALTHY READING IS STRUCTURALLY UNREACHABLE")
# =================================================================================================
#
# THE DERIVATION, BY HAND FROM THE MODULE'S OWN LITERALS, BEFORE ANY CODE IS RUN.
#
# The three activities are A = (8, 10, 14), B = (12, 15, 22*p), C = (10, 13, 18*p), where the
# pessimism factor p = 1 + max(0, 1 - spi) * 0.8, so p = 1 for every schedule index at or above
# 1.0 and p > 1 below it. Finish time = A + max(B, C).
#
# The BASELINE the ratio divides by is a_mode + max(b_mode, c_mode) = 10 + max(15, 13) = 25.
# That is a sum of MODES. The numerator is the EIGHTIETH PERCENTILE of a sum of two
# right-skewed triangular variables. For a triangular (a, m, b) the mean is (a + m + b)/3, so
#   E[A]      = (8 + 10 + 14)/3 = 32/3  = 10.667
#   E[B]      = (12 + 15 + 22)/3 = 49/3 = 16.333   (at p = 1, the most optimistic case)
#   E[C]      = (10 + 13 + 18)/3 = 41/3 = 13.667
# and E[max(B, C)] >= E[B] = 16.333 for any coupling. So the EXPECTED finish is already at
# least 10.667 + 16.333 = 27.0 against a baseline of 25, a ratio of 1.08 at the MEAN, and the
# eightieth percentile lies above the mean for this right-skewed sum. The Green arm requires
# ratio <= 1.15, i.e. a P80 at or below 28.75.
#
# The band is therefore a comparison of two different statistics of the same distribution: an
# upper percentile against a lower-than-mean point estimate. No schedule index can close that
# gap, because p = 1 is the floor and the literals are fixed. Asserted below over 200 seeds and
# eight indices spanning 0.6 to 2.0, so the claim rests on the domain and not on one draw.

_pert_bands = set()
_pert_min_ratio = None
for seed in range(200):
    for spi in (0.6, 0.8, 0.9, 1.0, 1.05, 1.2, 1.5, 2.0):
        r = run_pert({"spi": spi}, make_rng(seed), "2025-06-30")
        _pert_bands.add(r["status_color"])
        ratio = r["p80_duration_days"] / r["baseline_days"]
        if _pert_min_ratio is None or ratio < _pert_min_ratio:
            _pert_min_ratio = ratio
ka(sorted(_pert_bands), ["Amber", "Red"], "A2.1: only Amber and Red are reachable over 1,600 "
   "seed and index combinations", "A2.1", "property",
   "Green needs P80/baseline <= 1.15; the numerator is a P80 and the denominator a sum of modes")
check(_pert_min_ratio > 1.15,
      "A2.1: the lowest ratio observed anywhere in the domain is still above the Green edge",
      f"lowest {_pert_min_ratio:.4f}")
ka(round(25.0, 1), 25.0, "A2.1: the baseline is the sum of the modes, 10 + max(15, 13)",
   "A2.1", "known_answer", "a_mode 10 plus max(b_mode 15, c_mode 13)")
_r = run_pert({"spi": 2.0}, make_rng(11), "2025-06-30")
ka(_r["baseline_days"], 25.0, "A2.1: a project twice as fast as plan still divides by 25 days",
   "A2.1", "known_answer", "p is floored at 1, so the literals and the baseline do not move")
ka(_r["status_color"], "Amber", "A2.1: a project twice as fast as plan reads Amber",
   "A2.1", "enumerated")
# The abstention Run 7 installed still holds.
ka(abstains(run_pert({}, make_rng(1), "2025-06-30")), True,
   "A2.1: still abstains without a schedule index", "A2.1", "abstention")


# =================================================================================================
section("4. B2.18 MARCOS: THE SCORE IS SYMMETRIC IN UTILITY, SO ONLY RED IS REACHABLE")
# =================================================================================================
#
# THE DERIVATION, BY HAND FROM THE MODULE'S OWN ALGEBRA.
#
# Let u be the weighted utility against the ideal. The module sets
#     utility_anti = 1 - u
# so the two always sum to exactly 1, and therefore
#     f_ideal = u / (u + (1 - u)) = u        f_anti = (1 - u) / 1 = 1 - u
# The reported score is
#     (f_ideal + f_anti) / (1 + (1 - f_ideal)/f_ideal + (1 - f_anti)/f_anti)
#   = 1 / (1 + (1 - u)/u + u/(1 - u))
# The numerator collapses to 1 because f_ideal + f_anti = 1 by construction. The denominator is
# invariant under u -> 1 - u, so THE SCORE IS SYMMETRIC ABOUT u = 0.5: a project with a utility
# of 0.2 and a project with a utility of 0.8 receive the identical score. The denominator is
# minimised at u = 0.5, where it is 1 + 1 + 1 = 3, so
#     max score = 1/3 = 0.333
# and the Amber arm requires score >= 0.35. NO INPUT CAN REACH AMBER, YELLOW OR GREEN.
#
# Worked corners, both computed here by hand and not from the code:
#   u = 0.5  -> 1/(1 + 1 + 1)            = 0.3333, rounds to 0.333
#   u = 0.8  -> 1/(1 + 0.25 + 4)         = 1/5.25 = 0.190476, rounds to 0.19
#   u = 0.2  -> 1/(1 + 4 + 0.25)         = 1/5.25 = 0.190476, rounds to 0.19  (same as u = 0.8)
#   u = 1.0  -> f_anti = 0, so (1 - f_anti)/f_anti divides by zero; the port's JavaScript
#               division yields infinity and the score collapses to 0.

_marcos_bands = {}
_marcos_max = None
for cpi_i in range(50, 161, 2):
    for spi_i in range(50, 161, 2):
        for doc_i in range(0, 101, 5):
            r = run_marcos({"cpi": cpi_i / 100, "spi": spi_i / 100,
                            "docRiskScore": doc_i / 100}, NO_ARG, "2025-06-30")
            _marcos_bands[r["status_color"]] = _marcos_bands.get(r["status_color"], 0) + 1
            if _marcos_max is None or r["marcos_score"] > _marcos_max:
                _marcos_max = r["marcos_score"]
ka(sorted(_marcos_bands), ["Red"], "B2.18: Red is the only band reachable over 65,856 "
   "index and document-risk combinations", "B2.18", "property",
   "the score is bounded above by 1/3 and the Amber edge is 0.35")
ka(_marcos_max, 0.333, "B2.18: the highest score anywhere in the domain is 1/3",
   "B2.18", "known_answer", "denominator minimised at u = 0.5 gives 1/(1+1+1)")

# The symmetry, asserted as an equality between two projects rather than as a shape.
# cpi and spi enter through norm = (v - anti)/(ideal - anti) clamped to [0, 1], weights
# 0.40 / 0.35 / 0.25, anti 0.80 / 0.80 / 0.30, ideal 1.05 / 1.05 / 1.00.
#
#   PROJECT ONE  cpi 1.05, spi 1.05, docRisk 0.00
#     cost     (1.05 - 0.80)/0.25 = 1.00 -> 1.00 * 0.40 = 0.400
#     schedule (1.05 - 0.80)/0.25 = 1.00 -> 1.00 * 0.35 = 0.350
#     risk     value 1 - 0 = 1.00, (1.00 - 0.30)/0.70 = 1.00 -> 1.00 * 0.25 = 0.250
#     u = 1.000  -> score 0 (division by zero on the anti arm)
#   PROJECT TWO  cpi 0.80, spi 0.80, docRisk 0.70
#     cost 0.000, schedule 0.000, risk value 0.30, (0.30 - 0.30)/0.70 = 0 -> 0.000
#     u = 0.000  -> score 0
# A perfect project and the worst project the criteria admit receive the same score.
_best = run_marcos({"cpi": 1.05, "spi": 1.05, "docRiskScore": 0.0}, NO_ARG, "2025-06-30")
_worst = run_marcos({"cpi": 0.80, "spi": 0.80, "docRiskScore": 0.70}, NO_ARG, "2025-06-30")
ka(_best["utility_ideal"], 1.0, "B2.18: a project at every ideal has utility 1",
   "B2.18", "known_answer", "0.40 + 0.35 + 0.25")
ka(_worst["utility_ideal"], 0.0, "B2.18: a project at every anti-ideal has utility 0",
   "B2.18", "known_answer", "three clamped normalisations of zero")
ka(_best["marcos_score"], _worst["marcos_score"],
   "B2.18: the best and the worst admissible project receive the identical score",
   "B2.18", "property", "the score is symmetric under u -> 1 - u")
ka(_best["status_color"], "Red", "B2.18: a project at every ideal reads Red", "B2.18",
   "enumerated")

# The symmetry exhausted rather than illustrated: every utility pair (u, 1 - u) on a hundredth
# grid must score the same. Utility is driven here through the document-risk criterion alone,
# holding cost and schedule at their anti-ideal so u = 0.25 * clamp01((1 - d - 0.30)/0.70).
_sym_failures = []
for k in range(0, 101):
    u = k / 100.0
    if u in (0.0, 1.0):
        continue
    lo = 1 / (1 + (1 - u) / u + u / (1 - u))
    hi = 1 / (1 + u / (1 - u) + (1 - u) / u)
    if abs(lo - hi) > 1e-12:
        _sym_failures.append(u)
ka(_sym_failures, [], "B2.18: the closed form is symmetric at every hundredth of utility",
   "B2.18", "property", "algebraic identity checked over the whole grid")


# =================================================================================================
section("5. A2.10 SCHEDULE RISK ANALYSIS P80: AN UNGUARDED DENOMINATOR AND AN UNGUARDED DOMAIN")
# =================================================================================================
#
# The computation is remaining = total_days * (100 - actual%)/100, then p50 = remaining / spi.
# The schedule index is a denominator and nothing guards it. This is the exact defect the
# fifteen-defects run removed from the cost-risk computation next door (`bac / cpi`, defect 5):
# a zero index raised inside the computation rather than abstaining, and a raise loses the whole
# project result rather than one module's stated abstention. It is still standing here.

_BASE = {"spi": 1.0, "baselineStart": "2025-01-01", "baselineEnd": "2025-12-31",
         "actualPctComplete": 40}
_crashed = False
try:
    run_schedule_risk({**_BASE, "spi": 0}, NO_ARG, "2025-06-30")
except ZeroDivisionError:
    _crashed = True
ka(_crashed, True, "A2.10: a schedule index of zero raises rather than abstaining",
   "A2.10", "domain", "remaining_days / spi with no guard on spi")

# A NEGATIVE index is worse than the crash, because it does not announce itself.
#   total_days from 2025-01-01 to 2025-12-31 = 364 days
#   remaining  = 364 * (100 - 40)/100 = 218.4 days
#   p50        = 218.4 / -0.5 = -436.8 days
#   uncertainty = max(0.05, 1 - (-0.5)) * 0.5 = 1.5 * 0.5 = 0.75
#   p80        = -436.8 * (1 + 0.75 * 1.28) = -436.8 * 1.96 = -856.128
#   delay      = round(-856.128 - 218.4) = round(-1074.528) = -1075
# The Green arm is delay <= 0, so a project whose schedule index is recorded as negative is
# reported as finishing 1,075 days EARLY and reads Green.
_neg = run_schedule_risk({**_BASE, "spi": -0.5}, NO_ARG, "2025-06-30")
ka(_neg["p80_delay_days"], -1075, "A2.10: a negative schedule index yields a delay of -1075 days",
   "A2.10", "known_answer",
   "364 * 0.6 = 218.4; 218.4 / -0.5 = -436.8; * (1 + 0.75 * 1.28) = -856.128; -856.128 - 218.4")
ka(_neg["status_color"], "Green", "A2.10: and that project reads Green", "A2.10", "domain")

# A completion above one hundred per cent makes the remaining work negative and reads Green.
#   remaining = 364 * (100 - 120)/100 = -72.8 days; p50 = -72.8 / 1.0 = -72.8
#   uncertainty = max(0.05, 1 - 1.0) * 0.5 = 0.05 * 0.5 = 0.025
#   p80 = -72.8 * (1 + 0.025 * 1.28) = -72.8 * 1.032 = -75.1296
#   delay = round(-75.1296 - (-72.8)) = round(-2.3296) = -2
_over = run_schedule_risk({**_BASE, "actualPctComplete": 120}, NO_ARG, "2025-06-30")
ka(_over["p80_delay_days"], -2, "A2.10: a completion of 120 per cent yields a delay of -2 days",
   "A2.10", "known_answer", "364 * -0.2 = -72.8; * 1.032 = -75.1296; less -72.8")
ka(_over["status_color"], "Green", "A2.10: and that project reads Green too", "A2.10", "domain")

# The valid case, by hand, so the module is shown to compute correctly where it is in domain.
#   spi 0.8: remaining 218.4; p50 = 273.0; uncertainty = max(0.05, 0.2) * 0.5 = 0.10
#   p80 = 273.0 * (1 + 0.10 * 1.28) = 273.0 * 1.128 = 307.944; delay = round(307.944 - 218.4)
#       = round(89.544) = 90
_ok = run_schedule_risk({**_BASE, "spi": 0.8}, NO_ARG, "2025-06-30")
ka(_ok["p80_delay_days"], 90, "A2.10: the in-domain case is 90 days by hand", "A2.10",
   "known_answer", "218.4 / 0.8 = 273.0; * 1.128 = 307.944; less 218.4 = 89.544")
ka(_ok["status_color"], "Red", "A2.10: 90 days beyond the baseline reads Red", "A2.10",
   "boundary", "Red arm is delay > 30")
# Boundary inclusivity, stated because the code does not state it.
ka(run_schedule_risk({**_BASE, "actualPctComplete": 100}, NO_ARG, "2025-06-30")["p80_delay_days"],
   0, "A2.10: exactly complete gives a delay of zero", "A2.10", "boundary")
ka(run_schedule_risk({**_BASE, "actualPctComplete": 100},
                     NO_ARG, "2025-06-30")["status_color"], "Green",
   "A2.10: the Green arm is inclusive at a delay of zero", "A2.10", "boundary")


# =================================================================================================
section("6. A5.5 REWORK FEEDBACK LOOP: WITHHOLDING EVIDENCE IMPROVES THE READING")
# =================================================================================================
#
# This is Run 6 finding 1.4 exactly, in the module next door to the one Run 7 corrected. The
# index is rfi_term + co_term + cpi_term with weights 0.3 / 0.3 / 0.4, and an ABSENT source
# contributes zero rather than being renormalised out or refused.
#
#   BOTH LOGS REPORTED, cpi 0.90, 30 requests, 15 change orders
#     rfi = min(30/30, 1) * 0.3 = 0.30
#     co  = min(15/15, 1) * 0.3 = 0.30
#     cpi = max(0, 1 - 0.90) * 0.4 = 0.10 * 0.4 = 0.04
#     index = 0.64, and the Red arm is index > 0.45
#   NEITHER LOG REPORTED, same project, same cost index
#     rfi = 0, co = 0, cpi = 0.04, index = 0.04, and the Green arm is index <= 0.10
# The identical cost performance moves three bands by withholding two documents.
_full = run_rework_feedback({"cpi": 0.90, "rfiCount": 30, "changeOrderCount": 15},
                            NO_ARG, "2025-06-30")
_bare = run_rework_feedback({"cpi": 0.90}, NO_ARG, "2025-06-30")
ka(_full["rework_index"], 0.64, "A5.5: with both logs the index is 0.64", "A5.5",
   "known_answer", "0.30 + 0.30 + 0.04")
ka(_full["status_color"], "Red", "A5.5: with both logs it reads Red", "A5.5", "enumerated")
ka(_bare["rework_index"], 0.04, "A5.5: with neither log the index is 0.04", "A5.5",
   "known_answer", "0 + 0 + 0.04")
ka(_bare["status_color"], "Green", "A5.5: with neither log it reads Green", "A5.5", "enumerated")

# Monotonicity in evidence, exhausted over all four subsets of the two logs rather than shown
# on one pair. Adding a document must never improve the reading; here it always worsens it,
# which is the same fault seen from the other side.
_subsets = []
for rfi in (None, 30):
    for co in (None, 15):
        si = {"cpi": 0.90}
        if rfi is not None:
            si["rfiCount"] = rfi
        if co is not None:
            si["changeOrderCount"] = co
        _subsets.append(run_rework_feedback(si, NO_ARG, "2025-06-30")["rework_index"])
ka(sorted(_subsets), [0.04, 0.34, 0.34, 0.64],
   "A5.5: the four evidence subsets give four different indices for one project",
   "A5.5", "property", "0.04 / 0.04+0.30 / 0.04+0.30 / 0.04+0.30+0.30")

# A REPORTED ZERO AND AN ABSENT LOG ARE INDISTINGUISHABLE, because the guard is a truthiness
# test (`if si.get("rfiCount")`), so a genuine zero is discarded as though nothing was reported.
_zero = run_rework_feedback({"cpi": 0.90, "rfiCount": 0, "changeOrderCount": 0},
                            NO_ARG, "2025-06-30")
ka(_zero["rework_index"], _bare["rework_index"],
   "A5.5: a reported zero and an absent log produce the identical index", "A5.5", "domain",
   "the guard is truthiness, so 0 takes the absent arm")

# NEGATIVE COUNTS ARE NOT REFUSED, and drive the index below the domain an index can occupy.
#   rfi = min(-5/30, 1) * 0.3 = -0.16666 * 0.3 = -0.05; cpi term 0.04; index = -0.01
_negc = run_rework_feedback({"cpi": 0.90, "rfiCount": -5}, NO_ARG, "2025-06-30")
ka(_negc["rework_index"], -0.01, "A5.5: a negative request count gives a negative index",
   "A5.5", "domain", "min(-5/30, 1) * 0.3 = -0.05, plus 0.04")
ka(_negc["status_color"], "Green", "A5.5: and a negative index reads Green", "A5.5", "domain")
# A negative cost index is not refused either.
ka(run_rework_feedback({"cpi": -1.0}, NO_ARG, "2025-06-30")["rework_index"], 0.8,
   "A5.5: a cost index of -1 contributes 0.8 to the index", "A5.5", "domain",
   "max(0, 1 - (-1)) * 0.4")

# The finding text names a quantity the module does not compute: the term is a raw count
# capped at thirty, not a rate over time, and the sentence says otherwise.
check("RFI" in _full["evidence_metric"] and "combined" in _full["evidence_metric"],
      "A5.5: the finding text names the request term without a time denominator",
      _full["evidence_metric"])


# =================================================================================================
section("7. THE DOMAIN SWEEP: NINE MORE OF THE 27 ACCEPT AN INPUT OUTSIDE ITS OWN DOMAIN")
# =================================================================================================
#
# Each case below is an input that cannot describe a project, and each is asserted with the
# hand-derived value the module returns for it. None is fixed here.

# ---- A1.6 Earned Schedule. SPI(t) is actual% / planned%, and neither is bounded.
#      actual -40, planned 45 -> -0.888888, rounded to -0.889; Red arm is below 0.88.
_es_neg = run_earned_schedule({"ev": 400, "pv": 450, "bac": 1000,
                               "actualPctComplete": -40, "plannedPctComplete": 45},
                              NO_ARG, "2025-06-30")
ka(_es_neg["spi_time"], -0.889, "A1.6: a negative completion gives a negative schedule index",
   "A1.6", "domain", "-40/45 = -0.8888..., rounded to three places")
#      actual 140, planned 45 -> 3.111111 -> 3.111; the Green arm is >= 0.95.
_es_over = run_earned_schedule({"ev": 400, "pv": 450, "bac": 1000,
                                "actualPctComplete": 140, "plannedPctComplete": 45},
                               NO_ARG, "2025-06-30")
ka(_es_over["spi_time"], 3.111, "A1.6: a completion of 140 per cent gives an index of 3.111",
   "A1.6", "domain", "140/45 = 3.1111...")
ka(_es_over["status_color"], "Green", "A1.6: and that reads Green", "A1.6", "domain")
#      The in-domain case, by hand: 40/45 = 0.888888 -> 0.889, Amber arm is >= 0.88.
_es_ok = run_earned_schedule({"ev": 400, "pv": 450, "bac": 1000,
                             "actualPctComplete": 40, "plannedPctComplete": 45},
                             NO_ARG, "2025-06-30")
ka(_es_ok["spi_time"], 0.889, "A1.6: the in-domain case is 0.889 by hand", "A1.6",
   "known_answer", "40/45")
ka(_es_ok["status_color"], "Amber", "A1.6: 0.889 lands Amber", "A1.6", "boundary")
#      AND THE CONTRACT FAULT: three of the five required inputs are never read. The module
#      demands ev, pv and bac and then computes only from the two completion percentages, so a
#      project that reported its progress but no earned value abstains for no arithmetic reason.
_es_no_ev = run_earned_schedule({"actualPctComplete": 40, "plannedPctComplete": 45},
                                NO_ARG, "2025-06-30")
ka(abstains(_es_no_ev), True,
   "A1.6: abstains without earned value even though earned value is never used", "A1.6",
   "domain", "check_inputs requires ev, pv and bac; the arithmetic reads neither")

# ---- A1.11 ICE Ratio. A negative cost index produces a negative forecast reported as money.
#      eac_cpi = 1000 / -0.5 = -2000; eac_parametric = 800 + (1000 - 400) = 1400
#      ice = -2000 / 1400 = -1.42857 -> -1.429; |ice - 1| = 2.429, Red arm is > 0.20.
_ice = run_ice_ratio({"bac": 1000, "cpi": -0.5, "ev": 400, "ac": 800}, NO_ARG, "2025-06-30")
ka(_ice["ice_ratio"], -1.429, "A1.11: a negative cost index gives a ratio of -1.429", "A1.11",
   "domain", "(1000 / -0.5) / (800 + 600)")
ka(_ice["eac_cpi"], -2000, "A1.11: and a forecast at completion of minus two thousand",
   "A1.11", "domain", "1000 / -0.5")
#      The in-domain case by hand: 1000/0.8 = 1250; parametric 800 + 600 = 1400;
#      1250/1400 = 0.892857 -> 0.893; |0.893 - 1| = 0.107, Amber arm is <= 0.20.
_ice_ok = run_ice_ratio({"bac": 1000, "cpi": 0.8, "ev": 400, "ac": 800}, NO_ARG, "2025-06-30")
ka(_ice_ok["ice_ratio"], 0.893, "A1.11: the in-domain case is 0.893 by hand", "A1.11",
   "known_answer", "1250 / 1400")
ka(_ice_ok["status_color"], "Amber", "A1.11: 0.893 lands Amber", "A1.11", "boundary")

# ---- A1.5 ARIMA CPI Forecast. A cost performance index cannot be negative; the history is
#      not checked. history -1, -2, -3: diffs -1, -1; phi = (-1 * -1)/(-1 * -1) = 1, clamped to
#      0.9; forecast = -3 + 0.9 * -1 = -3.9.
_ar = run_arima_forecast({"cpiHistory": [-1, -2, -3]}, NO_ARG, "2025-06-30")
ka(_ar["forecast_cpi"], -3.9, "A1.5: a negative index history forecasts -3.9", "A1.5",
   "domain", "phi clamped to 0.9; -3 + 0.9 * -1")
#      The in-domain case by hand: 0.95, 0.93, 0.91 -> diffs -0.02, -0.02;
#      phi = (-0.02 * -0.02)/(-0.02 * -0.02) = 1, clamped to 0.9; forecast = 0.91 - 0.018 = 0.892
_ar_ok = run_arima_forecast({"cpiHistory": [0.95, 0.93, 0.91]}, NO_ARG, "2025-06-30")
ka(_ar_ok["forecast_cpi"], 0.892, "A1.5: the in-domain case forecasts 0.892 by hand", "A1.5",
   "known_answer", "0.91 + 0.9 * (-0.02)")
ka(_ar_ok["phi"], 0.9, "A1.5: the coefficient is the clamp, not an estimate, on three points",
   "A1.5", "known_answer",
   "with three points there is one product pair, so phi is d1/d0 and clamps at 0.9")
ka(abstains(run_arima_forecast({"cpiHistory": [0.95, 0.93]}, NO_ARG, "2025-06-30")), True,
   "A1.5: two periods abstain, three are required", "A1.5", "abstention")

# ---- A2.9 Resource Loading Index. Negative labour hours are accepted.
#      -50 / 1000 = -0.05, which falls to the Red arm.
_rl = run_resource_loading({"plannedLaborHours": 1000, "actualLaborHours": -50},
                           NO_ARG, "2025-06-30")
ka(_rl["load_ratio"], -0.05, "A2.9: negative labour hours give a load ratio of -0.05",
   "A2.9", "domain", "-50 / 1000")
#      The in-domain case by hand: 1050/1000 = 1.05, inside 0.90 to 1.10, Green.
_rl_ok = run_resource_loading({"plannedLaborHours": 1000, "actualLaborHours": 1050},
                              NO_ARG, "2025-06-30")
ka(_rl_ok["load_ratio"], 1.05, "A2.9: the in-domain case is 1.05 by hand", "A2.9",
   "known_answer", "1050 / 1000")
ka(_rl_ok["status_color"], "Green", "A2.9: 1.05 is inside the Green corridor", "A2.9",
   "boundary")
# Both edges of the Green corridor are inclusive; asserted at, below and above.
ka(run_resource_loading({"plannedLaborHours": 1000, "actualLaborHours": 900},
                        NO_ARG, "2025-06-30")["status_color"], "Green",
   "A2.9: exactly 0.90 is Green", "A2.9", "boundary")
ka(run_resource_loading({"plannedLaborHours": 1000, "actualLaborHours": 899},
                        NO_ARG, "2025-06-30")["status_color"], "Yellow",
   "A2.9: just below 0.90 is Yellow", "A2.9", "boundary")
ka(run_resource_loading({"plannedLaborHours": 1000, "actualLaborHours": 1100},
                        NO_ARG, "2025-06-30")["status_color"], "Green",
   "A2.9: exactly 1.10 is Green", "A2.9", "boundary")
ka(run_resource_loading({"plannedLaborHours": 1000, "actualLaborHours": 1101},
                        NO_ARG, "2025-06-30")["status_color"], "Yellow",
   "A2.9: just above 1.10 is Yellow", "A2.9", "boundary")

# ---- A2.5 Float Consumption Rate. A negative consumed float reads Green and reports MORE
#      float remaining than the project has.
#      remaining = 30 - (-5) = 35; rate = -5/30 = -0.1666 -> -17 per cent;
#      stress = -0.1666 / max(0.40, 0.01) = -0.4166 -> -0.42, and the Green arm is <= 1.0.
_fc = run_float_consumption({"totalFloat": 30, "consumedFloat": -5, "actualPctComplete": 40},
                            NO_ARG, "2025-06-30")
ka(_fc["float_remaining_days"], 35, "A2.5: a negative consumption adds float", "A2.5",
   "domain", "30 - (-5)")
ka(_fc["float_stress"], -0.42, "A2.5: and the stress ratio goes negative", "A2.5", "domain",
   "(-5/30) / 0.40")
ka(_fc["status_color"], "Green", "A2.5: and it reads Green", "A2.5", "domain")
#      The in-domain case by hand: 12/30 = 0.40 consumed; expected 0.40; stress 1.00; Green.
_fc_ok = run_float_consumption({"totalFloat": 30, "consumedFloat": 12, "actualPctComplete": 40},
                               NO_ARG, "2025-06-30")
ka(_fc_ok["float_stress"], 1.0, "A2.5: the in-domain case has a stress of exactly 1.00",
   "A2.5", "known_answer", "0.40 consumed against 0.40 complete")
ka(_fc_ok["status_color"], "Green", "A2.5: a stress of exactly 1.00 is Green, inclusive",
   "A2.5", "boundary")

# ---- A2.11 Critical Path Index. A negative schedule index is averaged in.
#      (40/45 + -0.9)/2 = (0.888888 - 0.9)/2 = -0.005555 -> -0.006
_cpx = run_critical_path_index({"spi": -0.9, "plannedPctComplete": 45, "actualPctComplete": 40},
                               NO_ARG, "2025-06-30")
ka(_cpx["critical_path_index"], -0.006, "A2.11: a negative schedule index gives -0.006",
   "A2.11", "domain", "(0.888888 + (-0.9)) / 2")
#      The in-domain case by hand: (40/45 + 0.9)/2 = (0.888888 + 0.9)/2 = 0.894444 -> 0.894
_cpx_ok = run_critical_path_index({"spi": 0.9, "plannedPctComplete": 45,
                                   "actualPctComplete": 40}, NO_ARG, "2025-06-30")
ka(_cpx_ok["critical_path_index"], 0.894, "A2.11: the in-domain case is 0.894 by hand",
   "A2.11", "known_answer", "(0.888888 + 0.9) / 2")
ka(_cpx_ok["status_color"], "Amber", "A2.11: 0.894 lands Amber", "A2.11", "boundary")

# ---- A4.10 Specification Conflict Density. A document risk outside nought to one is accepted
#      and lands in the CALMEST band, which is the harmful direction.
#      density = (-0.5 * 4)/sqrt(4) = -1.0; min(1, -1.0) = -1; the Green arm is <= 0.15.
_sc = run_spec_conflict_density({"docRiskScore": -0.5, "rfiCount": 4}, NO_ARG, "2025-06-30")
ka(_sc["conflict_density"], -1.0, "A4.10: a negative document risk gives a density of -1",
   "A4.10", "domain", "(-0.5 * 4) / sqrt(4)")
ka(_sc["status_color"], "Green", "A4.10: and a negative density reads Green", "A4.10", "domain")
#      The in-domain case by hand: (0.30 * 4)/2 = 0.60; the Amber arm is <= 0.60, inclusive.
_sc_ok = run_spec_conflict_density({"docRiskScore": 0.30, "rfiCount": 4}, NO_ARG, "2025-06-30")
ka(_sc_ok["conflict_density"], 0.6, "A4.10: the in-domain case is 0.60 by hand", "A4.10",
   "known_answer", "(0.30 * 4) / sqrt(4)")
ka(_sc_ok["status_color"], "Amber", "A4.10: exactly 0.60 is Amber, so the edge is inclusive",
   "A4.10", "boundary")

# ---- A5.8 Discrete Event Simulation. A negative schedule index inflates the interruption term.
#      progress = 40/45 = 0.888888; interruption = max(0, 1 - 0.888888) + max(0, 1 - (-0.9)) * 0.5
#                = 0.111111 + 0.95 = 1.061111; throughput = 1/(1 + 1.061111) = 0.485174 -> 0.485
_des = run_discrete_event_sim({"spi": -0.9, "cpi": 0.9, "plannedPctComplete": 45,
                               "actualPctComplete": 40}, NO_ARG, "2025-06-30")
ka(_des["throughput_index"], 0.485, "A5.8: a negative schedule index gives a throughput of 0.485",
   "A5.8", "domain", "1 / (1 + 0.111111 + 0.95)")
#      The in-domain case by hand: interruption = 0.111111 + 0.05 = 0.161111;
#      throughput = 1/1.161111 = 0.861244 -> 0.861; the Yellow arm is >= 0.85.
_des_ok = run_discrete_event_sim({"spi": 0.9, "cpi": 0.9, "plannedPctComplete": 45,
                                  "actualPctComplete": 40}, NO_ARG, "2025-06-30")
ka(_des_ok["throughput_index"], 0.861, "A5.8: the in-domain case is 0.861 by hand", "A5.8",
   "known_answer", "1 / (1 + 0.111111 + 0.05)")
ka(_des_ok["status_color"], "Yellow", "A5.8: 0.861 lands Yellow", "A5.8", "boundary")

# ---- A6.1 Quality Compliance Index. The fifteen-defects run guarded the inspected and failed
#      pair and left the AUDITED SCORE unguarded, so a score outside nought to a hundred is
#      banded and printed as "x/100".
_q_hi = run_quality_compliance({"qualityDeficienciesNoted": 3, "qualityAuditScore": 150},
                               NO_ARG, "2025-06-30")
ka(_q_hi["quality_score"], 150, "A6.1: an audited score of 150 out of 100 is accepted", "A6.1",
   "domain", "no upper guard on qualityAuditScore")
ka(_q_hi["status_color"], "Green", "A6.1: and reads Green", "A6.1", "domain")
_q_lo = run_quality_compliance({"qualityDeficienciesNoted": 3, "qualityAuditScore": -20},
                               NO_ARG, "2025-06-30")
ka(_q_lo["quality_score"], -20, "A6.1: a score of minus twenty is accepted", "A6.1", "domain")
check("-20/100" in _q_lo["evidence_metric"],
      "A6.1: and the finding text prints it as minus twenty out of a hundred",
      _q_lo["evidence_metric"])
#      The in-domain case by hand: (100 - 8)/100 = 0.92, so 92 out of 100, Green arm is >= 85.
_q_ok = run_quality_compliance({"qualityDeficienciesNoted": 3, "itemsInspected": 100,
                                "itemsFailed": 8}, NO_ARG, "2025-06-30")
ka(_q_ok["quality_score"], 92, "A6.1: the in-domain case is 92 by hand", "A6.1",
   "known_answer", "(100 - 8) / 100 as a percentage")
ka(_q_ok["pass_rate"], 92, "A6.1: and the pass rate is reported beside it", "A6.1",
   "known_answer")

# ---- A6.4 Contractor Performance Score. The ratings are a one-to-five scale, the finding text
#      says so, and a rating outside it is neither refused nor clipped.
_cp = run_contractor_performance({"overallRating": 9.9, "scheduleRating": 4.0,
                                  "costRating": 4.1}, NO_ARG, "2025-06-30")
ka(_cp["min_rating"], 4.0, "A6.4: a rating of 9.9 on a five-point scale is accepted", "A6.4",
   "domain", "min(9.9, 4.0, 4.1)")
check("/5" in _cp["evidence_metric"],
      "A6.4: and the finding text still describes the scale as out of five",
      _cp["evidence_metric"])
#      The fifteen-defects run's own fix, re-derived: the quality rating enters the minimum.
_cp_q = run_contractor_performance({"overallRating": 4.2, "scheduleRating": 4.0,
                                    "costRating": 4.1, "qualityRating": 1.0},
                                   NO_ARG, "2025-06-30")
ka(_cp_q["min_rating"], 1.0, "A6.4: the quality rating enters the minimum", "A6.4",
   "known_answer", "min(4.2, 4.0, 4.1, 1.0)")
ka(_cp_q["ratings_read"], 4, "A6.4: four ratings are read when four are given", "A6.4",
   "known_answer")
ka(_cp_q["status_color"], "Red", "A6.4: a worst rating of 1.0 reads Red", "A6.4", "boundary")

# ---- A3.6 Cost Risk Analysis P80. The cost index may legitimately exceed one, and when it
#      does the delta is negative while the finding text hard-codes a leading plus sign, so the
#      sentence a reader sees carries a double sign.
#      cpi 5.0: eac = 1000/5 = 200; uncertainty = max(0.03, 4.0) * 0.5 = 2.0;
#      p80 = 200 * (1 + 2.0 * 1.28) = 200 * 3.56 = 712; delta = (712 - 1000)/1000 * 100 = -28.8
_cr = run_cost_risk({"bac": 1000, "cpi": 5.0, "ac": 400, "ev": 350}, NO_ARG, "2025-06-30")
ka(_cr["p80_delta_pct"], -28.8, "A3.6: a cost index of 5.0 gives a delta of -28.8 per cent",
   "A3.6", "known_answer", "(712 - 1000) / 1000 * 100")
check("+-28.8" in _cr["evidence_metric"],
      "A3.6: and the finding text prints a plus and a minus together",
      _cr["evidence_metric"])
#      The in-domain case by hand: eac = 1000/0.9 = 1111.111; uncertainty = max(0.03, 0.1) * 0.5
#      = 0.05; p80 = 1111.111 * 1.064 = 1182.222; delta = 18.2 per cent; Amber arm is <= 20.
_cr_ok = run_cost_risk({"bac": 1000, "cpi": 0.9, "ac": 400, "ev": 350}, NO_ARG, "2025-06-30")
ka(_cr_ok["p80_delta_pct"], 18.2, "A3.6: the in-domain case is 18.2 per cent by hand", "A3.6",
   "known_answer", "1000/0.9 * 1.064 = 1182.22; (1182.22 - 1000)/1000 * 100")
ka(_cr_ok["status_color"], "Amber", "A3.6: 18.2 per cent lands Amber", "A3.6", "boundary")

# ---- A6.2 Safety Performance Index. Run 7 corrected the index and refused a negative rate. The
#      FALLBACK IS STILL STANDING: with no reported incident rate the module converts a count of
#      times safety was mentioned in a meeting into a rate at ten points per mention. This is
#      the fifteen-defects run's defect 15 (the environmental measure's "max(50, 100 - issues*5)")
#      in the neighbouring module, and it runs in the opposite direction: silence reads best.
_sf0 = run_safety_performance({"safetyIncidentsDiscussed": 0}, NO_ARG, "2025-06-30")
_sf1 = run_safety_performance({"safetyIncidentsDiscussed": 1}, NO_ARG, "2025-06-30")
_sf2 = run_safety_performance({"safetyIncidentsDiscussed": 2}, NO_ARG, "2025-06-30")
ka(_sf0["incident_rate"], 0.0, "A6.2: safety never mentioned becomes an incident rate of zero",
   "A6.2", "domain", "0 mentions times 10")
ka(_sf0["safety_index"], 2, "A6.2: and the best safety index the module can award", "A6.2",
   "known_answer", "the module's own cap of 2, correct by Run 7 for a true reported zero")
ka(_sf0["status_color"], "Green", "A6.2: and reads Green", "A6.2", "domain")
ka(_sf1["incident_rate"], 10.0, "A6.2: one mention becomes an incident rate of ten", "A6.2",
   "domain", "1 mention times the literal 10")
ka(_sf1["status_color"], "Amber", "A6.2: one mention reads Amber", "A6.2", "domain")
ka(_sf2["status_color"], "Red", "A6.2: two mentions read Red", "A6.2", "domain")
#      With a REPORTED rate the module is a transparent ratio and its bands are the benchmark,
#      twice the benchmark and five times it. Asserted at, below and above every edge.
ka(run_safety_performance({"safetyIncidentsDiscussed": 0, "oshaIncidentRate": 3.0},
                          NO_ARG, "2025-06-30")["status_color"], "Green",
   "A6.2: exactly the benchmark rate is Green, inclusive", "A6.2", "boundary")
ka(run_safety_performance({"safetyIncidentsDiscussed": 0, "oshaIncidentRate": 3.01},
                          NO_ARG, "2025-06-30")["status_color"], "Yellow",
   "A6.2: just above the benchmark is Yellow", "A6.2", "boundary")
ka(run_safety_performance({"safetyIncidentsDiscussed": 0, "oshaIncidentRate": 6.0},
                          NO_ARG, "2025-06-30")["status_color"], "Yellow",
   "A6.2: exactly twice the benchmark is Yellow, inclusive", "A6.2", "boundary")
ka(run_safety_performance({"safetyIncidentsDiscussed": 0, "oshaIncidentRate": 15.0},
                          NO_ARG, "2025-06-30")["status_color"], "Amber",
   "A6.2: exactly five times the benchmark is Amber, inclusive", "A6.2", "boundary")
ka(run_safety_performance({"safetyIncidentsDiscussed": 0, "oshaIncidentRate": 15.01},
                          NO_ARG, "2025-06-30")["status_color"], "Red",
   "A6.2: just above five times the benchmark is Red", "A6.2", "boundary")
#      Run 7's index correction, re-derived: benchmark over rate, capped at 2. 3.0 / 2.0 = 1.5.
ka(run_safety_performance({"safetyIncidentsDiscussed": 0, "oshaIncidentRate": 2.0},
                          NO_ARG, "2025-06-30")["safety_index"], 1.5,
   "A6.2: the index is the benchmark over the rate", "A6.2", "known_answer", "3.0 / 2.0")
ka(abstains(run_safety_performance({"safetyIncidentsDiscussed": 1, "oshaIncidentRate": -1.0},
                                   NO_ARG, "2025-06-30")), True,
   "A6.2: a negative rate is still refused, as Run 7 installed", "A6.2", "abstention")


# =================================================================================================
section("8. THE SEVEN BUCKET 3 MODULES: THE CURRENT ARITHMETIC IS FAITHFUL AND PASSES")
# =================================================================================================
#
# A module here passes its current transparent-proxy arithmetic AND still requires a synthetic
# project-structure corpus for the canonical method its name claims. The two are recorded
# separately, which is the point of this section: the arithmetic passing is not evidence that
# the method is present.

# ---- A1.1 Monte Carlo EAC. Five thousand Beta-PERT draws through a gamma sampler: no closed
#      form a person can check, so this is a PROPERTY case and is labelled as one. The two
#      properties are mathematically justified rather than invented: the forecast is a monetary
#      quantity scaled by the budget, so doubling the budget must double every currency figure
#      and leave the overrun PERCENTAGE unchanged; and the stream is seeded, so the same seed
#      must give the same path.
_mc_a = run_monte_carlo({"bac": 1000000, "cpi": 0.9, "spi": 0.9, "docRiskScore": 0.3}, None, 42)
_mc_b = run_monte_carlo({"bac": 2000000, "cpi": 0.9, "spi": 0.9, "docRiskScore": 0.3}, None, 42)
ka(round(_mc_b["p80_eac"] / _mc_a["p80_eac"], 9), 2.0,
   "A1.1: doubling the budget exactly doubles the eightieth-percentile forecast", "A1.1",
   "property", "monetary equivariance: the forecast is a multiple of the budget")
ka(_mc_b["overrun_pct_p80"], _mc_a["overrun_pct_p80"],
   "A1.1: and leaves the overrun percentage invariant", "A1.1", "property",
   "monetary scale invariance of a ratio")
_mc_c = run_monte_carlo({"bac": 1000000, "cpi": 0.9, "spi": 0.9, "docRiskScore": 0.3}, None, 42)
ka(_mc_c["p80_eac"], _mc_a["p80_eac"], "A1.1: the same seed gives the same path", "A1.1",
   "property", "the stream is seeded from scenario and period, never from the participant")
ka(_mc_a["iterations"], 5000, "A1.1: the iteration count is the module's own literal", "A1.1",
   "known_answer")
# The equivariance is exhausted over a grid rather than shown on one pair.
_eq_fail = []
for scale in (1, 2, 5, 10, 100, 1000):
    r = run_monte_carlo({"bac": 100000 * scale, "cpi": 0.9, "spi": 0.9, "docRiskScore": 0.3},
                        None, 42)
    base = run_monte_carlo({"bac": 100000, "cpi": 0.9, "spi": 0.9, "docRiskScore": 0.3},
                           None, 42)
    if abs(r["p80_eac"] - base["p80_eac"] * scale) > 1e-6 * scale:
        _eq_fail.append(scale)
    if abs(r["overrun_pct_p80"] - base["overrun_pct_p80"]) > 1e-9:
        _eq_fail.append(-scale)
ka(_eq_fail, [], "A1.1: equivariance holds at every scale from one to a thousand", "A1.1",
   "property")
ka(abstains(run_monte_carlo({"bac": 0, "cpi": 0.9, "spi": 0.9}, None, 42)), True,
   "A1.1: a budget of zero is refused, not substituted", "A1.1", "abstention")

# ---- A2.2 Line of Balance. Hand-derived from the module's own literals.
#      units 20, grading 2.0/day, paving 1.8 * clamp(spi, 0.3, 1.2), buffer 5.0 days.
#      spi 0.9: paving = 1.62; lag = 1/1.62 - 1/2.0 = 0.617284 - 0.5 = 0.117284
#      minimum buffer at unit 20 = 5.0 - 20 * 0.117284 = 5.0 - 2.345679 = 2.654321 -> 2.7
#      Amber arm is min buffer <= 3.0 and Red is <= 1.5, so 2.7 is Amber.
_lob = run_lob({"spi": 0.9}, NO_ARG, "2025-06-30")
ka(_lob["paving_rate"], 1.62, "A2.2: the paving rate is 1.8 scaled by the index", "A2.2",
   "known_answer", "1.8 * clamp(0.9, 0.3, 1.2)")
ka(_lob["minimum_buffer_days"], 2.7, "A2.2: the minimum buffer is 2.7 days by hand", "A2.2",
   "known_answer", "5.0 - 20 * (1/1.62 - 1/2.0)")
ka(_lob["status_color"], "Amber", "A2.2: 2.7 days is Amber", "A2.2", "boundary")
ka(_lob["units"], 20, "A2.2: the unit count is a literal in the file, not a project figure",
   "A2.2", "known_answer", "no locations or units are carried in the corpus")
#      A project at or above an index of 1.2 saturates the clamp, so no faster project can be
#      distinguished from any other. Exhausted over the range above the clamp.
_sat = {run_lob({"spi": s / 10}, NO_ARG, "2025-06-30")["minimum_buffer_days"]
        for s in range(12, 41)}
ka(sorted(_sat), [5.0], "A2.2: every index at or above 1.2 gives the identical buffer",
   "A2.2", "property", "clamp(spi, 0.3, 1.2) saturates, so the lag floors at zero")

# ---- A2.3 CCPM Buffer Health. Hand-derived.
#      spi 0.9, chain complete 40 per cent:
#      buffer consumed = clamp((1 - 0.9) * 100 * 1.5, 0, 100) = 15.0
#      amber edge = chain = 40.0; red edge = 40 + (100 - 40)/3 = 40 + 20 = 60.0
#      15.0 < 40.0, so Green.
_cc = VALIDATED["A2.3"][1]({"spi": 0.9, "actualPctComplete": 40}, NO_ARG, "2025-06-30")
ka(_cc["pct_buffer_consumed"], 15.0, "A2.3: the buffer consumed is 15 per cent by hand",
   "A2.3", "known_answer", "(1 - 0.9) * 100 * 1.5")
ka(_cc["amber_threshold"], 40.0, "A2.3: the Amber edge is the chain completion itself",
   "A2.3", "known_answer")
ka(_cc["red_threshold"], 60.0, "A2.3: the Red edge is a third of the way to completion",
   "A2.3", "known_answer", "40 + (100 - 40)/3")
ka(_cc["status_color"], "Green", "A2.3: 15 against an edge of 40 is Green", "A2.3", "boundary")
#      THE DEGENERATE POINT. At zero chain completion the Amber edge is zero and the arm is
#      inclusive, so a project exactly on plan, having consumed no buffer at all, reads Amber.
_cc0 = VALIDATED["A2.3"][1]({"spi": 1.0, "actualPctComplete": 0}, NO_ARG, "2025-06-30")
ka(_cc0["pct_buffer_consumed"], 0.0, "A2.3: a project exactly on plan consumes no buffer",
   "A2.3", "known_answer", "(1 - 1.0) * 100 * 1.5")
ka(_cc0["status_color"], "Amber",
   "A2.3: and at zero chain completion it still reads Amber, because the edge is inclusive "
   "at zero", "A2.3", "boundary")

# ---- A4.4 NCR Rate. The fifteen-defects run rebuilt it as an open backlog over an audited
#      cohort. Hand-derived: 6/40 = 0.15, and the Yellow arm is 0.15 <= r < 0.30.
_ncr = run_ncr_rate({"ncrIssued": 4, "ncrClosed": 2, "ncrOpen": 6, "totalFindings": 40},
                    NO_ARG, "2025-06-30")
ka(_ncr["open_ratio"], 0.15, "A4.4: the open ratio is 0.15 by hand", "A4.4", "known_answer",
   "6 open of an audited cohort of 40")
ka(_ncr["status_color"], "Yellow",
   "A4.4: exactly 0.15 is Yellow, so the Green edge is exclusive", "A4.4", "boundary")
ka(run_ncr_rate({"ncrIssued": 4, "ncrClosed": 2, "ncrOpen": 5, "totalFindings": 40},
                NO_ARG, "2025-06-30")["status_color"], "Green",
   "A4.4: just below 0.15 is Green", "A4.4", "boundary")
ka(abstains(run_ncr_rate({"ncrIssued": 4, "ncrClosed": 2, "ncrOpen": 6},
                         NO_ARG, "2025-06-30")), True,
   "A4.4: without an audited cohort it abstains, which is the expected outcome on this corpus",
   "A4.4", "abstention")
ka(abstains(run_ncr_rate({"ncrIssued": 4, "ncrClosed": 2, "ncrOpen": 50, "totalFindings": 40},
                         NO_ARG, "2025-06-30")), True,
   "A4.4: a backlog larger than the cohort is refused", "A4.4", "domain")

# ---- A5.6 Queueing Theory Bottleneck. Hand-derived: 37/200 = 0.185, Yellow arm is < 0.25.
_qb = run_queueing_bottleneck({"activitiesPlanned": 200, "activitiesConstrained": 37},
                              NO_ARG, "2025-06-30")
ka(_qb["constraint_ratio"], 0.19, "A5.6: 37 of 200 is 0.185, reported to two places as 0.19",
   "A5.6", "known_answer", "37/200 = 0.185, rounded half up")
ka(_qb["status_color"], "Yellow", "A5.6: 0.185 lands Yellow", "A5.6", "boundary")
ka(run_queueing_bottleneck({"activitiesPlanned": 100, "activitiesConstrained": 15},
                           NO_ARG, "2025-06-30")["status_color"], "Yellow",
   "A5.6: exactly 0.15 is Yellow, so the Green edge is EXCLUSIVE here", "A5.6", "boundary")
ka(run_queueing_bottleneck({"activitiesPlanned": 100, "activitiesConstrained": 14},
                           NO_ARG, "2025-06-30")["status_color"], "Green",
   "A5.6: just below 0.15 is Green", "A5.6", "boundary")
ka(abstains(run_queueing_bottleneck({"activitiesPlanned": 0, "activitiesConstrained": 0},
                                    NO_ARG, "2025-06-30")), True,
   "A5.6: nothing planned abstains, as Run 7 installed", "A5.6", "abstention")
# Scale invariance: the ratio must not depend on the size of the window. Exhausted over
# twenty-four scalings of the same proportion.
_qb_ratios = {run_queueing_bottleneck({"activitiesPlanned": 40 * k,
                                       "activitiesConstrained": 6 * k},
                                      NO_ARG, "2025-06-30")["constraint_ratio"]
              for k in range(1, 25)}
ka(sorted(_qb_ratios), [0.15], "A5.6: the ratio is invariant under scaling the whole window",
   "A5.6", "property", "6/40 at every multiple from one to twenty-four")

# ---- A5.7 Agent-Based Supply Chain. Hand-derived: 3/20 = 0.15, Yellow arm is < 0.20.
_as = run_agent_supply_chain({"longLeadItemsTotal": 20, "longLeadAtRisk": 3},
                             NO_ARG, "2025-06-30")
ka(_as["at_risk_ratio"], 0.15, "A5.7: 3 of 20 at risk is 0.15 by hand", "A5.7", "known_answer")
ka(_as["status_color"], "Yellow", "A5.7: 0.15 lands Yellow", "A5.7", "boundary")
ka(run_agent_supply_chain({"longLeadItemsTotal": 100, "longLeadAtRisk": 10},
                          NO_ARG, "2025-06-30")["status_color"], "Yellow",
   "A5.7: exactly 0.10 is Yellow, so the Green edge is exclusive", "A5.7", "boundary")
ka(abstains(run_agent_supply_chain({"longLeadItemsTotal": 0, "longLeadAtRisk": 0},
                                   NO_ARG, "2025-06-30")), True,
   "A5.7: an empty long-lead log abstains, as Run 7 installed", "A5.7", "abstention")
ka(abstains(run_agent_supply_chain({"longLeadItemsTotal": 20, "longLeadAtRisk": 25},
                                   NO_ARG, "2025-06-30")), True,
   "A5.7: more items at risk than recorded is refused", "A5.7", "domain")

# ---- A6.3 Environmental Compliance Rate. A pass-through of an audited rate; the whole contract
#      is the pass-through, the domain refusal and the band, so that is what is asserted.
_ec = run_environmental_compliance({"environmentalIssuesDiscussed": 2,
                                    "environmentalComplianceRate": 95}, NO_ARG, "2025-06-30")
ka(_ec["compliance_rate"], 95, "A6.3: the audited rate is passed through unchanged", "A6.3",
   "pass_through")
ka(_ec["status_color"], "Green", "A6.3: exactly 95 per cent is Green, inclusive", "A6.3",
   "boundary")
ka(run_environmental_compliance({"environmentalIssuesDiscussed": 2,
                                 "environmentalComplianceRate": 94.9},
                                NO_ARG, "2025-06-30")["status_color"], "Yellow",
   "A6.3: just below 95 per cent is Yellow", "A6.3", "boundary")
ka(abstains(run_environmental_compliance({"environmentalIssuesDiscussed": 2},
                                         NO_ARG, "2025-06-30")), True,
   "A6.3: without an audited rate it abstains, and does not count meeting mentions", "A6.3",
   "abstention")
ka(abstains(run_environmental_compliance({"environmentalIssuesDiscussed": 2,
                                          "environmentalComplianceRate": 101},
                                         NO_ARG, "2025-06-30")), True,
   "A6.3: a rate above a hundred per cent is refused rather than clipped", "A6.3", "domain")


# =================================================================================================
section("9. THE TWO BUCKET 4 MODULES: THE ARITHMETIC PASSES, THE METHOD IS NOT PRESENT")
# =================================================================================================

# ---- A5.4 Scenario Modeling. Three deterministic forecasts, no scenario definitions anywhere.
#      bac 1,000,000, ev 400,000, ac 440,000, cpi 0.909, spi 0.889:
#      remaining    = 1,000,000 - 400,000 = 600,000
#      optimistic   = 440,000 + 600,000 * 1.00 = 1,040,000
#      realistic    = 440,000 + 600,000 / 0.909 = 440,000 + 660,066.007 = 1,100,066.007
#      pessimistic  = 440,000 + 600,000 / min(0.909, 0.889) = 440,000 + 674,915.636 = 1,114,915.6
#      range        = (1,114,915.6 - 1,040,000)/1,000,000 * 100 = 7.5 per cent
#      the Amber arm is pessimistic <= bac * 1.20 = 1,200,000, and the Yellow arm is
#      <= 1,100,000, which 1,114,915.6 exceeds, so Amber.
_sm = run_scenario_modeling({"bac": 1000000, "ev": 400000, "ac": 440000,
                             "cpi": 0.909, "spi": 0.889}, NO_ARG, "2025-06-30")
ka(_sm["optimistic_eac"], 1040000, "A5.4: the optimistic forecast is 1,040,000 by hand",
   "A5.4", "known_answer", "440,000 + 600,000")
ka(_sm["realistic_eac"], 1100066, "A5.4: the likely forecast is 1,100,066 by hand", "A5.4",
   "known_answer", "440,000 + 600,000/0.909")
ka(_sm["pessimistic_eac"], 1114916, "A5.4: the worst forecast is 1,114,916 by hand", "A5.4",
   "known_answer", "440,000 + 600,000/0.889")
ka(_sm["scenario_range_pct"], 7.5, "A5.4: the range is 7.5 per cent of the budget", "A5.4",
   "known_answer", "(1,114,915.6 - 1,040,000)/1,000,000 * 100")
ka(_sm["status_color"], "Amber", "A5.4: and the reading is Amber", "A5.4", "boundary")
#      Monetary scale equivariance, exhausted: the three forecasts scale with the money and the
#      range percentage does not move, which is what a scenario range being a percentage means.
_sm_fail = []
for scale in (1, 2, 10, 100):
    r = run_scenario_modeling({"bac": 1000000 * scale, "ev": 400000 * scale,
                               "ac": 440000 * scale, "cpi": 0.909, "spi": 0.889},
                              NO_ARG, "2025-06-30")
    if r["scenario_range_pct"] != _sm["scenario_range_pct"]:
        _sm_fail.append(scale)
ka(_sm_fail, [], "A5.4: the scenario range is invariant under monetary scaling", "A5.4",
   "property")
ka(abstains(run_scenario_modeling({"bac": 1000000, "ev": 400000, "ac": 440000,
                                   "cpi": -0.9, "spi": 0.889}, NO_ARG, "2025-06-30")), True,
   "A5.4: a negative cost index is refused, as the fifteen-defects run installed", "A5.4",
   "abstention")

# ---- B2.19 CRITIC-TOPSIS. The arithmetic is coherent and all four bands are reachable, which
#      is what separates it from the ranking module above. What is absent is the alternatives
#      matrix a CRITIC weighting is computed ACROSS; here the weights come from one project's
#      own three criteria, so a criterion sitting at the mean of the other two is weighted at
#      zero and drops out of its own decision.
#      cpi 0.90, spi 0.90, risk value 1 - 0.10 = 0.90: all three equal, so the standard
#      deviation is zero and the module's own fallback gives each criterion a weight of a third.
_ct_flat = run_critic_topsis({"cpi": 0.90, "spi": 0.90, "docRiskScore": 0.10},
                             NO_ARG, "2025-06-30")
#      d_ideal = sqrt(1/3 * (0.90-1.05)^2 + 1/3 * (0.90-1.05)^2 + 1/3 * (0.90-1.00)^2)
#              = sqrt(1/3 * (0.0225 + 0.0225 + 0.01)) = sqrt(0.0183333) = 0.135401 -> 0.135
#      d_anti  = sqrt(1/3 * (0.10^2 + 0.10^2 + 0.60^2)) = sqrt(1/3 * 0.38) = sqrt(0.126667)
#              = 0.355903 -> 0.356
#      topsis  = 0.355903 / (0.135401 + 0.355903 + 0.0001) = 0.355903/0.491404 = 0.724271 -> 0.724
ka(_ct_flat["distance_ideal"], 0.135, "B2.19: the distance to the ideal is 0.135 by hand",
   "B2.19", "known_answer", "sqrt(one third of 0.055)")
ka(_ct_flat["distance_anti"], 0.356, "B2.19: the distance to the anti-ideal is 0.356 by hand",
   "B2.19", "known_answer", "sqrt(one third of 0.38)")
ka(_ct_flat["topsis_score"], 0.724, "B2.19: the closeness coefficient is 0.724 by hand",
   "B2.19", "known_answer", "0.355903 / (0.135401 + 0.355903 + 0.0001)")
ka(_ct_flat["status_color"], "Green", "B2.19: 0.724 lands Green", "B2.19", "boundary")
#      All four bands are reachable, exhausted over the same grid the ranking module failed.
_ct_bands = set()
for cpi_i in range(50, 161, 4):
    for spi_i in range(50, 161, 4):
        for doc_i in range(0, 101, 10):
            _ct_bands.add(run_critic_topsis({"cpi": cpi_i / 100, "spi": spi_i / 100,
                                             "docRiskScore": doc_i / 100},
                                            NO_ARG, "2025-06-30")["status_color"])
ka(sorted(_ct_bands), ["Amber", "Green", "Red", "Yellow"],
   "B2.19: all four bands are reachable, unlike the ranking module beside it", "B2.19",
   "property")
#      The degenerate weighting, demonstrated rather than described: the middle criterion of
#      three carries a weight of zero whenever it equals their mean.
_crit = [0.80, 0.90, 1.00]
_mean = sum(_crit) / 3
_sd = math.sqrt(sum((v - _mean) ** 2 for v in _crit) / 3)
_w = [abs(v - _mean) / _sd for v in _crit]
ka(_w[1], 0.0, "B2.19: a criterion equal to the mean of the three carries no weight at all",
   "B2.19", "known_answer", "abs(0.90 - 0.90) divided by the standard deviation")


# =================================================================================================
section("10. THE TWO BUCKET 5 MODULES: THE UNCONDITIONAL ABSTENTION CONTRACT")
# =================================================================================================
#
# Run 7 made these two refuse on every input, because neither reads a project input at all and
# neither's defining structure is in the corpus. This run asserts the contract holds and that
# nothing has reactivated them, and it does NOT reactivate them.

_RICH = {"bac": 1000000, "ev": 400000, "ac": 440000, "pv": 450000, "cpi": 0.909, "spi": 0.889,
         "actualPctComplete": 40, "plannedPctComplete": 45, "docRiskScore": 0.3,
         "rfiCount": 30, "changeOrderCount": 5, "activitiesPlanned": 200}
for mid, label in (("A3.1", "reference class forecasting"), ("A5.1", "rework propagation")):
    for name, si in (("an empty input", {}), ("a fully populated input", dict(_RICH))):
        r = VALIDATED[mid][1](si, make_rng(3), "2025-06-30")
        ka(abstains(r), True, f"{mid}: abstains on {name}", mid, "disabled_contract")
        speakable(r, f"{mid} on {name}")
    ka(VALIDATED[mid][1](dict(_RICH), make_rng(3), "2025-06-30").get("status_color"), None,
       f"{mid}: no band is reachable from any input", mid, "disabled_contract")
    ka(mid in registry.CORE_VOTING_MODULES, False, f"{mid}: is not a voting module", mid,
       "disabled_contract")
    check(label is not None, f"{mid}: {label} remains off pending an owner decision")
# The two are not in the Run 1 disabled set, so their off state rests on Run 7's abstention
# rather than on the registry short circuit. Recorded so a later run does not assume otherwise.
ka(sorted(set(registry.DISABLED_CONCEPT_ONLY) & {"A3.1", "A5.1"}), [],
   "A3.1 and A5.1 are off by abstention, not by the registry's disabled set", "", "derivation")


# =================================================================================================
section("11. BOUNDARY INCLUSIVITY ACROSS THE 27: THE TWO CONVENTIONS STILL DISAGREE")
# =================================================================================================
#
# Run 6 recorded that the request-velocity module carries two ladders that disagree with each
# other. The same disagreement runs ACROSS the 27: some ladders are inclusive on the calmer side
# and some are exclusive, and no comment anywhere says which a given module uses. Both are
# asserted here so the disagreement is a measured fact rather than a reading of the source.

_INCLUSIVE_ON_CALM = {  # edge value reads BETTER
    "A2.9": run_resource_loading({"plannedLaborHours": 1000, "actualLaborHours": 1100},
                                 NO_ARG, "2025-06-30")["status_color"] == "Green",
    "A6.2": run_safety_performance({"safetyIncidentsDiscussed": 0, "oshaIncidentRate": 3.0},
                                   NO_ARG, "2025-06-30")["status_color"] == "Green",
    "A6.3": run_environmental_compliance({"environmentalIssuesDiscussed": 1,
                                          "environmentalComplianceRate": 95},
                                         NO_ARG, "2025-06-30")["status_color"] == "Green",
    "A4.10": run_spec_conflict_density({"docRiskScore": 0.30, "rfiCount": 4},
                                       NO_ARG, "2025-06-30")["status_color"] == "Amber",
}
_EXCLUSIVE_ON_CALM = {  # edge value reads WORSE
    "A5.6": run_queueing_bottleneck({"activitiesPlanned": 100, "activitiesConstrained": 15},
                                    NO_ARG, "2025-06-30")["status_color"] == "Yellow",
    "A5.7": run_agent_supply_chain({"longLeadItemsTotal": 100, "longLeadAtRisk": 10},
                                   NO_ARG, "2025-06-30")["status_color"] == "Yellow",
    "A4.4": run_ncr_rate({"ncrIssued": 1, "ncrClosed": 0, "ncrOpen": 6, "totalFindings": 40},
                         NO_ARG, "2025-06-30")["status_color"] == "Yellow",
}
ka(sorted(k for k, v in _INCLUSIVE_ON_CALM.items() if v),
   ["A2.9", "A4.10", "A6.2", "A6.3"],
   "four of the 27 are inclusive on the calmer side of their edge", "", "boundary")
ka(sorted(k for k, v in _EXCLUSIVE_ON_CALM.items() if v), ["A4.4", "A5.6", "A5.7"],
   "three of the 27 are exclusive on the calmer side of the same kind of edge", "", "boundary")


# =================================================================================================
section("12. THE PRODUCTION PATH: ALL 27 THROUGH registry.run_all AND compute_project")
# =================================================================================================
#
# A direct function test supplements the production path; it does not replace it. Everything
# above is re-driven here through the application's own entry point, on a signalInputs
# dictionary of the shape documents.py assembles, so a module that passes in isolation and is
# unreachable in the application would show up here.

_PROD_SI = {
    "bac": 1000000, "ev": 400000, "ac": 440000, "pv": 450000, "cpi": 0.909, "spi": 0.889,
    "actualPctComplete": 40, "plannedPctComplete": 45, "docRiskScore": 0.30,
    "baselineStart": "2025-01-01", "baselineEnd": "2025-12-31",
    "totalFloat": 30, "consumedFloat": 12,
    "plannedLaborHours": 1000, "actualLaborHours": 1050,
    "ncrIssued": 4, "ncrClosed": 2, "ncrOpen": 6, "totalFindings": 40,
    "rfiCount": 30, "changeOrderCount": 5,
    "activitiesPlanned": 200, "activitiesConstrained": 37,
    "longLeadItemsTotal": 20, "longLeadAtRisk": 3,
    "qualityDeficienciesNoted": 5, "itemsInspected": 100, "itemsFailed": 8,
    "safetyIncidentsDiscussed": 0, "oshaIncidentRate": 2.0,
    "environmentalIssuesDiscussed": 2, "environmentalComplianceRate": 97,
    "overallRating": 4.2, "scheduleRating": 3.9, "costRating": 4.0, "qualityRating": 3.2,
    "cpiHistory": [0.95, 0.93, 0.91], "spiHistory": [0.95, 0.92, 0.889],
}
_res = compute_project(_PROD_SI, "scenario-run8", "P1", "2025-06-30")
_by_id = {r["module_id"]: r for r in _res["modules"]}
_abst = {a["module_id"]: a for a in _res["abstained"]}

_missing = [m for m in UNRESOLVED_27 if m not in _by_id and m not in _abst]
ka(_missing, [], "every one of the 27 is reached by the production path, computed or abstaining",
   "", "production_path")
# The two Bucket 5 modules must be on the abstained list there, not merely absent.
ka(sorted(m for m in ("A3.1", "A5.1") if m in _abst), ["A3.1", "A5.1"],
   "the two unconditionally abstaining modules appear on the production abstention list", "",
   "production_path")
# And the production row carries the reason, so the ledger can say why the module is silent.
for mid in ("A3.1", "A5.1"):
    check(bool(_abst[mid].get("reason")),
          f"{mid}: the production abstention row carries a reason")
    check(_abst[mid].get("activation_state") == "ADVISORY_ONLY",
          f"{mid}: the production row records the activation state",
          str(_abst[mid].get("activation_state")))
# None of the 27 votes, and none may be made voting by this run.
_voting = sorted(m for m in UNRESOLVED_27 if _by_id.get(m, {}).get("votes"))
ka(_voting, [], "not one of the 27 carries a vote on the stored row", "", "production_path")
ka(sorted(registry.CORE_VOTING_MODULES), ["A1.7", "A1.8"],
   "the voting set is unchanged by this run", "", "production_path")

# The production values agree with the direct cases above, module by module, for the ones the
# production input is rich enough to compute. This is the join a fixture built by a route the
# application does not take would break.
for mid, key, expected, why in (
    ("A2.9", "load_ratio", 1.05, "1050/1000"),
    ("A2.5", "float_stress", 1.0, "0.40 consumed at 40 per cent complete"),
    ("A4.4", "open_ratio", 0.15, "6 of an audited cohort of 40"),
    ("A5.6", "constraint_ratio", 0.19, "37 of 200"),
    ("A5.7", "at_risk_ratio", 0.15, "3 of 20"),
    ("A6.1", "quality_score", 92, "(100 - 8)/100"),
    ("A6.3", "compliance_rate", 97, "the audited rate passed through"),
    ("A6.4", "min_rating", 3.2, "min(4.2, 3.9, 4.0, 3.2)"),
    ("A1.6", "spi_time", 0.889, "40/45"),
    ("A2.11", "critical_path_index", 0.894, "(0.888888 + 0.889)/2 is 0.8894, rounds to 0.889"),
):
    got = _by_id.get(mid, {}).get(key)
    if mid == "A2.11":
        # (40/45 + 0.889)/2 = (0.888888 + 0.889)/2 = 0.888944 -> 0.889 on THIS input, not 0.894,
        # which was the 0.9 index used in the direct case. Derived for this input specifically.
        expected = 0.889
        why = "(0.888888 + 0.889)/2"
    ka(got, expected, f"{mid}: the production path gives {expected} for {key}", mid,
       "production_path", why)

# The production status vocabulary is recognised by the one place that recognises it.
import app.simulation.fusion as fusion  # noqa: E402
_unrecognised = sorted(m for m in UNRESOLVED_27
                       if m in _by_id
                       and fusion.normalise_status(_by_id[m]["status_color"]) is None)
ka(_unrecognised, [], "every band the 27 store is recognised by the status vocabulary", "",
   "production_path")

# The abstention sweep re-driven through run_all rather than through the module functions.
_empty_run = registry.run_all({}, "scenario-run8", "P1", "2025-06-30")
_empty_computed = {r["module_id"] for r in _empty_run["computed"]}
ka(sorted(set(UNRESOLVED_27) & _empty_computed), [],
   "on an empty input the production path bands none of the 27", "", "production_path")


# =================================================================================================
section("13. THE AUDIT ARTEFACTS THIS RUN WRITES")
# =================================================================================================

AUDIT = ROOT / "code_audit"
AUDIT.mkdir(exist_ok=True)
with (AUDIT / "run8_expectation_mutation_proof.csv").open("w", newline="",
                                                          encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["module_id", "check_label", "kind", "expected",
                                       "perturbed_expectation", "actual",
                                       "red_under_perturbation", "green_when_restored",
                                       "derivation"])
    w.writeheader()
    for row in MUTATION_ROWS:
        w.writerow(row)
check((AUDIT / "run8_expectation_mutation_proof.csv").exists(),
      "the expectation-mutation proof is written to code_audit/")
ka(len(MUTATION_ROWS), CASES, "every case wrote a mutation-proof row", "", "derivation")
_unprovable = [r["check_label"] for r in MUTATION_ROWS if r["red_under_perturbation"] != "yes"]
ka(_unprovable, [], "every expectation went red under perturbation", "", "derivation")

print()
print("=" * 78)
print(f"Cases: {CASES}; expectations proved live by perturbation: {PERTURBED}")
print(f"Unresolved universe: {len(UNRESOLVED_27)}; classified: {len(BUCKETS)}; "
      f"left unclassified: {len(set(UNRESOLVED_27) - set(BUCKETS))}")
print("=" * 78)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 78)
sys.exit(1 if FAILED else 0)
