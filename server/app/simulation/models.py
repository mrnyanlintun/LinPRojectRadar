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

from .canonical import (
    StructureAbsent,
    agent_supply_chain as canonical_agent_supply_chain,
    ccpm_buffer_health as canonical_ccpm,
    line_of_balance as canonical_line_of_balance,
    queue_bottleneck as canonical_queue,
    require_structure,
)
from .rng import as_percent, clamp, num, pctile, round1, round2

# Stamped on every result set, so a later change to this layer is detectable in already-collected
# data rather than being invisible in the analysis.
# Bumped by remediation Run 4, the freeze point. Runs 1 to 4 changed which modules vote, fixed
# fifteen arithmetic defects, made fourteen computations reachable, and re-banded two measures on
# sourced boundaries, and every result computed through all of it still said sim-2026.07-v1. The
# stamp exists precisely so a change to this layer is detectable in already-collected data, so it
# moves once, here, at the point the platform is frozen for the study.
#
# RUN 7 (FIX-NOW DEFECTS) moves it again, to sim-2026.08-v3, and sim-2026.08-v2 remains the
# historical audit baseline for every result already collected under it. Run 7 corrected sixteen
# modules that emitted a status where they held no input to emit one from: five banded from an
# empty dictionary, nine substituted a denominator or an input rather than refusing, one improved
# when evidence was withheld, and one scored courses of action from a payoff matrix the corpus
# does not contain. The stamp exists so a change to this layer is detectable in already-collected
# data, and this is such a change.
#
# RUN 10 (PRODUCTION REMEDIATION AND SYNTHETIC INTEGRATION) moves it again, to sim-2026.08-v4,
# and sim-2026.08-v2 and sim-2026.08-v3 both remain the historical audit baselines for the
# results already collected under them. Run 10 corrected the sixteen modules Run 8 placed in the
# fix-with-current-data bucket: eleven had an open input domain that let a reading outside the
# domain a quantity can occupy reach a band, two rewarded missing evidence with a better reading,
# two carried a disposition no input could reach, and one printed a sign the figure did not
# carry. This is a change to what this layer emits, so the stamp moves with it.
# RUN 10B (CRITICAL VOTER FIX AND CANONICAL-STRUCTURE INTEGRATION) moves it again, to
# sim-2026.08-v5. Every earlier stamp remains the historical audit baseline for the results
# already collected under it; none is overwritten. Run 10B closed the open input domain in the
# to-complete cost efficiency measure, which is one of the two modules that vote on project
# status and could therefore turn an out-of-domain reading into a favourable project status, and
# it required the defining structure of six canonical methods before they compute. Both change
# what this layer emits, so the stamp moves with them.
# RUN 11 (BROWSER, PARTICIPANT AND GOVERNANCE CLEANUP) moves it again, to sim-2026.08-v6. Every
# earlier stamp remains the historical audit baseline for the results already collected under it;
# none is overwritten. Run 11 corrected the seven remaining neighbour defects the Run 10B sweep
# reproduced and left standing: five modules banded a reading from an input outside the domain
# the quantity can occupy, and two rewarded a withheld input with a calmer band. All seven are
# non-voting and none became voting. This changes what this layer emits, so the stamp moves.
# RUN 12 (FINAL QUALIFICATION, PARTICIPANT CYCLE AND REFREEZE) moves it again, to
# sim-2026.08-v7. Every earlier stamp remains the historical audit baseline for the results
# already collected under it; none is overwritten. Run 12 attaches the evidence qualification
# object to every computed result, so a result carries a new field and this layer emits
# something it did not emit before. NOTHING ARITHMETICAL CHANGED WITH IT: no band, no boundary,
# no module, no vote and no status. The stamp moves because the emitted object changed, which is
# the rule this file has followed since Run 4, not because a number did.
# RUN 14 (TARGETED REMEDIATION, ANOMALY VALIDATION AND DISABLED-METHOD FUNCTIONAL TESTS) moves
# it again, to sim-2026.08-v8. Every earlier stamp remains the historical audit baseline for the
# results already collected under it; none is overwritten. Run 14 corrected the eight modules
# Run 13's evidence recorded as mismatches: five banded an impossible reported progress as
# health, two returned a calmer band when required evidence was withheld, and two returned a
# band under a canonical method's name computed from a construction that is not that method and
# now abstain when their defining structure is absent. The numeric contract also gained the
# upper end of the domain for the fields whose definition supplies one. All eight are
# non-voting, none became voting, and no band boundary moved. This changes what the layer
# emits, so the stamp moves with it.
# RUN 15 (CUSUM CALIBRATION, A REAL ISOLATION FOREST AND THE DISABLED-METHOD ROOT-CAUSE
# REVIEW) moves it to sim-2026.08-v9. The portfolio anomaly module registered as an isolation
# forest now IS one: an ensemble of isolation trees grown on the other projects in the
# portfolio, scored by normalised mean path length, per Liu, Ting and Zhou. The standardised
# distance it used to report under that name is gone from it, its threshold was recalibrated
# on a controlled synthetic population, and it now abstains rather than scoring a project
# against a population that includes the project itself. CUSUM was calibrated and NOT changed:
# the design the calibration selected is the one already shipped, so no CUSUM parameter, band
# or boundary moved. The eight disabled modules were investigated and none was activated or
# altered. The stamp moves because the portfolio layer emits a different object.
SIMULATION_VERSION = "sim-2026.08-v9"


