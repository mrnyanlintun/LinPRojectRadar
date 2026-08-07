"""upload_attempts: what was uploaded and what happened to it, recorded at upload time

Revision ID: 0022_upload_attempts
Revises: 0021_schedule_activities
Create Date: 2026-08-05

WHY THIS CANNOT BE DERIVED FROM WHAT IS STORED

Extraction refuses a WHOLE document rather than storing part of it. That rule is deliberate and
is not being changed here: a half-stored extraction puts a coerced figure into the research
record. But it has a consequence nobody had recorded. A document that fails extraction leaves
no `documents` row and no `document_uploads` row, so it is not merely marked bad, it is ABSENT.
Nothing downstream can be asked which files did not make it, because from storage's point of
view they were never offered.

Until now the only account of a failure was a sentence in a dialog on the uploader's screen,
which is gone the moment the dialog closes. Someone uploading twenty-seven documents could not
afterwards see which three failed, and could not retry one without re-uploading the set.

So the attempt is recorded when it is MADE, beside the outcome, for every file in the batch and
whether it succeeded or not. One row per (project, period, batch, filename). The batch id groups
the files that arrived together so a later reader can say "three of the twenty-seven in that
upload failed" rather than presenting a flat list.

`error` HOLDS THE WORDS OF THE ACTUAL FAILURE. Not a category, not a code. The reason a document
was refused is written by the thing that refused it — an out-of-range document risk score names
the score, a truncated model response names the field it stopped at — and paraphrasing it into
"extraction failed" is how the platform lost three retries to a message that described the wrong
failure.

APPEND ONLY. A retry writes a NEW row. The failed attempt stays, because the record of what a
document did the first time is evidence about the document, and overwriting it would make a
document that failed twice look like one that failed once.

NO BACKFILL. Attempts before this table existed were never recorded anywhere and cannot be
reconstructed; inventing rows for them would be inventing evidence.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0022_upload_attempts"
down_revision = "0021_schedule_activities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "upload_attempts",
        sa.Column("upload_attempt_id", sa.String(26), primary_key=True),
        sa.Column("project_id", sa.Uuid(),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        # Groups the files that arrived in one request. A retry of one file is its own batch of
        # one, which is what makes "retry per document" visible as such in the record.
        sa.Column("batch_id", sa.String(26), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        # The content hash, so a successful attempt can be joined to the document it produced.
        # NULL is impossible here: the bytes are hashed before anything else happens.
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        # 'extracted', 'matched' (served from the extraction cache), 'filed' (reference
        # material, stored with no extraction attempted) or 'failed'. The same four words the
        # upload response uses, so the durable record and the dialog cannot drift apart.
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("doc_type", sa.Text(), nullable=True),
        # The words of the actual failure, verbatim. NULL when nothing failed.
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("attempted_by", sa.Text(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('extracted','matched','filed','failed')",
            name="ck_upload_attempts_status",
        ),
        sa.CheckConstraint(
            "status <> 'failed' OR error IS NOT NULL",
            name="ck_upload_attempts_failure_has_reason",
        ),
    )
    op.create_index("ix_upload_attempts_project_period", "upload_attempts",
                    ["project_id", "period"])
    op.create_index("ix_upload_attempts_batch", "upload_attempts", ["batch_id"])


def downgrade() -> None:
    op.drop_index("ix_upload_attempts_batch", table_name="upload_attempts")
    op.drop_index("ix_upload_attempts_project_period", table_name="upload_attempts")
    op.drop_table("upload_attempts")
