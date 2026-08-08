# Periods partitioned, and a period whose evidence changed recomputed

**Date:** 2026-08-08
**Branch:** `claude/period-assignment-and-recompute-1nfjnx`, from `origin/main` at `1434b57`
**Model:** Opus

**Verification:** server suite **49 suites, 2626/2626** (fresh migrated SQLite per test file; the
new `test_period_lifecycle.py` adds 35). `tests.html` **51/51**. `tests_render.html`
**204/205**, the one red being the pre-existing auth-gated "production read path" check that is
red on `origin/main` too. A real browser drive of the whole flow — state a period, upload,
compute, upload again into the computed period, run the control — **14/14**. Two faults injected
against the compound case, each confirmed applied, each detected, each reverted with a SHA-256
comparison, baseline re-run green after both.

**MIGRATION 0023 (`document_uploads.period_end`) IS UNAPPLIED IN PRODUCTION**, along with **0020
(`abstained_modules`), 0021 (`schedule_activities`) and 0022 (`upload_attempts`)** from earlier
sessions. All four are Lin's to run. No `DATABASE_URL` pointed anywhere but throwaway SQLite.
Production was neither inspected nor queried.

**Nothing under `server/app/simulation/` was modified.** No module's arithmetic changed. Nothing
recomputes in the browser.

---

## Status of this brief, stated plainly

**Both defects were fixed earlier in this same session and are already merged on `main`.** This
brief arrived as a combined restatement of two tasks already completed:

| Part | Landed as | On `main` |
|---|---|---|
| Part 3, the recompute skip | `8af1178` / merge `5fb0be7` | yes |
| Parts 1 and 2, period partitioning and the selector | `7023a28` / merge `1434b57` | yes |

Rather than re-report finished work, I verified the merged state holds and built the one thing
neither prior task covered: **the two fixes interacting.** That is where the byte-identical
invariant is actually at risk, because partitioning decides which documents a period holds and
staleness compares a stored result's record of its inputs against exactly that set. The new
`test_period_lifecycle.py` is this session's deliverable; everything else below is verification
and measurement re-run on the current `main`.

---

## LEAD: which of the two causes the partitioning failure was

**The first. The period was never assigned at upload; the compute path was never at fault.**

Assembly has filtered `DocumentUpload.period == period` strictly since migration 0013, and the
document reconciliation report already recorded that documents never leak across periods. What
never happened is the assignment. Every client either hardcoded `period: 1` or sent no period
key at all, and `_resolve_period` defaults a missing period to `1`:

| Surface | What it sent |
|---|---|
| Workspace "Period documents" panel | `period: 1`, hardcoded |
| Files tab | no period key at all |
| Project detail single-document ingest (`extractsignals`) | no period key at all |

Reproduced before anything was built, uploading four monthly reports dated March to June through
both real client shapes: `{1: 4}` in the store, `[1]` discovered, every trend reader abstaining.

**That the second candidate cause is not the live one is now also proven by fault, not only by
reading.** Removing the period filter from `_period_documents` — making compute take every
document the project holds, which is exactly the alternative hypothesis — turns the compound
suite to **27/35** with the byte-identical check red at byte 14793 and every period reporting
five source documents. The partition is load-bearing and the suite detects its loss.

### How a period is determined, and whether the two can disagree

**The period number** — `_resolve_period`, in order: a research assignment's `current_period`
(the only sequence-driven assignment on the platform), else `payload["period"]`, else **1**.
Training is separate and does not go through upload (`run.state["period"]`).

**The period cutoff** — `_derive_cutoff`: on a recompute the superseded row's cutoff is reused so
C1.2 Data Timeliness cannot drift; otherwise the maximum over every document's `document_date`
and every observation's `as_of` in that period; falling back to the server date when nothing
parses.

**They could disagree, and did.** The number is a stated integer, the cutoff a date derived from
content, and nothing related them — there was no stored notion anywhere of a period's date range.
The reproduction is the disagreement at its plainest: **period 1 with cutoff 2026-06-30**. Worse,
because selection is bounded `as_of <= cutoff`, all four months passed the filter and the latest
value won each snapshot field, so the project reported June's figures under the label "period 1"
and March, April and May were outvoted rather than being periods of their own.

## What the 84-document project computes as now

Built twice from identical documents — four reporting periods, 21 documents each: one monthly
report carrying the EVM figures plus twenty supporting documents.

| | Before | After |
|---|---|---|
| documents per period | `{1: 84}` | **`{1: 21, 2: 21, 3: 21, 4: 21}`** |
| periods computed | `[1]` | **`[1, 2, 3, 4]`** |
| cost performance series at the last period | `None` | `[0.909, 0.909, 0.893, 0.87]` |
| modules computed at the last period | 36 | **40** |
| trajectory classifier in the portfolio snapshot | absent | present |

