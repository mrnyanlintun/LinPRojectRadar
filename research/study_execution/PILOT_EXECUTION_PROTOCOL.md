# Pilot execution protocol

**Frozen instrument identity.** Freeze candidate
`6142d877856ea651ef8d7e905f6d27604b3244f1`, accepted release
`f983bb020f7a184a5742e1fff09d690b0170f0de`, disposition `FINAL_FREEZE_ACCEPTED`.
Simulation `sim-2026.08-v25`. **Participant package `og-participant-2026.08-v13`.** Synthetic
package `OG-SYNTH-0.6`. Analysis export schema `og-analysis-2026.08-v1`.

Verify all of these before every pilot session:

```
cd server/tools && PYTHONIOENCODING=utf-8 python3 test_run39_frozen_immutability.py
```

It must print `RESULT: N/N checks passed`.

---

## 1. Purpose

The pilot exists to qualify **operations**, not science. It answers: can a session be
administered end to end, does the instrument behave as the frozen record says, does an
interruption recover, does the export and R hand-off work on real collected rows, and are the
incident and freeze procedures usable by a human under real conditions.

It is **not** a study, not a power calculation, not a pre-test of a hypothesis, and produces no
finding of any kind.

## 2. Pilot data are excluded from the primary study dataset

Every pilot participant is registered `PILOT` in
`research/study_execution/dataset_class_registry.csv`. `PILOT` rows are structurally ineligible
for a `MAIN_STUDY` export: selection is exact-match against that registry, and no code path
promotes a class. See `research/methodology/run39_dataset_classification_contract.md`.

Pilot observations are **retained as evidence and segregated**. They are never deleted to make a
completeness number look better.

## 3. The sequence a pilot participant performs

The same governed 36-decision sequence as the main study, unchanged:

6 controlled projects × 6 reporting periods = **36 project-period decisions**, each of them:

1. controlled evidence review
2. preliminary assessment, action and confidence
3. **preliminary lock** (written in the same statement as the judgment; irreversible)
4. AI reveal — permitted only after the preliminary lock
5. final action, confidence, disposition, evidence and rationale
6. **final lock**
7. transition to the next controlled period

## 4. Permitted administrator actions

- Provision an account (`adminparticipantcreate`) and hand over the access token out of band.
- Register the participant `PILOT` in the governed registry, before their first session.
- Provision scenarios, frozen configurations, frozen sequences, frozen packages, action families
  and frozen transition rules — **before** the participant begins.
- Monitor progress with `adminassignmentlist` / `adminparticipantlist` (status only).
- Take an export (`adminexportcreate`), which is role-gated and checksum-recorded.
- Record an incident in `STUDY_INCIDENT_LOG_TEMPLATE.csv`.
- Answer procedural questions about how to use the interface.

## 5. Prohibited administrator actions

- **Any direct database write to a participant response, by any means, at any time.** No routine
  administrative task requires one; the admin-route census in
  `code_audit/run39_administrative_authority_boundary.csv` shows zero administrative routes
  write a response column. Do not open a SQL client against the study database during collection.
- Editing a frozen configuration, sequence, package, action family or transition rule.
- Changing a participant's assignment set or its order after allocation.
- Changing the frozen release mid-collection.
- Coaching a participant on what to decide, or discussing the AI recommendation with them.
- Reclassifying a participant after their data is collected in order to move it between datasets.

## 6. Interruption procedure

Nothing is required to resume. The stage is derived from the persisted rows on every request, so
the participant signs in again and lands exactly where the rows say.

- If the interface appears to hang after a **reload**, have the participant **close the tab and
  open a new one** rather than reloading in place. See the recorded environment limitation in
  `code_audit/run39_pilot_browser_execution.csv`.
- If a period is abandoned mid-way, leave it. It will be classified `pre_only` or
  `revealed_not_decided` by `completion_state` in the export. **Do not complete it for them and
  do not delete it.**
- Log every interruption in the incident log.

## 7. Incident logging

Every anomaly is recorded in a copy of
`research/study_execution/STUDY_INCIDENT_LOG_TEMPLATE.csv`, using the study identifier only —
never a name, email or any direct identifier. An incident that affects response integrity or
frozen behaviour is escalated per section 9.

## 8. Completion criteria

A pilot session is complete when:

- `researchsequencestate` returns `all_assignments_complete: true`; **and**
- the export shows exactly 36 rows for that participant, all with
  `completion_state = complete`; **and**
- `duplicate participant/project/period rows = 0` for that participant.

Anything less is an **incomplete session and stays incomplete**.

## 9. Conditions requiring launch blockage

Stop and do not proceed to main-study collection if any of these occurs during the pilot:

- AI content is visible to a participant before their preliminary lock;
- a preliminary or final lock is bypassed through the application;
- one participant can read another's responses;
- a future period or another project's treatment becomes reachable;
- the export cannot reproduce a primary outcome, its provenance, or its checksum;
- R cannot ingest the export;
- pilot data proves able to enter a `MAIN_STUDY` export;
- any frozen participant-facing or scientific behaviour is found to have changed.

**A frozen-behaviour defect is never repaired in place.** It requires a successor freeze
candidate, and collection does not begin until that candidate is accepted.

## 10. Export procedure

Identical to the main study, with `dataset_class = "PILOT"`:

```python
import run39_launch_gate as LG
rows, payload, sidecar = LG.build_class_export(session, "PILOT")
LG.write_export(out_dir, "pilot_export", payload, rows, sidecar)
```

The artifact is named **pilot**, never "the study dataset".

## 11. Pilot data disposition

Pilot rows stay in the operational database, registered `PILOT`, indefinitely. They are:

- **excluded** from every `MAIN_STUDY` export by construction;
- **retained** as operational qualification evidence;
- **never** re-registered as `MAIN_STUDY` after the fact.

## 12. Human-subjects status

**This repository does not establish an IRB approval, an approved protocol number, or an
approved consent text.** `consentgrant` records a consent row; whether the consent it records is
the ethically approved one is outside anything this repository can evidence.

No pilot session involving a real person may be conducted on the basis of this document alone.
Obtaining and evidencing approval is a separate responsibility of the researcher, carried out
before any human participant is approached. Run 39 conducted **no** session with a real person:
every identity it exercised was synthetic.
