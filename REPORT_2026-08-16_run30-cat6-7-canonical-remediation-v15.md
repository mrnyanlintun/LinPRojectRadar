# Run 30 — Category 6/7 canonical synthesis and epistemic remediation, sim-2026.08-v15

**Scope:** Category 6 (Signal Synthesis, 4 targets) and Category 7 (Evidence Combination /
Epistemic Uncertainty, 20 targets). 24 targets. Categories 8–10 and Portfolio Health untouched.

---

## 1. v14 preservation proof

`sim-2026.08-v14` is preserved and is not rewritten anywhere.

- `SIMULATION_VERSION_HISTORY` is append-only. The tuple recorded at git object `ac7c011` is read
  out of git (not out of a note) and asserted to be a strict **prefix** of the tuple now; it grew
  by exactly one stamp. `server/tools/test_run30_version_boundary.py` §1.
- Every identifier in the history is unique; no stamp is re-used.
- `research/freeze/RUN29_CLOSURE_FREEZE_2026-08-16.json` and its `.sha256` are **untouched**. The
  Run-30 freeze names it as parent and carries its digest. No predecessor freeze, package record or
  manifest was regenerated in place.
- The predecessor production-tree manifests (`run22` … `run29_closure`) are all untouched; the pin
  moved to `code_audit/run30_production_tree.sha256`.

## 2. v15 identity and first commit

- Stamp: **`sim-2026.08-v15`**, superseding `sim-2026.08-v14`.
- First commit carrying it: **`08713a1`** (see §29 for the exact final merged head).
- Freeze: `research/freeze/RUN30_CANONICAL_CAT6_7_FREEZE_2026-08-16.json`,
  identifier `OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-16-RUN30-CANONICAL-CAT6-7-V15-1`,
  stage-1 digest `6a64aa91a70f3dbbd4707203384ae18132a42048b7ac414ccb6eb20d0e1a71da`.

### The v14 → v15 boundary, proved by executing the predecessor line

The v14 analytical package is extracted from git object `ac7c011`, written to a temporary package,
imported, and executed **beside** the current line on identical assembled inputs
(`server/tools/test_run30_version_boundary.py`, 19/19 checks). The extracted package is confirmed
to be stamped `sim-2026.08-v14` and its functions confirmed to be different objects from the live
ones, so the comparison runs two lines rather than one twice.

| input | v14 output | v15 output | reason for the difference |
|---|---|---|---|
| Three primary signals all reading lowercase `red`, beside a **3-row** module array | B1.4 → `Red` | B1.4 → `mean_worst_2 = 3.0`, `status_color = None` | v14 compared a red **count** against `ceil(0.3·M)` where M grew with the registered module array. v15 is the frozen Worst-2 **mean** over independent governed signals and has no denominator that grows with the registry. |
| The same evidence beside a **63-row** module array | B1.4 → `Yellow` | B1.4 → `mean_worst_2 = 3.0` | Identical adverse evidence, two different v14 verdicts — the Run-27 structural defect, executed. v15 returns the same statistic in both. |
| The same package, B1.2 | `Red`, from weight literals `1.5 / 1.0 / 0.6 / 1.5` | **abstains**, naming the missing governed weighting policy | The four weights had no authority anywhere in the repository. §14 of the contract forbids inventing weights; a weighted vote with no governed policy weighs nothing. |
| The same package, B1.3, 63-row array | `total_votes = 66`, `Green` — sixty Green transformations outvote the adverse evidence | `total_votes = 2`, `Red`, with `mc`/`cusum` named as duplicate-lineage suppressed | v14 counted one vote per **registered module**; v15 counts one per **independent evidence body**. |
| Assembled package, B1.1 | `Red` | `Red` | **No difference, deliberately.** Conservative Dominance is byte-for-byte the same computation on both lines. Run 20 cycle 9's promotion is intact. |
| Assembled signals, B2.1 | `belief_red = 0.93` | identical | **No difference, deliberately.** Run 20 cycle 7's same-lineage Dempster fix is preserved, not rewritten. |

The suite proves three genuine divergences plus two deliberate non-divergences. It does not claim
to enumerate every divergence, and the freeze record says so.

## 3. The exact 24-target population, mechanically reconciled

Derived by `server/tools/build_run30_artifacts.py` from
`code_audit/run20_cycle12_100_reaudit.csv` — the Run-20 cycle-12 re-audit, which Run 26 established
is the population source of truth and is 1:1 with the registry — filtered to `category in {6, 7}`.
Nothing was transcribed by hand.

- Category 6 = **4** (6.1–6.4 → registry B1.1–B1.4)
- Category 7 = **20** (7.1–7.20 → registry B2.1–B2.20)
- **Total = 24**, unique identities = 24, duplicates = 0, unaccounted = 0.

This matches the owner's expected scope exactly. `code_audit/run30_cat6_7_scope.csv`.

## 4. Category 6 — before and after

| | v14 | v15 |
|---|---|---|
| What was synthesised | the three primary signals **plus every row of `simulationSignals.signal_array`** — every other module the run had computed | the **independent governed signals**: the assembled arms, with duplicate lineage collapsed to one reading per evidence body |
| B1.1 Conservative Dominance | maximum over signal bands (Run 20 cycle 9) | **unchanged**, and re-expressed canonically in `canonical_v5.conservative_dominance` for the oracles |
| B1.2 Weighted Voting | four weight literals with no authority; always produced a state | class-weighted voting `Vote(c) = Σ wᵢ·I(sᵢ=c)` over normalised weights, with a declared unique-winner/tie policy; **abstains** without a governed weighting policy |
| B1.3 Majority Rules | one vote per registered module; no quorum; ties resolved silently | one vote per eligible independent qualified signal; explicit quorum (2); a tie is reported as a **conflict**, not resolved |
| B1.4 Worst-N-of-M | red count vs `ceil(0.3·M)`, M growing with the registry | **frozen Worst-2 mean**: `MeanWorst2 = (s₁+s₂)/2`; no traffic-light boundary asserted |

The four remain **comparison/sensitivity regimes**. None became a voter. Voting is exactly A1.7 and
A1.8, asserted at freeze time from the registry.

## 5. Category 7 — before and after

v14: nineteen of the twenty modules manufactured an epistemic object from `cpi`, `spi` and
`docRiskScore`. B2.14 and B2.17 were proved by Run 27 to be informationally functions of
`min(cpi, spi)` alone.

v15: `server/app/simulation/canonical_v5.py` implements the canonical mathematics of each supplied
contract on a **governed defining structure**. The file reads no crisp KPI: there is no branch
anywhere in it reachable from `cpi`, `spi` or `docRiskScore`, so the proxy dependency the contracts
name as an implementation defect cannot recur in the canonical layer. Where the structure is
absent, the method abstains and reports no substitute figure.

**What is NOT yet done, stated plainly:** the twenty Category-7 *runners* in `models_fuzzy.py` and
`models_gov.py` still execute their v14 proxy arithmetic on the operational path. Run 30 supplied,
oracled and proved the canonical layer and the governed intake that feeds it, and rewired
Category 6; it did **not** repoint the twenty Category-7 runners at `canonical_v5`. That is the
single largest piece of remaining work and it is named again in §11 and §12 below rather than
implied to be complete.

## 6. Real-corpus reconciliation

`code_audit/run30_real_corpus_structure_reconciliation.csv`, 24 rows, each decided
**individually** against the extraction registry rather than by one blanket sentence — because
Run 29 proved a blanket "none are populated" can hide a wiring gap.

- **Corpus-present-but-unwired = 0.**
- **Three positive rows** (6.1, 6.3, 6.4): the four assembled arms *are* in the corpus and *do*
  reach their modules. This is the one place a Category-6/7 structure is genuinely populated, and
  it is wired.
- 6.2 and all twenty Category-7 rows: **genuinely absent**, each with its own reason. No field in
  the extraction registry is a weight, a mass over a stated frame, an assessed membership, a
  linguistic probability, a rule weight, a possibility degree, a designed state space, or a set of
  decision alternatives. The four arm masses the shipped B2.1 uses are **literals in the module**,
  not evidence any project supplied.
- No structure found present-and-unwired, so nothing needed wiring beyond what Category 6 already
  reaches. No epistemic parameter was inferred from a crisp metric anywhere.

## 7. Genuinely absent structures

Twenty-one of the twenty-four: 6.2 and 7.1–7.20. Each is **reasonably supplyable** through the
governed intake (`saveprojectdata` → `project_data.py`, append-only, period-effective) except the
three research-only laboratory structures (7.7, 7.9, 7.20), which are not sought in the corpus.
`code_audit/run30_supply_path_reconciliation.csv`: **reasonably supplyable structures with no
production path = 0**, because `governed_structure_keys()` now reads the v5 map and every one of
the nineteen keys is writable through the same store every other structure uses.

## 8. Modules correctly abstaining

Twenty-one of twenty-four abstain on the real corpus, and that is the correct answer rather than a
gap. Three compute: 6.1, 6.3 and 6.4 (the last as a statistic with no band).

## 9. Quantum Probability (7.9) — archival result

`canonical_v5.QUANTUM_ARCHIVE` and the freeze record carry every field §16 requires: stable id
`B2.9`; canonical name; historical implementation (`models_gov.py::run_quantum_probability`,
ported from `assets/js/simulations.js`); historical tests
(`test_run14_disabled_method_functional.py`, `test_run15_disabled_root_cause.py`); literature
record; reason archived; missing restoration evidence; restoration prerequisites; and
`operational_activation = False`, `voting = False`,
`participant_operational_visibility = False`.

**Restoration prerequisites, verbatim:** an explicit Hilbert-space state space over
project-control propositions with governed provenance; an explicit measurement/projection model;
empirical evidence of an order or context effect in project-control judgement that a classical
model does not account for; owner authorisation; and calibration and empirical validation under
Run 33.

The laboratory identity is kept as research history only: `|ψ⟩ = (1/√2)(|0⟩+|1⟩)` gives
`P(0) = 0.5` under the Born rule (verified). It is registered nowhere and is unreachable from any
operational path. B2.9 remains in `registry.DISABLED_CONCEPT_ONLY`. Participant package bytes did
not move, so no successor was created.

## 10. Plithogenic (7.7) and Hypersoft (7.20) — disabled proof

- B2.7 and B2.9 are both still in `registry.DISABLED_CONCEPT_ONLY` (asserted at freeze time, and
  fault-injected: F37, F38 both go red when removed).
- `plithogenic_lab()` returns `operational = False`, `operator = None`,
  `disposition = DISABLED_FUTURE_RESEARCH`, and names the operator block. No operator was chosen.
- `hypersoft_lab()` returns `operational = False` and `estimable = False` **even on a complete
  structure**, so Cartesian completeness cannot become activation (checked explicitly, and
  fault-injected as F39).
- Neither produces an operational v15 result, and neither is on the participant surface.

## 11. Remaining Run-31 (qualification) work

**No Category-9 LINEAGE finding is marked resolved.** Every Category-6/7 input still carries
`signal_qualification = "unqualified"` and the `CATEGORY_9_DEVIATION` sentence. Run 30 built no
competing gate.

The Run-17 anti-fossilisation register entry `ARCH/raw-bypass` is deliberately **kept**, and its
probe was **moved** from B1.2 to B1.3 — because B1.2 now abstains for an unrelated reason (no
weighting policy) and letting that abstention answer the proposition would have marked a Run-31
finding resolved by accident. B1.3 still computes a project state from unqualified evidence, which
is exactly what the proposition is about.

