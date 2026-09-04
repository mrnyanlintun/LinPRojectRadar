# Run 135, agent D — selection, assembly and determinism

`SIMULATION_VERSION` DID NOT MOVE. Nothing under `server/app/simulation/` was changed by this
agent.

Branch: `worktree-agent-a5b2a216bedf11d2d`
Starting commit: `6d9899f34d7b08561ccfc7979c1f05389df8f772`
Ending commit: the tip of this branch, which is the commit carrying this report. Its sha cannot
be written inside itself; the commit immediately before it is `9cd3aae`, and the branch tip is
reported by the agent alongside this document.
Migration head: `0033_recognition_matches`, unchanged. NO MIGRATION WAS WRITTEN and none was
required — every change is to reading code, not to a stored shape.
`DATABASE_URL` pointed only at throwaway SQLite files under the run scratchpad. Production
Postgres was never contacted. No production recomputation was run; what one would have to cover
is stated below.

---

## Disposition table

| Finding | Disposition | Attempts | Files changed |
|---|---|---|---|
| H5 — trade-table first-pass aliases | RESOLVED | 1 | `server/app/documents.py` `_TD_COLS` (~2965-2988) |
| M4 — document order undefined | RESOLVED | 1 | `server/app/extraction_merge.py` (~1010-1046), `server/app/documents.py` (imports; `_period_documents` ~505-564) |
| H3 + R3 — qualification's field of view, and sha256 selecting a value | RESOLVED | 1 | `server/app/extraction_merge.py` (~1226-1345), `server/app/documents.py` (`_evidence_qualification`, `_compute_and_store`) |
| H4 — archive filter at one seam only | RESOLVED | 1 | `server/app/documents.py` (`_live_document_ids` + 5 sites) |
| M5 — bare 1 and 0 as a probability | RESOLVED | 1 | `server/app/risk_values.py` (~102-122) |
| `extraction_client.py:829` — dead truncation suffix | RESOLVED | 1 | `server/app/extraction_client.py` (~823-846) |
| `compliance_register._HEADINGS` — duplicated `"status"` | RESOLVED | 1 | `server/app/compliance_register.py` (~77-103) |

Nothing in this agent's scope is BLOCKED, UNRESOLVED AFTER 5, or NOT REACHED. S6 in Group 2
belongs to agent B (`backend/`) and was not touched.

New suite: `server/tools/test_run135d_selection_and_assembly.py`, 48 checks, all passing.
Classified under R4 as an ACTIVE QUALIFICATION TEST: it exercises production readers on
constructed inputs, and its expectations come from the owner's Run 135 order rather than from the
code under test. Its one DB-backed section SKIPS, loudly and uncounted, when `DATABASE_URL` is
unset.

---

## Iteration log

| finding | attempt | change made | proof result | suite | disposition |
|---|---|---|---|---|---|
| H5 | 1 | removed `"inspections_passed"` and `"commitments_met"` from the two `_TD_COLS` alias tuples | total-only document reaches no first-pass column (was 100.0) | run126 44/44, run132 31/31, run87 33/33 | RESOLVED |
| M4 | 1 | added `document_ordering_key`; `ORDER BY doc_type, document_id` plus a Python business-key sort in `_period_documents` | both upload orders give `as_of_day=2026-03-31` (was 03-31 vs 03-10) | run132 31/31, run126 44/44, run87 33/33, drive_run115 22/34 unmoved | RESOLVED |
| H3 + R3 | 1 | `_evidence_qualification` takes `carried`; `_snap_pick`/`_perm_pick` factored into business key + tie set + hash; `unresolved_value_conflicts` added and unioned in | `conflicts: ['originalContingency']` (was `[]`); keys-exhausted disagreement reported, agreement not | run135d 26/26, run132 31/31, run126 44/44, run87 33/33, run127 pass, drive_run115 22/34 unmoved | RESOLVED |
| H4 | 1 | `_live_document_ids` added; applied at three stores and two readers (the third reader goes through `_schedule_snapshot`) | archived `schedule_update` gives 0/0/None/None/0 (was 0/2/2 milestones/2 rows/1 snapshot) | run135d 32/32, run132 31/31, run126 44/44, run87 33/33, run127 pass, drive_run115 22/34 unmoved, drive_run71 15/17 unmoved | RESOLVED |
| M5 | 1 | `_FRACTION` requires a decimal point: `^(0?\.\d+\|1\.0+)$` | `"1"`/`"0"` refuse with the reason `"5"` gives (were 1.0 and 0.0) | run135d 42/42; **test_risk_register_and_notices 127/127 -> 125/127, reported not suppressed**; run86 14/16 unmoved | RESOLVED |
| extraction_client:829 | 1 | removed the always-empty `cut` term | message byte-identical; `describe_json_truncation("")` still None | run126 44/44 | RESOLVED |
| compliance_register | 1 | removed `"status"`, `"closure status"`, `"disposition"` from `_HEADINGS["satisfied"]` | status-only register now `assessed: False`, no `satisfied` (was both True) | run87 33/33 unmoved, run135d 48/48 | RESOLVED |

