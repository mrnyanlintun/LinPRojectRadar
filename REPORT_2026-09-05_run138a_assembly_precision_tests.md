# Run 138, agent A — Task 2: assembly and computation tests, before the corpus is touched

Nothing under `server/app/simulation/` was changed. `SIMULATION_VERSION` is untouched.
No production database was contacted: every run used a throwaway SQLite file under the
session scratchpad, migrated to `0033_recognition_matches`.

**Deliverable:** `server/tools/test_run138_assembly_and_precision.py`, carrying T1 through T8
against the production paths — `extraction_merge.assemble_signal_inputs`,
`extraction_merge.select_signal_inputs`, `extraction_merge.emit_observations`,
`simulation.models.check_inputs`, `models_evm.run_tcpi / run_vac / run_earned_schedule /
run_bayesian_eac`, and `documents.run_and_store` — never a re-implementation of any of them.

**Final figure, taken by me on the merged branch:** `RESULT: 82/83 checks passed`
(`68/69` plus `BLOCKED: 1` when `DATABASE_URL` is unset, because T8 refuses to pass vacuously).

The one failing check is deliberate and is a finding, not a broken test. See "Findings" below.

---

## The instrument

- Each expectation names, in a comment beside it, the source it is derived from (rule R2):
  the Run 132 order, the Run 135 H1/H2 rulings, `extraction_fields.py:392`'s monthly-report
  field list, `field_registry.py:214` and `:236-239`, A1.8's own band ladder, or arithmetic
  written out on this file's own fixture figures.
- Each section is wrapped in a `section` guard: an exception inside one T is recorded as a
  failed check for that T and the remaining sections still run. This was added *because* an
  injection proved the first draft could die mid-run and print no `RESULT` line, which under
  Run 135C ruling R4 is indistinguishable from a suite that had nothing to say.
- The T7 sweep table routes through the Run 135C `.artifact_scratch` mechanism
  (`tools/artifact_write.py::artifact_out`). `git status --porcelain` after a default run
  shows nothing; `.artifact_scratch/` is gitignored at line 36.
- T8 rolls back its transaction and leaves no row behind.

---

## T1 — both documents present

**Finding.** With a pay application and a monthly report in the same period, `ac` must come
from the monthly report, provenance must identify `monthly_report`, and CPI must use that figure.

**Proof.** `ac == 1,900,000`; `sources["ac"]["docType"] == "monthly_report"`;
`sources["ac"]` carries `documentId` `DOC-MR1`, `documentVersion` (sha256) `mr1` and
`asOf` `2025-01-31`; `cpi == 1815000 / 1900000 == 0.9552631578947368`, and
`cpi != 1815000 / 1633500`.

**Injection A2 (the Run 132 defect, whole).** Put `("amount_paid_to_date", "ac")` back into
`_NUMERIC_EMISSIONS["pay_application"]` *and* re-add `"ac": {"pay_application": 0,
"monthly_report": 1}` to `WRITER_TIERS`.
Before **82/83** -> injected **54/83**. T1's `ac` read 1,633,500, provenance read
`pay_application`, and `cpi` read 1.1111111111111112.
Restored, `__pycache__` cleared, **82/83**, `git status --porcelain` clean.

**Injection A (emission half only).** Emission restored without the tier: before **82/83** ->
injected **66/83**. T1 did *not* move (the monthly report still wins by rank), T2 collapsed.
This is why A2 exists — A alone does not exercise T1.

**Disposition: RESOLVED**, except the `sourceField` element of the provenance invariant — see
Findings, and the check that records it fails on purpose.

## T2 — pay application only

**Finding.** `ac` absent, no provenance record, the EVM input check fails cleanly, and
CPI/TCPI/VAC/Earned Schedule/EAC abstain with no zero, carry-forward, interpolation or
inferred value.

