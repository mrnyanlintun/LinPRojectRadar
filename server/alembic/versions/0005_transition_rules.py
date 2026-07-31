"""transition rules and action family mapping

Revision ID: 0005_transition_rules
Revises: 0004_condition_sequences
Create Date: 2026-07-31

Two seed tables, both data rather than code, for the same reason condition sequences are:
a branch structure and an action taxonomy are design decisions the committee owns, and encoding
them in Python would mean a code change and a deploy on every revision, in a place the design
record cannot see.

  transition_rules   one row per candidate branch for a (scenario, period, action_family)
  action_families    one row per literal action, mapping it to a family

Both are versioned and must be frozen before use. Versioning is what makes a completed
transition immutable in meaning: a rule edited later cannot change what an earlier participant
experienced, because the branch_version they were allocated under is recorded on their
transitions row.

An unmapped action is an error, never a silent default. There is deliberately no fallback family:
a default would silently absorb a typo or a newly added action and route a participant down a
branch nobody chose.

MIGRATION: /readyz reports 503 with SchemaOutOfDate until `alembic upgrade head` is run against
the target database.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_transition_rules"
down_revision = "0004_condition_sequences"
branch_labels = None
depends_on = None

ULID = sa.String(26)


def upgrade() -> None:
    op.create_table(
        "action_families",
        sa.Column("map_id", ULID, primary_key=True),
        # The literal action a participant submits, lowercased on write.
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("family", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.UniqueConstraint("action", "version", name="uq_action_families_action_version"),
    )
    op.create_index("ix_action_families_lookup", "action_families", ["action", "version"])

    op.create_table(
        "transition_rules",
        sa.Column("rule_id", ULID, primary_key=True),
        sa.Column("scenario_id", ULID, nullable=False),
        # Period the rule applies to, matching decisions.period.
        sa.Column("period", sa.Text(), nullable=False),
        sa.Column("action_family", sa.Text(), nullable=False),
        sa.Column("branch_id", sa.Text(), nullable=False),
        sa.Column("branch_version", sa.Text(), nullable=False),
        # Stored as text so an exact decimal survives the round trip; a float would make a
        # preregistered 0.30 into 0.29999999999999999 in the audit record.
        sa.Column("probability", sa.Text(), nullable=False),
        sa.Column("next_state_id", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.UniqueConstraint("scenario_id", "period", "action_family", "branch_id", "version",
                            name="uq_transition_rules_branch"),
    )
    op.create_index("ix_transition_rules_lookup", "transition_rules",
                    ["scenario_id", "period", "action_family", "version"])


def downgrade() -> None:
    op.drop_table("transition_rules")
    op.drop_table("action_families")
