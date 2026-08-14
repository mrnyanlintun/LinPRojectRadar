#!/usr/bin/env python3
"""
Known-answer testing across the taxonomy, after the freeze (Run 6).

THIS SUITE ADDS NO PRODUCTION CODE AND CHANGES NONE. The platform is frozen at sim-2026.08-v2.
Where a case reveals a defect it is asserted as the CURRENT behaviour and named in the report as a
defect, rather than being fixed here.

WHAT A KNOWN-ANSWER CASE IS HERE, and why it is built this way.

1. THE EXPECTED VALUE IS COMPUTED BY HAND FROM THE MODULE'S OWN STATED FORMULA AND WRITTEN AS A
   LITERAL, with the derivation in the comment beside it. Nothing in this file runs a module and
   records what it returned. That is the failure mode which has already occurred twice in this
   project (a chart suite asserting against a hand-maintained copy of the server logic, and
   test_period_series.py carrying a copy with the very divisor defect it was meant to catch), and
   it asserts only that the code equals itself.

2. EVERY KNOWN-ANSWER ASSERTION IS PROVED ABLE TO FAIL BY PERTURBING THE EXPECTED VALUE, not the
   input. `ka()` below checks that the actual value equals the expected one AND that it does not
   equal a perturbation of the expected one. Perturbing the input proves nothing about whether the
   assertion binds; perturbing the expectation proves the comparison is live. The perturbation
   count is reported at the end and a case whose expectation cannot be perturbed is refused.

3. A PROPERTY ASSERTED OVER A DOMAIN IS ASSERTED OVER THE WHOLE DOMAIN, exhausted or randomised.
   A previous run asserted a property that was false and passed because the sample space happened
   to satisfy it.

4. THE FOURTEEN NESTED-INPUT MODULES ARE FED THROUGH THE APPLICATION'S OWN ADAPTER
   (signal_package.build_signals / adapt), not through a package this file assembles itself.

Run:
    PYTHONIOENCODING=utf-8 python tools/test_run6_known_answer.py
"""

from __future__ import annotations

import itertools
import math
import pathlib
import random
import re
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

import app.simulation.fusion as fusion  # noqa: E402
import app.simulation.registry as registry  # noqa: E402
import app.simulation.signal_package as sp  # noqa: E402
from app.simulation.compute import compute_project  # noqa: E402
from app.simulation.models import VALIDATED  # noqa: E402
from app.simulation.models_doc import (  # noqa: E402
    run_co_frequency, run_dispute_escalation, run_quality_compliance, run_rfi_velocity,
    run_safety_performance, run_scenario_modeling, run_sensitivity_analysis,
    run_spec_conflict_density, run_subcontractor_performance, run_submittal_rejection,
    run_tornado_diagram, run_weather_impact, run_agent_supply_chain, run_discrete_event_sim,
    run_queueing_bottleneck, run_procurement_lead_time,
)
from app.simulation.models_evm import (  # noqa: E402
    run_bayesian_eac, run_budget_execution, run_kalman_filter, run_cpi_shrinkage,
)
from app.simulation.models_ext import (  # noqa: E402
    run_contingency_burn, run_critical_path_index, run_inflation_adjustment,
    run_labor_productivity, run_lookahead_health, run_material_cost_variance,
    run_milestone_trend, run_overhead_absorption, run_analogous_estimating,
    run_schedule_compression, run_scurve_deviation,
)
from app.simulation.models_fuzzy import (  # noqa: E402
    run_fermatean_fuzzy, run_hesitant_fuzzy, run_maximum_entropy, run_picture_fuzzy,
    run_possibility_theory, run_pythagorean_fuzzy, run_spherical_fuzzy, run_type2_fuzzy,
)
from app.simulation.models_gov import (  # noqa: E402
    run_constraint_satisfaction, run_contract_mod_frequency, run_whatif_matrix,
)
from app.simulation.models_sim import run_cusum  # noqa: E402
from app.simulation.portfolio import compute_portfolio  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
PASSED = 0
FAILED = 0
PERTURBED = 0
CASES = 0
NOOP = None


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def _perturb(expected):
    """
    A value that is definitely NOT the expected one, of the same kind.

    This is the mechanical form of "change the expected number, confirm red, restore, confirm
    green": if the actual value equals the expected one and does not equal this perturbation, the
    comparison in `ka` is demonstrably live rather than vacuously true. A value that cannot be
    perturbed (None) is refused rather than silently counted.
    """
    if isinstance(expected, bool):
        return not expected
    if isinstance(expected, (int, float)):
        return expected + 1 if expected == 0 else expected * 2 + 1
    if isinstance(expected, str):
        return expected + " (perturbed)"
    if isinstance(expected, (list, tuple)):
        return list(expected) + ["perturbed"]
    if isinstance(expected, dict):
        out = dict(expected)
        out["__perturbed__"] = True
        return out
    if isinstance(expected, (set, frozenset)):
        return set(expected) | {"perturbed"}
    if expected is None:
        return "__not-none__"
    return NOOP


def ka(actual, expected, label: str) -> None:
    """One known-answer case: the value, the hand-computed expectation, and the fail proof."""
    global PERTURBED, CASES
    CASES += 1
    bad = _perturb(expected)
    if bad is NOOP:
        check(False, f"{label}: expectation cannot be perturbed, so the check cannot be proved "
                     f"able to fail", repr(expected))
        return
    live = actual != bad
    if live:
        PERTURBED += 1
    check(actual == expected and live, label,
          f"expected {expected!r} got {actual!r}")


def section(n: str) -> None:
    print()
    print("=" * 78)
    print(n)
    print("=" * 78)


def band(result):
    return result.get("status_color")


def abstains(result) -> bool:
    return result.get("status_color") is None and result.get("insufficient_data") is True


def speakable(result, label: str) -> None:
    """The abstention contract as the ledger renders it: words, no module id, no em dash."""
    reason = result.get("evidence_metric") or ""
    ok = bool(reason.strip())
    ok = ok and not re.search(r"\b[A-D]\d+\.\d+\b", reason)
    ok = ok and "—" not in reason
    ok = ok and "_" not in reason
    check(ok, f"{label}: abstention reason is speakable", reason[:110])


# =================================================================================================
section("0. THE FROZEN-FILE GUARD, RE-BASED BY RUN 7 AND NARROWED RATHER THAN REMOVED")
# =================================================================================================

# WHAT THIS GUARD WAS, WHY IT HAD TO MOVE, AND WHAT IT PROTECTS NOW.
#
# Run 4 froze the analytical layer and this section asserted that NOTHING under server/app/ or
# assets/ differed from origin/main. Run 6 added tests only, so it passed untouched.
#
# Run 7 is authorised by the owner to change production files, scoped to the fix-now defect class
# and the shared eligibility machinery. A guard that compares against origin/main would then be
# comparing this branch with itself the moment the run merged, and a guard that was deleted would
# protect nothing. So it is RE-BASED, deliberately and in one place:
#
#   - the comparison is against a PINNED SHA, the commit this run was cut from, not a branch name,
#     so it keeps meaning the same thing after the merge;
#   - the set of files permitted to differ is enumerated here by name, so a change to any OTHER
#     file under server/app/ or assets/ still fails this check;
#   - assets/ is in the permitted set nowhere at all, so the browser instrument and every
#     participant surface remain byte-identical to the freeze, which is asserted rather than
#     described.
#
# What it no longer protects is the five named files, and that is the whole of what the owner
# authorised. The next run inherits this list and should narrow it back to empty once its own
# scope is settled.

import subprocess  # noqa: E402

#: The commit Run 7 was cut from: origin/main after Run 6 merged. Pinned by sha, never by branch.
GUARD_BASELINE_REV = "021d5e2"

#: The only production files Run 7 is authorised to change. Anything else under server/app/ or
#: assets/ differing from the pinned baseline is a scope breach and fails here.
RUN7_SCOPED_FILES = {
    "server/app/simulation/models.py",
    "server/app/simulation/models_doc.py",
    "server/app/simulation/models_ext.py",
    "server/app/simulation/models_gov.py",
    "server/app/simulation/registry.py",
    # The export carries the abstention reason from the corrected runtime state, which the
    # owner's instruction names as metadata this run may update.
    "server/app/research_export.py",
}

_diff = subprocess.run(["git", "diff", "--name-only", GUARD_BASELINE_REV, "--"],
                       cwd=str(ROOT), capture_output=True, text=True).stdout.split()
_prod = [p for p in _diff if p.startswith("server/app/") or p.startswith("assets/")]
#: RUN 10 adds its own authorised production scope rather than widening Run 7's, so the Run 7
#: record stays exactly as Run 7 left it and each run's authorisation is readable on its own.
#: Run 10 corrects the sixteen modules Run 8 placed in the fix-with-current-data bucket and
#: builds the dedicated forecast fixture family, which touches these files and no others.
RUN10_SCOPED_FILES = {
    "server/app/simulation/models.py",
    "server/app/simulation/models_doc.py",
    "server/app/simulation/models_evm.py",
    "server/app/simulation/models_ext.py",
    "server/app/simulation/models_fuzzy.py",
    "server/app/simulation/models_sim.py",
}

#: RUN 10B adds its own authorised production scope on the same footing, so each run's
#: authorisation stays readable on its own. Run 10B corrects the open input domain in one of the
#: two voting modules and requires the defining structure of six canonical methods and the
#: reference objects of two more, which touches the files above and adds one new file: the
#: canonical-structure layer itself.
RUN10B_SCOPED_FILES = {
    "server/app/simulation/canonical.py",
}

#: RUN 11 adds its own authorised production scope on the same footing. Two parts to it.
#:
#: The analytical part: the seven remaining neighbour defects the Run 10B sweep reproduced and
#: left standing, all non-voting, corrected in the four model files that hold them.
#:
#: THE BROWSER PART, WHICH IS THE FIRST TIME THIS GUARD HAS ADMITTED AN ASSET. Since Run 6 this
#: check has asserted that nothing under assets/ differs from the freeze, and that assertion was
#: right for every run that followed, because none of them was authorised to touch a participant
#: surface. Run 11 Gate 1 is authorised to, and its whole subject is those files: the dormant
#: client-arithmetic call sites on the participant route, and the algorithm version guard. The
#: check below therefore no longer says "nothing under assets/ differs at all"; it says the only
#: assets that differ are the three Run 11 names. The original finding is preserved rather than
#: deleted: every OTHER participant surface is still required to be byte-identical to the freeze,
#: which is what the guard was protecting.
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

#: RUN 14 adds its own authorised production scope, and it is the smallest of the three parts of
#: that run. The numeric contract gains the upper end of the domain it never had (the registry
#: table and the two entry-point validators), the shared analytical preflight applies the same
#: bound to the inputs a module declares, and four model files carry the module-level
#: corrections Run 13's evidence required. No asset, no participant surface, no registry entry,
#: no migration. Every earlier run's list is left exactly as that run left it.
RUN14_SCOPED_FILES = {
    "server/app/field_registry.py",
    "server/app/extraction_merge.py",
    "server/app/simulation/models.py",
    "server/app/simulation/models_ext.py",
    "server/app/simulation/models_doc.py",
    "server/app/simulation/models_dq.py",
    "server/app/simulation/models_fuzzy.py",
}

# RUN 15 replaced the standardised-distance proxy at D1.1 with a real isolation forest, which
# is a new algorithm file and a rewrite of the portfolio module's D1.1 block, and corrected the
# browser method description that still called the module a distance proxy.
RUN15_SCOPED_FILES = {
    "server/app/simulation/portfolio.py",
    "server/app/simulation/isolation_forest.py",
    "server/app/simulation/models.py",
    "assets/js/knowledge.js",
}

# RUN 16 corrected the Signal Flow diagram, which reported the platform's registry counts as
# the project's own activity and animated every connection on a project with no evidence; made
# the clear-all workflow invalidate the results derived from the evidence it clears, which is a
# write-path change; and disabled Material Cost Variance from operational execution, which the
# registry enforces and the export mirrors.
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

# RUN 20 CYCLE 3 (P0D) added the framework-level evidence lineage model: one file carrying the
# nine evidence relationships, the lineage record and the partition that decides which signals
# are one body of evidence. It is a new file rather than an edit; the combination rule and the
# compute entry point that read it are already inside earlier runs' authorised scope.
# RUN 20 CYCLE 9 adds two more, both ARCH.5. arm_lineage.py is a new file: the four assembled
# arm declarations, moved out of models_gov.py unchanged because seven more registered modules
# read the same four arms, together with the weight-free deduplication that gives each
# independent body of evidence exactly one reading. models_evc.py is an EDIT, and it is the one
# file in this list whose module RESULTS move: the six advisory evidence-combination siblings
# aggregated four arms with equal weight per arm when three of those arms are readings of one
# earned-value measurement. Every figure that moved is hand-reworked in this file beside the
# working it replaces, and no band moved on the fixture.
RUN20_SCOPED_FILES = {
    "server/app/simulation/lineage.py",
    "server/app/simulation/qualification_gate.py",
    "server/app/simulation/arm_lineage.py",
    # RUN 20 CYCLE 10, LABEL.1. A new file, and it carries no arithmetic: the truthful
    # method label for every registered name that claims a method the code does not perform,
    # the absent canonical structure in plain words, and the disposition. No band, boundary or
    # constant that any computation reads is in it.
    "server/app/simulation/method_labels.py",
    # RUN 20 CYCLE 11, PARAM.1. Also a new file and also carrying no arithmetic: the class and
    # the provenance of every tunable value in the registry, and the reason nothing is calibrated.
    "server/app/simulation/parameters.py",
    "server/app/simulation/models_evc.py",
    "server/app/simulation/models_fuzzy.py",
    "server/app/simulation/models_doc.py",
    "server/app/simulation/models_decision.py",
}

# RUN 21, QUEUE ITEM 3. The one production file this run changes. `assets/js/simulations.js`
# computes fourteen models in the browser and went on publishing the four regulatory claims Run
# 20 cycle 2 withdrew from the server. It is loaded by `research/deepdive.html` and `tests.html`
# and by NO participant route, so what it misled was the researcher-facing deep-dive page, not a
# participant. Withdrawn to match the server exactly; no band, boundary, threshold or arithmetic
# result changed. See server/tools/run21_production_changes.py and the executed JavaScript-
# against-server parity in server/tools/test_run21_governance_instrument_parity.py.
# RUN 21, section 5 STATE D. `assets/js/neural_flow.js` is the second and last: after the
# supported reset the diagram told the reader the project had no documents while the server
# still held them and was about to read them again. Words only; no count changed.
RUN21_SCOPED_FILES = {
    "assets/js/simulations.js",
    "assets/js/neural_flow.js",
}

# POST-RUN-22 UI CORRECTION. Its production scope, named on the same footing and no wider: the
# Signal Flow diagram, which lit nine platform-DISABLED module dots and three not-applicable
# document rows at the ACTIVE opacity tier on a project with nothing uploaded and nothing
# computed; the detail page's numbered Signal rail, whose SELECTION was spelt with the Signal
# Flow's word for analytical ACTIVITY, was set only by a scroll observer, and whose reset
# blanked the browser copy of the append-only event log; and the stylesheet, where the rail sat
# dimmed until hovered and vanished entirely below 700px. No band, boundary, threshold or
# arithmetic result changed in any of them.
RUN23_SCOPED_FILES = {
    "assets/js/neural_flow.js",
    "assets/js/detail.js",
    "assets/css/radar.css",
}

_unscoped = sorted(set(_prod) - RUN7_SCOPED_FILES - RUN10_SCOPED_FILES - RUN10B_SCOPED_FILES
                   - RUN11_SCOPED_FILES - RUN12_SCOPED_FILES - RUN14_SCOPED_FILES
                   - RUN15_SCOPED_FILES - RUN16_SCOPED_FILES
                   - RUN20_SCOPED_FILES - RUN21_SCOPED_FILES - RUN23_SCOPED_FILES)
check(not _unscoped,
      "no production file outside the authorised scope of Run 7, Run 10, Run 10B, Run 11, "
      "Run 12, Run 14, Run 20 or Run 21 differs from the pinned baseline",
      str(_unscoped))
_assets = sorted(p for p in _prod if p.startswith("assets/"))
# RESTATED BY RUN 11, original finding preserved. Until Run 11 this read "nothing under assets/
# differs at all". Run 11 Gate 1 is authorised to change exactly the browser files that carried
# the dormant client arithmetic, so the assertion narrows to those and keeps its force over
# every other participant surface.
# RUN 21 RESTATES THIS ONE AND RECORDS WHAT IT ACTUALLY MEASURES, because the two are not the
# same and a later reader should not be misled by the label. The check's WORDS say "participant
# surface"; its SET is every file under assets/. simulations.js is under assets/ but is loaded
# only by research/deepdive.html and tests.html and by no participant route, so admitting it
# here does NOT widen the guard over any participant surface. The narrower property -- that no
# file a participant route loads changed -- is asserted separately below, where it can fail on
# its own.
check(not (set(_assets) - RUN11_SCOPED_FILES - RUN12_SCOPED_FILES
           - RUN15_SCOPED_FILES - RUN16_SCOPED_FILES - RUN21_SCOPED_FILES
           - RUN23_SCOPED_FILES),
      "every browser surface outside the authorised browser scope of Runs 11, 12, 15, 16 and 21 "
      "is byte-identical to the freeze",
      str(sorted(set(_assets) - RUN11_SCOPED_FILES - RUN12_SCOPED_FILES
                 - RUN15_SCOPED_FILES - RUN16_SCOPED_FILES - RUN21_SCOPED_FILES
                 - RUN23_SCOPED_FILES)))
# THE NARROWER PROPERTIES, STATED SO EACH CAN FAIL ON ITS OWN, and stated ACCURATELY. The first
# version of this check asserted that no file Run 21 changed is loaded by index.html. That was
# FALSE and the guard said so: simulations.js is not on the participant route, but neural_flow.js
# is, and Run 21 corrected a display-truthfulness defect in it. The property that actually
# matters is not "no participant file changed" -- Run 21 is authorised to fix frontend rendering
# -- but that the PARTICIPANT EXPERIMENTAL PROTOCOL is untouched. Both are asserted below, from
# index.html itself rather than from a hand-kept list.
_index_scripts = set(re.findall(
    r'<script[^>]+src="([^"]+)"', (ROOT / "index.html").read_text(encoding="utf-8")))
_index_assets = {s.lstrip("./") for s in _index_scripts}
check("assets/js/detail.js" in _index_assets and "assets/js/neural_flow.js" in _index_assets,
      "the participant-route script list was actually read, so the checks below are not vacuous",
      str(sorted(_index_assets)[:6]))
