# Document table reconciliation, run 1

Parts 1 to 4 complete in one session. Part 4 is implemented; Parts 2 and 3 are reconciliation and
design only, as instructed.

Server 1361 checks across 24 suites, `tests_render.html` 49/49, `tests.html` 51/51, green on
merged `main`. 15 faults injected for the Part 4 checks, every one detected, every one reverted
and rechecked byte-for-byte.

**Both prerequisite audits are stale in ways that matter, and I verified against the code rather
than against them.** The evidence-policy audit is not in this repository at all: it exists only on
the unpushed branch `t15-local-unpushed`, dated 2026-08-01, and its central finding (CUSUM
fabricating its history) has since been fixed. The pipeline audit records that no evidence-policy
report existed, which was true when it was written. Every claim below was re-checked against
`main` at `926adf6`.

**The table and the code agree on the vocabulary exactly.** All 28 document types in your table
are the 28 mapped types in `extraction_fields.py`, no additions, no omissions. The 15 UI-only
types the older audit found are gone from `DOC_TYPES`; `UI_ONLY_DOC_TYPES` survives as dead code
that nothing imports.

---

# Part A. The disagreements that produce a wrong number today

Grouped by kind of disagreement, not by document type.

## A1. Two fields sum where the table says replace

These are the only two non-replacing numeric operations in the entire merge. Everything else is
last-write-wins or first-non-null.

| Field | Written by | Operation | What the table requires |
|---|---|---|---|
| `rfiCount` | `rfi` branch | `add()`, arithmetic sum over the document set | "Event ledger. **A revision is not a new RFI.** Never combine individual-RFI counts with the RFI-log total" |
| `changeOrderCount` | `change_order` branch, only when `change_order_count` is absent | `add(1)` per document | "Event ledger **by CO number**. Draft, pending, approved, rejected and executed states remain separate" |

The set is de-duplicated by **sha256 only**. A corrected revision has different bytes, so it is a
different member of the set and it adds again. Ten RFIs plus one corrected RFI is eleven.

**The mitigation that exists is an alphabetical accident.** If an `rfi_log` is present in the same
period, its `set_field("rfiCount", ...)` writes an absolute total, and `"rfi" < "rfi_log"` sorts
the log last, so the sum is overwritten. Rename either type and the double-count returns. Nothing
records that this ordering is load-bearing.

`add()` also deliberately writes no `sources` entry, so the two fields most able to double-count
are the two with no provenance record. That is a faithful reproduction of the Apps Script
(`.gs` 916 and 949 bypass `setField`), and `models_dq.run_source_reliability` weights by the
`sources` map, so an `rfi`-derived count contributes no reliability weight while an
`rfi_log`-derived one does.

## A2. The original contract baseline is destroyed, not preserved

**You asked me to confirm or refute this. Confirmed: the code overwrites `bac` directly from a
change order, and nothing retains the original.**

`bac` is written by five document types. `contract_value` writes it unconditionally at rank 0;
`change_order` writes it unconditionally at rank 2, and rank 2 folds last. The original contract
sum is written and then overwritten in the same pass.

`baselineContractSum` is not the original either. It is first-non-null from the change order's own
`baseline_contract_sum` field, so it exists only if a change order happens to carry it, and it is
the CO's account of the baseline, not the contract's.

`baselineEnd` is worse. `change_order` assigns it by **direct dictionary write**, bypassing
`set_field` entirely:

```python
si["baselineEnd"] = str(new_end)
acc._note("baselineEnd", str(new_end))
```

So an extension of time rewrites the baseline end date, and the as-planned finish the schedule was
measured against is gone. The table's rule, "preserve the original baseline; a revised contract
value is applied through approved change orders, not by overwriting history", is not implemented
in any form. There is nowhere in `signalInputs` for both numbers to exist at once.

## A3. Change order state gating does not exist at any layer

**Confirmed absent, and more completely than you supposed.** The extraction prompt never asks for
a state:

