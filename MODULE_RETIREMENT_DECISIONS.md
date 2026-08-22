# Module Retirement Decisions

Created by Run 43 on 2026-08-21. No file of this name existed in the repository before this
run, so nothing was superseded and nothing was amended: this record is created fresh. Run 43's
prompt is the sole authority for the decisions recorded here.

**Status of the run that wrote this file: INCOMPLETE. The branch was NOT merged.** The
retirement itself is implemented and proven result-preserving, but stop condition 15.8 fired
during requalification. Section 9 of this record states exactly what fired and why. The
decisions below stand as decided; what does not stand is the successor freeze.

Implementing commits:

| Decision | Commit |
|---|---|
| Prose count correction, 100 -> 101 and Group A 52 -> 53 | `5282d72` |
| Retirement of 38 modules, registry 101 -> 63 | `b37f133` |
| This decision record and the run report | see the final commit on `claude/run43-module-retirement` |

---

## 1. The criterion

Reproduced verbatim from the authorising prompt, section 2.

> A module is retired only if one of four stated reasons applies. Each retired module carries
> exactly one reason. Where a module qualifies under more than one, assign the lowest-numbered
> reason and record that it also met the others.
>
> 1. Outside the unit of analysis. No participant ever sees it, so it cannot affect the outcome
>    measure.
> 2. Already disabled. The module is in one of the three disabled enum states and is dead on
>    every path.
> 3. Input structure has never existed. The module reads a governed structure that no supported
>    document type supplies and none is planned to supply.
> 4. Duplicate primitive source. The module reads the same primitive source object as another
>    retained module, established mechanically by the parsimony test.
>
> Explicitly rejected as a criterion: "it is not reporting on this project." That reasoning
> retires A2, then A3, and ends at TCPI and Variance at Completion with no taxonomy at all.
> Darkness on one project is not a retirement reason.

## 2. The parsimony test

Reproduced from the authorising prompt, section 3. Run by this repository at Run 35 and Run 36,
not devised in conversation.

**Method.** While modules execute on the governed corpus, the signal-input dictionary is
instrumented to record which primitive keys each module actually reads. Every module is then
compared pairwise against every other. Pairwise only: no connected component, no transitive
closure.

**Verdicts.** `NONE`, `SHARED_GOVERNED_STRUCTURE`, `IDENTICAL_PRIMITIVE_SOURCE_SET`,
`PRIMITIVE_SOURCE_SUBSET`.

**Run 36 over 100 scientific targets:** 75 NONE, 19 shared governed structure, 5 identical
primitive source set, 1 subset. Seventeen marked `distinct_analytical_function = NO`. Deleted
modules at Run 35: zero.

Run 43 re-derived all five of those figures from
`code_audit/run36_parsimony_reconciliation.csv` rather than accepting them, and they match
exactly: 100 targets, 75 / 19 / 5 / 1, and 17 marked NO.

**Artifacts.** `code_audit/run35_parsimony_reconciliation.csv`,
`code_audit/run36_parsimony_reconciliation.csv`.

**Stated limits.** It measures shared inputs, not shared conclusions: two modules with different
inputs could still produce the same decision. It says nothing about usefulness, only about
distinctness. It therefore supports reason 4 only. Reasons 1, 2 and 3 are separate judgements.

**The Run 35 against Run 36 discrepancy.** The two runs disagree. Run 35 found 22 non-distinct
with 3 identical primitive source sets; Run 36 found 17 non-distinct with 5. Run 36 is later and
is authoritative here. The discrepancy is recorded rather than resolved, because no run has
established which measurement is correct, and a retirement resting on the disputed five would be
resting on an unreconciled instrument. None of the seven reason-4 retirements depends on the
disputed band: every one of them is a `SHARED_GOVERNED_STRUCTURE` verdict with
`distinct_analytical_function = NO` in Run 36, and each was checked individually.

---

## 3. Every retired module, with its assigned reason

38 modules. Registered count falls from 101 to 63 (Group A 53 -> 44, B 36 -> 12, C 7 -> 7,
D 5 -> 0).

Each module carries exactly ONE reason, the lowest-numbered that applied. The "Also met" column
is derived mechanically, not asserted: reason 4 is taken from `distinct_analytical_function ==
NO` in the Run 36 CSV, reason 3 from membership of B2, reason 2 from the live `DISABLED_MODULES`
union, and reason 1 from membership of Group D.

### Reason 1 — outside the unit of analysis (5)

