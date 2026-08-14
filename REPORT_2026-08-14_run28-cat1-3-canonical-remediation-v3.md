# Run 28: the supplied Category 1 to 3 canonical contracts, implemented in a new analytical line

## 0. THE VERSION-IDENTIFIER DISCREPANCY, AND HOW IT WAS RESOLVED

**The prompt's premise is factually wrong about this repository, and following it literally would
have corrupted the version history. It was not followed literally. The owner's INTENT was
honoured instead, and this is the departure.**

The evidence, from the file itself:

* `server/app/simulation/models.py` line 108 read `SIMULATION_VERSION = "sim-2026.08-v10"` at the
  start of this run. The platform was not at v2.
* `sim-2026.08-v3` **already exists.** The comment block at `models.py` lines 46 to 107 records
  Run 7 moving the stamp to v3, Run 10 to v4, Run 10B to v5, Run 11 to v6, Run 12 to v7, Run 14
  to v8, Run 15 to v9 and Run 16 to v10.
* The phrase "frozen at sim-2026.08-v2" is a stale label that has been carried in owner prompts
  since Run 22 and does not match the stamp.

Creating a new "v3" would have collided with Run 7's line and read as a **regression from v10**,
making results already collected under v10 ambiguous. That is precisely the harm the stamp exists
to prevent.

**Resolution.** The line frozen before this run becomes immutable historical evidence, and Run
28's analytical changes belong to a new line established with the next unused identifier in the
sequence Runs 7 through 16 built: **`sim-2026.08-v11`**. The comment convention is followed
exactly as those runs did. No historical stamp was edited. `SIMULATION_VERSION_HISTORY` now
records every stamp the layer has ever carried, so a future run that overwrote one instead of
appending is detectable, and `test_run6_known_answer.py` asserts the whole tuple and that no
identifier appears twice.

Throughout this report, "the frozen line" means sim-2026.08-v10 and everything before it.

---

## 1. PRESERVATION OF THE FROZEN LINE

The frozen line is preserved in two independent records, and **both are executable, not merely
archived**:

| record | what it is | proof |
|---|---|---|
| git commit `021d5e2` | the analytical package as it shipped at sim-2026.08-v2 | `test_run7_fix_now_defects.py` extracts every simulation source from it, imports them as `oldsim7`, **executes them**, and compares them with the current line on identical inputs. A git object cannot be mutated in place. |
| `code_audit/run20_production_freeze.sha256` | the digests of the frozen production tree | the declared-changes guard calls it IMMOVABLE and forbids regeneration; it still records the pre-cycle-1 bytes of the file cycle 1 changed. |

`test_run7_fix_now_defects.py` asserts `old_models.SIMULATION_VERSION == "sim-2026.08-v2"` and
runs 294 checks that drive the old code and the new code side by side. **Fault F1 corrupts the
immovable freeze's own recorded digest and the guard goes red (90/90 to 89/90).**

## 2. THE NEW LINE'S IDENTITY

`sim-2026.08-v11`, stamped on every result set. Superseding freeze record:

* **identifier:** `OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN28-CANONICAL-CAT1-3-V11-1`
* **manifest:** `research/freeze/RUN28_CANONICAL_CAT1_3_FREEZE_2026-08-14.json`
* **manifest sha256:** `383318621e97cb9ebb302a54d371cd5fe65789f8320a1f3d6fedc655e339e5bc`
* **companion:** `research/freeze/RUN28_CANONICAL_CAT1_3_FREEZE_2026-08-14.sha256`, stage-1
  commit `bc98bd530d1f35e367026ba82682d4db3e36327a`
* **supersedes:** `...-RUN26-COUNTS-WIRING-EMPTY-1` (named as parent, digest carried, not rewritten)
* **production surface:** 227 files, pinned at `code_audit/run28_production_tree.sha256`

This is the first freeze since the instrument was frozen that records
`simulation_package_untouched_by_this_run: false`, with the authority for that stated in the
record itself.

## 3. THE IN-SCOPE POPULATION, MECHANICALLY RECONCILED

Derived by `server/tools/build_run28_scope.py` from `code_audit/run27_98_module_remediation_matrix.csv`
and reconciled against the registry the server actually runs.

| category | rows in the Run-27 matrix | expected |
|---|---|---|
| Category 1 (A1) | **9** | 9 |
| Category 2 (A2) | **11** | 11 |
| Category 3 (A3) | **8** | 8 |
| **total** | **28** | **28** |

**It reconciles exactly. There is no discrepancy to report.** Category 1's nine are A1.1 to A1.6
and A1.9 to A1.11; A1.7 TCPI and A1.8 Variance at Completion are the two SCIENTIFIC_PASS targets
and are excluded. Category 3's eight are A3.1 to A3.3 and A3.5 to A3.9; A3.4 Material Cost
Variance is registered, disabled and excluded from the execution population. `code_audit/run28_cat1_3_scope.csv`
carries 31 rows: the 28 plus the two passes and the disabled module, so it is a complete account
of Categories 1 to 3 rather than only of the remediable part.

## 4. CANONICAL STRUCTURES ADDED

Twenty-three structure keys in `server/app/simulation/canonical_v3.py`, built as **shared
governed objects rather than one-off patches**. One schedule network serves five Category-2
methods; one time-phased baseline serves Earned Schedule and the S-curve; one reference-class
shape serves both the shrinkage forecast and reference class forecasting.

`costDriverDistributions`, `bayesianEacModel`, `kalmanStateSpaceModel`, `timePhasedBaseline`,
`expenditureBaseline`, `cpiReferenceClass`, `independentEacPair`, `scheduleNetwork`,
`milestoneForecastHistory`, `lookAheadSchedule`, `resourceProfile`, `referenceClassPopulation`,
`productionOutputRecord`, `overheadAllocationBase`, `costRiskModel`, `analogEstimate`,
`parametricCostModel`, `externalCostIndex`, plus the extended `lobStructure` and `ccpmStructure`.

Every structure must state its own provenance or it is refused. **One empirical quantile
convention is frozen for the whole line** in `canonical_v3.empirical_quantile` and every
percentile the platform reports goes through it.

## 5. MODULES NOW EXECUTING THEIR SUPPLIED CANONICAL METHOD

**Two are wired from evidence the corpus already holds and compute on real documents today:**

* **A2.7 Milestone Trend Analysis.** The baseline finish was already extracted per activity and
  stored per period and was reaching no module. `documents.py` now assembles it into a milestone
  forecast history. On the suite's own real schedule documents, three milestones are followed and
  D200's fourteen-day slip is measured **against the date it was committed to** for the first
  time on this platform.
