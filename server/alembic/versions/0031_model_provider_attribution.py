"""provider attribution: which provider produced a stored reading and a stored extraction

Revision ID: 0031_model_provider_attribution
Revises: 0030_extraction_contract
Create Date: 2026-08-31

WHY A COLUMN AND NOT A DERIVED FACT.

Run 93 made the model that serves the platform a SETTING. From here on, two stored figures may
have been produced by two different providers, and nothing in the row would say so:
`specification_readings.model_id` carried a bare model identifier, and `documents.extraction_model`
the same. A model identifier is not a provider -- the same name can be served by more than one
host, and a deployment that switches provider and switches back leaves rows on both sides of the
change that are indistinguishable afterwards. A figure produced by one model and a figure produced
by another are not the same evidence, so the provider is recorded beside the model, at the point
of storage, on both storage paths.

NULL ON EVERY PRE-0031 ROW, TRUTHFULLY. No value is invented for the existing rows: the provider
they were produced under was not recorded. Every row written after this migration states it. Rows
served by the recorded fixture rather than a model say `recorded`, which is what `served_by`
already says on the same row and is not a provider name.

MIGRATION: /readyz reports 503 with SchemaOutOfDate until `alembic upgrade head` is run against
the target database.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0031_model_provider_attribution"
down_revision = "0030_extraction_contract"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("specification_readings", sa.Column("provider", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("extraction_provider", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "extraction_provider")
    op.drop_column("specification_readings", "provider")
