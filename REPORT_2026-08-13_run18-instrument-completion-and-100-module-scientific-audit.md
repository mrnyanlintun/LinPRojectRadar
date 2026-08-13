Run 18 — Instrument Completion and 100-Module Scientific Audit
Starting commit: 1c07fed
Run-17 merge commit: 1c07fed
Corrected UI baseline commit: SEE SECTION 8
Ending merge commit: SEE SECTION 8
Run-16 handoff corrected: YES
Run-17 handoff corrected: YES
FINAL FLOW empty-project truthfulness: PASS
Clear-all same-session state: PASS
Clear-all post-reload state: PASS (proved in a fresh document; see section 4)
One-document selective activation: PASS
Project-switch state isolation: PASS
Signal navigation rail present: PASS
Obsolete collapse/hide control absent: PASS
Signal navigation functional: PASS
Material Cost Variance registered: YES
Material Cost Variance operationally disabled: YES
Material Cost Variance voting: NO
Material Cost Variance excluded from result rows: YES
Previously assessed modules re-executed: 21/21
Prior scientific results preserved or reconciled: 21/21
Previously unreached modules assessed: 0/79  (STOP CONDITION HIT, see section 10)
Final scientific-result rows: 100/100
NOT_REACHED_IN_THIS_RUN remaining: 79
Voting set: 2
Expected voting set: 2
Concept-only methods activated: 0
Full suite: 7207/7207 across 88 suites
Production Postgres accessed: NO



---

## 0. What this run establishes, in one paragraph, before any detail

Run 18 completed the instrument work and the baseline freeze, re-executed the twenty-one
modules Run 17 had assessed, and then **stopped the scientific audit of the remaining
seventy-nine rather than inventing evidence for them.** The reason is specific and is proved
mechanically in section 10: the controlling theoretical contract those seventy-nine assessments
require does not exist in this repository. Run 18 therefore reports **21 of 100 assessed and 79
still outstanding**, which is the same count Run 17 reported, and it does not round that
uncertainty into a disposition. The instrument half of the run did complete, and it closed a
proof gap Run 16 had left open.

## 1. Handoff and history correction

**Run 16 is recorded as PARTIAL.** Its own report already said so, and Run 18 confirms the
reason from the current real browser route rather than from the record. Run 16 did the
substantive work correctly: the Signal Flow column headers now separate registered architecture
from current project activity, and `w_resetsignals` invalidates the derived server row. What
Run 16 could not do was prove the post-clear-all reloaded state from the page. It recorded that
honestly, in source, as a container fact.

**That container fact was wrong, and Run 18 corrects it.** Run 16's driver states that "there is
no way to reload the served page inside this container that returns in reasonable time". Run 18
isolated the variable in a probe that changed nothing else and measured a reload returning in
**0.6 seconds**, with a pre-reload sentinel on `window` gone afterwards, which no same-document
operation can produce. The cause was a wait condition, not the container: `page.reload()`
defaults to waiting for `load`, and `load` never fires on this page because the aborted sign-in
script and the CONNECT-refused tile host leave requests outstanding for the life of the
document. The initial navigation in Run 16's own driver already avoided this by waiting for
`domcontentloaded`; only its reload path did not.

The correction is narrower than a simple reversal, and section 4 states the residual limitation
precisely rather than claiming more than was measured.

**Run 17 is recorded as closed and honest.** 21 of 100 assessed, 79 not reached, production
algorithms unchanged. Run 18 re-executed its suite and confirms all three claims. No Run 17B
exists. Run 17's anti-fossilisation register is preserved and none of its findings became a
passing assertion in this run.

**Two further harness facts** were measured while isolating the reload and are recorded so no
later session rediscovers them. `page.add_init_script` re-runs on the reloaded document and was
observed to stall the reload navigation here. And two drivers must not share a port: a second
uvicorn silently fails to bind, every request then lands on the first driver's server and
database, and the symptom presents as an authentication failure during seeding, which is a
misleading place to start debugging.

## 2. Module identity reconciliation

Reproduced mechanically by `server/tools/run18_scope_reconciliation.py`, 17 of 17 checks, output
in `code_audit/run18_scope_reconciliation.csv`.

The registry declares 101 live rows: 96 project-level and 5 portfolio. Removing Material Cost
Variance leaves 95 project-level, plus 5 portfolio, giving **100 scientific targets with 100
unique canonical identifiers**. The committed Run-17 matrix covers exactly that population, with
an empty symmetric difference. Its assessed and not-reached subsets are disjoint, their union is
the whole population, and **21 + 79 = 100**.

