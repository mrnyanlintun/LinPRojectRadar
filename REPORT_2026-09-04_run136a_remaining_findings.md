# Run 136 A — the remaining findings: F1 through F8

**`SIMULATION_VERSION` MOVED, v69 -> v70, because F1 changes what a published band rests on.**
B2.18 MARCOS and B2.19 CRITIC-TOPSIS each banded a `_round3`'d score against 0.65 / 0.50 / 0.35;
`_round3` is half-up, so any score in `[cut - 0.0005, cut)` was lifted onto its own cut and
published a rung too high. Neither module is in `CAT7_CANONICAL`, so the path executes and the
readings were published. No boundary moved. The history tuple was appended to in the same edit.

Branch: `worktree-agent-a349a1b543a4ae02f`. Starting sha `cd98235` (= origin/main at the branch
point). Migration head unchanged at `0033_recognition_matches`; no migration was written and none
was required. Not pushed, not merged.

---

## Disposition

| Finding | Disposition | Attempts | Files changed |
|---|---|---|---|
| F1 — B2.18 / B2.19 band a rounded score | **RESOLVED** | 1 | `server/app/simulation/models_fuzzy.py` (imports, `_MCDM_BAND_CUTS`, both band sites); stamp in `server/app/simulation/models.py` |
| F2 — CPI rounded before use, training engine | **RESOLVED**, and **LIVE** | 1 | `server/app/training_engine.py` (`_round3`, `:1283-84`, `:1301-02`, `:1377-78`, four prose sites) |
| F3 — CPI rounded before use, training debrief | **RESOLVED**, and **LIVE** | 1 | `server/app/training_debrief.py` (`_spend_summary`, `_counterfactual`, `build_debrief`) |
| F4 — a test expectation encodes the defect M5 fixed | **RESOLVED** | 1 | `server/tools/test_risk_register_and_notices.py:147-148` and the refusal block |
| F5 — superseded documents and the H4 seam | **RESOLVED — no change; the code's own comments settle it** | 1 | none (read `server/app/documents.py:480-486`, `:547-581`) |
| F6 — rows already projected from archived documents | **query written and proven; the production count is OUTSTANDING and needs the owner** | 1 | none |
| F7 — the two true-orphan band sets | **RESOLVED** | 1 | `server/app/simulation/band_reference_data.json` |
| F8 — `commitments_due` carries a bare superset alias | **RESOLVED** | 1 | `server/app/documents.py` (`_TD_COLS`) |

New file: `server/tools/test_run136a_remaining_h1_copies.py`, 23 checks, the durable cover for
F1, F2, F3, F7 and F8.

**Every tool-script number in this report was measured in this worktree and must be re-taken on
main.** One correction to the standing caution, recorded because it decides how F4's number
should be read: not all of these scripts hardcode `/home/user/LinPRojectRadar/server`.
`tools/test_risk_register_and_notices.py:36` sets `sys.path` from its own `__file__`
(`__file__.rsplit("tools", 1)[0]`), so its 129/129 *does* test this branch's `app/risk_values`.
It is still to be re-taken on main. Every proof in this report that is not a tool script was run
with `sys.path.insert(0, '.')` and cwd = this worktree's `server/`, so it tested this branch.

---

## F1 — B2.18 and B2.19 band on a rounded score. RESOLVED, attempt 1.

**Falsifiable outcome, stated before touching anything.** For every input, the band each module
publishes must equal the band the ladder gives for the FULL-PRECISION score, and the printed
figure must sit on the same side of every cut as that score.

**Reproduced.** The ladder in both modules is 0.65 / 0.50 / 0.35. Bisecting MARCOS's own score
construction to each cut and stepping down by one ULP:

```
cut=0.65  cpi=0.7393028063991319   raw=0.6499999999999997  round3=0.65  Yellow -> Green   FLIP
cut=0.50  cpi=0.24561754338394742  raw=0.4999999999999998  round3=0.5   Amber  -> Yellow  FLIP
   live run_marcos -> Green 0.65 | MARCOS score: 0.65 (utility vs ideal: 0.81)
```