Remaining for Run 31: the qualification gate itself; deciding which signals are eligible; and the
`B3.1` declaration that specification §18 forbids in those words.

**Also remaining, and owned by no other run yet named:** repointing the twenty Category-7 runners
at `canonical_v5`, so the proxies stop executing on the operational path.

## 12. Remaining Run-33 (calibration / validation / parsimony) work

- The Worst-2 status boundaries. None was invented; the statistic is exposed with
  `classification = None` and a stated block.
- Weighted-voting weights; DST mass assignments and reliability discounts; neutrosophic T/I/F;
  interval bounds; Z-number reliability; PLTS probabilities; BRB rule and attribute weights; the
  Pythagorean, Picture, hesitant, Type-2, spherical and Fermatean memberships; possibility degrees;
  MARCOS externally governed criterion weights. **Zero of these were invented.**
- Empirical validation of every Category-6/7 reading.
- Final parsimony. **No fuzzy-family consolidation was carried out and none is authorised here.**
  Run 27's proof that B2.10–B2.17 are not mathematically identical stands and was re-verified.
- Category placement of MARCOS and CRITIC-TOPSIS is **Run 32's**, not Run 33's or Run 30's. Both
  keep stable identities in Category 7; neither was moved, renamed or deleted.

## 13. The complete 24-row closure table

`code_audit/run30_cat6_7_final_closure.csv`, generated mechanically from the registry and the
Run-30 scope. Rows = 24, unique identities = 24, duplicates = 0, unaccounted = 0.

| canonical_id | registry_id | module | canonical_structure_implemented | canonical_mathematics_implemented | production_supply_path | real_corpus_populated | parameter_provenance | oracle_pass | invalid_admissibility_pass | lineage_pass | operationally_computes | abstains | calibration_pending | run31_qualification_pending | run33_validation_parsimony_pending | disabled_or_archive_state | final_run30_disposition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 6.1 | B1.1 | Conservative Dominance | yes | yes | yes | yes | yes | yes | yes | yes | yes | when every signal abstains | no | the qualification gate that decides which signals are eligible | empirical validity of the synthesised state | ADVISORY_ONLY | SCIENTIFIC_PASS |
| 6.2 | B1.2 | Weighted Voting | yes | yes | yes | no | no | yes | yes | yes | no | always, on the real corpus | yes | the qualification gate | the weights and their calibration | ADVISORY_ONLY | PARAMETER_PROVENANCE_BLOCKED |
| 6.3 | B1.3 | Majority Rules | yes | yes | yes | yes | yes | yes | yes | yes | yes | on one voter or all-abstain | no | the qualification gate | empirical validity of the majority | ADVISORY_ONLY | METHOD_PASS_CALIBRATION_PENDING |
| 6.4 | B1.4 | Worst-N-of-M | yes | yes | yes | yes | yes | yes | yes | yes | yes, as a statistic with no band | on fewer than two independent signals | yes | the qualification gate | the boundaries and their calibration | ADVISORY_ONLY | METHOD_PASS_CALIBRATION_PENDING |
| 7.1 | B2.1 | Dempster-Shafer | yes | yes | yes | no | no | yes | yes | yes | no | with no governed mass functions | yes | the qualification gate | mass provenance and calibration | ADVISORY_ONLY | METHOD_PASS_CALIBRATION_PENDING |
| 7.2 | B2.2 | Rough Sets | yes | yes | yes | no | no | yes | yes | yes | no | with no governed decision table | yes | the qualification gate | attribute selection and validation | ADVISORY_ONLY | CORRECT_ABSTENTION |
| 7.3 | B2.3 | Neutrosophic Logic | yes | yes | yes | no | no | yes | yes | yes | no | with no governed assessment | yes | the qualification gate | the mapping and its validation | ADVISORY_ONLY | PARAMETER_PROVENANCE_BLOCKED |
| 7.4 | B2.4 | Interval Fuzzy Sets | yes | yes | yes | no | no | yes | yes | yes | no | with no governed assessment | yes | the qualification gate | the bounds and their calibration | ADVISORY_ONLY | PARAMETER_PROVENANCE_BLOCKED |
| 7.5 | B2.5 | Z-numbers | yes | yes | yes | no | no | yes | yes | yes | no | with no governed assessment or no reliability | yes | the qualification gate | the reduction operator, the terms and calibration | ADVISORY_ONLY | PARAMETER_PROVENANCE_BLOCKED |
| 7.6 | B2.6 | PLTS | yes | yes | yes | no | no | yes | yes | yes | no | with no governed assessment | yes | the qualification gate | the probabilities and their calibration | ADVISORY_ONLY | PARAMETER_PROVENANCE_BLOCKED |
| 7.7 | B2.7 | Plithogenic Sets | yes | yes | not applicable (research only) | no | no | yes | yes | yes | no | always: it is disabled | yes | nothing: it is not on the qualification path | operator selection is an owner decision; then calibration | DISABLED_UNSAFE | FUTURE_RESEARCH_ONLY |
| 7.8 | B2.8 | Belief Rule Base | yes | yes | yes | no | no | yes | yes | yes | no | with no governed rule base | yes | the qualification gate | the ER operator, the weights and calibration | ADVISORY_ONLY | PARAMETER_PROVENANCE_BLOCKED |
| 7.9 | B2.9 | Quantum Probability | yes | yes | not applicable (research only) | no | no | yes | yes | yes | no | always: it is archived | no | nothing: it is not on the qualification path | restoration prerequisites are an owner decision | DISABLED_UNSAFE | FUTURE_RESEARCH_ONLY |
| 7.10 | B2.10 | Pythagorean Fuzzy Sets | yes | yes | yes | no | no | yes | yes | yes | no | with no governed assessment | yes | the qualification gate | the memberships and their calibration | ADVISORY_ONLY | PARAMETER_PROVENANCE_BLOCKED |
| 7.11 | B2.11 | Picture Fuzzy Sets | yes | yes | yes | no | no | yes | yes | yes | no | with no governed assessment | yes | the qualification gate | the memberships and their calibration | ADVISORY_ONLY | PARAMETER_PROVENANCE_BLOCKED |
| 7.12 | B2.12 | Hesitant Fuzzy Sets | yes | yes | yes | no | no | yes | yes | yes | no | with no governed assessment or an empty set | yes | the qualification gate | the degrees and the choice of score | ADVISORY_ONLY | PARAMETER_PROVENANCE_BLOCKED |
| 7.13 | B2.13 | Type-2 Fuzzy Sets | yes | yes | yes | no | no | yes | yes | yes | no | with no governed membership | yes | the qualification gate | an exact Karnik-Mendel formulation is an owner decision; then calibration | ADVISORY_ONLY | PARAMETER_PROVENANCE_BLOCKED |
| 7.14 | B2.14 | Maximum Entropy | yes | yes | yes | no | no | yes | yes | yes | no | with no state space or constraints | yes | the qualification gate | constraint provenance and validation | ADVISORY_ONLY | CORRECT_ABSTENTION |
| 7.15 | B2.15 | Possibility Theory | yes | yes | yes | no | no | yes | yes | yes | no | with no governed distribution | yes | the qualification gate | the degrees and their calibration | ADVISORY_ONLY | PARAMETER_PROVENANCE_BLOCKED |
| 7.16 | B2.16 | Spherical Fuzzy Sets | yes | yes | yes | no | no | yes | yes | yes | no | with no governed assessment | yes | the qualification gate | the memberships and their calibration | ADVISORY_ONLY | PARAMETER_PROVENANCE_BLOCKED |
| 7.17 | B2.17 | Fermatean Fuzzy Sets | yes | yes | yes | no | no | yes | yes | yes | no | with no governed assessment | yes | the qualification gate | the memberships and their calibration | ADVISORY_ONLY | PARAMETER_PROVENANCE_BLOCKED |
| 7.18 | B2.18 | MARCOS Ranking | yes | yes | yes | no | no | yes | yes | yes | no | with no explicit alternatives | yes | the qualification gate | placement is Run 32; weights and validation Run 33 | ADVISORY_ONLY | OWNER_DECISION_REQUIRED |
| 7.19 | B2.19 | CRITIC-TOPSIS | yes | yes | yes | no | no | yes | yes | yes | no | with fewer than three alternatives or zero variance | no | the qualification gate | placement is Run 32; validation Run 33 | ADVISORY_ONLY | CORRECT_ABSTENTION |
| 7.20 | B2.20 | Hypersoft Sets | yes | yes | not applicable (research only) | no | no | yes | yes | yes | no | always: it is disabled | no | nothing: it is not on the qualification path | activation is an owner decision; then calibration | DISABLED_UNSAFE | FUTURE_RESEARCH_ONLY |
---

## 14. Per-module record

Every ORACLE RESULT below is the contract's own supplied number, carried as a literal in
`server/tools/test_run30_canonical_oracles.py` (**239/239 checks**) and never read back out of
production.

### 6.1 Conservative Dominance
- **SUPPLIED CONTRACT** — result = most severe credible eligible non-abstaining signal; `S_CD = max` severity. Green/Yellow/Amber → Amber. Green/Red/Red → Red. Permutation invariance, monotonicity, duplicate-lineage neutrality, abstention visibility, all-abstain → Not Estimable, unknown label rejected, one Red not averaged away. Do not redesign; do not alter voting.
- **v14 BEHAVIOUR** — already `SCIENTIFIC_PASS`: a genuine maximum over signal bands (Run 20 cycle 9).
- **v15 STRUCTURE/SUPPLY** — the four assembled arms, each carrying identity, state, period, source, lineage body, qualification state and abstention reason (`governed_signals_from_project`).
- **v15 IMPLEMENTATION** — production runner **unchanged**. `canonical_v5.conservative_dominance` re-expresses the same rule on governed signals for the oracle and the sibling regimes.
- **ORACLE RESULT** — Green/Yellow/Amber → **Amber** ✓. Green/Red/Red → **Red** ✓. Permutation invariant across all 6 orderings ✓. Monotone ✓. Duplicate lineage changes nothing and the duplicate is named ✓. One Red among forty Greens still dominates ✓.
- **ADMISSIBILITY/MISSINGNESS** — all-abstain → Not Estimable ✓; unknown label refused, never coerced ✓.
- **LINEAGE** — duplicate-lineage neutral by construction (idempotent maximum).
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, computing. Protected.
- **REMAINING WORK** — Run 31 qualification; Run 33 empirical validity.

### 6.2 Weighted Voting
- **SUPPLIED CONTRACT** — `Vote(c) = Σ wᵢ I(sᵢ=c)`, `argmax` under a declared unique-winner/tie policy, `wᵢ ≥ 0`, normalised to sum 1. Oracle: weights .5/.3/.2 on Green/Amber/Red → Green=.5, Amber=.3, Red=.2, winner Green. Equal weights must reduce to Majority Rules. Abstainers do not vote. Same-lineage duplicates must not manufacture weight. **Do not invent production weights.**
- **v14 BEHAVIOUR** — four literals (`cat1 1.5`, `cat4 1.0`, `cat7 0.6`, `cat9 1.5`) with no authority; voted the whole module array; always produced a state.
- **v15 STRUCTURE/SUPPLY** — `signalWeightPolicy`, requiring `set_by`, `authority` and a weight for **every** voting signal.
- **v15 IMPLEMENTATION** — `canonical_v5.weighted_voting`; runner rewired.
- **ORACLE RESULT** — Green **0.5**, Amber **0.3**, Red **0.2**, winner **Green** ✓. Weights sum to 1 ✓. Equal weights reduce to Majority Rules ✓. Duplicate lineage: Red gets **0.25**, not 0.4, and cannot flip the winner ✓.
- **ADMISSIBILITY/MISSINGNESS** — no policy → refusal ✓; policy omitting a voter → refusal ✓; negative weight → refusal ✓; no stated authority → refusal ✓; tie → **no winner**, policy declared ✓.
- **LINEAGE** — duplicates collapsed before weighting.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, **abstaining** on the real corpus. `PARAMETER_PROVENANCE_BLOCKED`.
- **REMAINING WORK** — Run 33 owns the weights and their provenance; Run 31 the qualification.