```
"change_order": ["revised_contract_sum", "revised_completion_date", "change_order_date",
                 "change_order_count", "baseline_contract_sum"]
```

There is no `status`, no `state`, no `approved`, no `executed` anywhere in `extraction_fields.py`.
So the code cannot gate on state, and it is not that the gate was omitted at the merge: **the
information is never extracted, so it does not exist to gate on.** A draft change order and an
executed one are the same document to this pipeline, and both move `bac` and `baselineEnd`.

## A4. Field reports do not distinguish an atomic value from a period-to-date total

**Confirmed absent.** All three numeric field-report fields go through `set_field`, which is
unconditional last-write-wins:

```python
weather_days_lost      -> weatherDaysLost
float_remaining        -> floatRemaining
quality_deficiencies_noted -> qualityDeficienciesNoted
```

There is no cumulative-versus-atomic flag on any field, for any document type, anywhere in the
merge. `floatRemaining` is genuinely a snapshot and last-wins is right for it. `weatherDaysLost`
is the ambiguous one: if the model reports days lost **this day**, last-wins keeps one day's
figure and discards the rest of the period; if it reports days lost **to date**, last-wins is
correct. The pipeline cannot tell, does not ask, and produces a number either way.

This generalises. The same ambiguity is unresolved for `osha_recordable_incidents`,
`violations`, `ncr_issued`, and every other count the table describes as possibly cumulative.

## A5. The as-of date is decided by sort order, not by date

`docDate` is a single field written by **sixteen** document types, each with `set_date`, which is
last-write-wins. The surviving `docDate` is whichever contributing type sorts last alphabetically
within its rank, not the latest date.

`docDate` feeds C1.2 Data Timeliness. And `_derive_cutoff` in `documents.py` takes the **maximum**
parseable `document_date` across the period's documents, which is a different and more sensible
rule than the one `docDate` itself follows. Two notions of "as of" coexist and disagree.

## A6. Content hash decides which revision wins, when supersession is not declared

Migration 0013 added `supersedes_document_id` and `_period_documents` excludes superseded
documents from assembly. It works, and it is scoped to `(project, period)` correctly.

**There is no frontend control for it.** For every upload made through the interface, the
pre-0013 behaviour is unchanged: `_ordered_docs` sorts by `(rank, doc_type, sha256)`, so between
two same-type documents in one period the **lexicographically larger content hash wins** every
last-wins field, and the **smaller** wins every first-non-null field. One revision can therefore
produce a `signalInputs` mixing values from both versions.

This is deliberate as far as determinism goes, and the trade is documented: order-independence was
bought so that two projects holding the same evidence produce byte-identical `signalInputs`. What
is not recorded anywhere is that recency was the price. The self-check at the bottom of the module
asserts `assemble_signal_inputs(list(reversed(base))) == a`, which pins order-independence.
Nothing tests revision correctness.

## A7. Two document types collide on one field, resolved alphabetically

`qualityDeficienciesNoted` is written by `field_report` (from `quality_deficiencies_noted`) and by
`inspection_report` (from `deficiency_count`). They are different quantities. `field_report` sorts
after `inspection_report`, so field reports win. The code documents the collision; the table treats
Inspection Report deficiencies and Field Report deficiencies as separate concerns and has no way to
express that they share a slot.

`rfa_log` similarly fills `submittalsTotal` and `submittalsRejected` as a first-non-null fallback
when no submittal register supplied them, so a submittal rejection rate can be computed from RFA
figures. The table describes these as two different documents feeding two different methods.

## A8. Malformed numerics become a confident zero

`_num_or_null` reproduces the legacy `Number(String(v).replace(/[^0-9.\-]/g,''))`. `'N/A'`,
`'TBD'`, `'unknown'`, `'abc'` and `'  '` all become **0.0**. A model returning "TBD" for earned
value yields `cpi = 0.0`, the worst possible cost performance, with no refusal. `actual_cost`
degrades to `cpi = None` instead, only because the division guards `ac != 0` — which side of the
ratio the field sits on, not a designed protection.

