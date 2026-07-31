"""documents, upload events, and stored computed results

Revision ID: 0009_documents_and_results
Revises: 0008_account_admin
Create Date: 2026-07-31

The analytical layer has been ported and validated, and the research chain is built, but until
now nothing could get a document into the system. This migration is the storage half of that
path: upload -> hash -> extract once -> compute -> store one result that every later surface
READS rather than recomputes.

THREE TABLES, AND WHY THEY ARE THREE

`documents` is keyed on the sha256 of the bytes, one row per unique file, ever. The extraction
lives HERE and not on the upload event, which is the whole point: two PMs who upload the same
file get byte-identical signalInputs because they are reading the SAME extraction row, not
because some later step compared two extractions and found them equal. Identity of the research
stimulus is established by construction rather than by verification. It also means one model
call per unique document for the lifetime of the platform.

`document_uploads` is one row per upload EVENT. Three PMs uploading the same file produce three
rows here and one row in `documents`. This is what makes "which documents does project X have
for period 2" answerable without conflating it with "what have we ever extracted", and it is
where `was_cached` records whether that particular upload paid for a model call.

`computed_results` is one row per (project, period) computation. Append-only: a recompute writes
a NEW row and sets `superseded_by` on the old one. The old row stays readable forever, because a
decision that referenced it must still resolve years later.

WHY THE THREE PROVENANCE COLUMNS ARE NOT NULL

`simulation_version`, `seed` and `period_cutoff` are NOT NULL by design, not by oversight. A
stored result without them cannot be reproduced, and — worse — a later change to the analytical
layer becomes undetectable in already-collected data. A nullable column here would let a row be
written that is indistinguishable from a reproducible one but is not. The database refuses.

BYTES IN POSTGRES

`content` is BYTEA. One service, one credential, one backup domain; database storage autoscales
to 5 GB and the documents are PDFs of a few hundred KB. Object storage would add a second
failure domain and a second set of credentials for no benefit at this size.

THE IMMUTABILITY TRIGGER

`decisions.result_id` is added here — it is the reference from a recorded decision to the
computed result the participant actually saw. Once a decision has been SUBMITTED, the result it
references is frozen: rewriting the numbers underneath a submitted decision would silently
change what the collected data means. The application refuses it, and so does the database,
because an application-only guarantee is one careless `session.execute(update(...))` away from
being no guarantee at all.

The trigger permits exactly one change to a referenced row: setting `superseded_by`. Superseding
is how a recompute is recorded, and it does not alter a single stored value — it annotates the
old row as having been replaced. Superseding is permitted; changing is not.

MIGRATION: /readyz reports 503 with SchemaOutOfDate until `alembic upgrade head` is run against
the target database.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import BYTEA, JSONB

revision = "0009_documents_and_results"
down_revision = "0008_account_admin"
branch_labels = None
depends_on = None

ULID = sa.String(26)
# Same pattern as 0003: JSONB on Postgres, plain JSON on SQLite so local verification runs.
JSONType = JSONB().with_variant(sa.JSON(), "sqlite")
# LargeBinary maps to BYTEA on Postgres and BLOB on SQLite without a variant.
BytesType = BYTEA().with_variant(sa.LargeBinary(), "sqlite")
TS = sa.DateTime(timezone=True)


# The guarded columns. `superseded_by` is deliberately absent: annotating a row as replaced is
# not a modification of what it recorded. `result_id` is absent because it is the primary key.
_GUARDED = (
    "project_id", "period", "signal_inputs", "module_results", "category_statuses",
    "project_status", "portfolio_snapshot", "simulation_version", "seed", "period_cutoff",
    "computed_at",
)

PG_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION og_reject_referenced_result_update() RETURNS trigger AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM decisions d
        WHERE d.result_id = OLD.result_id
          AND d.pre_submitted_at IS NOT NULL
    ) AND (
        NEW.project_id IS DISTINCT FROM OLD.project_id
        OR NEW.period IS DISTINCT FROM OLD.period
        OR NEW.signal_inputs::text IS DISTINCT FROM OLD.signal_inputs::text
        OR NEW.module_results::text IS DISTINCT FROM OLD.module_results::text
        OR NEW.category_statuses::text IS DISTINCT FROM OLD.category_statuses::text
        OR NEW.project_status IS DISTINCT FROM OLD.project_status
        OR NEW.portfolio_snapshot::text IS DISTINCT FROM OLD.portfolio_snapshot::text
        OR NEW.simulation_version IS DISTINCT FROM OLD.simulation_version
        OR NEW.seed IS DISTINCT FROM OLD.seed
        OR NEW.period_cutoff IS DISTINCT FROM OLD.period_cutoff
        OR NEW.computed_at IS DISTINCT FROM OLD.computed_at
    ) THEN
        RAISE EXCEPTION
            'computed result is referenced by a submitted decision and is immutable; supersede it instead (result %)',
            OLD.result_id
            USING ERRCODE = 'OG002';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

PG_TRIGGER = """
CREATE TRIGGER trg_computed_results_referenced_guard
BEFORE UPDATE ON computed_results
FOR EACH ROW
EXECUTE FUNCTION og_reject_referenced_result_update();
"""

# SQLite has no IS DISTINCT FROM, hence the IFNULL sentinels — the same idiom 0003 uses. The
# trigger is scoped with UPDATE OF so that writing superseded_by never even fires it.
SQLITE_TRIGGER = """
CREATE TRIGGER trg_computed_results_referenced_guard
BEFORE UPDATE OF project_id, period, signal_inputs, module_results, category_statuses,
                 project_status, portfolio_snapshot, simulation_version, seed,
                 period_cutoff, computed_at ON computed_results
