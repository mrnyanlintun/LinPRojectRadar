# Pipeline audit: extraction through reporting

**Read-only session. No code was modified.**

Stages 1 to 4 and the period-transition scope are covered with proven evidence. **Stages 5 to 8
are NOT covered** and are listed as not reached at the end, with the partial results I do hold.
Every claim below was measured by running the code, not inferred. Where I could not prove a
behaviour I have written UNKNOWN.

**A prerequisite was missing: there is no evidence policy audit report in this repository.** I
searched the tree and the git history for it and found nothing. If it exists outside the
repository it did not reach this session, and anything it would have established is absent from
what follows.

**One correction to the framing.** The brief describes the merge layer as having "no revision
concept at all". That was true when the brief was written; it was fixed in commit `6e614c2`
(migration 0013) and the content-hash tiebreak now applies only to documents nobody has declared
as superseding. The defect is narrowed, not gone: see D5.

---

## Part 1. Defects that reach a user and are reachable today

### D1. Eleven module inputs can never be produced. Nine of them feed a project colour.

| | |
|---|---|
| **Stage** | 4, computation |
| **Where** | `server/app/simulation/` reads them; `server/app/extraction_merge.py` `SIGNAL_INPUT_KEYS` is the complete set of what can be produced |
| **Reachable** | **Today, on every server-computed project, always** |
| **Reaches a user** | **Yes.** Nine of the eleven are in Groups A and B, which vote in project status |

Measured by set difference between what the simulation reads and what the merge can emit:

```
merge can produce : 82 keys
simulation reads  : 77 keys
UNOBTAINABLE      : 11
  cusum  decision  doc  events  evm  fairnessSensitive  mc
  milestoneHistory  signals  simulationSignals  spiHistory
```

These are the legacy browser blob (`si.signals.evm` and friends) and the two history series. The
merge layer has no branch that writes any of them.

Modules whose own body reads one, from a scan of `VALIDATED`:

| Module | Method class | Unobtainable inputs | Group | Votes in status |
|---|---|---|---|---|
| A1.2 | CUSUM | `spiHistory` | A | **yes** |
| A2.7 | Milestone_Trend | `milestoneHistory` | A | **yes** |
| B2.2 | Rough_Sets_Classification | `cusum`, `doc`, `mc` | B | **yes** |
| B2.3 | Neutrosophic_Logic | `cusum`, `doc`, `mc` | B | **yes** |
| B2.5 | Z_Numbers | `cusum`, `doc`, `mc` | B | **yes** |
| B2.6 | PLTS | `cusum`, `doc`, `mc` | B | **yes** |
| B2.7 | Plithogenic_Sets | `cusum`, `doc`, `mc` | B | **yes** |
| B2.8 | Belief_Rule_Base | `cusum`, `doc`, `mc` | B | **yes** |
| B2.9 | Quantum_Probability | `cusum`, `doc` | B | **yes** |
| C1.4 | Audit_Trail_Completeness | `events` | C | no |
| C1.7 | Reporting_Frequency_Index | `events` | C | no |

Eleven of ninety-five project-level modules. A1.2 is reached through a wrapper so a source scan
alone finds ten; I confirmed the eleventh by executing it. The remaining five registered
computations are Group D in `portfolio.py`.

**None of these abstain. They emit a status.** Executed with a healthy `signalInputs` and the
blob keys absent, which is the state of every server-computed project:

```
rough sets   -> status='Amber'  evidence='Indeterminate (Green 0, Amber 0, Red 0 of 1 signals)'
audit trail  -> status='Red'    evidence='0% audit trail completeness, 0 events recorded'
CUSUM        -> status='red'    periods=12  breached=True   (series SYNTHESISED from the seed)
CUSUM seed 999 -> status='red'  periods=12  breached=True
```

Three distinct failure shapes, all silent:

- **Rough Sets counts zero evidence and still returns Amber.** `total = len(classes) or 1` turns
  an empty evidence set into a denominator of one, so "Green 0, Amber 0, Red 0 of 1 signals"
  resolves to Indeterminate and bands as Amber. A colour derived from nothing.
