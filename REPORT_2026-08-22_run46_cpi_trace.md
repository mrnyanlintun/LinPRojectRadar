# Run 46 — Trace the CPI defect from code

**Date:** 2026-08-22
**Repository used:** the Linux clone at `/home/user/LinPRojectRadar`. There is no `.venv` on this
clone; the documented fallback interpreter was used, **CPython 3.11.15** (`python3 --version`).
**Branch:** `run46-cpi-trace`, rooted at `f461671` (`HEAD == main == origin/main`, tree clean at
start). Stamp `sim-2026.08-v30` at `server/app/simulation/models.py:563`.
**What this is:** a trace, executed. **No fix is written. No behaviour is changed.** The only files
this run creates are this report, one read-only artifact `code_audit/run46_cpi_trace.csv`
(396 rows), and a `T6_HANDOFF.md` entry.
**Production Postgres was never configured or contacted.** No PRJ-001 document was read or
modified. No browser session was opened, so no browser cwd is reported. `DEng\Demo` was ignored.

**Method.** Every fixture below was built through the **real routes** — `/exec` `researchlogin`,
`adminparticipantcreate`, `adminmemberadd`, `projectupload`, `projectcomputeall`,
`projectresults` — against a **throwaway migrated SQLite database** in the session scratchpad,
with the extraction model stubbed by `app.documents.set_extractor_override` +
`app.extraction_client.StubExtractor`, which is the route every suite in this repository uses and
the only one available. **Everything downstream of extraction is the production path, untouched.**
The driver follows the shape of `server/tools/build_run45_census.py`; it lives in the scratchpad,
not in the repository, and it reimplements no retrieval logic — it drives the server and records
what the server said. The databases were torn down after use.

---

## 1. Does the defect still reproduce on current code? — stated first

**Split verdict, and the split is the finding.**

| render symptom | reproduces on current code? |
|---|---|
| **CPI 1.22** | **YES, exactly.** `cpi = 1.22` at every period of the base fixture, from `ev = 1,046,735` over `ac = 857,930` |
| **`pv = 824,370`** | **NO.** The base fixture stores `pv = 1,085,600` at period 4, sourced `time_phased_schedule asOf=2026-06-30` |
| **SPI 1.27** | **NO.** The base fixture computes `spi = 0.964`, exactly as Run 43J found |

**Run 45 did change what this fixture stores, and it changed exactly one field: `bac`.** In Run
43J's trace `bac` came from the **pay application** at periods 2, 3 and 4, because the contract was
uploaded at period 1 and `_period_documents` could not see it. On the current code, with the pay
application deliberately stating a *different* contract sum (4,463,290) so the change would be
visible, `bac` is **5,874,620 sourced `contract_value asOf=2026-03-01` at all four periods**. The
identity carry-forward holds and declared precedence holds across it. **That is the whole of Run
45's effect on this shape.**

**And it does not touch `pv`, `ev`, `ac`, `cpi` or `spi` at all.** `pv` is classified **PERIOD**,
not identity (`server/app/field_registry.py:251-267` — `IDENTITY_FIELDS` is thirteen names and
`pv` is not among them; `retrieval_kind("pv")` executed against the bytes on disk returns
`PERIOD`). So the headline is:

> **The CPI figure still reproduces exactly and is untouched by Run 45. The `pv` shortfall still
> does not reproduce from a period-consistent document set, and Run 45 neither introduced nor
> removed it. What Run 45 fixed was `bac`, and `bac` enters neither index.**

CPI is `ev / ac` and reads neither `pv` nor `bac` (`server/app/extraction_merge.py:994`). No
retrieval change of any kind can move it.

---

## 2. The four-period fixture (§5.1)

**Corpus `BASE`, project `PRJ-R46-BASE`.** Per period: a Monthly Progress Report, a Pay
Application (G702) and a Time-phased Schedule / Baseline. One Contract Value / Original Agreement,
uploaded at period 1 only, `document_date` 2026-03-01. Figures scaled so period 4 lands on the
render's own EV, AC, actual % and planned %, with `BAC = 5,874,620`. The pay application states
`original_contract_sum = 4,463,290` — deliberately different from the contract, so that any
fall-through to it would be visible in the stored figure.

