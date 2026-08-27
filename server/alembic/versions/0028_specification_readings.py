"""specification_readings: what a written specification read, per project, period and category

Revision ID: 0028_specification_readings
Revises: 0027_document_upload_archived
Create Date: 2026-08-27

WHY A NEW TABLE AND NOT A COLUMN ON `computed_results`

`computed_results` is append-only and a database trigger (migration 0009) rejects any UPDATE to a
row a submitted decision references. Writing a category's readings back onto it would mean
superseding the whole result every time one category is pressed, which would break the
one-row-per-computation meaning that every downstream surface reads. A category call is its own
event and gets its own append-only row.

WHY IT STORES THE STATE AS TEXT AND NOT AS A BOOLEAN OR A NULL

There are FOUR outcomes and the Run 76 order forbids blurring them: computed, abstained,
out_of_order, failed. A boolean cannot carry four values and a NULL cannot distinguish "the
evidence is not there" from "the platform could not apply the specification". `state` is the
word itself, so a reader of the raw row can tell them apart without consulting any code.

WHY `served_by` IS NOT OPTIONAL

A reading produced by a live model and a reading served by a recorded fixture must never be
confused, in the database least of all. Every row says which produced it.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0028_specification_readings"
down_revision = "0027_document_upload_archived"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "specification_readings",
        sa.Column("reading_id", sa.Text(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("category_key", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("counts", sa.JSON(), nullable=True),
        sa.Column("modules", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("missing_upstream", sa.JSON(), nullable=True),
        sa.Column("served_by", sa.Text(), nullable=False),
        sa.Column("model_id", sa.Text(), nullable=True),
        sa.Column("specification_sha256", sa.Text(), nullable=True),
        sa.Column("simulation_version", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("superseded_by", sa.Text(), nullable=True),
    )
    op.create_index("ix_specification_readings_scope", "specification_readings",
                    ["project_id", "period", "category_key"])


def downgrade() -> None:
    op.drop_index("ix_specification_readings_scope", table_name="specification_readings")
    op.drop_table("specification_readings")
