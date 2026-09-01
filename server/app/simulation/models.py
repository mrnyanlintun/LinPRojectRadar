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
    cpm_forward_backward,
    parse_schedule_network, pert_criticality, reference_class_forecast, require_v3_structure,
)
from . import band_reference as _BR
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
# RUN 32, v20. THE SEVEN CATEGORY-10 DECISION METHODS ARE REPOINTED onto `canonical_v7.py`, so
# the analytical layer no longer reports a decision recommendation manufactured from project
# indices. This stamp is APPENDED; v19 and every stamp before it remain the audit baseline for
# the results collected under them, and none is edited or removed.
#
#     A v19 -> v20 DIVERGENCE, executed rather than described. On a project carrying no governed
#     decision structure:
#
#       v19  B4.1  Multi-Objective Optimization   a number, blended from cpi, spi and the
#                                                 document risk score
#       v20  B4.1  Multi-Objective Optimization   no reading; awaiting the alternatives being
#                                                 compared and the objectives they are measured on
#
#     and on a project that DOES carry a governed decision problem both lines produce a reading,
#     but only v20's is the dominance relation the method is named for.
#
# server/tools/test_run32_closure_version_boundary.py extracts the v19 package FROM ITS GIT
# OBJECT, executes it beside the current one and asserts that, rather than comparing source text.
# RUN 33 (PORTFOLIO HEALTH PH.1-PH.5 CANONICAL REMEDIATION) -> sim-2026.08-v21. THE PORTFOLIO
# HEALTH ROUTE AND ITS ARITHMETIC BOTH CHANGED, so the stamp moves. On identical portfolio
# inputs the two lines differ, and the differences are behavioural rather than editorial:
#
#       v20  D1.3  Signal Trajectory Classifier   endpoint difference of the last three cost
#                                                 index values over (count - 1), read off LIST
#                                                 POSITION, banded Green/Yellow/Amber/Red
#       v21  D1.3  Signal Trajectory Classifier   ordinary-least-squares slope on the actual
#                                                 reporting times of a governed signal history,
#                                                 classified DETERIORATING/IMPROVING/FLAT with
#                                                 no magnitude band at all
#
#       v20  D1.5  Anomaly Score                  a scalar composite_score, the mean of the
#                                                 retired Mahalanobis proxy and 1 - PH.2's own
#                                                 percentile, banded to a status colour
#       v21  D1.5  Anomaly Score                  a PortfolioAnomalyProfile carrying every
#                                                 constituent and its lineage, with score = None
#                                                 under PARAMETER_PROVENANCE_BLOCKED
#
#       v20  D1.4  Cross-Project Pattern          a fixed unvalidated 0.15 radius over three raw
#                                                 mixed-unit features, then a status colour
#       v21  D1.4  Cross-Project Pattern          the continuous nearest-neighbour relationship
#                                                 on standardised features, no threshold
#
#       v20  D1.1  Isolation Forest               a genuine forest, but a DIFFERENT one per
#                                                 scored project, with scores from different
#                                                 forests shown side by side as one scale
#       v21  D1.1  Isolation Forest               one governed forest per cohort and model
#                                                 version, scoring every member from it
#
# and on a portfolio that carries NO governed cohort both lines refuse to compute, which is the
# legitimate non-divergence: v20 refuses for being too small and v21 refuses for having no
# governed cohort, and neither invents a reading.
#
# server/tools/test_run33_version_boundary.py extracts the v20 package FROM ITS GIT OBJECT,
# executes it beside the current one on identical inputs, and asserts that -- rather than
# comparing source text.
# RUN 34 (PORTFOLIO HEALTH CALIBRATION AND PARAMETER PROVENANCE) -> sim-2026.08-v22. PORTFOLIO
# HEALTH BEHAVIOUR CHANGED, so the stamp moves. On identical portfolio inputs the two lines
# differ, and the differences are behavioural rather than editorial:
#
#       v21  D1.2  Portfolio Outlier Detection   emitted a composite percentile under EQUAL
#                                                weighting, labelled OWNER_POLICY but emitted
#       v22  D1.2  Portfolio Outlier Detection   composite withheld absent governed weights;
#                                                the per-feature percentile profile is returned
#                                                and the disposition is
#                                                PARAMETER_PROVENANCE_BLOCKED
#
#       v21  D1.1  Isolation Forest              computed on a cohort of two eligible projects
#       v22  D1.1  Isolation Forest              NOT_ESTIMABLE below three: two projects cannot
#                                                establish what is normal for a portfolio, since
#                                                each is the other's entire reference population
#
#       v21  D1.3  Signal Trajectory Classifier  a zero slope classified FLAT
#       v22  D1.3  Signal Trajectory Classifier  a zero slope classified STABLE, and the fitted
#                                                series reports whether it was equally spaced
#                                                rather than leaving that to be assumed
#
# and on a portfolio that carries NO governed cohort both lines refuse identically, which is the
# legitimate non-divergence: the calibration work changed what is reported where a reading is
# possible, and changed nothing about when a reading is possible at all.
#
# server/tests/test_run34_version_boundary.py extracts the v21 package FROM ITS GIT OBJECT,
# executes it beside the current one on identical inputs, and asserts that -- rather than
# comparing source text.
#
# ---------------------------------------------------------------------------------------------
# v22 -> v23. THE RUN-35 FINAL SCIENTIFIC CLOSURE: THE TWO VOTING IDENTITIES.
#
# Run 35 scored A1.7 and A1.8 against the PMI identities that define them and recorded genuine
# FAILURES: on the governed corpus the emitted A1.7 value differed from (BAC - EV) / (BAC - AC)
# by exactly -3/7000, and the emitted A1.8 value differed from BAC - BAC/CPI by exactly +10/909.
# Both came from the same cause -- a presentation rounding applied to the ANALYTICAL value -- and
# in A1.7 the rounded number was then handed to the band, so it could decide a STATUS. The
# pre-change measurement found twenty-eight governed inputs on which v22 answered Green where the
# full-precision index implied Amber. These are the only two modules that vote.
#
#       v22  A1.7  TCPI  value rounded to three decimals; THE BAND READ THE ROUNDED VALUE
#       v23  A1.7  TCPI  canonical value at the application's own precision; the band reads it;
#                        `tcpi_display` carries the rounded presentation number
#
#       v22  A1.8  VAC   analytical field emitted as whole dollars (the band already used the
#                        full-precision percentage, so no status defect existed here)
#       v23  A1.8  VAC   canonical value and percentage at full precision; `vac_display` and
#                        `vac_pct_display` carry the presentation numbers
#
# THE REFERENCE STANDARD WAS NOT ALTERED TO MAKE THE IMPLEMENTATION PASS. The implementation was
# corrected to the published identity, after the validation, and the v22 failures stay recorded.
# The displayed sentences are unchanged wherever the band is unchanged, because they were already
# built from presentation values. No new decimal precision is introduced anywhere: this is a
# separation of the canonical value from its presentation, in the float arithmetic the
# application already used.
#
# The legitimate NON-divergence: every module that is not A1.7 or A1.8, and every input on which
# the rounded and the full-precision value agree, returns byte-identical results under both
# lines. That is proved by executing both packages, not by reading the diff.
#
# ------------------------------------------------------------------------------------------
# RUN 36, sim-2026.08-v24. THE A1.1 BAND WITHDRAWAL.
#
# A1.1 Monte Carlo EAC Forecast was the ONE scientific target in the whole instrument still
# emitting an authoritative status colour from an unresolved parameter on the governed corpus.
# That is derived and not transcribed: of the 100 scientific targets executed through
# `registry.run_module` on the controlled corpus, six leave the abstention branch, and exactly
# one of those six carries both a `status_color` and an UNSUPPORTED parameter classification.
#
# The ladder is the ten and five per cent boundaries `models_sim.mc_status` drew over the P80
# overrun percentage. `parameters.py` classifies them UNSUPPORTED: they are cited to nothing
# inside or outside this repository, and no calibration set exists here from which they could be
# fitted or tested. The supervisory specification's own pass ceiling for A1.1 is
# METHOD_PASS_CALIBRATION_PENDING, and rule 2 of `canonical_v3.py` already requires a caller with
# no evidence-established boundary to emit the number with calibration pending and assert no
# colour. A6.1, A6.2 and A6.3 already do exactly that; A1.1 now joins them.
#
#       v23  A1.1  Monte Carlo  emits status_color "red"/"amber"/"green" from mc_status
#       v24  A1.1  Monte Carlo  emits status_color None, band_asserted False,
#                               calibration_pending True, and the SAME figure
#
# NO NUMBER MOVED. The sampling, the seed, the Beta-PERT shape and the percentiles are untouched:
# the v23 line extracted from git object dafc35d35bafe5af76e1ce48ef7daceab9daed2c returns
# overrun_pct_p80 12.104441685525892 on the controlled corpus and 11.983407036630878 on the
# lineage fixture, identical to this line on both. What moved is the colour and nothing else.
# `mc_status` is PRESERVED rather than deleted, and production cannot reach it.
#
# The legitimate NON-divergence: every module that is not A1.1 returns byte-identical results
# under both lines. That is proved by executing both packages, not by reading the diff.
#
# ------------------------------------------------------------------------------------------
# RUN 36 CLOSURE, sim-2026.08-v25. THE OWNER'S A1.1 RULING OF 2026-08-19.
#
# The owner resolved the specification ambiguity Run 36 identified. The `Required:` input list in
# supervisory specification s1.1 GOVERNS what qualifies as canonical A1.1 Monte Carlo EAC
# Forecast. The permission to "retain" the scalar BAC/CPI/SPI/document-risk adaptation permits it
# to be PRESERVED as scientific and historical code; it does NOT waive the canonical input
# contract and does NOT authorize the adaptation to stand in for canonical Monte Carlo execution.
#
# Canonical A1.1 needs TWO governed elements: the declared `costDriverDistributions` structure,
# and an authoritative deterministic mapping from sampled cost drivers to EAC. The specification
# REQUIRES that mapping and DOES NOT DEFINE IT. None was invented. Until both exist A1.1 does not
# execute operationally.
#
#       v24  A1.1  computes from bac, cpi, spi and docRiskScore and reports a figure with no band
#       v25  A1.1  operationally disabled for insufficient canonical input; no figure, no band,
#                  reason code CANONICAL_DRIVER_DISTRIBUTION_MAPPING_NOT_GOVERNED
#
# THE RETAINED ADAPTATION IS PRESERVED AND UNREACHABLE. `models_sim.run_monte_carlo` and
# `monte_carlo_eac` are untouched and still reproduce their historical figures when driven
# directly; `registry.run_module` short-circuits A1.1 BEFORE the dispatch table is consulted, so
# no production route can enter them and none can fall back to them. That is asserted from the
# live source of the gate by `models_sim.assert_retained_adaptation_not_reachable`.
#
# THIS IS NOT A SOFTWARE FAILURE. Nothing is broken. What is absent is a governed scientific input
# contract, which is why the reason code is its own and not a missing-value code.
#
# The legitimate NON-divergence: every module that is not A1.1 returns byte-identical results
# under both lines. That is proved by executing both packages, not by reading the diff.
# -------------------------------------------------------------------------------------------
# RUN 41: THE v25 -> v26 BOUNDARY. TWO BEHAVIOUR CHANGES, NEITHER OF THEM ANALYTICAL.
#
# Run 40 confirmed two HIGH defects and the owner ruled that both be fixed before participant
# use rather than accepted for the study period. Fixing them changes persisted-response
# behaviour and document-serving behaviour, so v25 is superseded rather than edited under its
# own stamp: results already computed under v25 remain interpretable against v25.
#
#       v25 -> v26  1. untrusted document content can no longer execute through the same-origin
#                      document-content response
#                   2. substantive final responses become database-immutable after final lock
#
# Nothing else. Neither change touches a module, a formula, a qualification rule, a vote, a
# stimulus, the participant sequence or the AI binding. That is not asserted here: it is proved
# by executing the whole registered population on both lines from their own git objects, which
# is what build_run41_v25_v26_execution_proof.py does, and by the digest comparisons in
# test_run41_preservation.py.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 42 SUPERSEDES v26 WITH v27: THE PER-FIELD DOCUMENT LINEAGE THE RECORD ALWAYS OWED.
#
# The background data-processing mechanism was traced end to end: upload, selected-period
# persistence, extraction, stored facts, module input retrieval, C1/Category-9 qualification,
# category calculation, project status, brief and decision, longitudinal ordering and lineage.
# One defect in that path was proved and repaired.
#
# THE DEFECT. `extraction_merge` builds an observation per document that has always carried
# `document_id`, `sha256`, `revision_of` and `as_of`, and the stored result has always listed
# the same identity per document in `source_documents`. The PER-FIELD source record, however,
# was written as `{"docType", "value"}` and dropped every one of them. The evidence was in
# storage; only this one hop lost it. Consequently `qualification._provenance` -- which counts a
# field as traced only when it carries BOTH a document identity and a document version -- counted
# zero on every project ever computed, and `_timeliness` counted zero as-of dates, so both
# dimensions were structurally pinned to PARTIAL and could never report anything else.
#
#       v26 -> v27  the per-field source record carries the identity of the artefact the field
#                   was read from: documentId, documentVersion, asOf and revisionOf
#
# WHAT THIS IS NOT. No input was invented, no fact fabricated, no qualification rule relaxed and
# no scientific method changed. The figures are the same figures; only their provenance is now
# recorded where the qualification layer reads it. Proved by executing the whole registered
# population on both pinned lines: `module_results`, `category_statuses` and `project_status`
# are byte-identical across the boundary, and the divergence is confined to
# `signal_inputs.sources` and `evidence_qualification`. See build_run42_v26_v27_execution_proof.py.
#
# WHAT REMAINS DELIBERATELY UNRESOLVED. `revision_resolution_status` is still NOT_ESTIMABLE, and
# `_overall` is the weakest of the dimensions, so `overall_qualification_state` remains
# NOT_ESTIMABLE. That is a scientific decision this run did not overturn: test_run12 asserts the
# revision dimension is never anything but NOT_ESTIMABLE, and relaxing it to unblock categories
# would undo a deliberate fail-closed choice rather than repair a mechanism. It is reported to
# the owner as a decision, not silently changed.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 43, sim-2026.08-v28: THE RETIREMENT OF 38 MODULES FROM SERVICE.
#
# WHAT MOVED. Thirty-eight of the 101 registered modules are RETIRED FROM SERVICE. Retirement is
# a statement about the taxonomy and the explanation burden, not a claim that any arithmetic is
# wrong: every retired module keeps its registry entry, its formula function and its audit
# lineage, and `run_module()` on every one of the 101 identifiers returns output byte-identical
# to sim-2026.08-v27. What changed is which modules the production paths ENUMERATE. The single
# authority is the `notes` column of p0-baseline/module_renumbering_map.csv; no list of retired
# identifiers is written anywhere in the tree, and reinstating a module there restores it to
# service with no other edit.
#
# THE POPULATIONS AFTER THE RETIREMENT. The registry holds 101, unchanged. Sixty-three are in
# service and the analytical server computes 62 of those 63; the one it does not is Document Risk
# Score, which the extraction model supplies. Group D, Portfolio Health, falls to zero in
# service, so `portfolio_health.live_portfolio_modules()` returns the empty tuple and the
# dispatcher produces a retired snapshot. `canonical_v8` is untouched and still computes: the
# Run-33 supplied oracles are executed against it directly, so no scientific coverage is lost.
#
# WHAT DID NOT MOVE. No module in service changed its computed result. Project Status, the
# category rollup, the fusion and the voting set are untouched -- voting is still exactly A1.7
# and A1.8, and Group C still does not contribute to project status. Portfolio Health never
# contributed to Project Status, so its offload does not move a status either.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 44, sim-2026.08-v29: THE PARTICIPANT-FACING RENDER DEFECTS PHASE J DIAGNOSED.
#
# WHAT MOVED, AND IT IS ALL AT THE RENDER. Four defects Run 43J classified F, plus one stale
# docstring. (1) The two severity orderings on the project detail page were keyed on the
# capitalised spellings only, and the platform emits two: A1.2 stores lowercase 'green'. A key
# miss fell through to the unknown rank, which is more adverse than Green, so a module whose
# only irregularity was its capitalisation was selected as its category's worst ahead of two
# properly-cased Green ones. Matching is now case-insensitive at every site on that page that
# orders a status, through one shared rank, and no site may name a module as the driver of a
# severity better than its own. (2) An absent document-risk score is stored PRESENT AND NULL by
# design, and Number(null) is 0 and finite, so it rendered "0.00" Green and was shipped into the
# Executive Brief as a key driver. An absent score now renders as absent; a genuine stored zero
# still renders as zero, which is what extraction_merge.py:1128 exists to protect. (3) CPI and
# SPI are computed by select_signal_inputs and were stamped "extracted" on the signals panel and
# in the upload result line; both now say computed. (4) The Portfolio Health flyout told a
# participant it needed three projects; after Run 43's offload no number of projects makes it
# compute, and it now says so, from a predicate DERIVED from the loaded taxonomy so reinstating
# a Portfolio Level module restores the old sentence with no edit.
#
# WHAT DID NOT MOVE. No server computation. `run_module()` on every one of the 101 identifiers
# returns output byte-identical to sim-2026.08-v28, proved by executing both lines. The module
# populations are unchanged: 101 registered, 63 in service, 62 computed, voting exactly A1.7 and
# A1.8. The registry docstring correction at `available_modules()` changes no code path; the
# function's body is untouched.
#
# THE SEQUENCE-BEARING FILE. `assets/js/deepdive.js` is one of the six participant files every
# package record since v10 asserts byte-identical across a successor. This stamp breaks that
# invariant DELIBERATELY and once, for the Portfolio Health sentence, under the owner's explicit
# order at Run 44 section 4.4. The blocker was reconciled to the true bytes; it was not
# disabled, weakened or widened.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 45, sim-2026.08-v30: RETRIEVAL BY FIELD KIND. THE PERIOD-SCOPING FALL-THROUGH IS CLOSED.
#
# WHAT MOVED, AND IT IS IN RETRIEVAL, NOT IN ANY FORMULA. Every observation was scoped to the
# period its document was uploaded into (`documents._period_documents`), which is right for a
# fact about one reporting period and wrong for a fact about the project. A contract uploaded at
# period 1 was invisible from period 2 on, so `bac` fell through to a pay application's weaker
# restatement -- Run 44 measured 4,463,290 where the contract said 5,874,620 -- and
# `baselineContractSum` INVERTED its own declared precedence, a change order's account of the
# original beating the contract that established it.
#
# Fields are now divided into two canonical kinds, decided once and signed off by the owner
# (`code_audit/run45_field_classification_proposal.md`; the ruling is recorded in the Run 45
# report). IDENTITY fields retrieve the latest value AT OR BEFORE the period being computed,
# with declared document-type precedence holding ACROSS the carry-forward. PERIOD fields
# retrieve exactly as before: the period's own documents and nothing else. Thirteen fields are
# identity, sixty-two period, and two -- `totalFloat` and `consumedFloat` -- are recorded
# UNDETERMINED because their declarations contradict each other and the owner ruled the
# contradiction stands; they are retrieved as period fields, which is the unchanged behaviour.
#
# WHAT DID NOT MOVE. No formula, no band, no threshold, no voting set: voting is still exactly
# A1.7 and A1.8, 63 modules in service of 101 registered, Group C still does not contribute to
# project status. PERIOD-FIELD RETRIEVAL IS BYTE-IDENTICAL -- a period field absent in its
# period is still absent, and Run 42's upload-order proof is re-run under the new retrieval and
# holds for both kinds. `docDate` is still derived from the period's OWN observations, so a
# carried figure cannot date a period.
#
# THE CENSUS. On the repository fixtures, exactly three modules move, all on the corpus that has
# something to carry: A1.7 and A1.8 because `bac` is newly visible, and A3.2 because
# `originalContingency` is. The single-period and the four-monthly-report corpora are byte-
# identical before and after, which is the control on the period-field claim.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 47 BOUNDARY, sim-2026.08-v30 -> sim-2026.08-v31. THE EVM CONSISTENCY CHECK.
#
# WHAT MOVED. A served result now carries `consistency_findings`: every relation where ONE
# document stated both a value and the percentage that determines it against a known budget at
# completion, and the two differ by more than 2 per cent of the implied value. Two relations are
# checked: planned value against budget at completion times planned percent complete, and earned
# value against budget at completion times actual percent complete.
#
# WHAT DID NOT MOVE, AND IT IS EVERYTHING IN THIS FILE. No formula, band, threshold, calibration,
# abstention rule or population changed. Nothing is derived into storage: the document takes
# precedence and its figure stands, `pv` is absent from BOUNDED_MAX_SI_FIELDS and stays absent,
# and the check is a pure function called on the READ path from the stored row, so it cannot
# write. A finding carries no band, no colour and no severity, casts no vote and is read by no
# module. The full served census with and without a disagreement present is IDENTICAL.
#
# The stamp advances because what a served result CARRIES is executable behaviour, and a result
# read under v31 answers with a field a result read under v30 did not have.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 48, THE PERIOD THE PROJECT DETAIL PAGE OPENS ON, AND THE LIVE NAMING INSTANCES.
#
# The owner's three rulings of 2026-08-22. 1. THE DETAIL PAGE SHOWS THE LATEST PERIOD THAT HAS
# DOCUMENTS AND HAS BEEN COMPUTED FROM THEM, not period 1 and not the latest period with
# documents alone. `projectperiods` gains two derived read-only fields, `computed_periods` and
# `latest_computed_period`, read from the result table; `primeAndRefresh` reads the row back for
# that period instead of for the literal 1. 2. THE LIVE NAMING INSTANCES ARE CORRECTED: the
# deep-dive panel labels, a chart node label and the text sent to the brief's model carry no
# module identifier and no number. 3. THE BRIEF'S DEAD CATEGORY LABEL MAP IS DELETED.
#
# NOTHING IS COMPUTED DIFFERENTLY. No formula, band, threshold, calibration, abstention rule or
# population moved: voting is still exactly A1.7 and A1.8, 63 modules in service of 101
# registered. No stored figure changed and nothing is derived into storage: every addition is on
# the READ path. No user-facing control was added, moved or removed, and the detail page still
# has no period selector.
#
# The stamp advances because WHICH STORED ROW A PAGE READS is executable behaviour: the same
# project, served to the same reader, answers with period 2's row under v32 where it answered
# with period 1's under v31.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 49, THE COMPLETION OF THE NAMING CORRECTION, sim-2026.08-v32 -> sim-2026.08-v33.
#
# The owner's five rulings of 2026-08-22. Every surviving RENDERED instance of the retired
# "Cat N" scheme is corrected in assets/js/deepdive.js: the ten collapsible group headers, the
# Signal Stack banner, the Dempster-Shafer metric-box label, the synthesis comparison heading,
# its note, its three confidence sentences, the comparison table's row prefix and its column
# header, and the Portfolio Health flyout's module headings. The deep-dive panel label map is
# EXTENDED from nineteen keys to all seventy-seven the call sites pass, so each panel names its
# own category's purpose instead of one neutral phrase. assets/js/detail.js loses an ampersand
# from a section title and stops naming the retired scheme in the executive brief's prompt while
# still forbidding the model to print any identifier. assets/js/decision-ui.js gains COMMENTS
# ONLY at its three inert period literals.
#
# NOTHING IS COMPUTED DIFFERENTLY AND NOTHING IS READ DIFFERENTLY. No formula, band, threshold,
# calibration, abstention rule or population moved: voting is still exactly A1.7 and A1.8, 63
# modules in service of 101 registered. No stored figure changed. No module buckets to a
# different collapsible group: CAT_NUM_FROM_MODULE, the grouping map Run 48 separated from the
# displayed text for exactly this reason, is byte-identical to v32. No user-facing control was
# added, moved or removed, and no panel states a reporting period.
#
# The stamp advances because the SERVED CLIENT is part of the frozen candidate, and the text a
# participant reads on the deep-dive surface is different under v33 from what it was under v32.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 51, sim-2026.08-v34. THE SERVED CLIENT MOVED IN TWENTY-THREE FILES AND THE ANALYTICAL
# LAYER DID NOT.
#
# What a participant reads is different under v34: the Portfolio Health flyout is gone, the
# eight-module compliance panel is two panels, seven deep-dive panels are filed under the
# category their module belongs to in the current taxonomy, an eleventh collapsible group
# exists, the handbook no longer states "96 registered modules", every count on a served page
# derives from registry_index() and service_index() rather than from prose, and no served
# string carries a module identifier, a category identifier, the retired scheme, an ampersand,
# an em dash or an en dash.
#
# NOT ONE ANALYTICAL RESULT MOVED. 101 registered, 63 in service, voting exactly A1.7 and A1.8,
# every stored figure unchanged and the behaviour digest reproduced identically at
# 8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1. The stamp advances because
# the SERVED CLIENT is part of the frozen candidate, not because a computation changed.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 52, sim-2026.08-v35. TWO NAMES FOR THE MODULE IDENTIFIER BECOME ONE, AND ONE DEAD CONTROL
# IS REMOVED. THE ANALYTICAL LAYER DID NOT MOVE.
#
# What a participant reads is different under v35 in exactly one place: the dead "see Health"
# button is gone from the research deep-dive surface. Its handler called
# window.LinIngest.openHealthModal(), which exists nowhere in this repository, so clicking it
# did nothing; it was a control in appearance only. The anomaly sentence it sat beside is
# unchanged and still renders.
#
# THE REST IS ONE NAME ON BOTH SIDES OF THE WIRE. The module identifier is `module_id`
# everywhere: in server/tools/taxonomy_authority.json, in the generator, in both generated
# client mirrors, and in every client consumer. The server already called it `module_id` in the
# stored row, the API response and the export, so the client and the authority moved to the
# server's name rather than the server moving to theirs. Run 51 had moved the same field from
# `num` to `key`; this is the second and final move. The CATEGORY identifier is deliberately
# NOT renamed: a category is not a module, and `module_id` on a category object would be a
# third wrong name rather than one right one.
#
# NO NAMING SWEEP WAS RUN. The owner's ruling 4 of 2026-08-23 makes displayed identifiers --
# "Cat 4", "A4.2", "1.7" -- acceptable. Not one identifier was removed from rendered text and
# not one was restored.
#
# WHAT RULING 1 ASKED FOR WAS NOT DONE, AND THE REASON IS RECORDED HERE. The order directed the
# removal of the project list's "Open" control on the premise that Manage and Open lead to the
# same project detail page. DRIVEN IN A REAL BROWSER, THEY DO NOT: Manage opens an inline admin
# accordion under its own row and never leaves the portfolio page, while Open is the ONLY route
# from the project list to the project detail page. Removing it would have removed that route.
# The surface is stopped under the Run 52 order's section 8.1 and Open still renders.
#
# NOT ONE ANALYTICAL RESULT MOVED. 101 registered, 63 in service, voting exactly A1.7 and A1.8,
# every stored figure unchanged and the behaviour digest reproduced identically at
# 8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1. The stamp advances because
# the SERVED CLIENT is part of the frozen candidate, not because a computation changed.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 55 SUPERSEDES v35 WITH sim-2026.08-v36. THE STAMP ADVANCES BECAUSE THE SERVED CLIENT IS
# PART OF THE FROZEN CANDIDATE, NOT BECAUSE A COMPUTATION CHANGED. Runs 54 and 55 deleted the
# unreachable client-side deep-dive surface and its route, made the project list's Manage
# control navigate to the project detail page in place of a redundant Open control, and moved
# the six operational admin controls onto that detail page. NOT ONE FORMULA, BAND, THRESHOLD,
# CALIBRATION, ABSTENTION RULE OR POPULATION MOVED: 101 registered, 63 in service, voting
# exactly A1.7 and A1.8, every stored figure unchanged and the behaviour digest RE-DERIVED
# identically at 8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 56 SUPERSEDES v36 WITH sim-2026.08-v37. THE STAMP ADVANCES BECAUSE THE SERVED CLIENT IS
# PART OF THE FROZEN CANDIDATE, NOT BECAUSE A COMPUTATION CHANGED. Run 56 removed the duplicate
# "Upload documents" control from the project detail page -- the page already carried
# .detail-upload, which calls the same function with the same project id -- and put a
# confirmation in front of Archive and in front of Reset signals, reusing the LinUI.openModal
# shape the application already uses for its destructive project-scoped actions rather than
# inventing a second pattern. The ordered removal of .detail-reset was STOPPED under section 9.1
# of the Run 56 order: measured byte for byte at e13b4f1, NEITHER reset control is a superset of
# the other, so removing either loses something the survivor does not do, and both remain.
# NOT ONE FORMULA, BAND, THRESHOLD, CALIBRATION, ABSTENTION RULE OR POPULATION MOVED: 101
# registered, 63 in service, voting exactly A1.7 and A1.8, every stored figure unchanged and the
# behaviour digest RE-DERIVED identically at
# 8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 57 SUPERSEDES v37 WITH sim-2026.08-v38. THE STAMP ADVANCES BECAUSE THE SERVED CLIENT IS
# PART OF THE FROZEN CANDIDATE, NOT BECAUSE A COMPUTATION CHANGED. The project detail page
# carried TWO controls that clear stored signals, and Run 56 measured that NEITHER was a superset
# of the other and so stopped rather than remove either. Run 57 MERGES the two handler bodies
# into ONE control that does the UNION and removes the other: `.pe-reset` survives with the
# union and Run 56's confirmation, and `.detail-reset`, its aria-live span, its handler, its call
# site and its now-dead CSS rule are gone. WHAT A PARTICIPANT READS AND CLICKS is part of the
# frozen candidate, so the freeze is SUPERSEDED rather than amended.
# NOT ONE FORMULA, BAND, THRESHOLD, CALIBRATION, ABSTENTION RULE OR POPULATION MOVED: 101
# registered, 63 in service, voting exactly A1.7 and A1.8, every stored figure unchanged and the
# behaviour digest RE-DERIVED identically at
# 8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 59. NO MARKDOWN DOCUMENT CARRIES AUTHORITY. The stamp moves because SIX production-tree
# members moved: assets/js/decision-ui.js, p0-baseline/MODULE_TAXONOMY.md and four comments in
# server/app -- research_export.py, document_evidence.py, evm_consistency.py and
# simulation/portfolio_health.py -- each of which cited a markdown rule the owner SUPERSEDED on
# 2026-08-23, one of them ("NAMING_AUTHORITY section 4") citing the very section that recorded
# the reversal. Every one of the six edits is a COMMENT or a document. NOT ONE EXECUTABLE BYTE
# MOVED, no rendered string moved, no control was added, moved or removed.
# assets/js/decision-ui.js is SEQUENCE-BEARING and its move is a NAMED EXCEPTION of record on
# the v23-to-v24 link, declared in participant_packages.V23_TO_V24_SEQUENCE_EXCEPTION rather
# than discovered by a checksum.
# NOT ONE FORMULA, BAND, THRESHOLD, CALIBRATION, ABSTENTION RULE OR POPULATION MOVED: 101
# registered, 63 in service, voting exactly A1.7 and A1.8, every stored figure unchanged and the
# behaviour digest RE-DERIVED identically at
# 8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1.
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# RUN 62 SUPERSEDES v39 WITH sim-2026.08-v40. THE STAMP ADVANCES BECAUSE THE SERVED CLIENT IS
# PART OF THE FROZEN CANDIDATE, NOT BECAUSE A COMPUTATION CHANGED. This release PUBLISHES the
# work of Runs 60 and 61, which were finished, gated nowhere and stacked unmerged. Run 60
# DIAGNOSED, in a rendered browser, that the stored-signal row a project detail page reads was
# not necessarily the row of the period the page holds; Run 61 FIXED it by making the caller
# state its question -- the client taxonomy module now keys its row cache by (project, period)
# and exposes rowForPeriod / latest / rowsForPeriods, the workspace module resolves the computed
# period before it asks for results, and the detail module re-renders its provenance line from
# the row it actually received. (The client file names are deliberately NOT written as paths
# here: test_run16_material_cost_variance_disabled.py asserts that no source under server/app
# resolves the browser's taxonomy file, and it makes that assertion by substring search, so even
# a comment naming the path turns it red. The guard is over-broad against its own stated intent
# -- reported, not changed.)
# THREE production-tree members moved: the client detail, taxonomy and workspace modules under
# assets/js/. The workspace module is SEQUENCE-BEARING and its move is a NAMED
# EXCEPTION of record on the v24-to-v25 link, declared in
# participant_packages.V24_TO_V25_SEQUENCE_EXCEPTION rather than discovered by a checksum.
# NOT ONE FORMULA, BAND, THRESHOLD, CALIBRATION, ABSTENTION RULE OR POPULATION MOVED: 101
# registered, 63 in service, voting exactly A1.7 and A1.8, every stored figure unchanged and the
# behaviour digest RE-DERIVED identically at
# 8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1.
# -------------------------------------------------------------------------------------------
# RUN 67 ADVANCES THE STAMP TO v42, AND THE BEHAVIOUR BEHIND IT HAS GENUINELY MOVED, which is
# why it is a new stamp and not a re-derivation of the old one. Runs 65, 66 and 67 are published
# together. What a participant sees is different: categories carry statuses they did not carry
# before, because every module that produced a value now votes into its own category (Run 65),
# and five more modules compute because the period's Category-9 assessment is written for the
# first time (Run 67). 101 registered, 63 in service, voting boundaries still sourced for exactly
# A1.7 and A1.8. Results computed under sim-2026.08-v41 remain valid under that stamp.
# -------------------------------------------------------------------------------------------
# RUN 89 ADVANCES THE STAMP TO v43, AND THE BEHAVIOUR BEHIND IT HAS GENUINELY MOVED. Four
# changes, all of them the owner's rulings, and each changes what a stored row says:
#
#   1. B1.2 WEIGHTED VOTING READS THE SIX PERFORMANCE CATEGORY POSTURES, not the four assembled
#      arms. Two of those arms traced to modules the owner has dropped. The weight profile is
#      HIS STATED AUTHORITY -- A1 0.25, A2 0.25, A3 0.15, A4 0.10, A6 0.15, A5 0.10 -- and Data
#      Integrity is excluded from it by an executable guard. Because the postures do not exist
#      at module dispatch, B1.2 abstains there and is evaluated in a SECOND PASS after the
#      category rollup, which also makes it structurally incapable of reaching the rollup that
#      produced its own input. Its class-weight distribution moved off the row key `votes`,
#      which `registry.run_all` already uses for a boolean, onto `class_votes`.
#   2. DATA INTEGRITY IS AN ELIGIBILITY GATE. The category's role is stated in its
#      specification; nothing in the code moved, because three independent barriers already
#      held it out of the project status and all three were measured.
#   3. THE REQUIRED CORE. An OFFICIAL project status is issued only when A1, A2, A3 and A6 all
#      carry a posture; otherwise it is INDETERMINATE, with the fused band recorded beside it.
#      WORST-WINS IS UNTOUCHED -- measured identical across all 256 four-band combinations --
#      and "Indeterminate" is deliberately not a band and is not in BAND_SEVERITY.
#   4. THREE MODULES LEFT SERVICE by Run 43's own mechanism: A5.1 DSM Rework Propagation, A5.5
#      Rework Feedback Loop and B4.4 What-If Scenario Matrix, each defined on a structure
#      prepared for a method rather than on a thing a project document prints.
#
# THE POPULATION MOVED: 101 registered, 60 IN SERVICE (was 63), 41 retired (was 38), 59 the
# server computes. Voting is still exactly A1.7 and A1.8. Results computed under sim-2026.08-v42
# remain valid under that stamp.
# -------------------------------------------------------------------------------------------
# RUN 95 ADVANCES THE STAMP TO v44, AND THE BEHAVIOUR BEHIND IT HAS GENUINELY MOVED. Three
# changes, all of them the owner's rulings, and each changes what a stored row says:
#
#   1. FIFTEEN MODULES LEFT SERVICE by Run 43's own mechanism, the `RETIRED ` note on the
#      registry CSV row: A1.3, A1.4, A1.10, A2.2, A2.3, A3.1, A3.7, A3.9, A4.1, A4.10, A5.2,
#      A5.4, A5.6, A5.7 and A5.8. Their identifiers still resolve and `retired_modules()` still
#      lists them; their specifications were archived verbatim under `specifications/archive/`
#      with a pointer line left in place. RUN 96 SUPERSEDED THIS: the rows, the pointer lines and
#      the archive were all deleted, so those identifiers no longer resolve. Fewer modules compute, so category rollups that read
#      them produce different postures, which is why this is a new stamp.
#   2. A5 SYSTEMS AND DYNAMICS IS GONE. It held exactly the five A5 modules above, so it now
#      holds none in service. The owner's ruling is that an empty category has nothing to
#      report rather than failing to report: it is removed from the weighted profile, from the
#      required core, and from both charts.
#   3. THE REQUIRED CORE IS ALL FIVE remaining weighted performance categories -- A1, A2, A3,
#      A4, A6 -- superseding Run 89's core of four; A4 Document Signals moved from supporting to
#      required, and there is no supporting tier left. The weight profile is the owner's RESTATED
#      STATED AUTHORITY: A1 0.28, A2 0.28, A3 0.17, A4 0.11, A6 0.16, summing to one under a new
#      executable assert, with Data Integrity still excluded by the existing one. WORST-WINS IS
#      UNTOUCHED -- measured identical across all 1024 five-band combinations -- and
#      "Indeterminate" is still deliberately not a band.
#
# THE POPULATION MOVED AGAIN: 101 registered, 45 IN SERVICE (was 60), 56 retired (was 41), 45
# the server computes (was 59), and NOTHING is supplied any more (was 1) -- A4.1 Document Risk
# Score was the last module in service with no runner, and retiring it emptied
# `unported_modules()`. The five weighted performance categories hold 27 between them. Voting is
# still exactly A1.7 and A1.8. Results computed under sim-2026.08-v43 remain valid under that
# stamp.
# RUN 99 moves this to v45 because this run CHANGES WHAT THE PLATFORM COMPUTES: a project whose
# earned value, planned value and actual cost all equal its budget at 100 per cent now publishes
# "Complete", where before it published "Indeterminate" like every other project. Nothing else
# about the rollup moves: worst-wins, the required core and the Indeterminate gate are unaltered.
# RUN 100 moves this to v46 because this run CHANGES WHAT THE PLATFORM COMPUTES, in two places.
#
#   1. `docRiskScore` is no longer compared across documents when the period's Category-9
#      evidence record looks for material conflicts. It is a per-document self-score, not a
#      shared assertion about the project, so two documents carrying different ones were never
#      contradicting each other -- and the false conflict refused EVERY gated module on any
#      realistic upload. Measured on the real route: A6.1, A6.2 and A6.3 now compute on a
#      21-document fixture where all four A6 modules previously abstained on
#      "1 unresolved material conflict".
#   2. The recorded spec applier no longer falls back to the bare category key. A recorded
#      answer is served only on an exact prompt-sha256 match -- that is, only against the
#      figures it was recorded against -- and anything else abstains with the reason stated.
#      Before this run a project at 100 per cent and one at 25 per cent were measured receiving
#      the identical recorded A1 posture. THIS AFFECTS THE KEYLESS PATH ONLY: `build_applier`
#      returns the configured provider's applier whenever its key is present and never consults
#      the recorded corpus at all.
#
# Nothing else moves: worst-wins, the required core, the Indeterminate gate, Conservative
# Dominance and Run 99's `delivery_complete` are all unaltered. Results computed under
# sim-2026.08-v45 remain valid under that stamp.
#
# ------------------------------------------------------------------ RUN 101, sim-2026.08-v46 -> v47
#
# THE SUCCESSOR IS MINTED BECAUSE THIS RUN CHANGES WHAT MODULES COMPUTE, and section 10.10 of
# the owner's Run 101 order requires it. A reading stamped v46 and a reading stamped v47 are not
# comparable, and the stamp is what says so.
#
# WHAT MOVED, and every item of it changes a stored reading:
#
#   1. EIGHT MODULES GAINED OR LOST A BAND. A3.2 Contingency Burn and A3.3 Labor Productivity now
#      assert one; A3.6 Cost Risk P80 now READS `bac`, which it never did, and bands the gap
#      against it; A6.1, A6.3 and A6.4 assert one where their evidence supports it; A6.2 asserts
#      the near-miss band only. A3.5 Overhead Absorption asserts none and now records WHY on the
#      row. A4.3 Submittal Rejection LOST its uncited 5/15/25 ladder.
#   2. A4.2 RFI Velocity no longer bands on requests per week. The overdue count bands, against
#      the contract's own response period. A4.6 Change Order Frequency became change IMPACT and
#      bands on cost and schedule impact rather than reporting a frequency without a colour.
#   3. A6.2 SAFETY IS REBUILT. One recordable rate became three measures -- frequency on both the
#      OSHA and ILO bases, severity under the 180-day cap and the 6,000-day fatality charge, and
#      near-miss reporting and closure -- reported separately and never composited.
#   4. A6.4 GAINED A CORPUS PATH. `past_performance_report`'s four CPARS-shaped ratings were
#      orphan fields no module read; they now assemble a contractor assessment record.
#   5. EVERY BAND NOW CARRIES ITS BOUNDARY AND ITS BASIS in the stored reading
#      (`band_boundary`, `band_basis`, `band_provenance_class`). New keys on a JSON column, so no
#      migration -- but the stored row is genuinely different and the stamp must say so.
#
# Nothing else moves. Worst-wins, the required core of five, the Indeterminate gate, Conservative
# Dominance, `delivery_complete` and `scope_signal_inputs` are all unaltered, and no stored row
# was migrated, deleted or rewritten. Results computed under sim-2026.08-v46 remain valid under
# that stamp.
# RUN 102 -> sim-2026.09-v48. WHAT MODULES COMPUTE CHANGED AGAIN, and section 10.10 orders the
# mint. Six things moved:
#
#   1. A2.1 PERT Network Criticality, A2.7 Milestone Trend, A2.8 Look-Ahead Health and A2.9
#      Resource Loading NOW BAND. Run 101 ordered the first and the fourth left bandless and the
#      owner has reversed that. Each carries the owner's configured tolerance and its hard
#      override; A2.7 additionally COMPUTES A NEW QUANTITY, the slip ratio, which it did not.
#   2. A6.1 QUALITY IS REBUILT. It computed a requirement conformance rate and banded on it; it
#      now computes FIRST-PASS INSPECTION ACCEPTANCE and bands on that, with the critical-item
#      override. The conformance rate is still reported and is no longer what bands.
#   3. A6.2 SAFETY FREQUENCY BANDS ON THE BENCHMARK RATIO -- project TRIR over the published
#      construction TRIR -- rather than on three absolute cutoffs derived from it, and gains the
#      fatality / life-threatening / stop-work / high-severity hard override. The three measures
#      are unchanged and are still never composited; the exposure floor is unchanged.
#   4. A6.3 ENVIRONMENTAL IS REBUILT AGAIN, from Run 101's consequence ladder to a TIMELY
#      CLOSURE RATE with a mandatory-deadline override. It computes a quantity it did not.
#   5. A6.4 GAINED A NUMERIC FALLBACK for a score that is not one of the five CPARS ratings.
#   6. EVERY BAND NOW ALSO CARRIES `threshold_source` -- which rung of the owner's precedence
#      order supplied its figure. New key on a JSON column, so no migration; the stored row is
#      genuinely different and the stamp must say so.
#
# Nothing else moves. Worst-wins, the required core of five, the Indeterminate gate, Conservative
# Dominance, `delivery_complete` and `scope_signal_inputs` are all unaltered, and no stored row
# was migrated, deleted or rewritten. Results computed under sim-2026.08-v47 remain valid under
# that stamp.
SIMULATION_VERSION = "sim-2026.09-v49"

