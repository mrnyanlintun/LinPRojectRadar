"""per-user feature flags

Revision ID: 0007_feature_flags
Revises: 0006_project_membership
Create Date: 2026-07-31

Some features must be unavailable during a research decision period but are wanted for real
project work. The switch is per user, set by an admin, and stored as a small JSON object rather
than four boolean columns: the recognised key set will grow as features are added, and a column
per feature would mean a migration and a deploy for each one.

    features   JSONB NOT NULL DEFAULT '{}'

An ABSENT key is not "off". It resolves from participants.account_type — operational accounts
default to enabled, research accounts to disabled — so an admin who forgets to configure a
research participant gets the restrictive behaviour. Forgetting to enable a feature for a VP is
an annoyance; forgetting to disable one for a participant is contaminated data. The resolution
lives in app/features.py, deliberately in one function, so no call site can invent its own
default.

The column is NOT NULL with a default rather than nullable, so "never configured" and
"configured to nothing" are the same value and there is no third state to reason about.

MIGRATION: /readyz reports 503 with SchemaOutOfDate until `alembic upgrade head` is run against
the target database.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_feature_flags"
down_revision = "0006_project_membership"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # JSONB on Postgres, JSON on SQLite, so the same migration runs in local verification.
    json_type = (postgresql.JSONB() if bind.dialect.name == "postgresql" else sa.JSON())
    default = sa.text("'{}'::jsonb") if bind.dialect.name == "postgresql" else sa.text("'{}'")
    with op.batch_alter_table("participants") as batch:
        batch.add_column(sa.Column("features", json_type, nullable=False,
                                   server_default=default))


def downgrade() -> None:
    with op.batch_alter_table("participants") as batch:
        batch.drop_column("features")
