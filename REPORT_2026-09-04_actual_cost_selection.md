# Actual cost is what the work cost — the pay application stops emitting `ac`

**Run 132 · 2026-09-04 · `SIMULATION_VERSION` MOVED: `sim-2026.09-v67` → `sim-2026.09-v68`.**
The stamp moves because this change moves the input a computed result rests on. No band,
threshold, weight, category rule, project rule or module population is touched.

## The three answers, at the top

1. **Both documents present** (monthly report states `actual_cost` 1,900,000; pay application
   states `amount_paid_to_date` 1,633,500): `ac` resolves to **1,900,000**, sourced from
   `monthly_report`, and **CPI = 0.955** (over cost). Before this change it resolved to
   1,633,500 and CPI read **1.111** (under cost).
2. **Only a pay application present**: `ac` resolves to **`None`**. It is not selected, no
   `sources["ac"]` entry is written, `cpi` does not compute, and every EVM module that requires
   `ac` **abstains** (`check_inputs(si, ("ac",))` → `False`). Before this change it resolved to
   1,633,500 and CPI read 1.111.
3. **Stored results need recomputing. Yes — and a recompute alone is not sufficient.** See
   *Bearing on the corpus* below.

---

## Two of the order's premises were false. A third correction is the briefer's, and it holds.

### The order said the tie was broken by rank or sha256. There was no tie.

`server/app/field_registry.py` carries `WRITER_TIERS`, a **per-field writer-precedence table**,
and it decided this explicitly. The line, verbatim as it stood at the starting commit:

```python
"ac": {"pay_application": 0, "monthly_report": 1},
```

Lower tier wins outright. `_snap_pick` (`extraction_merge.py:1203`) sorts on
`(-tier, dated?, as_of, rank, doc_type, sha256)` — **tier is the first key**, so the pay
application beat the monthly report on tier 0 and nothing further was consulted. `as_of`, rank
and sha256 never entered it.

`_DOC_TYPE_RANK` (`extraction_merge.py:800`) is a **different, coarser** table and is only the
last tiebreak inside a tier. The comment immediately above it says so in the code's own words:
it "cannot resolve contested fields on its own — declared writer tiers do that."

**So: not arbitrary, not sha256, and not per-project. It was deterministic and wrong
everywhere identically.** That is worse in one way and better in another — the corpus is
uniformly wrong rather than inconsistently wrong, which makes the recompute tractable.

### The order said option 2 would be a structural change to shared machinery. It would have been one line.

Field-dependent ranking is the established idiom of this file, not a novelty: `bac` carries a
five-document ladder, `baselineContractSum` two, `submittalsTotal` two, `originalContingency`
two. Option 2 — ranking the monthly report above the pay application — was a **single-token
swap inside an existing table**. The owner was choosing between options on a cost estimate that
overstated option 2 by a wide margin, and understated how deliberate the existing behaviour was.

**I still did not take option 2.** Reasons below.

### On the `ac` line's provenance (the order's A.2)

`git log -S` puts it in `fc7be2c` "Training upgrade run 1: the quality thread (#212)" — the
commit that **created the file**. Every neighbouring entry in `WRITER_TIERS` records *why*:
`bac` ("A change order is the authoritative amendment to the contract sum…"),
`baselineContractSum`, `baselineEnd`, `qualityDeficienciesNoted` ("the A7 collision"),
`originalContingency` (a full Run 78 paragraph). **The `ac` line alone carried no reasoning.**
This is exactly the Run 124 situation the order names: a constant introduced with its file with
nothing recorded. It was not a decision deliberately taken.

---

## A. How `ac` was selected

`_NUMERIC_EMISSIONS` in `server/app/extraction_merge.py` had two writers of `ac`:

| Document type | Extraction field | Signal key | Line (start) |
|---|---|---|---|
| `pay_application` | `amount_paid_to_date` | `ac` | 884 |
| `monthly_report` | `actual_cost` | `ac` | 894 |

