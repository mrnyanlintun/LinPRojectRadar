Run 12 — Final Qualification, Participant Cycle and Refreeze
Starting commit: 3139773
Ending commit: 058345c (merge of 73933a3)
Previous simulation version: sim-2026.08-v6
Final simulation version: sim-2026.08-v7
Synthetic package version: OG-SYNTH-0.3
Participant/study package version: og-participant-2026.08-v1
Category-9 qualification object: PARTIAL
Category-9 fabricated scoring: no
Required-input qualification: PASS
Canonical-structure qualification: PASS
Provenance qualification: PARTIAL
Timeliness qualification: PARTIAL
Revision resolution: NOT_ESTIMABLE
Full participant cycle: PASS
Preliminary lock: PASS
AI reveal sequencing: PASS
Final lock: PASS
Real participant route: PASS
Browser/server parity: PASS
Cost Recovery Status wording: PASS
Conflict semantics: PASS
Voting set: 2
Bucket-5 disabled: 2/2
Synthetic/operational separation: PASS
Defensibility claims: PASS
Full suite: 6102/6102 over 77 suites
Final release status: PARTICIPANT READY

The qualification object is reported PARTIAL, and that is its correct and permanent state given
the evidence this repository holds. PARTIAL there is not a failure of this run and it is not
rounded up anywhere: it is the honest reading of two dimensions that are partly knowable and one
that is not knowable at all. The release verdict does not depend on that PARTIAL being a PASS;
it depends on the qualification not fabricating a confidence it does not have, which is proved.

## 1. Handoff-history audit

Every committed report since the last handoff entry is represented in `T6_HANDOFF.md`, and no
repair was needed. Checked one by one: Run 8 classification, Run 9 test-only synthetic
integration, the synthetic v0.3 Monte Carlo and DSM correction, the Run 10 production remediation
session, Run 10B, and Run 11. The simulation version history is continuous from sim-2026.07-v1
through sim-2026.08-v6 with every stamp preserved in `server/app/simulation/models.py`, and the
synthetic package history is continuous at 0.1, 0.2 and 0.3 with none regenerated or overwritten.
The file is not in chronological order, which Run 11 also recorded; that is a readability
problem and not a completeness problem, and nothing was reordered.

Two small discrepancies between the prompt's description and the repository, resolved in favour
of the repository: there is no `COMMON_PREAMBLE.md`, and there are no `code_audit/run10_*.csv`
files present although the Run 10 handoff entry names them. The Run 10 report itself is present
and controlling, so nothing was reconstructed and nothing was invented.

The pre-change suite reproduced the recorded baseline exactly: **75 suites, 5981 of 5981**.

## 2. Category-9 object schema

`server/app/simulation/qualification.py`, version `cat9-qual-v1`. Explicit dimensions, each with
its own controlled state drawn from PASS, PARTIAL, FAIL, NOT_APPLICABLE and NOT_ESTIMABLE.

| Field | Meaning |
| --- | --- |
| project_id, reporting_period, evidence_package | what this qualification is about |
| qualification_version | the version of the object's shape and meaning |
| required_inputs_status, missing_required_inputs | did every module that was allowed to run get what it requires |
| canonical_structure_status, missing_canonical_structures | is each canonical method's defining structure present |
| period_applicability_status | does this reporting period apply at all |
| provenance_status, provenance_evidence | how far a field can be traced to the artefact that produced it |
| timeliness_status, timeliness_basis | what is known about how current the evidence is |
| revision_resolution_status, revision_resolution_reason | whether the current revision was resolved |
| overall_qualification_state | the WEAKEST dimension, never an average |
| generated_at | passed in, never read from the clock |

**There is no numeric score anywhere in the object.** A suite check enumerates every leaf of every
dimension and fails if any one of them is a number, and a second check fails if any key is named
as a score or a confidence. The overall state is chosen by rank from the dimensions and can never
be better than the weakest of them, which is asserted directly rather than described.

## 3. Category-9 hard-gate versus metadata behaviour

Only the three answerable dimensions can affect execution, and they do it through the abstention
behaviour that already existed rather than a new one. A module missing a required input already
abstains through `models.eligible`; a canonical method missing its defining structure already
abstains through `canonical`. The qualification REPORTS that this happened. It does not decide it,
and removing the qualification would not change one status.

Provenance, timeliness and revision resolution are metadata and only metadata. They are never
converted to a penalty, never weighted, and never folded into anything. No new threshold and no
new numeric weight was introduced by this run, so the stop condition on subjective weights was
never reached.

The integration point is the smallest correct one: `compute.compute_project` attaches the object
AFTER the status is fused, from the run that produced it, and `documents._result_view` derives the
same object at read time from the stored row through the same function. No new column, no
migration, and 0020 through 0025 remain unapplied.

