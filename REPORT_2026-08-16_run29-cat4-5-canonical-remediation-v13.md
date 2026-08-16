# Run 29: the supplied Category 4 and 5 canonical contracts, implemented in sim-2026.08-v13

Date: 2026-08-16. Starting commit `01e943e`. First commit carrying v13: `0a4e862`.
Final head `5f8c409`. Freeze `OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-16-RUN29-CANONICAL-CAT4-5-V13-1`.

This file is the report named by the run instruction. Its text is identical to the copy held in
`T6_HANDOFF.md`, which was written first because the authoring session could not create this path.

**Scope authority:** the owner's supplied Run-29 supervisory method contract. The scientific
theory is SUPPLIED by that contract. This run implemented it; it did not review it, did not infer
theory from production, and did not substitute a weaker method because one resembled existing
code. Where production disagreed with a supplied contract, production was corrected.

## 1. v12 preservation proof

`sim-2026.08-v12` is preserved and is still executable.

- `SIMULATION_VERSION_HISTORY` in `server/app/simulation/models.py` is append-only and now reads
  `sim-2026.07-v1 ... sim-2026.08-v11, sim-2026.08-v12, sim-2026.08-v13`. No stamp was edited,
  removed or re-used.
- `server/tools/test_run29_version_boundary.py` reads the history OUT OF GIT OBJECT 01e943e and
  asserts that the tuple as it stood there is a strict PREFIX of the tuple now, and that the stamps
  added since are exactly `("sim-2026.08-v13",)`.
- `server/tools/test_run28_version_boundary.py` continues to make the same assertion against the
  v11 commit `0e0dfbd`, and continues to extract the v11 canonical layer, execute it, and observe
  the v11-to-v12 divergence. Run 29 did not weaken it: the one check that pinned growth at exactly
  one stamp was restated as monotone growth PLUS an exact statement of which stamps were added
  (v12 then v13), which is stronger, not looser.
- `server/tools/test_run7_fix_now_defects.py` still reconstructs and EXECUTES the whole
  `sim-2026.08-v2` analytical package from git object `021d5e2`.

## 2. v13 identity, and the boundary proved by execution

**`sim-2026.08-v13`**, superseding `sim-2026.08-v12`. First commit carrying it: the Run-29
implementation commit recorded in the final-head section below.

The bump is not argued. `server/tools/test_run29_version_boundary.py` extracts the v12 analytical
package from GIT OBJECT `01e943e`, imports it, and runs it beside the current one on identical
governed inputs. Four divergences, all observed:

| input (identical to both lines) | sim-2026.08-v12, executed | sim-2026.08-v13 |
|---|---|---|
| a governed queue model, lambda = 2, mu = 3, one server | ABSTAINS (it required a queue OBSERVATION log) | rho = 2/3, L = 2, W = 1, Lq = 4/3, Wq = 2/3 |
| the same queue with lambda = 3 | -- | REFUSES: no steady state, no finite wait offered |
| docRiskScore 0.5, rfiCount 10, changeOrderCount 5 | emits escalation_index = 0.5 | REFUSES: none of the three is dispute evidence |
| a governed dependency matrix D = [[0, 0.5], [0, 0]], R0 = [0, 1] | ABSTAINS unconditionally | R1 = [0.5, 0] |

Plus: the governed intake could not reach a single Category-4 or -5 structure at the v12 commit
(`canonical_v4` did not exist) and reaches all seventeen now, so five modules that could only ever
abstain can compute.

A module that could only abstain and can now compute is a change in executable analytical
behaviour. So is a module that emitted a number and now refuses. Both are present.

## 3. The exact eighteen-target population, mechanically reconciled

Derived from `code_audit/run27_98_module_remediation_matrix.csv` by filtering `category in {A4,
A5}`, not transcribed:

- A4 "Document-Derived Condition Signals" = **10 rows**
- A5 "System Dynamics & Complexity" = **8 rows**
- Total = **18**, exactly the expected scope. No row was added, dropped or substituted.

Recorded per target in `code_audit/run29_cat4_5_scope.csv` with identity, name, Run-27 disposition,
DATA/METHOD/CAL/LINEAGE/VALIDATE requirement flags, current evidence before Run 29, missing
evidence, the Run-29 objective, the governed structure key, and the remaining Run-31/33 work.

Category 8's Quality / Safety / Environmental orphan-field package was NOT touched; it is Run 31's,
per the contract's section 2.

## 4. Category-4 evidence structures supplied

All in `server/app/simulation/canonical_v4.py`, all reachable through the governed intake.

| structure key | serves | required fields the contract names, enforced |
|---|---|---|
| `documentRiskEvidence` | A4.1 | document id, type, evidence span, risk class, candidate, severity, confidence, coverage, effective date, classifier version, taxonomy, aggregation rule, provenance |
| `rfiEventLog` | A4.2 | RFI identity, created/response/close dates, status, topic, responsible party, reporting period, source register, exposure |
| `submittalDecisionRegister` | A4.3 | submittal id, revision id, governed disposition, decision date, reviewer, taxonomy version, source |
| `ncrExposureRecord` | A4.4 | NCR id, issue/close date, reopened, severity, exposure unit and quantity, reporting period |
| `weatherImpactEvents` | A4.5 | event, date, affected activity, planned work, actual lost time, weather allowance/calendar, schedule path, available float, causal evidence, mitigation |
| `changeEventRegister` | A4.6 | change id, issue date, type, cause, value, additive/deductive, contract baseline, exposure, provenance |
| `claimDisputeRegister` | A4.7 | issue id, the project's OWN governed process and version, stage and rank, stage/raised dates, notice, claim value, evidence source |
| `subcontractorAssessments` | A4.8 | subcontractor id, period, per-criterion ratings, evaluator, rating provenance, versioned weights, critical violation |
| `procurementItems` | A4.9 | item id, required-on-site date, forecast delivery, order date, status, criticality, activity, float, forecast uncertainty |
| `specificationConflictRegister` | A4.10 | conflict id, specification document and revision, two evidence locations, confirmed/candidate, reviewer, exposure unit and quantity, discipline, cross-reference |

