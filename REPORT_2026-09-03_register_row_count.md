# Run 126 — the register states its own row count, and a short register is refused

**NO MIGRATION WAS ADDED. `SIMULATION_VERSION` MOVED `sim-2026.09-v65` → `sim-2026.09-v66`,
because this run changes production behaviour: a document whose model under-read a register no
longer assembles at all, where under v65 it assembled short and banded on a partial population.**

- Starting commit `e4a263e` (`origin/main`), `git status --porcelain` empty.
- Ending commits `1dcb55b` (the instrument) and `94d4312` (three recorded fixtures).
- Tree clean at the end. Migration head `0033_recognition_matches`, unchanged.
- No model call was made or simulated. There is no key in this environment
  (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY` all absent) and `StubExtractor`
  refuses an unrecorded sha256 rather than inventing an extraction. What served in a model's
  place: constructed replies of exactly the shape `parse_json_response` returns, driven through
  `validate_register_row_counts`, `extract_many.run`, `describe_json_truncation`,
  `parse_json_response`, `extraction_contract_fingerprint` and the two provider clients' own
  truncation branches. Every count below names its fixture.

---

## Stated plainly, at the top

**Which registers are now protected — nineteen**, on nineteen document types:

`baseline_curve_json`, `change_events_json`, `disputes_json`,
`environmental_corrective_actions_json`, `environmental_requirements_json`,
`lookahead_activities_json`, `milestones_json`, `modifications_json`, `procurement_items_json`,
`quality_requirements_json`, `reference_class_json`, `resource_profile_json`,
`schedule_calendar_json`, `schedule_network_json`, `subcontractor_ratings_json`,
`submittal_decisions_json`, `trade_attribution_json`, `trade_denominators_json`,
`weather_events_json`.

**Which are deliberately excluded — eight**, each for a reason in the code:

| Field | Reason |
|---|---|
| `open_critical_ncr_json` | absent = NOT TESTED, `[]` = tested and did not hold (`documents.py:2225-2237`) |
| `hold_point_or_turnover_blocking_ncr_json` | same |
| `ncr_open_past_contractual_closure_json` | same |
| `rejected_critical_or_long_lead_late_json` | same (`documents.py:2179-2186`) |
| `rejected_blocking_past_deadline_json` | same |
| `critical_quality_failures_json` | excluded with the five above for the same prompt-pressure reason — see the finding below |
| `submittal_disposition_legend_json` | a JSON **object**, the register's disposition legend, read with `isinstance(_legend, dict)` at `documents.py:2172`. A row count of a mapping counts nothing |
| `schedule_calendars_json` | a list of calendar **names**, not rows. `documents.py:2076` stringifies it into `stated_calendar_names` and the code beside it says the name "is a label and is never read as a definition". Nothing bands on its length. The calendar *definitions* (`schedule_calendar_json`) **are** counted |

The override tables were excluded because asking the model for a row count on them invites the
answer `0` with `[]` returned, where the honest answer was to **omit** the field — and that
collapses "not tested" into "tested, did not hold", which A4.3 and A4.4 report differently.

**Can an under-read register still assemble as a complete one anywhere?** For the nineteen
counted registers, no: `extract_many.run` refuses the whole document before any `Document` row
exists, and `documents.py` persists only results whose `ok` is True. For the eight excluded
fields, **yes, and knowingly** — they are read as a boolean "did the document designate any
row", so an under-read that still leaves one row changes nothing, and one that empties the array
turns a True into a False. That residue is stated here rather than closed, because closing it
costs the tested/not-tested distinction, which is worth more. One further residue is real and is
named in Finding 1 below: the check is a contract with the model, and it can only be enforced
against a model that answers.

---

## 1. What was checked against the code, and where the briefing was right

The owner's pre-checked facts held, with one correction and one refinement.

- `len(ALL_FIELDS) == 114` — confirmed, and it is **still 114**: see §3.
- 19 document types carry at least one `*_json` field; 13 carry more than one — confirmed by
  execution over `_EXTRACTION_FIELDS`. 27 distinct `*_json` fields in total.
- Refusal site — confirmed. `extract_many.run` is at `extraction_client.py:1051`;
  `validate_doc_risk_score` at `:1075` and `validate_numeric_fields` at `:1090`; the
  `except Exception` that converts a raise into the per-file `{ok: False, error}` shape follows.
  `documents.py` persists only `ok: True` results, so a refusal leaves nothing behind.
- The two truncation defences — **`ai_provider.py:318`** (`stop_reason == "max_tokens"`,
  `AnthropicClient`) and **`ai_provider.py:368`**, not `:371`, (`finish_reason == "length"`,
  `OpenAICompatClient`). A three-line drift in the briefing, no consequence.
- Readers legitimately drop rows — confirmed at four sites, so **`len(parsed_array)` pre-read is
  what is compared**: `documents._json_rows` (`documents.py:375-390`) drops a non-object row;
  `compliance_register.read_requirement_rows` (`:200-202`) and `read_critical_failure_rows`
  (`:335-346`) drop the same; and `trade_attribution_json` drops a row printing no
  `record_reference`, counting it in `rows_unusable` (`extraction_fields.py:875-877`). Comparing
  a post-drop count would refuse documents for a fault the platform already reports honestly.
- The `unreadable_fields` / `NumericRangeError` split — confirmed at
  `extraction_merge.py:512-548`. This run takes the **raise** side, for the reason the code
  itself gives there: the Run 80 override is about a field that *cannot be read*, and an
  under-read register can be read perfectly. It is simply a smaller population than the reply
  says it is, and wrong in the reassuring direction.

---

## 2. The field shape, and why one object field

The count must be **per register**: thirteen of the nineteen register-bearing types carry more
than one, `schedule_update` and `submittal_register` carrying six each. Both candidate shapes
give that. One object field, `register_row_counts`, mapping register name → count, was chosen —
for four properties of this code, not for taste:

1. **The reply filter.** `ProviderExtractor.extract_with_confidence` keeps only
   `{k: v for k, v in extracted.items() if k in set(fields)}`. **One** name survives that and
   carries every register's count. Twenty-odd scalar names would each have to be declared on
   every type that asks for its register, and every one of those is another place a per-type
   list and the counted-register set can drift apart.
2. **The prompt.** Run 124 measured output length as the binding constraint on large registers
   (~4004 tokens for the 46-row submittal register). One field name plus one instruction
   paragraph is a fixed cost on every call; a scalar per register grows the JSON field list the
   prompt prints and needs a separate sentence tying each count to its own array.
3. **The commitment can be ordered.** §4 is the reason this matters more than the other three.
   One object returned as the first key is one thing to instruct and one thing to read.
   Twenty-odd scalars each needing to precede their own array is not instructable at all.
4. **It is inert everywhere else** — verified, not assumed. The numeric contract is a declared
   table (`_numeric_keys_for` = `_NUMERIC_EMISSIONS` + `_EXTRA_NUMERIC_KEYS` + the doc-risk
   pair), so an undeclared field is never parsed as a number. The emission tables are declared.
   `information_completeness._required_pairs` computes `kept = reaching & declared`, so a
   declared field with no path changes no denominator: `REQUIRED_TOTAL` is unchanged.

**It is deliberately NOT in `ALL_FIELDS`, which stays at 114.** `ALL_FIELDS` is the vocabulary
of figures *a document states* — `build_prompt`'s own reasoning rests on that sentence ("every
name in that list is a total, a date, a rating, a percentage or a count a construction report
states directly"). `register_row_counts` is a statement about **the reply**, so putting it there
would falsify that reasoning. Names in `_EXTRACTION_FIELDS` that are not in `ALL_FIELDS` are
long-standing and documented above the table.

**The two lists cannot silently drift.** `extraction_fields.py` carries an executable assert
that every `*_json` field any type asks for is in `COUNTED_REGISTERS` or `UNCOUNTED_REGISTERS`,
so a register added to a type in a later run without a decision **fails the import**. The field
is then added to each type by code reading the same `COUNTED_REGISTERS` the validator reads, so
the prompt and the check cannot disagree about which types carry it. It is inserted **first**.

---

## 3. What the model is told — the sentence this run turns on

Written in `build_prompt`, issued only to types that ask for at least one counted register, and
naming only the counted registers actually in that type's field list. As issued for
`inspection_report`:

> `register_row_counts` **MUST BE THE FIRST KEY** of the JSON object you return, written before
> any register array. It is a JSON object stating, for each of the register fields listed here
> that this document contains a table for, the **NUMBER OF ROWS YOU ARE ABOUT TO RETURN** in
> that register: `quality_requirements_json`, `trade_attribution_json`,
> `trade_denominators_json`. For example: `{"quality_requirements_json": 26}`. State the count
> for a register only where you are returning an array for it, and state it for EVERY register
> you return an array for, including one you return as an empty array. **THE NUMBER IS A
> STATEMENT ABOUT YOUR OWN ANSWER.** It must equal the number of rows the document prints in
> that table, and it must equal the number of objects you actually put in that array — these are
> the same number, and there is no answer in which they differ. Do not count the rows in the
> document and then return fewer of them; do not stop a register early, summarise it, sample it,
> abbreviate it or return only the rows you judge important; and do not write the count to match
> a shortened array after the fact. If a register is long, return every row of it anyway. Where
> the document has no such table, return null for that register and omit it from
> `register_row_counts` entirely.

**BEFORE, NOT AFTER, AND THIS IS THE WHOLE INSTRUMENT.** A count written *after* the arrays is
worth nothing. Generation is left-to-right and autoregressive: a model that has already closed a
register at eighteen rows can read its own output and write `18`, and the check then agrees with
itself forever. That is a check that cannot fail, which by the owner's own standing rule is
worse than no check. Stated **first**, the count is a commitment made while the document is
being read and before a single row has been written, and closing the array early then
contradicts a number already on the page. This is why `register_row_counts` is also inserted
first in every type's field list — the JSON array the prompt prints names it before any
register, so the ordering the instruction asks for is the ordering the field list already shows.

**It is a statement about the reply, not about the document, and the instruction says so in both
directions.** The number must equal what the document prints *and* what the answer returns, and
the sentence "these are the same number, and there is no answer in which they differ" removes
the escape of counting twenty-six and returning eighteen. What to do instead of shortening a
register is stated positively — return it whole — because an answer that genuinely runs out of
room is caught by the truncation defences, which report a fixable fault, whereas a quietly
shortened register reports nothing at all.

---

## 4. The check

`extraction_merge.validate_register_row_counts(extraction, *, filename=None)` →
`RegisterRowCountError` (a `ValueError`, beside `NumericRangeError`). Called at
`extract_many.run`, immediately before `validate_numeric_fields`.

It compares `len(the parsed array)` — pre-read, per §1 — against the count the same reply
states. A JSON string of an array is accepted, because `documents._json_rows` accepts one.

Four faults refuse, and the fifth case passes:

- **SHORT** — stated 26, returned 25. The failure the instrument exists for.
- **LONG** — stated 26, returned 27. **Refused, and for a reason rather than for symmetry.**
  One of the two numbers is wrong and the reply does not say which, so accepting the array would
  be choosing. Accepting the longer array would also make the contract one-sided, and a
  one-sided contract is satisfiable by stating a low count and returning whatever was produced —
  the check that cannot fail, again. An over-return is also the shape row fabrication takes.
- **MISSING** — an array returned with no count stated for it. Refused: this is exactly the
  shape an ignored instruction takes, and a register carrying no count has no defence at all.
- **CONTRADICTORY** — a count of *n* > 0 stated for a register no array was returned for. A
  stated `0` agrees with "no rows returned" and passes; any other number is a reply claiming
  rows it did not hand over. A non-integer or negative count refuses, and a boolean is not read
  as a count of one.
- **NOT A FAULT** — a register returned as `null` (the document has no such table) needs no
  count and is skipped; the eight excluded fields are never looked at; a count stated for a
  field that is not counted is ignored, because refusing on it would refuse a reply that
  volunteered more than it was asked for.

The refusal names the document, the register, the count stated and the count returned, in the
house style of `TruncatedResponseError`:

> the extraction in inspection-march.pdf states that `quality_requirements_json` holds 26 rows,
> but the answer returned 25: it stopped short of the register it said it was returning. A
> register that is not the size the reply claims cannot be read as the whole population, and the
> figures drawn from it would be measured against the wrong number of rows. Nothing was stored
> for this document and no figures from it were used. Re-run the extraction.

---

## 5. The four proof obligations — `tools/test_run126_register_row_count.py`, 44/44

A **check script**, not a pytest module, per `server/tools/` convention. Run as
`cd server && python tools/test_run126_register_row_count.py`. Every fault is introduced,
observed, and removed.

**Fixtures.** `QUALITY_26` — an inspection report's `quality_requirements_json` at 26 rows, the
register size Run 124 measured the output budget against; states 26, returns 26.
`QUALITY_26_SHORT_BY_ONE` — the same reply with the last row removed and the count untouched.
`QUALITY_26_LONG_BY_ONE` — a 27th row added, count untouched. `QUALITY_26_NO_COUNT` — the array
with the count field absent. `SUBMITTAL_46` — the 46-row submittal register Run 124 measured at
~4004 tokens, carrying its siblings in the three shapes that matter: the legend as an **object**,
one override table as `[]`, one override table absent.

1. **A correct register passes.** `QUALITY_26` (26/26) accepted. `SUBMITTAL_46` (46/46, plus a
   legend object, an `[]` override and an absent override) accepted. An excluded register with
   no count stated passes untouched — proven, not merely unchecked, because the tested /
   not-tested distinction dies if it does not. A register returned as `null` needs no count.
2. **Short by ONE row is refused.** `QUALITY_26_SHORT_BY_ONE` — 26 stated, 25 returned. Refused,
   and the message carries the filename, the register, `26 rows` and `returned 25`. **Restoring
   the row makes the same reply pass again.** Proven twice: at the function, and at the real
   boundary through `extract_many.run` with a `StubExtractor` — `ok=False`,
   `extraction=None`, and the row-count sentence in the PM-visible `error`; with the row
   restored, `ok=True`.
3. **Longer than stated is refused.** `QUALITY_26_LONG_BY_ONE` — 26 stated, 27 returned, refused
   with "it went beyond the register it said it was returning". The reasoning is in §4: it
   **should** refuse. The other two contradictions (array with no count; count with no array)
   refuse with their own sentences.
4. **Both existing truncation defences still fire, unchanged.** Re-established, not assumed:
   `AnthropicClient.complete` raises `ProviderTruncated` on `stop_reason: max_tokens`
   (`ai_provider.py:318`); `OpenAICompatClient.complete` raises it on `finish_reason: length`
   (`:368`); the 26-row register cut off inside its ninth row still reaches
   `describe_json_truncation` ("cut off while writing the value of `'Item'`") and still raises
   `TruncatedResponseError` through `parse_json_response`, never the row-count check — a
   truncated reply does not parse, so it cannot reach it. A complete reply is still not called
   truncated.

**Plus the lists themselves**, as executable checks: every `*_json` field any type asks for is
ruled on (27 fields = 19 counted + 8 excluded); the lists do not overlap; each of the six
override tables is excluded by name; the legend and the calendar-name list are excluded and the
calendar definitions are counted; the count field is asked of exactly the types carrying a
counted register (19), is the first field asked for on each, and is not asked of a type with no
counted register.

---

## 6. The restale, re-proved — and it is narrower than expected

`extraction_contract_fingerprint` is the sha256 of the exact prompt issued today, so adding the
field and the paragraph moves it. Measured at `e4a263e` and here:

| type | before | after | |
|---|---|---|---|
| `inspection_report` | `c3a32e0ab1fb` | `4903405a3f0c` | moved |
| `submittal_register` | `a1a72d970b66` | `d793fa8466b7` | moved |
| `schedule_update` | `d37a71d9316d` | `46eda46b78aa` | moved |
| `ncr_log` | `e6d629e8a596` | `fd0635956445` | moved |
| `risk_register` | `d195c7cb63b5` | `d195c7cb63b5` | **unchanged** |

**The restale is scoped to the nineteen register-bearing types, not to every cached extraction.**
A type that asks for no counted register gets a byte-identical prompt and its stored extractions
are still served from cache. The order anticipated a whole-corpus restale; the measured cost is
smaller. These values are pinned in the check script so a later prompt change is visible.

---

## 7. Regression sweep

All 191 `tools/test_*.py` were run against `e4a263e` (a git worktree) and against this tree,
each with its own freshly-migrated throwaway SQLite database. **The two sweeps differ in nothing
except the new script**, after the fixture commit.

Three scripts regressed on the first sweep and the check was right about all three: each hands
`StubExtractor` a recorded extraction carrying a register with no `register_row_counts` beside
it — the shape an ignored instruction takes. A recording stands in for a model reply, so the
recordings now state the count, written from `len()` of the rows above so a fixture's count
cannot drift from its own rows: `test_run87_compliance_registers.py` (`QUALITY_ROWS`, `ENV_ROWS`,
`ENV_ROWS[:3]`), `test_run86_lookahead_and_risk_docx.py` (`_ROWS`),
`test_schedule_milestones.py` (`P1_TABLE`, `P2_TABLE`). All three now match `e4a263e` exactly:
run87 exit 0, run86 15/16 (its one pre-existing A2.8 calibration failure),
schedule_milestones 77/78.

`tools/test_run34_version_boundary.py` — the script to run when the stamp moves — **18/18**.
`tools/test_extraction_prompt.py` 209/209. `tools/test_run85_extraction_contract.py` 12/12 and
`tools/test_docx_extraction.py` 42/42 against a freshly-migrated database.
`tools/test_run22_production_tree_completeness.py` fails 44/48 **identically at `e4a263e`** — a
stale pinned manifest naming thirty files added and three removed since it was pinned, unrelated
to this run. `tools/test_run34_holdout_provenance.py` fails on the known pre-existing
`portfolio_health` ImportError.

---

## 8. The three findings the owner most needs

**1. This is a CONTRACT WITH THE MODEL, and it cannot be proved against a model here.** Every
proof in §5 drives constructed replies, because there is no key and no model call may be
simulated. What is proven is that the check refuses the three wrong shapes and accepts the right
one. What is **not** proven, and cannot be proven in this environment, is that the extraction
model complies with the instruction — and the check refuses an array returned with no count, so
a model that ignores the paragraph refuses **every register-bearing document**. That is the
right direction to fail in (loudly, at upload, in the PM's "Extraction failed" dialog, rather
than assembling short and calming a band), and it is deliberately not softened, because
softening it restores the exact hole Run 125 found. **But it should be watched on the first real
upload of each register-bearing type after deployment.** If the model omits the count in
practice, the fix is the prompt, not the check.

**2. `critical_quality_failures_json` does NOT carry the absent-vs-empty semantics the order
attributes to it.** The other five override tables do, plainly, at `documents.py:2179-2186` and
`:2225-2237` (`if ex.get(field) is not None:` guards the write). But
`critical_quality_failures_json` has exactly one call site, `documents.py:1937-1939`, which
calls `compliance_register.read_critical_failure_rows` unconditionally, and that reader returns
`[]` for a non-list — so **absent and `[]` already collapse to the same value** on that path,
and `canonical_v6` reads `structure.get("critical_quality_failures") or []` downstream. It is
excluded anyway, and with the other five, for the *prompt-pressure* reason rather than the
reader reason: naming it in the count instruction beside the five would invite a `0`-and-`[]`
answer on all six. The distinction is recorded in the code so the next reader does not mistake
the reason. **If the owner wants that field's absence to mean "not tested", the reader needs
changing — Run 126 did not change it.**

**3. The excluded eight are a stated, accepted residue.** For those, an under-read register can
still assemble. It matters less than it sounds — six of them are read only as "did the document
designate any row at all", so an under-read that still leaves one row changes nothing — but an
under-read that empties one of those arrays flips a designated override from True to False, in
the reassuring direction, undetectably. Closing it costs the tested / not-tested distinction,
which is worth more, so it is left open and named here rather than closed quietly. The legend
and the calendar-name list carry no such risk: one is a mapping, the other a list of labels
nothing bands on.

---

## Ledger

- `git status --porcelain` before the first commit:
  `M server/app/extraction_client.py`, `M server/app/extraction_fields.py`,
  `M server/app/extraction_merge.py`, `M server/app/simulation/models.py`,
  `?? server/tools/test_run126_register_row_count.py` — only the intended files.
  (Seven `code_audit/run10_*.csv` files were rewritten as a side effect of running the sweep's
  own scripts; they were `git checkout --`'d back before any commit and are not in either
  commit.)
- `git status --porcelain` before the second commit: the three fixture scripts, only.
- `git add` by explicit path throughout. No `git add -A`, no `git add .`.
- `DATABASE_URL` pointed only at throwaway SQLite files in the scratchpad. Production Postgres
  was never contacted. No key was printed or committed.
- Nothing under `server/app/simulation/` was modified except `SIMULATION_VERSION` and its
  history, as the order requires and as this change to production behaviour demands.
