"""project_snapshots.project_id nullable for the portfolio-health singleton

Revision ID: 0002_snapshot_project_nullable
Revises: 0001_facade_schema
Create Date: 2026-07-31

Portfolio health is a portfolio-wide snapshot with no owning project. The live model keeps it as a
single portfolio_health.json at the Drive root, not under any project folder, so there is no
project to reference.

Storing it with a synthetic owner would have been worse: it would surface in that project's
gethistory and corrupt its history. Instead project_id becomes nullable and the row is identified
by the reserved period value in facade.PORTFOLIO_HEALTH_PERIOD, which a_gethistory explicitly
excludes.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_snapshot_project_nullable"
down_revision = "0001_facade_schema"
branch_labels = None
depends_on = None

UUIDType = sa.Uuid(as_uuid=True)


def upgrade() -> None:
    # batch_alter_table so this also runs on SQLite, which cannot ALTER a column in place and
    # needs the table rebuilt. Local contract verification runs on SQLite.
    with op.batch_alter_table("project_snapshots") as batch:
        batch.alter_column("project_id", existing_type=UUIDType, nullable=True)


def downgrade() -> None:
    # Rows with a NULL project_id cannot satisfy the restored constraint, so remove them first.
    op.execute(sa.text("DELETE FROM project_snapshots WHERE project_id IS NULL"))
    with op.batch_alter_table("project_snapshots") as batch:
        batch.alter_column("project_id", existing_type=UUIDType, nullable=False)
