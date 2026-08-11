# Known-answer testing across the taxonomy, after the freeze

Branch `claude/known-answer-tests` from `origin/main` at `cdc1d8a`. **This run adds tests and
changes no production code.** The platform is frozen at `sim-2026.08-v2`. Every defect a case
revealed is reported here and left in place: changing an algorithm now breaks the freeze and is
the owner's decision. The byte-identical frozen-file guard was not tripped; section 0 of the new
suite asserts that nothing under `server/app/` or `assets/` differs from `origin/main`.

`server/tools/test_run6_known_answer.py` (new), **268 known-answer cases, 437 checks, all
passing**, and every one of the 268 expectations proved live by perturbing the EXPECTED value.

---

## 1. LEAD: five findings where a module's output does not match its own label or its own
## stated formula. The freeze protects all five.

### 1.1 The module that scores the courses of action can never report a healthy project

`B4.7 Regret Minimization` computes expected regret from a fixed matrix and fixed state
probabilities, takes the lowest, and then overrides on the period's own indices. The three
expected regrets are literals with no input dependence: **monitor 11, investigate 5, escalate 8**.
The minimum is therefore **always investigate**, never monitor, and the override can only move it
to escalate. Monitor is the only branch that produces Green.

**Green is unreachable.** Asserted over the whole index grid, 3,721 cost and schedule index pairs
from 0.70 to 1.30 in hundredths: not one produces Green. A project performing twenty per cent
above plan on both indices is still told to investigate.

This is the module `recommendation_options.js` gates the courses of action on, and its finding
text reads "Minimax regret recommends: investigate ... this decision minimizes worst-case outcome
under uncertain future states", which describes a comparison that the constants have already
decided. The 2026-08-08 six-fixes run found that the scores are the same for every project and
corrected the card's wording; **it did not find that one of the three options is unreachable.**

### 1.2 Seven modules produce a status band from an input dictionary containing nothing at all

Exhausted over every implemented module, handed `{}`:

| Module | Band from nothing | Why |
|---|---|---|
| Missing Data Index | Red | correct: absence is its subject |
| Information Completeness Ratio | Red | correct: absence is its subject |
| PERT Network Criticality | **Green** | reads the schedule index with a default of 1.0 |
| Line of Balance | **Green** | same default |
| CCPM Buffer Health | **Amber** | same default |
| Reference Class Forecasting | **Red** | reads no project input at all; the multipliers are literals |
| DSM Rework Propagation | **Amber** | reads no project input at all; the matrix is literals |

The last five are the audit's sixth release blocker ("deterministic constants masquerade as
project analytics") measured rather than asserted. They are not merely uncalibrated: they report a
status about a project for which nothing has been reported. Three of them are not among the thirty
relabelled proxies and carry no qualifier anywhere.

### 1.3 Nine more modules substitute a value where the validate-seven run's guards refuse

Run 4's incidental finding 4 said "the class is wider than the seven". It is nine wider, and this
run enumerates it. Each is a zero denominator or an absent input, and each returns a band:

| Module | The input | What it returns |
|---|---|---|
| Overhead Absorption Rate | an indirect plan of zero | **Green** (absorption substituted as 1) |
| Inflation Adjustment Index | a material baseline of zero | **Green** (escalation substituted as 0) |
| Queueing Theory Bottleneck | nothing planned | **Green** (`max(planned, 1)`) |
| Agent-Based Supply Chain | an empty long-lead log | **Green** (`max(total, 1)`) |
| Schedule Compression Index | a schedule index of zero | **Green** (`spi \|\| 1.0`) |
| Critical Path Index | no planned progress | **Amber** (progress ratio substituted by the index) |
| Discrete Event Simulation | no planned progress | **Green** (progress ratio substituted as 1) |
| Safety Performance Index | nothing discussed | **Green** (an incident rate of zero) |
| Specification Conflict Density | no requests | Yellow |

Two of these are the same `max(count, 1)` invented denominator the fifteen-defects run removed
from Look-Ahead Schedule Health and Procurement Lead Time, still present in the two neighbouring
modules that read the identical inputs. **Queueing Theory Bottleneck and Look-Ahead Schedule
Health read the same two fields; one now abstains on an empty window and the other reads Green.**

### 1.4 A composite index improves when evidence is withheld

