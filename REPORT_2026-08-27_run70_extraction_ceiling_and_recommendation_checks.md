# Run 70: extraction to its ceiling, and the recommendation must cite what it reasons from

Repository: the Linux clone at `/home/user/LinPRojectRadar`. Base `3dd890b`.

## 1. The numbers

|                                 | before | after |
| ------------------------------- | ------ | ----- |
| Modules holding a current result (fixture) | 21 | 22 |
| Modules holding a current result (browser) | 21 | 22 |
| Categories carrying a status (fixture)     | 3  | 3  |
| Categories carrying a status (browser)     | 3  | 3  |

Measured, not inherited. The order's section 1 carried a baseline of "30 of 63 modules and
6 of 11 categories"; the run's own measurement on its own fixture is 21 and 3, which is what
Run 69's report also states.

Categories did not move and could not: the one module Part A lit, A1.5, is
`calibration_pending` with `band_asserted: False`, and a category takes its status from a
banded module. A1, A4 and B1 are the only categories holding a banded module at all.

## 2. A5.4, and the identifier

Live `A5.4` is **Scenario Modeling**, not Rework Feedback Loop. **Rework Feedback Loop is
`A5.5`.** Mapped by module name per section 11 and verified against `registry_index()`.

`A5.5` stays dark. Its own refusal, off the live run:

> Awaiting a system dynamics rework model: the stock of work in the backlog, the work
> arriving and completed each step, and the share of completed work that returns as rework.

The NCR register was opened. `extraction_fields.py` line 287 is the whole of it:

    "ncr_log": ["ncr_issued", "ncr_closed", "ncr_open", "ncr_overdue", "report_period"],

Occurrences and a backlog of REPORTS. No arriving or completed WORK, and no share of
completed work returning as rework. The register records occurrences, so `A5.5` stays dark.

## 3. Newly computing: A1.5 ARIMA CPI Forecast

No extraction field was added. A1.5 was the only dark module in service whose refusal named
no missing document: *"The cost performance history is too short for a time series model to
be identified from it."* `canonical_v3.identify_arima` takes `min_history: int = 8`;
`documents._period_history` builds `cpiHistory` from the project's own earlier live results.
The fixture now states eight periods of the same pay application and time-phased schedule.

Hand-check. cpiHistory = 0.952381, 0.952381, 0.934783, 0.916031, 0.906040, 0.893939,
0.882353, 0.868421. The module identifies (0,1,0) with drift; the drift it fits is the mean
of the six differences it retains, -0.013993; forecast = 0.868421 - 0.013993 = **0.854428**.
The module reports **0.854**, interval 0.847 to 0.861. Independently recomputed: identical.

## 4. The ceiling

**28 of 63.** 22 compute now; 6 more are reachable by adding fields to a document type the
platform already supports (A3.7, A3.9, A4.5, A4.6, A4.8, A4.9). **35 are not reachable from
the current document set.** Each is listed in the chat report with its own refusal verbatim.

`A4.1 Document Risk Score` is a separate case: in service but not in `VALIDATED`, and
`available_modules()` returns `sorted(set(VALIDATED) & set(service_index()))`, so it never
runs and never abstains. No document can reach it.

## 5. Part B

Three checks in `briefBodyHtml`'s ready branch — the single point at which any brief text,
from the chat endpoint or from the scripted fallback, becomes HTML. A recommendation failing
any of the three is rejected, the failure recorded, and the reasoning's structured fields
rendered in its place. Proved by three injections, each pinned to its exact site by deletion.

The completeness sentence is REMOVED. See the chat report for why.
