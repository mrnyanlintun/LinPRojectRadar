# Run 135, Agent A - cost modules, the rounding family, and the configured dead data

**`SIMULATION_VERSION` MOVED: `sim-2026.09-v68` -> `sim-2026.09-v69`**, once for the whole run,
appended to `SIMULATION_VERSION_HISTORY` in the same edit. It moved because H1 and H2 change
**published bands on A1.7 and A1.8, the two modules that vote on project status**, and because
S1, S5, the sweep's A3.4 find and M3 change published bands on A6.3, C1.3, A3.4 and A2.12. No
band edge moved anywhere in this run, no threshold was added, and no tolerance or epsilon exists
in any of it: what changed is *which quantity* is compared against the edges that were already
there, and *to what precision* the figure printed beside them is rendered.

- Branch: `worktree-agent-abb5be2550280300d`
- Starting commit: `6d9899f34d7b08561ccfc7979c1f05389df8f772`
- Ending commit: this report's own commit, reported in the final message
- Tree clean at end; no migration was added and none was required; nothing pushed, nothing merged.
- No model call was made or simulated. No production recomputation was run.

---

## 1. Disposition table

| Finding | Disposition | Attempts | Files:lines |
|---|---|---|---|
| H1 CPI rounded before storage | RESOLVED | 1 | `server/app/extraction_merge.py:1368-1402`; `server/tools/test_run132_actual_cost_selection.py:42,66` |
| H2 A1.8 Amber/Red edge flips with BAC | RESOLVED | 1 | `server/app/simulation/models_evm.py:766,:818-850`; `test_run133_a1_a3_band_contract.py:60-88` |
| H6 A1.7 prints `TCPI: 1` under Yellow | RESOLVED | 2 | `server/app/simulation/models_evm.py:716-735`; new `band_display.py` |
| H7 A1.8 prints `(0%)` under Yellow | RESOLVED | 1 | `server/app/simulation/models_evm.py:892-925` |
| Group 1 stamp move | RESOLVED | 1 | `server/app/simulation/models.py:1047,:1306` |
| S1 A6.3 rounds before banding | RESOLVED | 1 | `server/app/simulation/models_doc.py:~2860` |
| L1 A6.3/A6.4 on the retired path | RESOLVED | 1 | `server/app/simulation/models_doc.py:~2930` |
| S5 source reliability rounds before banding | RESOLVED | 1 | `server/app/simulation/models_dq.py:130-160` |
| M1 A3.3 stores a rounded index | RESOLVED | 1 | `server/app/simulation/models_ext.py:~951-995` |
| M2 four ladders print a rounded figure | RESOLVED | 1 | `models_ext.py` (A2.8, A3.5), `models_doc.py:~600,~790` (A4.3, A4.4) |
| H1 sweep - A3.4 (new, named by neither hunt) | RESOLVED | 1 | `server/app/simulation/models_ext.py:~1053-1080` |
| H1 sweep - C1.2 tolerance re-examination | RESOLVED | 1 | `server/app/simulation/models_dq.py:~268-300` |
| M3 A2.12 reads three of six float edges | RESOLVED | 1 | `server/app/simulation/models_ext.py` `_float_rule_band` |
| Group 5 - the five orphaned band sets | RESOLVED (2 wired, 3 verdicts) | 1 | `server/app/simulation/models_doc.py:~404,:428` |
| `project_posture.py:73,:80` asserts | RESOLVED | 1 | `server/app/simulation/project_posture.py:69-92` |

Nothing in this agent's scope is BLOCKED, UNRESOLVED AFTER 5, or NOT REACHED.
**No BLOCKED decision is required from the owner for this scope.** Two decisions are *offered*
below (section 6 orphan verdicts, section 5 unfixed sweep instances) but neither blocked a fix.

---

## 2. Per-finding record

### H1 - CPI rounded before storage; A1.8 bands the stored value - RESOLVED, 1 attempt