check("assets/js/simulations.js" not in _index_assets,
      "simulations.js, whose withdrawn regulatory claims Run 21 removed, is NOT on the "
      "participant route: what it misled was the researcher deep-dive page",
      str(sorted(_index_assets)))
# THE PROTOCOL SURFACE. decision-ui.js is the only shipped browser file that calls the
# preliminary, reveal and final routes, so it is the file the experimental treatment lives in.
# Run 21 must not have touched it.
_protocol = {"assets/js/decision-ui.js"}
check(not (RUN21_SCOPED_FILES & _protocol),
      "Run 21 changed no participant PROTOCOL surface: the preliminary/reveal/final browser "
      "file is untouched", str(sorted(RUN21_SCOPED_FILES & _protocol)))
_decision_ui = (ROOT / "assets" / "js" / "decision-ui.js").read_text(encoding="utf-8")
check(all(k in _decision_ui for k in
          ("researchprejudgment", "researchreveal", "researchdecision")),
      "and that file really is the protocol surface, so the check above is not vacuous")
check(_prod, "the guard is live: it does see the files this run did change", str(_prod))
# RESTATED BY RUN 10B, with the original reason preserved: this check has tracked the current
# stamp since Run 6, and it read sim-2026.08-v4 while Run 10 was current.
# RESTATED BY RUN 28. The stamp now reads sim-2026.08-v11, the analytical line Run 28
# established, and every earlier stamp from sim-2026.07-v1 onward remains the historical audit
# baseline for the results already collected under it. The history is asserted as a whole rather
# than one stamp at a time, so a run that overwrote an earlier stamp instead of appending would
# turn this red.
check(registry.SIMULATION_VERSION == "sim-2026.08-v11",
      "the analytical layer is stamped at Run 28's version",
      registry.SIMULATION_VERSION)
from app.simulation.models import SIMULATION_VERSION_HISTORY as _SVH  # noqa: E402
check(_SVH == ("sim-2026.07-v1", "sim-2026.08-v2", "sim-2026.08-v3", "sim-2026.08-v4",
               "sim-2026.08-v5", "sim-2026.08-v6", "sim-2026.08-v7", "sim-2026.08-v8",
               "sim-2026.08-v9", "sim-2026.08-v10", "sim-2026.08-v11"),
      "every earlier stamp remains recorded as a historical audit baseline, in order, and none "
      "was overwritten or re-used", str(_SVH))
check(_SVH[-1] == registry.SIMULATION_VERSION and len(set(_SVH)) == len(_SVH),
      "the current stamp is the last of the history and no identifier appears twice, so a new "
      "line can never collide with one results were already collected under")


# =================================================================================================
section("1. THE FIVE HELD-NON-VOTING CORE MODULES: known answers on the arithmetic itself")
# =================================================================================================

print("\n-- Look-Ahead Schedule Health (A2.8): ready fraction over a constraint inventory --")
# SUPERSEDED BY RUN 28, which implemented the owner's supplied canonical contract for this
# module. The block below was observed red against the v3 build before being rewritten.
# The v2 quantity was the constraint rate over two bare counts, with a four-band ladder whose
# boundaries the module's own comment recorded as uncited. The contract's quantity is the READY
# fraction over a governed inventory, and it supplies no bands.
# HAND: 200 activities planned, 37 carrying an open constraint. (200 - 37) / 200 = 163/200
# = 0.815.
def _la(planned, constrained, horizon="six week"):
    rows = [{"activity_id": f"ACT-{i}",
             "constraint_status": "OPEN" if i < constrained else "CLEARED",
             **({"constraint_category": "MATERIAL"} if i < constrained else {})}
            for i in range(planned)]
    return {"lookAheadSchedule": {"horizon": horizon, "status_date": "2026-06-30",
                                  "activities": rows}}


r = run_lookahead_health(_la(200, 37), NOOP, "2025-06-30")
ka(r["ready_fraction"], 0.82, "look-ahead 37 of 200: ready fraction 0.815 rounds to 0.82")
ka(r["planned"], 200, "look-ahead: the planned count is derived from the inventory")
ka(r["constrained"], 37, "look-ahead: and so is the constrained count")
ka(r["constraint_categories"], {"MATERIAL": 37}, "look-ahead: constraints carry their kind")
check(r.get("status_color") is None and r.get("calibration_pending") is True,
      "look-ahead: no band is asserted, and the contract supplies none")
# The ready fraction is exact at every point of a grid, so no rounding artefact hides in it.
_exact = True
for c in range(0, 1001, 50):
    rr = run_lookahead_health(_la(1000, c), NOOP, "2025-06-30")
    if abs(rr["ready_fraction"] - round((1000 - c) / 1000, 2)) > 1e-9:
        _exact = False
check(_exact, "look-ahead: the ready fraction is exact across the whole grid (21 windows)")
check(abstains(run_lookahead_health({"activitiesPlanned": 200, "activitiesConstrained": 37},
                                    NOOP, "2025-06-30")),
      "look-ahead: with no constraint inventory the answer is not estimable, and two bare "
      "counts are not used in its place")

print("\n-- Contingency Burn Rate (A3.2): consumed fraction and progress-normalised burn --")
# SUPERSEDED BY RUN 28. The arithmetic is unchanged and is still hand-checked below; what is
# gone is the four-band ladder at 1.0, 1.3 and 1.6, which Run 4 already recorded as uncited and
# which the owner's supplied contract settles by supplying no universal bands at all. The block
# was observed red against the v3 build (KeyError: 'burn_stress') before being rewritten.
# HAND: burned = 1,000,000 - 700,000 = 300,000; consumed fraction 0.30; progress 0.25;
# normalised burn 0.30 / 0.25 = 1.20.
r = run_contingency_burn({"originalContingency": 1000000, "remainingContingency": 700000,
                          "actualPctComplete": 25}, NOOP, "2025-06-30")
ka(r["consumed_fraction"], 0.3, "contingency: consumed fraction 0.30")
ka(r["normalized_burn"], 1.2, "contingency: normalised burn 0.30 / 0.25 = 1.2")
ka(r["burn_rate_pct"], 30, "contingency: burned share 30 per cent")
ka(r["remaining_pct"], 70, "contingency: remaining share 70 per cent")
check(r.get("status_color") is None and r.get("calibration_pending") is True,
      "contingency: no band is asserted, and the contract supplies none")
# The specification's own worked case: original 100, remaining 60, progress one half.
r2 = run_contingency_burn({"originalContingency": 100, "remainingContingency": 60,
                           "actualPctComplete": 50}, NOOP, "2025-06-30")
ka(r2["consumed_fraction"], 0.4, "contingency: the specification's consumed fraction of 0.40")
ka(r2["normalized_burn"], 0.8, "contingency: the specification's normalised burn of 0.80")
# The normalised burn is exact across a grid, and rises as contingency is drawn down.
_mono = []
for remaining in (1000000, 850000, 700000, 550000, 0):
    rr = run_contingency_burn({"originalContingency": 1000000,
                               "remainingContingency": remaining,
                               "actualPctComplete": 25}, NOOP, "2025-06-30")
    _mono.append(rr["normalized_burn"])
check(_mono == sorted(_mono) and len(set(_mono)) == len(_mono),
      "contingency: the normalised burn rises strictly as contingency is drawn down",
      str(_mono))
# With no progress the SECOND figure is withheld rather than the raw share substituted for it.
r3 = run_contingency_burn({"originalContingency": 100, "remainingContingency": 60},
                          NOOP, "2025-06-30")
check(r3.get("normalized_burn") is None and abs(r3["consumed_fraction"] - 0.4) < 1e-9,
      "contingency: with no progress reported the normalised burn is withheld and the raw "
      "consumed share is not published under its name")

print("\n-- Material Cost Variance (|(current - baseline*pct)| / (baseline*pct); .05/.12/.20) --")
# HAND: expected = 2,000,000 * 0.40 = 800,000; variance = (880,000 - 800,000)/800,000 = +0.10;
# |0.10| > 0.05 and <= 0.12, so Yellow. variance_pct = Math.round(10) = 10.
r = run_material_cost_variance({"materialCostBaseline": 2000000, "materialCostCurrent": 880000,
                                "actualPctComplete": 40}, NOOP, "2025-06-30")
ka(band(r), "Yellow", "material variance +10 per cent: band")
ka(r["variance_pct"], 10, "material variance: +10 per cent")
ka(r["evidence_metric"], "Material cost variance: +10% vs expected at current progress",
   "material variance: finding")

for current, expect, why in [
    (840000, "Green", "exactly +0.05"),
    (840800, "Yellow", "+0.051"),
    (760000, "Green", "exactly -0.05, the same edge on the other sign"),
    (759200, "Yellow", "-0.051"),
    (896000, "Yellow", "exactly +0.12"),
    (896800, "Amber", "+0.121"),
    (960000, "Amber", "exactly +0.20"),
    (960800, "Red", "+0.201"),
    (640000, "Red", "-0.20 is Amber's edge, -0.201 is Red"),
]:
    rr = run_material_cost_variance({"materialCostBaseline": 2000000,
                                     "materialCostCurrent": current,
                                     "actualPctComplete": 40}, NOOP, "2025-06-30")
    if why.startswith("-0.20 is"):
        # HAND: 640,000 vs 800,000 expected is -0.20 exactly, which is Amber's inclusive edge.
        expect = "Amber"
    ka(band(rr), expect, f"material variance boundary {why}")

print("\n-- RFI Velocity (two ladders: per week 2/4/8 and overdue share .10/.20/.35) --")
# HAND: 30 requests over 105 days. per30 = Math.round(30/105*300)/10 = Math.round(85.714)/10 = 8.6.
# per_week = Math.round(30/105*70)/10 = Math.round(20)/10 = 2.0, which is Green (<= 2).
# overdue 9 of 30 = 0.30, which is >= 0.20 and < 0.35, so Amber. The worse of the two wins: Amber.
r = run_rfi_velocity({"rfiCount": 30, "rfiPeriodDays": 105, "rfiOverdue": 9}, NOOP, "2025-06-30")
ka(band(r), "Amber", "rfi 30 over 105 days with 9 overdue: band is the worse of the two ladders")
ka(r["rfi_per_30d"], 8.6, "rfi: 8.6 per thirty days")
ka(r["rfi_per_week"], 2.0, "rfi: 2.0 per week")
ka(r["overdue_ratio"], 0.3, "rfi: overdue share 0.3")
ka(r["evidence_metric"], "30 RFIs over 105 days (8.6/30d, 2/week), 9 overdue (30%)",
   "rfi: finding")

# Velocity ladder. The rate is 7 * count / days, so a log period of 700 days makes it exactly
# count / 100.
for count, expect, why in [
    (200, "Green", "exactly 2.0 a week"),
    (400, "Yellow", "exactly 4.0 a week"),
    (800, "Amber", "exactly 8.0 a week"),
    (900, "Red", "9.0 a week"),
    (210, "Yellow", "2.1 a week, one tenth above the first edge"),
    (410, "Amber", "4.1 a week"),
    (810, "Red", "8.1 a week"),
    (190, "Green", "1.9 a week, one tenth below the first edge"),
]:
    rr = run_rfi_velocity({"rfiCount": count, "rfiPeriodDays": 700}, NOOP, "2025-06-30")
    ka(band(rr), expect, f"rfi velocity boundary {why}")
# Overdue ladder, with the velocity ladder pinned Green (100 requests over 350 days is exactly
# 2.0 a week).
for overdue, expect, why in [
    (9, "Green", "0.09, below the first edge"),
    (10, "Yellow", "exactly 0.10, which falls in the WORSE band because the test is strict <"),
    (19, "Yellow", "0.19"),
    (20, "Amber", "exactly 0.20, again the worse band"),
    (34, "Amber", "0.34"),
    (35, "Red", "exactly 0.35, again the worse band"),
]:
    rr = run_rfi_velocity({"rfiCount": 100, "rfiPeriodDays": 350, "rfiOverdue": overdue},
                          NOOP, "2025-06-30")
    ka(band(rr), expect, f"rfi overdue boundary {why}")
# THE INCLUSIVITY FINDING, asserted rather than asserted about: the two ladders inside this one
# module disagree about which side of a boundary is inclusive. The velocity ladder uses <=, so the
# edge sits in the calmer band; the overdue ladder uses <, so the edge sits in the worse band.
_vel_edge = run_rfi_velocity({"rfiCount": 2, "rfiPeriodDays": 70}, NOOP, "2025-06-30")
_ovr_edge = run_rfi_velocity({"rfiCount": 100, "rfiPeriodDays": 350, "rfiOverdue": 10},
                             NOOP, "2025-06-30")
ka((band(_vel_edge), band(_ovr_edge)), ("Green", "Yellow"),
   "rfi: the velocity edge is inclusive-calmer and the overdue edge is inclusive-worse, "
   "in the same module")
# THE ROUNDING FINDING: the rate is banded AFTER being rounded to one decimal, so the effective
# step either side of a boundary is a tenth. 204 over 7000 days is 2.04 a week and bands as 2.0.
_rounded = run_rfi_velocity({"rfiCount": 204, "rfiPeriodDays": 700}, NOOP, "2025-06-30")
ka((band(_rounded), _rounded["rfi_per_week"]), ("Green", 2.0),
   "rfi: 2.04 requests a week is rounded to 2.0 before banding and reads Green")

print("\n-- Submittal Rejection Rate (rejected / total; .05 / .15 / .25) --")
# HAND: 12 / 80 = 0.15 exactly; 0.15 <= 0.15, so Yellow. Math.round(0.15*100) = 15.
r = run_submittal_rejection({"submittalsTotal": 80, "submittalsRejected": 12}, NOOP, "2025-06-30")
ka(band(r), "Yellow", "submittal 12 of 80: band")
ka(r["rejection_rate"], 0.15, "submittal: rate 0.15")
ka(r["evidence_metric"], "12 of 80 submittals rejected (15%)", "submittal: finding")
for rejected, expect, why in [
    (50, "Green", "exactly 0.05"),
    (51, "Yellow", "0.051"),
    (49, "Green", "0.049"),
    (150, "Yellow", "exactly 0.15"),
    (151, "Amber", "0.151"),
    (250, "Amber", "exactly 0.25"),
    (251, "Red", "0.251"),
]:
    rr = run_submittal_rejection({"submittalsTotal": 1000, "submittalsRejected": rejected},
                                 NOOP, "2025-06-30")
    ka(band(rr), expect, f"submittal boundary {why}")

print("\n-- The five: domain refusals --")
_core_refusals = [
    ("look-ahead, nothing planned",
     run_lookahead_health, {"activitiesPlanned": 0, "activitiesConstrained": 0}),
    ("look-ahead, more constrained than planned",
     run_lookahead_health, {"activitiesPlanned": 10, "activitiesConstrained": 11}),
    ("look-ahead, negative constrained",
     run_lookahead_health, {"activitiesPlanned": 10, "activitiesConstrained": -1}),
    ("contingency, original of zero",
     run_contingency_burn, {"originalContingency": 0, "remainingContingency": 0,
                            "actualPctComplete": 20}),
    ("contingency, remaining above the original",
     run_contingency_burn, {"originalContingency": 100, "remainingContingency": 101,
                            "actualPctComplete": 20}),
    ("contingency, negative remaining",
     run_contingency_burn, {"originalContingency": 100, "remainingContingency": -1,
                            "actualPctComplete": 20}),
    # RUN 28 MOVED THIS ONE OUT OF THE REFUSAL LIST DELIBERATELY. The supplied contract
    # conditions only the progress-normalised burn on progress, not the consumed fraction, so at
    # nothing complete the consumed fraction is still a real measurement and the normalised burn
    # is withheld. The property the original check protected -- that the raw consumed share is
    # never published as the progress-normalised burn -- is asserted directly in the Contingency
    # Burn Rate block above, which is a stronger statement than a refusal.
    ("material variance, progress absent",
     run_material_cost_variance, {"materialCostBaseline": 100, "materialCostCurrent": 50}),
    ("material variance, zero expected cost",
     run_material_cost_variance, {"materialCostBaseline": 0, "materialCostCurrent": 50,
                                  "actualPctComplete": 40}),
    ("rfi, log period absent",
     run_rfi_velocity, {"rfiCount": 10}),
    ("rfi, log period of zero",
     run_rfi_velocity, {"rfiCount": 10, "rfiPeriodDays": 0}),
    ("rfi, negative count",
     run_rfi_velocity, {"rfiCount": -1, "rfiPeriodDays": 30}),
    ("rfi, more overdue than exist",
     run_rfi_velocity, {"rfiCount": 5, "rfiPeriodDays": 30, "rfiOverdue": 6}),
    ("submittal, empty register",
     run_submittal_rejection, {"submittalsTotal": 0, "submittalsRejected": 0}),
    ("submittal, more rejected than exist",
     run_submittal_rejection, {"submittalsTotal": 5, "submittalsRejected": 6}),
    ("submittal, negative rejected",
     run_submittal_rejection, {"submittalsTotal": 5, "submittalsRejected": -1}),
]
for label, fn, si in _core_refusals:
    try:
        rr = fn(si, NOOP, "2025-06-30")
    except Exception as exc:                                      # noqa: BLE001
        check(False, f"{label}: refuses rather than raising", repr(exc))
        continue
    check(abstains(rr), f"{label}: refuses rather than returning a band", str(band(rr)))
    speakable(rr, label)


# =================================================================================================
section("2. THE THIRTY ADVISORY PROXIES: one known-answer case each, against the qualifier")
# =================================================================================================

print("\n-- Two-sided CUSUM on real schedule-index history (A1.2) --")
# HAND: a flat series [1,1,1,1] against a target of 1 has zero sample variance, so sigma takes the
# documented 0.05 floor; k = 0.5*0.05 = 0.025 and H = 5*0.05 = 0.25. Every increment is
# max(0, 0 + 0 - 0.025) = 0, so both arms stay at zero, maxStat is 0 and nothing breaches.
# 0 >= 0.6 * 0.25 is false, so the status is green.
r = run_cusum({"spi": 1.0, "spiHistory": [1.0, 1.0, 1.0, 1.0]}, NOOP, 0)
ka(band(r), "green", "cusum flat series: green")
ka((r["sigma"], r["k"], r["H"]), (0.05, 0.025, 0.25),
   "cusum flat series: sigma takes the 0.05 floor, k is half of it and H is five times it")
ka((r["max_stat"], r["breached"]), (0.0, False), "cusum flat series: no accumulation, no breach")
ka(r["evidence_metric"], "CUSUM max 0.000 against H 0.250 over 4 periods; no breach",
   "cusum flat series: finding")
