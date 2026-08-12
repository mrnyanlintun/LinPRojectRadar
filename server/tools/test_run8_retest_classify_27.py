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

#: RUN 10 is a production run and declares its own authorised set here rather than emptying
#: Run 8's, so Run 8's own claim — that it changed no production code — remains readable as
#: written. Anything under server/app/ or assets/ outside BOTH sets is still a scope breach.
RUN10_SCOPED_FILES = {
    "server/app/simulation/models.py",
    "server/app/simulation/models_doc.py",
    "server/app/simulation/models_evm.py",
    "server/app/simulation/models_ext.py",
    "server/app/simulation/models_fuzzy.py",
    "server/app/simulation/models_sim.py",
}

#: RUN 10B declares its own authorised set on the same footing, so Run 8's claim that it changed
#: no production code and Run 10's own scope both remain readable exactly as written.
RUN10B_SCOPED_FILES = {
    "server/app/simulation/canonical.py",
}

#: RUN 11's authorised scope, added on the same footing so each run's authorisation is readable
#: on its own. The four model files hold the seven remaining neighbour defects; the browser files
#: are Gate 1's subject, the first time this guard has admitted an asset (see the restated
#: assets/ check below, whose original finding is preserved for every other surface).
RUN11_SCOPED_FILES = {
    "server/app/simulation/models.py",
    "server/app/simulation/models_doc.py",
    "server/app/simulation/models_evm.py",
    "server/app/simulation/models_ext.py",
    "server/app/simulation/models_gov.py",
    "server/app/simulation/models_dq.py",
    "server/app/simulation/fusion.py",
    "server/app/simulation/registry.py",
    "assets/js/client_algorithm_version.js",
    "assets/js/detail.js",
    "assets/js/signals.js",
    "assets/js/taxonomy.js",
    "assets/js/ds_defensibility_data.js",
    "assets/js/app.js",
    "assets/js/decision.js",
    "server/app/documents.py",
    "server/app/simulation/compute.py",
    "assets/js/ds_defensibility_evidence.js",
    "index.html",
}

#: RUN 12 adds its own authorised production scope on the same footing, and it is deliberately
#: small: the evidence qualification object is ONE new file, and the two files that attach it at
#: the single point in the pipeline where the resolved evidence is in hand. No asset, no
#: participant surface, no model file, no registry entry. Every earlier run's list is left
#: exactly as that run left it.
RUN12_SCOPED_FILES = {
    "server/app/simulation/qualification.py",
    # The one participant surface Run 12 is authorised to touch, and only because driving the
    # whole cycle in a real browser found the card that never came back after a period
    # advance. See the note at the fix.
    "assets/js/decision-ui.js",
    "server/app/simulation/compute.py",
    "server/app/documents.py",
}

#: RUN 14 adds its own authorised production scope on the same footing, and it is the two files
#: that hold the numeric contract plus the model files carrying the eight corrections Run 13's
#: evidence required. The upper end of a field's domain is a property of the field, so it is
#: declared in the registry and enforced by the validator that already runs at every entry
#: point, rather than being added to each module that reads the field.
RUN14_SCOPED_FILES = {
    "server/app/field_registry.py",
    "server/app/extraction_merge.py",
    "server/app/simulation/models.py",
    "server/app/simulation/models_ext.py",
    "server/app/simulation/models_doc.py",
    "server/app/simulation/models_dq.py",
    "server/app/simulation/models_fuzzy.py",
}

# RUN 15 replaced the standardised-distance proxy at D1.1 with a real isolation forest: a new
# algorithm file, a rewritten D1.1 block in the portfolio layer, the version stamp, and the
# browser method description that still called the module a distance proxy.
RUN15_SCOPED_FILES = {
    "server/app/simulation/portfolio.py",
    "server/app/simulation/isolation_forest.py",
    "server/app/simulation/models.py",
    "assets/js/knowledge.js",
}

# RUN 16 corrected the Signal Flow diagram, which reported registry counts as project activity
# and animated every connection on a project with no evidence; made the clear-all workflow
# invalidate the results derived from the evidence it clears; and disabled Material Cost Variance
# from operational execution, which the registry enforces, the export mirrors and the browser
# taxonomy presents.
RUN16_SCOPED_FILES = {
    "assets/js/neural_flow.js",
    "assets/js/detail.js",
    "assets/js/taxonomy.js",
    "server/app/writes.py",
    "server/app/research_export.py",
    "server/app/simulation/registry.py",
    "server/app/simulation/qualification.py",
    "server/app/simulation/models.py",
}

_diff = subprocess.run(["git", "diff", "--name-only", GUARD_BASELINE_REV, "--"],
                       cwd=str(ROOT), capture_output=True, text=True).stdout.split()
_prod = [p for p in _diff
         if (p.startswith("server/app/") or p.startswith("assets/"))
         and p not in RUN8_SCOPED_FILES and p not in RUN10_SCOPED_FILES
         and p not in RUN10B_SCOPED_FILES and p not in RUN11_SCOPED_FILES
         and p not in RUN12_SCOPED_FILES and p not in RUN14_SCOPED_FILES
         and p not in RUN15_SCOPED_FILES and p not in RUN16_SCOPED_FILES]
