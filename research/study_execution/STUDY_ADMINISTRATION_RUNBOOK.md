# Study administration runbook

**Scope.** How to execute the controlled study on the frozen Opus Gubernatio instrument and
produce the frozen analysis dataset. Every step below was exercised against the live routes by
`server/tools/test_run38_readiness.py` and `server/tools/drive_run38_browser.py` on isolated
test databases with TEST_ONLY identities.

**This document makes no human-subjects or IRB claim.** No governed document in this repository
establishes an approval, an approved protocol number, or a consent-form text, so none is stated
here. `consentgrant` is a technical gate that records a consent row; whether the consent it
records is the ethically approved one is outside anything this repository can evidence, and the
administrator is responsible for that separately.

---

## 1. Provisioning a test or study account

Everything is done through the `/exec` action surface. There is no separate admin console route.

1. A `ResearchAdmin` participant must exist. Sign in:
   `{"action":"researchlogin","access_token":"<admin token>"}` → `session_token`.
2. Create the participant:
   `{"action":"adminparticipantcreate","session_token":"<admin>"}` →
   `{participant_id, pseudonymous_code, access_token}`.
   **The pseudonymous code is the only identifier that ever reaches an export.** No name, email
   or employee number is asked for and none should be entered anywhere.
3. Hand the participant their `access_token` out of band. It is stored only as a hash; it cannot
   be recovered, only reissued.
4. **Test accounts must carry the `R38-TESTONLY-` code prefix.** That prefix is what
   `run38_analysis_export` reads to set `record_class = TEST_ONLY`. A study account must NOT
   carry it. This is the only thing standing between a dry run and a study observation in the
   analysis dataset; treat it as part of the protocol, not as a naming convenience.

## 2. Preparing the controlled study for a participant

Once, per study:

1. Six evidence projects (one per controlled project) must exist as `projects` rows and must not
   be flagged `is_training`. Six scenarios are then created, one per project, each with
   `period_count = 6` and `evidence_package_id` naming its project:
   `adminscenariocreate`.
2. Configurations `C0`/`C1`/`C2` created and **frozen** (`adminconfigurationcreate` with
   `"freeze": true`). An unfrozen configuration cannot be assigned.
3. A condition sequence created and **frozen** (`adminsequencecreate`), with one position per
   scenario.
4. One decision-support package per scenario, created and **frozen**
   (`adminpackagecreate` with `"freeze": true`). An unfrozen package cannot be revealed.
5. Action families registered (`adminactionfamilycreate`) for every action the form offers, and
   transition rules registered and frozen (`admintransitionrulecreate`) for periods P1..P5 of
   every scenario. **Without these a participant completes a period and cannot advance.**

Per participant:

6. `consentgrant` then `intakesave` (intake is consent-gated, and a preliminary judgment is
   refused until intake is complete).
7. `adminassign` with all six `scenario_ids`. Assignment order is `sorted(scenario_ids)`, which
   is ULID creation order — deterministic, and fixed for the whole study once the scenarios are
   made.
8. `adminpackageattach` for each assignment. **The package is attached per assignment, not per
   period: all six periods of a project disclose the same package.** That is frozen behaviour.

## 3. How a session begins, and how frozen version identity is verified

The participant signs in with their access token and the client calls `researchsequencestate`,
which returns the derived stage and period. Nothing about where they are is stored on the
client, so a session "begins" simply by authenticating.

**Verify the frozen version before every collection session:**

```
cd server/tools && PYTHONIOENCODING=utf-8 python3 test_run38_frozen_immutability.py
```

It must print `RESULT: N/N checks passed`. It proves, by diff against the accepted release and
the freeze candidate `6142d877856ea651ef8d7e905f6d27604b3244f1`, that `assets/`, `server/app/`,
`research_fixtures/synthetic/` and `index.html` have not moved, and that the simulation version,
participant package and synthetic package are still `sim-2026.08-v25`,
`og-participant-2026.08-v13`, `OG-SYNTH-0.6`.

**Known limitation, stated rather than glossed:** no research row stores the instrument version.
Version identity is stamped onto the export at export time. **Data must therefore be exported
under the same frozen release it was collected under.** If a release changes mid-collection,
export first, then upgrade.

## 4. Monitoring progress without seeing substantive answers

- `adminassignmentlist` returns `_admin_row(assignment)` — sequence number, scenario, status.
- `adminparticipantlist` returns the pseudonymous code and completion status.
- `researchsequencestate` is a **participant** action and requires that participant's session;
  an administrator cannot call it for someone else.

