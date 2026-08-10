"""project_risks: the risk register kept as structured data, one observation per period

Revision ID: 0024_project_risks
Revises: 0023_upload_period_end
Create Date: 2026-08-10

WHY A TABLE AND NOT TWO FIELDS

The register yielded `document_risk_score` and `document_date` and nothing else, so the
recommendation was formed with no knowledge of what the project had already written down that it
was worried about, and the three cost-forecasting modules had no calibration data whatever.

That absence had a measured consequence. On a design project whose authored estimate at
completion was 4,835,600 dollars, the platform produced an eightieth percentile of 10,555,811,
79.7 per cent above budget and more than twice either authored figure. The document sets supply
no distribution and no percentile of any kind, so nothing about that project produced it. It came
from literals inside the modules.

A register carries, per risk, a probability and a cost impact. That is a real input, and this
table is where it lives.

ONE ROW PER (project, period, document, risk), which is the observations store's rule applied to
a register: the same risk seen in four reporting periods is FOUR ROWS, one per period, not four
rows competing to be current. An earlier period's account of a risk is never rewritten by a later
one, so recomputing that earlier period reproduces it. That is the P1 invariant, held by the
storage shape rather than by care at the call site.

WHY NOT observations. An observation row is one VALUE per (field, entity). A risk is a dozen
attributes that only mean anything together: a probability without its cost impact cannot enter
an exposure, and an owner without its risk names nobody. `schedule_activities` set the precedent
for a per-item table for exactly this reason.

A BAND IS NOT A PROBABILITY, AND THAT IS TWO COLUMNS RATHER THAN ONE. `probability` is NOT NULL
only where the register stated a number: a percentage or a fraction. Where the register said
"High", or scored the risk 4 of 5, `probability` is NULL and `probability_band` carries the words
verbatim. Nothing converts the second into the first. "High" has no numeric value the document
states, and a scheme that maps it to 0.7, or to the midpoint of a stated range, imports a number
from outside the document and then presents it as read. That import is precisely the defect this
migration exists to end, so it is refused at the point of storage and not merely guarded later.

The CHECK on `probability` is 0..1 inclusive, so a percentage that arrived unscaled cannot be
stored as a probability of 35.

REFUSALS ARE STORED. `unparsed` holds one entry per cell that would not parse, with the field it
was refused for and the reason. A row that refuses is still a row: a register of two hundred
risks that yielded ninety usable probabilities has to be able to say which hundred and ten
refused and why, and a dropped row cannot. `usable_for_exposure` is true only where BOTH a
numeric probability and a numeric cost impact are present, which is the pair a cost distribution
needs and the flag a forecasting module reads before deciding whether it can compute at all.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

revision = "0024_project_risks"
down_revision = "0023_upload_period_end"
branch_labels = None
depends_on = None

JSONType = JSONB().with_variant(JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "project_risks",
        sa.Column("project_risk_id", sa.String(26), primary_key=True),
        sa.Column("project_id", sa.Uuid(),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.String(26),
                  sa.ForeignKey("documents.document_id"), nullable=False),
        sa.Column("risk_key", sa.Text(), nullable=False),
        sa.Column("keyed_by_position", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("probability", sa.Float(), nullable=True),
        sa.Column("probability_band", sa.Text(), nullable=True),
        sa.Column("probability_raw", sa.Text(), nullable=True),
        sa.Column("cost_impact", sa.Float(), nullable=True),
        sa.Column("time_impact_days", sa.Float(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("owner", sa.Text(), nullable=True),
        sa.Column("response_strategy", sa.Text(), nullable=True),
        sa.Column("mitigation_status", sa.Text(), nullable=True),
        sa.Column("residual_position", sa.Text(), nullable=True),
        sa.Column("is_open", sa.Boolean(), nullable=True),
        sa.Column("unparsed", JSONType, nullable=True),
        sa.Column("usable_for_exposure", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("as_of", sa.Date(), nullable=True),
        sa.Column("source_doc_type", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("probability IS NULL OR (probability >= 0 AND probability <= 1)",
                           name="ck_project_risks_probability_band"),
    )
    # The read path: every risk this project holds for a period, and the bounded read a later
    # period makes over earlier ones.
    op.create_index("ix_project_risks_project_period", "project_risks",
                    ["project_id", "period"])
    # Idempotence: re-deriving the same document's register inserts nothing new. The same
    # guarantee `uq_observations_identity` and `uq_schedule_activities_identity` give, and the
    # reason a recompute cannot produce a second copy of a risk.
    op.create_index("uq_project_risks_identity", "project_risks",
                    ["project_id", "period", "document_id", "risk_key"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_project_risks_identity", table_name="project_risks")
    op.drop_index("ix_project_risks_project_period", table_name="project_risks")
    op.drop_table("project_risks")