The 0.35 cut is not reachable from that one-parameter family — MARCOS's score bottoms out near
0.486 as cpi falls — but the sweeps below cover it, and the CRITIC-TOPSIS sweep drives the
closeness coefficient directly and reaches all three.

**Before -> after.** `models_fuzzy.py:378` was `score = _round3(score)` followed by the ladder;
`:418` was `score = _round3(reading["closeness"])` followed by the same ladder. Both now take the
band from the full-precision quantity through a shared `_mcdm_color`, and the score is printed
through `band_display.band_figure(score, _MCDM_BAND_CUTS, 3)` — the rule Run 135 built, not a
fifth variant. The cuts are named once, in `_MCDM_BAND_CUTS`, so the band and the printed figure
cannot drift apart.

**Neighbourhood sweep of every cut, as A did for H2.**

* B2.18: 400,001 values of cpi across [0.20, 1.60], of which 7,524 land within 0.002 of a cut.
  **Misbands after the fix: 0.**
* B2.19: 12,003 closeness coefficients at 1e-6 steps across plus or minus 0.002 of all three
  cuts. **Misbands after the fix: 0.**
* Printed figure: the same 12,003 values. **0 print on the wrong side of a cut.**

**No input in the neighbourhood of any cut still bands differently from its full-precision
value.**

**Proof can fail.** Reintroducing the fault (`_mcdm_color(_round3(...))` at both sites, with
`__pycache__` cleared) returns **940** MARCOS misbands and **1,500** CRITIC-TOPSIS misbands.
Restoring and clearing `__pycache__` again returns 0 and 0.

**Suites.** test_run10_bucket2_corrections 161/161, test_run30_canonical_oracles 239/239,
test_run29_closure_version_boundary 18/18 (this one asserts `HISTORY[-1] == SIMULATION_VERSION`,
so it covers the stamp move). test_run14_mismatch_remediation and
test_run20_cycle10_truthful_labels crash before a verdict — `ImportError: cannot import name
'portfolio'` and `KeyError: 'A3.8'`, both pre-existing members of F9's 66 and untouched here.

**The stamp.** `SIMULATION_VERSION = "sim-2026.09-v70"`, with the reason written above the line
and `"sim-2026.09-v70"` appended to `SIMULATION_VERSION_HISTORY` in the same edit, which is what
section 10.10 requires and what Runs 100 and 101 did not do.

---

## F2 — CPI rounded before use in the training engine. RESOLVED, attempt 1. **LIVE.**

**Live-or-latent, traced by registration and not by name** — Run 135 B's method for `backend/`.

```
POST /exec
  -> main.py:305      handler = ... or TRAINING_ACTIONS.get(action) ...
  -> training.py:408  TRAINING_ACTIONS = {trainingstatus, trainingstart, trainingstate,
                                          trainingdecision, trainingdebrief}
  -> a_trainingstate / a_trainingdecision
       -> _store_period  (training.py:140) -> signal_inputs_from_state -> run_and_store
          i.e. `documents.run_and_store`, "the same function the document path calls"
       -> _state_view    (training.py:155) -> build_recommendation  (line 191)
```

Both rounding sites sit on registered handlers of a served route. **The training path executes
today**, so F2 belongs in the recomputation set.

**Reproduced, on the engine itself.** With `ac = 10,000,000`, `ev = 8,995,100`:

```
true cpi            = 0.89951
si['cpi'] handed on = 0.9            <- rounded before use
B2.20 on si['cpi']  -> Yellow  Hypersoft [fair-fair-low]: score 0.55
B2.20 on true cpi   -> Amber   Hypersoft [poor-fair-low]: score 0.35
```

A favourable flip — the direction H1 always fails in. `actualPctComplete` was likewise handed on
as `22.488` for a true `22.487750000000002`.

**A second fault, found while fixing the first and fixed in the same edit.**
`training_engine._round3` was `round(v, 3)` — Python's half-to-EVEN — while every other `_round3`
on this platform (`models_fuzzy`, `models_evm`, `extraction_merge`) is `js_round`, half-UP. The
same ratio printed 0.899 in a training run and 0.900 on the document path: two algebraically
equivalent paths to one quantity, which R1 forbids. `_round3` is now `band_figure(v, (), 3)` —
the platform's half-up rule at three decimals — and its docstring says it is presentation-only
and must never be called on a quantity a band, a branch or a sum is about to read.