## 5. Category-5 model structures supplied

| structure key | serves | required elements |
|---|---|---|
| `dsmDependencyModel` | A5.1 | nodes, directed edges, DECLARED matrix orientation, strengths, seed rework vector, stopping rule, model version |
| `sensitivityModel` | **A5.2 and A5.3** | named/versioned response model, base state, selected inputs, low/high, perturbation, units, declared local method |
| `scenarioSet` | A5.4 | scenario id/name/version/rationale, jointly changed variables, consistency constraints, governed response model |
| `systemDynamicsModel` | A5.5 | time step, initial stock, per-step new work, work completed, error rate, model version |
| `queueModel` | A5.6 | queue id, arrival rate, service rate, servers, discipline, model version |
| `agentSupplyChainModel` | A5.7 | agents with type/state/behaviour rule/interaction links, environment, time steps, travel delay, disruption probability, seed, replications |
| `desProcessModel` | A5.8 | entities with arrival and service (or a seeded distribution), resources with capacity, queue discipline, event-ordering policy, termination condition, seed, replications |

Eighteen module-to-key entries over SEVENTEEN distinct keys: one sensitivity model serves both
A5.2 and A5.3, and that sharing IS the parsimony decision.

## 6. Modules now executing canonical methods

Sixteen modules stopped computing a proxy: A4.4, A4.5, A4.6, A4.7, A4.8, A4.9, A4.10, A5.1, A5.2,
A5.3, A5.4, A5.5, A5.6, A5.7, A5.8, and A4.1's score derivation. A4.2 and A4.3 were Run-27 method
passes and already computed the contract's formula; each gained the governed event/decision
register as its preferred source and kept its extracted-totals path, which is the SAME canonical
quantity from a thinner record.

## 7. Modules correctly abstaining on the real corpus

On the real corpus ALL FIFTEEN structure-required Category-4 and -5 targets abstain, because no
project has yet supplied a governed structure through the intake. That is the honest outcome and is
asserted mechanically (`test_run29_canonical_oracles.py`: on a fully reported project carrying
every scalar the old computations read, fifteen of the seventeen runnable targets abstain). A4.2
and A4.3 continue to compute from extracted register totals.

`test_run2_fifteen_defects.py` records the concrete consequence on the real ingested corpus: A4.9
now abstains where it used to render a ratio, because the corpus carries long-lead COUNTS and the
canonical method needs per-item DATES.

## 8. Remaining CAL / VALIDATE / LINEAGE work

- **CAL (Run 33).** No status band was introduced for any Category-4 or -5 quantity. Sixteen of
  the eighteen assert NO COLOUR and carry `calibration_pending`. A4.2 and A4.3 keep the ladders
  they always carried, which `registry.py` already records as uncited.
- **VALIDATE (Run 33).** A4.1 extraction precision/recall and A4.10 conflict-detection
  precision/recall are `PENDING_RUN_33`, carried on the results themselves. No labelled corpus
  exists here and none was invented. A5.7's supplier behaviour calibration is likewise pending.
- **LINEAGE (Run 31).** The Category-9 qualification gate remains UNIMPLEMENTED and production
  discloses it (`signal_package.py`: `SIGNAL_QUALIFICATION = "unqualified"`,
  `CATEGORY_9_DEVIATION`). Run 29 closed NO LINEAGE finding; it kept the provenance that gate will
  need true.

## Per-module record

Format per the contract: SUPPLIED CONTRACT, v12 BEHAVIOUR, v13 DATA/MODEL SUPPLY, v13
IMPLEMENTATION, ORACLE RESULT, ABSTENTION RESULT, REMAINING WORK.

### A4.1 Document Risk Score
- SUPPLIED CONTRACT: no universal scalar score; requires governed taxonomy, document type,
  evidence span, candidate, severity, confidence, coverage, recency, transparent aggregation,
  model/rule version, provenance. Keep extraction accuracy, aggregation arithmetic and banding
  apart. No source text or provenance means ABSTAIN.
- v12 BEHAVIOUR: an opaque per-document scalar from the extraction pipeline, with none of those,
  feeding about twenty-eight downstream modules.
- v13 DATA/MODEL SUPPLY: `documentRiskEvidence` through the governed intake.
- v13 IMPLEMENTATION: `canonical_v4.document_risk_evidence` aggregates by a NAMED rule and refuses
  without provenance; `documents.py` re-derives `docRiskScore` from it where a project supplies it
  and records `docRiskScoreDerivation` on the row. Where no such evidence exists the extraction
  scalar is left exactly as it was: no provenance is fabricated.
- ORACLE RESULT: two findings, severity 0.8 at confidence 1.0 and 0.4 at 0.5, under the
  confidence-weighted rule: (0.8*1.0 + 0.4*0.5)/(1.0 + 0.5) = 0.6667. PASS.
- ABSTENTION RESULT: refuses evidence with no span, no classifier version, no taxonomy, no source,
  no coverage, or a severity outside nought to one. PASS.
- REMAINING: EMPIRICAL VALIDATION PENDING RUN 33. The module remains registry-excluded
  (unchanged); no rename.

