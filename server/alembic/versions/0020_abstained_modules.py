"""computed_results.abstained: which modules abstained on this row, and why

Revision ID: 0020_abstained_modules
Revises: 0019_training_runs
Create Date: 2026-08-06

ONE NULLABLE JSON COLUMN, HOLDING WHAT `run_all()` ALREADY COMPUTES AND ALREADY DISCARDED.

`run_all()` (server/app/simulation/registry.py) already produces `abstained`: a list of
{module_id, reason} for every module that ran and abstained rather than computing, where
`reason` is that module's own `evidence_metric` message when it gave one, else null. Before
this migration `_compute_and_store` never wrote it onto the row, so the message was live only
for the instant between compute and the HTTP response of the compute-trigger endpoint, and
gone by the time anyone opened the ledger to read it back.

NULL is the honest answer for every row computed before this migration: `abstained` was never
stored for them, so there is nothing to backfill without inventing history the platform does
not have. A ledger reading this column treats NULL as "no reason on record", not as "nothing
abstained" — those are different claims and the code that reads this column keeps them
different.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0020_abstained_modules"
down_revision = "0019_training_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "computed_results",
        sa.Column(
            "abstained",
            sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("computed_results", "abstained")
