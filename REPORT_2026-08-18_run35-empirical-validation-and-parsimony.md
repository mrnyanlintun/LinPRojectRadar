# Run 35 — Empirical validation, validation eligibility, and final operational/parsimony decisions

**Date:** 2026-08-18. **Model:** Opus.
**Exact starting commit:** `584ccf9882c3c48fba85055ab3ef63ae9f89f890` (`HEAD == main == origin/main`, tree clean).
**Simulation line at start and at finish:** `sim-2026.08-v22`.
**Participant package:** `og-participant-2026.08-v11`. **Synthetic package:** `OG-SYNTH-0.6`.
**Voting at start and at finish:** exactly 2 — A1.7 TCPI and A1.8 VAC, under the governed overall
label *Cost Recovery Status*.

---

## 1. What this run found, stated plainly

**No scientific target in this instrument is empirically validated against an independent field
outcome, and none could be, because no such outcome exists in or reachable from this
repository.** `EMPIRICALLY_VALIDATABLE_NOW = 0`.

That is not a methodological failure and it is not reported as one. It is the correct reading of
the evidence available: the controlled corpus is a supervisory corpus, not an outcome corpus; no
participant responses exist; and synthetic laboratory evidence is not field evidence.

Three targets carry a **partial** reference standard — a published definitional or regulatory
identity that fixes the numeric quantity but says nothing about the band, the status, or how often
the reading is right. Those three were scored against an independent implementation of the
published identity in exact rational arithmetic. **One passed exactly and two failed the
predeclared exact-equality rule for a reason that is measured, understood and stated below.**

No percentage pass rate across incomparable methods appears in this report, and none should be
derived from it.

---

## 2. The 100-target mechanical scope

Derived by `server/tools/build_run35_eligibility.py` from the live registry, never transcribed.

| Population | Count | Derivation |
|---|---|---|
| Registry rows (`p0-baseline/module_renumbering_map.csv`, RETIRED removed) | **101** | live CSV |
| Registered project modules (groups A, B, C) | **96** | 53 + 36 + 7 |
| Portfolio Health targets (group D) | **5** | D1.1–D1.5 |
| Project **scientific** targets | **95** | 96 minus A3.4 Material Cost Variance (registered, disabled evidence-under-review) |
| **Total scientific targets** | **100** | 95 + 5 |
| `registry.VALIDATED` (computed project modules) | **95** | 96 minus A4.1, supplied not computed |

**The two counts of 95 exclude different things and are not collapsed.** `VALIDATED` = 95 excludes
A4.1 Document Risk Score, which is a *supplied* scalar and is nonetheless a scientific target. The
scientific project population = 95 excludes A3.4, which is *computed-capable* but disabled. The
scope artifact therefore carries **101 rows**: the 100 scientific targets plus A3.4 with
`scientific_target = NO`, so the two populations cannot be merged by reading the file.

Acceptance: scientific rows 100; unique scientific IDs 100; missing 0; duplicates 0; voting 2.
Artifact: `code_audit/run35_scientific_target_scope.csv`.

---

## 3. The empirical-validation taxonomy, frozen before testing

`research/methodology/run35_empirical_validation_protocol.md`, committed **alone** at `025eeb3`,
before any generator that scores anything existed. Seven classes, closed vocabulary, with an
explicit precedence `E → D → A → B → G → C → F`, plus the independence rules, the metric-by-output-
type table, and a four-value verdict vocabulary in which `NOT_APPLICABLE` is a distinct literal
that can never read as a pass.

The target-to-metric contract, `code_audit/run35_validation_metric_contract.csv`, was committed at
`bd5b15f`/`2c7050e` — still before the scoring generator existed. The scoring generator **reads**
that contract from disk rather than restating it, and guard `run35.fault09` proves by AST
inspection that its `score()` function contains no numeric comparison at all: the verdict is
`got == ref` on two exact rationals, so there is no threshold in the scorer to have chosen after
the fact.

---

