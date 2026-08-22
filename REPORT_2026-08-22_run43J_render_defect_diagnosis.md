# Run 43J — Render Defect Diagnosis

**Date:** 2026-08-22
**Repository used:** the Linux clone at `/home/user/LinPRojectRadar`.
**Branch:** `main` at the Run 43 merge, `sim-2026.08-v28`, `og-participant-2026.08-v14`.
**What this is:** a diagnosis. **No fix is written. No behaviour is changed.** The only files this
phase creates are this report and one read-only artifact,
`code_audit/run43J_in_service_abstentions.csv`.
**Scope:** modules in service only. The 38 retired modules are out of scope.

---

## 0. The section 2 gate, and the standing of this phase

| condition | verdict |
|---|---|
| Phase H merged, `HEAD == main == origin/main` | **satisfied** — `405f3d3` |
| full suite green on merged main | **satisfied** — 188 suites, 14,197 / 14,197, 0 red, 0 aborting |
| `sim-2026.08-v28` stamped, every gate re-run and reported | **satisfied** — 31/31, 0 of 15 blocker classes blocked |
| no Phase H stop condition open | **satisfied** |

---

## 1. What could and could not be reached

`PRJ-001` exists in no repository file. This was re-verified: no file under the repository root
contains that identifier as a project. Its stored rows live in production Postgres, which
**stop condition 14.1 forbids touching and which was not touched.**

Everything below is therefore one of three things, and each claim says which it is:

* **Code fact** — read or executed from the repository.
* **Fixture fact** — reproduced through the real routes on a throwaway SQLite database.
* **G** — not determinable from available evidence, with the access that would answer it named.

**Rule 4 of section 13 applies once**, at defect 10: the repository contradicts Run 41A's account
of the twelve-versus-eleven mechanism. Both are reported and the one I verified is stated.

---

## 2. The fixture

### 2.1 Definition

Built through the **real routes** — `/exec` `projectcreate`, `projectupload`, `projectcompute`,
`projectresults` — against a throwaway migrated SQLite database in the session scratchpad.
Production Postgres was never configured or contacted. The fixture files were deleted after use,
as section 8 requires; the definition is reproduced here in full so it can be rebuilt.

**The extraction model is stubbed** (`app.documents.set_extractor_override` with
`app.extraction_client.StubExtractor`). That is the same route every suite in this repository uses
and the only one available: `NAMING_AUTHORITY.md` records that extraction has never run against a
real project document. **Everything downstream of extraction is the production path, untouched** —
`emit_observations`, the field registry, `select_signal_inputs`, the period binding, the module
dispatch, the fusion, and the stored row.

Four reporting periods. Per period: a Monthly Progress Report, a Pay Application (G702) and a
Time-phased Schedule / Baseline. One Contract Value / Original Agreement, uploaded at period 1.
Figures scaled so that **period 4 lands on the section 9 render's own EV, AC, actual % and
planned %**, with `BAC = 5,874,620`:

| period | report date | EV | AC | PV (cumulative) | actual % | planned % |
|---|---|---|---|---|---|---|
| 1 | 2026-03-31 | 261,684 | 214,483 | 271,400 | 4.54 | 4.62 |
| 2 | 2026-04-30 | 523,368 | 428,965 | 542,800 | 9.08 | 9.24 |
| 3 | 2026-05-31 | 785,051 | 643,448 | 814,200 | 13.62 | 13.86 |
| 4 | 2026-06-30 | 1,046,735 | 857,930 | 1,085,600 | 18.16 | 18.47 |

Emissions per document type, exactly as `extraction_merge._NUMERIC_EMISSIONS` consumes them:

* `monthly_report` → `earned_value`, `actual_cost`, `planned_value`, `budget_at_completion`,
  `actual_percent_complete`, `planned_percent_complete`, `report_date`, `document_date`
* `pay_application` → `amount_paid_to_date`, `percent_complete_verified`, `completed_to_date`,
  `original_contract_sum`, `application_date`, `document_date`
* `time_phased_schedule` → `planned_value_to_date`, `planned_percent_complete`, `data_date`,
  `document_date`
* `contract_value` → `original_contract_sum`, `project_start_date`, `project_end_date`,
  `document_date`

**Four variants were built**, because section 9 item 4 offers two candidate causes and each needed
its own probe:

| variant | difference |
|---|---|
| `PRJ-J-DATED` | each Time-phased Baseline carries its **own** period `data_date` |
| `PRJ-J-BASELINE` | all four Time-phased Baselines carry **one** `data_date` (2026-03-01), which is what a *baseline* document is. Period binding cannot distinguish them and the tie falls to the content hash |
| `PRJ-J-PERIODPV` | the Time-phased Baseline states the **period** planned value instead of the cumulative planned-value-to-date, with `planned_percent_complete` unchanged |
| `PRJ-J-RICH` | period 4 additionally carries a `lookahead_schedule`, a `resource_report`, an `rfi_log` and a `change_order`, supplying every field section 11 names |

### 2.2 What the fixture reproduced

| section 9 symptom | reproduced? | evidence |
|---|---|---|
| CPI 1.22 | **YES, exactly** | `cpi=1.22` at every period of every variant |
| SPI 1.27 | **NO** — SPI computes to **0.964** | `spi=0.964` at every period of `PRJ-J-DATED` and `PRJ-J-BASELINE` |
| PV understated ~24% | **NO** — PV binds to the correct period in **both** baseline variants | `pv=1,085,600` at period 4, sourced `time_phased_schedule asOf=2026-06-30` |
| Document-risk score absent from storage | **YES** | `signal_inputs.docRiskScore = None`, present-and-null |
| "Reporting period" blank | **YES** | `p.reportingPeriod` is written by no server code path |
| longitudinal locked with four periods | **YES** | 4 live `ComputedResult` rows, `gethistory` returns 0 |
| A1 Amber over Green computing modules | **NO** — A1 reads Green | `category_statuses["A1"].status = "Green"`, `module_count = 2` |
| twelve-versus-eleven | **NO** — the fixture computes 1 category, too few document types | stated as a fixture limitation, not an absence |