### 6.3 Majority Rules
- **SUPPLIED CONTRACT** — one vote per eligible independent qualified signal. Green/Red/Red → Red. Green/Yellow/Red → no unique winner. Green/Red/Abstain → tie/conflict. Explicit tie handling, all-abstain, quorum, unknown labels rejected, duplicate-lineage neutrality, severe-minority comparison. Missing evidence never defaults Green.
- **v14 BEHAVIOUR** — one vote per registered module; no quorum; ties resolved silently by insertion order.
- **v15 STRUCTURE/SUPPLY** — the governed signals.
- **v15 IMPLEMENTATION** — `canonical_v5.majority_rules`, quorum 2 (structural, not tuned).
- **ORACLE RESULT** — Green/Red/Red → **Red** ✓. Green/Yellow/Red → **no unique winner, conflict** ✓. Green/Red/Abstain → **tie/conflict**, abstainer visible ✓. All-abstain → Not Estimable, `counts.Green = 0` ✓. One voter → below quorum ✓. Duplicate lineage casts no second vote ✓. Severe minority: majority says Green where dominance says Red ✓.
- **ADMISSIBILITY/MISSINGNESS** — unknown label refused ✓; missing evidence never Green ✓.
- **LINEAGE** — one vote per independent body; suppressed duplicates named on the result.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, computing.
- **REMAINING WORK** — Run 31 qualification; Run 33 validity.

### 6.4 Worst-N-of-M
- **SUPPLIED CONTRACT** — **Worst-2-of-M** for M ≥ 2: sort descending, `MeanWorst2 = (s₁+s₂)/2`. **Not** `max(worst two)`. Do not invent final bands. Expose the two selected signals, their lineage, the number, and calibration pending. Oracles: Green/Amber/Red → 2.5; Green/Green/Red → 1.5; Amber/Amber/Yellow → 2.0. Permutation invariance, monotonicity, duplicate-lineage neutrality, M<2 → Not Estimable, abstentions removed before M, unknown labels rejected.
- **v14 BEHAVIOUR** — red count vs `ceil(0.3·M)`, amber count vs `ceil(0.4·M)`, M including every module row. Run 27's structural defect: identical adverse evidence gave Red at M=3 and Yellow at M=63.
- **v15 STRUCTURE/SUPPLY** — the governed signals.
- **v15 IMPLEMENTATION** — `canonical_v5.worst_two_of_m`; runner rewired; `status_color = None`.
- **ORACLE RESULT** — **2.5** ✓, **1.5** ✓, **2.0** ✓. Does not collapse to max ✓. Permutation invariant ✓. Monotone ✓. Duplicate lineage cannot occupy both positions: (3+0)/2 = **1.5**, selected signals rest on different bodies ✓. M<2 after abstentions → Not Estimable ✓. Sixty further module rows do not dilute identical adverse evidence ✓.
- **ADMISSIBILITY/MISSINGNESS** — unknown label refused ✓.
- **LINEAGE** — duplicates collapsed before the worst two are selected.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, computing **as a statistic with no band**.
- **REMAINING WORK** — Run 33 owns the boundaries.

### 7.1 Dempster-Shafer
- **SUPPLIED CONTRACT** — frame Θ, `m(∅)=0`, `Σm(A)=1`; Bel, Pl; `K = Σ_{B∩C=∅} m₁(B)m₂(C)`; `m₁₂(A) = Σ_{B∩C=A} m₁(B)m₂(C)/(1−K)`; reliability discount α. Oracle: `m₁({G})=.6, m₁(Θ)=.4`, `m₂({G})=.5, m₂(Θ)=.5` → `K=0`, `m({G})=.8`, `m(Θ)=.2`. Total-conflict oracle `m₁({G})=1, m₂({R})=1` → `K=1`, explicit TOTAL_CONFLICT/REVIEW, no divide-by-zero, no fabricated verdict. **Ignorance on Θ is not conflict.** Same-lineage evidence cannot be combined as independent.
- **v14 BEHAVIOUR** — four arm masses that are literals in the module, over four arms separated into bodies (Run 20 cycle 7). Correct as far as it went; not defined on real mass functions.
- **v15 STRUCTURE/SUPPLY** — `evidenceMassFunctions`: a frame and bodies, each naming `body_id` and `evidence_source`.
- **v15 IMPLEMENTATION** — `canonical_v5`: `read_mass_function`, `belief`, `plausibility`, `conflict_coefficient`, `dempster_combine`, `discount`, `dempster_shafer`. `assume_independent` has **no default**. The shipped B2.1 runner is untouched.
- **ORACLE RESULT** — `K = 0` ✓; `m({G}) = 0.8` ✓; `m(Θ) = 0.2` ✓; `Bel({G}) = 0.8`, `Pl({G}) = 1.0`, `Bel({R}) = 0` ✓. Ignorance: `K(m₁, vacuous) = 0` and combining with ignorance leaves `m({G}) = 0.6` unchanged ✓. Total conflict `K = 1` → `TOTAL_CONFLICT`, no division ✓. Discount α=.5 → `m'({G}) = 0.3`, `m'(Θ) = 0.7` ✓.
- **ADMISSIBILITY/MISSINGNESS** — masses not summing to 1 refused, **not rescaled** ✓; mass on ∅ refused ✓; no frame → Not Estimable ✓.
- **LINEAGE** — two bodies read off one `evidence_source` return `DEPENDENCE_UNRESOLVED`; without an independence assertion there is no combination.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting. Canonical layer abstains without governed masses.
- **REMAINING WORK** — mass provenance and calibration (Run 33); qualification (Run 31); repointing the runner.

### 7.2 Rough Sets
- **SUPPLIED CONTRACT** — universe, condition attributes, decision attribute, information/decision table, indiscernibility. `Lower_B(X)`, `Upper_B(X)`, boundary. Oracle: U={1,2,3,4}, classes {1,2} and {3,4}, X={1,3,4} → Lower={3,4}, Upper={1,2,3,4}, Boundary={1,2}. One project row is not a decision table; no table → Not Estimable.
- **v14 BEHAVIOUR** — a ratio of arm counts against the arm total.
- **v15 STRUCTURE/SUPPLY** — `roughDecisionTable`.
- **v15 IMPLEMENTATION** — `canonical_v5.rough_approximations`.
- **ORACLE RESULT** — Lower **{3,4}** ✓; Upper **{1,2,3,4}** ✓; Boundary **{1,2}** ✓; accuracy 2/4 = **0.5** ✓.
- **ADMISSIBILITY/MISSINGNESS** — a single case refused ✓; no decision attribute refused ✓; a case missing an attribute refused, nothing assumed ✓.
- **LINEAGE** — the table's own provenance travels.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — a governed historical decision table; Run 31; Run 33.

### 7.3 Neutrosophic Logic
- **SUPPLIED CONTRACT** — `N=(T,I,F)`, each in [0,1], need not sum to one, `I` independent. **Do not define `I = 1−T−F`.** `(.7,.2,.1)` preserved exactly; `(.7,.8,.1)` remains distinct. Reject components outside [0,1].
- **v14 BEHAVIOUR** — T/I/F derived from the arm bands.
- **v15 STRUCTURE/SUPPLY** — `neutrosophicAssessment`, all three stated separately or refused.
- **v15 IMPLEMENTATION** — `canonical_v5.neutrosophic`. There is no branch that computes `I`.
- **ORACLE RESULT** — `(.7,.2,.1)` preserved exactly ✓; `(.7,.8,.1)` preserved and distinct ✓; the two are not collapsed ✓; `I ≠ 1−T−F` demonstrated (`1−.7−.1 = .2 ≠ .8`) ✓.
- **ADMISSIBILITY/MISSINGNESS** — component outside [0,1] rejected ✓; an omitted indeterminacy refused, never derived ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — T/I/F provenance; Run 31; Run 33.

### 7.4 Interval Fuzzy Sets
- **SUPPLIED CONTRACT** — `μ(x)=[l,u]`, `0 ≤ l ≤ u ≤ 1`; v15 min/max operators. A=[.4,.7], B=[.5,.8] → ∩=[.4,.7], ∪=[.5,.8]. Reject invalid bounds. Do not manufacture spreads around crisp KPIs.
- **v14 BEHAVIOUR** — intervals built around the arm bands.
- **v15 STRUCTURE/SUPPLY** — `intervalFuzzyAssessment`.
- **v15 IMPLEMENTATION** — `interval_fuzzy`, `interval_intersection`, `interval_union`.
- **ORACLE RESULT** — ∩ = **[.4,.7]** ✓; ∪ = **[.5,.8]** ✓; a governed interval read as given ✓.
- **ADMISSIBILITY/MISSINGNESS** — `l > u` rejected ✓; `u > 1` rejected ✓; `l < 0` rejected ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — bound provenance; Run 31; Run 33.

### 7.5 Z-Numbers
- **SUPPLIED CONTRACT** — `Z=(A,B)`, both explicit; missing B must not silently become full reliability; same A with B_high vs B_low must stay distinguishable. **Do not invent a reduction operator unless one is already frozen.**
- **v14 BEHAVIOUR** — a reliability-weighted average over the arms.
- **v15 STRUCTURE/SUPPLY** — `zNumberAssessment`, restriction and reliability both required.
- **v15 IMPLEMENTATION** — `canonical_v5.z_number`. Reduction **blocked**: no exact reduction is frozen in the supervisory artifacts, so none was chosen.
- **ORACLE RESULT** — same A with B_high and B_low remain distinguishable ✓; `reduction = None` with the block named ✓.
- **ADMISSIBILITY/MISSINGNESS** — a missing reliability is **refused**, not read as full reliability ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — the reduction operator is an owner decision; then provenance and calibration.

### 7.6 PLTS
- **SUPPLIED CONTRACT** — `L(p) = {s_k(p_k)}`, `p_k ≥ 0`, `Σp_k = 1`. Green(.2)/Amber(.5)/Red(.3) valid; Amber(1) degenerate valid; negative invalid; sum ≠ 1 invalid.
- **v14 BEHAVIOUR** — probabilities derived from arm bands.
- **v15 STRUCTURE/SUPPLY** — `probabilisticLinguisticAssessment`.
- **v15 IMPLEMENTATION** — `canonical_v5.plts`.
- **ORACLE RESULT** — .2/.5/.3 sums to **1.0**, three terms kept ✓; Amber(1) valid and flagged degenerate ✓.
- **ADMISSIBILITY/MISSINGNESS** — negative probability invalid ✓; sum ≠ 1 refused, **not rescaled** ✓; duplicate term refused ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — linguistic-probability provenance; Run 31; Run 33.