This is enough to see who is where. It does not show any preliminary or final judgment, and no
administrator route returns one. **An administrator who wants to see answers must take an
export**, which is an auditable act (`research_exports` row + `audit_events`). Do not query the
database directly during collection.

## 5. Handling an interrupted session

Nothing is required. The stage is derived from the rows on every request. The participant signs
in again and `researchsequencestate` returns them to the exact period and stage. Measured:
reload, session reopen, duplicate tab, back navigation and duplicate POST all leave the state
machine and the persisted record unchanged, and produce no second observation.

If a participant abandons mid-period, the row is in `pre_only` or `revealed_not_decided` and the
analysis dataset says so in `completion_state`. Do not delete it and do not complete it for them.

**A browser-driver limitation recorded in `code_audit/run38_browser_qualification.csv`:** in
this headless container, an in-place navigation issued *after* the workspace has opened a
project does not complete within 100 s. A fresh page or tab with the same session token resumes
correctly and immediately. Participants should be told to reopen the tab rather than reload it
if a reload appears to hang. This is a browser-execution observation, not a data-integrity one:
the persisted record and the derived stage were correct throughout.

## 6. Confirming completion

`researchsequencestate` returns `all_assignments_complete: true` when every assignment is
finished. Confirm additionally in the export: the participant must have exactly 36 rows, all
with `completion_state = complete`. The R ingestion script checks both.

## 7. Exporting records

Governed export (the full record, including free text):
`{"action":"adminexportcreate","session_token":"<admin>","kind":"participant_inputs",
"format":"csv"|"json"|"xlsx"}`. It is unconditionally filtered to research accounts and records
a checksum in `research_exports`.

Analysis dataset (the frozen CSV the statistics consume):

```python
from run38_analysis_export import build_analysis_rows, serialise_csv, freeze_manifest, checksum
rows = build_analysis_rows(session)
payload = serialise_csv(rows)
manifest = freeze_manifest(payload, rows)
```

## 8. Deidentification

The analysis dataset is deidentified **by construction, not by scrubbing**:

- the only participant identifier is the pseudonymous code, which joins that participant's 36
  decisions and nothing else;
- the column list is an allowlist that names no name, email, login, employee id, IP,
  authentication token, session secret or raw participant primary key;
- the three participant-authored free-text columns are **not columns of this dataset at all**.
  Only `*_present` flags and `*_chars` counts appear.

**Free text is where identity actually leaks, and it is handled by exclusion.** Verified by
measurement: a name, an email, a phone number and an employee number typed into `rationale` and
`pre_assessment` through the real routes reach the governed `participant_inputs` CSV verbatim
and reach the analysis dataset not at all.

If anyone needs the free text, they read the governed `participant_inputs` export, which carries
`review_required: true`, and a human reviews it before it leaves the study team. **No automated
removal exists and none is claimed.**

If a reidentification key is ever needed operationally, it is kept outside this repository and
outside the analysis dataset. **Do not create one during a dry run.**

## 9. Freezing and checksumming the export

See `research/methodology/run38_frozen_analysis_dataset_contract.md` §10. In short: write the
CSV and its manifest, confirm `sha256sum` matches, run the R qualification, commit both, never
edit either again.

## 10. Transferring the frozen CSV to R

```
Rscript research/study_execution/run38_ingest_qualification.R <dataset>.csv <dataset>.manifest.json
```

It must print `RESULT: N/N checks passed` and exit 0. It verifies the checksum, schema version,
required columns, types, categorical levels, unique key, project-period population, participant
completeness, missingness, impossible transitions and version provenance — and re-derives the
dependent variables in R to prove they are derivable.

It performs **no inferential analysis**, by design. Hypothesis testing happens afterwards, in R,
against a dataset whose `record_class` is `STUDY`.

## 11. What administrators must never change during data collection

- Any file under `assets/`, `server/app/`, `research_fixtures/synthetic/`, or `index.html`.
- Any frozen configuration, condition sequence, decision-support package, action family or
  transition rule. Freezing is what makes them evidence.
- A participant's assignment set or its order, once allocated.
- Any `decisions` row, by any means, including direct SQL. **The preliminary lock is enforced by
  a database trigger; the final lock is enforced only by the application.** A direct SQL update
  to `final_action` will succeed and will silently destroy the observation. Do not open a SQL
  client against the study database during collection.
- The `R38-TESTONLY-` prefix convention, in either direction.
- The frozen release itself. Verify it (§3) at the start of every session.