`field_registry.FIELD_KINDS` classes `ac` as `SNAPSHOT`, so `select_signal_inputs` routes the
group to `_snap_pick`, whose first sort key is the writer tier — and the tier table named the
pay application best. Confirmed by direct execution, not by reading.

## B. What the pay application actually offers

Everything a G702 states is a value or a payment, and **none of it is a cost**:

- `completed_to_date` — the value of work performed. That **is** earned value, and it is
  correctly emitted to `ev`.
- `amount_paid_to_date` — `completed_to_date` less retention. Earned value net of a withholding.
- `percent_complete_verified` — a percentage, certified.
- `original_contract_sum` — a budget figure, correctly a weak fallback for `bac` (tier 3).
- the two contingency figures — a summary line, correctly tier 1 behind the cost report.

There is no cost on the document. The emission was the whole defect.

**The trade-off, stated before it is taken.** Removing it means a period holding a pay
application and no monthly report has no `ac` at all. Measured, not assumed:

| | before | after |
|---|---|---|
| `ac` | 1,633,500 | `None` |
| `cpi` | 1.111 | `None` |
| `check_inputs(si, ("bac","ev","ac"))` | `True` | `False` |
| `check_inputs(si, ("ac",))` | `True` | `False` |

So A1.7, A1.8, A1.1, A1.5, B2.1, the EAC scenarios in `models_gov` and `budget_execution` in
`models_evm` all abstain in such a period where they previously computed. That is the real cost
and the owner should see it plainly: **modules that produced a number will now produce nothing.**

## C. Whether anything else has the same shape

- `completed_to_date` → `ev`: **correct.** Completed to date is the value of work performed;
  that is the definition of earned value. Not a conflation.
- `original_contract_sum` → `bac`: **correct and already ranked as a fallback** — tier 3 behind
  change order, contract and SoV. `→ baselineContractSum` is emitted only by `contract_value`.
- `percent_complete_verified` → `actualPctComplete`, ranked **above** the monthly report:
  **correct, and deliberately left.** See the verdict below.

**Does the near-synonym guard cover the cost figures?** No, and it could not have. The
near-synonyms the codebase keeps apart (`compliance_score` vs a firm rating;
`weather_days_claimed` vs `weather_days_approved`) are kept apart by **never mapping them to the
same key** — the guard is the emission table itself, not a runtime check. `validate_numeric_fields`
and `_range_check` police *ranges and signs*, never *meaning*. There is no mechanism anywhere on
this path that could have noticed that two different quantities were writing one key. The only
guard available is the emission table, and for `ac` it was set wrong. That is now fixed, and a
committed check holds it.

---

## The verdict on `actualPctComplete` — left as it stands, and why

`"actualPctComplete": {"pay_application": 0, "monthly_report": 1}` looks like the same shape in
the adjacent line. **It is not the same defect.**

`percent_complete_verified` on a G702 is the owner's or architect's *certified* completion
percentage — on the standard form, completed-to-date over the contract sum. **Retention reduces
the payment; it never reduces the percentage certified.** The figure is computed before any
withholding. So it is the *same quantity* as the monthly report's `actual_percent_complete`,
differing only in that it is independently verified rather than self-reported by the contractor.

Preferring the verified figure over the self-reported one is a defensible precedence, and it is
the same kind of judgement `bac`'s ladder records. **`amount_paid_to_date` is a different
quantity from actual cost; `percent_complete_verified` is the same quantity as actual percent
complete.** That is the whole distinction, and it is the reason one line moved and the other did
not. The reasoning is now written above the line in `field_registry.py`, where it was missing.

---

## What was changed, and why option 1

**Option 1 taken: the pay application no longer emits `ac` at all**, and `ac` therefore has one
writer and needs no tier entry.

