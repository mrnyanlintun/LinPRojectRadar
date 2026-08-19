# Run 38: controlled-study execution readiness and research-data pipeline qualification

**Date:** 2026-08-19
**Disposition:** `STUDY_EXECUTION_READY`
**Blocking defects:** 0
**Frozen behaviour changed:** NO

---

## 1. Frozen instrument identity

| | |
|---|---|
| freeze candidate | `6142d877856ea651ef8d7e905f6d27604b3244f1` |
| accepted release | `f983bb020f7a184a5742e1fff09d690b0170f0de` |
| freeze disposition | `FINAL_FREEZE_ACCEPTED` |
| simulation | `sim-2026.08-v25` |
| participant package | `og-participant-2026.08-v13` |
| synthetic package | `OG-SYNTH-0.6` |
| governed study contract | `OG-STUDY-DESIGN-2026.08-v1` |

Every one of these was re-verified from the repository at the start of the run, not inherited.

## 2. No scientific modification was permitted, and none occurred

Run 38 may not modify scientific formulas, module qualification, the Category-9 gate, the
Category-10 authority boundary, voting, controlled stimuli, the participant decision sequence,
AI outputs, project/period ordering, participant-facing treatment, or frozen client behaviour.

`server/tools/test_run38_frozen_immutability.py` proves this **by diff, not by assertion**
(16/16):

- every file named by `research/freeze/INSTRUMENT_FINAL_FREEZE_CHECKSUMS.csv` is byte-identical
  to the accepted release;
- `assets/`, `server/app/`, `research_fixtures/synthetic/` and `index.html` are byte-identical
  to freeze candidate `6142d877`;
- **Run 38 modified zero pre-existing files.** Every change against the release is an addition.

A distinction the gate measures rather than glosses: eight files differ between the *candidate*
and the *release*. They are Run 37's own audit artifacts and freeze bookkeeping, published on
top of its candidate. The gate attributes them to that interval explicitly and confirms none is
inside an executable frozen surface.

## 3. The actual participant state machine

Derived by driving the live `/exec` routes, not by encoding the methodology list.
`code_audit/run38_participant_state_machine.csv` — 9 transitions, all PASS.

| methodological step | live implementation |
|---|---|
| 1 controlled evidence review | `researchevidenceget`; evidence resolved from `scenario.evidence_package_id`, or from the participant's own prior transition's `next_state_id` from P2 on |
| 2–3 preliminary assessment, action, confidence | `researchprejudgment` (`pre_action`, `pre_confidence`, `pre_assessment`) |
| 4 preliminary lock | **the same INSERT.** `pre_submitted_at`, `pre_locked_at` and `pre_judgment_locked` are written in one statement; there is no window in which an unlocked judgment exists |
| 5 AI reveal | `researchreveal`; refuses unless locked; copies `package_hash` onto the decision |
| 6–9 final action, confidence, disposition, evidence, rationale | `researchdecision`, one transition |
| 10 final lock | **`final_submitted_at` being non-null IS the lock.** There is no separate flag |
| 11 advance | `researchadvance` within a scenario; **the move to the next scenario is implicit** — the last period's final decision completes the assignment and the participant's current assignment advances automatically |

**Two differences from the eleven-step methodology are reported, not reshaped:**

1. The final lock is a timestamp, not a flag. Behaviourally equivalent at the API.
2. Step 11 has two mechanisms — an explicit `researchadvance` between periods, and an implicit
   assignment advance between projects. At the last period of a non-final scenario,
   `researchadvance` returns "the current period's decision must be complete before advancing"
   because the participant has *already* moved to the next assignment. The message is
   misleading; the behaviour is correct and nothing is bypassed.

Required counts, all measured:

| requirement | observed |
|---|---|
| AI visible before preliminary lock | **0** |
| preliminary judgment editable after lock | **0** |
| final judgment accepted before AI reveal | **0** |
| final judgment editable after final lock | **0** |
| period advance before final lock | **0** |

## 4. 6 × 6 controlled-stimulus verification

`code_audit/run38_controlled_stimulus_execution_order.csv` — 36 rows, all PASS.

projects = **6**, periods per project = **6**, unique pairs = **36**, duplicates = **0**,
missing = **0**, unreachable on the participant route = **0**, distinct evidence identities
observed = **36**.

The six projects were checked against the **governed corpus** —
`research_fixtures/synthetic/OG-SYNTH-0.2/.../projects.csv` filtered on
`study_project_candidate == True` — and not against the driver's own constant. That check was
originally self-referential and the fault campaign caught it; see §13.

