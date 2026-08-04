"""training_runs: the deterministic state store behind the training loop

Revision ID: 0019_training_runs
Revises: 0018_project_training
Create Date: 2026-08-04

ONE TABLE, BESIDE THE OBSERVATIONS STORE, NEVER INSIDE IT.

A training run holds a small deterministic state (cost and schedule performance, float,
contingency, the open dispute and its notice clock, owner credibility) that
`training_engine.advance` — a pure function — moves one period per decision. The state and its
full decision history are JSON on this row; the analytical outputs are NOT stored here, because
period generation projects the state into `signalInputs` and runs the platform's normal
computation, which stores `computed_results` rows exactly as a real project's compute does. The
run points at a project with `is_training = true` (0018), so every isolation filter run 1 built
covers everything this table causes to exist.

NO BACKFILL. Nothing could have produced a training run before this table existed.

Production note: applied to throwaway SQLite only. Production has NOT been migrated, and 0018
from run 1 is also still unapplied there. Both must run before the first training run starts.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0019_training_runs"
down_revision = "0018_project_training"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "training_runs",
        sa.Column("run_id", sa.String(26), primary_key=True),
        sa.Column("project_id", sa.Uuid(),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("participant_id", sa.String(26),
                  sa.ForeignKey("participants.participant_id"), nullable=False),
        sa.Column("contract_form", sa.Text(), nullable=False),
        sa.Column("contract_value", sa.Float(), nullable=False),
        sa.Column("conditions", sa.Text(), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("state", sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"),
                  nullable=False),
        sa.Column("history", sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"),
                  nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('active','complete')", name="ck_training_runs_status"),
    )
    op.create_index("ix_training_runs_participant", "training_runs", ["participant_id"])


def downgrade() -> None:
    op.drop_index("ix_training_runs_participant", table_name="training_runs")
    op.drop_table("training_runs")
