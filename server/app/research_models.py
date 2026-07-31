"""
Research schema (B1).

Deliberately shares no foreign key with projects / project_snapshots / files. The facade tables
mirror an external system that is still authoritative and still changing; the research tables must
outlive it and must never be cascade-deleted by a project cleanup. The only link between the two
worlds is scenarios.evidence_package_id, which is an opaque reference, not a constraint.

Identifiers are ULIDs stored as CHAR(26). ULIDs sort lexicographically by creation time, so an
index on the primary key is also a time index, and unlike a UUIDv4 they do not scatter inserts
across the btree. They are generated in Python, not by the database, so an id can be known before
the row is written.

Every timestamp is timezone-aware and server-assigned. No client clock is trusted anywhere in this
schema: the pre-judgment lock is a measurement instrument, and a participant's clock is exactly the
thing it must not depend on.
"""

from __future__ import annotations

import os
import time
from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from .db import Base

JSONType = JSONB().with_variant(JSON(), "sqlite")
ULID = String(26)

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def new_ulid() -> str:
    """
    Crockford base32 ULID: 48-bit millisecond timestamp then 80 bits of randomness.

    Implemented here rather than taking a dependency, because it is twenty lines and the
    alternative is another pinned package in a build that has already been bitten twice by
    interpreter-specific wheels.
    """
    value = (int(time.time() * 1000) << 80) | int.from_bytes(os.urandom(10), "big")
    out = []
    for _ in range(26):
        value, rem = divmod(value, 32)
        out.append(_CROCKFORD[rem])
    return "".join(reversed(out))


def _pk() -> Mapped[str]:
    return mapped_column(ULID, primary_key=True, default=new_ulid)


class Participant(Base):
    __tablename__ = "participants"

    participant_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    # The only identifier that may appear in an export or a transcript.
    pseudonymous_code: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    # Hash only. A recoverable token would make the pseudonymous code re-identifiable.
    access_token_hash: Mapped[str] = mapped_column(Text, nullable=True)
    eligibility_status: Mapped[str] = mapped_column(Text, nullable=True)
    scenario_set: Mapped[str] = mapped_column(Text, nullable=True)
    condition_sequence: Mapped[str] = mapped_column(Text, nullable=True)
    order_group: Mapped[str] = mapped_column(Text, nullable=True)
    current_scenario: Mapped[str] = mapped_column(Text, nullable=True)
    current_stage: Mapped[str] = mapped_column(Text, nullable=True)
    completion_status: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('ResearchAdmin','Participant','Expert','Demo')",
            name="ck_participants_role",
        ),
    )


class ParticipantProfile(Base):
    __tablename__ = "participant_profiles"

    profile_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    participant_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("participants.participant_id", ondelete="CASCADE"), nullable=False, index=True
    )
    experience_level: Mapped[str] = mapped_column(Text, nullable=True)
    years_experience: Mapped[int] = mapped_column(Integer, nullable=True)
    industry: Mapped[str] = mapped_column(Text, nullable=True)
    certifications: Mapped[dict] = mapped_column(JSONType, nullable=True)
    ai_familiarity: Mapped[str] = mapped_column(Text, nullable=True)
    organizational_role: Mapped[str] = mapped_column(Text, nullable=True)
    # jsonb because the instrument is not finalised. A column per item would need a migration
    # every time the committee revises the scale.
    risk_attitude: Mapped[dict] = mapped_column(JSONType, nullable=True)
    demand_effect_items: Mapped[dict] = mapped_column(JSONType, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Consent(Base):
    __tablename__ = "consents"

    consent_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    participant_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("participants.participant_id", ondelete="CASCADE"), nullable=False, index=True
    )
    consent_version: Mapped[str] = mapped_column(Text, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    method: Mapped[str] = mapped_column(Text, nullable=True)
    session_ref: Mapped[str] = mapped_column(Text, nullable=True)
    # Withdrawal is recorded, never deleted. Deleting the row would destroy the evidence that
    # consent was given and then withdrawn.
    withdrawn_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class Configuration(Base):
    __tablename__ = "configurations"

    config_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    code: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    presentation_spec: Mapped[dict] = mapped_column(JSONType, nullable=True)
    elements_included: Mapped[dict] = mapped_column(JSONType, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    frozen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("code IN ('C0','C1','C2')", name="ck_configurations_code"),
    )


class Scenario(Base):
    __tablename__ = "scenarios"

    scenario_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    scenario_version: Mapped[str] = mapped_column(Text, nullable=False)
    project_type: Mapped[str] = mapped_column(Text, nullable=True)
    period_count: Mapped[int] = mapped_column(Integer, nullable=True)
    # Opaque reference into the facade world. Deliberately not a foreign key.
    evidence_package_id: Mapped[str] = mapped_column(Text, nullable=True)
    reference_standard_version: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=True)


