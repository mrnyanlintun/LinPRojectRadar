# Run 125 — an under-read register: the comparison is unsound for the demonstrated case, and the run stops before building it

`SIMULATION_VERSION` DID NOT MOVE. It stands at `sim-2026.09-v65`. Nothing under
`server/app/simulation/` was touched. No production code changed at all: this run establishes
A, B and C, finds C.3 fatal, and, on the order's own instruction, stops rather than wiring a
comparison that would refuse correct documents.

---

## The plain answer, at the top

**Yes. An under-read register can still assemble as a complete one, on every register structure
in the contract, and this run closes none of them.** The demonstration reproduces exactly as
Run 124 §D.2 recorded it. What this run establishes is *why the proposed fix cannot be built as
specified*: on the demonstrated case — `quality_requirements_json` against `items_inspected` —
the two figures count **different populations**, by the prompt's own words, by the reader's own
docstring, by Run 87's own comment and by `canonical_v6`'s own use of the scalar. A comparison
between them would refuse correct documents.

The gap remains open for **all eighteen** register structures:

`quality_requirements_json`, `submittal_decisions_json`, `procurement_items_json`,
`lookahead_activities_json`, `environmental_requirements_json`,
`environmental_corrective_actions_json`, `schedule_network_json`, `change_events_json`,
`disputes_json`, `weather_events_json`, `subcontractor_ratings_json`, `resource_profile_json`,
`baseline_curve_json`, `milestones_json`, `modifications_json`, `reference_class_json`,
`critical_quality_failures_json`, and the two attribution tables
`trade_attribution_json` / `trade_denominators_json`.

Exactly **one** structure in the contract has a same-reply total that the code itself states
counts the register's own population: `disputes_json` against `disputes_recorded`. For that one
the owner has **already ruled the opposite way** — assemble, let the register win, and carry the
disagreement on the record — in `documents.py:2325-2330`. Implementing refusal there would
overturn a settled decision, not close a gap. It is reported, not built.

---

## 0. Provenance of this run

* Starting commit: `bca6858` (Run 124), `= origin/main`.
* `git status --porcelain` at start: **empty**.
* Migration head: `alembic/versions/0033_recognition_matches.py`.
* `SIMULATION_VERSION`: `sim-2026.09-v65` at `server/app/simulation/models.py:1008`, unchanged.
* **No model key.** `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY` all absent;
  `build_extractor` (`extraction_client.py:998`) therefore returns `StubExtractor`, which raises
  on an unrecorded sha256. **No model call was made and none was simulated.** Everything below
  was established by reading the code and by driving `describe_json_truncation`,
  `parse_json_response`, `read_requirement_rows` and `extraction_contract_fingerprint` directly
  with constructed payloads — the same technique as Run 124 §D.

### The owner's briefed facts, checked

Every one held. `SIMULATION_VERSION = "sim-2026.09-v65"`; migration head `0033`;
`validate_numeric_fields` at `extraction_merge.py:512` with the docstring as quoted;
`_EXTRACTION_FIELDS["inspection_report"]` at `extraction_fields.py:506-517`; `StubExtractor`
raising on an unknown hash; `_WIRES = {"anthropic": AnthropicClient, "openai":
OpenAICompatClient}` at `ai_provider.py:373` with the `stop_reason == "max_tokens"` test at
`ai_provider.py:318` and the `finish_reason == "length"` test at `ai_provider.py:371`. Nothing
in the briefing was found false.

---

## 1. The finding reproduced, against the code

Driven at `bca6858`, no code modified. Fixture: constructed 26-row and 18-row
`quality_requirements_json` payloads, both stating `items_inspected: 26`
(scratchpad `d2.py`; not committed).