Identity is derived from `new_id` with the group letter mapped to the category number, and is
reconciled by module name against the 101-name specification, so a registry edit that broke the
mapping would fail loudly rather than silently renaming modules. `old_id` was not used: two
retired alias rows displace every later identifier by one, so `old_id` 3.4 is Labor Productivity
Index while the canonical key 3.4 is Material Cost Variance, and an exclusion driven off
`old_id` would have excluded the wrong module and executed the one the owner disabled. The check
that key 3.4 resolves to Material Cost Variance is asserted explicitly. Identifiers are strings
throughout, and the guard still detects all five pairs that float coercion would merge:
1.1/1.10, 2.1/2.10, 4.1/4.10, 7.1/7.10 and 7.2/7.20.

## 3. Run-16 website root-cause findings

The Signal Flow column headers and the clear-all server invalidation were already correct in the
inherited baseline, and Run 18 re-proved both from the served page. Run 16's work stands.

**A new defect was found, and it was found precisely because Run 18 closed Run 16's proof gap.**
Driving a fresh document at a cleared project, rather than only the session that performed the
clear-all, showed the cleared project reporting **24 UPLOADED ON THIS PROJECT** and lighting
**24 active document-to-module evidence paths**, while correctly reporting zero modules with a
current result, zero estimable categories and a status of not estimable.

**Root cause: MULTIPLE_CAUSES, with the governing cause STALE_SERVER_STATE consumed without a
reset boundary.** It is not BACKEND_DEFAULT_RESULT and not CACHE_INVALIDATION. The chain is:

1. Run 16 deliberately stopped the reset from deleting the project event log, for reasons
   recorded in `writes.py`. Deleting it destroyed audit history and took Audit Trail
   Completeness from 100 per cent to zero on a project whose trail was intact. Instead the reset
   **appends** a `signals_reset` entry. That decision was correct and is preserved.
2. Nothing in the Signal Flow diagram was taught to notice that entry. It counted every
   `signals_extracted` event the project had ever recorded, so a cleared project still read as
   holding all of its documents.
3. It was invisible in the session that performed the clear-all only because `detail.js`
   forcibly zeroes `p.events` on the in-memory copy afterwards. **That is a browser-side mask
   over a record the server still serves**, which is the thing the owner's clear-all requirement
   specifically prohibits.

**The fix** reads the event log from the last `signals_reset` onward, in `neural_flow.js`, for
both the uploaded-document count and the set of uploaded document types. No event is hidden or
deleted; the audit panel and the Uploaded Documents table still read the whole log, and Audit
Trail Completeness is untouched. The browser-side mask is left in place because it is now
harmless, and the page's truthfulness no longer depends on it.

This is authorized production change A, FINAL FLOW empty-project and clear-all truthfulness. It
is the only production change Run 18 made.

## 4. Empty-project and clear-all evidence

`server/tools/drive_run18_final_flow.py`, driving the served page in headless Chromium,
**87 of 87 checks**, facts in `code_audit/run18_browser_facts.csv` and screenshots alongside.
All six owner states were driven through real application routes against a throwaway database.

For each of the empty project, the cleared project in the same session, the cleared project in a
fresh document, and the empty project reached by switching, seven separate properties are
asserted: uploaded documents zero, executed module paths zero, active category-result paths
zero, no evidence path animated, no path marked active, no fabricated Cost Recovery Status, and
registered architecture still visible but labelled as architecture. The populated project
reports its own figures and animates its own paths, so the checks are not passing vacuously.

**The confirm-dialog proof.** The container's `window.confirm` returns false, so a confirm-gated
action silently no-ops and a test that merely checks the click did not throw would report green
for an operation that never ran. Run 18 did not trust the source comment claiming the control is
ungated. It instrumented `window.confirm` in the page to count calls and returns, registered a
Playwright dialog handler that accepts, and recorded both. Measured: **zero `window.confirm`
calls during the clear-all, zero native dialogs raised, zero suppressions.** The clear-all is
genuinely ungated, and the preamble's carried-forward assumption that it is confirm-gated is
false for this baseline. Because the absence of a dialog is not by itself proof that anything
happened, the operation is additionally proved by its effect at the authoritative layer: the
server's live derived row is `True` before the click and `False` after it.