No finding needed a second attempt. Each was reproduced first, changed once, re-proved, then had
its proof shown able to fail by reintroducing the exact fault and clearing `__pycache__` before
confirming the restore.

---

## H5 — trade-table aliases accept a total where the ladder is first-pass

`server/app/documents.py`, `_TD_COLS` inside `_run69_structures`.

`"inspections_passed"` mapped to `inspections_passed_first` and `"commitments_met"` mapped to
`commitments_met_on_time`. Both headings are TOTALS over every attempt; the ladder they feed is
FIRST OUTCOME ONLY, which `simulation/contractor_factors.py:530-538` states in those words for
A6.4. A total is a superset of the first-pass count, always greater or equal, so a firm banded
favourably on a number answering a different question — and A6 is worst-wins in the required
core, so the favourable direction is the one that survives.

* Before: `_first_of({"Inspections Passed": 100}, ...)` returned `100`; end to end,
  `denominators_by_subcontractor["ACME"]` carried `inspections_passed_first: 100.0`.
* After: the column is ABSENT and the module reaches NOT TESTED honestly.

The stated first-pass headings are untouched and still land ("Inspections Passed First",
"First Pass Inspections", "First Time Pass", "Passed On First"; "Commitments Met On Time",
"Commitments On Time", "On Time Commitments", "Responses On Time"), as does every denominator.

Proof can fail: re-adding `"inspections_passed"` to the tuple returns the check to FAIL with
`inspections_passed_first: 100.0`; removing it again restores the pass.

**Other supersets found in the same list, reported not fixed.** One: `commitments_due` carries the
bare alias `"commitments"`. It is a superset of the same shape, but it sits in a DENOMINATOR,
where a larger value LOWERS the ratio — the unfavourable direction, and therefore not the hazard
H5 names. No other alias in `_TD_COLS` or `_TD_FLAGS` is a superset of the column it maps to; the
remaining bare aliases (`"inspections"`, `"hours"`, `"audits"`, `"scheduled_deliveries"`,
`"planned_packages"` and the rest) are synonyms for the total the column IS.

---

## M4 — document order is undefined

`server/app/documents.py:_period_documents`, `server/app/extraction_merge.py`.

The query carried no `ORDER BY` and returned rows in whatever order the database chose. Four
Run-69 structures walk that list writing last-writer-wins, so two `oac_minutes` differing only in
upload order gave a different `disputeRecord` and a different `as_of_day` — A4.7's duration input
— from the same evidence, against `documents.py:17`'s promise of byte-identical `signalInputs`.

* Before, through `_period_documents` on a migrated throwaway SQLite:
  `A then B: as_of_day=2026-03-31` / `B then A: as_of_day=2026-03-10`.
* After: both `2026-03-31`, and the later-dated document wins although its sha256 is the LOWER of
  the two — the business key decides, not the hash.

### THE ORDER BY CHOSEN

SQL, as a stable base over the columns that exist:

```
.order_by(Document.doc_type, Document.document_id)
```

The FULL business-key order the owner named is applied in Python over the assembled dicts, by
`extraction_merge.document_ordering_key`, because the writer tier is a property of the document
TYPE and the as-of lives inside the extraction JSON — neither is a column, and neither can be
expressed in SQL without denormalising. Ascending, so the most authoritative document sorts LAST
and a last-writer-wins consumer takes it:

1. **writer tier** — `_doc_rank`: baseline (0), ordinary (1), revision (2), so a revision beats
   what it revises;
