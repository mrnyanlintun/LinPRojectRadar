# Run 138 — v70 corpus reassembly and requalification

**The corpus is internally consistent under v70 as far as it can be tested here, and it cannot
be completed from this container.** No stored computed result exists in this repository: a
freshly migrated database holds zero projects, zero computed results, zero observations, zero
documents and zero training runs, and no database file exists in the tree. Every stored result
the order describes lives in production Postgres, which the order itself places out of bounds.
So no corpus was reassembled, because there is none here to reassemble, and none was
manufactured to have something to recompute.

**What stands in the way:** the reassembly itself, which only the owner can run. **What the
owner must execute against production** is set out in full at the foot of this report, and the
one-line summary is: clone, inventory with the classifier this run landed, reassemble the rows
it classifies `reassembly_required` from raw documents rather than from stored signal inputs,
recompute the rest, compare on the clone, and only then repeat against production.

**This run did not need to change `server/app/simulation/`, and did not.** `SIMULATION_VERSION`
stays `sim-2026.09-v70` and no migration was added. Two files under `server/app/` changed, both
in `extraction_merge.py`, both stated below. No production database was contacted.

## Deployment sequence

Nothing in this run requires a deployment step beyond the ordinary push. The two production
changes are a corrected self-check and an added provenance key; neither changes a band, a
threshold, a weight or a stored figure. The v70 recomputation the owner triggers is unchanged
in shape by this run, and the procedure for it is at the foot of this report.

## Repository, branch, starting commit, environment

| | |
|---|---|
| repository | `/home/user/LinPRojectRadar` |
| branch | `main` |
| starting commit | `3015faf` |
| interpreter | `/usr/local/bin/python`, no virtual environment |
| database target | throwaway SQLite files in the session scratch directory, migrated to head `0033_recognition_matches` |
| production contacted | no. `DATABASE_URL` was unset in the session environment and was only ever set to a scratch file path |

Commands used: `git status --porcelain`, `git log`, `git diff`, `git fetch origin main`,
`git rev-parse`, `git merge --no-ff`, `git add <path>`, `git commit`, `git push -u origin main`,
`git checkout -- <path>`; `python -m alembic upgrade head`; `python -m app.extraction_merge`;
`python tools/<script>.py` with cwd `server/`; `find . -name __pycache__ -path '*/app/*' -exec
rm -rf {} +` after every fault injection.

## Pre-checks and premises verified

All eleven were taken by me on main before anything was dispatched.

| # | pre-check | result |
|---|---|---|
| 1 | Run 137 report and T6_HANDOFF read | Run 137 read in full. T6_HANDOFF is 13,743 lines, carries no authority since Run 133 and is stale by 40-plus runs. Not used as a premise |
| 2 | repository, branch, clean worktree, starting commit | as tabled above, tree clean |
| 3 | HEAD == origin/main | both `3015faff0cff888b9e069924e1ce42170c19b586` |
| 4 | `SIMULATION_VERSION` | `sim-2026.09-v70`, `models.py:1088` |
| 5 | current `ac` selection rule | `WRITER_TIERS` has no `ac` entry, with the Run 132 note that it must not regain one |
| 6 | pay application alone produces no `ac` | confirmed: its emissions are percent complete verified, contract sum, completed to date, and the two contingency figures. No `ac` emission exists |
| 7 | monthly report with eligible actual cost produces `ac` | confirmed, from `actual_cost` |
| 8 | `actualPctComplete` selection unchanged | confirmed, and deliberately so |
| 9 | `si["cpi"]` stored unrounded | confirmed at `extraction_merge.py:1530-1551` |
| 10 | throwaway database | yes, per agent, migrated before use |
| 11 | `DATABASE_URL` not production | it was unset; nothing could reach production by accident |

**One premise of mine was half-true and it mattered.** I told both agents that the module
self-check in `extraction_merge.py` asserts CPI 0.909 with the monthly report present. It does,
and it **was failing on main at `3015faf`**. See "Items found and fixed" below.

## v70 selection and precision proofs

`server/tools/test_run138_assembly_and_precision.py` carries T1 through T8 against the real
production paths: `assemble_signal_inputs`, `select_signal_inputs`, `emit_observations`,
`simulation.models.check_inputs`, the four EVM entry points, and `documents.run_and_store`.
**`RESULT: 83/83 checks passed`**, taken by me on merged main. Without a database it reports
68/69 plus one BLOCKED, because T8 refuses to pass vacuously rather than skipping.