| Module | Name | Group | Also met | Parsimony (Run 36) |
|---|---|---|---|---|
| `D1.1` | Isolation Forest | D | — | SHARED_GOVERNED_STRUCTURE; shares with D1.2, D1.4, D1.5; distinct=YES |
| `D1.2` | Portfolio Outlier Detection | D | 4 | SHARED_GOVERNED_STRUCTURE; shares with D1.1, D1.4, D1.5; distinct=NO |
| `D1.3` | Signal Trajectory Classifier | D | — | NONE; shares with —; distinct=YES |
| `D1.4` | Cross-project Pattern Detector | D | 4 | SHARED_GOVERNED_STRUCTURE; shares with D1.1, D1.2, D1.5; distinct=NO |
| `D1.5` | Anomaly Score | D | 4 | SHARED_GOVERNED_STRUCTURE; shares with D1.1, D1.2, D1.4; distinct=NO |

### Reason 2 — already disabled (10)

| Module | Name | Group | Also met | Parsimony (Run 36) |
|---|---|---|---|---|
| `A1.1` | Monte Carlo EAC Forecast | A | — | NONE; shares with —; distinct=YES |
| `A3.4` | Material Cost Variance | A | — | ; shares with —; distinct=— |
| `A3.8` | Parametric Cost Index | A | — | NONE; shares with —; distinct=YES |
| `B2.7` | Plithogenic Sets | B | 3 | NONE; shares with —; distinct=YES |
| `B2.9` | Quantum Probability | B | 3, 4 | IDENTICAL_PRIMITIVE_SOURCE_SET; shares with A3.2, B1.1, B1.3, B1.4; distinct=NO |
| `B2.20` | Hypersoft Sets | B | 3 | NONE; shares with —; distinct=YES |
| `B4.1` | Multi-Objective Optimization | B | 4 | SHARED_GOVERNED_STRUCTURE; shares with B2.18, B2.19, B4.6; distinct=NO |
| `B4.2` | Linear Programming | B | — | NONE; shares with —; distinct=YES |
| `B4.5` | Decision Sensitivity Matrix | B | — | NONE; shares with —; distinct=YES |
| `B4.6` | Pareto Frontier Analysis | B | 4 | SHARED_GOVERNED_STRUCTURE; shares with B2.18, B2.19, B4.1; distinct=NO |

### Reason 3 — input structure has never existed (16)

| Module | Name | Group | Also met | Parsimony (Run 36) |
|---|---|---|---|---|
| `B2.1` | Dempster-Shafer | B | — | NONE; shares with —; distinct=YES |
| `B2.2` | Rough Sets | B | — | NONE; shares with —; distinct=YES |
| `B2.3` | Neutrosophic Logic | B | — | NONE; shares with —; distinct=YES |
| `B2.4` | Interval Fuzzy Sets | B | — | NONE; shares with —; distinct=YES |
| `B2.5` | Z-numbers | B | — | NONE; shares with —; distinct=YES |
| `B2.6` | PLTS | B | — | NONE; shares with —; distinct=YES |
| `B2.8` | Belief Rule Base | B | — | NONE; shares with —; distinct=YES |
| `B2.10` | Pythagorean Fuzzy Sets | B | — | NONE; shares with —; distinct=YES |
| `B2.11` | Picture Fuzzy Sets | B | — | NONE; shares with —; distinct=YES |
| `B2.12` | Hesitant Fuzzy Sets | B | — | NONE; shares with —; distinct=YES |
| `B2.13` | Type-2 Fuzzy Sets | B | — | NONE; shares with —; distinct=YES |
| `B2.14` | Maximum Entropy | B | — | NONE; shares with —; distinct=YES |
| `B2.15` | Possibility Theory | B | — | NONE; shares with —; distinct=YES |
| `B2.16` | Spherical Fuzzy Sets | B | — | NONE; shares with —; distinct=YES |
| `B2.17` | Fermatean Fuzzy Sets | B | — | NONE; shares with —; distinct=YES |
| `B2.19` | CRITIC-TOPSIS | B | 4 | SHARED_GOVERNED_STRUCTURE; shares with B2.18, B4.1, B4.6; distinct=NO |

### Reason 4 — duplicate primitive source (7)

| Module | Name | Group | Also met | Parsimony (Run 36) |
|---|---|---|---|---|
| `A2.4` | Schedule Compression Index | A | — | SHARED_GOVERNED_STRUCTURE; shares with A2.1, A2.10, A2.11, A2.5; distinct=NO |
| `A2.5` | Float Consumption Rate | A | — | SHARED_GOVERNED_STRUCTURE; shares with A2.1, A2.10, A2.11, A2.4; distinct=NO |
| `A2.6` | S-Curve Deviation | A | — | SHARED_GOVERNED_STRUCTURE; shares with A1.6; distinct=NO |
| `A2.10` | Schedule Risk Analysis P80 | A | — | SHARED_GOVERNED_STRUCTURE; shares with A2.1, A2.11, A2.4, A2.5; distinct=NO |
| `A2.11` | Critical Path Index | A | — | SHARED_GOVERNED_STRUCTURE; shares with A2.1, A2.10, A2.4, A2.5; distinct=NO |
| `A5.3` | Tornado Risk Ranking | A | — | SHARED_GOVERNED_STRUCTURE; shares with A5.2; distinct=NO |
| `B4.7` | Minimax Regret Decision Rule | B | — | SHARED_GOVERNED_STRUCTURE; shares with B4.4; distinct=NO |
### The one inconsistency in the authorising prompt, and how it was resolved