### A4.2 RFI Velocity
- SUPPLIED CONTRACT: count / exposure time; 12 over 30 days = 0.4/day or 12 per standardised
  30-day period; OverdueRatio = overdue / relevant open; revisions of a cumulative register are not
  new events; no bands supplied.
- v12 BEHAVIOUR: the same formula on extracted totals, which Run 27 recorded as a method pass. It
  could not de-duplicate, because totals carry no identities.
- v13 DATA/MODEL SUPPLY: `rfiEventLog`.
- v13 IMPLEMENTATION: events de-duplicated BY REQUEST IDENTITY; a register carrying the same
  request twice with different dates is refused rather than silently collapsed; overdue share
  computed over relevant open only.
- ORACLE RESULT: 0.4/day and 12 per 30 days. PASS. Uploading the same register twice still reads
  0.4/day and reports twelve collapsed rows; twenty-four DISTINCT identities read 0.8/day. PASS.
- ABSTENTION RESULT: no exposure span refuses; neither register nor totals is NOT ESTIMABLE.
- REMAINING: the per-week and overdue ladders remain uncited (Run 33).

### A4.3 Submittal Rejection Rate
- SUPPLIED CONTRACT: Rejected / AssessedPopulation; 3 of 20 = 0.15; 0 <= Rejected <= Assessed;
  governed disposition taxonomy, no silent merging; a denominator mixing this period's decisions
  with a cumulative backlog is invalid.
- v12 BEHAVIOUR: the same share on extracted totals (a Run-27 method pass), with no disposition
  taxonomy and no period filter.
- v13 DATA/MODEL SUPPLY: `submittalDecisionRegister`.
- v13 IMPLEMENTATION: governed dispositions (APPROVED, APPROVED_AS_NOTED, REVISE_AND_RESUBMIT,
  REJECTED, FOR_RECORD, WITHDRAWN); a project maps its own statuses and an unmapped status is
  REFUSED; the period filter excludes other periods from BOTH sides; unique submittals separated
  from resubmission cycles; a decision declared twice at the same submittal-and-revision identity
  is refused.
- ORACLE RESULT: 0.15. PASS.
- ABSTENTION RESULT: rejected greater than assessed on the totals path refuses; nothing assessed in
  the period refuses.
- REMAINING: the rejection-share ladder remains uncited (Run 33).

### A4.4 NCR Rate
- SUPPLIED CONTRACT: NCR events / governed exposure; 4 / 100 inspections = 0.04; open count, age,
  severity and closure tracked SEPARATELY; no exposure means do not fabricate a rate.
- v12 BEHAVIOUR: open backlog over an audited findings cohort: a stock over the size of one audit,
  which is a ratio of two different populations.
- v13 DATA/MODEL SUPPLY: `ncrExposureRecord`.
- v13 IMPLEMENTATION: rate over a NAMED exposure unit and quantity; open/closed/reopened counts,
  closure rate, mean and max open age and severity mix reported beside it, never divided into it.
- ORACLE RESULT: 0.04. PASS. Doubling exposure halves the rate. PASS.
- ABSTENTION RESULT: exposure nought refuses; the audited cohort alone refuses; an NCR closed
  before it was raised refuses.
- REMAINING: no band; CAL Run 33.

### A4.5 Weather Day Impact
- SUPPLIED CONTRACT: weather occurrence is not schedule impact; requires event, activity, planned
  work, lost time, allowance/calendar, path/float, causal evidence, modelled consequence; 2 lost
  days on a zero-float critical activity with no mitigation = 2 DAYS before recovery; no schedule
  linkage means NOT ESTIMABLE; do not rename to preserve the proxy.
- v12 BEHAVIOUR: lost days over a float figure, banded.
- v13 DATA/MODEL SUPPLY: `weatherImpactEvents`.
- v13 IMPLEMENTATION: per event, lost days are absorbed first by the remaining weather allowance,
  then by the path's float; what survives both is the direct path effect. Mitigation is reported
  separately and NOT netted off, because the contract asks for the effect before recovery.
- ORACLE RESULT: 2.0 days. PASS. Five days of float on the same path gives 0.0. PASS. A two-day
  allowance gives 0.0. PASS.
- ABSTENTION RESULT: an event with no activity, path or causal evidence refuses; a lost-day count
  with a float figure is NOT ESTIMABLE.
- REMAINING: no band; CAL Run 33.

### A4.6 Change Order Frequency
- SUPPLIED CONTRACT: events / exposure; 6 over 180 days = 0.03333.../day or 1 per 30-day period;
  magnitude = SumChangeValue / BaselineContractValue, SEPARATE; do not combine into one unnamed
  composite; preserve type, cause, direction and contract lineage.
- v12 BEHAVIOUR: precisely that unnamed composite: a joint ladder over a raw count and the
  percentage contract growth.
- v13 DATA/MODEL SUPPLY: `changeEventRegister`.
- v13 IMPLEMENTATION: frequency per day and per standardised 30 days; magnitude net and gross under
  their own names; type, cause and additive/deductive counts preserved; baseline and revised
  contract value both carried. NO COLOUR IS ASSERTED OVER EITHER, which is how the composite is
  prevented rather than merely deprecated.
- ORACLE RESULT: 6/180 = 0.0333..., 1.0 per 30 days, magnitude 0.06. PASS.
- ABSTENTION RESULT: exposure nought refuses; a change with no declared direction refuses; the
  extracted contract sums alone are NOT ESTIMABLE.
- REMAINING: no bands; CAL Run 33.

