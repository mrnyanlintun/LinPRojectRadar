"""document versioning: explicit supersession, and result provenance

Revision ID: 0013_document_versioning
Revises: 0012_expert_reference_lock
Create Date: 2026-08-02

THE DEFECT THIS FIXES, AS MEASURED RATHER THAN ASSUMED

A revised document for a project and period does not replace the one it revises, and it does not
collide with it. It is stored alongside, and BOTH reach computation. `_period_documents` filters
on (project, period) and de-duplicates on sha256 only, so two versions of the same pay
application are two distinct members of the period's document set.

Which version's figures survive the merge is then decided by `_ordered_docs`, whose sort key is
(rank, doc_type, sha256). Two versions of one document share a rank and a doc_type, so the
tiebreak is the SHA256 -- a content hash. The consequences, all measured:

  * First-wins fields (monthly_report ev/ac/pv/bac): the LOWER hash wins.
  * Last-wins fields (pay_application ac, actualPctComplete): the HIGHER hash wins.
  * Additive fields (rfiCount): both are counted. An RFI log revised from 10 to 12 yields 22.
  * keep_max fields (rfiNumber): a downward correction is silently discarded.

So a single revision can produce a signalInputs that mixes fields from both versions, and the
direction of the error is opposite for first-wins and last-wins fields. It is deterministic and
meaningless, which is worse than random: it reproduces exactly, so it looks stable.

WHY `supersedes_document_id` ON `document_uploads`, AND NOT ON `documents`

`documents` is content-addressed: one row per unique file for the lifetime of the platform,
shared by every project that uploads those bytes. Supersession is not a property of the bytes.
The same file can be current evidence in one project and superseded in another, and marking the
shared row would leak one project's revision into every other project holding the same document.
That would also break the property `documents` exists to provide -- two PMs uploading the
identical file get byte-identical signalInputs because they read the same extraction row.

`document_uploads` is scoped to (project, period), which is exactly the scope in which "this
supersedes that" is a true or false statement. The claim is recorded on the row created by the
act that makes it, so `uploaded_by` and `uploaded_at` already say who asserted it and when.

WHY THE POINTER RUNS NEW -> OLD, RATHER THAN `superseded_by` OLD -> NEW

`computed_results` uses `superseded_by`, and the opposite direction here is deliberate:

  * Append-only. The superseding upload is INSERTED carrying the pointer; the superseded row is
    never updated. Nothing rewrites a row that a stored decision may already reference.
  * A revision can itself be revised. C supersedes B supersedes A is expressible as a chain of
    inserts. With `superseded_by` on the old row, superseding B would mean rewriting a pointer
    that had already been written, and the "current" answer would depend on update ordering.
  * The claim belongs to the act of uploading, not to the document being replaced.

The cost is that "is this document superseded" is a reverse lookup rather than a column read.
That is one indexed query, and `ix_document_uploads_supersedes` exists for it.

`computed_results.source_documents` RECORDS WHICH VERSIONS PRODUCED A RESULT

Before this, a stored result carried its merged `signal_inputs` but no document identity, so
"which version of the pay application produced this Amber" was unanswerable after a revision.
`signal_inputs.sources` records a docType per field, never a document. The new column lists the
documents actually used, so a result stays interpretable once the period's document set moves on.

NO BACKFILL, AND WHY THAT IS CORRECT

Both columns are nullable and are left NULL on existing rows. `supersedes_document_id` NULL means
"this upload superseded nothing", which is true of every upload made before this migration.
`source_documents` NULL means "this result predates provenance recording", which is honest;
inventing a document list for an old result by re-reading today's period set would attribute to
it a set that may already have changed, which is exactly the confusion the column exists to end.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0013_document_versioning"
down_revision = "0012_expert_reference_lock"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable and un-backfilled: NULL means "superseded nothing", true of every existing row.
    op.add_column(
        "document_uploads",
        sa.Column("supersedes_document_id", sa.String(length=26), nullable=True),
    )
    # The reverse lookup "which upload supersedes this document" is how the period's live set is
    # computed on every compute, so it is indexed rather than left to a scan.
    op.create_index(
        "ix_document_uploads_supersedes",
        "document_uploads",
        ["project_id", "period", "supersedes_document_id"],
    )
    # Deliberately NOT a foreign key to documents.document_id. The referenced document is
    # identified by the uploader in the request, and a bad id must fail as a validated refusal
    # naming the offending value, not as an integrity error surfacing from the driver. The
    # application checks that the id exists AND is in this project and period, which is a
    # stronger condition than a foreign key could express.

    op.add_column(
        "computed_results",
        sa.Column("source_documents", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("computed_results", "source_documents")
    op.drop_index("ix_document_uploads_supersedes", table_name="document_uploads")
    op.drop_column("document_uploads", "supersedes_document_id")