**Proof.** `ac is None` (and `is not 0`); `"ac" not in sources`; `cpi is None`;
`check_inputs(si, ("bac","ev","ac"))`, `("ac",)` and `("bac","cpi")` all return `False`
without raising; A1.7, A1.8, A1.6 and A1.1 each return `insufficient_data True`,
`status_color None`, and none is Green. No carry-forward is possible *structurally*:
`"ac" not in IDENTITY_FIELDS`, and feeding `select_signal_inputs` a prior period's real `ac`
observation as `carried` still yields `ac None` with no provenance entry.
`_NUMERIC_EMISSIONS["pay_application"]` emits no `ac` from any key.

**Injections.** A: **82/83 -> 66/83** (16 T2 checks fell; TCPI and VAC both read **Green** on
the retainage-net figure, which is the Run 132 defect reproduced).
F (`"ac"` added to `IDENTITY_FIELDS`): **82/83 -> 79/83** — the carry-forward check caught it,
returning `1,900,000` where `None` is required.
Both restored to **82/83**, tree clean.

**Disposition: RESOLVED.**

## T3 — monthly report only

**Finding.** `ac` from the monthly report, EVM eligible where the other inputs exist.

**Proof.** `ac == 1,900,000`, provenance `monthly_report`, `cpi == 0.9552631578947368`,
`check_inputs(("bac","ev","ac")) is True`, A1.7 and A1.8 do **not** abstain. A1.6 still
abstains, correctly and for a different reason — it needs the time-phased planned value curve
(`require_v3_structure`), which no monthly report states. That distinction is asserted so a
future change cannot quietly convert "no curve" into "no actual cost".

**Injection B.** Remove `("actual_cost", "ac")` from `_NUMERIC_EMISSIONS["monthly_report"]`.
Before **82/83** -> injected **56/74** (the denominator falls because two sections abort inside
their guard). Six T3 checks fell, `ac` read `None`, both A1.7 and A1.8 abstained.
Restored **82/83**, tree clean.

**Disposition: RESOLVED.**

## T4 — the retainage conflict

**Finding.** Same BAC, EV, PV and period from both documents; the payment figure is lower than
the actual cost; CPI must come from the monthly report, and the payment figure would produce a
falsely favourable CPI.

**Proof (all measured on the fixture, not assumed).** Both documents state EV 1,815,000 and
BAC 3,000,000 and cover 2025-01-31. `1,633,500 == 1,815,000 x 0.9` — the ten per cent
retainage identity. `1,633,500 < 1,900,000`. `cpi == 1815000/1900000 == 0.9553` (over cost);
the payment figure gives `1815000/1633500 == 1.1111` (under cost). Run through the production
A1.8 module at BAC 3,000,000: the stated cost bands **Yellow**, the payment figure bands
**Green**. The falsely favourable reading is shown, not described.

**Injection A2.** **82/83 -> 54/83**; four T4 checks fell, including "A1.8 on the stated cost"
reading Green. Restored **82/83**.

**Disposition: RESOLVED.**

## T5 — `actualPctComplete` selection unchanged

**Why it is not the same defect, documented in the file and printed by the suite:** retention
reduces the **payment**, never the **percentage certified**. `percent_complete_verified` is the
G702's certified completion percentage, computed before any retainage is withheld, so it is the
same quantity as the monthly report's `actual_percent_complete` — only independently verified
rather than self-reported. Preferring it is right, and it is preserved.

**Proof.** `WRITER_TIERS["actualPctComplete"] == {"pay_application": 0, "monthly_report": 1}`;
with both documents present `actualPctComplete` is 60.5 sourced from `pay_application`;
`"ac" not in WRITER_TIERS`.

**Injection C.** Reverse the preference to `{"monthly_report": 0, "pay_application": 1}`.
Before **82/83** -> injected **80/83**; two T5 checks fell and the selected source flipped to
`monthly_report`. Restored **82/83**.
**Injection A2** additionally broke "ac has no writer tier".

