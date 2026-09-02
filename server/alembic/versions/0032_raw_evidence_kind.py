"""observations.kind admits RAW: every extracted value is stored as evidence

Revision ID: 0032_raw_evidence_kind
Revises: 0031_model_provider_attribution
Create Date: 2026-09-02

WHY THIS MIGRATION IS NEEDED, AND WHY IT IS THE SMALLEST ONE THAT WORKS.

Run 110, order section 2.1: "Whatever extraction returns from a document is stored with its
document, period, label and value -- including fields no registry declares. Nothing extraction
finds is discarded because nobody declared it."

Run 110 measured, on a twenty-one document fixture through the real upload route, that of the
158 (document type, extracted key) pairs written to `documents.extraction`, SEVENTY-FOUR produced
no observation row at all. Among them were the six weather fields Run 107 added to `oac_minutes`
for A4.5 and the four per-firm rating fields it added to `subcontractor_report` for A4.8: they
were extracted, they were stored on the document, and the evidence store did not hold them.

`extraction_merge.emit_observations` now emits a RAW row for every key an extraction returns.
NO NEW COLUMN IS NEEDED for that -- the `observations` table already carries the document, the
period, the field and the value, which is exactly the four things the ruling names. What blocked
it was migration 0014's CHECK constraint, which admits only the four SELECTION behaviours:

    kind IN ('SNAPSHOT','EVENT','DELTA','PERMANENT')

RAW is not a fifth selection behaviour. It is the mark of a row that is NOT selected at all: a
verbatim transcription of what one document printed under its own label. Its field name is
`evidence:<doc_type>:<label>`, which contains a colon and so cannot equal any name in
`field_registry.ALL_SI_FIELDS`; `select_signal_inputs` iterates `_KEY_ORDER` and cannot reach one.

THE CONSTRAINT IS WIDENED, NOT DROPPED. An undeclared kind is still refused by the database, so
the guarantee 0014 was written to give -- that no code path can invent a storage behaviour by
writing a new string -- still holds. Widening to exactly one further named value is what keeps
that guarantee true while letting the evidence store hold the evidence.

NO EXISTING ROW IS TOUCHED, READ, REWRITTEN OR RECLASSIFIED. Every row written before this
migration keeps the kind it was written with, and every one of them still satisfies the widened
constraint. The downgrade is only safe once no RAW row remains, so it deletes none and refuses
none: it restores the four-value constraint, which SQLite and PostgreSQL will both reject if RAW
rows are present -- an honest failure rather than silent data loss.

MIGRATION: /readyz reports 503 with SchemaOutOfDate until `alembic upgrade head` is run against
the target database.
"""
from alembic import op

revision = "0032_raw_evidence_kind"
down_revision = "0031_model_provider_attribution"
branch_labels = None
depends_on = None

_FOUR = "kind IN ('SNAPSHOT','EVENT','DELTA','PERMANENT')"
_FIVE = "kind IN ('SNAPSHOT','EVENT','DELTA','PERMANENT','RAW')"
_NAME = "ck_observations_kind"


def upgrade() -> None:
    # batch_alter_table is required for SQLite, which cannot ALTER a CHECK constraint in place
    # and rebuilds the table instead. On PostgreSQL it lowers to a plain DROP/ADD CONSTRAINT.
    with op.batch_alter_table("observations") as batch:
        batch.drop_constraint(_NAME, type_="check")
        batch.create_check_constraint(_NAME, _FIVE)


def downgrade() -> None:
    with op.batch_alter_table("observations") as batch:
        batch.drop_constraint(_NAME, type_="check")
        batch.create_check_constraint(_NAME, _FOUR)
