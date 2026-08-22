# Run 47 — the EVM consistency check

**Date:** 2026-08-22
**Repository used:** the Linux clone at `/home/user/LinPRojectRadar`. There is no `.venv` on this
clone; the documented fallback interpreter was used, **CPython 3.11.15** (`python3 --version`).
**Branch:** `run47-evm-consistency-check`, rooted at `fe2e2df` (`HEAD == main == origin/main`,
tree clean at start). **Stamp minted: `sim-2026.08-v31`** at `server/app/simulation/models.py:582`.
**Participant package minted: `og-participant-2026.08-v16`.**
**Suites: 191, 14,437 / 14,437 checks, 0 red, 0 aborting. Successor freeze gate 32/32, 0 of 15
blocker classes blocked. Browser verification 19/19. Fault campaign 7/7 proven failable.
No stop condition fired.**
**Production Postgres was never configured or contacted.** No PRJ-001 document and no synthetic
corpus was read or modified. `DEng\Demo` was ignored.

**Method.** Every fixture was built through the **real routes** — `/exec` `researchlogin`,
`adminparticipantcreate`, `adminmemberadd`, `projectupload`, `projectcomputeall`,
`projectresults` — against a **throwaway migrated SQLite database**, with the extraction model
stubbed by `app.documents.set_extractor_override` + `app.extraction_client.StubExtractor`, which
is the route every suite in this repository uses and the only one available. Everything
downstream of extraction is the production path, untouched. The databases were torn down after
use. The browser driver ran from a **clean subdirectory**, never the scratchpad root, because a
`queue.py` there shadows the standard library and `anyio` then fails as an opaque HTTP 500.

---

## 0. The arithmetic in the order — one slip, found and corrected, verdict unchanged

**The order states the implied `ev` as 1,066,671 at its §1 and again at its §8 test 5. That
figure is wrong.** Hand-computed from the order's own stated formula, budget at completion times
actual percent complete:

```
5,874,620 x 18      = 105,743,160
5,874,620 x 0.16    =     939,939.2
sum / 100           =   1,066,830.992          <- the implied earned value
|1,046,735 - 1,066,830.992| = 20,095.992
20,095.992 / 1,066,830.992  = 1.8837090552 %   <- the relative difference
```

The order's figure is low by **159.992**. Run 46's report independently gives 1,066,830.99 as
well. **The verdict test 5 requires is unchanged**: 1.8837 per cent against the computed implied
value, or 1.87 per cent against the order's, are both at or below the 2 per cent tolerance, so
the earned-value pair produces **no finding** either way. The figure asserted by the code and by
the suite is the one computed here, not the one in the order
(`server/tools/test_run47_evm_consistency.py`, the `EV_IMPLIED` and `EV_DIFF_PCT` literals and
their derivation comment).

**The other figures in the order hold, and were re-executed rather than copied:**

```
5,874,620 x 18.47 % = 1,085,042.314                        (order: 1,085,042)   VERIFIED
|824,370 - 1,085,042.314| = 260,672.314
260,672.314 / 1,085,042.314 = 24.024161144 %               (order: 24.0 %)      VERIFIED
```

**What the relative difference is relative TO, stated once and not left to inference.** The
denominator is the **IMPLIED** value: `|stated - implied| / |implied|`. That is the reading the
order's own §1 uses to arrive at 24.0 per cent. The other defensible reading, relative to the
stated value, gives **31.6208 per cent** for the same pair, and the two differ. The implied-value
reading is the one implemented, it is declared in the module's own docstring
(`server/app/evm_consistency.py`), and **§8 tests 2 and 3 exercise the boundary of that reading
and no other**: the two boundary fixtures read 2.00 and 2.01 per cent relative to the implied
value, and 2.04 and 2.05 per cent relative to the stated value, so a check written against the
wrong denominator fails there rather than passing quietly. Fault F2 below proves that.

No surface names a base. Both rendered sentences say "the stated and implied figures differ by
24.0 percent", so nothing a project manager reads depends on which reading was chosen.

---

## 1. Every relation the §5 sweep found, and whether it was implemented

**The sweep was executed against the live emission tables, not transcribed**:
`extraction_merge._NUMERIC_EMISSIONS` (`server/app/extraction_merge.py:551-660`) and
`extraction_merge._EXTRA_NUMERIC_KEYS` (`:326-337`), document type by document type, looking for
any document type that emits BOTH a percentage-like field and a value that percentage determines.

### 1.1 Implemented — two relations

| relation | document types that state BOTH figures | implemented |
|---|---|---|
| `pv` against BAC x `plannedPctComplete` | `time_phased_schedule` (`planned_value_to_date` + `planned_percent_complete`, `:567`), `schedule_update` (`:653`), `monthly_report` (`planned_value` + `planned_percent_complete`, `:571-573`) | **YES** |
| `ev` against BAC x `actualPctComplete` | `pay_application` (`completed_to_date` + `percent_complete_verified`, `:561`), `monthly_report` (`earned_value` + `actual_percent_complete`, `:571-572`) | **YES** |

Both are declared in `CONSISTENCY_RELATIONS` (`server/app/evm_consistency.py`). The writer lists
above are re-derived from `_NUMERIC_EMISSIONS` inside the suite itself
(`test_run47_evm_consistency.py` section 8), so a document type that gains or loses one of these
emissions changes what the suite prints rather than silently escaping the check.

