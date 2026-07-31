"""research schema

Revision ID: 0003_research_schema
Revises: 0002_snapshot_project_nullable
Create Date: 2026-07-31

Twelve research tables, sharing no foreign key with the facade tables. See app/research_models.py
for the reasoning.

Two integrity guarantees are enforced in the database rather than the application, because the
preliminary judgment is the measurement the whole study rests on and application code is the thing
most likely to change:

  1. CHECK ck_decisions_reveal_after_pre_lock
     reveal_at IS NULL OR (pre_locked_at IS NOT NULL AND pre_locked_at <= reveal_at)

  2. Trigger trg_decisions_pre_lock_guard
     Rejects any UPDATE that would change pre_action or pre_confidence once pre_locked_at is set.
     The matching audit_events row is appended by app/research_audit.py rather than by the
     trigger; the next section explains why it cannot be the trigger.

WHY THE TRIGGER DOES NOT WRITE THE AUDIT ROW

A trigger that raises cannot durably record its own rejection, on any dialect. Whatever it inserts
belongs to the same transaction as the rejected UPDATE and is discarded when that transaction
unwinds. This was measured, not assumed: an earlier version of this migration inserted from inside
the trigger and zero rows survived on SQLite, despite RAISE(FAIL) preserving statement-level
changes, because the caller's rollback removed them anyway. Postgres behaves the same and has no
autonomous transactions without an extension such as dblink.

The alternative would be a trigger that silently reverts the protected columns and audits durably.
That was rejected: a database that accepts an UPDATE and quietly discards it is precisely the
silent failure this project forbids.

So the trigger rejects loudly and app/research_audit.py writes the audit row on a separate
connection. The Postgres exception carries SQLSTATE 'OG001' so the application can recognise it
without matching on message text; SQLite carries no SQLSTATE, so that path falls back to the
message marker.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003_research_schema"
down_revision = "0002_snapshot_project_nullable"
branch_labels = None
depends_on = None

JSONType = JSONB().with_variant(sa.JSON(), "sqlite")
ULID = sa.String(26)
TS = sa.DateTime(timezone=True)


def _ts_col(name: str, nullable: bool = True, default_now: bool = False):
    kwargs = {"nullable": nullable}
    if default_now:
        kwargs["server_default"] = sa.func.now()
    return sa.Column(name, TS, **kwargs)


PG_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION og_reject_locked_pre_judgment() RETURNS trigger AS $$
BEGIN
    IF OLD.pre_locked_at IS NOT NULL
       AND (NEW.pre_action IS DISTINCT FROM OLD.pre_action
            OR NEW.pre_confidence IS DISTINCT FROM OLD.pre_confidence) THEN


        RAISE EXCEPTION
            'pre-judgment is locked: pre_action and pre_confidence are immutable after pre_locked_at (decision %)',
            OLD.decision_id
            USING ERRCODE = 'OG001';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

PG_TRIGGER = """
CREATE TRIGGER trg_decisions_pre_lock_guard
BEFORE UPDATE ON decisions
FOR EACH ROW
EXECUTE FUNCTION og_reject_locked_pre_judgment();
"""

# SQLite: RAISE(ABORT) undoes the offending statement and reports the error. The audit row is
# written separately by app/research_audit.py; see the migration docstring.
SQLITE_TRIGGER = """
CREATE TRIGGER trg_decisions_pre_lock_guard
BEFORE UPDATE OF pre_action, pre_confidence ON decisions
FOR EACH ROW
WHEN OLD.pre_locked_at IS NOT NULL
     AND (IFNULL(NEW.pre_action, '<null>') <> IFNULL(OLD.pre_action, '<null>')
          OR IFNULL(NEW.pre_confidence, -999999) <> IFNULL(OLD.pre_confidence, -999999))
BEGIN
    SELECT RAISE(ABORT, 'pre-judgment is locked: pre_action and pre_confidence are immutable after pre_locked_at');
