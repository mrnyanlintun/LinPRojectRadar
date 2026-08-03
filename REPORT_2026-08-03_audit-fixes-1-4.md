# Audit fixes 1 to 4

Fixes for findings 1 to 4 of `REPORT_2026-08-02_full-audit.md`. Finding 5, the withdrawn
scenario UI, is untouched: it is a decision being made separately. No migration was added.

Every fix was proven able to fail by injecting the fault it addresses, restoring, and
re-checking the baseline. Two of the faults are recorded below because they did NOT behave as
expected the first time, and that is the more useful half of this report.

## Finding 0, settled first: the contradiction was always there

**It is not an artifact of superseding.** On a database created for this run, one project, one
document, one compute, and no second upload of any kind:

| Surface | Before the fix |
|---|---|
| Stored `computed_results.project_status` | `Green` |
| Signals tab | **Green** |
| Project list row | **Awaiting analysis** |
| Status legend | **Awaiting analysis 1**, Green 0 |

So finding 1 was an always-on defect affecting every computed project on the primary portfolio
surface, and the fix had to be a real one rather than a repair of upload ordering.

## Finding 1: every surface now reads the stored computed result

**Fixed on the read paths, not by writing a status back into the document.** `a_list`,
`a_listslim` and `a_get` in `server/app/facade.py` now resolve the live `computed_results` row
and let it supply the status.

Writing back into `project.doc` was rejected: it would have created a second copy of the status
that drifts the moment a recompute lands, which is precisely the "second source of truth" the
brief rules out. Reading it at the point of use cannot drift, because there is only ever one
copy. Three details worth keeping:

- **One query per page, not one per project.** `live_statuses()` resolves the whole visible set
  in a single `IN` query; an N+1 here would be paid on every portfolio load.
- **`superseded_by IS NULL`**, the same predicate `_live_result` already uses, so a recompute
  moves every surface at once and a superseded row can never be what a list renders.
- **`with_stored_status()` returns a copy and never mutates `project.doc`.** That attribute is a
  live ORM JSON column; assigning into it would be picked up by the next flush and written to
  the database, quietly recreating the very drift this avoids.

Only the status travels. `module_results` is deliberately excluded, because it carries the
action-bearing fields `_result_view` redacts unless `recommendation_visible` allows them, and a
project list is not a place that predicate has been evaluated.

**Verified in a browser** at the end of the run, against the final code:

| Surface | After |
|---|---|
| List row, computed project | `Clean Compute Project · AVIATION · Green` |
| List row, uncomputed project | `Never Computed Project · RAIL · Awaiting analysis` |
| Legend | `Green 1 · Awaiting analysis 1` |
| Signals tab | Green |

**Fault injection**: with both halves of the fix reverted, `listslim` returned `status: ''` for
the computed project and the list rendered "Awaiting analysis" again. Restored, re-read, `Green`.

## Finding 2: the render fixture now exercises the production path

The harness passed 62/62 while the live list was broken because `fresh()` called
`LinResults.prime(id, row)` — a cache nothing fills for a list. `prime` is called from exactly
two workspace panels, both of which fetch `projectresults` for one already-open project. The
list, legend and radar come from `list`/`listslim`, where that cache is empty. The harness was
handing the render path its data by a route production never takes.

Two changes:

1. **`fresh()` no longer primes.** It attaches `status` and `storedResult` to the project object,
   which is how `with_stored_status` delivers them, and clears the cache to prove nothing below
   depends on it.
2. **A new over-the-wire group** actually calls `listslim`, `list` and `projectresults` and
   asserts the delivered status matches the stored one. It borrows the application's own session
   token from `sessionStorage` (same origin, same tab), so it needs no configuration; with no
   token it reports a **failing** row rather than skipping silently.

**Which project is computed is established from `projectresults`, not from `list`.** The first
version asked `list` both questions, so with the server delivering nothing it failed as "no
computed project exists" — which reads like a setup problem and invites dismissal. Cross-checking
against the endpoint that was never broken makes the failure name the real defect:

```
production read path: list carries the stored status  ::  expected Green  ::  MISSING: list dropped it
production read path: listslim status IS the stored   ::  expected Green  ::  MISSING: listslim dropped it
production read path: the delivered document renders  ::  expected Green  ::  undefined
```

**Fault injection**: with finding 1 reverted the harness went 66/69 with those three rows red.
Restored: 69/69.

## Finding 3: an evidence-less scenario is refused, twice

`adminscenariocreate` now requires `evidence_package_id` **and** requires it to name a project
that exists — a typo'd id renders the same empty panel an absent one does. `adminassign` checks
again, per scenario, against the projects table, because the creation guard cannot reach
scenarios that already exist and those are exactly the ones still able to do harm. The
assignment refusal is audited (`assignment_denied_no_evidence`) and names which scenario, since
an allocation carries several:

```
cannot assign: no evidence is attached to LEGACY-NOEV (no evidence project named).
A participant would reach the preliminary judgment, which cannot be undone, with nothing to judge.

cannot assign: no evidence is attached to STALE-REF (names missing project PRJ-GONE-9999). ...
```

