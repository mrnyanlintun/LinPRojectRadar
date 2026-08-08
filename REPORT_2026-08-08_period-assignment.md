# 84 documents in one period: nothing ever assigned a period

**Date:** 2026-08-08
**Branch:** `claude/period-assignment-1nfjnx`, from `origin/main` at `6818b67`
**Model:** Opus

**Verification:** server suite **48 suites, 2591/2591** (fresh migrated SQLite per test file; the
new `test_period_assignment.py` adds 45). `tests.html` **51/51**. `tests_render.html`
**204/205**, the one red being the pre-existing auth-gated "production read path" check that is
red on `origin/main` too. A real upload driven in headless Chromium: **8/8**. Four faults
injected, each confirmed applied before its run, each detected, each reverted with a SHA-256
comparison, and the baseline re-run green after every one.

**MIGRATION 0023 (`document_uploads.period_end`) IS UNAPPLIED IN PRODUCTION.** So are **0020
(`abstained_modules`), 0021 (`schedule_activities`) and 0022 (`upload_attempts`)** from the
prior sessions. All four are Lin's to run. No `DATABASE_URL` pointed anywhere but throwaway
SQLite. Production was neither inspected nor queried.

**Nothing under `server/app/simulation/` was modified.** No module's arithmetic changed. Nothing
recomputes in the browser.

---

## LEAD: which of the two it was

**The first. The period is never assigned at upload, and everything lands in period one by
default. Compute was never at fault.**

Assembly has always been strictly per period. `_period_documents` filters
`DocumentUpload.period == period` and has since migration 0013; the document reconciliation
report already recorded that "documents never leak across periods". The compute path reads
exactly the period it is asked for.

What never happened is the assignment. Every upload surface in the client either sent
`period: 1` or sent no period at all, and `_resolve_period` defaults a missing period to `1`:

| Surface | What it sent |
|---|---|
| Workspace "Period documents" panel (`workspace.js`) | `period: 1`, hardcoded |
| Files tab (`files.js`) | no period key at all |
| Project detail single-document ingest (`signals.js` → `extractsignals`) | no period key at all |

`extractsignals` is an adapter over `a_projectupload` and inherits the same default. So a
project's entire document history landed in period one, and the all-periods control, which
discovers periods with `select(DocumentUpload.period).distinct()`, correctly reported the one
period that existed.

**Reproduced before anything was built**, uploading four monthly reports dated March to June
2026 through both real client shapes:

```
A. no period key at all      -> the server filed it to period 1
B. period: 1 hardcoded       -> M2 (2026-04-30) -> period 1
                                M3 (2026-05-31) -> period 1
                                M4 (2026-06-30) -> period 1
documents per period : {1: 4}
periods discovered   : [1]
period_cutoff stored : 2026-06-30
cpiHistory           : None
CUSUM / Kalman / ARIMA / Regression to Mean : all False
```

## How a period is determined at all, and whether the two can disagree

**What sets the period number** — `_resolve_period(session, project, payload)`, in order:

1. **A research assignment**, where one exists: the period is derived server-side from
   `current_period(assignment)` and the payload is ignored entirely. This is the only
   sequence-driven assignment on the platform and it is real.
2. **The payload's `period`**, for a project with no assignment.
3. **Otherwise `1`.**

Training is the fourth case and does not go through upload at all: `training.py` `_store_period`
passes `run.state["period"]` straight to `run_and_store`.

So outside the research chain, nothing assigned a period. The Workspace button's hardcoded
period 1 was not an isolated oddity; it was the whole of the mechanism.

**What sets the period cutoff** — `_derive_cutoff(documents, reuse)`:

- on a recompute, the superseded row's cutoff is reused, so C1.2 Data Timeliness cannot drift;
- otherwise it is the **maximum** over every document's `document_date` and every observation's
  `as_of` in that period;
- falling back to the server date when nothing carries a parseable date (D3, unchanged).

**Can they disagree? Yes, structurally, and they did.** The number is an integer somebody states
or defaults into; the cutoff is a date derived from content. Nothing related them, and there was
no stored notion anywhere of what date range a period covers — no `period_start`, no
`period_end`, no reporting-period table. The reproduction above is the disagreement in its
plainest form: **period 1, cutoff 2026-06-30**. Worse, because selection is bounded
`as_of <= cutoff`, all four months of evidence passed the filter and the latest value won each
snapshot field, so the project reported June's figures under the label "period 1" and March,
April and May were outvoted rather than being periods of their own.

---

## What the 84-document project computes as now

Built twice from the identical 84 documents (four reporting periods, 21 documents each: one
monthly report carrying the EVM figures plus twenty supporting documents), once the way every
client uploaded before this change and once with the period stated.