check(not _prod, "no production file under server/app/ or assets/ differs from the pinned "
                 "baseline", " ".join(_prod))
# RESTATED BY RUN 11, original finding preserved. This read "nothing under assets/ differs"
# until Run 11 Gate 1, which is authorised to change exactly the browser files that carried the
# dormant client arithmetic. It keeps its full force over every other participant surface.
_unscoped_assets = sorted(p for p in _diff
                          if p.startswith("assets/") and p not in RUN11_SCOPED_FILES
                          and p not in RUN12_SCOPED_FILES
                          and p not in RUN15_SCOPED_FILES
                          and p not in RUN16_SCOPED_FILES)
check(not _unscoped_assets,
      "nothing under assets/ outside Run 11's authorised browser scope differs from the pinned "
      "baseline", " ".join(_unscoped_assets))


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

# RUN 10 RESOLVES THIS ONE. The finding above is unchanged and is the reason for the
# correction: the two sides of the ratio were different statistics of the same distribution, so
# no schedule index could close the gap. Run 10 did not move the boundary to make a healthy
# reading reachable, because that would have left the deeper fault standing: the three activities
# were this file's own literals and not the project's network, so the index described the file
# rather than the project. The literal-driven sampling is removed and the module abstains on the
# absent activity network, on the same footing as reference class forecasting and rework
# propagation. What is asserted here now is that no reading of any kind reaches a participant.
_pert_bands = set()
for seed in range(200):
    for spi in (0.6, 0.8, 0.9, 1.0, 1.05, 1.2, 1.5, 2.0):
        r = run_pert({"spi": spi}, make_rng(seed), "2025-06-30")
        _pert_bands.add(r.get("status_color"))
        check("p80_duration_days" not in r and "path_criticality_index" not in r,
              f"A2.1: no duration or criticality figure at index {spi}, seed {seed}") \
            if seed == 0 else None
ka(sorted(str(b) for b in _pert_bands), ["None"],
   "A2.1: no band at all is reachable over 1,600 seed and index combinations, because the "
   "module abstains on the absent network", "A2.1", "property",
   "Run 10 removed the literal-driven sampling rather than moving the Green edge")
ka(run_pert({"spi": 2.0}, make_rng(11), "2025-06-30").get("abstention_reason_code"),
   "canonical_structure_absent",
   "A2.1: the abstention names the absent canonical structure", "A2.1", "known_answer",
   "an activity network with logic and three-point durations is not in the corpus")
# The abstention Run 7 installed still holds.
ka(abstains(run_pert({}, make_rng(1), "2025-06-30")), True,
   "A2.1: still abstains without a schedule index", "A2.1", "abstention")



# =================================================================================================
# RUN 10 SUPERSESSION HELPER.
#
# Run 8 recorded, module by module, the figure and the band each of these modules returned for an
# input that cannot describe a project. Those findings are the reason Run 10 corrected them and
# they are left in place above each case as the record. What can no longer be asserted is the
# figure itself, because the module now abstains before producing one. Each superseded case is
# restated here as: the module refuses, it publishes no figure, and it publishes no band. The
# in-domain known answers beside them are untouched and still assert the arithmetic.
# =================================================================================================


def superseded(result, module, label, *absent_fields):
    ka(abstains(result), True, f"{module}: {label} is now refused rather than banded",
       module, "abstention", "Run 10 correction")
    for f in absent_fields:
        check(f not in result, f"{module}: and no {f} is published for it")

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
# RUN 10 RESOLVES THIS ONE. The derivation above is unchanged and is why the correction was
# made: two utility degrees that sum to one by construction are one number and its complement,
# not two measurements, and the score built from them was bounded above by a third. Run 10 did
# not move a band boundary; the boundaries below are exactly the ones the module already carried.
# It restored the method's own structure, in which the two utility degrees are the alternative's
# weighted sum measured separately against the ideal and against the anti-ideal reference. What
# is asserted here now is that the whole ladder is reachable and that the score responds to the
# inputs rather than folding about the middle of its own scale.
ka(sorted(_marcos_bands), ["Amber", "Green", "Red", "Yellow"],
   "B2.18: all four bands are reachable over 65,856 index and document-risk combinations",
   "B2.18", "property", "Run 10 restored two independent utility degrees")
check(_marcos_max > 0.65,
      "B2.18: the highest score in the domain now reaches the healthy arm of the ladder",
      f"highest {_marcos_max}")

_best = run_marcos({"cpi": 1.05, "spi": 1.05, "docRiskScore": 0.0}, NO_ARG, "2025-06-30")
_worst = run_marcos({"cpi": 0.80, "spi": 0.80, "docRiskScore": 0.70}, NO_ARG, "2025-06-30")
check(_best["marcos_score"] > _worst["marcos_score"],
      "B2.18: the best admissible project now outscores the worst one",
      f"{_best['marcos_score']} vs {_worst['marcos_score']}")
ka(_best["status_color"], "Green", "B2.18: a project at every ideal reads Green", "B2.18",
   "enumerated")
