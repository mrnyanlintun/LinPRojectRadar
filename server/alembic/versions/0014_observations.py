"""observations: the append-only per-field storage layer

Revision ID: 0014_observations
Revises: 0013_document_versioning
Create Date: 2026-08-02

WHAT THIS TABLE MAKES EXPRESSIBLE THAT THE OLD SHAPE COULD NOT

The old storage held one current value per field per project — a flat dict with no reporting
period on any value, no per-field date, no entity identity and no room for two values of one
field at once. Four behaviours have to coexist and the flat dict can express none of them:

  * SERIES — one observation per period; the latest is current and the sequence is charted.
  * REGISTER REPLACE — the latest revision WITHIN a period is that period's observation.
  * EVENT — dated records, each its own thing; a revision supersedes that record, not the
    population.
  * PERMANENT — never superseded or replaced by anything later (the original baseline).

One row per (project, period, document, field, entity). Rows are DERIVED from stored
extractions (`documents.extraction` + `document_uploads.period` + the document's own date), so
this is an additive projection of what is already stored, not a second source of truth — a row
can always be re-derived and compared. Rows are never updated: a revision is a NEW document
whose observations carry `revision_of`, and selection picks between rows rather than anything
overwriting them.

THE TWO AXES THE DESIGN KEEPS DISTINCT, STRUCTURALLY

  * Same (project, field), same PERIOD, later `as_of` or an explicit `revision_of`: a revision.
    Selection takes the later one; the earlier row is retained and never deleted.
  * Same (project, field), DIFFERENT period: a new observation. It becomes a point in the
    series and selection never collapses it into the current value.

`as_of` is the date THIS VALUE speaks about — taken from the document's own date field, never
the upload clock. It is nullable, honestly: many extractions carry no parseable date, and
stamping the wall clock instead is exactly the D3 fault this design refuses to extend. An
undated observation is selected only on the deterministic (rank, doc_type, sha256) order the
merge has always used, and it never beats a dated one.

`entity_state` exists for stateful events. Change orders arrive already executed (approval
happens outside the platform), so their event rows carry 'executed' as a business fact, not a
gate on a state machine the platform does not run.

NO BACKFILL. The site starts fresh: there are no projects and no documents, so there is
nothing to project into this table and no repair logic belongs here.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014_observations"
down_revision = "0013_document_versioning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "observations",
        sa.Column("observation_id", sa.String(26), primary_key=True),
        sa.Column("project_id", sa.Uuid(),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("field", sa.Text(), nullable=False),
        # JSON, because a field's value can be a number or a date string, and coercing dates
        # to a numeric column would re-create the very ambiguity this table removes.
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("kind", sa.Text(), nullable=False),
        # '' (not NULL) for snapshots, so the uniqueness constraint below can include it —
        # NULLs are pairwise distinct in a unique index and would let duplicates in.
        sa.Column("entity_key", sa.Text(), nullable=False, server_default=""),
        sa.Column("entity_state", sa.Text(), nullable=True),
        # The date this value speaks about. Nullable: an undated value is stored as undated,
        # never stamped with the clock.
        sa.Column("as_of", sa.Date(), nullable=True),
        sa.Column("document_id", sa.String(26),
                  sa.ForeignKey("documents.document_id"), nullable=False),
        # supersedes_document_id, promoted from the upload onto every observation the
        # superseding document produces.
        sa.Column("revision_of", sa.String(26), nullable=True),
        sa.Column("source_doc_type", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.CheckConstraint("kind IN ('SNAPSHOT','EVENT','DELTA','PERMANENT')",
                           name="ck_observations_kind"),
    )
    # Idempotence: deriving the same document's observations twice inserts nothing new.
    op.create_index(
        "uq_observations_identity", "observations",
        ["project_id", "period", "document_id", "field", "entity_key"], unique=True,
    )
    op.create_index("ix_observations_project_period", "observations",
                    ["project_id", "period"])
    op.create_index("ix_observations_field", "observations", ["field"])


def downgrade() -> None:
    op.drop_index("ix_observations_field", table_name="observations")
    op.drop_index("ix_observations_project_period", table_name="observations")
    op.drop_index("uq_observations_identity", table_name="observations")
    op.drop_table("observations")
