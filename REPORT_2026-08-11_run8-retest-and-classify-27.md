# Run 8 — Retest and Classification of the 27 Unresolved Modules

## Executive Verdict

**Current commit:** branched from `origin/main` at `18b6b80`, the Run 7 merge.
**Post-fix simulation version:** `sim-2026.08-v3`, confirmed present as the successor implementation state before any test was written.
**Production files changed:** none. Not one file under `server/app/`, `assets/` or `research/` differs from the pinned baseline, asserted in section 0 of the new suite with an empty permitted set and re-checked against a tree hash taken at the start of the run.
**Exact unresolved universe:** **27**, reconciled mechanically rather than copied. The suite recomputes Run 6's own coverage arithmetic from the same sources: 100 registry-computed modules, minus the 63 Run 6 covered (read out of the merged Run 6 suite's own set rather than retyped), minus the 2 the validate-seven run covered, minus the 8 disabled concept-only, leaves exactly 27, and the 27 it leaves are character for character the list Run 6 printed.
**New tests:** one file, `server/tools/test_run8_retest_classify_27.py`.
**Total checks:** 232, all passing. 185 of those are known-answer, property, boundary, domain, abstention, pass-through or production-path cases, and every one of the 185 is proved able to fail by perturbing its expectation.
**Final unclassified count:** **0**. All 27 carry exactly one owner-action bucket.

The headline is not the classification. It is that **two more modules were found that cannot report a healthy project**, which is Run 6's finding 1.1 in two further places, and that **five of the sixteen defect-class findings are a defect the previous three runs already fixed in the module next door and did not carry across**.

---

## Bucket Totals

| Bucket | Meaning | Count |
|---:|---|---:|
| 1 | Pass, no production change and no new corpus required | **0** |
| 2 | Defect fix required using current data, or the correct current-data behavior is abstention | **16** |
| 3 | ChatGPT creates an additional synthetic project-structure corpus | **7** |
| 4 | ChatGPT creates a synthetic reference, training, expert-rule or decision dataset | **2** |
| 5 | Optional, disabled or concept-only: synthetic decision/reference structure required, module stays off | **2** |
| — | Unresolved after Run 8 | **0** |
| | **Total** | **27** |

**Bucket 1 is empty, and that is a finding rather than an omission.** Not one of the 27 both passes cleanly and needs no further data programme. Nine of them pass their current arithmetic exactly and are in Buckets 3, 4 or 5 solely because the canonical method their name claims requires a structure the corpus does not hold. The rest carry a reproducible defect. **None of the 27 carries a Run 1 proxy qualifier** — asserted in the suite by intersecting the derived 27 with `registry.PROXY_QUALIFIERS`, which returns empty — so the modules whose names most overstate what they compute are precisely the ones the relabelling programme did not reach.

---

## Master Classification Table

