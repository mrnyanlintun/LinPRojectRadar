#!/usr/bin/env python3
"""
Migration test for the pre-judgment lock (B1).

Proves, against whatever DATABASE_URL points at:

  1. A decision can be inserted and its pre-judgment locked.
  2. Once pre_locked_at is set, pre_action and pre_confidence cannot be changed through any of
     three separate paths: a Core UPDATE, an ORM update, and raw driver SQL.
  3. Every rejected attempt appends a row to audit_events.
  4. CHECK ck_decisions_reveal_after_pre_lock rejects a reveal_at earlier than pre_locked_at.
  5. Columns that are not part of the preliminary judgment remain writable after the lock, because
     the workflow has to record the final decision on the same row.

Run:
    DATABASE_URL=... python tools/test_pre_lock_guard.py

Exit code 0 on success, 1 on any failure.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from sqlalchemy import select, text, update  # noqa: E402
from sqlalchemy.exc import DatabaseError  # noqa: E402

from app.db import build_engine, build_session_factory  # noqa: E402
from app.research_audit import is_pre_lock_violation, record_rejected_write  # noqa: E402
from app.research_models import (  # noqa: E402
    Assignment, AuditEvent, Configuration, Decision, Participant, Scenario, new_ulid,
)
from app.settings import load_settings  # noqa: E402

REJECTED = "pre_judgment_modification_rejected"

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((ok, label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


def audit_count(session) -> int:
    return len(session.scalars(select(AuditEvent).where(AuditEvent.event_type == REJECTED)).all())


def main() -> int:
    settings = load_settings()
    engine = build_engine(settings)
    Session = build_session_factory(engine)
    dialect = engine.dialect.name

    print(f"Dialect: {dialect}")
    print("=" * 78)
    print("SETUP")
    print("=" * 78)

    with Session() as s:
        participant = Participant(pseudonymous_code=f"PM-{new_ulid()[:6]}", role="Participant")
        scenario = Scenario(scenario_version="v1", project_type="construction", period_count=2)
        config = Configuration(code="C1", version="v1", label="single-model")
        s.add_all([participant, scenario, config])
        s.flush()

        assignment = Assignment(
            participant_id=participant.participant_id,
            scenario_id=scenario.scenario_id,
            sequence_number=1,
            config_id=config.config_id,
        )
        s.add(assignment)
        s.flush()

        decision = Decision(
            assignment_id=assignment.assignment_id,
            period="P1",
            pre_action="monitor",
            pre_confidence=60,
            pre_submitted_at=datetime.now(timezone.utc),
        )
        s.add(decision)
        s.commit()
        decision_id = decision.decision_id
        check(True, "decision inserted")

        # role CHECK constraint
        try:
            bad = Participant(pseudonymous_code=f"PM-{new_ulid()[:6]}", role="Wizard")
            s.add(bad)
            s.commit()
            check(False, "role CHECK rejects an unknown role", "insert succeeded")
        except DatabaseError:
            s.rollback()
            check(True, "role CHECK rejects an unknown role")

    print()
    print("=" * 78)
    print("CHECK CONSTRAINT: reveal_at may not precede pre_locked_at")
    print("=" * 78)

    locked_at = datetime.now(timezone.utc)

    with Session() as s:
        # reveal_at with no lock at all
        try:
            s.execute(update(Decision).where(Decision.decision_id == decision_id)
                      .values(reveal_at=locked_at))
            s.commit()
            check(False, "reveal_at rejected while pre_locked_at is NULL", "update succeeded")
        except DatabaseError:
            s.rollback()
            check(True, "reveal_at rejected while pre_locked_at is NULL")

    with Session() as s:
        s.execute(update(Decision).where(Decision.decision_id == decision_id)
                  .values(pre_locked_at=locked_at, pre_judgment_locked=True))
        s.commit()
        check(True, "pre_locked_at set, judgment locked")

    with Session() as s:
        try:
            s.execute(update(Decision).where(Decision.decision_id == decision_id)
                      .values(reveal_at=locked_at - timedelta(seconds=30)))
            s.commit()
            check(False, "reveal_at earlier than pre_locked_at rejected", "update succeeded")
        except DatabaseError:
            s.rollback()
            check(True, "reveal_at earlier than pre_locked_at rejected")

    with Session() as s:
        s.execute(update(Decision).where(Decision.decision_id == decision_id)
                  .values(reveal_at=locked_at + timedelta(seconds=30)))
        s.commit()
        check(True, "reveal_at after pre_locked_at accepted")

    print()
    print("=" * 78)
    print("TRIGGER: three independent modification paths, all must be rejected")
    print("=" * 78)

    with Session() as s:
        before_audits = audit_count(s)
        original = s.get(Decision, decision_id)
        original_action, original_conf = original.pre_action, original.pre_confidence

    # Path 1: SQLAlchemy Core UPDATE
    with Session() as s:
        try:
            s.execute(update(Decision).where(Decision.decision_id == decision_id)
                      .values(pre_action="escalate"))
            s.commit()
            check(False, "path 1, Core UPDATE rejected", "update succeeded")
        except DatabaseError as exc:
            s.rollback()
            check(True, "path 1, Core UPDATE rejected", str(exc)[:80])
            check(is_pre_lock_violation(exc), "path 1 recognised as a pre-lock violation")
            check(record_rejected_write(engine, decision_id=decision_id, path="core-update",
                                        attempted={"pre_action": "escalate"}),
                  "path 1 audit row committed on a separate connection")

    # Path 2: ORM attribute assignment and flush
    with Session() as s:
        try:
            row = s.get(Decision, decision_id)
            row.pre_confidence = 99
            s.commit()
            check(False, "path 2, ORM update rejected", "update succeeded")
        except DatabaseError as exc:
            s.rollback()
            check(True, "path 2, ORM update rejected", str(exc)[:80])
            check(record_rejected_write(engine, decision_id=decision_id, path="orm-update",
                                        attempted={"pre_confidence": 99}),
                  "path 2 audit row committed on a separate connection")

    # Path 3: raw SQL straight at the driver, bypassing the ORM entirely
    with Session() as s:
        try:
            s.execute(
                text("UPDATE decisions SET pre_action = :a WHERE decision_id = :i"),
                {"a": "defer", "i": decision_id},
            )
            s.commit()
            check(False, "path 3, raw SQL rejected", "update succeeded")
        except DatabaseError as exc:
            s.rollback()
            check(True, "path 3, raw SQL rejected", str(exc)[:80])
            check(record_rejected_write(engine, decision_id=decision_id, path="raw-sql",
                                        attempted={"pre_action": "defer"}),
                  "path 3 audit row committed on a separate connection")

    print()
    print("=" * 78)
    print("VALUES UNCHANGED AND ATTEMPTS AUDITED")
    print("=" * 78)

    with Session() as s:
        row = s.get(Decision, decision_id)
        check(row.pre_action == original_action,
              f"pre_action still {original_action!r}", f"is {row.pre_action!r}")
        check(row.pre_confidence == original_conf,
              f"pre_confidence still {original_conf}", f"is {row.pre_confidence}")

        after_audits = audit_count(s)
        appended = after_audits - before_audits
        check(appended == 3, f"3 rejection rows durably appended to audit_events (got {appended})")

        rows = s.scalars(
            select(AuditEvent).where(AuditEvent.event_type == REJECTED)
            .order_by(AuditEvent.server_ts)
        ).all()
        paths = {(r.event_metadata or {}).get("path") for r in rows}
        check(paths == {"core-update", "orm-update", "raw-sql"},
              "each rejected path is identifiable in the audit metadata", str(paths))
        check(all(r.server_ts is not None for r in rows), "audit rows carry a server timestamp")

    print()
    print("=" * 78)
    print("NON-PROTECTED COLUMNS REMAIN WRITABLE AFTER THE LOCK")
    print("=" * 78)

    with Session() as s:
        s.execute(update(Decision).where(Decision.decision_id == decision_id).values(
            final_action="escalate", disposition="modify", final_confidence=80,
            rationale="post-reveal", final_submitted_at=datetime.now(timezone.utc),
        ))
        s.commit()
        row = s.get(Decision, decision_id)
        check(row.final_action == "escalate" and row.disposition == "modify",
              "final decision fields still writable after lock")
        check(row.pre_action == original_action,
              "writing final fields did not disturb the locked pre-judgment")

    print()
    print("=" * 78)
    failed = [r for r in results if not r[0]]
    print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
    for _, label, detail in failed:
        print(f"  FAILED: {label}  {detail}")
    print("=" * 78)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