**Before.** `select_signal_inputs` computed the derived indices through `_round3` --
`floor(n*1000 + 0.5)/1000`, a half-up **presentation** helper -- and stored the result. A1.8
(`run_vac`, `models_evm.py:806-818`) bands on exactly that stored field. Reproduced through the
real modules, via `assemble_signal_inputs` on a `monthly_report`:

```
EV 9995 / AC 10000 -> stored cpi 1.0  -> A1.8 Green   (true index 0.9995 -> Yellow)
EV 8995 / AC 10000 -> stored cpi 0.9  -> A1.8 Amber   (true index 0.8995 -> Red)
```

Both errors favourable, and systematically so: half-up widens the favourable side of every edge
by half a rounding step, so every true index in [0.9995, 1.0) published as 1.00. Run 35 repaired
this defect *inside* the module and never reached the field the module reads.

**After.** The three derived-index lines store the quotient itself. Nothing rounded is stored in
its place -- the display helpers round at render, and a second stored "rounded CPI" would only be
a second thing a band could rest on by mistake.

```
stored cpi 0.9995 -> A1.8 Yellow
stored cpi 0.8995 -> A1.8 Red
```

**Proof can fail.** Restoring `_round3` on the cpi line returns both readings to Green and Amber
and the proof script to FAIL (exit 1); restored, `__pycache__` cleared on both transitions, PASS.

**Suite.** `test_run132_actual_cost_selection.py` expected `0.955` for `cpi` and `spi` -- which is
`_round3` of the fixture's own quotient, i.e. an expectation derived from the function under
test. Under **R2** both were re-pointed at the quotient of the fixture's stated figures
(1,815,000 / 1,900,000) with the source recorded beside each. 29 -> **31/31**.

### H2 - A1.8's Amber/Red edge flips with the contract sum - RESOLVED, 1 attempt

**Before.** The module computed `((BAC - BAC/CPI)/BAC) * 100` and compared it to edges built as
`(1 - 1/x) * 100`. Algebraically identical, numerically not. Reproduced:

```
CPI exactly 0.90:  BAC 1,000,000 Amber | 330,000,000 Red | 4,400,000 Amber | 15,000 Red
sweep $1k-$200M (16,758 budgets):  5.94% band Red at CPI 0.90
                                   only 0.82% reach the owner's Yellow rung at CPI 0.95
```

**After, under R1.** One quantity, and it is the one the Run 114 order names, quoted verbatim in
`fc9d60c`: `VAC% = (1 - 1/CPI) x 100`, computed in exactly that expression -- the same expression
all three edges are built in. The budget is not in it, so no band on it can move with the budget.
`_VAC_BUDGET_MET_PCT` is now written `(1 - 1/1.00) * 100`: the same number, expressed so a reader
sees all three edges as one expression at 1.00, 0.95 and 0.90. **No epsilon, no tolerance** -- a
tolerance would have left both paths in place and added an unauthorised threshold on top.

```
CPI exactly 0.90 -> Amber at ALL 16,758 budgets $1k-$200M
CPI exactly 0.95 -> Yellow at ALL 16,758
CPI exactly 1.00 -> Green  at ALL 16,758
```

The dollar figure `vac` is still `BAC - BAC/CPI`; it is money, it is reported, and it is not what
bands. The `bac == 0` refusal is unchanged, moved ahead of the arithmetic now that the percentage
no longer produces NaN there.

**Proof can fail.** Restoring the BAC-bearing expression returns CPI 0.95 to Amber and fails both
re-pointed checks; restored, `__pycache__` cleared, 54/54.

**Suite.** `test_run133_a1_a3_band_contract.py` carried two rows that **pinned this defect**
because Run 133 was forbidden to repair it (`VAC at CPI 0.95 -> Amber`, and
`A1.8 DEFECT: CPI 0.95 does not attain the Yellow edge -> True`). Under **R2** both are
re-pointed at the Run 114 order -- each edge inclusive on its favourable side -- with the source
recorded beside them, plus a new row asserting the band is identical across six budgets.
53 -> **54/54**.

### H6 - A1.7 prints `TCPI: 1` under Yellow - RESOLVED, 2 attempts