Each period now carries its own cutoff (2026-03-31, 2026-04-30, 2026-05-31, 2026-06-30) instead
of one cutoff of 2026-06-30 covering everything.

## Which modules newly compute

Four analytical modules, plus one portfolio-level reader, and nothing was lost:

- **the control-chart anomaly monitor**
- **the schedule-performance smoother**
- **the cost-performance forecast reader**
- **the regression-to-mean reader**
- and in the portfolio snapshot, **the signal trajectory classifier**

**Milestone Trend Analysis still abstains, and the period defect was not the whole of what held
it back.** It needs two or more schedule snapshots, which requires documents carrying a readable
activity table; this fixture is monthly reports and supporting paperwork with no schedule table,
so there is nothing to assemble. That is the module's own guard working.
`test_schedule_milestones.py` (75/75, untouched) proves it computes at the second period when the
periods are distinct **and** schedules are present — a state that was unreachable before, since
every schedule document used to land in one period too. Honest summary: the period defect was
what held the four trend readers back, and it was *a* precondition for milestone trend rather
than the whole of it.

## Where the period selector went

**Two surfaces carry it; a third is reported rather than changed.**

1. **The Workspace "Period documents" panel** — the primary home. Its card is titled *Period
   documents* and it already carried the per-period compute button and status read.
2. **The Files tab** — the same two controls. It sent no period at all, and
   `REPORT_2026-08-05_project-not-computed.md` recorded PMs uploading through it, so leaving it
   would have fixed one surface and left the defect live on another.
3. **The project detail single-document ingest** — **not changed, and reported.** Legacy
   one-document path with no period notion of its own; it still reaches the server default.

Each selector is two controls: **Reporting period** (a number) and **Period ending** (a date).
The panel's compute and status reads now follow the stated period too.

**The cutoff is yielded through the partition, not set from the selector**, and `_derive_cutoff`
is untouched. Once documents are partitioned correctly, each period's cutoff is its own latest
evidence date — which is what the derivation always meant and could never produce while every
document sat in one period. Setting it from the stated ending date was rejected for two reasons,
both already-asserted invariants: it would break the `docDate == period_cutoff` check on a first
compute, and since selection is `as_of <= cutoff` it would silently exclude the observations of
the very document the out-of-period flag exists to report.

## What decides that a period is stale

**The stored result's own record of its inputs, compared against the period's current documents.
Not a timestamp.**

Every `computed_results` row carries `source_documents` (migration 0013): the exact
`{document_id, sha256, doc_type, filename}` set assembly consumed. A period is stale when
`{(document_id, sha256)}` from that record differs from the same set over `_period_documents`.

Three things were available and this is the strongest:

| Available | Why not used as the decision |
|---|---|
| `document_uploads.uploaded_at` | a wall clock; it moves on a re-upload the unique index makes a no-op, and answers "was there activity", not "is the result built from different evidence" |
| `observations.as_of` | the date the evidence speaks about, NULL wherever nothing parses, so a new undated document would be invisible |
| **`computed_results.source_documents`** | **used** — inputs versus inputs, with no inference between them |

The brief's own reasoning is why: a revised document can carry the same date as the one it
replaces. Content addressing catches that where a timestamp cannot. A row with NULL
`source_documents` (pre-0013) is skipped **with that stated as the reason** rather than guessed
at.

**A changed earlier period invalidates the later ones.** The series readers take earlier periods'
stored results as input, so a flag, once set by any period that computed or recomputed, forces
every later period to recompute regardless of its own document set. The loop already ran
ascending. The cutoff follows the reason: re-derived when the period's own documents changed,
reused from the superseded row when only an earlier period did.

**The same skip existed on the Workspace per-period button** (`a_projectcompute` tested only that
a live result existed and pointed at `adminrecompute`) and was fixed with it.

---

## The compound case, which is this session's new work

`server/tools/test_period_lifecycle.py`, **35 checks**. Four stated periods, then a further
document uploaded into period **two**, which already has a result, then the control run:

```
period 1  skipped      documents unchanged since last computation
period 2  recomputed   1 document(s) added since the last computation
period 3  recomputed   an earlier period was recomputed, invalidating series inputs
period 4  recomputed   an earlier period was recomputed, invalidating series inputs
```

Asserted: only period two gained a document, so the partition held; period one is byte-identical
**and keeps its `result_id`**; period two's stored figures moved and its result records both of
its documents; periods three and four were rewritten; each period still sees exactly its own
number of series points and none from later; the cascade's series carries period two's **new**
figure rather than its superseded one; and a third run with nothing changed skips all four and
leaves every payload and every `result_id` untouched.