**A symptom not reproduced is not thereby absent.** Where a symptom did not reproduce, the report
says what the fixture rules out and what remains open.

---

## 3. Defect 1 — PV understated by roughly 24 per cent

**Classification: G — not determinable from available evidence.** The two candidate causes are
*not* equally open: one is **ruled out by execution** and the other is **unfalsifiable without the
document**.

### 3.1 The trace of every value reaching `pv`, `ev`, `ac`, `bac`

Read from `signal_inputs.sources`, the per-field source record, on `PRJ-J-DATED`. Each entry names
the document type, the `as_of` the winning observation carried, and the value.

| period | field | document type | field on the document | `as_of` | value |
|---|---|---|---|---|---|
| 1 | `bac` | `contract_value` | `original_contract_sum` | 2026-03-01 | 5,874,620 |
| 1 | `ev` | `pay_application` | `completed_to_date` | 2026-03-31 | 261,684 |
| 1 | `ac` | `pay_application` | `amount_paid_to_date` | 2026-03-31 | 214,483 |
| 1 | `pv` | `time_phased_schedule` | `planned_value_to_date` | 2026-03-31 | 271,400 |
| 2 | `bac` | **`pay_application`** | `original_contract_sum` | 2026-04-30 | 5,874,620 |
| 2 | `ev` | `pay_application` | `completed_to_date` | 2026-04-30 | 523,368 |
| 2 | `ac` | `pay_application` | `amount_paid_to_date` | 2026-04-30 | 428,965 |
| 2 | `pv` | `time_phased_schedule` | `planned_value_to_date` | 2026-04-30 | 542,800 |
| 3 | `bac` | **`pay_application`** | `original_contract_sum` | 2026-05-31 | 5,874,620 |
| 3 | `ev` | `pay_application` | `completed_to_date` | 2026-05-31 | 785,051 |
| 3 | `ac` | `pay_application` | `amount_paid_to_date` | 2026-05-31 | 643,448 |
| 3 | `pv` | `time_phased_schedule` | `planned_value_to_date` | 2026-05-31 | 814,200 |
| 4 | `bac` | **`pay_application`** | `original_contract_sum` | 2026-06-30 | 5,874,620 |
| 4 | `ev` | `pay_application` | `completed_to_date` | 2026-06-30 | 1,046,735 |
| 4 | `ac` | `pay_application` | `amount_paid_to_date` | 2026-06-30 | 857,930 |
| 4 | `pv` | `time_phased_schedule` | `planned_value_to_date` | 2026-06-30 | 1,085,600 |

**Every value binds to its own period. Not one leaks across a period boundary.**

### 3.2 An incidental finding inside the trace, which the section 9 evidence does not show

**`bac` moves off the contract at every period after the one the contract was uploaded into.**

`_period_documents` (`server/app/documents.py:373`) is:

```
.where(DocumentUpload.project_id == project.id, DocumentUpload.period == period)
```

The observation set for a period is **only the documents uploaded into that period**. A contract
uploaded at period 1 is invisible at periods 2, 3 and 4. `bac`'s declared writer precedence
(`server/app/field_registry.py:183`) is `change_order 0, contract_value 1, schedule_of_values 2,
pay_application 3, monthly_report 4` — but precedence can only choose among observations that are
*present*, and at period ≥ 2 the contract's is not. So `bac` falls through to whatever document in
that period states a contract sum. In the fixture that is the pay application's
`original_contract_sum`.

**This is the mechanism the corpus warning describes**, and the field registry confirms the second
half of that warning literally: `FIELD_KINDS` and `WRITER_TIERS` have no basis dimension, and no
code path anywhere compares a value's basis. A fee-basis `original_contract_sum` on an invoice
would be admitted as `bac` with nothing to stop it.

**It is not, however, what section 9 shows.** Section 9 names `bac`'s source as *Contract Value /
Original Agreement*, so on PRJ-001's displayed period `bac` came from the contract. The
fee-substitution mechanism is real and reachable; **it is not evidenced as having occurred for
`bac` on this render.**

### 3.3 Candidate cause 2 — four baselines, one PV retained — is RULED OUT

Built and executed both ways:

* `PRJ-J-DATED`, each baseline with its own `data_date`: period 4's `pv` is period 4's figure.
* `PRJ-J-BASELINE`, **all four sharing one `data_date`**: period 4's `pv` is *still* period 4's
  figure, sourced `time_phased_schedule asOf=2026-06-30`.

The second result is the decisive one. Even when the baselines cannot be told apart by their own
`data_date`, `document_as_of` (`extraction_merge.py:726`) falls back to `document_date`, and the
per-period document set (§3.2) means only that period's baseline is in the candidate group at all.
**The retained PV belongs to the displayed period. Candidate cause 2 does not reproduce and does
not explain the gap.**

### 3.4 What the section 9 figures require, and why it cannot be settled here

Section 9 gives, on one render: `PV = 824,370`, `Planned % complete = 18.47`,
`BAC = 5,874,620`. 18.47 % of 5,874,620 is **1,085,046**. The stored PV is 14.03 % of BAC.

**`pv` and `plannedPctComplete` are emitted by the same document.** `extraction_merge.py:565-566`:

```python
"time_phased_schedule": (
    ("planned_value_to_date", "pv"), ("planned_percent_complete", "plannedPctComplete"),
```

and section 9 names *Time-phased Schedule / Baseline* as the source of both. So the inconsistency
is **inside one document's extraction, not across a merge.** That eliminates every cross-document
explanation, including the period-binding one.

