# Run 33 — Portfolio Health PH.1–PH.5 canonical remediation (`sim-2026.08-v21`)

**Branch `run33-portfolio-health-v21` from `main` at `54409af`.**
Artifacts: `code_audit/run33_*`. Suites: `server/tools/test_run33_*.py`.

---

## 1. Starting commit

`HEAD == main == origin/main == 54409af2a07ac989489447379e8379cc9f95e15f`, working tree clean,
verified from git before any edit. `SIMULATION_VERSION = "sim-2026.08-v20"`; participant package
`og-participant-2026.08-v10`; voting exactly 2 (A1.7 TCPI, A1.8 VAC); Category-9 raw and
missing-assessment bypasses 0.

## 2. v20 preservation

`sim-2026.08-v20` is preserved. It is named as `SIMULATION_VERSION_SUPERSEDED`, it holds its
position in `SIMULATION_VERSION_HISTORY`, and the v20 *package itself* is reconstructed from its
git object and executed in `test_run33_version_boundary.py`. The v20 portfolio implementation
`app.simulation.portfolio.compute_portfolio` is preserved **byte for byte in the tree**, because
Runs 2, 6, 13, 14, 15, 17 and 20 recorded findings about it and deleting it would delete the
subject of those findings. It is unreachable from production, proved from the live call site.

## 3. v21 identity and first commit

`sim-2026.08-v21`. History length 21, all identifiers unique, the v20 history a strict prefix of
the current one read out of git. The first v21 commit is the single Run-33 commit on this branch.

## 4. The exact five-target scope

Derived mechanically from `p0-baseline/module_renumbering_map.csv` — the source both registries
are generated from — by selecting the rows whose category is Portfolio Health. **Five rows, five
unique identities, missing 0, duplicates 0**, and they carry the PH.1–PH.5 identities the contract
names:

| stable id | PH id | name | method-class basis |
|---|---|---|---|
| D1.1 | PH.1 | Isolation Forest | Established canonical Isolation Forest (Liu, Ting and Zhou, ICDM 2008) |
| D1.2 | PH.2 | Portfolio Outlier Detection | PCEIF custom descriptive indicator — **not** a learned ML model |
| D1.3 | PH.3 | Signal Trajectory Classifier | PCEIF custom deterministic time-trend classifier — **not** trained |
| D1.4 | PH.4 | Cross-project Pattern Detector | PCEIF custom nearest-neighbour indicator — **not** a clustering model |
| D1.5 | PH.5 | Anomaly Score | PCEIF custom composite — **not** independent evidence |

`code_audit/run33_portfolio_health_scope.csv`.

---

## 5. PH.1 — Isolation Forest: the current fidelity result

**The algorithm is genuine and was verified BY EXECUTION, not from the Run-15 report.** Random
attribute, random split between the observed minimum and maximum, height limit `ceil(log2 psi)`,
external node retaining its sample size, `h(x) = depth + c(n)`,
`c(n) = 2H(n-1) − 2(n−1)/n`, `s(x, psi) = 2^(−E[h(x)]/c(psi))`, paper defaults t = 100 and
psi = 256, seeded. `c(0) = c(1) = 0` and `c(2) = 1` exactly. All of it holds.

**THE FINDING THIS RUN WAS ASKED TO LOOK FOR IS REAL, AND IT IS OPERATIONAL, NOT ALGORITHMIC.**
v20 fitted a **new forest for every scored project**, on the other projects. Section 6's
operational rule forbids exactly that: *every project score reported together must come from the
same fitted forest*. On a three-project portfolio the v20 route grew a forest of reference size 2
for P1 and a different forest of reference size 2 for P2 — with three projects, a reference of two
necessarily excludes the project being scored — and the portfolio card displayed those scores side
by side as though they were one scale. v21 fits **one governed forest per cohort and model
version** and scores every member from it; the model record carries the fitted project population,
psi, tree count, height limit, seed, preprocessing version, cohort id and model version.