### 1.2 Found by the sweep and NOT implemented — one relation, with its reason

| relation | document type | why not |
|---|---|---|
| `analogousOverrunPct` against `analogousBac` and `analogousFinalCost` | `historical_data` (`:632-635`) | **The shape is the same; the budget at completion is not.** These three determine each other against the REFERENCE project's budget at completion, `analogousBac`, and not against this project's. §5's first condition is written about a known budget at completion for the period being computed, and there is no period, no as-of date and no document date on a `historical_data` record at all (`extraction_merge.py:544-546` names it as one of the four types carrying no as-of). Reported rather than implemented. **It would not require deriving or overriding any stored value to implement later**, so §12.8 does not fire. |

### 1.3 Considered by the sweep and rejected — five, each with its reason

| candidate | document type | why it is not this relation |
|---|---|---|
| `ac` with `actualPctComplete` | `pay_application` | Actual cost is not determined by budget at completion times percent complete. A project may spend any amount to reach a given percentage; that gap is what cost performance measures. There is no identity to check. |
| `ev` with `bac` | `schedule_of_values` | Both are values; the document states no percentage, so nothing determines anything. |
| `oshaIncidentRate` with `totalManhours` | `safety_report` (`:331-333`) | A rate and its denominator do determine each other, but against a recordable-incident count and not against the budget at completion. Not the property §5 names. |
| `subcontractorComplianceScore` with `on_time_deliveries` / `scheduled_deliveries` | `subcontractor_report` (`:334-336`) | Same shape, same reason: no budget at completion enters it. |
| `environmentalComplianceRate` with `environmentalViolations`; `qualityAuditScore` with `totalFindings` | `environmental_report`, `quality_audit_report` | A rate or score beside a count, with no stated arithmetic relation between them at all. |

### 1.4 The two conditions, both implemented and both proven failable

1. **The budget at completion must be known.** Absence is stored present-and-null
   (`extraction_merge.py:936` initialises every key to `None`), so an absent budget at completion
   is a `None` and not a zero. The check does not run and reports nothing. A stored zero is
   refused too, because a zero budget determines nothing and dividing by an implied zero is not a
   disagreement.
2. **Both figures must come from the SAME document.** `signal_inputs.sources` records a
   `documentId` per field (`extraction_merge._source_entry`, `:882-895`), which is what
   establishes it. Two records that BOTH lack a document identity are **not** thereby the same
   document; that is asserted separately.

---

## 2. The exact disagreement text rendered on each surface, read back from the DOM

Read out of the rendered DOM of the real application, served by uvicorn from the repository root
against a throwaway migrated SQLite, driven by the real Chromium headless shell
(`server/tools/drive_run47_browser.py`).

**Browser session cwd:**
`/tmp/claude-0/-home-user-LinPRojectRadar/56ab0a7f-4e21-5061-8b33-396724907fe8/scratchpad/run47drv`
(a clean subdirectory, deliberately not the scratchpad root).
**Repository root:** `/home/user/LinPRojectRadar`.
**The `DEng\Demo` tell was checked before anything else was measured:** the DOM carries **7
`.page` sections**, which is what this application has, and **neither `api.js` nor `boot.js` is in
`document.scripts`**. The application under test is the right one.

### 2.1 The Executive Brief — verbatim from the DOM

Head (`.eb-consistency-head`):

> Figures stated in one document that do not agree with each other:

Item (`.eb-consistency-item`):

> In period 1, the Time-phased Schedule / Baseline states a planned value to date of 824,370 and
> a planned percent complete of 18.47. Applied to the budget at completion of 5,874,620, that
> percentage implies a planned value to date of 1,085,042. The stated and implied figures differ
> by 24.0 percent. Both figures were read from the same document, and both are reported as the
> document stated them.

Exactly one disagreement is rendered. The block contains **zero** user-facing controls of any
kind — no button, no input, no select, no textarea, no link, no element with a button role — and
the brief panel still carries **exactly the one control it carried before**, its regenerate
button. Nothing was added, moved or removed.

### 2.2 The recommendation — verbatim from the DOM

Rendered by `LinRecOptions.html(LinRecOptions.build(servedRow))`, which is the exact call the
Governance Decision card makes (`assets/js/app.js:1444-1445`, `assets/js/decision-ui.js:551`).

Heading (`.ro-option-title`):

> Figures that do not agree

Lede (`.ro-what`):

> These figures were stated together in one document and do not agree with each other. They are
> reported as the document stated them. Nothing here changes the recommendation above.

Item (`.ro-consistency-item`):

> In period 1, the Time-phased Schedule / Baseline states a planned value to date of 824,370 and
> a planned percent complete of 18.47. Applied to the budget at completion of 5,874,620, that
> percentage implies a planned value to date of 1,085,042. The stated and implied figures differ
> by 24.0 percent. Both figures were read from the same document, and both are reported as the
> document stated them.

Zero controls in this block too.

