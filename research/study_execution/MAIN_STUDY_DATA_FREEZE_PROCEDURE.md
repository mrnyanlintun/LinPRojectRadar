# Main-study data freeze procedure

What happens after the last participant completes. Every numbered step below is **executed** by
`server/tools/run39_main_study_freeze.py`; this document describes running code, not intention.

**Analysis never runs against the live operational database.** It runs against the frozen
artifact this procedure produces, and only against that.

---

## 1. Stop data collection

Deactivate the participant accounts (`is_active = false` via the governed route). Record the
stop time. From this point no route may write a `decisions` row.

## 2. Verify session completeness

```python
import run39_launch_gate as LG
LG.session_completeness(session)
```

Per participant it reports observations, unique project-periods, duplicates, preliminary locks,
reveals, final locks, reveal-after-lock counts and a `complete_36` flag — **all counted from
persisted rows**. Nothing is filled in, completed or repaired. A participant with 29 decisions is
reported as having 29.

## 3. Classify exclusions without altering responses

Exclusion is a **classification**, never an edit. See
`research/methodology/run39_dataset_classification_contract.md` and section 14 of the Run-39
report. The categories are:

`TEST_ONLY` · `PILOT` · `MAIN_STUDY complete` · `MAIN_STUDY incomplete` ·
`technically invalid record` · `UNCLASSIFIED (excluded, fail-closed)`

**No participant-withdrawal state is defined**, because no governed document in this repository
establishes one. If the study protocol later defines withdrawal, it is added to the governed
vocabulary before it is used — never invented at freeze time.

**Never delete a substantive observation to improve a completeness metric.**

## 4. Export MAIN_STUDY only

```python
import run39_main_study_freeze as FZ
record = FZ.freeze_dataset(session, out_dir, "og_main_study_2026", "MAIN_STUDY")
```

Selection is exact-match against the governed registry. A `PILOT`, `TEST_ONLY` or unregistered
participant cannot be selected. If no observation is classified `MAIN_STUDY`, the procedure
raises `EmptyDatasetError` and writes nothing — an empty artifact that looked like a dataset
would be worse than no artifact.

## 5. Deidentify

Deidentification is **by construction**, not by scrubbing:

- the only participant identifier is the pseudonymous study code;
- the column allowlist names no name, email, login, employee id, IP, token, session secret or
  raw database primary key;
- the three participant-authored free-text columns are not columns of this dataset at all —
  only `*_present` flags and `*_chars` counts appear.

Raw free text remains in the governed `participant_inputs` export, which is review-required and
is **not** the analysis dataset.

## 6. Validate invariants

`FZ.check_invariants()` runs **before** the checksum is taken. All ten must be zero:

duplicate participant/project/period rows · rows missing a project · rows missing a period ·
final response without preliminary lock · final response without AI reveal · AI reveal before
preliminary lock · impossible timestamp ordering · rows missing frozen-instrument version
identity · direct identifier columns · participant-authored free-text columns

Any violation **aborts the freeze**. It is never recorded with a caveat.

## 7. Generate the frozen CSV

Produced by the frozen export path (`og-analysis-2026.08-v1`, 59 columns, one row per
participant × project × period, UTF-8, LF, `NA` for null, `TRUE`/`FALSE` for booleans, sorted by
participant, sequence, period).

## 8. Calculate the checksum

```
sha256sum og_main_study_2026.csv
```

The procedure re-reads the file **from disk** and re-derives the digest. Trusting the in-memory
bytes would not detect a truncated or partially written file, which is the failure this step
exists for. A mismatch deletes the file and aborts.

## 9. Record provenance

`og_main_study_2026.freeze.json` carries: dataset class, sha256 and the checksum procedure, row
and column counts, schema version, row grain, simulation version, participant package, synthetic
package, freeze candidate commit, the classification registry digest, the participant list, the
invariants checked, and the freeze timestamp.

## 10. Make the frozen CSV immutable

Commit the CSV, its manifest, its class sidecar and its freeze record **together**, and never
edit any of them again.

**A correction is a NEW artifact with a NEW checksum, never an in-place change.** The superseded
artifact stays addressable, exactly as superseded freeze records do elsewhere in this repository.

## 11. Transfer the frozen CSV to R

```
Rscript research/study_execution/run38_ingest_qualification.R \
        og_main_study_2026.csv og_main_study_2026.manifest.json
```

It must print `RESULT: N/N checks passed` and exit 0. It verifies the checksum first, so R
refuses a file that is not the frozen artifact.

**R is not vendored in this repository.** It must be installed in the analysis environment
before this step; the Run-39 rehearsal used R 4.3.3.

## 12. Analyze only the frozen artifact

All statistical work reads `og_main_study_2026.csv`. No analysis connects to the operational
database. Re-running the analysis later must reproduce, which it can only do if the input is a
file with a recorded checksum rather than a query against data that keeps moving.
