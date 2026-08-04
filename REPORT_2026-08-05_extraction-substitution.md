# 2026-08-05 — Extraction stops substituting a nearby value for an absent field

**The model was actually called, against real Project A design documents, with a live key
supplied by Lin.** Every claim below is a real API response, not a stub recording. **Server 39
suites, 2161/2161 (was 38/2042). `tests_render.html` 86/86. `tests.html` 51/51.** Seven faults
injected against the new prompt-contract suite, all detected, all reverted byte-identical,
baseline re-measured after each. No migration. `simulation/` untouched.

---

## 1. THE PROBE OUTPUT, BEFORE AND AFTER — LEAD RESULT

Both real documents, both runs, same model (`claude-opus-4-6`), same guards. The only thing that
changed between the two blocks is `build_prompt`.

### 1.1 `2026_04_09 100% INFO - Contract Value Summary P01.docx` — classified `contract_value`, 0.97

| Field | Document actually says | BEFORE (old prompt) | AFTER (fixed prompt) |
|---|---|---|---|
| `original_contract_sum` | Original professional services agreement: $5,874,620.00 | 5874620.0 — correct | 5874620.0 — correct |
| `project_start_date` | **Not present.** The only date range in the document is `Period \| 1 March 2026 through 31 March 2026`, labelled as the reporting period, beside `Issue date \| 9 April 2026` and `Data date \| 31 March 2026`. | **`2026-03-01`** — the reporting period's start, mislabelled as a project baseline | **`None`** — correct |
| `project_end_date` | Not present, same reasoning | **`2026-03-31`** — the reporting period's end | **`None`** — correct |