#: THE LINE RUN 49 SUPERSEDED, kept addressable so a reader of this file can see which stamp the
#: immediately preceding audit baseline is without reading the comment above. Every stamp from
#: sim-2026.07-v1 to this one remains valid for the results computed under it.
SIMULATION_VERSION_SUPERSEDED = "sim-2026.09-v48"

#: Every stamp this analytical layer has carried, oldest first. A run that adds a stamp appends;
#: nothing here is ever edited or removed, because each row is the audit baseline for results
#: already collected under it.
SIMULATION_VERSION_HISTORY: tuple[str, ...] = (
    "sim-2026.07-v1", "sim-2026.08-v2", "sim-2026.08-v3", "sim-2026.08-v4", "sim-2026.08-v5",
    "sim-2026.08-v6", "sim-2026.08-v7", "sim-2026.08-v8", "sim-2026.08-v9", "sim-2026.08-v10",
    "sim-2026.08-v11", "sim-2026.08-v12", "sim-2026.08-v13", "sim-2026.08-v14",
    "sim-2026.08-v15", "sim-2026.08-v16", "sim-2026.08-v17",
    "sim-2026.08-v18", "sim-2026.08-v19", "sim-2026.08-v20", "sim-2026.08-v21",
    "sim-2026.08-v22", "sim-2026.08-v23", "sim-2026.08-v24", "sim-2026.08-v25",
    "sim-2026.08-v26", "sim-2026.08-v27", "sim-2026.08-v28", "sim-2026.08-v29",
    "sim-2026.08-v30", "sim-2026.08-v31", "sim-2026.08-v32", "sim-2026.08-v33",
    "sim-2026.08-v34", "sim-2026.08-v35", "sim-2026.08-v36", "sim-2026.08-v37",
 "sim-2026.08-v38", "sim-2026.08-v39", "sim-2026.08-v40",
 "sim-2026.08-v41",
 "sim-2026.08-v42",
 "sim-2026.08-v43",
 "sim-2026.08-v44",
 # RUN 99: the Complete promotion. A project whose earned value, planned value and actual cost
 # all equal its budget at 100 per cent publishes "Complete"; before v45 it published
 # "Indeterminate" like every other project. Rows stamped v44 and earlier remain valid under
 # their own stamp.
 "sim-2026.08-v45",
 # RUN 102 APPENDS THE THREE THAT WERE MISSED. This tuple is documented as never edited and
 # only appended to, and it stopped at v45: Run 100's v46 and Run 101's v47 moved
 # SIMULATION_VERSION without appending here, so the history disagreed with the stamp. Both are
 # added now in the order they were minted, with v48 after them. Nothing already in this tuple
 # is altered, and no stored row is touched: this is the record catching up with the stamps, not
 # a claim that anything was recomputed.
 "sim-2026.08-v46",
 # RUN 101: the bands and their provenance. A6.2 became three measures, A4.2 and A4.6 were
 # rebuilt, and every band began carrying its boundary, its basis and its provenance class.
 "sim-2026.08-v47",
 # RUN 102: Schedule gets its four bands, three A6 modules are re-banded on the owner's stated
 # measures, A6.4 gains a numeric fallback, and every band carries its `threshold_source`.
 "sim-2026.09-v48",
 # RUN 103: A2.12 Critical Path Analysis enters service; the schedule network gains a full
 # diagnostics pass and a document supply path; A2.1 PERT is gated behind the network's validity
 # and behind stated duration uncertainty; A2.7 Milestone Trend is re-banded onto the SAME hybrid
 # slip rule A2.12 uses; and A3.5 Overhead Absorption bands for the first time. THE STAMP IS
 # MOVED AND THIS TUPLE IS APPENDED TO IN THE SAME EDIT, which is what section 10.10 requires and
 # what Runs 100 and 101 did not do. No stored row is recomputed and none is touched: rows
 # stamped v48 and earlier remain valid under their own stamp.
 "sim-2026.09-v49",
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
                 reason_code: str | None = None, **fields: Any) -> dict[str, Any]:
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
    # RUN 103. AN ABSTENTION MAY CARRY THE EVIDENCE OF WHY IT ABSTAINED. The owner's section 2.1
    # requires the schedule-network diagnostics -- the counts and the affected rows -- to travel
    # with the refusal, so the scheduler can correct the source in one pass. Nothing here can
    # turn an abstention into a reading: `status_color` stays None and `insufficient_data` stays
    # True whatever is passed, and neither may be overwritten.
    for _k, _v in fields.items():
        if _k in ("status_color", "insufficient_data", "method_class"):
            raise ValueError(f"an abstention may not carry {_k!r}")
        out[_k] = _v
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
# rather than in `abstained`.
#
# CORRECTED BY RUN 67, BECAUSE THE SENTENCE THAT STOOD HERE IS NO LONGER TRUE AND IT IS
# LOAD-BEARING. It read: "the row cannot reach status fusion because fusion reads only the two
# voting modules". RUN 65 REMOVED THAT FILTER with the owner's authority, so a
# calibration-pending row DOES reach `by_category` now. What happens when it gets there was
# established by execution rather than assumed: `fusion.fuse_signals` skips a signal whose band
# is None before any mass is assigned, so such a row CONTRIBUTES NO MASS, cannot drag its
# category down and cannot lift it either. A category all of whose modules asserted no band
# fuses to nothing at all -- not to Unknown -- so it carries no status and does not vote.
# `test_run67_category9_and_no_band.py` pins all of that, including the proof that it is the
# missing band and not the fixture doing the work.
#
# WHAT THIS COSTS, STATED PLAINLY: 34 of the 63 modules in service can return this shape, and
# every one of them computes a real figure that contributes NOTHING to any status. That is the
# largest single reason a category stays grey with modules computing beneath it. It is not a
# defect to be repaired by attaching a ladder: every one of those 34 carries parameter class
# UNSUPPORTED in `parameters.PARAMETER_PROVENANCE`, whose own words are that no source in this
# repository, in the supervisory specification, or in any publication cited by this platform
# specifies a boundary for the quantity -- and that "replacing an invented number with a
# different invented number is not a repair". Only A1.7 and A1.8 have an entry in
# `registry.BAND_SOURCES`. A band attached to any of the other 34 would be invented.
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