```
CONTROL complete 26
  describe_json_truncation -> None
  parse_json_response      -> ACCEPTED
  read_requirement_rows    -> 26 rows
  items_inspected in reply -> 26
UNDER-READ 18
  describe_json_truncation -> None
  parse_json_response      -> ACCEPTED
  read_requirement_rows    -> 18 rows
  items_inspected in reply -> 26          <-- assembles, bands, stores. Nothing objects.
MID-ARRAY CUT
  describe_json_truncation -> the model's answer was cut off while writing a field name,
                              after 'Result'; the name it had reached was 'Criticali'
  parse_json_response      -> TruncatedResponseError
```

Run 124 §D.2 is confirmed. The self-closed array is indistinguishable from a complete answer at
every defence the pipeline has, and `extraction_merge` carries no row-count validation of any
kind (`grep` over `extraction_merge.py`: the only counting is `validate_numeric_fields`'s
per-scalar range check).

---

## 2. A — which register structures carry a stated total in the same reply

Derived by executing over `_EXTRACTION_FIELDS` (`extraction_fields.py`), not by reading prose.
Eighteen document types carry a `*_json` register; here is every one against the scalars asked
for in the same call.

| Register | Same-reply candidate total | Verdict |
|---|---|---|
| `quality_requirements_json` (inspection_report) | `items_inspected` | **Same reply, DIFFERENT population.** See §4. Not usable. |
| `quality_requirements_json` (quality_audit_report) | *none* — the type asks `total_findings`, `critical_findings`, `deficiency_count`, `audit_score`, `inspections_performed`, `active_work_packages`. A findings count is not a requirement count; `inspections_performed` is A4.4's denominator, explicitly a different one (`extraction_fields.py:144-147`). | **No stated total.** Uncoverable. |
| `submittal_decisions_json` | `submittals_total` | **Same reply, DIFFERENT population.** `extraction_fields.py:118-123` and the prompt at `extraction_client.py:457-464`: the register is **one row per DECISION**, revisions kept separate and explicitly not merged; `submittals_total` counts **submittals**. Rows ≥ total, by construction. Not usable. Compounded by `submittal_reporting_period`, which the order's C.2 already names. |
| `procurement_items_json` | `long_lead_items_total`; `on_schedule` + `at_risk` + `delayed` | **Same reply, DIFFERENT population.** Prompt at `extraction_client.py:501-511`: one row per **monitored item**, and the model is told in terms *not* to decide whether an item is long lead. The register is the superset; `long_lead_items_total` and the three state counts partition the long-lead **subset**. Not usable. |
| `lookahead_activities_json` | `activities_planned` | **Same reply, RELATION UNSTATED.** Nothing in the prompt, the reader or any comment equates `activities_planned` with the look-ahead table's row count. Wiring it would be inventing an input. Not usable without an owner ruling. |
| `environmental_requirements_json` | `permit_conditions_total` | **Same reply, DIFFERENT population.** Prompt at `extraction_client.py:415-423`: the table is "permit-condition, **observation or corrective-action**" rows — three populations in one array; `permit_conditions_total` counts only the first. Rows ≥ total. Not usable. |
| `environmental_corrective_actions_json` | *none* | **No stated total anywhere.** Uncoverable by this approach. |
| `schedule_network_json` | `activities_planned` | **Same reply, RELATION UNSTATED.** As `lookahead_activities_json`. Additionally the network table is the schedule export's activity rows, which need not equal a stated planned-activity count on the same update. Not usable. |
| `change_events_json` | `change_order_count` | **Same reply, DIFFERENT population.** `extraction_fields.py:355`: `change_order_count` is the count of change ORDERS. `change_events_json` is the change EVENT register — events, priced or not, executed or not. Also shares the document type with `modifications_json`, so one scalar cannot govern two registers. Not usable. |
| `modifications_json` | `change_order_count` | **Ambiguous — two registers, one scalar.** Not usable. |
| `disputes_json` | `disputes_recorded` | **Same reply, SAME population, stated so by the code.** `extraction_fields.py:137-140`: "a stated total is the minutes' own count of it". **The owner has already ruled the opposite of refusal here.** See §5. |
| `weather_events_json` | `weather_days_lost` / `weather_days_discussed` / `weather_days_claimed` | **No count of events.** These count DAYS, and `extraction_fields.py:524-533` is emphatic that a count is not the record. Uncoverable. |
| `subcontractor_ratings_json` | *none* | **No stated total.** Uncoverable. |
| `resource_profile_json` | *none* | **No stated total.** Uncoverable. |
| `baseline_curve_json` | *none* | **No stated total.** Uncoverable. |
| `milestones_json` | *none* (on either `schedule_update` or `monthly_report`) | **No stated total.** Uncoverable. |
| `reference_class_json` | *none* | **No stated total.** Uncoverable. |
| `critical_quality_failures_json` | *none* — it is by definition a designated **subset** | **Uncoverable, and correctly so.** |
| `trade_attribution_json`, `trade_denominators_json` | *none* on any of the eleven types carrying them | **No stated total.** Uncoverable. |