| | Before | After |
|---|---|---|
| documents per period | `{1: 84}` | `{1: 21, 2: 21, 3: 21, 4: 21}` |
| periods computed | `[1]` | `[1, 2, 3, 4]` |
| cost performance series at the last period | `None` | `[0.909, 0.909, 0.893, 0.87]` |
| modules computed at the last period | 36 | **40** |
| trajectory classifier in the portfolio snapshot | absent | present |

**84 documents, four periods, 21 documents in each.** Each period's cutoff is now its own
evidence date (2026-03-31, 2026-04-30, 2026-05-31, 2026-06-30) rather than one cutoff of
2026-06-30 covering everything.

## Which modules newly compute

Four, plus one portfolio-level reader, and nothing was lost:

- **the control-chart anomaly monitor** (CUSUM)
- **the schedule-performance smoother** (Kalman filter)
- **the cost-performance forecast reader** (ARIMA)
- **the regression-to-mean reader**
- and in the portfolio snapshot, **the signal trajectory classifier**, which needs two
  snapshots of this project's own stored figures

**Milestone Trend Analysis still abstains, and the period defect was not the only thing holding
it back.** It needs two or more schedule snapshots from `schedule_activities`, which requires
documents carrying a readable activity table; the 84-document fixture is monthly reports and
supporting paperwork with no schedule table, so `milestoneHistory` has nothing to assemble. That
is the module's own guard working. `test_schedule_milestones.py` (75/75, untouched) already
proves it computes at the second period when the periods are distinct and schedules are present,
which is now reachable in a way it was not before, since every schedule document used to land in
one period too.

Stated plainly: the period defect was what held the four trend readers back, and it was *a*
precondition for milestone trend rather than the whole of it.

---

## Where the period selector went, and why

**Two surfaces got it, and a third is reported rather than changed.**

1. **The Workspace "Period documents" panel** — the primary home. Its card is titled *Period
   documents*, and it already carries the per-period compute button and the per-period status
   read. It is the surface whose entire purpose is filing a reporting period's documents, so a
   selector belongs there more than anywhere else.
2. **The Files tab** — the same two controls. This surface sent no period at all, and it is not
   hypothetical traffic: `REPORT_2026-08-05_project-not-computed.md` recorded PMs uploading
   through it. Leaving it silently defaulting would have fixed the defect on one surface and
   left it live on another, which is the half-fix this task exists to avoid.
3. **The project detail single-document ingest** (`signals.js` → `extractsignals`) — **not
   changed, and reported.** It is the legacy one-document path, it has no period notion of its
   own, and giving it one is a larger change to a surface whose other problems are already on
   record. It still reaches the server default. Flagged below.

Each selector is two controls: **Reporting period** (a number, minimum 1) and **Period ending**
(a date). Both are sent with the upload.

The compute and status reads on the Workspace panel now follow the same stated period, because a
panel that uploads to period 3 while reporting period 1's status would be its own defect.

## How the selector yields both a number and a cutoff

The brief required that whatever the selector produces yields both the period number and the
period cutoff, consistent with how the cutoff is derived today.

- **The number** is stated directly and stored on `document_uploads.period`, as before.
- **The cutoff is yielded through the partition, not set directly**, and `_derive_cutoff` is
  unchanged. Once documents are correctly partitioned, each period's cutoff is the latest date
  its *own* evidence speaks about — which is exactly what the derivation always meant and could
  never produce while every document was in one period. The four-period project now stores four
  distinct cutoffs, asserted by a check.

**Setting the cutoff from the stated ending date instead was considered and rejected for two
reasons, both of which are already-asserted invariants:**

1. The storage redesign established that on a first compute `docDate` and `period_cutoff` are
   the same number, and a check asserts it. `docDate` is the latest `as_of` among the period's
   observations; a stated ending date would differ from it whenever the last document is not
   dated exactly on the period end, turning that check red for no gain.
2. Selection is bounded `as_of <= cutoff`. A document flagged as dated *after* its period would
   have its observations silently excluded — which is the "silently overridden" outcome the flag
   exists to prevent.

So `period_end` decides nothing about the analysis. It is what the out-of-period check is
measured against, and nothing else. That separation is stated in the migration and in the model.

## A document dated outside its period is flagged, stored, and not moved

The window is bounded by two dates a person stated: this upload's `period_end` above, and the
latest `period_end` among the project's earlier periods below. Where a bound is unknown it is
not enforced, because a guessed boundary produces a warning nobody can act on. Where no ending
date is stated at all, the check says nothing.

Read off the real page in the browser drive, verbatim:

```
1 document(s) are dated outside the reporting period you filed them to. They have been stored
in that period. Check whether this is a filing mistake.

OUT.pdf: dated 2026-12-31, which is after the 2026-04-30 end of the reporting period it was
filed to
```

