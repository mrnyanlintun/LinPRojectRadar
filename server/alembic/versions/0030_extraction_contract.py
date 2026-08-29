"""documents.extraction_contract: the fingerprint of the contract an extraction was made under

Revision ID: 0030_extraction_contract
Revises: 0029_observation_withdrawn
Create Date: 2026-08-29

WHY THE CACHE NEEDED A SECOND KEY.

`documents` is keyed on the sha256 of the bytes, and the upload path serves a known hash from
the stored extraction without a model call. That is correct for identical bytes under an
identical EXTRACTION CONTRACT -- the field list and prompt `extraction_client.build_prompt`
issues for the document's type. But the contract grows: Runs 78 and 80 added fields, and every
document extracted before them replays an extraction that never asked for those fields. The
owner measured it directly: a re-upload of a contingency report today came back `was_cached =
true` with zero contingency observations, while the document states the figures plainly.

THE FIX IS A SECOND CACHE KEY, NOT A DISABLED CACHE. This column records the sha256 of the
exact prompt the stored extraction was produced under. On a cache hit the upload path compares
it against the CURRENT fingerprint for the stored document type: equal means the cached
extraction answers today's contract and is served without a model call, exactly as before;
unequal (or NULL) means the contract has grown since this row was extracted, and the document
is re-extracted. The row is then UPDATED in place -- `documents` establishes stimulus identity
by construction (one row per unique bytes, 0009's ruling), so two PMs uploading identical
bytes still read the SAME extraction row and still get byte-identical signalInputs. The
append-only rule belongs to `computed_results`, not here; a stored computed_results row keeps
the inputs it was computed from regardless.

EVERY PRE-0030 ROW IS NULL, AND NULL MEANS STALE, TRUTHFULLY: the contract those rows were
extracted under was not recorded and is known to predate at least one contract change, so the
next upload of those bytes re-extracts once and stamps the fingerprint. No value is invented
for the old rows.

MIGRATION: /readyz reports 503 with SchemaOutOfDate until `alembic upgrade head` is run against
the target database.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0030_extraction_contract"
down_revision = "0029_observation_withdrawn"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents",
                  sa.Column("extraction_contract", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "extraction_contract")