## Affected-period inventory, by classification

`server/tools/test_run138b_inventory.py` classifies a `computed_results` row into exactly one
group, from the row itself:

| test | classification |
|---|---|
| the project is a training project | `training_period`. Run 136 F2/F3 only. **Run 132 cannot apply** — the training engine holds `ac` in state and never selects it from a document |
| the `ac` source document type is `pay_application` | `reassembly_required`, Run 132 |
| the stored `cpi` differs from its own row's quotient | `reassembly_required`, Run 135 H1 |
| neither, but a banded module is one of A1.8, A3.4, C1.3, A2.12, B2.18, B2.19, H6, H7 | `recompute_only` |
| otherwise | `unaffected` |

A CPI counts as rounded only when it differs from its own quotient, so a quotient that is
already three-place exact is not mistaken for evidence of rounding. The H1 favourable edge, a
true 0.9995 stored as 1.0, is caught. **12/12 checks passed**, and the classifier was proved
able to fail: flipping the rounding test from inequality to equality gives 5/12.

**The inventory, over the corpus this container can reach:**

| classification | count |
|---|---|
| reassembly_required | 0 |
| recompute_only | 0 |
| training_period | 0 |
| unaffected | 0 |
| total `computed_results` rows | **0** |

**R5, expected against actually moved.** Every named correction — Run 132; Run 135 H1, H2,
A3.4, C1.3, A2.12; Run 136 F1, F2, F3 and the A6.4 factors; Run 137 `packages_due` — moved
**zero stored periods locally, because there are zero**. The single project-period whose raw
documents this repository records, PRJ-002 period 1, moves three module bands and one category
posture, measured below. **Production counts are unproven from here and must not be guessed.**

A training run is ten periods of thirty days. Zero rows exist locally; the production count is
unproven.

## Test results, T1 through T8

Every injection below was run, observed, cleared of stale bytecode and restored, with the tree
confirmed clean afterwards. I re-took the headline figure and injection D myself on main.

| test | what it proves | injection | counts |
|---|---|---|---|
| **T1** both documents present | `ac` 1,900,000 from the monthly report, provenance naming document, version and as-of date; CPI is EV over that figure, not over the payment | re-add the pay-application `ac` emission **and** the `ac` writer tier | 83/83 → 54/83; `ac` read 1,633,500 with pay-application provenance and CPI 1.1111111111111112 |
| **T2** pay application only | `ac` is `None` and not zero; no source record; CPI absent; the input check returns false without raising; A1.7, A1.8, A1.6 and A1.1 all abstain with no band and none Green; no carry-forward, structurally, because `ac` is not an identity field | the emission alone; separately, adding `ac` to the identity fields | 83/83 → 66/83, with TCPI and VAC both reading **Green** on the retainage-net figure; and 83/83 → 79/83 with carry-forward returning 1,900,000 |
| **T3** monthly report only | `ac` present, CPI computes, the input check passes, neither EVM module abstains. A1.6 still abstains for its missing planned-value curve, asserted separately so the two reasons cannot be conflated | drop the monthly report's `actual_cost` emission | six T3 checks fall |
| **T4** retainage conflict | on identical BAC, EV and period, 1,633,500 is exactly 90% of EV and is less than the stated cost; CPI comes from the monthly report at 0.9553, over cost, where the payment figure gives 1.1111, under cost. Through the production A1.8 the stated cost bands **Yellow** and the payment figure bands **Green** | as T1 | four T4 checks fall |
| **T5** percent complete unchanged | the pay application is still preferred for `actualPctComplete`, value sourced from it, and `ac` has no tier at all. Retention reduces the payment, never the percentage certified: the G702 figure is certified before retainage is withheld, so it is the same quantity, independently verified | reverse the preference | 83/83 → 80/83, source flips to the monthly report |
| **T6** CPI precision | EV 9,995 over AC 10,000 stores exactly 0.9995, inside the H1 window, and differs from its own rounded form, which is 1.0. Through the production module: **before the fix, Green; after, Yellow** | restore the rounding H1 removed | 83/83 → 73/83, ten checks fall across four sections and A1.8 reads Green where the true index gives Yellow. **I re-took this injection myself: 82 → 73 → 82 before my own fix landed, 83 → 73 → 83 after** |
| **T7** the A1.8 edge | 200 budgets log-spaced from $1k to $200M at CPI exactly 0.90 give **one** band, Amber, and **one** variance percent, −11.111111111111116, equal to the formula computed independently. The dollar variance does vary with the budget, asserted too | revert to the pre-Run-135 path | **two** bands, Amber and Red, and **thirteen** distinct variance percents across the same 200 budgets |
| **T8** no historical rewrite | not blocked. A row is written and stamped v69, then the production recompute order is followed: mint an identifier, set the supersede pointer, insert. The prior row stays readable with its inputs, results, status, source documents, timestamp and version unchanged; two rows exist; the new row has a distinct identifier, is the live one, and carries v70 | test-side: reuse the identifier, skip the supersede, mutate the standing row | four checks fall |