**The residual harness limitation, stated exactly.** `page.reload()` commits a navigation
immediately, and an isolated probe reloads a freshly opened page in 0.6 seconds with the
sentinel gone. On a page that has been driven through the application routes, the clear-all and
the WebGL panels, the reloaded document does not settle: every evaluate for ninety seconds fails
with "Execution context was destroyed", which is repeated navigation rather than one slow load.
Run 18 therefore proves the post-clear-all state in a **brand-new page** in the same browser and
session. That is a stronger test of the property the owner cares about, not a weaker one: a
fresh document holds no in-memory application state at all, so everything it draws it obtained
from the server, and it is exactly where surviving stale state would reappear. It is also the
document that exposed the defect in section 3.

## 5. One-document control

With exactly one recognised document the header reads **1 UPLOADED ON THIS PROJECT**, and
**71 of the populated project's 100 evidence paths** activate. Activation is selective rather
than all-or-nothing, and the assertion is written as a strict inequality against the populated
project's own count in the same run, so it cannot pass by both being zero.

## 6. Signal-rail correction

**No production change was required, and none was made.** The obsolete grey collapse control
does not exist on this route in this baseline, which Run 16 also found. Run 18 re-proved it with
a **stricter** reader than Run 16 used.

Run 16's sweep filtered candidates to those with a non-zero rendered box, so a control hidden by
opacity or a zero-size box would have escaped it. Run 18's reader walks every element in the
document, matches any interactive element whose entire own text is one to three chevron or pipe
glyphs, or whose accessible name, title, class or id names a collapse or hide action on the
rail, and **applies no visibility filter at all**. It records opacity, display and visibility for
anything it finds, so a control with opacity zero and a live hitbox would be reported.

**Nothing was found, in any state, at any width.** The sweep covers the empty project, the
populated project, the one-document project, the cleared project in the same session, the
cleared project in a fresh document, the switched-to empty project, and desktop widths 1280,
1440, 1680 and 1920. In every case the rail is present in the DOM and visible, carries ten
numbered entries, **every numbered link resolves to a real section target**, the page remains
scrollable, and the rail does not push the page into horizontal overflow. The pre-existing
mobile breakpoint that hides the rail below 700 pixels is untouched.

## 7. Material Cost Variance state

`server/tools/test_run16_material_cost_variance_disabled.py`, **78 of 78 checks**, re-executed
on this baseline. Read from the live registry: canonical registry identity retained; audit
history retained; `DISABLED_EVIDENCE_UNDER_REVIEW`, which stays deliberately distinct from the
eight concept-only modules' `DISABLED_UNSAFE`; non-voting; no contribution to Cost Recovery
Status, recommendations, courses of action or the participant decision card; no browser-side
reactivation; and excluded from the 100 result rows, asserted in the Gate 1 reconciliation.

Run 16 had in fact completed the operational disablement, so nothing was completed here. The
reason remains EVIDENCE AND CONTEXT REQUIREMENT UNDER OWNER REVIEW. **It is not described as
mathematically disproved, and Run 18 did not execute its scientific method.**

## 9. Re-execution of the prior 21

`server/tools/test_run17_scientific_methods.py`, **250 of 250 checks**, re-executed against the
corrected baseline. Per-module record in `code_audit/run18_prior_21_reexecution.csv`.

For each of the 21: the same canonical specification, the same oracle, and the same scientific
disposition. **No analytical result moved.** That is the expected outcome and it was verified
rather than assumed, because the only production change in this run is a presentation-layer read
of the event log in `neural_flow.js`, which no analytical module consumes. Had any analytical
result moved, the instruction was to stop that module and explain why a supposedly
presentation-only change reached it; that did not arise.

The Run-17 anti-fossilisation register is preserved intact. Every Run-17 finding remains a
finding: the synthesis implementation defects, the method-label mismatches, the proxy
implementations, the calibration-pending modules, the missing Category-9 enforcement, the absent
lineage identifiers, the portfolio composite's dependency and re-weighting concerns, and the
Isolation Forest small-cohort limitations. **None was remediated in Run 18, and none became a
passing assertion.**

## 10. The remaining 79 — STOP CONDITION HIT

**Run 18 did not assess any of the 79. It stopped rather than invent evidence.** The honest count
is therefore **21 of 100 assessed and 79 outstanding**, unchanged from Run 17.

The blocker is specific, and it is proved mechanically by `server/tools/run18_build_artifacts.py`
rather than asserted: **0 of the 79 have any committed theoretical contract.**

Gate 7 names the controlling authority as "the complete committed Run-17 supervisory
specification". **That artifact is not in this repository.** Run 17's own source ledger records
it as source S1 with retrieval status `SUPPLIED_IN_PROMPT`. It was not supplied to Run 18. The
79 outstanding entries in `method_cards.json` are empty stubs: no declared method, no primary
source, no formal definition, no oracle.