`A4.7 Dispute Escalation Index` is labelled "an ad hoc 0.3 / 0.3 / 0.4 weighted sum; weights and
dependence uncalibrated". The weights are exactly those, asserted by isolating each term. But an
absent source contributes zero rather than being renormalised out, so the identical project scores
**0.8 when it reports a request log and a change order log and 0.2 when it reports neither.**
Withholding evidence improves the reading by three bands. This is the audit's "changing composite
denominators" finding, located.

Its finding text also reads "(doc risk + RFI velocity + CO frequency combined)". The term is a raw
request count capped at twenty, not a velocity, and the change-order term is a raw count capped at
ten, not a frequency. **Two of the three names in a user-facing sentence describe quantities the
module does not compute.**

### 1.5 The reported conflict figure depends on the order sources arrive in

Exhausted over every permutation of every multiset of length two to four drawn from the four
bands, 65 multisets:

- **the fused status does not depend on order in any of the 65** (good, and worth recording, since
  Dempster's rule is commutative and a reader is entitled to expect it);
- **the reported conflict differs by order in 50 of the 65.** `dst_fuse` records "the last genuine
  combine", and which combination is last is decided by arrival order. Green and Red fused in one
  order records 0.8936 and in the other 0.910091.

Category and project conflict are stored on every result and shown to a reader. The number is not
a property of the evidence alone.

---

## 2. Coverage table

Counted against the registry in section 9 of the suite, not claimed. **100 registry-computed
modules: 63 given a known-answer case here, 2 given one by the validate-seven run, 8 disabled and
never executed, 27 not given one.**

### 2.1 The five CORE modules held non-voting (priority 1)

| Module | Case | Expected, by hand from the module's own formula | Actual | Result |
|---|---|---|---|---|
| Look-Ahead Schedule Health | 37 of 200 constrained | 0.185, rounds half-up to 19 per cent, Yellow; "37 of 200 planned activities constrained (19%)" | as expected | pass |
| Contingency Burn Rate | 300k burned of 1m at 25 per cent complete | burn 0.30 / progress 0.25 = stress 1.2, Yellow; "Contingency: 30% burned at 25% complete" | as expected | pass |
| Material Cost Variance | 880k against a 2m baseline at 40 per cent | expected 800k, variance +0.10, Yellow; "+10% vs expected at current progress" | as expected | pass |
| RFI Velocity | 30 over 105 days, 9 overdue | 8.6 per thirty days, 2.0 a week (Green), overdue 0.30 (Amber), worse wins: Amber | as expected | pass |
| Submittal Rejection Rate | 12 of 80 | 0.15 exactly, Yellow; "12 of 80 submittals rejected (15%)" | as expected | pass |

Boundaries: every edge of all five ladders hit exactly, plus one step above and one below, using
denominators that make the edge exact (1,000 planned activities; a 700-day log period; a 1,000
entry register). 45 boundary cases. Domain refusals: 16 cases, every guard the validate-seven run
installed proved still to refuse and to give a speakable reason.

### 2.2 The thirty advisory proxies (priority 2) — one case each, all thirty covered

Each case asserts the number, the band and the finding text, and where the qualifier makes a
checkable claim the case checks that claim rather than only the output. Examples:

| Module | Expected | What the case proves about the qualifier |
|---|---|---|
| CUSUM Anomaly Monitor | flat series: sigma takes the 0.05 floor, k 0.025, H 0.25, no breach, green | that the chart is **two-sided**: a second case shows a fall below target accumulating 0.375 on the low arm |
| Bayesian EAC | posterior 1,066,176, +6.6 per cent, Yellow | that the variances are **designed and proportional**: doubling the budget leaves the percentage at 6.6 |
| Regression to Mean CPI | 0.95 from a history of 0.80 and 1.00 | that the shrinkage is **exactly one half, never estimated**, over all 289 histories in a grid |
| Dispute Escalation Index | 0.5 | that the weights are **exactly 0.3 / 0.3 / 0.4**, by isolating each term |
| Portfolio Outlier Detection | worst of four ranks at the 25th percentile, Amber | that the **small-n behaviour** the qualifier admits is real: in a two-project portfolio the worst project reads Green |
| Pythagorean, Picture, Hesitant, Type-2, Maximum Entropy, Possibility, Spherical, Fermatean | full membership vectors and bands from cpi 0.95, spi 0.92, document risk 0.20 | that all eight are **hard-coded transformations of two indices and one score**, with every constant reproduced by hand |

The other proxies covered with a full known-answer case: Kalman Filter SPI Smoother, Budget
Execution Rate, Schedule Compression Index, S-Curve Deviation, Milestone Trend Analysis, Labor
Productivity Index, Overhead Absorption Rate, Analogous Estimating Ratio, Inflation Adjustment
Index, Weather Day Impact, Change Order Frequency, Subcontractor Performance, Sensitivity
Analysis, Tornado Risk Ranking, Contract Modification Frequency, Constraint Satisfaction Analysis,
What-If Scenario Matrix.

**No proxy was found whose OUTPUT contradicts its qualifier.** The two labelling faults found are
in the finding text rather than the qualifier (1.4 above), and in what the qualifier omits: the
change-order and contract-modification qualifiers describe only the count and not the contract
growth term, which is half the ladder in both.

### 2.3 The twelve newly wired modules (priority 3) — all twelve covered

Fed through the application's own adapter (`signal_package.build_signals` then `adapt`) from a
flat dictionary plus this run's own module results, never through a package the suite assembles.
The adapter's own output is asserted first: an index pair of 0.85 and 0.85 assembles to `red`, a
document risk of 0.80 assembles to `red`, and the forecast overrun is carried on `p80DeltaPct`,
the key the modules actually read.

| Module | Expected | Result |
|---|---|---|
| Conservative Dominance | four red signals, so Red-review and "Multi-signal red-review" | pass |
| ABM Governance Layer | the escalation pair: recovery-plan review, Program director / PMO lead | pass |
| Dempster-Shafer | **the four-source combination worked by hand in the suite's comment**: K of 0.285, then 0.2297, then 0.20747; Green 0, Amber 0, Red 1.0, conflict 0.21 | pass |
| Rough Sets | four of four Red, lower approximation exactly {Red}, empty boundary, "Definite Red" | pass |
| Neutrosophic Logic | truth 1 - (0.25 x 0.25 x 0.10 x 0.25) = 0.9984, indeterminacy 0.15^3 x 0.05, normalised to 1 / 0 / 0, Red, Low | pass |
| Interval Fuzzy Sets | green [0,0], amber [0, 0.43], red [0.71, 1], width 0.71, High | pass |
| Z-numbers | red total 0.85 + 0.90 + 0.65 + 0.88 = 3.28, average reliability 0.82 | pass |
| PLTS | means 0.025 / 0.1375 / 0.8375, reported 3 / 14 / 84 | pass |
| Belief Rule Base | one rule activates, so its belief is returned unchanged: 2 / 8 / 90 | pass |
| Weighted Voting | Red 6.1 of 7.3 weighted, 84 per cent | pass |
| Majority Rules | Green 1, Amber 1, Red 4 of 6, 67 per cent | pass |
| Worst N of M | 4 Red and 1 Amber of 6, trigger ceil(6 x 0.3) = 2 | pass |

Plus: the two concept-only modules among the fourteen refuse **even on a fully assembled package**,
and both governance projections abstain in a first period, which is the one abstention among the
fourteen that resolves itself.

### 2.4 Data and evidence health, the governance thresholds, and the portfolio group

All seven Group C modules, the three threshold modules, the regret module, and all five Group D
modules carry a known-answer case. Selected expectations, all met: Data Timeliness 90 days exactly
lands Amber on the inclusive edge; Cross-document Consistency scores 2 of 3 at 67 per cent and
falls to Amber because 0.6667 is below the 0.67 edge; OMB A-11's ten-million boundary is inclusive
so a budget one unit below does not trigger; the Trajectory Classifier's slope divides by
intervals and returns 0.1 per period on 0.90, 1.00, 1.10, which is the fifteen-defects run's own
fix re-derived by hand rather than remembered.

### 2.5 Shared machinery (priority 4)

- **`normalise_status`**: 17 vocabulary values and 10 refusals asserted individually, plus every
  band in five casings exhausted. An unrecognised value returns None, never Green.
- **`dst_combine`**: the audit's own worked case (two sources at Green 0.8 and Theta 0.2 give
  conflict 0, Green 0.96, Theta 0.04); total disagreement returns the uniform escape rather than
  dividing by zero; and four algebraic properties asserted over **2,000 random mass pairs** each,
  not sampled illustratively: commutativity, mass summing to one, conflict bounded in zero to one,
  and a wholly vacuous source acting as the identity.
