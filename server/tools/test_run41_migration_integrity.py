#!/usr/bin/env python3
"""
RUN 41 section 8 - the final-lock guard arrives through the governed migration mechanism.

Two things must be true, and neither is provable by reading the migration file:

  1. FRESH DATABASE -> alembic upgrade head -> the trigger exists AND behaves.
  2. PREDECESSOR SCHEMA (0025, the immediate predecessor, carrying real rows written while it
     was still unprotected) -> alembic upgrade head -> succeeds, and the guard then protects
     the rows that already existed.

Case 2 is the one that matters operationally: the study's database will be upgraded, not
recreated, and a decision that was already final-locked under v25 must become protected without
the migration failing on the data already there.

This suite builds its OWN databases with alembic rather than using the runner's, because the
subject under test is the migration path itself. Behaviour is proven by executing an UPDATE and
observing the refusal - never by grepping the migration source, which would only prove that a
file says what it says.

Run (from server/): DATABASE_URL=... SESSION_SECRET=... python tools/test_run41_migration_integrity.py
"""
from __future__ import annotations

import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile

SERVER = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVER))

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   -- {detail}" if detail and not ok else ""))


PREDECESSOR = "0025_project_notices"
HEAD_REV = "0026_final_lock_guard"
TRIGGER = "trg_decisions_final_lock_guard"
MARKER = "final response is locked"

TMP = tempfile.mkdtemp(prefix="run41mig")


def alembic(db: str, target: str) -> tuple[bool, str]:
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", target],
                       cwd=str(SERVER), env=env, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr)[-600:]


def triggers(db: str) -> list[str]:
    c = sqlite3.connect(db)
    try:
        return [r[0] for r in
                c.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall()]
    finally:
        c.close()


def seed_locked_decision(db: str, did: str = "R41MIGDECISION0000000000AA") -> None:
    """Insert a final-locked decision using ONLY columns the 0025 schema has."""
    c = sqlite3.connect(db)
    try:
        c.execute(
            "INSERT INTO decisions (decision_id, assignment_id, final_action, disposition, "
            "rationale, final_confidence, final_submitted_at, pre_action, pre_confidence, "
            "pre_submitted_at, pre_locked_at, pre_judgment_locked) "
            "VALUES (?, ?, 'ORIGINAL ACTION', 'accept', 'ORIGINAL RATIONALE', 70, "
            "'2026-08-19 10:00:00', 'pre', 50, '2026-08-19 09:00:00', "
            "'2026-08-19 09:00:00', 1)",
            (did, "R41MIGASSIGNMENT000000000A"))
        c.commit()
    finally:
        c.close()


def try_tamper(db: str, did: str, col: str = "final_action",
               val: str = "'TAMPERED'") -> tuple[bool, str]:
    c = sqlite3.connect(db)
    try:
        c.execute(f"UPDATE decisions SET {col} = {val} WHERE decision_id = ?", (did,))
        c.commit()
        return True, ""
    except Exception as e:      # noqa: BLE001 - the refusal is the subject
        return False, str(e)
    finally:
        c.close()


def value_of(db: str, did: str, col: str = "final_action") -> str:
    c = sqlite3.connect(db)
    try:
        row = c.execute(f"SELECT {col} FROM decisions WHERE decision_id = ?", (did,)).fetchone()
        return row[0] if row else None
    finally:
        c.close()


print("=" * 78)
print("RUN 41 - migration integrity for the final-lock guard (finding S2)")
print("=" * 78)

# ------------------------------------------------------------------ case 1: fresh database
print()
print("-" * 78)
print("CASE 1 - fresh database -> alembic upgrade head")
print("-" * 78)
fresh = os.path.join(TMP, "fresh.db")
ok, log = alembic(fresh, "head")
check(ok, "alembic upgrade head succeeds on a fresh database", log)
check(TRIGGER in triggers(fresh), f"{TRIGGER} exists after a fresh migration",
      str(triggers(fresh)))

did = "R41MIGDECISION0000000000AA"
seed_locked_decision(fresh, did)
moved, err = try_tamper(fresh, did)
check((not moved) and MARKER in err,
      "on a freshly migrated database the guard REFUSES a post-lock raw mutation", err)
check(value_of(fresh, did) == "ORIGINAL ACTION", "the value did not move on the fresh database")

# ------------------------------------------- case 2: upgrade FROM the predecessor schema
print()
print("-" * 78)
print(f"CASE 2 - predecessor schema {PREDECESSOR} with existing rows -> upgrade head")
print("-" * 78)
pred = os.path.join(TMP, "pred.db")
ok, log = alembic(pred, PREDECESSOR)
check(ok, f"a database can be built at the predecessor revision {PREDECESSOR}", log)
check(TRIGGER not in triggers(pred),
      "the predecessor schema genuinely LACKS the guard (so case 2 is not vacuous)",
      str(triggers(pred)))

seed_locked_decision(pred, did)
moved_before, _ = try_tamper(pred, did)
check(moved_before,
      "on the predecessor schema the post-lock mutation SUCCEEDS - this is the S2 defect",
      "if this fails the upgrade proof below shows nothing")
check(value_of(pred, did) == "TAMPERED", "the predecessor really did record the tampered value")

# restore the row, then upgrade
c = sqlite3.connect(pred)
c.execute("UPDATE decisions SET final_action = 'ORIGINAL ACTION' WHERE decision_id = ?", (did,))
c.commit(); c.close()

ok, log = alembic(pred, "head")
check(ok, "alembic upgrade head succeeds FROM the predecessor schema with rows already present",
      log)
check(TRIGGER in triggers(pred), f"{TRIGGER} exists after upgrading the predecessor",
      str(triggers(pred)))

moved_after, err_after = try_tamper(pred, did)
check((not moved_after) and MARKER in err_after,
      "a row that was already final-locked under the predecessor is now PROTECTED", err_after)
check(value_of(pred, did) == "ORIGINAL ACTION",
      "the pre-existing final response did not move after the upgrade")

# ------------------------------------------------------------------ downgrade is honest
print()
print("-" * 78)
print("CASE 3 - the migration's own downgrade removes what it added")
print("-" * 78)
env = dict(os.environ, DATABASE_URL=f"sqlite:///{pred}", PYTHONIOENCODING="utf-8")
r = subprocess.run([sys.executable, "-m", "alembic", "downgrade", PREDECESSOR],
                   cwd=str(SERVER), env=env, capture_output=True, text=True)
check(r.returncode == 0, "alembic downgrade back to the predecessor succeeds",
      (r.stdout + r.stderr)[-400:])
check(TRIGGER not in triggers(pred), "the downgrade removed the trigger", str(triggers(pred)))
ok2, log2 = alembic(pred, "head")
check(ok2 and TRIGGER in triggers(pred), "and re-upgrading restores it", log2)

shutil.rmtree(TMP, ignore_errors=True)

passed = sum(1 for ok, _, _ in results if ok)
total = len(results)
print()
print("=" * 78)
print(f"RESULT: {passed}/{total} checks passed")
print("=" * 78)
sys.exit(0 if passed == total else 1)