**Reach of the proposed fix: one structure of eighteen** would have been checkable
(`disputes_json`), and that one is already settled the other way. The approach does not cover
the corpus. Of the five recurring multi-row register document types the order names, **none**
gains a sound check.

---

## 3. B — where the comparison belongs, if one were ever sound

**Validation time, in `extract_many.run(job)` (`extraction_client.py:1068-1101`), beside
`validate_numeric_fields`.** The code makes this natural and the alternative unnatural, for
three reasons read off the code:

1. **It is before any `Document` row exists.** The comment at `extraction_client.py:1068-1076`
   states the design in terms: "Refusing here, before the caller writes a Document row, is what
   makes 'no out-of-range value reaches storage' true rather than merely checked later:
   documents.py only persists results whose `ok` is True, so a refusal leaves nothing behind to
   clean up."
2. **The refusal channel already exists and already reaches the PM.** Any exception raised in
   `run(job)` is converted by the `except Exception` at `extraction_client.py:1097` into the
   per-file `{ok: False, error}` shape the "Extraction failed" dialog renders. That is the same
   channel `TruncatedResponseError` already travels. A refusal here has the shape the order asks
   for at implement-item 2, for free.
3. **The `documents.py` assembler is structurally the wrong place.** Assembly at
   `documents.py:1897-1938` runs after storage, has no refusal vocabulary, and — as Run 122
   recorded and this run confirms at `documents.py:1922-1935` — is built on *silent* precedence
   (longest-register-wins). Raising from inside it would leave a stored `Document` row and a
   half-written structure.

**Which of the two precedents an under-read belongs with:** the **raise** side.
`validate_numeric_fields`'s own docstring splits them — "returns the list of fields that could
not be read ... raises `NumericRangeError` for a value that reads as a number but sits outside
the field's permitted range" — and gives the reason for the split at `extraction_merge.py:534-542`:
out-of-range refuses because "the repair would be in the reassuring direction, which is the one
nothing downstream can trace". An under-read register is exactly that: readable, well-formed,
and wrong in the reassuring direction, with `longest-register-wins` able to propagate the error
across documents. It is not an unreadable field. **B is settled: raise, at validation.** This
section stands as the site specification for whoever implements a sound check later.

---

## 4. C — what the comparison must tolerate, and the C.3 verdict

### C.1 — reader drops. Confirmed, and the order's instruction is right.
`read_requirement_rows` (`compliance_register.py`) passes an identity-less row through
deliberately — "Dropping it would silently shrink the population the rate is measured over" —
but other readers do drop: `documents.py:2333-2336` drops a dispute row with no id, and Run 122's
procurement/submittal/change-event drops are in the same shape. Any count compared must be the
count the model **returned** (`len(json_array)`), never the post-read count.

### C.2 — legitimate subsets. Confirmed.
`submittal_reporting_period` (`extraction_client.py:463`) and `quality_register_period`
(`extraction_fields.py:511`) both scope a register to a window narrower than a document's
lifetime totals. Any check must tolerate this, and cannot distinguish it from an under-read.

### C.3 — THE VERDICT: `items_inspected` and `quality_requirements_json` DO NOT COUNT THE SAME POPULATION. The comparison is unsound. **STOP.**

