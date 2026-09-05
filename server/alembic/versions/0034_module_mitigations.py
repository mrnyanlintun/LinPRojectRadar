"""module_mitigations: the composed mitigation for one non-Green reading, and what replays it

Revision ID: 0034_module_mitigations
Revises: 0033_recognition_matches
Create Date: 2026-09-05

WHY THIS TABLE EXISTS, AND WHY A COLUMN WOULD NOT HAVE DONE.

Run 140 changes what the Suggested Decision card does: it now also suggests how to move each
non-Green reading ONE BAND UP. That prose is composed by a model ONCE and replayed for ever,
following the determinism argument the platform already recorded at `recognition.py:44-64` -- a
model call is not a deterministic function, so the platform does not ask twice; it records the
answer and replays it.

A MIGRATION IS GENUINELY REQUIRED, and three things force it.

1. THE COMPOSITION IS KEYED FINER THAN ANY EXISTING ROW. It is one answer per project, per
   period, per MODULE, per READING FINGERPRINT. No existing table has that grain.

2. IT MUST BE APPEND-ONLY, because the card feeds an audit record and "why did this suggestion
   change?" has to be answerable. A column on `computed_results` CANNOT be append-only: a
   recompute REPLACES that row, and the superseded text would be gone with it. Here the
   replaced row stays and `superseded_by` points at what replaced it.

3. THE KEY IS A CONTENT FINGERPRINT, NOT A FOREIGN KEY. The platform serves a category's
   readings from `specification_readings` OR from `computed_results`, merged per category by
   `spec_projection.merge_python_row`, so there is no single reading id to point at. The
   fingerprint covers everything that could change what a mitigation should say -- band,
   evidence sentence, boundary, basis, threshold source, both provenance classes, every override
   flag, every worst-of component, the whole code-built context, the template version, the
   provider and the model. Identical reading, replayed with NO CALL MADE AT ALL. Changed
   reading, fresh row, old row superseded and kept.

   THE v70 REASSEMBLY, WHEN IT RUNS, WILL MOVE BANDS AND FIGURES, so it will change those
   fingerprints and recompose the affected mitigations. That is the intended trigger.

`mitigations` holds an ordered list of candidate sentences, or the single fixed absence line
"no mitigation composed for this reading". IT IS NOT A SOURCE OF ANY FIGURE: the reading,
boundary and gap lines the card renders are composed in code from the stored module row on every
render and are never read out of this table.

MIGRATION: /readyz reports 503 with SchemaOutOfDate until `alembic upgrade head` is run against
the target database.
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# The same two types `app/research_models.py` declares, spelled here so this migration does not
# import the application: JSONB on PostgreSQL and JSON on SQLite, and a ULID as a 26-char string.
JSONType = JSONB().with_variant(sa.JSON(), "sqlite")
ULID = sa.String(26)

revision = "0034_module_mitigations"
down_revision = "0033_recognition_matches"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "module_mitigations",
        sa.Column("mitigation_id", ULID, primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Text(), nullable=False),
        sa.Column("reading_fingerprint", sa.Text(), nullable=False),
        sa.Column("band", sa.Text(), nullable=True),
        sa.Column("shape", sa.Text(), nullable=True),
        sa.Column("context", JSONType, nullable=True),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("prompt_sha256", sa.Text(), nullable=False),
        sa.Column("template_version", sa.Text(), nullable=False),
        sa.Column("mitigations", JSONType, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("superseded_by", ULID, nullable=True),
        sa.UniqueConstraint("project_id", "period", "module_id", "reading_fingerprint",
                            name="uq_module_mitigation_key"),
    )
    op.create_index("ix_module_mitigations_project", "module_mitigations",
                    ["project_id", "period"])


def downgrade() -> None:
    op.drop_index("ix_module_mitigations_project", table_name="module_mitigations")
    op.drop_table("module_mitigations")
