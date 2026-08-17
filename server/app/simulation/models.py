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
from .canonical_v3 import (
    ccpm_buffer_consumption as canonical_buffer_consumption,
    lob_production_rates as canonical_lob_rates,
    parse_schedule_network, pert_criticality, reference_class_forecast, require_v3_structure,
)
from .rng import as_percent, clamp, js_round, num, pctile, round1, round2

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
# RUN 16 (LOW-HANGING INSTRUMENT CLEANUP) moves it to sim-2026.08-v10. Material Cost Variance is
# disabled from operational execution pending an evidence and context decision, so this layer no
# longer emits a result for it and emits an abstention instead. That is a change in what a stored
# row contains and it has to be distinguishable in already-collected data, which is what this
# stamp exists for. Nothing is said here about that module's arithmetic, which is untouched and
# unreached, and no other module's behaviour changed. Every earlier stamp remains the historical
# audit baseline for the results computed under it.
# RUN 28 (CATEGORY 1 TO 3 CANONICAL REMEDIATION) moves it to sim-2026.08-v11, and this is the
# new analytical line the owner's Run-28 instruction calls for. Every earlier stamp remains the
# historical audit baseline for the results already collected under it; none is overwritten and
# none is re-used. THE OWNER'S PROMPT SAYS "PRESERVE v2, BUILD v3". The prompt's premise about
# the current stamp is not what this file records: sim-2026.08-v2 was superseded by Run 7 in
# August 2026 and the line has moved eight times since, so the stamp standing at the start of
# Run 28 was v10, not v2. Creating a second "v3" would collide with the line Run 7 established
# and would read as a REGRESSION from v10, which would make results already collected under v10
# ambiguous -- precisely the harm this stamp exists to prevent. The owner's INTENT is honoured
# instead: the line that was frozen before this run becomes immutable historical evidence, and
# Run 28's analytical changes belong to a NEW line, established with the next unused identifier
# in the sequence Runs 7 through 16 built.
#
# WHAT RUN 28 CHANGED. The twenty-eight remaining Category 1 to 3 scientific targets were
# implemented against the supervisory method contract supplied for this run. Twenty-one of them
# now compute a canonical method from a governed structure that did not exist in this platform
# before -- a time-phased planned value curve, an activity network, a milestone forecast history,
# a look-ahead constraint inventory, a time-phased resource profile, a reference class, a cost
# risk model, an analog record, an external price index, a state-space model and a Bayesian model
# record -- and ABSTAIN when that structure is absent, rather than reporting the transparent
# proxy each of them used to report in its place. Two approved renames are applied. Where the
# quantity a module reports is no longer the quantity its old band was drawn over, the module
# reports the number and asserts NO colour: the band is calibration pending and Run 33 owns it.
# That is a change in what a stored row contains, in several directions at once, and it has to be
# distinguishable in already-collected data, which is what this stamp exists for.
# RUN 28 CLOSURE moves it to sim-2026.08-v12, AND THIS CORRECTS A JUDGEMENT THE CLOSURE ITSELF
# GOT WRONG FIRST TIME. The closure's own report argued the line should stay at v11 because "no
# arithmetic, band, boundary or reported quantity moved". That reasoning was too narrow, and the
# counter-example is mechanical rather than rhetorical: on ONE identical governed input -- a cost
# risk model with three risk events and no stated dependence policy --
#
#     canonical_v3.py as it shipped at commit 0e0dfbd (v11)  emits p80_total_cost = 1200.0
#     canonical_v3.py after the closure                      RAISES StructureAbsent and abstains
#
# server/tools/test_run28_version_boundary.py extracts the v11 file from that git object,
# EXECUTES it beside the current one and asserts exactly that divergence, so the bump rests on
# observed behaviour rather than on a claim about it. Two further changes move what the layer
# emits for some input: the governed project-data intake means a module that could only ever
# abstain -- because twenty-one of the twenty-three structure keys were written by no production
# code at all -- can now compute, and a stored row gains a `projectDataStructures` key recording
# which structures the modules were given. A stamp identifies EXECUTABLE ANALYTICAL BEHAVIOUR,
# and this layer's behaviour differs from v11's. Every earlier stamp, v11 included, remains the
# historical audit baseline for the results collected under it; none is overwritten or re-used.
# RUN 29 (CATEGORIES 4 AND 5 AGAINST THE SUPPLIED CANONICAL CONTRACTS) moves it to
# sim-2026.08-v13, and sim-2026.08-v12 remains the historical audit baseline for every result
# already collected under it. Run 29 replaces the proxy computation in sixteen Category-4 and
# Category-5 modules with the canonical method each is named for, and supplies the eighteen
# governed structures those methods are defined on. THE PROOF IS MECHANICAL, not rhetorical, and
# it is the same shape Run 28's proof took: on ONE identical governed input -- a project whose
# only Category-5 evidence is a governed queue model with an arrival rate of two and a service
# rate of three --
#
#     models_doc.py as it shipped at commit 01e943e (v12)  ABSTAINS: it required a queue
#                                                          OBSERVATION log and no observation
#                                                          log was supplied
#     models_doc.py after Run 29                           computes rho = 2/3, L = 2, W = 1,
#                                                          Lq = 4/3 and Wq = 2/3
#
# server/tools/test_run29_version_boundary.py extracts the v12 file from that git object,
# EXECUTES it beside the current one and asserts exactly that divergence, so the bump rests on
# observed behaviour rather than on a claim about it. A module that could only abstain and can now
# compute is a behaviour change, which is the lesson Run 28 recorded above. A stamp identifies
# EXECUTABLE ANALYTICAL BEHAVIOUR, and this layer's behaviour differs from v12's. Every earlier
# stamp, v12 included, remains the historical audit baseline for the results collected under it;
# none is overwritten or re-used.
# RUN 29's CLOSURE moves it to sim-2026.08-v14, and the reasoning is the one this programme has
# already got wrong once by being too narrow. The closure's own instruction is explicit: a run
# that only touches tests, reports and synthetic packages keeps its stamp, and a run that wires
# real corpus fields into canonical structures does not, because a module that abstained on the
# real corpus will now compute on it.
#
# THAT IS WHAT HAPPENED. The closure decomposed Run 29's claim that no real corpus populates any
# of the seventeen Category-4 and -5 structures, and found the claim false for one of them: the
# nonconformance log already yields a COUNT of nonconformances raised in the period and the
# inspection report already yields the number of items inspected, which is a governed exposure in
# the supplied contract's own words. Both were extracted and neither reached a module.
# `documents.py` now assembles `ncrExposureRecord` from the two, and `canonical_v4.ncr_rate`
# gained a count numerator form that fabricates no identity, date or severity.
#
# THE PROOF IS MECHANICAL, not rhetorical. On ONE identical governed input -- the assembled
# record of four nonconformances against one hundred inspections --
#
#     models_doc.py as it shipped at commit 9cc6793 (v13)  ABSTAINS: it required a list of
#                                                          nonconformance EVENTS and a count is
#                                                          not a list
#     models_doc.py after this closure                     reports a rate of 0.04
#
# server/tools/test_run29_closure_version_boundary.py extracts the v13 package from that git
# object, EXECUTES it beside the current one and asserts exactly that divergence. Every earlier
# stamp, v13 included, remains the historical audit baseline for the results collected under it;
# none is overwritten or re-used.
#
# RUN 30 -> sim-2026.08-v15. THE CATEGORY-6 SYNTHESIS ENSEMBLES EMIT DIFFERENT RESULTS ON
# IDENTICAL INPUT, so the stamp moves. Proved by execution rather than asserted: the v14
# analytical package is extracted from git object ac7c011, imported, and run beside the current
# one on the identical assembled package.
#
#     input: three primary signals all reading lowercase red, beside a signal array of three
#            module rows and then of sixty-three
#
#     models_gov.py as it shipped at commit ac7c011 (v14)  B1.4 reports Red beside three module
#                                                          rows and Yellow beside sixty-three,
#                                                          on identical adverse evidence
#     models_gov.py after Run 30                           B1.4 reports a Worst-2 mean of 3.0 in
#                                                          both, and asserts no band
#
#     v14 B1.2 reports Red on four weight literals with no authority; v15 ABSTAINS, because a
#     weighted vote with no governed weighting policy weighs nothing.
#
# server/tools/test_run30_version_boundary.py extracts the v14 package from that git object,
# EXECUTES it beside the current one and asserts exactly those divergences. Every earlier stamp,
# v14 included, remains the historical audit baseline for the results collected under it; none is
# overwritten or re-used.
#
# RUN 30 CLOSURE -> sim-2026.08-v16. THE CATEGORY-7 OPERATIONAL ROUTE CHANGED, so the stamp moves
# again. v15 built the canonical Category-7 layer and PRODUCTION NEVER CALLED IT: executing the
# production entry point for all twenty identities and profiling the interpreter gave canonical_v5
# reached on zero of twenty, while seventeen ran their v14 proxy arithmetic. v16 repoints every
# one of the twenty through models_cat7.py into that layer.
#
#     input: signalInputs carrying cpi 0.85, spi 0.85 and a document risk score, and no governed
#            epistemic structure of any kind
#
#     models_fuzzy.py as it shipped at commit ce03eb1 (v15)  B2.14 Maximum Entropy reports Amber
#                                                            from the entropy of a lookup table
#                                                            indexed by min(cpi, spi)
#     the current line                                       B2.14 ABSTAINS: no state space and
#                                                            no constraints were supplied, so
#                                                            there is nothing to maximise over
#
#     On a governed maximum-entropy problem BOTH lines produce a reading, and only the current
#     one is the constrained optimisation the method is named for.
#
# server/tools/test_run30_closure_version_boundary.py extracts the v15 package from that git
# object, EXECUTES it beside the current one and asserts exactly that. Every earlier stamp, v15
# included, remains the historical audit baseline for the results collected under it.
SIMULATION_VERSION = "sim-2026.08-v18"