## 4. Category-9 known limitations

  * **Provenance is PARTIAL and will stay PARTIAL.** `signal_inputs.sources` records a document
    TYPE per field and no document identity or version, so a field cannot be traced to the
    artefact that produced it. The object exposes the count of typed fields and the count of
    fields carrying an identity and version, and the second is zero today. A separate and richer
    record does exist at the RESULT level, `source_documents` from migration 0013, but it is not
    joined per field, so it is not represented as per-field provenance.
  * **Timeliness is PARTIAL.** The period cutoff bounds every computation and is reported as the
    basis, but there is no per-field as-of date, so a field that is stale inside an applicable
    period cannot be detected.
  * **Revision resolution is NOT_ESTIMABLE and is never anything else.** Nothing joins a document
    revision to the field a module reads. Upload order is explicitly not treated as evidence of
    currency, and the object says so in the reason it carries.
  * **The object is not validation of anything.** It qualifies evidence availability. It is
    nowhere described as validated, calibrated, a data quality score, or empirical evidence, and
    a suite check enforces that on the file itself.

## 5. Test-participant provisioning path

`server/tools/drive_run12_participant_cycle.py`, recorded field by field in
`code_audit/run12_participant_provisioning.csv`. A throwaway SQLite database, never production
Postgres, and no real participant data.

| Step | Route |
| --- | --- |
| bootstrap research administrator | direct row; there is no route, because a route would need an administrator to call it |
| administrator session | researchlogin |
| operational uploader account | adminparticipantcreate, researchlogin |
| evidence uploaded and analysed | projectupload, projectcomputeall |
| frozen project packages | adminscenariocreate |
| configuration and sequence, frozen | adminconfigurationcreate, adminsequencecreate |
| action families and period transition rules, frozen | adminactionfamilycreate, admintransitionrulecreate |
| decision support packages, frozen | adminpackagecreate |
| test participant account | adminparticipantcreate, researchlogin |
| consent | consentgrant |
| participant profile | intakesave |
| project manager handover to the participant | adminmemberlist, adminmemberrevoke, adminmemberadd |
| project and reporting-period assignment | adminassign |
| packages attached to assignments | adminpackageattach |

The only direct row writes are the bootstrap administrator and two empty evidence project shells,
exactly as the existing decision-sequence suite creates them. **No decision state was inserted
directly to bypass an application transition at any point.**

Two provisioning facts were discovered by driving it rather than assumed. The participant must be
the project manager of the assigned evidence project or both `researchadvance` and
`projectresults` refuse them, and the uploader holds that single slot until it is revoked. And an
action with no frozen family mapping cannot advance a period at all, which is the application
correctly refusing to invent a branch.

## 6. Complete participant decision-sequence evidence

Driven in a real Chromium on the served application, `code_audit/run12_participant_cycle_evidence.csv`,
**56 of 56**. The sequence, in order: the participant reaches the project's Period decision tab;
the fixed evidence package is visible; the AI recommendation text is absent from the served DOM
and the reveal card is not offered; a preliminary action and confidence are recorded and an
assessment written; the commit control is pressed; the preliminary decision locks; the reveal
control appears; the package is revealed; the recommendation becomes inspectable; a final action,
disposition, rationale, confidence, owner, authority, deadline and evidence item are recorded; the
decision control is pressed; the final decision locks; the advance control appears; the governed
transition to the next reporting period executes; the next period opens at evidence again with no
recommendation, and its preliminary decision locks the same way.

Dispositions: the page offers no disposition the server does not accept, the governed set is eight
wide, and a disposition outside it is refused by the server.

**The confirm gate was proved rather than assumed away.** The commit control is confirm-gated and
`window.confirm` returns false in this container, so the first press was made with no dialog
handler and the server was then asked: the stage was still `evidence` and nothing had been
submitted. Only then was a dialog handler installed, which is what a browser that shows dialogs
does when the participant presses OK, and the same control was pressed again.

## 7. Preliminary-lock proof

Server-side, not a disabled control. After the lock: `researchprejudgment` called directly with the
participant's own session is refused with "already locked"; the stored row has
`pre_judgment_locked` true with a lock timestamp; the stored action and confidence are exactly what
the participant recorded; and a raw `UPDATE decisions SET pre_action='tampered'` executed against
the database with the application bypassed entirely is refused by the append-only trigger. The row
was re-read afterwards and is preserved byte for byte.

## 8. AI-reveal proof

The recommendation string is absent from the served page innerText before the lock, and still
absent after the lock and before the reveal. It is present only after the reveal control is
pressed. On the row: `reveal_at` is null before, non-null after, `pre_locked_at <= reveal_at`
holds, and the stored `package_hash` is the frozen package's own sha256.