**One consequence outside the three named sites, stated rather than discovered later.** `_round3`
is also called at `training_engine.py:627` on the notice-lookback fraction, which now rounds
half-up instead of half-to-even. The two rules differ only on an exact tie at the fourth decimal,
and unifying them is the point of the change.

**Before -> after.** `:1283-84` and `:1301-02` drop `_round3` entirely and hand the ratios on.
`:1377-78` computes the ratios at full precision, records them in the recommendation's `basis`,
and prints `cpi_shown` / `spi_shown` in the four `why` sentences.

**Proof can fail.** Restoring `_round3(` at `si["cpi"]` returns `si['cpi'] handed on = 0.9` and
the flip; restoring the fix and clearing `__pycache__` returns 0.89951.

**Suites**, all on a fresh migrated throwaway SQLite: test_training_options 29/29,
test_training_events 42/42, test_training_regimes 45/45, test_training_quality 39/39,
test_training_resources 63/63, test_training_gating 43/43, test_training_loop **52/54**. The two
loop failures are the training-isolation checks and read 52/54 at `cd98235` as well, measured the
same way — pre-existing, unmoved. test_training_detail is a RETIRED artefact and says so.
test_training_portfolio_isolation was not run: it names `portfolio`, removed at Run 97, and is
one of F9's 66.

---

## F3 — CPI rounded before use in the training debrief. RESOLVED, attempt 1. **LIVE.**

**Live-or-latent.** `POST /exec` -> `TRAINING_ACTIONS["trainingdebrief"]` -> `a_trainingdebrief`
(`training.py:380`) -> `build_debrief` -> `_spend_summary`. A registered handler on a served
route. **Live**, and in the recomputation set.

**Reproduced — two faults.**

```
(a) true cpi = 0.8995   debrief printed 0.899   platform prints 0.9    DISAGREE
(b) played   0.85000 -> printed 0.85
    replayed 0.85004 -> printed 0.85                                   REAL DIFFERENCE HIDDEN
```

(b) is the one that matters for what this module is for. The debrief's whole purpose is to set
the position played beside the position replayed — `_spend_summary` is called once for each, at
`:162` and `:177` — and two ratios that genuinely differ printed as the same figure, so a real
difference between the run played and the run that might have been read as no difference at all.

**Before -> after.** `round(state["ev"] / state["ac"], 3)` becomes: compute at full precision,
then print through `band_figure`, passing **the other side of the comparison as the boundary the
printed figure must stay on its own side of**. `_counterfactual` hands the replayed state back
through a private `_replayed_state` key, which `build_debrief` pops and passes as `against`; it is
never served. Precision grows a decimal exactly when the two figures would otherwise collapse onto
each other, and is unchanged otherwise. Nothing here compares with a tolerance and nothing rounds
a decision.

**Proof after.** 200,000 ratios agree with the platform's half-up rule; 2,000 played/replayed
pairs with a genuine CPI difference print as identical **0** times; an ordinary reading still
prints `0.85`.

**Proof can fail.** Reverting the two lines to `round(cpi, 3)` returns **2,000 of 2,000** pairs
printing as identical. Restoring returns 0.

**Suite.** test_training_loop 52/54, the same two pre-existing failures.

---

## F4 — a test expectation encodes the defect M5 fixed. RESOLVED, attempt 1. Two lines.

**The source of the expectation, recorded beside it, under R2.** Not `parse_probability`. The
rule M5 implemented, recorded at `app/risk_values.py:102-121` and in Run 135 D's report section
M5: *refuse a bare integer where the register states no scale, because on a 1-to-5 likelihood
register the lowest-likelihood rows would otherwise read as certain — the reassuring direction,
and the one nothing downstream catches. The register reader supplies no scale hint
(`risk_register.py:344` passes `column_is_percent` and nothing else), so there is no basis on
which a bare "1" could be told from a 1 of 5, and refusing is the only honest answer.*

