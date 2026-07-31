"""facade schema: projects, project_snapshots, files

Revision ID: 0001_facade_schema
Revises:
Create Date: 2026-07-30

JSONB first. The whole project.json is stored in projects.doc rather than shredded into columns,
because the Apps Script backend has no fixed project schema and any unanticipated key would
otherwise be silently dropped.

Types use dialect variants so this migration runs on Postgres (JSONB, native uuid) and on SQLite,
which is what local contract verification uses.

No research tables. Those arrive at B1.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001_facade_schema"
down_revision = None
branch_labels = None
depends_on = None

JSONType = JSONB().with_variant(sa.JSON(), "sqlite")
UUIDType = sa.Uuid(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", UUIDType, primary_key=True),
        # The display id the frontend uses, for example "PRJ-08421".
        sa.Column("legacy_id", sa.Text(), nullable=False),
        sa.Column("doc", JSONType, nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("legacy_id", name="uq_projects_legacy_id"),
    )
    op.create_index("ix_projects_legacy_id", "projects", ["legacy_id"])
    op.create_index("ix_projects_archived", "projects", ["archived"])

    op.create_table(
        "project_snapshots",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("project_id", UUIDType, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.Text(), nullable=True),
        sa.Column("snapshot", JSONType, nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_project_snapshots_project_id", "project_snapshots", ["project_id"])

    op.create_table(
        "files",
        sa.Column("id", UUIDType, primary_key=True),
        sa.Column("project_id", UUIDType, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("drive_file_id", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("doc_type", sa.Text(), nullable=True),
        sa.Column("sha256", sa.String(64), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_files_project_id", "files", ["project_id"])
    op.create_index("ix_files_drive_file_id", "files", ["drive_file_id"])
    op.create_index("ix_files_doc_type", "files", ["doc_type"])


def downgrade() -> None:
    op.drop_table("files")
    op.drop_table("project_snapshots")
    op.drop_table("projects")