- **Audit Trail Completeness returns Red permanently**, on every project, because `events` can
  never be populated. It reports "0 events recorded" about a platform that records events.
- **CUSUM invents its history.** `run_cusum` does `series = si.get("spiHistory")` and, when that is
  absent, `series = derive_series(float(si["spi"]), seed)`. It then reports twelve periods and a
  breach. This is the finding that prompted the audit, and it is confirmed: the periods are
  fabricated from a seed and the breach is a property of the fabrication.

**Test coverage: none.** No test in `server/tools/` references `spiHistory`, `derive_series`, or
any of the eleven keys. `VALIDATION.md` records each module as matching the JavaScript exactly,
which is true and is the problem: the JavaScript received the blob from the browser, so validating
against it confirms the port, not the input contract.

### D2. Malformed numeric text becomes 0.0, and a CPI of 0.0 reaches status

| | |
|---|---|
| **Stage** | 1, extraction, and 3, merge |
| **Where** | `server/app/extraction_merge.py` `_num_or_null` |
| **Reachable** | **Today.** Any document where the model returns a non-numeric string for a numeric field |
| **Reaches a user** | **Yes**, as a project colour |

`_num_or_null` reproduces the legacy `Number(String(v).replace(/[^0-9.\-]/g,''))`. Measured:

```
'N/A' -> 0.0    'TBD' -> 0.0    'unknown' -> 0.0    'abc' -> 0.0
'  '  -> 0.0    True  -> 0.0    False -> 0.0
'-'   -> None   ''    -> None   '1.2.3' -> None
'85%' -> 85.0   '$1,200,000' -> 1200000.0    '1e21' -> 121.0
```

Through a real merge branch:

```
earned_value='TBD'  -> ev=0.0, ac=5000000, cpi=0.0
actual_cost='N/A'   -> ev=5000000, ac=0.0,  cpi=None
actual_cost='1.2.3' -> ev=5000000, ac=None, cpi=None
```

**A model returning "TBD" for earned value yields a CPI of 0.0**, the worst possible cost
performance, with no refusal anywhere. The `actual_cost` cases degrade to `cpi=None` only because
the division guards on `ac != 0`; that is luck of which side of the ratio the field sits on, not
a designed protection.

The quirk is deliberate and documented as a legacy reproduction. What is not addressed is that it
converts a malformed extraction into a confident worst-case number. `'1e21' -> 121.0` is
acknowledged in the docstring as pathological and left in.

**Test coverage: none.** No test in `server/tools/` exercises `_num_or_null` or any malformed
numeric string.

### D3. A malformed or absent document date silently becomes the wall clock

| | |
|---|---|
| **Stage** | 1 and 6 |
| **Where** | `server/app/documents.py` `_derive_cutoff`; `extraction_merge.py` `_is_blank_date` |
| **Reachable** | **Today** |
| **Reaches a user** | Indirectly, through C1.2 Data Timeliness |

`_is_blank_date` rejects only empty and None, so `"not a date"` is stored verbatim as `docDate`.
`_derive_cutoff` then tries `date.fromisoformat`, catches the failure, and falls back:

```
parseable date   -> cutoff=2026-06-30
MALFORMED date   -> cutoff=2026-08-02   == TODAY (wall clock)
no date          -> cutoff=2026-08-02   == TODAY (wall clock)
```

`period_cutoff` exists specifically to keep the wall clock out of the analytical layer, and its
docstring says so. When no document carries a parseable date, the cutoff **is** the wall clock, so
the same documents computed on two different days produce two different C1.2 results. A recompute
reuses the stored cutoff, so the drift is pinned after the first compute, but the first compute is
the one a participant sees.

**Test coverage: UNKNOWN.** I did not search exhaustively for a cutoff test.

### D4. A declared document type is silently discarded for any already-seen bytes

| | |
|---|---|
| **Stage** | 2, storage and caching |
| **Where** | `server/app/documents.py` `a_projectupload`, the `existing` short-circuit |
| **Reachable** | **Today**, and it is the designed research case: the same stimulus document given to several participants |
| **Reaches a user** | Yes, as the document's type and therefore its extracted fields |