**Before.** `HANDLED = [..., ("0", 0.0), ("1", 1.0)]` — the pre-M5 behaviour asserted as correct.

**After.** Both removed from `HANDLED`. A new loop runs `"0"`, `"1"`, `"2"` and `"5"` through one
assertion — `ValueRefusal` whose reason names the ordinal ambiguity — so the four cases the rule
covers are tested together and cannot drift apart. The source is cited at both edits.

**127/127 -> 129/129** (two expectations removed, four added). *Worktree figure; re-take on main
— though as noted above this script resolves `sys.path` from its own `__file__`, so it did test
this branch.*

**Proof can fail.** Restoring M5's old `_FRACTION` pattern in `app/risk_values.py` returns
**127/129**, with `"0"` reading `RiskProbability(value=0.0)` and `"1"` reading
`RiskProbability(value=1.0)` while `"2"` and `"5"` still refuse. Restored with `git checkout --`
and `__pycache__` cleared; 129/129 returns.

---

## F5 — superseded documents and the H4 seam. RESOLVED: no change. The comments settle it.

**The two readings, and what each implies.**

*Reading A — superseded should keep projecting.* A superseded document has been REPLACED by a
revision, not withdrawn. The revision is in the same period and projects its own rows, so
excluding the old one normally loses nothing; but where a revision is partial, rows only the old
version carried disappear from the store. Under this reading `_live_document_ids` is widened by
one line to readmit superseded ids while still excluding archived ones.

*Reading B — superseded should not project.* Excluding it is the whole point of the seam.

**Which the code's own comments support: B, decisively, in three places.**

1. `_period_documents`'s docstring, `documents.py:480-486`: *"SUPERSEDED DOCUMENTS ARE EXCLUDED
   FROM COMPUTATION AND ARE NOT DELETED. Before 0013 both versions of a revised document reached
   assembly, and which one's figures survived was decided by `_ordered_docs`'s sha256 tiebreak: a
   content hash. First-wins fields took the lower hash, last-wins fields the higher, additive
   fields counted BOTH (an RFI log revised from 10 to 12 assembled to 22), and a downward
   correction to a keep_max field was discarded entirely."* Reading A reintroduces exactly that:
   two versions of one revised document both projecting rows into the same store.
2. `_live_document_ids`'s own docstring, `documents.py:571-578`, under the heading **"ONE
   DELIBERATE CONSEQUENCE, STATED RATHER THAN DISCOVERED LATER"**: *"the three stores stop
   projecting rows for a document a later upload in the same period replaced... the retention is
   untouched — no row is ever deleted or updated in place, and every row already stored stays
   readable — and what changes is only that a NEW row is no longer written for a document the
   document control has withdrawn from the period. **The readers already excluded superseded
   documents, so this makes the store agree with its own readers.**"*
3. The rows stay readable through `a_projectuploadstatus`, stated at both seams, *"which is what
   keeps a decision that referenced them reproducible"* — so nothing already decided becomes
   unreproducible.

The consequence was not an accident of H4. It was written down as intended, with its reason, in
the same edit that produced it, and the reason given is that the store now agrees with its own
readers. Widening would put them back into disagreement and would reopen the mixed-version defect
0013 exists to prevent. **No change made. This is not BLOCKED** — the comments answer the
question in as many words, so there is nothing here for the owner to rule on.

Seven callers, one definition: `documents.py:825, 915, 986, 1047, 1105`, plus
`_superseded_document_ids` and `_archived_document_ids` behind `_period_documents`.

---

## F6 — rows already projected from archived documents

**This environment cannot read production Postgres, and did not contact it.** `DATABASE_URL`
pointed only at throwaway SQLite files in the scratchpad. **Nothing was deleted.**

**The SQL that would count them.** The archive mark lives on `document_uploads.archived_at` and
is scoped to `(project_id, period)` — `documents` is shared content-addressed storage, so the
same bytes may be live evidence in another project or in another period of the same one. Every
join therefore matches on all three of `project_id`, `period` and `document_id`, exactly as
`_archived_document_ids` does.