- **`dst_fuse`**: exhausted over every permutation of every multiset of length two to four. See
  finding 1.5.
- **The rollup**: exactly the categories carrying a voting module have a fused status; one
  category votes; project conflict is structurally zero; no evidence-health category has a fused
  status; exactly two modules carry a vote on the stored row.

### 2.6 Abstentions (priority 5)

Every implemented module handed an empty input: **none raises**, 62 abstain with a speakable
reason (words, no key name, no module id, no em dash), and exactly seven band, which is finding
1.2. Plus the 16 domain refusals in section 1 of the suite and the 19 domain cases in section 7.

**At the surface that renders, not only the stored row.** The freeze run found abstention reasons
had never reached the ledger. This run asserts the whole chain: the server stores every abstention
as a `module_id` and a `reason` pair; `taxonomy.js`'s `getModuleAbstentionReason` reads the
`abstained` list off the row; `detail.js` grafts that list onto the projection the page reads; and
`app.js` calls the accessor and emits a `cat-mod-reason` element under a silent row.
`tests_render.html` group 18 already drives the renderer and asserts the reason element's text
character for character, and it passes. **What this run did not do is re-drive the live detail page
in a browser end to end**; the chain is asserted at each join and at the renderer, and the freeze
run confirmed the rendered result by eye.