The document extracted normally, was stored in period 2 as stated, and was not moved to a period
its date fits. A document dated into an *earlier* period is caught by the lower bound with its
own wording. The flag also rides on each file's own result row, so the Files tab shows it beside
that document's filing outcome.

---

## The invariant, and the confounded check that nearly hid a non-problem

**Recomputing period one after periods two, three and four exist is byte-identical.** Asserted
on the four-period project, with `result_id` and `computed_at` excluded by name for the reason
three prior sessions have recorded, and with a check that the recomputed period one still has no
series so the later periods demonstrably did not reach it.

**It failed on first run, and the diagnosis matters.** The differing field was
`portfolio_snapshot`, which moved from insufficient-data to `portfolio_size: 2`. The cause was my
own fixture: the suite created two *other* projects, carrying results at cutoffs at or before
period one's, **between** capturing the bytes and recomputing. The portfolio is cutoff-aligned
across projects by design — the P1 rule from the storage redesign includes every other project's
latest live result at or before this computation's cutoff — so those projects legitimately
joined period one's portfolio. That is the design working, and it is a different question from
the one the invariant asks.

The check now runs while the four-period project is the only one with results, which is the
stated invariant: later periods **of the same project**. The reason is recorded in the suite so a
future edit does not reintroduce the confound by reordering it.

## Proof each check can fail

Four faults, each anchor matching exactly once, each confirmed applied before the run, each
reverted with a SHA-256 comparison against the original, baseline re-run green after every one.
The suite's total moves under some faults because later sections stop reaching their assertions,
which is itself visible.

| Fault | Result | What went red |
|---|---|---|
| the server ignores the stated period and files everything to 1 (the defect, reproduced) | **6/14** | `{1: 4}` in the store, one period discovered, four documents in period one |
| the out-of-period check never fires | **39/45** | every flagging check, and the summary count |
| a flagged document is silently moved to the period its date fits | **6/13** | every "filed to the period stated" check, immediately |
| the client sends `period: 1` again (browser) | **4/8** | the documents land in period one and no notice is drawn |

Baselines 45/45 and 8/8 before and after every fault. The first and fourth are the reported
defect reproduced as failing checks on each side of the wire; the third is the guard against
"fixing" a mismatch by moving the document, which the brief explicitly forbids.

**The interpreter was confirmed real before any green was believed**: the server's `/readyz`
reported `schema at head 0023_upload_period_end`, so every drive ran against a migrated database
rather than a silently degraded one.

## What changed in code

- **`server/alembic/versions/0023_upload_period_end.py`** (new) — `document_uploads.period_end`,
  nullable, with the reasoning for both the nullability and the separation from the cutoff.
- **`server/app/research_models.py`** — the column.
- **`server/app/documents.py`** — `_parse_iso_date`, `_previous_period_end` and `_out_of_period`,
  new; `a_projectupload` reads and stores the stated ending date, computes the per-document flag,
  and returns `period_end`, `date_mismatches` and a per-file `period_date_mismatch`.
- **`index.html`** — the selector on both upload surfaces, plus the notice hosts.
- **`assets/js/workspace.js`** — sends the stated period; compute and status reads follow it;
  renders the mismatch notice.
- **`assets/js/files.js`** — the same selector, and the mismatch shown on each file's row.
- **`assets/css/radar.css`** — the picker layout.

No module id or number appears in any string added; no em dashes in user-facing text.

## Open, and flagged rather than built

- **The server still defaults a missing period to 1.** Both UI surfaces now always state one, so
  the default is reachable only by a direct API call or by the legacy single-document ingest.
  It is the one remaining place a period is inferred, and it is the mechanism this whole defect
  ran through. Making it a refusal is a contract change for `extractsignals` and wants a
  decision.
- **The project detail single-document ingest has no selector**, as above.
- **Nothing backfills the 84-document project.** Its documents are all in period one in the
  database, and this change does not move them: which document belongs to which period is
  exactly the judgement the platform must not make. Re-filing them means re-uploading each
  period's set with its period stated, or an admin operation that does not exist. **Worth
  deciding before the next real project is loaded**, because the fix prevents the defect rather
  than repairing its results.
- **The period selector does not know which periods a project already has.** It is a number the
  person types, so a typo files a document to period 7 of a four-period project and creates one.
  Populating it from the project's existing periods needs a per-project period list the server
  does not currently serve.

## Files changed

`server/alembic/versions/0023_upload_period_end.py` (new), `server/app/research_models.py`,
`server/app/documents.py`, `index.html`, `assets/js/workspace.js`, `assets/js/files.js`,
`assets/css/radar.css`, `server/tools/test_period_assignment.py` (new), `T6_HANDOFF.md`, this
report.

No file under `server/app/simulation/` was modified. Nothing outside `DEng\LinPRojectRadar` was
touched, and nothing was deleted or moved outside it.