* **A3.6 Cost Risk Analysis P80.** The comment in `documents.py` has said since the risk-register
  run that the register was served to a module with no slot for it and that reaching for it was
  "left to be authorised". It is authorised and done.

**Nineteen more execute the canonical method when a project supplies its structure:** A1.3, A1.4,
A1.5, A1.6, A1.9, A1.10, A1.11, A2.1, A2.4, A2.5, A2.6, A2.8, A2.9, A2.10, A2.11, A3.1, A3.3,
A3.5, A3.7. A2.2 and A2.3 were already canonical and gained the contract's missing output terms.

## 6. MODULES CORRECTLY NOT ESTIMABLE, AND WHAT EACH LACKS

On the real corpus today:

| module | what it lacks |
|---|---|
| A1.3 Bayesian EAC | a governed prior with a stated source and an observation model with a stated variance basis |
| A1.4 Kalman Filter SPI Smoother | a state-space record whose Q and R state where they came from |
| A1.5 ARIMA CPI Forecast | eight readings; the corpus supplies three to four |
| A1.6 Earned Schedule | a cumulative time-phased planned value curve |
| A1.9 Budget Execution Rate | an approved time-phased expenditure baseline |
| A1.10 CPI Shrinkage Forecast | a governed reference population of comparable projects |
| A1.11 Independent EAC Reconciliation Index | a second, genuinely independently prepared estimate |
| A2.1, A2.4, A2.5, A2.10, A2.11 | the project's activity network |
| A2.6 S-Curve Deviation | cumulative planned and actual series on one basis |
| A2.8 Look-Ahead Schedule Health | a governed constraint inventory |
| A2.9 Resource Loading Index | time-phased resource capacity |
| A3.1 Reference Class Forecasting | a population of completed comparable projects |
| A3.3 Labor Productivity Index | a comparable installed quantity |
| A3.5 Overhead Absorption Rate | an explicit allocation base |
| A3.7 Analogous Estimating Ratio | an identified analog with adaptation factors |
| A3.9 Inflation Adjustment Index | a named external price index — **the one item needing data from outside the platform entirely** |

**Not one of these fabricates a substitute.** Each names, in words a reader can speak, the
structure that is missing, and carries the machine code `canonical_structure_absent`.

## 7. THE APPROVED RENAMES

| id | before | after |
|---|---|---|
| A1.10 | Regression to Mean CPI | **CPI Shrinkage Forecast** |
| A1.11 | ICE Ratio | **Independent EAC Reconciliation Index** |

Applied in `p0-baseline/module_renumbering_map.csv`, the single source of truth both registries
are generated from, and propagated to `assets/js/ds_defensibility_evidence.js` by regenerating it
from that registry.

**`assets/js/taxonomy.js` is NOT renamed.** It is the participant ledger's own name source, it is
inside the frozen and checksummed participant package `og-participant-2026.08-v1`, and the study
is mid-sequence, so renaming what a participant reads would change the treatment. That is the
boundary `method_labels.py` has drawn since Run 20 and it was not crossed. **Fault F5 renames a
third module and the guard goes red.**

Carried forward for their later runs, **not applied**: ABM Governance Layer → Agent-Based
Governance Model; FAR Threshold Monitor → FAR/Agency EVMS Applicability Monitor; OMB A-11 Check →
Versioned A-11 Capital Programming Conformance Check; EVM Reporting Threshold → EVMS Reporting
Compliance Monitor; Contract Modification Frequency → Contract Modification Governance Check;
Contractor Performance Score → Contractor Performance Assessment Signal; Regret Minimization
Index → Minimax Regret Decision Rule.

## 8. A1.1 NAME RECONCILIATION

`NAMING_AUTHORITY.md` makes `p0-baseline/module_renumbering_map.csv` the source of truth both
registries are generated from. The registry records **`Monte Carlo EAC`**; the taxonomy heading
carried "Monte Carlo EAC Forecast".

**Resolution: the registry's `Monte Carlo EAC` stands, and nothing was changed.** The drift was a
heading in a prose taxonomy against the generated registry, not a disagreement between two
authorities. Prompt B's contract 1.1 is headed "Monte Carlo EAC Forecast" but supplies no rename
for it, and section 3 authorises exactly two Category 1 to 3 renames, neither of them A1.1.
Renaming on the strength of a heading would have been an unauthorised third rename.
`run17/population.py` compares the registry against the specification's own list and passes.

## 9. THE FROZEN-FILE GUARD REBASELINE, AS AN OWNER-DIRECTED CHANGE

The guard was **turned red first and observed**, before any declaration was written:

```
undeclared: ['assets/js/ds_defensibility_evidence.js',
             'p0-baseline/module_renumbering_map.csv',
             'server/app/documents.py',
             'server/app/simulation/models.py',
             'server/app/simulation/models_evm.py']
and no OTHER file has appeared in the simulation package undeclared:
            ['server/app/simulation/canonical_v3.py']
```

`server/tools/run28_production_changes.py` is the sixth manifest. **The guard's property is
unchanged and is not loosened by a word:** the union of all six manifests must still equal the
differing set exactly, and no path may appear in two. Two checks were **added**: the freeze may
only widen, never narrow, and every file whose bytes moved must be declared by Run 28 or already
declared by an earlier run.

Recorded in `code_audit/run20_anti_fossilization_register.csv` alongside three further
owner-directed contract changes: two uncited band ladders removed because the contract settles
them; three lineage declarations inverted because the modules stopped reading the facts they
named; and one campaign-integrity defect found in the campaign itself.

## 10. NON-VACUITY: SIX FAULTS, EACH PROVEN

`code_audit/run28_fault_injection.csv`. Every fault: baseline rechecked GREEN → injected →
**injection confirmed by re-reading the file from disk** → guard observed **RED, not crashed** →
restored byte for byte → baseline rechecked GREEN.

| id | fault | guard | baseline before | observed | baseline after |
|---|---|---|---|---|---|
| F1 | frozen-byte violation: the Run-20 freeze's own digest | declared production changes | GREEN 90/90 | **RED 89/90** | GREEN 90/90 |
| F2 | v3 version mismatch: stamp set to v3 | run6 known answers | GREEN 501/501 | **RED 499/501** | GREEN 501/501 |
| F3 | missing canonical input: Earned Schedule falls back | run17 scientific methods | GREEN 280/280 | **RED 279/280** | GREEN 280/280 |
| F4 | fabricated default: RCF's fixed multiplier reinstated | risk register and notices | GREEN 126/126 | **RED 119/126** | GREEN 126/126 |
| F5 | unauthorised rename of a third module | run17 scientific methods | GREEN 280/280 | **RED 279/280** | GREEN 280/280 |
| F6 | oracle-breaking mutation: normal-normal precision weighting | run17 scientific methods | GREEN 280/280 | **RED 275/280** | GREEN 280/280 |

