"""document_uploads.archived_at / archived_by: withdrawing ONE document from a project's period

Revision ID: 0027_document_upload_archived
Revises: 0026_final_lock_guard
Create Date: 2026-08-27

WHY THIS IS NOT A COLUMN ON `documents`

`documents` is content-addressed and SHARED: one row per unique file ever, keyed on the sha256
of the bytes, reachable from every project that ever uploaded those bytes. Marking a document
archived there would withdraw it from every project at once. Archival is a statement about a
(project, period, document) — exactly as `supersedes_document_id` (0013) and `folder_path`
(0016) are, and for the same reason — so it lives on the upload EVENT.

WHY ARCHIVE AND NOT DELETE

Nothing is destroyed. `documents.content` is untouched, `/documents/{id}/content` keeps serving
the bytes to any active member, and `a_projectuploadstatus` lists the archived rows separately
so a decision recorded against the withdrawn evidence still resolves. The only thing the mark
changes is membership of the period's LIVE document set (`documents._period_documents`), which
is the one place supersession is already excluded from computation.

WHY TWO COLUMNS AND NOT A BOOLEAN

A boolean cannot answer "when" or "by whom", and this is an audited withdrawal of evidence from
a research instrument. `archived_at` NULL means live; non-NULL means withdrawn and names the
moment. `archived_by` is the participant id taken from the session, never from a request body.
Both are NULL on every pre-0027 row, which is the truthful state: those uploads were never
archived and no value is invented for them.

WHY IT IS NOT ITSELF THE AUDIT RECORD

It is the current state, not the history. The history is an append-only `audit_events` row of
type `documents_archived`, which additionally names the fields withdrawn and the exact
confirmation sentence the person was shown.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0027_document_upload_archived"
down_revision = "0026_final_lock_guard"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document_uploads",
                  sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("document_uploads", sa.Column("archived_by", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("document_uploads", "archived_by")
    op.drop_column("document_uploads", "archived_at")
