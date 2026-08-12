Run 11 — Browser, Participant, Governance Cleanup

Starting commit: 68fe615
Ending commit: recorded below at the merge
Previous simulation version: sim-2026.08-v5
New simulation version: sim-2026.08-v6
Synthetic package version: v0.3 (unchanged, not re-ingested)
Browser/server single authority: PASS
Participant route verified: PASS
Seven neighbour defects fixed: 7/7
Defensibility claims corrected: 69/69 unqualified validation claims removed or qualified; 101 of 101 registered computations now carry a generated evidence record
Governed status label: Cost Recovery Status
Conflict semantics: NOT_ESTIMABLE_SINGLE_LINEAGE, shown as "Conflict: not estimable from one voting lineage"
Category-9 qualification: PARTIAL (audited and reported; no qualification object exposed, nothing fabricated)
Voting set: 2
Bucket-5 disabled: 2/2
Participant decision sequence changed: no
Participant-visible wording changed: yes
Production Postgres accessed: no
Full suite: 5981/5981 over 75 suites, confirmed on merged main

GATES COMPLETED: start gate, 1, 2, 3, 4, 5, 6, 8 (verification only), 9, 10, 11.
GATE NOT COMPLETED: 7 (Category-9 qualification) is audited and its gaps are reported, but no
versioned qualification object was built. Named as partial rather than claimed.

## 1. Handoff audit and repairs

Every completed session since the last recorded handoff is represented in `T6_HANDOFF.md`, and
no repair was needed. Checked by reading the file's own section headings against the committed
`REPORT_*` files and the Git history: Run 6 known-answer testing, Run 7 fix-now defects, Run 8
retest and classify, Run 5 export regeneration, the synthetic package ingest and the v0.2
re-ingest, Run 9 test-only synthetic integration, the v0.3 Monte Carlo and DSM correction, Run
10A production remediation, and Run 10B all have their own entry. The file is not in
chronological order, which is why an earlier reading appeared to be missing Runs 6 to 8; they are
present at lines 379, 285 and 160. The simulation version history is complete in
`server/app/simulation/models.py`: sim-2026.08-v2 through v5 are all preserved as historical
audit baselines with the reason each moved, and v6 is appended in the same shape. Nothing earlier
was overwritten.

The pre-change suite was run first and reproduced the recorded baseline exactly: **71 suites,
5627 of 5627**, which is what the Run 10B entry said the next session should record.

## 2. Browser and server computation inventory

`code_audit/run11_browser_server_parity.csv`, 101 rows, one per registered computation. 76 have a
browser implementation in `sim.js` or `simulations.js`; 25 have none.

The state of things at the start of this run was better than the gate assumed, and worse in one
specific way. index.html already loaded none of `sim.js`, `simulations.js` or `categories.js`:
the T6 Part 3 work removed them because a browser-side status computation produced false Red
statuses on healthy projects. What it left behind was five DORMANT CALL SITES in files the
participant route does load, each guarded by a presence check:

  - `signals.js` `ensureSimulations()` — `if (!window.LinSimulations) return;`
  - `signals.js` `runModels()` — an `if (window.LinSimulations) { ... }` recompute block
  - `signals.js` `runModels()` — an UNGUARDED `LinSim.buildSignals(...)` call, which on the
    participant route threw a ReferenceError from inside a live call site rather than saying
    anything a reader could act on. This is a real defect the gate surfaced.
  - `detail.js` `ensureEvidenceModules()` — a nine-module backfill grafted onto the snapshot the
    spider web renders
  - `ingest.js` — two entry points that already refused explicitly, and were correct

A presence check is not a refusal. It was never false only because of which files a page happens
to include, and a future edit that reloaded one of those files would have silently reactivated
arithmetic whose bands predate Run 7, Run 10, Run 10B and Run 11.

### Removed versus retained

**Removed from the live participant route**: every dormant recompute path above. Each is now
gated on `window.LIN_ALLOW_CLIENT_ANALYTICS`, an opt-in the application never sets, and the
unguarded `buildSignals` call is an explicit refusal that returns false, which is what its
callers actually need to know.

**Retained as historical test artefacts**: `sim.js`, `simulations.js` and `categories.js`, which
still load on `research/deepdive.html`. That page re-runs the models live so the working can be
watched, which is the point of it. It is not linked from the application and is not a participant
surface. The page comment now labels them as historical.