The prompt's section 10.2 says "`B2.19` retires under reason 4 in this run". Section 8's reason 3
covers every `B2` module except the three already disabled and except `B2.18`, which includes
`B2.19`. Under section 2's lowest-numbered rule, **`B2.19` takes reason 3, not reason 4.**

`B2.19` is recorded here under reason 3, with reason 4 recorded as also met. The Run 36 CSV
supports the additional reason: `B2.19` CRITIC-TOPSIS reads `decisionAlternatives`, shares that
object with `B2.18`, `B4.1` and `B4.6`, and is marked `distinct_analytical_function = NO`. The
resolved total is unaffected either way, because `B2.19` is retired under both readings. The
inconsistency is recorded so it is not re-argued.

---

## 4. The reasoning for each reason group

### Reason 1, outside the unit of analysis

`registry.py` already makes Group D a hard error on the single-project path, and `compute.py`
states Group D does not appear there at all, so retiring changes no computed result. The study's
row grain is participant by project by period; Group D is never exposed to a participant and
cannot influence the outcome measure. Run 36 independently flags `D1.2`, `D1.4` and `D1.5` as
sharing `D1.1`'s primitive source, so reason 4 covers three of the five on its own. Portfolio
Health empirical validation was an open item with no owner, and retiring closes it. The Group D
absence from the Signal Ledger, against twelve categories enumerated in the Executive Brief,
disappears with the group.

**Cost accepted:** the platform can no longer claim to operate above the project level. This is
scope, not absence. The instrument operates at the project-period level because that is the level
at which the judgment being studied is made.

### Reason 2, already disabled

The ten identifiers were READ from the live registry at `registry.py`, not assumed. They are the
union of three disjoint sets, and all three were verified to hold exactly the members a prior
read-only session had reported:

- `DISABLED_CONCEPT_ONLY` (8): `A3.8`, `B2.7`, `B2.9`, `B2.20`, `B4.1`, `B4.2`, `B4.5`, `B4.6`
- `DISABLED_EVIDENCE_UNDER_REVIEW` (1): `A3.4`
- `DISABLED_CANONICAL_INPUT_NOT_GOVERNED` (1): `A1.1`

`B4.1` and `B4.6` also meet reason 4 but take reason 2, being already disabled. `B2.9` also meets
reasons 3 and 4. `B2.7` and `B2.20` also meet reason 3.

**Note on the site render.** Sixteen rows show as Not relevant. That is the disabled ten plus six
construction-phase modules excluded by applicability rule on a design project. Those six are NOT
retired: they compute on a construction project.

### Reason 3, input structure has never existed

Every module in `B2` except those covered by reason 2 (`B2.7`, `B2.9`, `B2.20`) and except
`B2.18` MARCOS Ranking, which is held under section 6 below. Sixteen modules.

**The reasoning here was corrected during design and the correction matters.** B2 was initially
nominated on REDUNDANCY, on the grounds that twenty methods fuse the same signal package. Run 36
shows that is FALSE: each B2 module reads its own distinct governed structure —
`pythagoreanFuzzyAssessment`, `neutrosophicAssessment`, `zNumberAssessment`,
`evidenceMassFunctions` and so on. Run 43 re-derived this from the CSV: **18 of the 20 B2 modules
are marked `distinct_analytical_function = YES`.** Only `B2.9` and `B2.19` are marked NO.

The correct reason is 3: those input structures have never existed on any corpus and no supported
document type supplies them. That is true and checkable against the CSV. The redundancy argument
is not, and anyone who checked would defeat it.

### Reason 4, duplicate primitive source

Seven modules. **Every one was verified against `code_audit/run36_parsimony_reconciliation.csv`
BEFORE being retired**, as the prompt requires. All seven show `SHARED_GOVERNED_STRUCTURE (same
primitive source object)`, name exactly the partner the prompt names in
`closest_overlapping_targets`, and carry `distinct_analytical_function = NO`:

| Module | Shares the object of | Confirmed in CSV |
|---|---|---|
| `A2.4` Schedule Compression Index | `A2.1` activity network | yes |
| `A2.5` Float Consumption Rate | `A2.1` | yes |
| `A2.6` S-Curve Deviation | `A1.6` Earned Schedule | yes |
| `A2.10` Schedule Risk Analysis P80 | `A2.1` | yes |
| `A2.11` Critical Path Index | `A2.1` | yes |
| `A5.3` Tornado Risk Ranking | `A5.2` Sensitivity Analysis | yes |
| `B4.7` Minimax Regret Decision Rule | `B4.4` | yes |