# THE QUALIFIER SAYS "two-sided". A one-sided chart would miss a fall below target. HAND: the
# series [1,1,1,0.5] on target 1 has mean 0.875 and sample variance
# ((0.125^2)*3 + (0.375^2))/3 = (0.046875 + 0.140625)/3 = 0.0625, so sigma = 0.25, k = 0.125,
# H = 1.25. The low arm accumulates 0.5 - 0.125 = 0.375 on the last point and the high arm stays
# at 0, so maxStat = 0.375 and the chart has detected a DOWNWARD shift, which is the second side.
r = run_cusum({"spi": 0.5, "spiHistory": [1.0, 1.0, 1.0, 0.5]}, NOOP, 0)
ka((r["sigma"], r["k"], r["H"]), (0.25, 0.125, 1.25),
   "cusum shifted series: sigma 0.25 from the sample, k 0.125, H 1.25")
ka(r["max_stat"], 0.375, "cusum is two-sided: a fall below target accumulates on the low arm")

print("\n-- Bayesian EAC (A1.3): a governed normal-normal update --")
# SUPERSEDED BY RUN 28, observed red against the v3 build (KeyError: 'posterior_eac') before
# being rewritten. The designed constant variances the old block hand-checked -- (0.15*BAC)^2 and
# (BAC(1-CPI)/CPI)^2 -- are gone: the contract requires a stated prior with its source and a
# stated observation model, and the module abstains without them.
# HAND, and it is the specification's own worked example: prior N(100, 100), y = 120,
# sigma^2 = 100. Posterior variance 1/(1/100 + 1/100) = 50; posterior mean 50*(100/100 + 120/100)
# = 50 * 2.2 = 110.
_BM = {"parameter": "cost at completion",
       "prior": {"mean": 100.0, "variance": 100.0, "source": "approved budget baseline"},
       "likelihood": {"observation": 120.0, "variance": 100.0,
                      "source": "reported cost at completion",
                      "variance_basis": "residual spread of reported forecasts"}}
r = run_bayesian_eac({"bayesianEacModel": _BM}, NOOP, "2025-06-30")
ka(round(r["posterior_eac"], 6), 110.0, "bayesian eac: posterior mean 110")
ka(r["posterior_variance"], 50.0, "bayesian eac: posterior variance 50")
ka(r["prior_source"], "approved budget baseline", "bayesian eac: the prior states its source")
check(r["credible_low"] < r["posterior_eac"] < r["credible_high"],
      "bayesian eac: a credible interval is reported and brackets the posterior mean")
check(r.get("status_color") is None and r.get("calibration_pending") is True,
      "bayesian eac: no band is asserted on a governed posterior")
# The posterior is a genuine precision-weighted average: doubling the prior's precision must
# pull it toward the prior, which a designed scale-free variance could not do.
r2 = run_bayesian_eac({"bayesianEacModel": {**_BM,
                                            "prior": {**_BM["prior"], "variance": 50.0}}},
                      NOOP, "2025-06-30")
check(r2["posterior_eac"] < r["posterior_eac"],
      "bayesian eac: a tighter prior pulls the posterior toward the prior mean",
      f"{r2['posterior_eac']} vs {r['posterior_eac']}")
check(abstains(run_bayesian_eac({"bac": 1000000, "ev": 400000, "ac": 500000, "cpi": 0.8},
                                NOOP, "2025-06-30")),
      "bayesian eac: with no governed model record the answer is not estimable, and the "
      "designed constant variances are not used in its place")

print("\n-- Kalman SPI smoother (A1.4): a governed scalar state-space recursion --")
# SUPERSEDED BY RUN 28. Q = 0.01 and R = 0.1 were literals with no stated origin; the contract
# requires both to carry provenance and the module abstains without them.
# HAND, the specification's own worked step: x0 = 1, P0 = 1, Q = 0, R = 1, z1 = 2 gives
# P_pred = 1, K = 1/(1+1) = 0.5, x1 = 1 + 0.5*(2-1) = 1.5 and P1 = (1-0.5)*1 = 0.5.
_SSM = {"initial_state": 1.0, "initial_variance": 1.0, "process_variance": 0.0,
        "measurement_variance": 1.0, "observations": [2.0],
        "process_variance_source": "declared random walk, no process noise",
        "measurement_variance_source": "repeated readings of one period across two document "
                                       "types"}
r = run_kalman_filter({"kalmanStateSpaceModel": _SSM}, NOOP, "2025-06-30")
ka(r["smoothed_spi"], 1.5, "kalman: the specification's filtered state of 1.5")
ka(r["final_gain"], 0.5, "kalman: the specification's gain of 0.5")
ka(r["posterior_variance"], 0.5, "kalman: the specification's posterior variance of 0.5")
check(r.get("status_color") is None and r.get("calibration_pending") is True,
      "kalman: no band is asserted on a filtered state")
# The old fixed Q and R reproduced exactly, now as a SUPPLIED model rather than a literal:
# x starts at 0.80 with P = 1, one update at 1.00 gives p = 1.01, gain 1.01/1.11 = 0.909090...,
# x = 0.80 + 0.909090*0.20 = 0.9818181..., which rounds to 0.982.
r2 = run_kalman_filter({"kalmanStateSpaceModel": {
    **_SSM, "initial_state": 0.80, "initial_variance": 1.0, "process_variance": 0.01,
    "measurement_variance": 0.1, "observations": [1.00]}}, NOOP, "2025-06-30")
ka(r2["smoothed_spi"], 0.982, "kalman: one update from 0.80 toward 1.00 gives 0.982")
check(abstains(run_kalman_filter({"spiHistory": [0.80, 1.00]}, NOOP, "2025-06-30")),
      "kalman: with no governed state space record the answer is not estimable, and a fixed Q "
      "and R are not used in its place")
check(abstains(run_kalman_filter({"kalmanStateSpaceModel": {
          **_SSM, "measurement_variance_source": ""}}, NOOP, "2025-06-30")),
      "kalman: a variance that does not say where it came from is refused")

print("\n-- Budget Execution Rate (A1.9): against an approved expenditure baseline --")
# SUPERSEDED BY RUN 28, observed red against the v3 build (KeyError: 'execution_rate') before
# being rewritten. The old denominator was BAC times the reported percent complete, which the
# supplied contract names in terms as the thing this module must NOT manufacture.
# HAND, the specification's own worked case: expected spend 50, actual cost 60, so the execution
# ratio is 60/50 = 1.20 and the deviation is +0.20.
_EXP = {"status_period_index": 3,
        "periods": [{"period_index": i, "expected_spend": v}
                    for i, v in enumerate([10.0, 25.0, 40.0, 50.0])],
        "baseline_version": "BL-1", "approval_source": "approved spend plan"}
r = run_budget_execution({"ac": 60.0, "expenditureBaseline": _EXP}, NOOP, "2025-06-30")
ka(r["execution_ratio"], 1.2, "budget execution: the specification's ratio of 1.20")
ka(r["execution_deviation"], 0.2, "budget execution: and its deviation of +0.20")
ka(r["expected_spend"], 50.0, "budget execution: the planned amount comes off the profile")
check(r.get("status_color") is None and r.get("calibration_pending") is True,
      "budget execution: no band is asserted, and the contract supplies none")
# The profile is read AT the governed status period, so an earlier period reads its own amount
# rather than the last one on the curve.
r2 = run_budget_execution({"ac": 60.0, "expenditureBaseline": dict(_EXP, status_period_index=1)},
                          NOOP, "2025-06-30")
ka(r2["expected_spend"], 25.0, "budget execution: the profile is read at the reported period")
check(abstains(run_budget_execution({"ac": 550000, "bac": 1000000, "actualPctComplete": 50},
                                    NOOP, "2025-06-30")),
      "budget execution: with no approved expenditure profile the answer is not estimable, and "
      "budget times percent complete is not used in its place")

print("\n-- CPI Shrinkage Forecast (A1.10): partial pooling toward a reference population --")
# SUPERSEDED BY RUN 28. Run 6 hand-checked a FIXED one-half shrinkage toward the project's OWN
# history, and asserted over a 289-history grid that the coefficient was never estimated. That
# was a true statement about v2 and is a false one about v3: the owner's Run-28 contract renames
# the module CPI Shrinkage Forecast, requires partial pooling toward a GOVERNED REFERENCE
# POPULATION, and states in terms that a hard-coded 0.5 weight is not acceptable. The old block
# was observed red against this build (ImportError: cannot import name
# 'run_regression_to_mean') before being rewritten. The hand calculation below is the
# specification's own: 0.60 * 0.80 + 0.40 * 1.00 = 0.88.
_REF = {"members": [{"reference_project_id": f"REF-{i}", "cpi_outcome": v}
                    for i, v in enumerate([0.95, 1.00, 1.05])],
        "shrinkage_weight": 0.60,
        "class_membership_basis": "same delivery method and size band",
        "weight_estimation_method": "variance components across the population",
        "data_vintage": "2026-06", "project_stage": "execution"}
r = run_cpi_shrinkage({"cpi": 0.80, "cpiReferenceClass": _REF}, NOOP, "2025-06-30")
ka(r["cpi_shrunk"], 0.88, "CPI shrinkage: 0.88, the specification's own worked answer")
ka(r["mu_reference"], 1.0, "CPI shrinkage: the reference mean is 1.00 across three projects")
ka(r["shrinkage_weight"], 0.60, "CPI shrinkage: the weight is the population's, not one half")
check(r.get("status_color") is None and r.get("calibration_pending") is True,
      "CPI shrinkage: no status band is asserted, which is Run 33's work")
# The weight is now the STRUCTURE'S, asserted over a grid rather than at one point: for every
# weight in the grid the pooled value sits exactly that far from the reference mean, so no fixed
# coefficient survives anywhere in the module.
_weighted = True
for w in [x / 100 for x in range(0, 101, 5)]:
    rr = run_cpi_shrinkage({"cpi": 0.80, "cpiReferenceClass": dict(_REF, shrinkage_weight=w)},
                           NOOP, "2025-06-30")
    if abs(rr["cpi_shrunk"] - (w * 0.80 + (1 - w) * 1.00)) > 0.0006:
        _weighted = False
check(_weighted, "CPI shrinkage: the weight is the reference class's own over the whole grid, "
                 "never a fixed one half (21 weights)")
check(abstains(run_cpi_shrinkage({"cpiHistory": [0.80, 1.00], "cpi": 1.00}, NOOP,
                                 "2025-06-30")),
      "CPI shrinkage: with no reference population the answer is not estimable, and the "
      "project's own history is not used as a substitute population")

# SUPERSEDED BY RUN 28 FOR THE SEVEN MODULES BELOW, each observed red against the v3 build
# before being rewritten. Every hand calculation here is the supplied contract's own worked
# answer, not a number read back out of production.

print("\n-- Schedule Compression Index (A2.4): reconciled remaining duration demand --")
# HAND: two activities, baseline remaining 10 + 10 = 20 days, current remaining 8 + 12 = 20
# days, so the demand ratio is 20/20 = 1.00, which the contract states is equal demand.
def _net(acts, version="SCH-1", basis="2026-06-30 data date"):
    return {"scheduleNetwork": {"schedule_version": version, "status_basis": basis,
                                "activities": acts}}


_SCI_ACTS = [
    {"activity_id": "A", "predecessors": [], "current_duration": 10,
     "baseline_duration": 10, "remaining_duration": 8},
    {"activity_id": "B", "predecessors": ["A"], "current_duration": 10,
     "baseline_duration": 10, "remaining_duration": 12},
]
r = run_schedule_compression(_net(_SCI_ACTS), NOOP, "2025-06-30")
ka(r["schedule_compression_index"], 1.0, "schedule compression: equal demand is 1.00")
ka(r["reconciled_activities"], 2, "schedule compression: both activities reconciled")
check(r.get("status_color") is None and r.get("calibration_pending") is True,
      "schedule compression: no band is asserted")
r2 = run_schedule_compression(_net([dict(a, remaining_duration=a["remaining_duration"] * 2)
                                    for a in _SCI_ACTS]), NOOP, "2025-06-30")
ka(r2["schedule_compression_index"], 0.5,
   "schedule compression: twice the current remaining demand halves the index, which the "
   "contract states is increasing compression pressure")
check(abstains(run_schedule_compression({"baselineStart": "2025-01-01",
                                         "baselineEnd": "2025-12-31",
                                         "actualPctComplete": 50, "spi": 0.80},
                                        NOOP, "2025-06-30")),
      "schedule compression: with no activity network the answer is not estimable, and the "
      "reciprocal of the schedule index is not used in its place")

print("\n-- S-Curve Deviation (A2.6): two cumulative series on one basis --")
# HAND, the specification's own worked case: planned 0.60 against actual 0.50 is a deviation of
# -0.10, and the relative deviation is -0.10/0.60 = -0.1666..., which rounds to -0.17.
def _curve(planned, actual):
    return {"timePhasedBaseline": {
        "baseline_version": "BL-1", "approval_source": "approved baseline",
        "periods": [{"period_index": i, "period": f"P{i}", "cumulative_pv": v}
                    for i, v in enumerate(planned)],
        "cumulative_actual": list(actual)}}


r = run_scurve_deviation(_curve([0.60], [0.50]), NOOP, "2025-06-30")
ka(r["deviation"], -0.1, "s-curve: the specification's deviation of -0.10")
ka(r["relative_deviation"], -0.17, "s-curve: relative deviation -0.10/0.60")
check(r["longitudinal"] is False and r["trend"] is None,
      "s-curve: one point is NOT presented as a longitudinal trend")
r2 = run_scurve_deviation(_curve([0.20, 0.40, 0.60], [0.20, 0.35, 0.50]), NOOP, "2025-06-30")
check(r2["longitudinal"] is True and r2["trend_direction"] == "deteriorating",
      "s-curve: a series gives a trend and says which way it runs")
check(abstains(run_scurve_deviation({"actualPctComplete": 40, "plannedPctComplete": 50,
                                     "ev": 400000, "pv": 500000}, NOOP, "2025-06-30")),
      "s-curve: with no cumulative series the answer is not estimable, and a composite of two "
      "reported percentages is not used in its place")

print("\n-- Milestone Trend Analysis (A2.7): variance against the original commitment --")
# HAND, the specification's own worked case: baseline day 100 with successive forecasts 104, 108
# and 111 gives variances of 4, 8 and 11 days against the ORIGINAL commitment, and drifts of
# 4 and 3 days between successive forecasts.
_MFH = {"milestoneForecastHistory": {"schedule_version": "SCH-1", "milestones": [
    {"milestone_id": "M-FOUNDATION", "original_baseline_day": 100,
     "forecasts": [{"report_index": i, "forecast_day": d}
                   for i, d in enumerate([104, 108, 111])]}]}}
r = run_milestone_trend(_MFH, NOOP, "2025-06-30")
_m = r["milestones"][0]
ka(_m["variance_days"], [4, 8, 11], "milestone trend: the specification's slips of 4, 8 and 11")
ka(_m["period_drift_days"], [4, 3], "milestone trend: the drifts between forecasts")
ka(_m["direction"], "deteriorating", "milestone trend: the direction is deteriorating")
check(abstains(run_milestone_trend({"milestoneHistory": [
          {"at": "2025-01-31", "milestones": [{"name": "F", "forecast": "2025-06-01"}]},
          {"at": "2025-02-28", "milestones": [{"name": "F", "forecast": "2025-06-11"}]}]},
          NOOP, "2025-06-30")),
      "milestone trend: with no forecast history the answer is not estimable, and two snapshots "
      "matched by name are not used in its place")

print("\n-- Labor Productivity Index (A3.3): output per labour hour --")
# HAND, the specification's own worked case: 800 units in 100 hours is 8 an hour, against 1000
# units planned in 100 hours which is 10 an hour, so the index is 8/10 = 0.80.
r = run_labor_productivity({"productionOutputRecord": {
    "output_unit": "cubic yards", "quantity_source": "surveyed installed quantities",
    "earned_output": 800.0, "planned_output": 1000.0,
    "actual_labor_hours": 100.0, "planned_labor_hours": 100.0}}, NOOP, "2025-06-30")
ka(r["actual_productivity"], 8.0, "labour productivity: eight units an hour")
ka(r["planned_productivity"], 10.0, "labour productivity: against ten planned")
ka(r["productivity_index"], 0.8, "labour productivity: the specification's index of 0.80")
check(abstains(run_labor_productivity({"plannedLaborHours": 10000, "actualLaborHours": 8000,
                                       "actualPctComplete": 80}, NOOP, "2025-06-30")),
      "labour productivity: with no comparable output basis the answer is not estimable, and a "
      "hours ratio is not used in its place")

print("\n-- Overhead Absorption Rate (A3.5): rates over an explicit allocation base --")
# HAND, the specification's own worked case: 100 of overhead over a base of 1000 is a planned
# rate of 0.10; 120 over the same 1000 is an actual rate of 0.12; the rate variance is 0.02 and
# the relative variance is 0.02/0.10 = 0.20.
r = run_overhead_absorption({"overheadAllocationBase": {
    "allocation_base": "direct labour hours", "driver_source": "certified payroll",
    "planned_overhead": 100.0, "planned_driver": 1000.0,
    "actual_overhead": 120.0, "actual_driver": 1000.0}}, NOOP, "2025-06-30")
ka(round(r["planned_rate"], 6), 0.1, "overhead absorption: planned rate 0.10")
ka(round(r["actual_rate"], 6), 0.12, "overhead absorption: actual rate 0.12")
ka(round(r["rate_variance"], 6), 0.02, "overhead absorption: rate variance 0.02")
ka(round(r["relative_rate_variance"], 6), 0.2, "overhead absorption: relative variance 0.20")
check(abstains(run_overhead_absorption({"indirectCostPlan": 200000, "indirectCostActual": 90000,
                                        "actualPctComplete": 40}, NOOP, "2025-06-30")),
      "overhead absorption: with no allocation base the answer is not estimable, and the ratio "
      "of actual to planned indirect cost is not used in its place")

print("\n-- Analogous Estimating Ratio (A3.7): an identified analog, adapted --")
# HAND, the specification's own worked example: 100 * 1.20 * 1.10 = 132.
r = run_analogous_estimating({"analogEstimate": {
    "analog_project_id": "PRJ-ANALOG-1", "source": "closed project cost ledger",
    "comparability_criteria": "same structure type, same delivery method",
    "normalization": "constant 2026 dollars", "analog_cost": 100.0,
    "adaptation_factors": [{"factor_name": "size", "factor_value": 1.20},
                           {"factor_name": "location", "factor_value": 1.10}]}},
    NOOP, "2025-06-30")