FOR EACH ROW
WHEN EXISTS (SELECT 1 FROM decisions d
             WHERE d.result_id = OLD.result_id AND d.pre_submitted_at IS NOT NULL)
     AND (IFNULL(NEW.project_id,'<n>') <> IFNULL(OLD.project_id,'<n>')
          OR IFNULL(NEW.period,-999999) <> IFNULL(OLD.period,-999999)
          OR IFNULL(NEW.signal_inputs,'<n>') <> IFNULL(OLD.signal_inputs,'<n>')
          OR IFNULL(NEW.module_results,'<n>') <> IFNULL(OLD.module_results,'<n>')
          OR IFNULL(NEW.category_statuses,'<n>') <> IFNULL(OLD.category_statuses,'<n>')
          OR IFNULL(NEW.project_status,'<n>') <> IFNULL(OLD.project_status,'<n>')
          OR IFNULL(NEW.portfolio_snapshot,'<n>') <> IFNULL(OLD.portfolio_snapshot,'<n>')
          OR IFNULL(NEW.simulation_version,'<n>') <> IFNULL(OLD.simulation_version,'<n>')
          OR IFNULL(NEW.seed,'<n>') <> IFNULL(OLD.seed,'<n>')
          OR IFNULL(NEW.period_cutoff,'<n>') <> IFNULL(OLD.period_cutoff,'<n>')
          OR IFNULL(NEW.computed_at,'<n>') <> IFNULL(OLD.computed_at,'<n>'))
BEGIN
    SELECT RAISE(ABORT, 'computed result is referenced by a submitted decision and is immutable; supersede it instead');