## 4. Reference-standard independence

Every proposed reference is recorded in `code_audit/run35_reference_standard_independence.csv`
with source, period, reference variable, method inputs, availability to the method, derivation
from the method, lineage, the six invalidity tests answered individually, and the independence
judgment.

The deciding rule is the **algebraic-relatedness rule**: for earned-value quantities, independent
means *not derivable from the method's own inputs by the method's own definition*. A
differently-named quantity that is an algebraic rearrangement of the inputs is not independent.
Applying it:

- PMI's TCPI identity, PMI's VAC identity and the OSHA incidence-rate identity are **independently
  authored** — external, published, pre-existing, not derived from this platform.
- Their arguments are the method's own inputs. They therefore establish that the shipped
  implementation computes the quantity the published standard defines, and **nothing about field
  performance**.
- All three are admitted for `PARTIAL_REFERENCE_STANDARD` scoring of the scalar component only,
  and all three carry `supports_class_A_empirical_claim = NO`.

**No qualified reference, no empirical validation score.** 97 targets have no admitted reference
and are scored nowhere.

---

## 5. Validation-eligibility distribution (primary class, protocol precedence)

| Class | Count |
|---|---|
| A `EMPIRICALLY_VALIDATABLE_NOW` | **0** |
| B `PARTIAL_REFERENCE_STANDARD` | **3** |
| C `SYNTHETIC_VALIDATION_ONLY` | **0** (primary) |
| D `CALIBRATION_GAP_BLOCKS_VALIDATION` | **1** |
| E `STRUCTURE_OR_DATA_ABSENT` | **96** |
| F `NO_INDEPENDENT_REFERENCE_STANDARD` | **0** (primary) |
| G `EMPIRICAL_VALIDATION_PENDING_STUDY` | **0** (primary) |

**Why E dominates, stated honestly.** The precedence was fixed in the committed protocol before
any of this was measured, and it puts structure absence first because a module that produces no
output has nothing to validate. Executing the production entry point on the controlled corpus, 6
of 95 project targets compute at all (A1.1, A1.7, A1.8, A6.1, A6.2, A6.3); A4.1 is supplied, not
computed; all 5 Portfolio Health targets abstain because the controlled portfolio supplies no
governed cohort. Everything else abstains for want of its governed structure.

**Secondary truths are recorded, not destroyed by precedence.** The result artifact carries a
`secondary_classes_also_true` column. All 5 Portfolio Health rows carry
`EMPIRICAL_VALIDATION_PENDING_STUDY`, exactly as Run 34 left them. All 100 rows carry
`SYNTHETIC_VALIDATION_ONLY` as a co-true secondary class, on the mechanical basis that every
module identity is asserted by at least one executable suite — which is coverage of identity, not
proof of a canonical known-answer oracle for each, and is stated that way.

---

## 6. Actual empirical validation results

Three targets scored. All arithmetic exact (`fractions.Fraction`), no float decided any verdict.

| Module | Reference | Predeclared rule | Measured | Verdict |
|---|---|---|---|---|
| A1.7 TCPI | REF-PMI-TCPI, `(BAC−EV)/(BAC−AC)` | exact equality, tolerance 0 | production `1071/1000`; identity `15/14`; **exact difference `−3/7000`** | **FAIL** |
| A1.8 VAC | REF-PMI-VAC, `BAC − BAC/CPI` | exact equality, tolerance 0 | production `−100110`; identity `−91000000/909`; **exact difference `+10/909`** | **FAIL** |
| A6.2 Safety Performance | REF-OSHA-INCIDENCE, `cases × 200000 / hours` | exact equality, tolerance 0 | production `3`; identity `3`; difference `0` | **PASS** |

**The two FAILs are a real finding and are not explained away.** Their cause was measured, not
assumed: `models_evm.run_tcpi` computes `tcpi = _round3(remaining_work / remaining_budget)` and
then compares the **rounded** value against the band boundaries; `run_vac` rounds to whole
dollars. The emitted scalar is therefore a rounded rendering of the identity rather than the
identity, and for A1.7 the rounding happens *before* the Green/Amber/Red decision, so a value of
1.1004 is banded as though it were 1.100.