# =============================================================================================
# RUN 101 -- THE BAND, ITS BOUNDARY, AND WHERE THE BOUNDARY CAME FROM
#
# THE OWNER'S RULING, RUN 101 SECTION 2. A module may assert a band only when a threshold exists
# whose QUANTITY, DENOMINATOR, TIME BASIS and DIRECTION OF FAVOURABILITY match what the module
# actually computes. Otherwise it computes, displays, asserts no band, casts no vote.
#
# AND WHERE A BAND IS ASSERTED, ITS SOURCE TRAVELS WITH IT, PERMANENTLY AND IN THE STORED ROW.
# Section 3: "A threshold with no recorded basis is the defect this platform has spent forty runs
# removing -- so the source travels with the number." `computed_results.module_results` is a JSON
# blob (`research_models.py`), so these keys need no column and no migration.
#
# THE THREE PROVENANCE CLASSES ARE THE OWNER'S, VERBATIM FROM SECTION 3.
# =============================================================================================

#: The threshold rests on a standard, regulation, or agency requirement.
PROVENANCE_CODIFIED: str = "CODIFIED"
#: Widely used in practice, no standards clause fixing it.
PROVENANCE_CONVENTION: str = "CONVENTION"
#: No published basis found; the number is the owner's stated decision.
PROVENANCE_OWNER_CALIBRATED: str = "OWNER-CALIBRATED"