ka(round(r["adapted_estimate"], 6), 132.0, "analogous estimating: the specification's 132")
ka(r["analog_project_id"], "PRJ-ANALOG-1", "analogous estimating: the analog is identified")
check(abstains(run_analogous_estimating({"analogousOverrunPct": 8, "bac": 5000000},
                                        NOOP, "2025-06-30")),
      "analogous estimating: with no identified analog the answer is not estimable, and a "
      "stored overrun percentage is not used in its place")

print("\n-- Inflation Adjustment Index (A3.9): a named external price index --")
# HAND, the specification's own worked case: an index moving 200 to 220 is a factor of 1.10, so
# an exposure of 100 becomes 110.
_IDX = {"externalCostIndex": {
    "index_name": "Construction Cost Index, all items",
    "authority": "national statistical office", "geography": "national",
    "scope": "construction materials and labour", "base_period": "2020-01",
    "observation_period": "2026-06", "vintage": "2026-07 release",
    "base_index_value": 200.0, "current_index_value": 220.0, "cost_exposure": 100.0}}
r = run_inflation_adjustment(_IDX, NOOP, "2025-06-30")
ka(r["escalation_factor"], 1.1, "inflation adjustment: the specification's factor of 1.10")
ka(round(r["adjusted_cost"], 6), 110.0, "inflation adjustment: and its adjusted cost of 110")
# A FALLING index deflates, which the floored proxy structurally could not show.
r2 = run_inflation_adjustment({"externalCostIndex": {
    **_IDX["externalCostIndex"], "current_index_value": 180.0}}, NOOP, "2025-06-30")
check(r2["escalation_factor"] < 1.0 and r2["escalation_amount"] < 0,
      "inflation adjustment: a falling index is visible as deflation rather than floored at "
      "nothing", str(r2["escalation_factor"]))
check(abstains(run_inflation_adjustment({"materialCostBaseline": 2000000,
                                         "materialCostCurrent": 880000,
                                         "actualPctComplete": 40}, NOOP, "2025-06-30")),
      "inflation adjustment: with no governed external index the answer is not estimable, and "
      "the project's own material price movement is not used in its place")

print("\n-- Weather Day Impact (A4.5): lost days over available float --")
# HAND: 6 lost days against 20 days of float is a ratio of 0.30; lost is not zero, and
# 0.30 > 0.20 and <= 0.50, so Amber. The finding reports Math.round(30) = 30 per cent.
r = run_weather_impact({"weatherDaysLost": 6, "floatRemaining": 20}, NOOP, "2025-06-30")
ka(r["weather_ratio"], 30, "weather impact: 30 per cent of float consumed")
ka(band(r), "Amber", "weather impact: band")
ka(r["evidence_metric"], "6 weather days lost, 30% of available float consumed",
   "weather impact: finding")

print("\n-- Change Order Frequency (A4.6): contract growth plus a raw count --")
# HAND: growth = (11,500,000 - 10,000,000)/10,000,000 * 100 = 15 per cent, count 8.
# The Green arm needs growth <= 5 AND count <= 3: false. Yellow needs <= 10 and <= 6: false.
# Amber needs <= 20 and <= 10: true. So Amber.
r = run_co_frequency({"changeOrderCount": 8, "baselineContractSum": 10000000,
                      "revisedContractSum": 11500000}, NOOP, "2025-06-30")
ka((r["co_count"], r["scope_growth_pct"]), (8, 15), "change order frequency: 8 orders, 15 per cent")
ka(band(r), "Amber", "change order frequency: band")
ka(r["evidence_metric"], "8 change orders, scope growth: +15%", "change order frequency: finding")

print("\n-- Dispute Escalation Index (A4.7): an ad hoc 0.3 / 0.3 / 0.4 weighted sum --")
# HAND: min(10/20, 1) * 0.3 = 0.15; min(5/10, 1) * 0.3 = 0.15; 0.5 * 0.4 = 0.20. Sum 0.50.
# 0.50 > 0.40 and <= 0.65, so Amber.
r = run_dispute_escalation({"rfiCount": 10, "changeOrderCount": 5, "docRiskScore": 0.5},
                           NOOP, "2025-06-30")
ka(r["escalation_index"], 0.5, "dispute escalation: 0.5")
ka(band(r), "Amber", "dispute escalation: band")
# THE WEIGHTS ARE THE ONES THE QUALIFIER NAMES, asserted by isolating each term.
# RUN 7. These three cases used to isolate a term by OMITTING the other two, which is the very
# thing Run 6 found wrong with this module: an omitted source scored zero instead of being
# absent, so the reading improved when evidence was withheld. All three sources are now
# required and a reported zero is a reported zero, so each term is isolated by REPORTING the
# other two as zero. The weights, the saturation points and the expected values are unchanged,
# and each is still derived by hand from the module's own formula.
ka(run_dispute_escalation({"rfiCount": 0, "changeOrderCount": 0, "docRiskScore": 1.0},
                          NOOP, "x")["escalation_index"], 0.4,
   "dispute escalation: the document-risk term carries exactly 0.4")
ka(run_dispute_escalation({"rfiCount": 20, "changeOrderCount": 0, "docRiskScore": 0.0},
                          NOOP, "x")["escalation_index"], 0.3,
   "dispute escalation: the request term carries exactly 0.3 and saturates at twenty")
ka(run_dispute_escalation({"rfiCount": 0, "changeOrderCount": 10, "docRiskScore": 0.0},
                          NOOP, "x")["escalation_index"], 0.3,
   "dispute escalation: the change-order term carries exactly 0.3 and saturates at ten")
# AND THE FINDING TEXT NAMES WHAT THE MODULE COMPUTES. It used to say "RFI velocity" of a raw
# count capped at twenty and "CO frequency" of a raw count capped at ten. Neither term has a
# time or exposure denominator, so neither was a velocity or a frequency.
ka(r["evidence_metric"],
   "Dispute escalation index: 0.5 (document risk, request count and change order count "
   "combined)",
   "dispute escalation: finding names the counts it actually uses")

print("\n-- Subcontractor Performance (A4.8): a precomputed compliance score --")
# HAND: the score is carried through and multiplied by a hundred: 0.72 -> 72.
# 72 >= 70 and < 85, so Yellow. Document risk of 0.40 is above 0.30, so it is named as a signal.
r = run_subcontractor_performance({"subcontractorComplianceScore": 0.72, "docRiskScore": 0.40},
                                  NOOP, "2025-06-30")
ka(r["compliance_score"], 72, "subcontractor performance: 72 per cent")
ka(band(r), "Yellow", "subcontractor performance: band")
ka(r["evidence_metric"],
   "Subcontractor compliance: 72% (elevated document risk (40%)), "
   "from subcontractor performance report",
   "subcontractor performance: finding")

print("\n-- Sensitivity Analysis (A5.2): local CPI perturbation plus deviations --")
# HAND: base forecast 1,000,000/0.90 = 1,111,111.11. The cost term perturbs the index by 0.05
# either way: |1e6/0.85 - 1e6/0.95| / 1,111,111.11 = |1,176,470.59 - 1,052,631.58| / 1,111,111.11
# = 123,839.01/1,111,111.11 = 0.11146. The schedule term is |0.95-1|*0.5 = 0.025 and the document
# term is 0.10, so the cost term is the top driver. 0.11146 > 0.10 and <= 0.20, so Yellow, and the
# reported percentage is Math.round(11.146) = 11.
r = run_sensitivity_analysis({"bac": 1000000, "ev": 400000, "ac": 450000, "pv": 500000,
                              "cpi": 0.90, "spi": 0.95, "docRiskScore": 0.10},
                             NOOP, "2025-06-30")
ka(r["top_driver"], "CPI", "sensitivity analysis: the cost index is the top driver")
ka(r["top_sensitivity"], 11, "sensitivity analysis: 11 per cent")
ka(band(r), "Yellow", "sensitivity analysis: band")

print("\n-- Tornado Risk Ranking (A5.3): four present-state deviations --")
# HAND: cost |1-0.90|*100 = 10; schedule |1-0.95|*100 = 5; document 0.20*100 = 20;
# progress |40-50| = 10. The largest is document risk at 20. The composite is
# (10+5+20+10)/4 = 11.25, which rounds to 11.3 and is above 10 and at or below 20, so Amber.
r = run_tornado_diagram({"cpi": 0.90, "spi": 0.95, "docRiskScore": 0.20,
                         "actualPctComplete": 40, "plannedPctComplete": 50}, NOOP, "2025-06-30")
ka(r["top_risk"], "Document Risk", "tornado: the top risk is document risk")
ka((r["top_impact"], r["composite_score"]), (20, 11.3), "tornado: 20 impact, 11.3 composite")
ka(band(r), "Amber", "tornado: band")
ka(r["evidence_metric"], "Top risk: Document Risk (20% impact)", "tornado: finding")

print("\n-- The eight fuzzy-extension proxies (B2.10 to B2.17) --")
_FZ = {"cpi": 0.95, "spi": 0.92, "docRiskScore": 0.20}
# Every one of these reads only min(cpi, spi) = 0.92 and the document risk score, which is what
# "hard-coded transformations of raw CPI, SPI and document risk" says.

# B2.10 Pythagorean. HAND: mu = (0.92-0.85)/0.15 = 0.466667, nu = (0.95-0.92)/0.15 = 0.2.
# mu^2 + nu^2 = 0.2578 <= 1, so no renormalisation; pi = sqrt(1-0.2578) = 0.86152.
# adjusted mu = 0.466667 * (1 - 0.2*0.3) = 0.466667*0.94 = 0.438667 -> 0.44,
# adjusted nu = min(1, 0.2 + 0.06) = 0.26. Score 0.17867, which is >= 0 and < 0.3, so Yellow.
r = run_pythagorean_fuzzy(_FZ, NOOP, "x")
ka((r["membership"], r["non_membership"], r["hesitancy"]), (0.44, 0.26, 0.86),
   "pythagorean fuzzy: memberships")
ka(band(r), "Yellow", "pythagorean fuzzy: band")
ka(r["evidence_metric"], "PFS: μ=0.44 ν=0.26 π=0.86", "pythagorean fuzzy: finding")

# B2.11 Picture. HAND: positive 0.466667 -> 0.47; negative 0.2 * (1 + 0.2*0.5) = 0.22;
# neutral max(0, 0.6 - 0.466667 - 0.22) * 0.3 = 0; refusal 1 - 0.466667 - 0 - 0.22 = 0.313333
# -> 0.31. Score 0.246667, which is >= 0 and < 0.30, so Yellow.
r = run_picture_fuzzy(_FZ, NOOP, "x")
ka((r["positive"], r["neutral"], r["negative"], r["refusal"]), (0.47, 0, 0.22, 0.31),
   "picture fuzzy: the four memberships")
ka(band(r), "Yellow", "picture fuzzy: band")

# B2.12 Hesitant. HAND: min 0.92, max 0.95, mean 0.935 give memberships 0.466667, 0.666667,
# 0.566667; their average is 1.7/3 = 0.566667 -> 0.57, and the spread is 0.2.
# 0.566667 >= 0.5 and < 0.7, so Yellow.
r = run_hesitant_fuzzy(_FZ, NOOP, "x")
ka(r["memberships"], [0.47, 0.67, 0.57], "hesitant fuzzy: three designed perturbations")
ka((r["average_membership"], r["hesitancy_degree"]), (0.57, 0.2),
   "hesitant fuzzy: average and hesitancy")
ka(band(r), "Yellow", "hesitant fuzzy: band")

# B2.13 Type-2. HAND: primary 0.466667; uncertainty |0.95-0.92|*2 = 0.06; lower 0.436667,
# upper 0.496667, centroid 0.466667 -> 0.47, footprint 0.06. Centroid is below 0.5, so Amber.
r = run_type2_fuzzy(_FZ, NOOP, "x")
ka((r["lower_membership"], r["upper_membership"], r["centroid"],
    r["footprint_of_uncertainty"]), (0.44, 0.5, 0.47, 0.06),
   "type-2 fuzzy: the membership interval is a designed constant multiple of the index gap")
ka(band(r), "Amber", "type-2 fuzzy: band")

# B2.14 Maximum Entropy. HAND: 0.92 is in the middle branch, so the raw probabilities are
# 0.20/0.50/0.25/0.05, summing to 1. Document risk moves the third to 0.25+0.04 = 0.29 and the
# fourth to 0.05+0.02 = 0.07, and the new total is 1.06. The renormalised probabilities are
# 0.18868/0.47170/0.27358/0.06604, so the dominant state is Yellow (47 per cent).
r = run_maximum_entropy(_FZ, NOOP, "x")
ka(r["probabilities"], {"Green": 19, "Yellow": 47, "Amber": 27, "Red": 7},
   "maximum entropy: the renormalised designed probabilities")
ka(band(r), "Yellow", "maximum entropy: the reported status is the argmax, not the entropy")
ka(r["entropy"], 0.87, "maximum entropy: normalised entropy 0.87")

# B2.15 Possibility. HAND: Green min(1, max(0,(0.92-0.85)/0.10) * (1-0.1)) = 0.7*0.9 = 0.63;
# Amber min(1, max(0, 1-(0.92-0.88)/0.10) * (1+0.06)) = 0.6*1.06 = 0.636;
# Red min(1, max(0,(0.92-0.92)/0.10) + 0.08) = 0.08. The largest is Amber.
#
# RUN 20 CYCLE 9. THE HAND WORKING ABOVE IS KEPT AND IS NOW THE WORKING OF THE UNNORMALISED
# MAPS. A possibility distribution is normalised -- at least one element is fully possible -- and
# this one was not: its supremum was 0.636, so on this project NOTHING was fully possible, which
# is not a statement possibility theory can make. Dividing through by the supremum is a monotone
# rescaling, so the DOMINANT BAND CANNOT MOVE and does not: Amber before, Amber after.
#   Green 0.63/0.636 = 0.990566 -> 0.99;  Amber 0.636/0.636 = 1.0;  Red 0.08/0.636 = 0.125786
#   -> 0.13.
# THE NECESSITY WAS NOT A NECESSITY EITHER. It was the possibility less 0.30, a constant with no
# provenance. Necessity is the dual, N(A) = 1 - Pi(not A), and over this three-element frame the
# complement of Amber is {Green, Red}, so N(Amber) = 1 - max(0.990566, 0.125786) = 0.009434,
# which rounds to 0.01. The unnormalised maps are still reported beside the normalised ones so a
# reader can see exactly what was rescaled.
r = run_possibility_theory(_FZ, NOOP, "x")
ka(r["possibility_unnormalised"], {"Green": 0.63, "Amber": 0.64, "Red": 0.08},
   "possibility theory: the fixed mappings from the raw indices, unchanged")
ka(r["possibility"], {"Green": 0.99, "Amber": 1.0, "Red": 0.13},
   "possibility theory: and the distribution normalised so its supremum is one")
ka(band(r), "Amber", "possibility theory: band, which a monotone rescaling cannot move")
ka(r["necessity"]["Amber"], 0.01,
   "possibility theory: necessity is the dual, one less the possibility of the complement, and "
   "not the possibility less an invented 0.3")

# B2.16 Spherical. HAND: mu (0.92-0.82)/0.18 = 0.555556; nu (0.98-0.92)/0.18 = 0.333333, scaled by
# (1 + 0.2*0.5) to 0.366667. mu^2 + nu^2 = 0.44309 <= 1, so no rescale; pi = sqrt(0.55691)
# = 0.74627. Score 0.188889, which is >= 0.1 and < 0.4, so Yellow.
r = run_spherical_fuzzy(_FZ, NOOP, "x")
ka((r["mu"], r["nu"], r["pi"], r["score"]), (0.56, 0.37, 0.75, 0.19),
   "spherical fuzzy: algebraically bounded but fixed memberships")
ka(band(r), "Yellow", "spherical fuzzy: band")

# B2.17 Fermatean. HAND: mu (0.92-0.80)/0.20 = 0.6, nu (1.00-0.92)/0.20 = 0.4.
# mu^3 + nu^3 = 0.216 + 0.064 = 0.28 <= 1, so the renormalisation loop never runs and
# pi = (1-0.28)^(1/3) = 0.72^(1/3) = 0.89628 -> 0.9. Score 0.2, so Yellow.
r = run_fermatean_fuzzy(_FZ, NOOP, "x")
ka((r["mu"], r["nu"], r["pi"]), (0.6, 0.4, 0.9), "fermatean fuzzy: designed memberships")
ka(band(r), "Yellow", "fermatean fuzzy: band")

print("\n-- Contract Modification Frequency (B3.5): a raw modification count --")
# HAND: the same three inputs as change order frequency. count 8 is not >= 10 and growth 15 is not
# >= 20, so not Red; count 8 >= 6, so Amber.
r = run_contract_mod_frequency({"changeOrderCount": 8, "baselineContractSum": 10000000,
                                "revisedContractSum": 11500000}, NOOP, "2025-06-30")
ka(band(r), "Amber", "contract modification frequency: band")
ka(r["evidence_metric"],
   "8 contract modifications, 15% scope growth, elevated modification frequency",
   "contract modification frequency: finding")

print("\n-- Constraint Satisfaction Analysis (B4.3): an explainable four-rule checklist --")
# HAND: cost 0.92 >= 0.90 true; schedule 0.88 >= 0.90 false; document 0.40 < 0.70 true;
# the fourth rule tests 0.92 > 0.80, true. Three of four, a rate of 0.75, which is >= 0.75, Yellow.
r = run_constraint_satisfaction({"cpi": 0.92, "spi": 0.88, "bac": 1000000, "docRiskScore": 0.40},
                                NOOP, "2025-06-30")
ka((r["satisfied"], r["total"], r["satisfaction_rate"]), (3, 4, 75),
   "constraint satisfaction: three of four rules, exactly four rules")
ka(band(r), "Yellow", "constraint satisfaction: band")
ka(r["violated_constraints"], ["Schedule constraint (SPI ≥ 0.90)"],
   "constraint satisfaction: the violated rule is named")

print("\n-- What-If Scenario Matrix (B4.4): four deterministic EAC variants --")
# HAND: remaining work 1,000,000 - 400,000 = 600,000.
#   optimistic  500,000 + 600,000        = 1,100,000
#   base        1,000,000/0.80           = 1,250,000
#   pessimistic 1,000,000/(0.80*0.95)    = 1,315,789.47
#   recovery    1,000,000/(0.80*1.05)    = 1,190,476.19
# The range is (1,315,789.47 - 1,100,000)/1,000,000 * 100 = 21.58, rounding to 22, which is
# above 20, so Red.
r = run_whatif_matrix({"bac": 1000000, "ev": 400000, "ac": 500000, "cpi": 0.80, "spi": 0.90},
                      NOOP, "2025-06-30")
ka([s["eac"] for s in r["scenarios"]], [1100000, 1250000, 1315789, 1190476],
   "what-if: exactly four deterministic variants")