class DecisionSupportPackage(Base):
    __tablename__ = "decision_support_packages"

    package_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    # sha256 of the frozen content. Copied onto each decision so a later edit is detectable.
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    config_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("configurations.config_id"), nullable=True, index=True
    )
    provider_id: Mapped[str] = mapped_column(Text, nullable=True)
    model_version: Mapped[str] = mapped_column(Text, nullable=True)
    use_case: Mapped[str] = mapped_column(Text, nullable=True)
    data_cutoff: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    provenance: Mapped[dict] = mapped_column(JSONType, nullable=True)
    output_type: Mapped[str] = mapped_column(Text, nullable=True)
    detected_condition: Mapped[str] = mapped_column(Text, nullable=True)
    uncertainty: Mapped[dict] = mapped_column(JSONType, nullable=True)
    limitations: Mapped[str] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=True)
    alternatives: Mapped[dict] = mapped_column(JSONType, nullable=True)
    applicability_boundary: Mapped[str] = mapped_column(Text, nullable=True)
    expiration_trigger: Mapped[str] = mapped_column(Text, nullable=True)
    approval_status: Mapped[str] = mapped_column(Text, nullable=True)
    frozen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class Assignment(Base):
    __tablename__ = "assignments"

    assignment_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    participant_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("participants.participant_id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("scenarios.scenario_id"), nullable=False, index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=True)
    config_id: Mapped[str] = mapped_column(ULID, ForeignKey("configurations.config_id"), nullable=True)
    package_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("decision_support_packages.package_id"), nullable=True
    )
    status: Mapped[str] = mapped_column(Text, nullable=True)


class Decision(Base):
    """
    The measurement record. Everything about this table exists to make the preliminary judgment
    unfalsifiable after the support package is revealed.
    """

    __tablename__ = "decisions"

    decision_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    assignment_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("assignments.assignment_id", ondelete="CASCADE"), nullable=False, index=True
    )
    package_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("decision_support_packages.package_id"), nullable=True
    )
    # Copied at reveal time. If the package is ever edited, the stored hash stops matching and the
    # affected decisions are identifiable rather than silently reinterpreted.
    package_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    period: Mapped[str] = mapped_column(Text, nullable=True)

    pre_action: Mapped[str] = mapped_column(Text, nullable=True)
    pre_confidence: Mapped[int] = mapped_column(Integer, nullable=True)
    pre_submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    pre_locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    pre_judgment_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    reveal_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    final_action: Mapped[str] = mapped_column(Text, nullable=True)
    disposition: Mapped[str] = mapped_column(Text, nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=True)
    final_confidence: Mapped[int] = mapped_column(Integer, nullable=True)
    final_submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    escalation_level: Mapped[str] = mapped_column(Text, nullable=True)
    owner_role: Mapped[str] = mapped_column(Text, nullable=True)
    authority_role: Mapped[str] = mapped_column(Text, nullable=True)
    resource_constraint: Mapped[str] = mapped_column(Text, nullable=True)

    __table_args__ = (
        # Constraint 1. A package can never be revealed before the preliminary judgment is locked,
        # and the lock can never be backdated to after the reveal. Without this, the central
        # measurement of the study could be invalidated by a single out-of-order write.
        CheckConstraint(
            "reveal_at IS NULL OR (pre_locked_at IS NOT NULL AND pre_locked_at <= reveal_at)",
            name="ck_decisions_reveal_after_pre_lock",
        ),
    )