Every cell below is read back from `computed_results.signal_inputs` through `projectresults`;
the document column is read from `signal_inputs.sources[field].docType` and `.asOf`.

| period | field | stored value | document it came from | as-of |
|---|---|---|---|---|
| 1 | `bac` | 5,874,620 | `contract_value` | 2026-03-01 |
| 1 | `ev` | 261,684 | `pay_application` | 2026-03-31 |
| 1 | `ac` | 214,483 | `pay_application` | 2026-03-31 |
| 1 | `pv` | 271,400 | `time_phased_schedule` | 2026-03-31 |
| 1 | actual % complete | 4.54 | `pay_application` | 2026-03-31 |
| 1 | planned % complete | 4.62 | `time_phased_schedule` | 2026-03-31 |
| 1 | **CPI** | **1.22** | derived, `extraction_merge.py:994` | — |
| 1 | **SPI** | **0.964** | derived, `extraction_merge.py:996` | — |
| 2 | `bac` | 5,874,620 | `contract_value` | 2026-03-01 |
| 2 | `ev` | 523,368 | `pay_application` | 2026-04-30 |
| 2 | `ac` | 428,965 | `pay_application` | 2026-04-30 |
| 2 | `pv` | 542,800 | `time_phased_schedule` | 2026-04-30 |
| 2 | actual % complete | 9.08 | `pay_application` | 2026-04-30 |
| 2 | planned % complete | 9.24 | `time_phased_schedule` | 2026-04-30 |
| 2 | **CPI** | **1.22** | derived | — |
| 2 | **SPI** | **0.964** | derived | — |
| 3 | `bac` | 5,874,620 | `contract_value` | 2026-03-01 |
| 3 | `ev` | 785,051 | `pay_application` | 2026-05-31 |
| 3 | `ac` | 643,448 | `pay_application` | 2026-05-31 |
| 3 | `pv` | 814,200 | `time_phased_schedule` | 2026-05-31 |
| 3 | actual % complete | 13.62 | `pay_application` | 2026-05-31 |
| 3 | planned % complete | 13.86 | `time_phased_schedule` | 2026-05-31 |
| 3 | **CPI** | **1.22** | derived | — |
| 3 | **SPI** | **0.964** | derived | — |
| 4 | `bac` | 5,874,620 | `contract_value` | 2026-03-01 |
| 4 | `ev` | 1,046,735 | `pay_application` | 2026-06-30 |
| 4 | `ac` | 857,930 | `pay_application` | 2026-06-30 |
| 4 | `pv` | 1,085,600 | `time_phased_schedule` | 2026-06-30 |
| 4 | actual % complete | 18.16 | `pay_application` | 2026-06-30 |
| 4 | planned % complete | 18.47 | `time_phased_schedule` | 2026-06-30 |
| 4 | **CPI** | **1.22** | derived | — |
| 4 | **SPI** | **0.964** | derived | — |

**Plainly: the current code reproduces CPI 1.22. It does not reproduce `pv = 824,370`, and it does
not reproduce SPI 1.27, from a document set whose figures are period-consistent.**

### 2.1 The arithmetic the order hands over, verified

Executed, not assumed:

```
824,370 / 5,874,620            = 14.032737 %      (order: 14.03 %)          VERIFIED
5,874,620 x 18.47 %            = 1,085,042.314    (order: 1,085,042)        VERIFIED
1,085,042.314 - 824,370        =   260,672.314    (order: 260,672)          VERIFIED
260,672.314 / 1,085,042.314    = 24.024161 %      (order: 24.0 %)           VERIFIED
1,046,735 / 857,930            = 1.2200704  -> CPI 1.220                    VERIFIED
1,046,735 / 824,370            = 1.2697393  -> SPI 1.270                    VERIFIED
```

Two further figures from the same six numbers, needed below:

```
1,046,735 / 5,874,620 = 17.8179 %   against a stated actual %  of 18.16
  857,930 / 5,874,620 = 14.6040 %
  824,370 / 5,874,620 = 14.0327 %   against a stated planned % of 18.47
       18.16 / 18.47  = 0.983216    the SPI the two stated percentages imply
```

**EV and BAC are very nearly consistent with the stated actual % (1.9 % apart). `pv` and BAC are
31.6 % apart on the stated planned %.** Whatever is wrong with `pv` is not wrong with `ev` in the
same proportion, and that is a fact about the six rendered numbers alone, independent of any code.

---

## 3. Every path that can write `pv`, with reachability established by execution (§5.2)

### 3.1 The declared writers

`pv` is written by exactly **three** document types, and by nothing else. Two tables decide it and
both were read:

* the emission tables — `server/app/extraction_merge.py:567` (`time_phased_schedule`:
  `planned_value_to_date -> pv`), `:571` (`monthly_report`: `planned_value -> pv`), `:653`
  (`schedule_update`: `planned_value_to_date -> pv`). `_EXTRA_NUMERIC_KEYS`
  (`extraction_merge.py:327-337`) adds **no** further `pv` writer for any type;
* the precedence table — `server/app/field_registry.py:191`:
  `"pv": {"schedule_update": 0, "time_phased_schedule": 1, "monthly_report": 2}`. Lower tier wins
  outright; within a tier, latest `as_of`.

For comparison, the five that can supply a contract sum for `bac` are
`server/app/field_registry.py:183-184`: `change_order 0, contract_value 1, schedule_of_values 2,
pay_application 3, monthly_report 4`. **`pv` has three writers, not five, and none of them is a
contract or an invoice.**

### 3.2 Each path, executed

Every row was executed on the current code through the real routes.
`code_audit/run46_cpi_trace.csv` holds all 396 rows.

| # | path | corpus that executed it | reachable? | `pv` it produced | can it be 824,370? |
|---|---|---|---|---|---|
| 1 | `time_phased_schedule.planned_value_to_date` (tier 1) | `BASE` | **YES** | 1,085,600 at p4 | **YES** — `P1ONLY` p1 stored `pv = 824,370` from this writer directly |
| 2 | `schedule_update.planned_value_to_date` (tier 0) beating a tier-1 baseline **and** a tier-2 monthly report in the same period | `SU` p4 (all three present, all three stating a value) | **YES** | **824,370**, sourced `schedule_update asOf=2026-06-30` | **YES, and it reproduces the render exactly: `cpi 1.22`, `spi 1.27`, planned % 18.47** |
| 3 | `monthly_report.planned_value` (tier 2) as the only writer in the period | `MRONLY` p4 | **YES** | **824,370**, sourced `monthly_report` | **YES, and it too reproduces `cpi 1.22`, `spi 1.27`** |
| 4 | tier 1 beating tier 2 when the two state **different** figures in one period | `TIER12` p4 (`monthly_report` says 824,370, `time_phased_schedule` says 1,085,600) | **YES** | **1,085,600** — the baseline wins, the monthly report's 824,370 is refused | the monthly report cannot win here |
| 5 | **no writer in the period at all** | `NOPV` (contract + pay applications only) | **YES** | **`null`** — present-and-null, not absent, and `spi` is `null` too | **NO** — absence produces null, never a number |
| 6 | **carry-forward of an earlier period's `pv`** | `P1ONLY` (a single baseline at period 1 stating 824,370 / 18.47, pay applications at 1-4) | **NO — BLOCKED** | `pv = 824,370` at period 1; **`null` at periods 2, 3 and 4** | **NO on the current code.** See §5 |
| 7 | the SPI **percentage substitution** — `pv` absent, both percentages present | `PCTFB` p4 | **YES** | `pv` stays `null`; `spi` is computed as `18.16 / 18.47 = 0.983` (`extraction_merge.py:998-1003`) | this path never writes `pv`; it produced **0.983**, not 1.27 |

**Substitutions, defaults and fallbacks on the way, enumerated.** There are four and only four,
and all four were executed above:

1. **tier fall-through** (paths 2, 3, 4) — a lower-numbered tier wins outright; when it is absent
   the next tier wins. This is the substitution that produced `bac`'s pre-Run-45 defect. On `pv` it
   is reachable in both directions and demonstrably ordered `schedule_update < time_phased_schedule
   < monthly_report`;
2. **absence -> present-and-null** (path 5) — `select_signal_inputs` initialises every key to
   `None` (`extraction_merge.py:936`), so a missing `pv` is stored as null, never as 0 and never as
   a borrowed number;
3. **the SPI percentage substitution** (path 7) — a *derived-index* fallback, not a `pv` write;
4. **no clamp and no default exists for `pv`.** `BOUNDED_MAX_SI_FIELDS`
   (`field_registry.py:162-168`) does not name it, so no ceiling is applied; a negative value is
   **refused outright** with `NumericRangeError` (`extraction_merge.py:355-361`), never clamped.

**Nothing else writes `pv` on the production path.** `server/app/training_engine.py:555, 820, 1281`
writes a `pv` into a *training* simulation state; that is the training mode, a different route, and
it never reaches `computed_results` for a real project.

---

## 4. The fee-basis test, by construction (§5.3)

### 4.1 Every ratio between the four stored figures

| pair | ratio | inverse |
|---|---|---|
| BAC / EV | 5.612328 | 0.178179 |
| BAC / AC | 6.847435 | 0.146040 |
| BAC / PV | 7.126193 | 0.140327 |
| EV / AC | 1.220070 | 0.819625 |
| EV / PV | 1.269739 | 0.787563 |
| AC / PV | 1.040710 | 0.960883 |

**Is any of these consistent with two figures on different bases?** A basis mismatch would show as
a ratio that is stable and meaningful against a *third* figure the two share. The only such anchor
here is the pair of stated percentages, and against them:

* `EV / BAC = 17.818 %` against a stated actual % of **18.16** — a discrepancy of **1.88 %**;
* `PV / BAC = 14.033 %` against a stated planned % of **18.47** — a discrepancy of **24.02 %**.

**EV and BAC are on the same basis to within 1.9 %; `pv` and BAC are not on the same basis, or one
of the two figures is wrong.** `824,370 / 0.1847 = 4,463,291.8`: the stored `pv` and the stored
planned % are internally consistent with each other on an implied total of **4,463,290**, not on
BAC. That is an arithmetic restatement of the 24 % shortfall and nothing more — it does not by
itself identify 4,463,290 as any real document's figure. **The 4,463,290 that appears in Run 44's
and Run 45's fixtures is not independent corroboration: it entered the record as Run 43J's own
`824,370 / 0.1847` derivation (`REPORT_2026-08-22_run43J_render_defect_diagnosis.md:201`) and was
adopted as a fixture constant thereafter.** It is not a measurement of PRJ-001.

### 4.2 Solved algebraically

Write `r` for one fee-to-cost ratio applied to exactly one of the three EVM figures, and let the
"otherwise-correct" cost-basis figures be internally consistent — `EV_c = actual% x BAC`,
`PV_c = planned% x BAC`, so `SPI_c = 18.16 / 18.47 = 0.983216`.

`CPI = EV/AC` and `SPI = EV/PV`, so a single `r` on one figure moves each index by `r`, `1/r` or
`1`:

```
SPI_obs / SPI_c = 1.2697393 / 0.983216 = 1.2914144  =>  r = 1.2914144  (or 1/1.2914144 = 0.774343)
CPI_obs / CPI_c = 1.2200704 / CPI_c
```

Setting the two equal gives `CPI_c = 1.2200704 / 1.2914144 = 0.9447552`, which **is** inside the
corpus's authored 0.94-1.01 band. **So a single ratio does exist that makes the two INDICES come
out at 1.22 and 1.27 together: `r = 1.29141`, on `ev`, with a true CPI of 0.94476.**

But that same `r` fixes the stored figures too, and there it fails:

```
EV_c = 18.16 % x 5,874,620 = 1,066,830.99   EV_obs / EV_c = 0.981163
PV_c = 18.47 % x 5,874,620 = 1,085,042.31   PV_obs / PV_c = 0.759758
AC_c (at CPI_c = 1.00)     = 1,066,830.99   AC_obs / AC_c = 0.804185
```

**Three different ratios, not one.** No single scalar carries all three observed figures onto a
consistent cost basis.

### 4.3 Confirmed by construction — two fixtures, both built through the real routes

**`FEEBOTH`** — `ev` on a fee basis at `r = 1.2914144`, `ac` cost-basis stating the true CPI
0.9447552, `pv` and `bac` cost-basis and correct. Period 4, read back from storage:

| field | stored | render |
|---|---|---|
| `bac` | 5,874,620 | 5,874,620 |
| `ev` | **1,377,720.89** | 1,046,735 |
| `ac` | **1,129,214.25** | 857,930 |
| `pv` | **1,085,042.31** | **824,370** |
| actual % | 18.16 | 18.16 |
| planned % | 18.47 | 18.47 |
| **CPI** | **1.22** | **1.22** |
| **SPI** | **1.27** | **1.27** |

**`PVFEE`** — `pv` on a fee basis at `r = 0.759758`, everything else cost-basis and correct.
Period 4:

| field | stored | render |
|---|---|---|
| `ev` | 1,066,830.99 | 1,046,735 |
| `ac` | 1,066,830.99 | 857,930 |
| `pv` | **824,370.00** | **824,370** |
| **CPI** | **1.00** | 1.22 |
| **SPI** | **1.294** | 1.27 |

(Two calibration fixtures were also built and are in the CSV: `FEE129` — `r = 1.29135` on `ev`
with a true CPI of 1.00 — gives `cpi 1.291`, `spi 1.269`; `FEE076` — `r = 0.75976` on `ev` — gives
`cpi 0.76`, `spi 0.747`. Neither is the render.)

### 4.4 The verdict, stated plainly

**A fee-to-cost ratio that produces CPI 1.22 and SPI 1.27 simultaneously EXISTS: `r = 1.29141`
applied to `ev`, against a true CPI of 0.94476. It is `FEEBOTH`, and it was built and executed.**

**It is nevertheless not what the render shows, and the hypothesis therefore fails on the numbers
as an account of the render.** `FEEBOTH` reproduces both indices while storing `pv = 1,085,042`,
`ev = 1,377,721` and `ac = 1,129,214` — **not one of the render's four stored figures.** And
`PVFEE`, the only single-ratio arrangement that reproduces the render's `pv = 824,370` exactly,
gives CPI 1.00 and SPI 1.294 — **neither of the render's two indices.**

> **No single fee-to-cost ratio reproduces the render's four stored figures. A single basis
> mismatch explains the two indices only by contradicting every stored figure, and explains the
> stored `pv` only by contradicting both indices. It does not explain both at once.**

What that leaves standing is narrower than "fee basis" and is worth stating exactly: the render's
`ev` is 1.9 % away from its own stated actual %, while its `pv` is 24.0 % away from its own stated
planned %. **Those are not one distortion of one magnitude. Whatever produced them acted on `pv`
and on `ev`/`ac` differently, or acted on only one of them.** Which of those it was is **G — not
determinable** here; see section 6.

---

## 5. The wrong-document test, and whether Run 45's carry-forward can pin `pv` (§5.4)

### 5.1 Does any document in the fixture state a figure equal or close to 824,370?

**In the base fixture, no.** Its stated planned values are 271,400 / 542,800 / 814,200 / 1,085,600.
The nearest is period 3's **814,200**, which is **10,170 short of 824,370 — 1.23 % away, not
equal.** On the 18.47 %-of-BAC scale the same period is 814,222.33, 1.25 % away. **824,370 is not
any period's planned value on this fixture's baseline.** In `P1ONLY`, `SU`, `MRONLY` and `TIER12`
it appears only because this run planted it there deliberately, in order to execute the write paths
of section 3. **What PRJ-001's own documents state is not determinable here** — see section 6.

### 5.2 Is 824,370 an earlier period's planned value rather than the computed one?