ka((r["scenario_range_pct"], r["base_eac"]), (22, 1250000), "what-if: range and base forecast")
ka(band(r), "Red", "what-if: band")

print("\n-- Portfolio Outlier Detection (D1.2): an empirical CPI and SPI percentile rank --")
# HAND: four projects with distinct indices; the current one is the lowest on both, so its rank on
# each axis is 1/4 = 0.25 (the rank counts the project itself). The composite is 0.25, which is
# > 0.15 and <= 0.30, so Amber, and the reported percentile is 25.
_pf = [{"id": "p1", "cpi": 0.80, "spi": 0.80}, {"id": "p2", "cpi": 0.90, "spi": 0.90},
       {"id": "p3", "cpi": 1.00, "spi": 1.00}, {"id": "p4", "cpi": 1.10, "spi": 1.10}]
out = compute_portfolio(_pf, "p1", None, "2025-06-30")["results"]["cat8_2_portfolio_outlier"]
ka((out["cpi_percentile"], out["spi_percentile"], out["composite_percentile"]), (25, 25, 25),
   "portfolio outlier: the worst of four ranks at the twenty-fifth percentile")
ka(band(out), "Amber", "portfolio outlier: band")
# THE SMALL-N BEHAVIOUR THE QUALIFIER ADMITS, made concrete. With two projects the WORST one ranks
# at 1/2, which is above every boundary, so a project that is the worst in its portfolio reads
# Green. This is a known answer for the formula, not a defect introduced here.
_pf2 = [{"id": "p1", "cpi": 0.50, "spi": 0.50}, {"id": "p2", "cpi": 1.20, "spi": 1.20}]
out2 = compute_portfolio(_pf2, "p1", None, "2025-06-30")["results"]["cat8_2_portfolio_outlier"]
ka((out2["composite_percentile"], band(out2)), (50, "Green"),
   "portfolio outlier: in a two-project portfolio the worst project reads Green, because the "
   "rank counts the project itself")


# =================================================================================================
section("3. THE TWELVE NEWLY WIRED MODULES: known answers against the assembled package")
# =================================================================================================

# The package is built by the application's own adapter from a flat dictionary plus this run's own
# module results, exactly as registry.run_all does. Nothing here assembles a nested package by
# hand.

def package(flat: dict, mc: dict | None, cusum: dict | None, array: list | None = None,
            decision=None) -> dict:
    computed = []
    if mc is not None:
        computed.append(dict(mc, module_id="A1.1"))
    if cusum is not None:
        computed.append(dict(cusum, module_id="A1.2"))
    signals, _absence = sp.build_signals(flat, computed)
    return sp.adapt(flat, signals, decision=decision, signal_array=array or [])


_FLAT_RED = {"cpi": 0.85, "spi": 0.85, "bac": 1000000, "docRiskScore": 0.80}
_MC_RED = {"status_color": "red", "overrun_pct_p80": 18.0, "p80_eac": 1180000, "p50_eac": 1100000}
_CU_RED = {"status_color": "red", "breached": True, "max_stat": 2.0, "H": 1.0}

print("\n-- What the adapter assembles, asserted before anything reads it --")
_sig, _abs = sp.build_signals(_FLAT_RED, [dict(_MC_RED, module_id="A1.1"),
                                          dict(_CU_RED, module_id="A1.2")])
# HAND: evmStatus(0.85, 0.85) takes the first arm because cpi < 0.90, so "red".
# docStatus(0.80) takes the first arm because 0.80 >= 0.70, so "red".
ka(_sig["evm"]["status"], "red", "adapter: the index pair assembles to red")
ka(_sig["doc"]["status"], "red", "adapter: a document risk of 0.80 assembles to red")
ka(_sig["mc"]["p80DeltaPct"], 18.0,
   "adapter: the forecast overrun is carried on the key the modules actually read")
ka(_abs, {}, "adapter: with all four signals present nothing is recorded absent")

_PKG = package(_FLAT_RED, _MC_RED, _CU_RED)

print("\n-- B1.1 Conservative Dominance and B3.1 ABM Governance --")
# HAND: all four assembled signals normalise to Red, so the most adverse band any of them reads
# is Red, and under a dominance rule that is the answer. The conflict class is still the decision
# layer's, Multi-signal red-review, and the decision layer's own state is still Red-review, which
# escalates, so B3.1's action and authority are the escalation pair.
#
# RUN 20 CYCLE 9. THE EXPECTED STATE WAS "Red-review" BECAUSE THE MODULE RETURNED THE DECISION
# LAYER'S COUNTING STATE RATHER THAN A DOMINANCE STATE. That is what the P1 finding was: two or
# more Reds escalated and a LONE Red did not, so adverse evidence was outvoted by the count of
# the signals with nothing adverse to say. On this fixture all four are Red, so both rules agree
# that the answer is adverse and only the NAME of the state changes -- which is exactly why the
# fixture that separates them is the lone-Red one, checked in the cycle 9 suite. Both states are
# now reported, so nothing is hidden by the change.
r = registry.run_module("B1.1", _PKG, NOOP, "2025-06-30")
ka((r["state"], r["conflict"]), ("Red", "Multi-signal red-review"),
   "conservative dominance: four red signals dominate to Red")
ka(r["decision_layer_state"], "Red-review",
   "conservative dominance: and the decision layer's own state is still reported beside it")
ka(r["evidence_metric"], "Red: Multi-signal red-review", "conservative dominance: finding")
r = registry.run_module("B3.1", _PKG, NOOP, "2025-06-30")
ka((r["action"], r["authority"]),
   ("Recovery-plan review and management escalation", "Program director / PMO lead"),
   "abm governance: the escalation action and authority")

print("\n-- B2.1 Dempster-Shafer evidence combination --")
# HAND, worked in full because this is the module the audit's fourth finding names.
# The four sources on this input are
#   index pair, min 0.85 < 0.90        : G .05  A .15  R .75  U .05
#   forecast overrun 18 > 10           : G .05  A .10  R .80  U .05
#   trend breached                     : G .05  A .15  R .75  U .05
#   document risk 0.80, not below 0.70 : G .05  A .15  R .75  U .05
# Combining the first two under Dempster's rule with Theta intersecting every state:
#   G .05*.05 + .05*.05 + .05*.05 = .0075
#   A .15*.10 + .15*.05 + .05*.10 = .0275
#   R .75*.80 + .75*.05 + .05*.80 = .6775
#   U .05*.05                     = .0025      sum .715, so K = .285
# Combining that with the third gives K = .2297 and Red = .98752; combining with the fourth gives
# K = .20747 and Red = .99704. Rounded: Green 0, Amber 0, Red 1.0, conflict 0.21.
#
# RUN 20 CYCLE 7. THAT HAND WORKING IS KEPT ABOVE, AND IT IS NOW THE WORKING OF THE DEFECT. The
# arithmetic in it is right and its premise is wrong: it combines FOUR sources as though they
# were four independent bodies of evidence, and they are not. The index pair, the forecast
# overrun and the trend breach are three readings of ONE earned-value measurement, and Dempster's
# rule normalises by a conflict coefficient defined only between INDEPENDENT bodies. Reading one
# body three times is not three sources agreeing; it is one source quoted three times, and the
# 1.00 above is what that manufactures.
#
# The corrected working, from the two bodies the evidence actually holds:
#   earned-value body, most adverse of its three readings: G .05  A .15  R .75  U .05
#   document body, risk 0.80, not below 0.70            : G .05  A .15  R .75  U .05
#   G .05*.05 + .05*.05 + .05*.05 = .0075
#   A .15*.15 + .15*.05 + .05*.15 = .0375
#   R .75*.75 + .75*.05 + .05*.75 = .6375
#   U .05*.05                     = .0025      sum .685, so K = .315
#   Red = .6375 / .685 = .930657. Rounded: Green .01, Amber .05, Red .93, conflict .31.
#
# THE CHECK IS NOT DELETED AND ITS EXPECTATION IS NOW THE NEGATION OF WHAT IT ASSERTED, because a
# deleted check is a check nobody can see was wrong. The band is unchanged at Red: the evidence
# always did say Red, and what was wrong was the certainty attached to it.
r = registry.run_module("B2.1", _PKG, NOOP, "2025-06-30")
ka(band(r), "Red", "dempster-shafer: band")
ka((r["belief_green"], r["belief_amber"], r["belief_red"]), (0.01, 0.05, 0.93),
   "dempster-shafer: belief on Red when TWO bodies of evidence agree, and NOT the 1.0 that "
   "counting one body three times used to produce")
ka(r["conflict_mass"], 0.31, "dempster-shafer: conflict mass 0.31 across the two bodies, and "
   "not the 0.21 that a fourth combination of already-counted evidence used to give")
ka(r["evidence_metric"],
   "Belief: Green 1% · Amber 5% · Red 93% · Conflict mass 31%",
   "dempster-shafer: finding")
ka(r["evidence_bodies"], 2, "dempster-shafer: the module reports two bodies of evidence, not "
   "the four arms it read them through")
ka(r["conflict_estimable"], True, "dempster-shafer: and that its conflict coefficient is "
   "estimable, because there are two independent bodies for it to be estimated across")

print("\n-- B2.2 Rough Sets --")
# HAND: all four ARMS classify Red.
#
# RUN 20 CYCLE 9, ARCH.5. THE HAND WORKING IS KEPT AND ITS PREMISE IS NOW RECORDED AS WRONG, the
# same way cycle 7 kept B2.1's. It counted FOUR classes because there are four arms. There are
# not four bodies of evidence: the index arm, the forecast overrun and the trend breach are three
# readings of ONE earned-value measurement, established by execution in cycle 7. The ratio below
# is a count of classes against the class TOTAL, so those three readings occupied three quarters
# of it on their own. On the cycle 7 fixture that is exactly 0.75, which is the boundary this
# module's lower-approximation test sits on: the duplication was not a rounding effect, it
# decided which side of the boundary the module landed on.
#
# The corrected working, over the two bodies the evidence actually holds: the earned-value body
# reads Red (the most adverse of its three readings, all Red here) and the document body reads
# Red at a risk score of 0.80. Red is 2 of 2, which is 1.0 and still above 0.75, so the lower
# approximation is still exactly {Red} and the classification is still definite. THE BAND AND THE
# CLASSIFICATION ARE UNCHANGED; what changed is the count the module reports, which now says two
# bodies of evidence rather than four quotations of two.
r = registry.run_module("B2.2", _PKG, NOOP, "2025-06-30")
ka((r["lower_approximation"], r["boundary_region"], r["classification"]),
   (["Red"], [], "Definite Red"), "rough sets: a definite lower approximation")
ka(r["evidence_metric"], "Definite Red (Green 0, Amber 0, Red 2 of 2 signals)",
   "rough sets: finding, counted over BODIES of evidence and not over arms")
ka((r["arms_present"], r["bodies_of_evidence"], r["arms_suppressed_as_duplicate"]), (4, 2, 2),
   "rough sets: four arms, two bodies, two arms suppressed as further readings of one body")

print("\n-- B2.3 Neutrosophic Logic --")
# HAND, AND ITS PREMISE IS NOW RECORDED AS WRONG. The old working combined FOUR components --
# (.75,.15,.10) for the index arm, (.75,.15,.10) for the forecast, (.90,.05,.05) for the trend
# and (.75,.15,.10) for the document -- and truth combines DISJUNCTIVELY, so three readings of
# one earned-value measurement drove T to 1.0 on the evidence of one measurement.
#
# The corrected working, over the two bodies: the earned-value body contributes the most adverse
# of its three readings, which is the trend arm at (.90,.05,.05) -- all three are Red, so the tie
# keeps the earliest, the index arm at (.75,.15,.10) -- and the document body contributes
# (.75,.15,.10).
#   T = 1 - (.25 * .25)     = .9375
#   I = .15 * .15           = .0225
#   F = .10 * .10           = .01
#   sum = .97, so T = .9375/.97 = .96649 -> 0.97, I = .0225/.97 = .02320 -> 0.02,
#   F = .01/.97 = .010309 -> 0.01.
# Red is 2 of 2 components, a share of 1.0, which is at least one half, so the status is Red. An
# indeterminacy of 0.02 is not above 0.15, so the level is Low. THE BAND IS UNCHANGED.
r = registry.run_module("B2.3", _PKG, NOOP, "2025-06-30")
ka((r["T"], r["I"], r["F"]), (0.97, 0.02, 0.01),
   "neutrosophic: truth, indeterminacy and falsity over TWO bodies, and not the 1.0 that "
   "combining one body three times disjunctively used to produce")
ka((band(r), r["indeterminacy_level"]), ("Red", "Low"), "neutrosophic: band and level")

print("\n-- B2.4 Interval Fuzzy Sets --")
# HAND: the cost index carries an uncertainty of 0.03 either side, giving [0.82, 0.88]; the
# schedule index carries 0.02, giving [0.83, 0.87]. Green membership is zero below 0.92, so both
# green intervals are [0,0]. Amber rises from 0 at 0.85 to 1 at 0.92, so the cost interval is
# [0, (0.88-0.85)/0.07 = 0.42857] and the schedule interval is [0, 0.28571]. Red falls from 1 at
# 0.85 to 0 at 0.92, so the cost interval is [(0.92-0.88)/0.07 = 0.57143, 1] and the schedule
# interval is [0.71429, 1]. Aggregating by taking the larger endpoint of each pair gives
# green [0,0], amber [0, 0.42857], red [0.71429, 1]; the red midpoint is the largest, so Red.
# The width is (1-0.71429) + (0.42857-0) = 0.71429, which is above 0.3, so High.
r = registry.run_module("B2.4", _PKG, NOOP, "2025-06-30")
ka(band(r), "Red", "interval fuzzy: band")
ka((r["uncertainty_width"], r["uncertainty_level"]), (0.86, "High"),
   "interval fuzzy: the width of the ONE index reading kept, not the span of two readings of "
   "one measurement")
ka(r["evidence_metric"], "Green [0, 0] Amber [0, 0.43] Red [0.57, 1]",
   "interval fuzzy: finding")
ka((r["index_readings_present"], r["index_reading_used"],
    r["index_readings_suppressed_as_same_body"]),
   (2, "cost index", ["schedule index"]),
   "interval fuzzy: two index readings present, one kept, one suppressed as the same body")

print("\n-- B2.5 Z-numbers --")
# HAND, AND ITS PREMISE IS NOW RECORDED AS WRONG. All four restrictions are Red, carrying
# reliabilities 0.85 (indices), 0.90 (trend), 0.65 (document risk) and 0.88 (forecast), and the
# old working SUMMED them to 3.28. A sum of reliabilities is a vote by count: three readings of
# one earned-value measurement summed three reliabilities against the document score's one, so
# that measurement won on how many times it was quoted rather than on evidence.
#
# The corrected working, over the two bodies: the earned-value body contributes one reading, the
# most adverse of its three, all Red, so the tie keeps the earliest -- the index arm at
# reliability 0.85 -- and the document body contributes 0.65. The red total is 1.50, the amber
# and green totals are zero, and the average reliability is 1.50/2 = 0.75. NO RELIABILITY IS
# COMBINED, DISCOUNTED OR INVENTED: the kept reading brings its own, unchanged. The band is
# unchanged at Red.
r = registry.run_module("B2.5", _PKG, NOOP, "2025-06-30")
ka((r["weighted_red"], r["weighted_amber"], r["weighted_green"]), (1.5, 0, 0),
   "z-numbers: reliability totals over the two bodies, not the 3.28 that summing one body's "
   "three readings used to produce")
ka((r["avg_reliability"], band(r)), (0.75, "Red"), "z-numbers: average reliability and band")

print("\n-- B2.6 PLTS --")
# HAND, AND ITS PREMISE IS NOW RECORDED AS WRONG. The four arms contribute (.02,.08,.90) for an
# index minimum below 0.87, (.02,.13,.85) for a breached trend, (.03,.17,.80) for document risk
# at or above 0.70 and (.03,.17,.80) for an overrun above 10, and the old working took the MEAN
# over all four. A mean is a weight: three readings of one earned-value measurement pulled it
# three times as hard as the document score.
#
# The corrected working, over the two bodies: the earned-value body contributes the most adverse
# of its three readings, all Red, so the tie keeps the earliest, the index arm at (.02,.08,.90);
# the document body contributes (.03,.17,.80). The means are .025, .125 and .85, which report as
# 3, 13 and 85 per cent after rounding half up. The band is unchanged at Red.
r = registry.run_module("B2.6", _PKG, NOOP, "2025-06-30")
ka((r["p_green"], r["p_amber"], r["p_red"]), (3, 13, 85),
   "plts: probabilities averaged over the two bodies, not over four quotations of two")
ka(band(r), "Red", "plts: band")

print("\n-- B2.8 Belief Rule Base --")
# HAND, AND ITS PREMISE IS NOW RECORDED AS WRONG. The index minimum is 0.85, so the index state
# is Red, and the trend has breached, so the old working activated R1 -- "EVM Red PLUS trend
# breach" -- whose belief is (.02, .08, .90) at weight 1.00. That rule conditions on the index
# state AND the breach as two facts. They are two readings of one earned-value measurement, so
# the rule base was counting one measurement twice at the point where it decides which rule fires
# at all, and the rule that fires because of the second count is the most extreme in the base.
#
# The corrected working: the earned-value body reads ONE band, the more adverse of the index
# state (Red) and the trend reading (Red, breached), which is Red. The breach stops acting as a
# separate antecedent, so R2 activates -- earned-value body Red -- whose belief is (.05, .25, .70)
# at weight 0.85. With one rule the weighted mean is that belief unchanged: 5, 25 and 70 per
# cent. The band is unchanged at Red, on a belief that no longer counts one measurement twice.
r = registry.run_module("B2.8", _PKG, NOOP, "2025-06-30")
ka((r["belief_green"], r["belief_amber"], r["belief_red"]), (5, 25, 70),
   "belief rule base: the single activated rule's belief, on the earned-value BODY's band and "
   "not on the index state conjoined with a second reading of the same measurement")
ka(r["earned_value_body_state"], "Red",
   "belief rule base: the earned-value body reads Red, the more adverse of its two readings")
ka((r["rules_matched"], band(r)), (1, "Red"), "belief rule base: one rule activated")

print("\n-- B1.2, B1.3 and B1.4, the three voting ensembles --")
# The array is supplied explicitly so the counts are hand-checkable. This is the same shape
# registry.run_all builds from its own results.
_ARRAY = [{"module_id": "X1", "method_class": "X1", "status_color": "Red"},
          {"module_id": "X2", "method_class": "X2", "status_color": "Green"},
          {"module_id": "X3", "method_class": "X3", "status_color": "Amber"}]