```sql
-- RUN 136, F6. Rows ALREADY PROJECTED from a document the document control has ARCHIVED.
--
-- H4 (Run 135) stopped NEW rows being projected for an archived document. It did not remove
-- rows projected before that, which remain in the three projection stores and in the
-- observation store and are still read. This is the count. IT DELETES NOTHING.
--
-- The archive mark lives on `document_uploads.archived_at` and is scoped to
-- (project_id, period) -- `documents` is shared content-addressed storage, so the same bytes
-- may be live evidence in another project or another period. Every join below therefore
-- matches on all three of project_id, period and document_id, exactly as
-- `_archived_document_ids` does.

SELECT 'schedule_activities' AS store, s.project_id, s.period,
       COUNT(*) AS rows_from_archived_documents,
       COUNT(DISTINCT s.document_id) AS archived_documents
FROM schedule_activities s
JOIN document_uploads u
  ON u.project_id = s.project_id AND u.period = s.period AND u.document_id = s.document_id
WHERE u.archived_at IS NOT NULL
GROUP BY s.project_id, s.period

UNION ALL

SELECT 'project_risks', r.project_id, r.period, COUNT(*), COUNT(DISTINCT r.document_id)
FROM project_risks r
JOIN document_uploads u
  ON u.project_id = r.project_id AND u.period = r.period AND u.document_id = r.document_id
WHERE u.archived_at IS NOT NULL
GROUP BY r.project_id, r.period

UNION ALL

SELECT 'project_notices', n.project_id, n.period, COUNT(*), COUNT(DISTINCT n.document_id)
FROM project_notices n
JOIN document_uploads u
  ON u.project_id = n.project_id AND u.period = n.period AND u.document_id = n.document_id
WHERE u.archived_at IS NOT NULL
GROUP BY n.project_id, n.period

UNION ALL

-- The observation store. `_persist_observations` runs off `_period_documents`, so it has
-- never emitted for an archived document; rows here would predate the 0027 archive mark or
-- predate the archiving of a document that was live when it was read. Counted separately, and
-- withdrawn rows are counted separately again because `observations.withdrawn_at` is already
-- an archive mark on the row itself (migration 0029).
SELECT 'observations (not withdrawn)', o.project_id, o.period, COUNT(*),
       COUNT(DISTINCT o.document_id)
FROM observations o
JOIN document_uploads u
  ON u.project_id = o.project_id AND u.period = o.period AND u.document_id = o.document_id
WHERE u.archived_at IS NOT NULL AND o.withdrawn_at IS NULL
GROUP BY o.project_id, o.period

UNION ALL

SELECT 'observations (withdrawn)', o.project_id, o.period, COUNT(*),
       COUNT(DISTINCT o.document_id)
FROM observations o
JOIN document_uploads u
  ON u.project_id = o.project_id AND u.period = o.period AND u.document_id = o.document_id
WHERE u.archived_at IS NOT NULL AND o.withdrawn_at IS NOT NULL
GROUP BY o.project_id, o.period

ORDER BY 1, 2, 3;   -- positional: a UNION's ORDER BY may only name the first SELECT's columns
```

**Proof that the query works.** Run against a throwaway SQLite migrated with
`python -m alembic upgrade head` to `0033_recognition_matches`, seeded with a known population:
one archived document `D_ARCH` and one live document `D_LIVE` in project 1 period 3, plus **the
same `D_ARCH` bytes live in project 2 period 1** — the scoping trap the join must not fall into.
Seeded 3 schedule activities, 2 risks, 1 notice, 1 live observation and 1 withdrawn observation
from `D_ARCH`, and one row each from `D_LIVE` and from project 2.

```
store                           project  period   rows   docs
observations (not withdrawn)          1       3      1      1
observations (withdrawn)              1       3      1      1
project_notices                       1       3      1      1
project_risks                         1       3      2      1
schedule_activities                   1       3      3      1

RESULT: PASS -- the query counts exactly the rows from the archived document, and nothing
from the live document or from the other project where the same bytes are live
```