### 7.7 Plithogenic Sets — DISABLED / FUTURE RESEARCH
- **SUPPLIED CONTRACT** — remain disabled; laboratory structure requires attributes, values, dominant value, appurtenance and contradiction degrees, and an explicitly selected operator. **If no exact operator contract is frozen, do not choose one.** No operational v15 result.
- **v14 BEHAVIOUR** — disabled; refused before input is read.
- **v15 STRUCTURE/SUPPLY** — `plithogenicLabStructure`, research-only.
- **v15 IMPLEMENTATION** — `canonical_v5.plithogenic_lab`. **No operator chosen**; none is frozen.
- **ORACLE RESULT** — structure read and verified complete ✓; `operational = False`, `operator = None`, `disposition = DISABLED_FUTURE_RESEARCH` ✓.
- **ADMISSIBILITY/MISSINGNESS** — appurtenance outside [0,1] refused ✓. Contradiction degrees are never inferred.
- **OPERATIONAL STATE** — DISABLED_UNSAFE, non-voting, no operational result.
- **REMAINING WORK** — operator selection is an owner decision (future research).

### 7.8 Belief Rule Base
- **SUPPLIED CONTRACT** — `β_j ≥ 0`, `Σβ_j ≤ 1`; antecedent reference values, rule weights, attribute weights, matching/activation degrees, consequent beliefs, ER aggregation. Single-rule oracle: fully activated rule with Green .7 / Amber .2 / Red .1 → exactly (.7,.2,.1). **Use only an exact frozen RIMER/ER formulation; if none is frozen, multi-rule aggregation remains blocked.**
- **v14 BEHAVIOUR** — a single rule matched on the arm bands.
- **v15 STRUCTURE/SUPPLY** — `beliefRuleBase`.
- **v15 IMPLEMENTATION** — `canonical_v5.belief_rule_base`. Multi-rule aggregation **blocked**.
- **ORACLE RESULT** — single fully activated rule → Green **0.7**, Amber **0.2**, Red **0.1**, aggregation named ✓. Two activated rules → `AGGREGATION_BLOCKED` ✓.
- **ADMISSIBILITY/MISSINGNESS** — `Σβ > 1` refused ✓; no attribute weights refused ✓; belief on a non-consequent refused ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — the ER variant is an owner decision; then weights and calibration.

### 7.9 Quantum Probability — ARCHIVED_FUTURE_RESEARCH
- **SUPPLIED CONTRACT** — preserve with the historical research line; do not delete; do not expose as runnable; activation false; voting false. Laboratory identity `|ψ⟩=(1/√2)(|0⟩+|1⟩)`, `P(0)=.5`.
- **v14 BEHAVIOUR** — disabled concept-only; refused before input is read.
- **v15 STRUCTURE/SUPPLY** — `QUANTUM_ARCHIVE` record; no project structure.
- **v15 IMPLEMENTATION** — `quantum_lab_born_rule`, registered nowhere.
- **ORACLE RESULT** — `P(0) = 0.5`, `P(1) = 0.5` ✓; archive record carries every §16 field ✓; activation/voting/participant-visibility all False ✓.
- **OPERATIONAL STATE** — DISABLED_UNSAFE, archived, non-operational, not on the participant surface.
- **REMAINING WORK** — restoration prerequisites (§9 above). Not counted as a runnable v15 capability.

### 7.10 Pythagorean Fuzzy Sets
- **SUPPLIED CONTRACT** — `μ²+ν² ≤ 1`, `π = √(1−μ²−ν²)`. Valid: (.6,.8) → 1.00, π=0. Invalid: (.8,.8) → 1.28.
- **v14 BEHAVIOUR** — memberships from `min(cpi,spi)` and the document risk score.
- **v15 STRUCTURE/SUPPLY** — `pythagoreanFuzzyAssessment`.
- **v15 IMPLEMENTATION** — `canonical_v5.pythagorean_fuzzy`, its own domain check.
- **ORACLE RESULT** — squared sum **1.00**, hesitancy **0** ✓; (.8,.8) → **1.28** and rejected, **not scaled** ✓; component > 1 rejected ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — membership provenance; Run 31; Run 33.

### 7.11 Picture Fuzzy Sets
- **SUPPLIED CONTRACT** — `μ,η,ν ≥ 0`, `μ+η+ν ≤ 1`, refusal `r = 1−μ−η−ν`. Oracle (.4,.2,.3) → r = .1. Reject sum > 1. Neutrality is distinct from missingness and refusal.
- **v14 BEHAVIOUR** — degrees from arm bands.
- **v15 STRUCTURE/SUPPLY** — `pictureFuzzyAssessment`.
- **v15 IMPLEMENTATION** — `canonical_v5.picture_fuzzy`, additive domain, its own check.
- **ORACLE RESULT** — refusal **0.1** ✓; the three degrees stay distinct from one another and from the refusal ✓; sum > 1 rejected ✓; negative component rejected ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — membership provenance; Run 31; Run 33.

### 7.12 Hesitant Fuzzy Sets
- **SUPPLIED CONTRACT** — `h(x) ⊂ [0,1]`; v15 laboratory score is the arithmetic mean (a PCEIF laboratory operator, not the only HFS score). `h={.2,.5,.7}` → 0.4666666667. Empty set rejected; one value returns itself; permutation invariance; outside [0,1] rejected. Do not generate hesitation by perturbing one crisp metric.
- **v14 BEHAVIOUR** — a degree set perturbed from one crisp metric.
- **v15 STRUCTURE/SUPPLY** — `hesitantFuzzyAssessment`.
- **v15 IMPLEMENTATION** — `canonical_v5.hesitant_fuzzy`; the operator is declared as laboratory scoring.
- **ORACLE RESULT** — score **0.4666666667** (= 1.4/3) ✓; single value returns itself (0.35) ✓; permutation invariant across all 6 orderings ✓.
- **ADMISSIBILITY/MISSINGNESS** — empty set → Not Estimable, **never favourable** ✓; degree outside [0,1] rejected ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — degree provenance and the choice of score; Run 31; Run 33.

### 7.13 Type-2 Fuzzy Sets
- **SUPPLIED CONTRACT** — genuine interval type-2 structure, `0 ≤ lower(x) ≤ upper(x) ≤ 1`, footprint preserved. Exact frozen Karnik-Mendel type reduction **only if** the supervisory artifacts contain a complete formulation sufficient for implementation and independent verification; otherwise implement the FOU structure and leave type reduction explicitly blocked. **No operational result from `(lower+upper)/2`.** Oracle: lower .3 / upper .7 → FOU [.3,.7], width .4; lower = upper = .5 → width 0, which is not missing data.
- **WHICH ARTIFACTS WERE CHECKED, AND WHAT WAS FOUND** — `research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md` (the only supervisory method specification in the repository), plus `NAMING_AUTHORITY.md`, `GROUP_ASSIGNMENT.md`, `T6_HANDOFF.md`, `remediation_programme.md`, `remediation_decisions_answered.md`, `server/app/simulation/VALIDATION.md`, the Run-27/28/29 reports and matrices, and a repository-wide search for *karnik*, *mendel* and *type reduc*. **The specification cites Karnik-Mendel by DOI at line 341 and, at line 2152, asks only that a centroid type reduction "if" used be tested against an independent reference. There is no formulation anywhere.** A citation is not a formulation.
- **WHAT WAS DONE** — the genuine IT2 membership and FOU structure was implemented, lower and upper preserved separately, admissibility verified, and the production supply path provided. **Type reduction and inference are explicitly blocked.** No formulation was invented, none was reconstructed from production, and midpoint averaging was not used as a substitute.
- **v15 STRUCTURE/SUPPLY** — `type2FuzzyAssessment`: per-point `x`, `lower`, `upper`.
- **ORACLE RESULT** — FOU **[.3,.7]** preserved as two separate bounds ✓; `FOU_width = 0.4` ✓; `FOU_width = 0` for lower = upper = .5, and `estimable = True` — zero width is a real assessment ✓; `type_reduced = None` with the block named ✓; no `(lower+upper)/2` figure is produced ✓.
- **ADMISSIBILITY/MISSINGNESS** — `lower > upper`, `upper > 1`, `lower < 0` all rejected ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — an exact Karnik-Mendel formulation is an owner decision; then calibration.

### 7.14 Maximum Entropy
- **SUPPLIED CONTRACT** — maximise `H(p) = −Σ p_i ln p_i` subject to `p_i ≥ 0`, `Σp_i = 1` and supplied moment constraints. Oracle A: two states, normalisation only → (.5,.5), `H = ln 2`. Oracle B: `x ∈ {0,1,2}`, `Σp x = 1` → (1/3,1/3,1/3), mean 1, `H = ln 3`. **Verify the optimizer actually solves the constrained problem.** Do not merely compute the entropy of a supplied vector; do not map `min(CPI,SPI)` into a result. Remove that dependency. Required structure: state space, constraints, provenance, optimization status, distribution, entropy, solver/version. No state space or constraints → NOT ESTIMABLE; infeasible → explicit.
- **v14 BEHAVIOUR** — entropy over a designed lookup table indexed by `min(cpi,spi)`; Run 27 proved it was informationally a function of that alone.
- **v15 STRUCTURE/SUPPLY** — `maximumEntropyProblem`: states, constraints with per-state values and an expectation, `defined_by` and `source`.
- **v15 IMPLEMENTATION** — `canonical_v5.maximum_entropy`: the convex **dual**, `p_i ∝ exp(Σλ_k f_k(x_i))`, `λ` minimising `ln Z(λ) − Σλ_k b_k` by Newton with a backtracking line search; gradient = constraint residual, Hessian = covariance of the constraint functions. The crisp-KPI dependency is gone: the function cannot reach a KPI.
- **ORACLE RESULT** — Oracle A: `p₁ = p₂ = 0.5`, `H = ln 2 = 0.6931471805599453` ✓. Oracle B: `p = (1/3, 1/3, 1/3)`, mean **1**, `H = ln 3 = 1.0986122886681098` ✓. **It genuinely optimises:** with mean 0.5 the constraint is met exactly, the solution moves off uniform, and its entropy is at least that of the best of a **1000-point independent grid search** over constraint-satisfying distributions (no production formula used) ✓.
- **ADMISSIBILITY/MISSINGNESS** — expectation outside the achievable range → `INFEASIBLE`, no distribution fabricated ✓; no states → Not Estimable ✓; a single state → refused ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — constraint provenance; Run 31; Run 33.

### 7.15 Possibility Theory
- **SUPPLIED CONTRACT** — normalised `π(x) ∈ [0,1]` with `sup π = 1`; `Π(A) = sup_{x∈A} π(x)`; `N(A) = 1 − Π(Aᶜ)`; maxitivity. Oracle: π(a)=1, π(b)=.4 → Π({a})=1, Π({b})=.4, Π({a,b})=1, N({a})=.6. **Do not normalise as a probability; do not require `Σπ = 1`.**
- **v14 BEHAVIOUR** — an unnormalised distribution with necessity computed as possibility less an invented 0.30 (partly corrected in Run 20 cycle 9).
- **v15 STRUCTURE/SUPPLY** — `possibilityAssessment`.
- **v15 IMPLEMENTATION** — `possibility`, `possibility_of`, `necessity_of`. No sum is computed anywhere for any purpose.
- **ORACLE RESULT** — Π({a}) = **1** ✓; Π({b}) = **0.4** ✓; Π({a,b}) = **1** ✓; N({a}) = **0.6** ✓. Maxitivity holds over **all 64 subset pairs** of a three-state universe ✓. The degrees sum to **1.4** and that is admissible ✓.
- **ADMISSIBILITY/MISSINGNESS** — no fully possible state → refused, **not rescaled** ✓; degree > 1 rejected ✓; no distribution → Not Estimable ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — possibility-degree provenance; Run 31; Run 33.