`research_fixtures/README.md` bars the synthetic corpus from a participant database, so the
corpus was **not** imported. Each of the 36 study project-periods is represented on the
participant route by a `TEST-ONLY-<PROJECT>-<PERIOD>` evidence project, and the transition rules
chain them P1→P6. The corpus itself was read only as the authority on which six projects exist.

## 5. Lock integrity

`code_audit/run38_lock_integrity.csv` — 8 steps.

**Preliminary lock: two independent layers.**
- API resubmission refused (`preliminary judgment is already locked and cannot be resubmitted`).
- Raw SQL `UPDATE decisions SET pre_action=...` refused by database trigger
  `trg_decisions_pre_lock_guard`.
- Value survives reload, session reopen, and a stale-version write naming the locked period.

**Final lock: one layer, and this is reported honestly.**
- API second submission refused; the persisted value is unchanged.
- A mechanically derived census of `server/app/` shows `research_decision.py` is the **only**
  application writer of `final_action`, `final_submitted_at`, `disposition` and
  `final_confidence`. There is no other route to reach them.
- **A raw SQL `UPDATE` of `final_action` succeeds.** There is no database trigger for the final
  lock, unlike the preliminary one.

Classification: **not a readiness blocker.** Blocker 6 is "final lock bypass", and the server
boundary has none — no API path reaches it. Recorded as a finding and named as
successor-candidate work, because closing it requires a new migration on the participant data
path, which is a successor freeze candidate, not a Run-38 repair.

## 6. Information leakage

All measured against the live routes, not inferred from visual hiding:

- `researchevidenceget` returns no configuration, no package and no condition at any stage.
- `researchsequencestate` returns timestamps only — never `pre_action`, `pre_confidence`, or
  any package content, at any stage including after reveal.
- `researchreveal` before the lock refuses and its refusal names only the state.
- In the browser, the package's `detected_condition`, version, hash and model version are absent
  from both `body.innerText` **and** the served DOM before the lock.
- A later assignment is unreachable before earlier ones complete; no later period's evidence
  identity appears in a current-period response.
- Participant B cannot reveal or read participant A's assignment; B's state names nothing of A's.
- An invalid session token is refused.
- Reload, back navigation, duplicate tab, repeated read, stale request and session reopen all
  leave the state machine where it was.

**Cross-participant data leakage = 0. Future-period leakage = 0.**

## 7. Research data contract

`research/methodology/run38_research_data_contract.md`;
`code_audit/run38_research_field_reconciliation.csv` — 17 constructs, all PASS.

**No primary study outcome is unreconstructible from persisted data.** Three measured facts
shape how the analysis dataset is built:

1. **The AI recommendation is not in the governed flat CSV.** It is on the workbook's Stimulus
   sheet, joinable on `instance_id`. Revision direction relative to the AI therefore cannot come
   from the governed CSV alone; the Run-38 export performs the join.
2. **No research row stores the frozen-instrument version.** It is stamped at export time.
   Consequence: data must be exported under the release it was collected under. The runbook
   states this as a rule.
3. `decisions` has **no UNIQUE constraint on `(assignment_id, period)`**. Uniqueness is an
   application invariant (periods are server-derived) and is checked at export.

## 8. Deidentification

`code_audit/run38_deidentification_reconciliation.csv` — 12 classes, all PASS.

**Direct identifiers in the analysis export = 0**, proved by planting a name, an email address,
a phone number and an employee number through the real `researchprejudgment` and
`researchdecision` routes and then searching the serialised bytes of both exports:

| identifier | governed `participant_inputs` CSV | Run-38 analysis dataset |
|---|---|---|
| name / email / phone / employee id in free text | **present verbatim** | absent |
| access-token hash | absent | absent |
| raw `participant_id` primary key | absent | absent |
| IP, session secret, email column, display name | no such column | no such column |

The study identifier is the pseudonymous code. It joined one participant's 36 decisions in the
dry run, and it is the only participant identifier in the dataset.

**Free text (section 10), answered honestly.** The governed export flags
`pre_assessment`, `rationale`, `residual_risk` as review-required in its JSON form; the CSV form
carries no flag at all, because RFC 4180 has no comment syntax. There is **no automated removal,
no governed manual-review procedure, and no rationale coding protocol** in this repository.

So the analysis dataset **excludes free text by construction** — following the precedent the
repository already set for the workbook's `analysis_long` sheet — and carries only
non-identifying derivations (`*_present` flags, `*_chars` counts) plus the two structured closed
vocabularies (`reason_code`, `evidence_items_count`). **No scrubber is claimed, because a
scrubber's efficacy cannot be proved.** The raw text stays in the review-required governed
export and is read as a separate, human-reviewed act.

## 9. Deterministic export

