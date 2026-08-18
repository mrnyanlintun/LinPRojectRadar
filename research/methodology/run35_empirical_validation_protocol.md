# Run 35 — Empirical validation protocol

**Status:** frozen before any empirical scoring was executed. This document is committed on its
own, ahead of the commit that produces any measured result, so the git history shows the
classification vocabulary and the independence rules were fixed before results were seen.

**Date:** 2026-08-18. **Starting commit:** `584ccf9882c3c48fba85055ab3ef63ae9f89f890`.
**Simulation line at protocol time:** `sim-2026.08-v22`.

---

## 0. What this protocol is for

Run 35 must decide, for each of the 100 scientific targets, **whether an empirical validation is
possible at all**, and only then perform one where it genuinely is. The single failure this
protocol exists to prevent is the manufacture of a reference standard — inventing an outcome to
score against, or renaming synthetic laboratory evidence as field evidence.

Absence of empirical-validation evidence is **not** a methodological failure of a method, and it
is **not** permission to manufacture evidence. The classes below describe *validation
availability*, not method correctness.

---

## 1. Validation-eligibility classes

Exactly one class is assigned to every scientific target. The vocabulary is closed; no eighth
class may be added.

### A. `EMPIRICALLY_VALIDATABLE_NOW`
An independent **observed or reference outcome** exists in evidence available to this repository,
and that outcome is **not part of the method's input**, is not derived from the method, and was
not selected after seeing the method's performance. Only this class supports the sentence "this
method is empirically validated".

### B. `PARTIAL_REFERENCE_STANDARD`
Independent evidence exists for **only part** of the method's output or decision. In this
repository the recurring instance is a *published definitional or regulatory identity* that fixes
the numeric quantity a module reports, while nothing fixes the interpretive band, status colour or
decision the module attaches to it. The supported component is scored; the unsupported component
is recorded as not validated and is **not** upgraded.

A class-B result is a **reference-supported analytical result** (section 4 item 2 of the Run-35
contract). It is *not* an empirical field validation, and no class-B row may be reported as one.

### C. `SYNTHETIC_VALIDATION_ONLY`
Canonical, synthetic or laboratory evidence exists — known-answer tests, governed synthetic
fixtures, cross-implementation convergence, fault sensitivity, reproducibility — but **no
independent empirical field outcome** exists. Synthetic evidence establishes arithmetic,
structure, stability and fault detection. It never becomes empirical field validation.

### D. `CALIBRATION_GAP_BLOCKS_VALIDATION`
A parameter or calibration the method **actually applies to its emitted output** remains
unresolved (`UNSUPPORTED`, `HEURISTIC`, calibration-pending or provenance-blocked), so an
empirical performance number could not be interpreted defensibly: a measured error would be
attributable to the uncalibrated value rather than to the method. Run 35 does **not** resolve
these by tuning.

The applied-ness test is mechanical: the parameter is applied if executing the current production
path on the governed corpus produces an output field whose value depends on it (for band ladders,
a non-null `status_color`). A parameter carried but never reached is recorded as
`applied=no`, and then it does not, by itself, place the target in class D.

### E. `STRUCTURE_OR_DATA_ABSENT`
The governed input structure the canonical method requires does not exist in the governed corpus,
so the method legitimately abstains and there is nothing to validate. Disabled targets whose
disablement reason is exactly this absence belong here.

### F. `NO_INDEPENDENT_REFERENCE_STANDARD`
The method can compute, and its parameters do not block interpretation, but there is **no
defensible independent outcome** against which to score it. Continuous diagnostics with no field
label belong here. A binary label must **not** be invented to move a target out of this class.

### G. `EMPIRICAL_VALIDATION_PENDING_STUDY`
The planned controlled praxis study, or future observed project data, are required before any
empirical claim can be made. Assigned where a field outcome is *conceivable and planned* but does
not yet exist.

### Precedence
Where more than one class could apply, the first applicable in this order is assigned:

`E` → `D` → `A` → `B` → `G` → `C` → `F`

Structure absence is decided first because there is then no output at all; calibration blockage is
decided next because it makes any score uninterpretable; `A` before `B` because a whole-output
reference outranks a partial one; `G` before `C`/`F` because a planned study is a stronger
statement about the future than the current absence of a standard.

---

## 2. Independence rules for a proposed reference standard

Every proposed reference outcome must record: source document or data; timestamp or period;
reference variable; the method's inputs; whether the reference was available to the method;
whether the reference is derived from the method; lineage; independence judgment; evidence.

A reference is **invalid** if any of the following holds:

1. it is a direct method input;
2. it is calculated by the same method;
3. it is a transformation of the method output;
4. it was selected after seeing the method's performance;
5. it comes from the synthetic detector used to create the prediction;
6. it leaks future-period information into an earlier-period prediction.