# -------------------------------------------------------------------------------------------
# RUN 7: THE SHARED INPUT-ELIGIBILITY AND ABSTENTION LAYER.
#
# Sixteen modules were found emitting a band from something they had not been given: an absent
# schedule index defaulted to one, an absent denominator floored to one, an absent progress
# ratio substituted by a different index. Each had been patched locally, or not at all, and the
# two modules that read the identical pair of fields disagreed about whether an empty window was
# an abstention or a Green. This layer is the one place that decides, so a module states what it
# needs and the decision is made the same way for all of them.
#
# It validates five things and nothing else: required inputs present, a denominator in a valid
# domain, a required canonical structure present, a minimum history present, and applicability.
# It is not a scoring engine and it does not band. A module still owns its own arithmetic.
#
# The reason CODE is a stable machine string carried beside the result for the API, the export
# and the analysis. The reason SENTENCE is what a reader sees, and it obeys the naming rules:
# words, no module ids, no key names, no em dashes. The two are deliberately separate, because a
# code in a sentence is the exact thing the ledger must never show.
# -------------------------------------------------------------------------------------------

#: Missing scalar inputs: a figure the module reads was not reported for this period.
ABSTAIN_MISSING_INPUT = "missing_required_input"
#: Missing canonical structure: the defining structure of the named method is not in the corpus
#: at all, so no input could make the module eligible. Abstention is the fix, not a proxy.
ABSTAIN_STRUCTURE_ABSENT = "canonical_structure_absent"
#: The same, for a decision method whose defining structure is an action-by-scenario matrix.
ABSTAIN_DECISION_STRUCTURE_ABSENT = "canonical_decision_structure_absent"
#: A denominator outside the domain on which the module's own ratio is defined.
ABSTAIN_INVALID_DENOMINATOR = "invalid_denominator"
#: No exposure: the population, window or log the rate is measured over is empty, so a zero in
#: the numerator is not evidence of a zero rate.
ABSTAIN_NO_EXPOSURE = "no_exposure"
#: Not applicable: the quantity is undefined for this project's state rather than unmeasured.
ABSTAIN_NOT_APPLICABLE = "not_applicable"
#: Insufficient history: fewer periods than the method needs.
ABSTAIN_INSUFFICIENT_HISTORY = "insufficient_history"
#: Malformed input: present, but not a number, or outside the domain it must lie in.
ABSTAIN_MALFORMED_INPUT = "malformed_input"

#: Every code the layer can emit, so the export and the API can enumerate them without guessing.
ABSTENTION_REASON_CODES: tuple[str, ...] = (
    ABSTAIN_MISSING_INPUT,
    ABSTAIN_STRUCTURE_ABSENT,
    ABSTAIN_DECISION_STRUCTURE_ABSENT,
    ABSTAIN_INVALID_DENOMINATOR,
    ABSTAIN_NO_EXPOSURE,
    ABSTAIN_NOT_APPLICABLE,
    ABSTAIN_INSUFFICIENT_HISTORY,
    ABSTAIN_MALFORMED_INPUT,
)

#: The four dispositions Run 7 classified every zero-or-missing case into, recorded here so the
#: classification is in the code rather than only in a report. RETURN_ZERO_TRUE_ZERO is the one
#: that still computes: a zero measured over a valid positive exposure is a finding.
ZERO_CASE_DISPOSITIONS: tuple[str, ...] = (
    "RETURN_ZERO_TRUE_ZERO",
    "ABSTAIN_NO_EXPOSURE",
    "ABSTAIN_INVALID_DENOMINATOR",
    "NOT_APPLICABLE",
)