#: The plain words the decision brief prints for each class (Run 101 section 6.3). The brief
#: composes from THIS, not from a model and not from a sentence written at the call site, so the
#: same class always reads the same way wherever it is printed.
PROVENANCE_WORDS: dict[str, str] = {
    PROVENANCE_CODIFIED: "a standard, regulation or agency requirement",
    PROVENANCE_CONVENTION: "widely used convention",
    PROVENANCE_OWNER_CALIBRATED: "no published basis; the owner's stated threshold",
}

BAND_PROVENANCE_CLASSES: frozenset[str] = frozenset(PROVENANCE_WORDS)


# =============================================================================================
# RUN 102, SECTION 6. `threshold_source` -- WHICH LAYER OF THE PRECEDENCE ORDER SUPPLIED THIS
# THRESHOLD. IT SITS BESIDE `band_basis_provenance_class` AND DOES NOT REPLACE IT.
#
# THE TWO ANSWER DIFFERENT QUESTIONS AND THAT IS WHY BOTH ARE STORED:
#
#   band_basis_provenance_class  -- WHAT KIND OF THING the basis is. CODIFIED / CONVENTION /
#                                   OWNER-CALIBRATED. An epistemic claim: is there a standard
#                                   behind this number, a widely used practice, or nothing but
#                                   the owner's judgement.
#   threshold_source             -- WHICH RUNG OF THE OWNER'S PRECEDENCE ORDER actually
#                                   supplied the figure THIS reading used. project_specific /
#                                   formal_external_basis / owner_configured_default. A
#                                   procedural claim about where the platform got it.
#
# THEY ARE NOT A RENAMING OF ONE ANOTHER AND THE MAPPING IS NOT ONE-TO-ONE. A codified basis can
# arrive from a project document (a contract restating a regulatory deadline: CODIFIED /
# project_specific) or from the formal external instrument itself (CODIFIED /
# formal_external_basis). An owner-calibrated boundary is normally owner_configured_default, but
# a project quality plan stating a stricter acceptance figure is OWNER-CALIBRATED in kind and
# project_specific in source. So both are written and neither is derived from the other.
#
# RUNG 4 OF THE PRECEDENCE ORDER -- no threshold available -- HAS NO VALUE HERE ON PURPOSE. A
# reading with no threshold asserts no band, so it never reaches this function; it goes through
# `band_abstained` with its reason, which is section 6's rung 4 implemented exactly.
THRESHOLD_SOURCE_PROJECT = "project_specific"
THRESHOLD_SOURCE_EXTERNAL = "formal_external_basis"
THRESHOLD_SOURCE_OWNER = "owner_configured_default"