**Before.** `TCPI 1.0004 -> Yellow, "TCPI: 1"`; `1.0504 -> Amber, "1.05"`; `1.1004 -> Red, "1.1"`.
Each rounded *onto* an edge the value had crossed, on all three of the ladder's boundaries.

**Attempt 1** applied the new shared rule and introduced a double space in the rendered sentence
("must achieve  to finish"). PARTIAL -- the defect was gone and something else had moved.
**Attempt 2** fixed the string. RESOLVED.

**After.** `1.0004 -> "TCPI: 1.0004"`, `1.0504 -> "1.0504"`, `1.1004 -> "1.1004"`, each under its
unchanged band. **The band is not rounded to match the display** -- that is the Run 35 defect --
`tcpi` is untouched.

### H7 - A1.8 prints `VAC: $100 over budget (0%)` under Yellow - RESOLVED, 1 attempt

**Before.** `vac_pct -0.0100`, `vac_pct_display 0.0`, `"(0%)"`, band Yellow, beside "Green at or
above zero" -- and the display field **stored on the row**, so the contradiction was in the record.

**After.** `vac_pct_display -0.01`, sentence `"(0.01%)"`, band Yellow.

**The decision the order asked for, stated: the display-rounded figure is STILL STORED, and it is
stored boundary-safe.** It is not derived at render. Three existing guards --
`test_run35_closure_voter_identities` g06, `test_run36_fault_guards`, `drive_run37_browser` --
assert that the analytical field and the display field are separate objects with distinct values,
which is the Run 35 closure they exist to hold; deriving at render would delete the field those
guards read and the separation would stop being provable from a stored row. So the field stays
and the defect leaves the field. `abs()` is applied *after* the rule, never before: the edges are
signed and the rule must see the sign.

### The shared display rule (H6, H7, S1, S5, M1, M2, L1)

`server/app/simulation/band_display.py`, new, one module, one function:

> Print at the fewest decimals -- never fewer than the precision the site already used -- that
> keep the printed figure on the **same side of every edge of its own ladder** as the canonical
> value.

A reading not near an edge renders exactly as it always did; only a reading genuinely on an edge
grows a digit. A value that *is* exactly on a boundary still prints as that boundary -- that is
not the defect, the row and the sentence agree in that case. Nothing in it rounds a band, moves a
boundary, or introduces a tolerance. **H6/H7's display rule and M2's are the same rule**, as the
order required.

### S1 / L1 - A6.3 and A6.4 - RESOLVED, 1 attempt each

S1: `rate = round1(rate)` ran **before** the ladder, so the rounding decided the answer.
`94.95 -> Green` where it is Yellow; same upward flip at `84.95` and `69.95`. After: Yellow,
Amber, Red, raw rate stored, `"94.95%"` printed. L1 (A6.4): band already raw, row contradicted it
-- `min_rating` was `round1(worst)`, so `3.9501` banded Yellow and recorded `4.0`, the Green edge.
After: raw stored, `"worst 3.95/5"`. The individual ratings take the same rule because each is a
candidate for `worst` and printing one coarser put two figures for the same number in one
sentence.

**Does the path execute today? NO.** `models.py:2310-2311` runs
`VALIDATED.update(CAT89_CANONICAL)` **last**, and `CAT89_CANONICAL` carries both `A6.3` and
`A6.4` (verified by executing the import), so both `models_doc` functions are overridden on every
production route and remain as the historical record of the v16 line. Repaired regardless -- High
governs the hunts' severity split, and a defect on a path is repaired whether or not the path is
currently reached.

**Proof can fail.** Restoring `rate = round1(rate)` fails **9** checks (all three bands flip
favourable and all three sentences print the boundary). Restoring `round1(worst)` prints
`"worst 4/5"` under Yellow and fails 1.

### S5 - source reliability - RESOLVED, 1 attempt

`avg = round2(...)` ran before the ladder. `(159 x 0.80 + 0.40)/160 = 0.7975` is below the 0.80
Green edge; half-up made it `0.80` and published **Green**. After: raw average banded -> Yellow,
`avg_reliability` 0.797499..., sentence `"79.7%"`. Restoring `round2` returns Green, stores `0.8`
and prints `"80%"` -- 3 checks fail.

