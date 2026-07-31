"""condition sequences seed table

Revision ID: 0004_condition_sequences
Revises: 0003_research_schema
Create Date: 2026-07-31

Counterbalancing sequences are data, not code.

A preregistered condition order is a design decision the committee owns. Encoding it in Python
would mean a code change, a review and a deploy every time the design is revised, and it would put
the allocation rule somewhere the design record cannot see. Here it is queryable, versioned, and
freezable, and the version actually used is recorded on every allocation so an assignment can be
reproduced years later even after the sequence is revised.

One row per position in a sequence, rather than an array column, so a single position can be read,
indexed and constrained on its own.

MIGRATION: /readyz reports 503 with SchemaOutOfDate until `alembic upgrade head` is run against
the target database.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_condition_sequences"
down_revision = "0003_research_schema"
branch_labels = None
depends_on = None

ULID = sa.String(26)


def upgrade() -> None:
    op.create_table(
        "condition_sequences",
        sa.Column("sequence_id", ULID, primary_key=True),
        sa.Column("order_group", sa.Text(), nullable=False),
        sa.Column("scenario_set", sa.Text(), nullable=False),
        # 1-based, matching assignments.sequence_number.
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("config_code", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        # A sequence must be frozen before it can be used to allocate, exactly as a configuration
        # must be frozen before it can be assigned.
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("config_code IN ('C0','C1','C2')", name="ck_condition_sequences_code"),
        sa.CheckConstraint("position >= 1", name="ck_condition_sequences_position"),
        # One config per position per version of a group's sequence. This is what makes an
        # allocation reproducible: the same version can never yield two answers.
        sa.UniqueConstraint("order_group", "scenario_set", "version", "position",
                            name="uq_condition_sequences_position"),
    )
    op.create_index("ix_condseq_lookup", "condition_sequences",
                    ["order_group", "scenario_set", "version"])


def downgrade() -> None:
    op.drop_table("condition_sequences")