**THE PRODUCTION COUNT IS OUTSTANDING AND NEEDS THE OWNER TO RUN THAT SQL.** Until it is run, the
scope of F6 — how many rows, in which stores, for which projects and periods — is unknown.
Nothing in this run assumes a figure for it.

**What clearing would require, and what it would change.** Clearing is a DELETE against
`schedule_activities`, `project_risks` and `project_notices`, and — separately — a withdrawal
mark rather than a delete on `observations`, since migration 0029 gives that store its own
archive mark on the row and deleting would throw away the record of what was once read. It would
change what `_schedule_snapshot`, `_schedule_display` and `_milestone_history` return for the
affected periods, which changes `milestoneHistory`, which is A2.7's input — so it changes stored
readings. It therefore belongs **with** the recomputation and not ahead of it: deleting first
would leave stored results computed from rows that no longer exist, with no stamp to explain the
gap. Not done here.

---

## F7 — the two true-orphan band sets. RESOLVED, attempt 1.

**Confirmed by search across the WHOLE repository before removing**, not only `app/`: `grep -rn`
for all three names outside `.git` returns the JSON entries themselves,
`tools/drive_run104.py:160` for `pert_criticality_bands`, and report prose from Runs 104 and 135
and the dependency thread. **No module, tool, test, driver, JS file, spec or audit CSV reads
either orphan.**

**Removed:** `construction_frequency_band_cutoffs` — the safety module bands on
`safety_benchmark_ratio_bands` against the `construction_industry_recordable_rate` anchor
instead — and `milestone_slip_ratio_bands` — A2.7 was re-banded at Run 103 onto the same hybrid
slip rule A2.12 uses, `critical_path_control_bands`.

**Kept:** `pert_criticality_bands`. Not an orphan. `tools/drive_run104.py:160` reads it
deliberately, to re-apply the Run 102 activity-level rule to a Run 104 reading so the reversal is
*measured* rather than asserted; removing it would silently break that measurement. It keeps its
`superseded_by` mark. drive_run104 reads **47/53 before and 47/53 after**.

**The figures are recorded, not deleted without trace.** A `_removed_run136` note at the head of
the file carries both entries' boundaries, units and the reason each stopped being read. A
configured owner tolerance that once existed is part of this file's record after it stops being
read, and this file's whole ethic is to record rather than silently drop.

**Proof.** `band_reference.entry()` — which never raises, and answers with an explicitly
unconfigured stub — now returns `configured: False` and *"no reference entry named ... is
configured"* for both, and still returns the configured `pert_criticality_bands`. Three checks in
the new suite hold this.

**Suites.** test_run133_a1_a3_band_contract 54/54, test_run67_category9_and_no_band 21/21,
test_schedule_milestones 77/78 (77/78 at HEAD too), test_run135a_cost_and_rounding 60/60.

---

## F8 — `commitments_due` carries a bare superset alias. RESOLVED, attempt 1.

**Where the platform's position is recorded, and what it says.** It is recorded in four places
and **carries no direction**:

* `app/extraction_client.py:696-698` — the extraction contract applied to every field of every
  document: *"A field is returned ONLY when the document itself states that field, under a label
  or heading whose meaning matches the field's name. A different value sitting nearby, under a
  different label, is never a substitute, even if it is a plausible value of the right type and
  in a sensible range."*
* `app/simulation/models_ext.py:858-862`, the contingency-burn band — substituting a related
  quantity silently is *"the exact defect section 2 forbids"*, and where the quantity the ladder
  is drawn over is absent the module publishes the figures and asserts no band.
* `app/schedule_table.py:126` — a table that fails to resolve *"is passed over, which is the safe
  direction."*
* `app/simulation/lineage.py:241` — take the direction that *"can only refuse corroboration,
  never manufacture it."*

None of those is conditioned on the direction of the error. The H5 commit message (`aee0485`)
reasons about the FAVOURABLE direction because that was the case in front of it, and closes with
*"as does every denominator"* — it did not rule on denominators, it left them. **The established
position is to abstain on an adjacent quantity, whichever way the error falls. Applied.**