Option 2 was cheap — one token — and I still rejected it. Under option 2 a period with no
monthly report keeps computing CPI from a figure that is systematically ~10% low, in the
reassuring direction, with nothing on the panel to mark it. The defect would not be removed; it
would be made *rarer*, which across fifteen projects and eight periods means it survives in
whichever periods happen to lack a monthly report and nobody would know which those were. The
owner's own rule settles it: **a fallback that produces a wrong answer is worse than an
abstention that produces none.** An abstention is visible; a 10%-optimistic CPI is not.

Option 3 (conditional emission) is mechanically identical to option 2 — tier ordering *is* the
conditional-fallback machinery — so it inherits option 2's objection exactly.

No retainage adjustment was invented. Adding retention back would compute a figure no document
states, in the reassuring direction.

### Files changed

| File | Change |
|---|---|
| `server/app/extraction_merge.py` | Removed `("amount_paid_to_date", "ac")` from the `pay_application` block of `_NUMERIC_EMISSIONS`, with the reasoning recorded in place. Re-pointed the in-file self-check assertion 7 (see below). Repaired a pre-existing broken assertion 5 (see below). |
| `server/app/field_registry.py` | Removed the `"ac"` entry from `WRITER_TIERS` — one writer needs no tier — replaced by a comment recording that it must not regain one, and the reasoning for keeping `actualPctComplete` as it is. |
| `server/app/simulation/models.py` | `SIMULATION_VERSION` `v67` → `v68`, with the reason above it, and `v68` appended to `SIMULATION_VERSION_HISTORY`. Nothing already in that tuple altered. |
| `server/tools/test_run132_actual_cost_selection.py` | New committed check, 31 assertions. |

### Two things found in the self-check that the order did not anticipate

**The in-file self-check encoded the defect.** `extraction_merge.py` asserted
`a["ac"] == 4400000` and `a["cpi"] == 0.909` on an evidence set whose only cost-ish figure was a
pay application's `amount_paid_to_date`. It is **re-pointed, not deleted**: `base` holds no
document stating an actual cost, so `ac` is now asserted absent and `cpi` absent, and a monthly
report is added to a second assembly to prove the stated figure is taken and does decide `cpi`.

**And the self-check had been dead since before this run.** Assertion 5 compared
`fields_by_doc["aaa"]` against four field names, but `evidence:<doc_type>:<key>` pseudo-fields
had since joined that list, so the module raised at assertion 5 **at the starting commit,
`029b4e8`, unmodified** — verified by `git stash`. Assertions 6 through 9 never ran. That is
precisely how the defective assertion 7 survived unexamined. I repaired it (signal-input fields
asserted as before, evidence pseudo-fields asserted as a set) because leaving it broken would
have left my own re-pointed assertion unreachable. `python -m app.extraction_merge` now prints
`extraction_merge self-check: OK`.

---

## Proof

Driven directly against `assemble_signal_inputs`, which is pure over observation rows. **No
model call was made or simulated; there is no key in this environment.** No database was
contacted.

**1. The demonstrated case.** Monthly report `actual_cost` 1,900,000 + pay application
`amount_paid_to_date` 1,633,500, same period.

| | before (`029b4e8`) | after |
|---|---|---|
| `ac` | 1,633,500 | **1,900,000** |
| `sources["ac"].docType` | `pay_application` | **`monthly_report`** |
| `cpi` | 1.111 | **0.955** |

**2. The fallback case.** Pay application only, no monthly report. `ac`: 1,633,500 → `None`.
`cpi`: 1.111 → `None`. `sources` has no `ac` entry. `check_inputs` for `("bac","ev","ac")` and
for `("ac",)` both go `True` → `False`, so the EVM modules abstain. Table in section B above.