def insufficient(method_class: str, message: str | None = None,
                 reason_code: str | None = None) -> dict[str, Any]:
    """
    The abstention contract, matching the JavaScript helper exactly.

    A module with missing inputs abstains. It does not fall back to a neutral value: a fabricated
    Green is indistinguishable from a measured one once it reaches fusion.

    `reason_code` is Run 7's addition: a stable machine string from the list above, carried on
    the result and propagated to the stored abstention row, the API and the export. It is never
    rendered: the sentence in `evidence_metric` is what a reader sees. Omitted rather than set to
    None when absent, so a result computed before Run 7 and one computed after are distinguishable
    rather than both carrying an empty field.
    """
    out: dict[str, Any] = {
        "method_class": method_class,
        "status_color": None,
        "insufficient_data": True,
        "evidence_metric": message or "Insufficient data: upload required documents",
    }
    if reason_code is not None:
        out["abstention_reason_code"] = reason_code
    return out


def check_inputs(si: dict, required: tuple[str, ...]) -> bool:
    return all(si.get(k) is not None for k in required)


def eligible(si: dict, required: tuple[tuple[str, str], ...] = (),
             positive: tuple[tuple[str, str], ...] = ()) -> tuple[str, str] | None:
    """
    The shared preflight. Returns (reason_code, sentence) when the module must abstain, else None.

    `required` and `positive` are pairs of (input key, the plain words for what that input IS).
    The words are the module's, because only the module knows what its own figure is called in a
    document; the layer decides what happens when it is absent, malformed or out of domain, and
    it decides it identically everywhere.

    - required: absent gives ABSTAIN_MISSING_INPUT; present but not a finite number gives
      ABSTAIN_MALFORMED_INPUT.
    - positive: the same, and additionally a value at or below zero gives
      ABSTAIN_INVALID_DENOMINATOR. A denominator of zero is never floored to one here: that
      floor is the defect this layer exists to remove.
    """
    for key, words in tuple(required) + tuple(positive):
        raw = si.get(key)
        if raw is None:
            return (ABSTAIN_MISSING_INPUT,
                    f"Insufficient data: {words} has not been reported for this period.")
        if num(raw, None) is None:
            return (ABSTAIN_MALFORMED_INPUT,
                    f"Insufficient data: {words} was reported in a form that is not a number.")
    for key, words in positive:
        if num(si.get(key), 0.0) <= 0:
            return (ABSTAIN_INVALID_DENOMINATOR,
                    f"Insufficient data: {words} is zero or below, and a rate cannot be formed "
                    f"on it. No substitute figure is used in its place.")
    # RUN 14. The upper end of the domain, for the declared inputs that have one. The numeric
    # contract now refuses an impossible figure at every entry point, so in a corpus ingested
    # after this run nothing here can fire; it fires on a figure stored BEFORE the contract
    # gained its upper bound, and on any future path that reaches a module without passing the
    # boundary. Run 13 found five modules banding an impossible percentage as health, and a
    # module that abstains on it needs no knowledge of where the figure came from.
    from ..field_registry import BOUNDED_MAX_SI_FIELDS
    for key, words in tuple(required) + tuple(positive):
        upper = BOUNDED_MAX_SI_FIELDS.get(key)
        if upper is None:
            continue
        value = num(si.get(key), None)
        if value is not None and value > upper:
            return (ABSTAIN_MALFORMED_INPUT,
                    f"Insufficient data: {words} was reported as a figure this quantity cannot "
                    f"take, so it is not read as evidence of anything. No substitute figure is "
                    f"used in its place.")
    return None