**One declared deviation, carried unchanged from Run 15 and recorded rather than hidden:** `H` is
taken by the paper's own `ln(i) + γ` estimate rather than the exact harmonic sum. The suite
measures the gap against the exact closed form and asserts it shrinks monotonically and agrees to
three decimals by psi = 256. It was NOT changed, because the Run-15 threshold was frozen on that
scale and section 14 forbids retuning.

**The frozen Run-15 threshold was verified mechanically and is not retuned and not extended.**
The artifact says 0.576; v21 carries 0.576; the artifact itself records
`FIELD_EMPIRICAL_VALIDATION = NOT_CLAIMED`. It is exposed **only** as a labelled synthetic /
laboratory artefact — `threshold_basis = SYNTHETIC_LABORATORY`, `is_project_status_band = false`,
`is_sole_trigger = false`, `field_validated = false` — and **no flag is derived from it on a
cohort whose feature schema is not the one it was fitted on**, so its claim does not travel. The
four v20 status bands hung off it are gone.

**Independent oracle (dev-only scikit-learn), reported honestly.**
`code_audit/run33_ph1_sklearn_oracle.csv`. scikit-learn 1.9.0 in a throwaway virtualenv;
`server/requirements.txt` is unchanged and no committed file imports it.

- On the compact structural fixture both implementations put **the same project at the top**.
  Its rank correlation is **not** held to the 0.99 requirement and the reason is stated in the
  artifact: nine of its ten points are a near-identical cluster, so the within-cluster ordering is
  ensemble sampling noise in *both* implementations and a correlation over it measures noise.
- On a seeded 300-project reference population with a graded radial spread, Spearman is
  **0.9875 at the paper default t = 100 — short of the contract's 0.99 — and 0.9955 at t = 400 and
  0.9975 at t = 1000.** The cause is ensemble Monte-Carlo variance and it is **demonstrated, not
  asserted**: fixture, psi and seed held fixed, only the ensemble size raised, for both
  implementations. **No production parameter was changed to obtain it.** Production keeps t = 100.

> **SUPERSEDED AS A FIDELITY VERDICT — see "PH.1 oracle correction" below.** These three
> measurements are preserved unchanged, but the `>= 0.99` acceptance condition they were judged
> against has been withdrawn: it was never a canonical requirement and it could not distinguish
> implementation fidelity from independent ensemble randomness. The fidelity question is now
> settled by fixed-forest scoring equivalence, and these figures are retained as
> `CROSS_IMPLEMENTATION_STOCHASTIC_COMPARISON`.

**Degenerate and small-n cases** all behave: one project → abstain under `INSUFFICIENT_COHORT`,
no flag of any kind; two projects → computes with an explicit small-sample limitation claiming no
predictive validity; identical vectors → no project more anomalous than another; zero-variance
feature → the published construction never selects an attribute admitting no split; missing
qualified feature → abstain, and the missing value is never zero; mixed periods and mixed feature
schemas → rejected for all five modules alike.

## 5a. PH.1 oracle correction (Run-33 final closure)

**The original single-seed `>= 0.99` Spearman requirement was not a canonical literature
requirement, and it has been withdrawn as a fidelity condition.** It conflated two different
things. Both implementations construct *randomized* ensembles, and equivalent algorithms need not
generate identical forests from nominally corresponding seeds — the seeds index different
generators consumed in different orders. One observed rank correlation is therefore a single draw
from a distribution that mixes algorithm fidelity with Monte Carlo ensemble variation, and a low
draw is not evidence of an implementation defect.

**The measurement that does separate them is fixed-forest scoring equivalence, and it is now the
primary method-fidelity proof.** `server/tests/test_run33_ph1_fixed_forest.py` (132/132, wired
into the acceptance runner by `server/tools/test_run33_ph1_fixed_forest.py`) freezes the forest
and requires two independently written scorers to agree on the same points over the same trees.
Ensemble randomness is held constant and only the arithmetic is under test.

