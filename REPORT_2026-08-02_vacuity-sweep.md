# Vacuity sweep of the test suite

**Read-only session. No code was modified. No test file was edited.**

Scope: all 21 Python suites in `server/tools/`, plus `tests.html` and `tests_render.html`.
Roughly 850 `check(...)` call sites. The question asked of each was not "does it pass" but
"could it fail".

**Method, stated so the coverage claim is not overread.** I read every `check(...)` call site in
all 21 Python suites (extracted mechanically, then read in context where the line was suspicious)
and the assertion lists of both browser harnesses. I did **not** re-execute the suite with faults
injected, so the findings below are argued from the code rather than proven by making each check
go red. Where the argument is airtight I say so; where judging a check would need a fault
injection run I say that instead of guessing. Two items I judged expensive are listed at the end
rather than resolved.

**Counting.** Eight findings below. Two are unconditional passes in checks guarding
research-critical properties. Three are checks that cannot fail because a term in them is a
constant. Three are checks that assert a property the defect satisfies.

---

## 1. `server/tools/test_workspace_t3t5.py:229` — an unconditional pass guarding the recommendation redaction

```python
redacted_any = any(
    isinstance(m, dict) and m.get("recommendation_withheld") for m in (r["module_results"] or [])
)
check(True, "module-level redaction flag present where applicable",
      f"redacted_any={redacted_any}")
```

**What it appears to assert.** That modules carrying a recommendation are individually marked
withheld before the participant's preliminary judgment is locked. This is the per-module half of
Guarantee 8, and the comment two lines above says so explicitly: the surrounding string-marker
scan was judged imprecise and "the per-module redaction flag is the precise proof".

**Why it cannot fail.** The first argument is the literal `True`. `redacted_any` is computed,
formatted into the *detail* string, and never tested. `check()` prints the detail only on failure,
so a run where `redacted_any` is `False` prints `PASS` and never shows the reader the `False`.

**Why this one is first.** The blind, locked preliminary judgment is the study's central
measurement. Everything else in Guarantee 8 tests the *envelope* (four literal markers absent from
the JSON body). This was the only check on the per-module flag, and it is a no-op. If the
per-module redaction were removed entirely, this suite would stay green.

**What it would have to assert.** `check(redacted_any, ...)`, and it needs a precondition beside
it: that at least one module in this fixture *is* action-bearing, so that `redacted_any` being
true is evidence rather than an accident of which modules ran. `test_decision_ui_t4.py:249`
(`check(len(withheld) > 0, ...)`) is the correct shape and does exist, which limits the damage —
but it is a different suite against a different fixture, and this file's own claim to prove the
property is false.

---

## 2. `server/tools/test_features.py:158` — the only audit check on a feature change, disarmed by a disjunction

```python
check(audit_rows("features_set", changed_by=None) == [] or
      any(m.get("applied") == {"chat": True} for m in audit_rows("features_set")),
      "the change is audited with previous and new values")
```

**What it appears to assert.** That `adminfeaturesset` writes an audit row recording who changed
what, with previous and new values.

**Why it cannot fail.** `audit_rows(event_type, **meta)` (line 58) keeps a row only when
`m.get(k) == v` for every filter. `features.py:317` writes `changed_by=caller.participant_id`,
always a non-empty ULID string, on every `features_set` row. So `audit_rows("features_set",
changed_by=None)` is `[]` on every possible run, the `or` short-circuits, and the right-hand side
is never evaluated. It would still be `[]` — and still pass — if `features_set` were never
audited at all, because then there are no rows to filter.

**Also worth stating:** the label promises "previous and new values" and the live half of the
expression only ever looks at `applied`. `previous`, `previous_effective` and `now_stored` are
written by the server and asserted nowhere.

**What it would have to assert.** The `or` removed, and the row read positively:

```python
rows = audit_rows("features_set", participant_id=res_p["participant_id"])
check(any(m.get("applied") == {"chat": True} and m.get("changed_by") == admin_id
          and m.get("previous") == {} and m.get("now_stored") == {"chat": True}
          for m in rows), ...)
```

---

## 3. `server/tools/test_export.py:133` — an unconditional pass standing in for the whole export fixture

```python
pa_id, pa_tok = run("GA", "escalate", 50, 80, "escalated after review")
pb_id, pb_tok = run("GB", "monitor", 60, 55, "held position")
check(True, "two participants completed two periods each")
```

**What it appears to assert.** That the two-participant, two-period fixture the entire export
suite is measured against was actually built.

**Why it cannot fail.** Literal `True`. `run()` (lines 95-131) fires fourteen `post()` calls and
inspects the `ok` of none of them. Consent, intake, assignment, package attach, evidence, the
preliminary judgment, the reveal, the decision and the advance can each fail silently and this
check still prints PASS with that label.