**T8 needed two fixes before it could fail at all**, both recorded in the file: rows are expunged
and re-read from the database on both sides, because otherwise the prior row was the same Python
object as the first and every check compared a value with itself; and the before-snapshot is
taken from a reloaded row too, because JSON turns tuples into lists. This is the checks-that-
cannot-fail class caught in the act.

## Reassembly process

Only one period could be assembled here, and it was assembled from raw documents, not from
stored signal inputs. The prohibited shortcut was not used anywhere. On PRJ-002 period 1 that
shortcut is the difference between A1 Green and A1 Amber, which is precisely why the order
forbids it.

## Recompute process

No period qualified as recompute-only, because no stored period exists. The classifier that
identifies them is landed and proved.

## PRJ-002 Period 1 full readout

Reassembled from the monthly report and the G702 pay application, both as-of 2025-01-31,
through `assemble_signal_inputs` at that cutoff, then the full computation and the Decision
Brief. **Reassembled, not recomputed.** I re-ran this myself on merged main.

| quantity | value |
|---|---|
| BAC | 3,000,000 |
| PV | 1,900,000 |
| EV | 1,815,000 |
| **selected `ac`** | **1,900,000** |
| `ac` source and provenance | monthly report, field `actual_cost`, document `mr1`, as-of 2025-01-31 |
| stored `cpi` | 0.9552631578947368 |
| CPI as EV ÷ `ac`, full precision | 0.9552631578947368 |
| **is the stored CPI rounded?** | **No.** It equals its own quotient exactly. Rounded it would be 0.955 |
| stored `spi` | 0.9552631578947368 |

The pay application's 1,633,500 paid to date supplies no actual cost and appears nowhere in the
cost identity.

**A1.7 to-complete performance index.** Formula `(BAC − EV) / (BAC − ac)`, inputs 1,185,000 over
1,100,000, raw **1.0772727272727274**, band **Amber**. The ladder is Green at or below 1.00,
Yellow to 1.05, Amber to 1.10, Red above.

**A1.8 variance at completion.** Formula `(1 − 1/CPI) × 100` on the unrounded CPI, raw
**−4.683195592286515** percent, variance **−140,495.87**, band **Yellow**, against the owner's
Yellow edge of −5.263157894736842.

**All A1 module results.** A1.7 Amber; A1.8 Yellow. A1.2 abstains awaiting history, two periods
needed. A1.5 abstains because the cost performance history is too short for a time series model
to be identified from it. A1.6, A1.9 and A1.11 abstain for an absent canonical structure: no
time-phased baseline, no approved time-phased expenditure baseline, and neither a change-order
register nor two independent forecasts.

**A1 category posture: Amber.** Roll-up basis, verbatim: *"A1.7 Amber −1; A1.8 Yellow +1 — 2
banded modules, total +0, mean +0, which crosses into Amber."* Rule: the average of module
scores, set by A1.7 and A1.8.

**All A3 module results.** A3.2 Green, on a consumed fraction of 0.4 against a normalised burn
of 0.66. A3.3, A3.5 and A3.6 abstain for an absent canonical structure: no production record,
no overhead allocation base, no cost risk model.

**A3 category posture: Green**, on one banded module, carrying its own sentence that the
posture rests on one reading and should not be read as a settled category position.

**All five category postures.** A1 Amber. A2 not assessed. A3 Green, one reading. A4 not
assessed. A6 not assessed.

**Official project posture: "Awaiting analysis" — withheld.** The required core is A1, A2, A3,
A4, A6, and two of five carry a posture. Recorded beside the withholding and never in place of
it: weighted band **Amber**, weighted sum **+0.1333**, from *"A1 Amber −1 × 0.6222; A3 Green +2
× 0.3778 … 3 of the five weighted categories carry no posture (A2, A4, A6), so it was REMOVED
FROM THE DENOMINATOR and the remaining weights renormalised over A1, A3."* An unassessed
category is never scored as zero.

