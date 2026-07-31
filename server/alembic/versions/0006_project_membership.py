"""project membership and account separation

Revision ID: 0006_project_membership
Revises: 0005_transition_rules
Create Date: 2026-07-31

Two requirements that arrived after B1-B6 were built:

  project_members            a project has one PM who decides and any number of observers who
                             watch. Membership is granted per project by an audited admin action;
                             there is no role that sees everything. Revocation sets revoked_at;
                             rows are never deleted, so membership history is itself audit
                             evidence — the same pattern as the existing role assignments.

  participants.account_type  the platform will carry real work as well as research. Operational
                             projects run by practising staff must never enter a research export,
                             and separating them by username alone is procedural and will fail
                             once nobody remembers which usernames were which. The separation is
                             structural: 'research' | 'operational' on the account row, filtered
                             unconditionally at export and refused at consent.

The one-active-PM rule is enforced IN THE DATABASE, not only in the application: a partial
unique index on (project_id) where project_role = 'PM' and revoked_at IS NULL. Adding a second
active PM fails at the database even if the application layer is bypassed with raw SQL. Partial
indexes are supported by both Postgres and SQLite, so the constraint holds in local verification
too.

project_members.project_id is a real foreign key into the facade's projects table. That is a
deliberate departure from the research schema's no-facade-FK rule: membership is ABOUT a facade
project and is meaningless without it, unlike the research measurement tables, which must
outlive the facade world.

MIGRATION: /readyz reports 503 with SchemaOutOfDate until `alembic upgrade head` is run against
the target database.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_project_membership"
down_revision = "0005_transition_rules"
branch_labels = None
depends_on = None

ULID = sa.String(26)


def upgrade() -> None:
    op.create_table(
        "project_members",
        sa.Column("member_id", ULID, primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("user_key", ULID,
                  sa.ForeignKey("participants.participant_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("project_role", sa.Text(), nullable=False),
        sa.Column("added_by", sa.Text(), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", sa.Text(), nullable=True),
        sa.CheckConstraint("project_role IN ('PM','Observer')",
                           name="ck_project_members_role"),
    )
    op.create_index("ix_project_members_project", "project_members", ["project_id"])
    op.create_index("ix_project_members_user", "project_members", ["user_key"])
    # Exactly one active PM per project, enforced by the database. The application refuses a
    # second PM too, but this index is what makes the rule hold when the application is bypassed.
    op.create_index(
        "uq_project_members_one_active_pm",
        "project_members",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("project_role = 'PM' AND revoked_at IS NULL"),
        sqlite_where=sa.text("project_role = 'PM' AND revoked_at IS NULL"),
    )

    with op.batch_alter_table("participants") as batch:
        batch.add_column(sa.Column("account_type", sa.Text(), nullable=False,
                                   server_default="research"))
        batch.create_check_constraint(
            "ck_participants_account_type",
            "account_type IN ('research','operational')",
        )


def downgrade() -> None:
    with op.batch_alter_table("participants") as batch:
        batch.drop_constraint("ck_participants_account_type", type_="check")
        batch.drop_column("account_type")
    op.drop_index("uq_project_members_one_active_pm", table_name="project_members")
    op.drop_index("ix_project_members_user", table_name="project_members")
    op.drop_index("ix_project_members_project", table_name="project_members")
    op.drop_table("project_members")
