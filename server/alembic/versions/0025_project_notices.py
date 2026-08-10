"""project_notices: a served notice kept as the discrete event it is

Revision ID: 0025_project_notices
Revises: 0024_project_risks
Create Date: 2026-08-10

WHY

`correspondence_notice` extracted `document_risk_score` and `document_date`, on the reading that
correspondence is narrative and carries no structured project-controls content. A notice is not
narrative. Someone served it, on someone, it asserts something, and under the contract form it
starts a clock that can extinguish a right. Reducing that to a number between zero and one threw
away every part of it a project manager acts on.

ONE ROW PER (project, period, document), because a notice document IS one notice. That is why
this is a table rather than rows in `observations`, which holds one VALUE per (field, entity):
who served it, on whom, what it claims and what it references only mean anything together.

THE DEADLINE IS DERIVED IN CODE FROM THE FORM THE DOCUMENT NAMED, never asked of the model and
never assumed from a project default this platform does not hold. `deadline_basis` is NOT NULL:
where no date could be derived it says which of the three requirements failed (no form named, no
fixed count for that notice type under that form, or a served date that would not parse), so a
reader is never shown a blank where a rule should be.

`deadline_kind` separates a DEADLINE from a LOOKBACK. The federal twenty-day figure is a cost
cutoff measured backward from the notice, not an expiry: nothing is time-barred, the money is
simply gone. Storing it as a deadline date would tell a reader their claim dies on a day it does
not, so a lookback carries its day count and no date.

`second_step` holds the ConsensusDocs two-step clock, whose second period runs from the NOTICE
and not from the occurrence. A single deadline column would silently drop it, and going quiet
after giving notice is named in the training material as the trap that loses the right.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

revision = "0025_project_notices"
down_revision = "0024_project_risks"
branch_labels = None
depends_on = None

JSONType = JSONB().with_variant(JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "project_notices",
        sa.Column("project_notice_id", sa.String(26), primary_key=True),
        sa.Column("project_id", sa.Uuid(),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.String(26),
                  sa.ForeignKey("documents.document_id"), nullable=False),
        sa.Column("filename", sa.Text(), nullable=True),
        sa.Column("served_by", sa.Text(), nullable=True),
        sa.Column("served_on", sa.Text(), nullable=True),
        sa.Column("claim", sa.Text(), nullable=True),
        sa.Column("date_served", sa.Date(), nullable=True),
        sa.Column("date_served_raw", sa.Text(), nullable=True),
        sa.Column("date_served_refusal", sa.Text(), nullable=True),
        sa.Column("contract_form", sa.Text(), nullable=True),
        sa.Column("notice_kind", sa.Text(), nullable=True),
        sa.Column("references_text", sa.Text(), nullable=True),
        sa.Column("deadline_date", sa.Date(), nullable=True),
        sa.Column("deadline_days", sa.Integer(), nullable=True),
        sa.Column("deadline_kind", sa.Text(), nullable=True),
        sa.Column("deadline_citation", sa.Text(), nullable=True),
        sa.Column("deadline_basis", sa.Text(), nullable=False),
        sa.Column("second_step", JSONType, nullable=True),
        sa.Column("as_of", sa.Date(), nullable=True),
        sa.Column("source_doc_type", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("deadline_kind IS NULL OR deadline_kind IN ('deadline','lookback')",
                           name="ck_project_notices_deadline_kind"),
    )
    op.create_index("ix_project_notices_project_period", "project_notices",
                    ["project_id", "period"])
    # Idempotence: re-deriving the same document's notice inserts nothing new.
    op.create_index("uq_project_notices_identity", "project_notices",
                    ["project_id", "period", "document_id"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_project_notices_identity", table_name="project_notices")
    op.drop_index("ix_project_notices_project_period", table_name="project_notices")
    op.drop_table("project_notices")