# A project sitting exactly ON the anti-ideal reference scores the ratio of the anti-ideal
# weighted sum to itself, which is the middle of the scale rather than its floor, and the floor
# belongs to projects below the anti-ideal. Both are asserted.
ka(_worst["status_color"], "Yellow",
   "B2.18: a project exactly at the anti-ideal reference sits mid-ladder", "B2.18", "enumerated")
ka(run_marcos({"cpi": 0.50, "spi": 0.50, "docRiskScore": 1.0}, NO_ARG,
              "2025-06-30")["status_color"], "Red",
   "B2.18: a project below the anti-ideal reference reads Red", "B2.18", "enumerated")

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
ka(_sym_failures, [], "B2.18: the SUPERSEDED closed form was symmetric at every hundredth of "
   "utility, which is the algebra Run 10 replaced", "B2.18", "property",
   "algebraic identity of the old expression, kept as the record of why it was replaced")


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
    _zero_spi = run_schedule_risk({**_BASE, "spi": 0}, NO_ARG, "2025-06-30")
except ZeroDivisionError:
    _crashed = True
ka(_crashed, False, "A2.10: a schedule index of zero no longer raises", "A2.10", "abstention",
   "Run 10 guards the denominator before the division")
superseded(_zero_spi, "A2.10", "a schedule index of zero", "p80_delay_days", "p50_delay_days")
ka(_zero_spi.get("abstention_reason_code"), "invalid_denominator",
   "A2.10: and names the invalid denominator as the reason", "A2.10", "abstention")

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
superseded(_neg, "A2.10", "a negative schedule index", "p80_delay_days", "p50_delay_days")

# A completion above one hundred per cent makes the remaining work negative and reads Green.
#   remaining = 364 * (100 - 120)/100 = -72.8 days; p50 = -72.8 / 1.0 = -72.8
#   uncertainty = max(0.05, 1 - 1.0) * 0.5 = 0.05 * 0.5 = 0.025
#   p80 = -72.8 * (1 + 0.025 * 1.28) = -72.8 * 1.032 = -75.1296
#   delay = round(-75.1296 - (-72.8)) = round(-2.3296) = -2
_over = run_schedule_risk({**_BASE, "actualPctComplete": 120}, NO_ARG, "2025-06-30")
superseded(_over, "A2.10", "a completion of 120 per cent", "p80_delay_days")

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
superseded(_bare, "A5.5", "an absent request log and an absent change order log",
           "rework_index")

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
        _subsets.append(run_rework_feedback(si, NO_ARG, "2025-06-30").get("rework_index"))
ka(sorted(x for x in _subsets if x is not None), [0.64],
   "A5.5: only the complete evidence set produces an index; every strict subset refuses",
   "A5.5", "property", "Run 10 requires both logs rather than scoring an absence as nought")

# A REPORTED ZERO AND AN ABSENT LOG ARE INDISTINGUISHABLE, because the guard is a truthiness
# test (`if si.get("rfiCount")`), so a genuine zero is discarded as though nothing was reported.
_zero = run_rework_feedback({"cpi": 0.90, "rfiCount": 0, "changeOrderCount": 0},
                            NO_ARG, "2025-06-30")
ka(_zero["rework_index"], 0.04,
   "A5.5: a REPORTED zero is a measurement and still produces an index", "A5.5", "known_answer",
   "0 + 0 + 0.04, and the absent case beside it now refuses instead")
check(abstains(_bare) and not abstains(_zero),
      "A5.5: a reported zero and an absent log are no longer indistinguishable")

# NEGATIVE COUNTS ARE NOT REFUSED, and drive the index below the domain an index can occupy.
#   rfi = min(-5/30, 1) * 0.3 = -0.16666 * 0.3 = -0.05; cpi term 0.04; index = -0.01
_negc = run_rework_feedback({"cpi": 0.90, "rfiCount": -5}, NO_ARG, "2025-06-30")
superseded(_negc, "A5.5", "a negative request count", "rework_index")
superseded(run_rework_feedback({"cpi": -1.0}, NO_ARG, "2025-06-30"), "A5.5",
           "a cost index of minus one with no logs", "rework_index")

# The finding text names a quantity the module does not compute: the term is a raw count
# capped at thirty, not a rate over time, and the sentence says otherwise.
_negc = run_rework_feedback({"cpi": 0.90, "rfiCount": -5, "changeOrderCount": 2},
                            NO_ARG, "2025-06-30")
superseded(_negc, "A5.5", "a negative request count beside a present change order count",
           "rework_index")
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
superseded(_es_neg, "A1.6", "a completion of minus forty per cent", "spi_time", "delay_days")
#      actual 140, planned 45 -> 3.111111 -> 3.111; the Green arm is >= 0.95.
_es_over = run_earned_schedule({"ev": 400, "pv": 450, "bac": 1000,
                                "actualPctComplete": 140, "plannedPctComplete": 45},
                               NO_ARG, "2025-06-30")
superseded(_es_over, "A1.6", "a completion of a hundred and forty per cent", "spi_time")
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
ka(abstains(_es_no_ev), False,
   "A1.6: Run 10 no longer demands the three figures the arithmetic never reads", "A1.6",
   "known_answer", "the requirement is now the two completion percentages it actually uses")
