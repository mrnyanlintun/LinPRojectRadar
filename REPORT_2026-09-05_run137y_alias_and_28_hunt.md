# Run 137, agent Y — the `packages_due` alias, and the hunt on the 28

**`SIMULATION_VERSION` DID NOT MOVE. It stands at `sim-2026.09-v70`.** Nothing under
`server/app/simulation/` was edited. Item 3 classified no failure as a stale expectation whose
smallest correct fix lay in the analytical layer, so the layer was not touched, exactly as the
order anticipated.

Branch `worktree-agent-ac215df037be5c0cc`. Starting sha `2cb024e`. Ending sha recorded at the
foot of this report. Not pushed, not merged. Migration head unchanged at
`0033_recognition_matches`; no migration was written and none was required. `DATABASE_URL`
pointed at a throwaway SQLite file under `…/scratchpad/run137/Y/y.db`, migrated to head;
production Postgres was never contacted.

**The v70 recomputation.** Nothing in this run adds to what it must cover. Item 4 changes what is
extracted from a document going forward; it recomputes nothing and moves no boundary.

## The measurement caution, and a correction to it for these three suites

The standing caution is that 30 tool scripts hardcode `/home/user/LinPRojectRadar/server` on
`sys.path`, so a figure taken in a worktree is not a figure about that worktree. **All three
suites in my scope are `__file__`-relative and therefore DID test this branch:**

| suite | `sys.path` line | tests |
| --- | --- | --- |
| `tools/test_run17_scientific_methods.py:28` | `sys.path.insert(0, str(HERE.parent))` | this worktree |
| `tools/test_run36_fault_guards.py:26,47` | `ROOT = Path(__file__).resolve().parents[2]` | this worktree |
| `tools/test_run41_preservation.py:41,43` | `ROOT = Path(__file__).resolve().parents[2]` | this worktree |
| `tools/test_run136a_remaining_h1_copies.py:25` | `Path(__file__).resolve().parents[1]` | this worktree |

The Item 4 proof was taken separately with `sys.path.insert(0, '.')` and cwd = this worktree's
`server/`, as the order required. **Every suite figure below is nonetheless marked "worktree —
re-take on main", because the merged tree is the only place a figure is final.**

---

# Item 4 — `packages_due` no longer accepts the bare alias `"packages"`. RESOLVED, attempt 1.

Commit `3bd0069`. File `server/app/documents.py`, the `_TD_COLS` block, one tuple and the note
above it.

## What F8's disposition was

Run 136 A, §F8, `REPORT_2026-09-04_run136a_remaining_findings.md`:

> **F8 — `commitments_due` carries a bare superset alias. RESOLVED, attempt 1.**
> … `commitments_due` is *"firm COMMITMENTS DUE in the reporting period"*
> (`extraction_fields.py`) … A column headed only "Commitments" states no period and no status,
> so it may be every commitment the firm holds. A6.4 already carries the honest alternative: with
> no denominator the factor reads UNAVAILABLE and is *"not treated as Green"*
> (`contractor_factors.py:624-630`).
> … **The established position is to abstain on an adjacent quantity, whichever way the error
> falls. Applied.**

On the direction of the error, F8 cites four places carrying the platform's position —
`extraction_client.py:696-698`, `models_ext.py:858-862`, `schedule_table.py:126`,
`lineage.py:241` — and concludes *"None of those is conditioned on the direction of the error."*
The H5 commit (`aee0485`) had reasoned about the favourable direction *"because that was the case
in front of it"*, closing with *"as does every denominator"* — which **left** denominators rather
than ruling on them. F8 removed the alias from the denominator anyway, and left the numerator
(`commitments_met_on_time`, 90.0 in its worked case) untouched.

## This one's disposition, and the match

Identical in every respect.

* **Same shape.** `packages_due` is *"firm work packages or milestones DUE in the reporting
  period"* (`extraction_fields.py:1009`), the A6.4 schedule-reliability **denominator**. A column
  headed only "Packages" states no period and no status, so it may be every package in the scope
  of work — a superset.
