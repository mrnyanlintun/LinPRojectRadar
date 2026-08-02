# Five checks that cannot fail: fixed two, confirmed two, referred one

Test files only. No application code touched. Server suite: **1361 checks before, 1361 after**
(no checks added or removed; two existing checks now assert real content instead of nothing).

---

## 1. `test_workspace_t3t5.py:229` — FIXED

**Asserted:** that a module carrying a recommendation is individually marked
`recommendation_withheld` before the participant's preliminary judgment is locked (the per-module
half of Guarantee 8).

**Why it could not fail.** The call was `check(True, "...", f"redacted_any={redacted_any}")`.
`redacted_any` was computed and formatted into the *detail* string, and never passed as the
condition. `check()` only prints the detail on failure, so a run where `redacted_any` was `False`
would still print `PASS` and never show the reader the false value.

**What it asserts now:**

```python
check(redacted_any, "module-level redaction flag present on at least one action-bearing module",
      f"redacted_any={redacted_any}")
```

Ground truth confirmed by running the suite before touching the assertion: `redacted_any=True`
against the real fixture, so the fix does not paper over a live defect at this location.

**The fault that proved it.** App code is off limits for this task, so the fault was injected in
the test file's own local computation, at the point the flag is read: the key name was changed
from `recommendation_withheld` to `recommendation_withheld_RENAMED`, simulating the flag
disappearing. Result: `69/70`, `redacted_any=False`, red. Reverted, byte-identical, suite back to
`70/70`.

---

## 2. `test_features.py:158` — FIXED

**Asserted:** that `adminfeaturesset` writes an audit row recording who changed a participant's
features and what changed.

**Why it could not fail.** 

```python
check(audit_rows("features_set", changed_by=None) == [] or
      any(m.get("applied") == {"chat": True} for m in audit_rows("features_set")),
      "the change is audited with previous and new values")
```

`features.py:317` always writes `changed_by=caller.participant_id`, a real ULID, never `None`. So
`audit_rows("features_set", changed_by=None)` is `[]` on every possible run, the left side of the
`or` is always true, and the right side — the only part that reads real content — never executes.
It would still pass if `features_set` were never audited at all.

**What it asserts now:**

```python
rows = audit_rows("features_set", changed_by=admin_id)
check(any(m.get("applied") == {"chat": True} and m.get("previous") == {}
          and m.get("now_stored") == {"chat": True} for m in rows),
      "the change is audited with who changed it, the previous state and the new state",
      str(rows))
```

`admin_id` did not previously exist in this file; capturing it required changing
`admin = post(...)["session_token"]` to `admin_login = post(...)`, then reading both
`session_token` and `participant_id` from the one response.

**A second defect found while fixing the first.** My first attempt filtered by
`participant_id=res_p["participant_id"]`. It failed — not because the audit content was wrong, but
because `audit_rows()` only reads `AuditEvent.event_metadata`, and `audit()` stores
`participant_id` as a dedicated column, never inside the metadata dict. The filter could never
match anything. `changed_by`, unlike `participant_id`, is passed through `**metadata` and is real
content, so the filter now uses that instead.

**The fault that proved it.** `changed_by=admin_id` was pointed at a wrong id
(`"00000000000000000000000000"`), simulating a row that does not identify who actually made the
change — the exact property the check's label claims. Result: `48/49`, red. Reverted,
byte-identical, suite back to `49/49`.

---

## 3. Three `all()`-over-possibly-empty checks — ALREADY FIXED, no action taken

The brief's own description ("a previous session found them during injection in the D1 work")
matches `T6_HANDOFF.md`'s T22 section exactly: *"Three more vacuous checks were caught by that
injection — `all()` over an empty list — which is the fourth session running."* That session's
report (`REPORT_2026-08-02_d1-implementation.md`) states they were found **and fixed** in the same
pass, before commit `c05d028` landed.

Confirmed against the current file, `server/tools/test_d1_module_inputs.py`:

```python
check(len(si3.get("events") or []) >= 3 and all(len(str(e.get("at"))) == 10 for e in si3["events"]),
      "event timestamps are narrowed to date-only at the boundary, as models_dq requires", ...)
...
check(len(ev1) >= 3 and all(e.get("at", "")[:10] <= cut1 for e in ev1),
      "period 1's event log is truncated at its cutoff: later activity does not reach it", ...)
check(len(ev3) >= 3 and not any(e.get("at", "").startswith("2026-12") for e in ev3),
      "and the December event reaches no period, all three cutoffs preceding it", ...)
check(len(ev3) >= len(ev1) > 0,
      "a later period sees at least as much of the log as an earlier one", ...)
```

All three the report describes ("three truncation assertions") carry a non-empty length guard
(`>= 3`, or `> 0`) ahead of the `all()`/`not any()`/comparison, so none of them can pass
vacuously on an empty list today.

`git log` confirms the guard was present from the type's introduction (`c05d028`, `== 3`
originally, widened to `>= 3` in a later unrelated session, `ead2357`) — it was never committed in
a vacuous form.

Ran the file against real data as confirmation, not as a fix: all four checks above passed with
genuine non-empty event lists (`3` events at period 1, `>= 3` at period 3), so the guard is
exercised, not dead weight. **No edit made**, per the brief's own instruction to say so and move on
rather than editing around an already-fixed check.

---

## Verification discipline

Both fault-injection runs used a harness that: asserts the fault text occurs exactly once before
patching (so an injection cannot silently fail to apply against the wrong text), checks the suite
prints an actual `RESULT:` line rather than crashing, reverts, and then **byte-compares the file
against a pristine snapshot and re-runs the suite to confirm it is back at baseline** — after each
fault individually, not once at the end.

| Fault | Suite | Before | After fault | Restored |
|---|---|---|---|---|
| Redaction flag key renamed | `test_workspace_t3t5.py` | 70/70 | **69/70, RED** | 70/70, byte-identical |
| Audit filter pointed at wrong admin id | `test_features.py` | 49/49 | **48/49, RED** | 49/49, byte-identical |

Neither fault touched application code. Both were injected into the test file's own local
computation, at the point where the value under assertion is read — the closest available proxy to
"the thing the check exists to catch" without going outside the test-files-only scope this task set.

## Server suite

Before: 1361 checks across 24 suites. After: 1361 checks across 24 suites, 0 failures. The count
is unchanged because no `check()` call was added or removed — two existing calls now test their
argument instead of a literal `True`, and one now filters on real content instead of a disjunct
that could never take its live branch.

## Left alone

Item 3 only, and it is left alone because it was already fixed, not because it was judged
low-priority. No other check in scope for this task was left unaddressed.
