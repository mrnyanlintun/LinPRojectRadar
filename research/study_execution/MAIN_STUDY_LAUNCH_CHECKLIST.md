# Main-study launch checklist

Every line is verified **mechanically** before the first real participant begins. A tick that was
not produced by a command is not a tick.

---

## Automated gates

```
cd server/tools
PYTHONIOENCODING=utf-8 python3 test_run39_frozen_immutability.py    # frozen surfaces unmoved
PYTHONIOENCODING=utf-8 python3 test_run38_frozen_immutability.py    # Run-38 proof still holds
DATABASE_URL=... SESSION_SECRET=... python3 test_run38_readiness.py # study execution readiness
DATABASE_URL=... SESSION_SECRET=... python3 test_run39_launch_gate.py
PYTHONIOENCODING=utf-8 python3 run39_dataset_class.py               # registry loads and counts
```

Each must print `RESULT: N/N checks passed`.

## Checklist

| # | check | how it is verified | authority |
|---|---|---|---|
| 1 | freeze accepted | `release_disposition == FINAL_FREEZE_ACCEPTED` | `INSTRUMENT_FINAL_FREEZE_RECORD.json` |
| 2 | Run 38 READY | `final_disposition == STUDY_EXECUTION_READY`, blockers 0 | `STUDY_EXECUTION_READINESS_MANIFEST.json` |
| 3 | Run 39 READY | `launch_disposition == MAIN_STUDY_LAUNCH_READY`, blockers 0 | `MAIN_STUDY_LAUNCH_MANIFEST.json` |
| 4 | correct deployment version | `test_run39_frozen_immutability.py` — `server/app/`, `assets/`, `index.html` byte-identical to candidate `6142d877` | git diff |
| 5 | correct participant package | `og-participant-2026.08-v13` | `participant_packages.CURRENT` |
| 6 | correct simulation | `sim-2026.08-v25` | `app.simulation.models.SIMULATION_VERSION` |
| 7 | correct controlled stimuli | `research_fixtures/synthetic` byte-identical to candidate; 6 projects × 6 periods | immutability gate + design contract |
| 8 | study-mode account isolation | cross-participant read refused at the server boundary | Run-38 leakage artifact, re-proved by the Run-39 gate |
| 9 | zero-state main dataset | MAIN_STUDY registrations = 0 **and** MAIN_STUDY persisted observations = 0 | `run39_main_study_zero_state.csv` |
| 10 | pilot segregation | pilot cannot become MAIN_STUDY; relabelling cannot reclassify; exact-match keys | `run39_pilot_main_segregation.csv` |
| 11 | export tested | pilot export at `og-analysis-2026.08-v1`, 59 columns, deterministic, 0 direct identifiers | `test_run39_launch_gate.py` |
| 12 | R ingestion tested | `run38_ingest_qualification.R` passes on the pilot export, no manual cleanup | R rehearsal |
| 13 | incident procedure ready | template present; administrators know where it lives | `STUDY_INCIDENT_LOG_TEMPLATE.csv` |
| 14 | administrators instructed not to alter responses | acknowledged in writing before collection | `PILOT_EXECUTION_PROTOCOL.md` §5, runbook §11 |
| 15 | freeze procedure ready | executes, refuses an empty dataset, reproduces its checksum | `run39_main_study_freeze.py` |
| 16 | R installed in the analysis environment | `Rscript --version` returns | operator |
| 17 | every participant registered before their first session | governed registry names them with a class | `dataset_class_registry.csv` |

## Registering the first main-study participant

1. Provision the account (`adminparticipantcreate`); record the pseudonymous code.
2. **Add a row to `research/study_execution/dataset_class_registry.csv`** with
   `dataset_class = MAIN_STUDY`, the date, the registering authority and a note.
3. Commit that change on its own, so the moment a participant became main-study-eligible is
   visible in version control.
4. Re-run `test_run39_launch_gate.py`. **The zero-state check will now legitimately fail**, which
   is correct: zero state is a pre-launch condition, not a permanent invariant. Record the launch
   moment in the incident log and proceed.

## Not asserted

**No IRB or human-subjects approval claim appears in this checklist**, because no governed
document in this repository establishes one. Obtaining and evidencing ethical approval is a
separate prerequisite the researcher completes before approaching any participant. Run 39
approached none.