* **Same direction problem, same answer.** A larger denominator lowers the on-time percentage and
  bands the firm **worse**. F8 removed a bare alias that failed unfavourably because the recorded
  position carries no direction; this one is removed on that same reasoning, cited in the note
  beside it.
* **Same honest alternative.** With no denominator A6.4 reads UNAVAILABLE and is not treated as
  Green.
* **Same scope discipline.** Only the bare heading goes. Every heading that states the population
  still lands: `packages_due`, `work_packages_due`, `milestones_due`, `activities_due`,
  `workfronts_due`, `planned_packages`. The numerator `packages_completed_on_time` is untouched.
* **Same treatment of the note.** F8's reasoning was written into `documents.py` beside the tuple;
  so is this one, and it cites F8 by name as the precedent.

**Before → after.** `_first_of({"Packages": 100}, <packages_due aliases>)` returned `100` before
and returns `None` after.

**Proof it can fail.** The alias was restored by `sed`, `__pycache__` cleared under `app/`, the
proof re-run: `RESULT: FAIL (accepts bare 'Packages')`. Removed again, cache cleared, re-run:
`RESULT: PASS (abstains on bare 'Packages')`.

**Suite.** `test_run136a_remaining_h1_copies` **23/23** — the durable cover Run 136 built for H5,
F8 and the rest — *worktree, re-take on main.*

