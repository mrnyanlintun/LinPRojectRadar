"""structured decision-capture fields

Revision ID: 0011_decision_capture_fields
Revises: 0010_questionnaire_responses
Create Date: 2026-08-01

T4 captures four things the decision form asks for that `decisions` has no column for. B4 built
the sequence and its timestamps; it did not build the structured content of the final decision
beyond action, disposition, rationale and confidence.

  pre_assessment   TEXT   the brief written assessment given WITH the preliminary judgment
  evidence_items   JSONB  which displayed evidence the participant says they relied on
  reason_code      TEXT   the primary reason, from a closed vocabulary
  deadline         TEXT   by-when, where the scenario requires it
  residual_risk    TEXT   what risk the participant accepts remains after acting

pre_assessment is the one of these that belongs to the PRE side of the lock, and it matters more
than its size suggests: it is the only record of the participant's reasoning BEFORE the package
was shown. Without it the pre/post comparison has an action and a number on one side and a full
argument on the other. It is written in the same INSERT as pre_action and pre_locked_at, so it is
covered by the lock from the instant it exists — and it is deliberately NOT protected by the
pre-lock trigger, which guards pre_action and pre_confidence only. Widening that trigger would
change a validated B4 constraint; the application's own resubmission refusal already prevents any
second write through the API, and the trigger remains the last line for the two fields B4 chose.

WHY evidence_items IS JSONB AND NOT A JOIN TABLE

The items a participant can select are whatever the evidence screen displayed — category names
and document filenames drawn from a stored computed_results row and the period's uploads. Those
are not rows in a table with stable ids of their own; they are a rendering of one result. A join
table would need a synthetic id per displayed item per period, invented at render time, and its
foreign keys would describe a screen rather than an entity. Storing the selected labels verbatim
records exactly what the participant was looking at when they chose, which is the thing the
analysis needs.

WHY deadline IS TEXT AND NOT DATE

Participants answer this in the register they actually use — "next reporting cycle", "before the
March board", "30 days". Forcing a DATE would make the common answer unrepresentable and push
the real one into rationale, where it is not analysable. This is the same reasoning that left
owner_role and authority_role as free Text in 0003.

EXPORT IS AN ALLOWLIST, SO THREE EDITS MOVE TOGETHER

research_export.py's EXPORT_COLUMNS is a de-identification allowlist and build_rows raises if the
assembled row and the allowlist disagree. Adding a column to this table therefore also requires
adding it to EXPORT_COLUMNS and to the row assembly, and residual_risk additionally joins
FREE_TEXT_COLUMNS because it is participant-authored prose that may name a person or a project.
All four edits are in this changeset.

MIGRATION: /readyz reports 503 with SchemaOutOfDate until `alembic upgrade head` is run against
the target database.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0011_decision_capture_fields"
down_revision = "0010_questionnaire_responses"
branch_labels = None
depends_on = None

JSONType = JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    with op.batch_alter_table("decisions") as batch:
        batch.add_column(sa.Column("pre_assessment", sa.Text(), nullable=True))
        batch.add_column(sa.Column("evidence_items", JSONType, nullable=True))
        batch.add_column(sa.Column("reason_code", sa.Text(), nullable=True))
        batch.add_column(sa.Column("deadline", sa.Text(), nullable=True))
        batch.add_column(sa.Column("residual_risk", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("decisions") as batch:
        batch.drop_column("residual_risk")
        batch.drop_column("deadline")
        batch.drop_column("reason_code")
        batch.drop_column("evidence_items")
        batch.drop_column("pre_assessment")
