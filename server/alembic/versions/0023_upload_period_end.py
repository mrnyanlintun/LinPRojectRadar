"""document_uploads.period_end: the reporting period the person said these documents belong to

Revision ID: 0023_upload_period_end
Revises: 0022_upload_attempts
Create Date: 2026-08-08

WHAT THIS FIXES, AND WHY A COLUMN IS NEEDED FOR IT

`document_uploads.period` has always existed and assembly has always been strictly per period,
so the store could always express four periods. What it could not express is which reporting
period a person MEANT, because nothing on the upload path ever asked. Every client either sent
`period: 1` or sent nothing, and the server defaulted a missing period to 1, so a project's
whole document history landed in one period and the cross-period series saw one point where
there should have been several.

The period NUMBER needed no column. This one exists for the second half of the fix: a document
whose own date falls outside the period it was filed to must be FLAGGED rather than silently
accepted or silently moved, and there was no stored notion anywhere of what date range a period
covers. `period_end` is the reporting period's ending date as the person stated it at upload.

WHY IT IS NULLABLE

Rows written before this migration were filed without anyone being asked, so there is no honest
value to backfill and none is invented. NULL means "no period ending date was stated", and the
out-of-period check reports nothing for such a row rather than comparing against a guess. The
same is true of a caller that supplies a period number and no ending date.

WHY IT IS NOT THE PERIOD CUTOFF

`period_cutoff` on `computed_results` is derived by `documents._derive_cutoff` as the latest date
the period's own evidence speaks about, and two checks already depend on that derivation: on a
first compute `docDate` and `period_cutoff` are the same number, and a recompute reuses the
superseded row's cutoff so C1.2 Data Timeliness cannot drift. Setting the cutoff from this
column instead would break the first and change what the second preserves. It would also mean a
document flagged as dated after its period had its observations silently excluded from
selection, which is the "silently overridden" outcome the flag exists to avoid. So the stated
ending date decides nothing about the analysis; it is what the flag is measured against.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0023_upload_period_end"
down_revision = "0022_upload_attempts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document_uploads", sa.Column("period_end", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("document_uploads", "period_end")