Three explanations remain and the evidence does not distinguish them:

1. the two figures are on **different bases** — a fee-basis planned value against a cost-basis BAC
   (824,370 / 0.1847 implies an own-baseline total of 4,463,290);
2. `planned_value_to_date` was **mis-extracted** from a different cell of the same document;
3. the document itself states an inconsistent pair.

A fourth was tested and **rejected**: a period figure mistaken for a cumulative one. `PRJ-J-PERIODPV`
gives `pv = 271,400`, 4.62 % of BAC and `spi = 3.857` — an overshoot of the wrong sign and
magnitude, nothing like section 9's.

> **G. The access that would answer it:** the extracted field values of PRJ-001's Time-phased
> Schedule / Baseline document for the displayed period — the stored `document_extractions` /
> observation rows, or the document itself. Both are in production Postgres or the PRJ-001 document
> set. Stop conditions 14.1 and 14.2 forbid reaching either.

---

## 4. Defect 2 — CPI 1.220 and SPI 1.270 against authored figures of 0.94 to 1.01

**Classification: G for CPI. For SPI, item 1 fully accounts for it and nothing else is needed.**

**Item 1 does NOT fully account for it, and the reason is arithmetic.** `select_signal_inputs`
(`extraction_merge.py:968-973`) computes:

```python
cpi = _round3(si["ev"] / si["ac"])       # PV is not in this expression
spi = _round3(si["ev"] / si["pv"])
```

* **SPI is entirely inherited from PV.** With a period-consistent PV the fixture computes
  **`spi = 0.964`** — consistent with actual 18.16 % below planned 18.47 %, which is what section 9
  item 2 predicts. Correct PV, correct SPI. Item 1 accounts for SPI completely.
* **CPI does not read PV at all.** The fixture reproduces **`cpi = 1.22` exactly**, from
  `ev = 1,046,735` (pay application `completed_to_date`) over `ac = 857,930` (pay application
  `amount_paid_to_date`). The formula is right and the division is right.

So CPI 1.22 against an authored 0.94–1.01 means **EV and AC are not on the same basis as each
other, or not the pair the corpus authored.** Section 9's own note is that EV came from the Pay
Application while AC came from the Monthly Progress Report — two different documents. `ac`'s writer
precedence is `pay_application 0, monthly_report 1`, so AC coming from the monthly report means the
pay application in that period supplied **no** `amount_paid_to_date`, while the *same* pay
application did supply `completed_to_date` for EV. A partially-extracted G702 produces exactly that.

> **G. The access that would answer it:** PRJ-001's stored observations for `ev` and `ac` in the
> displayed period, showing whether the pay application emitted one figure and not the other, and
> the corpus's authored EV/AC pair. Production Postgres and the PRJ-001 document set.

---

## 5. Defect 3 — document-risk score empty in storage, printed as `0.00` Green

**Classification: F — render or presentation defect, storage correct. The evidence DOES distinguish
the two candidate sites: `assets/js/detail.js` produced it.**

**Storage is correct, and correct deliberately.** `select_signal_inputs` initialises every key to
`None` (`extraction_merge.py:915`), so a project with no document-risk observation carries
`docRiskScore` **present and null**, not absent:

```
empty-observation select -> 'docRiskScore' in si: True | value: None
```

That is the shape `extraction_merge.py:1128` protects — a genuine zero must be stored and must be
distinguishable — and the fixture confirms it end to end: `signal_inputs.docRiskScore = None`.

**`assets/js/detail.js:1528-1531` turns that null into `0.00` Green.** (The order named
1521-1524; the site has moved seven lines and is quoted here at its current position.)

```js
const docScore = Number(s.doc && s.doc.score != null ? s.doc.score : si.docRiskScore);
if (Number.isFinite(docScore)) {
  out.push({ label: "Document risk", value: docScore.toFixed(2),
             status: docScore >= 0.70 ? "Red" : docScore >= 0.40 ? "Amber" : "Green" });
}
```

Executed:

```
null       Number -> 0    isFinite: true  | renders "0.00" status Green
undefined  Number -> NaN  isFinite: false | OMITTED
0          Number -> 0    isFinite: true  | renders "0.00" status Green
```

The enclosing function is `briefKeySignals` (`detail.js:1497`), whose return is truncated to
`out.slice(0, 6)` (`:1532`) and shipped into the brief prompt at `:1609` as *"Computed key signal
values (internal context, quote these ACTUAL numbers in Key Drivers)"*. So the `0.00` Green is
carried into the Executive Brief as a key driver, exactly as section 9 reports. **A genuine
extracted 0.00 and an absent score are indistinguishable on that surface** — the defect that
`extraction_merge.py:1128` exists to prevent, reintroduced at the render.

**`assets/js/signals.js:535-536` did NOT produce it.** Those lines sit inside `portfolioVector(p)`
(`signals.js:527`), which builds the Portfolio Health comparison vector and nothing else. It is not
on the Executive Brief path. It is now doubly irrelevant: all five Portfolio Health identities were
retired from service at Run 43, so that path emits nothing at all.

**The signals panel itself is correct.** `extractedTableHtml` gates on `raw != null`
(`signals.js:1737`), so `docRiskScore` renders `—` with no mark — which is exactly what section 9's
panel shows.

**Incidental, in scope:** `A4.1 Document Risk Score` is registered, **in service**, and **unported**
— `registry.unported_modules() == ["A4.1"]`. It publishes **no row at all** on the production path
(fixture: outcome `NO_ROW`). The document-risk value is supplied by extraction and computed by no
module, which is why nothing on the analytical side ever contradicts a `0.00` invented at the render.

---

## 6. Defect 4 — CPI and SPI labelled "extracted" when they are computed

**Classification: F — render or presentation defect, storage correct.**