This is D2 from the pipeline audit and I confirmed it still stands. The table assumes every value
is a number or absent; it has no third state for "the extractor returned prose".

---

# Part B. Per-field merge behaviour

53 distinct `signalInputs` fields are written by 21 branches (five document types share one risk
branch). The complete inventory of non-replacing behaviour is small:

| Operation | Fields | Count |
|---|---|---|
| `set_field` / `set_date`, last-write-wins in sort order | everything not listed below | 49 |
| first-non-null guard (`if si[x] is None`) | `bac`, `ev`, `ac`, `pv`, `actualPctComplete`, `plannedPctComplete`, `baselineContractSum`, `submittalsTotal`, `submittalsRejected` | 9 sites |
| `add()`, arithmetic sum | `rfiCount`, `changeOrderCount` | 2 |
| `keep_max()` | `rfiNumber` | 1 |
| direct assignment, bypassing `set_field` | `baselineEnd` (from `change_order`) | 1 |

Fields written by more than one document type, which is where precedence becomes visible:

| Field | Writers, in fold order |
|---|---|
| `bac` | contract_value → schedule_of_values (first-null) → pay_application (first-null) → monthly_report (first-null) → **change_order (overwrites)** |
| `ev` | schedule_of_values → pay_application (first-null) → monthly_report (first-null) |
| `pv` | time_phased_schedule → monthly_report (first-null) |
| `ac`, `actualPctComplete` | pay_application → monthly_report (first-null) |
| `plannedPctComplete` | time_phased_schedule → monthly_report (first-null) → **schedule_update (overwrites)** |
| `baselineEnd` | contract_value → **change_order (direct write)** |
| `qualityDeficienciesNoted` | inspection_report → **field_report (overwrites)** |
| `submittalsTotal`, `submittalsRejected` | submittal_register → rfa_log (first-null) |
| `rfiCount` | rfi (sums) → **rfi_log (overwrites absolutely)** |
| `docRiskScore` | the shared risk branch → commissioning_report |
| `docDate` | 16 types, last-wins |

---

# Part C. Precedence the code has that the table does not mention

**The document rank system is a code-only concept.** `_DOC_TYPE_RANK` classifies types as
baseline (0), default (1) or revision (2):

- baseline: `contract_value`, `schedule_of_values`, `time_phased_schedule`
- revision: `change_order`, `schedule_update`
- everything else: 1

Documents fold in rank order, then `(doc_type, sha256)` within a rank. This exists because the
Apps Script resolved "which document applied last" by **upload order**, which a fold over a set
cannot reproduce. Ranking by role reproduces the intent deterministically. It is a real
precedence rule, it changes numbers, and your table has no equivalent.

**Source reliability weighting is also code-only.** The `sources` map records which document type
supplied each field, and `models_dq.run_source_reliability` weights by fixed per-type reliabilities
(contract_value 0.95, pay_application 0.90 … oac_minutes 0.55, derived 0.40). The table has no
notion that one document is a better source than another for the same field.

**A hard refusal path exists that the table does not anticipate.** `validate_doc_risk_score` raises
`DocRiskScoreRangeError` for a document risk score outside 0 to 1 inclusive: nothing is stored and
no figures from that document are used. It is the only place the pipeline refuses rather than
coerces.

---

# Part D. Rules the table states that the code cannot express

Beyond A2, A3 and A4 above:

1. **Any event identity.** Dedup is on file bytes. No RFI number, change order number, NCR id,
   inspection event, audit event or submittal item is used as a key. `rfiNumber` is tracked only as
   a running maximum and never identifies anything. So "a corrected inspection replaces prior
   values for the same inspection" and "repeated mention of one open action must not create
   multiple incidents" have nothing to attach to.
2. **Any per-entity scope.** "Latest report per subcontractor and period" and "item-level analysis
   requires stable procurement-item ids" both need an entity dimension. `subcontractor_report`
   writes project-level scalars; a second subcontractor's report overwrites the first's.