**Retained as presentation only**: `taxonomy.js`, `module_charts.js`, `detail.js`'s radar
geometry, `decision.js`'s palette. None computes a module result; all read the stored row.

### The version guard

`assets/js/client_algorithm_version.js` declares `client-legacy-2026.07-historical` as the stamp
of the arithmetic actually implemented in the browser files, and compares it with the
`simulation_version` on the stored result. Three outcomes: `current` only when both are present
and equal, `mismatch`, and `unknown` when the stored result carries no stamp. The two strings are
not equal and are not expected to become equal, so the deep dive shows a refusal naming both
stamps before it renders anything. That is the honest state: the browser arithmetic IS stale, and
the guard says so rather than letting it render as current.

### Parity tests

`server/tools/test_run11_browser_server_authority.py`, 61 checks. It deliberately does NOT
compare a browser band constant with a server band constant: that would assert against a
hand-maintained copy of the logic, and would pass the moment somebody kept both copies in step
while the divergence lived elsewhere. It asserts the stronger structural property — there is no
second arithmetic source on the participant route — by parsing index.html's real script list and
sweeping every file it loads for an ungated reference into the client model layer, with block and
line comments stripped so a truthful comment is still writable. Proved red against the pre-fix
code (57 of 61) and green after.

## 3. Parity changes

No server arithmetic was changed for parity. The change is entirely one-directional: the browser
stopped being able to compute. `code_audit/run11_browser_server_parity.csv` records, per module,
the browser path, the server path, the prior divergence, that the live browser computation is
removed, that the server value source is the stored `computed_results` row read through
`taxonomy.js`, and the parity test that holds it.

## 4. Real participant-route evidence

`server/tools/drive_run11_participant_route.py`, **52 of 52**, and
`code_audit/run11_participant_route_verification.csv`.

A real server, a real Chromium headless shell, a real signed-in participant session, a project
seeded from six document types across four periods and computed through `projectcomputeall`, then
the detail page opened through `LinApp.openDetail` and every collapsed section expanded.

**THIS GATE CAUGHT A REAL DEFECT, which is exactly why it exists.** The first drive found the
participant's conflict banner still reading "Mixed early warning" on a project whose server result
says the conflict is not estimable. The cause: `rowFor()` prefers the slim list projection, that
projection has never carried the new fields, and `getProjectFusion` did not fall back to the
primed full row. The same shape as a bug already documented in that file for `module_results`.
Corrected in `taxonomy.js` with a `pick()` fallback, re-driven, and the banner now reads
"Conflict: not estimable from one voting lineage". No suite would have found this: the server
was right, the file was right, and only the served page was wrong.

Also verified on the served page, which `tests_render.html` structurally cannot do because it
never loads index.html: `sim.js`, `simulations.js`, `categories.js` and `deepdive.js` are not
among the loaded scripts; `window.LinSim` and `window.LinSimulations` are `undefined`;
`LIN_ALLOW_CLIENT_ANALYTICS` is not set; the generated defensibility evidence object is present
and states platform-wide that nothing here is calibrated; no uncaught page error occurred; no em
dash appears on the ledger or the decision card.

### What was not driven, stated plainly

The full preliminary-decision, preliminary-lock, reveal, final-decision, final-lock, advance cycle
was NOT driven end to end. That needs a consented, profiled, assigned participant and an attached
research package, and this run did not build that fixture. What was verified in the browser is
that all five stage cards are present in the served page, in the fixed order, and that the reveal
is a control the participant presses rather than a timer. The order and the gating are
additionally asserted mechanically by the server suites. Recorded as PARTIAL in the CSV rather
than dressed up as complete. **This is the single largest remaining verification gap.**

## 5. Intentional abstention-display confirmation

The four Signal Ledger rows Run 10B changed from proxy findings to abstentions were reviewed on
the rendered page. Forty-three ledger lines state an abstention reason. No row disappears
silently. The string `(proxy:` appears nowhere on the ledger or the decision card. Six
remediation words were swept and none appears: remediation, defect, corrected, fixed in, was
wrong, previously reported. No abstaining row is described as voting. The settled owner decision
is what a participant actually sees, and it is not presented as a repair.

## 6. The seven neighbour defects