### A4.7 Dispute Escalation Index
- SUPPLIED CONTRACT: the project's own governed dispute process; a later governed state cannot look
  less escalated; missing dispute evidence cannot improve the condition; RFI count, change count
  and document risk do NOT prove a dispute; no evidence means NOT ESTIMABLE; do not preserve the
  0.3/0.3/0.4 composite. The S0 to S5 ladder is a TEST FIXTURE, not a production taxonomy.
- v12 BEHAVIOUR: exactly the 0.3/0.3/0.4 composite over a capped request count, a capped change
  count and the document risk score.
- v13 DATA/MODEL SUPPLY: `claimDisputeRegister`, carrying the project's OWN process and its
  version. The S0 to S5 ladder lives only in `server/tools/run29_fixtures.py`.
- v13 IMPLEMENTATION: stage ranks read from the declared process; the reading is the rank of the
  highest stage reached, monotone in the declared order by construction; duplicate stage ids or
  duplicate ranks refused; issues, claim value and unresolved age carried.
- ORACLE RESULT: a submitted claim reads S1_CLAIM_SUBMITTED, rank 1 of 6; swept over all six stages
  the ranks are [0,1,2,3,4,5], so a later state never reads calmer. PASS.
- ABSTENTION RESULT: across TWENTY-SEVEN combinations of the three generic KPI fields, no stage is
  ever produced. PASS. No register means NOT ESTIMABLE.
- REMAINING: no stage-to-health band; CAL Run 33.

### A4.8 Subcontractor Performance
- SUPPLIED CONTRACT: Score = sum(w_i * r_i) with sum(w_i) = 1; 0.80/0.90/0.70 equally weighted =
  0.80; weights versioned and provenanced; a critical violation may stay separately visible; do not
  validate by consuming an opaque precomputed compliance score.
- v12 BEHAVIOUR: exactly that opaque score, banded.
- v13 DATA/MODEL SUPPLY: `subcontractorAssessments`.
- v13 IMPLEMENTATION: per-firm criterion ratings, evaluator, period, rating provenance; weights must
  sum to one; a firm not rated against exactly the declared criteria is refused; critical violations
  listed separately so a noncompensatory policy can be applied later.
- ORACLE RESULT: 0.80. PASS.
- ABSTENTION RESULT: the opaque scalar refuses; weights not summing to one refuse; a blank weights
  version refuses.
- REMAINING: no band; the weights themselves are declared, not empirically sourced (Run 33).

### A4.9 Procurement Lead Time Monitor
- SUPPLIED CONTRACT: slack = RequiredOnSiteDate - ForecastDeliveryDate; 100 against 110 = -10 DAYS;
  do not double-count delayed inside at-risk; a count ratio alone is not the canonical monitor.
- v12 BEHAVIOUR: a weighted count ratio over the long-lead set, with no dates in it.
- v13 DATA/MODEL SUPPLY: `procurementItems`.
- v13 IMPLEMENTATION: per-item slack; each item in exactly ONE state (LATE, AT_RISK, ON_TIME)
  decided by its own slack against its own float, so the states partition the register and nothing
  can be counted twice; criticality, status, activity, float and forecast uncertainty carried.
- ORACLE RESULT: -10 days. PASS. Translating both dates by any amount leaves it at -10 (24 shifts).
  PASS.
- ABSTENTION RESULT: the long-lead counts alone are NOT ESTIMABLE; a duplicated item id refuses;
  negative float refuses.
- REMAINING: no band; CAL Run 33.

### A4.10 Specification Conflict Density
- SUPPLIED CONTRACT: VerifiedConflicts / ExposureUnit; 5 over 250 requirements = 0.02, or 20 per
  1,000; exposure explicit; each conflict retains its evidence locations; docRiskScore * sqrt(RFI
  count) is NOT conflict density; no numerator or denominator means NOT ESTIMABLE.
- v12 BEHAVIOUR: precisely docRiskScore * rfiCount / sqrt(rfiCount), capped at one and banded.
- v13 DATA/MODEL SUPPLY: `specificationConflictRegister`.
- v13 IMPLEMENTATION: confirmed conflicts over a declared exposure; candidates counted separately
  and excluded from the density; a conflict citing the same location twice is refused, because that
  records no disagreement between two places.
- ORACLE RESULT: 0.02 and 20 per 1,000. PASS. Doubling exposure HALVES the density, the correct
  direction; the v12 quantity ROSE with volume. PASS.
- ABSTENTION RESULT: exposure nought is NOT ESTIMABLE; a document risk score with a request count is
  NOT ESTIMABLE.
- REMAINING: detection precision/recall PENDING_RUN_33; no band.

### A5.1 DSM Rework Propagation
- SUPPLIED CONTRACT: named nodes, directed matrix D, declared orientation, edge strengths, seed
  rework vector, stopping rule; R(k+1) = D * R(k); with D = [[0,0.5],[0,0]] and R0 = [0,1],
  R1 = [0.5,0] and R2 = [0,0]; no DSM means NOT ESTIMABLE; CPI/SPI may not substitute for topology.
- v12 BEHAVIOUR: abstained UNCONDITIONALLY: no input of any kind could make it eligible.
- v13 DATA/MODEL SUPPLY: `dsmDependencyModel`.
- v13 IMPLEMENTATION: matrix assembled under the DECLARED orientation (ROW_RECEIVES_FROM_COLUMN or
  ROW_FEEDS_COLUMN); propagation iterated under the declared stopping rule with a convergence
  tolerance; per-wave and total propagated rework reported.
- ORACLE RESULT: R1 = {n1: 0.5, n2: 0}, R2 = {n1: 0, n2: 0}. PASS. Linear in the seed; monotone in
  edge strength; a zero matrix propagates nothing; a cycle stops at the declared limit. PASS.