### 7.16 Spherical Fuzzy Sets
- **SUPPLIED CONTRACT** — `(μ,ν,π)` each in [0,1] with `μ²+ν²+π² ≤ 1`; three distinct components. Valid: (.6,.6,.5) → .97. Invalid: (.8,.8,.1) → 1.29. **Do not silently project an invalid tuple into the admissible region.**
- **v14 BEHAVIOUR** — components from the arm bands.
- **v15 STRUCTURE/SUPPLY** — `sphericalFuzzyAssessment`.
- **v15 IMPLEMENTATION** — `canonical_v5.spherical_fuzzy`, its own domain check.
- **ORACLE RESULT** — squared sum **0.97** ✓; three components remain distinct ✓; (.8,.8,.1) → **1.29** and rejected, not projected ✓; component outside [0,1] rejected ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — membership construction and operator are unsupplied, so the operational result remains method/parameter blocked; Run 31; Run 33.

### 7.17 Fermatean Fuzzy Sets
- **SUPPLIED CONTRACT** — `μ³+ν³ ≤ 1`. Valid: (.8,.7) → .855. Invalid: (.9,.9) → 1.458. Reject; **do not clamp or project**. Run 27's `min(cpi,spi)` finding is an implementation defect to remove, not evidence of redundancy.
- **v14 BEHAVIOUR** — memberships from `min(cpi,spi)`, with a `while (μ³+ν³ > 1) { μ *= 0.95; ν *= 0.95 }` renormalisation loop that reported a pair nobody assessed.
- **v15 STRUCTURE/SUPPLY** — `fermateanFuzzyAssessment`.
- **v15 IMPLEMENTATION** — `canonical_v5.fermatean_fuzzy`. **No renormalisation loop.** The crisp-KPI dependency is gone from the canonical layer.
- **ORACLE RESULT** — cubed sum **0.855** ✓; (.9,.9) → **1.458** and rejected, not shrunk ✓; component outside [0,1] rejected ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains.
- **REMAINING WORK** — membership provenance; Run 31; Run 33. **Not deleted, not consolidated.**

### 7.18 MARCOS Ranking
- **SUPPLIED CONTRACT** — a real alternatives × criteria problem; ≥2 alternatives, criteria, values, benefit/cost orientation, weights, decision matrix, ideal, anti-ideal, MARCOS normalisation, weighted matrix, utility degrees/functions, ranking. **Do not use CPI/SPI/docRiskScore as three "alternatives."** Benchmark: ≥3 alternatives, ≥3 criteria, ≥1 benefit and ≥1 cost, weights summing to 1, all intermediates hand-derived and frozen. Keep identity stable; do not move or delete; Run 32 owns placement; must not masquerade as project-condition evidence.
- **v14 BEHAVIOUR** — three project health values presented as three alternatives, with `_jsdiv` reproducing a JavaScript infinity limit.
- **v15 STRUCTURE/SUPPLY** — `decisionAlternatives`, **shared with 7.19** (§10 of the contract): context id, alternatives, criteria, values, units, orientation, governed weight with `weight_source`, period, provenance.
- **v15 IMPLEMENTATION** — `canonical_v5.marcos` over `decision_problem`.
- **ORACLE RESULT** — see §15 for every frozen intermediate. Production ranking = reference ranking = frozen ranking **A1 > A3 > A2** ✓; every `f(K)`, ideal, anti-ideal, `S_AI` and `S_AAI` matches to 1e-9 ✓. Identical alternatives tie ✓; a dominated alternative does not rank first ✓.
- **ADMISSIBILITY/MISSINGNESS** — a single alternative refused ✓; criteria presented as alternatives refused ✓; a criterion with no orientation refused ✓; weights with no stated provenance refused ✓.
- **LINEAGE** — the result carries `derived_from: "the decision alternatives supplied for this project; this ranking is not a further reading of the project's condition"` ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains (no project has explicit alternatives). Identity unchanged.
- **REMAINING WORK** — Run 32 placement; Run 33 weights and validation.

### 7.19 CRITIC-TOPSIS
- **SUPPLIED CONTRACT** — `C_j = σ_j Σ_k (1−r_jk)`, `w_j = C_j/ΣC`; TOPSIS normalisation, weights, `A⁺`/`A⁻`, `D⁺`/`D⁻`, `CC_i = D⁻/(D⁺+D⁻)`, rank descending. Benchmark: ≥4 alternatives, ≥3 criteria, ≥1 cost, non-zero variance; all intermediates frozen. Weights sum to 1; zero variance must not divide; identical alternatives tie; row permutation must not change the ranking; orientation changes ideal selection. Single row → NOT ESTIMABLE. Keep identity stable; Run 32 owns placement.
- **v14 BEHAVIOUR** — `CORRECT_ABSTENTION` on the flat path; a real decision structure only in the synthetic package.
- **v15 STRUCTURE/SUPPLY** — the same shared `decisionAlternatives` object.
- **v15 IMPLEMENTATION** — `canonical_v5.critic_topsis`.
- **ORACLE RESULT** — weights sum to **1** ✓; every σ, `C_j`, `w_j`, `D⁺`, `D⁻` and `CC` matches the independent reference to 1e-12 **and** the frozen literals to 1e-9 ✓; ranking = **A1 > A4 > A3 > A2** ✓; row permutation leaves the ranking unchanged ✓; identical alternatives tie ✓; reversing a criterion's orientation changes the ranking to A2 > A4 > A3 > A1 ✓.
- **ADMISSIBILITY/MISSINGNESS** — a single project row refused ✓; a zero-variance criterion **refused**, never silently divided by ✓.
- **LINEAGE** — `weights_are_algorithmic = True`; the ranking carries its decision-input lineage ✓.
- **OPERATIONAL STATE** — ADVISORY_ONLY, non-voting, canonical layer abstains. Identity unchanged.
- **REMAINING WORK** — Run 32 placement; Run 33 validation.

### 7.20 Hypersoft Sets — DISABLED / FUTURE RESEARCH
- **SUPPLIED CONTRACT** — attributes, **disjoint** attribute-value subspaces, their Cartesian product, and an explicit mapping for **every** admissible tuple. 2×2 oracle: A1={a1,a2}, A2={b1,b2} → all four tuples must exist. Delete (a2,b2) → explicit incomplete structure / abstention. **Do not silently supply 0, neutral, Green or a default.** No operational v15 result; no participant-facing implication that it is runnable.
- **v14 BEHAVIOUR** — disabled concept-only; refused before input is read.
- **v15 STRUCTURE/SUPPLY** — `hypersoftLabStructure`, research-only.
- **v15 IMPLEMENTATION** — `canonical_v5.hypersoft_lab`: builds the Cartesian product, checks disjointness, and reports missing tuples.
- **ORACLE RESULT** — all four tuples exist, `cartesian_size = 4`, `mapped = 4`, complete ✓; the product measured against is exactly (a1,b1),(a1,b2),(a2,b1),(a2,b2) ✓; deleting (a2,b2) gives `structure_complete = False`, `missing_tuples = [["a2","b2"]]`, and an abstention with a stated reason ✓; **even a complete structure returns `operational = False`** ✓.
- **ADMISSIBILITY/MISSINGNESS** — attributes sharing a value refused ✓; a mapping against an impossible tuple refused ✓; a duplicate mapping refused ✓.
- **OPERATIONAL STATE** — DISABLED_UNSAFE, non-voting, no operational result.
- **REMAINING WORK** — activation is an owner decision; then calibration.

---

## 15. MARCOS and CRITIC-TOPSIS benchmark provenance

`code_audit/run30_decision_ranking_oracles.csv`. Both benchmarks are labelled
**HAND_DERIVED_CANONICAL_FIXTURE**: constructed for Run 30, **not** taken from a published worked
example, and not presented as one.

**Independence proof.** `server/tools/run30/reference_mcdm.py` imports nothing from `app`, so no
production expression can be evaluated through it; it works on plain lists assembled by its own
reader rather than on the production structure objects; it was written from the published method
steps (Stević et al. 2020 for MARCOS, Diakoulaki et al. 1995 for CRITIC, Hwang & Yoon for TOPSIS)
as set out in the supplied contract, not by reading production. Production is compared against
**both** the reference and the frozen literals, so an error common to reference and production
would still have to match the frozen numbers.

### MARCOS — every intermediate frozen

3 alternatives × 3 criteria; C1 capability (benefit, w .5), C2 resilience (benefit, w .3),
C3 whole-life cost (cost, w .2); weights sum to 1.
A1 (4, 3, 2); A2 (2, 5, 4); A3 (3, 1, 1).

- Ideal **AI = (C1 4, C2 5, C3 1)**; anti-ideal **AAI = (C1 2, C2 1, C3 4)**.
- Normalised against the ideal (benefit `x/AI`, cost `AI/x`):
  A1 (1, .6, .5); A2 (.5, 1, .25); A3 (.75, .2, 1); AAI (.5, .2, .25); AI (1, 1, 1).
- `S = Σ w·n`: **S(A1) = .5(1)+.3(.6)+.2(.5) = 0.78**; **S(A2) = .25+.30+.05 = 0.60**;
  **S(A3) = .375+.06+.20 = 0.635**; **S_AAI = .25+.06+.05 = 0.36**; **S_AI = 1.0**.
- `K⁻ = S/S_AAI`: A1 **2.1666666667**, A2 **1.6666666667**, A3 **1.7638888889**.
  `K⁺ = S/S_AI`: A1 **0.78**, A2 **0.60**, A3 **0.635**.
- A1 worked through: `K⁺+K⁻ = 2.9466666667`; `f(K⁻) = .78/2.9466666667 = 9/34`;
  `f(K⁺) = 2.1666666667/2.9466666667 = 25/34`; `(1−f(K⁺))/f(K⁺) = 9/25 = 0.36`;
  `(1−f(K⁻))/f(K⁻) = 25/9 = 2.7777777778`; denominator `4.1377777778`;
  **f(K) = 2.9466666667 / 4.1377777778 = 0.7121374866**.
- `f(K)`: A1 **0.7121374866**, A2 **0.5477980666**, A3 **0.5797529538**.
- **Final ranking: A1 > A3 > A2.**

### CRITIC-TOPSIS — every intermediate frozen

4 alternatives × 3 criteria; C3 a cost criterion; non-zero variance on all three.
A1 (8, 5, 3); A2 (6, 7, 5); A3 (9, 4, 6); A4 (5, 8, 2).

- Min-max normalised with orientation, every column is a permutation of {0, .25, .75, 1}:
  C1 (8,6,9,5) → (.75,.25,1,0); C2 (5,7,4,8) → (.25,.75,0,1); C3 cost (3,5,6,2) → (.75,.25,0,1).
- Each column has mean .5 and sample variance .625/3, so
  **σ = √0.2083333 = 0.4564354646** for all three.
- Correlations: **r(C1,C2) = −1 exactly** (C2 = 1 − C1); **r(C1,C3) = −0.375/0.625 = −0.6**;
  **r(C2,C3) = +0.6**.
- `C_j = σ_j Σ_k (1−r_jk)`:
  **C_C1 = .4564354646 × (0 + 2 + 1.6) = 1.6431676725**;
  **C_C2 = .4564354646 × (2 + 0 + 0.4) = 1.0954451150**;
  **C_C3 = .4564354646 × (1.6 + 0.4 + 0) = 0.9128709292**; sum **3.6514837167**.
- **Weights w = (C1 0.45, C2 0.30, C3 0.25) exactly**, summing to 1.
- TOPSIS on the vector-normalised, weighted matrix with ideals by orientation gives
  **CC = A1 0.6078816913, A2 0.3921183087, A3 0.4533710992, A4 0.5466289008**.
- **Final ranking: A1 > A4 > A3 > A2.** Reversing C3's orientation gives A2 > A4 > A3 > A1.