**Not on this fixture: no earlier period's planned value equals it (§5.1).** And the question is
moot on the current code, because §5.3 shows the retrieval cannot deliver an earlier period's `pv`
at all.

### 5.3 Can a time-phased baseline from period 2 or 3, retrieved at period 4, produce it? **NO — and this was executed, not read.**

**`pv` is a PERIOD field, and I established it two ways rather than assuming it.**

1. **By reading the classification.** `IDENTITY_FIELDS` (`server/app/field_registry.py:251-267`) is
   thirteen names: `bac`, `baselineContractSum`, `baselineEnd`, `baselineStart`,
   `revisedContractSum`, `originalContingency`, `analogousBac`, `analogousFinalCost`,
   `analogousOverrunPct`, `overallRating`, `scheduleRating`, `costRating`, `qualityRating`.
   `pv` is not among them, and `PERIOD_FIELDS` is derived by subtraction
   (`field_registry.py:286-287`), so `pv` is PERIOD by construction. `retrieval_kind("pv")`
   executed against the bytes on disk returns **`PERIOD`**.
2. **By execution.** Corpus `P1ONLY`: **one** Time-phased Schedule / Baseline, uploaded at
   **period 1 only**, stating `planned_value_to_date = 824,370` and
   `planned_percent_complete = 18.47`; pay applications at periods 1-4. Read back:

| period | `pv` | planned % | SPI |
|---|---|---|---|
| 1 | 824,370 (`time_phased_schedule`, asOf 2026-03-31) | 18.47 | 0.317 |
| 2 | **null** | **null** | **null** |
| 3 | **null** | **null** | **null** |
| 4 | **null** | **null** | **null** |

**The baseline does not carry forward. It goes absent, and absence is stored as null.** The filter
that stops it is `extraction_merge.py:927-931` — `carried` observations are admitted only if
`str(o.get("field")) in IDENTITY_FIELDS` — and it is applied a second time in
`documents.py:395` (`_identity_observations_before`), which is why a single-site defeat proves
nothing (Run 45 section 9 item 2).

**Proof that this probe can fail.** Protocol: inject -> re-read the bytes from disk -> observe the
opposite result -> restore -> confirm the original.

* **Injection I-PV.** `"pv",  # RUN46 INJECTION I-PV` added to `IDENTITY_FIELDS` at
  `server/app/field_registry.py:253`.
* **Bytes re-read from disk:** `retrieval_kind('pv')` -> **`IDENTITY`**, `len(IDENTITY_FIELDS)` ->
  **14**.
* **Observed, on a fresh migrated database, through the same real routes:**

  | period | `pv` | asOf | SPI |
  |---|---|---|---|
  | 1 | 824,370 | 2026-03-31 | 0.317 |
  | 2 | **824,370** | **2026-03-31** | 0.635 |
  | 3 | **824,370** | **2026-03-31** | 0.952 |
  | 4 | **824,370** | **2026-03-31** | **1.27** |

  The period-1 baseline was carried to period 4 and **period 4 then reads `pv = 824,370` and
  `spi = 1.27` — the render, exactly.** So the probe is capable of showing precisely the thing it
  reports as absent, for the intended reason, and the negative result is meaningful.
* **Restored** by `git checkout -- server/app/field_registry.py`; `git status --short` empty;
  `retrieval_kind('pv')` -> `PERIOD`, `len(IDENTITY_FIELDS)` -> 13; the probe re-run on a fresh
  database reproduces `null` at periods 2-4.

> **Run 45's carry-forward CANNOT pin `pv` to an early period's figure. It is not a defect
> introduced or exposed by Run 45.** Had `pv` been classified identity instead, it would have been
> — the injection shows exactly that outcome — which is the measure of how much the PERIOD
> classification is doing here.

Note also the coupling: `plannedPctComplete` is a PERIOD field too, and it went null alongside
`pv`. A carried `pv` with an absent planned % would have been a worse state than either.

---

## 6. What remains unanswerable, and the exact table and column that would answer it (§5.5)