`assets/js/signals.js:94-104` declares the panel rows, and CPI and SPI are in the list with labels
that already say what they are:

```js
{ key: "cpi", label: "CPI (computed)", editable: false },
{ key: "spi", label: "SPI (computed)", editable: false }
```

`extractedTableHtml` (`signals.js:1735-1755`) then stamps every row that has a value,
unconditionally and with no test of whether the field is derived:

```js
const mark = has ? `<span class="ds-extracted" title="extracted">✓ extracted</span>` : "";
```

The whole table sits under the eyebrow `Extracted signal inputs` (`signals.js:1885`). CPI and SPI
are computed by `select_signal_inputs` (`extraction_merge.py:968-973`) and carry **no** entry in
`signal_inputs.sources`, so the `via <document>` tag is empty while the `✓ extracted` mark is
present. That is precisely section 9's *"CPI (computed) 1.22 — labelled 'extracted'"*.

Storage is correct: the two are derived values in a derived-values slot with no source record,
which is the truthful shape.

---

## 7. Defect 5 — A1 reads Amber while TCPI and Variance at Completion read Green

**Classification: G — not determinable from available evidence. But the mechanism is closed off by
execution, and section 9's stated rule is not the rule the code implements.**

### 7.1 Only two modules can contribute a band to A1

`server/app/simulation/compute.py:97-105`:

```python
for row in run["computed"]:
    if row["module_id"] not in CORE_VOTING_MODULES:
        continue
    ...
    by_category.setdefault(row["category"], []).append(qs)
```

`CORE_VOTING_MODULES` is exactly `['A1.7', 'A1.8']` — TCPI and Variance at Completion, both **in
service**. The fixture confirms it: `category_statuses["A1"]` carries `module_count = 2` while three
A1 modules computed; `A1.2 CUSUM Anomaly Monitor` computed a status and was **not** admitted.

**So the A1 category status is the fusion of TCPI and VAC and of nothing else.** No other module —
in service, retired, computing or abstaining — can move it.

### 7.2 Two Greens cannot fuse to Amber

Executed against the shipped `fuse_signals`:

```
lineage_record supplied=True : status=Green conflict=0.3088 bodies=2 declared=True
   mass: {Green 0.9722, Yellow 0.0139, Amber 0.0087, Red 0.0046, Unknown 0.0006}
lineage_record supplied=False: status=Green conflict=0.0 bodies=0 declared=False
   unresolved_band=Green   mass: {Green 0.80, Yellow 0.08, Amber 0.06, Red 0.04, Unknown 0.02}
sweep of 1..8 all-Green bodies -> Green Green Green Green Green Green Green Green
```

Nothing downstream alters it: `fuse_qualified` (`qualification_gate.py:319-335`) only reshapes and
refuses, it never changes a band; `compute.py` writes `category_statuses[cat]` once (`:122`) and
never mutates it; and the client reads it verbatim —
`getCategoryStatus` returns `(stored && stored.status) || null` from
`row.category_statuses[cat.num]` (`assets/js/taxonomy.js:547-549`) and recomputes nothing.

### 7.3 The repository contradicts section 9's stated rule, and it does not matter

Section 9 argues from *worst-active-module-wins*. **The code does not implement that between
modules.** `fuse_signals` uses `worst_band` only **within** a body of evidence
(`fusion.py:141-144`, applied at the body level) and **Dempster's rule between** bodies, reporting
the argmax of the fused mass (`fusion.py:318-321`). The premise is wrong about the rule. It is
right about the outcome, which I verified directly by execution above: all-Green in, Green out.

### 7.4 What this leaves

If TCPI and VAC both read Green, the server cannot have written Amber. Three possibilities remain
and the evidence does not distinguish them: TCPI or VAC did not in fact read Green on that render;
the Amber the reader saw belongs to a different element than `category_statuses["A1"].status`; or
the stored row was written by an earlier version of the fusion.

> **G. The access that would answer it:** PRJ-001's stored `category_statuses["A1"]` together with
> its `module_results` rows for `A1.7` and `A1.8`, and the row's `simulation_version`. Production
> Postgres. Stop condition 14.1.

**Stop condition 14.5 was checked explicitly and does not fire.** `A1.1 Monte Carlo EAC Forecast`
is the one retired module in category A1, and the obvious worry is that it supplied the Amber. It
cannot have: it is not in `CORE_VOTING_MODULES`, so `compute.py:98` skipped it before the
retirement as it does after. **This defect does not prove to involve a retired module.**

---

## 8. Defect 6 — the header attributes the Amber to TCPI, which is Green

**Classification: F — render or presentation defect, storage correct.** Two independent mechanisms,
both established from code, one of them observed live in the fixture.

### 8.1 The status and the "worst module" are drawn from different populations

`assets/js/detail.js:1543-1553`:

```js
const worst = (c.modules || [])
  .filter((m) => m.status)
  .slice()
  .sort((a, b) => (order[a.status] != null ? order[a.status] : 3) - (order[b.status] != null ? order[b.status] : 3))[0];
const worstDesc = worst ? " (worst: " + worst.name + ...) : "";
return c.num + " " + c.name + ": " + c.status + worstDesc;
```

* `c.status` comes from the server's fusion of **the two voting modules only** (§7.1).
* `c.modules` comes from `buildCategorySnapshot` (`signals.js:418-426`), which walks
  **`cat.modules` from `LIN_CATEGORIES`** — all ten A1 modules in service.

**Nothing checks that `worst.status` is as adverse as `c.status`.** When the category is Amber and
every module in the client's list reads Green, `worst` is a Green module, and the line reads
`A1 Cost and EVM Performance: Amber (worst: TCPI, …)`. Executed:

```
all-Green category, worst picked: {"name":"TCPI","status":"Green"}
```

