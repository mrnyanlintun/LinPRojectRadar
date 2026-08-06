# The schedule: parsed, refused where it must be, stored per period, and compared

**Date:** 2026-08-05
**Branch:** `claude/schedule-milestones-s5s90m` (merged to `main`, commit `bb382fc`, PR #222)
**Verification:** server suite **43 suites, 2365/2365** (fresh migrated SQLite per test file; the new `test_schedule_milestones.py` adds 75), `tests.html` **51/51**, `tests_render.html` **169/170** (the one red is the pre-existing auth-gated "production read path" check, red on `origin/main` too). Five faults injected against the new suite, each confirmed applied by SHA before the run, each detected, each reverted with a SHA comparison and the baseline re-run green.

**Migrations unapplied in production: 0021 (`schedule_activities`, added here) AND 0020 (`abstained_modules`, added last session).** No `DATABASE_URL` pointed anywhere but throwaway SQLite. Production was neither inspected nor queried.

**Nothing under `server/app/simulation/` was modified.** No module's arithmetic changed. The granted exception was not needed.

---

## LEAD: which date shapes parse, and which refuse

The whole platform had exactly one date parser, `date.fromisoformat`, which accepts strict `YYYY-MM-DD` and nothing else. `server/app/schedule_dates.py` is new and is the schedule's parser. Every shape below is asserted in the suite **against its resolved calendar date**, not against "it returned something".

### Parses

| Shape | Example | Resolves to | Kind |
|---|---|---|---|
| day-month-two-digit-year with the actual marker | `24-Mar-26 A` | 2026-03-24 | **actual** |
| day-month-two-digit-year | `24-Mar-26`, `12-Jan-26` | 2026-03-24, 2026-01-12 | forecast |
| day-month-four-digit-year | `24-Mar-2026` | 2026-03-24 | forecast |
| space or slash separated, abbreviated month | `24 Mar 26`, `24/Mar/26` | 2026-03-24 | forecast |
| day, month spelled out, four-digit year | `14 August 2026`, `1 March 2026` | 2026-08-14, 2026-03-01 | forecast |
| month first, spelled out or abbreviated | `Mar 24, 2026`, `August 14 2026` | 2026-03-24, 2026-08-14 | forecast |
| the four-letter September abbreviation | `30-Sept-26` | 2026-09-30 | forecast |
| the actual marker on the spelled-out shape | `14 Aug 2026 A` | 2026-08-14 | **actual** |
| ISO, the one shape that already parsed | `2026-09-30` | 2026-09-30 | forecast |

Two-digit years expand on a **stated window**: 00-69 to the 2000s, 70-99 to the 1900s, so `24-Mar-99` is 1999 and not 2099. This is not inference. The document states a year, abbreviated by a convention the exporting tool applies to every row; the window is written in the parser and is never derived from any document.

### Refuses, with the reason

| Shape | Example | Refusal |
|---|---|---|
| day-month, no year | `29-May`, `02-Apr`, `17-Jul`, `16-Oct`, `06-Nov` | no year stated |
| month-day, no year | `May 29` | no year stated |
| all-numeric | `03/04/26`, `2026/03/04` | day and month order is a convention, not a fact |
| unrecognised trailing marker | `24-Mar-26 X` | the marker is not silently dropped |
| a date not on the calendar | `31-Feb-26` | no such calendar date |
| unrecognised month name | `24-Smarch-26` | unrecognised month name |
| a cell stating no date | `TBD`, `N/A`, `-` | the cell states no date |
| prose or a period | `next quarter`, `Q3 2026` | unrecognised date format |

An **empty** cell is neither: it returns `None`. A column the row did not fill in is not a value that failed to parse, and the two must not be reported as the same thing.

### The year cannot be resolved, and is not

`29-May` in a March 2026 status report can mean May 2025 (an activity that finished late in the previous year and is still listed) or May 2026 (the next forecast). **Nothing in the row distinguishes them.** The document's reporting period and data date are values under a different label, and taking a value of the right type sitting nearby is precisely the substitution defect the extraction prompt was already fixed for (`REPORT_2026-08-05_extraction-substitution.md` section 3).

So the year is refused, and the refusal is **structural, not a matter of care**: `parse_schedule_date` takes exactly one argument. There is no context parameter for a caller to pass a period or a data date into. A check asserts the signature, so a future session cannot add one without turning the suite red.

A row whose current finish refused is stored, with the reason, and marked `usable_for_trend = false`. It is a **missing row**, not a slip of zero.

### The actual-date marker is preserved, not stripped

The trailing `A` in `24-Mar-26 A` is standard scheduling-tool export notation: the date is an **actual**, the activity finished on it, and it will not move again. Every other date in the column is a forecast, which is the thing that can slip. Stripping the marker to normalise the date would turn a recorded fact into a prediction.

`ScheduleDate.kind` is `actual` or `forecast`; `schedule_activities.current_finish_kind` stores it, under a CHECK constraint; and it travels into what the analytical layer is served as `forecast_kind` beside each milestone. Three checks assert the two are distinguishable at each of those layers, and a fault that strips the marker turns the suite red.

---

## Does Milestone Trend Analysis now compute? Yes

**It computes at the second reporting period, for the first time on this platform.** Asserted end to end through `projectupload` / `projectcompute` / `projectresults` on a two-period project, with the figures asserted, not just the presence of the result: three activities matched, worst slip at plus 14 days, mean slip 7.0 days.

It abstains where it cannot compute, and the abstention is on **its own guard**:

- **One period is not a trend.** With fewer than two snapshots the `milestoneHistory` key is omitted from `signalInputs` entirely, so the module abstains on its own minimum-length check rather than on a series padded to reach a minimum. Asserted at period 1.
- **A milestone present in one period and absent from the next is not a slip.** Asserted twice. Through the real pipeline: one activity exists in period 1 and is gone in period 2, another arrives in period 2 only, and the result names three matches and mentions neither. And directly against the module, with a two-snapshot input where one milestone vanishes: one match, the vanished one is not the worst, and the mean is the survivor's own ten-day slip undiluted by a zero for the missing row. A fault that carries a missing milestone forward from the previous period turns this red.
- A period that read no schedule contributes **no snapshot** rather than an empty one. An empty snapshot would make every activity look absent, and absence read as movement is the exact error above.

### The shape the module reads is right, and nothing was reshaped to fit a key name

This was the stated stop condition, and it does not trigger. The module reads a list of snapshots, each carrying a timestamp and a list of milestones with a name and a forecast. That is what a per-period schedule store naturally produces: the name is the activity's own identifier, and the forecast is its current expected finish, which is exactly what the source table's current-finish column states. Nothing was bent.

The extra facts each row carries travel **beside** those keys, not instead of them: `forecast_kind`, `description`, `baseline_start`, `baseline_finish`, `percent_complete`, plus an `unusable` list naming the rows that refused. The module ignores every one of them; a reader does not. The module's own function is unchanged.

**One thing the module does not do, reported rather than built:** it compares the latest forecast against the *previous* forecast only. It never reads the baseline, although the baseline is now stored per activity. Baseline-versus-current is a different comparison from forecast-versus-forecast, and building it would be changing the module's arithmetic. See Part 4.

---

## What was built

**`server/app/schedule_dates.py`** (new). `parse_schedule_date(raw)` returning `ScheduleDate` (value, kind, raw), `DateRefusal` (raw, reason), or `None` for an empty cell. No context argument.

**`server/app/schedule_activities.py`** (new). The heading-to-field mapping, on **this** side of the model boundary. The extraction prompt correctly tells the model to use the table's own column headings as keys; mapping them is code that can be read and tested, not a model's judgement. The real table's headings map, and so do common alternatives, matched on a normalised form. An unrecognised heading contributes nothing rather than being guessed into the nearest field. A row with neither identifier nor description is dropped: it has no identity to match itself by next period, and positional matching would compare two different activities. `parse_percent_complete` returns `None`, never 0, for an unreadable or out-of-range cell, and keeps a stated 0 because a stated zero is data.

**Migration 0021, `schedule_activities`** (new table). One row per project, period, document and activity, unique on that tuple so re-deriving inserts nothing. Columns: `activity_key`, `description`, `baseline_start` and its kind, `baseline_finish` and its kind, `current_finish` and its kind, `percent_complete`, `unparsed` (JSON, one entry per refused cell with its reason), `usable_for_trend`, `as_of`, `source_doc_type`. Dates are ISO strings rather than DATE columns because a refused date is stored as NULL alongside its reason and a DATE column cannot hold "why not". No backfill: rows are derived from stored extractions and the site starts fresh.

**`server/app/research_models.py`** — the `ScheduleActivity` model.

**`server/app/documents.py`** — three new functions and two wiring points:

- `_persist_schedule_activities`, called at upload and at compute, exactly where `_persist_observations` is called and for the same reasons.
- `_schedule_snapshot(session, project, period)` — one period's schedule as one snapshot. Superseded documents are excluded as they are from computation; among the rest the document with the latest `as_of` wins, dated beats undated, ties fall back to the document id. That is the SNAPSHOT precedence `select_signal_inputs` already applies, restated because a schedule is a snapshot: two schedule updates in one period are two accounts of the same activities, not two populations to merge. Merging them would let one document's activity and another's describe a schedule that never existed.
- `_milestone_history(session, project, period)` — snapshots for periods at or below the period being computed, oldest first. The `_earlier_live_results` rule applied to the schedule store.
- `run_and_store` writes the milestone series only at two or more snapshots.

**`server/app/field_registry.py`** — `milestoneHistory` moves from `servable: False` to `{"shape": SERIES, "min_points": 2, "servable": True}`, with the reason it was unservable and the reason it no longer is recorded in place.

**`server/tools/test_schedule_milestones.py`** (new, 75 checks).

## The P1 invariant, proven rather than asserted

**Recomputing period 1 after period 2 exists is byte-identical to the original period-1 result.** Asserted directly, on a real two-period project driven through `projectupload` / `projectcompute` / `adminrecompute`.

What is compared: the stored row's `period`, `signal_inputs`, `module_results`, `category_statuses`, `project_status`, `portfolio_snapshot`, `simulation_version`, `seed`, `period_cutoff` and `source_documents`, serialised `json.dumps(sort_keys=True)` and compared as bytes. `result_id` and `computed_at` are excluded **by name and for a stated reason**: a recompute is a new append-only row and is required to have a new id, so including them would make the check unpassable for a reason unrelated to period alignment. This is the same comparison `REPORT_2026-08-05_period-series.md` describes, deliberately identical.

The design makes it reachable rather than lucky, and in two independent ways. A period's schedule rows are **written once, for that period**, and no later period's upload ever rewrites them; and the assembly reads only rows whose own period is at or below the period being computed. Two further checks pin it: the recomputed period 1 still has no milestone series and Milestone Trend Analysis still abstains there, which is what makes the byte comparison a real constraint rather than a coincidence between two rows that happen to be short.

## Verification, and proof each check can fail

Five faults. Each anchor asserted to match exactly once, each confirmed applied by SHA-256 comparison before the run, each reverted with a SHA-256 comparison against the original, baseline re-run green after every one.

| Fault | Result |
|---|---|
| a no-year date guesses the year instead of refusing | **65/75** |
| the actual marker is stripped, every date becomes a forecast | 69/75 |
| the milestone series is not bounded by the period being computed | **71/75**, and the byte-identical check is one of the four, first difference at byte 44 |
| one snapshot is served as a trend | 73/75 |
| a milestone missing from this period is carried forward from the last | 73/75 |

Baseline 75/75 before and after every fault. The third fault is the one that matters: it proves the P1 acceptance condition is a check that can fail, not an assertion.

## Real documents versus constructed examples, stated plainly

**No validation in this session was performed against a real document.** There are zero PDF, XLSX or DOCX files anywhere in this repository clone; the real document sets live on the owner's own machine and were not available. Only `server/dev_fixtures` and `tools/contract-fixtures` exist here. The owner was asked and chose to proceed on the named shapes.

What the fixture **is**: a reconstruction from findings that prior sessions recorded **against** real documents. `REPORT_2026-08-05_extraction-substitution.md` section 1.2 records the real design activity table's exact column headings and its nine rows; section 4 records the exact date strings `29-May`, `02-Apr`, `17-Jul`, `16-Oct`, `06-Nov`, `12-Jan-26`, `14 August 2026` and `24-Mar-26 A`. Those strings and those headings are in this suite verbatim. Everything else in the fixture, and every alternative heading and date shape beyond that list, is **constructed** from the named examples and from what the common scheduling tools export.

The limit that matters: the prior sessions' point stands, and stands against this work too. These gaps were found on real documents and missed by fixtures. A fixture built from a report about a real document is closer than one invented from nothing, but it is still not the document. **When the real sets are available, the first thing to run is the parser over every date cell in every schedule table in them, and the measure of success is the refusal list, not the parse count.** A refusal that names a shape nobody anticipated is the parser working; a silently wrong date is not something this suite can catch on shapes it has never seen.

Two further limits worth naming. `milestones_json` is requested by both the schedule-update and monthly-report document types; only a schedule update has ever been observed returning one. And the model's behaviour on a table with merged cells, sub-headings, or a total row was not observed at all; those rows will either be dropped for having no identity or will contribute a refusal, which is the safe direction, but which of the two is unknown.

---

## Part 4 — what the platform can now say, and is not yet saying

Reported as possibility, not built. The owner decides what the platform says about any of it.

**Available today, from the stored data alone.**

- **Which milestones are slipping, and by how much.** Every activity's forecast finish is stored per period with its own identity, so the slip of any one activity between any two periods is a subtraction over stored rows. Milestone Trend Analysis today reports the mean and the single worst; the per-activity list is in the store and is not surfaced anywhere.
- **Baseline versus current.** `baseline_start` and `baseline_finish` are stored per activity and nothing reads them. Variance against the *original plan* is a different and often larger number than variance against last month's forecast, and the platform now holds both and reports only the second.
- **Which activities are finished and which are still predictions.** `current_finish_kind` distinguishes an actual from a forecast. A schedule where the remaining forecasts have all slipped while the completed actuals sit on baseline is a different situation from one where the early work already ran late, and nothing currently draws that line.
- **How much of the schedule is unreadable, and why.** `unparsed` and `usable_for_trend` mean the platform can say "nine activities read, six comparable, three unusable because the source states no year" instead of quietly comparing six. That is evidence quality about the schedule, which is the Data and Evidence Health group's subject, and no computation there reads this store.

**Available once three or more periods are stored.**

- **Whether a slip is accelerating.** Four periods give four forecasts for the same activity, so the *second difference* is computable: an activity that slipped 5 days, then 10, then 20 is a different fact from one that slipped 12 days once and has held since. Milestone Trend Analysis compares only the last two snapshots and cannot see this.
- **Whether the slip is broad or concentrated.** The count of activities moving in one period, against the size of the movement, separates a general schedule deterioration from a single late activity.

**Not available, and not claimed.**

- **Whether the critical path has moved.** The stored table carries no logic links, no predecessors, no successors, and no float per activity, so which activities are critical is not derivable from it. Total float and consumed float exist as project-level scalars in the extraction vocabulary, which is a different question from which chain of activities drives the finish date. To say the critical path moved, the platform would need the schedule's logic, and it does not read the logic. Stated here because the task named it, and the honest answer is no.

**One decision left open, deliberately.** An activity whose finish date is **actual** cannot slip, by definition, and today it enters the mean as a zero. Three complete activities and one slipping one average to a small number that reads as a healthy schedule. Whether completed activities should be excluded from the mean is a change to what Milestone Trend Analysis computes, which is the module's arithmetic and out of scope. Flagged, not touched.

## Staleness noted and deliberately not edited

`server/app/simulation/VALIDATION.md` still records that the milestone series is unsupplied and the module still abstains. That is now wrong. It was not edited, because editing it means opening `server/app/simulation/` for a documentation change, and that directory is off limits except to let the module accept its input, which it did not need. The same choice `REPORT_2026-08-05_period-series.md` made about the same file, for the same reason.

## Repository state

`origin/main` was at `b64135f` when this began and had not moved at merge time. Branch `claude/schedule-milestones-s5s90m`, merged to `main` as `bb382fc` via PR #222. Files changed: `server/app/schedule_dates.py` (new), `server/app/schedule_activities.py` (new), `server/alembic/versions/0021_schedule_activities.py` (new), `server/app/research_models.py`, `server/app/documents.py`, `server/app/field_registry.py`, `server/tools/test_schedule_milestones.py` (new), `T6_HANDOFF.md`. No front-end file was modified. Nothing under `server/app/simulation/` was modified. The working tree held only this task's files at every commit.
