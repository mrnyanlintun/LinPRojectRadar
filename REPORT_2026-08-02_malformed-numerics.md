# D2: malformed numerics refuse instead of becoming a confident zero

**Server 1440/1440 across 26 suites, `tests_render.html` 49/49, `tests.html` 51/51, green on
merged `main`.** Eight faults injected, all confirmed applied, all detected with distinct
signatures, all reverted byte-identical with the baseline re-run after every single fault.

---

# The entry points, enumerated — all four now guarded

Every route by which a numeric field can reach storage or computation was traced from the
writers, not assumed. `Document` rows have exactly one writer (`documents.py`, from
`extract_many` results); the import and seed tools create none.

| # | Entry point | What it is | Guarded |
|---|---|---|---|
| 1 | `extract_many` (extraction_client.py) | Fresh extraction from the model; the only path that creates a `Document` row | **Yes.** `validate_numeric_fields` runs beside the doc-risk guard, BEFORE the caller writes any row. Refusal is per document, not per batch. |
| 2 | `emit_observations` (extraction_merge.py) | The merge / observation-persistence boundary — the backstop for rows stored before the guard or arriving by any other route | **Yes.** Validation runs before anything is emitted, so a refused document emits nothing at all — all-or-nothing by construction. |
| 3 | `overwritesignal` (writes.py) | The legacy facade's live write into an arbitrary named `signalInputs` field | **Yes.** `validate_signal_value`: malformed refuses, negative non-signed fields refuse, `docRiskScore` keeps its 0..1 authority. Returned as the module's `err` shape. |
| 4 | `save` (writes.py) | The legacy facade's wholesale document replacement, whose client copy carries a full `signalInputs` blob — **the live action nobody had listed**; the risk-score guard never covered it either | **Yes**, for fields whose value CHANGED. Refusing a save because an already-stored value fails the contract would brick every edit of a project carrying it; the stored value is not this save's doing. The site starts fresh, so no such stored value exists today. |

No half-store is possible: at entry 1 the refusal happens inside `extract_many`, and
`documents.py` only persists results whose `ok` is true, so nothing exists to clean up. At
entry 2 validation precedes emission, so a document with one bad field contributes zero
observations, never a partial set. Both are asserted by checks.

# The three cases

- **Absent** (None, `""`, key missing): unchanged. The observation is not emitted and the
  computation abstains. Asserted: a monthly report with no earned value uploads, computes, and
  yields `cpi = None`.
- **Malformed** (present, not readable as a number: `"TBD"`, `"N/A"`, `"unknown"`, `"1.2.3"`,
  a boolean): **refused**, whole document, field and file named.