**One thing a later reader needs, and it is not a defect this run introduced.** The
courses-of-action card reports `available: false` on **every** project this platform currently
stores, because the analysis that scores the courses is not one of the two modules that vote
(`assets/js/recommendation_options.js:155`, `CORE_VOTING_MODULES = ['A1.7', 'A1.8']`). The
disagreement text is therefore rendered on **both** branches of that card, the available one and
the unavailable one, so it cannot be lost with the courses it is not about. Fault F7 proves the
unavailable branch's rendering is failable.

**Wording, measured on the text that was actually rendered, not on the source:** no module
identifier, no number-scheme label, no em dash and no en dash; the text names the stated figure,
the implied figure, the difference, the budget at completion, the percentage, the document and
the period; the earned-value pair does not appear, because it is inside tolerance. No uncaught
page error was raised while rendering.

---

## 3. Every §8 guarantee, marked, with the injection that proved its check could fail

**Fault protocol on every injection**: inject into the real file, **re-read the bytes from disk**
to confirm the injection landed, run the named suite, require **RED for the intended reason** (a
crash is not a RED, and a suite printing no `RESULT:` line has not run), restore byte-for-byte,
re-run, require GREEN. Baseline before: suite 56/56, browser 19/19. Baseline after: suite 56/56,
browser 19/19.

| # | §8 guarantee | verdict | evidence | the injection that proved the check can fail |
|---|---|---|---|---|
| 1 | A document stating `pv` and `plannedPctComplete` that disagree by more than 2% against a known BAC produces a finding with the correct stated, implied and difference figures | **VERIFIED** | suite §1: stated 824,370; implied 1,085,042.314; difference 24.024161 %; document named by type and by identity; period carried | **F1** `TOLERANCE = 0.02` -> `0.50`. RED: "the render's planned value produces a disagreement finding" |
| 2 | A disagreement of exactly 2% produces no finding | **VERIFIED** | suite §3: 98,000 against an implied 100,000 on a budget at completion of 1,000,000 and a percentage of 10 — exact in binary on both sides — produces `[]` | **F2** denominator `abs(implied)` -> `abs(stated)`. RED: "a difference of exactly 2 per cent produces NO finding" (it then reads 2.04 % and fires) |
| 3 | A disagreement of 2.01% produces a finding | **VERIFIED** | suite §3: 97,990 against an implied 100,000 produces one finding, reported as 2.01 per cent, and the sentence prints `2.01` and not a rounded `2.0` | **F1** as above. RED: "a difference of 2.01 per cent produces a finding" |
| 4 | The render's own figures produce a finding: stated 824,370, implied 1,085,042, difference 24.0% | **VERIFIED** | suite §1 and the DOM read-back at §2 above | **F1**. RED on the same check |
| 5 | The render's `ev` figures produce no finding | **VERIFIED**, with the order's figure corrected | suite §2: stated 1,046,735 against an implied **1,066,830.992**, difference **1.8837 %**, below tolerance. **The order's 1,066,671 is wrong; see §0.** The pair is REACHABLE — both figures present, both from one document — so the refusal is the tolerance and not an absent precondition, asserted separately | **F1**. Under the fault the tolerance question is answered differently and the whole section goes red |
| 6 | `pv` is stored exactly as the document stated it; no stored figure changes anywhere | **VERIFIED** | suite §5: `pv` stores 824,370, not the implied 1,085,042.314; the percentage stores as stated; schedule performance is still `ev / pv` on the STORED planned value, 1.27, unaltered by the finding; a full recompute after the check exists stores **byte-identical** signal inputs. Structurally: the check is a pure function called on the READ path from the stored row (`server/app/documents.py:1790`), so it cannot write | **F5** (below) is the strongest available: it makes the read path write into the served view and the census comparison goes red |
| 7 | An absent BAC produces no finding and no error | **VERIFIED** | suite §4: the no-contract project stores `bac = None` (present and null) and holds the SAME disagreeing pair, so the refusal is the absent budget and not an absent pair; `consistency_findings` is `[]` and the route returns `ok` | **F4** `bac = _num(si.get("bac"))` -> `... or 1.0`. RED: "an absent budget at completion produces NO finding and NO error" |
| 8 | A disagreement changes no band, status, colour or posture; the census with and without is identical | **VERIFIED** | suite §6 and §4 of this report | **F5** the finding is allowed to set `project_status = "Red"`. RED: "THE FULL CENSUS WITH AND WITHOUT THE DISAGREEMENT IS IDENTICAL" and "project status unchanged [Red]" |
| 9 | No module abstains that would otherwise compute | **VERIFIED** | suite §6: the `abstained` list is identical between the serve that carries the disagreement and the serve with it suppressed | **F5** as above |
| 10 | The disagreement text renders on the Executive Brief and on the recommendation, verified in a browser and read back from the DOM | **VERIFIED** | §2 above, 19/19 | **F6** the brief's `briefConsistencyHtml` builder neutered — this kills BOTH insertion paths at once, which is why a single-site injection was rejected as insufficient (see §3.1). RED: "the disagreement block is in the rendered DOM". **F7** the recommendation card's unavailable branch loses `consistencyHtml(spec)`. RED: "the disagreement block is in the rendered card" |
| 11 | The rendered text contains no module identifier, no number-scheme label and no em dash | **VERIFIED** | browser §3, measured on the DOM text; and suite §7, measured on the served sentences | **F6/F7** remove the text, and the "there is rendered text to measure" guard goes red rather than the wording checks passing over an empty string |
| 12 | Modules in service is 63, registry total 101, both derived | **VERIFIED** | suite §10: `len(service_index()) == 63`, `len(registry_index()) == 101`, both derived, neither written down | freeze gate B02 (population mismatch) is the standing guard, 0 |
| 13 | Voting count is exactly 2, `A1.7` and `A1.8` | **VERIFIED** | suite §10: `sorted(CORE_VOTING_MODULES) == ["A1.7", "A1.8"]` | freeze gate B09 (voting count is not exactly 2), 0 |
| 14 | The successor freeze gate passes in full | **VERIFIED** | §10 below: 32/32, 15 blocker classes evaluated, 0 blocked | the gate's own non-vacuity campaign is Run 37's, unchanged |

