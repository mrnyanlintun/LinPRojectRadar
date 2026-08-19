# Run 41 — Successor freeze: closing S1 and S2

**Disposition: `SUCCESSOR_FREEZE_ACCEPTED`** · `sim-2026.08-v26`

## What this run was for

Run 40 confirmed two HIGH defects on the accepted v25 instrument and could fix neither, because
remediating either moves a byte inside a frozen surface. It ended `FABLE_ACCEPTANCE_BLOCKED` with
both left for the owner. The owner ruled: **fix both before participant use**, accepting neither
risk for the study period.

That ruling is what makes this a successor freeze rather than a repair. Both fixes change
executable behaviour, so v25 is superseded, not amended.

## Both defects were reproduced on v25 first

This matters more than it sounds. Once a defect is fixed, the evidence that it was real exists
only in the pinned predecessor object. Reproducing first is also what makes the v25→v26 delta
provable rather than asserted.

**S1** was reproduced at the HTTP boundary and then in real Chromium, loading the document-content
route inside a same-origin iframe exactly as `assets/js/files.js` previews documents:

| | before | after |
|---|---|---|
| attacker payloads executing script in the app origin | **4 of 4** | **0 of 4** |
| attacks reaching the serving boundary (HTTP 200) | 4 of 4 | **4 of 4** |

The second row is the one that stops this being self-congratulation. After the fix the attacks
still *arrive* — so the refusal belongs to the document-serving boundary and not to some unrelated
authentication or routing gate that happened to say no first.

**S2** was reproduced with a decision driven to final lock entirely through the real application
routes, never by inserting a row:

| | before | after |
|---|---|---|
| raw SQL mutations succeeding after final lock | **13 of 13** | **0 of 13** |

## The field set was derived, and the prompt was wrong

The controlling specification named three protected fields: `final_action`, `final_confidence`,
`rationale`. It also said to derive the real set from the live model rather than guess. Reading the
AST of `a_researchdecision` — the only route that records a final response — and cross-checking
against `EXPORT_COLUMNS` gives **twelve** substantive final-response fields, every one of them an
analysis-export variable.

The nine the prompt did not name:

`disposition` (the participant's stance toward the AI recommendation) · `evidence_items` (evidence
use) · `reason_code` · `escalation_level` · `owner_role` · `authority_role` ·
`resource_constraint` · `deadline` · `residual_risk`

Protecting only the named three would have left nine components of the primary outcome freely
editable — including the participant's disposition toward the AI, which is close to the centre of
what this study measures.

A thirteenth column, `final_submitted_at`, is protected too. It is the guard's own predicate: a
trigger keyed off a timestamp it lets you clear is bypassable in two statements.

## Non-vacuity was built in, not checked afterwards

Every S2 attack runs the *identical* UPDATE twice — once on a control decision stopped just before
the final lock, where it must succeed, and once after the lock, where it must be refused carrying
the trigger's own marker text with the value re-read and unmoved. 13 of 13 reached the table
before the lock; 13 of 13 were refused after it. A statement that succeeds pre-lock and fails
post-lock was refused by the lock state and by nothing else.

Predeclared before running: an idempotent write of a protected field to its existing value is
**permitted**, matching the preliminary guard's `IS DISTINCT FROM` semantics. The guard exists to
stop the final response *changing*; refusing a write that changes nothing would also break
ordinary ORM flushes.

## Two of my own instruments were wrong, and were caught

Both would have produced a confident false claim.

The AI-binding harness labelled positions from its own loop counter. Every `researchadvance` had
silently refused, so the participant never left the first period and one idempotent reveal was
re-read 36 times — reported as 36 positions carrying a single recommendation, under six different
project names. It now takes each label from the decisions row the application actually wrote, and
refuses to emit unless it observed 36 genuinely distinct positions.

The field-derivation cross-check walked `ast.Assign`, which cannot match an annotated assignment.
`EXPORT_COLUMNS` is one, so the authority came back empty and every field was reported as absent
from the export. It now targets `EXPORT_COLUMNS` by name and refuses to emit a vacuous
cross-check.

The programme's standing lesson held again: the checking apparatus failed before the instrument
did, twice.

## Preservation, proved by execution

| Claim | Method | Result |
|---|---|---|
| Science unchanged | all 101 registered modules run on the pinned v25 git object and on the v26 tree | **0 rows moved** |
| AI binding unchanged | recommendation digest at all 36 project-period positions, both lines | **0 moved**, 6 unique project exposures each |
| Participant sequence unchanged | 70 governed package bytes, 6 sequence-bearing files | **0 moved** |
| Voting | live registry | exactly 2 (`A1.7`, `A1.8`) |
| Category-9 gate / Category-10 boundary | execution on an unqualified package | unchanged |

Because no governed participant bytes moved, `og-participant-2026.08-v13` is **retained**. A
successor package was not minted merely because server behaviour changed. `OG-SYNTH-0.6` and
`og-analysis-2026.08-v1` likewise.

## Twelve-fault campaign

**12 applied · 12 RED for the intended reason · 12 restored GREEN · 0 crashes credited as RED · 0
unrelated refusals credited.**

Two faults were repointed after being caught proving nothing, and both are recorded rather than
quietly fixed:

- Fault 11 first renamed the migration's revision id. That changes bytes and nothing else — the
  file still chained from 0025, so the trigger was still there and the guard stayed green. It now
  deletes the migration, which is what "absent on a fresh database" means.
- The campaign recorded a RED verdict whose own truncated evidence column did not contain the
  fragment it claimed. It now stores the exact failing line, and the enforcing suite checks the
  verdict against that line.

Fault 12 — behaviour changed while the stamp stays at v25 — is the one that protects every version
boundary this repository asserts. It is RED.

## Requalification

Executed, not copied forward. No old manifest was edited to say PASS.

| Gate | Result |
|---|---|
| Freeze qualification (Run-37 equivalent) | `FINAL_FREEZE_ACCEPTED` — 15 blocker classes, 0 blocked |
| Study execution readiness (Run-38 equivalent) | `STUDY_EXECUTION_READY` |
| Main-study launch (Run-39 equivalent) | `MAIN_STUDY_LAUNCH_READY` |
| Functional/security acceptance (Run-40 affected) | S1 fixed, S2 fixed, **0** unresolved HIGH blockers |

The frozen-surface guards were not relaxed to achieve this. They were made *exact*: they now
permit a named set of owner-authorised successor changes and still fail on anything else.

## The predecessor is intact

`sim-2026.08-v25`, its candidate `6142d877`, its release `f983bb02`, its identity, its gate, its
behaviour digest and its release records are unchanged. That they still say v25 is asserted by the
requalified gates, not assumed. Everything already computed under v25 remains interpretable.

## Scope

The entire production change is one serving function and one migration. No cleanup, no renaming,
no style normalisation, no docstring rewrites, no sanitising. Run 42 and Codex own
professionalization.

**Observation deferred to Run 42:** the three suites that reached a now-protected column
(`test_export.py`, `test_admin_ops_t7t8.py`, `test_decision_ui_t4.py`) each demonstrate export
tamper-detection through a decision column. They are repointed at `pre_assessment`, which is
exported and unprotected. If a future run protects that too, those demonstrations need a
non-decision carrier rather than another repoint.

**No real participant data was collected. Main-study observations remain 0.**
