"""intake and debrief questionnaire response columns

Revision ID: 0010_questionnaire_responses
Revises: 0009_documents_and_results
Create Date: 2026-08-01

T7/T8 needs somewhere to store two questionnaires, and `participant_profiles` (0003) was built
for exactly one of them — its narrow columns (experience_level, years_experience, industry,
ai_familiarity, organizational_role) and two JSONB columns (certifications, risk_attitude) map
almost field-for-field onto the intake instrument's moderator variables. There is nothing for
the debrief instrument (familiarity with the researcher, perceived study purpose, expectation to
agree) at all.

WHY RAW JSONB CAPTURE ALONGSIDE THE NARROW COLUMNS, NOT INSTEAD OF THEM

Neither instrument is finalised — the risk-attitude scale in particular is still being selected
with the researcher's committee (see assets/questionnaires/intake.json's top-level `note`). A
narrow column per item would need a migration every time the committee revises a scale, which is
precisely the failure mode risk_attitude/demand_effect_items were already built to avoid (see
their comments in 0003). `intake_responses` and `debrief_responses` below capture EVERY item's
answer, keyed by the item id from the JSON definition, verbatim and complete, regardless of how
the definition evolves. The existing narrow columns are still populated for the items that map
cleanly onto them (server/app/questionnaires.py documents the exact mapping) — the raw blob is
belt, the narrow column is suspenders. If an item is renamed, added, or removed in the JSON
definition, the raw blob never loses data; only the narrow-column mapping might need updating,
and updating a Python dict literal is not a schema migration.

WHY SEPARATE *_captured_at COLUMNS RATHER THAN REUSING `captured_at`

`captured_at` is NOT NULL with server_default=now() — it is stamped the instant the row is
created, which happens whenever ANY profile field is first written, not specifically when the
participant finished a questionnaire. Using it to prove "the intake questionnaire was actually
submitted" would conflate row-creation with instrument-completion. `intake_captured_at` and
`debrief_captured_at` are nullable and set explicitly by their respective save actions, so a
non-null value there is itself the evidence that that specific questionnaire was completed —
which is what T7's Guarantee 9 needs to demonstrate.

MIGRATION: /readyz reports 503 with SchemaOutOfDate until `alembic upgrade head` is run against
the target database.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0010_questionnaire_responses"
down_revision = "0009_documents_and_results"
branch_labels = None
depends_on = None

JSONType = JSONB().with_variant(sa.JSON(), "sqlite")
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    with op.batch_alter_table("participant_profiles") as batch:
        batch.add_column(sa.Column("intake_responses", JSONType, nullable=True))
        batch.add_column(sa.Column("intake_captured_at", TS, nullable=True))
        batch.add_column(sa.Column("debrief_responses", JSONType, nullable=True))
        batch.add_column(sa.Column("debrief_captured_at", TS, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("participant_profiles") as batch:
        batch.drop_column("debrief_captured_at")
        batch.drop_column("debrief_responses")
        batch.drop_column("intake_captured_at")
        batch.drop_column("intake_responses")