### 3.1 Two injections that did NOT prove what they appeared to, and were replaced

Recorded because a run that only reports the injections that worked is not reporting its method.

- **Removing `${consistency}` from the brief panel template alone: GREEN under fault.** The block
  still reached the DOM, because `refreshBriefConsistency` rebuilds it after the row arrives.
- **Removing the `refreshBriefConsistency(p)` call alone: GREEN under fault.** The block still
  reached the DOM, because on this fixture the detail page renders after the row has already been
  grafted, so the template slot was populated.

Two independent paths put the same text on the same surface, and neither alone is load-bearing.
Neither injection was reported as a pass. **F6 neuters the shared builder both paths call**, and
that is RED. A reader should take from this that the brief's disagreement block survives either
ordering of render and fetch, which is why the fixture had to be built with all documents in
period 1: `primeAndRefresh` reads back `projectresults` for **period 1** and hard-codes it
(`assets/js/detail.js:1304`), so a disagreement sitting in a period the page never reads back
would have proved nothing about the page. That hard-coding is pre-existing and is recorded as an
incidental finding at §7.

### 3.2 The seven faults, in full

| id | injected into | fault | result under fault | restored |
|---|---|---|---|---|
| F1 | `server/app/evm_consistency.py` | `TOLERANCE = 0.02` -> `0.50` | suite 34/40, 6 named checks RED, no crash | 56/56 |
| F2 | `server/app/evm_consistency.py` | relative difference denominator `abs(implied)` -> `abs(stated)` | suite 51/56, 5 named checks RED (24.02 becomes 31.62; the exact-2% fixture starts firing) | 56/56 |
| F3 | `server/app/evm_consistency.py` | the same-document condition dropped | suite 53/56, 3 named checks RED | 56/56 |
| F4 | `server/app/evm_consistency.py` | the known-budget condition defeated | suite 53/56, 3 named checks RED | 56/56 |
| F5 | `server/app/documents.py` | a finding is allowed to set `project_status = "Red"` | suite 54/56, the census identity and the project-status check RED | 56/56 |
| F6 | `assets/js/detail.js` | the brief's disagreement builder neutered | browser 15/19, 4 checks RED | 19/19 |
| F7 | `assets/js/recommendation_options.js` | the card's unavailable branch loses the block | browser 16/19, 3 checks RED | 19/19 |

Every injection was re-read from disk before any conclusion was drawn from it, every one landed,
none crashed, and every restore was byte-verified and re-run green. Baseline re-checked at the
end: suite 56/56, browser 19/19, `git status --porcelain` clean.

---

## 4. The census with and without a disagreement, proving they are identical

This is §8 test 8 and it is the sharpest check in the run, so the construction is stated in full.

**The comparison is on ONE project, not two.** Comparing a disagreeing project with an agreeing
one would compare two different stored figures and prove nothing. Project `PRJ-R47-DISAGREE` is
served twice at period 4:

1. **with the disagreement present** — the served result carries one finding;
2. **with it suppressed** — `documents.consistency_findings` replaced by a function returning
   `[]` for the duration of the second serve, then restored.

**The census is every band, status, colour, posture, module result and abstention the served
result carries**, serialised in canonical order. `consistency_findings` itself is excluded, and
`computed_at` and `result_id` with it; including the finding would make the comparison trivially
unequal and prove nothing. Everything else is in: `module_results`, `category_statuses`,
`project_status`, the governed status semantics, `abstained`, `evidence_qualification`,
`portfolio_snapshot`, `recommendation_basis`, `recommendation`, `source_documents`,
`simulation_version`, `seed`, `period_cutoff`.

**Result, from `test_run47_evm_consistency.py` section 6:**

| check | verdict |
|---|---|
| the disagreement IS present on the first serve, so the comparison is not vacuous | PASS |
| the suppressed serve carries none, so the two serves genuinely differ in it | PASS |
| **THE FULL CENSUS WITH AND WITHOUT THE DISAGREEMENT IS IDENTICAL** | **PASS** |
| project status unchanged | PASS |
| category statuses unchanged | PASS |
| **NO MODULE ABSTAINS THAT WOULD OTHERWISE COMPUTE**: the abstention list is identical | PASS |
| the recommendation's own basis is unchanged | PASS |
| the agreeing control project reports nothing, so the check does not fire on everything | PASS |