- `server/tools/run33_frozen_forest.py` reimplements `c(n)`, the path-length traversal, the
  ensemble mean and the normalized score from the published definition, and evaluates frozen tree
  structures recorded as plain data: selected feature, split value, left/right children, leaf
  sample size, path-depth convention, external-node adjustment, `psi` and `c(psi)`.
- **It never calls the production scorer.** That independence is proved structurally — the
  oracle's parsed import set contains nothing from `app`, its executable code references none of
  `_path_length`, `c_factor`, `anomaly_score`, `mean_path_length` or `harmonic`, and the two files
  share no literal text even for Euler's constant — and *behaviourally*: perturb production's path
  length in process and production's score moves while the oracle's does not.
- **Result: exact agreement.** Worst absolute score difference **0.000e+00** and worst per-tree
  path-length difference **0.000e+00** across 100 trees × 10 points, against a predeclared
  tolerance of 1e-12 justified by floating-point association alone. `c(psi)`, recomputed
  independently, matches the constant production divides by.

**Oracles A–D** (hand-built forests, every path calculable): a point isolated at 1 edge outranks
one isolated at 6; two points with identical adjusted path lengths in every tree receive equal
scores; hand-specified path lengths `[1,2,2]` and `[3,3,3]` give means `5/3` and `3` and put
**point A** as the more anomalous, matching `2^(-E[h]/c(10))` computed by hand; and a terminal node
holding 7 samples contributes `depth + c(7)` where a single-sample node contributes raw depth, so
the adjustment is observable rather than assumed.

**Production stayed at 100 trees.** Raising the tree count to clear a test threshold would be
tuning production to a fixture, and it was not done.

**Cross-implementation correlation is retained as convergence evidence, not as a verdict.** A
predeclared repeated-seed campaign — fixture, seeds, tree counts and statistics committed at
`200aec1` *before* the campaign was run — over 30 independent seeds per tree count on the frozen
300-project graded fixture:

| t | seeds | mean | median | min | max | sd | top-1 agreement | **same implementation vs. itself across seeds** |
|---|---|---|---|---|---|---|---|---|
| 100 | 30 | 0.986057 | 0.986461 | 0.977038 | 0.992606 | 0.002975 | 9/30 | **0.986049** |
| 400 | 30 | 0.995628 | 0.995500 | 0.994230 | 0.997408 | 0.000714 | 16/30 | 0.995392 |
| 1000 | 30 | 0.997821 | 0.997884 | 0.996843 | 0.998503 | 0.000478 | 25/30 | 0.997836 |

**The last column is decisive.** At t = 100 this implementation agrees with **itself** across
seeds at **0.986049** and with scikit-learn at **0.986057** — indistinguishable. The
cross-implementation shortfall is therefore *entirely* ensemble Monte Carlo variation and carries
no information about algorithm fidelity, which is precisely why the single-seed correlation could
never have been a fidelity requirement. Increasing the tree count reduced Monte Carlo ranking
variation on this frozen fixture; **no claim is made that 400 or 1,000 is therefore the correct
operational setting.**

**The original observations are preserved, not deleted:** t=100 **0.9875**, t=400 0.9955, t=1000
0.9975, retained in `code_audit/run33_ph1_sklearn_oracle.csv` and restated in
`code_audit/run33_ph1_cross_implementation_convergence.csv`. They are **reclassified** from
`CANONICAL_FIDELITY_FAILURE` to `CROSS_IMPLEMENTATION_STOCHASTIC_COMPARISON`, and that
reclassification was applied only *after* fixed-forest equivalence was measured to pass.

**Reproducibility.** Same cohort, feature schema, `psi`, tree count, seed and model version give
an identical frozen-forest digest and identical scores. A different seed gives a different forest
and may give different scores — the method is randomized, and that is the method behaving, not a
nondeterminism failure.