**The `result_id` check earns its place, and a fault proved it.** Fault 1 makes the cascade
rewrite period one as well. The byte-comparison of period one **still passes** — recomputing
unchanged evidence correctly reproduces the payload, which is the invariant working — but the
`result_id` check goes red, catching a period being rewritten when it should have been left
alone. A payload comparison alone would have missed it.

### A fixture correction worth recording

The first run failed one check: period two's cost performance did not move. That was the platform
behaving correctly, not a defect. Both documents were the same type carrying the same date, so
the equal-date tiebreak resolved by content hash and the original won — exactly as the storage
redesign documents. The fixture had assumed a recency it had not given the new document. Dating
each period's report mid-period and the revision at the period end makes the later document win
on recency, which is what a real revision does, and keeps the check about recompute rather than
about a hash.

## Proof each check can fail

Two faults against the compound suite, each anchor matching exactly once, each confirmed applied
before its run, each reverted with a SHA-256 comparison, baseline 35/35 after both.

| Fault | Result | What went red |
|---|---|---|
| the cascade rewrites period one as well | **27/35** | period one's `result_id` changes, the message no longer says "unchanged", and the settled-state run recomputes all four |
| the period filter is removed from `_period_documents` (the rejected second cause, injected) | **27/35** | period one's byte comparison at byte 14793, and every period reports five source documents |

Earlier in the session, four faults were proven against the recompute suite (22/36, 32/37, 24/38,
35/39) and four against the assignment suite (6/14, 39/45, 6/13, 4/8 browser), each detected and
reverted with the baseline re-run green.

**The interpreter was confirmed real before any green was believed**: `/readyz` reported
`schema at head 0023_upload_period_end` and `/healthz` reported Python 3.11.15, so every drive
ran against a migrated database on the pinned interpreter.

## Driven in a real browser

Headless Chromium with `--use-gl=swiftshader --enable-webgl --ignore-gpu-blocklist`, the Google
SSO script aborted at the route layer, `window.confirm` stubbed to false, against the real
application on a throwaway SQLite instance. **14/14.**

State period 2 with an ending date of 2026-04-30 in the selector; drop two files; both land in
period 2 and none in period 1. The document dated 2026-12-31 is named on screen:

> 1 document(s) are dated outside the reporting period you filed them to. They have been stored
> in that period. Check whether this is a filing mistake.
> OUT.pdf: dated 2026-12-31, which is after the 2026-04-30 end of the reporting period it was
> filed to

Press the panel's compute button: *"Computed. Project status: Amber"*, and a result is stored for
period 2. Upload a further document into that same computed period and run the all-periods
control:

> period 2: 1 document(s) added since the last computation

A new result row is stored and the figures change. The model call was not stubbed in the server
the browser talked to — the extractions were pre-placed in the content-addressed cache, so the
uploads were genuine sha256 cache hits on the real upload path.

## Open, and flagged rather than built

- **The server still defaults a missing period to 1.** Both UI surfaces now always state one, so
  the default is reachable only by a direct API call or the legacy single-document ingest. It is
  the one remaining place a period is inferred, and it is the mechanism this defect ran through.
- **Nothing backfills the existing 84-document project.** Its documents are all in period one in
  the database and this change does not move them, because which document belongs to which period
  is exactly the judgement the platform must not make. Re-filing means re-uploading each period's
  set with its period stated, or an admin operation that does not exist. **Worth deciding before
  the next real project is loaded**, because the fix prevents the defect rather than repairing
  its results.
- **The period selector is a typed number** and does not know which periods a project already
  has, so a typo files to period 7 of a four-period project and creates one.
- **A recompute cascade is unbounded work behind one button press.** A twelve-period project
  whose period 1 changes recomputes all twelve serially in one request, with no progress
  reported.
- **Abstention messages are still discarded before storage** (`registry.py` `run_all()`), so a
  module that genuinely did not compute cannot say why. Unchanged, and still a
  `server/app/simulation/` change.

## Files changed

**This session:** `server/tools/test_period_lifecycle.py` (new),
`REPORT_2026-08-08_period-assignment-and-recompute.md` (new), `T6_HANDOFF.md`.

**Already on `main` from earlier in this session**, listed because this report covers them:
`server/alembic/versions/0023_upload_period_end.py`, `server/app/research_models.py`,
`server/app/documents.py`, `index.html`, `assets/js/workspace.js`, `assets/js/files.js`,
`assets/js/detail.js`, `assets/css/radar.css`, `server/tools/test_period_assignment.py`,
`server/tools/test_stale_period_recompute.py`.

No file under `server/app/simulation/` was modified. Nothing outside `DEng\LinPRojectRadar` was
touched, and nothing was deleted or moved outside it.
