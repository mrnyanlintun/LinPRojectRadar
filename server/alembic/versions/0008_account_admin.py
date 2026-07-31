"""account activation, Google SSO linkage, display name

Revision ID: 0008_account_admin
Revises: 0007_feature_flags
Create Date: 2026-07-31

T2 gives operational users a second sign-in path (Google SSO, resolved to a real Participant
row) and gives an admin the power to deactivate an account without deleting its history. Three
columns:

    is_active       BOOLEAN NOT NULL DEFAULT true
    google_email    TEXT NULL, unique when present
    display_name    TEXT NULL

is_active is checked in resolve_caller — the single choke point every authenticated action
already passes through — so deactivating an account takes effect everywhere at once rather than
needing to be re-implemented per endpoint. Defaulting to true means every row created before this
migration, and every row created without the field set, stays reachable; deactivation is
something an admin does, not a state a row can silently fall into.

google_email is nullable and partial-unique (unique only where NOT NULL) rather than NOT NULL
UNIQUE, because most rows — every research participant — will never have one: the two auth paths
in this phase are deliberately separate (username+password for research, so no real identity is
stored; Google SSO for operational, where a real identity is appropriate). A plain UNIQUE
constraint over a mostly-NULL column would still work on Postgres (NULLs are not considered equal
for uniqueness there), but the explicit partial index makes that guarantee independent of which
database is running underneath — it holds identically on the SQLite databases used for local
verification.

display_name is the label an operational account is known by in the interface. Research accounts
never set it: their only identifier anywhere in the system is the pseudonymous code, by design.

MIGRATION: /readyz reports 503 with SchemaOutOfDate until `alembic upgrade head` is run against
the target database.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_account_admin"
down_revision = "0007_feature_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("participants") as batch:
        batch.add_column(sa.Column("is_active", sa.Boolean(), nullable=False,
                                   server_default=sa.true()))
        batch.add_column(sa.Column("google_email", sa.Text(), nullable=True))
        batch.add_column(sa.Column("display_name", sa.Text(), nullable=True))

    op.create_index(
        "uq_participants_google_email",
        "participants",
        ["google_email"],
        unique=True,
        postgresql_where=sa.text("google_email IS NOT NULL"),
        sqlite_where=sa.text("google_email IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_participants_google_email", table_name="participants")
    with op.batch_alter_table("participants") as batch:
        batch.drop_column("display_name")
        batch.drop_column("google_email")
        batch.drop_column("is_active")