- **Out of contract** (readable, outside the field's range): **refused**, same shape as the
  existing risk-score guard. The range contract is per field in `field_registry`: everything
  numeric is non-negative EXCEPT `totalFloat` / `consumedFloat` / `floatRemaining` (negative
  float is a real schedule state) and `analogousOverrunPct` (a reference project can underrun).
  `docRiskScore` keeps its existing 0..1 guard as the authority for its range. No percentage
  upper bounds were imposed: the table's units-and-basis question (scale 0..1 vs 0..100) is
  unresolved, and refusing `102` for a percent-complete would be guessing a contract nobody
  has stated.

# The parsing rule, and what the code did before

**Before:** `_num_or_null` reproduced the legacy `Number(String(v).replace(/[^0-9.\-]/g,''))`
— it stripped every non-numeric character and parsed what was left. `"TBD"` stripped to `""`
and became `0.0`; `"N/A"` likewise; `"(500)"` lost its parentheses and became **positive**
500. Permissive in exactly the wrong places: it accepted garbage as zero and silently flipped
an accountant's negative.

**Now:** `_parse_numeric` accepts the recognised decorations and nothing else — a currency
symbol (`$ € £`), comma thousands separators, spaces, one trailing `%`, and parentheses
meaning NEGATIVE (honoured, not stripped). `"$1,200,000"` → 1200000, `"1,200"` → 1200,
`"45%"` → 45, `"(500)"` → −500. Anything that still fails a strict float parse after removing
those is malformed and refuses. This is the answer to "would a strict rule refuse legitimate
values": yes it would — currency, separators, percent signs and parenthesised negatives are
all real and all accepted — which is why the rule is decoration-aware rather than strict, and
why it is also not the legacy stripper, which could not tell `"TBD"` from an absent value or
a negative from a positive.

Emission now coerces through the same parser, so the value the guard accepted is the value
selection sees (the legacy stripper would have disagreed with the guard about `"(500)"`).
`_num_or_null` survives only inside the risk-score range guard and as documented history; its
malformed-to-0.0 quirk is dead at every guarded boundary, and the module docstring says so.

# What the uploader sees

The existing per-file `{ok: false, error}` shape, rendered verbatim by the extraction-failure
dialog — no new surface. The message names the field, the file, the offending value, states
that nothing was stored, and says what to do:

> earned_value in tbd.pdf is 'TBD', which cannot be read as a number. Nothing was stored for
> this document and no figures from it were used. If the document does not state this value,
> the extraction should leave it blank rather than write 'TBD'; re-run the extraction, or
> correct the document.

**Strings written this session, flagged per the standing rule** (operational error wording
only, no liability or consent language): the message above; the range variant ("… is −3, and
this field cannot be negative. Nothing was stored …"); the facade variants ("ev cannot be set
to 'TBD': it is not readable as a number. Nothing was changed." and the `Save refused: …`
prefix). No em dashes.

# Verification

- Baseline before: 1394/1394 across 25 suites. After: **1440/1440 across 26** (new suite
  `test_malformed_numerics.py`, 46 checks). `tests_render.html` 49/49, `tests.html` 51/51 in
  real Chromium, DOM reads.
- All existing suites stayed green with the guards live — no fixture anywhere was feeding
  malformed numerics, so nothing legitimate was refused.
- The new suite covers the four minimums and more: malformed refuses rather than storing zero
  (and no `Document` row and no observation row exists afterwards); decorated-but-legitimate
  values are accepted end to end into a computed result; the clean document in the same batch
  still stores (whole-document, not whole-batch); the uploader's error names field, file,
  value, and remedy; absent still abstains; the signed-field exceptions accept negatives.
- The suite is wrapped so a crash prints a failing RESULT line. That wrapper fired for real
  during this session (a `KeyError` in fixture setup read as `FAIL suite crashed`, never as a
  clean run), and three of the eight faults (F1, F3, F7) crashed the suite mid-run and were
  still reported as red results.
- **Eight faults, all confirmed applied (anchor must match exactly once), all detected, all
  reverted byte-identical, baseline re-run green after EVERY fault:**

| Fault | Result |
|---|---|
| F1 extraction boundary guard removed | 4/13 (crashed, wrapped as red) |
| F2 merge/store backstop removed | 43/46 |
| F3 parser coerces malformed to 0.0 again | 18/33 (crashed, wrapped as red) |
| F4 range check dropped | 45/46 |
| F5 parenthesised negative loses its sign | 44/46 |
| F6 overwritesignal guard removed | 43/46 |
| F7 save guard removed | 30/33 (crashed, wrapped as red) |
| F8 refusal stops naming the field | 42/46 |

# Files changed

- `server/app/extraction_merge.py` — `_parse_numeric`, `_coerce_numeric`,
  `MalformedNumericError`, `NumericRangeError`, `validate_numeric_fields`,
  `validate_signal_value`; validation wired into `emit_observations`; emission coercion
  switched to the honest parser; stale docstring claims about the N/A quirk corrected.
- `server/app/field_registry.py` — `NUMERIC_SI_FIELDS`, `SIGNED_SI_FIELDS`,
  `DATESTR_SI_FIELDS`.
- `server/app/extraction_client.py` — the boundary call in `extract_many`.
- `server/app/writes.py` — `overwritesignal` guard generalised from docRiskScore-only;
  `save` guards changed numeric fields in the incoming blob.
- `server/tools/test_malformed_numerics.py` — new, 46 checks.
- No migration: the contract is enforcement, not schema. Nothing under
  `server/app/simulation/` touched; no stored data altered; production not inspected.

# Still open

- **Unit/scale contracts for percents and scores** (0..1 vs 0..100) remain undeclared; this
  guard deliberately does not invent them.
- Values entering through entry points 3 and 4 are stored as sent once they pass (e.g. the
  string `"$1,200"` in the legacy blob) — the legacy record keeps client formatting; only the
  contract is enforced there, not normalisation.
- D3 (wall-clock cutoff fallback) unchanged, as before.