2. **dated over undated** — undated sorts FIRST and therefore never displaces a dated document;
3. **`as_of`** — `document_as_of`, the same date rule emission uses, so "which document is later"
   has one answer on this platform;
4. **document type** — lexical, declared and readable;
5. **sha256** — LAST and only there. Under R3 a hash may stabilise an order and never select a
   value; two documents reaching that position are identical on every business key above it.

The key is defined once so this seam and the emission ordering cannot drift apart. `_ordered_docs`
was deliberately NOT re-pointed at it: that would change emission order and `assembly_report`
output, which is a separate change with its own proof obligation and is not what M4 asks for.

Proof can fail: replacing `out.sort(key=document_ordering_key)` with a no-op returns the two
upload orders to `2026-03-31` vs `2026-03-10` (IDENTICAL: False).

---

## H3 + R3 — qualification's field of view, and sha256 selecting a value

### H3

`_evidence_qualification` received only the PERIOD'S OWN observations while `select_signal_inputs`,
called four lines earlier from the same function on the same evidence, also received `carried` —
the earlier periods' IDENTITY-field observations. Selection therefore resolved conflicts ACROSS
periods that qualification could not see.

* Before: two `cost_report`s in different periods, same date `2026-03-31`, tier 0,
  `original_contingency` 500,000 vs 300,000 — selected **300,000** on the higher sha256, and
  `material_conflicts: []`. The identical pair inside ONE period reported the conflict correctly.
* After: `material_conflicts` names `originalContingency`, `distinct_values: 2`, `writer_tier: 0`.

Only the conflict scan widens. `effective_date` still derives from the period's own observations
alone (verified `2026-03-31`, unchanged) — it answers "as of when does this period speak", and a
carried document from an earlier period must not be able to date it.

Proof can fail: withdrawing the carried view (`scanned = list(observations)`) returns
`conflicts: []`.

### R3 — what the platform now does when the business keys are exhausted and the values disagree

**IT PUBLISHES A FIGURE AND REPORTS THE DISAGREEMENT. It does not abstain.**

Blanking a field on a contradiction would replace a wrong figure with no figure and take every
module reading it dark — a false refusal, which this programme has repeatedly recorded as being as
much a defect as a false pass, and which `_evidence_qualification`'s own header argues at length.
So the hash still breaks the final tie, the pick is unchanged, and it remains order independent in
both directions (checked for `_snap_pick` and `_perm_pick`). What the hash may no longer do is
settle the disagreement in SILENCE.

**WHERE THE REPORT LANDS:** the period's Category-9 record, on
`signalInputs.evidenceQualification.material_conflicts` — the structure that already exists for
exactly this, and whose REVIEW_REQUIRED assessment is already the platform's declared answer to
documents that contradict each other. Nothing new was invented to hold it.

**How it is made structural rather than incidental.** `_snap_pick` and `_perm_pick` are refactored
into an explicit business key (`_snap_business_key`, `_perm_business_key` — every key they used,
same sequence, same direction, hash excluded), the set of observations tied on that key, and the
hash applied to that tie set. WHAT THEY RETURN IS UNCHANGED. That factoring makes the condition
enumerable, and `extraction_merge.unresolved_value_conflicts` names every field where each kind's
OWN precedence key is exhausted and the values still differ. `_evidence_qualification` takes the
UNION of that with the rule it already applied.

**Why the union is not redundant.** The pre-existing rule stops at tier and latest as-of, so for
SNAPSHOT fields its conflict set is a strict SUPERSET of the hash-decided set — it already covered
those and more. It did NOT cover PERMANENT fields: `_perm_pick` takes the EARLIEST dated
observation while that rule looks at the LATEST, so two documents sharing the earliest as-of and
disagreeing had the hash pick the published value while the rule, looking at a later date where
perhaps only one document speaks, saw a single value and reported nothing. That gap is now closed,
and taking the union rather than replacing the rule means nothing previously reported stops being
reported.

Also checked: values that AGREE at an exhausted key are NOT reported (R3 expressly permits the
hash there); a disagreement the business keys DO settle is not reported as unresolved.

Proof can fail: suppressing the report (`if True:` for `if len(values) <= 1:`) fails "keys
exhausted and values disagree is REPORTED".

---

## H4 — archive filter applied at one seam; three stores and three readers bypass it

