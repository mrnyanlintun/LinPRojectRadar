#!/usr/bin/env python3
"""
RUN 41 regression - final-lock database integrity (finding S2).

Baseline defect, reproduced on v25 before the fix (code_audit/run41_s2_prefix_reproduction.json):
with a decision driven to final lock entirely through the real application routes, 13 of 13 raw
SQL UPDATEs against the decisions row succeeded, rewriting every substantive component of the
participant's final judgment and clearing final_submitted_at itself.

Migration 0026 adds trg_decisions_final_lock_guard, mirroring the preliminary-lock guard of
migration 0003 onto the final side.

HOW THIS SUITE AVOIDS PROVING NOTHING

A refusal is only evidence if the statement reached the guard. Every attack here is therefore
run TWICE against the same column with the same SQL: once BEFORE the final lock, where it must
SUCCEED, and once AFTER, where it must be refused. The pre-lock success is what proves the
statement is well formed, the column exists, and no unrelated constraint, type error or typo is
doing the work - so the post-lock refusal can only be the lock state.

Each refusal is additionally required to carry this trigger's own marker text, so a refusal
raised by some other constraint cannot be mistaken for this one, and the row is re-read
afterwards to confirm the value did not move.

Predeclared expectations, fixed before execution:

  change one protected field after lock ........ REFUSED
  change all protected fields together ......... REFUSED
  clear the lock timestamp itself .............. REFUSED
  set a protected field to its EXISTING value .. PERMITTED (idempotent write changes nothing;
                                                 matches trg_decisions_pre_lock_guard's
                                                 IS DISTINCT FROM semantics, and refusing it
                                                 would break ordinary ORM flushes)
  mutate a protected field BEFORE the lock ..... PERMITTED (this is the normal governed path)
  update an UNPROTECTED column after lock ...... PERMITTED (the guard must not obstruct
                                                 unrelated operation)

Run (from server/): DATABASE_URL=... SESSION_SECRET=... python tools/test_run41_final_lock_guard.py
Exit 0 on success, 1 on any failure.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select, text  # noqa: E402

import app.main as main  # noqa: E402
from app.research_models import Decision  # noqa: E402
import run41_flow  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
results: list[tuple[bool, str, str]] = []

#: The refusal must be THIS trigger's. Matching the marker stops an unrelated constraint
#: failure from being counted as proof that the final-lock guard fired.
MARKER = "final response is locked"

PROTECTED_CONTENT = [
    "final_action", "disposition", "rationale", "final_confidence", "escalation_level",
    "owner_role", "authority_role", "resource_constraint", "evidence_items", "reason_code",
    "deadline", "residual_risk",
]
LOCK_COLUMN = "final_submitted_at"

#: A literal SQL value per column that differs from what the flow writes.
TAMPER = {
    "final_action": "'TAMPERED ACTION'",
    "disposition": "'reject'",
    "rationale": "'TAMPERED RATIONALE'",
    "final_confidence": "3",
    "escalation_level": "'TAMPERED'",
    "owner_role": "'TAMPERED'",
    "authority_role": "'TAMPERED'",
    "resource_constraint": "'TAMPERED'",
    "evidence_items": "'[\"TAMPERED\"]'",
    "reason_code": "'TAMPERED'",
    "deadline": "'1999-01-01'",
    "residual_risk": "'TAMPERED'",
    LOCK_COLUMN: "NULL",
}


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   -- {detail}" if detail and not ok else ""))


def raw_update(decision_id: str, col: str, sql_value: str):
    """Run one raw UPDATE. Returns (succeeded, error_text, value_after)."""
    Session = main.SessionFactory
    with Session() as s:
        try:
            s.execute(text(f"UPDATE decisions SET {col} = {sql_value} WHERE decision_id = :d"),
                      {"d": decision_id})
            s.commit()
            ok, err = True, None
        except Exception as e:      # noqa: BLE001 - the refusal is the subject under test
            s.rollback()
            ok, err = False, f"{type(e).__name__}: {e}"
    with Session() as s2:
        after = getattr(s2.get(Decision, decision_id), col)
    return ok, err, after


print("=" * 78)
print("RUN 41 - final-lock database integrity (finding S2)")
print("=" * 78)

# ---------------------------------------------------------------- trigger exists at all
Session = main.SessionFactory
with Session() as s:
    dialect = s.bind.dialect.name
    if dialect == "sqlite":
        names = [r[0] for r in s.execute(
            text("SELECT name FROM sqlite_master WHERE type='trigger'")).fetchall()]
    else:
        names = [r[0] for r in s.execute(
            text("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal")).fetchall()]
check("trg_decisions_final_lock_guard" in names,
      "migration 0026 created trg_decisions_final_lock_guard", f"triggers present: {names}")

print()
print("-" * 78)
print("SECTION 7 - the governed application path still works end to end")
print("-" * 78)

ctx = run41_flow.build(main, client, "R41G")
steps = run41_flow.run_to_final_lock(ctx)
post, p = ctx["post"], ctx["p"]

check(steps["evidence"].get("ok") is True, "evidence readable")
check(steps["prejudgment"].get("ok") is True, "preliminary response entered and locked",
      str(steps["prejudgment"])[:160])
check(steps["reveal"].get("ok") is True, "AI reveal succeeds after the preliminary lock",
      str(steps["reveal"])[:160])
check(steps["final"].get("ok") is True,
      "final response entered and final-locked in the governed path (trigger permits it)",
      str(steps["final"])[:200])
check(steps["final"].get("current_stage") == "complete", "stage derives to complete after lock",
      str(steps["final"].get("current_stage")))

did = run41_flow.decision_id(ctx)
with Session() as s:
    d = s.get(Decision, did)
    check(d.final_submitted_at is not None, "final_submitted_at is set (the decision IS locked)")
    baseline = {c: getattr(d, c) for c in PROTECTED_CONTENT}
    check(d.final_action == run41_flow.FINAL_PAYLOAD["final_action"],
          "the stored final response is what the participant submitted")

reload_state = post({"action": "researchsequencestate", "session_token": p})
check(reload_state.get("ok") is True, "reload/resume after final lock succeeds",
      str(reload_state)[:200])
who = post({"action": "researchwhoami", "session_token": p})
check(who.get("ok") is True, "session/read-only operation is unaffected by the trigger",
      str(who)[:160])

# Asserted on ok is True, not on "not False": a mistyped action name returns a dict with no
# "ok" key at all, and a "not False" test would have called that a pass.
export = post({"action": "adminexportcreate", "session_token": ctx["admin"],
               "kind": "participant_inputs"})
check(export.get("ok") is True, "export after final lock succeeds", str(export)[:300])
check(str(export.get("export_id") or "") != "",
      "the export actually produced an artifact (not an empty success)", str(export)[:300])

print()
print("-" * 78)
print("SECTION 9 - attack the trigger directly (each attack proved to REACH it)")
print("-" * 78)
print("Reachability method: the identical UPDATE is run before the lock on a second decision,")
print("where it must SUCCEED. A statement that succeeds pre-lock and is refused post-lock was")
print("refused by the lock state and by nothing else.")
print()

# A second decision, stopped just BEFORE the final lock, for the reachability half.
ctx2 = run41_flow.build(main, client, "R41P")
post2 = ctx2["post"]
post2({"action": "researchevidenceget", "session_token": ctx2["p"]})
post2({"action": "researchprejudgment", "session_token": ctx2["p"],
       "pre_action": "Monitor", "pre_confidence": 50, "pre_assessment": "pre"})
post2({"action": "researchreveal", "session_token": ctx2["p"]})
did2 = run41_flow.decision_id(ctx2)
with Session() as s:
    check(s.get(Decision, did2).final_submitted_at is None,
          "control decision exists and is NOT final-locked (pre-lock reachability control)")

refused_after = 0
permitted_before = 0
for col in PROTECTED_CONTENT + [LOCK_COLUMN]:
    val = TAMPER[col]
    # (a) pre-lock: the same statement must succeed -> proves it reaches the table
    if col == LOCK_COLUMN:
        pre_ok, pre_err, _ = raw_update(did2, col, "'2026-08-19 00:00:00'")
    else:
        pre_ok, pre_err, _ = raw_update(did2, col, val)
    permitted_before += 1 if pre_ok else 0
    check(pre_ok, f"[reach] {col}: the same UPDATE SUCCEEDS before the final lock",
          f"pre-lock refusal means the post-lock refusal proves nothing: {pre_err}")
    # (b) post-lock: refused, by THIS trigger, with the value unmoved
    post_ok, post_err, after = raw_update(did, col, val)
    hit_marker = (post_err or "") and MARKER in post_err
    unchanged = (after == baseline[col]) if col != LOCK_COLUMN else (after is not None)
    ok = (not post_ok) and bool(hit_marker) and unchanged
    refused_after += 1 if ok else 0
    check(ok, f"[guard] {col}: raw SQL mutation REFUSED after the final lock",
          f"succeeded={post_ok} marker={bool(hit_marker)} unchanged={unchanged} err={post_err}")

check(refused_after == len(PROTECTED_CONTENT) + 1,
      f"every protected field refuses raw mutation after lock "
      f"({refused_after}/{len(PROTECTED_CONTENT) + 1})")
check(permitted_before == len(PROTECTED_CONTENT) + 1,
      f"every one of those statements reached the table before the lock "
      f"({permitted_before}/{len(PROTECTED_CONTENT) + 1})")

# case 4: all protected fields changed together in ONE statement
assigns = ", ".join(f"{c} = {TAMPER[c]}" for c in PROTECTED_CONTENT)
with Session() as s:
    try:
        s.execute(text(f"UPDATE decisions SET {assigns} WHERE decision_id = :d"), {"d": did})
        s.commit()
        combo_ok, combo_err = True, None
    except Exception as e:      # noqa: BLE001
        s.rollback()
        combo_ok, combo_err = False, f"{type(e).__name__}: {e}"
with Session() as s:
    still = s.get(Decision, did)
    intact = all(getattr(still, c) == baseline[c] for c in PROTECTED_CONTENT)
check((not combo_ok) and MARKER in (combo_err or "") and intact,
      "all protected fields changed in ONE statement: REFUSED, row intact",
      f"succeeded={combo_ok} intact={intact} err={combo_err}")

# case 5: no-op write of a protected field to its EXISTING value -> PERMITTED (predeclared)
with Session() as s:
    d = s.get(Decision, did)
    same = d.final_action
noop_ok, noop_err, after_noop = raw_update(did, "final_action",
                                           "'" + str(same).replace("'", "''") + "'")
check(noop_ok and after_noop == baseline["final_action"],
      "idempotent write of a protected field to its existing value is PERMITTED (predeclared)",
      f"succeeded={noop_ok} err={noop_err}")

# the guard must not obstruct unrelated columns after the lock
unrel_ok, unrel_err, _ = raw_update(did, "period", "'P01'")
check(unrel_ok, "an UNPROTECTED column still updates after the lock (guard is not over-broad)",
      str(unrel_err))

print()
print("-" * 78)
print("SECTION 7 - application routes after the final lock")
print("-" * 78)

normal = post({"action": "researchdecision", "session_token": p,
               "final_action": "Second attempt at a different action",
               "disposition": "reject", "final_confidence": 10,
               "rationale": "should not be recorded"})
check(normal.get("ok") is False, "normal API final-decision update after lock is refused",
      str(normal)[:200])

stale = post({"action": "researchdecision", "session_token": p,
              **run41_flow.FINAL_PAYLOAD})
check(stale.get("ok") is False, "stale API re-submission after lock is refused",
      str(stale)[:200])

with Session() as s:
    d = s.get(Decision, did)
    check(all(getattr(d, c) == baseline[c] for c in PROTECTED_CONTENT),
          "after every application and raw attack, the final response is byte-for-byte intact")

passed = sum(1 for ok, _, _ in results if ok)
total = len(results)
print()
print("=" * 78)
print(f"RESULT: {passed}/{total} checks passed")
print("=" * 78)
sys.exit(0 if passed == total else 1)