**Fault injection**: with both guards disabled, five checks in `test_assignment_blinding.py`
went red, including the deliberate non-vacuity check that a scenario *with* evidence still
assigns. Restored: 50/50.

### The already-stuck instance

Local data has exactly one, in the throwaway audit database from the 2026-08-02 walkthrough:
participant `AUD-P-001`, scenario `AUDIT-S1`, no evidence, preliminary judgment locked, never
revealed. **Nothing was altered.** For a real one the options are: leave it and let the export
carry it (correct if the record of a spent judgment is itself evidence); or delete the
participant, which cascades the decision away and destroys the measurement record. There is no
path that un-spends a preliminary judgment, by design. **I cannot say whether production has
one** — production was not inspected, and the query above only ran against local databases.

## Finding 4: filing is decided before extraction

`reference_kind()` is now consulted when the upload is decoded, and a reference document is
never queued for extraction. It is stored with `doc_type`, `extraction`, `extraction_model` and
`classification_confidence` all NULL, which is the honest record that nothing read it, and
`_decide_filing` files it from the filename exactly as before.

A third upload outcome, `"filed"`, joins `"extracted"` and `"matched"`: reporting a reference
document as extracted would claim a model call that never happened. `workspace.js` renders it as
"filed, not analysed".

**Verified in a browser**: uploading `Division 23 Specification rev D.txt` through the real
upload control returned "filed, not analysed · filed as reference material for technical review;
deliberately kept out of the analytical path", and the Files tab shows it in
`4_QC/UNDATED_XX%/D_SPECIFICATIONS`. Before this fix the same upload returned `status: "failed"`
and was never filed at all.

**The register-only rule does not regress.** `rfi`, `rfa` and `submittal` remain absent from
`DOC_TYPES` while `rfi_log`, `rfa_log` and `submittal_register` remain present, and
`reference_kind` returns None for individual forms, registers and monthly reports — asserted for
four filenames in the suite so the gate cannot widen unnoticed.

### The fault that did not fail, and what it changed

The first version of this check asserted the downstream outcome: status `filed`, class
`reference`, no stored extraction. With the skip removed it **stayed green**, because the
reference-storage branch further down still created the document row and the symptoms looked
identical. The check was measuring a consequence that had two possible causes.

Rewritten to assert the rule itself: `StubExtractor.calls` records every hash the extractor was
asked to read, and the check is that the specification's hash is absent from it, paired with a
positive control that an analysable document *is* present so the assertion cannot pass
vacuously. That version fails correctly:

```
FAIL  the analytical extractor was NEVER asked to read the specification  [3 call(s) made this run]
```

**The suite's own fixture was hiding this too.** It recorded an extraction for the specification
under a comment reading "documents the analytical extractor is never asked about" — the comment
stated the intent while the fixture guaranteed the opposite could not be detected. The recording
is gone. `StubExtractor` refuses an unknown hash rather than inventing one, so if anything ever
routes a specification back to the analytical path there is nothing to answer with and the
checks go red. Do not add a recording to make a failure go away.

## Test suites touched, and why

Four suites created scenarios with no evidence, which finding 3 now correctly forbids:
`test_admin_ops_t7t8`, `test_assignment_blinding`, `test_decision_sequence`,
`test_decision_ui_t4`. Each now supplies a real evidence project. In `test_decision_ui_t4` the
projects were created *after* the scenarios that name them, so that block moved above; the
ordering is the dependency made explicit, and nothing about what those projects are changed.

One existing check changed meaning: `test_files_tab` asserted `spec.doc_type == "unmapped"`, the
value the classifier returned after reading a specification. It no longer reads one, so the
check now asserts no type, no extraction and no model were recorded — a stronger statement, and
the one the design always claimed.

## Results

- **Server suite: 30/30 suites, 1649/1649 checks**, each against a fresh database migrated to
  head. `PYTHONIOENCODING=utf-8` set throughout. `DATABASE_URL` never pointed anywhere but a
  local throwaway SQLite file; production was not inspected or queried.
- **`tests_render.html`: 69/69** (was 62; 7 new over-the-wire checks).
- **`tests.html`: 51/51**, unchanged.

## Two traps this run hit, recorded so the next one does not

**A backup that was never written made a restore silently do nothing.** `cp x /tmp/b || cp x
$SCRATCH/b` succeeded on the first branch, so the fallback never ran; the later restore read
from the scratchpad path, found nothing, printed a `cp` error in a block whose output was not
being checked closely, and left the fault applied. The restore was only caught because the
baseline was re-measured afterwards and still showed the fault. **Re-measure the baseline after
every restore; do not treat the restore command's success as evidence.**

**`rm -f` on a SQLite file can silently fail while the file is locked on Windows**, so a suite
re-ran against a populated database and failed on leftover state that looked like a code defect.
Use a fresh filename rather than deleting.

Also still true, and it cost time again: a multi-line injection needle written with `\n` matches
nothing in these CRLF files. The assert on the needle count is what caught it before any partial
write happened.