`_period_documents` was written as THE ONE SEAM applying the document control's two rules and says
so: "no module can hold a value that came only from an archived document, because the observations
were never emitted". True of the observation path, false everywhere else. Three projection stores
issued their own `Document`/`DocumentUpload` join with NO archive filter at all
(`_persist_schedule_activities`, `_persist_project_risks`, `_persist_project_notices`), and three
readers filtered on supersession alone (`_schedule_snapshot`, `_schedule_display`, and
`_milestone_history` through the first).

Before, one ARCHIVED `schedule_update` on a migrated throwaway SQLite:

```
_period_documents:            []
_persist_schedule_activities: 2 inserted
_schedule_snapshot:           2 milestones at 2026-03-31
_schedule_display:            2 rows
_milestone_history:           1 snapshot          <- A2.7's input
```

After: `0, 0, None, None, 0`. Over-blocking checked: a LIVE `schedule_update` still gives 1
document, 2 activities, a snapshot, a display and 1 history snapshot.

**The filter is not replicated.** `_live_document_ids` calls `_period_documents` and takes the ids
of what survives, so membership of the live set keeps exactly one definition and a rule added there
reaches all seven callers without being remembered.

**One deliberate consequence, stated rather than left to be discovered.** `_period_documents` also
excludes SUPERSEDED documents, so the three stores stop projecting NEW rows for a document a later
upload in the same period replaced — their docstrings had said superseded documents were projected
on purpose. The RETENTION is untouched: no row is deleted or updated in place and everything
already stored stays readable through `a_projectuploadstatus`. What changes is that a store no
longer writes a new row for a document its own readers already refused to read. If the owner wants
superseded documents to keep being projected, that is a one-line widening of `_live_document_ids`,
made there once, rather than three copies of a filter.

Proof can fail: removing the live-set gate from the three stores and from `_schedule_snapshot`
returns "2 inserted / 2 milestones / 1 snapshot" on the archived document.

**A pre-existing failure this fix does NOT clear, reported not suppressed.**
`tools/drive_run71_document_control.py` reads 15/17 on a clean database, IDENTICAL before and after
this change, measured on a clean checkout of the parent commit. Its two failures are "7.1 no module
still holds a value that came only from the archived document" and "7d. selecting a period lists
THAT period's live documents with checkboxes". 7.1 is not a site-specific check:
`drive_run71_document_control.py:333-337` matches ANY numeric leaf of ANY module result against the
withdrawn document's values, so it fails on a coincidental value collision and cannot distinguish
"a module holds the withdrawn figure" from "a module holds that number for another reason".
Repairing it is R4 tooling work in another agent's scope.

---

## M5 — probability parsing accepts bare 1 and 0 while refusing 2 through 5

`server/app/risk_values.py`. `_FRACTION` was `^(0?\.\d+|0|1(?:\.0+)?)$` and matched a bare `"1"`
and a bare `"0"`, reaching `RiskProbability(value=1.0)` and `value=0.0` before the bare-number
refusal further down could see them.

**Does the register reader pass a scale hint? NO.** `risk_register.py:344` passes
`column_is_percent` and nothing else, and `_heading_says_percent` is the only hint that reaches
this parser. There is no basis on which a bare "1" could be told from a 1 of 5, so — as the owner's
order requires — "1" and "0" now refuse exactly as "2" through "5" do, with the SAME reason string.

* Before: `"1" -> RiskProbability(value=1.0)`, `"0" -> RiskProbability(value=0.0)`.
* After: both `ValueRefusal`, reason identical to `"5"`'s.

**A second wrong reading in the same place, corrected by the same change.** The fraction branch is
tested BEFORE the percent-column branch, so on a column headed "Probability (%)" a stated "1" — one
per cent — read as 1.0, CERTAINTY. It now falls through and reads 0.01. `"30"` on that column still
reads 0.3.

Nothing written as a fraction moved: `".4"`, `"0.4"`, `"1.0"`, `"0.0"`, `"0.999"` all still read;
`"100%"` is 1.0; `"1 %"` is 0.01; `"Low"` is still a band; `"1.5"` still refuses.

Proof can fail: restoring the old pattern returns four checks to FAIL, among them "bare '1'
refuses" reading `RiskProbability 1.0` and "a percent COLUMN reads a bare '1' as 0.01" reading 1.0.