The CSV supported every one, so stop condition 15.2 did not fire and no reason-4 retirement was
made without evidence.

### The C1 retention argument

Group C is retained entire, and the argument is recorded because the group has been questioned.

C1 is the only group describing the EVIDENCE rather than the project, and it is what licenses
abstention. The platform's strongest defensible claim is that it declines rather than fabricates,
and C1 is the vocabulary in which "we declined, and here is why" is expressible. It already does
not vote, with a stated reason at `compute.py`: early reporting periods carry the least evidence,
so folding it into status would make every early scenario read worse for reasons unrelated to the
project. Seven rows, none entering the stimulus.

Run 43 verified that Group C still does not contribute to project status after the retirement.

---

## 5. Explicitly retained

`A1` entire, `A2.1`, `A2.2`, `A2.3`, `A2.7`, `A2.8`, `A2.9`, `A3` entire, `A4` entire, `A5.1`,
`A5.2`, `A5.4` through `A5.8`, `A6` entire, `B1` entire (see section 6), `B2.18`, `B3` entire,
`B4.3`, `B4.4`, `C1` entire.

Modules retired from within those groups under reasons 2 and 4 are of course removed; "entire"
above describes the groups not nominated wholesale.

---

## 6. The Group B1 hold

**All four B1 modules are HELD, not retired. No B1 module was retired in this run.**

An earlier version of this decision retired `B1.2` Weighted Voting, `B1.3` Majority Rules and
`B1.4` Worst-N-of-M under reason 4, keeping `B1.1` Conservative Dominance.

**The evidence that stopped it:** `server/app/research_export.py:350` reads all four —
`"B1.1", "B1.2", "B1.3", "B1.4"`. That is the path producing `og-analysis-2026.08-v1`, the frozen
analysis dataset the R pipeline consumes. Retiring three would change an export schema that Runs
38, 39 and 41 qualified.

**Owner ruling: hold all four.** Nothing forces the retirement now — they are advisory and
non-voting. Keeping them costs three justifications; retiring them costs an export-schema
successor plus requalification of three prior runs. The parsimony finding is real but not urgent.

Run 43 verified after the retirement that all four remain named at `research_export.py:350`, all
four remain in the registry, and `run_module()` accepts all four.

**Retained for the future decision.** Had they been retired, the justification for keeping `B1.1`
specifically would have been: all four read the same primitive source set, so parsimony alone does
not select between them; `B1.1` is the only one consistent with the platform's own escalation rule
of worst-category-wins and worst-active-module-wins. Weighted Voting and Majority Rules can
average a Red away, and Worst-N-of-M requires an N and an M nobody has governed.

Run 36 detail supporting this: `B1.1`, `B1.3` and `B1.4` all carry
`IDENTICAL_PRIMITIVE_SOURCE_SET` with `distinct_analytical_function = NO`, while `B1.2` is marked
`NONE` and YES. Parsimony therefore does not even group all four the same way, which is a further
reason not to act on it hastily.

---

## 7. Open, unacted

Everything in this section is recorded as OPEN. Run 43 did not act on any of it and inferred no
cause for any of it.

### 7.1 The PRJ-001 render defects

These cannot be diagnosed from the repository, because `PRJ-001` exists in no repository file and
in no reachable database. Run 43 attempted none of them.

1. The Executive Brief reporting CPI 1.220 and SPI 1.270 where the authored corpus figures sit
   between 0.94 and 1.01.
2. `Document risk: 0.00 (Green)` printed as a key driver while the module reads No data.
3. A1 reading Amber while both its computing modules, TCPI and Variance at Completion, read Green.
4. The Amber attributed to TCPI, which is Green.
5. A blank reporting period with four periods loaded, and the longitudinal view locked.
6. 75 uploaded with 25 retained against 100 documents.

**A candidate mechanism for item 2 is recorded and is UNCONFIRMED.** `assets/js/detail.js`
around lines 1521-1524: `Number(null)` is `0`, which is finite, so a null score would render as
`"0.00"` with a Green status. This appears to contradict `server/app/extraction_merge.py:1128`,
which states a genuine zero must be stored. **Run 43 did not confirm this, did not test it, and
did not fix it.** It is a candidate only.

### 7.2 Group A5's remaining seven modules

Not decided. Each has a distinct decision consequence, so reason 4 does not apply. Reason 3
arguably does, since DSM matrices, queue models, agent models and discrete event models are
supplied by no document type. If retired later it must be on reason 3, and the sentence is that
the platform will never hold these structures, not that the modules are redundant.

### 7.3 B2.18 against B2.19

Not decided: which is the single retained method over `decisionAlternatives`. `B2.19` is retired
in this run (reason 3, also meeting reason 4); `B2.18` is held. Note from Run 35: the programme
deliberately supplies ONE alternatives-and-criteria object to several methods rather than parallel
copies, so the sharing is design, not accident. Run 43 confirms both read `decisionAlternatives`
and that `B2.18` is marked distinct YES while `B2.19` is marked NO, which is the only mechanical
discriminator available and is thin ground for a permanent choice.