| # | Module ID | Module | Cat | Category Name | Run 6 Gap | Current Test Type | Current Test Result | Expected | Actual | Canonical Structure Required | Present Now? | Final Bucket | Reason | Production Fix Needed? | Synthetic Asset Needed? |
|---:|---|---|---|---|---|---|---|---|---|---|---|---:|---|---|---|
| 1 | A1.1 | Monte Carlo EAC | A1 | Cost and forecast | too involved to hand-compute | metamorphic property | PROPERTY_ONLY_PASS | forecast doubles with the budget, overrun per cent invariant, seed reproducible | as expected | quantified cost risk ranges | no | 3 | spread designed from two indices, not drawn from a risk register | no | yes |
| 2 | A1.5 | ARIMA CPI Forecast | A1 | Cost and forecast | ran out of run | known answer plus domain | FAIL_DOMAIN | a negative index history refused | forecast −3.9 banded Red | history long enough to identify an order | partial | 2 | history domain unguarded; the coefficient is a clamped ratio, not an estimate | yes | no |
| 3 | A1.6 | Earned Schedule | A1 | Cost and forecast | ran out of run | known answer plus domain | FAIL_DOMAIN | completion outside 0–100 refused | −40% gives −0.889 Red; 140% gives 3.111 **Green** | time-phased planned value curve | no | 2 | domain unguarded, and it requires earned value, planned value and budget while reading none of them | yes | no |
| 4 | A1.11 | ICE Ratio | A1 | Cost and forecast | ran out of run | known answer plus domain | FAIL_DOMAIN | a negative cost index refused | ratio −1.429 and a forecast of −$2,000 printed as money | none | yes | 2 | the guard exists in four neighbouring computations and is absent here | yes | no |
| 5 | A2.1 | PERT Network Criticality | A2 | Schedule | constant pre-Run 7 | property over 1,600 combinations | FAIL_BOUNDARY | a project on or ahead of plan can read healthy | **Green unreachable**; only Amber and Red | activity network with three-point durations | no | 2 | a P80 divided by a sum of modes; structurally above the Green edge on every input | yes | yes |
| 6 | A2.2 | Line of Balance | A2 | Schedule | constant pre-Run 7 | exact known answer | EXACT_KAT_PASS | buffer 2.7 days at an index of 0.9, Amber | as expected | locations, crews, production rates | no | 3 | units, both rates and the buffer are literals in the file | no | yes |
| 7 | A2.3 | CCPM Buffer Health | A2 | Schedule | constant pre-Run 7 | exact known answer | EXACT_KAT_PASS | 15% consumed at 40% chain complete, Green | as expected | critical chain and sized buffers | no | 3 | buffer derived from the schedule index, not from a sized chain buffer | no | yes |
| 8 | A2.5 | Float Consumption Rate | A2 | Schedule | covered elsewhere, not re-derived | known answer plus domain | FAIL_DOMAIN | a negative consumed float refused | 35 days remaining out of 30, stress −0.42, **Green** | activity network with float history | no | 2 | the fifteen-defects run removed the completion fallback and left the float domain open | yes | yes |
| 9 | A2.9 | Resource Loading Index | A2 | Schedule | ran out of run | known answer plus boundary | FAIL_DOMAIN | negative labour hours refused | −50 hours accepted, ratio −0.05 | none | yes | 2 | Red for the wrong reason; the ratio beside it is not a quantity | yes | no |
| 10 | A2.10 | Schedule Risk Analysis P80 | A2 | Schedule | ran out of run | known answer plus domain | FAIL_DOMAIN | a zero index abstains; a negative index refused | **a zero index RAISES**; a negative index reports 1,075 days early and reads Green | schedule risk register | no | 2 | the exact unguarded denominator the fifteen-defects run removed next door | yes | yes |
| 11 | A2.11 | Critical Path Index | A2 | Schedule | substituted pre-Run 7 | known answer plus domain | FAIL_DOMAIN | a negative schedule index refused | index −0.006, Red | CPM paths and float history | no | 2 | Run 7 guarded the denominator and left the index domain open | yes | yes |
| 12 | A3.1 | Reference Class Forecasting | A3 | Cost estimating | reads no project input at all | disabled contract | DISABLED_CONTRACT_PASS | abstains on every input | as expected | a reference class of completed projects | no | 5 | off since Run 7; stays off pending the owner | no | yes |
| 13 | A3.6 | Cost Risk Analysis P80 | A3 | Cost estimating | covered by a guard case only | known answer plus text | FAIL_QUALIFIER | one sign in the finding sentence | `+-28.8% BAC` | quantified cost risk register | no | 2 | a hard-coded plus in front of a formatted negative, on a participant-reachable surface | yes | yes |
| 14 | A4.4 | NCR Rate | A4 | Documents and quality records | covered elsewhere | exact known answer | EXACT_KAT_PASS | 6 of 40 is 0.15, Yellow | as expected | audited nonconformance cohort | one project only | 3 | faithful and fully guarded; abstains for want of corpus, not for a fault | no | yes |
| 15 | A4.10 | Specification Conflict Density | A4 | Documents and quality records | substituted pre-Run 7 | known answer plus domain | FAIL_DOMAIN | a document risk outside 0–1 refused | −0.5 gives a density of −1 and reads **Green** | requirements dependency structure | no | 2 | the out-of-domain value lands in the calmest band | yes | yes |
| 16 | A5.1 | DSM Rework Propagation | A5 | Risk and simulation | reads no project input at all | disabled contract | DISABLED_CONTRACT_PASS | abstains on every input | as expected | a design structure matrix | no | 5 | off since Run 7; stays off pending the owner | no | yes |
| 17 | A5.4 | Scenario Modeling | A5 | Risk and simulation | covered elsewhere | exact known answer | EXACT_KAT_PASS | 1,040,000 / 1,100,066 / 1,114,916, range 7.5%, Amber | as expected | actions-by-scenarios payoff structure | no | 4 | three deterministic forecasts; there are no scenarios in the corpus to model | no | yes |
| 18 | A5.5 | Rework Feedback Loop | A5 | Risk and simulation | ran out of run | property plus domain | FAIL_PROPERTY | adding a document must not improve the reading | 0.64 **Red** with both logs, 0.04 **Green** with neither | none | yes | 2 | Run 6 finding 1.4 standing in the module beside the one Run 7 corrected | yes | no |
| 19 | A5.6 | Queueing Theory Bottleneck | A5 | Risk and simulation | substituted pre-Run 7 | exact known answer | EXACT_KAT_PASS | 37 of 200 is 0.185, Yellow | as expected | arrival and service processes | no | 3 | a transparent share; no queueing model present | no | yes |
| 20 | A5.7 | Agent-Based Supply Chain | A5 | Risk and simulation | substituted pre-Run 7 | exact known answer | EXACT_KAT_PASS | 3 of 20 is 0.15, Yellow | as expected | agents, states, rules, interactions | no | 3 | a transparent share; no agent model present | no | yes |
| 21 | A5.8 | Discrete Event Simulation | A5 | Risk and simulation | substituted pre-Run 7 | known answer plus domain | FAIL_DOMAIN | a negative schedule index refused | throughput 0.485, Red | events, entities, resources, queues | no | 2 | the same residue as the critical path measure | yes | yes |
| 22 | A6.1 | Quality Compliance Index | A6 | Quality and safety | covered elsewhere | known answer plus domain | FAIL_DOMAIN | an audited score outside 0–100 refused | 150 reads **Green**; −20 printed as `-20/100` | none | yes | 2 | the fifteen-defects run guarded the inspection pair and left the audited score open | yes | no |
| 23 | A6.2 | Safety Performance Index | A6 | Quality and safety | substituted pre-Run 7 | known answer plus domain | FAIL_DOMAIN | an incident rate comes from a safety record | silence gives a rate of zero, the best index and **Green**; one mention gives Amber | none | yes | 2 | the fifteen-defects run's defect 15 standing in the neighbouring module | yes | no |
| 24 | A6.3 | Environmental Compliance Rate | A6 | Quality and safety | covered elsewhere | pass-through contract | PASS_THROUGH_CONTRACT_PASS | 95% passes through and is Green; 101% refused | as expected | audited permit conditions | one project only | 3 | clean pass-through; abstains for want of corpus | no | yes |
| 25 | A6.4 | Contractor Performance Score | A6 | Quality and safety | ran out of run | known answer plus domain | FAIL_DOMAIN | a rating outside 1–5 refused | 9.9 accepted, text still says "out of five" | none | yes | 2 | the rating scale is ungoverned | yes | no |
| 26 | B2.18 | MARCOS Ranking | B2 | Uncertainty representation | ran out of run | property over 65,856 combinations | FAIL_FORMULA | a project at every ideal outranks one at every anti-ideal | **both score zero; only Red is reachable** | alternatives-by-criteria matrix | no | 2 | the score collapses to an expression symmetric about a utility of one half and bounded above by one third | yes | yes |
| 27 | B2.19 | CRITIC-TOPSIS | B2 | Uncertainty representation | ran out of run | exact known answer | EXACT_KAT_PASS | closeness 0.724 from distances 0.135 and 0.356 | as expected | alternatives-by-criteria matrix | no | 4 | coherent arithmetic, all four bands reachable; the weighting is degenerate on one alternative | no | yes |