**The comparison is failable, and F5 proves it**: allowing a finding to set `project_status` to
`"Red"` turns the census-identity check and the project-status check red. Stop condition 12.5 did
not fire.

**Nothing is stored, so nothing can move.** The check is derived at read time in `_result_view`
(`server/app/documents.py:1790`), by a pure function, from the row that response already carries
— the same construction `recommendation_basis` uses. No column is added, no migration is needed,
and a row stored before this run answers exactly as one stored after it. A full recompute of the
disagreeing project after the check existed stored **byte-identical** signal inputs.

---

## 5. Was a case found where a value and its percentage come from different documents?

**Yes. It is reachable, it was constructed, and it produces no finding — which is what §5's second
condition requires of this run.**

Project `PRJ-R47-SPLIT` holds, at period 4:

- a Time-phased Schedule stating `planned_value_to_date = 824,370` and **no percentage**;
- a Monthly Progress Report stating `planned_percent_complete = 18.47` and **no planned value**;
- a contract at period 1 giving `bac = 5,874,620`, carried forward as an identity field.

Read back from `projectresults`, the stored row holds `pv = 824,370`,
`plannedPctComplete = 18.47` and `bac = 5,874,620` — the same disagreeing pair against the same
known budget at completion — and `signal_inputs.sources["pv"].documentId` differs from
`signal_inputs.sources["plannedPctComplete"].documentId`. The check reports nothing. All four
facts are asserted separately in the suite, so the refusal is demonstrably the two-document
condition and not an absent figure. **F3 proves the condition can fail**: dropping it makes the
split project report a disagreement.

This is reported, not treated as a disagreement, exactly as §5 orders. Nothing further was built
for it.

---

## 6. Which audit artifacts the suites rewrote, and were restored

**Eighteen. Seventeen under `code_audit/`, plus one outside it.** Identical to what Run 45 saw.
Every one restored with `git checkout --`. **None committed.** After each of the three full suite
runs, `git status --porcelain` was taken and every rewritten artifact restored before anything was
staged; no fault-injection suite was ever run in the background while staging.

```
code_audit/run10_no_operational_effect.csv
code_audit/run20_cycle12_100_reaudit.csv
code_audit/run20_cycle12_guard_nonvacuity.csv
code_audit/run20_cycle12_lineage_campaign.csv
code_audit/run21_guard_nonvacuity_results.csv
code_audit/run30_cat7_operational_execution.csv
code_audit/run38_controlled_stimulus_execution_order.csv
code_audit/run38_lock_integrity.csv
code_audit/run38_participant_state_machine.csv
code_audit/run39_launch_identity.csv
code_audit/run8_expectation_mutation_proof.csv
code_audit/run9_abstention_results.csv
code_audit/run9_alias_overlay_verification.csv
code_audit/run9_fixture_import_results.csv
code_audit/run9_known_answer_results.csv
code_audit/run9_no_operational_effect.csv
code_audit/run9_validator_gap_recomputations.csv
server/tools/run17/coverage.csv                 <- the one OUTSIDE code_audit/
```

**One ordering artifact, recorded because it wastes a session's time if rediscovered.**
`test_run22_production_tree_completeness.py` failed 40/44 inside the full-suite runner on the
first pass and passed 44/44 standing alone against the same tree. It reads audit artifacts that
earlier suites in the same run had already rewritten. It is green in the runner once the pinned
manifest is reconciled, and it is green in the final run.

---

## 7. Incidental findings, unacted

1. **`primeAndRefresh` reads back `projectresults` for period 1 and hard-codes it**
   (`assets/js/detail.js:1304`, `period: 1`). Every panel on the project detail page then holds
   that row: the key drivers, the abstention reasons, `recommendation_basis` and now the
   disagreement findings. On a project whose current period is not 1 the page is showing period
   1's row. This is pre-existing, it affects four grafted fields and not only this run's, and it
   is not in scope. It is why the browser fixture had to be single-period.
2. **`BRIEF_CAT_LABEL` is dead code.** It is defined at `assets/js/detail.js:1702` and read
   **nowhere** in the repository — `grep -rn "BRIEF_CAT_LABEL"` returns the definition and five
   report mentions and nothing else. Run 44's report already recorded this
   (`REPORT_2026-08-10_google-maps-and-copy.md:208`: "dead code, never rendered"). It is corrected
   as §11 orders, and the correction is therefore **not verifiable from a rendered DOM**, because
   there is no surface that renders it. That is stated rather than dressed up.
3. **Two Run-45 census artifacts do not match the v30 release manifest.**
   `build_run47_successor_release.py` reports `code_audit/run45_census_before.csv` and
   `code_audit/run45_census_after.csv` as moved since v30. Neither was touched by this run —
   `git log` shows both last written by `6d7757e`, and the working tree is clean for both — so the
   v30 checksum rows were taken before their final bytes landed. Pre-existing, recorded, unacted.
4. **The brief's LLM prompt still prints a category identifier.** `assets/js/detail.js:1612`
   builds `c.num + " " + c.name + ": " + c.status` into the text sent to the model. That is not
   `BRIEF_CAT_LABEL` and is outside §11's order, so it was not touched. Named here so the next
   session does not have to rediscover it.
