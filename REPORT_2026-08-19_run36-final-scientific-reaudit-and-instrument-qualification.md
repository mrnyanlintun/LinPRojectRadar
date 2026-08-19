# Run 36 — Final 100-target scientific re-audit, instrument qualification, and the freeze decision

**Outcome: `FREEZE_BLOCKED`.** One blocking defect remains and it requires an owner decision that
no existing authority resolves. The instrument is otherwise green, the forty-fault campaign is
complete, and the authenticated participant path qualifies in a real browser — but a green suite
is not a qualification, and this run did not manufacture one.

---

## 1. Exact starting commit, verified rather than assumed

`HEAD == main == origin/main == dafc35d35bafe5af76e1ce48ef7daceab9daed2c`, tree clean,
`SIMULATION_VERSION = sim-2026.08-v23`, participant `og-participant-2026.08-v11`, synthetic
`OG-SYNTH-0.6`. Complete-suite baseline re-run before any edit: **172 suites / 13460 checks, all
green**. Voting exactly 2 (A1.7 TCPI, A1.8 VAC). Every one of these was checked from git and from
execution in this session; none was taken from the handoff.

---

## 2. A1.1 — the lead item

### All four carried-forward claims REPRODUCE

Measured, not accepted:

| Claim | Measured | Verdict |
|---|---|---|
| declares `costDriverDistributions` | `canonical_v3.V3_STRUCTURE_KEYS["A1.1"]`, one declaration site | reproduces |
| the governed intake accepts it | present in `project_data.governed_structure_keys()` (85 keys) | reproduces |
| consumers found = 0 | supplied **through the real intake** (`add_revision` → `apply_to_signal_inputs`, which reported it added the key) and the emitted row is **byte-identical** | reproduces |
| production computes from scalars | `app.simulation.models.run_monte_carlo_module`, reading `bac`, `cpi`, `spi`, `docRiskScore` | reproduces |

### The reachable unresolved parameter, derived rather than transcribed

Of the 100 scientific targets executed through `registry.run_module` on the controlled corpus,
**six leave the abstention branch** and **exactly one** carries both a `status_color` and an
`UNSUPPORTED` parameter classification: A1.1, emitting `red` from a ten-and-five-per-cent ladder
over the P80 overrun percentage. That is a section-6 hard-gate failure and a section-23 blocking
defect.

### Which section-2 outcome the evidence actually selects

- **Outcome B (declaration is stale) — REFUTED.** The supervisory specification §1.1 *requires*
  "explicit uncertain variables/distributions; parameter provenance; dependencies/correlation if
  assumed; … iteration count; seed/reproducibility; … convergence evidence". Canonical theory does
  require the structure. Absence of a consumer is consistent with both B and C and proves neither;
  it is not evidence that theory does not require it.
- **Outcome C (abstain or disable) — CONTRADICTED** by the same committed clause, which says the
  production model "may retain the dedicated BAC/CPI/SPI/document-risk Beta-PERT adaptation", with
  pass ceiling `METHOD_PASS_CALIBRATION_PENDING`.
- **Outcome D (unresolved parameter blocks output) — APPLIED, and closed.**
- **Outcome A (wire the genuine structure) — NOT AVAILABLE WITHOUT INVENTION.** The specification
  requires a "deterministic mapping from sampled variables to EAC" and **does not state what that
  mapping is**. `canonical_v3.declared_cost_driver_model` reads and validates the structure and
  says in its own docstring that no sampling happens there. Nothing in this repository says whether
  declared drivers sum to the EAC, scale it, or cover part of it. Supplying one would be inventing
  the canonical method, which this programme forbids.

### What Run 36 did

`mc_status` is **preserved** — this programme does not erase scientific history — and production
can no longer reach it (asserted: exactly one occurrence in the file, its own definition). A1.1 now
emits `status_color: None`, `band_asserted: False`, `calibration_pending: True`, which is precisely
what `canonical_v3.py` rule 2 already requires of a caller with no evidence-established boundary
and precisely what A6.1, A6.2 and A6.3 already do.

**No number moved.** The v23 line extracted from git object `dafc35d3` returns
`overrun_pct_p80 = 12.104441685525892` on the controlled corpus and `11.983407036630878` on the
lineage fixture; the v24 line returns the identical two figures. The divergence is the colour and
nothing else.