**Rendered Decision Brief.** The posture block states "Awaiting analysis", not official, fused
band Amber, sum +0.1333, and names A2, A4 and A6 each as not assessed with the sentence that the
status is withheld rather than imputed and no value was substituted. The finding reads: *"An
official project posture is withheld: 2 of the 5 required categories carry a posture and 3 do
not (A2, A4, A6). That withholding does not qualify what was assessed: Cost & EVM Performance
(Amber, A1.7 tcpi 1.0772727272727274)."* The why block gives the required-core rule, both
category rules and both arithmetics, then warns that A3 rests on a single banded module. The
forecast carries TCPI 1.0772727272727274 and variance −140,495.87. The drivers block names A1.7
as having set the posture, with its full boundary provenance. Adverse readings, limitations, the
question, the weighted voting and the audit blocks are all present. **No remedy, deadline, role
or authority appears anywhere in it.**

## Prior-to-v70 comparison table

The prior column is reconstructed by putting both defects back. **It is not a claim about any
stored production row.**

| project / period | prior `ac` | prior source | v70 `ac` | v70 source | prior CPI | v70 CPI | EVM result | A1 posture | overall posture | brief |
|---|---:|---|---:|---|---:|---:|---|---|---|---|
| PRJ-002 / 1 | 1,633,500 | pay application, amount paid to date | 1,900,000 | monthly report, actual cost | 1.111, stored rounded | 0.9552631578947368, unrounded | A1.7 Green→**Amber**, A1.8 Green→**Yellow** | **Green → Amber** | withheld → withheld; recorded band Green +2.0 → **Amber +0.1333** | eight blocks differ |

Module band changes measured: **three** — A1.7 Green to Amber, A1.8 Green to Yellow, B1.2 Green
to Amber. Category changes: **one**, A1. A3 unchanged. The published project status is unchanged,
withheld both ways; the band recorded beside it changed. The eight differing Decision Brief
blocks are posture, finding, why, forecast, drivers, adverse readings, question and weighted
voting.

**The pay-application-only condition, measured:**

| prior condition | v70 condition | correct interpretation |
|---|---|---|
| CPI calculated from the payment amount: 1,815,000 ÷ 1,633,500 = 1.111, favourable | `ac` unavailable, EVM abstains | data insufficiency is visible; no favourable performance is inferred |

Measured: `ac` absent, CPI absent, no `ac` source record. A1.7 and A1.8 both abstain and neither
appears among the computed modules, reason "Insufficient data: upload required documents". The
project status is "Awaiting analysis". **EVM analysis withheld — authoritative actual cost is
unavailable for the reporting period.**

## Training artefacts recomputed

Reported separately as the order requires. **Computed result: zero stored locally, nothing to
recompute. Recommendation basis: zero stored. Debrief: zero stored.** The code path is corrected
and live through the execution endpoint. Production content is unproven from here. Note that a
training period can never be a Run 132 case: the training engine holds `ac` in state and never
selects it from a document, so only the Run 136 rounding corrections apply to it.

## EVM abstentions and their reasons

For PRJ-002 period 1: A1.2 insufficient history, two periods needed; A1.5 cost performance
history too short to identify a time series model; A1.6 no time-phased baseline; A1.9 no
approved time-phased expenditure baseline; A1.11 no change-order register and no two independent
forecasts; A3.3 no production record; A3.5 no overhead allocation base; A3.6 no cost risk model.
For the pay-application-only case: A1.7 and A1.8, both for absent authoritative actual cost.
**None was treated as Green.** A1 and A3 formed their postures only from modules that spoke.

## Category and project status changes

One category moved, A1, from Green to Amber. The published project status did not move: it is
withheld both before and after, because three required categories are unassessed either way.
The band recorded beside the withholding moved from Green to Amber.

## Decision Brief changes

Eight blocks differ between the reconstructed prior and v70, listed above. The wording rules
were not touched; the differences are entirely consequences of the corrected figures.

## Study-use gate result — **does not pass**