3. **Combining independent completed projects.** Historical Data stores one analogous overrun, one
   historical BAC, one final cost, all last-wins. Ten reference projects produce one, whichever
   sorts last. Reference Class Forecasting is reading a sample of size one.
4. **Any series other than cpi and spi.** NCR backlog change, procurement trend point, milestone
   trend, S-curve, weekly lookahead series, safety period deltas: none exist. `milestoneHistory` is
   structurally unobtainable, and A2.7 Milestone Trend reads it.
5. **Units and basis.** Currency basis, price date, rating scale and rating source are named in the
   table and are not extracted fields.
6. **Normalisation for project type, year, currency, scope** on historical data: not extracted.

---

# Part E. What the Apps Script did differently

Report only; nothing was ported.

| Behaviour | Apps Script `Code_v10.36` | Current backend |
|---|---|---|
| Which document applies last | **Upload order** | `(rank, doc_type, sha256)` |
| `rfiCount` accumulation | `si.rfiCount = (si.rfiCount \|\| 0) + n` mutating **persisted** state, so a replay double-counted | Fold over a per-call de-duplicated set; a replay is a no-op |
| Unrecognised filename | `return 'monthly_report'` — every unknown document became a monthly report and was asked for EV/AC/PV/BAC, and the model obliged | Returns `None`; caller records `UNMAPPED` and extracts nothing |
| "We do not know what this is" | No such state existed | `UNMAPPED` |
| EOT on a change order | Also appended a `baseline_adjusted_eot` entry to `project.events` | Not reproduced; events are project state, not `signalInputs` |
| Document risk score range | No validation | Refuses outside 0 to 1 |
| `sources` for additive fields | Bypassed `setField`, so no source recorded | Reproduced deliberately |

The monthly-report fallback is the one that mattered most: it manufactured project-controls inputs
from contracts, photo logs and scanned letters, and those flowed into CPI and SPI.

---

# Part F. What the storage cannot express, and a design

## F1. What is actually stored today

More than the brief assumes, and it is worth being precise because two things have changed since
the audits.

- `DocumentUpload.period` is NOT NULL and assembly is **strictly per period**
  (`_period_documents` filters `period == period`). So the table's "latest per period" is half
  honoured: documents never leak across periods.
- `ComputedResult` is append-only with one live row per `(project, period)`, and it stores the
  `signal_inputs` used and the `period_cutoff`.
- **`_period_history` now builds real cpi and spi series** from earlier periods' live
  `ComputedResult` rows, filtered `period < period`. This is period-safe by construction and is
  why CUSUM, Kalman, ARIMA and Regression to Mean no longer fabricate or abstain wrongly. It
  supplies a series only when there are at least two points.
- `_events_as_of` truncates the project event log at the cutoff.
- `supersedes_document_id` exists and works, with no UI.

So the shape is: **a per-period flat dict, plus two derived series reconstructed after the fact
from stored results.**

## F2. What it cannot express

1. **The kind of a value.** `signalInputs` says `ac = 5,000,000`. It does not say whether that is a
   cumulative snapshot, a period delta, or an event total. Every rule in your right-hand column
   depends on that distinction and none of it is representable.
2. **A field's kind varying within one document.** Your framing is exactly right: a pay application
   is a series for CPI and an event for a contingency draw. The kind belongs to the **field**, not
   the document type, and the storage has no per-field metadata at all.
3. **Entity identity**, so no event ledger, no per-subcontractor or per-item scope, no "a revision
   is not a new RFI".
4. **Event state**, so no "only approved or executed COs modify BAC".
5. **Two values for one field at once**, so no "original baseline preserved while the revised sum
   is applied".
6. **An as-of date per value.** There is one shared `docDate` for the whole assembly, written by 16
   types. Selection therefore cannot be by date, and is by hash.
7. **A series for anything but cpi and spi**, and even those are reconstructed from stored results
   rather than stored as observations, so a field that is not carried on `signal_inputs` can never
   have one.
8. **Alignment between projects.** The portfolio vector selector takes each other project's
   `max(period)` live result with no relation to the period being computed. This is P1 and it is
   the one defect that lets a later period's figures change an earlier period's stored result.