Everything here needs PRJ-001's stored rows, which live in production Postgres. **Stop condition
8.1 forbids touching it, it was not touched, and this run had no production access.** Each item
names the table and column, not "the database".

| # | question left open | table and column that would answer it |
|---|---|---|
| 1 | **Which document type actually supplied `pv = 824,370`** — a `schedule_update` (tier 0), a `time_phased_schedule` (tier 1) or a `monthly_report` (tier 2)? Section 3 shows all three reach that value. | `observations.source_doc_type`, with `observations.value`, `observations.as_of` and `observations.document_id`, filtered `observations.project_id = <PRJ-001>` **and** `observations.field = 'pv'` **and** `observations.period = <displayed period>`. Cross-check: `computed_results.signal_inputs -> 'sources' -> 'pv' -> 'docType'` on the displayed row |
| 2 | **What that document itself stated** — whether 824,370 was extracted faithfully or mis-extracted from a different cell. | `documents.extraction`, JSON key `planned_value_to_date` (or `planned_value` for a monthly report), joined via `observations.document_id = documents.document_id`; and `documents.doc_type` for the type the classifier assigned. `documents.content` holds the bytes themselves |
| 3 | **Whether the document that supplied `pv` also supplied `plannedPctComplete = 18.47`**, or whether the two came from different documents. | `observations.source_doc_type` and `observations.document_id` for `observations.field IN ('pv','plannedPctComplete')` at the same `project_id`/`period` |
| 4 | **Whether the pay application that supplied `ev` supplied `ac`**, or whether `ac` fell through to the monthly report — Run 43J's surviving account of CPI 1.22. | `observations.source_doc_type` for `observations.field IN ('ev','ac')` at the same `project_id`/`period`; and `documents.extraction` keys `completed_to_date` / `amount_paid_to_date` on the pay application's row |
| 5 | **Whether any PRJ-001 document states 4,463,290** — the total the stored `pv` and planned % imply — or whether that figure exists only as Run 43J's division. | `documents.extraction`, key `original_contract_sum` (and `revised_contract_sum`, `scheduled_value_total`, `budget_at_completion`), across the project's rows; and `observations.value` for `observations.field = 'bac'` |
| 6 | **What the corpus authored as the true EV/AC pair**, against which 1.22 is the anomaly. | Not a database question — the PRJ-001 document set itself, which stop condition 8.2 forbids modifying and which this run did not read |
| 7 | **Which document versions produced the displayed row.** | `computed_results.source_documents` (list of `{document_id, sha256, doc_type, filename}`) on the `computed_results` row for that `project_id`/`period` |

**One structural limitation found while answering these, and it bears on item 1.** The stored
per-field source record names the **document type and the document, but not the extraction key**:
`_source_entry` (`extraction_merge.py:882-895`) writes `docType`, `value`, `documentId`,
`documentVersion`, `asOf` and `revisionOf` — and no field name. So even with the stored row in
hand, `signal_inputs.sources` alone cannot say **which cell of the document** a figure came from;
answering item 2 requires going back to `documents.extraction`. That is a code fact, recorded, not
acted on.

---

## 7. Incidental findings, unacted

