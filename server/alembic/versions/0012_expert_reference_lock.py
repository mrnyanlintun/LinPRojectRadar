"""expert reference period scope and immutability lock

Revision ID: 0012_expert_reference_lock
Revises: 0011_decision_capture_fields
Create Date: 2026-08-01

T6 makes B1's `expert_references` table usable. B1 created the table and the `locked_at` column;
it did not create the lock. Until this migration the column was a timestamp like any other and
nothing stopped an expert reference from being rewritten after it was sealed.

WHY THE REFERENCE MUST BE IMMUTABLE, AND WHY THAT IS A DATABASE CONCERN

The expert reference is the standard every participant decision is scored against. Its evidential
value rests on one claim: it was committed before the expert saw the AI package. An expert who has
read the recommendation cannot then produce an independent reference, because the score would be
contaminated by the very thing it exists to evaluate.

The application refuses a second write, and the interface never offers one. Neither is proof. A
reviewer asking "could a reference have been revised after the package was revealed?" needs an
answer that does not depend on trusting the application layer, and the only place that answer can
live is the database. This is the same argument 0003 made for the participant's preliminary
judgment, and this migration deliberately reuses that mechanism rather than inventing a second
one.

WHAT IS PROTECTED, AND WHAT IS NOT

Once `locked_at` is set, the trigger rejects any UPDATE that would change the seven fields that
constitute the reference — preferred_action, acceptable_alternatives, unsupported_actions,
rationale, required_evidence, escalation_expectation, confidence — or that would move or clear
`locked_at` itself. Re-locking is as much a falsification as editing.

`realism_review` is deliberately NOT protected, because it is the one thing written after the
lock: the expert views the package only once the reference is sealed, and records whether the
package is plausible as a real system output. That review is a separate judgment about the
package, not a revision of the reference, and the trigger's field list is what keeps those two
things apart at the storage layer.

WHY THE TRIGGER DOES NOT WRITE THE AUDIT ROW

Unchanged from 0003, and for the same measured reason: a trigger that raises cannot durably record
its own rejection, because whatever it inserts belongs to the transaction that is about to unwind.
app/research_audit.py writes the audit row on a separate connection. The Postgres exception here
carries SQLSTATE 'OG002' — distinct from the pre-judgment lock's 'OG001', so the application can
tell which lock fired without matching on message text. SQLite carries no SQLSTATE and falls back
to a message marker, exactly as the pre-judgment path does.

WHY A `period` COLUMN IS ADDED

B1 scoped a reference to (scenario, expert). Participant decisions are recorded per period, so a
scenario-level reference cannot be compared against them: a four-period scenario yields four
participant decisions and would have had one reference to score them all. The column is nullable
so any reference already written keeps its meaning, and the unique index that replaces the old
scope is defined over (scenario_id, expert_id, period).

MIGRATION: /readyz reports 503 with SchemaOutOfDate until `alembic upgrade head` is run against
the target database.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012_expert_reference_lock"
down_revision = "0011_decision_capture_fields"
branch_labels = None
depends_on = None


# The fields that constitute the reference. Listed once here and once in each dialect's trigger
# below; the T6 suite asserts the three lists agree, because a field that falls out of one of them
# becomes silently editable after locking.
PROTECTED = (
    "preferred_action",
    "acceptable_alternatives",
    "unsupported_actions",
    "rationale",
    "required_evidence",
    "escalation_expectation",
    "confidence",
    "locked_at",
)


PG_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION og_reject_locked_expert_reference() RETURNS trigger AS $$
BEGIN
    IF OLD.locked_at IS NOT NULL
       AND (NEW.preferred_action IS DISTINCT FROM OLD.preferred_action
            OR NEW.acceptable_alternatives IS DISTINCT FROM OLD.acceptable_alternatives
            OR NEW.unsupported_actions IS DISTINCT FROM OLD.unsupported_actions
            OR NEW.rationale IS DISTINCT FROM OLD.rationale
            OR NEW.required_evidence IS DISTINCT FROM OLD.required_evidence
            OR NEW.escalation_expectation IS DISTINCT FROM OLD.escalation_expectation
            OR NEW.confidence IS DISTINCT FROM OLD.confidence
            OR NEW.locked_at IS DISTINCT FROM OLD.locked_at) THEN

        RAISE EXCEPTION
            'expert reference is locked: the reference is immutable after locked_at (reference %)',
            OLD.reference_id
            USING ERRCODE = 'OG002';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

PG_TRIGGER = """
CREATE TRIGGER trg_expert_references_lock_guard
BEFORE UPDATE ON expert_references
FOR EACH ROW
EXECUTE FUNCTION og_reject_locked_expert_reference();
"""

# SQLite: RAISE(ABORT) undoes the offending statement and reports the error. JSON columns are
# stored as text on this dialect, so the JSON fields compare as strings, which is what we want —
# any textual change to the stored document is a change to the reference.
SQLITE_TRIGGER = """
CREATE TRIGGER trg_expert_references_lock_guard
BEFORE UPDATE OF preferred_action, acceptable_alternatives, unsupported_actions, rationale,
                 required_evidence, escalation_expectation, confidence, locked_at
ON expert_references
FOR EACH ROW
WHEN OLD.locked_at IS NOT NULL
     AND (IFNULL(NEW.preferred_action, '<null>') <> IFNULL(OLD.preferred_action, '<null>')
          OR IFNULL(NEW.acceptable_alternatives, '<null>')
             <> IFNULL(OLD.acceptable_alternatives, '<null>')
          OR IFNULL(NEW.unsupported_actions, '<null>')
             <> IFNULL(OLD.unsupported_actions, '<null>')
          OR IFNULL(NEW.rationale, '<null>') <> IFNULL(OLD.rationale, '<null>')
          OR IFNULL(NEW.required_evidence, '<null>') <> IFNULL(OLD.required_evidence, '<null>')
          OR IFNULL(NEW.escalation_expectation, '<null>')
             <> IFNULL(OLD.escalation_expectation, '<null>')
          OR IFNULL(NEW.confidence, -999999) <> IFNULL(OLD.confidence, -999999)
          OR IFNULL(NEW.locked_at, '<null>') <> IFNULL(OLD.locked_at, '<null>'))
BEGIN
    SELECT RAISE(ABORT, 'expert reference is locked: the reference is immutable after locked_at');
END;
"""


def upgrade() -> None:
    op.add_column("expert_references", sa.Column("period", sa.Text(), nullable=True))

    # One reference per expert per scenario period. Without this, a second INSERT is the trivial
    # way around an immutability trigger that only guards UPDATE.
    op.create_index(
        "uq_expert_references_scenario_expert_period",
        "expert_references",
        ["scenario_id", "expert_id", "period"],
        unique=True,
    )

    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute(PG_TRIGGER_FN)
        op.execute(PG_TRIGGER)
    elif dialect == "sqlite":
        op.execute(SQLITE_TRIGGER)
    else:
        # Refuse rather than migrate without the lock. A deployment that silently lacked this
        # trigger would look identical to one that had it, right up until a reference was edited.
        raise RuntimeError(
            f"No expert reference lock trigger defined for dialect {dialect!r}. The lock is not "
            "optional: it is the guarantee the expert reference rests on."
        )


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_expert_references_lock_guard ON expert_references")
        op.execute("DROP FUNCTION IF EXISTS og_reject_locked_expert_reference()")
    else:
        op.execute("DROP TRIGGER IF EXISTS trg_expert_references_lock_guard")
    op.drop_index("uq_expert_references_scenario_expert_period", table_name="expert_references")
    op.drop_column("expert_references", "period")