## F3. The design

Three layers. Only the first is storage.

### Layer 1: observations, append-only

One row per (field, document, entity), never overwritten.

```
observation
  project_id        
  period            int          the reporting period the document was filed to
  field             text         "ac", "changeOrderCount", "rfiOpen" ...
  value             numeric/text
  kind              enum         SNAPSHOT | EVENT | DELTA
  entity_key        text NULL    "CO-014", "RFI-233", subcontractor id; NULL for snapshots
  entity_state      text NULL    draft|pending|approved|rejected|executed, for stateful events
  as_of             date         the date THIS VALUE speaks about, not the upload date
  document_id       fk
  revision_of       fk NULL      = supersedes_document_id, promoted to the observation
  source_doc_type   text         retained for source-reliability weighting
```

**`kind` is declared per field, not per document type.** That is the change that makes the table
expressible. A pay application emits `ac` as SNAPSHOT and a contingency draw as EVENT from the same
extraction. The field registry, not the document branch, owns the declaration.

This is derivable from what is already stored: `Document.extraction` plus `DocumentUpload.period`
plus the document's own date. It is an additive projection, not a rewrite, so it can be built and
compared against the current merge before anything depends on it.

### Layer 2: selection, a pure function

`signalInputs` stops being storage and becomes the **output** of selection: the same flat dict the
computation layer already consumes, so nothing downstream changes.

- **SNAPSHOT**: the observation with the greatest `as_of` where `as_of <= cutoff`, excluding
  superseded ones, tie-broken by `revision_of` depth then `document_id`. **Never by content hash.**
  This fixes A6 for undeclared revisions too, because a corrected document filed later carries a
  later `as_of` and wins on its own merits.
- **EVENT**: group by `entity_key`; within each entity take the latest non-superseded observation
  (that is "a revision is not a new RFI"); filter by `entity_state` where the field declares one
  (that is change order state gating); then aggregate. Ten RFIs plus a correction is ten.
- **DELTA**: summed within a period, never across, and never mixed with a SNAPSHOT of the same
  quantity. This is where "10 open then 12 open means 12, and the series is [10, 12]" is decided:
  `ncrOpen` is a SNAPSHOT, so the series is the per-period selection, and summing is not an
  available operation on it.

### Layer 3: the request, and refusal

A computation declares what it needs; the assembler answers or the module abstains.

```
need("spi",           shape=SERIES, span=PERIODS_UPTO(period), min_points=2)
need("ac",            shape=SCALAR, as_of=cutoff)
need("change_orders", shape=EVENT_SET, states={"approved", "executed"})
```

**Abstention must be the default and must be enforced at the registry, not left to each module.**
The strongest argument for declarations is not documentation: it is that a module needing a series
that cannot exist becomes a startup failure instead of a silent fabrication. That is precisely the
CUSUM defect, and the three EVM modules that abstained correctly did so by each author's care
rather than by a rule.

### Revision within a period versus a new period's observation

Structural, not inferred:

- Same `(project, field, entity_key)`, **same period**, later `as_of` or an explicit `revision_of`
  → a revision. Selection takes the later one. The earlier row is retained and never deleted.
- Same `(project, field)`, **different period** → a new observation. It becomes a point in the
  series. Selection never collapses it into the current value.

Today these two cases are indistinguishable because the only axis is the period integer on the
upload, and within a period everything is a peer.

### Latest-as-of-cutoff

`as_of` lives on the observation, so the cutoff filters **values**, not documents. Today
`period_cutoff` filters nothing and is read by exactly one module. Under this design every
selection is `as_of <= cutoff`, so a recompute of an earlier period reproduces it exactly, and the
`docDate`-versus-`_derive_cutoff` disagreement in A5 disappears because there is no single shared
`docDate` to disagree about.

### Interaction with `supersedes_document_id`