Run 35 does **not** change this. The rounding is the frozen JavaScript-parity behaviour that the
numeric-validation history of this platform rests on, and altering it would change
participant-visible output during a frozen participant sequence. It is carried to Run 36 as an
open finding, with the residual stated exactly.

**What these three results do not establish:** how often any band is right; false-positive or
false-negative performance; any field-outcome relationship. There is no labelled outcome
population, so no confusion matrix, sensitivity or specificity is admissible for any target.
`synthetic_as_empirical_claims = 0`.

Remaining 97 targets: `NOT_APPLICABLE`, each with an explicit
`empirical_metric_applicable = NO`, `reference_standard_id = NONE`, and a limitation sentence that
states in terms that `NOT_APPLICABLE` is the correct final state and **is not a pass**.

---

## 7. Voting-module validation

A1.7 and A1.8 are the only two voters and remain the only two. Their partial plain-EVM reference
standard was exercised as far as it genuinely goes (section 6) and **was not generalised to the
other 98 targets**. No voter was added; A6.2's exact PASS against the OSHA identity confers no
vote and its disposition is advisory. Required final voting count 2; measured 2, both in the live
`registry.CORE_VOTING_MODULES` and in the 100-row disposition artifact.

---

## 8. Portfolio Health

Run-34 conclusions carried forward unchanged, and re-read from the Run-34 closure artifact rather
than from prose: PH.1 tree count 100 with tree-count calibration `UNRESOLVED_NO_OPERATIONAL_
CONSEQUENCE` and the 0.576 threshold synthetic, schema- and cohort-bound and unapplied; PH.2
composite NONE without governed weights; PH.3 minimum 3 observations and actual reporting times;
PH.4 continuous distance only with the 0.15 radius retired; PH.5 score null under
`PARAMETER_PROVENANCE_BLOCKED`.

Run-34 layer 5 was **PENDING ×5** and remains **PENDING ×5**. No Run-35 evidence changed it: the
controlled portfolio supplies no governed cohort, so all five abstain, and `OG-SYNTH-0.6` is a
laboratory package that cannot make a field claim. All five verdicts are `NOT_APPLICABLE`. Seven
UNSUPPORTED Portfolio Health parameters remain, and `canonical_v8` refuses to apply any of them —
measured, not assumed, from the live `applied_operationally` flag.

---

## 9. Unresolved calibration and provenance

`code_audit/run35_unresolved_calibration_inventory.csv`, **96 rows**: 89 project targets each
carrying one UNSUPPORTED band ladder, plus the 7 UNSUPPORTED Portfolio Health parameters from the
live `canonical_v8` register (which replaces, rather than duplicates, the coarse per-module row).

**Applied = 1. Not reached = 95.** The single applied unresolved parameter is **A1.1 Monte Carlo
EAC Forecast's four-band ladder**, which emits a status colour on the governed corpus. That is why
A1.1 is the one `CALIBRATION_GAP_BLOCKS_VALIDATION` target: a measured error would be attributable
to the uncalibrated ladder rather than to the method. **No parameter was tuned in Run 35.**

**A second A1.1 finding, disclosed rather than repaired.** `canonical_v3` declares A1.1's governed
structure as `costDriverDistributions`. That key appears **nowhere else in the repository**: no
canonical function reads it, no production route requires it, and the shipped runner computes from
plain `cpi`, `spi`, `bac` and `docRiskScore` instead. The governed intake accepts the key — it is
in `governed_structure_keys()` — so an owner can supply it and it will silently have no effect.
This is the "declared canonical structure with no implementation and no consumer" defect, and it
is handed to Run 36 rather than fixed here, because implementing A1.1's canonical method is a
Run-28-scale workstream and changing its routing would change participant-visible output.