`commitments_due` is *"firm COMMITMENTS DUE in the reporting period"* (`extraction_fields.py`); a
commitment is the owner's own list — a required submittal, an RFI response, a procurement release
or delivery, a corrective-action closure, or a required change-document response. A column headed
only "Commitments" states no period and no status, so it may be every commitment the firm holds.
A6.4 already carries the honest alternative: with no denominator the factor reads UNAVAILABLE and
is *"not treated as Green"* (`contractor_factors.py:624-630`).

**Before -> after.** A trade-denominator row `{"Commitments": 100, "Commitments Met On Time": 90}`
produced `commitments_due: 100.0`; it now produces no `commitments_due` at all, and the numerator
is untouched at 90.0. Every stated heading still lands: `commitments_due`, `submittals_due`,
`rfis_due`, `responses_due`, `obligations_due`.

**Proof can fail.** The new suite read **22/23** before this change — the one failure being that
document reaching `commitments_due: 100.0` — and **23/23** after.

**Suites.** test_run135d_selection_and_assembly all passed, test_run126_register_row_count all
passed, test_run132_actual_cost_selection 31/31, test_run87_compliance_registers 33/33.

---

## Found in passing — findings for the next run, not fixed here

1. **`packages_due` accepts the bare alias `"packages"`**, `documents.py` `_TD_COLS`, alongside
   `"milestones_due"` and `"activities_due"`. Identical shape to F8, in the sibling denominator
   of the same table. Not touched: F8 names `commitments_due`, and bundling is forbidden by the
   loop's rule 2.
2. **`extraction_fields.py` still documents `inspections_passed` and `commitments_met` as
   recognised headings**, though H5 removed both from `_TD_COLS` at Run 135. The contract note
   and the code now disagree. `extraction_fields.py` is outside this agent's scope, and F8's
   removal of `"commitments"` adds a third line of the same drift.
3. `training_engine.py:627` calls `_round3` on the notice-lookback fraction — a computed
   quantity, not a printed one. Worth a look under the H1 lens in its own right.

---

## What the v69 recomputation must now cover

The v69 reassembly was already outstanding from Run 135. **This run moves the stamp to v70 and
adds to what must be recomputed.** Nothing was triggered here; it is left to the owner.

* **B2.18 MARCOS and B2.19 CRITIC-TOPSIS**, every stored reading. Their published band changes
  wherever the score fell in `[cut - 0.0005, cut)` on any of 0.65 / 0.50 / 0.35. F1.
* **Every training period's computed result**, because `signal_inputs_from_state` now hands the
  modules unrounded CPI, SPI and both percent-complete figures, and the whole analytical layer
  bands on them. The training path is LIVE. F2.
* **Every training recommendation's recorded `basis`**, which now carries the ratios themselves
  rather than the printed figures. F2.
* **Every training debrief**, whose two ratios and whose played-versus-replayed comparison change.
  F3.
* **A6.4 commercial-and-administration factors** for any firm whose `commitments_due` came from a
  column headed only "Commitments": those now read UNAVAILABLE rather than banding. F8.
* **F6's rows are NOT covered by a recomputation alone.** Rows already projected from archived
  documents remain in the three projection stores and are still read. The count must be taken in
  production first, with the SQL above, and clearing must be sequenced WITH the recomputation,
  never before it.
* Nothing in F5 or F7 requires recomputation: F5 changed no code, and F7 removed data nothing
  read.

---

## Iteration log