#: THE LINE THAT RUN 28 FROZE, kept addressable so a reader of this file can see which stamp the
#: historical audit baseline is without reading the comment above. Every stamp from
#: sim-2026.07-v1 to this one remains valid for the results computed under it.
SIMULATION_VERSION_SUPERSEDED = "sim-2026.08-v17"

#: Every stamp this analytical layer has carried, oldest first. A run that adds a stamp appends;
#: nothing here is ever edited or removed, because each row is the audit baseline for results
#: already collected under it.
SIMULATION_VERSION_HISTORY: tuple[str, ...] = (
    "sim-2026.07-v1", "sim-2026.08-v2", "sim-2026.08-v3", "sim-2026.08-v4", "sim-2026.08-v5",
    "sim-2026.08-v6", "sim-2026.08-v7", "sim-2026.08-v8", "sim-2026.08-v9", "sim-2026.08-v10",
    "sim-2026.08-v11", "sim-2026.08-v12", "sim-2026.08-v13", "sim-2026.08-v14",
    "sim-2026.08-v15", "sim-2026.08-v16", "sim-2026.08-v17",
    "sim-2026.08-v18",
)


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


# -------------------------------------------------------------------------------------------
# RUN 28: THE CALIBRATION-PENDING CONTRACT.
#
# WHY IT EXISTS. Run 28 replaces a proxy computation with the canonical method the module is
# named for in twenty-one places. In most of them the QUANTITY CHANGES: a look-ahead module that
# used to report the share of activities carrying a constraint now reports the share that are
# ready; a critical-path module that used to average a schedule index with a progress ratio now
# reports the float and the critical activities off a real forward and backward pass. The band
# ladder each of those modules carried was drawn -- uncalibrated, and already recorded as such --
# over the OLD quantity. Applying it to the new one would be inventing a threshold for a measure
# nobody has calibrated, which the supervisory contract forbids in exactly those words.
#
# So the module reports the number and asserts NO colour. `status_color` is None, `band_asserted`
# is False, and `calibration_pending` is True. This is NOT an abstention: the method ran, the
# figure is real, and `insufficient_data` is absent. The registry keeps such a row in `computed`
# rather than in `abstained`, and the row cannot reach status fusion because fusion reads only
# the two voting modules, neither of which is in this run's scope.
#
# Run 33 owns the calibration campaign that may later attach bands to these quantities.
# -------------------------------------------------------------------------------------------