- ABSTENTION RESULT: no matrix is NOT ESTIMABLE, unchanged; no orientation refuses; an edge to an
  undeclared node refuses; no stopping rule refuses.
- REMAINING: no band; CAL Run 33.

### A5.2 Sensitivity Analysis
- SUPPLIED CONTRACT: explicit response Y, input Xi, base point, perturbation;
  S_i = (dY/Y)/(dXi/Xi); Y = x1^2 + x2 at (2,1) gives 5, +10 per cent on x1 gives 5.84, dY = 0.84,
  S = 1.68; ranking currently-bad variables is not sensitivity; local one-at-a-time acceptable IF
  DECLARED AS SUCH and not called global.
- v12 BEHAVIOUR: one hard-coded elasticity of bac/cpi perturbed by plus and minus 0.05, with two
  unperturbed LEVELS reported beside it. No declared response, base state, range or input set.
- v13 DATA/MODEL SUPPLY: `sensitivityModel`, carrying a named and versioned POLYNOMIAL RESPONSE
  SURFACE (a term list), a base state and the inputs to move. The response model is DATA, so no
  laboratory function is hard-coded into production.
- v13 IMPLEMENTATION: the response is evaluated at the base state and RECOMPUTED at each moved
  input; low and high responses computed for the tornado; method_scope = "LOCAL".
- ORACLE RESULT: base 5.0, moved 5.84, dY 0.84, S = 1.68. PASS. Confirmed independently by
  `oracles_cat_5.normalised_sensitivity`. PASS.
- ABSTENTION RESULT: a perturbation of zero refuses; an input absent from the base state refuses; a
  term-less model refuses; the earned-value scalars are NOT ESTIMABLE.
- REMAINING: no band; CAL Run 33.

### A5.3 Tornado Risk Ranking
- SUPPLIED CONTRACT: Impact_i = Y_i(high) - Y_i(low), ranked by absolute impact; 30 / 7 / 30 puts A
  and C TIED ABOVE B; tie policy explicit; CONSUMES 5.2's OUTPUTS; DOES NOT CREATE A SECOND
  INDEPENDENT EVIDENCE BODY; lineage must show derivation from the sensitivity results.
- v12 BEHAVIOUR: ranked four present-state deviations and banded their mean; nothing was evaluated
  at any range and none of it came from A5.2.
- v13 DATA/MODEL SUPPLY: the SAME `sensitivityModel` key A5.2 reads.
- v13 IMPLEMENTATION: the runner calls `sensitivity_analysis`, then hands the RESULT DICTIONARY to
  `tornado_ranking`, whose signature takes nothing else. It cannot reach the structure, the response
  model or the signal inputs, so it is structurally incapable of forming an independent body. Tie
  policy: EQUAL_ABSOLUTE_IMPACT_SHARES_A_RANK_ORDERED_BY_INPUT_ID.
- ORACLE RESULT: A = 30, B = 7, C = 30; order ["A","C","B"] with A and C sharing rank 1. PASS.
- ABSTENTION RESULT: no sensitivity model is NOT ESTIMABLE; a sensitivity that moved no inputs
  leaves nothing to present.
- REMAINING: no band; CAL Run 33.

### A5.4 Scenario Modeling
- SUPPLIED CONTRACT: X(s) = {x1(s)...xp(s)}, Y(s) = f(X(s)); scenario id/version, rationale, jointly
  changed inputs, consistency constraints, governed response model; Y = 2*x1 + x2 gives BASE 5,
  ADVERSE 8, RECOVERY 4; NOT CATEGORY 10: the question is what happens under a condition, not which
  intervention to choose.
- v12 BEHAVIOUR: read an actions-by-scenarios payoff and returned a RECOMMENDED ACTION and its
  expected cost. That is Category 10's question. PRODUCTION DISAGREED WITH THE SUPPLIED CONTRACT,
  SO PRODUCTION WAS CORRECTED.
- v13 DATA/MODEL SUPPLY: `scenarioSet`.
- v13 IMPLEMENTATION: every scenario must set a value for every variable the response model reads (a
  partial state is not a coherent state) and must satisfy the declared consistency constraints;
  responses evaluated through ONE governed model; nothing is recommended.
- ORACLE RESULT: {BASE: 5.0, ADVERSE: 8.0, RECOVERY: 4.0}. PASS. `recommended_action` is absent.
  PASS.
- ABSTENTION RESULT: an inconsistent state refuses; a partial state refuses; the decision object is
  NOT ESTIMABLE.
- REMAINING: no band (Run 33). OWNER DECISION SURFACED, NOT TAKEN: whether the retired
  actions-by-scenarios path should be re-registered under Category 10. Its guards remain in
  `canonical.py` and are still exercised through B2.19; the coverage reduction is recorded in
  `test_run10b_canonical_integration.py` rather than glossed.

### A5.5 Rework Feedback Loop
- SUPPLIED CONTRACT: Backlog(t+1) = Backlog(t) + NewWork(t) + ReworkGenerated(t) - WorkCompleted(t);
  ReworkGenerated(t) = ErrorRate(t) * WorkCompleted(t); 10 + 5 + 2 - 8 = 9 with rework 2; a weighted
  CPI/RFI/CO score is not a feedback loop; no stock/flow model means NOT ESTIMABLE.
- v12 BEHAVIOUR: exactly that weighted score.
- v13 DATA/MODEL SUPPLY: `systemDynamicsModel`.
- v13 IMPLEMENTATION: stepped through time with a declared time step; a step completing more work
  than the backlog held is refused; the ACCOUNTING RESIDUAL is computed and reported, and a run that
  does not conserve is refused.