### M1 / M2 - RESOLVED, 1 attempt

M1 (A3.3): stored `productivity_index` was `round2` -- `0.9499` banded Yellow and the row stored
and printed `0.95` beside "at or above 0.95 is Green", contradicting the rule the comment at
`:940` states in terms. Now raw stored, boundary-safe printed.

M2, as **one rule, not four patches**:

| | before | after |
|---|---|---|
| A2.8 | 899/1000 Yellow, printed `0.9` beside "at or above 0.9 is Green" | prints `0.899`, stores raw; edges read from the module's own configured cuts |
| A3.5 | variance 5.04% Yellow, **the boundary sentence itself** read "here 5.0 per cent: at or below 5.0 per cent is Green" | message and boundary sentence render through one function, `_absorption_pct_display` |
| A4.3 | 249/2500 = 9.96% Green, printed "(10.0 per cent)" beside "at or above 10 is Yellow" | prints `9.96` |
| A4.4 | 49/2500 = 1.96% Green, printed "That is 2.0 per cent" beside "at or above 2 is Yellow" | prints `1.96` |

**Disclosed:** the A4.3/A4.4 hunks live in `models_doc.py` and rode into the S1/L1 commit, which
shares that file. They belong to M2 and are described in the M2 commit message. No other
finding's change is bundled anywhere.

### M3 - A2.12 reads three of six configured float edges - RESOLVED, 1 attempt

Read: `float_green_above` (20), `float_yellow_at_or_above` (11), `float_amber_at_or_above` (1).
**Never read:** `float_yellow_at_or_below` (20), `float_amber_at_or_below` (10),
`float_red_at_or_below` (0) -- all three configured, all three **printed in the boundary sentence
on every row**, all three deciding nothing.

```
f = 10.5  -> AMBER, beside "11 to 20 is Yellow; 1 to 10 is Amber"  (10.5 is in NEITHER)
f =  0.5  -> RED,   beside "at or below 0 is Red"                  (0.5 is not)
```

**Which of the order's two options, and why: all six are READ, not removed.** Removing them would
delete the only statement in the configuration of where each band *ends*, and every row prints
exactly those endings -- removal would leave the printed ladder unsourced, which is the defect one
layer along rather than a repair. The ladder is now banded as **continuous** from the
`at_or_below` edges, so no value falls between two bands, and the three `at_or_above` edges are
read as the consistency statement they are (each exactly one working day above the `at_or_below`
edge beneath it; the Yellow ceiling is the Green floor). A configuration failing that is not a
ladder with a gap but a ladder that disagrees with itself, and `FloatLadderInconsistent` is
raised rather than one reading silently picked.

**Every whole-day outcome is unchanged** -- proved at 25, 20, 11, 10, 1, 0, -3. `10.5` is now
Yellow and `0.5` Amber, each the band its own printed sentence names. That is a band change on
A2.12 and the v69 history note records it.

### `project_posture.py:73,:80` - RESOLVED, 1 attempt

Both were `assert`s carrying comments reading "executable, so the profile cannot ..." -- and under
`python -O` they are **not executable at all**. Neither is a debugging aid: the first is what
makes the project rule a *weighted vote* rather than an arbitrary scaling of one; the second is
the standing ruling that Data Integrity is a precondition for using the criteria and never a
criterion in them. Both now raise `ValueError` at import, each preserving its own message and
naming what would have moved.

**Proof can fail.** With `A1` edited 0.28 -> 0.38, `python -O -c "import project_posture"` raises,
naming the profile, its sum and the consequence -- where the assert version imported **silently**
and every published project status would have moved.

---

## 3. Full iteration log