END;
"""


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("document_id", ULID, primary_key=True),
        # THE cache key. Unique, so the "extract once, ever" guarantee is the database's job
        # rather than a check the application might forget under concurrency.
        sa.Column("sha256", sa.String(64), nullable=False, unique=True),
        # As FIRST uploaded. A later uploader's filename does not overwrite it: the extraction
        # was performed against this name, and the classifier may have used it.
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("content", BytesType, nullable=True),
        sa.Column("doc_type", sa.Text(), nullable=True),
        sa.Column("extraction", JSONType, nullable=True),
        # Model identifier AND version. "claude-opus-..." alone would not let a later reader
        # tell which weights produced a stored figure.
        sa.Column("extraction_model", sa.Text(), nullable=True),
        sa.Column("extracted_at", TS, nullable=True, server_default=sa.func.now()),
        sa.Column("first_uploaded_by", sa.Text(), nullable=True),
    )
    op.create_index("ix_documents_sha256", "documents", ["sha256"], unique=True)
    op.create_index("ix_documents_doc_type", "documents", ["doc_type"])

    op.create_table(
        "document_uploads",
        sa.Column("upload_id", ULID, primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("document_id", ULID, sa.ForeignKey("documents.document_id"), nullable=False),
        # From the session, never the request body. A body-supplied uploader would let a
        # participant attribute an upload to someone else.
        sa.Column("uploaded_by", sa.Text(), nullable=False),
        sa.Column("uploaded_at", TS, nullable=False, server_default=sa.func.now()),
        sa.Column("was_cached", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_document_uploads_project_period", "document_uploads",
                    ["project_id", "period"])
    op.create_index("ix_document_uploads_document", "document_uploads", ["document_id"])
    # One row per (project, period, document). Re-uploading the same file to the same period is
    # a no-op rather than a second row, so the period's document SET stays a set — which is what
    # makes assembly idempotent and a recompute reproducible.
    op.create_index("uq_document_uploads_once_per_period", "document_uploads",
                    ["project_id", "period", "document_id"], unique=True)

    op.create_table(
        "computed_results",
        sa.Column("result_id", ULID, primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("signal_inputs", JSONType, nullable=True),
        sa.Column("module_results", JSONType, nullable=True),
        sa.Column("category_statuses", JSONType, nullable=True),
        sa.Column("project_status", sa.Text(), nullable=True),
        # Null below the portfolio threshold. Distinct from "computed and came back empty".
        sa.Column("portfolio_snapshot", JSONType, nullable=True),
        # NOT NULL: see the migration docstring. A result that cannot be reproduced is not a
        # result, it is a number with no provenance.
        sa.Column("simulation_version", sa.Text(), nullable=False),
        sa.Column("seed", sa.Text(), nullable=False),
        sa.Column("period_cutoff", sa.Date(), nullable=False),
        sa.Column("computed_at", TS, nullable=False, server_default=sa.func.now()),
        sa.Column("superseded_by", ULID, nullable=True),
    )
    op.create_index("ix_computed_results_project_period", "computed_results",
                    ["project_id", "period"])
    # At most one LIVE result per (project, period). Superseded rows are exempt, which is what
    # makes the append-only recompute work: the old row stays, but stops being the current one.
    op.create_index(
        "uq_computed_results_one_live", "computed_results", ["project_id", "period"],
        unique=True,
        postgresql_where=sa.text("superseded_by IS NULL"),
        sqlite_where=sa.text("superseded_by IS NULL"),
    )

    # The reference from a decision to the result the participant actually saw. Nullable: every
    # decision recorded before this migration has no computed result behind it, and back-filling
    # one would be inventing provenance that never existed.
    with op.batch_alter_table("decisions") as batch:
        batch.add_column(sa.Column("result_id", ULID, nullable=True))

    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute(PG_TRIGGER_FN)
        op.execute(PG_TRIGGER)
    elif dialect == "sqlite":
        op.execute(SQLITE_TRIGGER)
    else:
        raise RuntimeError(
            f"No referenced-result immutability trigger defined for dialect {dialect!r}. The "
            "guarantee is not optional, so this migration refuses to create the schema "
            "without it."
        )


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    op.execute("DROP TRIGGER IF EXISTS trg_computed_results_referenced_guard ON computed_results"
               if dialect == "postgresql" else
               "DROP TRIGGER IF EXISTS trg_computed_results_referenced_guard")
    if dialect == "postgresql":
        op.execute("DROP FUNCTION IF EXISTS og_reject_referenced_result_update()")

    with op.batch_alter_table("decisions") as batch:
        batch.drop_column("result_id")

    op.drop_index("uq_computed_results_one_live", table_name="computed_results")
    op.drop_index("ix_computed_results_project_period", table_name="computed_results")
    op.drop_table("computed_results")

    op.drop_index("uq_document_uploads_once_per_period", table_name="document_uploads")
    op.drop_index("ix_document_uploads_document", table_name="document_uploads")
    op.drop_index("ix_document_uploads_project_period", table_name="document_uploads")
    op.drop_table("document_uploads")

    op.drop_index("ix_documents_doc_type", table_name="documents")
    op.drop_index("ix_documents_sha256", table_name="documents")
    op.drop_table("documents")