Derived mechanically from `code_audit/run10b_neighbour_findings.csv` — the rows with `fixed=no`,
which are exactly seven — and the suite fails if that set is not exactly the seven it tests.
Full detail in `code_audit/run11_neighbour_defects_fixed.csv`.

| Module | Defect class | Correction |
|---|---|---|
| A1.9 Budget Execution Rate | out-of-domain banding | actual cost and budget at or above zero, progress in 0 to 100 |
| A2.6 S-Curve Deviation | out-of-domain banding | both percentage-complete figures in 0 to 100, earned and planned value at or above zero |
| A3.9 Inflation Adjustment Index | out-of-domain banding | both material cost figures at or above zero |
| A3.9 Inflation Adjustment Index | missingness improved the reading | reported progress required; the unscaled-baseline substitution removed |
| A5.2 Sensitivity Analysis | missingness improved the reading | document risk required and domain-checked; the `or 0` default removed |
| A5.3 Tornado Risk Ranking | out-of-domain banding | document risk in 0 to 1, indices above zero, progress figures in 0 to 100 |
| B3.2 FAR Threshold Monitor | out-of-domain banding | the existing zero refusal widened to at or below zero |

Five are out-of-domain banding and two are missingness improving the reading. No band moved, no
threshold was introduced, and every domain was derived from what the quantity IS — money spent is
not negative, a percentage complete is a share of the work, a performance index is a ratio of two
non-negative quantities — not from where the bands sit. Where a domain already existed elsewhere
for the same field it was reused verbatim: document risk in 0 to 1 is the domain the
conflict-density module has enforced since Run 10, and an index above zero is the domain
variance at completion has stated since Run 4.

All seven were and remain non-voting.

`server/tools/test_run11_neighbour_defects.py`, **121 checks**. Two independent properties rather
than seven hand-written expectations: domain closure, checked by 200 randomised out-of-domain
draws per field per module plus the exact recorded reproducer; and missingness never being an
improvement, checked by deleting and by nulling each required field. Domain edges are checked to
remain INSIDE the domain, so a guard that silenced the module altogether would fail. The mutation
proof executes each module file out of the pinned commit `68fe615` in its own namespace and
requires the shipped pre-fix function to band the reproducer Green while the corrected one
abstains, with the two sources asserted to differ first.

## 7. Defensibility claim audit

`code_audit/run11_defensibility_claim_audit.csv`, 101 rows, with the nine statuses separated:
implementation, known-answer verification, boundary test, band source, calibration, empirical
validation, canonical structure, voting, permitted claim and qualification.

**Before: 69 of 103 handbook entries stated that a module HAD BEEN VALIDATED.** Run 6 measured
this and reported it rather than editing it, because the handbook's content was the owner's
decision at the time; that check has been restated to assert the overclaim is gone, with Run 6's
original finding preserved as the reason it exists.

**After: zero.** Each such sentence now says what validation for that method WOULD consist of,
that none of it has been performed here, and what the repository actually holds instead. Two
calibration overclaims were corrected the same way. Three front-matter sentences that claimed
every capability was validated were rewritten.

Counts by permitted claim: 65 modules may say "Arithmetic independently verified for the stated
formula" because a known-answer case exists for them; 28 may say only that they are implemented
as stated, with no independent verification held; 8 are disabled and claim nothing.

`assets/js/ds_defensibility_evidence.js` is GENERATED by
`tools/build_run11_defensibility_evidence.py` from the registry, the canonical-structure layer,
Run 6's own coverage set and the committed audit CSVs. The suite re-runs the generator and
compares byte for byte, so a hand edit to the generated file fails.
`server/tools/test_run11_defensibility_claims.py`, **128 checks**, including three fault
injections: an unsupported "Validated by field comparison" claim, an "empirically calibrated"
claim, and a hand edit to the generated evidence object. All three go red.

The audit pattern carries a negative lookbehind, and it is not a loophole: "It is not a calibrated
forecast" is the correction, not the defect, and a pattern that flagged it would force the
handbook to stop saying what a module is NOT, which is the most useful sentence on the page.

## 8. Project-status naming

Both voting modules sit in registry category A1, Cost and EVM Performance. A rollup of the
to-complete cost efficiency and the variance at completion says whether the remaining budget can
still carry the remaining work. It says nothing about schedule, quality, document evidence,
procurement or safety.