**A third finding, also disclosed.** `method_labels.TRUTHFUL_METHOD_LABELS` still describes B4.4
What-If Scenario Matrix as a proxy that "computes four completion forecasts by perturbing the cost
index", and B1.2 similarly. Run 32 repointed B4.4 onto `models_cat10` and the canonical v7 layer
and withdrew its proxy qualifier, but left the method label. Measured through `__wrapped__`, B4.4's
production route is `app.simulation.models_cat10.run_B4_4`. The label is therefore stale on an
exported surface. Run 35 does not edit it: altering a truthful method label is a rename, and
renames require owner authority. Carried to Run 36.

---

## 10. Parsimony

`code_audit/run35_parsimony_reconciliation.csv`, 100 rows, built from **pairwise** primitive-source
lineage only — the primitive keys each module's production path actually reads, captured by
instrumenting the signal-input dictionary during execution. No connected component, no transitive
closure.

| Overlap type | Count |
|---|---|
| NONE | 77 |
| SHARED_GOVERNED_STRUCTURE (same primitive source object) | 19 |
| IDENTICAL_PRIMITIVE_SOURCE_SET | 3 |
| PRIMITIVE_SOURCE_SUBSET | 1 |

**22 targets do not add a distinct analytical function** on the evidence available: they transform
the same primitive source object as another target under a different label. Duplicate evidence
receives no additional authority for being transformed twice — none of the 22 votes, and the 19
sharing a governed structure share it because the programme deliberately supplies **one**
alternatives-and-criteria object to several methods rather than parallel copies.

Lineage states across the 100: `LINEAGE_UNRESOLVED` 77, `LINEAGE_ESTABLISHED_DEPENDENT` 8,
`LINEAGE_NOT_APPLICABLE` 8, `LINEAGE_ESTABLISHED_INDEPENDENT` 7. **Unknown lineage is not
independent lineage:** every parsimony row carries the live `independence_established()` answer,
and guard `run35.fault22` fails if any row claims independence from a non-independent state.

Parsimony governs current operational exposure only. **Deleted modules: 0.** Nothing was removed
from scientific history.

---

## 11. Final operational disposition

`code_audit/run35_operational_disposition.csv`, exactly 100 rows, one disposition each from the
seven-value controlled vocabulary, every row carrying validation state, canonical-method state,
data availability, calibration/provenance state, lineage, routing, voting, rationale and a Run-36
action. No eighth value was invented.

| Disposition | Count | Who |
|---|---|---|
| `KEEP_OPERATIONAL` | **2** | A1.7 TCPI, A1.8 VAC |
| `KEEP_ADVISORY` | **2** | A1.1 Monte Carlo EAC, A6.2 Safety Performance |
| `KEEP_ABSTENTION_CAPABLE` | **87** | canonical methods whose governed structure is absent |
| `RESEARCH_ONLY` | **1** | A4.1 Document Risk Score (supplied scalar, precision/recall unmeasured) |
| `DISABLED_INSUFFICIENT_INPUT` | **5** | A3.8, B4.1, B4.2, B4.5, B4.6 |
| `DISABLED_INSUFFICIENT_PROVENANCE` | **2** | B2.7 Plithogenic, B2.20 Hypersoft (no frozen operator formulation exists) |
| `ARCHIVED` | **1** | B2.9 Quantum Probability |

Boundaries preserved exactly: MCV A3.4 stays disabled and outside the 100; Plithogenic, Hypersoft
disabled; Quantum archived; the four Category-10 concept-only modules stay disabled; archived
history stays reconstructable. **No module was activated to obtain a score.** Category 9 stays a
gate and metadata — raw bypass 0 and missing-assessment bypass 0 measured across all 40 gated
routes by execution. Category 10 exercises no approval authority and creates no project-condition
evidence, measured on every B4.x row including abstaining ones.

---

## 12. Non-vacuity / fault campaign