_PKG_V = package(_FLAT_RED, _MC_RED, _CU_RED, array=_ARRAY,
                 decision={"state": "Red-review", "conflict": "Multi-signal red-review"})

# HAND, weighted voting: forecast red 1.5, trend red 1.5, document red 1.0, the three array rows
# at 0.6 each (one Red, one Green, one Amber) and the decision state Red-review at 1.5.
# Red = 1.5+1.5+1.0+0.6+1.5 = 6.1, Green = 0.6, Amber = 0.6, Yellow = 0. Total 7.3.
# The dominant share is 6.1/7.3 = 83.56 per cent, rounding to 84.
r = registry.run_module("B1.2", _PKG_V, NOOP, "2025-06-30")
ka(r["votes"], {"Green": 0.6, "Yellow": 0, "Amber": 0.6, "Red": 6.1},
   "weighted voting: the weighted tally")
ka((band(r), r["dominant_pct"]), ("Red", 84), "weighted voting: band and dominant share")

# HAND, majority rules: the same sources without the decision state and unweighted.
# Red 4, Amber 1, Green 1, total 6; 4/6 rounds to 67 per cent.
r = registry.run_module("B1.3", _PKG_V, NOOP, "2025-06-30")
ka(r["counts"], {"Green": 1, "Yellow": 0, "Amber": 1, "Red": 4}, "majority rules: the tally")
ka(r["evidence_metric"], "Red by majority (4 of 6 modules, 67%)", "majority rules: finding")

# HAND, worst N of M: six banded statuses, four Red and one Amber. The Red trigger is
# ceil(6*0.3) = 2, and 4 is at least 2, so Red.
r = registry.run_module("B1.4", _PKG_V, NOOP, "2025-06-30")
ka((r["red_count"], r["amber_count"], r["total_modules"]), (4, 1, 6), "worst n of m: the counts")
ka(r["evidence_metric"], "4 Red + 1 Amber of 6 total modules", "worst n of m: finding")

print("\n-- The two of the fourteen that are disabled refuse before their input is read --")
for mid, name in (("B2.7", "Plithogenic Sets"), ("B2.9", "Quantum Probability")):
    rr = registry.run_module(mid, _PKG_V, NOOP, "2025-06-30")
    check(abstains(rr) and rr["activation_state"] == "DISABLED_UNSAFE"
          and name in rr["evidence_metric"],
          f"{name}: refused as concept-only even on a fully assembled package")

print("\n-- A first period has no trend, and the two governance projections say so --")
_PKG_P1 = package({"cpi": 0.95, "spi": 0.95, "bac": 1000000, "docRiskScore": 0.1},
                  _MC_RED, None)
for mid, label in (("B1.1", "conservative dominance"), ("B3.1", "abm governance")):
    rr = registry.run_module(mid, _PKG_P1, NOOP, "2025-06-30")
    check(abstains(rr), f"{label}: abstains without a performance trend", str(band(rr)))


# =================================================================================================
section("3b. GROUP C, THE PORTFOLIO GROUP AND THE GOVERNANCE THRESHOLDS")
# =================================================================================================

print("\n-- Group C, data and evidence health (seven modules, none of which votes) --")
# C1.1 Missing Data Index. HAND: eleven core fields; supplying four leaves seven missing, a
# missing ratio of 7/11 = 0.63636, which is above 0.45, so Red. Completeness is
# Math.round((1-0.63636)*100) = Math.round(36.36) = 36.
r = registry.run_module("C1.1", {"bac": 1, "ev": 1, "ac": 1, "pv": 1}, NOOP, "2025-06-30")
ka((r["missing_count"], r["total_fields"], r["completeness_pct"]), (7, 11, 36),
   "missing data index: seven of eleven core fields absent")
ka(band(r), "Red", "missing data index: band")

# C1.2 Data Timeliness. HAND: 2025-04-01 to 2025-06-30 is 30 + 31 + 29 = 90 days, and 90 <= 90,
# so Amber. The finding adds the stale note because 90 is above 60.
r = registry.run_module("C1.2", {"docDate": "2025-04-01"}, NOOP, "2025-06-30")
ka(r["days_since_last_doc"], 90, "data timeliness: ninety days")
ka(band(r), "Amber", "data timeliness: band at the inclusive edge")
ka(r["evidence_metric"], "Last document: 2025-04-01 (90 days ago, data may be stale)",
   "data timeliness: finding")
r = registry.run_module("C1.2", {"docDate": "2025-04-02"}, NOOP, "2025-06-30")
ka((r["days_since_last_doc"], band(r)), (89, "Amber"),
   "data timeliness: eighty-nine days is still Amber, so the sixty-day edge is the one below")

# C1.3 Source Reliability. HAND: a pay application weighs 0.90 and OAC minutes 0.55; the mean is
# 0.725, which is >= 0.65 and < 0.80, so Yellow. Nothing is derived, so the finding says measured.
r = registry.run_module("C1.3", {"sources": {"bac": {"docType": "pay_application"},
                                             "rfiCount": {"docType": "oac_minutes"}}},
                        NOOP, "2025-06-30")
ka(r["avg_reliability"], 0.73, "source reliability: mean of 0.90 and 0.55 rounds to 0.73")
ka(band(r), "Yellow", "source reliability: band")
ka(r["evidence_metric"], "Avg source reliability: 73%, all measured",
   "source reliability: finding")

# C1.4 Audit Trail. HAND: both required events are present, so completeness is 1.0, but the Green
# arm additionally requires at least three events and there are two, so it falls to Yellow.
_ev = [{"event": "project_created", "at": "2025-01-01"},
       {"event": "simulation_run", "at": "2025-02-01"}]
r = registry.run_module("C1.4", {"events": _ev}, NOOP, "2025-06-30")
ka((r["completeness_pct"], r["total_events"], r["has_decision_record"]), (100, 2, False),
   "audit trail: both required events present, two events, no decision")
ka(band(r), "Yellow", "audit trail: complete but under the three-event Green condition")

# C1.5 Information Completeness. HAND: nineteen declared fields; four supplied with no source
# entry count as measured, so the ratio is 4/19 = 0.21053, which is below 0.35, so Red, and the
# reported percentage is Math.round(21.05) = 21.
r = registry.run_module("C1.5", {"bac": 1, "ev": 1, "ac": 1, "pv": 1}, NOOP, "2025-06-30")
ka((r["measured"], r["estimated"], r["missing"], r["total"]), (4, 0, 15, 19),
   "information completeness: four measured of nineteen")
ka((r["completeness_ratio"], band(r)), (21, "Red"), "information completeness: band")

# C1.6 Cross-document Consistency. HAND: three checks are possible. The cost index derived from
# 400,000/500,000 is 0.8 and matches; the schedule index derived from 400,000/400,000 is 1.0
# against a reported 0.9, which is inconsistent; the progress derived from 400,000/1,000,000 is
# 40.0 against a reported 40, which matches. Two of three, a score of 0.66667, which is below
# 0.67, so Amber, and the reported percentage is Math.round(66.667) = 67.
r = registry.run_module("C1.6", {"ev": 400000, "ac": 500000, "pv": 400000, "cpi": 0.8,
                                 "spi": 0.9, "bac": 1000000, "actualPctComplete": 40},
                        NOOP, "2025-06-30")
ka((r["checks_performed"], r["inconsistencies"], r["consistency_score"]), (3, 1, 67),
   "cross-document consistency: one of three checks disagrees")
ka(band(r), "Amber", "cross-document consistency: band, because 0.6667 is below the 0.67 edge")

# C1.7 Reporting Frequency. HAND: two extraction events twenty days apart give an average interval
# of twenty days, which is above 14 and at or below 30.
#
# RUN 20, P0B. The band is no longer read from that mean alone. Nothing has been uploaded since
# 2025-01-21 and the period cutoff is 2025-06-30, so the gap since the last report is 160 days:
# 10 remaining in January, then 28 + 31 + 30 + 31 + 30 = 150 through to the end of June. The gap
# is an observed interval too, and it is the one currently running, so the band is the worse of
# the two readings and 160 days is Red. The expectation was Yellow, which reported this project
# by the cadence it once kept rather than the cadence it now has, and it is corrected rather
# than deleted. The mean interval itself is unchanged and still asserted.
_ev2 = [{"event": "signals_extracted", "at": "2025-01-01"},
        {"event": "signals_extracted", "at": "2025-01-21"}]
r = registry.run_module("C1.7", {"events": _ev2}, NOOP, "2025-06-30")
ka((r["avg_interval_days"], r["uploads"]), (20, 2), "reporting frequency: twenty-day interval")
ka(r["gap_since_last_report_days"], 160,
   "reporting frequency: and 160 days have passed since the last one")
ka(band(r), "Red", "reporting frequency: band, taken from the gap since the last report")
ka(r["evidence_metric"],
   "20 day avg interval between document uploads, but nothing has been uploaded for 160 days, "
   "reporting gap, data may be stale",
   "reporting frequency: finding, which now names the gap as well as the mean")

print("\n-- The governance thresholds (B3.2, B3.3, B3.4) and the regret module (B4.7) --")
# B3.2 FAR. HAND: forecast 10,000,000/0.85 = 11,764,705.88, an overrun of 17.647 per cent, which
# rounds to 17.6. 17.6 is above 15 and at or below 25, so Amber, and the headroom is
# 25 - 17.647 = 7.353, rounding to 7.4.
r = registry.run_module("B3.2", {"bac": 10000000, "cpi": 0.85, "ev": 4000000, "ac": 4700000},
                        NOOP, "2025-06-30")
# RUN 20 CYCLE 2 CORRECTED THIS BLOCK, WHICH HAD FOSSILIZED THREE GOVERNANCE OVERCLAIMS AS ITS
# EXPECTED ANSWERS AND CRASHED WITH A KeyError RATHER THAN FAILING WHEN THEY WERE REMOVED.
#
# The hand arithmetic below is unchanged and still correct, because cycle 2 moved no boundary
# and changed no calculation. What it asserted alongside the arithmetic was the defect: the
# field far_reporting_required, which asserted a reporting obligation from a cost ratio; the
# field reporting_triggered under a name taken from OMB Circular A-11; and three fields named
# for a reporting BREACH that measure cost and schedule performance. Each is now asserted under
# the name it carries after the remediation, with the superseded reading stated beside it.
ka((r["overrun_pct"], r["distance_to_threshold"], r["exceeds_review_threshold"]),
   (17.6, 7.4, False),
   "far threshold: overrun, headroom and the internal review level flag, which was "
   "far_reporting_required and asserted a reporting obligation")
ka(band(r), "Amber", "far threshold: band, unchanged by the remediation")
ka((r["review_threshold_pct"], r["threshold_provenance"], r["regulatory_determination"]),
   (25, "UNCITED_INTERNAL_REVIEW_LEVEL", "NOT_MADE"),
   "far threshold: the level is named an internal one, its provenance is carried, and no "
   "regulatory determination is claimed")
ka("far" in r["evidence_metric"].lower(), False,
   "far threshold: the sentence no longer attaches a regulation's name and part number to the "
   "twenty-five, which FAR 34.201 does not state")

# B3.3 OMB A-11. HAND: an index of 0.85 is below 0.90 and the budget is at or above ten million,
# so the internal review condition is met; 0.85 is below 0.88, so Red.
r = registry.run_module("B3.3", {"bac": 10000000, "cpi": 0.85, "actualPctComplete": 40},
                        NOOP, "2025-06-30")
ka((r["cpi_below_90"], r["large_budget"], r["review_condition_met"]), (True, True, True),
   "omb a-11: both conditions and the internal review condition, which was reporting_triggered "
   "and told the reader MANDATORY REPORTING TRIGGERED")
ka(band(r), "Red", "omb a-11: band, unchanged by the remediation")
ka(("mandatory" in r["evidence_metric"].lower(), r["regulatory_determination"]),
   (False, "NOT_MADE"),
   "omb a-11: no obligation is asserted and no determination under the circular is claimed")
# The boundary the module names: a budget one unit below ten million is not a large budget.
r = registry.run_module("B3.3", {"bac": 9999999, "cpi": 0.85, "actualPctComplete": 40},
                        NOOP, "2025-06-30")
ka(r["review_condition_met"], False,
   "omb a-11: the ten-million boundary is inclusive, so one unit below does not meet it")

# B3.4 EVM Reporting Threshold. HAND: cost 0.85 is below the internal review level of 0.90 and
# schedule 0.95 is not, so exactly one is below, which is the Yellow arm whatever the delta.
r = registry.run_module("B3.4", {"bac": 10000000, "cpi": 0.85, "spi": 0.95}, NOOP, "2025-06-30")
ka((r["cpi_below_review_level"], r["spi_below_review_level"], r["both_below_review_level"]),
   (True, False, False),
   "evm reporting threshold: one of the two indices is below the internal review level, where "
   "the three fields were named for a reporting BREACH")
ka(band(r), "Yellow", "evm reporting threshold: band, unchanged by the remediation")
ka((r["reporting_compliance_assessed"], "breach" in r["evidence_metric"].lower()),
   (False, False),
   "evm reporting threshold: the result states that reporting compliance is not assessed here "
   "and the sentence uses no breach language")

# B4.7 Regret Minimization. RUN 6 FOUND THAT GREEN WAS UNREACHABLE; RUN 7 REMOVED THE MODULE'S
# OUTPUT ENTIRELY, AND THIS BLOCK NOW ASSERTS THE SECOND FACT OVER THE SAME EXHAUSTED DOMAIN.
#
# What Run 6 established by hand and this file recorded: the regret matrix and the state
# probabilities were literals with no input dependence, so the expected regrets were always
#   monitor      0*0.3 + 5*0.4 + 30*0.3 = 11
#   investigate  5*0.3 + 0*0.4 + 10*0.3 = 4.5, rounded half up to 5
#   escalate    15*0.3 + 8*0.4 +  0*0.3 = 7.7, rounded half up to 8
# the minimum was always investigate, the two overrides could only move it to escalate, and
# monitor was the only branch that produced Green. Green was therefore unreachable across all
# 3,721 index pairs from 0.70 to 1.30 in hundredths.
#
# Minimax regret is defined by an action by scenario payoff matrix, and the corpus contains
# none, so Run 7's disposition is abstention rather than different literals. The property is
# exhausted over the SAME grid, which is what makes this a stronger assertion than the one it
# replaces: not "no pair produces Green" but "no pair produces any band, any ranking or any
# recommended course at all".
_banded, _ranked = [], []
for _c in [x / 100 for x in range(70, 131)]:
    for _sp in [x / 100 for x in range(70, 131)]:
        _rr = registry.run_module("B4.7", {"cpi": _c, "spi": _sp, "bac": 1}, NOOP, "x")
        if _rr.get("status_color") is not None:
            _banded.append((_c, _sp))
        if "expected_regret" in _rr or "recommended_action" in _rr:
            _ranked.append((_c, _sp))
ka(len(_banded), 0,
   "regret minimization: no band anywhere on the whole index grid (3,721 index pairs), where "
   "the shipped code banded on every one of them and could reach Green on none")
ka(len(_ranked), 0,
   "regret minimization: and no ranking and no recommended course on any of the 3,721 either")
r = registry.run_module("B4.7", {"cpi": 0.92, "spi": 0.99, "bac": 1000000}, NOOP, "2025-06-30")
ka(r["insufficient_data"], True, "regret minimization: it abstains on a complete input")
ka(r["abstention_reason_code"], "canonical_decision_structure_absent",
   "regret minimization: the stable reason names the structure the corpus does not contain")
speakable(r, "regret minimization")

print("\n-- The portfolio group, D1.1, D1.3, D1.4 and D1.5 --")
# HAND, a four-project portfolio of identical vectors except the current one. Each dimension's
# standard deviation is floored at 0.001 only when the variance is exactly zero.
_pfid = [{"id": "a", "cpi": 1.00, "spi": 1.00, "docRiskScore": 0.10, "actualPctComplete": 50},
         {"id": "b", "cpi": 1.00, "spi": 1.00, "docRiskScore": 0.10, "actualPctComplete": 50},
         {"id": "c", "cpi": 1.00, "spi": 1.00, "docRiskScore": 0.10, "actualPctComplete": 50}]
_out = compute_portfolio(_pfid, "a", None, "2025-06-30")["results"]
# RUN 15. D1.1 is a real isolation forest and this case is now a KNOWN ANSWER OF THE PUBLISHED
# ALGORITHM rather than of a distance. With two identical reference projects no attribute admits
# a split, so every tree is a single external node holding both points and the path length is
# 0 + c(2) = 1 exactly. The normaliser is c(2) = 1, so the score is 2 ** (-1/1) = 0.5 exactly,
# which is the value Liu, Ting and Zhou state means the sample holds no distinct anomaly.
ka((_out["cat8_1_isolation_forest"]["anomaly_score"],
    _out["cat8_1_isolation_forest"]["mean_path_length"],
    _out["cat8_1_isolation_forest"]["normaliser"],
    _out["cat8_1_isolation_forest"]["is_anomaly"]), (0.5, 1.0, 1.0, False),
   "isolation forest: a portfolio of identical projects scores exactly one half, the paper's "
   "own no-distinct-anomaly value")
ka(band(_out["cat8_1_isolation_forest"]), "Green", "isolation forest: band")
# Cross-project pattern: the other two projects are at distance zero, so both match, and their
# mean cost index is 1.00, which is at or above 1.00, so Green rather than a distress pattern.
ka((_out["cat8_4_cross_project_pattern"]["similar_project_count"],
    band(_out["cat8_4_cross_project_pattern"])), (2, "Green"),
   "cross-project pattern: a matched cluster performing at plan reads Green, which the ladder "
   "could not reach before the fifteen-defects run")
# Anomaly score: with no usable history the mean is taken over the two terms actually measured,
# the anomaly score (0) and one minus the composite rank (1 - 1.0 = 0), so the composite is 0.
ka((_out["cat8_5_anomaly_score"]["composite_score"], band(_out["cat8_5_anomaly_score"])),
   (0, "Green"),
   "anomaly score: no placeholder third term, so the least anomalous project scores zero")
check("cat8_3_trajectory_classifier" not in _out,
      "trajectory classifier: absent entirely rather than present with a colour, when there is "
      "no history")
# D1.3 Trajectory Classifier. HAND: cost indices of 0.90, 1.00 and 1.10 are TWO intervals of one
# tenth, so the trend is 0.1 per period, not 0.0667. 0.1 >= 0.01, so Green.
_hist = [{"signal_inputs": {"cpi": 0.90}}, {"signal_inputs": {"cpi": 1.00}},
         {"signal_inputs": {"cpi": 1.10}}]
