# A period with new documents is recomputed, not skipped

**Date:** 2026-08-08
**Branch:** `claude/period-recompute-new-docs-1nfjnx`, from `origin/main` at `3d77a6f`
**Model:** Opus

**Verification:** server suite **46 suites, 2517/2517** (fresh migrated SQLite per test file; the
new `test_stale_period_recompute.py` adds 39). `tests.html` **51/51**. `tests_render.html`
**184/185**, the one red being the pre-existing auth-gated "production read path" check, which was
re-run on a clean `origin/main` in the same browser session and is red there too. A real headless
Chromium drive of the actual application: **12/12**. Four faults injected, each confirmed applied
by SHA-256 before its run, each detected, each reverted with a SHA-256 comparison, and the
baseline re-run green after every one.

**No migration was written and none is needed: this task added no column and no table.** The
migrations still unapplied in production are unchanged from the previous sessions: **0020
(`abstained_modules`), 0021 (`schedule_activities`) and 0022 (`upload_attempts`)**. Those remain
Lin's to run. No `DATABASE_URL` pointed anywhere but throwaway SQLite. Production was neither
inspected nor queried.

**Nothing under `server/app/simulation/` was modified.** No module's arithmetic changed. Nothing
recomputes in the browser.

---

## LEAD: what the platform uses to decide a period is stale

**It compares the stored result's own record of its inputs against the period's current
documents. It does not compare timestamps.**

Every `computed_results` row already carries `source_documents` (migration 0013): a list of
`{document_id, sha256, doc_type, filename}`, written from the live document set that assembly
actually consumed. The period's current evidence is `_period_documents`, the same function the
computation itself reads. Staleness is the comparison of those two as sets of
`(document_id, sha256)` pairs:

```
stored  = {(document_id, sha256) for each entry in result.source_documents}
current = {(document_id, sha256) for each document in _period_documents(project, period)}
stale   = stored != current
```

**Three things were available and this is the strongest of them**, which is the choice the brief
asked to be established rather than assumed:

| Available | What it answers | Why not used as the decision |
|---|---|---|
| `document_uploads.uploaded_at` | when a file was filed | A wall clock. It answers "was there activity", not "is the result built from different evidence". A re-upload of an identical file is a no-op by unique index, yet its clock moves. |
| `observations.as_of` | the date the evidence *speaks about* | Deliberately not the upload clock, and NULL where nothing parses. A new document carrying no parseable date would be invisible to it. |
| **`computed_results.source_documents`** | **exactly which document versions produced this result** | **Used.** It is the result's own statement of what it was computed from, so the comparison is inputs-versus-inputs with no inference in between. |

The brief said comparing a stored result's own record of its inputs against the period's current
documents is stronger than comparing timestamps, *if that is available*. It is available, it is
what `source_documents` was built for, and it is what this uses.

**It is content-addressed, so it catches all three ways evidence changes**, not just addition: a
document added, a document removed, and a revision that supersedes another (the superseding
upload changes the live set, so the pair set changes). The reported reason distinguishes added
from removed/replaced and states the count.

**A row with no `source_documents` is left alone, not guessed at.** The column is NULL on rows
computed before migration 0013. There is no record of what those were built from, so no
comparison is possible, and the honest outcome is to skip with that stated rather than to recompute
on the assumption that absence means change. This is the one case where the platform declines to
answer instead of guessing.

## Whether the Workspace per-period button had the same defect

**Yes. Identical defect, same shape, on the other surface. Fixed with it.**

`a_projectcompute` — the action behind the Workspace panel's "Run analysis for this period"
button, and the only caller of it anywhere in the client — did this:

```python
existing = _live_result(session, project, period)
if existing is not None:
    return {..., "recomputed": False,
            "note": "a computed result already exists for this period; use adminrecompute "
                    "to replace it"}
```

The test that a live result *exists* was the whole test. A PM who uploaded into a computed period
and pressed that button got the same false reassurance as the all-periods control gave, phrased
slightly differently. It now runs the same staleness comparison and recomputes when the documents
have moved.

**This was established by reading both call paths, and then proven twice**: the suite drives the
per-period action against a project whose computed period gains a document (section 5), and Fault
4 — restoring the old unconditional skip on `a_projectcompute` alone — turns exactly those checks
red and leaves the all-periods checks green. The two surfaces are independently covered.

**The button's hard-coded `period: 1` was not changed.** It is a separate, already-recorded
limitation (`REPORT_2026-08-05_unbounded-schedule.md` Part 5) and fixing it is a period-selector
question, not a staleness question.