### 8.2 An unrecognised status sorts as Yellow, and the platform emits one

`order` is `{Red:0, "Red-review":1, Amber:2, Yellow:3, Green:4, Complete:5}` and an unknown status
defaults to **3** — more adverse than Green. **The platform emits a status the map does not
contain.** From the fixture's stored row, through the real routes:

```
A1.2 'green'   votes= False      <- lowercase
A1.7 'Green'   votes= True
A1.8 'Green'   votes= True
```

Executed on that exact list:

```
worst picked: {"name":"CUSUM Anomaly Monitor","status":"green"}
```

A module whose only irregularity is its capitalisation is selected as the category's "worst" ahead
of two properly-cased Green ones — and `A1.2` is a module that does not vote and therefore did not
contribute to the status at all.

Both mechanisms feed the brief prompt at `detail.js:1610`, *"Per-category worst module"*. Storage
is correct throughout; only the attribution is wrong.

---

## 9. Defect 7 — the recommendation against its own key drivers

**Classification: F for the mechanism; G for whether the model read them on that render.**

The two sections are anchored on **different inputs of the same prompt**, and nothing requires them
to agree.

* **Key Drivers** is anchored on `keySignals` — `detail.js:1609` supplies *"Computed key signal
  values (internal context, quote these ACTUAL numbers in Key Drivers)"*, and `:1627` instructs
  *"each naming a SPECIFIC computed signal value from the list above"*.
* **Recommendation** is anchored on the governance decision record — `detail.js:1611-1613` supplies
  `"Overall governance state: " + (gov.state || "unknown")` and `"Recommended action on file: " +
  (gov.action || "unknown")`, read from `snapshot.governance` (`signals.js:372-378`,
  `:493-494`), which is built from the stored **decision** (`d.state`, `s.decision.state`) and not
  from any signal. `:1618-1620` then instructs *"Begin with the overall status in CAPS followed by
  ' · ' and a single short action clause"*.

So a Red or Amber governance state produces a review recommendation while every key driver reads
Green, with no inconsistency for anything to catch: **no code compares the recommendation to the
drivers.**

> **G on the instance. The access that would answer it:** the stored brief request and response for
> PRJ-001 — the exact prompt text sent and the text returned. Whether one generation attended to a
> section of its own prompt is not a code fact and cannot be read out of the repository.

---

## 10. Defect 8 — `Reporting period:` blank, and the longitudinal view locked with four periods

**Classification: C — stored fact exists, canonical mapping or query failed. Both halves reproduced
through the real routes.**

### 10.1 The longitudinal view queries a store the compute path never writes

Reproduced on the fixture after computing four periods through `/exec`:

```
projectperiods -> periods: [1, 2, 3, 4], next_period: 5
gethistory     -> ok=False, history length=0
ComputedResult rows for this project: 4 | periods: [1,2,3,4] | live (not superseded): 4
ProjectSnapshot rows for this project: 0
```

* `periodComparisonHtml` (`detail.js:607-612`) gates on `storedHistory(project).length >= 2`.
* `storedHistory` (`detail.js:499-503`) reads `project.history`, filtered to entries with a truthy
  `h.period`.
* `project.history` is filled from `?action=gethistory`, which reads **`project_snapshots`**
  (`facade.py:371-378`), a store `models.py:78-84` says is *"deliberately separate"* from the
  computed results.
* `project_snapshots` rows are written **only** by `w_savehistory` (`writes.py:605-617`), a
  client-initiated action that takes a `snapshot` payload from its caller.
* `_compute_and_store` writes a `ComputedResult` (`documents.py:1572`) and **no** `ProjectSnapshot`.

Four computed periods therefore yield zero history entries and the panel renders *"Longitudinal
view unlocks after two reporting periods."* The facts are stored; the view asks a different store.

### 10.2 `reportingPeriod` is written by no server code path

`detail.js:1007` renders:

```js
Reporting period: <span class="mod-mono">${esc(p.reportingPeriod)}</span> ·
```

Every occurrence of `reportingPeriod` in the repository is client-side — `app.js`, `assistant.js`,
`categories.js`, `data.js` (the two demo rows), `decision.js`, `detail.js`, `signals.js`,
`taxonomy.js`. **No file under `server/app/` writes it.** `assistant.js:29` states the consequence
in its own comment: *"Server-created projects carry no sector and no reportingPeriod."* And
`esc(undefined)` is the empty string:

```
esc(undefined) -> []   esc(null) -> []
```

So the label renders with a blank value. The period is stored — `projectperiods` returns all four
and every `ComputedResult` carries its `period` — and this header reads a field the server never
populates.

---

## 11. Defect 9 — 75 uploaded and 25 retained against a documents panel reading 100

**Classification: F — render or presentation defect, storage correct. Both figures are correct for
what they count, and they reconcile: 75 + 25 = 100.**

Both surfaces read the **same array**, `project.events`, filtered to `signals_extracted`.

| surface | what it counts | code |
|---|---|---|
| Documents panel | **every** `signals_extracted` event, unioned with `signalInputs.sources` doc types — no partition | `detail.js:658-672`, rendered at `:779` as `Documents: ${evs.length}` |
| Signal-flow note | the same events **partitioned at the last `signals_reset` event**: those after it are `uploadedDocCount`, those before it are `retainedBeforeReset` | `neural_flow.js:419-424`, `:444-463`, `:487-493`, header at `:758-761` |