def refuse(method_class: str, verdict: tuple[str, str]) -> dict[str, Any]:
    """`eligible`'s verdict as the abstention contract. One call site shape for all sixteen."""
    return insufficient(method_class, verdict[1], verdict[0])


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

    RUN 7. Handed an empty dictionary this read Green. The schedule index defaulted to 1.0, which
    is the value of a project exactly on plan, so a project about which nothing had been reported
    was modelled as a project performing to plan and banded accordingly. The index is now
    required. The activity durations remain the module's own literals and this run does not
    pretend otherwise: a project-specific activity network is not in the corpus, and building one
    is out of scope. What is corrected is that the module no longer reports on a project it has
    been told nothing about.
    """
    # RUN 10, BUCKET 2. Run 8 established that Green is structurally unreachable here: the band
    # divides an eightieth percentile of a SUM of right-skewed activity durations by a baseline
    # built from the MODES of the same activities, and that ratio sits above the Amber boundary
    # whatever the schedule index does. The two sides of the ratio are not the same quantity.
    #
    # The correction is not a new boundary. Inventing one to make Green reachable would leave the
    # deeper fault standing, which is that the three activities below are this FILE'S literals
    # and not the project's network: the durations, the logic and the parallel branch are the
    # same for every project the platform holds. A criticality index computed from literals is a
    # statement about this file, published under the project's name.
    #
    # Canonical criticality needs an activity network with logic and three-point durations. The
    # production corpus carries no such object: the schedule reader assembles a milestone and
    # activity table with dates and percent complete, and no predecessor logic and no optimistic
    # or pessimistic duration anywhere. So the module abstains on the absent structure, on the
    # same footing as reference class forecasting and rework propagation, and the aggregate-index
    # arithmetic is not retained under a canonical label. The sampling code below is reached only
    # when a real network is supplied, and no production path supplies one today.
    # No production path supplies such a network today, so this module abstains on every
    # project the platform holds. The literal-driven sampling that used to stand here is removed
    # rather than gated: leaving it reachable would keep aggregate arithmetic over three
    # hard-coded activities running under a canonical criticality label, which is the fault
    # itself and not merely its trigger.
    return insufficient(
        "PERT_Network_Criticality",
        "This method needs the project's activity network: the activities, the logic between "
        "them and a three-point duration for each. No such network has been recorded for this "
        "project, and a criticality index is not reported from stand-in durations.",
        ABSTAIN_STRUCTURE_ABSENT)


# ---------------------------------------------------------------- A2.2 LOB


def run_lob(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Line of balance: the smallest time separation between a leading and a following line of work.

    RUN 7 removed a default that let an empty dictionary read Green, and left the unit count, the
    two production rates and the buffer as literals in this file, because locations, crews and
    production rates were not in the corpus.

    RUN 10B REQUIRES THE LINE OF BALANCE ITSELF. A line-of-balance measure computed from literals
    and a schedule index describes this file, not the project, and a reader cannot tell the two
    apart on the ledger. The canonical structure is now required: locations in sequence, the
    crews working them, and a production rate and a start for each line of work. Where it is
    absent this ABSTAINS. It does not fall back to the schedule index, and it does not fall back
    to the literals it used to carry. The band is unchanged and is applied to the same quantity
    it always read, the minimum separation in days, now taken from the real lines of work.
    """
    try:
        structure = require_structure(si, "A2.2")
        reading = canonical_line_of_balance(structure)
    except StructureAbsent as absent:
        return insufficient("Line_of_Balance_Velocity", absent.sentence,
                            ABSTAIN_STRUCTURE_ABSENT)

    min_buffer = reading["minimum_separation_days"]
    color = "Red" if min_buffer <= 1.5 else ("Amber" if min_buffer <= 3.0 else "Green")
    return {
        "method_class": "Line_of_Balance_Velocity",
        "status_color": color,
        "minimum_buffer_days": round1(min_buffer),
        "critical_unit_index": reading["critical_location_sequence"],
        "grading_rate": round2(reading["leading_rate"]),
        "paving_rate": round2(reading["following_rate"]),
        "initial_buffer_days": round1(reading["first_separation_days"]),
        "units": reading["locations"],
        "canonical_structure": "line_of_balance",
        "evidence_metric": (
            f"Minimum crew separation {round1(min_buffer)} days across "
            f"{reading['locations']} locations, with the following line advancing at "
            f"{round2(reading['following_rate'])} against {round2(reading['leading_rate'])} "
            f"locations per day"
        ),
    }


# ---------------------------------------------------------------- A2.3 CCPM