**3. The check can fail.** The fault was reintroduced — `("amount_paid_to_date", "ac")` put back
in `_NUMERIC_EMISSIONS` and `"ac": {"pay_application": 0, "monthly_report": 1}` put back in
`WRITER_TIERS`. `tools/test_run132_actual_cost_selection.py` went from **31 passed / 0 failed**
to **19 passed / 12 failed**, reporting `ac: got 1633500, expected 1900000` and
`cpi: got 1.111, expected 0.955`. The in-file self-check also failed, at
`a["ac"] is None — a pay application must not supply actual cost`. Both were then restored and
both pass again. (The twelve failures are the discriminating assertions; the nine "nothing else
moved" assertions correctly pass in both states, being invariants rather than discriminators.)

**4. Nothing else moved.** Recorded before and after for the same documents, identical in every
cell:

| field | both docs | pay-app only |
|---|---|---|
| `ev` | 1,815,000 | 1,815,000 |
| `pv` | 1,900,000 | `None` |
| `bac` | 3,000,000 | 3,000,000 |
| `baselineContractSum` | `None` | `None` |
| `actualPctComplete` | 60.5 | 60.5 |
| `plannedPctComplete` | 63.3 | `None` |
| `originalContingency` | 150,000 | 150,000 |
| `remainingContingency` | 90,000 | 90,000 |
| `spi` | 0.955 | `None` |

`tools/test_run34_version_boundary.py`: **18/18 passed** after the stamp moved.

---

## Bearing on the corpus

**Every stored result that used a pay application's `amount_paid_to_date` as `ac` is wrong in
the same direction — CPI too high, cost performance too favourable — including PRJ-002 period 1.**
Because the tier table decided this deterministically rather than by sha256, the error is
uniform: wherever both documents were present the pay application won, always.

**A recompute alone is not sufficient.** The defect is in **selection**, not in the analytical
layer. `signalInputs` is selected by `select_signal_inputs` from stored observations and then
persisted with the result; a recompute path that re-runs the modules over the *stored*
`signalInputs` would faithfully reproduce the wrong `ac`. What is required is:

1. **Re-selection** of `signalInputs` from the stored observation rows, per project per period,
   at each period's own stored cutoff. The observations themselves are unaffected — the
   extraction prompt and field list are unchanged and nothing needs re-extracting.
   Note that after re-selection the stored observation rows will still contain an `ac`
   observation sourced from a pay application for periods assembled under v67; re-selection
   must be a fresh assembly from the raw extractions, not a re-pick over old observation rows,
   or the emission change will not take effect.
2. **Then** recompute the modules over the re-selected inputs, stamping `sim-2026.09-v68`.
3. **Periods that will now go Indeterminate must be expected, not treated as failures.** Any
   period whose only cost-bearing document was a pay application loses `ac`, and A1/EVM will
   abstain. Rows stamped v67 and earlier remain valid *under their own stamp* per this repo's
   convention, but they are not comparable to v68 rows on any cost measure.

**No production recompute was run.** `DATABASE_URL` pointed only at a throwaway file and
production Postgres was never contacted. This is left to the owner.

**No migration.** Nothing in the schema changes; only which figure is selected into an existing
column. Migration head remains `0033_recognition_matches`.

`T6_HANDOFF.md` was read (top block). It carries no authority by its own header and states
nothing this run contradicts, so it was not edited.

---

## Confirmation

- **Starting commit:** `029b4e8` (= `origin/main`, tree clean at start).
- **Ending commit:** see the commit that carries this file; tree clean after.
- **Migration head:** `0033_recognition_matches` — unchanged, no migration written.
- **`SIMULATION_VERSION`:** `sim-2026.09-v68` (was `sim-2026.09-v67`). History appended, not edited.
- **`git status --porcelain` before commit** showed only the intended files:

```
 M server/app/extraction_merge.py
 M server/app/field_registry.py
 M server/app/simulation/models.py
?? server/tools/test_run132_actual_cost_selection.py
?? REPORT_2026-09-04_actual_cost_selection.md
```

- All adds by explicit path. No `git add -A`, no `git add .`. Not pushed.