#: The one sentence carried on every calibration-pending row, stated once so it cannot drift.
CALIBRATION_PENDING_NOTE: str = (
    "The method this measure is named for has been carried out and the figure is reported. No "
    "status colour is offered with it, because no boundary for this quantity has been "
    "established from evidence, and a colour drawn from an unestablished boundary would read as "
    "a judgement nobody has made."
)


def calibration_pending(method_class: str, message: str, **fields: Any) -> dict[str, Any]:
    """A canonical result with no band asserted. See the block above for why this is not an
    abstention and why the band is withheld rather than carried over from the proxy."""
    out: dict[str, Any] = {
        "method_class": method_class,
        "status_color": None,
        "calibration_pending": True,
        "band_asserted": False,
        "calibration_note": CALIBRATION_PENDING_NOTE,
        "evidence_metric": message,
    }
    out.update(fields)
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
    RUN 28, v3. STOCHASTIC CRITICALITY OVER A REAL ACTIVITY NETWORK.

    THE SUPPLIED CONTRACT requires a real activity network in which each activity carries an
    identity, its predecessors and a duration distribution or three-point estimate. The classical
    PERT moments are E[T] = (O + 4M + P)/6 and Var[T] = ((P-O)/6)^2, and the criticality index of
    an activity is the share of simulation trials in which it is critical. Where no network
    exists the answer is NOT ESTIMABLE, and SPI or BAC may not be used to reconstruct topology.

    WHAT v2 AND v10 DID. The original computed a criticality index from three activity durations
    that were literals in this file, identical on every project. Run 7 required the schedule
    index, Run 10 established Green was structurally unreachable, and Run 10B removed the
    arithmetic entirely and made the module abstain UNCONDITIONALLY, because no production path
    supplied a network. That abstention was correct and is the disposition Run 27 recorded.

    WHAT RUN 28 ADDS is the supply path the abstention was waiting for. The governed schedule
    network is now a structure on the signal inputs, and when a project carries one the module
    computes: every trial redraws every activity duration from its three-point estimate and
    RECOMPUTES the forward and backward passes, so criticality is measured rather than ranked.
    Where the network is absent the module still ABSTAINS, and nothing is reconstructed from an
    index. No band is asserted: the old ladder was drawn over a ratio of an eightieth percentile
    to a modal baseline, which is not this quantity.
    """
    try:
        structure = require_v3_structure(si, "A2.1")
        network = parse_schedule_network(structure)
        reading = pert_criticality(network, rand, trials=2000)
    except StructureAbsent as absent:
        return insufficient("PERT_Network_Criticality", absent.sentence,
                            ABSTAIN_STRUCTURE_ABSENT)
    index = reading["criticality_index"]
    top = max(index, key=lambda a: (index[a], a))
    return calibration_pending(
        "PERT_Network_Criticality",
        f"Over {reading['trials']} simulated runs of the network, {top} lies on the critical "
        f"path in {int(js_round(index[top] * 100))} per cent of them, the most of any activity",
        criticality_index={a: round(index[a], 4) for a in sorted(index)},
        most_critical_activity=top,
        most_critical_share=round(index[top], 4),
        trials=reading["trials"],
        deterministic=reading["deterministic"],
        project_finish_p80=reading.get("project_finish_p80"),
        activity_moments={a: v for a, v in sorted(reading["activity_moments"].items())},
        schedule_version=network["schedule_version"],
        canonical_structure="schedule_network",
    )


# ---------------------------------------------------------------- A2.2 LOB


def run_lob(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Line of balance on repetitive, location-based production.

    RUN 10B required the line of balance itself: locations in sequence, the crews working them,
    and a production rate and start for each line of work. Where it is absent this ABSTAINS and
    falls back on nothing.

    RUN 28, v3. THE SUPPLIED CONTRACT adds what v10 did not report: the method is for
    repetitive/location-based production and requires the activity, the location or unit, the
    quantity, the crew, the PLANNED production rate, the ACTUAL production rate and the sequence,
    with rate = change in units / change in time, and it asks that the actual production slope be
    shown against plan so deterioration is visible. v10 read only the actual rates, so a crew
    running at half its planned rate and a crew running exactly to plan were indistinguishable
    once the separation between two lines was formed. The planned rate is now required alongside
    the actual one and the two slopes are reported per line of work.

    The minimum separation between the leading and following lines is unchanged and is still the
    quantity the module's boundaries were drawn over. No band is asserted on the NEW quantities:
    a production rate ratio has no established boundary in this platform and Run 33 owns it.
    """
    try:
        structure = require_structure(si, "A2.2")
        reading = canonical_line_of_balance(structure)
        rates = canonical_lob_rates(structure)
    except StructureAbsent as absent:
        return insufficient("Line_of_Balance_Velocity", absent.sentence,
                            ABSTAIN_STRUCTURE_ABSENT)

    min_buffer = reading["minimum_separation_days"]
    deteriorating = sorted(a for a, v in rates["by_activity"].items() if v["deteriorating"])
    return calibration_pending(
        "Line_of_Balance_Velocity",
        f"Minimum crew separation {round1(min_buffer)} days across "
        f"{reading['locations']} locations, with the following line advancing at "
        f"{round2(reading['following_rate'])} against {round2(reading['leading_rate'])} "
        f"locations per day; "
        + (f"{len(deteriorating)} of {rates['activities']} lines of work are running slower "
           f"than planned" if deteriorating
           else f"all {rates['activities']} lines of work are at or above their planned rate"),
        minimum_buffer_days=round1(min_buffer),
        critical_unit_index=reading["critical_location_sequence"],
        grading_rate=round2(reading["leading_rate"]),
        paving_rate=round2(reading["following_rate"]),
        initial_buffer_days=round1(reading["first_separation_days"]),
        units=reading["locations"],
        production_rates=rates["by_activity"],
        deteriorating_lines=deteriorating,
        line_count=rates["activities"],
        canonical_structure="line_of_balance",
    )