Measured end to end. Project A uploads bytes X declaring nothing; the classifier says `rfi`.
Project B uploads **identical bytes** declaring `docType: "monthly_report"`:

```
A declares nothing  -> rfi | cached: False
B declares monthly  -> rfi | cached: True
B's DECLARED type was honoured: False
```

Because the hash is already in `documents`, no extraction job is created and `d["doc_type"]` from
this upload is never consulted. The first uploader's classification is global and permanent, for
every project that ever uploads those bytes.

The returned `files[0].doc_type` does show `rfi`, so the override is visible to a caller who reads
it, but nothing flags that a declaration was overridden. **The API accepts a parameter it does not
honour.**

Whether same bytes should mean same type is defensible and is the stated design. The defect is
narrower: the declaration is accepted silently and discarded silently, and a misclassification on
first upload is uncorrectable through the upload path.

**Test coverage: none found** for the declared-type-versus-cached-type conflict.
`test_documents_b7b` Guarantee 1 covers the cache itself and passes.

### D5. An undeclared revision still merges by content hash

| | |
|---|---|
| **Stage** | 3, merge and assembly |
| **Where** | `extraction_merge.py` `_ordered_docs`; `documents.py` `_period_documents` |
| **Reachable** | **Today**, whenever a revision is uploaded without the `supersedes` field |
| **Reaches a user** | **Yes** |

Migration 0013 added explicit supersession and it works. It only helps when the uploader declares
it, and **there is no frontend control**, so today the field is reachable only by an API caller.
For every upload made through the interface the pre-0013 behaviour is unchanged:

```
without supersession, the sha256 decides which version wins, not recency
without supersession, an additive field DOUBLE COUNTS a revision (10 then 12 -> 22)
```

First-wins fields take the lower hash and last-wins fields the higher, in opposite directions, so
one revision can produce a `signalInputs` mixing both versions.

**Test coverage: yes, and it is honest.** `test_document_versioning.py` sections 1 and 2 assert
this defect still exists for the undeclared case and assert the precondition that makes the
supersede tests non-vacuous. Proven able to fail six ways in the session that wrote it.

---

## Part 2. Period handling

### P1. Recomputing an earlier period rewrites it with later information. PROVEN.

**This is the one the brief said matters most, and it is real.**

| | |
|---|---|
| **Stage** | 6 and 9 |
| **Where** | `server/app/documents.py` `_compute_and_store`, the `vectors` block |
| **Reachable** | **Today**, on any operational project, via `adminrecompute` |
| **Reaches a user** | **Yes**, as the stored `portfolio_snapshot` on a period a participant may already have decided against |

The portfolio vector set is built from every other project's **most recent live result**, selected
by `max(period)`, with no alignment to the period being computed:

```python
for r in others:
    prev = by_project.get(r.project_id)
    if prev is None or (r.period or 0) > (prev.period or 0):
        by_project[r.project_id] = r
```

Demonstrated. Project A period 1 computed while project B was also at period 1; B then advanced to
period 2 with much worse figures; A's **period 1** was recomputed with A's own period-1 documents
unchanged:

```
A period 1 snapshot, computed when B was ALSO at period 1:
    {"insufficient_data": true, "message": "Portfolio too small for anomaly detection ..."}

adminrecompute on A period 1 -> ok | period actually used: 1

A period 1 snapshot AFTER recompute (B has since moved to period 2):
    {"portfolio_size": 2, "results": {"cat8_1_isolation_forest": {"status_color": "Yellow",
     "anomaly_score": 1.0, ...

  SNAPSHOT CHANGED: True
```

A stored period-1 result went from "insufficient data" to a Yellow anomaly finding, driven
entirely by another project's later period. The old row is superseded and retained, so the record
is not destroyed, but **the live period-1 result now contains information from period 2.**

The same mechanism affects first computes: two projects computed for period 1 at different
wall-clock moments see different portfolios, so period-1 results are not mutually comparable.