### New failure exposed by this repair — DECISION NEEDED

`tools/test_risk_register_and_notices.py` goes **127/127 -> 125/127** on a clean database. The two
failures are at `tools/test_risk_register_and_notices.py:147-148`:

```python
HANDLED = [("30%", 0.30), ("30 %", 0.30), ("30 per cent", 0.30), ("0.3", 0.30),
           (".3", 0.30), ("0", 0.0), ("1", 1.0)]
```

`("0", 0.0)` and `("1", 1.0)` are expectations that encode the defect itself, derived from the
implementation rather than from a specification — precisely what ruling R2 forbids. The correct
repair is to move those two entries to the refusal list and record the Run 135 order beside them as
their source: *"Refuse bare integers where the register states no scale. Reading '1' on a
five-point scale as probability 1.0 is the reassuring direction."*

That file is outside this agent's declared scope (`server/tools/`, except the one new check), so
the failures are REPORTED rather than edited away, per the order's rule 4.

**SMALLEST DECISION NEEDED FROM THE OWNER:** authorise re-pointing those two expectations in
`tools/test_risk_register_and_notices.py:147-148` under R2, citing the Run 135 order. It is a
two-line change and no other check in that suite is affected.

`tools/test_run86_lookahead_and_risk_docx.py` reads 14/16 both before and after — pre-existing,
unmoved.

---

## `extraction_client.py:829` — dead truncation suffix

`cut = describe_json_truncation("")` cannot return anything but `None`: that function's own
`if not saw_value: return None` fires on an empty string before any of its describing runs. So
`(": " + cut if cut else "")` appended nothing on every execution this code has ever had, while
reading as though the message sometimes named where the JSON was cut off. It never did. The message
a caller sees is byte-identical after removal, verified by driving `_post` with a stubbed client
that raises `ProviderTruncated`.

**Removed rather than made reachable, and why.** Making it reachable means carrying the PARTIAL
BODY out on the exception: `ai_provider` has that text in hand at both raise sites
(`stop_reason == "max_tokens"` at `:351`, `finish_reason == "length"` at `:401`) and discards it.
That is a change to the provider boundary's exception contract, not to this line, and
`ai_provider.py` is outside this agent's scope. It would also be a SECOND, INFERRED account of a
fact the provider has already stated authoritatively in `str(exc)` — the comment directly above says
`describe_json_truncation` is the fallback for a caller that never sees `stop_reason`, and this
caller does see it. If the owner wants the cut point named, the place is `ProviderTruncated`, once,
for every caller.

`describe_json_truncation` is NOT orphaned: its live caller is `extraction_client.py:767`, on the
path for a reply that arrived complete and would not parse, where the text is real. run126, which
exercises both truncation branches, stays 44/44.

---

## `compliance_register._HEADINGS` — the duplicated `"status"`

**THREE headings were claimed by two fields, not one.** `"status"`, `"closure status"` and
`"disposition"` all appeared under BOTH `satisfied` and `status`. The order names the first; the
other two are the same defect on the same rows and were removed with it.

`_pick` walks the table field by field, so a register printing only one of those columns had it read
TWICE — once as free descriptive text under `status`, which is harmless, and once through `_tri` as
the row's two-state OUTCOME, which is not. `_row` sets `assessed = satisfied is not None` where the
document printed no assessed column, so one ambiguous heading decided both.

**Which field keeps them: `status`.** A status is a WORKFLOW STATE; a satisfaction is a CONFORMANCE
OUTCOME; they are not the same fact. `"Closed"` is in `_AFFIRMATIVE`, so a nonconformance whose NCR
had been dispositioned and closed out — the ordinary end of a nonconformance — read as a requirement
that was SATISFIED. Favourable, and bought from a column that never claimed to state conformance.

```
before: {"Requirement ID": "R1", "Status": "Closed"} -> satisfied True, assessed True
after:                                              -> no `satisfied`, assessed False,
                                                       status "Closed"
unchanged: {"Result": "Pass"}                       -> satisfied True, assessed True
unchanged: {"Result": "Fail", "Status": "Closed"}   -> satisfied False, assessed True
```

`satisfied` keeps eleven headings for a register that means to state an outcome. One printing only a
status column now reaches NOT ASSESSED, and the canonical functions put such a row in
`unassessed_applicable`, exactly as this reader's own header says they should.