## 9. Final-lock proof

After the final submission: `researchdecision` called again directly is refused; the stored final
action and disposition are what the participant recorded; `final_submitted_at` is set and is the
lock; `pre_locked_at <= reveal_at <= final_submitted_at`; and the row is against the correct
assignment and project period.

## 10. Live participant rendering evidence, and what the browser found that no suite could

**A live participant-blocking defect, found only by driving the whole cycle.** The preliminary
judgment card is REMOVED from the document at the lock, deliberately, so that a submittable locked
form cannot sit in the DOM. Nothing put it back. Advancing to the next reporting period returns the
stage to evidence IN PLACE, without a page load, so the participant arrived at their second period
with no preliminary judgment form at all: `renderPreForm()` wrote into a null, threw, and the
sequence could not be continued. Every server suite was green throughout, because the server was
never wrong. Fixed in `assets/js/decision-ui.js` by retaining the detached node and its anchor and
re-inserting it when the stage legitimately returns to evidence. The removal at the lock is kept.
Proved on the page: after the advance the card is present, its form renders, and the second
period's preliminary decision locks.

On the served page: the governed status label reads Cost Recovery Status; the conflict state is
NOT_ESTIMABLE_SINGLE_LINEAGE and no coefficient is published; no stale mixed early warning banner
appears; the qualification reaches the served read with revision resolution NOT_ESTIMABLE and
provenance PARTIAL; none of the machine vocabulary reaches the participant text; there is no em
dash; and there was no uncaught page error across the entire cycle. The one occurrence of the word
"validated" on the page is inside a properly qualified negative claim, that analytical outputs are
not a validated compliance determination, and is left as it is.

## 11. Browser/server parity

`server/tools/test_run12_final_verification.py` inventories every live participant and researcher
surface that can display module arithmetic and asserts what each reads. The participant
application loads none of `sim.js`, `simulations.js` or `categories.js`; `LinSim` is undefined in
the participant's browser, checked on the served page and not on the file; every remaining call
into the historical client arithmetic is gated, either by the opt-in the application never sets or
by the explicit refusal that returns when the retired model file is absent; the researcher deep
dive keeps the historical artefacts behind the algorithm version guard. No second arithmetic source
was created: the qualification object is derived from a run, not computed twice.

## 12. Status and conflict wording

Unchanged from Run 11 and asserted again from `fusion.governed_status_semantics`: label **Cost
Recovery Status**, conflict **NOT_ESTIMABLE_SINGLE_LINEAGE**, coefficient not published. Voting
set exactly two, both cost lineage, so both remain derived from the voting set as it stands.

## 13. Defensibility verification

Regenerating `assets/js/ds_defensibility_evidence.js` from the registry reproduces the committed
file byte for byte. No unsupported validation or calibration claim appears in either defensibility
file. The Category-9 object is nowhere represented as empirical validation. Voting set two,
concept-only disabled set eight, Bucket-5 two of two disabled.

## 14. Synthetic and operational separation

OG-SYNTH-0.3 unchanged and not regenerated; 0.1 and 0.2 untouched. The fixture importer still
requires `data_origin = SYNTHETIC_RESEARCH_FIXTURE` and `not_for_empirical_validation = true`, and
holds no database URL, no session factory and no network client, so it cannot reach operational
storage. No production module under `server/app/` reads the research or synthetic fixtures, checked
by scanning every file. The test participant's responses live in a throwaway database and are
separate from the synthetic reference material. **No participant response was used to train or
calibrate anything in this run, and nothing in this run trains or calibrates at all.**

## 15. Test-mutation and fault-injection proof

`code_audit/run12_mutation_proof.csv`. Nine injections plus the five harness cases, every one
confirmed to have altered bytes before its result was believed, every one restored, and a green
reconfirmed after each restore. The strict harness was reproved against all four failure modes plus
a green control using a BYTE-IDENTICAL copy of `run_all_suites.sh`, verified with `cmp`, against a
scratch suite in an isolated directory: no canonical RESULT line, reported failure, green line with
a nonzero exit, and a crash before reporting all fail the runner; the green control passes.
`run_all_suites.sh` itself was not touched and is still strict.

## 16. Complete suite results

  * Pre-change baseline: 75 suites, **5981 of 5981**
  * Final: 77 suites, **6102 of 6102**, ALL SUITES GREEN, each against its own freshly migrated
    database
  * Two new suites: `test_run12_category9_qualification.py` (70),
    `test_run12_final_verification.py` (49)
  * Browser drives: `drive_run12_participant_cycle.py` **56 of 56**;
    `drive_run11_participant_route.py` re-run and green
  * `tests.html` **51 of 51**; `tests_render.html` **286 of 287**, the same one non-pass Run 10B
    and Run 11 both recorded, check 264 needing a signed-in session token
  * Five earlier suites restated with every original finding preserved as the reason:
    `test_run6_known_answer.py`, `test_run8_retest_classify_27.py`,
    `test_run10_state_protection.py`, `test_run7_fix_now_defects.py`,
    `test_run10b_a1_7_domain.py`. None deleted and none loosened.