```
finding            | att | change made                                              | proof result                        | suite                          | disposition
H1                 |  1  | drop _round3 from the 3 derived-index lines              | 0.9995->Yellow, 0.8995->Red         | run132 29->31/31 after R2 repoint | RESOLVED
H1 (fault inject)  |  -  | restore _round3 on the cpi line                          | proof FAILS (Green/Amber), exit 1   | -                              | fault confirmed
H1 (restore)       |  -  | restore file, clear __pycache__                          | proof PASSES                        | run132 31/31                   | restored
H2                 |  1  | vac_pct = (1 - 1/cpi)*100; Green edge as (1-1/1.00)*100  | 0.90 Amber and 0.95 Yellow at all 16,758 BACs | run133 51->54/54 after R2 repoint | RESOLVED
H2 (fault inject)  |  -  | restore ((bac-bac/cpi)/bac)*100                          | 0.95 -> Amber                       | run133 52 pass 2 fail          | fault confirmed
H2 (restore)       |  -  | restore file, clear __pycache__                          | 0.95 -> Yellow                      | run133 54/54                   | restored
H6                 |  1  | tcpi_display = band_figure(...)                          | "TCPI: 1.0004", sentence gained a double space | -                    | PARTIAL
H6                 |  2  | fix the double space in the f-string                     | "TCPI: 1.0004, the cost efficiency ..." | run133 54/54               | RESOLVED
H7                 |  1  | vac_pct_display = band_figure(...); abs() after the rule | -0.01 stored, "(0.01%)" printed     | run133 54/54, run34 18/18      | RESOLVED
H6+H7 (fault inj.) |  -  | restore _round3(tcpi) and round1(vac_pct)                | "TCPI: 1" and "(0%)" return         | -                              | fault confirmed
H6+H7 (restore)    |  -  | restore file, clear __pycache__                          | boundary-safe again                 | run133 54/54                   | restored
STAMP              |  1  | v68 -> v69, history appended, reasoning recorded         | -                                   | run34 18/18                    | RESOLVED
S1                 |  1  | remove round1 before the A6.3 ladder; display via rule   | 94.95 Yellow / 84.95 Amber / 69.95 Red | run135a 46/46               | RESOLVED
L1                 |  1  | A6.4 min_rating raw; all ratings on the shared rule      | 3.9501 Yellow, "worst 3.95/5"       | run135a 46/46                  | RESOLVED
S5                 |  1  | band the raw average; display via the shared rule        | 0.7975 Yellow, "79.7%"              | run135a 46/46                  | RESOLVED
M1                 |  1  | store raw productivity_index; display via the rule       | rule renders 0.9499 as 0.9499       | run135a 46/46                  | RESOLVED
M2                 |  1  | A2.8, A3.5, A4.3, A4.4 onto the one shared rule          | none prints its own boundary        | run135a 46/46                  | RESOLVED
Group3 (fault inj) |  -  | 4 faults, one at a time, restored between                | 9 / 1 / 3 / 1 checks fail respectively | 46/46 after each restore    | faults confirmed
SWEEP A3.4         |  1  | remove _round3 before the ladder; display via the rule   | 0.0504 Yellow, 0.1204 Amber, 0.2004 Red | run135a 49/49              | RESOLVED
SWEEP A3.4 (fault) |  -  | restore _round3(variance)                                | all three flip favourable, 3 fail   | 49/49 after restore            | fault confirmed
SWEEP C1.2         |  1  | derive cpi/spi unrounded; tolerance meaning restated     | comparison exact where derived      | run135a 49/49                  | RESOLVED
M3                 |  1  | _float_rule_band reads all six; continuous ladder        | 10.5 Yellow, 0.5 Amber; whole days unchanged | run135a 58/58         | RESOLVED
M3 (fault inject)  |  -  | restore the three-edge expression                        | 10.5 Amber, 0.5 Red -- 2 fail       | 58/58 after restore            | fault confirmed
GROUP 5            |  1  | wire A4.3/A4.4 ladders to band_reference_data.json       | ladders byte-identical to the literals | run135a 60/60               | RESOLVED
GROUP 5 (fault)    |  -  | edit ncr amber edge 5.0 -> 7.5 in the JSON               | module ladder moves to 7.5          | restored, 60/60                | fault confirmed
project_posture    |  1  | two asserts -> two explicit raises                       | imports clean under -O              | run135a 60/60                  | RESOLVED
p_posture (fault)  |  -  | A1 0.28 -> 0.38                                          | raises under -O (assert was silent) | restored, clean under -O       | fault confirmed
```