| finding | attempt | change made | proof result | suite | disposition |
|---|---|---|---|---|---|
| F1 | 1 | band on the full-precision score at `models_fuzzy.py:378` and `:418`; print through `band_display.band_figure`; cuts named once in `_MCDM_BAND_CUTS` | 400,001 + 12,003 sweeps, 0 misbands (940 + 1,500 with the fault reinjected); 0 of 12,003 printed figures contradict their band | run10 161/161, run30 239/239, run29 18/18 | RESOLVED |
| F1 | 1 (same commit) | `SIMULATION_VERSION` v69 -> v70, history appended in the same edit | test_run29_closure_version_boundary asserts `HISTORY[-1] == SIMULATION_VERSION` and passes | run29 18/18 | RESOLVED |
| F2 | 1 | drop `_round3` at `:1283-84` and `:1301-02`; full precision into `basis` at `:1377-78` with `cpi_shown` printed; `_round3` redefined as the platform's half-up rule and documented presentation-only | `si['cpi']` 0.9 -> 0.89951; the B2.20 flip Yellow -> Amber removed; fault reinjection returns 0.9 | options 29/29, events 42/42, regimes 45/45, quality 39/39, resources 63/63, gating 43/43, loop 52/54 = HEAD | RESOLVED, LIVE |
| F3 | 1 | `_spend_summary` computes at full precision and prints through `band_figure` against the other side of the comparison; `_counterfactual` returns the replayed state privately | 200,000 ratios agree with half-up; 0 of 2,000 genuinely-differing pairs print alike (2,000 of 2,000 with the fault reinjected); ordinary reading unchanged | loop 52/54 | RESOLVED, LIVE |
| F4 | 1 | `("0", 0.0)` and `("1", 1.0)` out of HANDLED; a four-case bare-integer refusal check in, with M5's rule cited as the source at both edits | 129/129; restoring M5's old `_FRACTION` returns 127/129 with the two reading 0.0 and 1.0 while "2" and "5" still refuse | test_risk_register_and_notices 127/127 -> 129/129 | RESOLVED |
| F5 | 1 | none — read `documents.py:480-486` and `:547-581` | the comments state the exclusion as deliberate, name the sha256-tiebreak defect it prevents, and say it "makes the store agree with its own readers" | — | RESOLVED, no change; not BLOCKED |
| F6 | 1 | none — wrote the counting SQL | seeded throwaway SQLite at head 0033: counts 3 / 2 / 1 / 1 / 1 exactly, excluding the live document and the other project holding the same bytes | — | query proven; production count OUTSTANDING |
| F7 | 1 | removed the two orphan entries; recorded their figures in `_removed_run136` | `entry()` returns `configured: False` for both and `True` for `pert_criticality_bands`; drive_run104 47/53 = 47/53 | run133 54/54, run67 21/21, milestones 77/78 = HEAD, run135a 60/60 | RESOLVED |
| F8 | 1 | removed `"commitments"` from the `commitments_due` alias tuple, citing the extraction contract | `{"Commitments": 100}` reaches nothing; all five stated headings still land | new suite 22/23 -> 23/23; run135d and run126 all passed, run132 31/31, run87 33/33 | RESOLVED |

No finding required a second attempt. No finding reached the ten-attempt cap. None is UNRESOLVED
AFTER 10, and none is BLOCKED.

---

## Confirmations

* **Starting commit** `cd98235a2ee493415cc8c4e8ba2f796bd490fd91` — origin/main at the branch
  point.
* **Branch** `worktree-agent-a349a1b543a4ae02f`. **Not pushed. Not merged to main.** Main's
  working tree was never touched, and the baseline fleet run executing against it was not
  disturbed.
* **Migration head** `0033_recognition_matches`, unchanged. No migration was written and none was
  required.
* `git status --porcelain` before each commit showed only the intended files: F1
  `server/app/simulation/models_fuzzy.py` + `server/app/simulation/models.py`; F2
  `server/app/training_engine.py`; F3 `server/app/training_debrief.py`; F4
  `server/tools/test_risk_register_and_notices.py`; F7
  `server/app/simulation/band_reference_data.json`; F8 `server/app/documents.py` plus the
  untracked `server/tools/test_run136a_remaining_h1_copies.py`. Every `git add` was by explicit
  path; no `git add -A` and no `git add .`.
* `__pycache__` under `app/` was cleared after every fault injection and before every restore
  confirmation.
* **No production recomputation was run.** `DATABASE_URL` pointed only at throwaway SQLite files
  in the scratchpad; production Postgres was never contacted. No model key exists in this
  environment and nothing called or simulated a model.
* `server/tests/`, `code_audit/` and `research/` were not touched. Within `server/tools/` only the
  one file F4 names was edited and the one new check file was added.
* Six commits, one per resolved finding, F1 first, in the order F1, F2, F3, F4, F7, F8. This
  report is the seventh and last.
