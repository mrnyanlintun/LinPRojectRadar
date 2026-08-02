"""research_exports.kind: which of the two export scopes produced this record

Revision ID: 0015_export_kind
Revises: 0014_observations
Create Date: 2026-08-02

The export now produces two things, selected by the caller: participant_inputs (per
participant, filtered to research accounts, a date window over decision completion) and
project_health (per project, not filtered by account type, a date window over the computation
timestamp). A fetch re-derives the payload from the stored `date_range` and now also needs to
know which builder to re-derive it WITH, since the two scopes read different tables and produce
different sheets.

NOT NULL with a server default of 'participant_inputs': the only kind that existed before this
column, so an export row created earlier is correctly described without a backfill script — the
default IS the backfill, because there was only ever one possible value for it to have been.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0015_export_kind"
down_revision = "0014_observations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "research_exports",
        sa.Column("kind", sa.Text(), nullable=False, server_default="participant_inputs"),
    )


def downgrade() -> None:
    op.drop_column("research_exports", "kind")