**6/6 PROVEN NON-VACUOUS.** A crash is counted as a campaign failure, not a success; the runner
requires an anchored `RESULT:` line and none was missing.

**A defect the campaign found in itself.** F6's first run restored the file byte for byte — the
digest confirmed it — and the baseline still came back RED. CPython had cached the compiled
mutant: its cache is invalidated on mtime and size, and an injection restored inside the same
clock second changes neither. A restore that fails while every byte-level check says it succeeded
would have left a mutated analytical layer running under a green report. The compiled cache is
now dropped on **both** sides of every injection. Recorded in the register.

---

# MODULE BY MODULE

Each entry: SUPPLIED CONTRACT / CURRENT BEHAVIOUR / DATA SUPPLY / IMPLEMENTATION / ORACLE RESULT /
ABSTENTION RESULT / REMAINING WORK. **Every oracle number below is the contract's own or an
independent oracle committed by Run 17 before Run 28 existed. No expected value was read out of
production.**

## A1.1 Monte Carlo EAC Forecast
**CONTRACT** Declared variables, distributions, provenance, dependence, iteration count, seed,
P50, P80, convergence. Beta-PERT λ=4 oracle: a=80, m=100, b=140 → mean 103.333333.
**CURRENT** The PCEIF stochastic model, which the contract permits to be retained.
**SUPPLY** `costDriverDistributions` readable, with family, parameters, provenance, correlation,
iterations, seed and a convergence tolerance; convergence evidence added.
**IMPLEMENTATION** `beta_pert_moments`, `declared_cost_driver_model`, `monte_carlo_convergence`.
**ORACLE** (80 + 4·100 + 140)/6 = **103.333333** ✓ (contract's own).
**ABSTENTION** unchanged: no positive budget or index → refuses.
**REMAINING** Run 33: bands; the elicitation record behind each distribution.

## A1.2 CUSUM Anomaly Monitor
**CONTRACT** Frozen two-sided standardised tabular CUSUM, k=0.5σ, h=5σ. **Do not retune.**
Oracle: μ₀=0, σ=1, x=1 repeatedly → obs 10 Cplus=5, obs 11 Cplus=5.5.
**CURRENT/IMPLEMENTATION** Unchanged. `cusum_series` already implements exactly this.
**ORACLE** hi increments by 1−0.5=0.5 each step: obs 10 → **5.0**, obs 11 → **5.5** ✓.
**ABSTENTION** fewer than two periods → refuses.
**REMAINING** Run 33: the in-control window, the σ estimate and the ARL target. Run 15's
calibration record is preserved.

## A1.3 Bayesian EAC
**CONTRACT** posterior ∝ likelihood × prior, with parameter, prior, prior source, likelihood,
observation model, variance provenance, posterior and interval. Oracle: N(100,100), y=120,
σ²=100 → posterior variance 50, mean 110.
**CURRENT** Normal-normal with **designed constants**: prior variance (0.15·BAC)², likelihood
variance (BAC(1−CPI)/CPI)². Neither stated a source; both were the same on every project.
**SUPPLY** `bayesianEacModel`; a prior or likelihood with a blank source is refused.
**IMPLEMENTATION** `normal_normal_posterior` + 95% credible interval.
**ORACLE** variance 1/(1/100+1/100) = **50** ✓; mean 50·(100/100+120/100) = **110** ✓. Agrees
with `run17/oracle.normal_normal_posterior` to 1e-9.
**ABSTENTION** no record → NOT ESTIMABLE; the designed variances are not used in its place.
**REMAINING** Run 33: field calibration. Run 31: Category-9 qualification of the record itself.

## A1.4 Kalman Filter SPI Smoother
**CONTRACT** x_pred=x_prev; P_pred=P_prev+Q; K=P_pred/(P_pred+R); x_post=x_pred+K(z−x_pred);
P_post=(1−K)P_pred. Oracle: x0=1, P0=1, Q=0, R=1, z1=2 → P_pred=1, K=0.5, x1=1.5, P1=0.5.
**CURRENT** The recursion was right; **Q=0.01 and R=0.1 were literals with no stated origin**,
and the reported "trend" was a two-period difference that is no part of a Kalman filter.
**SUPPLY** `kalmanStateSpaceModel`; a variance with no stated source is refused.
**IMPLEMENTATION** `kalman_scalar_step`, `kalman_filter_run`, carrying every gain.
**ORACLE** **P_pred=1, K=0.5, x1=1.5, P1=0.5** ✓, matching `run17/oracle.kalman_scalar_step`
exactly.
**ABSTENTION** no record → NOT ESTIMABLE; no moving average substituted.
**REMAINING** Run 33: Q and R calibration. Run 27 proved R is estimable from repeated readings of
one period; **assembling that estimate from the corpus is corpus work this run did not do.**

## A1.5 ARIMA CPI Forecast
**CONTRACT** Explicit p, d, q; differencing rule; AR and MA coefficients; drift; identification;
estimation; stationarity; invertibility; residual diagnostics; forecast; prediction interval.
Parsimonious by AIC/AICc/BIC. **Not an AR(1) on first differences.** Minimum history →
NOT ESTIMABLE.
**CURRENT** Exactly the forbidden thing: differenced once unconditionally, regressed each
difference on the one before, clamped φ to ±0.9. No q, no selection, no intercept, no
diagnostics, no interval. Three observations sufficed.
**SUPPLY** The cost performance history `documents.py` already assembles.
**IMPLEMENTATION** `identify_arima`: d by a stated **variance-reduction rule**; (p,q) to (2,1) by
conditional least squares; **selected by AICc**, the small-sample criterion, so parsimony wins on
short histories by construction; stationarity and invertibility checked; Ljung-Box and residual
autocorrelation reported; 95% interval.
**ORACLE** constant series forecasts itself to 1e-9 ✓; a deterministic ramp differences to a
constant and forecasts the next level ✓; a series with a non-positive reading refuses ✓.
**ABSTENTION** under eight readings → NOT ESTIMABLE.
**REMAINING** the eight-reading minimum is a stated design choice a later run may revisit.

## A1.6 Earned Schedule
**CONTRACT** Find C with PV_C ≤ EV < PV_(C+1); ES = C + (EV−PV_C)/(PV_(C+1)−PV_C); SV(t)=ES−AT;
SPI(t)=ES/AT. **Actual-percent / planned-percent is not Earned Schedule.**
Oracle: PV [0,20,40,60], EV=50, AT=3 → C=2, ES=2.5, SV(t)=−0.5, SPI(t)=0.8333333333.
**CURRENT** Exactly the forbidden thing: `actualPctComplete / plannedPctComplete`, published as
"ES SPI(t)". No curve, no interpolation, no earned schedule.
**SUPPLY** `timePhasedBaseline` with baseline version and approval source.
**IMPLEMENTATION** `earned_schedule`, refusing a curve that falls over time.
**ORACLE** **ES=2.5, SV(t)=−0.5, SPI(t)=0.833** ✓, matching `run17/oracle.earned_schedule`.
**The discriminator Run 17 wrote is now satisfied in the other direction:** production tracks the
SHAPE of the PV curve, which a percent ratio structurally cannot — a front-loaded curve
[0,40,55,60] on the same EV and AT gives a different answer, and production follows it.
**ABSTENTION** no curve → NOT ESTIMABLE; no percent ratio offered.
**REMAINING** corpus: the cumulative PV curve is not extracted from any document type.

## A1.7 TCPI — SCIENTIFIC PASS, PROTECTED
Untouched. Arithmetic, bands, citations and vote byte-identical. Oracle BAC=100, EV=60, AC=70 →
40/30 = **1.3333333333** ✓; with EAC=120 → 40/50 = **0.8** ✓. Still votes.

## A1.8 Variance at Completion — SCIENTIFIC PASS, PROTECTED
Untouched. Oracle BAC=100, EAC=120 → VAC = **−20** ✓. Its lineage record continues to declare it
a transform of the same earned-value body as TCPI: no independent evidential lineage. Still votes.

## A1.9 Budget Execution Rate
**CONTRACT** A PCEIF transparent indicator, not a universal statistical method.
ExecutionRatio = AC/ExpectedSpend; ExecutionDeviation = ratio − 1. **ExpectedSpend must come from
an approved time-phased expenditure baseline; do not manufacture it from BAC × percent complete.**
No status bands supplied. Oracle: 60/50 → 1.20 and +0.20.
**CURRENT** Exactly the forbidden thing: `expected = bac * actualPctComplete/100`.
**SUPPLY** `expenditureBaseline`, read at the governed status period.
**IMPLEMENTATION** `budget_execution`, `expenditure_baseline_to_date`.
**ORACLE** **1.20** and **+0.20** ✓ (contract's own).
**ABSTENTION** no approved profile → NOT ESTIMABLE.
**REMAINING** corpus: no expenditure profile today. **The contract supplies no bands at all**, so
none is asserted.

## A1.10 CPI Shrinkage Forecast *(renamed from Regression to Mean CPI)*
**CONTRACT** **Not** an assumption that CPI regresses toward 1.0. Partial pooling toward a
governed reference-class expectation: CPI_shrunk = w·CPI_project + (1−w)·μ_reference, 0≤w≤1.
**A hard-coded 0.5 weight is not acceptable.** Oracle: 0.60·0.80 + 0.40·1.00 = 0.88.
**CURRENT** Both forbidden things at once: the weight was the literal **0.5**, and the "mean" was
the mean of **this project's own history** — a smoother, with no reference population at all.
**SUPPLY** `cpiReferenceClass` with membership basis, weight estimation method and data vintage;
**a weight declared HARD_CODED or FIXED is refused outright**; the project may not be a member of
the class it is pooled toward.
**IMPLEMENTATION** `cpi_shrinkage`, `cpi_reference_class`.
**ORACLE** **0.88** ✓ (contract's own), matching `run17/oracle.cpi_shrinkage`. Asserted over a
21-point weight grid so no fixed coefficient survives anywhere.
**ABSTENTION** no class → NOT ESTIMABLE; the project's own history is not a substitute population.
**REMAINING** Run 33: final empirical weight calibration.

## A1.11 Independent EAC Reconciliation Index *(renamed from ICE Ratio)*
**CONTRACT** Two genuinely provenance-distinct EACs. IER = Independent/Management;
Divergence = (Independent − Management)/Management. Each must preserve source, method,
assumptions, model version, responsible party, lineage. **Two transformations of the same
BAC/CPI/EV/AC vector are not independent.** Oracle: 120/100 → IER 1.20, Divergence 0.20.
**CURRENT** Exactly the forbidden thing: (BAC/CPI) ÷ (AC + (BAC − EV)). Both sides arithmetic on
one vector of four reported figures, prepared by nobody. Run 17's independence probe proved it.
**SUPPLY** `independentEacPair`. **Independence is CHECKED, not asserted:** both sides must state
all five lineage fields, and the method AND the responsible party must both differ.
**IMPLEMENTATION** `independent_eac_reconciliation`.
**ORACLE** **IER 1.20, Divergence 0.20** ✓ (contract's own).
**ABSTENTION** absent, incomplete, same method, or same party → NOT ESTIMABLE.
**REMAINING** Run 33: reconciliation bands. Corpus: no independent estimate is collected.

## A2.1 PERT Network Criticality
**CONTRACT** A real network with activity IDs, predecessors and distributions.
E[T]=(O+4M+P)/6; Var[T]=((P−O)/6)²; CriticalityIndex = trials critical / total trials.
Deterministic collapse oracle: A=3, B=2, C=1 with A→C, B→C → A and C critical, B not.
**CURRENT** Abstained unconditionally since Run 10B, correctly: no production path supplied a
network.
**SUPPLY** `scheduleNetwork` — **the supply path the abstention was waiting for.**
**IMPLEMENTATION** `pert_moments`, `pert_criticality`: every trial redraws every duration and
**recomputes the whole network**.
**ORACLE** mean (80+400+140)/6 = **103.333** ✓; variance ((140−80)/6)² = **100** ✓; the collapse
gives **A=1.0, C=1.0, B=0.0** ✓ (contract's own).
**ABSTENTION** no network → NOT ESTIMABLE; a cycle, a dangling predecessor or a duplicate
identity each refuse. **SPI is not used to reconstruct topology.**
**REMAINING** corpus: no activity network extracted.

## A2.2 Line of Balance
**CONTRACT** Activity, location, quantity, crew, **planned** and **actual** production rates,
sequence. rate = Δunits/Δtime. Oracle: locations 1,2,3 planned 1,2,3 days, actual 1,2.25,3.5 →
planned slope 1.0, actual slope 0.8, deteriorating.
**CURRENT** Canonical since Run 10B, but read only the **actual** rates, so a crew at half its
planned rate and one exactly to plan were indistinguishable.
**SUPPLY** `unit_progress` on `lobStructure`, carrying both rates.
**ORACLE** actual slope (3−1)/(3.5−1) = **0.8** against planned **1.0** ✓ (contract's own);
production reports a leading line at exactly 2.0 as not deteriorating and a following line at 1.6
against a planned 2.0 as deteriorating ✓.
**ABSTENTION** no planned rates → NOT ESTIMABLE.
**REMAINING** Run 33: no boundary for a production rate ratio is established, so none is asserted.

## A2.3 CCPM Buffer Health
**CONTRACT** BC = B0 − Bt; BCR = (B0−Bt)/B0. **Do not substitute CPM float.** Fever-chart bands
remain calibration/policy. Oracle: B0=10, Bt=6 → BC=4, BCR=0.40.
**CURRENT** Canonical since Run 10B, reporting consumption as a percentage under a three-zone
fever chart whose red line adds a third of the remaining chain — a policy constant nobody sourced.
**IMPLEMENTATION** `ccpm_buffer_consumption` alongside the existing reading.
**ORACLE** **BC=4, BCR=0.40** ✓ (contract's own). On the Run-8 case, 9 of 20 days and 0.45 ✓.
**ABSTENTION** unchanged. **REMAINING** the zone boundaries are now reported as the **policy
lines** they are and **no colour is asserted from them**.

## A2.4 Schedule Compression Index
**CONTRACT** The PCEIF remaining-duration-demand contract, **explicitly not a universal index**:
SCI = Σ baseline remaining ÷ Σ current remaining over reconciled activities at one status basis.
**CURRENT** Baseline span scaled by (1 − percent complete), divided by the same figure times SPI
— algebraically **exactly 1/SPI**. No activity consulted, nothing reconciled.
**SUPPLY** `scheduleNetwork`; only activities carrying **both** a baseline and a current remaining
duration are used, so reconciliation is a property of the data.
**ORACLE** 20 baseline against 20 current → **1.00** ✓; doubling current demand → **0.5**, which
the contract states is increasing compression pressure ✓; invariant at every scale from half a day
to two and a half years ✓.
**ABSTENTION** no reconcilable activity → NOT ESTIMABLE.
**REMAINING** Run 33: bands. Run 19's `2.4/independent-of-spi` finding is **closed**.

## A2.5 Float Consumption Rate
**CONTRACT** Float must be CPM/network derived: TF = LS−ES = LF−EF. FC = TF_base − TF_current;
FCR = FC/TF_base; FDV where history exists. Zero baseline float needs explicit handling.
**Do not fabricate float from percent complete.** Oracle: 5 → 2 gives FC=3, FCR=0.60.
**CURRENT** Two reported scalars, their ratio divided by percent complete — the forbidden step
twice over.
**SUPPLY** `scheduleNetwork`; the module runs the passes itself.
**ORACLE** independent oracle 5→2 gives 0.60 ✓; production on the contract's own CPM network,
where A begins with 5 days and the passes leave it 1, gives **FC=4, FCR=0.8** ✓.
**ABSTENTION** no network, or no baseline float on any activity → NOT ESTIMABLE. An activity that
began at zero float is **already critical with no fraction**, not divided by nothing.
**REMAINING** Run 33: bands. Corpus: no activity network.

## A2.6 S-Curve Deviation
**CONTRACT** SD_t = Actual_t − Planned_t; SDR_t = SD_t/Planned_t; ΔSD_t = SD_t − SD_(t−1).
**A single point may not be represented as a longitudinal trend.** Oracle: 0.60 planned, 0.50
actual → SD = −0.10.
**CURRENT** The mean of two quantities in different units — a percentage-point difference and a
percentage value difference — from a single snapshot, under a curve's name.
**SUPPLY** `timePhasedBaseline` plus `cumulative_actual`.
**ORACLE** **−0.10** ✓ (contract's own), matching `run17/oracle.scurve_point_deviation`.
**ABSTENTION** no series → NOT ESTIMABLE. **One point sets `longitudinal: False` and carries no
trend field at all**, so a snapshot cannot be read as a trend.
**REMAINING** Run 33: bands. Run 19's `2.6/banded-quantity-is-point-deviation` is **closed**.

## A2.7 Milestone Trend Analysis — **WIRED FROM THE CORPUS**
**CONTRACT** Stable identity; original baseline, approved baseline, report date, forecast date,
schedule version, actual date. MV = Forecast − **Baseline**; MD = Forecast_t − Forecast_(t−1).
Insufficient repeated forecasts → NOT ESTIMABLE. **Do not erase original commitment history.**
Oracle: baseline day 100, forecasts 104, 108, 111 → slips 4, 8, 11; deteriorating.
**CURRENT** The **drift term alone**, matching milestones by name across two snapshots. Variance
against the commitment was never computed and a rebaseline was invisible.
**SUPPLY** `documents.py` assembles `milestoneForecastHistory` from baseline finishes already
extracted per activity. Activities with no parseable baseline finish are left out.
**ORACLE** **variances [4, 8, 11]**, drifts [4, 3], direction deteriorating ✓ (contract's own),
matching `run17/oracle.milestone_slips_against_baseline`. **On the suite's real schedule
documents:** three milestones followed, D200's variance **14 days**, D300's **7**, D100 stable,
two deteriorating.
**ABSTENTION** one forecast only → NOT ESTIMABLE for a trend claim.
**REMAINING** Run 33: bands. Run 19's `2.7/slip-measured-against-baseline` is **closed**.

## A2.8 Look-Ahead Schedule Health
**CONTRACT** A PCEIF readiness indicator grounded in constraint removal; **PPC may not be
substituted**. ReadyFraction = (P−C)/P. Governed horizon, activity identity, constraint status and
category required. Bands remain policy. Oracle: 10 planned, 3 constrained → 0.70.
**CURRENT** Two bare counts, reporting the **complement** of the contract's quantity, with no
inventory behind them and a four-band ladder Run 4 recorded as uncited.
**SUPPLY** `lookAheadSchedule`; counts derived from the inventory.
**ORACLE** **0.70** ✓ (contract's own), matching `run17/oracle.ready_fraction`; exact across a
21-point grid.
**ABSTENTION** no inventory, an activity named twice, or a constraint status not stated →
NOT ESTIMABLE.
**REMAINING** Run 33: bands. **The uncited ladder is removed**, an owner-directed contract change.

## A2.9 Resource Loading Index
**CONTRACT** LoadRatio_t = Demand_t / AvailableCapacity_t per time bucket and resource type.
**A project-total planned-versus-actual labour ratio is not this index.** Oracle: 120/100 = 1.20.
**CURRENT** Exactly the thing the contract names as not canonical: one whole-project hours ratio,
no bucket, no resource type, **no capacity anywhere**.
**SUPPLY** `resourceProfile`.
**ORACLE** **1.20** ✓ (contract's own), matching `run17/oracle.load_ratio`, and the per-period
ratios agree with `time_phased_load` term by term.
**ABSTENTION** no profile, no capacity above zero, or negative demand → NOT ESTIMABLE.
**REMAINING** Run 33: bands. Run 19's `2.9/time-phased` is **closed**.

## A2.10 Schedule Risk Analysis P80
**CONTRACT** Stochastic network simulation with **Monte Carlo recomputation of the network for
every trial**; P80 = 0.80 empirical quantile. **A deterministic z-score uplift is not SRA P80.**
Laboratory oracle: one activity T ~ Uniform(0,10), true P80 = 8, within a tolerance **declared
before execution**.
**CURRENT** Exactly the forbidden thing: p50 = remaining/SPI, then
p80 = p50·(1 + max(0.05, 1−SPI)·0.5·**1.28**) — one closed-form multiplication, 1.28 being the
standard normal 80th percentile. No network, no distribution, no trial.
**SUPPLY** `scheduleNetwork` with a duration distribution per activity; UNIFORM and TRIANGULAR
families, the family **declared** rather than inferred.
**IMPLEMENTATION** `schedule_risk_p80`, recomputing the passes on every one of 2000 trials.
**ORACLE** **tolerance 0.5 days declared in the check name before the run**; simulated P80
converges on the true **8** ✓; P80 ≥ P50 ✓. Driven with a real seeded generator — a constant draw
is not a simulation and would have made the check vacuous.
**ABSTENTION** no network or no distribution → NOT ESTIMABLE.
**REMAINING** corpus: no network. Run 19's `2.10/simulated-distribution` is **closed**.

## A2.11 Critical Path Index
**CONTRACT** Registered name kept. Actual CPM status and margin; forward and backward pass
required. **A weighted SPI/progress calculation is not a critical-path method.**
Oracle: A=3→C=2, B=4→C=2 → finish 6; B and C critical; TF A=1, B=0, C=0.
**CURRENT** Exactly the forbidden thing: (actualPct/plannedPct + SPI)/2. Run 27 proved it a
function of those two alone across thirty-two perturbations.
**SUPPLY** `scheduleNetwork`.
**IMPLEMENTATION** `cpm_forward_backward`, `critical_path_status`.
**ORACLE** **finish 6, critical [B, C], TF {A:1, B:0, C:0}** ✓ (contract's own), agreeing with
`run17/oracle.cpm_passes` activity by activity; smallest non-critical margin **1.0** ✓.
**ABSTENTION** no valid network → NOT ESTIMABLE.
**REMAINING** corpus: no network. Run 19's `2.11/critical-path-computed` is **closed**.

## A3.1 Reference Class Forecasting
**CONTRACT** A real empirical outside view: completed comparables, IDs, inclusion and exclusion
criteria, outcome definition, normalization, historical overruns, sample size, governed
percentile. U_p = Quantile_p({r_i}); Adjusted = InsideView·(1+U_p). **No embedded fixed
multiplier.** Oracle: {0.00, 0.10, 0.20, 0.30, 0.40} → median uplift 0.20.
**CURRENT** Abstained unconditionally since Run 7, correctly: nine multipliers were literals.
**SUPPLY** `referenceClassPopulation` — **the supply path the abstention was waiting for.** The
project may not be a member of the class it is compared against.
**ORACLE** median uplift **0.20** ✓ and adjusted forecast **1200** on an inside view of 1000 ✓
(contract's own), matching `run17/oracle.quantile_of_reference_class`. Under the **frozen
right-continuous convention**, which the contract requires and which is used platform-wide.
**ABSTENTION** no class, fewer than three members, or a blank criterion → NOT ESTIMABLE.
**REMAINING** corpus: no population of completed comparables is held.

## A3.2 Contingency Burn Rate
**CONTRACT** C = (Original − Remaining)/Original; NormalizedBurn = C/ProgressFraction when
progress > 0. **No universal traffic-light bands are supplied.**
Oracle: 100, 60, 0.50 → consumed 0.40, normalized burn 0.80.
**CURRENT** Both figures correct; the four-band ladder at 1.0/1.3/1.6 was uncited, as Run 4
recorded.
**IMPLEMENTATION** `contingency_burn`. **Absent and impossible are kept apart:** progress never
reported → the consumed fraction is still reported and only the normalized burn is withheld;
progress reported **outside** the range a percentage can occupy → the whole reading is refused,
preserving Run 13's finding.
**ORACLE** **0.40** and **0.80** ✓ (contract's own), matching `run17/oracle`; monotone as
contingency is drawn down.
**REMAINING** Run 33: threshold calibration. **The ladder is removed**, an owner-directed change.

## A3.3 Labor Productivity Index
**CONTRACT** Output per labour input. ActualProductivity = EarnedOutput/ActualHours;
PlannedProductivity = PlannedOutput/PlannedHours; Index = the ratio. **Planned hours over actual
hours alone is not the canonical metric.** Oracle: 8 against 10 units/hour → 0.80.
**CURRENT** The forbidden form with a percentage in front: ((actualPct/100)·plannedHours)/
actualHours. The numerator is not an installed quantity.
**SUPPLY** `productionOutputRecord`, including the unit both quantities are counted in.
**ORACLE** actual **8.0**, planned **10.0**, index **0.80** ✓ (contract's own), matching
`run17/oracle.productivity_index`.
**ABSTENTION** no comparable output basis, or no stated unit → NOT ESTIMABLE.
**REMAINING** corpus: no installed quantity extracted. Run 19's `3.3/earned-output` is **closed**.

## A3.4 Material Cost Variance — REGISTERED, DISABLED, UNCHANGED
Not executed, not reactivated, not deleted. Registry entry and audit lineage retained exactly as
Run 16 left them. Verified on merged main.

## A3.5 Overhead Absorption Rate
**CONTRACT** PlannedRate = PlannedOH/PlannedDriver; ActualRate = ActualOH/ActualDriver; rate
variance and relative rate variance. **IndirectActual/IndirectPlan without an allocation base is
not overhead absorption.** Oracle: 100/1000 = 0.10, 120/1000 = 0.12 → variance 0.02, relative 0.20.
**CURRENT** The forbidden thing with a progress scaling: indirectActual ÷ (indirectPlan ×
percent complete). **No driver anywhere in it.**
**SUPPLY** `overheadAllocationBase`, naming the base.
**ORACLE** **0.10, 0.12, 0.02, 0.20** ✓ (contract's own), matching `run17/oracle`.
**ABSTENTION** no allocation base → NOT ESTIMABLE.
**REMAINING** corpus: no allocation base collected. Run 19's `3.5/allocation-base` is **closed**.
**LINEAGE:** the progress figure is **removed** from its declaration — Run 20 cycle 5 required it
because the module scaled by it, and it no longer does. An owner-directed change.

## A3.6 Cost Risk Analysis P80 — **WIRED FROM THE CORPUS**
**CONTRACT** TotalCost = BaseCostComponents + RealizedRiskEvents, simulated to an empirical
distribution; P80 = the 0.80 quantile under a frozen convention. **A deterministic CPI uplift is
not CRA P80.** Oracle: base 100, one Bernoulli event p=0.5 impact 20 → {100, 120} at half weight
each, mean 110, **P80 = 120** right-continuous.
**CURRENT** Exactly the forbidden thing: eac = BAC/CPI, then ×(1 + max(0.03,|1−CPI|)·0.5·1.28).
The Run-2 suite proved the register changed **nothing**: identical answer with and without it.
**SUPPLY** `documents.py` assembles `costRiskModel` from the budget and register rows carrying
**both** a probability and a cost impact. No impact distribution is invented: a register states
one figure, so the family is POINT.
**IMPLEMENTATION** `cost_risk_simulation`, 20000 trials.
**ORACLE** **P80 = 120** ✓ and mean **110** within a **1.0 tolerance declared before the run** ✓
(contract's own), matching `run17/oracle.bernoulli_cost_model` and
`empirical_quantile_right_continuous`. **The Run-2 defect is inverted:** twenty register rows now
give a different answer from one.
**ABSTENTION** no model, no base cost above zero, or a likelihood outside [0,1] → NOT ESTIMABLE.
**REMAINING** Run 19's `3.6/simulated-distribution` is **closed**.

## A3.7 Analogous Estimating Ratio
**CONTRACT** Identified analog, provenance, comparability criteria, normalization, adaptation
factors. **A preloaded overrun percentage with no identified analog is not canonical.**
Example: 100 × 1.20 × 1.10 = 132.
**CURRENT** A single scalar `analogousOverrunPct` applied to the budget. Run 20 recorded plainly
that it carried **no analog selection, no comparability criteria and no adaptation factors**, and
called that a separate structural finding out of its scope.
**SUPPLY** `analogEstimate`.
**ORACLE** **132** ✓ (contract's own), matching `run17/oracle.adapted_analog_estimate`;
order-invariant; monotone in the analog's cost.
**ABSTENTION** no identified analog, no criteria, no factors, or a factor ≤ 0 → NOT ESTIMABLE.
**Every historical P0B defect is now unreachable**, because the scalar they rested on is not an
input the module has.
**REMAINING** corpus: no analog record collected. Run 19's `3.7/analog-provenance` is **closed**.

## A3.8 Parametric Cost Index — DISABLED, LABORATORY ONLY
**CONTRACT** Keep operationally disabled. Build only the canonical structure and laboratory
implementation. Cost = β₀ + β₁x₁ + … **Comparing EAC formulas is not parametric estimating.**
Even if the laboratory passes, remain disabled and non-voting. Oracle: 10 + 2·4 + 3·5 = 33.
**CURRENT** Exactly the forbidden thing: (BAC/CPI) ÷ (AC + BAC − EV).
**IMPLEMENTATION** `canonical_v3.parametric_cost`, requiring drivers with units, fitted
coefficients, a coefficient source, a fit dataset and a model version. **The forbidden arithmetic
is REMOVED from the production function** rather than left behind a gate.
**ORACLE** **33** ✓ (contract's own). Intercept, coefficients, units and design-row length all
reported. **Run 14's fidelity finding is inverted:** the implementation moves with the driver
quantity, which the shipped code could not. An omitted driver is **refused**, never valued at zero.
**STATUS** **`A3.8 in DISABLED_MODULES` and not in `CORE_VOTING_MODULES`, asserted on merged
main. No production path reaches the laboratory implementation.**
**REMAINING** owner: the activation decision. Run 33: coefficient fitting on a real dataset.

## A3.9 Inflation Adjustment Index
**CONTRACT** A governed external index: named series, authority, geography, scope, base period,
observation period, vintage, cost exposure. Factor = Index_current/Index_base.
**A baseline-to-current project material price ratio is not an external index.** **Do not
fabricate or hard-code an external market index.** Oracle: 200 → 220 gives 1.10; on 100, adjusted
110.
**CURRENT** Exactly the forbidden thing, floored at zero so **deflation was invisible**: the
project's own price movement against its own progress-scaled baseline.
**SUPPLY** `externalCostIndex`; **all seven provenance fields must be stated or it is refused.**
**IMPLEMENTATION** `inflation_adjustment`. **No index level appears anywhere in production code**;
both come off the supplied structure, and changing them changes the answer.
**ORACLE** factor **1.10**, adjusted **110** ✓ (contract's own), matching
`run17/oracle.escalation_factor`. **A falling index gives a factor below one and a negative
escalation amount** — which the floored proxy structurally could not show.
**ABSTENTION** no index, or a missing authority or geography → NOT ESTIMABLE.
**REMAINING** external: no official index series is held. **This is the one item that needs data
from outside the platform entirely.** Run 19's `3.9/external-index` and `3.9/deflation-visible`
are both **closed**.

---

# 11. CALIBRATION, AND WHAT IS NOT ASSERTED

**No band was invented anywhere in this run.** Where the v3 quantity is not the quantity a
module's old ladder was drawn over, the module reports the figure and asserts **no colour**:
`status_color` None, `band_asserted` False, `calibration_pending` True, with one sentence saying
why. `registry.record()` routes such a row to `computed`, not to `abstained` — the method ran and
only the colour is withheld — and it cannot reach status fusion, which reads only the two voting
modules.

Two uncited ladders were **removed**: A2.8's constraint-rate ladder and A3.2's burn-against-
progress ladder, both of which Run 4 recorded as unsourced and the contract now settles.
A2.3's fever-chart lines are reported as **policy lines** with no colour drawn from them.

Handed to **Run 33**: Monte Carlo distribution parameters; Bayesian priors and variances; Kalman
Q and R; Budget Execution boundaries; the CPI shrinkage weight; EAC reconciliation bands; CCPM
fever bands; Schedule Compression bands; float bands; S-curve bands; look-ahead bands; resource
loading bands; contingency burn bands; A3.8 coefficient fitting.

# 12. LINEAGE, AND WHAT WAS NOT CLOSED

**The Category-9 gate is NOT implemented here and no LINEAGE finding is closed.** Production
continues to disclose its own deviation: `signal_package.py` records
`SIGNAL_QUALIFICATION = "unqualified"` and `CATEGORY_9_DEVIATION`. That gate is **Run 31**.

What Run 28 did do is keep the provenance that gate will need **true**. Six declarations were
rewritten because the facts they named are no longer the facts those modules read, and eleven new
evidence bodies were introduced. In each case the correction runs in the direction the evidence
runs, and each guard was **inverted rather than deleted**, so a regression turns it red:

* **A1.3** left the earned-value body for a Bayesian model record. Run 20 cycle 12's control
  required it to be *dependent* on the earned value; that is now false, and the control asserts
  independence **plus** that it can still find a dependence where one exists.
* **A1.4** left the earned-value and reporting-history bodies for a state-space record.
* **A1.11** was correctly declared SAME_SOURCE_TRANSFORM — another way of saying no independent
  estimate existed. It is now INDEPENDENT because that is a property the module **enforces at run
  time**.
* **A3.5** dropped the progress figure; **A3.9** dropped the project's own material costs;
  **A3.6** dropped the cost index and kept the budget, because production genuinely assembles the
  base cost from it.

**A structural consequence, reported rather than smoothed over:** removing progress from A3.5
removed the only bridge between the earned-value body and the indirect-cost ledger.
`test_run20_primitive_lineage.py` sweeps the whole table, confirms **no record now bridges them**,
and drives its bridging control from a bridge built out of those two bodies' **own facts** — with
the construction disclosed in the file.

**RECORDED DISTINCTION: METHOD and STRUCTURE corrected in Run 28; LINEAGE qualification pending
Run 31.**

# 13. SCOPE DISCIPLINE

Not touched, and verified not touched: `PKG-ORPHANFIELDS` (Categories 4–5, Run 29); Category 7
methods; Category 8 regulatory work; the Category 9 gate (Run 31); Category 10 optimization;
Portfolio Health; B2.9 Quantum Probability (Run 30); A3.4 Material Cost Variance, which remains
registered and disabled; **A5.8, which shares primitives with A2.11 and was left alone** — it
still reads the progress figure and still refuses an impossible one, and the suites say so by
name. Voting is exactly two. Participant protocol unchanged.

# 14. WHAT COULD NOT BE COMPLETED, WITH EVIDENCE

1. **Twenty of the twenty-eight modules abstain on the real corpus.** The structures they need
   are not in the document corpus, exactly as Run 27 established. This is the contract's own
   required outcome — "if real evidence is absent on a particular project, the method must
   truthfully return Not Estimable" — but it should be read as what it is: the methods are
   correct and mostly **not yet fed**. Section 6 lists what each lacks.
2. **A1.4's measurement variance was not assembled from the corpus.** Run 27 proved R is estimable
   from repeated readings of one period. Implementing that extraction is corpus work this run did
   not do, and Q — the process variance of the true schedule index — cannot be estimated from this
   corpus without a modelling assumption I was not willing to make silently.
3. **A3.9 needs data from outside the platform.** No official index series is held and none can be
   fabricated. Live web access is unavailable in this environment and is not treated as a blocker.
4. **No browser drive was run.** This run changed no rendered surface; the two files under
   `assets/` that moved are a regenerated evidence object and nothing else.
5. **The frontend taxonomy was deliberately not renamed**, so a participant reading the ledger
   still sees "Regression to Mean CPI" and "ICE Ratio". That is the frozen-package boundary and
   is an owner decision, recorded here so it is visible rather than assumed.

# 15. VERIFICATION SUMMARY

| item | result |
|---|---|
| frozen line preserved and **executable** | ✓ `oldsim7` extracted from `021d5e2`, imported, executed, compared |
| new line identity | ✓ `sim-2026.08-v11`, history asserted as a whole, no identifier twice |
| population reconciled | ✓ **28 = 9 + 11 + 8**, no discrepancy |
| approved renames applied | ✓ 2, in the registry map |
| unauthorized rename | ✓ none; F5 proves the guard catches one |
| voting | ✓ exactly 2: A1.7, A1.8 |
| Material Cost Variance | ✓ registered, disabled, not executed |
| A3.8 | ✓ disabled, non-voting, laboratory only |
| participant protocol | ✓ unchanged |
| unsupported bands introduced | ✓ none; two removed |
| Category-9 findings closed | ✓ none |
| non-vacuity | ✓ **6/6 faults PROVEN**, each confirmed applied and each restored |

# 15a. THE COMPLETE SUITE ON MERGED MAIN

**`server/run_all_suites.sh` on merged `main`: 127 suites, `10730/10730`, ALL SUITES GREEN.**
Fresh SQLite per test file, `PYTHONIOENCODING=utf-8`, interpreter CPython 3.11.15 confirmed real.
This is the merged-main total and the only one quoted. The pre-merge branch total was identical.

**Merged-main commit: `a74efe2`** (merge), with the guard re-pointing and the register row that
followed it at **`bc98bd5`**, which is the commit the freeze names as its stage-1 parent.

**One thing found after the merge, and reported rather than smoothed over.** Two scope guards —
`test_run6_known_answer.py` and `test_run8_retest_classify_27.py` — had been GREEN through every
pre-commit full-suite run of this work while `canonical_v3.py`, a whole new production module,
sat in the working tree undeclared. They went red the moment it was committed. Both diff against
a pinned baseline with `git diff --name-only`, which does not report untracked files. What caught
the file before it was committed is the byte-level guard, which walks
`server/app/simulation/*.py` from the filesystem. Both scope guards are now re-pointed with Run
28's scope, and **the blind spot is recorded OPEN in the anti-fossilization register** for a later
run to close by giving them the same filesystem walk.

# 16. RUN-29 HANDOFF

1. **`PKG-ORPHANFIELDS`** (Categories 4–5) — Run 27's cheap P0 work, deliberately untouched.
2. **`canonical_v3.py` is available to Categories 4–10.** `parse_schedule_network`,
   `cpm_forward_backward`, `empirical_quantile` and the structure-contract pattern are general.
   **A5.8 shares primitives with A2.11 and was left alone; it is Run 29's.**
3. **The calibration-pending contract exists** (`models.calibration_pending`). Any later run
   finding an uncalibrated band can use it rather than inventing a threshold.
4. **The declared-changes guard now has six manifests.** Run 29 writes a seventh; it may not
   declare a path an earlier manifest declares.
5. **The freeze chain is** RUN22 → POSTRUN22-UI-1 → RUN24 → RUN25 → RUN26 → **RUN28**.
6. **Approved future renames** are listed in section 7 and in `T6_HANDOFF.md`.
7. **The version-stamp premise in owner prompts is stale.** The line is at `sim-2026.08-v11`.
   Run 29 should read `SIMULATION_VERSION_HISTORY` rather than the prompt.