30 failure modes, each injected into a real file, each confirmed applied by re-reading the bytes
from disk, each expected to turn **one named guard** red for its own reason, each restored
byte-for-byte and re-verified green. `__pycache__` dropped on both sides of every injection.

- **faults declared 30 — applied 30 — intended RED 30 — restored GREEN 30 — NOT_APPLIED 0 — crashes accepted as RED 0.**

Guard suite: `server/tools/test_run35_validation_governance.py`, 30 named checks, picked up by
`server/run_all_suites.sh` (which globs `tools/test_*.py`), so every oracle is enforced.
Campaign runner: `server/tools/run35_fault_campaign.py`. Results:
`code_audit/run35_fault_injection_results.csv`.

The campaign's first pass reached **29/30**: fault 30 (a report count disagreeing with the
artifacts) had no subject, because no Run-35 report existed yet. It was re-run against this
committed report and then landed.

---

## 13. Simulation and package decisions

**`sim-2026.08-v22` STANDS. No version bump.** Decided from executed behaviour, not from which
files changed: Run 35 added validation evidence, eligibility classes, dispositions, artifacts and
guards, and changed **no** routing, **no** abstention, **no** module operational state, **no** gate
behaviour, **no** parameter application and **no** participant-visible analytical output. Not one
line of `server/app/` was modified. The three findings in section 9 that would have changed
executed behaviour were deliberately **not** acted on, and are recorded as Run-36 work.

The **production manifest is byte-identical** to the one Run 34 pinned — regenerating
`code_audit/run34_production_tree.sha256` produced no change — and that is the mechanical proof
that no production byte moved. The **authority** manifest was repointed onto
`code_audit/run35_authority_tree.sha256` because the Run-35 protocol is a scientific authority
document and belongs inside the walked authority tree; the Run-34 and Run-22 authority manifests
are kept addressable and were not rewritten.

**Participant package `og-participant-2026.08-v11` STANDS.** No participant-facing byte changed;
the controlled participant sequence is unchanged.

**Synthetic package `OG-SYNTH-0.6` STANDS.** No governed synthetic byte changed. No new validation
fixture was required, because the three reference standards are published identities implemented
in the scoring generator itself, not fixture data — so nothing was added to the synthetic
programme and nothing was silently mutated.

---

## 14. The study distinction, preserved

The controlled praxis study measures influence on professional judgment. AI agreement is not
automatically correctness, and this run did not rewrite the study into an accuracy experiment. The
six quantities stay distinct: analytical-method correctness; reference-supported analytical
result; participant agreement with AI; participant revision after AI; whether the revision was
reference-supported; whether the revision was documented and auditable. **Items 3–6 require
participant outcomes, none exist in this repository, and none were fabricated.** Every Run-35 row
is confined to items 1 and 2. This run qualifies the analytical instrument for later study use and
makes no participant claim.

---

## 15. Exact limitations carried to Run 36

1. **Nothing is empirically field-validated.** 0 targets are `EMPIRICALLY_VALIDATABLE_NOW`; 3
   carry a partial published-identity reference standard for the scalar only; 97 have no reference
   standard at all. No band, in any module, has measured false-positive or false-negative
   performance.
2. **A1.7 and A1.8 fail exact equality against their own published identities** by `−3/7000` and
   `+10/909`, because the production path rounds before emitting and, for A1.7, before banding.
   Unrepaired by design; Run 36 must decide whether JavaScript-parity rounding or identity
   fidelity governs, and whether banding may read a rounded value.
3. **A1.1 declares a governed structure that nothing implements or consumes**
   (`costDriverDistributions`), computes from plain scalars instead, and applies the only
   unresolved parameter that reaches an output anywhere in the instrument.
4. **B4.4 and B1.2 carry stale truthful-method labels** describing proxies that Run 32 removed.
   Correcting them is a rename and needs owner authority.
5. **96 of 100 targets abstain or produce nothing on the controlled corpus.** The instrument's
   governed structures are supplied by an intake that works but by a corpus that does not carry
   them.