---

## Bucket 1 — Pass, No Touch

**Empty.** Nine of the 27 pass their current arithmetic exactly and are recorded in Buckets 3, 4 and 5 rather than here, because Bucket 1 requires that no additional corpus, reference population, rule base or decision matrix be needed for the role the architecture permits, and for every one of the nine that condition fails. Those nine are A1.1, A2.2, A2.3, A4.4, A5.4, A5.6, A5.7, A6.3 and B2.19, and each carries its evidence in the bucket sections below.

The nearest module to Bucket 1 is **A6.3 Environmental Compliance Rate**. Its whole contract is a pass-through: the audited rate is carried through unchanged, a rate above a hundred per cent is refused rather than clipped, the meeting-mention fabrication the fifteen-defects run removed has not returned, and the ninety-five per cent Green edge is inclusive with the value just below it landing Yellow. It is in Bucket 3 only because the report type it reads exists for one project.

---

## Bucket 2 — Fix Required

Sixteen modules. **No fix is made in this run.** Each defect below is reproduced from a stated input with an independently derived expected behaviour. Five of the sixteen are a defect an earlier run fixed in a neighbouring module and did not carry across; that pattern is the single most useful thing in this report.

### 2.1 B2.18 MARCOS Ranking — no input can produce a healthy reading, and the best project scores zero

**The derivation, from the module's own algebra, before any code was run.** Let `u` be the weighted utility against the ideal. The module sets `utility_anti = 1 - u`, so the two sum to exactly one by construction and therefore `f_ideal = u` and `f_anti = 1 - u`. The reported score is

```
(f_ideal + f_anti) / (1 + (1 - f_ideal)/f_ideal + (1 - f_anti)/f_anti)
  = 1 / (1 + (1 - u)/u + u/(1 - u))
```

The numerator collapses to one. The denominator is **invariant under `u -> 1 - u`**, so the score is symmetric about a utility of one half: a project with a utility of 0.2 and a project with a utility of 0.8 receive the identical score. The denominator is minimised at `u = 0.5`, where it is `1 + 1 + 1 = 3`, so **the maximum score the module can ever return is one third**, and the Amber arm requires 0.35.

**Reproducible input and actual behaviour.** Exhausted over 65,856 combinations of cost index, schedule index and document risk, spanning indices from 0.50 to 1.60 and risk from 0 to 1: **Red is the only band that occurs**, and the highest score anywhere is 0.333. A project at every ideal (`cpi 1.05, spi 1.05, docRisk 0.00`, utility exactly 1.000) and a project at every anti-ideal (`cpi 0.80, spi 0.80, docRisk 0.70`, utility exactly 0.000) **both score zero**, the first because the anti arm divides by zero.

**Defect class:** formula. The output contradicts the method the name claims: a ranking method that ranks the best and the worst alternative identically is not ranking.

**Smallest recommended correction:** abstention. The corpus holds no alternatives-by-criteria matrix, and a single-alternative MARCOS has no meaning to correct toward — the utility-against-ideal is computable but the ranking is not. This is the same disposition Run 7 gave the regret module for the same reason, and the reason code `canonical_decision_structure_absent` already exists for it.

**Voting and participant surface:** non-voting before and after, and it is not read by the recommendation text or the courses of action. It is visible on the Signal Ledger, which is participant-reachable, so a participant currently sees a permanently Red ranking on every project in every period.

### 2.2 A2.1 PERT Network Criticality — a healthy reading is structurally unreachable

**The derivation.** The three activities are the module's own literals: A = (8, 10, 14), B = (12, 15, 22p), C = (10, 13, 18p), finish = A + max(B, C), with `p = 1 + max(0, 1 - spi) * 0.8` so `p = 1` for every index at or above one. The band divides the **eightieth percentile of that sum** by a baseline of `10 + max(15, 13) = 25`, which is a **sum of modes**. For a triangular distribution the mean is `(a + m + b)/3`, so `E[A] = 32/3 = 10.667` and `E[max(B, C)] >= E[B] = 49/3 = 16.333`, giving an expected finish of at least 27.0 against a baseline of 25 — a ratio of 1.08 **at the mean**, before the percentile is taken. The Green arm requires a ratio at or below 1.15.