**The six assurance layers are kept separate** in `code_audit/run33_ph1_oracle_closure.csv`, with
genuinely different statuses:

| layer | status |
|---|---|
| canonical tree construction | VERIFIED |
| fixed-forest score equivalence | **PASS** |
| reproducibility | **PASS** |
| cross-implementation stochastic comparison | CROSS_IMPLEMENTATION_STOCHASTIC_COMPARISON (descriptive) |
| tree-count calibration | **PENDING_RUN_34** |
| threshold calibration | **PENDING_RUN_34** |
| PH.1 final disposition | CANONICAL_IMPLEMENTATION_PROVEN_CALIBRATION_PENDING |

**Simulation version unchanged.** Fixed-forest equivalence passed, so no analytical fix was
required and `sim-2026.08-v21` stands: a test and report closure does not move the stamp.

**Ten-fault non-vacuity campaign: 10 required, 10 applied, 10 RED for the intended reason, 10
restored GREEN, NOT_APPLIED 0, crashes accepted as RED 0**
(`code_audit/run33_ph1_fault_injection_results.csv`). Two are worth recording. Fault 3 could not
be expressed as "use `len(training)` instead of `psi`" on the compact fixture, because there
`psi = min(256, 10) = 10 = len(training)` and the mutation would have applied while changing
nothing; it is exercised on the 300-point fixture where `psi = 256` differs from `n = 300`. Fault
10 cannot be caught by the equivalence guard at all — an oracle that *delegates* to production
agrees with it trivially — so its guard is the independence proof instead.

**No empirical validation is claimed by any of this.** Fixed-forest equivalence is a statement
about arithmetic, and the convergence study is a comparison of two implementations on a synthetic
fixture. Neither is evidence about any real project.

## 6. PH.2 — the descriptive-ranking result

Midrank adverse-tail empirical percentile, in **exact rational arithmetic**, with the governed
orientation applied **before** ranking, composited as the unweighted mean over the complete
governed required risk-oriented feature set.

**The supplied oracle reproduces exactly, and through the production route:** values
`[1, 2, 3, 10]` give `1/8, 3/8, 5/8, 7/8`; 10 is the most extreme adverse project. Ties receive
the same midrank; project ordering does not change results; feature units do not change the rank;
a lower-is-worse orientation reverses it correctly (the value 1 becomes 7/8). A missing required
feature causes **abstention** — the feature is not dropped and the remainder is not renormalised.
n < 3 gives an explicit `INSUFFICIENT_COHORT` state; n < 10 carries the small-sample warning.

The equal-feature weighting is recorded as **`OWNER_POLICY`**, a transparent v21 design decision,
explicitly not an empirically calibrated constant. No status colours. The module declares itself
not a learned ML model and not a probability of failure. **The D1.2 proxy qualifier was
withdrawn** — every clause of "an empirical CPI and SPI percentile rank; small-n behaviour and
bands unvalidated" became false — and is preserved as history in
`code_audit/run33_proxy_qualifier_withdrawal.csv`.

## 7. PH.3 — the trajectory result

Ordinary-least-squares slope on **actual reporting times**, in exact rational arithmetic;
`q = +1` when higher is more adverse, `q = −1` when lower is; `a = q·b`;
`a > 0 → DETERIORATING`, `a < 0 → IMPROVING`, `|a| ≤ 1e-12 → FLAT`.

**The supplied oracle reproduces exactly:** `t = [0,1,2]`, `x = [1.0,0.9,0.8]` gives slope
**−1/10**; with `q = −1`, AdverseSlope **+1/10**; classification **DETERIORATING**. The suite also
asserts the slope is **not** −1/15: three observations contain two adjacent intervals and the
endpoint change is not divided by three.

**The 1e-12 is numerical zero handling. It is not an operational threshold**, and nothing in the
implementation or the report describes it as one. There is no magnitude band and no status band.