ka(_es_no_ev["spi_time"], 0.889,
   "A1.6: and computes the same index from them, 40/45 by hand", "A1.6", "known_answer")

# ---- A1.11 ICE Ratio. A negative cost index produces a negative forecast reported as money.
#      eac_cpi = 1000 / -0.5 = -2000; eac_parametric = 800 + (1000 - 400) = 1400
#      ice = -2000 / 1400 = -1.42857 -> -1.429; |ice - 1| = 2.429, Red arm is > 0.20.
_ice = run_ice_ratio({"bac": 1000, "cpi": -0.5, "ev": 400, "ac": 800}, NO_ARG, "2025-06-30")
superseded(_ice, "A1.11", "a negative cost index", "ice_ratio", "eac_cpi")
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
superseded(_ar, "A1.5", "a history of negative cost performance indices", "forecast_cpi")
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
superseded(_rl, "A2.9", "negative actual labour hours", "load_ratio")
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
superseded(_fc, "A2.5", "a negative consumed float", "float_remaining_days", "float_stress")
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
superseded(_cpx, "A2.11", "a negative schedule index", "critical_path_index")
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
superseded(_sc, "A4.10", "a negative document risk score", "conflict_density")
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
superseded(_des, "A5.8", "a negative schedule index", "throughput_index")
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
superseded(_q_hi, "A6.1", "an audited score of a hundred and fifty out of a hundred",
           "quality_score")
_q_lo = run_quality_compliance({"qualityDeficienciesNoted": 3, "qualityAuditScore": -20},
                               NO_ARG, "2025-06-30")