### 7.4 A1, A3, A4, A6, B3, C1 for retirement

Not decided. No reason has been established for any of them.

### 7.5 The two owner decisions Run 42 raised

Not decided, and not touched:

1. `revision_resolution_status` hard-coded `NOT_ESTIMABLE`, pinning `overall_qualification_state`
   for every project permanently.
2. Ten declared extraction fields consumed by nothing.

### 7.6 Portfolio Health after the Group D retirement — NEW, raised by this run

Retiring `D1.1` through `D1.5` removes Group D from the registry and the taxonomy, but the live
Portfolio Health card does NOT compute through those module ids. It runs
`portfolio_health.compute_portfolio_health_snapshot` into `canonical_v8.compute_portfolio_health`,
which maps PH.1 to PH.5 onto D1.1 to D1.5 internally. `portfolio.compute_portfolio`, the v20
route that does key off `PORTFOLIO_VALIDATED`, is already documented in `portfolio_health.py` as
preserved and unreachable.

So after this run the platform has retired its portfolio-level MODULES while a portfolio-level
CARD continues to compute and display. Run 43 did not resolve this, because resolving it in
either direction touches a user-facing surface and section 5.4 of the authorising prompt forbids
deciding that inside a run. **No card, control or surface was added, moved or removed.** The
`D1` category container is retained in the client taxonomy with an empty module list.

This needs an owner decision. The two coherent options are to gate the portfolio health snapshot
on the registry so the card renders its existing insufficient-evidence state, or to keep the card
and state plainly that portfolio health is a capability outside the module taxonomy.

### 7.7 The export's proxy-qualifier mirror has drifted — NEW, incidental

`server/app/research_export.py` mirrors `registry.PROXY_QUALIFIERS` rather than importing it, by
deliberate design, so the export keeps no import dependency on the simulation package. That mirror
has drifted badly: **`registry.PROXY_QUALIFIERS` now holds 1 entry; the export's
`_RUN1_PROXY_QUALIFIERS` still holds 30.** Twenty-nine ids are in the export mirror and not in the
registry, `B4.4` among them — and Run 32 explicitly WITHDREW `B4.4`'s proxy qualifier.

The export is committee-facing evidence. On the current code it can print a proxy qualifier the
platform has formally withdrawn. Run 43 did not act on this. It is recorded because it is exactly
the stale-mirror class of defect this programme keeps finding, and because it was found while
checking the `B4.4` label, not by looking for it.

---

## 8. Superseded positions

**Do not delete anything in this section. The point of recording these is that they are not
re-argued.**

1. **B2 was wrongly nominated on redundancy.** The original argument was that twenty B2 methods
   fuse the same signal package and are therefore duplicates. Run 36 disproves it: 18 of the 20
   are marked `distinct_analytical_function = YES`, each reading its own governed structure. The
   correct reason is 3, input structure has never existed. Anyone who checked the CSV would have
   defeated the redundancy argument.

2. **A2 was wrongly ruled untouchable.** An earlier position held that A2 should not be touched at
   all. Run 36 shows five of its eleven modules are duplicate readers of one object, `A2.1`'s
   activity network. That position was taken before the CSV was read and was wrong.

3. **The B4.4 label premise was stale.** An earlier version of this decision instructed correcting
   a stale truthful-method label on `B4.4` What-If Scenario Matrix on the basis of a Run 35
   finding. That premise was already out of date when it was written:
   `server/app/simulation/method_labels.py:223` records that **Run 35's own closure already
   REMOVED** the `B1.2` and `B4.4` label entries, and `registry.py:266` records that Run 32
   repointed `B4.4` onto `models_cat10` and the canonical v7 layer. Run 43 read the live state and
   confirms it: **`B4.4` has no entry in `TRUTHFUL_METHOD_LABELS` or `STRUCTURAL_CLAIM_LIMITS`,
   and no proxy qualifier in `registry.PROXY_QUALIFIERS`.** Its label is the registry's own
   canonical name, "What-If Scenario Matrix". **Nothing was wrong, so nothing was corrected.**

4. **A prior derivation gave 41 rather than 38.** An earlier read-only session derived a
   retirement list of 41, including three B1 modules (`B1.2`, `B1.3`, `B1.4`) under reason 4. That
   derivation is superseded. Section 6 above records why B1 is held: `research_export.py:350`
   reads all four, and retiring three would change a frozen export schema that three prior runs
   qualified. The correct total is 38, and Run 43 derived it independently from the live registry
   before making any change.