The only in-repository documents describing these 79 methods are
`code_audit/GROUP_A..D_*.md`. **Those are regenerated exports of the registry and embed the
production function bodies verbatim.** Using them as the theoretical contract would be
reconstructing the theory from production code, which Gate 7 prohibits in terms, and would
reproduce exactly the failure mode Run 17 built the anti-fossilisation register to prevent:
asserting a method against a copy of its own implementation. Five suites were previously found
encoding a defect as expected behaviour by that route.

The owner's stop condition applies as written: **a method lacks an independently defensible
theoretical contract.** The 79 rows therefore stay at `NOT_REACHED_IN_THIS_RUN` rather than
being rounded into a disposition, and no module is marked assessed on a shallow read.

Consequently **Gates 8, 9 and 11's scientific fault campaign are also not advanced for these
modules**, and Category 8, Category 10 and the seven Category-9 modules remain unassessed.
Category 8 remains UNASSESSED rather than cleared, and absence of a finding is not a clean bill.
The Category-9 and lineage findings that DO exist are architectural, carried unchanged from
Run 17 and re-executed here: the ensembles consume assembled signal statuses with no
qualification step between raw evidence and synthesis, and no module result carries a lineage
identifier, so a second transform of the same adverse cost index raises the adverse count.

**Committing the supervisory specification is the single highest-value item in the Run-19
queue.** Without it no further scientific assessment is defensible, and with it the remaining 79
resume cleanly: `findings.py` is keyed by module identifier and every unreached row is already
stubbed, so a follow-up adds entries and re-runs `build_artifacts.py`.

## 11. Final table and disposition distribution

`code_audit/run18_final_100_reconciliation.csv`, 100 rows, 100 unique canonical identifiers,
0 blank dispositions. All headline counts derive from the CSV.

| Disposition | Count |
| --- | --- |
| NOT_REACHED_IN_THIS_RUN | 79 |
| METHOD_PASS_CALIBRATION_PENDING | 7 |
| METHOD_LABEL_MISMATCH | 4 |
| CORRECT_PROXY_ONLY | 3 |
| IMPLEMENTATION_DEFECT | 3 |
| SCIENTIFIC_PASS | 2 |
| MISSING_CANONICAL_DATA_STRUCTURE | 1 |
| OWNER_DECISION_REQUIRED | 1 |

Material Cost Variance is recorded separately and is not one of the 100 rows: REGISTERED;
TEMPORARILY DISABLED; EXCLUDED BY OWNER DECISION; NOT PART OF THE 100 ROWS.

**Run 18 did not reach 0 NOT_REACHED, and does not claim to.** The definition of done is not met
for the scientific half of the run, and section 10 states why.

## 25. Fault injection and harness integrity

Run 17's ten-fault scientific campaign was re-executed inside
`test_run17_scientific_methods.py` as part of its 250 checks, and is recorded in
`code_audit/run18_fault_injection_results.csv`. Each fault altered bytes or execution, produced
a named red failure, occurred in a controlled mutation harness, was restored, and returned
green: wrong Earned Schedule interpolation, Dempster ignorance converted to conflict, a
dominated Pareto point admitted, a queue denominator operator error, an Isolation Forest
exponent sign, a Pythagorean admissibility violation, a wrong linear-programming optimum, a
regulatory version mismatch, a Category-9 raw-input bypass, and a seed perturbation.

Harness integrity holds. `run_all_suites.sh` accepts only an anchored
`^RESULT: N/M( checks passed)?$`, rejects prose summaries, and fails on a nonzero exit code, so
the four known lies remain detected: a prose-only "all passed", a reported failed count, a green
RESULT line accompanied by a nonzero exit, and a silent crash that prints no result line at all.

**The remaining faults Gate 11 names are NOT complete**, because they belong to modules in the
outstanding 79. No claim is made about them.

## 26. Production hash proof

`server/tools/run18_production_hashes.py` covers **143 production files** across `server/app/`,
`assets/`, `p0-baseline/` and `index.html`.

Exactly one production file differs from the Run-17 merge commit: `assets/js/neural_flow.js`,
the authorized change A described in section 3. Everything else is byte-identical. The manifest
was re-frozen after that change, and every subsequent audit-only commit is verified against the
frozen bytes rather than against whatever the latest commit happens to contain.

No production Postgres was accessed, no production credential was used, no production migration
was applied, nothing was deployed, and no real participant or confidential project data was
touched. Every run used a throwaway SQLite database migrated from scratch. Migrations 0020
through 0025 remain unapplied. No audit fixture entered operational storage.