### A second A1.1 defect, found by re-deriving rather than re-reading

Run 35 did not report this. The served defensibility object described A1.1 as
`CONDITIONAL_ON_GOVERNED_STRUCTURE`, with `canonicalStructureRequired: true` and the sentence
"when that structure is absent the module returns Not Estimable". **Execution disproves all three.**

Root cause: both the generator and the Run-32 truth inventory assigned the conditional state from
`elif structure_key:` — inferring conditionality from the **presence of a declaration** rather than
measuring it. In the inventory the measurement was already computed two lines above and unused.
All 101 rows were then executed against a structure-free probe: **exactly one** module was
misdescribed. The five Portfolio Health rows keep the required-structure sentence, because their
route refuses before the probe reaches them.

### The residual, which is the blocking defect

**A1.1 still declares a structure that canonical theory requires, the intake still accepts it, and
no route reads it.** The committed authority is internally in tension: §1.1's *Required* list
demands the structure and §1.1's own next paragraph permits the scalar adaptation instead. Only the
owner can say which clause governs. Record: `code_audit/run36_a1_1_closure.csv`.

---

## 3. Mechanical population reconciliation

`code_audit/run36_population_reconciliation.csv`, 16 rows, derived from `registry.load_registry()`
and `DISABLED_EVIDENCE_UNDER_REVIEW`. **Every expected count reconciles; discrepancies = 0.**

| Population | Derived | Expected |
|---|---|---|
| registered total | 101 | 101 |
| registered project modules | 96 | 96 |
| project scientific targets | 95 | 95 |
| Portfolio Health targets | 5 | 5 |
| scientific targets | **100** | 100 |
| voting | 2 | 2 |
| disabled (all) | 9 | — |
| disabled inside the 100 | 8 | — |
| archived | 1 | — |
| supplied rather than computed | 1 | — |

**Three different populations of the same size exist and are recorded as distinct.** The two
historical 95s intersect at **94** — `registry.VALIDATED` excludes A4.1 (supplied, and a scientific
target); the scientific project population excludes A3.4 (disabled under evidence review, and not a
scientific target). And a **third 100** exists: `GROUP_ASSIGNMENT.md`'s "the analytical server
registers 100 of them" is `VALIDATED` + the portfolio registry, which excludes A4.1 and *includes*
A3.4 — the opposite exclusion. The two hundreds intersect at **99**. None is collapsed into another.

---

## 4. The 100-target re-audit

`code_audit/run36_100_target_scientific_reaudit.csv`. **Rows 100, unique 100, missing 0,
duplicates 0.** Nothing was copied from a Run-35 artefact: every field is recomputed from the
registry, the dispatch table read through `__wrapped__`, the structure maps, the parameter register,
the lineage module, and execution of the real production entry point.