THRESHOLD_SOURCE_WORDS: dict[str, str] = {
    THRESHOLD_SOURCE_PROJECT: ("a threshold stated in a document this project uploaded -- its "
                               "contract, permit, approved baseline, quality control plan, "
                               "inspection and test plan, or an owner-supplied figure"),
    THRESHOLD_SOURCE_EXTERNAL: ("a formal external basis -- a published standard, regulation, "
                                "agency instrument or industry benchmark"),
    THRESHOLD_SOURCE_OWNER: ("the owner's configured default tolerance for this platform, "
                             "stated in his Run 102 threshold table"),
}

THRESHOLD_SOURCES: frozenset[str] = frozenset(THRESHOLD_SOURCE_WORDS)


#: RUN 101, MID-RUN. THE RESEARCH REPORTS ARRIVED AFTER GOAL ONE WAS FIRST IMPLEMENTED, AND THEY
#: FORCED THIS DISTINCTION. `RESEARCH_2_safety_and_environmental_severity.md`, recommendation 2:
#: "Band frequency against the published industry average, not an invented cutoff. State that ONLY
#: THE INDUSTRY-AVERAGE ANCHOR IS SOURCED; intermediate cutoffs are platform-chosen with no
#: published basis." `RESEARCH_1_threshold_bands_eight_metrics.md` section 5 puts it more broadly:
#: "There is no recognized standard governing how a number maps to a Green/Yellow/Amber/Red band
#: ... all boundary numbers are ultimately owner design choices that should be documented, not
#: presented as externally mandated."
#:
#: SO ONE CLASS PER MODULE CANNOT TELL THE TRUTH ABOUT SEVERAL OF THEM. Safety's ANCHOR is the
#: BLS construction average and the OSHA identity -- codified; its half-average and twice-average
#: CUTOFFS are the owner's. The P80 CONCEPT is DOE O 413.3B and GAO-20-195G -- codified; the exact
#: gap percentage that divides Yellow from Amber is, in Report 1's words, "moderate ...
#: interpretive". Storing one class for both would present a platform-chosen cutoff as though a
#: standard fixed it, which is the precise misrepresentation this run exists to remove.
#:
#: TWO FIELDS, THEREFORE. `band_basis_provenance_class` is where the MEASURE and its ANCHOR come
#: from; `band_boundary_provenance_class` is where the CUTOFFS come from. A module whose two are
#: the same passes one value and both are written, so nothing is lost for the simple cases.
def banded(method_class: str, message: str, *, status_color: str, boundary: str,
           basis: str, provenance: str, threshold_source: str,
           boundary_provenance: str | None = None,
           **fields: Any) -> dict[str, Any]:
    """
    A result that DOES assert a band, carrying the boundary it crossed and that boundary's basis.

    `boundary` is what the figure was measured against, in words, including WHICH SIDE each
    boundary is inclusive on (section 3, boundary rule 1). `basis` is the source, as the owner's
    order states it. `provenance` is one of the three classes above.

    Nothing here decides a band: the caller has already decided it from its own arithmetic. This
    function exists so that a band and its provenance cannot be stored apart from one another --
    it raises rather than emitting a colour with no recorded basis, which is exactly the defect
    section 12.2 fails the run for.
    """
    boundary_provenance = boundary_provenance or provenance
    # RUN 102, SECTION 12.5. A BAND STORED WITHOUT ITS THRESHOLD SOURCE IS A RUN-FAILING ACT, so
    # this is a REQUIRED keyword and it raises rather than defaulting. A default here would be a
    # place where forgetting is possible, which is the whole reason provenance is enforced the
    # same way one line below.
    if threshold_source not in THRESHOLD_SOURCES:
        raise ValueError(f"{method_class}: {threshold_source!r} is not one of the three "
                         f"threshold sources; a band may not be stored without one")
    for _p in (provenance, boundary_provenance):
        if _p not in BAND_PROVENANCE_CLASSES:
            raise ValueError(f"{method_class}: {_p!r} is not one of the three provenance "
                             f"classes; a band may not be stored without one")
    if not str(basis).strip() or not str(boundary).strip():
        raise ValueError(f"{method_class}: a band may not be stored without its boundary and "
                         f"its basis")
    out: dict[str, Any] = {
        "method_class": method_class,
        "status_color": status_color,
        "band_asserted": True,
        "band_boundary": boundary,
        "band_basis": basis,
        # KEPT UNDER ITS ORIGINAL NAME so nothing that already reads it breaks; it is the
        # BASIS class, which is what it always meant.
        "band_provenance_class": provenance,
        "band_provenance_words": PROVENANCE_WORDS[provenance],
        "band_basis_provenance_class": provenance,
        "band_boundary_provenance_class": boundary_provenance,
        "band_boundary_provenance_words": PROVENANCE_WORDS[boundary_provenance],
        # RUN 102, SECTION 6. Which rung of the precedence order supplied this threshold.
        "threshold_source": threshold_source,
        "threshold_source_words": THRESHOLD_SOURCE_WORDS[threshold_source],
        "threshold_precedence_order": (
            "project-specific document, then formal external basis, then the owner's configured "
            "default. Where none of the three supplies a threshold the figure is displayed, no "
            "band is asserted, no vote is cast and the reason is stated"),
        "band_provenance_split_note": (
            "the BASIS -- the measure and the anchor it is drawn against -- and the BOUNDARIES "
            "-- the cutoffs that divide the bands -- may come from different places, and where "
            "they do this reading says so rather than presenting a platform-chosen cutoff as "
            "though a standard fixed it"
            if boundary_provenance != provenance else None),
        "evidence_metric": message,
    }
    out.update(fields)
    return out