Four independent places in the code say the register is a **superset** of the inspected items:

1. **The prompt itself** (`extraction_client.py:394-405). It asks for the "requirement,
   inspection-item, checklist or audit-findings table (one row per item assessed)" and then, in
   the same breath, instructs: *"do not mark an item assessed that the document leaves blank or
   marks pending"*. Rows therefore exist for items that were **not** inspected.
2. **Run 87's own comment** (`extraction_fields.py:498-502), which the briefing quotes: the
   register is "one row per inspection item, with whether it applied, **whether it was
   checked**, and whether it passed". A column recording *whether* an item was checked exists
   only because unchecked items are on the register. `items_inspected` counts only the checked.
3. **The reader's docstring** (`compliance_register.py:35-52) and its `_NOT_ASSESSED`
   vocabulary (`not assessed`, `not inspected`, `pending`, `tbd`, `deferred`, `scheduled`,
   `awaiting`, `future`, …), plus "not applicable" rows the canonical function skips. Both
   classes of row are **on the register and not inspected**, by explicit design.
4. **`canonical_v6._first_pass_acceptance`** (`canonical_v6.py:925-986`) uses `items_inspected`
   as the denominator of a *different measure entirely* — first-pass acceptance — while A6.1's
   denominator is `ApplicableAssessed`, derived from the register rows and strictly smaller than
   them. `documents.py:1917-1938` stores the two side by side on one structure as **two
   denominators**, and never equates them.

So under the code's own semantics: **register rows ≥ items_inspected**, with equality only when
no row is pending and none is not-applicable.

**An equality check would refuse correct documents.** That disposes of `rows == items_inspected`.

**The one-sided test (`rows < items_inspected` → refuse) is also unsound**, and this is the part
worth reading. Two things kill it:

* **The platform's own sealed fixture contradicts the code.**
  `tools/test_run87_compliance_registers.py:85-153` — the only worked example of a correct
  inspection report in the repository — states `items_inspected: 10` against a **10-row**
  `QUALITY_ROWS`, whose own header reads *"10 rows: 1 not applicable, 1 pending (assessed = No),
  8 applicable and assessed"*. Under the code's semantics that report should state
  `items_inspected: 8`. Under the fixture's authoring, `items_inspected` **is** the register row
  count. **The repository holds two incompatible meanings for this field**, and neither is
  written down as the contract. A refusal built on either would be a refusal built on a coin
  flip. *(Where a report and the code disagree the code wins; here the disagreement is between
  the code and a sealed fixture, and the honest statement is that the contract is undefined.)*
* **The common, correct inspection report is refused.** An inspection report that states
  `items_inspected: 200` and prints only its **deficiency log** — twelve rows — is an ordinary
  construction document. Run 87 designed for exactly this: *"Where the document states less than
  a readable table, no register is assembled and A6.1 goes on abstaining"*
  (`extraction_fields.py:504-505`). A `rows < items_inspected` test refuses that document whole
  — losing its `items_passed`, `deficiency_count`, `critical_deficiency_count`, first-pass
  figures and trade attribution with it — where the platform's designed behaviour is to abstain.
  Exempting `rows == 0` does not save it: twelve rows is not zero.

The order is explicit and this run follows it: *"if the two figures count different things, say
so and stop rather than wiring a comparison that would refuse correct documents."* **They count
different things. This run stops.** Nothing was implemented; no false-refusal path was
introduced.

---

## 5. The one same-population case, and why it is not a gap to close

`disputes_json` / `disputes_recorded` is the only pair in the contract the code itself states
counts one population: *"a stated total is the minutes' own count of it"*
(`extraction_fields.py:139-140`). And the assembler already **detects and handles the
disagreement**, under an explicit precedence ruling (`documents.py:2325-2330`):

> "Where they print both and disagree, the register wins, because the register is the thing
> recorded and the total is a statement about it — and the disagreement is carried on the record
> so A4.7 can say so rather than hiding it."