## 17. Final simulation-version record

sim-2026.08-v6 to **sim-2026.08-v7**. Every earlier stamp is preserved in
`server/app/simulation/models.py` and a suite asserts each of v2 through v6 is still present. The
stamp moves because the emitted result object gained a field. **Nothing arithmetical changed with
it:** no band, no boundary, no module, no vote and no status.

## 18. Participant and study package hashes

Participant and study package version **og-participant-2026.08-v1**, the first of its kind here.
Per-file digests for `index.html` and every file under `assets/` are in
`code_audit/run12_participant_package_checksums.sha256`, 70 files, aggregate sha256
`502c03b8f789d1c9ced19ba993f2e88cf610eb0df3f313afd8ee35c749e2192b`. Synthetic v0.3 archive digest
carried forward unchanged.

## 19. Dependency and version freeze

`code_audit/run12_release_freeze.md`. Python 3.11.15; fastapi 0.115.6; uvicorn 0.34.0; SQLAlchemy
2.0.36; alembic 1.14.0; pydantic 2.13.4; playwright 1.48.0. **lxml is absent from the normal
application and test interpreter**, confirmed by import. Migrations applied through 0019; 0020 to
0025 remain unapplied and this run added none.

## 20. Frozen-file-guard proof

The guard was first tripped for real, not staged: the new qualification file was outside every
run's authorised scope and two suites failed by name until Run 12's own scope was declared. It was
then proved deliberately: appending a comment to `assets/js/store.js`, a participant asset outside
every run's scope, produced a red naming that file; restoring it produced a green. Run 12's
authorised scope is three server files and one browser asset, added beside every earlier run's list
rather than widening any of them.

## 21. Guarantees

**Verified.** The full participant cycle driven end to end through the real application on the real
route. The preliminary lock enforced by the server and by the database. The AI reveal occurring only
after the preliminary lock. The final lock enforced by the server. The participant route displaying
current server results with no executable stale browser arithmetic. Cost Recovery Status and the
single-lineage conflict wording. The Category-9 object built, integrated and proved unable to
fabricate confidence. Required-input and canonical-structure failures abstaining. Voting set two.
Bucket-5 two of two disabled. Registry-derived defensibility with no unqualified validation claim.
Synthetic and operational separation. All suites green. Every new critical check proved able to
fail. Release hashes and versions recorded.

**Partly met.** Category-9 provenance and timeliness, permanently PARTIAL, and revision resolution,
permanently NOT_ESTIMABLE, for the reasons in section 4. This is reported as a stated limit of the
evidence and not as an unfinished piece of work.

**Not met.** Nothing in the release gate is unmet.

## 22. Remaining deviations

  1. Provenance, timeliness and revision resolution cannot be completed without evidence
     structures the repository does not hold. Building them is an owner decision.
  2. `tests_render.html` check 264 still needs a signed-in session token. Carried since Run 10B.
  3. The dead control-chart penalty in the forecast module remains unreached on every production
     path. Carried since Run 10.
  4. The registry canonical name reads "Monte Carlo EAC" while the programme prose says "Monte
     Carlo EAC Forecast". Carried since Run 10.
  5. Two prior-run audit artefacts, `run9_no_operational_effect.csv` and
     `run10_no_operational_effect.csv`, are still rewritten by their own suites on every execution
     and would overwrite a prior run's recorded digests. They were restored rather than committed
     in this run. Carried since Run 10.
  6. `code_audit/run10_*.csv` files named in the Run 10 handoff entry are not present in the
     repository. Recorded, not reconstructed.

## 23. Final release verdict

**PARTICIPANT READY.**

Every condition in the release gate is actually met and was actually executed, not inferred: the
full sequence was driven in a real browser through the real application; both locks are enforced by
the server and the preliminary one by the database as well; the reveal cannot precede the lock; the
served page shows current server results and cannot execute stale browser arithmetic; the governed
wording is correct on the page a participant reads; the qualification object exposes what is
unknown as unknown; the voting set and the disabled set are unchanged; and the complete suite is
green at 6102 of 6102 with every new critical check proved capable of failing.

The verdict rests on one correction this run had to make first. Driving the cycle end to end found
that a participant could not begin their second reporting period at all. Had the cycle not been
driven, that defect would have shipped behind a fully green suite.