END;
"""


def upgrade() -> None:
    op.create_table(
        "participants",
        sa.Column("participant_id", ULID, primary_key=True),
        sa.Column("pseudonymous_code", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("access_token_hash", sa.Text(), nullable=True),
        sa.Column("eligibility_status", sa.Text(), nullable=True),
        sa.Column("scenario_set", sa.Text(), nullable=True),
        sa.Column("condition_sequence", sa.Text(), nullable=True),
        sa.Column("order_group", sa.Text(), nullable=True),
        sa.Column("current_scenario", sa.Text(), nullable=True),
        sa.Column("current_stage", sa.Text(), nullable=True),
        sa.Column("completion_status", sa.Text(), nullable=True),
        _ts_col("created_at", nullable=False, default_now=True),
        _ts_col("updated_at", nullable=False, default_now=True),
        sa.UniqueConstraint("pseudonymous_code", name="uq_participants_pseudonymous_code"),
        sa.CheckConstraint(
            "role IN ('ResearchAdmin','Participant','Expert','Demo')", name="ck_participants_role"
        ),
    )
    op.create_index("ix_participants_code", "participants", ["pseudonymous_code"])

    op.create_table(
        "participant_profiles",
        sa.Column("profile_id", ULID, primary_key=True),
        sa.Column("participant_id", ULID,
                  sa.ForeignKey("participants.participant_id", ondelete="CASCADE"), nullable=False),
        sa.Column("experience_level", sa.Text(), nullable=True),
        sa.Column("years_experience", sa.Integer(), nullable=True),
        sa.Column("industry", sa.Text(), nullable=True),
        sa.Column("certifications", JSONType, nullable=True),
        sa.Column("ai_familiarity", sa.Text(), nullable=True),
        sa.Column("organizational_role", sa.Text(), nullable=True),
        sa.Column("risk_attitude", JSONType, nullable=True),
        sa.Column("demand_effect_items", JSONType, nullable=True),
        _ts_col("captured_at", nullable=False, default_now=True),
    )
    op.create_index("ix_profiles_participant", "participant_profiles", ["participant_id"])

    op.create_table(
        "consents",
        sa.Column("consent_id", ULID, primary_key=True),
        sa.Column("participant_id", ULID,
                  sa.ForeignKey("participants.participant_id", ondelete="CASCADE"), nullable=False),
        sa.Column("consent_version", sa.Text(), nullable=False),
        _ts_col("granted_at", nullable=False, default_now=True),
        sa.Column("method", sa.Text(), nullable=True),
        sa.Column("session_ref", sa.Text(), nullable=True),
        _ts_col("withdrawn_at"),
    )
    op.create_index("ix_consents_participant", "consents", ["participant_id"])

    op.create_table(
        "configurations",
        sa.Column("config_id", ULID, primary_key=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("presentation_spec", JSONType, nullable=True),
        sa.Column("elements_included", JSONType, nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.false()),
        _ts_col("frozen_at"),
        sa.CheckConstraint("code IN ('C0','C1','C2')", name="ck_configurations_code"),
    )
    op.create_index("ix_configurations_code", "configurations", ["code"])

    op.create_table(
        "scenarios",
        sa.Column("scenario_id", ULID, primary_key=True),
        sa.Column("scenario_version", sa.Text(), nullable=False),
        sa.Column("project_type", sa.Text(), nullable=True),
        sa.Column("period_count", sa.Integer(), nullable=True),
        sa.Column("evidence_package_id", sa.Text(), nullable=True),
        sa.Column("reference_standard_version", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
    )

    op.create_table(
        "decision_support_packages",
        sa.Column("package_id", ULID, primary_key=True),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("config_id", ULID, sa.ForeignKey("configurations.config_id"), nullable=True),
        sa.Column("provider_id", sa.Text(), nullable=True),
        sa.Column("model_version", sa.Text(), nullable=True),
        sa.Column("use_case", sa.Text(), nullable=True),
        _ts_col("data_cutoff"),
        sa.Column("provenance", JSONType, nullable=True),
        sa.Column("output_type", sa.Text(), nullable=True),
        sa.Column("detected_condition", sa.Text(), nullable=True),
        sa.Column("uncertainty", JSONType, nullable=True),
        sa.Column("limitations", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("alternatives", JSONType, nullable=True),
        sa.Column("applicability_boundary", sa.Text(), nullable=True),
        sa.Column("expiration_trigger", sa.Text(), nullable=True),
        sa.Column("approval_status", sa.Text(), nullable=True),
        _ts_col("frozen_at"),
    )
    op.create_index("ix_packages_config", "decision_support_packages", ["config_id"])

    op.create_table(
        "assignments",
        sa.Column("assignment_id", ULID, primary_key=True),
        sa.Column("participant_id", ULID,
                  sa.ForeignKey("participants.participant_id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_id", ULID, sa.ForeignKey("scenarios.scenario_id"), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=True),
        sa.Column("config_id", ULID, sa.ForeignKey("configurations.config_id"), nullable=True),
        sa.Column("package_id", ULID,
                  sa.ForeignKey("decision_support_packages.package_id"), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
    )
    op.create_index("ix_assignments_participant", "assignments", ["participant_id"])
    op.create_index("ix_assignments_scenario", "assignments", ["scenario_id"])

    op.create_table(
        "decisions",
        sa.Column("decision_id", ULID, primary_key=True),
        sa.Column("assignment_id", ULID,
                  sa.ForeignKey("assignments.assignment_id", ondelete="CASCADE"), nullable=False),
        sa.Column("package_id", ULID,
                  sa.ForeignKey("decision_support_packages.package_id"), nullable=True),
        sa.Column("package_hash", sa.String(64), nullable=True),
        sa.Column("period", sa.Text(), nullable=True),
        sa.Column("pre_action", sa.Text(), nullable=True),
        sa.Column("pre_confidence", sa.Integer(), nullable=True),
        _ts_col("pre_submitted_at"),
        _ts_col("pre_locked_at"),
        sa.Column("pre_judgment_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        _ts_col("reveal_at"),
        sa.Column("final_action", sa.Text(), nullable=True),
        sa.Column("disposition", sa.Text(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("final_confidence", sa.Integer(), nullable=True),
        _ts_col("final_submitted_at"),
        sa.Column("escalation_level", sa.Text(), nullable=True),
        sa.Column("owner_role", sa.Text(), nullable=True),
        sa.Column("authority_role", sa.Text(), nullable=True),
        sa.Column("resource_constraint", sa.Text(), nullable=True),
        # Constraint 1.
        sa.CheckConstraint(
            "reveal_at IS NULL OR (pre_locked_at IS NOT NULL AND pre_locked_at <= reveal_at)",
            name="ck_decisions_reveal_after_pre_lock",
        ),
    )
    op.create_index("ix_decisions_assignment", "decisions", ["assignment_id"])

    op.create_table(
        "transitions",
        sa.Column("transition_id", ULID, primary_key=True),
        sa.Column("decision_id", ULID,
                  sa.ForeignKey("decisions.decision_id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.Text(), nullable=True),
        sa.Column("branch_version", sa.Text(), nullable=True),
        sa.Column("seed", sa.Text(), nullable=True),
        sa.Column("probability", sa.Text(), nullable=True),
        sa.Column("next_state_id", sa.Text(), nullable=True),
        _ts_col("displayed_at"),
    )
    op.create_index("ix_transitions_decision", "transitions", ["decision_id"])

    op.create_table(
        "expert_references",
        sa.Column("reference_id", ULID, primary_key=True),
        sa.Column("scenario_id", ULID, sa.ForeignKey("scenarios.scenario_id"), nullable=False),
        sa.Column("expert_id", sa.Text(), nullable=True),
        sa.Column("preferred_action", sa.Text(), nullable=True),
        sa.Column("acceptable_alternatives", JSONType, nullable=True),
        sa.Column("unsupported_actions", JSONType, nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("required_evidence", sa.Text(), nullable=True),
        sa.Column("escalation_expectation", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        _ts_col("locked_at"),
        sa.Column("realism_review", JSONType, nullable=True),
    )
    op.create_index("ix_expert_refs_scenario", "expert_references", ["scenario_id"])

    op.create_table(
        "audit_events",
        sa.Column("event_id", ULID, primary_key=True),
        # Not foreign keys on purpose: an audit row must outlive whatever it describes.
        sa.Column("participant_id", ULID, nullable=True),
        sa.Column("scenario_id", ULID, nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        _ts_col("server_ts", nullable=False, default_now=True),
        sa.Column("metadata", JSONType, nullable=True),
    )
    op.create_index("ix_audit_participant", "audit_events", ["participant_id"])
    op.create_index("ix_audit_scenario", "audit_events", ["scenario_id"])
    op.create_index("ix_audit_type", "audit_events", ["event_type"])

    op.create_table(
        "research_exports",
        sa.Column("export_id", ULID, primary_key=True),
        sa.Column("format", sa.Text(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("destination", sa.Text(), nullable=True),
        sa.Column("date_range", sa.Text(), nullable=True),
        sa.Column("initiated_by", sa.Text(), nullable=True),
        _ts_col("completed_at"),
    )

    # Constraint 2, dialect specific.
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute(PG_TRIGGER_FN)
        op.execute(PG_TRIGGER)
    elif dialect == "sqlite":
        op.execute(SQLITE_TRIGGER)
    else:
        raise RuntimeError(
            f"No pre-judgment lock trigger defined for dialect {dialect!r}. The lock is not "
            "optional, so this migration refuses to create the schema without it."
        )


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    op.execute("DROP TRIGGER IF EXISTS trg_decisions_pre_lock_guard ON decisions"
               if dialect == "postgresql" else
               "DROP TRIGGER IF EXISTS trg_decisions_pre_lock_guard")
    if dialect == "postgresql":
        op.execute("DROP FUNCTION IF EXISTS og_reject_locked_pre_judgment()")

    for table in ("research_exports", "audit_events", "expert_references", "transitions",
                  "decisions", "assignments", "decision_support_packages", "scenarios",
                  "configurations", "consents", "participant_profiles", "participants"):
        op.drop_table(table)