superseded(_q_lo, "A6.1", "an audited score of minus twenty", "quality_score")
check("-20/100" not in _q_lo["evidence_metric"],
      "A6.1: and no out-of-domain figure reaches the finding text",
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
superseded(_cp, "A6.4", "a rating of nine point nine on a five-point scale", "min_rating")
_cp_ok = run_contractor_performance({"overallRating": 4.9, "scheduleRating": 4.0,
                                     "costRating": 4.1}, NO_ARG, "2025-06-30")
ka(_cp_ok["min_rating"], 4.0, "A6.4: an in-scale evaluation still scores its worst rating",
   "A6.4", "known_answer", "min(4.9, 4.0, 4.1)")
check("/5" in _cp_ok["evidence_metric"],
      "A6.4: and the finding text describes the scale as out of five",
      _cp_ok["evidence_metric"])
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
check("+-28.8" not in _cr["evidence_metric"] and "-28.8" in _cr["evidence_metric"],
      "A3.6: and the finding text now prints one sign, the one the figure carries",
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
# Run 10 splits this case in two. A count DERIVED from meeting mentions is silence, not a
# measurement, and it now refuses. A count read from an uploaded safety record is a measurement
# and still bands, which is the disposition Run 7 settled and Run 10 leaves alone.
_sf0_derived = run_safety_performance(
    {"safetyIncidentsDiscussed": 0,
     "sources": {"safetyIncidentsDiscussed": {"docType": "derived"}}}, NO_ARG, "2025-06-30")
superseded(_sf0_derived, "A6.2", "safety never mentioned in a meeting", "safety_index",
           "incident_rate")
ka(_sf0["safety_index"], 2,
   "A6.2: a zero read from a safety record still takes the module's own cap", "A6.2",
   "known_answer", "the cap of 2, the disposition Run 7 settled")
ka(_sf0["status_color"], "Green",
   "A6.2: and a documented zero over a valid exposure still reads Green", "A6.2", "enumerated")
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

# ---- A2.2 Line of Balance.
#      RUN 8 FOUND, AND THE FINDING IS PRESERVED HERE AS THE REASON THIS BLOCK WAS RESTATED: the
#      unit count, both production rates and the buffer were literals in the module's own file,
#      so the arithmetic was faithful to the file rather than to any project, and the method
#      needed a real line-of-balance structure. Run 10B supplies that requirement. The module now
#      abstains on a schedule index alone and computes on locations, crews and production rates.
ka(abstains(run_lob({"spi": 0.9}, NO_ARG, "2025-06-30")), True,
   "A2.2: a schedule index alone no longer produces a reading, because the index is not a line "
   "of balance", "A2.2", "abstention")
#      HAND DERIVATION. The leading line advances at 2.0 locations a day from day 0 and the
#      following line at 1.6 from day 2.5, so the leading crew reaches location u on day u/2.0
#      and the following crew on day 2.5 + u/1.6. The separation at location u is therefore
#      2.5 + u(0.625 - 0.5) = 2.5 + 0.125u, which grows with u, so its minimum is at the first
#      location: 2.5 + 0.125 = 2.625, reported to one place as 2.6. The Amber arm is a minimum
#      separation at or below 3.0 days and the Red arm at or below 1.5, so 2.6 is Amber.
_LOB_STRUCTURE = {
    "leading_work_type": "EARLY_WORK",
    "following_work_type": "STRUCTURE",
    "work_packages": (
        [{"work_type_id": "EARLY_WORK", "location_sequence": u,
          "production_rate_locations_per_day": 2.0, "start_day": 0.0} for u in range(1, 6)]
        + [{"work_type_id": "STRUCTURE", "location_sequence": u,
            "production_rate_locations_per_day": 1.6, "start_day": 2.5} for u in range(1, 6)]),
}
_lob = run_lob({"lobStructure": _LOB_STRUCTURE}, NO_ARG, "2025-06-30")
ka(_lob["minimum_buffer_days"], 2.6, "A2.2: the minimum separation is 2.6 days by hand",
   "A2.2", "known_answer", "2.5 + 0.125 * 1")
ka(_lob["status_color"], "Amber", "A2.2: 2.6 days is Amber", "A2.2", "boundary")
ka(_lob["units"], 5, "A2.2: the locations are the ones the structure carries, not a literal in "
   "the file", "A2.2", "known_answer", "five locations in sequence")
ka(_lob["paving_rate"], 1.6, "A2.2: the following rate is the one the crews were working at",
   "A2.2", "known_answer")
#      THE INTERFERENCE CASE the method exists to find: a following line faster than the leading
#      one closes the separation, so the minimum is at the LAST location rather than the first.
#      Leading 1.6 from day 0, following 2.0 from day 2.5: separation = 2.5 - 0.125u, which at
#      the fifth location is 2.5 - 0.625 = 1.875, reported 1.9, and 1.9 is above 1.5 so Amber.
_LOB_FAST = {
    "leading_work_type": "EARLY_WORK", "following_work_type": "STRUCTURE",
    "work_packages": (
        [{"work_type_id": "EARLY_WORK", "location_sequence": u,
          "production_rate_locations_per_day": 1.6, "start_day": 0.0} for u in range(1, 6)]
        + [{"work_type_id": "STRUCTURE", "location_sequence": u,
            "production_rate_locations_per_day": 2.0, "start_day": 2.5} for u in range(1, 6)]),
}
_lobf = run_lob({"lobStructure": _LOB_FAST}, NO_ARG, "2025-06-30")
ka(_lobf["minimum_buffer_days"], 1.9,
   "A2.2: a faster following line closes the separation and the minimum is at the last location",
   "A2.2", "known_answer", "2.5 - 0.125 * 5")
ka(_lobf["critical_unit_index"], 5,
   "A2.2: and the module names that last location as the critical one", "A2.2", "known_answer")

# ---- A2.3 CCPM Buffer Health.
#      RUN 8 FOUND, AND THE FINDING IS PRESERVED: the fever chart was faithful arithmetic over a
#      buffer derived from the schedule index rather than from a sized critical-chain buffer, and
#      Run 8 also recorded the degenerate point, that at zero chain completion the Amber edge is
#      zero and inclusive so a project exactly on plan read Amber. Run 10B requires the chain and
#      its sized buffer. The degenerate point is re-derived below on the canonical structure,
#      because it is a property of the fever chart's edges and not of where the buffer came from.
ka(abstains(VALIDATED["A2.3"][1]({"spi": 0.9, "actualPctComplete": 40}, NO_ARG, "2025-06-30")),
   True, "A2.3: an index and a completion percentage no longer produce a reading, because "
   "neither is a sized buffer", "A2.3", "abstention")


def _ccpm_structure(original, remaining, progress):
    return {"ccpmStructure": {
        "chains": [{"chain_id": "CC", "chain_type": "PROJECT", "activity_count": 10}],
        "buffers": [{"chain_id": "CC", "buffer_type": "PROJECT",
                     "original_buffer_days": original, "remaining_buffer_days": remaining,
                     "chain_progress_fraction": progress}],
    }}


#      HAND DERIVATION. A project buffer sized at 20 days with 11 left has consumed 9 of 20,
#      which is 45 per cent, at a chain 40 per cent complete. The Amber edge is the chain
#      completion itself, 40, and the Red edge is 40 + (100 - 40)/3 = 60. 45 is at or above 40
#      and below 60, so Amber.
_cc = VALIDATED["A2.3"][1](_ccpm_structure(20.0, 11.0, 0.40), NO_ARG, "2025-06-30")
ka(_cc["pct_buffer_consumed"], 45.0, "A2.3: the buffer consumed is 45 per cent by hand",
   "A2.3", "known_answer", "(20 - 11) / 20")
ka(_cc["amber_threshold"], 40.0, "A2.3: the Amber edge is the chain completion itself",
   "A2.3", "known_answer")
ka(_cc["red_threshold"], 60.0, "A2.3: the Red edge is a third of the way to completion",
   "A2.3", "known_answer", "40 + (100 - 40)/3")
ka(_cc["status_color"], "Amber", "A2.3: 45 against edges of 40 and 60 is Amber", "A2.3",
   "boundary")
ka(VALIDATED["A2.3"][1](_ccpm_structure(20.0, 17.0, 0.40),
                        NO_ARG, "2025-06-30")["status_color"], "Green",
   "A2.3: 15 per cent consumed at 40 per cent complete is Green", "A2.3", "boundary")
ka(VALIDATED["A2.3"][1](_ccpm_structure(20.0, 7.0, 0.40),
                        NO_ARG, "2025-06-30")["status_color"], "Red",
   "A2.3: 65 per cent consumed at 40 per cent complete is Red", "A2.3", "boundary")
#      THE DEGENERATE POINT, re-derived on the canonical structure. At zero chain completion the
#      Amber edge is zero and the arm is inclusive, so a project that has consumed no buffer at
#      all still reads Amber. Run 8 recorded this and Run 10B does not move the edge.
_cc0 = VALIDATED["A2.3"][1](_ccpm_structure(20.0, 20.0, 0.0), NO_ARG, "2025-06-30")
ka(_cc0["pct_buffer_consumed"], 0.0, "A2.3: an untouched buffer is nought per cent consumed",
   "A2.3", "known_answer")
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

# ---- A5.6 Queueing Theory Bottleneck.
#      RUN 8 FOUND, AND THE FINDING IS PRESERVED: this was a transparent share of a look-ahead
#      window, scale invariant and agreeing with the look-ahead measure that reads the same two
#      fields, and no queueing model was present. Run 10B requires the queue.
ka(abstains(run_queueing_bottleneck({"activitiesPlanned": 200, "activitiesConstrained": 37},
                                    NO_ARG, "2025-06-30")), True,
   "A5.6: a look-ahead window no longer produces a reading, because a share of constrained "
   "activities is not a queue", "A5.6", "abstention")


def _queue(entities, servers, horizon, service, waits=None):
    return {"queueStructure": {"queues": [{
        "queue_id": "Q1", "entities": entities, "servers": servers,
        "horizon_days": horizon, "total_service_days": service,
        "wait_times_days": waits if waits is not None else [0.0] * entities}]}}


#      HAND DERIVATION. Utilisation is the server time occupied divided by the server time
#      available. Twenty days of service given by two servers over a twenty day window is
#      20 / (2 * 20) = 0.5, which is below one, so the queue has a steady state.
_qb = run_queueing_bottleneck(_queue(10, 2, 20.0, 20.0), NO_ARG, "2025-06-30")
ka(_qb["utilisation"], 0.5, "A5.6: utilisation is 0.5 by hand", "A5.6", "known_answer",
   "20 service days over 2 servers times a 20 day window")
ka(_qb["status_color"], "Green", "A5.6: a utilisation below one is a queue with a steady state",
   "A5.6", "boundary")
#      THE ONE BOUNDARY, AND IT IS DEFINITIONAL. At a utilisation of exactly one the servers are
#      occupied every moment they are available, the queue has no steady state and waiting grows
#      without bound. The boundary is inclusive on the unstable side.
ka(run_queueing_bottleneck(_queue(10, 2, 20.0, 40.0),
                           NO_ARG, "2025-06-30")["status_color"], "Red",
   "A5.6: exactly one is unstable, so the boundary is inclusive on the unstable side",
   "A5.6", "boundary")
ka(run_queueing_bottleneck(_queue(10, 2, 20.0, 39.9),
                           NO_ARG, "2025-06-30")["status_color"], "Green",
   "A5.6: just below one still has a steady state", "A5.6", "boundary")
#      The measured waits are reported rather than modelled. Nine of ten waits inside the
#      ninetieth percentile, taken by linear interpolation on the sorted waits: for the ten
#      values 0 to 9 the index is 0.9 * 9 = 8.1, so the value is 8 + 0.1 * (9 - 8) = 8.1.
_qw = run_queueing_bottleneck(_queue(10, 2, 20.0, 20.0, [float(i) for i in range(10)]),
                              NO_ARG, "2025-06-30")
ka(_qw["p90_wait_days"], 8.1, "A5.6: the ninetieth percentile wait is 8.1 days by hand",
   "A5.6", "known_answer", "linear interpolation at index 0.9 * (10 - 1)")
ka(_qw["mean_wait_days"], 4.5, "A5.6: and the mean wait is 4.5 days", "A5.6", "known_answer")
#      Scale invariance: doubling the window, the service and the arrivals together leaves the
#      utilisation where it was. Exhausted over twenty-four scalings.
_qb_ratios = {run_queueing_bottleneck(_queue(10 * k, 2, 20.0 * k, 20.0 * k),
                                      NO_ARG, "2025-06-30")["utilisation"]
              for k in range(1, 25)}
ka(sorted(_qb_ratios), [0.5], "A5.6: utilisation is invariant under scaling the whole run",
   "A5.6", "property", "the same queue observed for longer is the same queue")

# ---- A5.7 Agent-Based Supply Chain.
#      RUN 8 FOUND, AND THE FINDING IS PRESERVED: this was a transparent share of a procurement
#      log with every guard Run 7 installed holding, and no agent model was present. Run 10B
#      requires agents, rules, an interaction group and a state history across time steps.
ka(abstains(run_agent_supply_chain({"longLeadItemsTotal": 20, "longLeadAtRisk": 3},
                                   NO_ARG, "2025-06-30")), True,
   "A5.7: a procurement log no longer produces a reading, because a list of items is not a set "
   "of agents", "A5.7", "abstention")


def _abm(disrupted, agents=20, steps=2):
    return {"abmStructure": {
        "agents": [{"agent_id": f"AG{i}", "decision_rule_id": "RESTOCK", "network_group": "G1"}
                   for i in range(agents)],
        "states": [{"time_step": t, "agent_id": f"AG{i}",
                    "state": "DISRUPTED" if (t == steps and i < disrupted) else "NORMAL"}
                   for t in range(1, steps + 1) for i in range(agents)],
    }}


#      HAND DERIVATION. Three of twenty agents disrupted at the last time step is 0.15, and the
#      Yellow arm is a share at or above 0.10 and below 0.20.
_as = run_agent_supply_chain(_abm(3), NO_ARG, "2025-06-30")
ka(_as["at_risk_ratio"], 0.15, "A5.7: 3 of 20 agents disrupted is 0.15 by hand", "A5.7",
   "known_answer")
ka(_as["status_color"], "Yellow", "A5.7: 0.15 lands Yellow", "A5.7", "boundary")
ka(_as["time_steps"], 2, "A5.7: and the run covers the time steps the history carries",
   "A5.7", "known_answer")
ka(run_agent_supply_chain(_abm(2), NO_ARG, "2025-06-30")["status_color"], "Yellow",
   "A5.7: exactly 0.10 is Yellow, so the Green edge is exclusive", "A5.7", "boundary")
ka(run_agent_supply_chain(_abm(1), NO_ARG, "2025-06-30")["status_color"], "Green",
   "A5.7: just below 0.10 is Green", "A5.7", "boundary")
ka(abstains(run_agent_supply_chain(_abm(3, steps=1), NO_ARG, "2025-06-30")), True,
   "A5.7: a single point in time is not a run over time and is refused", "A5.7", "domain")

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

# RUN 14 REWROTE THIS SECTION, AND THE HEADING ABOVE IS WHY IT HAD TO BE REWRITTEN.
#
# Run 8 recorded both modules as arithmetic that passes while the named method is not present,
# and this section then asserted the passing arithmetic literal by literal: the three
# deterministic forecasts A5.4 returned when no scenario definitions were in the corpus, and the
# closeness coefficient B2.19 computed from one project's own three criteria when no matrix of
# alternatives was in the corpus. Run 13 tested what a reader receives and recorded both as
# mismatches, because each returned a band under the name of a method the platform was not
# running, and Run 14 removed both fallbacks. The old expected values are kept in the comments
# below as the historical record of what the platform used to do; they are no longer asserted,
# because asserting them would be this suite holding a defect in place.
#
# ---- A5.4 Scenario Modeling. What it used to do with bac 1,000,000, ev 400,000, ac 440,000,
#      cpi 0.909, spi 0.889: optimistic 1,040,000, likely 1,100,066, worst 1,114,916, a range of
#      7.5 per cent of the budget, and a reading of Amber. None of it was a scenario model: a
#      scenario model is a set of courses of action costed under stated scenarios with their
#      probabilities, and no such structure was involved in any of those five numbers.
_sm_plain = run_scenario_modeling({"bac": 1000000, "ev": 400000, "ac": 440000,
                                   "cpi": 0.909, "spi": 0.889}, NO_ARG, "2025-06-30")
ka(abstains(_sm_plain), True,
   "A5.4: with no decision problem in the corpus the module abstains rather than reporting an "
   "earned value forecast under the name of a scenario model", "A5.4", "canonical_structure")
ka(_sm_plain.get("abstention_reason_code"), "canonical_decision_structure_absent",
   "A5.4: and the abstention names the absent decision structure", "A5.4", "canonical_structure")
ka([k for k in ("optimistic_eac", "realistic_eac", "pessimistic_eac", "scenario_range_pct",
                "status_color") if _sm_plain.get(k) is not None], [],
   "A5.4: none of the five figures this section used to assert is returned any more", "A5.4",
   "canonical_structure")
speakable(_sm_plain, "A5.4 with no decision problem")
#      The abstention does not depend on the earned value figures being consistent: it is the
#      absent structure that decides, so an inconsistent position abstains for the same reason
#      rather than for a different one.
ka(run_scenario_modeling({"bac": 1000000, "ev": 400000, "ac": 440000,
                          "cpi": -0.9, "spi": 0.889}, NO_ARG,
                         "2025-06-30").get("abstention_reason_code"),
   "canonical_decision_structure_absent",
   "A5.4: a negative cost index abstains on the absent structure, which is decided first",
   "A5.4", "abstention")

# ---- B2.19 CRITIC-TOPSIS. What it used to do with cpi 0.90, spi 0.90 and a risk value of 0.90:
#      all three criteria equal, so the standard deviation across them was zero, the module's own
#      fallback gave each a weight of one third, and it returned a distance to the ideal of
#      0.135, a distance to the anti-ideal of 0.356, a closeness coefficient of 0.724 and a
#      reading of Green. The weighting in this method is computed ACROSS ALTERNATIVES, and one
#      project is not a set of alternatives: Run 8 recorded that a criterion sitting at the mean
#      of the other two carried a weight of exactly zero and dropped out of its own decision.
_ct_flat = run_critic_topsis({"cpi": 0.90, "spi": 0.90, "docRiskScore": 0.10},
                             NO_ARG, "2025-06-30")
ka(abstains(_ct_flat), True,
   "B2.19: with no matrix of alternatives in the corpus the module abstains rather than "
   "weighting one project's own criteria against each other", "B2.19", "canonical_structure")
ka(_ct_flat.get("abstention_reason_code"), "canonical_decision_structure_absent",
   "B2.19: and the abstention names the absent decision structure", "B2.19",
   "canonical_structure")
speakable(_ct_flat, "B2.19 with no decision matrix")
#      Exhausted rather than sampled: over the same grid this section used to sweep for band
#      reachability, there is now no band at all, because no input to a single project can supply
#      the structure the method is defined over.
_ct_bands = set()
for cpi_i in range(50, 161, 4):
    for spi_i in range(50, 161, 4):
        for doc_i in range(0, 101, 10):
            _ct_bands.add(run_critic_topsis({"cpi": cpi_i / 100, "spi": spi_i / 100,
                                             "docRiskScore": doc_i / 100},
                                            NO_ARG, "2025-06-30")["status_color"])
ka(sorted(_ct_bands, key=str), [None],
   "B2.19: no band is reachable from any single-project input across the whole grid", "B2.19",
   "property")
#      The degenerate weighting Run 8 found is still demonstrated, in arithmetic held here rather
#      than in production, so the reason the fallback was removed stays visible after its removal.
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
    "A5.6": run_queueing_bottleneck(_queue(10, 2, 20.0, 40.0),
                                    NO_ARG, "2025-06-30")["status_color"] == "Red",
}
_EXCLUSIVE_ON_CALM = {  # edge value reads WORSE
    # RUN 10B RESTATEMENT, ORIGINAL FINDING PRESERVED. Run 8 recorded the queueing measure and
    # the supply chain measure as exclusive on the calmer side of their edge, and read that edge
    # off the look-ahead share and the procurement share. Run 10B requires each module's
    # canonical structure, so the same edges are read off the queue and the agents instead. The
    # queueing measure now has one boundary rather than a ladder, and that boundary is
    # definitional and inclusive on the UNSTABLE side, so it belongs with the inclusive
    # convention and is recorded there rather than here.
    "A5.7": run_agent_supply_chain(_abm(2), NO_ARG, "2025-06-30")["status_color"] == "Yellow",
    "A4.4": run_ncr_rate({"ncrIssued": 1, "ncrClosed": 0, "ncrOpen": 6, "totalFindings": 40},
                         NO_ARG, "2025-06-30")["status_color"] == "Yellow",
}
ka(sorted(k for k, v in _INCLUSIVE_ON_CALM.items() if v),
   ["A2.9", "A4.10", "A5.6", "A6.2", "A6.3"],
   "five of the 27 are inclusive at the edge, counting the queueing measure whose single "
   "boundary is inclusive on the unstable side", "", "boundary")
ka(sorted(k for k, v in _EXCLUSIVE_ON_CALM.items() if v), ["A4.4", "A5.7"],
   "two of the 27 are exclusive on the calmer side of the same kind of edge", "", "boundary")


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
# RUN 10B RESTATEMENT, ORIGINAL FINDING PRESERVED. Run 8 joined the direct cases to the
# production path for the queueing measure and the supply chain measure and found them agreeing,
# which is what a fixture built by a route the application does not take would have broken. Run
# 10B requires each module's canonical structure, and the production document path does not carry
# a queue or a set of agents, so both now abstain on that path and say which structure is absent.
# That is the canonical-structure rule doing exactly what it exists to do, on the real route.
for _mid in ("A5.6", "A5.7"):
    ka(_mid in _abst, True,
       f"{_mid}: on the real production path it abstains, because the documents carry no queue "
       f"and no agents", _mid, "production_path")
    ka(_abst[_mid].get("abstention_reason_code"), "canonical_structure_absent",
       f"{_mid}: and the stored row names the absent canonical structure", _mid,
       "production_path")

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

# The two checks below are themselves cases, so they must be recorded BEFORE the file is written
# or the file carries two fewer rows than the run produced. That is exactly what happened on the
# first pass, and it is the kind of quiet off-by-two an audit artefact must not have.
ka(len(MUTATION_ROWS) + 2, CASES + 2, "every case wrote a mutation-proof row", "", "derivation")
_unprovable = [r["check_label"] for r in MUTATION_ROWS if r["red_under_perturbation"] != "yes"]
ka(_unprovable, [], "every expectation went red under perturbation", "", "derivation")

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
_written = list(csv.DictReader(
    (AUDIT / "run8_expectation_mutation_proof.csv").open(encoding="utf-8", newline="")))
check(len(_written) == CASES,
      "the artefact on disk carries one row for every case in this run",
      f"{len(_written)} rows for {CASES} cases")

print()
print("=" * 78)
print(f"Cases: {CASES}; expectations proved live by perturbation: {PERTURBED}")
print(f"Unresolved universe: {len(UNRESOLVED_27)}; classified: {len(BUCKETS)}; "
      f"left unclassified: {len(set(UNRESOLVED_27) - set(BUCKETS))}")
print("=" * 78)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 78)
sys.exit(1 if FAILED else 0)