**Algebraic-relatedness rule.** For earned-value quantities, "independent" means
*not derivable from the method's own inputs by the method's own definition*. A differently-named
quantity that is an algebraic rearrangement of the inputs is **not** independent. This is why
no earned-value quantity in this repository yields a class-A reference standard.

**No qualified reference, no empirical validation score.** A row with no qualified reference gets
`NOT_APPLICABLE`, never `PASS`.

---

## 3. What a class-B published-identity reference does and does not establish

A published definitional identity (for example the PMI to-complete-performance-index and
variance-at-completion definitions, or the OSHA recordable-incidence-rate identity) is an
**external, independently authored specification of the arithmetic**. Comparing the production
output against an independent implementation of that identity, in exact rational arithmetic,
establishes:

- that the shipped implementation computes the quantity the published standard defines;
- that it does so without an undeclared transformation.

It does **not** establish:

- how often the resulting status is right;
- false-positive or false-negative performance;
- any field-outcome relationship whatever.

The reference's inputs are the method's inputs, so under the algebraic-relatedness rule this is
explicitly **not** a class-A empirical validation. It is recorded as class B and reported as a
reference-supported analytical result.

---

## 4. The study distinction is preserved

The controlled praxis study measures **influence on professional judgment**. AI agreement is not
automatically correctness. Run 35 qualifies the analytical instrument for later study use and
makes no participant claim. Six quantities remain distinct and must never be collapsed:

1. analytical-method correctness;
2. reference-supported analytical result;
3. participant agreement with AI;
4. participant revision after AI;
5. whether the revision was reference-supported;
6. whether the revision was documented and auditable.

Items 3–6 require participant outcomes. **No participant outcome data are available to this
repository and none may be fabricated.** Every Run-35 row is confined to items 1 and 2.

---

## 5. Metric contract by output type

The target-to-metric contract is committed **before** scoring, in
`code_audit/run35_validation_metric_contract.csv`. Metrics are chosen by output type:

| Output type | Admissible metrics |
|---|---|
| Deterministic scalar | exact equality; absolute error; relative error; tolerance justified only by numerical precision |
| Categorical / status | exact agreement; confusion matrix; sensitivity/specificity **only** where a genuine independent label population exists |
| Ranking | rank agreement; top-k agreement; pairwise ordering |
| Forecast | temporal separation **required**; MAE; RMSE; absolute percentage error only where the denominator permits; interval coverage only where genuine intervals are produced |
| Decision rule | validated against its declared mathematical/reference problem; agreement with a synthetic oracle is **not** field validation |
| Continuous diagnostic without field label | no metric. Classify `NO_INDEPENDENT_REFERENCE_STANDARD`; do **not** invent a binary label |

**Acceptance rules.** A predeclared acceptance rule may be applied only if it existed before the
result was observed. Where none exists, the measurement is reported **descriptively** and the
verdict is `INCONCLUSIVE` or `NOT_APPLICABLE` — never `PASS` against a threshold chosen
afterwards. No threshold and no metric may be changed after a result is seen; the metric contract
is frozen by its own commit and the scoring generator reads it rather than restating it.

---

## 6. Verdict vocabulary and the NOT_APPLICABLE separation

The result artifact uses four verdicts and no blanks:

- `PASS` — a predeclared acceptance rule existed and the measured result satisfies it.
- `FAIL` — a predeclared acceptance rule existed and the measured result does not satisfy it.
- `INCONCLUSIVE` — a measurement was made but no predeclared acceptance rule exists, so no
  pass/fail claim is available.
- `NOT_APPLICABLE` — **no measurement was made at all**, because no qualified independent
  reference standard exists for this target. This is the correct final state for most targets and
  it is not a defect.

`NOT_APPLICABLE` is a distinct literal value carried in its own column together with an explicit
`empirical_metric_applicable=NO` and an empty-forbidden `limitation` sentence. No empty cell may
stand where a verdict belongs, so an absent verdict can never be read as a benign pass.

---

## 7. Prohibitions in force for the whole run

- Synthetic calibration is never labelled empirical validation. Required:
  `synthetic_as_empirical_claims = 0`.
- No detector output becomes its own reference outcome.
- No module is activated to obtain a score.
- No parameter is calibrated opportunistically in this run.
- The voting set remains exactly `A1.7` (TCPI) and `A1.8` (VAC), count 2, under the governed
  overall label **Cost Recovery Status**. A good empirical result confers no vote.
- The Category-9 qualification gate stays a gate and metadata; it casts no risk vote; raw bypass
  and missing-assessment bypass stay 0.
- Category-10 methods exercise no approval authority and their recommendations never re-enter as
  project-condition evidence.
- Disabled and archived targets keep their eligibility rows and are neither deleted nor activated.
- Dependence is pairwise on primitive-source lineage only; no transitive closure. Unknown lineage
  is **not** independent lineage.