| # | condition | state |
|---|---|---|
| 1 | every affected project-period reassembled or recomputed as its classification requires | **open**, and unreachable from here. Vacuously met locally at zero rows |
| 2 | v70 outputs recomputed and provenance-checked | **met for PRJ-002 period 1 only**: the actual cost carries document type, document id, source field, version and as-of date, and the stored CPI was verified equal to its own quotient |
| 3 | PRJ-002 period 1 read and accepted | read and reported here. **Acceptance is the owner's**, and the prior-state discrepancy below wants a ruling first |
| 4 | comparison identifies every changed module, category and project outcome | met for PRJ-002 period 1, **open** for everything else |
| 5 | qualification suite passes | **no corpus suite was run, because there is no corpus.** The bearing suites pass on merged main: the assembly and precision suite 83/83, the actual-cost selection suite 31/31, the A1/A3 band contract 54/54, the inventory classifier 12/12, the H1 copies 23/23, run17 222/222, run36 42/43, run41 32/33 |
| 6 | owner explicitly approves the v70 corpus | **open** |

Open: 1, 3, 4, 5 and 6.

## Iteration log

| finding | attempt | change | proof | disposition |
|---|---|---|---|---|
| T1 both documents | 1 of 10 | suite section written against the real assembler | injection A2 → 54/83; restored 83/83 | RESOLVED |
| T2 pay application only | 1 of 10 | as above | injection A → 66/83; injection F → 79/83 | RESOLVED |
| T3 monthly report only | 1 of 10 | as above | drop the emission → six checks fall | RESOLVED |
| T4 retainage conflict | 1 of 10 | as above, banding both figures through the production module | injection A2 → four checks fall | RESOLVED |
| T5 percent complete | 1 of 10 | as above | reverse the tiers → 80/83 | RESOLVED |
| T6 CPI precision | 1 of 10 | as above | injection D → 73/83, re-taken by me | RESOLVED |
| T7 A1.8 edge | 1 of 10 | 200-budget sweep at CPI 0.90 | injection E → two bands, thirteen variance values | RESOLVED |
| T8 no historical rewrite | 2 of 10 | first version compared objects with themselves; rows are now expunged and re-read on both sides | injection G → four checks fall | RESOLVED |
| affected-period classifier | 1 of 10 | five-way classifier over a stored row | flip the rounding test → 5/12; restored 12/12 | RESOLVED |
| PRJ-002 period 1 | 1 of 10 | assembled from raw, not recomputed | figures reproduce independently on main | RESOLVED |
| the stale H1 guard | 1 of 10 | re-pointed to the quotient of the fixture's own figures | restore the rounding → fails with 0.909; restore the pay-application emission → fails on the pay-application rule | RESOLVED |
| the missing source field | 1 of 10 | the raw key is carried from the declared mappings to the source record | drop the pass-through → 82/83 with that check failing on None; restored 83/83 | RESOLVED |

No finding needed more than two attempts. Nothing reached the cap.

## What the owner must run against production

None of this was run here. Steps 1 through 8 run on a **clone**; production is touched only at
the end, and only after the comparison is accepted.

1. **Clone the production database and never touch the original.** Point `DATABASE_URL` at the
   clone. Everything below runs against the clone.
2. **Inventory, and report it before recomputing anything.** With cwd `server/`, run
   `python tools/test_run138b_inventory.py`. It refuses a Postgres URL by design, so either
   alias the clone or remove that guard deliberately and record that you did. It prints one row
   per live computed result — prior actual cost, its source document type, prior stored CPI,
   classification, and the corrections that apply — then the counts by classification.
3. **Freeze.** Confirm that computed results are superseded by pointer and never updated in
   place, and that observations stay append-only. Verify no step issues an update or a delete
   against either.
4. **Reassemble every `reassembly_required` row from raw.** Documents and uploads to
   observations to `assemble_signal_inputs` at the period cutoff. **Not** from stored signal
   inputs. Persist a new row with its source documents populated, and set the supersede pointer
   on the row it replaces.
5. **Verify per period before believing any band:** the selected actual cost has document type
   `monthly_report`, or there is no actual cost at all with an explicit absence reason; and the
   stored CPI equals earned value over actual cost exactly. Failing either means the period was
   not reassembled.
6. **Recompute the `recompute_only` rows** through the project computation over their existing
   correct inputs, then category postures, project posture and Decision Brief. Do not reassemble
   these.
7. **Recompute training.** For every training run re-derive the computed result, the
   recommendation basis and the debrief through the corrected engine and debrief path, and
   report the three separately.
8. **Compare and requalify on the clone.** Then, and only once that comparison is accepted,
   repeat steps 4 through 7 against production.

**The production reassembly is genuinely required, not a precaution.** Recomputing over stored
signal inputs reproduces the retainage-net actual cost and the rounded CPI faithfully and passes
every check. On PRJ-002 period 1 that shortcut is the difference between A1 Green and A1 Amber.