## 27. Voting and activation proof

Read from the live registry, not from a copy: the voting set is **exactly two**, TCPI and
Variance at Completion. The **eight** concept-only methods remain operationally disabled. No
concept-only module appears in the voting set. Material Cost Variance is
`DISABLED_EVIDENCE_UNDER_REVIEW` and non-voting. **Concept-only methods activated: 0.** The
voting set was not expanded and no disabled method was reactivated.

## 28. Complete suite

**88 suites, 7207 of 7207 checks, all green**, each against its own freshly migrated database,
with the production change in place. Plus the browser drive at 87 of 87, the scope
reconciliation at 17 of 17, the Material Cost Variance state at 78 of 78, and the production
hash and registry invariants at 11 of 11.

## 29. Owner decisions

Every decision Run 17 surfaced remains open and none was made here. In addition Run 18 surfaces
one new decision, which is a prerequisite rather than a preference: **whether to commit the
supervisory method specification to the repository.** Until it exists there, no scientific
assessment of the remaining 79 is defensible, and any run attempting one would be reconstructing
theory from the production code it is supposed to be auditing.

## 30. Run-19 remediation queue

`code_audit/run18_run19_queue.csv`. Ordered as the owner specified.

**P0-PREREQUISITE, ahead of everything else: commit the supervisory method specification, or
supply an independently defensible per-module theoretical contract.** This blocks 79 of 100
modules.

- **P0A voting and status defects:** none found.
- **P0B scientifically invalid favourable or adverse output:** the ensemble that absorbs a
  single Red rather than escalating it; the ensemble in which benign evidence dilutes an adverse
  rollup; and the portfolio composite that re-weights on availability, so a project with fewer
  supplied inputs is scored on a different basis than one with more.
- **P0C regulatory or governance overclaim:** none found, and Category 8 is UNASSESSED rather
  than cleared.
- **P0D Category-9 bypass and evidence-lineage double counting:** the ensembles consume
  assembled signal statuses with no qualification step before synthesis, a deviation declared in
  code rather than prevented; and no module result carries a lineage identifier, so a second
  transform of the same adverse cost index raises the adverse count and a duplicate
  transformation manufactures independent corroboration.
- **P1:** nothing beyond P0B.
- **P2:** the one missing canonical data structure.
- **P3:** unsourced Beta-PERT distribution parameters; CUSUM and Isolation Forest operating
  points calibrated on synthetic data only; the four unversioned Category-6 ensemble bands.
- **P4:** the four naming, proxy-disclosure and parsimony items, including the collapsing
  worst-of aggregation that makes one ensemble redundant with another.
- **FUTURE:** the eight concept-only methods, none of which has demonstrated incremental
  research value. No activation is proposed.

One item is added from this run's own work: **a headless regression asserting the event-log
reset boundary.** The property is currently held by the browser driver, which is deliberately
outside the `test_*.py` glob because it needs Chromium. It should also be held by a suite that
runs without a browser.

## 31. What Run 18 establishes, and what it does not

**It establishes**, from the served page in a real browser through real application routes: that
a project with no evidence states that plainly and animates nothing; that registered
architecture is labelled as architecture and never presented as project activity; that a
clear-all invalidates state at the authoritative layer and that the page tells the truth about
it both in the session that performed it and in a document that never saw it; that one document
activates only what it supports; that switching projects does not carry figures across; that the
Signal navigation rail is present, complete and functional at every supported desktop width and
that the obsolete collapse control is absent from the DOM entirely rather than merely invisible;
that Material Cost Variance is registered, disabled, non-voting and excluded; that voting is
exactly two and the eight concept-only methods are disabled; and that the 21 modules Run 17
assessed re-execute unchanged against the corrected baseline with no analytical result moved.

**It does not establish anything about the remaining 79 modules.** They are not passing, not
failing, and not cleared. They are unassessed, for the specific and documented reason that their
controlling theoretical contract is not in this repository. Absence of a finding is not a clean
bill. Category 8 in particular is unassessed, so nothing in this run should be read as saying
the instrument's regulatory modules check anything correctly, and no rule check anywhere in the
instrument is called legal compliance.

**It does not establish empirical validity for any module.** Implementation verification is not
empirical validation, and synthetic known-answer success is not field validity. Every calibration
in the instrument that has a calibration at all rests on synthetic data.

**Run 18 did not meet its own definition of done.** The instrument half is complete; the
scientific half is not, and section 10 says exactly why rather than rounding the gap away.