**Found in passing, not fixed** (bundling is forbidden by the loop's rule 2): the alias list
documented at `app/extraction_fields.py:1036-1037` still lists `packages` as a recognised heading
for `packages_due`. This is the same documentation drift Run 136 recorded for `inspections_passed`
and `commitments_met`; the list is a comment and the code is `_TD_COLS`, but the comment is now
wrong in three places and should be corrected in one edit by a later run.

---

# Item 3 — the hunt on the 28. All 28 disposed.

Established by running the three suites against the migrated throwaway SQLite:

| suite | before | after | worktree / re-take on main |
| --- | --- | --- | --- |
| `test_run17_scientific_methods` | 214/231, **17 failures** | **222/222** | yes |
| `test_run36_fault_guards` | 34/41, **7 failures** | **42/43** | yes |
| `test_run41_preservation` | 29/33, **4 failures** | **32/33** | yes |

The two remaining failures are the two real defects, left standing deliberately. `test_run17`'s
total falls from 231 to 222 because nine checks about modules Run 96 removed are now correctly
replaced by the substitution's one-for-one removal assertions, which is what that mechanism was
written to do; two live canonical-engine checks were moved rather than lost.

## Classification summary

| classification | count |
| --- | --- |
| Stale expectation — re-pointed under R2 | 16 |
| Vacuous check — repaired (10) or retired (1) | 11 |
| Real defect — reported, not fixed | 1 |
| Unclear | 0 |
| **total** | **28** |

A second real defect was **exposed** by re-pointing #28 and is reported alongside the first. It is
not one of the 28; it is what one of the 28 turned into once its derivation was correct.

## The module-number mapping, established before anything was read

`p0-baseline/module_renumbering_map.csv` (Run 43) gives `1.6 -> A1.5`, `1.9 -> A1.8`,
`6.2 -> B1.2`; rows whose numeric part did not change are not listed, so `6.3 -> B1.3` and
`6.4 -> B1.4` by the group rule. **The section labels in `test_run17` are Run-17 display labels;
the identifiers the sections actually dispatch are the NEW ones** — section `[1.5]` runs `A1.5`,
`[6.3]` runs `B1.3`. No failure below is about a different module from the one its label suggests.
That mapping is also the whole of finding Y-1: the suite's suppression logic paired label to
identifier by stripping the group letter, which Run 43 silently broke for the Category-6 sections.

---

## `test_run17_scientific_methods` — 17

### Y-1 to Y-10 · VACUOUS · one cause, ten checks · commit `7987daf`

The ten: `[6.3]` x4, `[6.4]` x4, `[ARCH]` duplicate lineage, `[FAULT]` Category-9 raw bypass.

1. **What each asserts.** That `B1.3` Majority Rules and `B1.4` Worst-N-of-M refuse an absent or
   unknown status, hold quorum, do not dilute under benign evidence, assert no band; that a second
   transform of the same adverse evidence does not raise the adverse count; and that the
   Category-9 raw-bypass fault is decidable.
2. **What the code does, and since when.** `B1.3` and `B1.4` have not existed since **Run 96**,
   which struck 51 retired rows from the registry. The suite's own substitution asserts their
   removal, and those assertions pass.
3. **Did a later run deliberately change it?** Yes — Run 96's removal, and before it Run 43's
   renumbering. The suite was built to handle exactly this: `run()` substitutes an
   `_AbsentReading` and `_suppressed_for` silences the propositions that follow.
   **`_suppressed_for` matched a section label to an identifier by stripping the group letter —
   `"1.3"` against `"A1.3"` — which Run 43 broke: `"B1.3".lstrip("ABCD")` is `"1.3"`, never the
   section label `"6.3"`.** So the substitution fired and suppressed nothing.
4. **Classification: VACUOUS.** These checks read the `_Absent` sentinel, whose `__eq__` is
   `False` and which is never `None`. They failed whatever production did and could not have
   passed. They were not adverse findings; they could not distinguish a correct instrument from a
   broken one.

**Repair, not suppression.** (a) `SECTION_TO_MODULE` records the pairing from the renumbering map
and `_suppressed_for` reads it instead of guessing from digits. (b) The two live canonical-engine
checks in those sections — `canonical_v5.majority_rules` collapsing duplicate lineage, and
`worst_two_of_m` being a mean and not a maximum — are taken **before** the first removed-module
dispatch, so correct suppression does not silently drop them. (c) The ARCH raw-bypass probe and
fault injection 9 move their carrier from `B1.3` to `B1.1`, by **Run 30's own test**: the carrier
must be a Category-6 ensemble that still computes from unqualified evidence; `B1.2` abstains at
dispatch, which is the disqualification Run 30 itself recorded, and `B1.1` computes. (d) The ARCH
dispatch-level duplicate-lineage check is **retired**, because the property needs a *counting*
ensemble and none is left in the registry — `B1.1` is a dominance rule with no counts. The
property itself is still asserted on the canonical engine in section 6.3.

**Proof it can fail.** Reverting the `SECTION_TO_MODULE` clause returns the suite to 215/230 with
the eight 6.3/6.4 failures; restored, 214/221.

### Y-11, Y-12, Y-13 · STALE · source Run 107 · commit `1fa9c19`

`[1.5]` A1.5 ARIMA CPI Forecast, `[1.6]` A1.6 Earned Schedule, `[1.9]` A1.9 Budget Execution.

1. **Assert:** each carries **no** status band and reports `calibration_pending`.
2. **Code today:** all three band. A1.5 returned `Red`, `band_provenance_class`
   `OWNER-CALIBRATED`, `threshold_source` `owner_configured_default`, with the ladder published
   verbatim in `band_boundary`; A1.6 and A1.9 likewise.
3. **Deliberate?** Yes. `SIMULATION_VERSION_HISTORY`, `sim-2026.09-v53`: *"RUN 107: the eight
   thresholds. A1.5, A1.6, A1.9, A1.11, A4.5, A4.7, A4.8 and A4.9 band for the first time on the
   owner's supplied ladders, each on the most adverse component posture."* Run 133's alignment
   audit reached the same conclusion from the other side: A1.5 and A1.9 carry a *"none may be
   attached"* prohibition in a **stale specification** while banding in code under the owner's Run
   107 order, and `specifications/` is derived from code and disclaims authority — the code
   governs. **These three are Run 133's disagreement arriving through the other door.**
4. **Classification: STALE.** Re-pointed under R2, source recorded beside each: a band from the
   four-band vocabulary, no pending calibration, `OWNER-CALIBRATED` provenance and a stated
   threshold source — so an unsourced ladder still cannot pass as a calibrated one.

### Y-14 · STALE · source Run 106 · commit `622a77a`

`[6.2]` "the second pass weighs the postures and declares the owner's authority".

1. **Asserts:** `weighted_voting_result` over four Green categories and one Red returns `Green`.
2. **Code today:** returns `Yellow`, `weighted_sum` `1.36`.
3. **Deliberate?** Yes, and documented in the function itself:
   `models_gov.weighted_voting_result` — *"RUN 106. `status_color` IS THE PROJECT RULE'S OWN
   BAND. Before this run it was the band class holding a plurality of the weight, which is a
   different quantity; see the header above for the measured case where the two disagree."* Stamp
   `sim-2026.09-v52`, *"RUN 106: the weights set the status."* The old expectation was the
   plurality: Green holds 0.84 of the profile against Red's 0.16.
4. **Classification: STALE.** Re-pointed, and the expectation is **computed from the owner's rule,
   not read off the module** (R2): his profile is A1 0.28, A2 0.28, A3 0.17, A4 0.11, A6 0.16 and
   his scores Green +2 … Red -2, so 2(0.28+0.28+0.17+0.11) - 2(0.16) = 1.68 - 0.32 = **+1.36**,
   and his cuts (>= 1.5 Green, >= 0.5 Yellow) make that **Yellow**. The weighted sum is asserted
   beside the band, so a right answer for a wrong reason still fails. This is the very case Run
   106 recorded as the one where the two quantities disagree.

### Y-15 · STALE · source Run 103 · commit `622a77a`

`[GATE]` "the only registry/specification mapping problems are modules Run 96 removed", failing on
`['A2.12 -> 2.12: no owner-specification module at that key']`.

1. **Asserts:** the only tolerated registry/specification mapping problem is a module the
   specification names that Run 96 removed.
2. **Code today:** `A2.12` Critical Path Analysis is registered and the Run-17 supervisory
   specification has no module at key `2.12`.
3. **Deliberate?** Yes — **Run 103** registered A2.12, after the audit. Its report settles the
   shape: *"the Run 17/26 audit population is **sealed historical evidence** and cannot name a
   module registered after it; a post-audit roster naming A2.12 and its run replaces the 'nothing
   is outside the population' assertion, and an unrostered new module still fails"* — and
   re-pointed `test_run26_counts_and_wiring` that way.
4. **Classification: STALE.** Re-pointed identically and **narrowly**: a named roster of one. Any
   other unnamed row, and any name mismatch, still fails; a new check requires every roster entry
   to be genuinely in the registry, so the roster cannot excuse a module that is simply gone.

### Y-16 · VACUOUS · repaired · commit `622a77a`

`[GATE]` "and coercing an identifier to a number would not round-trip back to it", failing on `[]`.

1. **Asserts:** at least one identifier **in the population** loses information under float
   coercion — the stated reason identifiers are carried as text.
2. **Code today:** none does. `_would_lose` is empty.
3. **Deliberate?** Yes, and the check three lines below asserts it: **Run 96 removed every
   colliding member** (`1.1` against `1.10`), so the collision no longer arises.
4. **Classification: VACUOUS.** It is a statement about which rows survived a removal, not about
   whether the instrument carries identifiers faithfully; it failed while nothing was wrong and
   could not have distinguished right from wrong either way. **Repaired, not deleted**: it now
   asserts the trap itself — `"1.10"` does not round-trip and `"1.1"` does — which is true
   whatever the registry holds, and which is what keeps the *live* property above it ("every
   identifier is text") non-vacuous. The census figure is kept in the detail line.

### Y-17 · STALE · source Run 97 · commit `622a77a`

`[GATE]` "every register entry was actually exercised this run — exercised `['ARCH/raw-bypass']`".

1. **Asserts:** every entry in the anti-fossilisation register was exercised, so neither a new
   defect nor a repaired one passes silently.
2. **Code today:** two of the three entries cannot be reached.
   `PH.5/availability-reweighting` and `PH.1/degenerate-cohort-resolution` are findings about
   `simulation/portfolio.py` and `simulation/portfolio_health.py`.
3. **Deliberate?** Yes. **Run 97 goal one, commit `88e6ca0`**, deleted both files, struck the five
   D1 rows from the registry and the taxonomy authority, and removed the Group D branch from
   `run_module`. The suite's own `portfolio_health()` docstring records this.
4. **Classification: STALE.** The gate was asking a register to be exercised against code that no
   longer exists. The two entries are retired **with the reason recorded beside them**. Nothing is
   forgiven: what replaced those propositions is stronger and is already asserted — the modules
   are gone, the identifiers do not resolve, the dispatcher refuses each by name, and it goes red
   the moment a future run writes any of it back. The findings themselves survive in the Run 17
   register and in `code_audit/`, which is where evidence about a removed implementation belongs.

**Proof Y-14 through Y-17 can fail.** Restoring the `Green` expectation, emptying the roster,
asserting that `"1.10"` round-trips, and putting `PH.5` back into the register returns exactly
those four failures (218/222). Restored: 222/222.

---

## `test_run36_fault_guards` — 7

Six are one shared cause and are in commit `bd713be`; the seventh is a real defect and was not
touched.

### Y-18 · STALE · source Run 103

`fault01.inventory_complete`, missing `['A2.12']`.

1. **Asserts:** the sealed 100-target inventory
   (`code_audit/run36_100_target_scientific_reaudit.csv`) holds every scientific target the
   registry carries.
2. **Code today:** the registry carries `A2.12`; the inventory does not.
3. **Deliberate?** Yes — Run 103, exactly as Y-15. The CSV is Run 36's evidence and is not
   rewritten.
4. **Classification: STALE.** A named post-audit roster of one, plus a new `fault01b` requiring
   every roster entry to be genuinely registered. Both directions stay closed.

### Y-19 · STALE · source Runs 96 and 97

`fault03.no_fake_target`, listing 40-odd inventory rows absent from the registry.

1. **Asserts:** every inventory row is a registered module.
2. **Code today:** the inventory names the 51 rows Run 96 removed and the 20 Run 97 removed with
   the B2, B3, B4 and D1 categories.
3. **Deliberate?** Yes; `tools/run96_removed.py` is the roster of both removals and is the
   authority.
4. **Classification: STALE.** The roster is now **read** from `run96_removed.REMOVED` rather than
   typed, and a new `fault03b` requires that not one removed module has come back into the
   registry.

### Y-20 · **REAL DEFECT — reported, not fixed**

`fault05.no_unsupported_authoritative`, offender `['A6.2']`. See D1 below.

### Y-21, Y-22, Y-23, Y-24 · STALE · source Run 96

`fault13` A3.4 Material Cost Variance, `fault14` B2.7 Plithogenic Sets, `fault15` B2.20 Hypersoft
Sets, `fault16` B2.9 Quantum Probability.

1. **Assert:** each is disabled, **still registered**, and produces no operational reading.
2. **Code today:** each is on `REG.DISABLED_MODULES` and on `REMOVED_AT_RUN96`, is **absent from
   the registry**, and the dispatcher raises `MissingModuleError` for it. The failure detail
   proves what did *not* go wrong: `disabled=True … colour=None`. The clause that failed was
   `_mid in IDX`.
3. **Deliberate?** Yes — Run 96 struck the retired rows out of the registry rather than leaving
   them held down inside it.
4. **Classification: STALE.** These four failed on the removal, not on a reactivation; the
   operational reading they guard against was never observed. Each now asserts the state the
   module is actually in, which is the stronger one: on the disabled roster, on the Run 96 removal
   roster, does not resolve, refused by name, no reading. A row written back into the registry
   turns each red, which is what the check is for.

**Proof the six can fail.** Emptying the post-audit roster, dropping the removal roster from
`fault03`, and flipping `_mid not in IDX` back to `in` returns exactly those six failures (36/43).
Restored: 42/43, the one standing failure being A6.2.

---

## `test_run41_preservation` — 4

All four in commit `7822878`.

### Y-25, Y-26, Y-27 · STALE · source: every stamp from v42 to v70

1. **Assert:** the live stamp is `sim-2026.08-v41`; it supersedes `sim-2026.08-v40`; and the last
   twelve rows of the history are v30 … v41, position by position.
2. **Code today:** `SIMULATION_VERSION` is `sim-2026.09-v70`; `SIMULATION_VERSION_SUPERSEDED` is
   `sim-2026.09-v48`; the tail is v68, v69, v70.
3. **Deliberate?** Yes, one run at a time, each with its own recorded reason on its own line of
   `SIMULATION_VERSION_HISTORY` — v52 for Run 106's weighted vote, v53 for Run 107's eight
   thresholds, v70 for Run 136's full-precision banding of B2.18 and B2.19. **The suite went red
   for the mechanism working.** `SIMULATION_VERSION_SUPERSEDED` reading v48 rather than v69 is
   also not a defect: `models.py:1089-1091` defines it as *"the immediately preceding **audit
   baseline**"*, not the previous row.
4. **Classification: STALE.** Re-pointed under R2 to the invariants Run 41's boundary actually
   is — the live stamp is the last row and appears once; the superseded stamp is a member of the
   history, strictly earlier; and the v25…v41 block stands contiguously and in order, **anchored
   at v25 and read forward** so a legitimate append no longer shifts every clause and no stamp
   falls off the bottom of the ladder. Removing, replacing or reordering any member of that block
   still turns it red. The section's other checks — v26 still directly follows v25, no stamp
   twice, the v25 and v26 predecessors reconstruct from their pinned objects — were already
   passing and are untouched.

### Y-28 · STALE derivation, re-pointed — **and it exposed a real defect**

`"of the 70 governed participant-package bytes, exactly the 28 the v14 … v19 successors declare
between them moved, and no others"`.

1. **Asserts:** the participant-package files that moved since the v13 checksum record are exactly
   the ones the successor links declare.
2. **Code today:** the union was typed out link by link and stopped at `V18_TO_V19_CHANGED`, while
   the package has since been superseded to `og-participant-2026.08-v26` — a check in the same
   section asserts that and passes — with links present in `participant_packages.py` through
   `V26_TO_V27_*`.
3. **Deliberate?** Yes: each later run minted its own successor and declared its own delta,
   exactly as v14…v19 did. Measuring the live tree against a union that stops at v19 reports every
   later declared supersession as drift — which the note above the check itself names as the
   defect Run 43 had to correct in the freeze gate's B11.
4. **Classification: STALE derivation.** The union is now **read** from `participant_packages`
   from v13 forward, CHANGED and DELETED both, restricted to the files the v13 record governs (a
   later link may declare a file that record never named — `research/deepdive.html` is one — and
   such a file can never appear on the left-hand side).

**The check still fails, and it is now failing for the right reason.** With the union correct,
three governed bytes moved that **no** link declares. That is D2 below. It is left standing, not
suppressed.

**Proof the four can fail.** Pointing the live stamp at `[-2]`, negating the membership test,
moving the block anchor from v25 to v26, and dropping the `& set(rec)` restriction each return
their own failure (30/33 and 29/33 across two injections). Restored: 32/33.

---

# Real defects — findings for a ruling. NOT fixed in this run.

## D1 — A6.2 authorises a banded reading on a parameter the instrument records as UNSUPPORTED

**Found by** `test_run36_fault_guards`, `fault05.no_unsupported_authoritative`, offender `A6.2`.
**Still failing.**

**The check.** No module that COMPUTES and returns a `status_color` may carry a parameter whose
`parameter_class` is `UNSUPPORTED`.

**What is true today.** Both halves hold of A6.2 Safety Performance, and they contradict each
other:

* `app/simulation/parameters.py:325` lists `A6.2` in `_LADDER_ONLY`, whose entries the file
  describes as *"an unsourced band ladder, and in several cases a cap beside it"*, and
  `REG.parameter_provenance("A6.2")` returns exactly one row, class **`UNSUPPORTED`**.
* On the Run 36 corpus A6.2 returns `status_color` **Amber** with `band_provenance_class`
  **`CODIFIED`**, `threshold_source` `owner_configured_default`, and a `band_boundary` that
  publishes the rule verbatim: the recordable case rate per 200,000 employee hours against the
  applicable published construction benchmark, banded 0.75 / 1.0 / 1.5, with the note *"THE
  FORMULA AND THE BENCHMARK ARE CODIFIED; THESE THREE MULTIPLIERS ARE THE OWNER'S"*, an exposure
  floor beneath which nothing bands, and a hard override for a fatality or stop-work order.

The reading comes through `CAT89_CANONICAL` (`models_cat89.py:1539`, repointed at
`models.py:2336`) — the Run 31 canonical route that Run 133 established overrides `A6_EXTENSIONS`
for A6.2, A6.3 and A6.4. **The instrument therefore says two different things about the same
band**: its parameter table says the ladder is unsourced, and the published reading says the
formula and benchmark are codified with the owner's multipliers. One of them is wrong.

**Why this is not a stale expectation.** The check is right about the property. What is stale is a
**production record**, not a test expectation, and correcting it is a governance act: it moves a
published provenance classification. Item 3 does not fix real defects.

**What a fix would be** (stated, not applied): remove `"A6.2"` from `_LADDER_ONLY` in
`app/simulation/parameters.py` and give it its own `PARAMETER_PROVENANCE` row recording what the
band actually rests on — the codified recordable-rate-per-200,000-hours formula and the published
construction benchmark, with the three multipliers, the exposure floor and the hard override
identified as the **owner's** stated tolerance — so its class matches the `CODIFIED` /
`owner_configured_default` the reading already publishes. **If instead the owner rules that the
benchmark is not codified for this platform, the correct fix is the opposite one and A6.2 must
stop banding**; that is the decision, and it is his. Either way the same disagreement should be
checked for A6.3 and A6.4, which Run 133 named alongside A6.2 as overridden by `CAT89_CANONICAL`.

## D2 — three governed participant-package bytes moved with no successor link declaring them

**Exposed by** `test_run41_preservation`, sections 14-15, once the declared-delta union was
corrected. **Still failing.**

The v13 checksum record governs 70 participant-package files. 28 have moved. 25 of those are
declared across the links v13->v14 … v26->v27 in `tools/participant_packages.py`. **Three are
declared at no link at all:**

| file | last moved in |
| --- | --- |
| `assets/js/assistant.js` | Run 106 (`2d0ff85`) |
| `assets/js/config.js` | Run 94b (`bdc37e2`) |
| `assets/js/files.js` | Run 127 (`6235050`) |

This is undeclared drift in the frozen participant package — precisely what this check exists to
catch, and it has been unable to say so since Run 97 because the suite did not run at all. Whether
any of the three carries a step of the participant sequence is asserted separately and that check
**passes**, so the six sequence-bearing files are not implicated; these three are governed bytes
that changed without a successor declaring them.

**What a fix would be** (stated, not applied): the owner decides whether each of the three edits
was participant-visible. For each that was, the run that made it owes a declared delta at the
appropriate link — or, if the package is to be re-baselined, a successor that names all three in
one declared delta with the reason. Nothing here should be repaired by editing the v13 record,
which is evidence.

---

# BLOCKED / Unclear decisions

**None.** No finding was classified Unclear, none reached BLOCKED, and no finding needed more than
one attempt. The two real defects above are complete results — they are reported with the fix
stated, as the order requires, and both need an owner's ruling before anyone applies one.

---

# Iteration log

| finding | attempt | change made | proof result | suite | disposition |
| --- | --- | --- | --- | --- | --- |
| Item 4 `packages_due` <- `"packages"` | 1 of 10 | removed the bare alias from `_TD_COLS`, with the F8 reasoning recorded beside it | `_first_of({"Packages":100})` `100` -> `None`; alias restored -> `100` again; removed -> `None` | `test_run136a_remaining_h1_copies` 23/23 | **RESOLVED** |
| Y-1…Y-10 (vacuous, Run 96 substitution) | 1 of 10 | `SECTION_TO_MODULE` + `_suppressed_for`; two canonical-engine checks moved ahead of the dispatch; ARCH and fault 9 carrier B1.3->B1.1; ARCH duplicate-lineage retired | 17 failures -> 7 | `test_run17` 214/231 -> 214/221 | **RESOLVED** |
| Y-11, Y-12, Y-13 (A1.5 / A1.6 / A1.9 bands) | 1 of 10 | re-pointed to Run 107's ladders, with provenance class and threshold source asserted | 7 failures -> 4 | `test_run17` 217/221 | **RESOLVED** |
| Y-14 (6.2 plurality vs project rule) | 1 of 10 | re-pointed to Yellow, expectation computed from the owner's profile and cuts | see the four-fault injection below | `test_run17` 222/222 | **RESOLVED** |
| Y-15 (GATE mapping, A2.12) | 1 of 10 | named post-audit roster, plus a roster-is-real check | see below | `test_run17` 222/222 | **RESOLVED** |
| Y-16 (GATE float round-trip) | 1 of 10 | repaired to assert the coercion trap rather than the census | see below | `test_run17` 222/222 | **RESOLVED** |
| Y-17 (register entries PH.1, PH.5) | 1 of 10 | retired both, with the Run 97 deletion recorded beside them | four injections return exactly the four failures (218/222); restored 222/222 | `test_run17` 222/222 | **RESOLVED** |
| Y-18, Y-19, Y-21…Y-24 (run36 inventory and disabled rows) | 1 of 10 | post-audit roster; removal roster read from `run96_removed`; four "disabled" checks re-pointed to "removed"; two new non-vacuity checks | three injections return exactly those six failures (36/43); restored 42/43 | `test_run36` 34/41 -> 42/43 | **RESOLVED** |
| Y-20 (A6.2 UNSUPPORTED authorises a band) | 1 of 10 | none — real defect, reported | reproduces on every run | `test_run36` 42/43, this one standing | **REPORTED, NOT FIXED** |
| Y-25, Y-26, Y-27 (run41 stamp pins) | 1 of 10 | re-pointed to the append-only invariants; block anchored at v25 and read forward | injections at `[-2]`, negated membership, anchor v26 each fail (30/33, 29/33); restored 32/33 | `test_run41` 29/33 -> 32/33 | **RESOLVED** |
| Y-28 (package delta union stopped at v19) | 1 of 10 | union read from all declared links from v13 forward, restricted to the governed file set; failure line now names the undeclared movers | derivation correct; check still red on three genuinely undeclared files | `test_run41` 32/33, this one standing | **RE-POINTED; the residual failure is D2, REPORTED, NOT FIXED** |

---

# Confirmations

* **Starting commit** `2cb024e`. **Ending commit**: this report's own commit, recorded in the
  final message. Branch `worktree-agent-ac215df037be5c0cc`. Not pushed, not merged.
* **`SIMULATION_VERSION` did not move**; nothing under `server/app/simulation/` was edited.
* **Migration head** `0033_recognition_matches`, unchanged; no migration written.
* **`git status --porcelain` before each commit showed only the intended files.** Running
  `test_run17` dirties `code_audit/run17_failed_propositions.csv`,
  `code_audit/run17_fault_injection.csv` and `server/tools/run17/coverage.csv`; those three were
  present in every pre-commit status and **were never staged** — `git add` was by explicit path
  throughout — and were restored with `git checkout --` at the end. Run 136 named these three as
  the next generators to route; they remain unrouted and are agent X's to route on main.
* **Files changed:** `server/app/documents.py` (Item 4);
  `server/tools/test_run17_scientific_methods.py`, `server/tools/test_run36_fault_guards.py`,
  `server/tools/test_run41_preservation.py` (Item 3). Nothing in `server/tools/run17/`,
  `tools/run96_removed.py` or `tools/participant_packages.py` was edited — they were read as
  authorities. Main's working tree was never touched.
* **Every suite figure in this report was measured in this worktree and must be re-taken on
  main**, even though all four suites resolve `sys.path` from `__file__` and therefore tested this
  branch.
