"""observations.withdrawn_at / withdrawn_by / withdrawn_by_event_id: the archive mark, on the row

Revision ID: 0029_observation_withdrawn
Revises: 0028_specification_readings
Create Date: 2026-08-28

WHAT THIS CLOSES, AND WHAT IT DOES NOT.

Run 71 built the document control and required that an archived document's observations be
withdrawn from the live figures. That requirement IS met on the computation path and was met
before this migration: `documents._period_documents` excludes archived uploads at the one seam
`assemble_signal_inputs` reads, so no module, category, chart or brief has ever received a
figure that came only from an archived document. Measured, not assumed.

What was NOT true is that the OBSERVATION STORE said so. `observations` is append-only by
design and `_persist_observations` projects EVERY upload in the period, superseded and archived
alike, because storage is not selection -- the same argument 0013 made for superseded rows.
That is correct as an audit store and it is why nothing here deletes anything. But it left the
table unable to answer "was this withdrawn, when, and by which archive action" without joining
back to `document_uploads`, and it left any reader that queries the table directly free to
present an archived document's figure as live -- which `a_projectuploadstatus`'s baseline and
amendments block did.

SO THE MARK IS RECORDED ON THE ROW, AND THE ROW REMAINS.

  * `withdrawn_at`   -- NULL means live. Non-NULL is the moment the archive action ran. It is
                        the archive's own timestamp, copied from `document_uploads.archived_at`,
                        NOT the clock at marking time: the two must agree or the audit record
                        and the observation would name different moments for one event.
  * `withdrawn_by`   -- the participant id from the session that archived. Never a request body.
  * `withdrawn_by_event_id` -- the append-only `audit_events` row of type `documents_archived`
                        that withdrew it. This is what makes "by which archive action" answerable
                        from the observation alone, which is the whole point: one archive action
                        may withdraw several documents and a document may be archived in one
                        period while live in another.

Every pre-0029 row is NULL on all three, which is the truthful state: those observations were
never withdrawn and no value is invented for them.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0029_observation_withdrawn"
down_revision = "0028_specification_readings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("observations",
                  sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("observations", sa.Column("withdrawn_by", sa.Text(), nullable=True))
    op.add_column("observations",
                  sa.Column("withdrawn_by_event_id", sa.Text(), nullable=True))
    op.create_index("ix_observations_withdrawn_at", "observations", ["withdrawn_at"])


def downgrade() -> None:
    op.drop_index("ix_observations_withdrawn_at", table_name="observations")
    op.drop_column("observations", "withdrawn_by_event_id")
    op.drop_column("observations", "withdrawn_by")
    op.drop_column("observations", "withdrawn_at")