---

## 3. What could not be covered, and why

**27 of the 100 registry-computed modules were not given a known-answer case.** Printed by the
suite rather than listed from memory:

`A1.1 A1.5 A1.6 A1.11 A2.1 A2.2 A2.3 A2.5 A2.9 A2.10 A2.11 A3.1 A3.6 A4.4 A4.10 A5.1 A5.4 A5.5
A5.6 A5.7 A5.8 A6.1 A6.2 A6.3 A6.4 B2.18 B2.19`

Three reasons, stated per module rather than in aggregate:

1. **Genuinely too involved to hand-compute, so skipped rather than recorded from a run.**
   Monte Carlo EAC (5,000 Beta-PERT draws through a Marsaglia-Tsang gamma sampler on a mulberry32
   stream) and PERT Network Criticality (2,000 triangular draws) have no closed form a person can
   check. Recording what they return would assert that the code equals itself, which is the
   failure mode this run exists to avoid. Line of Balance, CCPM Buffer Health, Reference Class
   Forecasting and DSM Rework Propagation are hand-computable but produce a constant independent
   of the project, which finding 1.2 records as the more useful result.
2. **Covered by an earlier run's known-answer case and not re-derived here**, to keep this run
   inside its budget: Quality Compliance Index, Scenario Modeling, Contractor Performance,
   Environmental Compliance Rate, NCR Rate and Float Consumption Rate all carry the
   fifteen-defects run's own cases, and Cost Risk P80 carries its guard case.
3. **Ran out of run**, and this is the honest category: ARIMA CPI Forecast, Earned Schedule, ICE
   Ratio, Resource Loading Index, Schedule Risk Analysis P80, Specification Conflict Density,
   Rework Feedback Loop, Queueing Theory Bottleneck, Agent-Based Supply Chain, Discrete Event
   Simulation, Safety Performance Index, MARCOS and CRITIC-TOPSIS are all straightforwardly
   hand-computable and simply were not reached. **Every one of them is covered by the abstention
   sweep and the domain sweep, so none is untested; what none has is a hand-computed expected
   value.** This is the first thing a following run should close.

The eight disabled concept-only modules are excluded by construction: they never execute, and this
run asserts that they refuse even on a fully assembled package.

---

## 4. `ds_defensibility_data.js`: the overclaim count

**103 module entries. 69 of them state that the module HAS BEEN VALIDATED** in their
`accreditationBasis` field, in the form "Validated by convergence checks...", "Validated by
back-testing...", and so on. **75 of the 103 carry no calibration or validation qualification
anywhere in the entry.**

No module on this platform has that property. The freeze record states in as many words that no
labelled holdout corpus and no expert reference standard exist, so false-positive and
false-negative performance is unmeasured, and the two modules with sourced band boundaries carry
`BAND_SOURCE_LIMIT` saying exactly that. The file is loaded by `index.html`, so it is a live
surface, asserted here.

