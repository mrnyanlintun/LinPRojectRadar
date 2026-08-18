# Run 34 — Portfolio Health calibration protocol (PREDECLARED)

**Status: PREDECLARED. Committed before any calibration search was executed.**
Branch `run34-portfolio-health-calibration` from `main` at `f5c52d3`.
Modules: PH.1–PH.5 (D1.1–D1.5). Simulation at time of writing: `sim-2026.08-v21`.

This document is the protocol. It is committed **first**, in its own commit, so that the
ordering — protocol, then campaign, then result — is a matter of record rather than a claim.
Fault 4 and fault 20 of the Run-34 campaign exist to prove that ordering is *enforced*.

---

## 0. Disclosure of prior information (stated because it is not zero)

I am **not blind** to some of the quantities this protocol governs. Run 33 already measured, on
the same frozen fixture and seeds this protocol reuses, the within-production rank stability of
the Isolation Forest across 30 seeds:

| t | within-production mean pairwise Spearman |
|---|---|
| 100 | 0.986049 |
| 400 | 0.995392 |
| 1000 | 0.997836 |

Declaring a stability cut-point *after* seeing those numbers would be choosing the answer and
calling it a rule. **The decision rule in §6 is therefore constructed so that it does not depend
on any cut-point fitted to those values**: its controlling clause is an *operational-relevance
gate* that is decidable from the state of the corpus, not from the stability numbers. The
stability numbers are still measured and reported in full, because §6A of the contract requires
them; they are simply not what selects the parameter.

---

## 1. Calibration objective

**For PH.1 tree count:** determine whether any candidate tree count has *defensible superiority*
over the published default of 100, treating tree count as what the contract calls it — a
**stability / compute-budget parameter**, not an accuracy parameter.

**For every other Portfolio Health parameter:** establish **provenance**, not value. The objective
is to classify each parameter into exactly one of the seven permitted classes and to remove any
parameter that is applied without provenance. Where a parameter would have to be invented to
produce a reading, the reading is withheld instead.

**Explicit non-objectives.** This run does not seek an operational anomaly threshold, a percentile
band, a slope magnitude band, a match radius, or composite weights. None of those may be created
here.

## 2. Candidate parameters and ranges

| module | parameter | candidates / treatment |
|---|---|---|
| PH.1 | `IF_TREES` (tree count) | **exactly** {100, 400, 1000}. No candidate may be added after results are seen. |
| PH.1 | `IF_SUBSAMPLE` (psi) | fixed at the published default 256; not searched in Run 34. |
| PH.1 | `IF_SEED` | fixed constant; a reproducibility device, not a tuned value. |
| PH.1 | frozen threshold 0.576 | **not searched.** Schema-bound laboratory artifact; retained or withheld, never retuned. |
| PH.1 | cohort-size policy | fixed by contract §6B: n<3, 3≤n<10, n≥10. Not searched. |
| PH.2 | feature weights | **not searched.** Supplied or absent. Absent ⇒ no composite. |
| PH.2 | percentile bands | **none permitted.** |
| PH.3 | minimum observations | fixed at 3 by contract §8A, predeclared here, not tuned. |
| PH.3 | numerical zero tolerance | 1e-12, a floating-point device, not an operational band. |
| PH.4 | radius / cluster threshold | **none permitted.** Continuous distance only. |
| PH.5 | constituent weights | **not searched.** Supplied or absent. Absent ⇒ composite NONE. |

## 3. Datasets

All datasets are **synthetic research calibration** fixtures and every one of them carries, as
literal fields:

```
data_origin = SYNTHETIC_RESEARCH_CALIBRATION
not_for_empirical_validation = true
ground_truth_defined_before_detector = true
```

**Ground truth is defined before generation, never after.** Each labelled fixture is produced by
first choosing which project identifiers are anomalous and by what generative mechanism, and then
drawing feature values from that specification. **No detector output is consulted to settle any
label, at any point.** The generator writes the label alongside the point that the label caused.

| role | dataset | contents |
|---|---|---|
| STABILITY | `ph1_rank_agreement_fixture.json` (existing, frozen in OG-SYNTH-0.5, **unmodified**) | 300 unlabelled projects, graded radial spread. Used for the seed-stability metrics only. |
| CALIBRATION | `run34_ph1_calibration_labelled.json` (new) | 200 projects, labelled; anomalies defined before generation. Used for any parameter selection that needs labels. |
| HOLDOUT | `run34_ph1_holdout_labelled.json` (new) | 200 projects from an **independent draw** under the same specification and a different generator seed. **Scored exactly once, after selection is final.** |

**The holdout may never influence selection.** It is read after the tree count is fixed, and its
result is reported whatever it is. If the holdout result were unacceptable, the outcome recorded
is *calibration unresolved, escalated to Run 35* — never a re-selection.

## 4. Random seeds

- Stability campaign: **30 seeds**, `S_k = 20250815 + 1000·k`, `k = 0..29`. Identical to Run 33's
  predeclared set, reused deliberately so the two campaigns are comparable. Every seed is used;
  none is selected or discarded.
- Calibration fixture generator seed: `340001`. Holdout fixture generator seed: `340002`.
  Different seeds, same generative specification — that is what makes the holdout independent.
- Production scoring seed remains `IF_SEED = 20250815`.

## 5. Performance and stability metrics

For each candidate tree count, on the STABILITY dataset across the 30 seeds:

