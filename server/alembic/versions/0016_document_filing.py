"""document filing: where each upload was filed, what it is, and how sure the classifier was

Revision ID: 0016_document_filing
Revises: 0015_export_kind
Create Date: 2026-08-02

FOUR COLUMNS, AND DELIBERATELY NO NEW TABLE.

The obvious shape for a folder tree is a `folders` table. It is not needed here and would be
actively worse. The Arora project directory is a TEMPLATE a project manager prunes: the source
document says to delete the disciplines outside Arora's scope, to delete either the CAD or the
REVIT folder, and that the PM creates the room-by-room photo folders by hand. Materialising it
would mean writing about sixty folder rows per project and then asking someone to delete most
of them, and every one of those rows would be a row nothing has ever put a document in.

So the template lives in code (`app/jdrive_tree.py`) and a project's real tree is computed as
the template plus the distinct `document_uploads.folder_path` values for that project. An empty
folder therefore never exists to be pruned, the CAD/REVIT choice resolves itself because
whichever one receives a file is the one that appears, and a folder the template describes only
as a pattern (`YYYY-MM-DD SITE OBS #`, `CLAIM #`) comes into existence as a real name the
moment something is filed into it.

WHY THE THREE FILING COLUMNS SIT ON `document_uploads` AND NOT ON `documents`

`documents` is content-addressed and shared between projects: one row per unique file, ever.
Where a file belongs, what it counts as, and whether its placement has been reviewed are all
statements about a (project, period, document), not about the bytes. The same specification
could be reference material in one project and never appear in another. This is the same
argument migration 0013 made for `supersedes_document_id`, and it is made again here rather
than assumed.

WHY `classification_confidence` SITS ON `documents` INSTEAD

Confidence qualifies the classification, and the classification is of the bytes. Two projects
holding the same file hold the same classification at the same confidence, for the same reason
they share its extraction.

The classify prompt has asked the model for `{"docType", "confidence"}` since the port. Until
this column existed the confidence was parsed out of the response and then dropped, so nothing
on the platform had ever read it. NULL is meaningful and does NOT mean "fine": it means the
model's own claim was not what decided the type, so there is no confidence in the answer that
was actually used. See `jdrive_tree.needs_review`.

NO BACKFILL. The site starts fresh: there are no uploads to file retrospectively.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0016_document_filing"
down_revision = "0015_export_kind"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document_uploads", sa.Column("folder_path", sa.Text(), nullable=True))
    op.add_column("document_uploads", sa.Column("filing_class", sa.Text(), nullable=True))
    op.add_column(
        "document_uploads",
        sa.Column("needs_filing_review", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
    )
    # The Files tab lists one folder at a time, so the lookup is always
    # (project_id, folder_path). Indexed together rather than separately for that reason.
    op.create_index("ix_document_uploads_folder", "document_uploads",
                    ["project_id", "folder_path"])
    op.add_column("documents",
                  sa.Column("classification_confidence", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "classification_confidence")
    op.drop_index("ix_document_uploads_folder", table_name="document_uploads")
    op.drop_column("document_uploads", "needs_filing_review")
    op.drop_column("document_uploads", "filing_class")
    op.drop_column("document_uploads", "folder_path")