5. **`signal_inputs.sources` still records no source FIELD name**, only document type and
   identity (`extraction_merge.py:882-895`), as Run 46 found. This run does not need it — a
   `documentId` per field is exactly what §5's second condition requires — but a finding cannot
   say which CELL of a document a figure came from, and it does not pretend to.
6. **Four status comparisons remain case-sensitive**, two of them in `decision.js`, a
   sequence-bearing file. Carried unchanged from Run 44. Untouched.

---

## 8. What the next session needs, stated as a decision for the owner

1. **The `historical_data` triple: implement the check against the reference project's own budget
   at completion, or leave it alone?** `analogous_overrun_pct`, `similar_project_bac` and
   `similar_project_final_cost` are stated together by one document and determine each other, but
   against `analogousBac` and not against this project's budget at completion, and the record
   carries no date of any kind. Implementing it needs one ruling: whether "a known BAC" in §5
   means this project's, as written, or any budget at completion the same document states.
   **Nothing about it requires deriving or overriding a stored value.** This is the only relation
   the sweep found and did not implement.
2. **The period-1 hard-coding at `detail.js:1304` (incidental finding 1): repair, or leave?** It
   is a render-side defect of the same family as the four Run 44 repaired, and it now governs
   which period's disagreement a project manager sees. It is a one-line change with a real blast
   radius — four grafted fields, every panel on the page — so it needs an order, not an
   improvisation.
3. **`BRIEF_CAT_LABEL` is dead code (incidental finding 2): delete it, or keep it corrected?**
   It has now been carried by four runs and corrected by one, and it renders nowhere. Deleting it
   removes the thing that keeps being rediscovered; keeping it costs nothing but will be
   rediscovered again.

No fix is recommended beyond what §2 orders. These are the three decisions, not proposals.

---

## 9. What was built, in full

**New:** `server/app/evm_consistency.py`. A pure function, `consistency_findings(signal_inputs,
period)`, and the two relations it checks. It reads; it never writes. It carries no band, no
colour and no severity. Nothing in the analytical layer imports it.

**Wired in at exactly one place:** `server/app/documents.py:1790`, inside `_result_view`, beside
`recommendation_basis` and for the same reason — derived at READ time from the row the response
already carries, so no column is added, no migration is needed, a row stored before this run
answers exactly as one stored after it, and no stored figure can change even in principle. It is
not gated by the reveal: a disagreement between two figures a document itself stated is evidence,
in the same class as `signal_inputs`, and carries no action.

**Two surfaces, both of which already existed:**

- `assets/js/detail.js` — `briefConsistencyHtml` and `refreshBriefConsistency`, rendering into the
  executive brief panel beside the existing deterministic flags block. Deterministic: read from
  the stored row, not from the generated brief, so a cached brief, a model refusal or a
  regenerate cannot lose it.
- `assets/js/recommendation_options.js` — `consistencyOf` and `consistencyHtml`, rendering beside
  the recommendation on both branches of the courses-of-action card.

**No user-facing control was added, moved or removed.** Measured in the real DOM: zero controls in
either block, and the brief panel still carries exactly its one regenerate button. Stop condition
12.1 did not fire.

**One suite and one browser driver:** `server/tools/test_run47_evm_consistency.py` (56 checks) and
`server/tools/drive_run47_browser.py` (19 checks). Every expected value in the suite is
hand-computed from the stated formula and written as a literal; nothing is read back from
`evm_consistency` and compared with itself.

---

## 10. Freeze and merge — every gate row with its verdict

**Stamp minted: `sim-2026.08-v31`**, `server/app/simulation/models.py:582`, with the boundary
recorded above the line. `SIMULATION_VERSION_SUPERSEDED` advances to `sim-2026.08-v30`;
`SIMULATION_VERSION_HISTORY` is appended to and nothing in it is edited or removed.
(Run 46 was report-only and minted nothing, so v30 is the immediate predecessor.)

**Participant package minted: `og-participant-2026.08-v16`**,
`code_audit/run47_participant_package_v16_checksums.sha256`, 70 files. **TWO moved:
`assets/js/detail.js` and `assets/js/recommendation_options.js`. NEITHER IS SEQUENCE-BEARING.**
The six sequence-bearing files — `decision.js`, `decision-ui.js`, `workspace.js`, `deepdive.js`,
`intake.json`, `debrief.json` — are byte for byte identical to v15, asserted directly, so **no
named sequence exception was needed and none was written**: the invariant v15 had to break with an
exception is intact again. The v15 record is pinned to `fe2e2df`, the commit whose blobs it
describes, and is not regenerated.

**Production tree manifest re-taken to TRUE bytes:** `code_audit/run47_production_tree.sha256`,
244 rows. `production_tree.PINNED` moves to it and `PINNED_RUN45` keeps the parent addressable.

**Successor freeze gate — 15 blocker classes, all evaluated, 0 blocked**
(`research/freeze/run47_successor_freeze_gate.csv`, regenerated from the live tree by
`build_run37_acceptance.py` and re-evaluated by `test_run37_freeze_gate.py`; the gate was not
edited to say PASS):