6. **95 unresolved parameters remain unreached and 1 applied.** No calibration set exists; none was
   invented.
7. **Portfolio Health empirical validation remains PENDING ×5.**
8. **Lineage is unresolved for 77 of 100 targets.** Unknown lineage is not independent lineage and
   was not treated as such.

None of these blocks Run 36; each is a Run-36 input.


---

## 16. POST-VALIDATION VOTER CORRECTION (closure, 2026-08-19)

Run 35 identified canonical-reference failures **in the only two modules that vote on project
status**, and this closure repaired them. The order matters and the git history shows it: the
protocol was frozen first, the validation was scored second, and the implementation was corrected
third. **The reference standard was never altered to make the implementation pass.**

- **Both failures arose from premature rounding behaviour.** A presentation rounding was applied
  to the analytical value, so the emitted quantity was a rounded rendering of the published
  identity rather than the identity.
- **A1.7 additionally used the rounded value for band classification.** That is the serious half.
  The pre-change measurement (`code_audit/run35_voter_prechange_measurement.json`, taken before a
  line was edited and pinned to its own commit) *searched* for governed inputs on which the
  rounded and the full-precision index fall on opposite sides of a band edge, and found
  **twenty-eight**. On every one of them v22 answered **Green** where the full-precision index is
  above 1.00 and implies **Amber**. Premature rounding therefore decided a **status**, not merely
  a displayed number, on a voting module.
- **A1.8 had no status defect and none is claimed.** Its band already read the full-precision
  percentage. What it had was the first consequence only: the emitted analytical field was a
  whole-dollar presentation value.
- **The implementation was corrected after Run-35 validation.** `tcpi` and `vac` are now the
  canonical values at the precision the application already uses, the bands derive from them, and
  `tcpi_display`, `vac_display` and `vac_pct_display` carry presentation numbers that nothing
  analytical reads. No new decimal precision was introduced anywhere.
- **v22 remains preserved as the failing predecessor**, pinned at
  `034cf03be257f4582bc1a856262c56ea11bb4558`. The boundary proof asserts that object still stamps
  itself v22 and still carries the defective line, so no predecessor was regenerated.
- **v23 is the corrected successor**, proved by executing both packages:
  `code_audit/run35_v22_v23_voter_execution_proof.csv`.
- **The original empirical findings remain in the historical artifacts unchanged.** The FAIL rows
  in `code_audit/run35_empirical_validation_results.csv` record what v22 did and are not rewritten.

| Module | v22 result (Run 35) | v23 result (closure) |
|---|---|---|
| A1.7 TCPI | `1071/1000`, discrepancy **−3/7000**, **FAIL** | `1.0714285714285714` = the identity in the application's own arithmetic, **PASS** |
| A1.7 band boundary | Green on 28 governed inputs where the index exceeds 1.00 | Amber on all 28 |
| A1.8 VAC | `−100110`, discrepancy **+10/909**, **FAIL** | `−100110.01100110007` = the identity, **PASS** |
| A6.2 Safety | PASS exactly | **unchanged**, PASS exactly |

The acceptance rule applied at v23 is the one the owner's Decision 1 bounds: equality with the
published identity **evaluated in the arithmetic the application already uses**, tolerance zero.
Against an infinitely precise rational a residue of order 1e-17 relative (A1.7) and 1e-11 absolute
(A1.8) remains; that is IEEE-754 double representation, not premature rounding, and no decimal
precision was invented to remove it.

## 17. STALE METHOD-LABEL CORRECTION (closure, 2026-08-19)

Two modules carried truthful-method labels describing proxies that earlier runs had already
removed, so the labels had become false **in the opposite direction** — advertising a weakness the
code does not have, which is the error `method_labels.py` exists to prevent.