Irregular intervals enter the fit as they are; duplicate timestamps, fewer than three
observations, fewer than three distinct times, a broken stable signal identity, a missing period,
a missing value and an unassessed observation all abstain with their own reason; a constant series
is FLAT on an exactly zero slope; reversed input order gives the identical slope.

## 8. PH.4 — the pattern result

Cohort z-standardisation, zero-variance features **excluded and recorded**, abstention if all
features are non-informative, `d(i,k) = sqrt(Σ(z_ij − z_kj)² / p)`, `sim = 1/(1+d)`, self-match
excluded, all tied nearest neighbours returned in ascending project-id order under a **declared**
tie rule, peer condition reported separately.

**The unvalidated 0.15 match radius is retired and nothing replaces it.** There is no threshold
value, no matched-count field and no per-project radius field. Matching a healthy peer creates no
status: `similarity_is_not_failure` is a named constant and no status colour exists. Identical
vectors give distance 0 and similarity 1 and are named as duplicates explicitly; the uniformly
distant vector is the nearest match of no member of the compact cluster; ordering does not change
distances; mixed schemas and mixed periods are rejected; a missing required feature abstains.

## 9. PH.5 — the profile / scalar decision

**`score = null`, disposition `PARAMETER_PROVENANCE_BLOCKED`. This is the correct and required
outcome of Run 33, not a failure to complete it.** No governed normalisation, transformation,
weight set, missingness policy or calibration objective exists, and Run 34 owns all five.

The `PortfolioAnomalyProfile` exposes the exact constituent identities by module id and role
(PH.1 anomaly score, PH.2 outlier percentile, PH.3 slope/classification, PH.4 nearest-neighbour
result), each carrying its cohort, project, period, feature schema and model version, together
with the project's own source lineage.

- No constant placeholder survives: there is no score list, no composite mean, and the only
  number on a project profile is its evidence-body count.
- The retired Mahalanobis proxy and `1 − composite_rank` appear nowhere.
- **Missing PH.3 history leaves PH.1, PH.2 and PH.4 byte-identical.** No weight is renormalised,
  because there are no weights.
- A missing constituent is named as missing and is never converted to a neutral or favourable
  value.
- **Duplicate lineage cannot reinforce.** The evidence-body count counts evidence bodies, not
  constituents; `corroboration_established` is false and `confidence` is null. Every constituent
  declares itself **non-independent** of the others, because they are transforms of the same
  governed feature records under one schema.

## 10. The real three-project portfolio result

`code_audit/run33_real_portfolio_structure_reconciliation.csv`. **All five abstain on the real
corpus**, with one reason: the controlled portfolio supplies no governed portfolio cohort, feature
schema, feature record or signal history through `saveprojectdata`. **portfolio-present-but-unwired
= 0** — the intake exists and is wired end to end, proved by executing it, and an intake interface
is not data, so the corpus is recorded ABSENT rather than present-but-unwired.

This is the correct reading. At v20, the mere existence of two rows carrying a cost index was
enough to produce four populated portfolio readings; a comparison needs a declared population,
period, feature schema and model version, and "the rows this query returned" is none of those.

## 11. Small-n limitations

The controlled portfolio holds three projects, which sits exactly at the boundary the contract
names: at or above the minimum of 3 for a ranking, and far below 10. Every reading carries a
`limitation` block with the cohort size, an explicit `small_sample` flag, the small-sample note in
words, and `predictive_validity_claimed = false`. The participant-facing card renders the
small-sample sentence whenever the cohort holds fewer than ten projects. **No predictive validity
is claimed anywhere, for any module, on any corpus.**

## 12. Qualification and lineage