Keep it, and promote it. It becomes `revision_of` on every observation the superseding document
produces, so one declared document-level edge still expresses "this replaces that" while the
per-field selection gains a recency rule that works **without** a declaration. Two mechanisms, one
meaning, with the explicit one winning when present. Its `(project, period)` scoping is already
correct and should not change: the same document can be current evidence in another project.

### P1, and why this design closes it

A design that leaves P1 possible is not finished, so it is a rule, not a convention:

> A portfolio vector for another project, used in computing project P at period N, must be selected
> by `period_cutoff <= P.period_cutoff`, taking that project's latest live result at or before the
> cutoff. Never `max(period)`.

`period_cutoff` is already stored on `ComputedResult`, so this needs no new column. It makes
recomputing period 1 after other projects have moved to period 2 reproduce the period-1 snapshot,
because a period-2 result has a later cutoff and is excluded. It also makes two projects computed
for period 1 at different wall-clock moments mutually comparable, which they are not today.

This must carry a check that recomputes an earlier period after a later one exists and asserts the
stored snapshot is byte-identical. The nearest current test cannot detect P1: both its projects are
period 1 and it never varies period, so it passes with the defect fully present.

---

# Part G. The four changes

## G1. The `fairnessSensitive` gate is removed

`_derive_decision` computed `fairness_gate = escalate and project.get("fairnessSensitive") is
True`, and selected a different escalation action and a different escalation authority from it.

**Proven unable to fire**: `fairnessSensitive` is not in `SIGNAL_INPUT_KEYS` (79 keys), no merge
branch writes it, and `documents.py` never supplies it. On the server the condition has always been
`False`.

The condition and both gated wordings are gone. **The response key stays, always `False`**, because
`assets/js/app.js` reads `d.fairnessGateRequired` to decide whether to render an acknowledgement
checkbox and whether to permit submission, and this task may not touch the frontend. Removing the
dead condition is the change; removing the contract is not.

The browser's own `decision.js:228` still computes a live gate from `project.fairnessSensitive`,
which `ingest.js:105` does write into the project document. That is the legacy client path, it is
untouched, and it is a separate decision.

## G2. Submittal is split, and the register is what the platform keeps

`submittal` named two documents with different version policies. An individual submittal is one
item with a state moving through review, and a resubmission is a new event about the same item. A
register is a log, and a later revision replaces the earlier one.

**The individual form was never actually supported.** The extraction mapping only ever asked for
`submittals_total` and `submittals_rejected`, which are register fields. There is no item identity,
no submittal state, and no per-item field anywhere in the pipeline.

The canonical type is now **`submittal_register`**. `DOC_TYPES` offers it; the merge branch, the
document-risk set and the field list all use it.

**What happens to anything typed as the individual form**, which is your question:

- Nothing is lost. `submittal` remains accepted and normalises to `submittal_register` through a
  declared alias, so every `Document.doc_type` row already carrying the old string still reaches
  the register branch and still contributes its figures. Dropping the string would have made every
  stored submittal silently stop contributing at the next recompute, which is the exact silent-loss
  shape this codebase refuses. A check asserts the legacy string produces byte-identical
  `signalInputs` to the canonical one.
- The classifier is no longer offered the ambiguous name, so new documents are classified as the
  register or not at all.
- A document that genuinely **is** one submittal will now be classified as a register and asked for
  totals it does not have. It will yield nulls, or the model's guess at a total. **That is not
  fixed here and it is the honest consequence of keeping only the register**: until an event
  ledger with item identity and state exists (Layer 1 above), the individual form has nowhere to
  go. The safer alternative would be to classify individual submittals as `UNMAPPED` so they
  contribute nothing rather than a guess, which is a decision for you.

## G3. Commissioning Report: what expanding it requires

Today it is evidence only: `docRiskScore` and, deliberately, not even `docDate`. It has its own
terminal merge branch.

It is the project closeout document, the final record, and carrying only a risk score is the
largest single gap between the table and the code. Expanding it requires, in order:

1. **Extraction fields**: systems commissioned, tests planned, tests passed, tests failed,
   deficiencies open, deficiencies closed, turnover milestones planned and achieved, and the
   commissioning authority's sign-off date. None of these exist in `ALL_FIELDS`, so this is new
   vocabulary, not legacy drift to preserve.
2. **A per-system entity**, because a commissioning report is a ledger by system, not a project
   scalar. Under the current storage the second system overwrites the first. This is the clearest
   case in the whole table for Layer 1's `entity_key`, and expanding commissioning before that
   exists would produce a report that reads one system and calls it the project.
3. **A closeout state on the project**, because `_derive_health_state` already has a `"Complete"`
   arm that nothing can currently reach: no code path sets that state. Commissioning is what would
   set it.
4. **New computations, or an explicit decision not to add any.** The table names Document Risk and
   Evidence Synthesis as today's use. Turnover completeness, deficiency closure rate and test pass
   rate would be new modules, and `NAMING_AUTHORITY.md` fixes the taxonomy at 100 computations, so
   adding them is a taxonomy change and needs your approval, not a session's.

Not implemented, as instructed.

## G4. D2 to D5, and how they interact with the redesign

Reported, not fixed.

| | Finding | Interaction with the design |
|---|---|---|
| **D2** | Malformed numeric text becomes `0.0`; `'TBD'` for earned value yields `cpi = 0.0` | **Layer 1 makes this worse before it makes it better.** An observation store records every value with provenance, so a coerced zero becomes a durable, queryable, authoritative-looking row. The coercion must be replaced by a refusal or a null **before** observations are stored, not after. This is the one D-finding that should be fixed *first*, not alongside. |
| **D3** | An unparseable or absent document date falls back to the wall clock for `period_cutoff` | **Directly blocks the design.** `as_of` is the selection key for every field in Layer 2. A wall-clock `as_of` means selection order depends on when the compute ran. The design requires that a document with no usable date is refused or explicitly marked undated and excluded from as-of selection, rather than silently stamped with today. |
| **D4** | A declared document type is silently discarded for already-seen bytes; the first uploader's classification is global and permanent | **Orthogonal to storage, but it becomes visible.** With per-field observations carrying `source_doc_type`, a misclassification propagates into every field the wrong branch writes. The design does not fix it; it makes the blast radius legible. The narrow defect is that the API accepts a `docType` parameter it does not honour and says nothing. |
| **D5** | An undeclared revision merges by content hash | **This is the finding the design closes.** Layer 2's SNAPSHOT rule selects by `as_of` then revision depth, so recency wins without the uploader declaring anything, and `supersedes_document_id` becomes the explicit override rather than the only mechanism. It is also why the design must not depend on the supersede field alone: there is no frontend control for it, so in practice it is never set. |

---

# Part H. Verification of Part G

Only Part G was implemented, so only Part G is verified.

`server/tools/test_submittal_and_fairness.py`, 23 checks, no database and no network.

**15 faults injected, every one detected, every one reverted with a byte comparison against a
pristine snapshot and a re-run confirming the suite returned to baseline — after every single
fault, not once at the end.**

| Fault | Checks red |
|---|---|
| The fairness gate condition is put back | 1 |
| The gated escalation wording returns | 2 |
| The response key is dropped | 5 |
| `fairnessSensitive` added to the producible key set | 2 |
| A merge branch starts writing `fairnessSensitive` | 1 |
| The submittal alias entry is removed | 7 |
| `canonical_doc_type` becomes identity | 6 |
| Canonicalisation stops being identity for other types | 2 |
| The ambiguous name is offered again | 1 |
| The register is dropped from the offered types | 5 |
| The merge fold stops canonicalising | 3 |
| The register loses its document risk score | 1 |
| The register field list loses its totals | 1 |
| `is_mapped` stops resolving aliases | 1 |
| `is_mapped` accepts anything | 1 |

### Three of my own checks were wrong, and injection found all three