Proof can fail: re-adding the three headings returns both the duplicate check and the behavioural
check to FAIL, the latter reading `satisfied: True, assessed: True`.

`tools/test_run87_compliance_registers.py` stays **33/33** on a clean database — R2 re-pointing was
not needed for it.

---

## Recomputation

**RECOMPUTATION IS REQUIRED, and the triggering is left to the owner.** Six of the seven changes
alter what a stored `signalInputs` / `ComputedResult` row would contain for evidence already
uploaded:

* **H5** — any period whose trade denominators came from a document printing only a total now
  yields an ABSENT first-pass column where it previously carried the total. A6.4 moves from a
  favourable band to NOT TESTED on those firms.
* **M4** — any period holding two or more documents of one type may produce a different
  `disputeRecord` / `as_of_day`, and A4.7's duration input moves with it.
* **H3 + R3** — `evidenceQualification.material_conflicts` gains entries on periods with
  cross-period identity conflicts and on PERMANENT-field ties; Category-9 may move to
  REVIEW_REQUIRED, which gates downstream modules.
* **H4** — any project with an ARCHIVED document loses that document's schedule activities, risks
  and notices from the projection stores. `milestoneHistory` and A2.7 move. NOTE: rows ALREADY
  stored from archived documents are not deleted by this change — a recomputation will not remove
  them, and clearing them is a separate, deliberate act the owner must authorise.
* **M5** — risk registers with bare 1/0 probability cells lose those probabilities and gain
  refusals; the three forecasting modules abstain more often, which is the intended direction.
* **compliance_register** — status-only registers move from satisfied/assessed to NOT ASSESSED, and
  A6.1 / A6.3 populations shrink accordingly.

Coverage: every project and every period whose documents include a trade-denominator table, more
than one document of a single type, an archived upload, a risk register, or a compliance register —
in practice, all of them. The `extraction_client` change alters no stored value.

## Not in this agent's scope

S6 (backend/browser P80) is agent B's. Groups 1, 3, 4, 5 and 6 belong to the other agents. No R4
classification of the 244 tools scripts was performed here beyond classifying the one script this
agent added. `band_reference_data.json` was not examined — it is Group 5, agent-assigned elsewhere.

---

## `git status --porcelain` before each commit

```
H5 (aee0485)
 M server/app/documents.py
?? server/tools/test_run135d_selection_and_assembly.py

M4 (6463281)
 M server/app/documents.py
 M server/app/extraction_merge.py
 M server/tools/test_run135d_selection_and_assembly.py

H3 + R3 (b80bc16)
 M server/app/documents.py
 M server/app/extraction_merge.py
 M server/tools/test_run135d_selection_and_assembly.py

H4 (48b2ed1)
 M server/app/documents.py
 M server/tools/test_run135d_selection_and_assembly.py
(one untracked artefact, server/run71_capture.json, was written by
 drive_run71_document_control.py during verification and was DELETED, not committed)

M5 (3b6db72)
 M server/app/risk_values.py
 M server/tools/test_run135d_selection_and_assembly.py
(only server/app/risk_values.py was added to this commit)

extraction_client (f824d06)
 M server/app/extraction_client.py
 M server/tools/test_run135d_selection_and_assembly.py
(only server/app/extraction_client.py was added to this commit)

compliance_register (9cd3aae)
 M server/app/compliance_register.py
 M server/tools/test_run135d_selection_and_assembly.py
```

Every `git add` named explicit paths. No `git add -A` and no `git add .` was used. Nothing under
`code_audit/` was committed.

## Commits

```
aee0485  H5. Trade-table aliases no longer accept a total where the ladder is first-pass
6463281  M4. Document order is defined by business keys, not by upload order
b80bc16  H3 + R3. Qualification sees what selection sees, and a hash-settled disagreement is reported
48b2ed1  H4. The archive filter reaches every projection store and reader
3b6db72  M5. Bare 1 and 0 refuse as a probability, exactly as 2 through 5 do
f824d06  extraction_client:829. Remove the dead truncation suffix
9cd3aae  compliance_register._HEADINGS. Remove the duplicated outcome headings
```

Nothing was pushed and nothing was merged to main. The working tree is clean at the ending commit
apart from this report, which is the last commit.