**Mitigation, stated so this is not overstated.** The failure is not fully silent downstream:
`row_a1 = [...][0]` at line 231 raises `IndexError` if the rows are missing, which kills the
script. But a *partial* build — say period 2 failing to advance while period 1 succeeds — gives
`row_count == 2`, fails check 142 with a confusing label, and leaves this line still claiming the
fixture is complete.

**What it would have to assert.** `run()` returning the `ok` of each stage, and this check
asserting all of them true — or at minimum a positive count query against `decisions` for the two
participants.

---

## 4. `server/tools/test_workspace_t3t5.py:210` — determinism asserted where read-only-ness is claimed

```python
result2 = post({"action": "projectresults", ...})
check(result["result"] == result2["result"],
      "reading twice returns the byte-identical stored row (a read, not a compute)")
```

**What it appears to assert.** That `projectresults` reads a stored row rather than recomputing.

**Why it cannot fail in the way the label claims.** The analytical layer is deterministic by
construction and is proven so by `test_simulation.py` Guarantee 1: identical inputs give
byte-identical output, and the seed is derived from the project id, not from a clock. So a
`projectresults` that *did* recompute on every read, from the same documents, would return two
byte-identical results and pass this check. The property being asserted is determinism, which the
defect this check exists to catch would also satisfy.

This is the same shape as the `assemble_signal_inputs(list(reversed(base))) == a` case named in
the brief: a property that the fault preserves.

**What it would have to assert.** The check at line 207 (`result["result"]["result_id"] ==
compute["result_id"]`) is the one carrying the weight and it is sound. To make 210 non-vacuous it
would have to observe an effect a recompute cannot avoid: no new `computed_results` row appears
across the two reads, and `computed_at` is unchanged. A row count before and after is one line.

---

## 5. `server/tools/test_decision_sequence.py:169` — an equality that a shared absence satisfies

```python
check(pj.get("pre_submitted_at") == pj.get("pre_locked_at"),
      "submitted and locked are the same instant")
```

**What it appears to assert.** That the preliminary judgment is locked in the same statement that
records it, so there is no window in which it exists unlocked.

**Why it can pass without the property holding.** Both sides are `.get()` on the same dict. If the
response ever stops carrying these two keys, both are `None`, `None == None`, and the check passes
while the property it names is unobserved. This is not hypothetical drift: the response shape is
assembled by hand in `research_decision.py` and nothing else in this suite asserts these two keys
are present.

Severity is lower than 1 to 3 because the property itself is separately guarded — the CHECK
constraint `ck_decisions_reveal_after_pre_lock` and the migration 0009 trigger are exercised at
lines 242 and 263, and line 168 does assert `pre_judgment_locked is True`. But the check as
written cannot distinguish "same instant" from "field absent".

**What it would have to assert.** A non-null guard first: `check(pj.get("pre_submitted_at") is not
None and pj["pre_submitted_at"] == pj["pre_locked_at"], ...)`.

---

## 6. `server/tools/test_export.py:243` and `:245` — the study's timing measures checked only for sign

```python
check(row_a1["deliberation_seconds"] is not None and row_a1["deliberation_seconds"] >= 0,
      "deliberation_seconds computed and non-negative")
check(row_a1["pre_assessment_seconds"] is not None and row_a1["pre_assessment_seconds"] >= 0,
      "pre_assessment_seconds computed and non-negative")
```

**What it appears to assert.** That the two derived timing variables in the analysis dataset are
computed correctly.

**Why it is near-vacuous.** `>= 0` is satisfied by a constant zero, by the two timestamps being
swapped in a way that still yields a positive interval, and by any wrong-but-positive pair. The
fixture deliberately sleeps `0.05 s` between stages (lines 115 and 119), so a *correct*
implementation and a "return 0.0" implementation are separated by 50 ms, and only one of the two
possible results is excluded. Neither check names a value.

These are dependent variables of the praxis. `test_decision_ui_t4.py:369-371` does better on
`deliberation_seconds` — it sleeps `PAUSE_SECONDS` and asserts `delib >= PAUSE_SECONDS` and
`delib < PAUSE_SECONDS + 60`, which is a real bound — so the correct pattern exists in the repo
and was not applied here. Nothing anywhere bounds `pre_assessment_seconds`.

**What it would have to assert.** The `test_decision_ui_t4` pattern: a deliberate pause of known
length, then a two-sided bound around it, for both variables.

---

## 7. `tests.html` (52 assertions) — an entire harness over code no shipped route loads

```html
<script src="assets/js/categories.js"></script>
<script src="assets/js/sim.js"></script>
<script src="assets/js/simulations.js"></script>
```