`server/tools/run38_analysis_export.py`. Measured properties: deterministic column population;
stable explicitly ordered schema (58 columns); explicit `schema_version`; one documented row
grain; byte-deterministic for identical database state; UTF-8; LF only; `NA` for null;
`TRUE`/`FALSE` for booleans; closed categorical vocabularies.

`code_audit/run38_research_export_invariants.csv` — 11 invariants, every one observed at 0:

duplicate participant/project/period rows · unknown project · unknown period · invalid state
transition · final response without preliminary lock · final response without AI reveal · AI
reveal before preliminary lock · impossible timestamp ordering · missing frozen-instrument
version identity · direct identifiers · test/live record ambiguity.

## 10. Frozen CSV contract

`research/methodology/run38_frozen_analysis_dataset_contract.md`, schema version
`og-analysis-2026.08-v1`. Row grain **participant × project × period**, proved from the schema
and confirmed by a key census (36 rows, 36 distinct keys, 0 duplicates) — not assumed.

**No final study dataset was created.** Only a dry-run export, every row `record_class =
TEST_ONLY`.

## 11. R ingestion qualification

R 4.3.3 was installed and `research/study_execution/run38_ingest_qualification.R` was **actually
executed** against the dry-run export: **RESULT: 35/35 checks passed**, exit 0, no manual
cleanup. It verifies checksum, schema version, required columns, types, categorical levels,
unique key, project-period population (6 projects × P1..P6 × 36 rows per participant),
missingness, impossible transitions and version provenance — and **re-derives the dependent
variables in R** (action revision, revision direction relative to the AI, confidence change,
disposition presence), which is how derivability is proved rather than asserted.

Base R only, no packages, so the qualification cannot fail for a reason unrelated to the data.
**No inferential analysis was run**, on dry-run data or otherwise.

## 12. Dry-run population and operational resilience

Synthetic sessions, all `TEST_ONLY`: complete session (36/36 periods), partial/resumed session,
attempted post-lock edit, duplicate submission, stale write, omitted optional rationale,
Unicode and delimiter-bearing free text (`Pré-évaluación 测试 «quoted, comma» — ok`), every
project-period, multiple isolated participants.

- duplicate POST of an identical preliminary judgment → refused, **no second observation**;
- re-advancing a completed period → **no duplicated observation**;
- resumed session → lands exactly where the rows say;
- completed study → `all_assignments_complete: true`.

**No duplicated or silently overwritten research observation.**

## 13. 18-fault campaign

`code_audit/run38_fault_campaign_results.csv`.

**faults = 18 · applied = 18 · intended RED = 18 · restored GREEN = 18 · crash accepted as
RED = 0 · unrelated RED = 0 · not applied = 0.**

The four the owner named specifically:
- **Fault 4** (AI available before the preliminary lock) → gate RED, restored GREEN.
- **Fault 9** (remove the persisted field behind the judgment-revision outcome) → gate RED.
- **Fault 12** (insert a direct participant identifier into the analysis export) → gate RED.
- **Fault 18** (break frozen-version provenance) → gate RED.

Fault 1 is the only one that touches a frozen file: it perturbs one byte of
`assets/js/decision-ui.js` for a single invocation of the immutability gate, which refuses, and
is then restored and re-verified byte for byte. That is the only honest way to prove blocker 1
is detected.

**The campaign found three real defects, two of them in the readiness gate itself:**

1. The six-project check compared the driven projects against the *same constant the driver used
   to create them* — a self-referential oracle that could not fail. It now reads the governed
   corpus. This is the sixth time this programme has produced an infer-instead-of-measure
   defect, and it was caught by fault injection, not by reading.
2. The provenance invariant did not require `synthetic_package`, so breaking it left the gate
   green.
3. The revision section raised `KeyError` on a missing column — **a crash, not a RED**, which is
   the first of the five ways a check has lied here. The section now uses `.get()` throughout.

All three were fixed before the reported 18/18 was taken.

## 14. Browser qualification

`code_audit/run38_browser_qualification.csv`. Real Chromium headless shell, real served
application, isolated `TEST_ONLY` identity, throwaway SQLite. **RESULT: 28/28 checks passed. 17
surfaces recorded, 16 PASS, 1 NOT_VERIFIED.**

Exercised in the browser: login/authentication · start session · evidence review · preliminary
response · preliminary lock · AI reveal · final response · final lock · next period ·
reload/resume · back navigation · duplicate tab · completion. Zero JavaScript console errors.
Then **all 36 route identities were verified reachable mechanically**, and the study reported
complete.