**Reproducible input and actual behaviour.** Over 200 seeds crossed with eight schedule indices from 0.6 to 2.0, **only Amber and Red occur**, and the lowest ratio observed anywhere is 1.16. A project running twice as fast as plan reads Amber.

**Defect class:** boundary against a mis-specified denominator. The band compares an upper percentile of a distribution against a lower-than-mean point estimate of the same distribution.

**Smallest recommended correction:** compare like with like — divide the P80 by the P80 of the unpessimised baseline, or by the deterministic mean rather than the mode sum, and re-source the band. Alternatively abstain, since the activity network is not in the corpus. Arithmetic, not wiring.

**Voting and participant surface:** non-voting; ledger-visible.

### 2.3 A2.10 Schedule Risk Analysis P80 — an unguarded denominator that raises

`p50_days = remaining_days / si["spi"]` has no guard. **A schedule index of exactly zero raises `ZeroDivisionError` inside the computation.** Per this project's own test discipline, a check that crashes prints no result line and looks clean; worse, a raise here loses the whole project computation rather than one module's stated abstention. This is precisely the defect the fifteen-defects run removed from `bac / cpi` in Cost Risk Analysis P80, one module away in the same file family, and it did not carry across.

The negative case does not announce itself and is worse. With a baseline of 364 days, forty per cent complete and an index of −0.5: remaining = 218.4; p50 = −436.8; uncertainty = `max(0.05, 1.5) * 0.5 = 0.75`; p80 = `−436.8 * 1.96 = −856.128`; delay = `round(−856.128 − 218.4) = −1075`. **The project is reported as finishing 1,075 days early and reads Green.** A completion above a hundred per cent does the same on a smaller scale: 120 per cent gives a delay of −2 days and Green.

**Correction:** abstain on a non-positive index, refuse a completion outside nought to a hundred. Both are abstention fixes using data already present.

### 2.4 A5.5 Rework Feedback Loop — withholding evidence improves the reading by three bands

This is Run 6 finding 1.4 exactly, in the module beside the one Run 7 corrected. The index is `rfi + co + cpi` with weights 0.3 / 0.3 / 0.4, and an **absent** source contributes zero rather than being required or renormalised out.

| Same project, cost index 0.90 | rfi | co | cpi | index | band |
|---|---|---|---|---|---|
| both logs reported (30 requests, 15 change orders) | 0.30 | 0.30 | 0.04 | **0.64** | **Red** |
| neither log reported | 0 | 0 | 0.04 | **0.04** | **Green** |

All four evidence subsets were exhausted and give four different indices for one project: 0.04, 0.34, 0.34, 0.64. Two further faults sit under it. **A reported zero and an absent log are indistinguishable**, because the guard is a truthiness test (`if si.get("rfiCount")`), so a genuine measurement of zero is discarded as though nothing was reported. And **negative counts are not refused**: a count of −5 gives an index of −0.01, outside the domain an index can occupy, and reads Green. A negative cost index is not refused either and contributes 0.8.

**Correction:** require all three sources, treat a reported zero as evidence, refuse negative counts. Exactly the correction Run 7 applied to A4.7. Abstention and domain, no arithmetic change.

### 2.5 A6.2 Safety Performance Index — silence reads as the best possible safety record

Run 7 corrected the index at a zero rate and refused a negative rate, and left the fallback standing. With no reported incident rate the module converts a count of times safety was raised in a meeting into an incident rate **at ten points per mention**, a literal with no derivation anywhere. A recordable incident rate is incidents multiplied by 200,000 and divided by hours worked; it is not a count of mentions.