The code implements it: `_drec["stated_total"] = _dstated` is carried beside
`dispute_count = len(_disputes)` (`documents.py:2371-2372`). This is a deliberate
assemble-and-disclose decision, already taken, on the only pair where a comparison is sound.

**This is the single most consequential thing in this report.** The order's premise is that
refusal is right and disclosure is wrong. On the one structure where the comparison is
provable, the platform already chose disclosure and wrote down why. Changing it to refusal is an
owner decision, not a defect fix, and this run does not take it. It is also worth the owner
knowing that Run 123 §7.5's "unread surface" argument applies to that disclosure too: the
`stated_total` is carried, and whether A4.7 or any surface actually *reads* it was not verified
by this run.

---

## 6. Implement-item 4 — the existing truncation defences, verified

No code changed, so nothing could displace them; verified anyway, by execution and by reading.

* **`describe_json_truncation` fires on a mid-array cut.** Demonstrated in §1: it names the
  field and the partial key. `parse_json_response` converts it to `TruncatedResponseError`.
* **Both provider wires test the stop signal.** `AnthropicClient` raises `ProviderTruncated` on
  `stop_reason == "max_tokens"` (`ai_provider.py:318-321`); `OpenAICompatClient` on
  `finish_reason == "length"` (`ai_provider.py:368-371`). `_WIRES` (`ai_provider.py:373`)
  contains exactly those two classes, so no client path lacks the test. `ProviderExtractor._post`
  (`extraction_client.py:781-788`) converts either into `TruncatedResponseError`.
  Run 124 §D.1 re-established, not assumed.

## 7. Implement-item 5 — `extraction_contract_fingerprint`, verified by execution

`extraction_contract_fingerprint` (`extraction_client.py:672-688`) is the sha256 of the exact
prompt `build_prompt` issues, field list included, derived at call time. Proven able to change:

```
inspection_report fingerprint: c3a32e0ab1fb20533ed4252a5cd73a9c73630fb672c598b76bf6c648a4491684
with one char added   : 7ae1e39e6414494b506107e159c8443373ce9fad8aacc25c2c6e525259d46447
restored              : c3a32e0ab1fb20533ed4252a5cd73a9c73630fb672c598b76bf6c648a4491684  (equal to first: True)
```

**Nothing prompt-facing changed in this run, so no cached extraction restales and none
re-extracts.** Stated as verified, not assumed.

---

## 8. What would actually close the gap

Recorded so the next run does not have to re-derive it. None of this was built.

1. **A stated total is the wrong instrument.** It is absent on thirteen of eighteen registers,
   and counts a different population on four of the remaining five. Any fix built on it covers
   almost nothing.
2. **Ask the model for the register's own row count, as a field.** The model that closed the
   array early would still have to state a count, and a count against `len(array)` in the *same
   reply* is a self-consistency check with no population ambiguity at all. It is a
   prompt-and-field-list change, so it restales every cached extraction — once, deliberately —
   and the fingerprint mechanism handles that correctly (§7).
3. **Site B is settled regardless** (§3): raise, in `extract_many.run(job)`, beside
   `validate_numeric_fields`, before any `Document` row exists.
4. **`longest-register-wins` remains the compounding hazard** (`documents.py:1922-1930`,
   `1883-1890`). Until an under-read is detectable, a short register can still displace a
   complete one from another document in the same period. This is independent of any total.

---

## 9. Closing statement

* Starting commit: `bca6858`. Tree clean at start.
* `git status --porcelain` before commit showed **only** `?? REPORT_2026-09-03_register_under_read.md`.
* Ending commit: recorded in the commit that carries this file.
* Migration head: `0033_recognition_matches.py`. **No migration was written; none was required.**
* `SIMULATION_VERSION`: `sim-2026.09-v65`, **unchanged**. No production constant or behaviour
  moved. `server/app/simulation/` untouched.
* No model call was made; none was simulated. `StubExtractor` served and was not invoked.
* **Can an under-read register still assemble as a complete one? Yes — on all eighteen register
  structures. The gap is open, and this run deliberately declined to close it with an unsound
  check.**