The note's own wording is `uploadedDocCount + ' UPLOADED SINCE THE RESET, ' + retainedBeforeReset +
' RETAINED'`. Neither number is wrong; the documents panel simply does not partition, so a reader
sees 75 beside 100 with nothing on screen reconciling them. `neural_flow.js:482-483` records that
this exact class was corrected once before: *"the NUMBER was right for what it counted and the
WORDS asserted something else."*

---

## 12. Defect 10 — twelve categories in the brief, eleven in the Signal Ledger

**Classification: F — render or presentation defect, storage correct.**
**Section 13 rule 4 applies: the repository contradicts Run 41A's account, and I verified the
repository.**

### 12.1 The mechanism, confirmed against the code

| surface | population | code |
|---|---|---|
| **Signal Ledger — 11** | `LIN_CATEGORIES` filtered to exclude `level === "portfolio"`, rendered whatever the status | `app.js:1304-1306`: `const projectCats = window.projectLevelCategories ? projectLevelCategories() : LIN_CATEGORIES.filter((c) => !(c && c.level === "portfolio"));` |
| **Executive Brief — 12** | **all** of `LIN_CATEGORIES`, with **no** level filter | `signals.js:418`: `LIN_CATEGORIES.forEach((cat) => {…})`, consumed by `briefCategoryGroups` (`detail.js:1476-1493`) |

**The difference is the `level: "portfolio"` filter alone.**

### 12.2 Run 41A's account is half confirmed and half refuted

* **Refuted:** the difference is *not* governed by `contributes_to_project_status`.
  `compute.py:26-37` returns `group not in ("C", "D")` — it excludes **C and D**, which would give
  **10**, not 11. And neither `briefCategoryGroups` nor `categoryLedgerHtml` consults it at all.
  Group C (`C1`, seven modules in service) **is** rendered by the ledger and **is** enumerated by
  the brief; it simply does not vote in the project rollup. The twelve-versus-eleven gap is Group D
  alone.
* **Confirmed:** `assets/js/detail.js` ships the literal `"Cat 1-12"` into the brief's prompt. The
  line has moved — Run 41A cited 1607; it is now **`detail.js:1617`**:

  > `"Do NOT mention category numbers except when grouping them in Signal Pattern; a program director does not think in Cat 1-12.\n\n"`

### 12.3 The correct number after the retirement

Measured from the shipped `assets/js/taxonomy.js`:

```
LIN_CATEGORIES objects: 12
categories carrying >=1 module in service: 11
empty: [ 'D1 Portfolio Health' ]
parked: []
```

**Eleven.** The taxonomy still declares twelve category objects, and `D1 Portfolio Health` now
carries **zero** modules. The ledger already renders 11 and is unchanged by the retirement. The
brief still enumerates 12: `buildCategorySnapshot` walks all twelve, `D1`'s `cat.modules` is now
`[]`, so it yields no status and lands in `groups.Conditional` — the brief will report a twelfth
category as *"CONDITIONAL / NO DATA"* forever. And the literal `"Cat 1-12"` is now wrong twice over:
against the eleven the ledger shows, and against `NAMING_AUTHORITY.md:96`, which forbids a module or
category number in user-facing text at all.

---

## 13. Defect 11 — "All required values present. Nothing outstanding" while most modules abstain

**Classification: F — render or presentation defect, storage correct.**

**The population "required" ranges over is: the `missing` array returned by the most recent
extract-or-upload response in the current browser session for this project id, defaulting to the
empty array when there has been none.** It has no relationship to the modules, to the analytical
inputs, or to the stored row.

`assets/js/signals.js:1862-1878`:

```js
function panelInnerHtml(project) {
  const id = project ? project.id : "";
  const entry = cache[id] || {};
  ...
  const si = entry.signalInputs || (persistedHasData ? persisted : null) || storedSi;
  const missing = entry.missing || [];
```

and `signals.js:1814-1816`:

```js
function missingHtml(missing) {
  if (!missing || !missing.length) {
    return `<p class="kn-sub ds-missing-clear">All required values present. Nothing outstanding.</p>`;
```

`cache[id]` is written at exactly three sites — `signals.js:1196`, `:1555`, `:1964` — all inside
extraction and upload handlers. **`si` has a three-step fallback that ends at the stored row;
`missing` has none.** On any page load without an upload in that session, `entry` is `{}`,
`missing` is `[]`, and the panel asserts that nothing is outstanding — directly beneath a table of
values it read from the stored row.

The fixture shows the scale of what the claim is silent about: on a four-period project computed
through the real routes with a rich document set, **4 modules in service computed and 58
abstained**.

---

## 14. Section 11 — abstention classification for modules in service

Measured on `PRJ-J-RICH`, period 4, which supplies **every field section 11 names**:

```
activitiesPlanned = 200      activitiesConstrained = 37     lookaheadWeeks = 6
plannedLaborHours = 41000    actualLaborHours = 44800
rfiCount = 84   rfiOpen = 19   rfiOverdue = 6   rfiOldestOpenDays = 63
changeOrderCount = 7
originalContingency = None   remainingContingency = None   docRiskScore = None
```

Full per-module outcomes are in `code_audit/run43J_in_service_abstentions.csv` (63 rows, one per
module in service).

| # | module | outcome with its named fields supplied | classification |
|---|---|---|---|
| 1 | **A2.7** Milestone Trend Analysis | ABSTAINS, `canonical_structure_absent`. Awaits *"a milestone forecast history: each milestone's committed date and the date it was forecast for in each reporting period since."* `activitiesPlanned` is a count of activities, not a per-milestone forecast history. | **D** — canonical input genuinely absent |
| 2 | **A2.8** Look-Ahead Schedule Health | ABSTAINS, `canonical_structure_absent`, **with `lookaheadWeeks`, `activitiesPlanned` and `activitiesConstrained` all present**. Awaits *"the window it covers, the activities planned in it, and whether **each one** still carries an open constraint."* Three scalars are not a per-activity constraint inventory. This is section 11's own worked example, confirmed by execution. | **D** on the missing parts |
| 3 | **A3.2** Contingency Burn Rate | ABSTAINS, `missing_required_input`: *"the original and remaining contingency amounts are needed, and at least one of them has not been reported for this period."* **`originalContingency` and `remainingContingency` have exactly ONE writer in the whole emission table — `pay_application` (`extraction_merge.py:562-563`). There is no contingency-status document type.** | **G** — see below |
| 4 | **A4.2** RFI Velocity | **COMPUTES**, Red: *"84 RFIs over 30 days (84/30d, 19.6/week), 6 overdue (7%), avg response 11 days"*. Its named inputs are sufficient. | **G** for PRJ-001 — see below |
| 5 | **A4.6** Change Order Frequency | ABSTAINS, `canonical_structure_absent`, **with `changeOrderCount = 7` present**. Awaits *"a change event register with the exposure it is measured over: each change, its type, cause and value, and the span of time or contract value it arose against."* A count is not a register. | **D** on the missing parts |
| 6 | **A3.3** Labor Productivity Index | ABSTAINS, `canonical_structure_absent`, **with both labour-hour fields present**. Awaits *"a record of production: the quantity of work installed, the quantity planned, and the labour hours each of those took."* Hours without quantities are not productivity. | **D** on the missing parts |

**A3.2 — why G rather than D.** The module's requirement is two scalars and the platform can carry
them, but only from a pay application. Section 11 names *"the Owner Design Contingency Status
documents"* on PRJ-001. Whether those documents are classified as a type that emits
`original_contingency` / `remaining_contingency`, as some other type, or as unmapped, decides
between **A** (the source fact exists and extraction dropped it) and **D** (genuinely absent).

> **The access that would answer it:** PRJ-001's `documents` rows for those artefacts — the assigned
> `doc_type` and the extracted keys. Production Postgres, stop condition 14.1.

**A4.2 — why G rather than a defect.** It computes from exactly the fields section 11 names, so
nothing in the module's own contract makes it abstain. If it abstains on PRJ-001 while those fields
are extracted, the cause lies elsewhere.

> **The access that would answer it:** PRJ-001's stored `signal_inputs.rfiCount` / `rfiOpen` /
> `rfiOldestOpenDays` for the displayed period and its `A4.2` row. Production Postgres.

### 14.1 The wider abstention picture, and one honest limitation

Of the 63 modules in service on the rich fixture: **4 computed, 58 abstained, 1 published no row**.
The 58 break down as

| code | count |
|---|---|
| `canonical_structure_absent` | 39 |
| `CATEGORY9_ASSESSMENT_MISSING` | 16 |
| `insufficient_history` | 1 |
| `missing_required_input` | 1 |

**The 16 `CATEGORY9_ASSESSMENT_MISSING` abstentions are a fixture limitation, not a finding about
PRJ-001.** The fixture supplies no governed Category-9 assessment, and from `sim-2026.08-v19` a
package without one fails closed. They are reported here so the count reconciles and are **not**
classified.

`A4.1 Document Risk Score` is the one `NO_ROW`: registered, in service, and the single member of
`registry.unported_modules()`.

---

## 15. The ten unconsumed extraction fields

**All ten are declared in `server/app/extraction_fields.py` and mapped to no `signalInputs` key in
`server/app/extraction_merge.py`.** Measured:

```
actual_equipment_days          merge_mentions=0 fields_decl=1  emission_map=NONE
analogous_project_type         merge_mentions=0 fields_decl=1  emission_map=NONE
constraint_rate                merge_mentions=0 fields_decl=1  emission_map=NONE
environmental_observations     merge_mentions=0 fields_decl=1  emission_map=NONE
items_passed                   merge_mentions=0 fields_decl=1  emission_map=NONE
on_schedule                    merge_mentions=0 fields_decl=1  emission_map=NONE
planned_equipment_days         merge_mentions=0 fields_decl=1  emission_map=NONE
rfi_answered                   merge_mentions=0 fields_decl=1  emission_map=NONE
safety_observations            merge_mentions=0 fields_decl=1  emission_map=NONE
subcontractor_observations     merge_mentions=0 fields_decl=1  emission_map=NONE
```

The extraction model is asked for each of them and the merge drops each of them. Run 42's finding
is re-verified.

### Does any module in service abstain for want of an input one of these already carries?

**No.** Every abstention reason of every module in service was searched for the concept each field
carries. Four fields match a reason; in each case the module awaits a **per-entity structure** that
a single scalar or label cannot supply, and the other six are named by no abstention reason at all.

| field | in-service module whose reason mentions the concept | what the module actually awaits | satisfied? |
|---|---|---|---|
| `constraint_rate` | **A2.8** Look-Ahead Schedule Health | *"whether **each one** still carries an open constraint"* — per-activity status | **No.** A rate is an aggregate over activities |
| `items_passed` | **A4.4** NCR Rate | *"the nonconformances raised, and the inspections, hours or value they arose from"* — the exposure | **No.** `items_passed` is the count that passed; the exposure is items *inspected*, which is separately mapped as `itemsInspected` |
| `subcontractor_observations` | **A4.8** Subcontractor Performance | *"each firm, the criteria it was rated against, the rating on each, who assessed it and the weights that were applied"* | **No.** A count of observations is none of those |
| `analogous_project_type` | **A1.10** CPI Shrinkage Forecast; **A3.1** Reference Class Forecasting; **A3.7** Analogous Estimating Ratio | a governed reference **population** with the cost performance each achieved; a reference **class** with entry criteria and each project's overrun; an **identified** analogous project with its cost and adaptation factors | **No.** A type string identifies no project and no population |
| `actual_equipment_days`, `planned_equipment_days`, `environmental_observations`, `on_schedule`, `rfi_answered`, `safety_observations` | — | no in-service abstention reason mentions the concept | **No** |

**Each of the ten is D on the missing parts, not a defect**, in the sense section 11 sets out: the
field is real and dropped, but consuming it would not satisfy any module in service, because every
module that touches its subject awaits a structure rather than a scalar.

---

## 16. The eleven classifications, in one table

| # | defect | classification |
|---|---|---|
| 1 | PV understated ~24 % | **G** — candidate cause 2 ruled out by execution; cause 1 unfalsifiable without the document |
| 2 | CPI 1.220 and SPI 1.270 | **G** for CPI. Item 1 accounts for SPI **completely** and for CPI **not at all** |
| 3 | document-risk `0.00` Green | **F** — `assets/js/detail.js:1528-1531`; `signals.js:535-536` excluded |
| 4 | CPI/SPI labelled "extracted" | **F** — `signals.js:1746`, unconditional mark |
| 5 | A1 Amber over two Green voters | **G** — the server cannot write it; three explanations remain |
| 6 | Amber attributed to a Green TCPI | **F** — `detail.js:1543-1553`, two mechanisms |
| 7 | recommendation against its drivers | **F** mechanism; **G** on the instance |
| 8 | blank period, locked longitudinal view | **C** — both halves reproduced |
| 9 | 75 + 25 against 100 | **F** — both correct, reconciled, unreconciled on screen |
| 10 | twelve categories against eleven | **F** — Run 41A half refuted, half confirmed |
| 11 | "Nothing outstanding" | **F** — session cache with no fallback |

Seven **F**, one **C**, three **G**. No **A**, **B**, **D** or **E** among the eleven.
**No defect proved to involve a retired module.**

---

## 17. Every question classified G, with the access that would answer it

| # | question | access that would answer it | why it was not taken |
|---|---|---|---|
| 1 | Is PRJ-001's PV on a different basis, mis-extracted, or internally inconsistent in its own document? | the extracted field values of PRJ-001's Time-phased Schedule / Baseline for the displayed period, or the document itself | production Postgres (14.1) and the PRJ-001 document set (14.2) |
| 2 | Why is CPI 1.22 against an authored 0.94–1.01? | PRJ-001's stored observations for `ev` and `ac` in the displayed period, showing which document supplied each; and the corpus's authored pair | production Postgres (14.1), PRJ-001 document set (14.2) |
| 5 | What supplied A1's Amber? | PRJ-001's stored `category_statuses["A1"]`, its `module_results` for `A1.7` and `A1.8`, and the row's `simulation_version` | production Postgres (14.1) |
| 7 | Did the model read the drivers it printed? | the stored brief request and response for that render | not a code fact; not stored in the repository |
| §11.3 | Is A3.2's contingency an extraction failure or a genuine absence? | PRJ-001's `documents` rows for the Owner Design Contingency Status artefacts — assigned `doc_type` and extracted keys | production Postgres (14.1) |
| §11.4 | Why does A4.2 abstain on PRJ-001 when it computes from those fields? | PRJ-001's stored `signal_inputs` RFI fields and its `A4.2` row | production Postgres (14.1) |

---

## 18. Incidental findings, unacted

1. **`bac` leaves the contract at every period after the one the contract was uploaded into.**
   `_period_documents` (`documents.py:373`) scopes observations to one period, so a `PERMANENT`
   contract fact is invisible to later periods and `bac` falls through the writer tiers to whatever
   document in that period states a contract sum. Reproduced (§3.2). Not evidenced on the section 9
   render, where `bac` came from the contract.
2. **The field registry has no concept of basis.** `FIELD_KINDS` and `WRITER_TIERS`
   (`field_registry.py`) carry kind and writer precedence only. No code path compares a value's
   basis, so a fee-basis figure and a cost-baseline figure are interchangeable in every slot.
3. **The platform emits a status outside its own capitalisation convention.** `A1.2 CUSUM Anomaly
   Monitor` stores `'green'` where every other module stores `'Green'`. `fusion.normalise_status`
   absorbs it, but `detail.js`'s `order` map does not, and treats it as more adverse than Green
   (§8.2).
4. **`BRIEF_CAT_LABEL` (`detail.js:1636-1644`) carries the retired "Cat N" scheme** — `"Cat 1"`
   through `"Cat 10"` plus `"PH"` — as user-facing category labels, against
   `NAMING_AUTHORITY.md:96`.
5. **`A4.1 Document Risk Score` is in service, registered and computed by nothing.** It is the sole
   member of `registry.unported_modules()` and publishes no row on the production path, so no
   analytical result ever contradicts a document-risk value invented at the render.
6. **`gethistory` returned `ok=False` on a project with four computed periods** in the fixture, not
   merely an empty list. The longitudinal view treats the two identically.

---

## 19. What the next session needs, stated as a decision for the owner

Stated as decisions, not recommendations, and not ranked.

1. **Six questions are G and every one of them needs the same thing: read access to PRJ-001's
   stored rows.** Stop condition 14.1 forbids production Postgres. The owner decides whether a
   read-only export of PRJ-001's `computed_results`, `documents` and observation rows is produced
   for diagnosis, or whether these six stay G.
2. **Defect 1 cannot be closed from stored rows alone.** Distinguishing a fee-basis PV from a
   mis-extraction needs the Time-phased Schedule / Baseline document's own text beside its extracted
   values. Stop condition 14.2 forbids modifying the PRJ-001 document set; reading it is a separate
   permission the owner has not given.
3. **Defect 5 has three surviving explanations and one of them is that section 9's premise is
   wrong.** The owner decides whether the render's claim that both computing modules read Green is
   to be treated as established evidence or as an observation to be re-checked against the stored
   row.
4. **The ten unconsumed extraction fields satisfy no module in service.** Consuming them would
   change what is extracted-and-kept without changing what any module can compute. Whether they stay
   declared-and-dropped, or are withdrawn from `extraction_fields.py`, is a decision about what the
   instrument claims to extract.
