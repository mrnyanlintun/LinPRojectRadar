"""
Durable audit for rejected writes.

Why this module exists, and why the audit row is not written by the trigger.

The trigger rejects a write to a locked preliminary judgment by raising. Anything the trigger
inserts before raising is part of the same transaction as the rejected UPDATE, so it is discarded
when that transaction unwinds. This is not a Postgres quirk: it was measured on SQLite too, where
RAISE(FAIL) preserves statement-level changes but the caller's rollback still removes them.
Postgres has no autonomous transactions without an extension such as dblink.

So a raising trigger cannot durably record its own rejections. The choice is between:

  a) a trigger that silently reverts the protected columns and audits durably, or
  b) a trigger that rejects loudly, with the audit written on a separate connection.

(a) was rejected. A database that accepts an UPDATE and quietly discards it is the exact silent
failure this project forbids, and a participant's attempt to revise a locked judgment must not
look like it succeeded.

This module implements (b). The audit write uses its own connection with its own transaction, so
it commits whether or not the caller's transaction survives.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

log = logging.getLogger("opus-gubernatio-server")

REJECTED_EVENT = "pre_judgment_modification_rejected"

# SQLSTATE raised by the Postgres trigger. Matching on this is precise; matching on message text
# would break the moment the wording changes.
PRE_LOCK_SQLSTATE = "OG001"

_MESSAGE_MARKER = "pre-judgment is locked"


def is_pre_lock_violation(exc: BaseException) -> bool:
    """
    True when an exception is the pre-judgment lock rejecting a write.

    Checks SQLSTATE first and falls back to the message, because SQLite carries no SQLSTATE.
    """
    sqlstate = getattr(getattr(exc, "orig", None), "sqlstate", None) or \
        getattr(getattr(exc, "orig", None), "pgcode", None)
    if sqlstate == PRE_LOCK_SQLSTATE:
        return True
    return _MESSAGE_MARKER in str(exc)


def record_rejected_write(
    engine: Engine,
    *,
    decision_id: str | None = None,
    participant_id: str | None = None,
    scenario_id: str | None = None,
    attempted: dict[str, Any] | None = None,
    path: str | None = None,
) -> bool:
    """
    Append one audit row on a fresh connection, outside the caller's transaction.

    Returns True when the row was committed. A failure here is logged and reported to the caller
    rather than raised: losing the audit must not also lose the rejection the caller is handling.
    """
    import json
    import os
    import time

    # Inline ULID rather than importing research_models, which would pull the ORM into a path that
    # has to work while a transaction is unwinding.
    crockford = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    raw = (int(time.time() * 1000) << 80) | int.from_bytes(os.urandom(10), "big")
    chars = []
    for _ in range(26):
        raw, rem = divmod(raw, 32)
        chars.append(crockford[rem])
    event_id = "".join(reversed(chars))

    metadata = {"decision_id": decision_id, "path": path, "attempted": attempted or {}}

    try:
        # A separate connection with its own transaction. begin() commits on clean exit.
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(
                    text(
                        "INSERT INTO audit_events "
                        "(event_id, participant_id, scenario_id, event_type, metadata) "
                        "VALUES (:event_id, :participant_id, :scenario_id, :event_type, :metadata)"
                    ),
                    {
                        "event_id": event_id,
                        "participant_id": participant_id,
                        "scenario_id": scenario_id,
                        "event_type": REJECTED_EVENT,
                        # Bound as text and cast by the column type. Passing a dict would need a
                        # dialect-specific JSON bind, and this path must work on both.
                        "metadata": json.dumps(metadata),
                    },
                )
        return True
    except Exception as exc:  # noqa: BLE001 - never let an audit failure mask the rejection
        log.error(
            "audit_write_failed",
            extra={"event_type": REJECTED_EVENT, "decision_id": decision_id,
                   "error_type": type(exc).__name__, "detail": str(exc)[:200]},
        )
        return False