5. **The taxonomy prose said 100 and Group A 52.** Both the live registry and
   `assets/js/taxonomy.js` derived 101 and 53 and agreed with each other; only prose disagreed.
   Corrected in commit `5282d72`, before the retirement, so that history shows the count being
   corrected and then being changed by the retirement rather than the two being conflated. This is
   the ninth time this programme has been wrong about a stated set and caught it only by deriving
   mechanically. Every population in this run was derived from the live registry for that reason.

---

## 9. Why the run that wrote this record did not complete

**Stop condition 15.8 fired: the successor freeze cannot be taken without weakening the guard.**

The retirement is implemented and is proven result-preserving. What could not be done is
requalification, and therefore the successor freeze `sim-2026.08-v28` was NOT minted. The live
stamp remains `sim-2026.08-v27`.

The measurement, taken with the repository's own runner and not estimated:

| | Suites | Checks | Verdict |
|---|---|---|---|
| Baseline at `f461630`, re-run by Run 43 in a clean worktree | 188 | 14176/14176 | ALL GREEN |
| After the retirement | 188 | 9671/9817 | 73 SUITES FAILING |

The baseline figure was NOT taken on trust; it was reproduced, and it matches the recorded
188 / 14176 exactly. So every failure is attributable to this run.

The cause is single and uniform. **56 of the crashes are `MissingModuleError`**: the per-module
scientific audit, known-answer and fault-campaign suites enumerate the module population and call
`run_module()` on each id. The authorising prompt's own guarantee 13.4 requires that a retired
module be unreachable through `run_module()`, and it is. The suites that exercise the retired
modules' arithmetic therefore crash by design.

Making those suites green would mean removing or skipping roughly **4,359 checks** across 73
suites. Section 6.1 of the authorising prompt says "Do not disable, weaken, or bypass the guard.
Add to the authorised set; never remove or widen a check." Deleting four thousand checks is
removing checks. The alternative — leaving `run_module()` able to compute retired modules so the
audit suites keep passing — would violate guarantee 13.4, which is equally an owner-mandated
check.

Both available routes weaken something the owner mandated. That is precisely stop condition 15.8,
so the run stopped, the freeze was not taken, and the branch was left unmerged.

**This is an owner decision, not a decision for a run.** The two coherent options are recorded in
the run report. Neither can be chosen inside a run, because both change what the instrument's
qualification evidence consists of.

---

# Run 43B addendum, 2026-08-21

Run 43B was authorised to complete the retirement: repoint the failing suites onto the live
registry, remove the artifacts keyed to retired identifiers, offload Portfolio Health, reconcile
the check count, mint `sim-2026.08-v28` and merge. **It stopped at the same wall as Run 43, one
step further along, and the wall is now measured rather than predicted.** Stop conditions 7.1 and
7.8 fired. The branch `claude/run43B-retirement-completion` is unmerged and no successor was
minted. Full detail in `REPORT_2026-08-21_run43B_retirement_completion.md`.

**Three corrections to what this record said above.**

1. **The failing-suite count is 72, not 73.** The runner's own arithmetic: 116 `ok` plus 72
   `FAIL` is 188, and the `FAILED SUITES` block holds 72 entries with no duplicates. The check
   figures, 9671/9817, are confirmed exactly.

2. **"The cause is single and uniform" is not correct.** It is at least five distinct causes, and
   the difference decides whether the work is possible. 32 suites crash with `MissingModuleError`
   and 6 with `KeyError`; the remaining 34 run to completion and fail on checks. Among those,
   separate mechanisms: hard-coded expected counts inside check bodies (`96`, `101`, `five`);
   pinned byte-identity freeze manifests that Run 43's own edits falsified; the literal string
   `RETIRED` leaking out of the renumbering CSV into derived populations; and `A1.1` surviving in
   the browser taxonomy.

3. **"The suites enumerate the module population" is not correct of most of them.** Measured over
   the 72 source files: 53 carry a quoted retired identifier in the source, 845 occurrences in
   all. In those, the identifier is the subject of a hand-written per-module block or a
   hand-computed expected value — it sits *inside the check body*, where there is no enumeration
   source to repoint. Run 43B's authorising prompt forbids changing a check body, which is why
   7.1 fired.

**The irreducible case, and it is not a test file.**
`server/app/simulation/models_sim.py:254`, the production guard
`assert_retained_adaptation_not_reachable`, proves A1.1's retained Monte Carlo adaptation cannot
be entered — by *executing* A1.1 and asserting the abstention that comes back. Its own comment
records that a non-executing version of it once passed while the adaptation was live, and states
the rule: *a guard that is satisfied by somebody else's refusal is proving nothing about its own
subject.* After the retirement `run_module` refuses A1.1 first, so the guard raises. Removing the
retired identifiers from the registry constants — which is what the artifact-removal step
authorises — was simulated in-process and makes the guard fail twice instead of once. There is no
third route. The guard's body must change, or the guard must go.

**What Run 43B did complete**, because each was independently ordered and none depends on the
blocked repointing:

