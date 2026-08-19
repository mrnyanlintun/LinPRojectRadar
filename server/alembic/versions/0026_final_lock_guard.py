"""final-lock guard

Revision ID: 0026_final_lock_guard
Revises: 0025_project_notices
Create Date: 2026-08-19

RUN 41, finding S2. Mirrors the preliminary-lock protection of migration 0003 onto the FINAL
side of the same row.

WHAT WAS WRONG

Migration 0003 put the preliminary judgment beyond the reach of raw SQL, because that judgment
is the measurement the study rests on. The FINAL response never got the same treatment. Run 41
reproduced the consequence on the v25 schema, with the decision driven to final lock entirely
through the real application routes: with final_submitted_at set, 13 of 13 direct UPDATE
statements against the decisions row succeeded, silently rewriting every substantive component
of the participant's final judgment, and clearing final_submitted_at itself.

The final response is primary outcome data. An instrument in which it can be edited after the
fact, without trace, cannot support a claim about what participants decided.

WHICH COLUMNS ARE PROTECTED, AND WHY THIS LIST

The list is derived mechanically, not chosen. server/tools/run41_derive_final_fields.py reads
the AST of a_researchdecision - the only route that records a final response - and takes every
`decision.<attr> = ...` it performs, then cross-checks the result against EXPORT_COLUMNS in
research_export.py. Both authorities agree on the same thirteen names. Twelve are substantive
content; the thirteenth is the lock timestamp.

The lock timestamp is protected too, and that is not decoration. A guard predicated on
final_submitted_at that permits final_submitted_at to be cleared is bypassable in two
statements: clear the stamp, then edit freely. Protecting the predicate is what makes the
guard hold.

Deliberately NOT protected: pre-side columns (already covered by trg_decisions_pre_lock_guard),
reveal_at, package linkage, result_id, and every operational column. Nothing is protected that
is not part of the final participant judgment.

BEFORE AND AFTER THE LOCK

The trigger fires only when OLD.final_submitted_at IS NOT NULL. Before the final lock the
application writes the final response normally - indeed a_researchdecision writes all thirteen
columns in the same statement that first sets final_submitted_at, and that statement is
permitted precisely because OLD.final_submitted_at is still NULL. Reads, sessions, transitions
and every unrelated write are untouched.

AN IDEMPOTENT WRITE IS PERMITTED, ON PURPOSE

A statement that sets a protected column to the value it already holds is allowed, matching
trg_decisions_pre_lock_guard's use of IS DISTINCT FROM. The guard exists to stop the final
response CHANGING; a write that changes nothing has nothing to stop. Refusing it would also
break ordinary ORM flushes, which routinely re-send unchanged columns, and section 7 of the
Run-41 specification forbids a trigger that obstructs normal operation.

WHY THE TRIGGER DOES NOT WRITE AN AUDIT ROW

Same reason as migration 0003, measured there rather than assumed: a trigger that raises cannot
durably record its own rejection, because whatever it inserts belongs to the transaction that is
about to unwind. The trigger rejects loudly; the application audits on a separate connection.
Postgres carries SQLSTATE 'OG002' so the application can recognise this refusal without matching
message text (0003 uses 'OG001' for the preliminary side); SQLite has no SQLSTATE and falls back
to the message marker.
"""
from __future__ import annotations

from alembic import op

revision = "0026_final_lock_guard"
down_revision = "0025_project_notices"
branch_labels = None
depends_on = None


#: Substantive components of the final participant judgment, derived by
#: server/tools/run41_derive_final_fields.py from a_researchdecision and cross-checked against
#: EXPORT_COLUMNS. Kept here as literal text so the migration is self-contained and readable as
#: the historical record of what v26 protects.
PROTECTED_CONTENT = (
    "final_action",
    "disposition",
    "rationale",
    "final_confidence",
    "escalation_level",
    "owner_role",
    "authority_role",
    "resource_constraint",
    "evidence_items",
    "reason_code",
    "deadline",
    "residual_risk",
)

#: The lock predicate itself. Protected so the guard cannot be disarmed before it is evaded.
LOCK_COLUMN = "final_submitted_at"

ALL_PROTECTED = PROTECTED_CONTENT + (LOCK_COLUMN,)

_PG_CHANGED = "\n            OR ".join(
    f"NEW.{c} IS DISTINCT FROM OLD.{c}" for c in ALL_PROTECTED
)

PG_TRIGGER_FN = f"""
CREATE OR REPLACE FUNCTION og_reject_locked_final_response() RETURNS trigger AS $$
BEGIN
    IF OLD.{LOCK_COLUMN} IS NOT NULL
       AND ({_PG_CHANGED}) THEN

        RAISE EXCEPTION
            'final response is locked: the substantive final judgment is immutable after {LOCK_COLUMN} (decision %)',
            OLD.decision_id
            USING ERRCODE = 'OG002';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

PG_TRIGGER = """
CREATE TRIGGER trg_decisions_final_lock_guard
BEFORE UPDATE ON decisions
FOR EACH ROW
EXECUTE FUNCTION og_reject_locked_final_response();
"""

# SQLite has no IS DISTINCT FROM, so NULL-safe comparison is spelled out with sentinels, exactly
# as migration 0003 does for the preliminary side. Text sentinel for text/JSON columns, numeric
# sentinel for the integer confidence, and a text sentinel for the timestamp.
_SQLITE_TEXT = tuple(c for c in PROTECTED_CONTENT if c != "final_confidence")
_sqlite_changed = ["IFNULL(NEW.final_confidence, -999999) <> IFNULL(OLD.final_confidence, -999999)"]
_sqlite_changed += [
    f"IFNULL(NEW.{c}, '<null>') <> IFNULL(OLD.{c}, '<null>')" for c in _SQLITE_TEXT
]
_sqlite_changed.append(
    f"IFNULL(NEW.{LOCK_COLUMN}, '<null>') <> IFNULL(OLD.{LOCK_COLUMN}, '<null>')"
)
_SQLITE_CHANGED = "\n          OR ".join(_sqlite_changed)
_SQLITE_UPDATE_OF = ", ".join(ALL_PROTECTED)

SQLITE_TRIGGER = f"""
CREATE TRIGGER trg_decisions_final_lock_guard
BEFORE UPDATE OF {_SQLITE_UPDATE_OF} ON decisions
FOR EACH ROW
WHEN OLD.{LOCK_COLUMN} IS NOT NULL
     AND ({_SQLITE_CHANGED})
BEGIN
    SELECT RAISE(ABORT, 'final response is locked: the substantive final judgment is immutable after final_submitted_at');
END;
"""


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute(PG_TRIGGER_FN)
        op.execute(PG_TRIGGER)
    elif dialect == "sqlite":
        op.execute(SQLITE_TRIGGER)
    else:
        raise RuntimeError(
            f"No final-lock trigger defined for dialect {dialect!r}. The lock is not optional, "
            "so this migration refuses to leave the final response unprotected."
        )


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    op.execute("DROP TRIGGER IF EXISTS trg_decisions_final_lock_guard ON decisions"
               if dialect == "postgresql" else
               "DROP TRIGGER IF EXISTS trg_decisions_final_lock_guard")
    if dialect == "postgresql":
        op.execute("DROP FUNCTION IF EXISTS og_reject_locked_final_response()")