def band_abstained(method_class: str, message: str, *, reason: str,
                   **fields: Any) -> dict[str, Any]:
    """
    A COMPUTED figure with NO band, and the reason stated on the row.

    Section 2: a module with no matching threshold "computes and displays its figure, asserts no
    band, casts no vote, and takes no part in category posture ... with the reason stated on the
    module and carried into the decision brief's limitations". Section 3 boundary rule 2: a
    figure outside every band abstains WITH A STATED REASON and does not fall to a nearest band.

    This is `calibration_pending` with the reason made specific to this module rather than the
    one shared sentence, and it routes to `run["computed"]` by the same `calibration_pending`
    flag `registry.record` already reads.
    """
    out = calibration_pending(method_class, message, **fields)
    out["band_withheld_reason"] = reason
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
    index.

    RUN 102, SECTION 0.1. THE OWNER HAS REVERSED RUN 101's INSTRUCTION THAT THIS MODULE STAY
    BANDLESS. It bands on the criticality index against his configured tolerances, with the
    zero-or-negative-controlling-float hard override; see the block at the band below for why
    that override is evaluated against an IMPOSED finish date and not against the backward
    pass's own float. The old ladder Run 28 removed is NOT restored: it was drawn over a ratio
    of an eightieth percentile to a modal baseline, which is a different quantity, and nothing
    here reintroduces it.
    """
    # ================== RUN 103, SECTION 2.4. PERT IS GATED BEHIND THE NETWORK'S VALIDITY, AND
    # BEHIND THE PRESENCE OF DURATION UNCERTAINTY.
    #
    # The owner's ruling: "PERT Network Criticality runs only after the network validates and
    # only when duration-uncertainty inputs exist -- three-point or distribution durations.
    # Absent them, PERT is Not Assessed while Critical Path Analysis still produces its posture.
    # PERT is never a substitute for CPA."
    #
    # BEFORE THIS RUN `pert_criticality` FELL BACK to a single deterministic pass when any
    # activity lacked a three-point estimate, and reported a criticality index of 1.0 or 0.0 per
    # activity from ONE pass. That index is a deterministic critical-path flag wearing a
    # stochastic measure's name, and section 12.3 forbids exactly that. The fallback is not
    # removed from `canonical_v3` -- it is still the documented deterministic-collapse oracle --
    # but this MODULE no longer takes it: with no duration uncertainty stated, PERT is NOT
    # ASSESSED and A2.12 Critical Path Analysis is the module that reports on this network.
    from .canonical_v3 import schedule_network_diagnostics as _diagnose
    try:
        structure = require_v3_structure(si, "A2.1")
    except StructureAbsent as absent:
        return insufficient("PERT_Network_Criticality", absent.sentence,
                            ABSTAIN_STRUCTURE_ABSENT)
    _diag = _diagnose(structure)
    _diag_fields = {k: v for k, v in _diag.items() if not k.startswith("_")}
    if not _diag["valid"]:
        return insufficient(
            "PERT_Network_Criticality",
            (_diag["structure_refusal"] or
             (f"The schedule export provided carries {_diag['fault_total']} logic faults "
              f"({', '.join(_diag['faults_present'])}), so the network does not validate. PERT "
              f"runs only after the network validates, and no criticality is simulated over a "
              f"network whose logic could not be read. The affected rows are recorded beside "
              f"this reason.")),
            ABSTAIN_STRUCTURE_ABSENT,
            schedule_network_diagnostics=_diag_fields,
            canonical_structure="schedule_network")
    try:
        network = parse_schedule_network(structure)
    except StructureAbsent as absent:
        return insufficient("PERT_Network_Criticality", absent.sentence,
                            ABSTAIN_STRUCTURE_ABSENT,
                            schedule_network_diagnostics=_diag_fields)
    _no_uncertainty = sorted(
        a for a, v in network["activities"].items()
        if v["optimistic"] is None or v["most_likely"] is None or v["pessimistic"] is None)
    if _no_uncertainty:
        return insufficient(
            "PERT_Network_Criticality",
            (f"The network validates, but {len(_no_uncertainty)} of "
             f"{network['count']} activities state no duration uncertainty -- no three point "
             f"estimate and no duration distribution (first: "
             f"{', '.join(_no_uncertainty[:5])}). PERT measures how often an activity is "
             f"critical ONCE DURATIONS VARY, so with no variation stated there is nothing to "
             f"simulate and NO READING IS TAKEN. A single deterministic pass is not a "
             f"criticality index and is not reported as one. Critical Path Analysis reports the "
             f"deterministic controlling path on this same network."),
            ABSTAIN_MISSING_INPUT,
            activities_without_three_point_durations=_no_uncertainty,
            schedule_network_diagnostics=_diag_fields,
            canonical_structure="schedule_network")
    try:
        reading = pert_criticality(network, rand, trials=2000)
    except StructureAbsent as absent:
        return insufficient("PERT_Network_Criticality", absent.sentence,
                            ABSTAIN_STRUCTURE_ABSENT,
                            schedule_network_diagnostics=_diag_fields)
    index = reading["criticality_index"]
    top = max(index, key=lambda a: (index[a], a))
    # ================== RUN 102, SECTION 3. THE BAND ON THE CRITICALITY INDEX, AND ITS OVERRIDE.
    # RUN 101 ORDERED THIS MODULE LEFT BANDLESS AND THE OWNER HAS REVERSED THAT (Run 102,
    # section 0.1). The measure matches the owner's definition exactly: criticality index = runs
    # in which the activity or path is critical / total simulation runs, which is what
    # `canonical_v3.pert_criticality` computes and has computed since Run 28. The direction is
    # ADVERSE UPWARD -- an activity critical in more runs is more of a threat -- so the
    # boundaries are inclusive on their LOWER side and Red is the open top.
    #
    # THE HARD OVERRIDE, AND WHY IT IS NOT FIRED FROM CPM FLOAT ALONE. The owner's condition is
    # "zero or negative total float on the controlling path", and his stated rationale is that
    # "zero total float defines a critical condition, while negative float indicates the current
    # schedule cannot meet its IMPOSED COMPLETION CONDITION". In a network with NO imposed
    # completion date the critical path's total float is ZERO BY CONSTRUCTION -- that is what the
    # backward pass does -- so firing the override from it would take EVERY project to Red and
    # would be measuring the arithmetic rather than the schedule. The override is therefore
    # evaluated against the IMPOSED FINISH the network states, and where the network states none
    # the override is NOT EVALUABLE and the row says so rather than firing or silently passing.
    _cuts = _BR.entry("pert_criticality_bands")
    _share = index[top]
    _imposed = structure.get("imposed_finish_day")
    _finish = reading.get("project_finish")
    if _finish is None:
        _finish = cpm_forward_backward(network)["project_finish"]
    _controlling_float = (float(_imposed) - float(_finish)
                          if isinstance(_imposed, (int, float)) else None)
    _override_words = (
        "HARD OVERRIDE: Red if the current deterministic schedule has zero or negative total "
        "float on the controlling path. Zero total float defines a critical condition; negative "
        "float means the current schedule cannot meet its imposed completion condition. It is "
        "evaluated against the IMPOSED completion date the network states, never against the "
        "backward pass alone, whose float on the critical path is zero by construction when no "
        "date is imposed.")
    _fields = dict(
        criticality_index={a: round(index[a], 4) for a in sorted(index)},
        most_critical_activity=top,
        most_critical_share=round(_share, 4),
        trials=reading["trials"],
        deterministic=reading["deterministic"],
        project_finish_p80=reading.get("project_finish_p80"),
        activity_moments={a: v for a, v in sorted(reading["activity_moments"].items())},
        schedule_version=network["schedule_version"],
        canonical_structure="schedule_network",
        imposed_finish_day=_imposed,
        controlling_path_total_float=_controlling_float,
        controlling_path_float_override_evaluable=_controlling_float is not None,
    )
    _message = (
        f"Over {reading['trials']} simulated runs of the network, {top} lies on the critical "
        f"path in {int(js_round(_share * 100))} per cent of them, the most of any activity")
    if not _cuts.get("configured"):
        return band_abstained(
            "PERT_Network_Criticality", _message,
            reason="no criticality band is configured, so the index is displayed and no band "
                   "is asserted",
            **_fields)
    _g, _y, _a = _cuts["green_below"], _cuts["yellow_below"], _cuts["amber_below"]
    if _controlling_float is not None and _controlling_float <= 0:
        _colour = "Red"
    else:
        _colour = ("Green" if _share < _g else "Yellow" if _share < _y
                   else "Amber" if _share < _a else "Red")
    _boundary = (
        f"on the criticality index -- runs in which the activity or path is critical divided by "
        f"total simulation runs: below {_g} is Green; at or above {_g} and below {_y} is "
        f"Yellow; at or above {_y} and below {_a} is Amber; at or above {_a} is Red. Each "
        f"boundary is INCLUSIVE ON ITS LOWER SIDE and the direction is adverse upward. "
        + _override_words
        + (f" This network states an imposed finish, and the controlling path's total float "
           f"against it is {_controlling_float}."
           if _controlling_float is not None else
           " This network states NO imposed completion date, so the override is not evaluable "
           "on it and was not applied; the band above rests on the criticality index alone."))
    return banded(
        "PERT_Network_Criticality", _message,
        status_color=_colour,
        boundary=_boundary,
        basis=("the owner's Run 102 order, section 3, and the threshold table attached to it. "
               "OWNER-CONFIGURED: the criticality index itself is a standard PERT/Monte Carlo "
               "quantity, but no published standard fixes where 0.20, 0.50 and 0.80 divide the "
               "bands. They are a documented owner tolerance and are not presented as a "
               "construction standard. A stricter figure stated in a project document overrides "
               "them, and none is stated by any document this project has uploaded"),
        provenance=PROVENANCE_OWNER_CALIBRATED,
        threshold_source=THRESHOLD_SOURCE_OWNER,
        band_hard_override_fired=bool(_controlling_float is not None
                                      and _controlling_float <= 0),
        **_fields)


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
    "A1.2": ("CUSUM", run_cusum_module),
    "A2.1": ("PERT_Network_Criticality", run_pert),
}


def _register_extensions() -> None:
    # Imported late: models_ext imports helpers from this module.
    from .models_doc import A4_EXTENSIONS, A5_EXTENSIONS, A6_EXTENSIONS
    from .models_decision import DECISION_EXTENSIONS
    from .models_dq import DQ_EXTENSIONS
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
    VALIDATED.update(FUZZY_EXTENSIONS)
    VALIDATED.update(DQ_EXTENSIONS)
    VALIDATED.update(DECISION_EXTENSIONS)
    # RUN 30 CLOSURE, v16. THE TWENTY CATEGORY-7 IDENTITIES ARE REPOINTED, LAST, so this line is
    # the one that decides which implementation production runs and a reader can see it decide.
    # RUN 97. `models_evc.py` is DELETED. It served B2.2 through B2.9, Evidence Combination,
    # whose rows Run 96 removed -- `EVC_EXTENSIONS` had been an empty dict since -- and Run 97's
    # addendum removes B2 entirely. It was kept only because eight suites called its functions
    # directly, which the addendum names as not a reason.
    # `FUZZY_EXTENSIONS` is still imported and still updated above, because
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
    # RUN 32, v20. THE SEVEN CATEGORY-10 IDENTITIES ARE REPOINTED, LAST, by the same pattern and
    # for the same reason: whatever registers last decides what production executes, and a reader
    # can see it decide here. `DECISION_EXTENSIONS` is still imported and still updated above --
    # it carries modules outside Run 32's scope -- and every B4.x key it sets is overwritten here
    # by the thin canonical route in `models_cat10.py`. The legacy Category-10 functions remain
    # in the tree as the historical record of the v19 line and are reachable from no production
    # route; `test_run32_operational_route.py` proves that count is zero by profiling the
    # interpreter through `registry.run_module` rather than by reading this file.
    #
    # WHAT THIS LINE RETIRES. At v19 B4.1 blended cpi, spi and a document risk score and called
    # the result multi-objective optimization; B4.2 returned a fixed rule score for a linear
    # program with no variables; B4.6 reported threshold booleans over a single project as a
    # Pareto frontier. After this line none of them is reachable, and the seven measures abstain
    # until a governed decision problem is supplied rather than reporting a proxy.
    from .models_cat10 import CAT10_CANONICAL
    VALIDATED.update(CAT10_CANONICAL)
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