- `research_export._RUN1_PROXY_QUALIFIERS` reconciled from 30 stale entries to the live
  registry's 1, and `registry.py`'s "thirty proxy modules" prose corrected.
- The `canonical_v8` PH.1 to PH.5 Portfolio Health path offloaded, derived from the registry
  rather than declared, with the intake path offloaded too. This is the retirement of `D1.1` to
  `D1.5` actually taking effect: Run 43 retired the identifiers, but the computation continued
  under the PH names.
- The complete enumeration of artifacts keyed to a retired identifier, committed as
  `code_audit/run43B_retired_identifier_artifact_enumeration.csv`: **458 files, 8,340
  occurrences, and 169 files carrying at least one line that names a retired module and a module
  in service together.** Nothing was removed.

**The offload cost four previously-green suites** — `test_run33_portfolio_health`,
`test_run34_holdout_provenance`, `test_run34_provenance_fault_campaign` and `test_period_series`
— all four with a wholly retired subject, all four exactly what the artifact-removal step would
have removed had it been reachable. This is the visible consequence of separating the offload
from the removal, and it is recorded rather than absorbed.

**The decision remains the owner's, and it is now sharper.** Run 43 framed it as a choice between
deleting checks and violating guarantee 13.4. Run 43B's measurement narrows it: the retirement
of 38 modules necessarily falsifies every check whose subject is one of them and every manifest
pinning a file the retirement edited, and those checks have no enumeration source to repoint. The
three coherent options are stated in section 12 of the Run 43B report. All three change what the
instrument's qualification evidence consists of, which is why none may be chosen inside a run.

---

## Addendum — Run 43D, 2026-08-21: retirement becomes removal FROM SERVICE

The owner's Run 43D section 5.1 replaced removal-from-existence with **removal from service**, and
this addendum records what that changed, what it fixed, and where it stopped. Full account:
`REPORT_2026-08-21_run43D_retirement_from_service.md`. Branch
`claude/run43B-retirement-completion`, head `776f130`. **UNMERGED.**

**The reason each of the 38 carries is unchanged and was not rewritten.** It stays exactly where
Run 43 wrote it, in the `notes` column of `p0-baseline/module_renumbering_map.csv`, which is now
the sole authority for both populations and the only place the retirement is recorded.

**What changed.** Run 43's `b37f133` wrote the literal `RETIRED` into the `new_id` column, which
destroyed the identifier. That is superseded. Every one of the 38 `new_id` values is restored —
verified column-for-column against `f461630`, identical outside `notes`, row order included — and
the RETIRED marking now lives only in the notes. `registry.py` gains `retired_modules()`,
`modules_in_service()` and `service_index()`, all derived from the CSV with no list written
anywhere. `run_module()` resolves a retired identifier and **refuses** it with its stated reason
instead of raising `MissingModuleError`.

**What that fixed, measured.** The registry resolves all 101 while serving 63. The `RETIRED`
literal no longer leaks into any derived population — the leak's cure was the restoration itself.
**2,924 checks that could not run under `b37f133` now run** (9,615 to 12,539 executed). Zero
modules in service changed their computed result, byte-compared across three fixed cases against a
`git worktree` at `f461630`: 186 common results, 0 differences.

**Where it stopped.** Stop conditions **7.1** and **7.4**. Section 5.1 asserts that no check body
need change because the existing checks "now assert the refusal". They do now run, but they assert
**which** refusal, by name, in the body — `DISABLED_UNSAFE` for the ten retired under reason 2,
`canonical_structure_absent` and the named structure awaited for the sixteen under reason 3, and
hand-computed figures for the seven under reason 4. A retirement refusal cannot satisfy an
assertion written about a different refusal. Measured: **62 red suites, 181 failing checks naming a
retired module across 26 suites, and 14 suites that abort on a body-level index into a results dict
that no longer carries the key.** None of the four suites the Portfolio Health offload turned red
returns green, which is 7.4 in terms.

**The owner's choice is unchanged in shape and narrowed in content**, and it is stated with its
measured cost in section 12 of the Run 43D report. The mechanism built by 43D should not be
reverted whatever is chosen: it is correct, and every option is cheaper on top of it than under
`b37f133`.


---

## Addendum, Run 43F (2026-08-21) — retirement is delinking, and nothing else

**The `run_module()` retirement refusal introduced by Run 43D is withdrawn and removed.** Section
5.1 of the Run 43F order rules that a retired identifier returns exactly what it returned at
`f461630`: the same result, or the same refusal, with the same reason, in the same words.
`DISABLED_UNSAFE` stays `DISABLED_UNSAFE`; `canonical_structure_absent` stays
`canonical_structure_absent`. **Retirement does not change why a module does or does not produce a
value.** It is expressed by roster membership and category linkage, and nowhere else.