- ORACLE RESULT: rework 2.0, backlog 9.0, residual 0. PASS. Equilibrium at new 6 / completed 8 /
  error 0.25 holds flat over five steps; error 0.60 amplifies. PASS.
- ABSTENTION RESULT: the three v12 fields are NOT ESTIMABLE; an error rate outside nought to one
  refuses.
- REMAINING: no band; CAL Run 33.

### A5.6 Queueing Theory Bottleneck
- SUPPLIED CONTRACT: arrival rate lambda, service rate mu, servers, discipline, stability;
  rho = lambda/mu, L = rho/(1-rho), W = 1/(mu-lambda), Lq = rho^2/(1-rho), Wq = rho/(mu-lambda);
  lambda = 2, mu = 3 gives rho = 2/3, L = 2, W = 1, Lq = 4/3, Wq = 2/3; Little's Law must hold; IF
  LAMBDA >= MU DO NOT EMIT A REASSURING STEADY STATE; ActivitiesConstrained/ActivitiesPlanned is not
  queueing theory.
- v12 BEHAVIOUR: a measured occupancy from an observation log (server time used over server time
  available) with waits READ OUT OF THE LOG; an unstable queue was banded Red.
- v13 DATA/MODEL SUPPLY: `queueModel`.
- v13 IMPLEMENTATION: M/M/c via Erlang C (reducing exactly to M/M/1 at c = 1); rho, L, W, Lq, Wq and
  P0 derived; both forms of Little's Law reported; an unknown discipline refused; RHO >= 1 RAISES,
  so the caller abstains and no finite wait is offered.
- ORACLE RESULT: rho = 2/3, L = 2, W = 1, Lq = 4/3, Wq = 2/3; L = lambda*W = 2 and
  Lq = lambda*Wq = 4/3. PASS. Confirmed independently by `oracles_cat_5.mm1`. PASS.
- ABSTENTION RESULT: lambda = mu and lambda > mu both refuse and report NO L or W; lambda = 2.999
  still computes, so the boundary is not a blanket refusal. PASS. Look-ahead counts are NOT
  ESTIMABLE.
- REMAINING: no band; CAL Run 33.

### A5.7 Agent-Based Supply Chain
- SUPPLIED CONTRACT: agents + states + behaviour rules + interaction rules + environment + time; the
  minimum deterministic model of supplier / carrier / project; hand-compute every state transition;
  a long-lead at-risk ratio is not ABM; no agent or rule structure means NOT ESTIMABLE; synthetic
  behaviour verifies implementation, not real supplier behaviour.
- v12 BEHAVIOUR: read a supplied state history and counted non-NORMAL agents at the last step. Rules
  were NAMED BUT NEVER EXECUTED: a table read, not a simulation.
- v13 DATA/MODEL SUPPLY: `agentSupplyChainModel`.
- v13 IMPLEMENTATION: a stepped simulation with a DECLARED STEP ORDER
  POST_DEMAND, DELIVER, COLLECT, SHIP, published on the result so any trace is hand-checkable.
  Exactly one supplier, one carrier and one project; links must resolve; rules must be ones the
  platform implements.
- ORACLE RESULT: stock 2, delay 1, demand 2: supplier inventory [1,0,0,0,0,0], receipts
  [0,0,1,2,2,2], received 2, backordered 0. Every transition matches the hand trace. PASS. Zero
  stock gives received 0, backordered 2. PASS. Delay 2 moves the receipts later. PASS.
- ABSTENTION RESULT: no agents refuses; blank behaviour rules refuse; one time step refuses; a link
  to an agent the model lacks refuses; procurement counts are NOT ESTIMABLE.
- REMAINING: empirical_calibration = PENDING_RUN_33; no band.

### A5.8 Discrete Event Simulation
- SUPPLIED CONTRACT: entities, events, clock, resources, queues, routing, durations, ordering
  policy, termination, seed/distributions when stochastic; one server, A at 0 for 2 and B at 1 for
  2 gives A 0/2/0, B 2/4/1, MEAN WAIT 0.5; a progress/SPI index is not DES; no event/resource/queue
  structure means NOT ESTIMABLE.
- v12 BEHAVIOUR: the reciprocal of an interruption term built from the progress shortfall and the
  schedule-index shortfall. Run 27 proved it a function of the schedule index and the progress ratio
  alone.
- v13 DATA/MODEL SUPPLY: `desProcessModel`.
- v13 IMPLEMENTATION: a real event-driven loop: an event list, a clock advanced to the next event, a
  queue, a resource with capacity that is RELEASED on departure, FIFO or PRIORITY routing, and a
  declared simultaneous-event policy (DEPARTURE_BEFORE_ARRIVAL_THEN_ENTITY_ID).
- ORACLE RESULT: A start 0 end 2 wait 0; B start 2 end 4 wait 1; MEAN WAIT 0.5; four events; clock
  ends at 4. PASS. Confirmed independently by `oracles_cat_5.des_single_server`. PASS. Two servers
  give mean wait 0. PASS. Simultaneous arrivals resolve by entity id. PASS.
- ABSTENTION RESULT: no resource refuses; no entities refuses; negative service refuses; the two
  indices and two progress figures are NOT ESTIMABLE.
- REMAINING: no band; CAL Run 33.

## Supply-path reconciliation

`code_audit/run29_supply_path_reconciliation.csv`: 17 rows, one per structure, each recording
structure, modules served, producer/intake, production reachable, real corpus populated, canonical
validation point and behaviour when absent.

**REASONABLY SUPPLYABLE STRUCTURES WITH NO PRODUCTION PATH = 0.**