**The one NOT_VERIFIED row, stated rather than passed.** An *in-place* navigation of an
already-loaded workspace page did not complete within 180 s. A three-arm probe isolated it: a
bare authenticated page re-navigates in 0.2 s; the same page after `LinWorkspace.openProject`
takes 97.4 s; after the full decision sequence it exceeds 180 s. The server was probed
immediately before and answered at once, so the cost is client rendering under swiftshader
software rasterisation. A **fresh page with the same session token resumes instantly and
correctly**, which is the substantive resume requirement and which PASSes.

This container has no GPU, so the qualification **cannot** distinguish "slow only under software
rendering" from "slow everywhere", and it does not claim to. Classified as a recorded
operational limitation, not a readiness blocker: the complete governed sequence executed, all 36
identities were reached, the study completed, and no persisted record was affected. The runbook
tells administrators to have participants reopen the tab rather than reload it.

## 15. Frozen-instrument immutability

Proved before merge and again on exact final `main`. See §2. **Scientific/client behavioural
changes = 0.**

## 16. Readiness blockers

All eighteen blocker classes were fault-injected and every one is detected. **Blocker count: 0.**

Findings recorded that are **not** blockers, each named with the successor work it implies:

| finding | successor work |
|---|---|
| final lock has no database trigger (application-only) | successor freeze candidate: a migration adding a final-lock guard mirroring `trg_decisions_pre_lock_guard` |
| no research row stores instrument version | successor candidate: a version stamp on `decisions` or `assignments`; until then, export within the collecting release |
| no UNIQUE constraint on `(assignment_id, period)` | successor candidate: add the constraint; until then, the export invariant is the guard |
| free text reaches the governed export verbatim | a governed manual-review procedure, or a coding protocol, neither of which exists yet |
| in-place reload very slow under software rendering | verify on GPU hardware before collection |

## 17. Complete-suite verification

Run on the WIP head and again on exact final `main`, each suite against its own freshly migrated
SQLite (never `:memory:`).

**Suites run: 179. Total checks: 13788/13788. ALL SUITES GREEN.**

The Run-37 figure of 177 suites / 13664 checks is **not inherited**. Run 38 adds two suites
(`test_run38_readiness.py`, 107 checks; `test_run38_frozen_immutability.py`, 17 checks), which
accounts for +2 suites and +124 checks exactly.

Three Run-38 audit CSVs (`run38_participant_state_machine.csv`,
`run38_lock_integrity.csv`, `run38_controlled_stimulus_execution_order.csv`) are regenerated by
the readiness gate on every run and carry per-run ULIDs and timestamps, so they differ after each
execution. They are Run 38's own artifacts and the committed copy is the record of the last
measurement. The pre-existing self-rewriting artifacts of earlier runs (run8, run9, run10, run20,
run17/coverage) were **restored, not committed**, before every commit in this run.

## 18. Final disposition

`STUDY_EXECUTION_READY` — blockers = 0.

**Not claimed.** Nothing here is empirical validation; empirical field validation remains 0/100.
No test session is a study observation. No controlled study was conducted, no participant was
enrolled, and no final study dataset exists.

---

## Artifacts

| path | contents |
|---|---|
| `code_audit/run38_participant_state_machine.csv` | 9 transitions, measured |
| `code_audit/run38_controlled_stimulus_execution_order.csv` | 36 project-periods |
| `code_audit/run38_lock_integrity.csv` | 8 lock steps |
| `code_audit/run38_research_field_reconciliation.csv` | 17 constructs |
| `code_audit/run38_deidentification_reconciliation.csv` | 12 identifier classes |
| `code_audit/run38_research_export_invariants.csv` | 11 invariants |
| `code_audit/run38_fault_campaign_results.csv` | 18 faults |
| `code_audit/run38_browser_qualification.csv` | 17 browser surfaces |
| `research/methodology/run38_research_data_contract.md` | the measured data contract |
| `research/methodology/run38_frozen_analysis_dataset_contract.md` | the frozen CSV contract |
| `research/study_execution/STUDY_ADMINISTRATION_RUNBOOK.md` | how to execute the study |
| `research/study_execution/STUDY_EXECUTION_READINESS_MANIFEST.json` | the machine-readable record |
| `research/study_execution/run38_ingest_qualification.R` | the R ingestion contract |
| `server/tools/test_run38_readiness.py` | the readiness gate (107 checks) |
| `server/tools/test_run38_frozen_immutability.py` | the section-22 gate (16 checks) |
| `server/tools/run38_analysis_export.py` | the analysis export path |
| `server/tools/run38_dryrun.py` | the TEST_ONLY population builder |
| `server/tools/run38_fault_campaign.py` | the 18-fault campaign |
| `server/tools/drive_run38_browser.py` | the browser driver |
| `server/tools/run38_build_manifest.py` | the manifest builder |
| `code_audit/run38_authority_tree.sha256` | the repointed scientific-authority manifest |