| blocker | class | count | result |
|---|---|---|---|
| B01 | dirty candidate identity | 0 | PASS |
| B02 | population mismatch | 0 | PASS |
| B03 | controlled-stimulus mismatch | 0 | PASS |
| B04 | participant-sequence drift | 0 | PASS |
| B05 | false defensibility statement | 0 | PASS |
| B06 | unexpected execution exception | 0 | PASS |
| B07 | Category-9 bypass | 0 | PASS |
| B08 | Category-10 authority violation | 0 | PASS |
| B09 | voting count is not exactly 2 | 0 | PASS |
| B10 | current taxonomy dual authority | 0 | PASS |
| B11 | package or predecessor mutation | 0 | PASS |
| B12 | browser qualification failure | 0 | PASS |
| B13 | unresolved blocking Run-36 defect | 0 | PASS |
| B14 | unsupported final empirical-validation claim | 0 | PASS |
| B15 | candidate behaviour changed during the run | 0 | PASS |

**The gate suite's own 32 rows — 32/32:**

| row | verdict |
|---|---|
| `run37.gate.generator_runs` — the acceptance generator runs to completion; a crash is a blocker, not a pass | PASS |
| `run37.gate.artifact_present` — the committed freeze gate exists | PASS |
| `run37.gate.reproduces` — and it REPRODUCES from the current tree, so it is not a stale snapshot | PASS |
| `run37.gate.fifteen_blocker_classes` — all fifteen blocker classes are evaluated | PASS |
| `run37.gate.B01` — dirty candidate identity is zero | PASS |
| `run37.gate.B02` — population mismatch is zero | PASS |
| `run37.gate.B03` — controlled-stimulus mismatch is zero | PASS |
| `run37.gate.B04` — participant-sequence drift is zero | PASS |
| `run37.gate.B05` — false defensibility statement is zero | PASS |
| `run37.gate.B06` — unexpected execution exception is zero | PASS |
| `run37.gate.B07` — Category-9 bypass is zero | PASS |
| `run37.gate.B08` — Category-10 authority violation is zero | PASS |
| `run37.gate.B09` — voting count is not exactly 2 is zero | PASS |
| `run37.gate.B10` — current taxonomy dual authority is zero | PASS |
| `run37.gate.B11` — package or predecessor mutation is zero | PASS |
| `run37.gate.B12` — browser qualification failure is zero | PASS |
| `run37.gate.B13` — unresolved blocking Run-36 defect is zero | PASS |
| `run37.gate.B14` — unsupported final empirical-validation claim is zero | PASS |
| `run37.gate.B15` — candidate behaviour changed during the run is zero | PASS |
| `run37.gate.blocking_defects_zero` — BLOCKING DEFECTS = 0 | PASS |
| `run37.gate.predecessor_release_preserved` — the v25 release record still says v25 | PASS |
| `run37.gate.immediate_predecessor_release_preserved` — the v26 successor record still says v26 | PASS |
| `run37.gate.immediate_predecessor_release_preserved` — the v27 successor record still says v27 | PASS |
| `run37.gate.immediate_predecessor_release_preserved` — the v28 successor record still says v28 | PASS |
| `run37.gate.no_release_while_blocked` — no final release record may exist while any blocker stands | PASS |
| `run37.gate.release_present_when_clean` — and when the gate is clean the record, report and checksum manifest exist | PASS |
| `run37.gate.limitation_stated` — empirical field validation is stated as 0 of 100 | PASS |
| `run37.gate.limitation_stated` — the release explicitly denies any claim of validated real-world predictive effectiveness | PASS |
| `run37.gate.limitation_stated` — the historical incompleteness of OG-SYNTH-0.1 is stated | PASS |
| `run37.gate.limitation_stated` — qualification is stated as bounded controlled-study instrument use | PASS |
| `run37.gate.disposition` — the recorded disposition is FINAL_FREEZE_ACCEPTED and the gate agrees | PASS |
| `run37.gate.no_self_reference` — the record distinguishes candidate, digest and recording method, and names the Run-45 candidate as its parent | PASS |

**Full suite: 191 suites, 14,437 / 14,437 checks, 0 red, 0 aborting, ALL SUITES GREEN.**
(190 before this run, plus `test_run47_evm_consistency.py`.)

**Ten pinned guards were reconciled to TRUE bytes. Not one was weakened, disabled or widened.**
Each names the Run-47 scope explicitly, on the construction those files already use:

| guard | what it now names |
|---|---|
| `test_run2_fifteen_defects.py` | the exact removed and added lines of `detail.js` and `recommendation_options.js`, as literal sets |
| `test_run8_retest_classify_27.py` | `RUN47_SCOPED_FILES = {"server/app/evm_consistency.py"}` |
| `test_run6_known_answer.py` | the same one file, named rather than the comparison relaxed |
| `test_run10_state_protection.py` | `RUN47_NON_ANALYTICAL_SCOPE = {"server/app/evm_consistency.py"}` |
| `test_run25_rail_removal.py` | `run47_production_tree.sha256` appended to the pin chain |
| `test_run28_participant_packages.py` | v15 becomes a predecessor measured at `fe2e2df`; a new v16 current-link section asserting all six sequence-bearing files unmoved, both changed files GAINING the block, and control counts unchanged |
| `test_run31_version_boundaries.py`, `test_run32_closure_version_boundary.py` | `sim-2026.08-v31` appended to the expected history |
| `test_run36_instrument_qualification.py`, `test_run39_launch_gate.py`, `test_run38_frozen_immutability.py`, `test_run39_frozen_immutability.py`, `test_run41_preservation.py` | `sim-2026.08-v31` and `og-participant-2026.08-v16` |
| `test_run37_freeze_gate.py` | the Run-47 successor artefacts, and the Run-45 candidate as the parent the record must name |