- **A source scan that was reading 24% of the file.** `code_of()` stripped comments and docstrings
  by tracking triple-quote toggling line by line. It desynchronised and silently discarded **735
  of `extraction_merge.py`'s 964 lines, including every merge branch**. The fault that writes
  `acc.set_field("fairnessSensitive", True)` into the pay_application branch left the suite green,
  because that branch was not in the text being searched. Rewritten using `tokenize` and `ast`:
  comments and docstrings are removed by token position, string literals are kept, because a merge
  branch writing a field names it as a literal and that is exactly what the scan looks for.
- **A suite that died instead of failing.** Renaming the output key made `run_abm_governance` raise
  `KeyError` at module scope, and the file printed **no `RESULT:` line at all**, which reads
  exactly like a clean run. The call is now wrapped so a raising module produces a red check.
- **A missing check that made a real behaviour unasserted.** Removing alias resolution from
  `is_mapped` left the suite green, because the merge fold canonicalises before asking. But
  `documents.py:721` calls `is_mapped` with a stored `doc.doc_type` and puts the answer in the
  upload response as `contributes`, so a stored `submittal` failing there would tell the PM their
  document contributed nothing while the merge quietly used it. Two checks added.

The comment-stripping is itself proven non-vacuous: `models_decision.py` mentions
`fairnessSensitive` four times, all in comments explaining the removal, and the scan still passes.

### Suites

- **Server: 24 suites, 1361 checks, 0 failures**, on a throwaway sqlite built by
  `alembic upgrade head`. Never pointed at production.
- **`tests_render.html` 49/49**, **`tests.html` 51/51**, in a real browser. No compositing in this
  container, so these are DOM reads and no screenshot is claimed.

---

# Part I. What I could not establish

- **How often same-period same-type revisions actually happen.** This is a code reconciliation. The
  frequency determines how much A1 and A6 bite in practice and I have no data on it.
- **Whether `weatherDaysLost` and the other ambiguous counts are atomic or cumulative in the
  documents themselves.** The prompt does not ask, the extraction does not say, and I did not have
  sample documents. A4 is a statement that the distinction is unrepresentable, not a claim about
  which reading is correct.
- **Whether any operational tooling or the research harness writes `signalInputs` directly**,
  bypassing the merge. I traced `server/app`; `server/tools` and `research/` were not exhaustively
  searched for writers.
- **The real extraction prompt's full text as sent.** I read the per-type field lists and the
  classifier hints, which is the contract; I did not capture a complete assembled prompt from a
  live call.
- **Whether the frontend surfaces `unmapped_filenames` and the per-file `contributes` note to the
  PM.** The server returns them; I did not trace the upload UI.
- **Whether `Code_v10.36_editor_head.gs` is the version that actually ran in production.** It is
  the reference copy in the repository and the port's line citations resolve against it, but
  `apps_script/deployed/` exists separately and I did not diff the two.

---

## Repository state

`origin/main` was `926adf6` and in sync with a clean working tree at the start. No other session's
work was present. All checks were run on the merged state before committing.

## Files changed

- `server/app/simulation/models_decision.py` — the fairness gate removed. The one permitted change
  under that directory.
- `server/app/extraction_fields.py` — `submittal_register` canonical, `LEGACY_TYPE_ALIASES`,
  `canonical_doc_type`, alias-aware `is_mapped`.
- `server/app/extraction_merge.py` — the register branch and sets renamed, canonicalisation at both
  fold sites.
- `server/tools/test_submittal_and_fairness.py` — new, 23 checks.
- `REPORT_2026-08-02_document-reconciliation.md`, `T6_HANDOFF.md`.

## Flagged for you

- **Individual submittals now classify as a register and will be asked for totals they lack.**
  Routing them to `UNMAPPED` instead is a decision for you (G2).
- **D2 should be fixed before the observation store is built, not with it** (G4).
- **The evidence-policy audit is not on `main`.** It is on `t15-local-unpushed` only, dated
  2026-08-01. If it matters as a record it should be landed; its CUSUM finding is now out of date.
- **`UI_ONLY_DOC_TYPES` is still dead code** in `extraction_fields.py`, imported by nothing.