The governed rollup is therefore labelled **Cost Recovery Status**. This is a display string
derived by `fusion.governed_status_semantics` from the voting lineages as they actually stand: if
a second lineage ever votes, the label widens by itself. No code constant was renamed —
`project_status` is still `project_status` — and Group A is still called Project Health, because
that is the name of a group of 53 modules and not of this rollup. No unrelated project-health
concept was touched.

## 9. Conflict semantics

With one voting lineage, `dst_fuse` never performs a genuine combine and returns K = 0.0. The
suite establishes exhaustively over the status vocabulary that **no genuine two-source combine
produces zero**: the calmest is two identical Greens at K = 0.309. So a published zero could only
ever mean nothing was combined, and beside a status it reads as a stronger absence of
disagreement than two real sources can achieve. It is not a calm reading; it is not a reading.

`project_conflict` is now `None` under one lineage rather than `0.0`, the state
`NOT_ESTIMABLE_SINGLE_LINEAGE` is published beside it, and the participant-visible sentence is
"Conflict: not estimable from one voting lineage". No conflict score was manufactured. With two
or more lineages the genuine coefficient is published exactly as before.

Derived at read time from the `category_statuses` every stored result already carries, by the
same function the compute path uses, so no column was added and **migrations 0020 through 0025
remain unapplied**. A row stored before this run answers exactly as one stored after it.
Verified on the fusion layer, the compute path, the read path, the API response the participant's
own session receives, and the rendered banner.

## 10. Category-9 qualification — PARTIAL, and the gap is reported rather than filled

`code_audit/run11_category9_qualification.csv`, 101 rows. Of the six questions the gate asks:

  - **required input present** — KNOWN. Every module declares its inputs through `check_inputs`
    and abstains with `missing_required_input`.
  - **required canonical structure present** — KNOWN, enforced by `canonical.py`.
  - **reporting-period applicability** — KNOWN. `period_cutoff` bounds every computation and
    nothing in the layer reads the system clock.
  - **provenance known** — PARTLY. `signal_inputs.sources` records a document TYPE per field,
    never a document identity or version, so a field cannot be traced to the artefact that
    produced it.
  - **evidence current enough** — PARTLY. C1.2 measures document age against the cutoff, but
    there is no per-field as-of date, so a stale field inside a current period is undetectable.
  - **required revision resolved** — NOT AVAILABLE. Document versioning exists at the document
    level and is not joined to the field a module reads.

**No versioned qualification object was built and nothing downstream consumes one.** Building the
three missing pieces would require evidence structures the repository does not hold, and inventing
them is the failure mode the gate names. Category 9 remains non-voting and excluded from the
category rollup. This gate is honestly PARTIAL.

## 11. Participant-sequence regression

The sequence is unchanged: evidence, preliminary decision, preliminary lock, AI reveal, final
decision, final lock, next period. No assignment order, locking rule, reveal timing, response
field, consent flow or session progression was touched. Verified in the served browser that all
five stage cards are present and in order and that the reveal is participant-initiated;
`test_pre_lock_guard.py` (20 of 20) and the research suites hold the gating mechanically. Every
wording change in this run is confined to status, abstention, conflict and defensibility
representation.

## 12. Voting and activation proof

`CORE_VOTING_MODULES` is exactly `{A1.7, A1.8}`, asserted in two Run 11 suites and unchanged from
Run 10B. None of the seven fixed neighbour modules became voting; each is asserted individually.
Bucket-5 remains two disabled modules. The integrated Bucket-3 and Bucket-4 modules remain
non-voting. Recommendation text, courses of action and the decision card all read the same
`category_statuses` rollup, which only voting modules enter, so no non-voting module can reach
them.

## 13. Test mutation and fault-injection proof

Every new check was proved able to fail, and every injection was asserted to have altered bytes
or behaviour before its red was believed.

  - Gate 1: four injections — loading `simulations.js` on index.html, removing the opt-in gate,
    claiming the server's simulation version for the client arithmetic, removing the comparison
    call from the deep dive. Additionally the whole suite was run against the pre-fix working tree
    and went red at 57 of 61.
  - Gate 3: five pinned-baseline comparisons executing the shipped pre-fix functions out of commit
    `68fe615`, each required to band its reproducer Green while the corrected function abstains;
    plus two missingness comparisons proving the pre-fix function moved Red to Amber and Red to
    Yellow on the same inputs.
  - Gate 4: three injections — an unsupported validated claim, an unsupported calibration claim,
    and a hand edit to the generated evidence object.
  - Gate 6: zero conflict published under one-lineage voting, and an "Overall Project Health"
    label under one cost lineage. Both detected.