The two pending authorizations ($86,740 and $34,980, headed "Pending authorizations - excluded
from current agreement") were correctly excluded from `original_contract_sum` in **both** runs —
not a regression risk this change touched, confirmed by both probe outputs printing 5874620.0,
not 5,996,340.

### 1.2 `2026_04_06 100% INFO - Design Activity Status U03.docx` — classified `schedule_update`, 0.95

The activity table has **nine rows** (`D100` through `D700`).

| Field | Document actually says | BEFORE | AFTER |
|---|---|---|---|
| `data_date` | Data date: 31 March 2026 | `2026-03-31` — correct | `2026-03-31` — correct |
| `activities_planned` | 9 rows in the activity table | **`None` — MISSED** | **`9`** — correct |
| `milestones_json` | The activity table itself | **`None` — MISSED** | **A 9-element JSON array**, one object per row, keys `Activity`, `Description`, `Baseline start`, `Baseline finish`, `Complete`, `Current finish / actual` |
| `planned_percent_complete`, `planned_value_to_date`, `total_float`, `consumed_float`, `activities_constrained`, `lookahead_weeks` | Genuinely absent — the document states none of them | `None` (all six) — correct | `None` (all six) — correct, **unchanged** |

Six of nine fields were already correctly null before this change and stay null after it. The fix
did not make the model more talkative in general — only on the two fields it had wrongly withheld
and the two it had wrongly invented.

### 1.3 The acceptance test, run against the actual production code

`server/tools/real_extraction_regression.py`, calling `AnthropicExtractor` through the same
`extract_with_confidence` path `a_projectupload` uses — **16/16 checks passed**, all six pass
conditions:

```
PASS  1. project_start_date is null  [None]
PASS  1. project_end_date is null  [None]
PASS  2. original_contract_sum is 5,874,620  [5874620.0]
PASS  3. the pending authorizations are NOT folded into the sum  [got 5874620.0, would be 5996340.0 if leaked]
PASS  4. activities_planned is 9  [9]
PASS  5. milestones_json carries all nine activity rows  [type=list len=9]
PASS  6. planned_percent_complete is still null (genuinely absent from the document)  [None]
PASS  6. planned_value_to_date is still null (genuinely absent from the document)  [None]
PASS  6. total_float is still null (genuinely absent from the document)  [None]
PASS  6. consumed_float is still null (genuinely absent from the document)  [None]
PASS  6. activities_constrained is still null (genuinely absent from the document)  [None]
PASS  6. lookahead_weeks is still null (genuinely absent from the document)  [None]
PASS  6. data_date is still extracted (genuinely present) -- no overcorrection  ['2026-03-31']
```

**The same script, run against the reverted (pre-fix) prompt, fails exactly the two conditions
the defect predicts** — `project_start_date`/`project_end_date` non-null (11/15) — confirming the
check is not vacuous before it is trusted as evidence.

---

## 2. Neither input was available in this environment; both were supplied mid-task

This session started the same way the 2026-08-04 session ended: no `ANTHROPIC_API_KEY`, no real
documents. The brief's acceptance test could not run without both. Rather than proceed against the
stub — which **cannot exhibit this defect**, since `StubExtractor` returns whatever a hand-written
recording says regardless of prompt wording — the blocker was reported and Lin supplied a key and
the path to the two real files
(`Desktop\Project Samples\2028-11-01_ProjectA_Design_Revised_Verified_Corpus\ProjectA_Design\Period_01`).
The key was set as a local environment variable for this session only, never echoed to output or
committed anywhere; it does not appear in any file in this repository.

---

## 3. The fix, in `server/app/extraction_client.py`'s `build_prompt`

### 3.1 Why the existing "never carry a value over" instruction was not enough

The old prompt already said *"Never guess, infer, or carry a value over from a different field."*
That forbids moving a value **between two named fields**. It says nothing about a value sitting
under **no matching label at all** — a reporting period is not a "different field" in the prompt's
own vocabulary, because nothing asked for a reporting period. The model was not disobeying the old
instruction; the instruction simply did not cover this shape of failure.

**No guard could have caught it either.** Both `validate_doc_risk_score` and
`validate_numeric_fields` guard the *value* — is it a number, is it in range. A substituted date is
a perfectly good date. The only place this can be caught is the prompt itself.

### 3.2 The wording added

```
A field is returned ONLY when the document itself states that field, under a label or
heading whose meaning matches the field's name. A different value sitting nearby, under
a different label, is never a substitute, even if it is a plausible value of the right
type and in a sensible range: a reporting period is not a project start or end date, an
issue date or a data date is not a baseline date, and a schedule-progress percentage is
not a cost-basis percentage. If you cannot point to the specific label in the document
that names this field, return null for it. Counting entries in the document's own table
is reading a stated fact, not inferring one, when the field name plainly refers to that
table (for example, a count of rows in a schedule or activity table).
```

**Applied across the whole field vocabulary, not only dates**, per the brief. It is stated as a
general label-matching rule and only the three concrete examples happen to be date-shaped, because
that is the shape the real document exhibited. The fault-injection campaign (section 5) asserts
the rule survives independent of any one example, and the last sentence (table-count reasoning) is
what stops "never guess or infer" from over-suppressing a legitimate count — see 3.4.

### 3.3 Whether any field legitimately needs a derived value

**Checked, not assumed: no.** Every name in `extraction_fields.ALL_FIELDS` (87 fields, the full
historical vocabulary) is a total, a date, a rating, a percentage or a count that a construction
report states directly. This matches the platform's own standing description
(`NAMING_AUTHORITY.md` section 3), which already commits to **"reads the reported figures"**, not
"extracts" or "computes" them, and flags that wording as deliberately not strengthened until
extraction had run against a real document. `CPI`/`SPI` are the one place a value is genuinely
derived, and those are computed server-side — "Do not compute indices" already existed in the
prompt before this change and is unmodified.

### 3.4 The second, opposite failure this fix also had to not make worse

Defect 2 (missed fields) is under-application of "read what is there", not over-application. A
prompt tightened purely toward "never invent, never infer" risks making the model MORE
conservative about legitimate content, not less — and `activities_planned` is exactly a case where
a naive reading of the old "never infer" instruction could argue counting table rows is "inferring
a count" rather than reading one. The added sentence about table-counting draws that line
explicitly, so tightening the anti-substitution rule does not accidentally suppress the count.

**`milestones_json` needed a second, separate addition — not the anti-substitution rule.** It is
not a scalar, and nothing in the original prompt described how to shape a whole table into one
JSON field, or told the model that a document's own activity/schedule table qualifies as a
milestones source at all (the document never uses the word "milestone"). This is a distinct
addition, added only when `milestones_json` is in the requested field list:

```
milestones_json, if requested and the document contains a schedule, activity or
milestone table, is a JSON array with one object per row of that table, using the
table's own column headings as keys and its values as printed (do not reformat or
reinterpret a value inside this table — dates inside it are NOT required to be
YYYY-MM-DD, unlike every other date field below); return an empty array only if the
document has no such table.
```

The "values as printed" and "NOT required to be YYYY-MM-DD" clauses are deliberate: see section 4.

---

## 4. The three date formats in the milestone table — do they parse?

The activity table's "Current finish / actual" column carries three distinct shapes across nine
rows, plus a fourth variant with a scheduling-tool marker suffix:

| Example | Shape |
|---|---|
| `29-May` | day-month, no year |
| `14 August 2026` | day month year, spelled out |
| `24-Mar-26 A` | day-month-year with a trailing actual-date marker |
| `02-Apr`, `17-Jul`, `16-Oct`, `06-Nov` | more of the no-year shape |

**None of them parse.** The pipeline's ONLY date-parsing function, `date.fromisoformat`
(`extraction_merge.py:442`, `documents.py:386`), was tested against all three directly:

```
'12-Jan-26'      -> ValueError: Invalid isoformat string: '12-Jan-26'
'29-May'         -> ValueError: Invalid isoformat string: '29-May'
'14 August 2026' -> ValueError: Invalid isoformat string: '14 August 2026'
'24-Mar-26 A'    -> ValueError: Invalid isoformat string: '24-Mar-26 A'
```

`date.fromisoformat` accepts strict `YYYY-MM-DD` only. This is why `milestones_json`'s prompt hint
explicitly tells the model **not** to reformat these values: normalising `"24-Mar-26 A"` to
`YYYY-MM-DD` would either silently drop the actual-date marker (a real signal — it distinguishes a
completed activity's actual finish from a still-forecast one) or fail outright, and the model has
no way to know which convention this particular scheduling tool export used without being told to
leave it alone. **If the merge gap in section 5 is ever closed, whoever writes that code needs
real date parsing for this field — not `date.fromisoformat` — and needs to decide what to do with
the trailing `A` marker.** Recorded here so that decision does not have to be rediscovered.

---

## 5. The `milestones_json` merge gap — confirmed still open

**Checked against the code directly, not assumed from the reconciliation report.** Exhaustive
search of every `.py` file in `server/app` for `milestones_json`:

```
extraction_fields.py:161   "milestones_json",        <- requested for schedule_update
extraction_fields.py:169   ..., "milestones_json",    <- requested for monthly_report
field_registry.py:202      "milestoneHistory": {"shape": SERIES, "servable": False}
```

**Zero writers.** `extraction_merge.py`'s per-doc-type emission tables (the ones that map
`("planned_percent_complete", "plannedPctComplete")` etc. into `signalInputs`) have no entry for
`milestones_json` in either the `schedule_update` or `monthly_report` block. The extraction model
is asked for it, and now — after this fix — genuinely returns it. It is stored on the `Document`
row's own `extraction` JSON (visible in the probe output above). It never reaches `signalInputs`,
never reaches a computed result, and A2.7 Milestone Trend still abstains for the same reason the
reconciliation report gave: `milestoneHistory` is declared `servable: False`.

**This is not a one-line change, and it was not closed in this task.** Closing it would require,
at minimum:

- A merge branch that converts the extracted list-of-row-objects into whatever shape
  `milestoneHistory` (a `SERIES`, per `field_registry.py`) actually needs — the extraction is a
  snapshot of one document's table; a SERIES needs values indexed across periods, which means
  deciding how one document's activity table folds into a trend when a later period's document
  reports on the same activities with updated percentages.
  - Section 4's date-parsing gap is a prerequisite: a series indexed on dates that don't parse
    cannot be built at all.
  - Selection/precedence rules across documents and periods (which of two schedule updates in the
    same period wins, per `field_registry`'s tier system) would need deciding for a field type
    that currently has none.
  - `field_registry.NEEDS["milestoneHistory"]["servable"]` would need to flip to `True`, and
    whatever A2.7's module does with an abstained field would need to be re-verified against a
    populated one — inside `server/app/simulation/`, which this task was told not to touch.

**Reported, not started**, per the brief's explicit instruction.

---

## 6. Verification

### 6.1 The deterministic prompt-contract suite

`server/tools/test_extraction_prompt.py` — needs neither a key nor a document, always runnable,
**119/119**. Asserts the prompt's own wording survives an edit: the label-matching sentence and
its two named examples, the `milestones_json` hint present/absent exactly when the field is/isn't
requested (checked against all 27 document types, not a sample), the table-dates-not-ISO
carve-out, and every pre-existing invariant (`document_risk_score`'s 0..1 band, "Do not compute
indices", the ISO date instruction, the JSON-only output instruction, the field list itself still
quoted verbatim).

**This suite cannot prove the fix works.** It can only prove the words are still there after a
future edit. The proof that the words work is section 1's real model output, and the live
re-verification script below.

### 6.2 `server/tools/real_extraction_regression.py` — NOT swept into the standard suite, and why

Named without a `test_` prefix on purpose. If it were `test_*`, every future session's "run the
server suite" step would either fail (no key, no committed real documents) or need
skip-if-missing logic some future runner script forgets to carry forward — silently downgrading
"the suite passed" from a fact into an approximation. It takes the two real file paths as
arguments, refuses to run without a key (same `require_real=True` contract as
`real_extraction_probe.py`), and writes nothing to any database. It is what section 1.3's 16/16
came from, and what a future session with a key should re-run before trusting this fix still
holds.

**The two real documents are not committed to this repository.** They are the owner's own project
files, outside `LinPRojectRadar`. Committing them would put real project financial and schedule
figures into git history for a reason no part of this task asked for.

### 6.3 Fault injection

All against the new deterministic suite, since that is the only suite whose behaviour is
determined purely by the prompt text (the live regression script's outcome depends on the real
model and cannot be fault-injected against source edits in a repeatable way). Every fault applied,
confirmed to change the file, run, detected, reverted, **verified byte-identical**, baseline
re-measured **after each one individually**.

| Fault | Detected by | Baseline |
|---|---|---|
| G1a label-matching phrase removed | prompt suite 119 → 92 | restored |
| G1b named-example sentence removed | prompt suite 119 → 118 | restored |
| G1c "point to the specific label" clause removed | prompt suite 119 → 92 | restored |
| G2 `milestones_json` hint made unconditional (leaks into every doc type) | prompt suite 119 → 94 | restored |
| G3 `milestones_json` hint's shape-marker text removed | prompt suite 119 → 117 | restored |
| G4 table-dates-not-ISO carve-out inverted | prompt suite 119 → 118 | restored |
| G5 `document_risk_score` band clause deleted (pre-existing invariant) | prompt suite 119 → 118 | restored |

A trap repeated from prior sessions: the first draft of G1a's fault needle was a multi-line string
copied from the source, and it matched zero times — the sentence is built from adjacent
single-line string literals concatenated at runtime, not one contiguous line in the file. Every
fault needle here is anchored within a single source line, per the standing CRLF-file guidance.

### 6.4 Full suite and both harnesses

**Server: 39 suites, 2161/2161** (was 38 suites, 2042/2042 before this session's two new files).
**`tests_render.html`: 86/86. `tests.html`: 51/51.** Both driven in a real browser, a PM session
token supplied via `sessionStorage`, against a freshly computed project — the same live-state
proof method the 2026-08-04 report established (the count moves with server state, which is the
evidence the checks reach the server rather than a primed fixture).

A dev server left running from the previous session on port 8012 was still serving pre-fix code
when first checked (`/exec` for `extractsignals` still answered the pre-2026-08-04 wiring). It was
stopped and a fresh instance started on port 8013, confirmed to be running the current code (the
post-2026-08-04 auth-before-shape-check ordering) before any harness number was recorded. **A
second occurrence of the port-8010 trap from the previous report — verify what is running before
trusting a run against it, every time, not just once per task.**

---

## 7. Open, carried forward

- **The `milestones_json` merge gap remains open** (section 5). Real work, not a one-liner, and it
  touches `field_registry` decisions and (eventually) `simulation/`, which is out of scope here.
- **Real-world date parsing for milestone table entries does not exist anywhere in this pipeline**
  (section 4). Needed before the merge gap above can close.
- **No other document type in the 27-type vocabulary has been run against the real model.** This
  fix generalises the anti-substitution rule across the whole vocabulary by design, but only two
  document types (`contract_value`, `schedule_update`) have been observed against a real document.
  The `milestones_json` hint is also requested by `monthly_report`, untested against a real one.
- **The key used this session was supplied ad hoc and is not persisted anywhere.** A future
  session verifying this fix again needs the same two real files and a key, supplied the same way.