---

## What was built

`server/app/documents.py`:

- **`_document_fingerprint(documents)`** and **`_result_fingerprint(result)`** — new. The
  period's current live set and the stored result's recorded set, each reduced to
  `{(document_id, sha256)}`. `_result_fingerprint` returns None when the row carries no record.
- **`_period_is_stale(session, project, period, result)`** — new. Returns `(is_stale, reason)`.
  The reason is the sentence the user is shown, not a code.
- **`a_projectcomputeall`** — a period that already has a result is now recomputed when stale and
  skipped when not, instead of always skipped. The recompute supersedes the old row and inserts
  the new one under a pre-minted ULID, which is the same append-only, one-live-row-per-period
  discipline `adminrecompute` uses and the partial unique index requires.
- **`a_projectcompute`** — the same staleness test on the per-period path.

**Forward invalidation.** The series readers (`_period_history`, `_period_snapshots`,
`_milestone_history`) take earlier periods' stored results as their input, so a recomputed period 1
changes what period 2 and period 3 were computed from. An `earlier_recomputed` flag, once set by
any period that computed or recomputed, forces every later period to recompute regardless of its
own document set. The loop already ran ascending, so "recompute forward from the earliest changed
period" is what the flag expresses.

**The cutoff rule follows the reason for the recompute**, which matters for reproducibility:

- Recomputed because **its own documents changed** — the cutoff is re-derived from the new
  document set. The period's evidence is different, so the date its evidence speaks to may be too.
- Recomputed only because **an earlier period changed** — the cutoff is reused from the superseded
  row. This period's own evidence did not move, and re-deriving would drift C1.2 Data Timeliness
  for a reason unrelated to the recompute.

`assets/js/detail.js` and `assets/js/workspace.js`: the messages. See below.

## The message says what changed, per period

The old message counted:

> 0 period(s) computed, 1 already had a result and were left untouched
> (periods computed in order: 1)

The new one names. Read off the real browser drive, verbatim from the page:

> 1 period(s) recomputed: period 1 (1 document(s) added since the last computation)
> (periods in order: 1).

and on a second press with nothing changed:

> 1 period(s) unchanged, left untouched (periods in order: 1).

The three outcomes are distinct and each carries its reason: computed for the first time,
recomputed with what changed, or unchanged and left alone. The per-period reasons come from the
server on each result entry, so the browser reports the server's finding rather than composing
its own account of it. The Workspace button's note reports its recompute and reason the same way.

## The invariant that governs this, and that it still holds

**Recomputing a period whose evidence has not changed is byte-identical to its stored result.**

Held, and checked in two directions rather than asserted:

1. **A skipped period is not touched at all.** After a run in which other periods recomputed, the
   unchanged periods' stored payloads compare byte-identical *and* their `result_id`s are
   unchanged — so the period was not superseded-and-reinserted with identical content, it was
   genuinely left alone.
2. **A recompute on unchanged inputs reproduces the row.** Period 2 is recomputed through
   `adminrecompute` and compared byte for byte.

What "byte-identical" compares is unchanged from the three prior sessions that established it:
`period`, `signal_inputs`, `module_results`, `category_statuses`, `project_status`,
`portfolio_snapshot`, `simulation_version`, `seed`, `period_cutoff` and `source_documents`, via
`json.dumps(sort_keys=True)`, with `result_id` and `computed_at` excluded **by name** because a
recompute is a new append-only row required to have a new id.

**It is a check that can fail, and the fault that proves it is the dangerous one.** Fault 3
reverses the staleness test so an *unchanged* period recomputes. It turns red exactly the checks
that protect this invariant — `all three periods skipped [computed=2, skipped=1]` and
`period 2 result_id unchanged` / `period 3 result_id unchanged`. That is the guard against the
failure mode the brief named: a recompute that silently moves an untouched period's result.

**No untouched period's result differed at any point in this work**, so the stop condition the
brief set was never reached.

**Periods still compute in order, and each still sees only itself and earlier periods.** Nothing
about the ascending loop or the selection bounds changed. `test_period_series.py` (40/40) and
`test_unbounded_schedule.py` (87/87), which are the suites that own that property and its own
byte-identical checks, are green and unmodified.

## Proof each check can fail

Four faults, each anchor matching exactly once, each confirmed applied by SHA-256 before the run,
each reverted with a SHA-256 comparison against the original, baseline re-run green after every
one. The suite's total moves between faults because four checks are emitted per recomputed period;
a fault that suppresses recomputes emits fewer, which is itself visible.