## 14. Version transition

sim-2026.08-v5 to **sim-2026.08-v6**, because the seven corrections change what the analytical
layer emits. Every earlier stamp is preserved in `models.py` with the reason it moved. Four
suites that track the current stamp were updated and the check that every earlier stamp survives
is unchanged and still green.

## 15. Complete-suite results

  - Pre-change baseline: 71 suites, **5627 of 5627**
  - Final, on MERGED MAIN: 75 suites, **5981 of 5981**, ALL SUITES GREEN, each against its own
    freshly migrated database
  - `tests.html` **51 of 51**; `tests_render.html` **286 of 287**, the one non-pass being check
    264's requirement for a signed-in session token, which is the same non-pass Run 10B recorded
  - Four new suites: `test_run11_browser_server_authority.py` (61),
    `test_run11_neighbour_defects.py` (121), `test_run11_status_and_conflict.py` (39),
    `test_run11_defensibility_claims.py` (128)
  - Browser drive: `drive_run11_participant_route.py`, **52 of 52**
  - Five earlier suites restated, every original finding preserved as the reason for the
    restatement and none deleted or loosened: `test_run6_known_answer.py`,
    `test_run8_retest_classify_27.py`, `test_run10_state_protection.py`,
    `test_run2_fifteen_defects.py`, `test_run4_validate_seven.py`
  - `run_all_suites.sh` was not loosened. It still accepts only an anchored
    `^RESULT: N/M( checks passed)?$` and still fails on a nonzero exit code.

## 16. Guarantees

**Verified.** Live browser arithmetic no longer diverges from authoritative server results, and
cannot silently return. The actual participant route was driven and verified. The approved
canonical abstentions are truthful on the page. All seven remaining neighbour defects are
corrected. Unsupported validation and calibration claims are removed or qualified, and the
replacement is generated rather than hand-authored. The governed status wording matches the
actual voting lineage. One-lineage conflict is not represented as independent agreement. The
voting set did not expand. Bucket-5 remains disabled. The participant decision sequence is
unchanged. Every new check was proved capable of failing. The full suite passes on merged main.

**Partly met.** Category-9 qualification: audited, three of six questions answerable, gaps
reported, nothing fabricated, no object exposed. The participant decision sequence: verified for
structure and order in the served browser, not driven through a full lock-reveal-lock cycle.

**Not met.** Nothing in the acceptance criteria is unaddressed, but Gate 7's constructive half was
not built.

## 17. Remaining owner decisions

  1. Whether to build the evidence structures Category 9 would need — per-field provenance
     identity, per-field as-of dates, revision resolution — or to accept the qualification gap as
     a stated limit.
  2. Whether a full participant decision-sequence browser fixture should be built, which would
     require a seeded consent, profile, assignment and research package.
  3. Whether "Cost Recovery Status" should also replace any wording in the exported workbook and
     the Methods tab, which this run left alone because neither presents the governed rollup under
     a health claim.
  4. Carried forward from Run 10B and still open: whether to register the bottom-up cost-risk
     family as its own module; the dead control-chart penalty in the forecast module; the registry
     canonical name reading "Monte Carlo EAC" against the programme's "Monte Carlo EAC Forecast";
     and the audit artefacts rewritten by their own suites on each run.

## 18. Exact final-refreeze requirements

  1. Run the complete suite first and record **75 suites and 5981 checks** as the baseline.
  2. Re-run `drive_run11_participant_route.py` and require 52 of 52.
  3. Close Gate 7 or record the qualification gap as an accepted stated limit.
  4. Build the full decision-sequence browser fixture, or record that gap as accepted.
  5. Re-run `tools/build_run11_defensibility_evidence.py` and confirm the committed file is
     unchanged, which is what proves the claims still match the registry.
  6. Confirm the voting set is still exactly two and Bucket-5 still two disabled.
  7. Do not reopen the seven neighbour corrections, the Gate 1 refusals, the Cost Recovery Status
     label or the single-lineage conflict semantics unless a regression test proves one is broken.