One reconciliation was itself a defect and is recorded: the v16 sequence-step probe counted
`"lock"` as a substring, which also matches `"block"`, and my own added HTML uses `block`. A probe
that cannot tell those apart measures the wrong thing. It counts whole words now.

**No stop condition fired.** 12.1 no control moved; 12.2 no stored figure changed; 12.3 no band,
status, colour or posture changed; 12.4 no module abstained that would otherwise compute; 12.5 the
censuses are identical; 12.6 every gate row passes and the only rows that ever failed were
manifests this run's edits falsified; 12.7 no check was deleted; 12.8 the sweep found no relation
whose check would require deriving or overriding a stored value.

---

## 11. `BRIEF_CAT_LABEL` — before and after, and the sweep

`assets/js/detail.js`, formerly `:1689-1697`, now `:1702-1713`. Against `NAMING_AUTHORITY.md:96`,
quoted verbatim as §3.5 of the order requires:

> **Never use a module id or number in user-facing text.** No "Cat 4", no "1.7", no "PH.2", no
> "A4.2". Groups and purposes only. The old "Cat N" scheme is retired along with the names.

**The ten labels, before and after.** Only the printed VALUES changed; the KEYS are the stored
category snapshot's own identifiers, are matched against and never displayed, and are not
user-facing text.

| key | BEFORE | AFTER |
|---|---|---|
| `Cat 1` | `Cost Performance (Cat 1)` | `Cost Performance` |
| `Cat 2` | `Schedule Simulation (Cat 2)` | `Schedule Simulation` |
| `Cat 3` | `Cost Simulation (Cat 3)` | `Cost Simulation` |
| `Cat 4` | `Document & Risk (Cat 4)` | `Document and Risk` |
| `Cat 5` | `System Dynamics (Cat 5)` | `System Dynamics` |
| `Cat 6` | `Signal Synthesis (Cat 6)` | `Signal Synthesis` |
| `Cat 7` | `Evidence Combination (Cat 7)` | `Evidence Combination` |
| `Cat 8` | `Governance & Compliance (Cat 8)` | `Governance and Compliance` |
| `Cat 9` | `Data Integrity (Cat 9)` | `Data Integrity` |
| `Cat 10` | `Decision Optimization (Cat 10)` | `Decision Optimization` |
| `PH` | `Portfolio Health: ML & AI (portfolio-scale, not a numbered category)` | `Portfolio Health: machine learning and artificial intelligence, at portfolio scale` |

The ampersand went with the number in three of them, because `NAMING_AUTHORITY.md` also rules
that user-facing text uses "and" and not the ampersand the code constants use. The `PH` label's
parenthetical was rewritten rather than deleted: it said something true about scale, and it said
it by contrast with a numbering scheme that no longer exists.

**Recorded plainly, because it changes what this correction is worth: `BRIEF_CAT_LABEL` is dead
code.** It is read nowhere in the repository. There is therefore no rendered DOM to read the new
labels back from, and none is claimed. The correction is asserted against the shipped bytes
instead, by `test_run28_participant_packages.py`, which requires that no label carrying the
retired scheme survives and that the ten replacements are present.

### 11.1 The sweep for other surviving instances of the scheme

`grep` over `assets/js/*.js`, `index.html` and `assets/*.html`. Reported, not acted on: §11 orders
`BRIEF_CAT_LABEL` corrected and the rest swept.

| file:line | instance | live on a surface? | acted? |
|---|---|---|---|
| `assets/js/deepdive.js:93-103` | `CAT_FROM_MODULE`, nineteen entries `"Cat 1.1"` … `"Cat 8.1"`, plus a fallback `"Cat " + key` | **YES**, rendered | **NO. `deepdive.js` is one of the six SEQUENCE-BEARING files.** Moving it needs its own owner's order and its own named exception record, exactly as Run 44 section 4.4 was for the flyout sentence. This run has no such order and did not ask for one. |
| `assets/js/charts3d.js:2542` | a chart node labelled `Synthesis\n(Cat 6)` | **YES**, rendered | **NO.** Not named by §11 and not a naming order this run holds. Recorded. |
| `assets/js/app.js:1298-1299`, `assets/js/categories.js:255,355,422`, `assets/js/deepdive.js:2168,2192`, `assets/js/neural_flow.js:174`, `assets/js/taxonomy.js:286` | `ex-"Cat 8"` and similar, inside **code comments** | no | **NO.** Comments are not user-facing text, and each records why a thing moved. Deleting them would destroy the record `NAMING_AUTHORITY` exists to keep. |

**The honest summary: one dead-code instance corrected, two live ones found and left, one of them
behind a sequence-bearing file that needs the owner's authority to touch.**

---

## 12. Merge

Branch `run47-evm-consistency-check`, four commits above `fe2e2df`, merged to `main` with
`--no-ff`. `main` pushed to `origin/main`. Nothing was squashed and nothing was force-pushed.