**Disposition: RESOLVED.**

## T6 — CPI precision

**Finding.** A true CPI in [0.9995, 1.0) stores unrounded and bands from the unrounded value;
the band before and after the Run 135 fix must be shown.

**Proof.** Fixture EV 9,995 / AC 10,000. Stored `cpi == 0.9995` exactly, inside the interval,
and `cpi != _round3(cpi)`. `_round3(0.9995) == 1.0` — that is what was stored before Run 135.
Both bands taken from the production A1.8 module:
**before the fix (rounded 1.0): Green. After the fix (unrounded 0.9995): Yellow.**
`vac_pct == (1 - 1/0.9995) x 100 == -0.050025012506238475`.

**Injection D.** Restore `_round3` on the stored cpi in `select_signal_inputs`.
Before **82/83** -> injected **73/83**. Ten checks fell across T1, T3, T4 and T6; T6's stored
cpi read `1.0`, and A1.8 read **Green** where the unrounded index gives Yellow — the H1 defect
reproduced end to end. Restored **82/83**, tree clean.

**Disposition: RESOLVED.**

## T7 — A1.8 edge at CPI exactly 0.90

**Finding.** The band must be identical across a budget sweep.

**Proof.** 200 budgets log-spaced $1,000 to $200,000,000, each run through the production
`run_vac` at `cpi = 0.90`. One band across all 200: **Amber** (0.90 is the inclusive amber
edge). One `vac_pct` across all 200: `-11.111111111111116`, equal to `(1 - 1/0.90) x 100`
computed here independently. The dollar VAC *does* vary with the budget, which it must, and
that is asserted too so the fix is not mistaken for making money budget-independent.

**Injection E.** Revert A1.8 to the budget-dependent path, `vac_pct = (vac / si["bac"]) * 100`.
Before **82/83** -> injected **76/83**. The sweep produced **2 bands** (`{'Amber', 'Red'}`) and
**13 distinct `vac_pct` values** across 200 budgets — the H2 defect reproduced on a 200-point
sample. Restored **82/83**, tree clean.

**Disposition: RESOLVED.**

## T8 — no historical rewrite

**Finding.** Prior signal inputs and results remain readable and unchanged; v70 outputs carry a
new version and provenance identity; nothing is overwritten in place.

It was **not** BLOCKED. It is provable without production data: a project is created in a
throwaway SQLite file, `documents.run_and_store` writes a first row, that row is stamped
`sim-2026.09-v69` (what a prior-run row looks like), and then the **production recompute order
from `a_adminrecompute`** is followed — mint the new ULID, set `superseded_by` on the outgoing
row, then insert — because `uq_computed_results_one_live` permits exactly one live row per
(project, period).

**Proof.** The prior row is still readable; its `signal_inputs`, `module_results`,
`project_status`, `source_documents`, `computed_at` and `simulation_version` are unchanged;
two rows exist for the project; the new row has a distinct `result_id`; the prior row names its
successor; the new row is the live one and carries `sim-2026.09-v70`, distinct from the prior
row's version, with its own `source_documents`, `seed` and `period_cutoff`.

Two things were needed to make these checks able to fail at all, and both are recorded in the
file: the rows are **expunged and re-read out of the database** on both sides of the comparison
(otherwise `prior` was the same Python object as `first` and every "unchanged" check compared a
value with itself), and the *before* snapshot is taken from a reloaded row too (JSON storage
turns tuples into lists, which a naive in-memory snapshot reported as a rewrite — measured:
that one check failed spuriously until fixed).

**Injection G (test-side, stated as such).** Make the recompute overwrite the prior row in
place — `new_id = old_id`, no supersede, mutate `signal_inputs` and `simulation_version` on the
standing row. Before **82/83** -> injected **78/83**: "prior version unchanged", "two rows
exist" (got 1), "the new row has a distinct identity" and "the prior row names its successor"
all fell. Restored **82/83**.