| Module | Previous stale label | Canonical existing name | Source of authority |
|---|---|---|---|
| B1.2 | "Fixed-weight signal band tally" — "tallies the bands of the assembled signals under four fixed weights" | **Weighted Voting** | `p0-baseline/module_renumbering_map.csv`, the registry authority the client taxonomy is generated from |
| B4.4 | "Earned value completion forecast range" — "computes four completion forecasts by perturbing the cost index" | **What-If Scenario Matrix** | the same registry authority |

**No arbitrary new naming.** Both names already existed in the registry authority; neither module
ID, algorithm, category, voting state, lineage nor operational disposition changed
(`implementation_changed = NO`, measured by resolving the production dispatch entry through
`__wrapped__`: B1.2 → `models_gov.run_weighted_voting` into `canonical_v5.weighted_voting` with a
governed weight policy, weight provenance and an eligibility refusal; B4.4 →
`models_cat10.run_B4_4` on the canonical v7 layer, abstaining without the governed
action-by-scenario structure). The correction is a **withdrawal**, following this repository's own
precedent for proxy qualifiers: `MethodLabel` refuses a truthful name equal to the registered
name, so an entry exists only where the two differ, and with the entry gone the surface presents
the registry name. The withdrawn sentences are preserved in
`code_audit/run35_stale_method_label_reconciliation.csv`.

A consequence worth recording: **every remaining truthful-method label now sits on a disabled
module.** No enabled module carries a claim that its registered name misdescribes it. That is
asserted mechanically rather than left implicit.

## 18. A1.1 IS NOT REPAIRED IN THIS CLOSURE

By owner decision, and recorded unchanged for Run 36 as
`DECLARED_STRUCTURE_UNCONSUMED_AND_REACHABLE_PARAMETER_UNRESOLVED`
(`code_audit/run35_a1_1_run36_handoff.json`): governed structure `costDriverDistributions` is
declared; the intake accepts it; **consumers found = 0**, re-measured by search rather than
asserted; production computes from `bac`, `cpi`, `spi` and `docRiskScore`; and the instrument's
only reachable unresolved parameter remains. No remediation was attempted.

## 19. Closure package decisions, measured

`code_audit/run35_closure_package_decision.csv`.

- **Participant package `og-participant-2026.08-v11` RETAINED.** All **70** files the v11
  checksum record names were re-hashed against that record: **0 moved**. The closure edited only
  `server/app/simulation/` and `server/tools/`, and no dispatched participant file is under either
  path. The declared protocol surface was not touched, so the experimental sequence — fixed
  evidence, preliminary judgment and confidence, lock, AI reveal, final judgment/confidence/
  disposition/evidence/rationale, final lock, next period — is unchanged. v11 stays the current
  record and is not rewritten; every predecessor stays pinned to its own commit.
- **Participant-VISIBLE analytical outputs measured, not assumed.** A1.7 and A1.8 were executed
  on both pinned lines over every controlled-corpus earned-value scalar set: **0 of 6 moved** —
  identical status and byte-identical displayed sentence. A **constructed boundary probe does
  move** (Green → Amber); that is the defect being repaired, it is recorded rather than hidden,
  and it is not a governed corpus scenario. **The retention is bounded accordingly: it says the
  governed corpus scenarios are unchanged, not that A1.7 can never move a participant-visible
  status.**
- **Synthetic package `OG-SYNTH-0.6` RETAINED.** Its sealed files were re-hashed against the
  package's own `CHECKSUMS.sha256`: **0 moved**. No governed expected output for A1.7 or A1.8
  lives inside the package, so a corrected analytical value moves no package byte. Nothing was
  regenerated in place.

## 20. Closure fault campaign

Fifteen failure modes, each injected into a real file, confirmed applied by re-reading bytes, each
turning **one named guard** red for its own reason, restored byte-for-byte and re-verified green:
**15 declared, 15 applied, 15 intended RED, 15 restored GREEN, NOT_APPLIED 0, crashes accepted as
RED 0.** Guard suite `server/tools/test_run35_closure_voter_identities.py`; results
`code_audit/run35_closure_fault_injection.csv`.
