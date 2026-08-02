# Storage redesign: observations, selection, and the four defects

Built as designed in `REPORT_2026-08-02_document-reconciliation.md` Part F. **Server 1394 checks
across 25 suites, `tests_render.html` 49/49, `tests.html` 51/51, green on merged `main`.** Nine
faults injected for the new suite, every one detected with a distinct signature, every one
reverted with a byte comparison and the baseline re-run after every single fault.

---

# What the new structure can express that the old one could not

The old storage held one current value per field per project — a flat dict with no reporting
period on any value, no per-field date, no entity identity, and no room for two values of one
field at once. Which value survived a contested field was decided by alphabetical sort order and
content-hash tiebreaks.

The new structure is the design's three layers:

**Layer 1 — `observations`, append-only (migration 0014).** One row per
(project, period, document, field, entity): value, kind, `entity_key`, `entity_state`, `as_of`
(the date the value speaks about, never the upload clock, NULL when nothing parses),
`revision_of` (0013's `supersedes_document_id` promoted onto every observation the superseding
document produces), `source_doc_type`. Rows are DERIVED from what is already stored
(`documents.extraction` + `document_uploads.period` + the document's own dates), persisted at
upload and at compute, keyed uniquely so re-deriving inserts nothing — an additive projection,
never a second source of truth, and never updated or deleted.

**Layer 2 — selection, a pure function.** `signalInputs` stops being storage and becomes the
OUTPUT of `select_signal_inputs(observations, cutoff)`: the same flat dict, same key order, same
`sources` shape, same JS-truthiness quirks, same cpi/spi derivation — the 100 computations
receive exactly what they expect and `server/app/simulation/` is untouched. Selection rules:

- **SNAPSHOT** (register replace): lowest declared writer tier wins; within a tier the latest
  `as_of` wins. A dated observation always beats an undated one; wholly undated groups fall back
  to the historical `(rank, doc_type, sha256)` order, so selection stays deterministic and order
  independent. **Recency is never decided by a content hash between dated values** — that closes
  A6/D5 for undeclared revisions too, while the declared `supersedes` edge keeps working as the
  explicit override.
- **PERMANENT**: the earliest wins and nothing later replaces it. The original baseline.
- **EVENT**: grouped by entity; the latest observation per entity is that entity's record — a
  revision supersedes THAT record, never the population; entities are then aggregated, and a
  stated ledger total still beats counting. Change-order rows carry `entity_state="executed"`
  (they arrive executed; approval happens off-platform) and the need declaration filters on it.
- **DELTA**: summed within a period, never across. Declared for completeness; **no field
  declares it** — both accumulating branches died with the individual forms.
- Every selection is bounded `as_of <= cutoff`, so a recompute of an earlier period with its
  stored cutoff reproduces it even after later-dated evidence lands in the period.

**Layer 3 — declarations (`field_registry.py`).** The kind attaches to the FIELD, not the
document type; a field with no declared kind cannot be emitted at all (`emit_observations`
raises). `NEEDS` declares the served shapes: `cpiHistory`/`spiHistory` as SERIES (served by
`_period_history`, unchanged and not regressed), `changeOrderCount` as EVENT_SET with
states={executed}, and `milestoneHistory` explicitly declared UNSERVABLE so nothing synthesises
it. **The registry-enforcement half of Layer 3 — a module's need failing at simulation-registry
startup — lives inside `server/app/simulation/` and was deliberately not built**, because that
directory is out of scope; abstention remains the default by the modules' own `check_inputs`,
exactly as before. This is the one part of Part F not built as written, for the reason Part F
itself anticipated; nothing downstream depends on it.

The two axes stay distinct structurally: same (project, field), same period, later `as_of` or a
`revision_of` edge is a revision (selection takes the later; the earlier row is retained);
a different period is a new observation and a new point in the series. Verified end to end:
a register at 10 then 12 within period 1 yields 12; the same register at 15 in period 2 yields
two stored observations with 15 current and period 1 still reading 12.

# The four defects

**1. Contract Value baseline preservation — CLOSED.** `contract_value` now emits
`baselineContractSum` as a PERMANENT observation of its own `original_contract_sum`, so the
original survives every executed change order and is readable in `signalInputs` alongside the
amended `bac` (the CO wins `bac` by declared tier, as the amendment layered on the baseline —
no longer by rank-2-folds-last). The `baselineEnd` direct dictionary write is gone with the
fold; the CO's revised end wins by the same declared precedence and the contract's original end
survives as its own observation. `projectuploadstatus` returns a `baseline` block:
`original` (sum, start, end) and `amendments` (each executed CO's revised figures, dated,
state "executed") — both readable, from the store.

**2. `docDate` has one answer — CLOSED.** `docDate` is no longer a written field with sixteen
last-wins writers. It is DERIVED at selection: the latest `as_of` among the period's eligible
observations — the same rule as the cutoff, which now takes the maximum over the observations'
own dates as well as `document_date`, so on a first compute `docDate` and `period_cutoff` are
the same number, asserted by a check. Two consequences worth knowing: `docDate` is now always an
ISO date (an unparseable date string no longer becomes `docDate`, and `historical_data`'s bare
completion year "2019" no longer leaks into it), and a type that never set `docDate` before but
carries a real date (e.g. commissioning's `document_date`) now legitimately participates —
which is exactly what `_derive_cutoff` already did.

**3. P1, portfolio contamination — CLOSED.** The portfolio vector selector in
`_compute_and_store` filters `period_cutoff <= cutoff` and takes each other project's latest
live result at or before this computation's cutoff — never `max(period)`. Verified with three
projects: recomputing A's period 1 after B advanced to period 2 is byte-identical on the stored
portfolio snapshot; B's own period 1 recomputed after its period 2 exists is byte-identical
too; and A and B recomputed for period 1 at different moments see the same three-project
population at the same cutoff. The `max(period)` fault re-injected turns exactly the
byte-identical check red. No change to how periods are assigned was needed.

**4. Registers and logs only — CLOSED.** The individual `rfi` form is out of `DOC_TYPES`, out
of the extraction mapping, out of the risk-document set, and the bare-"rfi" filename heuristic
returns None — an individual RFI is stored, reported `contributes: false`, and never asked for
totals it cannot supply (the same decision G2 flagged for individual submittals, now taken).
Its accumulating `add()` branch is gone — no additive accumulator survives in the merge source,
asserted — and **the `"rfi" < "rfi_log"` dependency is gone by construction, verified rather
than assumed**: a check enumerates the emission table and asserts `rfiCount` has exactly one
writer (`rfi_log`), so no ordering between two writers exists to depend on.

# What changed in code

- `alembic/versions/0014_observations.py` — the table, unique on (project, period, document,
  field, entity). Run against a throwaway sqlite (`upgrade head`, `current` verified). **No
  backfill and no repair logic: the site starts fresh.** Production migration is Lin's to run.
- `app/research_models.py` — the `Observation` model.
- `app/field_registry.py` — new: kinds, writer tiers, needs.
- `app/extraction_merge.py` — rewritten: `emit_observations` + `select_signal_inputs`;
  `assemble_signal_inputs`/`assembly_report` keep their signatures (assemble gains an optional
  `cutoff`), determinism/order-independence/idempotence pinned by the self-check as before.
- `app/documents.py` — persists observations at upload and compute; selection at the cutoff;
  the cutoff-aligned portfolio selector; the `baseline` block on `projectuploadstatus`.
- `app/extraction_fields.py` — `rfi` removed from the vocabulary; classifier hint reworded to
  the log; filename heuristic returns None for a bare RFI.
- `tools/test_storage_redesign.py` — new, 32 checks.
- `tools/test_document_versioning.py` — its section 1 used to REPRODUCE the old defects
  (hash-decided revisions, 10+12=22); it now asserts them dead, and its fixture's hash ordering
  flipped so "the original wins unaided, supersession flips it" still holds under the
  equal-date tiebreak (29 checks, was 28).

# Behaviour changes that are not one of the four defects

- `sources` is built in key order from selection winners (same shape and content per field;
  entry = winning observation). A counted change-order ledger writes NO `sources` entry,
  preserving the legacy additive-branch parity that `models_dq` weighting depends on; a stated
  total does, as `setField` did.
- `rfiNumber` and `rfiResponseTimeDays` can no longer be produced (only the individual form
  wrote them). The keys remain in the dict as None; A4.2's `rfiNumber` fallback path abstains.
  Recorded in `field_registry.UNEMITTABLE_FIELDS` so it is a decision, not drift.
- Between two same-type, same-date (or both-undated) documents, ties resolve by the historical
  last-write order (higher hash) uniformly — including fields that were legacy first-non-null,
  where the lower hash used to win. Deterministic either way; the fixture flip in
  `test_document_versioning` documents it.
- On `adminrecompute`, the reused cutoff now BOUNDS selection: a document added to the period
  after the original compute, carrying a later `as_of`, no longer silently changes the
  recomputed figures. That is the design's stated intent.

# Still open, and flagged

- **D2 (malformed numerics coerce to 0.0) is unchanged and now persists as observation rows.**
  The reconciliation report said D2 should be fixed BEFORE the store is built; it was not in
  this task's four defects, and changing `_num_or_null` alters validated instrument behaviour,
  so it was not done unasked. It is now more visible, not less: a coerced zero is a queryable
  row with provenance. It should be the next fix.
- **D3 (wall-clock cutoff fallback) unchanged**: a period whose documents carry no parseable
  date still gets the server date as cutoff. Undated observations are stored as undated and
  pass the cutoff filter — refusing them would have blanked most fields.
- Layer 3 registry enforcement inside `simulation/` — see above; needs a decision to open that
  directory.
- `UI_ONLY_DOC_TYPES` is still dead code.

# Verification

- Baseline before work: 1361/1361 across 24 suites. After: **1394/1394 across 25** (new suite
  32; versioning 28→29), fresh migrated sqlite per suite, `PYTHONIOENCODING=utf-8`.
- `tests_render.html` **49/49**, `tests.html` **51/51** in real Chromium; DOM reads, no
  screenshot claimed (no compositing in this container).
- The new suite is wrapped so a crash prints a failing RESULT line, never silence.
- **Nine faults, all confirmed applied (anchor must match exactly once), all detected, all
  reverted byte-identical, baseline re-run green after EVERY fault:**

| Fault | Result |
|---|---|
| P1 selector back to `max(period)` | 31/32 |
| `as_of` dropped from snapshot selection (hash decides again) | 28/32 |
| contract stops emitting the original baseline sum | 29/32 |
| observation persistence disabled | 28/32 |
| selection stops bounding at the cutoff | 31/32 |
| `docDate` derivation removed | 31/32 |
| individual `rfi` offered again | 30/32 |
| an event revision becomes a second event | 31/32 |
| the log stops writing `rfiCount` | 25/32 |

- One of my own checks was vacuous and was caught before it could lie: the first "two projects
  see the same portfolio" fallback compared an expression to itself. Rewritten as two
  byte-identical recompute comparisons plus a population/cutoff equality, and the P1 fault
  proves the byte-identical one can fail.

## Repository state

`origin/main` at `f4a60a9`, branch `claude/storage-redesign-8d16zm` contains it; working tree
held only this task's files. Nothing under `server/app/simulation/` was modified; nothing
outside the repository was touched; production was not inspected and no DATABASE_URL pointed
anywhere but throwaway sqlite files.