**What it appears to assert.** The signal mathematics, per its own header ("the sibling harness
for signal MATH").

**Why it cannot fail in a way that matters.** `index.html` deliberately loads none of these three
files (T6 Part 3; `taxonomy.js` replaced `categories.js` and the browser computes nothing). So
these 52 assertions exercise the client-side derivation that was *removed* from every
participant-facing route precisely because it produced the false-Red defect. Whatever the code
under test does, no user sees it. It cannot go red for a reason that reaches a person, and it
cannot go green as evidence about what ships.

This is not a bad test file; it is a correct test file pointed at retired code. Worth flagging
because a green `tests.html` reads as coverage of the signal mathematics, and the signal
mathematics that ships is in `server/app/simulation/`.

**What it would have to be.** Either explicitly relabelled as the legacy/`research/deepdive.html`
harness (that page genuinely does load these files and is the one surface that computes in the
browser), or retired. Deciding which is not a sweep's call.

---

## 8. The `check(True, ...)` after an unguarded write — a pattern, not a single line

Fifteen further sites are `check(True, "...")` placed after a statement that would raise if the
property failed:

| File | Lines |
|---|---|
| `test_pre_lock_guard.py` | 89, 99, 117, 123, 133, 139, 160, 175, 191 |
| `test_decision_sequence.py` | 242, 263 |
| `test_transitions.py` | 290, 298 |
| `test_research_identity.py` | 183, 208, 241 |

**These are a weaker case than 1 to 3 and I am separating them deliberately.** Two shapes:

- Inside an `except DatabaseError:` arm whose `try` arm ends in `check(False, ...)`. This is the
  correct idiom for "assert this raises" and is **not** vacuous. Most of the list is this.
- After a bare `s.commit()` outside any `try` (e.g. `test_pre_lock_guard.py:89`, `:123`, `:139`;
  `test_research_identity.py:208`). If the write fails, the exception escapes, the script dies,
  and no `RESULT: n/n` line is printed. That is a loud failure, so the property is not unguarded —
  but the check itself contributes a guaranteed PASS to the count, and a suite whose count is
  read as evidence should not include lines that can only ever be PASS.

No action is proposed here. It is recorded so the next sweep does not re-derive it, and so the
headline count (`1013 checks across 21 suites`) is read knowing roughly fifteen of them are
structural.

---

## Judged expensive, not resolved

Stated rather than guessed, per the brief.

- **`test_group_assignment.py` lines 107/108 versus 127/129.** The first pair asserts the
  registered set and the artifact set have no difference in either direction; the second pair
  asserts each has exactly `EXPECTED_TOTAL` members. Given the first pair holds, the second pair
  can only fail by both sides drifting together to the same wrong count, which is possible (a
  module added to both the code and the artifact in one commit) but not obviously the failure the
  check is for. Deciding whether 127/129 add anything needs the artifact-parsing code read
  properly against the registry loader. I did not do that.
- **`test_admin_ops_t7t8.py:119` and `:122`** use `>=` against a pre-count for audit rows
  (`after_admin >= before_admin + len(...)`). Whether the inequality can be satisfied by unrelated
  audit rows written by the same request depends on how many events each refused action emits,
  which needs the refusal paths traced. `>=` where `==` is available is a smell, and
  `test_features.py:192` uses `==` for the same kind of assertion, but I did not establish that
  the `>=` here is loose enough to hide a missing audit row.
- **`tests_render.html`'s single fixture.** All 26 assertions run against one stored-result
  project. Its period is never varied and no second project exists, so, exactly like
  `test_workspace_t3t5.py` Guarantee 9, it is blind to anything cross-period or cross-project by
  construction. Whether that blindness hides a live defect in the render paths needs the render
  paths audited, which is stage 7 work and is in the sibling report.

---

## What I could not establish

- **Whether any of these eight has ever hidden a live defect**, other than 1, where the property
  is real and the check is a no-op, so the coverage claim in the file's own comment is false today.
- **Whether the suite has vacuous checks I did not recognise.** I read the call sites; I did not
  inject faults. A check that is subtly satisfied by the fault it guards — item 4's shape — is
  found by reasoning about the fault, and I only reasoned about faults I already knew of from
  `REPORT_2026-08-02_pipeline-audit.md`. **Treat this sweep as thorough on the mechanical patterns
  (literal `True`, dead disjunct, shared-absence equality, one-sided bound) and partial on the
  semantic pattern.** The semantic pattern is where the two known cases named in the brief live.
- **Nothing here was fixed, and no test file was touched.** Two other sessions are adding tests to
  this suite concurrently; line numbers above are against `ce73d6d`.