| Mentions in the minutes | Derived rate | Safety index | Band |
|---:|---:|---:|---|
| 0 | 0.0 | **2** (the module's cap, its best) | **Green** |
| 1 | 10.0 | 0.3 | Amber |
| 2 | 20.0 | 0.15 | Red |

**A project where safety was never discussed reads Green with the best index the module can award.** This is the fifteen-defects run's defect 15 — the environmental measure's `max(50, 100 - issues * 5)`, whose report said in as many words that "a project where the subject was never discussed scored one hundred per cent compliant, which is the opposite of what silence means" — standing in the module immediately beside it, running in the same direction.

**Correction:** require a reported incident rate and abstain without one, exactly as A6.3 now does. With a reported rate the module is a correct transparent ratio and every one of its five boundaries is confirmed here.

### 2.6 A1.6 Earned Schedule — an unguarded domain, and three required inputs it never reads

`SPI(t)` is computed as actual per cent complete over planned per cent complete, and neither is bounded. A completion of −40 per cent against a plan of 45 gives −0.889 and Red; a completion of 140 per cent gives **3.111 and Green**.

Separately, the module's input contract demands earned value, planned value and budget at completion and then **computes from neither**: the arithmetic reads only the two completion percentages. A project that reported its progress but no earned value abstains for no arithmetic reason. This is also the clearest evidence in the run that the module is not earned schedule: real earned schedule reads the time at which the planned value curve equals the current earned value, which is exactly what those three unused inputs would be for.

**Correction:** guard the completion domain, and either drop the unused requirements or implement the method they imply. Domain plus contract.

### 2.7 A6.1 Quality Compliance Index — an audited score outside the domain a percentage can occupy

The fifteen-defects run guarded the inspected-and-failed pair thoroughly and left the **audited score** ungoverned. A score of 150 out of 100 is accepted and reads Green. A score of −20 is accepted, reads Red, and is printed in the finding text as `-20/100`, which reaches the participant-visible ledger. **Correction:** refuse a score outside nought to a hundred, the same guard already present on the pair beside it.

### 2.8 A4.10 Specification Conflict Density — an out-of-domain input lands in the calmest band

Run 7 removed the substitution and left the document risk domain open. A document risk of −0.5 with four requests gives `(-0.5 * 4)/sqrt(4) = -1.0`, and `min(1, -1.0)` is −1, which the Green arm accepts. Run 6's incidental finding 3 recorded that no module in the analytical layer refuses a document risk outside its declared domain and that the layer relies entirely on the one ingestion guard; **this is where that reliance costs, because the failure direction is the calm one.**

### 2.9 A3.6 Cost Risk Analysis P80 — a participant-facing sentence with two signs

The finding text hard-codes a leading plus and then formats the delta, which may legitimately be negative because a cost index may exceed one. At an index of 5.0 the sentence reads `CRA P80 EAC: $712 (+-28.8% BAC)`. **Correction:** format the sign once. Label, not arithmetic; the number itself is correct and was re-derived by hand.

### 2.10 The five remaining domain defects

| Module | Reproducible input | Actual | Independently derived correct behaviour | Class |
|---|---|---|---|---|
| A1.5 ARIMA CPI Forecast | history −1, −2, −3 | forecast −3.9 | a cost performance index cannot be negative; refuse the history | domain |
| A1.11 ICE Ratio | budget 1,000, index −0.5, earned 400, actual 800 | ratio −1.429 and a forecast of −$2,000 printed as money | refuse a non-positive index, as four neighbouring computations do | domain |
| A2.5 Float Consumption Rate | total float 30, consumed −5, 40% complete | 35 days remaining out of 30, stress −0.42, **Green** | refuse a negative consumed float | domain |
| A2.9 Resource Loading Index | planned 1,000 hours, actual −50 | ratio −0.05, Red | refuse negative hours; Red is right for the wrong reason | domain |
| A6.4 Contractor Performance Score | overall rating 9.9 on a five-point scale | accepted, text still reads "out of five" | refuse a rating outside the scale the text names | domain |

Two more are recorded at lower severity because the band is Red either way and only the reported figure is wrong: **A2.11 Critical Path Index** gives −0.006 on a negative schedule index, and **A5.8 Discrete Event Simulation** gives a throughput of 0.485 on the same input. Both are Run 7 residue: the denominator was guarded and the index domain was not.

**Participant-surface impact across all sixteen:** none of the sixteen votes, none is read by the recommendation text, the courses of action or the decision card, and this run makes no module voting. All sixteen are visible on the Signal Ledger, which **is** participant-reachable, so the four that report a healthy or calm band from an input that cannot describe a project (A1.6, A2.10, A4.10, A5.5, A6.1, A6.2) are the ones with participant consequence.

---

## Bucket 3 — Synthetic Project-Structure Corpus Required

Seven modules. Complete schemas are in `code_audit/run8_required_project_corpus_specs.csv`; the summary and the shared-corpus grouping are here.

**Why current project documents are insufficient.** The corpus is a document corpus: pay applications, monthly reports, meeting minutes, request and submittal logs, schedules as dates rather than as networks. None of the seven modules can reach its canonical method from those, because each needs *operational structure* — a network, a set of locations and crews, a queue, an agent population, an audited cohort — rather than another scalar.

| Module | Structure absent from the corpus | Shared package |
|---|---|---|
| A1.1 Monte Carlo EAC | quantified cost ranges per risk or work package | `CORPUS_A1_cost_uncertainty` |
| A2.2 Line of Balance | locations, crews, quantities, production rates | `CORPUS_A2_linear_production` |
| A2.3 CCPM Buffer Health | a critical chain with sized project and feeding buffers | `CORPUS_A2_critical_chain` |
| A4.4 NCR Rate | an audited nonconformance cohort | `CORPUS_A4_quality_audit` |
| A5.6 Queueing Theory Bottleneck | arrival and service processes, capacity, queue discipline | `CORPUS_A5_flow_processes` |
| A5.7 Agent-Based Supply Chain | agents, states, rules, interactions | `CORPUS_A5_supply_agents` |
| A6.3 Environmental Compliance Rate | audited permit conditions | `CORPUS_A6_environmental_audit` |

**Modules that share a corpus.** `CORPUS_A2_activity_network` is specified as an eighth package because **four Bucket 2 modules need it as their follow-on** once their defects are fixed: A2.1 PERT Network Criticality, A2.5 Float Consumption Rate, A2.10 Schedule Risk Analysis P80 and A2.11 Critical Path Index all read a schedule they currently approximate from two percentages and an index. Building it once serves all four and is the highest-leverage single asset in this report. `CORPUS_A2_critical_chain` extends it rather than duplicating it: the activities and predecessors are the same tables with aggressive and safe durations added.

**Minimum canonical fixture and ground truth, per package**, are in the CSV. Two worth quoting because they are the ones a later run should test against first:

- **`CORPUS_A2_activity_network`.** The three-activity network the schedule modules currently hard-code — A = (8, 10, 14), then B = (12, 15, 22) parallel with C = (10, 13, 18) — with the ground truth stated as *both* the deterministic CPM result on the modes (25 days) *and* the analytic P50 and P80 of the sum. Stating both is the point: the defect in A2.1 is that the code compares one against the other.
- **`CORPUS_A4_quality_audit`.** Six findings open of an audited cohort of forty gives an open ratio of exactly 0.15, which is the first Yellow value because that Green edge is exclusive.

Every artefact must be labelled `SYNTHETIC_RESEARCH_FIXTURE`. **This run creates none of them.**

---

## Bucket 4 — Synthetic Reference, Training or Decision Dataset Required

Two modules, and the two Bucket 5 modules share this build package. Complete schemas are in `code_audit/run8_required_reference_decision_specs.csv`.

| Module | Object required | Why it is not an ordinary project document |
|---|---|---|
| A5.4 Scenario Modeling | `DATASET_B1_scenario_payoff`: an actions-by-scenarios payoff matrix with elicited probabilities | scenarios are a designed decision structure, not something a project uploads |
| B2.19 CRITIC-TOPSIS | `DATASET_B2_alternatives_matrix`: an alternatives-by-criteria matrix with more than one alternative | a CRITIC weighting is computed *across* alternatives; one project is not a decision problem |

**The degenerate weighting, demonstrated rather than described.** With a single alternative, CRITIC weights come from the spread of that one project's three criteria, so a criterion equal to the mean of the other two carries a weight of **exactly zero** and drops out of its own decision. Asserted in the suite on the criteria (0.80, 0.90, 1.00), where the middle weight is 0.0. The arithmetic is otherwise coherent and all four bands are reachable, which is what separates B2.19 from B2.18 beside it.

**B2.18 MARCOS shares `DATASET_B2_alternatives_matrix`** as its follow-on once its Bucket 2 defect is dispositioned, and the specification names the property the dataset must be able to demonstrate: the top-ranked alternative must be the one dominating on every criterion, which the current module violates.

---

## Bucket 5 — Optional or Disabled Synthetic Structure

Two modules: **A3.1 Reference Class Forecasting** and **A5.1 DSM Rework Propagation**.

**These are not among the Run 1 disabled concept-only eight**, and the suite asserts that explicitly so a later run does not assume otherwise. Their off state rests on **Run 7's unconditional abstention**, not on the registry short circuit. They are classified here because the owner action is identical to Bucket 5's: a synthetic decision or reference structure must exist before they can be implemented at all, and they remain off until the owner separately authorises reactivation.

**Disabled-state verification.** Each was executed on an empty input and on a fully populated project input. Both abstain in every case, no band is reachable from any input, both give a speakable reason with no key name, no module id and no em dash, both appear on the production abstention list from `compute_project` carrying a reason and an activation state, and neither votes. **Neither was reactivated by this run.**

**Required synthetic structure, technical feasibility, and why each stays off:**

- **A3.1** needs `DATASET_B3_reference_class`: a population of comparable completed projects with realised cost and schedule overruns. Technically implementable the moment such a population exists — the method is an empirical percentile lookup and needs no new machinery. **Overlap:** the cost forecasters (Monte Carlo, Bayesian, ICE, Cost Risk P80) already occupy the outside-view role from inside-view data, so the incremental value is the outside view specifically. **Incremental-value test required before activation:** show that the reference-class forecast and the index-based forecast disagree materially on at least a quarter of periods, and that where they disagree the reference-class one is closer to the realised outcome on the holdout. Without that, activation adds a fifth cost forecast saying what the other four say.
- **A5.1** needs `DATASET_B4_dependency_matrix`: a 7 by 7 design structure matrix with dependency strengths, rework probabilities, and a stated row-depends-on-column convention. Implementable as a Neumann series once the matrix exists. **Overlap:** the rework feedback and change-order measures already carry the rework signal from real counts. **Incremental-value test required:** show the propagated rework the matrix predicts is not a monotone function of the change-order count already measured. **Low priority** because the matrix must be elicited per project type and re-elicited when the design discipline mix changes, which is a standing cost for a signal two existing modules already approximate.

---

## Expectation-Mutation Proof

`code_audit/run8_expectation_mutation_proof.csv`, 185 rows, one per case, each carrying the module, the check label, the kind, the expected value, the perturbed expectation, the actual value, whether the check went red under perturbation, whether it went green when restored, and the hand derivation.

**Mechanically:** `ka()` refuses any case whose expectation cannot be perturbed and asserts both that the actual equals the expectation and that it does *not* equal a perturbation of it. **185 of 185 went red under perturbation.** One perturbation bug was found and fixed while building this: `expected * 2 + 1` is a fixed point at −1, which would have silently made one case unprovable; the perturbation now falls back to a shift whenever the doubling returns the value it was meant to differ from. That case is A4.10's negative density, and it is now proved live.

**End to end, by hand, as the instruction requires.** Three expectations were perturbed in the file itself — the MARCOS maximum from 0.333 to 0.999, the rework index from 0.64 to 0.99, and the schedule-risk delay from 90 to 91 — the suite was run and returned **229/232 with exactly those three red**, the file was restored, and the suite returned **232/232**.

---

## Production-Path Coverage

Section 12 drives `compute_project` and `registry.run_all` on a signalInputs dictionary of the shape `documents.py` assembles, and asserts:

- **all 27 are reached** by the production path, computed or abstaining, with none silently absent;
- the two unconditionally abstaining modules appear on the production **abstention list** with a reason and an activation state, not merely missing from the computed list;
- **not one of the 27 carries a vote** on the stored row, and the voting set is still exactly `{A1.7, A1.8}`;
- ten modules' production values equal the hand-derived direct-case values, module by module — this is the join that a fixture built by a route the application does not take would break, and it holds;
- every band the 27 store is recognised by `fusion.normalise_status`, the one place the vocabulary is recognised;
- on an empty input the production path **bands none of the 27**.

The direct function cases supplement this section; they do not replace it.

---

## Boundary and Domain Findings

**Inclusivity is still two conventions with no comment saying which a module uses**, and the disagreement Run 6 found *within* RFI Velocity runs *across* the 27. Measured, not read off the source:

- **Inclusive on the calmer side** (the edge value reads better): A2.9 Resource Loading at both corridor edges, A6.2 Safety at the benchmark and at twice and five times it, A6.3 Environmental at ninety-five per cent, A4.10 Specification Conflict Density at 0.60.
- **Exclusive on the calmer side** (the edge value reads worse): A5.6 Queueing at 0.15, A5.7 Agent-Based Supply Chain at 0.10, A4.4 NCR Rate at 0.15.

**A5.6 and A5.7 are the pointed case.** Run 7 brought them into agreement with the look-ahead measure on *abstention*, and they remain in disagreement with it on *inclusivity*: the look-ahead ladder is inclusive on the calm side and these two are exclusive, on ratios of exactly the same kind.

**A2.3 CCPM has a degenerate edge.** At zero chain completion the Amber threshold is zero and the arm is inclusive, so **a project exactly on plan, having consumed no buffer at all, reads Amber** in its first period. This is the same shape as Run 6's finding that Cross-document Consistency has an unreachable edge: a boundary that is correct in general and wrong at the only point that matters.

**A2.2 saturates.** Every schedule index at or above 1.2 gives the identical minimum buffer of 5.0 days, exhausted over the range, because of the clamp. Not a defect; recorded so a reader does not take the module to distinguish fast projects.

**Domain summary.** Twelve of the 27 accept at least one input that cannot describe a project. Six of those twelve return a **calm** band for it, which is the harmful direction: A1.6 at 140 per cent complete, A2.5 on a negative consumed float, A2.10 on a negative index and on over-completion, A4.10 on a negative document risk, A5.5 on a negative count, A6.1 on a score of 150, A6.2 on silence.

---

## Modules Still Unresolved

**None.** All 27 carry exactly one bucket, the totals sum to 27, and the suite asserts the sum. No module was assigned by elimination: each bucket assignment is defended by a case in the suite and a row in `code_audit/run8_module_classification.csv`.

---

## Inputs for ChatGPT's Corpus and Dataset Creation

Three build packages. Every asset must carry the label `SYNTHETIC_RESEARCH_FIXTURE`. **None is created in this run.**

### Corpus A — Synthetic Canonical Project Structures
Full schemas: `code_audit/run8_required_project_corpus_specs.csv` (field names, types, primary keys, relationships, units, minimum and recommended counts, period structure, valid ranges, edge cases, known-answer fixtures, ground truth).

| Package | Modules served | Shared schema core |
|---|---|---|
| `CORPUS_A2_activity_network` | **A2.1, A2.5, A2.10, A2.11** (Bucket 2 follow-on) and feeds `CORPUS_A2_critical_chain` | `activities` + `predecessors` + `calendars` + `schedule_snapshots`, one full snapshot per period so float history is derivable. Float may be negative and that is not an error. |
| `CORPUS_A2_critical_chain` | A2.3 | extends `activities` with aggressive and safe durations, adds `buffers` and `buffer_consumption` |
| `CORPUS_A2_linear_production` | A2.2 | `locations` + `crews` + `production_records` |
| `CORPUS_A1_cost_uncertainty` | A1.1, and A3.6's follow-on | `cost_risk_ranges` + `wbs_cost_baseline`, three-point costs with a distribution flag |
| `CORPUS_A4_quality_audit` | A4.4 | `quality_audits` + `audit_findings`, findings carried across periods until closed |
| `CORPUS_A5_flow_processes` | A5.6, and A5.8's follow-on | `process_stations` + `work_item_arrivals` + `service_records` |
| `CORPUS_A5_supply_agents` | A5.7 | `supply_agents` + `agent_states` + `interaction_rules` + `agent_events` |
| `CORPUS_A6_environmental_audit` | A6.3 | `environmental_permits` + `permit_conditions` + `compliance_assessments` |

### Corpus B — Synthetic Reference, Training and Decision Objects
Full schemas: `code_audit/run8_required_reference_decision_specs.csv`.

| Object | Modules served | Grain | Minimum size |
|---|---|---|---|
| `DATASET_B1_scenario_payoff` | A5.4 | one action and scenario pair | 5 actions by 5 scenarios |
| `DATASET_B2_alternatives_matrix` | B2.19, and B2.18 as its follow-on | one alternative and criterion pair | 8 alternatives by 6 criteria, spanning each criterion so no criterion has zero variance |

### Corpus C — Optional Disabled-Module Decision and Reference Structures

| Object | Module | Grain | Minimum size | Gate |
|---|---|---|---|---|
| `DATASET_B3_reference_class` | A3.1 | one completed comparable project | 60 per class, at least fifteen per cent completing under budget | incremental-value test, then owner authorisation |
| `DATASET_B4_dependency_matrix` | A5.1 | one ordered pair of design elements | 7 by 7, 42 off-diagonal cells | incremental-value test, then owner authorisation |

---

## Guarantees

- **The exact Run 6 unresolved universe is reconciled, not guessed.** VERIFIED. Recomputed from the same arithmetic Run 6 used, reading Run 6's own coverage set out of the merged file rather than retyping 27 ids: 100 − 63 − 2 − 8 = 27, and the 27 match Run 6's printed list exactly.
- **All 27 have a current test result and exactly one owner-action bucket; the totals sum to 27; none is unresolved.** VERIFIED, asserted in the suite.
- **Every expected value derived by hand from the module's own stated formula, with the derivation beside it.** VERIFIED. No case in this file runs a module and records what it returned as its expectation. Where no independent oracle exists the case is a property, a pass-through contract or a disabled contract, and is labelled as such: A1.1 is `PROPERTY_ONLY_PASS` and says so.
- **Every added check proved able to fail.** VERIFIED, 185 of 185 mechanically, plus a hand injection of three expectations taking the suite to 229/232 and back to 232/232.
- **Properties asserted over a domain are exhausted or randomised.** VERIFIED: 65,856 combinations for the ranking finding, 1,600 seed and index pairs for the network finding, all four evidence subsets for the rework finding, 24 scalings for the queue ratio, 29 indices for the line-of-balance saturation, the whole hundredth grid for the ranking symmetry.
- **The production path is driven, not only the functions.** VERIFIED, section 12.
- **No production file changed.** VERIFIED three ways: the suite's own frozen-file guard with an empty permitted set against the pinned baseline `18b6b80`; a tree hash of `server/app/` and `assets/` taken at the start of the run and compared at the end; and `git diff --name-only origin/main`.
- **No module fixed, reactivated, relabeled or made voting.** VERIFIED. The voting set is still exactly two modules, and the two abstaining modules still abstain on every input.
- **The full existing suite returns to green after every temporary mutation is restored.** VERIFIED, section below.
- **Every module with a band given a case above, at and below each boundary.** PARTLY MET. Complete for A2.9, A6.2, A6.3, A5.6, A5.7, A4.4 and A2.10's Green edge. Not attempted for every ladder of every one of the 27, which would be a run of its own; the boundaries tested are the ones the classification turns on.
- **No migration applied to production, and production never inspected or queried.** VERIFIED. Throwaway SQLite only; 0020 through 0025 remain unapplied in production.

---

## Decisions Requiring Lin

1. **B2.18 MARCOS reports Red on every project in every period, and a perfect project scores zero.** It is on the Signal Ledger, which a participant reaches. This is the same class as Run 6's regret finding that you dispositioned by abstention in Run 7. The recommended disposition is the same, and the reason code already exists.
2. **A2.1 PERT can never report a healthy project either.** Two modules with unreachable healthy bands is no longer a coincidence; it is worth asking of every banded module whether each of its bands is reachable, which is a cheap sweep and is the natural Run 9 opener.
3. **Five of this run's sixteen defects are a fix that did not carry across to the module next door** — the unguarded denominator, the invented completion, the absent-source-scores-zero composite, the meeting-mentions-as-a-measurement fallback, and the out-of-domain input landing in the calm band. A defect-class sweep across the whole layer would be cheaper than finding the sixth one in Run 9.
4. **None of the 27 carries a Run 1 proxy qualifier.** The modules whose names most overstate what they compute — Agent-Based Supply Chain is a share of a procurement log, Discrete Event Simulation is a ratio of two percentages, Queueing Theory Bottleneck is a share of a look-ahead window — are exactly the ones the relabelling programme did not reach. Extending the qualifier set is a Run 1 scope decision and is yours, not this run's.
5. **The activity-network corpus serves four Bucket 2 modules as well as one Bucket 3 module.** If only one synthetic asset is built, build that one.
6. **A6.2 Safety currently reads Green when safety was never mentioned.** Of everything in this report this is the finding with the least defensible participant-facing consequence.

---

## What the Next Session Needs

1. **The sixteen Bucket 2 defects, dispositioned as one conversation rather than sixteen.** They fall into four classes: unreachable bands (A2.1, B2.18), unguarded domains (nine modules), absent-source composites (A5.5), and fabricated inputs (A6.2). The guard shapes for three of the four already exist in the shared eligibility layer Run 7 built.
2. **The band-reachability sweep**, across every banded module and not only the 27. Two of the four the taxonomy has checked so far have an unreachable healthy band.
3. **Corpus A's activity network first**, then the alternatives matrix, then the rest. The specifications are complete enough to build from without reopening the audit.
4. **The boundary-inclusivity convention** should be decided once and written down, because it is now three runs of findings and no rule.
5. **0020 through 0025 remain unapplied in production.** This run adds no migration and touched no schema.

**Files changed.** `server/tools/test_run8_retest_classify_27.py` (new), this report, the six `code_audit/run8_*.csv` artefacts, and `T6_HANDOFF.md`. No file under `server/app/`, `assets/` or `research/`. No file outside the repository was touched.