- `S(t)` — within-production rank stability: **mean pairwise Spearman** of the score vector with
  itself across distinct seeds;
- `A1(t)` — top-1 agreement: fraction of seed pairs naming the same most-anomalous project;
- `A10(t)` — top-10 agreement: mean Jaccard overlap of top-10 sets across seed pairs;
- `V(t)` — mean per-project score variance across seeds;
- `R(t)` — median wall-clock runtime to fit and score the cohort;
- `M(t)` — peak memory where measurable (`tracemalloc`), reported as "not measurable" if not;
- marginal improvement 100→400 and 400→1000, reported as both `ΔS` and the **instability ratio**
  `I(t')/I(t)` where `I(t) = 1 − S(t)`.

On the CALIBRATION and HOLDOUT datasets (labelled), reported for the selected candidate only:

- ROC-AUC and PR-AUC of the continuous score against the pre-defined labels;
- score separation between the labelled anomalous and labelled normal populations.

These are **separation statistics on synthetic data**. They are not field performance and may not
be reported as such.

## 6. Decision rule for the PH.1 tree count (predeclared, in force as written)

**D1 — Admissibility.** A candidate is admissible only if its metrics are computed on the
predeclared STABILITY fixture with the predeclared seed set, with no candidate added or removed.

**D2 — Operational-relevance gate (controlling clause).** A change of tree count may be selected
**only if the tree count has a demonstrable operational consequence** — that is, only if there
exists at least one *governed cohort reachable through the production route* on which PH.1
produces an operational reading whose reported content differs between candidates.

> Rationale, stated in advance. Tree count is a stability/compute trade-off. A trade-off requires
> units on both sides. PH.1 currently produces **no** operational reading on the real corpus:
> Run 33 established that the controlled portfolio supplies no governed portfolio cohort, so all
> five modules abstain, and PH.1 emits no authoritative flag under any schema (§6C). If nothing
> operational varies with the parameter, then no candidate has defensible superiority, and
> selecting one on the strength of a stability statistic alone would be tuning a parameter to a
> fixture.

**D3 — Selection, applicable only if D2 passes.** Among admissible candidates, promote from the
smaller to the larger only where the instability at least halves, `I(t') ≤ 0.5·I(t)`, **and** the
runtime ratio `R(t')/R(t) ≤ 4`. Apply pairwise in ascending order and stop at the first failure.

**D4 — Default, applicable if D2 fails.** **Retain 100**, the published default, and record
`TREE_COUNT_CALIBRATION = UNRESOLVED_NO_OPERATIONAL_CONSEQUENCE`. Under the contract's §6A this
is an authorised outcome and is not a failure to complete.

**D5 — Tie-break.** Where two candidates are otherwise equally defensible, prefer the **smaller**
tree count: it is the published default and the lower compute budget.

**D6 — Holdout.** Scored once, after selection is final. It reports; it never selects.

**Explicitly prohibited as a basis for selection:** that cross-implementation Spearman with
scikit-learn exceeds 0.99. The contract forbids it (§6A) and Run 33 established why — at t=100
the implementation agrees with *itself* across seeds (0.986049) essentially as closely as it
agrees with scikit-learn (0.986057), so that statistic carries no information about the parameter.

## 7. Minimum acceptable conditions

- Every parameter that reaches production carries exactly one of the seven provenance classes.
- No parameter classified `UNSUPPORTED` may be *applied* to produce an operational reading; it is
  either withdrawn or its reading is withheld.
- No threshold, band, radius or weight is created by this run.
- Every module states all five assurance layers separately; layer 5 stays pending for all five.
- Any production behaviour change is proved by execution and moves the simulation version.

## 8. Tie-breaking rule

Prefer, in order: (1) the outcome that withholds a reading over the outcome that produces one on
invented provenance; (2) the published default over a fitted value; (3) the smaller compute
budget; (4) the status quo.

## 9. Compute-budget consideration

Tree count is linear in both fit and score cost. The deployment target is a small service and the
dependency set is deliberately pure-Python with no numeric extension, so a 4× or 10× increase in
ensemble cost is a real operational cost and is weighed as one in D3, not treated as free.

## 10. Sensitivity analysis (predeclared)

- PH.1: score and rank sensitivity to seed (30 seeds); to cohort size (n = 3, 5, 10, 25, 100);
  to a declared affine rescaling of one feature; to psi at the fixed default.
- PH.2: percentile sensitivity to orientation declaration and to feature-set composition.
- PH.3: slope sensitivity to unequal date spacing versus assumed equal spacing.
- PH.4: nearest-neighbour sensitivity to input ordering and to normalization version.
- PH.5: profile sensitivity to a missing constituent and to duplicated lineage.

## 11. Prohibited post-hoc changes

The following are prohibited once this protocol is committed:

1. adding, removing or reordering tree-count candidates;
2. altering the decision rule, the admissibility conditions or the tie-break;
3. changing the stability fixture or the seed set;
4. regenerating either labelled fixture after any detector output has been inspected;
5. using the holdout dataset for selection, or scoring it more than once;
6. selecting a parameter after inspecting holdout results;
7. relabelling synthetic calibration as empirical or field validation;
8. introducing an operational threshold, band, radius or weight;
9. reclassifying a parameter to a stronger provenance class than its evidence supports.

**If a necessary correction is discovered**, this document is preserved unchanged, an amendment is
appended below explaining the correction and its reason, and the **full campaign is rerun**.

## 12. Amendments

*(none at time of commit)*