The injection is test-side rather than in `app/documents.py` because this agent does not own
that file and another agent may hold it. Stated plainly rather than glossed.

**Disposition: RESOLVED.**

---

## Findings, and what was not fixed

1. **The selected `ac` carries no source field.** The order's invariant is "document type,
   document id, source field, as-of period and extraction reference". `emit_observations` does
   not put the raw extraction key on the observation, so `_source_entry` cannot record it, and
   `sources["ac"]` has no `sourceField`. **The check for it is in the suite and it FAILS on
   main — that is the 1 of 83.** Closing it means editing `app/extraction_merge.py`, which this
   agent does not own. Unfixed, on the record, falsifiable.

2. **The Run 132 fixture's monthly report carries no as-of date.**
   `test_run132_actual_cost_selection.py` gives its monthly report
   `"report_period": "2025-01-31"`, but the monthly report's as-of key is `report_date`
   (`_AS_OF_KEYS`) and `report_period` is not in the monthly-report field list at
   `extraction_fields.py:392` at all. Measured: with that fixture `sources["ac"]` is
   `{'docType', 'value', 'documentId', 'documentVersion'}` with **no `asOf`**. The Run 132
   suite passes because it never asserts `asOf`. My fixture uses `report_date`, so T1 can
   assert the as-of period. Not fixed — `test_run132_*` is not mine.

3. **The `extraction_merge` self-check was failing on main at `3015faf`.** `python -m
   app.extraction_merge` died at line 1724 on `assert with_mr["cpi"] == 0.909` with
   `AssertionError: 0.9090909090909091` — a pre-Run-135 literal, i.e. the module's own guard
   still expected the rounded value H1 removed. I reported it; the coordinator fixed it in
   `a87bde3`. Verified after merging: `extraction_merge self-check: OK`.

4. **The new suite is not in `tools/TOOLS_CLASSIFICATION.csv`.** Neither is agent B's. Until a
   row classifying it `active` is added, Run 135C's R4 completion check does not cover it.
   Not done here because the CSV is shared and another agent may hold it. Recommended
   follow-up, one line.

## Premises that turned out false

- The brief's fact 7 said `extraction_merge.py:1711-1724` "has a self-check asserting
  `with_mr["cpi"] == 0.909`". True as stated — but the implication that it held is false: it
  was **failing**, and had been since Run 135 removed the rounding. See finding 3.
- The brief anticipated T8 might be BLOCKED for want of production data. It is not; it is
  RESOLVED against a throwaway SQLite file through the real `run_and_store` path.

## Cross-check against agent B

My figures, taken by me: `ac` 1,900,000 from the monthly report; `cpi` 0.9552631578947368
stored unrounded; A1.7 TCPI 1.0772727272727274 Amber; A1.8 `vac_pct` -4.683195592286515
Yellow; project status "Awaiting analysis". These match agent B's independently.
I did not verify B's A1-category-Amber claim; unproven from my side.

## Counts

| Injection | Target | Before | Injected | Restored |
|---|---|---|---|---|
| A | `pay_application` emits `ac` again | 82/83 | 66/83 | 82/83 |
| A2 | A, plus the `ac` writer tier | 82/83 | 54/83 | 82/83 |
| B | `monthly_report` stops emitting `ac` | 82/83 | 56/74 | 82/83 |
| C | `actualPctComplete` preference reversed | 82/83 | 80/83 | 82/83 |
| D | `_round3` restored on the stored cpi | 82/83 | 73/83 | 82/83 |
| E | A1.8 reverted to the budget-dependent path | 82/83 | 76/83 | 82/83 |
| F | `ac` added to `IDENTITY_FIELDS` | 82/83 | 79/83 | 82/83 |
| G | recompute overwrites in place (test-side) | 82/83 | 78/83 | 82/83 |

`__pycache__` was cleared after every injection and every restore. `git status --porcelain`
was clean after every restore.