Portfolio Health reads the **current** Category-9 boundary object itself — `ELIGIBLE_STATES` from
`qualified_evidence` — so there is no second Portfolio Health qualification framework to drift.
Raw bypass 0: an `UNASSESSED` record is excluded from the cohort with its reason and is never
converted. Missing-assessment bypass 0: `REVIEW_REQUIRED`, `INSUFFICIENT_EVIDENCE` and
`NOT_APPLICABLE` cannot be read analytically; both eligible states can, so the gate is not simply
refusing everything. A missing value never becomes zero. Qualification does not imply
independence, and PH.5 says so in a field.

## 13. The 25-fault campaign

`code_audit/run33_portfolio_fault_injection_results.csv`.
**faults required 25 · applied 25 · intended RED 25 · restored GREEN 25 · NOT_APPLIED 0 ·
crashes accepted as RED 0.**

Source mutations rewrite real production source, run a probe in a fresh interpreter with bytecode
writing disabled, and drop `__pycache__` on **both** sides. An exception in a probe is reported as
a CRASH and scored zero, never as a RED.

**The campaign did not reach 25 on the first pass, and what happened is worth recording.** Six
faults were initially ill-posed: their "mutation" changed only the *input* — supplying records in
reverse order, withdrawing a history, offering a duplicate lineage — and the module correctly gave
the same answer, so nothing went red. That is not a fault injection; the property genuinely held.
Each was repointed at the actual defect in production source: a positional rank replacing the
midrank, the tie-break and member ordering both dropped, PH.1's ensemble size made to depend on
whether a history exists, the evidence-body count made to count constituents with a confidence
derived from it, the seeded RNG unseeded, and the score contaminated by raw feature magnitude.
Faults 10 and 18 each needed **two** anchors, because mutating one alone left the property
standing and the campaign would have credited a fault it had not proved.

The three load-bearing ones all go red for their intended reason:

- **Fault 5** (incomparable forests): the probe independently refits **one** forest on the whole
  cohort from the reported model metadata and requires every reported score to be that forest's
  score. Per-project forests fail it.
- **Fault 21** (duplicate lineage inflating confidence): offering the same PH.1 result twice under
  the PH.2 slot must not move the evidence-body count, corroboration or confidence.
- **Fault 23** (portfolio output entering project status or voting): merging the readings into
  `module_results` — the field Project Status, the rollups, fusion and the vote all read — goes
  red on a probe that reads the live call site, the storage column and the two-module voting set.

## 14. Package preservation

- **Simulation:** `sim-2026.08-v21`. v20 preserved, named as superseded, prefix-verified from git.
- **Synthetic:** successor **`OG-SYNTH-0.5`** minted, because governed fixture bytes are new. The
  five canonical Portfolio Health fixtures plus the reference population the dev-only rank oracle
  needs, each stating `data_origin = SYNTHETIC_RESEARCH_FIXTURE` and
  `not_for_empirical_validation = true`. `OG-SYNTH-0.1` to `0.4` are untouched; `0.4` is demoted
  from current and its record is not rewritten.
- **Participant:** successor **`og-participant-2026.08-v11`** minted, because three
  participant-visible files moved: `workspace.js` (the Portfolio Health card loses its status
  dot and gains the cohort identity and the small-sample sentence), `knowledge.js` (the D1.2 proxy
  qualifier withdrawn) and the generated defensibility evidence object. v10 is pinned to
  `54409af` and is **not** regenerated. **The participant experimental sequence is unchanged**,
  and this is proved structurally rather than claimed: everything in `workspace.js` before the
  Portfolio Health rendering block is **byte-identical** between v10 and v11, and `decision.js`,
  `decision-ui.js`, `deepdive.js` and both questionnaires are byte-identical.
- **Production tree:** successor manifest `code_audit/run33_production_tree.sha256`. The guard was
  turned red first and observed reporting exactly 2 added and 7 changed files and nothing else.

## 15. Remaining Run-34 and Run-35 work

