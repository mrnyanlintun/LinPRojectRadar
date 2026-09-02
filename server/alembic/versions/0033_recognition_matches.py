"""recognition_matches: what a model matched to what, and the fingerprint that replays it

Revision ID: 0033_recognition_matches
Revises: 0032_raw_evidence_kind
Create Date: 2026-09-02

WHY THIS TABLE EXISTS, AND IT IS ABOUT DETERMINISM RATHER THAN ABOUT CACHING.

Run 110 built the RAW evidence store: every value an extraction returns is kept with its
document, its period, the label the document printed it under, and the value itself. Nothing read
it, because reading it means deciding that a value printed under one label is the quantity a
specification asks for -- a model-driven step Run 110 refused to fake with a hand-coded synonym
table.

Run 111 builds that reader. A model call is NOT a deterministic function: temperature 0 narrows
the distribution rather than removing it, serving stacks batch requests, and an identifier such
as `claude-3-5-haiku-latest` is an alias that can be repointed under a running deployment. A
research instrument whose readings changed between two computations of one period on one body of
evidence would be unusable, and the owner's order states that this matters more than shipping the
feature.

So the platform does not ask twice. A recognition question is keyed by a sha256 over EVERYTHING
that could change its answer -- every candidate offered (document id, document type, sha256,
period, label, value), the specification text the model was shown, the prompt template version,
the provider name and the model identifier -- and a question already answered under that key is
replayed from this table with NO CALL MADE AT ALL.

Change the evidence, the specification, the template, the provider or the model and the
fingerprint changes: the question is asked again and BOTH rows remain. The unique constraint is
on (project, quantity, fingerprint), so one answer per question per body of evidence, and the
table is append-only -- nothing here is updated or deleted by the platform.

`match` holds what was recorded: the candidate identifier, the label as printed, the document it
came from, and the model's own one-sentence reason. IT IS NOT THE SOURCE OF THE VALUE. The value
is always read back out of `observations` by the recorded candidate, so a model that echoed a
figure could never put that figure into a reading.

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

revision = "0033_recognition_matches"
down_revision = "0032_raw_evidence_kind"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recognition_matches",
        sa.Column("recognition_match_id", ULID, primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("quantity_id", sa.Text(), nullable=False),
        sa.Column("evidence_fingerprint", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("prompt_sha256", sa.Text(), nullable=False),
        sa.Column("template_version", sa.Text(), nullable=False),
        sa.Column("match", JSONType, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "quantity_id", "evidence_fingerprint",
                            name="uq_recognition_match_key"),
    )
    op.create_index("ix_recognition_matches_project", "recognition_matches",
                    ["project_id", "quantity_id"])


def downgrade() -> None:
    op.drop_index("ix_recognition_matches_project", table_name="recognition_matches")
    op.drop_table("recognition_matches")