**Not edited.** The freeze run corrected two entries; the remaining content is the owner's
decision. The measure used is stated in the suite so the number can be re-derived: an entry
overclaims when its accreditation basis asserts validation, and the count of entries carrying no
qualification anywhere is reported separately so the owner can choose which threshold to act on.

---

## 5. The browser instrument's current state

Unchanged from the fifteen-defects run's report, asserted rather than remembered:

- `assets/js/sim.js` still defines `DEMO_BAC` and still emits the forecast overrun as
  `p80eacOverrunPct`, the key no consuming module reads;
- `assets/js/simulations.js` still carries the pre-remediation arithmetic;
- **`research/deepdive.html` still loads both**, so the researcher deep-dive route still shows the
  defective arithmetic, including all fifteen fixed defects in their pre-fix form.

Neither file loads on a participant route. This remains an owner decision: annotate the divergence
or bring the browser copies into line. `VALIDATION.md`'s parity claims for those fifteen are parity
with a defect.

---

## 6. Metamorphic cases: where invariance was expected and not found

| Property | Expected | Found |
|---|---|---|
| Isolation Forest under an equivalent rescaling of document risk from zero-to-one to zero-to-one-hundred | invariant | **the distance IS invariant; the THRESHOLD is not**, because it sums the raw standard deviations, so the classification moves while the distance does not. The audit's own proof reproduced. |
| Schedule Compression Index under a scaling of the project's duration | invariant (the ratio is one over the index) | **not invariant.** A year-long baseline at an index of 0.50 gives 2.0 and Red; a two-day baseline at the SAME index gives 1.0 and Green, because the available days are floored at one day. |
| Dispute Escalation Index under adding evidence | monotone, or at worst neutral | **not monotone**: 0.8 with two logs, 0.2 with neither. See 1.4. |
| `dst_fuse` under reordering the sources | invariant | **status invariant, conflict not.** See 1.5. |
| Majority Rules under reordering the results array | invariant | invariant, exhausted over all six permutations |
| Procurement Lead Time under scaling every count | invariant | invariant, exhausted over 24 scalings; 0.65 every time |
| Kalman filter on a constant series | returns the constant | holds, over 124 series in a grid of levels and lengths |

---

## 7. Boundary inclusivity findings

**Stated per ladder, because the code does not state it anywhere.**

- **Look-Ahead Schedule Health, Contingency Burn Rate, Material Cost Variance, Submittal Rejection
  Rate**: every boundary is inclusive on the CALMER side (`<=`), so the edge value reads better.
- **RFI Velocity carries two ladders that disagree with each other.** The per-week ladder uses
  `<=`, so exactly two a week is Green. The overdue ladder uses `<`, so exactly ten per cent
  overdue is Yellow rather than Green. One module, two conventions, no comment saying so.
- **RFI Velocity bands after rounding.** 2.04 requests a week is rounded to 2.0 and reads Green;
  the effective step either side of the boundary is a tenth, not a hundredth. Recorded by the
  validate-seven run and asserted here.
- **Cross-document Consistency has an unreachable edge.** The Yellow arm is `score >= 0.67` and
  two of three checks gives 0.66667, so a module that passes two of its three checks lands Amber.
  The stated boundary and the only score that could sit near it do not meet.
- **Regret Minimization's two overrides are both strict**, so exactly 0.88 does not escalate and
  exactly 0.95 does not investigate. Immaterial in practice, since Green is unreachable anyway.
- **OMB A-11's ten-million major-programme boundary is inclusive.**

---

## 8. Guarantees, each marked

- **Every expected value computed by hand from the module's own stated formula, with the
  derivation written beside it.** VERIFIED. No case in this suite runs a module and records what
  it returned. The two four-source Dempster combinations and the Bayesian posterior are worked
  arithmetic in the file's own comments.
- **Every known-answer assertion proved able to fail by perturbing the EXPECTED value.** VERIFIED,
  268 of 268, mechanically by `ka()`, which refuses a case whose expectation cannot be perturbed.
  Additionally demonstrated end to end: perturbing two expected numbers by hand takes the suite to
  430/432, restoring them returns it to 432/432.
- **Properties asserted over a domain are exhausted or randomised.** VERIFIED: 2,000 random mass
  pairs for four algebraic properties; every permutation of every multiset for the fusion; 3,721
  index pairs for the regret finding; 289 histories for the shrinkage coefficient; every
  implemented module for the abstention sweep.