**Run 34 (calibration and parameter provenance).** PH.1: an anomaly threshold and bands if any are
still wanted, and the provenance of psi, tree count, seed and the feature set. PH.2: calibration
and value assessment of the equal-feature weighting now recorded `OWNER_POLICY`, and any
percentile band. PH.3: slope magnitude calibration if any magnitude distinction is wanted — none
is authorised at v21. PH.4: match-threshold calibration if a threshold is still wanted, and the
choice of standardisation. PH.5: **the governed normalisation, transformations, weights,
missingness policy and calibration objective — all five are prerequisites of any scalar.**

**Run 35 (empirical validation and parsimony).** Empirical validation against real project
outcomes and the final parsimony decisions. Nothing in Run 33 is empirically validated, and the
frozen Run-15 threshold's own artifact records `FIELD_EMPIRICAL_VALIDATION = NOT_CLAIMED`.

---

## Per-module summary

| | PH.1 | PH.2 | PH.3 | PH.4 | PH.5 |
|---|---|---|---|---|---|
| supplied contract | canonical iForest, one forest per cohort | midrank adverse-tail percentile | OLS slope on real time | continuous nearest neighbour | truthful profile, no scalar |
| old behaviour | a forest per scored project + 4 bands | `<=` rank on cpi/spi + 4 bands | endpoint/(n−1) on list position + 4 bands | fixed 0.15 raw radius + status ladder | scalar from a retired proxy + PH.2's own output |
| current structure | governed cohort + feature schema + records | same | governed signal history | governed cohort + feature schema + records | the four constituents over one cohort |
| current implementation | `canonical_v8.isolation_forest` | `canonical_v8.portfolio_outlier` | `canonical_v8.trajectory_classifier` | `canonical_v8.cross_project_pattern` | `canonical_v8.anomaly_profile` |
| oracle | distant anomaly tops the cohort; sklearn rank comparison | `1/8, 3/8, 5/8, 7/8` exactly | slope `−1/10`, adverse `+1/10`, DETERIORATING | identical → d 0, sim 1; distant is nobody's nearest | score null, blocked |
| real-portfolio result | abstains — no governed cohort | abstains | abstains | abstains | blocked |
| small-n limitation | explicit, no predictive validity | n<3 insufficient, n<10 warned | ≥3 obs and ≥3 distinct times | n<2 insufficient | inherited from constituents |
| qualification | Category-9 eligible states only | same | per-observation | same | inherited |
| lineage | per-project source lineage | same | signal source + history version | same | every constituent, with declared non-independence |
| calibration | pending (Run 34) | pending (Run 34) | pending (Run 34) | pending (Run 34) | pending (Run 34) |
| validation | pending (Run 35) | pending (Run 35) | pending (Run 35) | pending (Run 35) | pending (Run 35) |

## Version execution proof

`code_audit/run33_simulation_version_execution_proof.csv`. The v20 package is extracted from git
object `54409af` and executed beside v21 on identical portfolio figures. **Four genuine
divergences observed by execution** — D1.3, D1.5, D1.4 and D1.1 as described above — and **one
real non-divergence**: A1.7 To-Complete Performance Index, a voting project-level module outside
this run's scope, returns a **byte-identical** result on both lines, and it really computed rather
than both lines abstaining. No divergence was invented and no non-divergence was manufactured.

## Acceptance counters

Portfolio Health targets 5/5 · canonical routes 5/5 · portfolio-present-but-unwired 0 ·
raw bypass 0 · missing-assessment bypass 0 · legacy proxy route 0 · mixed-model score comparisons
0 · mixed-period/schema cohorts 0 · portfolio-output feedback 0 · Portfolio Health votes 0 ·
project-status effect 0 · PH.5 unsupported scalar 0 · PH.5 duplicate-lineage reinforcement 0 ·
voting exactly 2 · Material Cost Variance disabled · Plithogenic disabled · Quantum archived ·
Hypersoft disabled · participant protocol changes 0 · scikit-learn not a production dependency.