**Final scientific qualification** (section 22's closed five-value vocabulary; no sixth minted):

| Value | Count |
|---|---|
| `QUALIFIED_FOR_BOUNDED_STUDY_USE` | 4 — A1.1, A1.7, A1.8, A6.2 |
| `QUALIFIED_WITH_ABSTENTION` | 87 |
| `DISABLED` | 7 |
| `RESEARCH_ONLY` | 1 — A4.1, supplied |
| `ARCHIVED` | 1 — B2.9 Quantum Probability |

**Cross-validation worth stating.** The operational-disposition distribution came out
`KEEP_OPERATIONAL` 2 · `KEEP_ADVISORY` 2 · `KEEP_ABSTENTION_CAPABLE` 87 · `RESEARCH_ONLY` 1 ·
`DISABLED_INSUFFICIENT_INPUT` 5 · `DISABLED_INSUFFICIENT_PROVENANCE` 2 · `ARCHIVED` 1 — **identical
to Run 35's**, reached by a different derivation. Lineage `UNRESOLVED` came out **77 of 100**, also
identical, also independently. Agreement reached by an independent route is evidence; agreement
reached by reading the previous answer is not, and none was.

One classification refinement is recorded rather than silently applied: `KEEP_ADVISORY` is keyed off
a **numeric reading**, not off leaving the abstention branch. A6.1 (`NOT_ESTIMABLE`) and A6.3
(`APPLICABILITY_NOT_ESTABLISHED`) exit that branch and report nothing; counting them advisory would
have inflated the operational population with two modules that advise on nothing.

---

## 5. Canonical routing

| Routing | Count |
|---|---|
| `CANONICAL_REACHED` | 6 |
| `CANONICAL_ABSTENTION` | 80 |
| `PORTFOLIO_COMPUTED` | 5 |
| `DISABLED` | 7 |
| `ARCHIVED` | 1 |
| `SUPPLIED` | 1 |

`PORTFOLIO_COMPUTED` is **not** a value minted for convenience: it is the already-governed state
name carried by `build_run32_defensibility_inventory.STATE_OF_EXECUTION`. The five Portfolio Health
targets are refused on a single project's route with `PortfolioModuleError` before any method is
entered, which is not the same fact as abstaining.

**Legacy production reachability = 1**, and it is not a hidden route: A1.2 is the one surviving
proxy qualifier the platform itself declares. Every other target routes to its canonical layer or
to a governed refusal. No target is marked canonical merely because a helper exists.

---

## 6. Input contracts and parameter provenance

`code_audit/run36_parameter_provenance_reaudit.csv`, 97 parameter rows plus 2 acceptance counters.
The expected population was **not** taken from the provenance artefact: it was walked from
`parameters.PARAMETER_PROVENANCE` and each module then executed.

- **Unclassified reachable parameters = 0.**
- **Reachable UNSUPPORTED parameters producing authoritative output = 0** — the section-6 hard gate,
  closed by the A1.1 band withdrawal. Before it, the count was 1.
- Illegal parameter classes = 0; the vocabulary is closed.
- No `UNSUPPORTED` parameter was deleted. They remain recorded historically, applied to nothing
  authoritative.

**One declared-but-unconsumed input remains: A1.1's `costDriverDistributions`.** It is the blocking
defect, and the served record now says so in the participant's own words rather than claiming an
enforcement no route performs.

---

## 7. The seven validity layers, kept apart

Canonical theory established: 92 of 100 (the 8 concept-only disabled are governed as concept-only
and claim no canonical method). Implementation fidelity: established for every dispatched target,
route-verified through `__wrapped__`. Governed input sufficiency: the controlled corpus carries no
governed structure, so 88 targets abstain correctly. Parameter provenance: 0 unclassified, 0
unsupported-and-authoritative. Calibration: **no calibration set exists** — no labelled outcome
corpus and no expert reference standard. Empirical validation: see below. Operational qualification:
the table in section 4.

These are **not** collapsed into one PASS anywhere in this run.

---

## 8. Empirical validation — the honest limits

| Class | Count |
|---|---|
| `PARTIAL_REFERENCE_STANDARD` | 3 — A1.7, A1.8, A6.2 |
| `CALIBRATION_GAP_BLOCKS_VALIDATION` | 1 — A1.1 |
| `EMPIRICAL_VALIDATION_PENDING_STUDY` | 5 — Portfolio Health |
| `STRUCTURE_OR_DATA_ABSENT` | 91 |

**Empirically validated against an independent observed field outcome: 0 of 100.** No band anywhere
in the instrument has a measured false-positive or false-negative rate. Run 35's `E` count of 96 and
this run's 91 + 5 are the **same 96** under a different precedence: Run 35 applied E→D→A→B→G→C→F and
recorded PH's pending-study class as secondary; Run 36 records it as primary and the two are
reconciled here rather than forced to agree. The three partial-reference results were re-executed
through the current final route and all three hold at v24. The historical v22 failures are not
erased.

---

## 9. Voting

**Voting count = 2**, exactly A1.7 TCPI and A1.8 VAC, from `registry.CORE_VOTING_MODULES` and
independently from the 100-row artefact. A1.7 carries its canonical value at full precision with a
separate `tcpi_display`, and the band reads the canonical value; A1.8's analytical result is not
replaced by its formatted output. Both were verified on the **participant surface in a real
browser**, not only in a unit test. A6.2's exact OSHA pass confers no vote. No third target votes,
and fault 8 proves the guard that says so can go red.

---

## 10. Category-9 boundary

Category 9 is qualification and metadata. `contributes_to_project_status` is `False` for group C, no
C-group module is in the voting set, and a package carrying no assessment is refused with
`CATEGORY9_ASSESSMENT_MISSING` before a governed downstream method is reached. Raw bypass 0,
missing-assessment bypass 0. **The gate was faulted** (faults 9 and 10) and both guards went red for
their own reason and restored green.

---

## 11. Category-10 authority boundary

Every Category-10 result carries `human_authorization_required: True` and
`creates_project_evidence: False`; nothing in `canonical_v7` returns a `status_color`, so nothing
enters fusion. **Authority violations = 0.** MARCOS B2.18 and CRITIC-TOPSIS B2.19 each have one
stable identity and one engine, and **no analytical engine anywhere is shared by two module
identities** — zero duplicate implementations, read through `__wrapped__` because `functools.wraps`
masks route identity from naive introspection. Faults 11 and 12 turn both guards red.

---

## 12. Disabled and archived

9 disabled: 8 concept-only plus A3.4 Material Cost Variance under evidence review. Material Cost
Variance, Plithogenic Sets, Hypersoft Sets and Quantum Probability are each still **registered**,
produce no status on the controlled corpus, and do not crash. Nothing was deleted. Disabled means
production unreachable; archived means production unreachable with the historical record preserved.
Faults 13–16 reactivate each one and each guard goes red.

---

## 13. Portfolio Health

All five non-voting, all refused on a single project's route. PH.1: tree count 100, `0.576` remains
`SYNTHETIC_LABORATORY`, schema-bound to `run15-synthetic-4feature-v1`, `is_project_status_band:
False`, `field_validated: False`; cohorts below 3 are not estimable and small cohorts carry an
explicit limitation with **no authoritative flag**. PH.2: no composite without governed weights.
PH.3: minimum 3 distinct observations, enforced. PH.4: the 0.15 radius stays retired, continuous
distance only. PH.5: score null under `PARAMETER_PROVENANCE_BLOCKED`. Empirical validation PENDING
for all five. Faults 17–23 exercise each boundary.

---

## 14. Lineage

`LINEAGE_UNRESOLVED` 77 · `LINEAGE_ESTABLISHED_INDEPENDENT` 9 · `LINEAGE_ESTABLISHED_DEPENDENT` 6 ·
`LINEAGE_NOT_APPLICABLE` 8. **Unknown lineage was not treated as independent**: every row claiming
independent lineage carries an actual record in `lineage.MODULE_LINEAGE`, and every unresolved row
genuinely has none. No independence was invented to improve coverage. Fault 24 proves the guard.

---

## 15. Parsimony — re-derived, with a discrepancy reported rather than reconciled away

`code_audit/run36_parsimony_reconciliation.csv`. The primitive-source profile is **measured by
ablation through the real entry point**, not read from a declaration: each controlled-corpus scalar
is removed in turn and the module re-executed, and a scalar whose removal changes the emitted row is
one the module actually reads. For a target defined on a governed structure, that structure is the
profile — two modules defined on one structure read one object.

| Overlap type | Run 36 | Run 35 |
|---|---|---|
| `NONE` | 75 | 77 |
| `SHARED_GOVERNED_STRUCTURE` | 19 | 19 |
| `IDENTICAL_PRIMITIVE_SOURCE_SET` | 5 | 3 |
| `PRIMITIVE_SOURCE_SUBSET` | 1 | 1 |

**Distinct primitive-source profiles: 83. Targets sharing a profile with at least one other: 24.
Targets adding no distinct analytical function: 17** — A2.4, A2.5, A2.6, A2.10, A2.11, A5.3, B1.1,
B1.3, B1.4, B2.9, B2.19, B4.1, B4.6, B4.7, D1.2, D1.4, D1.5.

**This is 17, not Run 35's 22, and the difference is not suppressed.** The two figures answer
different questions: Run 35's `unique_analytical_contribution` column marked NO under a taxonomy
that counted declared shared structures and subset relations; Run 36 counts a target as adding
nothing only when another target already occupies the **identical measured** profile. The artefact
carries a `REPORTED_DISCREPANCY` row saying exactly this. Neither figure was forced to the other.

Nothing was deleted. The seven-value disposition vocabulary was not extended, and no eighth
disposition exists.

---

## 16. Defensibility

The generator/output no longer validates itself: the Run-36 guard runs the generator into a
temporary directory and compares. **One module's served statement was untrue and is corrected**
(A1.1, above). No conditional method is described as unconditionally computing; no disabled method
is described as active; no Portfolio Health method is described as a project-level computation.
A1.1 gets a sentence of its own rather than A4.1's — "the platform does not compute this value" is
false of a module that computes every period. Faults 25 and 26 turn both guards red.

---

## 17. Authenticated browser qualification

`code_audit/run36_authenticated_browser_qualification.csv`, **25/25**, real Chromium, real
authenticated participant route, throwaway migrated SQLite. Production Postgres never accessed.

The **whole study path was reached and passed**: authentication, project/period workflow, fixed
evidence review, preliminary judgment, preliminary lock, AI reveal (absent before the lock,
inspectable after it), final judgment fields, final lock, evidence and rationale capture, the
governed timestamp order, and the next-period transition with the preliminary card rendering again.
Both locks were additionally attacked **through the route** with the participant's own valid
session and the server refused — a disabled button proves nothing. The confirm gate was exercised
first with no dialog handler, proving it no-ops rather than silently submitting.

A1.1's band withdrawal was confirmed **where it matters**: on the participant surface A1.1 is still
present, still reports its P80 figure, and shows no status colour. No JavaScript console crash. The
handbook/method-reference surface was reached through `hb-tab-methods → [data-topic] →
[id^=body-modref-]`; two rows were initially `NOT_VERIFIED` and were closed by finding the route the
participant's own page uses, not by relaxing the claim.

---

## 18. Participant protocol qualification — and a count that is NOT mechanically derivable

The sequence — fixed evidence review → preliminary assessment/action/confidence → lock → AI reveal →
final action/confidence/disposition/evidence/rationale → final lock → next period — is **enforced
mechanically**, at the route and at the database (`ck_decisions_reveal_after_pre_lock`), and was
driven end to end in the browser. The experimental sequence is byte-identical to the frozen package:
`decision.js`, `decision-ui.js`, `workspace.js`, `deepdive.js` and both questionnaires unmoved.

**Reported rather than forced, as section 19 requires.** The expected design of 6 projects / 6
periods / 36 project-periods is **not mechanically derivable from the participant package or the
data contract**. `Scenario.period_count` is a nullable per-scenario integer and the project and
sequence counts are operator-configured `ConditionSequence` rows. The instrument fixes the
*sequence*; it does not fix the *counts*. This is a limitation of what can be verified, not a defect
found — but it is not a verified 6×6×36 either, and it is not written up as one.

---

## 19. Reproducibility and packages

`code_audit/run36_reproducibility_inventory.csv`, 19 components, each with path, sha256, git object,
package/version owner, role, generated-or-source, predecessor and reproducibility status, re-hashed
against disk by the guard.

**OG-SYNTH-0.1 remains historically incomplete and is recorded as such**: 519 manifest entries
against 504 recovered, 15 unrecoverable rows over 5 unique paths. No completeness is claimed, and
the guard fails if that sentence is removed.

---

## 20. The forty-fault campaign

`code_audit/run36_fault_injection_results.csv`:

> faults declared **40**; applied **40**; intended RED **40**; restored GREEN **40**;
> NOT_APPLIED **0**; guards that CRASHED **0**; crash accepted as RED **0**; COUNTED **40**.

Each fault names one oracle in `test_run36_fault_guards.py`, and credit requires the **named** guard
to fail **and** its failure line to carry the intended-reason fragment — a red elsewhere is not
evidence. `__pycache__` is dropped on both sides of every injection.

**Seven of the forty were ill-posed on the first pass and are repointed and documented rather than
quietly dropped.** Four shared one root cause worth recording: a first-occurrence-only text edit
does not falsify an oracle that tests for *any* occurrence of a property, so the mutation left the
property in place and was a `NOT_APPLIED` dressed as a fault. Fault 23 additionally needed a
replacement token that does not *contain* the token being removed. Fault 6 was repointed at the real
historical defect (banding on the rounded TCPI) rather than at a field rename.

**Fault 40 is the one that protects every other conclusion in this run**: it creates a freeze
manifest while a blocking defect stands, and the freeze gate goes red.

---

## 21. Two guard defects found by this run's own change, and repaired

1. `test_run10b_canonical_integration` used "a colour came back" as its proxy for "the module
   computed", while the sentence it printed claimed that handing A1.1 a cost register changes
   **nothing**. The oracle is now that claim itself — full row equality with and without the
   register — which is strictly stronger.
2. **Three version-boundary guards took their "new" line from the LIVE TREE while asserting settled
   claims about what a PAST run changed.** Any legitimate later change falsified them. Both the
   Run-32 and the Run-35 boundary guards now extract both lines from git objects, so the historical
   claim is fixed forever and still fails if either pinned object is rewritten — which is the thing
   it was really guarding.

---

## 22. Version and package decisions, taken from executed behaviour

- **Simulation: `sim-2026.08-v24`.** Required, because A1.1's emitted row changed. Predecessor →
  successor proved by executing both pinned lines, not by reading the diff. Genuine divergence: the
  colour. Genuine non-divergence: the figures, and every module that is not A1.1.
- **Participant package: `og-participant-2026.08-v12`.** Required, because one of the seventy files
  moved — the generated defensibility object. v11 is pinned to `dafc35d3` and verified against that
  git object, so only one record claims the working tree. The experimental sequence is unmoved.
- **Synthetic package: `OG-SYNTH-0.6` RETAINED.** No governed synthetic byte changed. Nothing was
  regenerated in place. Run 36's audit fixtures are Run-36-owned audit artefacts and were **not**
  put into the synthetic programme package.

---

## 23. Blocking defects

**Blocking defects on the 100 target rows: 0. Instrument-level blocking defects: 1.**

> **A1.1 — `DECLARED_STRUCTURE_UNCONSUMED`.** A known scientific contradiction left unresolved, in
> the exact sense section 23 names. A1.1 declares `costDriverDistributions`; canonical theory
> requires it; the governed intake accepts it; no current route reads it. An owner who supplies it
> changes nothing.

### The exact closure needed

**The owner must decide which clause of supervisory specification §1.1 governs A1.1.** Both are in
the same committed document and they point opposite ways:

- **(a) The `Required:` list governs.** Then the declared cost-driver distribution set is a
  precondition, and the owner must supply the one thing the specification demands and does not
  define: **the deterministic mapping from sampled cost drivers to EAC** — whether declared drivers
  sum to the EAC, scale it, or cover a stated part of it — together with the dependence treatment
  and the convergence criterion tied to the reported percentile. With that, A1.1 executes the
  canonical Monte Carlo when the structure is supplied and abstains when it is not.
- **(b) The "may retain" permission governs.** Then the retained BAC/CPI/SPI/document-risk
  adaptation *is* A1.1's governed method for this instrument, and `costDriverDistributions` should
  be **withdrawn** from `V3_STRUCTURE_KEYS` and recorded as an unimplemented enrichment, so the
  intake stops accepting a key that reaches nothing.

Run 36 will not choose between them, because choosing (a) means inventing a canonical method and
choosing (b) means overriding a committed `Required:` list. Either is an owner decision.

---

## 24. Freeze decision

**`FREEZE_BLOCKED`.** No freeze manifest and no companion were created, and the guard asserts they
do not exist while the blocking count is non-zero.

The instrument is in good order otherwise: 174 suites / 13596 checks green, forty faults applied and
red for their intended reasons, the participant path qualified in a real browser, populations
reconciled exactly, the section-6 hard gate closed. **None of that is a qualification.** The owner's
own rule is that scientific and governance qualification must independently pass, and one governance
question — which clause of the specification governs A1.1 — is open.

---

## 25. The final statement, with the layers kept apart

- **Canonical correctness.** 92 of 100 targets perform the method their registered name claims; the
  other 8 are governed as concept-only and claim none. A1.1's canonical *identity* is the open
  question, not its arithmetic.
- **Implementation qualification.** Every dispatched target routes to its canonical layer or to a
  governed refusal. Legacy production reachability is 1 and is the platform's own declared proxy.
  Duplicate engines 0. Unclassified parameters 0. Unsupported parameters authorizing output 0.
- **Calibration.** Nothing is calibrated. No calibration set exists in this repository — no labelled
  outcome corpus and no expert reference standard — so no band has a fitted or tested boundary.
- **Empirical validation.** **0 of 100** are validated against an independent observed field
  outcome. Three are scored against a published identity on a scalar component only. Five carry
  pending-study status. No false-positive or false-negative rate is known for any band anywhere.
- **Bounded controlled-study qualification.** 4 targets are fit for the bounded role assigned to
  them, 87 are scientifically retained and correctly abstain, 1 is research-only, 7 are disabled and
  1 archived — **subject to the A1.1 decision above.**

There is no "100% scientifically validated" figure in this instrument and this report does not
report one.