## 16. Fuzzy-family cross-check (§8 and §20)

Seven **separate** implementations, each stating its own defining constraint in its own terms;
there is no generic tuple validator any of them delegates to (asserted: seven distinct function
objects). Results:

| family | own valid case | own invalid control |
|---|---|---|
| Pythagorean | (.6,.8) → μ²+ν² = 1.00, π = 0 — **valid** | (.8,.8) → 1.28 — **rejected, not scaled** |
| Fermatean | (.8,.7) → μ³+ν³ = .855 — **valid** | (.9,.9) → 1.458 — **rejected, not shrunk** |
| Spherical | (.6,.6,.5) → .97 — **valid** | (.8,.8,.1) → 1.29 — **rejected, not projected** |
| Picture | (.4,.2,.3) → r = .1 — **valid** | (.5,.4,.3) → sum 1.2 — **rejected** |
| Interval | [.4,.7] — **valid** | [.7,.4], [.4,1.4], [−.1,.4] — **all rejected** |
| Hesitant | {.2,.5,.7} → .4666666667 — **valid** | ∅ and {.2,1.5} — **rejected** |
| Type-2 | lower .3 / upper .7, width .4 — **valid** | lower > upper, upper > 1, lower < 0 — **rejected** |

**Cross-family, same dimensions.** `(.8,.7)` is **valid Fermatean** (.855 ≤ 1) and **invalid
Pythagorean** (.64+.49 = 1.13 > 1): one tuple, two verdicts, so the two domains are not one. Over a
441-point grid every Pythagorean-admissible pair is Fermatean-admissible and the containment is
**strict** — the domains are nested, not identical. `(.6,.6,.5)` is **valid Spherical** and
**invalid Picture** (additive sum 1.7), separating the power-sum families from the additive one.
Where representation dimensions differ (interval vs hesitant vs type-2) the tuples are **not**
cross-cast; what is asserted is that each refuses the others' shape. No silent clamping, no silent
normalisation into another family, and representation fields remain distinct throughout.

## 17. Supply-path reconciliation

`code_audit/run30_supply_path_reconciliation.csv`, 24 rows. Source types used:
`EXISTING_QUALIFIED_SIGNAL` (6.1, 6.3, 6.4), `EXPERT_ELICITATION` (6.2, 7.1, 7.3–7.6, 7.8,
7.10–7.13, 7.15–7.17), `PROJECT_DATA_OBJECT` (7.14), `HISTORICAL_DECISION_TABLE` (7.2),
`DECISION_ALTERNATIVES_OBJECT` (7.18, 7.19), `RESEARCH_ONLY_LAB_STRUCTURE` (7.7, 7.9, 7.20).

**Reasonably supplyable structures with no production path = 0.** The nineteen v5 keys are all in
`governed_structure_keys()`, which is now the union of the canonical, v3, v4 **and v5** maps, so
every one is writable through `saveprojectdata` → `project_data.py`. A structure name existing only
in a test would not have counted, which is why the intake was extended rather than described.
No epistemic parameter was populated with a default anywhere.

## 18. Lineage and dependence (§17)

- **false reinforcement = 0.** Four probes: a same-lineage duplicate gains no Weighted Voting
  weight; casts no second Majority vote; cannot occupy both Worst-2 positions; and two DST bodies
  read off one source return `DEPENDENCE_UNRESOLVED`.
- **false suppression = 0.** Four probes: two genuinely independent adverse bodies give
  `counts.Red = 2`, `MeanWorst2 = 3.0`, dominance `Red`, and a genuine DST combination.
- The four Category-6 regimes read **one** signal set and each reports what it considered, so a
  reader combining two of their outputs is visibly combining one body twice. They legitimately
  disagree (Red / 2.5 / no unique winner on the same input), which is what makes them comparison
  regimes rather than four project facts.
- **Dependence is not transitive.** `independent_signals` is a pairwise operation over a declared
  evidence body with **no transitive closure and no connected-component partitioning**. Asserted:
  bodies X and Y stay separate when a third names both. The production assembler uses
  `arm_lineage.separate_arms`, the existing pairwise model, resolved against the project's own
  evidence.
- MARCOS and CRITIC-TOPSIS rankings carry `derived_from` naming their decision inputs and are not
  independent project-condition evidence.

## 19. Non-vacuity campaign — all 39 mandated faults

`server/tools/test_run30_non_vacuity.py` (**120/120 checks**), record in
`code_audit/run30_fault_injection.csv`.

Each fault replaces a production function or constant with a mutant reintroducing the named
defect; the injection is **confirmed applied by re-reading the attribute off the module**; the
guard must go red for the intended reason, with both probe values recorded; then restored and
observed green. A crash is reported as a crash and never counted as red.

**39 attempted, 39 `RED_THEN_GREEN`, 0 `INJECTION_NOT_APPLIED`, 0 not proven.**

| # | fault | baseline → injected |
|---|---|---|
| 1 | Conservative Dominance averages away a Red | `Red` → `Yellow` |
| 2 | Weighted Voting consumes raw cpi/spi rather than governed states | weighed `['mc']` → weighed `['cpi']` |
| 3 | Weighted Voting same-lineage duplicate gains weight | Red weight `0.25` → `0.4` |
| 4 | Majority unknown label becomes Green | refusal → accepted |
| 5 | Majority same-lineage duplicate gains a vote | `1` → `2` |
| 6 | Worst-N uses max and collapses to Conservative Dominance | `1.5` → `3` |
| 7 | Worst-N duplicate lineage occupies both worst positions | `1.5` → `3.0` |
| 8 | DST treats ignorance as conflict | `K = 0.0` → `K ≠ 0` |
| 9 | DST total conflict divides by zero or fabricates a verdict | `TOTAL_CONFLICT` → `COMBINED` |
| 10 | DST same-lineage masses combine independently | `DEPENDENCE_UNRESOLVED` → `COMBINED` |
| 11 | Rough Sets executes without a decision table | refusal → result |
| 12 | Neutrosophic I silently defined as 1−T−F | `0.8` → `0.2` |
| 13 | Invalid Interval Fuzzy bounds accepted | refusal → accepted |
| 14 | Z-number missing B becomes full reliability | refusal → accepted |
| 15 | PLTS probabilities not summing to one accepted | refusal → accepted |
| 16 | Plithogenic becomes operational | `False` → `True` |
| 17 | BRB invalid belief distribution accepted | refusal → accepted |
| 18 | Quantum becomes operational/runnable | `(False,False,False)` → `(True,True,True)` |
| 19 | Invalid Pythagorean tuple accepted | refusal → accepted |
| 20 | Invalid Picture tuple accepted | refusal → accepted |
| 21 | Hesitant empty set becomes favourable | refusal → score 1.0 |
| 22 | Type-2 inference collapses to interval midpoint | `None` → `0.5` |
| 23 | Maximum Entropy merely calculates entropy of a supplied vector | mean `0.5` → `1.0` |
| 24 | Maximum Entropy runs with no state space/constraints | refusal → result |
| 25 | Possibility violates maxitivity | residual `0.0` → non-zero |
| 26 | Possibility normalised as probability | Σπ `1.4` → `1.0` |
| 27 | Invalid Spherical tuple accepted | refusal → accepted |
| 28 | Invalid Fermatean tuple accepted | refusal → accepted |
| 29 | MARCOS treats criteria as alternatives | refusal → result |
| 30 | MARCOS accepts one project state as an alternatives problem | refusal → result |
| 31 | CRITIC-TOPSIS accepts one project row | refusal → result |
| 32 | CRITIC-TOPSIS zero-variance criterion silently divides | refusal → result |
| 33 | Hypersoft missing Cartesian tuple defaults favourable | incomplete+named → complete |
| 34 | orphan canonical structure has no production path | all keys consumed → orphan `B2.99` |
| 35 | corpus-present structure disconnected from its module | `Red` → abstention |
| 36 | duplicate simulation-version stamp | unique → duplicate v14 |
| 37 | archived Quantum appears on the current operational surface | in disabled set → removed |
| 38 | disabled Plithogenic becomes active | in disabled set → removed |
| 39 | disabled Hypersoft becomes active | `(False, DISABLED_FUTURE_RESEARCH)` → `(True, ACTIVE)` |