**Test coverage: none, and the nearest test cannot detect it.** `test_workspace_t3t5.py`
Guarantee 9 is the only test touching `portfolio_snapshot`. It asserts the snapshot is non-null,
that below threshold it says `insufficient_data`, and that above threshold it carries five
sub-results. **Both its projects are period 1 and it never varies period**, so it would pass
unchanged with this defect fully present.

### P2. Period assignment is caller-declared and unvalidated for operational projects

| | |
|---|---|
| **Where** | `server/app/documents.py` `_resolve_period` |
| **Reachable** | Today, operational projects only |

For a project with a research assignment the period is **server-derived** from the decision chain
and the payload is ignored entirely, which is correct and closes the obvious abuse.

For an operational project there is no assignment, so the payload is used, defaulting to 1 and
validated only as `>= 1`. There is **no upper bound and no relation to the document's own date**.
A document dated June can be filed to period 999 and nothing objects. Nothing cross-checks
`document_date` against the declared period at any point.

### P3. Can a computation for period N read a value from period N plus or minus 1?

**Yes, by one path: the portfolio snapshot.** P1 above. Other projects' results at any period
enter period N's computation.

**No, for the project's own documents.** `_period_documents` filters `DocumentUpload.period ==
period` exactly, and the project's own vector is excluded from `others` before its fresh vector is
appended. I found no path by which a project's own period N-1 documents or results reach its
period N computation.

### P4. Does a late document for an earlier period change a result already shown?

**Not automatically.** `projectcompute` refuses when a live result exists and directs the caller to
`adminrecompute`. So an upload alone never rewrites a stored result.

**Yes on explicit recompute**, which requires ResearchAdmin and a stated reason, supersedes rather
than edits, and retains the old row. That is the append-only discipline working as designed. The
qualification is P1: the recompute also pulls in later portfolio information.

### P5. Does a stored result record its period, and can it display under the wrong one?

**It records it.** `ComputedResult.period` is NOT NULL, and `_result_view` returns `"period":
row.period`.

**Whether any display surface can show it under the wrong period is UNKNOWN.** That is stage 7 and
I did not reach it.

### P6. Trend and history across periods

**There is no cross-period trend assembly, because the inputs for it cannot be produced.**
`spiHistory` and `milestoneHistory` are two of the eleven unobtainable keys in D1. A1.2 fabricates
its series from a seed; A2.7 Milestone_Trend reads `milestoneHistory` and I did not execute it, so
its absence behaviour is **UNKNOWN**.

The question of what happens when a period is missing from the middle of a sequence therefore does
not arise for the analytical layer as built: nothing assembles a sequence. Whether any **display**
surface builds a trend from stored results across periods is **UNKNOWN**, stage 7.

`compute_portfolio` takes a `history` argument and guards `len(history) >= 2`; what supplies it on
the server path is **UNKNOWN** and worth establishing next.

### P7. A silent parameter override on research projects

`adminrecompute` calls `_resolve_period`, which for a research project returns the participant's
**current** period and ignores the payload. An admin asking to recompute period 1 of a project now
at period 3 silently recomputes **period 3**.

This protects earlier research periods from recompute, which is the right outcome and materially
limits P1's blast radius for research data. But the parameter is accepted and discarded without
comment. The response reports the period actually used, so it is visible but not flagged.

---

## Part 3. Stage findings not already covered

### Stage 1, extraction: what is handled well

Stated because an audit that lists only defects misrepresents the code.

- **Unrequested keys are dropped.** `AnthropicExtractor.extract` filters the model's response to
  the declared field list, so a model volunteering extra keys cannot widen the stored extraction.
- **Malformed JSON is loud.** `parse_json_response` raises rather than returning empty; the
  wrapped-in-prose case is recovered by outermost braces, and a non-object raises.
- **An unmapped document type stores an empty extraction** rather than asking the generic
  two-field default, which would have produced a `docRiskScore` for a type nothing interprets.
- **Per-document failure is isolated.** `extract_many` captures per job, so one unreadable document
  does not sink a batch, and the reason reaches the uploader through the "Extraction failed"
  dialog.
- **`document_risk_score` is refused outside 0 to 1** at four entry points, added in `ab32fd7`.

### Stage 2, caching

- The hash keys **one extraction per unique file for the lifetime of the platform**, globally
  across projects. Verified by `test_documents_b7b` Guarantee 1.
- Same bytes, different project or period: reuses the extraction, creates a new
  `DocumentUpload`. Working as designed.
- Different bytes carrying the same figures: two documents, both merge, additive fields
  double-count. This is D5.
- `uq_document_uploads_once_per_period` makes a re-upload of the same file to the same period a
  no-op rather than a second row.

### Stage 5, status derivation: partial

**Groups C and D are correctly excluded.** `server/app/simulation/compute.py`
`contributes_to_project_status` returns `group not in ("C", "D")`, and the project fusion votes
only on categories where that is true. Group D additionally never reaches a single-project path.
Verified by reading and consistent with `GROUP_ASSIGNMENT.md`.

**One dead flag.** `taxonomy.js` `getProjectFusion` reads `row.red_review`, and nothing on the
server ever writes that column, so `redReview` is permanently false. Established in a prior
session and unchanged. It fails safe.

The rest of stage 5 was not examined.

### Stage 6, snapshot: partial

Covered only where it intersects period handling, P1. The snapshot is **rebuilt on every compute
and recompute** from live rows, not copied forward, which is what makes P1 possible. Whether a
snapshot can change underneath a stored decision by any other route is **UNKNOWN**.

---

## Part 4. Checks that cannot fail

The brief asked for these specifically. I examined the tests touching the defects above rather
than sweeping the suite, so this list is not exhaustive.

1. **`test_workspace_t3t5.py` Guarantee 9, the portfolio snapshot checks.** Cannot detect P1: both
   its projects are period 1 and it never varies period. It would pass unchanged with the
   cross-period contamination fully present. Not vacuous for what it does assert, but blind to the
   defect in the code it covers.
2. **`VALIDATION.md`'s exact-match validation for the eleven modules in D1.** Every one is recorded
   as matching the JavaScript to 0.0e+00. That is true and cannot fail in the way that matters: the
   JavaScript was handed the browser blob, so the comparison validates the port while the input
   contract is broken underneath both. A perfect score against the wrong oracle.

**I did not run a systematic vacuity sweep of the suite**, and given five have been found by
accident so far, that sweep is worth its own session.

---

## Part 5. Where I stopped, and what is not covered

Stopped at a clean boundary after stages 1 to 4 and the period scope, as the brief directed.

**Not covered at all:**

- **Stage 7, reporting and display.** Whether what a user reads matches what was computed and
  stored, across the assistant, the portfolio views, and the exports. P5 depends on this.
- **Stage 8, audit trail and logging.** What is recorded, what is not, whether the record can
  reconstruct why a number was shown, and what mutates rather than appends.

**Partially covered:** stage 5 (the Group C and D exclusion only), stage 6 (only via P1).

**Specific UNKNOWNs raised above:** A2.7's absence behaviour; what supplies `compute_portfolio`'s
`history` on the server path; whether any display surface can show a result under the wrong
period; whether any display surface builds a cross-period trend; whether a `period_cutoff` test
exists.

---

## Summary of proven defects

| # | Stage | Reachable today | Reaches a user | Test covers it |
|---|---|---|---|---|
| D1 | 4 | yes, always | yes, project colour | no |
| D2 | 1, 3 | yes | yes, project colour | no |
| D3 | 1, 6 | yes | indirectly | UNKNOWN |
| D4 | 2 | yes | yes, document type | no |
| D5 | 3 | yes, undeclared revisions | yes | yes, honestly |
| P1 | 6, 9 | yes, operational | yes, stored snapshot | no, and the nearest test is blind to it |
| P2 | 9 | yes, operational | no, enables misfiling | UNKNOWN |
| P7 | 9 | yes, research | no, silent override | UNKNOWN |

**D1 and P1 are the two I would act on first.** D1 because nine modules that vote in a project's
colour are reading inputs that cannot exist, and three of them emit a confident status from
nothing rather than abstaining. P1 because it is the specific property the research record was
said to depend on being impossible, and it is not.