_traj = compute_portfolio(_pfid, "a", _hist, "2025-06-30")["results"][
    "cat8_3_trajectory_classifier"]
ka(_traj["trend"], 0.1,
   "trajectory classifier: the slope divides by intervals, not observations")
ka((band(_traj), _traj["evidence_metric"]), ("Green", "CPI trend: +10% per period"),
   "trajectory classifier: band and finding")


# =================================================================================================
section("4. THE SHARED MACHINERY")
# =================================================================================================

print("\n-- fusion.normalise_status, the one place the vocabulary is recognised --")
_VOCAB = {
    "Green": "Green", "green": "Green", "GREEN": "Green", " Green ": "Green",
    "Yellow": "Yellow", "yellow": "Yellow",
    "Amber": "Amber", "amber": "Amber", "orange": "Amber",
    "Red": "Red", "red": "Red", "Red-review": "Red", "RED-REVIEW": "Red",
    "light-amber": "Yellow",
    "Complete": "Green", "complete": "Green", "blue": "Green",
}
for value, expect in _VOCAB.items():
    ka(fusion.normalise_status(value), expect, f"normalise_status({value!r})")
for value in ("", "   ", None, "purple", "n/a", "unknown", "NA", 0, False, "None"):
    ka(fusion.normalise_status(value), None,
       f"normalise_status({value!r}) refuses rather than returning Green")
# EXHAUSTED over casing rather than sampled: every band in every casing maps to itself.
_cases = True
for b in fusion.BANDS:
    for variant in (b, b.lower(), b.upper(), b.swapcase(), f"  {b}  "):
        if fusion.normalise_status(variant) != b:
            _cases = False
check(_cases, "normalise_status: every band in every casing maps to itself (20 variants)")

print("\n-- fusion.dst_combine, Dempster's rule over four states plus Theta --")
# HAND, and it is the audit's own worked case: two sources each committing 0.8 to Green and
# leaving 0.2 uncommitted. Theta intersects every state, so Green.Theta and Theta.Green both land
# on Green: 0.64 + 0.16 + 0.16 = 0.96 for Green, 0.04 for Theta, and no conflict at all.
_m = {"Green": 0.8, "Yellow": 0.0, "Amber": 0.0, "Red": 0.0, "Unknown": 0.2}
c = fusion.dst_combine(_m, _m)
ka(round(c["conflict"], 10), 0.0, "dst_combine: ignorance is not conflict")
ka(round(c["Green"], 6), 0.96, "dst_combine: Green 0.96")
ka(round(c["Unknown"], 6), 0.04, "dst_combine: Theta 0.04")
# HAND: two sources disagreeing completely, one all Green and one all Red, are entirely in
# conflict, and the guard returns the uniform escape rather than dividing by zero.
c = fusion.dst_combine({"Green": 1.0, "Yellow": 0, "Amber": 0, "Red": 0, "Unknown": 0},
                       {"Green": 0, "Yellow": 0, "Amber": 0, "Red": 1.0, "Unknown": 0})
ka(c["conflict"], 1.0, "dst_combine: total disagreement is total conflict")
ka(c["Green"], 0.2, "dst_combine: total conflict returns the uniform escape rather than dividing "
                    "by zero")
# HAND: a wholly vacuous source is the identity of the rule, so combining with it changes nothing
# and produces no conflict. Asserted over 2,000 random masses rather than at one point.
_rng = random.Random(20260811)


def _mass():
    raw = [_rng.random() for _ in range(5)]
    tot = sum(raw)
    return dict(zip(fusion.STATES, [x / tot for x in raw]))


_identity = _commutes = _sums = _bounded = True
_vac = {"Green": 0.0, "Yellow": 0.0, "Amber": 0.0, "Red": 0.0, "Unknown": 1.0}
for _ in range(2000):
    a, b = _mass(), _mass()
    ab = fusion.dst_combine(a, b)
    ba = fusion.dst_combine(b, a)
    for s in fusion.STATES:
        if abs(ab[s] - ba[s]) > 1e-12:
            _commutes = False
    if abs(ab["conflict"] - ba["conflict"]) > 1e-12:
        _commutes = False
    if abs(sum(ab[s] for s in fusion.STATES) - 1.0) > 1e-9:
        _sums = False
    if not (0.0 <= ab["conflict"] <= 1.0):
        _bounded = False
    idc = fusion.dst_combine(a, _vac)
    for s in fusion.STATES:
        if abs(idc[s] - a[s]) > 1e-12:
            _identity = False
    if abs(idc["conflict"]) > 1e-12:
        _identity = False
check(_commutes, "dst_combine: commutative over 2,000 random mass pairs")
check(_sums, "dst_combine: the combined mass sums to one over 2,000 random pairs")
check(_bounded, "dst_combine: the conflict coefficient stays inside zero to one, 2,000 pairs")
check(_identity, "dst_combine: a wholly vacuous source is the identity, 2,000 pairs")

print("\n-- fusion.dst_fuse, and whether it depends on the order sources arrive in --")
# Dempster's rule is commutative and associative, so a reader is entitled to expect the fused
# result not to depend on the order. dst_fuse applies a half-strength re-combination after each
# Red source, which is applied INLINE, so the question is measured rather than assumed.
# EXHAUSTED over every permutation of every multiset of length 2 to 4 drawn from the four bands.
_status_dep, _conflict_dep, _checked = [], [], 0
for length in (2, 3, 4):
    for combo in itertools.combinations_with_replacement(fusion.BANDS, length):
        statuses, conflicts = set(), set()
        for perm in set(itertools.permutations(combo)):
            f = fusion.dst_fuse(list(perm))
            statuses.add(f["status"])
            conflicts.add(round(f["conflict"], 9))
        _checked += 1
        if len(statuses) > 1:
            _status_dep.append(combo)
        if len(conflicts) > 1:
            _conflict_dep.append((combo, sorted(conflicts)))
print(f"     {_checked} multisets exhausted over every permutation of each")
print(f"     status differs by order in {len(_status_dep)}; conflict differs in "
      f"{len(_conflict_dep)}")
ka(len(_status_dep), 0,
   "dst_fuse: the fused STATUS does not depend on the order sources arrive in, exhausted over "
   "every permutation of every multiset of length 2 to 4")
check(len(_conflict_dep) > 0,
      f"dst_fuse: the reported CONFLICT does depend on that order in {len(_conflict_dep)} of "
      f"{_checked} multisets, because the figure recorded is the last genuine combination and "
      f"which combination is last is decided by arrival order")
if _conflict_dep:
    print(f"     example: {_conflict_dep[0][0]} -> {_conflict_dep[0][1]}")

print("\n-- The rollup: only the two voting modules open a category --")
_SI = {"cpi": 0.92, "spi": 0.90, "bac": 12000000, "ev": 4000000, "ac": 4400000, "pv": 4200000,
       "docRiskScore": 0.35, "actualPctComplete": 35, "plannedPctComplete": 38,
       "activitiesPlanned": 120, "activitiesConstrained": 20,
       "originalContingency": 600000, "remainingContingency": 380000,
       "materialCostBaseline": 3000000, "materialCostCurrent": 1100000,
       "rfiCount": 24, "rfiPeriodDays": 90, "rfiOverdue": 5,
       "submittalsTotal": 60, "submittalsRejected": 9}
res = compute_project(_SI, "scenario-run6", "P1", "2025-06-30")
_voting_cats = {registry.registry_index()[m]["category"] for m in registry.CORE_VOTING_MODULES}
ka(set(res["category_statuses"].keys()), _voting_cats,
   "rollup: exactly the categories carrying a voting module have a fused status")
ka(res["categories_voting"], 1,
   "rollup: one category votes, so project conflict of zero means one source and not agreement")
# RESTATED BY RUN 11 GATE 6, AND THE ORIGINAL FINDING IS THE REASON THE RESTATEMENT EXISTS.
# Run 6 recorded that the rollup's conflict was structurally zero, and named why in the line
# above: one source, not agreement. That finding was correct and it is what Run 11 acted on. A
# zero is now withheld rather than published, because zero is a number the coefficient reaches
# only by never combining anything, and no genuine two-source combine produces it. The assertion
# is therefore that the coefficient is NOT REPORTED under one-lineage voting, and that the state
# says so in words.
ka(res["project_conflict"], None,
   "rollup: with one voting lineage no conflict coefficient is published, because zero would "
   "read as agreement that was never tested")
ka(res["project_conflict_state"], "NOT_ESTIMABLE_SINGLE_LINEAGE",
   "rollup: and the state names why rather than leaving a blank")
_c_cats = {registry.registry_index()[m]["category"] for m in VALIDATED
           if registry.group_of(m) == "C"}
ka(_c_cats & set(res["category_statuses"].keys()), set(),
   "rollup: no data and evidence health category has a fused status on a real computation")
_votes = {m["module_id"] for m in res["modules"] if m.get("votes")}
ka(_votes, set(registry.CORE_VOTING_MODULES),
   "rollup: exactly two modules carry a vote on the stored row")


# =================================================================================================
section("5. ABSTENTION: every module, on an input that carries nothing")
# =================================================================================================

# The sweep that matters: a module handed an EMPTY input dictionary must either abstain or, where
# its whole purpose is to measure absence, band on that absence and say so. A module that returns
# a band from nothing is manufacturing a status. Exhausted over every implemented module.
# HAND, and this is the run's own accounting rather than a number read off a run: two of these
# have absence as their SUBJECT (how many core fields are missing, and how much of the field set
# came from documents), so a band on an empty input is the correct answer for them. The other
# five are the deterministic-constant computations the audit's sixth release blocker names: they
# read an index with a default of 1.0, or no input at all, and report a status about a project
# nothing has been reported for.
#
# RUN 7 CORRECTED THE FIVE. Three of them read the schedule index with a default of 1.0, the
# value of a project exactly on plan, and now require it. The other two read no project input at
# all: the reference-class multipliers and the dependency-matrix coefficients were literals, and
# a project could not move either band. Neither method's defining structure is in the corpus, so
# they abstain unconditionally rather than being handed a proxy that keeps emitting a constant.
# The expected set is therefore the two that measure absence, and no others.
_MEASURES_ABSENCE = {"C1.1", "C1.5"}
_CONSTANT_FROM_NOTHING = set()
_CORRECTED_BY_RUN7 = {"A2.1", "A2.2", "A2.3", "A3.1", "A5.1"}
_banded_on_nothing = []
_raised = []
for mid in sorted(VALIDATED):
    if mid in registry.DISABLED_CONCEPT_ONLY:
        continue
    try:
        rr = registry.run_module(mid, {}, lambda: 0.5, "2025-06-30")
    except Exception as exc:                                       # noqa: BLE001
        _raised.append((mid, repr(exc)))
        continue
    if not abstains(rr):
        _banded_on_nothing.append((mid, rr.get("status_color")))
    else:
        speakable(rr, f"{mid} on an empty input")
check(not _raised, "no module raises on an empty input", str(_raised[:3]))
ka({m for m, _ in _banded_on_nothing}, _MEASURES_ABSENCE,
   "exactly two modules produce a band from an empty input, and both have absence as their "
   "subject: how many core fields are missing, and how much of the field set came from documents")
_still_banding = _CORRECTED_BY_RUN7 & {m for m, _ in _banded_on_nothing}
ka(_still_banding, set(),
   "none of the five Run 7 corrected reports a status about a project nothing has been reported "
   "for, where every one of them did before")
for _m in sorted(_CORRECTED_BY_RUN7):
    _rr = registry.run_module(_m, {}, lambda: 0.5, "2025-06-30")
    ka(_rr.get("insufficient_data"), True, f"{_m} abstains on an input carrying nothing")
    ka(_rr.get("status_color"), None, f"{_m} offers no band on an input carrying nothing")
    check(bool(_rr.get("abstention_reason_code")),
          f"{_m} carries a stable machine reason beside its sentence",
          str(_rr.get("abstention_reason_code")))
    check("_" not in str(_rr.get("evidence_metric")),
          f"{_m} keeps that code OUT of the sentence a reader sees",
          str(_rr.get("evidence_metric"))[:80])

print("\n-- The reason reaches the surface that renders it, not only the stored row --")
# The freeze run found abstention reasons had never rendered: the ledger reads row.abstained, the
# page reads the list projection, and the projection does not carry it. detail.js now grafts it.
# Asserted at the graft, because that is the point the render depends on.
_detail = (ROOT / "assets" / "js" / "detail.js").read_text(encoding="utf-8")
check(re.search(r"abstained", _detail) is not None,
      "detail.js references the abstention list at all")
_graft = re.search(r"\babstained\b\s*[:=]", _detail) or re.search(
    r"\.abstained\s*=", _detail)
check(_graft is not None,
      "detail.js grafts the abstention list onto the row the ledger reads")
_app = (ROOT / "assets" / "js" / "app.js").read_text(encoding="utf-8")
check("abstained" in _app, "the ledger renderer reads the abstention list")
check("getModuleAbstentionReason" in _app and "cat-mod-reason" in _app,
      "the ledger renderer calls the abstention-reason accessor and emits a reason element "
      "under a silent row")
_tax = (ROOT / "assets" / "js" / "taxonomy.js").read_text(encoding="utf-8")
_acc = re.search(r"getModuleAbstentionReason\s*=\s*function[\s\S]{0,900}", _tax)
check(_acc is not None and "abstained" in _acc.group(0),
      "the accessor reads the abstention list off the row, which is the graft the freeze run "
      "installed")
# THE JOIN BETWEEN THE STORED ROW AND THE SURFACE. The renderer reads a reason off an entry keyed
# by the module's method class, matched through the taxonomy. Both keys the accessor needs are
# asserted to be on what the server actually stores, so the two halves cannot drift apart while
# each half's own test stays green.
_absent_run = registry.run_all({}, "scenario-run6", "P1", "2025-06-30")
_shape = {k for e in _absent_run["abstained"] for k in e}
check({"module_id", "reason"} <= _shape,
      "the server stores every abstention as a module id and a reason, which is the pair the "
      "renderer reads", str(sorted(_shape)))
_with_reason = [e for e in _absent_run["abstained"] if e.get("reason")]
check(len(_with_reason) >= 30,
      f"{len(_with_reason)} of {len(_absent_run['abstained'])} abstentions carry a reason for "
      f"the ledger to print")
check(all("_" not in (e["reason"] or "") and "—" not in (e["reason"] or "")
          and not re.search(r"\b[A-D]\d+\.\d+\b", e["reason"] or "")
          for e in _with_reason),
      "every stored reason is speakable: no key name, no module id, no em dash")


# =================================================================================================
section("6. METAMORPHIC CASES")
# =================================================================================================

print("\n-- Rescaling document risk from a zero-to-one scale to a zero-to-one-hundred scale --")
# RESTATED BY RUN 15, ORIGINAL FINDING PRESERVED. Until Run 15 this recorded a real defect of
# the standardised-distance proxy: the distance was invariant to a linear rescale of one
# dimension but the threshold added the raw per-axis spreads together, so rescaling document
# risk moved the classification while leaving the distance unchanged. D1.1 is now a real
# isolation forest, whose split points are drawn uniformly across each attribute's own observed
# range, so a positive linear rescale of one attribute maps the partitioning onto itself. Both
# the score AND the classification are now invariant, which is what the proxy could not manage.
_pfa = [{"id": "a", "cpi": 0.80, "spi": 0.80, "docRiskScore": 0.90, "actualPctComplete": 50},
        {"id": "b", "cpi": 1.00, "spi": 1.00, "docRiskScore": 0.10, "actualPctComplete": 50},
        {"id": "c", "cpi": 1.02, "spi": 1.01, "docRiskScore": 0.12, "actualPctComplete": 50},
        {"id": "d", "cpi": 0.99, "spi": 1.00, "docRiskScore": 0.11, "actualPctComplete": 50}]
_pfb = [dict(p, docRiskScore=p["docRiskScore"] * 100) for p in _pfa]
_ia = compute_portfolio(_pfa, "a", None, "2025-06-30")["results"]["cat8_1_isolation_forest"]
_ib = compute_portfolio(_pfb, "a", None, "2025-06-30")["results"]["cat8_1_isolation_forest"]
check(_ia["anomaly_score"] == _ib["anomaly_score"],
      "isolation forest: the anomaly score is invariant to rescaling document risk",
      f"{_ia['anomaly_score']} vs {_ib['anomaly_score']}")
check(_ia["status_color"] == _ib["status_color"] and _ia["threshold"] == _ib["threshold"],
      "isolation forest: and so is the classification, because the threshold is a threshold on "
      "the score itself and no longer a sum of raw per-axis spreads",
      f"{_ia['status_color']}/{_ia['threshold']} vs {_ib['status_color']}/{_ib['threshold']}")

print("\n-- Scaling the schedule should not change a compression RATIO --")
# SUPERSEDED BY RUN 28, observed red against the v3 build (KeyError: 'compression_ratio') before
# being rewritten. Run 6's finding was that a one-day floor under the denominator broke the scale
# invariance of the declared ratio; Run 7 removed the floor. The v3 quantity is a different one
# -- the ratio of two sums of activity durations taken from two reconciled schedules -- but the
# SAME invariance must hold of it and is what is asserted here: scaling both schedules by any
# positive factor cannot move the demand ratio, because the factor cancels.
def _scale_net(factor, baseline=10.0, remaining=20.0):
    return _net([{"activity_id": "A", "predecessors": [], "current_duration": remaining * factor,
                  "baseline_duration": baseline * factor,
                  "remaining_duration": remaining * factor}])


_long = run_schedule_compression(_scale_net(365.0), NOOP, "2025-06-30")
_short = run_schedule_compression(_scale_net(2.0), NOOP, "2025-06-30")
ka(_long["schedule_compression_index"], 0.5,
   "schedule compression: ten baseline days against twenty current is a demand ratio of 0.5")
ka(_short["schedule_compression_index"], 0.5,
   "schedule compression: the SAME 0.5 on a schedule two orders of magnitude shorter, because "
   "the scale factor cancels out of the ratio")
_FACTORS = (0.5, 1.0, 2.0, 7.0, 30.0, 365.0, 912.5)
_scale_stable = all(
    run_schedule_compression(_scale_net(f), NOOP,
                             "2025-06-30")["schedule_compression_index"] == 0.5
    for f in _FACTORS)
check(_scale_stable,
      "schedule compression: the demand ratio is unmoved at every scale tried, from half a day "
      "to two and a half years")