- **The fourteen nested-input modules fed through the application's own adapter.** VERIFIED.
- **Abstention asserted at the surface that renders, not only on the stored row.** PARTLY MET.
  Each join in the chain is asserted and `tests_render.html` drives the renderer and asserts the
  rendered text; the live detail page was not re-driven in a browser in this run.
- **Every module with a band given a case above, below and AT each boundary.** MET for the five
  CORE modules held non-voting. NOT MET for the 27 modules in section 3, and not attempted for the
  proxies beyond one case each, which is what the run's priority order asked for.
- **No production code changed and the frozen-file guard not tripped.** VERIFIED in the suite
  itself and by `git diff --name-only origin/main`.
- **No existing check regressed.** VERIFIED, section 9 below.

---

## 9. Verification performed

Server suite, fresh SQLite per file via `alembic upgrade head`, `PYTHONIOENCODING=utf-8`
throughout, interpreter confirmed real. **62 files, 4,063/4,063 checks under the `RESULT: n/n`
convention, plus `test_run5_export.py`'s own 34/34, so 4,097 in total, 0 failing files.** The
baseline was 3,628/3,628 across 60 files under that convention; this run's new file adds 435 of
the 437 it reports (two of its checks are the coverage roster, which reports rather than counts).
**No existing check went red.** Nothing had to be re-pointed, loosened or rewritten, which is
itself worth recording after three consecutive runs in which existing suites turned out to encode
an old defect.

`tests.html`: **51/51**, real headless Chromium
(`/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`).
`tests_render.html`: **286/287**, the one red being the pre-existing auth-gated production-read row
that has been red in every run since Run 2 and requires a signed-in session in the same tab.

---

## 10. Incidental findings

1. **Change Order Frequency and Contract Modification Frequency read the same three inputs.** Two
   registered modules, two ladders, one measurement. They agreed on every case tried here. Worth a
   line in whatever consolidates the taxonomy.
2. **`models_dq.py`'s `run_info_completeness` defines a local `field_dt` helper that is never
   called.** Dead code, harmless, recorded.
3. **No module in the analytical layer refuses a document risk score outside its declared zero to
   one domain.** Forty implemented modules accept 85 and compute with it. The range guard is at
   ingestion (`extraction_merge.validate_doc_risk_score`), so the layer relies entirely on that one
   guard. Recorded so the reliance is explicit rather than assumed.
4. **Reference Class Forecasting and DSM Rework Propagation take no project input at all.** RCF
   reads the budget only to scale a display figure; the band comes from a literal list of
   multipliers. Both were already known to be constant; what is new is that they are constant even
   with an empty input, so nothing about a project can move them.
5. **Possibility Theory can only ever return Green, Amber or Red**, never Yellow: its dictionary
   has three keys. Not a defect, but a four-band ledger showing a three-band module.
6. **The status vocabulary is still mixed in stored results.** Monte Carlo and CUSUM store
   lowercase; nearly everything else stores capitalised. `fusion.normalise_status` handles it and
   is the one place that should.

---

## 11. What the next session needs

1. **Close the 27.** Thirteen of them are straightforwardly hand-computable and were simply not
   reached; that is the cheapest remaining coverage in the taxonomy.
2. **Finding 1.1 is the one to put in front of the owner first.** The module that scores the
   courses of action cannot report a healthy project, and the courses of action are on the
   participant's decision card.
3. **Findings 1.2 and 1.3 are a single unfreeze conversation**, not sixteen: they are one class,
   substitute-instead-of-refuse, and the validate-seven run already wrote the guard shape for it.
4. **Finding 1.5 belongs in the methods chapter beside the two consequences the validate-seven run
   named.** A conflict figure of zero already means "one source"; it now also means "whichever
   source happened to be last".
5. **The defensibility handbook is still the largest overclaim surface**, and there is now a
   number for it: 69 of 103 entries claim validation.
6. **0020 through 0025 remain unapplied in production.** This run adds no migration and touched no
   schema. Production was never inspected or queried; throwaway SQLite only.

**Files changed.** `server/tools/test_run6_known_answer.py` (new), this report, `T6_HANDOFF.md`.
No file under `server/app/` or `assets/`. No file outside the repository was touched.