def run_ccpm(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    CCPM buffer-health fever chart: buffer consumption against chain completion.

    RUN 7 required both figures and removed the defaults that placed an unreported project in the
    warning zone. The buffer itself remained derived from the schedule performance index rather
    than from a sized critical-chain buffer, and the qualifier said so.

    RUN 10B REQUIRES THE CHAIN AND THE BUFFER. A buffer derived from a performance index is not a
    sized buffer, and a fever chart drawn on one is not this method. The critical chain with its
    activities and a sized project buffer is now required, and where it is absent this ABSTAINS
    rather than falling back to the index. The fever-chart zones are unchanged.
    """
    try:
        structure = require_structure(si, "A2.3")
        reading = canonical_ccpm(structure)
    except StructureAbsent as absent:
        return insufficient("CCPM_Buffer_Health", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)

    pct_chain = reading["pct_chain_complete"]
    pct_buffer = reading["pct_buffer_consumed"]
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
    """
    Reference class forecasting: empirical overrun multipliers as a cost prior.

    RUN 7, AND THIS ONE ABSTAINS UNCONDITIONALLY.

    The method is defined by its reference class: a population of comparable completed projects
    whose realised overruns give the distribution the forecast is drawn from. This platform holds
    no such population. The nine multipliers below are literals, so the percentile, the debiasing
    factor and therefore the band are the same numbers on every project and in every period, and
    handed an empty dictionary the module read Red about a project nobody had reported anything
    for. It read the budget only to scale a figure it displayed; nothing about a project could
    move the band.

    There is no input that would make it eligible, so there is no preflight to write: the missing
    thing is the reference class itself. Building one is out of scope, and a proxy that keeps
    emitting a constant band is the fault this run exists to remove. The module therefore refuses
    and states that the reference class is absent. The arithmetic it used to perform is not kept
    here as dead code: the suite reads it out of the pinned baseline commit, which is how every
    remediation run on this repository has proved what the shipped code did.
    """
    return insufficient(
        "Reference_Class_Forecasting",
        "Insufficient data: no reference class of comparable completed projects is held, so "
        "there is no distribution of realised overruns to place this project against. No "
        "forecast is offered in its place.",
        ABSTAIN_STRUCTURE_ABSENT)



# ---------------------------------------------------------------- A5.1 DSM


def run_dsm(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Design structure matrix rework propagation across Arch, Structural and MEP.

    RUN 7, AND THIS ONE ABSTAINS UNCONDITIONALLY.

    The method is defined by its dependency matrix: which parts of a project's design depend on
    which others, and how strongly, for the project being analysed. The nine coefficients below
    were literals, the initiating wave was a literal, and no project input was read anywhere in
    the computation. Handed an empty dictionary the module read Amber, and handed a complete
    project it read the same Amber, because nothing about a project could reach the arithmetic.
    The result had the shape of an analysis of a project and was a property of the file.

    No dependency matrix is in the corpus and building one is out of scope, so there is no input
    that would make the module eligible. It refuses and says which structure is missing. The
    suite reads the previous arithmetic out of the pinned baseline commit rather than this file
    keeping it as dead code.
    """
    return insufficient(
        "DSM_Rework_Cat5",
        "Insufficient data: no dependency matrix has been established for this project, so "
        "there is no record of which parts of the design depend on which others and a rework "
        "wave cannot be traced through them. No multiplier is offered in its place.",
        ABSTAIN_STRUCTURE_ABSENT)


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
    from .models_doc import A4_EXTENSIONS, A5_EXTENSIONS, A6_EXTENSIONS
    from .models_decision import DECISION_EXTENSIONS
    from .models_dq import DQ_EXTENSIONS
    from .models_evc import EVC_EXTENSIONS
    from .models_fuzzy import FUZZY_EXTENSIONS
    from .models_gov import GOV_BATCH_A, GOV_BATCH_B
    from .models_evm import A1_EXTENSIONS
    from .models_ext import A2_EXTENSIONS, A3_EXTENSIONS
    VALIDATED.update(A1_EXTENSIONS)
    VALIDATED.update(A2_EXTENSIONS)
    VALIDATED.update(A3_EXTENSIONS)
    VALIDATED.update(A4_EXTENSIONS)
    VALIDATED.update(A5_EXTENSIONS)
    VALIDATED.update(A6_EXTENSIONS)
    VALIDATED.update(GOV_BATCH_A)
    VALIDATED.update(GOV_BATCH_B)
    VALIDATED.update(EVC_EXTENSIONS)
    VALIDATED.update(FUZZY_EXTENSIONS)
    VALIDATED.update(DQ_EXTENSIONS)
    VALIDATED.update(DECISION_EXTENSIONS)


_register_extensions()

# Stochastic models, for the seed record on the result set.
STOCHASTIC: frozenset[str] = frozenset({"A1.1", "A1.2", "A2.1"})
