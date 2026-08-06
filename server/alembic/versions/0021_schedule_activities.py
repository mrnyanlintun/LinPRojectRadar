"""schedule_activities: the schedule kept as structured data, one observation per period

Revision ID: 0021_schedule_activities
Revises: 0020_abstained_modules
Create Date: 2026-08-05

WHY A TABLE AND NOT A RENDERED CHART

A chart cannot be compared across periods. The activity table a schedule update carries was
already stored — as raw `milestones_json` on the document row, keyed by the source's own
column headings and holding dates (`29-May`, `14 August 2026`, `24-Mar-26 A`) that the only
date parser in `server/app` could not read. Nothing could ask that blob whether an activity had
moved, which is why Milestone Trend Analysis had never computed.

ONE ROW PER (project, period, document, activity), which is the observations store's rule
applied to a schedule: the same activity seen in four reporting periods is FOUR ROWS, one per
period, not four rows competing to be current. An earlier period's account of an activity is
never rewritten by a later one, so recomputing that earlier period reproduces it.

DATES ARE STORED WITH THEIR KIND. `current_finish_kind` is 'actual' where the source marked the
date actual (the trailing `A` of a Primavera P6 / Microsoft Project export) and 'forecast'
otherwise. An actual date and a forecast date are different facts: one is what happened, one is
what is predicted, and only the second can slip. Stripping the marker to normalise the date
would destroy that distinction, so it is a column.

REFUSALS ARE STORED TOO. `unparsed` holds one entry per cell that would not parse, with the
reason, and `usable_for_trend` is false when the current finish is among them. A row that
cannot be read is a MISSING ROW, recorded as missing. It is never a slip of zero, and no year
is inferred for a date that did not state one.

NO BACKFILL. Rows are derived from stored extractions and are re-derived idempotently by the
unique index below; there is nothing to repair here.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0021_schedule_activities"
down_revision = "0020_abstained_modules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "schedule_activities",
        sa.Column("schedule_activity_id", sa.String(26), primary_key=True),
        sa.Column("project_id", sa.Uuid(),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.String(26),
                  sa.ForeignKey("documents.document_id"), nullable=False),
        # The row's own identifier as the table printed it (e.g. "D100"), falling back to the
        # description where the table has no identifier column. This is what a trend matches
        # on across periods; positional matching would compare two different activities.
        sa.Column("activity_key", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # ISO strings, because a date that refused is stored as NULL alongside its reason and
        # a Date column could not hold "why not".
        sa.Column("baseline_start", sa.Text(), nullable=True),
        sa.Column("baseline_start_kind", sa.Text(), nullable=True),
        sa.Column("baseline_finish", sa.Text(), nullable=True),
        sa.Column("baseline_finish_kind", sa.Text(), nullable=True),
        sa.Column("current_finish", sa.Text(), nullable=True),
        sa.Column("current_finish_kind", sa.Text(), nullable=True),
        sa.Column("percent_complete", sa.Float(), nullable=True),
        sa.Column("unparsed", sa.JSON(), nullable=True),
        sa.Column("usable_for_trend", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
        sa.Column("as_of", sa.Date(), nullable=True),
        sa.Column("source_doc_type", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.CheckConstraint(
            "current_finish_kind IS NULL OR current_finish_kind IN ('actual','forecast')",
            name="ck_schedule_activities_finish_kind",
        ),
    )
    # Idempotence: re-deriving the same document's schedule inserts nothing new.
    op.create_index(
        "uq_schedule_activities_identity", "schedule_activities",
        ["project_id", "period", "document_id", "activity_key"], unique=True,
    )
    op.create_index("ix_schedule_activities_project_period", "schedule_activities",
                    ["project_id", "period"])


def downgrade() -> None:
    op.drop_index("ix_schedule_activities_project_period",
                  table_name="schedule_activities")
    op.drop_index("uq_schedule_activities_identity", table_name="schedule_activities")
    op.drop_table("schedule_activities")