print("\n-- Adding evidence should not improve a composite index --")
# HAND: Run 6 found that the dispute index added a term per source and never renormalised, so a
# project reporting a request log and a change order log scored 0.8 while the identical project
# reporting neither scored 0.2. Three bands better for withholding the evidence.
#
# Run 7 required all three sources. The project that reports them all is measured on the same
# weighted sum with the same weights and the same bands, and 0.8 is re-derived by hand here:
# min(20/20,1)*0.3 + min(10/10,1)*0.3 + 0.5*0.4 = 0.3 + 0.3 + 0.2 = 0.8. The project that
# withholds a source abstains, so it cannot read better, and that is asserted over EVERY strict
# subset of the three inputs rather than on the one the finding used.
_with = run_dispute_escalation({"rfiCount": 20, "changeOrderCount": 10, "docRiskScore": 0.5},
                               NOOP, "x")
ka(_with["escalation_index"], 0.8,
   "dispute escalation: the project that reports every source still scores 0.8")
_FULL_DISPUTE = {"rfiCount": 20, "changeOrderCount": 10, "docRiskScore": 0.5}
_improved_by_withholding = []
for _r in range(3):
    for _keep in itertools.combinations(sorted(_FULL_DISPUTE), _r):
        _sub = {k: _FULL_DISPUTE[k] for k in _keep}
        _out = run_dispute_escalation(_sub, NOOP, "x")
        if _out.get("status_color") is not None:
            _improved_by_withholding.append(sorted(_sub))
ka(_improved_by_withholding, [],
   "dispute escalation: every strict subset of the three sources abstains, so removing evidence "
   "cannot produce any reading at all, let alone a better one (seven subsets exhausted)")
ka(run_dispute_escalation({"rfiCount": 0, "changeOrderCount": 0, "docRiskScore": 0.5},
                          NOOP, "x")["escalation_index"], 0.2,
   "dispute escalation: a REPORTED zero on both logs is evidence and still computes, at 0.2, "
   "which is the reading the withheld project used to get for free")

print("\n-- Reordering the sources must not change a majority --")
_perm_stable = True
for perm in itertools.permutations(_ARRAY):
    p = package(_FLAT_RED, _MC_RED, _CU_RED, array=list(perm),
                decision={"state": "Red-review", "conflict": "x"})
    if registry.run_module("B1.3", p, NOOP, "x")["counts"] != {"Green": 1, "Yellow": 0,
                                                               "Amber": 1, "Red": 4}:
        _perm_stable = False
check(_perm_stable, "majority rules: invariant to the order of the results array, exhausted over "
                    "all six permutations")

print("\n-- Scaling every count must not change a proportion --")
_ratio_stable = True
for k in range(1, 25):
    rr = run_procurement_lead_time({"longLeadItemsTotal": 10 * k, "longLeadAtRisk": 8 * k,
                                    "longLeadDelayed": 5 * k}, NOOP, "x")
    if rr["risk_ratio"] != 0.65:
        _ratio_stable = False
check(_ratio_stable, "procurement lead time: the weighted disruption ratio is 0.65 for every "
                     "multiple of the audit's own counts, exhausted over 24 scalings")

print("\n-- A constant series must smooth to the constant --")
# SUPERSEDED BY RUN 28: the series now arrives on the governed state-space model rather than as
# a bare history, and Q and R come with it. The PROPERTY is unchanged and is what matters here --
# a filter handed the same reading over and over must settle on it -- so it is asserted over the
# same grid against the same fixed Q and R the old block used.
_flat_ok = True
for v in [x / 100 for x in range(80, 111)]:
    for n in (1, 2, 4, 8):
        rr = run_kalman_filter({"kalmanStateSpaceModel": {
            "initial_state": v, "initial_variance": 1.0, "process_variance": 0.01,
            "measurement_variance": 0.1, "observations": [v] * n,
            "process_variance_source": "declared random walk",
            "measurement_variance_source": "repeated readings of one period"}}, NOOP, "x")
        if abs(rr["smoothed_spi"] - v) > 0.0006:
            _flat_ok = False
check(_flat_ok, "kalman: a constant series smooths to that constant for every level and length "
                "in the grid (124 series)")


# =================================================================================================
section("7. DOMAIN SAFETY: which modules still substitute a value where they should refuse")
# =================================================================================================

# The fifteen-defects run closed several of these. This section proves the REST do not have the
# same problem, rather than assuming the fifteen were all of them. Each case below is a
# zero denominator, an absent input or an out-of-domain value; the expectation recorded is the
# CURRENT behaviour, and where that behaviour is a substituted value it is named in the report as
# a defect the freeze protects rather than fixed here.
_SURVIVORS = []


def domain(fn, si, label, refuses_expected: bool):
    try:
        rr = fn(si, NOOP, "2025-06-30")
    except Exception as exc:                                       # noqa: BLE001
        check(False, f"{label}: refuses rather than raising", repr(exc))
        return
    refuses = abstains(rr)
    if refuses_expected:
        check(refuses, f"{label}: refuses", str(band(rr)))
    else:
        check(not refuses, f"{label}: CURRENT behaviour is a band, not a refusal",
              str(band(rr)))
        _SURVIVORS.append((label, band(rr)))


print("\n-- Guards the fifteen-defects and validate-seven runs installed, still holding --")
domain(run_scenario_modeling, {"bac": 1000000, "ev": 0, "ac": 0, "cpi": 0, "spi": 1},
       "scenario modelling, a cost index of zero", True)
domain(run_scenario_modeling, {"bac": 1000000, "ev": 0, "ac": 0, "cpi": -0.5, "spi": 1},
       "scenario modelling, a negative cost index", True)
domain(run_scenario_modeling, {"bac": 1000000, "ev": 1200000, "ac": 0, "cpi": 1, "spi": 1},
       "scenario modelling, more earned than the budget contains", True)
domain(run_whatif_matrix, {"bac": 1000000, "ev": 0, "ac": 0, "cpi": 0, "spi": 1},
       "what-if matrix, a cost index of zero", True)
domain(run_procurement_lead_time, {"longLeadItemsTotal": 0, "longLeadAtRisk": 1,
                                   "longLeadDelayed": 1},
       "procurement lead time, an empty log", True)
domain(run_procurement_lead_time, {"longLeadItemsTotal": 10, "longLeadAtRisk": 3,
                                   "longLeadDelayed": 5},
       "procurement lead time, more delayed than at risk", True)
domain(run_quality_compliance, {"qualityDeficienciesNoted": 2, "itemsInspected": 5,
                                "itemsFailed": 8},
       "quality compliance, more failed than inspected", True)
domain(run_quality_compliance, {"qualityDeficienciesNoted": 2, "itemsInspected": 0,
                                "itemsFailed": 0},
       "quality compliance, nothing inspected", True)
domain(run_weather_impact, {"weatherDaysLost": 3},
       "weather day impact, no float figure", True)
domain(run_weather_impact, {"weatherDaysLost": -1, "floatRemaining": 5},
       "weather day impact, a negative count of lost days", True)

print("\n-- The same substitution pattern, in the nine modules Run 7 corrected --")
# RUN 6 FOUND NINE MODULES BEYOND THE ORIGINAL FIFTEEN THAT SUBSTITUTED RATHER THAN REFUSED, AND
# EIGHT OF THEM NOW REFUSE. Each was classified into exactly one disposition before it was
# touched, and the classification is what decides whether it refuses at all:
#
#   overhead absorption          zero planned indirect cost      invalid denominator, refuses
#   inflation adjustment         zero progress-adjusted baseline invalid denominator, refuses
#   queueing bottleneck          nothing planned                 invalid denominator, refuses
#   supply chain                 an empty long-lead log          no exposure, refuses
#   schedule compression         a schedule index of zero        invalid denominator, refuses
#   critical path index          no planned progress             invalid denominator, refuses
#   discrete event simulation    no planned progress             invalid denominator, refuses
#   specification conflict       no requests                     no exposure, refuses
#   safety performance           zero incidents reported         a true zero, and it computes
#
# The ninth is the one that proves the classification is doing work rather than refusing
# everywhere: a safety record that was read and recorded no incidents is a measurement, and it
# keeps its band. What it does not keep is the fabricated index beside that band. See below.
domain(run_overhead_absorption, {"indirectCostPlan": 0, "indirectCostActual": 50000,
                                 "actualPctComplete": 40},
       "overhead absorption, an indirect plan of zero", True)
domain(run_inflation_adjustment, {"materialCostBaseline": 0, "materialCostCurrent": 50000,
                                  "actualPctComplete": 40},
       "inflation adjustment, a material baseline of zero", True)
domain(run_queueing_bottleneck, {"activitiesPlanned": 0, "activitiesConstrained": 0},
       "queueing bottleneck, nothing planned", True)
domain(run_agent_supply_chain, {"longLeadItemsTotal": 0, "longLeadAtRisk": 0},
       "supply chain, an empty long-lead log", True)
domain(run_schedule_compression, {"baselineStart": "2025-01-01", "baselineEnd": "2025-12-31",
                                  "actualPctComplete": 50, "spi": 0},
       "schedule compression, a schedule index of zero", True)
domain(run_critical_path_index, {"spi": 0.9, "plannedPctComplete": 0, "actualPctComplete": 0},
       "critical path index, no planned progress", True)
domain(run_discrete_event_sim, {"spi": 0.9, "cpi": 0.9, "plannedPctComplete": 0,
                                "actualPctComplete": 0},
       "discrete event simulation, no planned progress", True)
# THE ONE THAT STILL COMPUTES, AND WHY. A reported zero incidents is a measurement over a
# reported record, so the band stands: that is the true-zero disposition. What Run 6 found and
# Run 7 removed is the safety INDEX beside it, which is the benchmark over the rate, capped by
# the module's own min(2, ...). At a rate of zero the ratio is unbounded and the module's own
# answer to an unbounded ratio is its cap, which is 2. The shipped code substituted 1, a value
# the formula never produces at a zero rate and which reads as performance exactly at benchmark.
# RUN 20, P0B. The expectation below was built on a multiplication by ten that turned an
# incident COUNT into an incidence RATE. That multiplier had no source anywhere, and
# specification 8.7 defines the rate as recordable cases times two hundred thousand over
# employee hours worked, a denominator this module does not carry. The multiplier is gone,
# so a count with no reported rate beside it abstains. The checks are rewritten to the
# corrected contract rather than deleted, and the superseded expectation is stated here so
# the reason they changed is readable at the point they changed.
domain(run_safety_performance, {"safetyIncidentsDiscussed": 0},
       "safety performance, an incident count with no reported rate", True)
_sp0 = run_safety_performance({"safetyIncidentsDiscussed": 0, "oshaIncidentRate": 0.0},
                              NOOP, "2025-06-30")
ka(_sp0["safety_index"], 2,
   "safety performance: at a REPORTED rate of zero the index is the module's own cap of 2, not "
   "the literal 1 the shipped code substituted")
ka(_sp0["incident_rate"], 0.0, "safety performance: and the rate itself is the reported zero")
ka(band(_sp0), "Green",
   "safety performance: the band stands on a reported zero rate, which is a measurement rather "
   "than an absence")
domain(run_safety_performance, {"oshaIncidentRate": -4, "safetyIncidentsDiscussed": 1},
       "safety performance, a negative incident rate", True)
domain(run_spec_conflict_density, {"docRiskScore": 0.2, "rfiCount": 0},
       "specification conflict density, no requests", True)

print("\n-- Ratio-domain inputs above one, where no module guards them --")
# Document risk is declared a zero-to-one score and is range-guarded at ingestion, not in the
# analytical layer. Recorded so the reliance is explicit rather than assumed.
_unguarded = []
for mid in sorted(VALIDATED):
    if mid in registry.DISABLED_CONCEPT_ONLY or registry.group_of(mid) == "D":
        continue
    si = {"cpi": 0.95, "spi": 0.95, "bac": 1000000, "ev": 400000, "ac": 400000, "pv": 400000,
          "actualPctComplete": 40, "plannedPctComplete": 40, "docRiskScore": 85}
    try:
        rr = registry.run_module(mid, si, lambda: 0.5, "2025-06-30")
    except Exception as exc:                                       # noqa: BLE001
        check(False, f"{mid}: raises on a document risk score of 85", repr(exc))
        continue
    if not abstains(rr):
        _unguarded.append(mid)
print(f"     {len(_unguarded)} implemented modules accept a document risk score of 85 without "
      f"refusing")
check(True, f"document risk above its declared domain is refused by NO module in the analytical "
            f"layer ({len(_unguarded)} accept it); the range guard is at ingestion only")


# =================================================================================================
section("8. THE TWO THINGS TO REPORT RATHER THAN FIX")
# =================================================================================================

import json  # noqa: E402

_ds = (ROOT / "assets" / "js" / "ds_defensibility_data.js").read_text(encoding="utf-8")
_body = _ds[_ds.index("{", _ds.index("const DS_DEFENSIBILITY")):].rstrip().rstrip(";")
_doc = json.loads(_body)
_entries = [m for c in _doc["categories"] for m in c.get("modules", [])]
# THE OVERCLAIM MEASURE, stated so the number can be checked. An entry claims a property the
# module does not have when its accreditation basis asserts the module HAS BEEN VALIDATED. No
# module on this platform has that: the freeze record states in as many words that no labelled
# holdout corpus and no expert reference standard exist, so false-positive and false-negative
# performance is unmeasured. Two entries were corrected in the freeze run.
_claims_validated = [m["name"] for m in _entries
                     if re.search(r"\bvalidated by\b", m.get("accreditationBasis", ""), re.I)]
_unqualified = [m["name"] for m in _entries
                if not re.search(r"uncalibrat|not calibrated|not validated|unvalidated|"
                                 r"rather than a calibrated", json.dumps(m), re.I)]
print(f"     ds_defensibility_data.js: {len(_entries)} module entries")
print(f"     {len(_claims_validated)} state that the module has been VALIDATED")
print(f"     {len(_unqualified)} carry no calibration or validation qualification anywhere")
check(len(_entries) == 103, "ds_defensibility_data.js holds 103 module entries",
      str(len(_entries)))
# RESTATED BY RUN 11 GATE 4, AND THE ORIGINAL FINDING IS EXACTLY WHY. Run 6 measured this and
# reported it rather than editing it, because the handbook's content was the owner's decision at
# the time: 69 of 103 entries stated that a module HAD BEEN VALIDATED, on a platform that holds
# no validation evidence for any module. Run 11 was authorised to correct it, and did: each of
# those entries now states what such validation would consist of, that none of it has been
# performed, and what the repository actually holds instead. The assertion therefore flips from
# "the overclaim is present, and here is how many" to "the overclaim is gone", and the measure
# itself is unchanged so the two runs are counting the same thing.
check(len(_claims_validated) == 0,
      f"no entry claims validation the platform does not have; Run 6 measured 69 of 103 and "
      f"reported them, Run 11 corrected them, and this run counts "
      f"{len(_claims_validated)}",
      str(_claims_validated[:5]))
check((ROOT / "index.html").read_text(encoding="utf-8").find("ds_defensibility_data.js") >= 0,
      "ds_defensibility_data.js is loaded by index.html, so it is a LIVE surface")

_sim = (ROOT / "assets" / "js" / "sim.js").read_text(encoding="utf-8")
_sims = (ROOT / "assets" / "js" / "simulations.js").read_text(encoding="utf-8")
_deep = (ROOT / "research" / "deepdive.html").read_text(encoding="utf-8")
check("DEMO_BAC" in _sim, "the browser instrument still defines the placeholder budget")
check("p80eacOverrunPct" in _sim,
      "the browser instrument still emits the forecast overrun under the key no module reads")
check("sim.js" in _deep and "simulations.js" in _deep,
      "the researcher deep-dive route still loads both browser instrument files")


# =================================================================================================
section("9. COVERAGE, COUNTED AGAINST THE REGISTRY RATHER THAN CLAIMED")
# =================================================================================================

#: Every module this suite gives a known-answer case to: a stated input, an expected value or band
#: computed by hand from the module's own formula, and the expected finding text.
COVERED_HERE = {
    # the five CORE modules held non-voting
    "A2.8", "A3.2", "A3.4", "A4.2", "A4.3",
    # the thirty advisory proxies
    "A1.2", "A1.3", "A1.4", "A1.9", "A1.10", "A2.4", "A2.6", "A2.7", "A3.3", "A3.5", "A3.7",
    "A3.9", "A4.5", "A4.6", "A4.7", "A4.8", "A5.2", "A5.3", "B2.10", "B2.11", "B2.12", "B2.13",
    "B2.14", "B2.15", "B2.16", "B2.17", "B3.5", "B4.3", "B4.4", "D1.2",
    # the twelve newly wired that compute
    "B1.1", "B1.2", "B1.3", "B1.4", "B2.1", "B2.2", "B2.3", "B2.4", "B2.5", "B2.6", "B2.8",
    "B3.1",
    # data and evidence health
    "C1.1", "C1.2", "C1.3", "C1.4", "C1.5", "C1.6", "C1.7",
    # governance thresholds and the module that scores the courses of action
    "B3.2", "B3.3", "B3.4", "B4.7",
    # the portfolio group
    "D1.1", "D1.3", "D1.4", "D1.5",
    # covered as the fifteen-defects run's own case, re-derived here by hand
    "A4.9",
}
#: Given a known-answer case and exhausted boundary tests by the validate-seven run, not here.
COVERED_BY_RUN_4 = {"A1.7", "A1.8"}

_registered = {m for m in registry.registry_index()
               if m in VALIDATED or m in registry.PORTFOLIO_VALIDATED}
_disabled = set(registry.DISABLED_CONCEPT_ONLY)
_uncovered = sorted(_registered - COVERED_HERE - COVERED_BY_RUN_4 - _disabled)
check(COVERED_HERE <= _registered, "every id this suite claims to cover is a registered module",
      str(sorted(COVERED_HERE - _registered)))
print(f"     registry-computed modules: {len(_registered)}")
print(f"     given a known-answer case here: {len(COVERED_HERE)}")
print(f"     given one by the validate-seven run: {len(COVERED_BY_RUN_4)}")
print(f"     disabled as concept-only, never executed: {len(_disabled)}")
print(f"     NOT given a known-answer case: {len(_uncovered)}")
print(f"     {' '.join(_uncovered)}")
# Every uncovered module is nevertheless covered by the abstention sweep and the domain sweep
# above, so none of them is untested; what none of them has is a hand-computed expected value.
check(all(m in _registered for m in _uncovered), "the uncovered set is drawn from the registry")

print()
print("=" * 78)
print(f"Known-answer cases: {CASES}; expectations proved live by perturbation: {PERTURBED}")
if _SURVIVORS:
    print(f"Modules that substitute rather than refuse: {len(_SURVIVORS)}")
    for label, colour in _SURVIVORS:
        print(f"    {label} -> {colour}")
print("=" * 78)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 78)
sys.exit(1 if FAILED else 0)