The intake is the existing mechanism, extended rather than duplicated:
`server/app/writes.py::w_saveprojectdata -> server/app/project_data.py ->
server/app/documents.py::run_and_store`. `governed_structure_keys()` is now the union of the
canonical, v3 and v4 maps, read from the analytical layer rather than restated.

`server/tools/test_run29_supply_path_guard.py` (121 checks) proves it end to end: for each of the
seventeen structures a record is STORED, READ BACK, MERGED ONTO SIGNAL INPUTS and the module then
RUN FROM THE REGISTRY and required to compute, which is the same sequence `run_and_store` performs.
It also proves the store's rules for the new keys (unknown key refused, blank provenance refused,
period-effective isolation, append-only), reconciles the CSV against the code row for row, and
demonstrates its own non-vacuity by removing a key from the vocabulary in an isolated copy,
observing red, and restoring.

HONESTLY STATED: `real_corpus_populated = no` for all seventeen. The path exists; the data do not
yet. Neither claim is dressed as the other. A fixture is not a supply path, and
`server/tools/run29_fixtures.py` says so in its own docstring; no production code imports it.

## 5.2 / 5.3 lineage proof

Three independent demonstrations that Tornado creates no second evidence body:

1. STRUCTURAL. `tornado_ranking(sensitivity)` takes the sensitivity RESULT as its only argument. It
   has no access to the structure, the response model or the signal inputs.
2. BY VALUE. Every bar's response_at_low / response_at_high is asserted equal, value for value, to
   the corresponding figures in A5.2's own result.
3. BY PERTURBATION (fault 13). Doubling the response model's coefficient on A moves A5.2's answers,
   and the tornado's bars move with them. A module holding independent evidence would not have
   moved. Its lineage carries derived_from = "A5.2", derived_from_response_model_version and
   derived_from_base_response, all equal to A5.2's.

`lineage.py` now declares A5.2 INDEPENDENT on SENSITIVITY_MODEL and A5.3 DERIVED with
dependency_ids = ("A5.2",). Fusion places them in ONE body, so two readings of one evidence body
cannot corroborate each other.

Both registry identities are kept. Neither module was removed. No other consolidation was made.

## Stochastic reproducibility evidence

| | A5.7 | A5.8 |
|---|---|---|
| deterministic limiting case tested first | yes (disruption 0) | yes (explicit service times) |
| seed | 20260816, recorded on the result | 20260816, recorded on the result |
| replications | 5, recorded on the result | 20, recorded on the result |
| reproducibility | identical traces replication for replication across two runs | mean waits identical within the PREDECLARED tolerance of 1e-9 |
| seed really drives it | a different seed gives different disrupted-step counts | a different seed gives different replication means |

The generator is a self-contained seeded LCG inside `canonical_v4`, deliberately not Python's
process-global `random`, so an unrelated call elsewhere cannot shift the stream.

## Non-vacuity campaign: all twenty faults

`code_audit/run29_fault_injection.csv`, produced by `server/tools/test_run29_fault_campaign.py`
(118 checks, all green). For every fault: injection CONFIRMED BY READING THE MUTATED STATE BACK,
guard GREEN before, RED under the fault for the intended reason, restored, GREEN after. NO CRASH
WAS ACCEPTED AS RED: every red observation is a boolean over a value the module returned.

| # | fault | guard turned red |
|---|---|---|
| 1 | Document Risk Score with no evidence provenance | document_risk_evidence provenance guard |
| 2 | RFI cumulative-register revision double-counted | identity de-duplication; and 24 DISTINCT ids really do read double, so it is not blind |
| 3 | submittal rejected greater than assessed | totals-path domain guard; and a duplicated register decision refused |
| 4 | NCR numerator with no exposure | ncr_rate exposure guard |
| 5 | weather day with no schedule linkage | weather_day_impact linkage guard |
| 6 | change frequency with no exposure | change_frequency exposure guard |
| 7 | dispute inferred from RFI/change counts | require_v4_structure; swept over 27 combinations, no stage ever produced |
| 8 | opaque subcontractor score | subcontractor_performance provenance guard; and a version-less governed structure too |
| 9 | delayed procurement item double-counted | duplicate item identity refused; states partition |
| 10 | specification density with no denominator | exposure guard |
| 11 | DSM edge removed AND reversed | propagation falls to zero in both cases |
| 12 | sensitivity without input perturbation | perturbation guard |
| 13 | Tornado as an independent evidence body | the bars move with the sensitivity's |
| 14 | inconsistent scenario state | consistency-constraint guard |
| 15 | broken system-dynamics accounting identity | accounting guard |
| 16 | unstable queue lambda >= mu | refuses, reports no L or W; lambda = 2.999 still computes |
| 17 | ABM with no agents / no rules | agent and rule guards, two injections |
| 18 | DES with no resource / no entities | resource and entity guards, two injections |
| 19 | orphan canonical structure with no supply path | supply-path completeness check names it; the store refuses to accept it |
| 20 | duplicate simulation version stamp | uniqueness guard; and the append-only prefix guard against a rewritten earlier entry |

## Participant-package chain

`og-participant-2026.08-v1 -> v2 -> v3 -> v4`.

A successor was required and created. Run 29 removed six proxy qualifiers from `registry.py`
because the six modules they described now perform their canonical methods; the participant-facing
defensibility evidence object is GENERATED from the registry, so its bytes moved.

- **v3 WAS NOT REGENERATED.** It is pinned in `participant_packages.py` to commit `01e943e`, whose
  blobs it describes, and the guard asserts its record file in the tree is byte-identical to that
  commit's. This is exactly the defect Run 28's closure had to correct in the v2 record, and it was
  not repeated.