class Transition(Base):
    __tablename__ = "transitions"

    transition_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    decision_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("decisions.decision_id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[str] = mapped_column(Text, nullable=True)
    branch_version: Mapped[str] = mapped_column(Text, nullable=True)
    # The seed is stored so a branch draw can be replayed exactly during analysis.
    seed: Mapped[str] = mapped_column(Text, nullable=True)
    probability: Mapped[str] = mapped_column(Text, nullable=True)
    next_state_id: Mapped[str] = mapped_column(Text, nullable=True)
    displayed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class ExpertReference(Base):
    __tablename__ = "expert_references"

    reference_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    scenario_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("scenarios.scenario_id"), nullable=False, index=True
    )
    expert_id: Mapped[str] = mapped_column(Text, nullable=True)
    preferred_action: Mapped[str] = mapped_column(Text, nullable=True)
    acceptable_alternatives: Mapped[dict] = mapped_column(JSONType, nullable=True)
    unsupported_actions: Mapped[dict] = mapped_column(JSONType, nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=True)
    required_evidence: Mapped[str] = mapped_column(Text, nullable=True)
    escalation_expectation: Mapped[str] = mapped_column(Text, nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, nullable=True)
    # Set when the reference is sealed, before any package is shown.
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    # Written only after locking, during the realism review stage.
    realism_review: Mapped[dict] = mapped_column(JSONType, nullable=True)


class AuditEvent(Base):
    """
    Append-only. Nothing in the application updates or deletes a row here.

    Rows arrive from two sources: the application, and the database trigger that rejects writes to
    a locked preliminary judgment.
    """

    __tablename__ = "audit_events"

    event_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    # Not foreign keys. An audit row must survive the deletion of whatever it describes.
    participant_id: Mapped[str] = mapped_column(ULID, nullable=True, index=True)
    scenario_id: Mapped[str] = mapped_column(ULID, nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    server_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    event_metadata: Mapped[dict] = mapped_column("metadata", JSONType, nullable=True)


class ConditionSequence(Base):
    """
    One position in a preregistered counterbalancing sequence. See migration 0004.

    Sequences are data so the design can change without a code change, and the version used is
    recorded on every allocation so an assignment stays reproducible after the design is revised.
    """

    __tablename__ = "condition_sequences"

    sequence_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    order_group: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    scenario_set: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    config_code: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    # Must be set before the sequence can allocate, as for configurations.
    frozen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                 server_default=func.now())

    __table_args__ = (
        CheckConstraint("config_code IN ('C0','C1','C2')", name="ck_condition_sequences_code"),
        CheckConstraint("position >= 1", name="ck_condition_sequences_position"),
        UniqueConstraint("order_group", "scenario_set", "version", "position",
                         name="uq_condition_sequences_position"),
    )


class ActionFamily(Base):
    """Maps a literal action to its family. Data, versioned, frozen before use. See migration 0005."""

    __tablename__ = "action_families"

    map_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    action: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    family: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    frozen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                 server_default=func.now())

    __table_args__ = (
        UniqueConstraint("action", "version", name="uq_action_families_action_version"),
    )


class TransitionRule(Base):
    """
    One candidate branch for a (scenario, period, action_family).

    probability is text so a preregistered decimal survives the round trip exactly; a float would
    turn 0.30 into 0.29999999999999999 in the audit record.
    """

    __tablename__ = "transition_rules"

    rule_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    scenario_id: Mapped[str] = mapped_column(ULID, nullable=False, index=True)
    period: Mapped[str] = mapped_column(Text, nullable=False)
    action_family: Mapped[str] = mapped_column(Text, nullable=False)
    branch_id: Mapped[str] = mapped_column(Text, nullable=False)
    branch_version: Mapped[str] = mapped_column(Text, nullable=False)
    probability: Mapped[str] = mapped_column(Text, nullable=False)
    next_state_id: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    frozen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                 server_default=func.now())

    __table_args__ = (
        UniqueConstraint("scenario_id", "period", "action_family", "branch_id", "version",
                         name="uq_transition_rules_branch"),
    )


class ResearchExport(Base):
    __tablename__ = "research_exports"

    export_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    format: Mapped[str] = mapped_column(Text, nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=True)
    destination: Mapped[str] = mapped_column(Text, nullable=True)
    date_range: Mapped[str] = mapped_column(Text, nullable=True)
    initiated_by: Mapped[str] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