One fault (#2) and one (#34) were **repaired mid-campaign** rather than scored: #2's first probe
could not distinguish the fault because Weighted Voting abstained either way, and #34's first probe
was circular because the intake derives its vocabulary from the map under mutation. Both were
rewritten to probe something the fault can actually move, which is the campaign-repair discipline
the contract requires. One injection site in an inherited suite (`test_run2_fifteen_defects.py`)
had **moved** — the v15 ensembles read the vocabulary through `fusion.normalise_status`, not
through a name bound in `models_gov` — and the injection was repointed rather than scored.

## 20. Package preservation

- **Simulation chain** — 15 stamps, all unique, append-only, none rewritten. The v14 tuple read
  from git object `ac7c011` is a strict prefix of the current tuple and grew by exactly one.
- **Synthetic chain** — OG-SYNTH 0.1 / 0.2 / 0.3 / **0.4 current**. **No successor was created,
  and that is a finding rather than an omission.** §15 requires an in-scope fixture that encodes
  the *old proxy* to be replaced now; every Category-6/7 fixture in the package was inspected and
  none does. The only Category-7 fixture the package carries is B2.19 CRITIC-TOPSIS, and its
  structure is already a real alternatives-by-criteria decision problem
  (`package_B_reference_training_decisions/B3_decision_optimization/`:
  `alternative_criteria_matrix.csv`, `criteria.csv`, `ground_truth_decisions.csv`) — exactly what
  the supplied contract requires, and not a proxy. Minting a package identifier for bytes nobody
  changed is the masquerade the chain's own rule 4 forbids. The Run-30 canonical fixtures live in
  `server/tools/run30/fixtures_cat67.py`, are test-only, and every one carries
  `data_origin = SYNTHETIC_RESEARCH_FIXTURE` and `not_for_empirical_validation = True`.
  All predecessors are unchanged and their records still verify.
- **Participant chain** — v1 (`c44e3ce`), v2 (`0293dc5`), v3 (pinned `01e943e`), **v4 current**.
  **Unchanged by this run**, so no successor was created: the three Category-6 ensembles are
  ADVISORY_ONLY and were already off the participant operational surface; Quantum and Plithogenic
  were already disabled and stay disabled; no registry qualifier was removed and no served
  participant evidence object changed. No predecessor record was regenerated in place.
  **Participant experimental sequence unchanged.**
- **Freeze chain** — `RUN30_CANONICAL_CAT6_7_FREEZE_2026-08-16.json` supersedes
  `RUN29_CLOSURE_FREEZE_2026-08-16.json` (following `RUN29-CLOSURE-V14-1`), naming it as parent and
  carrying its digest. The parent and every freeze behind it are untouched.
- **Production-tree guard** — extended, not weakened. `canonical_v5.py` was deliberately added to
  the governed inventory: declared in `server/tools/run30_production_changes.py`
  (`RUN30_NEW_PRODUCTION_FILES`), added to the scoped-file lists in `test_run6_known_answer.py` and
  `test_run8_retest_classify_27.py`, and covered by the new pinned manifest
  `code_audit/run30_production_tree.sha256` (230 files). The guard was turned **red first and
  observed** reporting `added: [canonical_v5.py]` and `changed: [models_gov.py]` before anything
  was declared. The declared-changes manifest's changed-file list is **empty**, because
  `models_gov.py` is already declared by Run 20, `project_data.py` by Run 29 and `models.py` by
  Run 28, and **no path may appear in two manifests**.

## 21. Acceptance criteria (§27), answered one by one

| criterion | state |
|---|---|
| scope = 24/24 | **met**, mechanically reconciled |
| v14 preserved | **met** |
| v15 established and behaviourally justified | **met**, by executing the predecessor line |
| Conservative Dominance remains correct | **met**, byte-for-byte unchanged |
| Weighted Voting = class-weighted voting | **met** |
| Majority Rules handles tie/quorum/abstention | **met** |
| Worst-N = frozen Worst-2 mean statistic | **met** |
| Worst-N final bands not invented | **met** |
| DST ignorance ≠ conflict | **met** |
| DST total conflict handled explicitly | **met** |
| DST dependent duplicates cannot reinforce | **met** |
| Rough Sets requires a real decision table | **met** |
| Neutrosophic indeterminacy remains independent | **met** |
| Interval Fuzzy admissibility correct | **met** |
| Z-number reliability remains explicit | **met** |
| PLTS normalisation correct | **met** |
| Plithogenic disabled | **met** |
| BRB structure/admissibility correct to supplied level | **met** |
| Quantum archived and non-operational | **met** |
| Pythagorean / Picture / Hesitant / Spherical / Fermatean admissibility | **met** |
| Type-2 not represented by midpoint averaging | **met** |
| Maximum Entropy actually optimizes under constraints | **met** |
| Possibility obeys maxitivity | **met** |
| MARCOS / CRITIC-TOPSIS use explicit alternatives | **met** |
| Hypersoft Cartesian completeness enforced; Hypersoft disabled | **met** |
| corpus-present-but-unwired = 0 | **met** |
| reasonably supplyable structures without production path = 0 | **met** |
| unsupported epistemic parameters invented = 0 | **met** |
| false reinforcement = 0 / false suppression = 0 | **met** |
| stale in-scope synthetic fixtures = 0 | **met** (none found; see §20) |
| unauthorized renames = 0 | **met** |
| voting = exactly 2 | **met** (A1.7, A1.8) |
| Material Cost Variance remains disabled | **met** (A3.4 in `DISABLED_MODULES`) |
| participant experimental sequence unchanged | **met** |
| full suite green on exact final pushed head | **met**, see §22 |

**One acceptance item is met at the canonical layer and NOT at the operational runner, and I am
stating it rather than letting the table imply otherwise:** the twenty Category-7 *runners* still
execute their v14 proxy arithmetic on the operational path. `canonical_v5` is correct, oracled,
fault-injected and reachable through the governed intake, and Category 6 is fully rewired; the
Category-7 runners are not yet repointed at it. Until that is done, a Category-7 row on the ledger
is still the old proxy reading. Nothing in this report should be read as claiming otherwise.

## 22. Exact final-head verification

Recorded after the final commit landed, with the complete suite re-run on that exact head:

- `HEAD == main == origin/main`, tree clean.
- **Suites run: 141. Total checks: 11867/11867. ALL SUITES GREEN.**
- Final simulation version: **`sim-2026.08-v15`**.
- Exact final merged `main` commit: recorded in §23 below.

The suite was **not** inherited from an earlier commit: it was executed after the report-landing
commit, against a fresh migrated SQLite database per test file, with `PYTHONIOENCODING=utf-8`, via
`server/run_all_suites.sh` (which accepts only an anchored `^RESULT: N/M( checks passed)?$` line
and fails on a non-zero exit). The interpreter was confirmed real before the run.

## 23. Final head

See the closing section of `T6_HANDOFF.md` for the exact merged-main commit hash, which is written
there by the same commit that lands this report.

## 24. What Run 30 did not do

- It did **not** repoint the twenty Category-7 operational runners at `canonical_v5`. §5 and §21.
- It did **not** implement, complete or close the Category-9 qualification gate. Run 31.
- It did **not** invent a Karnik-Mendel formulation, an ER variant, a Z reduction or a plithogenic
  operator, because none is frozen in the supervisory artifacts. §7.5, §7.7, §7.8, §7.13.
- It did **not** invent a single membership, mass, linguistic probability, rule weight,
  distribution or threshold.
- It did **not** consolidate the fuzzy family, move or rename MARCOS or CRITIC-TOPSIS, expand
  voting, reactivate Material Cost Variance, activate any disabled or archived method, or change
  the participant experimental sequence.
- It did **not** launch Run 31.

---
---

# RUN 30 CLOSURE ADDENDUM — the operational Category-7 path itself, sim-2026.08-v16

## 0. The defect

**Category-7 canonical mathematics existed, but the operational runners still executed legacy
proxy arithmetic.**

This report disclosed it, in §5, §21 and §23. The owner refused to let it travel to another run,
and was right to. `canonical_v5.py` was correct, oracled against the contracts' own numbers 239
ways, and fault-injected 39 ways — and production never called it. **Every direct-call proof of
that layer was green for the entire time the defect existed.** That is why nothing in this closure
proves anything by calling `canonical_v5`: every claim below is made by executing
`registry.run_module`, the same entry point that builds real ledger rows, and recording from the
interpreter (`sys.setprofile`) which functions actually ran.

## 1. The twenty routes BEFORE, proved by execution

Not inferred from filenames. `registry.run_module` executed for each identity on its production
input shape, with the interpreter profiled.

**`canonical_v5` reached: 0 of 20.**

| id | what actually executed | legacy functions that ran |
|---|---|---|
| B2.1 | `models_gov.run_dst` | 0 in the scanned proxy modules; its own arm-mass arithmetic |
| B2.2 | `models_evc.run_rough_sets` | 6 |
| B2.3 | `models_evc.run_neutrosophic` | 7 |
| B2.4 | `models_evc.run_interval_fuzzy` | 13 |
| B2.5 | `models_evc.run_z_numbers` | 7 |
| B2.6 | `models_evc.run_plts` | 7 |
| B2.7 | registry disabled gate; no runner reached | 0 |
| B2.8 | `models_evc.run_brb` | 4 |
| B2.9 | registry disabled gate; no runner reached | 0 |
| B2.10 | `models_fuzzy.run_pythagorean_fuzzy` | 2 |
| B2.11 | `models_fuzzy.run_picture_fuzzy` | 1 |
| B2.12 | `models_fuzzy.run_hesitant_fuzzy` | 3 |
| B2.13 | `models_fuzzy.run_type2_fuzzy` | 2 |
| B2.14 | `models_fuzzy.run_maximum_entropy` | 3 |
| B2.15 | `models_fuzzy.run_possibility_theory` | 3 |
| B2.16 | `models_fuzzy.run_spherical_fuzzy` | 1 |
| B2.17 | `models_fuzzy.run_fermatean_fuzzy` | 1 |
| B2.18 | `models_fuzzy.run_marcos` | 4 |
| B2.19 | `models_fuzzy.run_critic_topsis` | 1 |
| B2.20 | registry disabled gate; no runner reached | 0 |

Seventeen executed proxy arithmetic. Three were short-circuited as disabled.

## 2. The twenty routes AFTER

`code_audit/run30_cat7_operational_route_inventory.csv` and
`code_audit/run30_cat7_operational_execution.csv`, both generated by executing the route.

**Canonical function reached: 17 of 17 operational identities. Legacy proxy reached: 0 of 20.**

| id | canonical functions that actually executed | legacy reached |
|---|---|---|
| B2.1 | `v5_structure`, `read_mass_function`, `conflict_coefficient`, `dempster_combine`, `belief`, `plausibility`, `dempster_shafer` | no |
| B2.2 | `v5_structure`, `rough_approximations` | no |
| B2.3 | `v5_structure`, `_unit`, `neutrosophic` | no |
| B2.4 | `v5_structure`, `_unit`, `_interval`, `interval_fuzzy` | no |
| B2.5 | `v5_structure`, `z_number` | no |
| B2.6 | `v5_structure`, `plts` | no |
| B2.7 | canonical operational gate refused before any mathematics | no |
| B2.8 | `v5_structure`, `_unit`, `belief_rule_base` | no |
| B2.9 | canonical operational gate refused before any mathematics | no |
| B2.10 | `v5_structure`, `_unit`, `pythagorean_fuzzy` | no |
| B2.11 | `v5_structure`, `_unit`, `picture_fuzzy` | no |
| B2.12 | `v5_structure`, `_unit`, `hesitant_fuzzy` | no |
| B2.13 | `v5_structure`, `_unit`, `_interval`, `type2_fuzzy` | no |
| B2.14 | `v5_structure`, `maximum_entropy` (with its dual solver) | no |
| B2.15 | `v5_structure`, `_unit`, `possibility` | no |
| B2.16 | `v5_structure`, `_unit`, `spherical_fuzzy` | no |
| B2.17 | `v5_structure`, `_unit`, `fermatean_fuzzy` | no |
| B2.18 | `v5_structure`, `_reference_material_guards`, `decision_problem`, `marcos` | no |
| B2.19 | `v5_structure`, `_reference_material_guards`, `decision_problem`, `critic_topsis` | no |
| B2.20 | canonical operational gate refused before any mathematics | no |

All twenty resolve to `app.simulation.models_cat7`, read live from `registry.VALIDATED`.

## 3. Legacy proxy paths: classification and non-reachability

| implementation | classification | proof |
|---|---|---|
| `models_evc.py` B2.2–B2.6, B2.8 (+ disabled B2.7, B2.9) | **HISTORICAL_ONLY** | present in tree; no production identity resolves to it |
| `models_fuzzy.py` B2.10–B2.20 | **HISTORICAL_ONLY** | same |
| `models_gov.run_dst` (B2.1) | **HISTORICAL_ONLY** | same; still exercised directly by the Run-6 known-answer suite |

**Current production-reachable legacy Category-7 paths = 0.**

They are **preserved, not deleted**. Run 19's Category-7 audit (229 checks), Run 27's parsimony
proofs and Run 14's disabled-method suite were all made *about* these implementations; deleting
them would delete the evidence for nineteen findings along with the defect. Each of those suites
now resolves them through the legacy extension maps **read live**, and each asserts separately
that no production identity reaches them.

**The guard is not a hand-written list.** `test_run30_cat7_operational_route.py` enumerates
`registry.VALIDATED` — the shipped routing table — and profiles the interpreter. A list restating
the dispatcher would stay green when the dispatcher changed underneath it, which is the failure
mode the owner named explicitly.

## 4. Production-dispatcher oracle results

Every value below came back from `registry.run_module`. `canonical_v5` is not called anywhere in
that section.

| method | expected (supplied contract) | through production |
|---|---|---|
| 7.1 Dempster-Shafer | m({G}) = .8, K = 0 | **0.8**, **0.0** ✓ |
| 7.2 Rough Sets | Lower {3,4}, Upper {1,2,3,4}, Boundary {1,2} | exact ✓ |
| 7.3 Neutrosophic | (.7,.2,.1) exact; (.7,.8,.1) distinct | exact, distinct ✓ |
| 7.4 Interval Fuzzy | [.4,.7] as given | **[0.4, 0.7]** ✓ |
| 7.6 PLTS | probabilities sum to 1 | **1.0** ✓ |
| 7.8 Belief Rule Base | one fully activated rule → (.7,.2,.1) | exact ✓ |
| 7.10 Pythagorean | π = 0 for (.6,.8) | **0.0** ✓ |
| 7.11 Picture | refusal .1 for (.4,.2,.3) | **0.1** ✓ |
| 7.12 Hesitant | score .4666666667 | **1.4/3** ✓ |
| 7.13 Type-2 | FOU width .4 | **0.4**, and `type_reduced` is **None** ✓ |
| 7.14 Maximum Entropy | H = ln 3, mean = 1 | **1.0986122886681098**, **1.0** ✓ |
| 7.15 Possibility | degrees sum to 1.4 and that is admissible | **1.4** ✓ |
| 7.16 Spherical | (.6,.6,.5) distinct components | exact ✓ |
| 7.17 Fermatean | (.8,.7) as given, not shrunk | exact ✓ |
| 7.18 MARCOS | A1 > A3 > A2 | **A1 > A3 > A2** ✓ |
| 7.19 CRITIC-TOPSIS | A1 > A4 > A3 > A2; weights sum 1 | exact, **1.0** ✓ |

**The blocked operators survived the routing pressure**, which is the moment they were most at
risk: 7.5 returns `reduction = None` with the block named; 7.8 on two activated rules returns
`OPERATOR_BLOCKED / AGGREGATION_BLOCKED`; 7.13 produces no reduced figure at all; 7.20 produces
no operational reading on a complete *or* an incomplete structure.

## 5. Real corpus, before and after

`code_audit/run30_cat7_real_corpus_route.csv`. The "before" column is a **measurement**: the
preserved legacy implementation executed on the identical input, not a memory.

| id | v15 would have returned | v16 returns |
|---|---|---|
| B2.1 | Red — Belief G 4% / A 46% / R 49%, conflict 68% | abstains, awaiting mass functions |
| B2.2 | Red — Borderline Amber/Red, 1 of 2 signals | abstains, awaiting a decision table |
| B2.3 | Red — T=0.95 I=0.04 F=0.01 | abstains, awaiting three independent degrees |
| B2.4 | Amber — Green [0,0.38] Amber [0.41,0.68] Red [0,0.59] | abstains, awaiting a membership range |
| B2.5 | Red — reliability-weighted Red 0.85 | abstains, awaiting a stated reliability |
| B2.6 | Amber — P(G)=6% P(A)=49% P(R)=45% | abstains, awaiting linguistic probabilities |
| B2.7 | disabled, unchanged | disabled, and it now says so truthfully |
| B2.8 | Red — BRB belief G 5% A 25% R 70% | abstains, awaiting a rule base |
| B2.9 | disabled, unchanged | archived, and it now says so truthfully |
| B2.10 | Amber — μ=0.23 ν=0.51 π=0.83 | abstains, awaiting an assessed pair |
| B2.11 | Amber — +0.26 0 −0.48 r0.26 | abstains |
| B2.12 | Amber — avg membership 0.33 | abstains, awaiting a degree set |
| B2.13 | Red — **centroid 0.26**, FOU 0.04 | abstains; no centroid is produced |
| B2.14 | Amber — **MaxEnt entropy 0.76 from a lookup** | abstains, awaiting a state space |
| B2.15 | Amber — Π=1, N=0.55 | abstains, awaiting a possibility distribution |
| B2.16 | Red — μ=0.38 ν=0.59 π=0.71 | abstains |
| B2.17 | Amber — μ=0.44 ν=0.55 | abstains |
| B2.18 | Yellow — MARCOS score 0.642 | abstains, awaiting explicit alternatives |
| B2.19 | (already abstained) | abstains, same |
| B2.20 | disabled, unchanged | disabled, truthfully |

**Real-corpus Category-7 results generated by legacy proxy = 0.** Eighteen populated rows became
abstentions. **The ledger is emptier and that is the correct outcome**; not one old reading was
preserved to keep a row occupied.

## 6. The ledger, before and after

| property | v15 | v16 |
|---|---|---|
| result source recorded on the row | absent | `CANONICAL_V5_LAYER` on all 20 |
| disposition | absent | `CANONICAL_RESULT` / `NOT_ESTIMABLE_STRUCTURE_ABSENT` / `OPERATOR_BLOCKED` / `DISABLED` / `ARCHIVED` |
| structure named | absent | on 19 (B2.9 is archived and names its archival instead) |
| provenance carried | absent | on every computed row |
| abstention reason in words | on some | on all 20 |
| lineage on the row | absent | on all 17 operational |
| legacy-proxy marker | 8 proxy qualifiers, 3 truthful labels | **none** |
| disabled/archived as live readings | none | **none** |
| simulation version | v15 | **v16** |

An **abstaining** row now carries these fields too — `registry.record` was extended for exactly
that reason. A row that merely goes quiet cannot tell a reader which line produced the silence.

## 7. v15 preservation, and the v16 boundary

`sim-2026.08-v15` is preserved: the history recorded at git object `ce03eb1` is read out of git
and asserted to be a strict **prefix** of the history now, grown by exactly one stamp; all
sixteen identifiers unique; the v15 freeze record untouched and still verifying.

**v16 identity:** `sim-2026.08-v16`. **First commit:** `9c669c6`.

The boundary is executed, not argued (`test_run30_closure_version_boundary.py`, 20/20). The v15
package is extracted from `ce03eb1`, imported, and run beside the current one. The extracted line
is confirmed stamped v15 **and its own routing table is read out of it**: it sends B2.14 to
`models_fuzzy`, where the current line sends it to `models_cat7`.

| input | v15 output | v16 output | reason |
|---|---|---|---|
| flat inputs, no governed structure | B2.14 **Amber**, entropy of a lookup indexed by min(cpi,spi) | **abstains** | no state space, no constraints, nothing to maximise over |
| same | B2.13 **Red**, centroid from designed constants | **abstains**, no reduced figure | the midpoint collapse the contract forbids is gone |
| same | B2.17 computes a Fermatean pair from the indices | **abstains** | no assessed membership pair exists |
| assembled arms | B2.2 bands them as a rough-set classification | **abstains** | four crisp readings are not a decision table |
| governed max-entropy problem | v15 has no structure to read it | **ln 3 = 1.0986122886681098** | the closure widened what can be read |

**Two legitimate agreements**, so the boundary is not overclaimed: Plithogenic refuses on a
complete laboratory structure under **both** lines — the closure retired proxies and activated
nothing — and B1.1 Conservative Dominance is byte-for-byte identical on both.

## 8. Package decisions

- **Synthetic — no successor, re-evaluated as instructed.** No package byte moved, and minting an
  identifier for bytes nobody changed is the masquerade the chain's rule 4 forbids. What changed
  is that the package's Category-7 fixture now **reaches** the canonical production runner:
  `production_structures.decision_alternatives` imports the package's own decision problem into
  the shared alternatives-and-criteria shape — same rows, nothing invented, no weight supplied —
  and driven through the production dispatcher it reproduces the package's **recorded CRITIC
  weights** (0.250586 / 0.223434 / 0.175846 / 0.187310 / 0.162823) and its **recorded top
  alternative DP-01-A5**. The locked-holdout leakage control survived the change of structure and
  is asserted after it.
- **Participant — successor created: `og-participant-2026.08-v5`.** Bytes moved: the served
  defensibility evidence object is generated from the registry and the structure maps, and both
  changed. v4 is now pinned to `ce03eb1`; exactly one record matches the live tree and it is the
  declared current link. The delta is proved exactly — restoring the eight deleted qualifier
  sentences and the pre-closure structure statement reproduces the v4 bytes byte for byte. No
  predecessor was regenerated. **Participant experimental sequence unchanged.**

## 9. Non-vacuity: all fourteen mandated faults

`test_run30_closure_non_vacuity.py` (47/47), record in
`code_audit/run30_closure_fault_injection.csv`. **14 attempted, 14 `RED_THEN_GREEN`, 0
`INJECTION_NOT_APPLIED`.** Each injection re-read from the module to confirm it applied; each
probe ran through `registry.run_module`.

| # | fault | result |
|---|---|---|
| 1 | a dispatcher points back to its legacy proxy | RED → GREEN |
| 2 | missing structure falls through to a proxy | RED → GREEN |
| 3 | canonical Dempster fixture routed to the old proxy | RED → GREEN |
| 4 | canonical fuzzy fixture routed to the old fuzzy implementation | RED → GREEN |
| 5 | Maximum Entropy routed to the old min(CPI,SPI) implementation | RED → GREEN |
| 6 | Fermatean routed to the old min(CPI,SPI) implementation | RED → GREEN |
| 7 | Type-2 routed to a midpoint fallback | RED → GREEN |
| 8 | MARCOS routed to a single-project proxy | RED → GREEN |
| 9 | CRITIC-TOPSIS routed to a single-project proxy | RED → GREEN |
| 10 | disabled Plithogenic made operational | RED → GREEN |
| 11 | archived Quantum made operational | RED → GREEN |
| 12 | disabled Hypersoft made operational | RED → GREEN |
| 13 | a row claims the canonical source while a legacy function ran | RED → GREEN |
| 14 | duplicate simulation-version stamp | RED → GREEN |

**Three injection sites had to be repointed, and each was found by observing the fault change
nothing rather than by scoring it:**
1. `models.VALIDATED` — `registry.py` does `from .models import VALIDATED`, so rebinding the
   models attribute set something the dispatcher never reads. Repointed to `registry.VALIDATED`.
2. The two disabled-activation faults — `run_module` short-circuits `DISABLED_CONCEPT_ONLY`
   *before* it consults `VALIDATED`. Repointed to `models_cat7.CAT7_CANONICAL`, which the
   disabled branch resolves at call time.
3. Fault 7 — mutating `canonical_v5.type2_fuzzy` applied cleanly and changed nothing, because the
   renderer never copies a reduced figure out of the canonical result. **That is the guarantee
   working**, so the fault was repointed to the renderer, the one place a midpoint could actually
   reach a row. Both the canonical function and the renderer were made late-bound so a mutation
   there is a real mutation and not a silent no-op.

The baseline was rechecked after the whole campaign, not only after each fault.

## 10. The regenerated 24-row closure

`code_audit/run30_cat6_7_final_closure.csv`, generated from the registry, the **live routing
table** and the Run-30 scope. Rows 24, unique identities 24, unaccounted 0.

**Category-7 production canonical = 20/20. Category-7 legacy production path reachable = 0.**

Category 6 is unchanged and remains remediated: B1.1 computes and is byte-identical across the
boundary; B1.3 and B1.4 compute; B1.2 abstains for want of a governed weighting policy.

## 11. Final head

- **`HEAD == main == origin/main`**, tree clean.
- Complete suite on that exact head: **144 suites, 11891/11891 checks, ALL SUITES GREEN.** Not
  inherited from `ce03eb1`.
- Final simulation version: **`sim-2026.08-v16`**.
- Freeze: `research/freeze/RUN30_CLOSURE_FREEZE_2026-08-16.json`, identifier
  `...-RUN30-CLOSURE-V16-1`, superseding `...-RUN30-CANONICAL-CAT6-7-V15-1`.

## 12. What this closure did NOT do

- It did **not** implement or close the Category-9 qualification gate. Every Category-7 row still
  carries `signal_qualification = "unqualified"`. The Run-17 register entry `ARCH/raw-bypass` is
  still open. **Run 31 owns it.**
- It did **not** invent a Karnik-Mendel formulation, an ER variant, a Z reduction or a plithogenic
  operator. All four remain blocked and each returns a named refusal.
- It did **not** activate anything. Plithogenic, Quantum and Hypersoft are disabled or archived
  and refuse on a complete laboratory structure.
- It did **not** delete any legacy implementation, move or rename MARCOS or CRITIC-TOPSIS, expand
  voting beyond A1.7 and A1.8, reactivate Material Cost Variance, or change the participant
  protocol.
- It did **not** calibrate anything. No band was introduced. **Run 33 owns it.**
- It did **not** launch Run 31.