- **v4** is `code_audit/run29_participant_package_v4_checksums.sha256`, 70 files.
- EXACTLY ONE FILE CHANGED, `assets/js/ds_defensibility_evidence.js`, and the change is the DELETION
  of six sentences that would now be false. Proved by normalisation, not asserted: restoring the six
  qualifiers to the current file reproduces its v3 bytes exactly.
- IDENTITY GUARD HOLDS: exactly one record in the four-link chain matches the live tree and it is
  the one declared current.
- PROTOCOL UNCHANGED: every file carrying a sequence step, the randomization, the reveal timing, the
  lock enforcement, the server contract, the append-only record or the treatment logic is
  byte-identical across v2, v3 and v4. No participant-facing NAME changed.

## Other guarantees the contract asks for

- VOTING REMAINS EXACTLY TWO: A1.7, A1.8. Asserted in the oracle suite and unchanged.
- MATERIAL COST VARIANCE (A3.4) REMAINS DISABLED and non-executed.
- NO RENAME was made in Categories 4 or 5, or anywhere else.
- NO UNSOURCED STATUS BAND WAS INTRODUCED. Sixteen modules assert no colour. A4.2 and A4.3 keep the
  ladders they already carried, which `registry.py` records as uncited.
- SIX TRUTHFUL METHOD LABELS REMOVED (A4.6, A4.7, A4.10, A5.3, A5.5, A5.8) and six proxy qualifiers
  removed (A4.5, A4.6, A4.7, A4.8, A5.2, A5.3), because leaving them would be the same untruth those
  tables exist to prevent, told in the opposite direction.
- CATEGORY-9 NOT CLAIMED. SIGNAL_QUALIFICATION = "unqualified" and CATEGORY_9_DEVIATION stand. Run
  31 owns the gate.

## What Run 29 could not do, stated plainly

1. NO REAL CORPUS POPULATED ANY OF THE SEVENTEEN STRUCTURES. Every Category-4 and -5 module that
   requires one abstains on the real corpus. The supply path is built and exercised; the data are
   not there.
2. THE SYNTHETIC RESEARCH PACKAGE STILL CARRIES THE v2 SHAPES for A4.4, A5.6 and A5.7 (an audited
   cohort, an occupancy log, a typed-in state history). Those shapes are no longer what the
   canonical methods read, so the thirty-plus project periods of synthetic agreement Run 10B
   recorded for those three modules are NOT replaced by an equivalent number. Rebuilding the
   synthetic package in the v4 shapes is Run 30 work.
3. A4.1 REMAINS REGISTRY-EXCLUDED. Its evidence contract, aggregation and abstention behaviour are
   correct and its production consumer is the extraction merge, but no new registry module was
   created, so the 100-target registry arithmetic is unchanged.
4. A5.4's DECISION PATH WAS RETIRED FROM CATEGORY 5, which reduces the coverage of the
   reference-object leakage controls from two modules to one (B2.19). Recorded in
   `test_run10b_canonical_integration.py` rather than glossed.
5. NO CALIBRATION AND NO EMPIRICAL VALIDATION was performed, per sections 11 and 9.

## Run-30 handoff requirements

1. Rebuild the synthetic research package structures in the v4 shapes (`ncrExposureRecord`,
   `queueModel`, `agentSupplyChainModel`, and ideally the remaining fourteen) so Category-4 and -5
   integration regains a multi-project corpus.
2. Decide the owner question A5.4 raises: whether the retired actions-by-scenarios decision method
   should be re-registered under Category 10.
3. Categories 6 to 10 and Portfolio Health remain unremediated and were explicitly out of scope.
4. Run 31 still owns the Category-9 qualification gate and the Category-8 orphan-field package.
5. Run 33 still owns every calibration and every empirical validation named above.

---

*(End of the Run-29 report reproduced verbatim.)*

### Run 29 final-head record

- Analytical line: **`sim-2026.08-v13`**.
- Freeze identifier: **`OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-16-RUN29-CANONICAL-CAT4-5-V13-1`**,
  superseding `OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN28-CLOSURE-V12-2`.
- Freeze manifest: `research/freeze/RUN29_CANONICAL_CAT4_5_FREEZE_2026-08-16.json`,
  sha256 `a833a3b805fbdb4f4f2f1d0bb8520ff73f753d0b06720c148c8e9b7f7472e684`,
  stage-1 commit `0a4e862aafa011b4d08e2fdd63c7ddaa9b47816f`.
- Production tree manifest: `code_audit/run29_production_tree.sha256`, 229 files.
- Participant package: **`og-participant-2026.08-v4`**,
  `code_audit/run29_participant_package_v4_checksums.sha256`, 70 files. v1, v2 and v3 preserved;
  v3 pinned to `01e943e` and NOT regenerated.
- Freeze chain: RUN22, POSTRUN22-UI-1, RUN24, RUN25, RUN26, RUN28-CANONICAL-CAT1-3-V11-1,
  RUN28-CLOSURE-V11-2, RUN28-CLOSURE-V12-1, RUN28-CLOSURE-V12-2, **RUN29-CANONICAL-CAT4-5-V13-1**.
- **The complete suite result from the exact final head is recorded in the finalisation commit
  message.**

## Final head, recorded here as well as in the finalisation commit

HEAD == main == origin/main == `5f8c40991d18ee03864492ee98334d2fdc3d8c39`, working tree clean.
Complete suite on that exact commit, run after it was the last commit: **134 suites,
11281/11281 checks, all suites green.** Nothing inherited from an earlier commit.