# ---------------------------------------------------------------- A2.3 CCPM


def run_ccpm(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    CCPM buffer health, read off a sized critical-chain buffer.

    RUN 10B REQUIRED THE CHAIN AND THE BUFFER: a buffer derived from a performance index is not a
    sized buffer, and where the chain and buffer are absent this ABSTAINS rather than falling
    back to the index or to CPM float.

    RUN 28, v3. THE SUPPLIED CONTRACT states the two figures explicitly -- buffer consumed
    BC = B0 - Bt, and the buffer consumption ratio BCR = (B0 - Bt) / B0 -- and states that the
    fever-chart bands are calibration and policy rather than universal constants. v10 reported
    the consumption as a percentage and drew a three-zone fever chart on it, where the amber line
    is chain completion (a definitional forty-five degree line) and the red line adds a third of
    the remaining chain, which is a policy constant nobody in this repository sourced. Both
    figures are now reported in the contract's own terms, the zone boundaries are reported as the
    POLICY LINES THEY ARE rather than as an established status, and no colour is asserted.
    """
    try:
        structure = require_structure(si, "A2.3")
        reading = canonical_ccpm(structure)
        consumption = canonical_buffer_consumption(
            reading["project_buffer_days"],
            reading["project_buffer_days"] * (1.0 - reading["pct_buffer_consumed"] / 100.0))
    except StructureAbsent as absent:
        return insufficient("CCPM_Buffer_Health", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)

    pct_chain = reading["pct_chain_complete"]
    pct_buffer = reading["pct_buffer_consumed"]
    amber = pct_chain
    red = pct_chain + (100 - pct_chain) / 3
    zone = "beyond the red policy line" if pct_buffer >= red else (
        "beyond the amber policy line" if pct_buffer >= amber else "inside both policy lines")
    return calibration_pending(
        "CCPM_Buffer_Health",
        f"Buffer {round1(pct_buffer)}% consumed at {round1(pct_chain)}% chain complete, "
        f"{round1(consumption['buffer_consumed_days'])} days of the "
        f"{round1(consumption['original_buffer_days'])} day project buffer used, {zone}",
        pct_chain_complete=round1(pct_chain),
        pct_buffer_consumed=round1(pct_buffer),
        buffer_consumed_days=consumption["buffer_consumed_days"],
        buffer_consumption_ratio=consumption["buffer_consumption_ratio"],
        original_buffer_days=consumption["original_buffer_days"],
        remaining_buffer_days=consumption["remaining_buffer_days"],
        feeding_buffer_count=reading["feeding_buffer_count"],
        chain_activity_count=reading["chain_activity_count"],
        amber_policy_line=round1(amber),
        red_policy_line=round1(red),
        policy_line_note=("the amber line is chain completion, which is definitional; the red "
                          "line adds a third of the chain remaining, which is a policy choice "
                          "no source in this repository establishes"),
        zone_relative_to_policy_lines=zone,
        canonical_structure="ccpm_buffer",
    )


# ---------------------------------------------------------------- A3.1 RCF


def run_rcf(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. AN EMPIRICAL OUTSIDE VIEW OVER A GOVERNED REFERENCE CLASS.

    THE SUPPLIED CONTRACT requires a real empirical outside-view reference class: completed
    comparable projects with their identities, the inclusion and exclusion criteria, a comparable
    outcome definition, normalization, the historical forecast errors or overruns, the sample
    size and a governed percentile. U_p is the p quantile of the historical proportional
    overruns, and AdjustedForecast = InsideViewForecast * (1 + U_p). Where no governed reference
    class is retrieved the answer is NOT ESTIMABLE, and an embedded fixed multiplier may not be
    used.

    WHAT v2 AND v10 DID. Nine overrun multipliers were literals in this file, so the percentile,
    the debiasing factor and the band were the same numbers on every project in every period.
    Run 7 removed the arithmetic and made the module abstain UNCONDITIONALLY, which Run 27
    recorded as CORRECT_ABSTENTION.

    WHAT RUN 28 ADDS is the supply path. A governed reference class is now a structure on the
    signal inputs, carrying the members and every one of the criteria above, and the project
    being assessed may not be a member of the class it is compared against. The quantile
    convention is the one frozen for the whole v3 line in canonical_v3.empirical_quantile. Where
    the class is absent the module still ABSTAINS. No band is asserted.
    """
    try:
        structure = require_v3_structure(si, "A3.1")
        inside = num(si.get("bac"), None)
        if inside is None:
            raise StructureAbsent(
                "No inside view forecast of the cost at completion has been reported for this "
                "project, so there is nothing for an outside view to adjust.")
        percentile = num(structure.get("governed_percentile"), None)
        if percentile is None:
            raise StructureAbsent(
                "The reference class provided does not say which percentile of the historical "
                "outcomes governs the uplift, so no uplift is taken from it.")
        reading = reference_class_forecast(structure, float(inside), float(percentile))
    except StructureAbsent as absent:
        return insufficient("Reference_Class_Forecasting", absent.sentence,
                            ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Reference_Class_Forecasting",
        f"Across {reading['sample_size']} completed comparable projects the "
        f"{int(js_round(reading['percentile'] * 100))}th percentile outcome overran by "
        f"{int(js_round(reading['uplift'] * 100))} per cent, which puts this project's "
        f"forecast at {int(js_round(reading['adjusted_forecast']))} against an inside view of "
        f"{int(js_round(reading['inside_view']))}",
        uplift=round(reading["uplift"], 4),
        governed_percentile=reading["percentile"],
        sample_size=reading["sample_size"],
        inside_view=reading["inside_view"],
        adjusted_forecast=reading["adjusted_forecast"],
        min_overrun=reading["min_overrun"],
        max_overrun=reading["max_overrun"],
        inclusion_criteria=reading["inclusion_criteria"],
        exclusion_criteria=reading["exclusion_criteria"],
        outcome_definition=reading["outcome_definition"],
        normalization=reading["normalization"],
        data_vintage=reading["data_vintage"],
        canonical_structure="reference_class",
    )


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

    No dependency matrix was in the corpus and building one was out of scope, so there was no
    input that would make the module eligible. It refused and said which structure was missing.
    The suite reads the previous arithmetic out of the pinned baseline commit rather than this
    file keeping it as dead code.

    RUN 29 SUPPLIES THE MATRIX, which is what the unconditional abstention was waiting for.

    SUPPLIED CONTRACT 5.1: named nodes, a directed dependency matrix D, a declared matrix
    orientation, edge strengths, a seed rework vector and a stopping or cycle policy, propagated
    as R(k+1) = D * R(k) under the declared orientation. With D = [[0, 0.5], [0, 0]] and
    R0 = [0, 1], R1 = [0.5, 0] and R2 = [0, 0]. With no project DSM the answer is NOT ESTIMABLE,
    and CPI or SPI may not be substituted for dependency topology.

    Where the governed dependency matrix is absent this module STILL ABSTAINS, and nothing is
    reconstructed from an index. No band is asserted: no ladder was ever drawn over propagated
    rework, and inventing one is Run 33's decision to make from evidence, not this run's.
    """
    from .canonical_v4 import dsm_rework_propagation, require_v4_structure
    from .models_ext import _js_str
    try:
        reading = dsm_rework_propagation(require_v4_structure(si, "A5.1"))
    except StructureAbsent as absent:
        return insufficient("DSM_Rework_Cat5", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    propagated = reading["propagated_rework"]
    worst = max(propagated, key=lambda n: (propagated[n], n))
    return calibration_pending(
        "DSM_Rework_Cat5",
        f"Rework seeded in this project's dependency matrix propagates through "
        f"{_js_str(reading['wave_count'])} waves across "
        f"{_js_str(len(reading['nodes']))} parts of the design, and the part that receives the "
        f"most of it is {worst}, at {_js_str(round(propagated[worst], 4))}. The propagation "
        f"stopped because it {'converged' if reading['stopped_because'] == 'CONVERGED' else 'reached the step limit the model declares'}.",
        nodes=reading["nodes"],
        matrix_orientation=reading["matrix_orientation"],
        matrix=reading["matrix"],
        edges=reading["edges"],
        seed_rework_vector=reading["seed_rework_vector"],
        waves=reading["waves"],
        wave_count=reading["wave_count"],
        propagated_rework=propagated,
        total_propagated_rework=round(reading["total_propagated_rework"], 6),
        most_affected_node=worst,
        stopped_because=reading["stopped_because"],
        model_version=reading["model_version"],
        canonical_structure="dsm_dependency_model",
        source=reading["source"])


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
    # RUN 30 CLOSURE, v16. THE TWENTY CATEGORY-7 IDENTITIES ARE REPOINTED, LAST, so this line is
    # the one that decides which implementation production runs and a reader can see it decide.
    # `EVC_EXTENSIONS` and `FUZZY_EXTENSIONS` are still imported and still updated above, because
    # they also carry Category-7-adjacent modules that Run 30 is not in scope to touch; what
    # changes is that every B2.x key they set is overwritten here by the thin canonical route in
    # models_cat7.py. The legacy Category-7 functions therefore remain in the tree as the
    # historical record of the v14/v15 line and are reachable from no production route.
    from .models_cat7 import CAT7_CANONICAL
    VALIDATED.update(CAT7_CANONICAL)
    # RUN 31, v17. THE SIXTEEN CATEGORY-8 AND CATEGORY-9 IDENTITIES ARE REPOINTED, LAST, for the
    # same reason and by the same pattern: this line decides which implementation production
    # runs, and a reader can see it decide. `A6_EXTENSIONS`, `GOV_BATCH_A/B` and `DQ_EXTENSIONS`
    # are still imported and still updated above -- they carry modules outside Run 31's scope --
    # and every A6.x, B3.x and C1.x key they set is overwritten here by the thin canonical route
    # in models_cat89.py. The legacy Category-8/9 functions therefore remain in the tree as the
    # historical record of the v16 line, preserved because Run 19's audit, Run 14's disabled-
    # method suite and Run 27's parsimony proofs are evidence ABOUT them, and they are reachable
    # from no production route. `test_run31_operational_route.py` proves the reachability count
    # is zero by profiling the interpreter through `registry.run_module`.
    from .models_cat89 import CAT89_CANONICAL
    VALIDATED.update(CAT89_CANONICAL)
    # RUN 31 PASS 2, v18. THE SYSTEM-WIDE QUALIFICATION BOUNDARY IS INSTALLED LAST, INTO THE
    # DISPATCH TABLE ITSELF. This is the line that makes the Category-9 gate operational rather
    # than decorative: after it, no Category-6, -7, -8 or -10 entry in VALIDATED reaches its
    # runner without the boundary first, and `registry.run_module` looks the runner up here. It
    # runs after every extension map for the same reason the Category-7 and Category-8/9
    # repointings do -- whatever registers last decides what production executes, and a reader
    # can see it decide. Category 9 is excluded by construction: it performs the assessment.
    from .qualification_boundary import install as _install_boundary
    global QUALIFICATION_BOUNDARY_INSTALLED
    QUALIFICATION_BOUNDARY_INSTALLED = _install_boundary(VALIDATED)


_register_extensions()

# Stochastic models, for the seed record on the result set.
STOCHASTIC: frozenset[str] = frozenset({"A1.1", "A1.2", "A2.1"})