---

## 4. Suites - exact counts

| Suite | before this agent | after |
|---|---|---|
| `tools/test_run135a_cost_and_rounding.py` (new) | - | **60 pass, 0 fail** |
| `tools/test_run133_a1_a3_band_contract.py` | 53 pass, 0 fail | **54 pass, 0 fail** (2 expectations re-pointed under R2, 1 check added) |
| `tools/test_run132_actual_cost_selection.py` | 31 pass, 0 fail | **31 pass, 0 fail** (2 expectations re-pointed under R2) |
| `tools/test_run34_version_boundary.py` | 18/18 | **18/18** (re-run after the stamp moved) |
| `tools/test_run35_closure_voter_identities.py` | 9/15 (6 fail) | **9/15 (6 fail) - unchanged**, verified by stashing this agent's work and re-running |
| `tools/test_run36_fault_guards.py` | crashes: `ModuleNotFoundError: app.simulation.portfolio` | unchanged - this is finding **H10**, not this agent's scope |

`test_run35_closure_voter_identities.py` is finding **H8** and belongs to Group 6. Its baseline
here is **6 failures, not the 10 the order states**; this agent moved neither the count nor the
identity of any failure. Two of its failures are worth passing to whoever takes H8: `fault09`
reports its own guard has gone **vacuous** ("this fixture no longer has a display string that
disagrees with the analytical band"), and `fault14` reports `B4.4` has no name in the registry
authority.

---

## 5. The H1 rounded-field sweep - every instance found

**Fixed in this run** (all in this agent's files):

| Site | Field | What it did |
|---|---|---|
| `extraction_merge.py:1372,:1374,:1381` | `cpi`, `spi` | stored half-up; A1.8 bands it - **H1** |
| `models_ext.py:~1054` (A3.4) | `variance` | `_round3` **before** the 0.05/0.12/0.20 ladder - three favourable flips: 0.0504 Green->Yellow, 0.1204 Yellow->Amber, 0.2004 Amber->Red. **Named by neither hunt.** |
| `models_doc.py:~2860` (A6.3) | `rate` | `round1` before the ladder - **S1** |
| `models_dq.py:130` (C1.3) | `avg` | `round2` before the ladder - **S5** |
| `models_ext.py:~978` (A3.3) | `productivity_index` | rounded field stored, raw banded - **M1** |
| `models_dq.py:~268,:274` (C1.2) | `derived_cpi`, `derived_spi` | branched on a rounded quotient at tolerance 0.005 - re-examined, below |

**Found and NOT fixed - outside this agent's files, reported as the order requires:**

| Site | Field | Assessment |
|---|---|---|
| `training_engine.py:1301,:1302` | `si["cpi"]`, `si["spi"]` | **Exactly H1, second copy.** `_round3(ev/ac)` stored on the training path's `si`, which the same banding modules read. The H1 fix does not reach it. |
| `training_engine.py:1283,:1284` | `si["actualPctComplete"]`, `si["plannedPctComplete"]` | same shape; both read in decision contexts by `models_ext`, `models_dq`, `models_gov` |
| `training_engine.py:1377,:1378` | `cpi`, `spi` | third copy of the same expression |
| `training_debrief.py:43,:44` | `cpi`, `spi` | `round(x, 3)` stored on the debrief record |
| `models_fuzzy.py:378` (B2.18 MARCOS) | `score` | `score = _round3(score)` **immediately before** a 0.65/0.50/0.35 ladder - band-on-rounded, same family as S1. **B2.18 is not in `CAT7_CANONICAL`**, so unlike A6.3 this is not obviously a retired path. |
| `models_fuzzy.py:418` (B2.19 CRITIC-TOPSIS) | `score` | identical shape, identical ladder |

**Found and assessed as NOT the defect:** `models_gov.py:1066` rounds `score` but the band is
decided by the `efficient`/`tradeoff`/`dominated` booleans, not by `score`. The display-side
`int(js_round(pct))` figures at `models_dq.py:52,:188,:318` and `models_doc.py:285,:329,:364`
band raw and round only for display; they are the *M2 shape* rather than the S1 shape, and were
left rather than expanded into unverified work at the end of the run.

**The C1.2 tolerance re-examination the order asked for.** The 0.005 tolerance was **ten times
the rounding step** -- which is precisely why the module whose whole purpose is to notice
disagreement could not see H1: a half-up stored index differs from the true quotient by at most
0.0005. `_round3` is gone from both comparisons, so like is compared with like. **The 0.005 stays
and its meaning changes**, which is worth the owner knowing: it is no longer a rounding allowance
-- there is no rounding step left to absorb -- but the **cross-document agreement** tolerance the
method is defined over, for the case where an index arrives from a document rather than from this
platform's arithmetic. Where the index was derived here the comparison is now exact. Narrowing it
further is a question about what a document disagreement *is*, not a rounding question, and is
left for the owner.

---

## 6. `band_reference_data.json` - the five band sets no module reads

Verified by grepping every `_BR.entry(...)` call in `server/app/`.

| Band set | Verdict |
|---|---|
| `submittal_first_review_rejection_bands` | **LADDER TO WIRE - wired in this run.** Not an orphan: `models_doc.py:404` retyped its 35/20/10 figures as literals, so the same ladder existed in two places with nothing holding them equal. Now read from the configuration. |
| `ncr_rate_bands` | **LADDER TO WIRE - wired in this run.** Same condition, 10/5/2, `models_doc.py:428`. |
| `pert_criticality_bands` | **KEEP, and mark SUPERSEDED - do not remove.** Not dead: `tools/drive_run104.py:160` reads it deliberately, to re-apply the Run 102 activity-level rule to a Run 104 reading so the reversal is *measured* rather than asserted. Removing it silently breaks that measurement. It is a superseded ladder retained as evidence, and the file should say so. |
| `milestone_slip_ratio_bands` | **ORPHAN TO REMOVE.** A2.7 was re-banded at Run 103 onto the same hybrid slip rule A2.12 uses (`critical_path_control_bands`); nothing in `app/` or `tools/` reads this entry. Removal recommended and **not** done here: it deletes owner-configured data with its own provenance note, which is the owner's call. |
| `construction_frequency_band_cutoffs` | **ORPHAN TO REMOVE.** The safety module bands on `safety_benchmark_ratio_bands` and `construction_industry_recordable_rate` instead; nothing reads this. Same recommendation, same reason for not acting. |

**The smallest decision the owner is asked for (not blocking):** delete
`milestone_slip_ratio_bands` and `construction_frequency_band_cutoffs`, or state that they are
retained deliberately. Either answer closes them; the present state -- configured, provenanced,
and read by nothing -- is the hazard the order names.

---

## 7. Recomputation

**A production recomputation IS REQUIRED and was not run.** Triggering it is left to the owner.
It must cover:

1. **Every project period whose stored `signalInputs` carry `cpi` or `spi`** -- the stored field
   itself changes (H1), so the inputs must be re-assembled before anything reading them is
   re-run. `docDate` and every other field are unaffected.
2. **A1.7 (TCPI) and A1.8 (VAC) on every period** -- the two **core voting modules**, so H1 and H2
   can move a *project status*, not merely a row. Any period whose true CPI falls in
   [0.9995, 1.0005) or within a few ULP of 0.90 or 0.95 is a candidate to change band.
3. **A3.4 (Material Cost Variance)** -- any period whose absolute variance is within 0.0005 of
   0.05, 0.12 or 0.20. A3.4 does **not** vote (`registry.CORE_VOTING_MODULES`).
4. **C1.3 (Source Reliability)** -- any period whose raw weighted average is within 0.005 of 0.80,
   0.65 or 0.50.
5. **A2.12 (Critical Path Analysis)** -- only periods whose controlling-path float is **not a
   whole working day** and falls in (0, 1) or (10, 11). Every whole-day outcome is unchanged.
6. **Category and project postures for every period touched by 1-5**, because A1.7, A1.8 and
   A2.12 feed the weighted vote.
7. **Not required:** A6.3 and A6.4. Both `models_doc` implementations are overridden by
   `CAT89_CANONICAL` on every production route, so no stored row was produced by the code
   repaired under S1 and L1.

Rows already stamped `sim-2026.09-v68` and earlier remain valid **under their own stamp** and are
not comparable to v69 rows on A1.7, A1.8, A3.4, A2.12 or C1.3.

---

## 8. `git status --porcelain` before each commit

```
# before 64c2d93 (H1)
 M server/app/extraction_merge.py
 M server/tools/test_run132_actual_cost_selection.py
?? server/app/simulation/band_display.py            (uncommitted here, landed with H6)
?? server/tools/test_run135a_cost_and_rounding.py   (uncommitted here, landed with S1/L1)

# before a3ed127 (H2)
 M server/app/simulation/models_evm.py
 M server/tools/test_run133_a1_a3_band_contract.py
?? server/app/simulation/band_display.py
?? server/tools/test_run135a_cost_and_rounding.py

# before 26012b8 (H6)
 M server/app/simulation/models_evm.py
?? server/app/simulation/band_display.py
?? server/tools/test_run135a_cost_and_rounding.py

# before aef5a14 (H7 + stamp)
 M server/app/simulation/models.py
 M server/app/simulation/models_evm.py
?? server/tools/test_run135a_cost_and_rounding.py

# before 235db37 (S1 + L1) / 1825fe5 (S5) / 047e7f2 (M1 + M2)
 M server/app/simulation/models_doc.py
 M server/app/simulation/models_dq.py
 M server/app/simulation/models_ext.py
?? server/tools/test_run135a_cost_and_rounding.py

# before 7b6d508 (sweep)
 M server/app/simulation/models_dq.py
 M server/app/simulation/models_ext.py
 M server/tools/test_run135a_cost_and_rounding.py

# before 56ebbec (M3)
 M server/app/simulation/models.py
 M server/app/simulation/models_ext.py
 M server/tools/test_run135a_cost_and_rounding.py

# before 335e09c (Group 5)
 M server/app/simulation/models_doc.py
 M server/tools/test_run135a_cost_and_rounding.py

# before 9714054 (project_posture)
 M server/app/simulation/project_posture.py

# before this report's own commit
?? REPORT_2026-09-04_run135a_cost_modules.md
```

Every stage was by explicit path; no bulk staging of any kind was used. **No `code_audit/` change
was staged or committed** -- `test_run34_version_boundary.py` rewrites
`code_audit/run34_simulation_version_execution_proof.csv` in place when run (finding M14) and it
was run three times here; it never appeared in a staged set.

`__pycache__` under `server/app/` was cleared before **every** restore-confirmation run, without
exception. No fault was left in the tree: every injection was followed by a restore and a
re-measured green.

---

## 9. Files changed

```
server/app/extraction_merge.py                       H1 (the _round3 lines only; no other region)
server/app/simulation/band_display.py                NEW -- the one shared display rule
server/app/simulation/models_evm.py                  H2, H6, H7
server/app/simulation/models.py                      the stamp and its history note only
server/app/simulation/models_doc.py                  S1, L1, M2 (A4.3/A4.4), Group 5 wiring
server/app/simulation/models_dq.py                   S5, the C1.2 sweep re-examination
server/app/simulation/models_ext.py                  M1, M2 (A2.8/A3.5), sweep A3.4, M3
server/app/simulation/project_posture.py             the two asserts
server/tools/test_run135a_cost_and_rounding.py       NEW -- 60 checks
server/tools/test_run132_actual_cost_selection.py    2 expectations re-pointed under R2
server/tools/test_run133_a1_a3_band_contract.py      2 expectations re-pointed under R2, 1 added
```

`server/app/documents.py`, `backend/`, `server/tests/` and the rest of `server/tools/` were not
touched. Within `extraction_merge.py` only the derived-index block was changed: `_snap_pick`,
`select_signal_inputs`'s selection body and the `_evidence_qualification` wiring are untouched.