The F6 archived-row count from Run 137 remains outstanding and belongs with this recomputation,
not ahead of it. Its SQL is in the Run 137 report.

## Guarantees verified

Each was asserted by a check that was proved able to fail.

- A payment application alone never supplies actual cost.
- A monthly report with eligible actual cost supplies it when present.
- No actual cost is imputed from the payment amount, billed value, percent complete, budget,
  earned value, planned value, or a prior period's actual cost. Carry-forward is refused
  structurally, not by convention.
- Every selected actual cost carries document type, document id, **source field**, as-of period
  and extraction reference. The source field was missing until this run; see below.
- Every absent actual cost carries an explicit absence reason.
- EVM modules lacking actual cost abstain and never compute a band.
- An abstaining module is never treated as Green.
- No stored CPI is rounded before a band reads it.
- No prior stored signal input is overwritten; recomputation supersedes and inserts.
- No production database was contacted.
- The Decision Brief states computed findings and limitations only.

## Guarantees not met

None of the above is unmet on the code paths. What is unmet is the **corpus** side of the gate:
conditions 1, 3, 4, 5 and 6, all of which need production data or the owner's ruling.

## Items found and fixed

**1. The H1 guard left behind.** The self-check at the foot of `extraction_merge.py` still
asserted the stored CPI equalled 0.909 — the value from before Run 135 H1 removed the storage
rounding. Running the module directly had been failing on the very defect H1 fixed, because the
true quotient is 0.9090909090909091. It is re-pointed to the quotient of the fixture's own
stated figures rather than a transcribed presentation value, so it cannot drift again. Proved
able to fail twice: restoring the rounding fails with 0.909; restoring the pay-application
emission fails first on the pay-application rule. Found by agent A, fixed by me.

**2. A selected field named its document but not its source field.** The owner's invariant asks
for five identifiers and only four held. Observation emission dropped the raw extraction key, so
the source record could not carry it: a reader could see that actual cost came from a given
document but not that it was read from the `actual_cost` field. The key is now carried from the
declared mappings, which are the only place that pairing exists, rather than reconstructed later
where a second mapping would become a second authority for the same fact. It is omitted rather
than written null when absent, exactly as the four existing keys are. Proved able to fail:
dropping the pass-through returns the suite to 82/83 with that check failing on `None`.

## Items found but not fixed

**1. Observations emitted through hand-written calls still carry no source field.** The declared
mappings now carry it, which covers every field in the EVM cost identity, but the hand-written
emissions for change orders, safety reports and the other structured types do not. They produce
an honest record with the key omitted rather than a null. Naming each one's raw key is a
per-type judgement, not a mechanical change, and it is left for a ruling.

**2. The Run 132 fixture's monthly report carries no as-of date.** It uses a period key where
the monthly report's as-of key is the report date, and the period key is not in the monthly
report's field list. Measured: that fixture's actual-cost source record has no as-of date. The
Run 132 suite passes only because it never asserts one, and it still passes at 31/31. Not fixed
because that suite is not this run's to re-point without a reason of its own.

**3. Neither new suite is in the tools classification CSV**, so the R4 completion check does not
cover them. One line each, left deliberately because the CSV is shared and Run 137's rule is not
to redo it casually.

**4. Two of the owner's prior-state figures did not reproduce.** The order gives actual cost
1,633,500, CPI 1.11, A1 Green, project Amber at a weighted sum of −0.11. The actual cost and A1
Green reproduce exactly. The stored CPI reconstructs as **1.111**, so 1.11 reads as a display
value rather than the stored one. The project reconstructs as **withheld with a Green band at
+2.0**, not Amber at −0.11. A sum of −0.11 requires A2, A4 and A6 postures that these two
documents cannot produce, so the production row presumably carries more documents than the
repository records. **Nothing was adjusted to reach the stated figure.** That figure is unproven
here, not contradicted, and it wants the owner's ruling before condition 3 of the gate can close.

**5. Run 137's open rulings are untouched by this run** and remain open: the A6.2 parameter
classification, the three undeclared participant-package files, the A1.1 guard subject, and the
driver-seeding question.

## Commit, branch, version, merge status

Branch `main`. Agent B merged at `91366d9`, agent A at `1a18735`, both `--no-ff`. Production
fixes at `a87bde3` and `5cd3c96`. `SIMULATION_VERSION` unchanged at `sim-2026.09-v70`; migration
head unchanged at `0033_recognition_matches`. Pushed to `origin main`, which triggers a Render
deploy.