1. **`BRIEF_CAT_LABEL` is still present and still carries the retired "Cat N" scheme.**
   `assets/js/detail.js:1689-1697`, ten entries, every one of the form `"Cat 1": "Cost Performance
   (Cat 1)"` ... `"Cat 10": "Decision Optimization (Cat 10)"`, against `NAMING_AUTHORITY.md:96`
   (*"Never use a module id or number in user-facing text. No 'Cat 4' ... Groups and purposes only.
   The old 'Cat N' scheme is retired along with the names."*). Found by Run 44, carried unacted by
   Run 45, **still unacted**. This run did not act on it either.
2. **`signal_inputs.sources` records no source FIELD name**, only the document type and identity —
   `extraction_merge.py:882-895`. See the note closing section 6.
3. **`pv` has no upper bound and no default.** It is absent from `BOUNDED_MAX_SI_FIELDS`
   (`field_registry.py:162-168`), so an implausible planned value is stored as given; a negative
   one is refused outright rather than clamped (`extraction_merge.py:355-361`). Correct by the
   file's own stated reasoning (*"an implausible figure is not an impossible one"*), recorded here
   because it means nothing downstream would flag a `pv` that is 24 % low.
4. **A scratchpad shadowing trap, recorded so a later session does not lose time to it.** The
   session scratchpad holds files named `queue.py`, `parameters.py`, `harness.py` and others left
   by earlier runs. A driver script placed directly in that directory puts it on `sys.path[0]`,
   `queue.py` shadows the standard library's `queue`, and `anyio` then fails with
   *"Backend 'asyncio' is not available"* — surfacing as an opaque HTTP 500 from the first
   `TestClient` request, not as an import error. The fix is to run the driver from a clean
   subdirectory. Nothing in the repository is at fault.
5. **The four unconsumed items Run 45 recorded** (its section 9) are unchanged: the double-enforced
   identity filter, the O(N) earlier-period reads in `_identity_observations_before`, and the ten
   unconsumed extraction fields from Run 43J section 15.

---

## 8. What the next session needs, stated as a decision for the owner

1. **The `pv` question is now a two-way fork, and only stored rows can choose.** `pv = 824,370` is
   reachable from **three** different document types (section 3), and each of the two that can be
   the sole writer in a period reproduces the render's `cpi 1.22` **and** `spi 1.27` exactly. **The
   code cannot narrow it further.** *Decision: authorise a read-only query of
   `observations.source_doc_type` / `observations.value` / `observations.document_id` for
   `field = 'pv'` on PRJ-001's displayed period, or accept that the `pv` cause stays G.* Nothing
   else will settle it.
2. **The fee-basis hypothesis is decided and should be closed as an explanation of the render.** It
   produces both indices only by contradicting all four stored figures, and the stored `pv` only by
   contradicting both indices (section 4). *Decision: close it, or state a different definition of
   "otherwise correct" under which it should be re-tested.* If it is closed, the surviving account
   of CPI 1.22 is Run 43J's — that `ev` and `ac` came from different documents — and that too needs
   item 1's access.
3. **`pv`'s PERIOD classification is now load-bearing in a way the classification record does not
   say.** The injection in §5.3 shows that classifying `pv` identity would make the render's exact
   figures appear from a single stale baseline. `FIELD_CLASSIFICATION_DECISIONS.md` records why the
   thirteen identity fields are identity; it does not record why `pv` in particular must not be.
   *Decision: record `pv`'s PERIOD classification as a deliberate, evidenced ruling, or leave it
   resting on the derived-by-subtraction default.*
4. **This run changed no behaviour and needs no gate.** Stamp `sim-2026.08-v30` is untouched, no
   production file moved, no user-facing control was added, moved or removed. *Decision: whether
   the next run is the read-only production query of item 1, or something else.*

### The four decisions carried from Run 45 section 10, one line each (§7 item 1)

1. **`totalFloat` / `consumedFloat` are still UNDETERMINED** — rule the contradiction now, or leave
   it until a module in service actually consumes one of them.
2. **The event-accumulation rule for `changeOrderCount` is undefined** — define the third retrieval
   rule (union at-or-before, latest-per-entity), or accept the under-report and record it as
   intended.
3. **The four past-performance ratings rest on the weakest evidence in the classification** —
   revisit only if a module comes to consume them; nothing else triggers a review.
4. **`BRIEF_CAT_LABEL` is a one-line naming fix carried unacted since Run 44** — schedule it, or
   leave it.

### Suites and artifacts

Three suites read `T6_HANDOFF.md` and were run after this run's handoff entry was appended, to
confirm the append breaks nothing: `test_run32_qualifier_count_closure.py` **18/18**,
`test_run35_closure_voter_identities.py` **15/15**, `test_run37_documentation_scope.py` **18/18**.
**No full-suite run was performed**, and none of the 18 audit artifacts the full suite rewrites (17
under `code_audit/` plus `server/tools/run17/coverage.csv`) was touched — `git status` was verified
clean of them before commit. `git add -A` and `git add .` were never used; every `git add` in this
run names its paths.