| Fault | Result | What went red |
|---|---|---|
| staleness detection disabled (the reported defect, reproduced) | **22/36** | the period is skipped, the result does not change, the new document never reaches `source_documents` |
| forward invalidation disabled | **32/37** | only the cascade to periods 2 and 3; period 1's own recompute still correct |
| staleness reversed (unchanged recomputes, changed skips) | **24/38** | **the byte-identical/untouched checks**, including both `result_id unchanged` checks |
| the per-period button keeps the old unconditional skip | **35/39** | only the Workspace-button checks; the all-periods checks stay green |

Baseline 39/39 before and after every fault. The first fault is the reported defect reproduced
exactly: the suite reports the period skipped, `same=True` on the result, and `['A1.pdf']` as the
only source document — which is the user's complaint, stated as a failing check.

## Driven in a real browser

Headless Chromium with `--use-gl=swiftshader --enable-webgl --ignore-gpu-blocklist`, against the
real FastAPI application on a throwaway SQLite instance, with the parser-blocking Google SSO
script aborted at the route layer and `window.confirm` stubbed to return false. **12/12.**

The drive is the reported scenario: a project whose period 1 already holds a stored result
(Amber, cpi 0.909), a further monthly report uploaded **into that same computed period** through
the application's own upload action, then the actual `[data-compute-all]` button clicked in the
DOM. Read back afterwards, from the page and from the store:

- the on-screen message names the recompute and what changed (quoted above),
- a **new** `result_id` was stored, the old one superseded,
- **the stored result moved: cpi 0.909 to 0.694**, so the new document reached the analysis
  rather than only the message,
- `D2.pdf` appears in the recomputed result's `source_documents`,
- and a second press with nothing changed reports "unchanged, left untouched" and does **not**
  move the stored result.

**The model call was not stubbed away by a test seam in the server.** The second document's
extraction was placed in the content-addressed `documents` cache beforehand under a different
project, so the browser's upload was a genuine cache hit on the real `a_projectupload` path —
the platform's documented "hash already in `documents`, reuse the stored extraction, no model
call" behaviour, exercised rather than bypassed. No extractor override was installed in the
server process the browser talked to.

**The interpreter was confirmed real before any green was believed**: the server's own
`/healthz` reported Python 3.11.15 and `/readyz` reported `schema at head 0022_upload_attempts`,
so the suite ran against a migrated database on the pinned interpreter rather than a silently
degraded one.

## What was deliberately not changed

- **`adminrecompute` is untouched.** It remains the audited, reason-bearing way to replace a
  result whose *inputs have not changed* — a re-run after a simulation-version change, for
  instance. This task did not make it redundant; it made it unnecessary for the one case where
  the reason is already on record in the evidence itself.
- **The research-account gate on `projectcomputeall` is unchanged**, both in the action and in
  `features.RESEARCH_FORBIDDEN_ACTIONS`. A staleness recompute is still not something a research
  participant may do to their own study data.
- **The Workspace button's hard-coded period 1**, as above.
- **`server/app/simulation/`**, and the stale `VALIDATION.md` line 214 noted by two prior
  sessions, both untouched for the reason those sessions gave.

## Open, and flagged rather than built

- **A period is only recomputed when someone presses a control.** Upload still does not compute;
  that is the separate, already-reported gap
  (`REPORT_2026-08-05_project-not-computed.md`). What changed here is that pressing the control
  after an upload now does the right thing. A PM who uploads and presses nothing still has a
  stale result, and nothing on the page yet says so. **Showing "this period's documents have
  changed since it was computed" as a state on the period surface is the natural next piece**,
  and it is a read of the same comparison this task added — no new storage required.
- **A recompute cascade can be long.** A project with twelve periods whose period 1 changes
  recomputes all twelve, serially, in one request. That is correct and is what the series
  invariant requires, but it is unbounded work behind one button press and no progress is
  reported. Worth a look before a project with many periods meets it.
- **The NULL `source_documents` case is skipped with a stated reason.** No row in this
  environment carries a NULL, so the branch is reasoned about rather than exercised against real
  legacy data. If production holds pre-0013 rows, they will skip until they are recomputed once
  by any other route.

## Files changed

`server/app/documents.py`, `assets/js/detail.js`, `assets/js/workspace.js`,
`server/tools/test_stale_period_recompute.py` (new), `T6_HANDOFF.md`, this report.

No file under `server/app/simulation/` was modified. No migration was added. Nothing outside
`DEng\LinPRojectRadar` was touched, and nothing was deleted or moved outside it.