Measured, not asserted: `run_module()` over all 101 identifiers under two input fixtures is
byte-identical to a worktree at `f461630`, 0 diff lines, proved failable at 1,530.

**The roster mechanism built by Run 43D stands unchanged** — the 38 identifiers in
`p0-baseline/module_renumbering_map.csv`, `retired_modules()`, `modules_in_service()`,
`service_index()`, and the populations derived from them. Registry 101, in service 63, both derived.

**Where it stopped.** Stop conditions **7.1** and **7.6**. The refusal-collision class Run 43D
measured is gone entirely. What remains is a different and irreducible class: 114 checks across 34
suites, and 8 suites that abort, assert that a retired module is present in an enumerated
population — the ledger, the abstention list, the browser taxonomy, a results dict. Requirement 2
of the same section says it must not be. All four Portfolio Health suites are class 1 at section
5.4: they assert the pre-offload state, and the offload is correct and derived.

**The owner's choice is the same three options Run 43D stated, now with the refusal class removed
from their cost.** Nothing in this addendum revises a retirement decision above; all 38 stand.

---

## Addendum — Run 43H, 2026-08-21. The retirement is complete and merged.

The owner's Run 43H order gave the **class sanction** the three previous phases stopped for: any
check asserting the pre-retirement population is updated to assert the post-retirement population,
as one sanction covering the whole class. Option (A) of the three Run 43D stated.

**Nothing in this addendum revises a retirement decision. All 38 stand, and all 38 keep their
registry entry, their formula function and their audit lineage.** `run_module()` on every one of
the 101 registered identifiers returns output byte-identical to `sim-2026.08-v27`, measured against
a worktree at that commit and proved failable at 1,530 diff lines.

**What closed.** The 114 red checks across 33 suites and the 8 aborting suites are all green:
188 suites, **14,197 / 14,197**, 0 red, 0 aborting. The successor freeze gate is **31/31** with 0
of 15 blocker classes blocked. `sim-2026.08-v28` is stamped and `og-participant-2026.08-v14` is
minted; the v27 and v13 records are pinned to their own commits, not rewritten.

**Two measured facts the order's own figures did not have.**
- **`B2` falls from 20 in the registry to 1 in service, not 4.** Only `B2.18` (MARCOS Ranking)
  remains. `A2` 11 → 6, `B4` 7 → 2 and Group D 5 → 0 are as the order stated.
- **Every one of the ten modules in `DISABLED_MODULES` is also retired.** `DISABLED_MODULES ∩
  service_index()` is empty, so the client taxonomy now flags **zero** entries disabled, where it
  flagged ten.

**One correction was refused and is a decision for the owner.** The Portfolio Health flyout at
`assets/js/deepdive.js:2373` tells a participant that Portfolio Health "needs at least 3 projects";
after the offload no number of projects would make it compute. The correction was written and
verified, then reverted: `deepdive.js` is one of the six `SEQUENCE_BEARING_FILES`, and every
participant-package record since v10 and the freeze gate's B04 blocker assert those six are
byte-identical across a successor. Correcting a sentence is not a reason to move the participant
sequence without the owner saying so.

---

## Addendum — Run 44, 2026-08-22. Two consequences of the retirement, corrected on the surfaces.

**Nothing in this addendum revises a retirement decision. All 38 stand, all 38 keep their registry
entry, their formula function and their audit lineage, and `run_module()` on every one of the 101
registered identifiers returns output byte-identical to `sim-2026.08-v28`** — measured by executing
the v28 line and the v29 line side by side on a full and a starved evidence package, and proved
failable by perturbing one module's own input and observing that module, and only that module,
diverge.

**The two decisions Run 43H left open for the owner are both closed, by the owner's order of
2026-08-22.**

1. **The Portfolio Health flyout's reason sentence.** After the Group D offload no number of
   projects makes the panel compute, yet it told a participant it needed at least three. The owner
   ordered it corrected, accepting a participant-package successor that moves ONE sequence-bearing
   file. `og-participant-2026.08-v15` is that successor, and it is the first record since v10 that
   cannot say the six sequence-bearing files are byte-identical. It says so instead, and the
   exception is declared by name in `participant_packages.V14_TO_V15_SEQUENCE_EXCEPTION` so a
   second file moving is still a failure. The correction is the `cat8Retired()` predicate Run 43H
   wrote and reverted, DERIVED from the taxonomy the page loaded: reinstating a Portfolio Level
   module restores the old sentence with no edit to that file.
2. **`available_modules()`'s stale docstring.** It described the retirement-reason refusal Phase F
   withdrew. Corrected under this stamp. The function body is untouched.

**One further retirement consequence was found and reported rather than acted on.** Group D is
retired from service, so `signals.js:535` `portfolioVector` — which defaults an absent document
risk to zero, the same class of defect Run 44 repaired elsewhere — now feeds nothing at all. It is
left in place and recorded in the Run 44 report's incidental findings.
