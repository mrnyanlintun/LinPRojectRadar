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
from datetime import date, datetime

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, LargeBinary, String,
    Text, UniqueConstraint, Uuid, func,
)
from sqlalchemy.dialects.postgresql import BYTEA, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from .db import Base

JSONType = JSONB().with_variant(JSON(), "sqlite")
BytesType = BYTEA().with_variant(LargeBinary(), "sqlite")
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
    # Structural separation between research subjects and practising staff (B8). An operational
    # account can never obtain a consents row, so the consent gate blocks every research write at
    # source, and adminexportcreate filters on this column unconditionally.
    account_type: Mapped[str] = mapped_column(Text, nullable=False, server_default="research",
                                              default="research")
    # Hash only. A recoverable token would make the pseudonymous code re-identifiable.
    access_token_hash: Mapped[str] = mapped_column(Text, nullable=True)
    # T2. Checked once, in resolve_caller — every authenticated action passes through there, so
    # deactivation takes effect everywhere at once rather than needing a check per endpoint.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true",
                                            default=True)
    # T2. Only ever set for an operational account: research accounts authenticate with the
    # pseudonymous access token and never carry a real identity. Nullable and partial-unique
    # (migration 0008) rather than NOT NULL UNIQUE, since most rows never have one.
    google_email: Mapped[str] = mapped_column(Text, nullable=True)
    # T2. Display label for an operational account. Never set for a research participant, whose
    # only identifier anywhere in the system stays the pseudonymous code.
    display_name: Mapped[str] = mapped_column(Text, nullable=True)
    # Migration 0017. NULL means "has not chosen" and resolves to the default theme, which is
    # what keeps an existing account's appearance unchanged until they choose. Ignored entirely
    # for a research account: app/theme.py returns the fixed theme regardless of this value.
    theme: Mapped[str] = mapped_column(Text, nullable=True)
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
        CheckConstraint(
            "account_type IN ('research','operational')",
            name="ck_participants_account_type",
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
    # T7/T8, migration 0010. Raw, complete capture of every item's answer keyed by the item id
    # from the JSON definition — see that migration's docstring for why this exists alongside
    # the narrow columns above rather than instead of them. A non-null *_captured_at is itself
    # the evidence that that questionnaire was actually submitted, not merely that this row
    # exists (captured_at above is stamped at row creation, which is a different event).
    intake_responses: Mapped[dict] = mapped_column(JSONType, nullable=True)
    intake_captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    debrief_responses: Mapped[dict] = mapped_column(JSONType, nullable=True)
    debrief_captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


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
    # B7b. The computed result this participant actually saw. Once pre_submitted_at is set, the
    # referenced row is frozen by a database trigger (migration 0009) — rewriting the numbers
    # underneath a submitted decision would silently change what the collected data means.
    # Nullable, because a decision recorded before B7b has no computed result behind it and
    # back-filling one would be inventing provenance.
    result_id: Mapped[str] = mapped_column(ULID, nullable=True)

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
    # T4, migration 0011. The structured content of the final decision — see that migration's
    # docstring for why evidence_items is JSONB and deadline is Text. pre_assessment belongs to
    # the PRE side and is written in the same INSERT as pre_action, so the lock covers it from
    # the instant it exists.
    pre_assessment: Mapped[str] = mapped_column(Text, nullable=True)
    evidence_items: Mapped[dict] = mapped_column(JSONType, nullable=True)
    reason_code: Mapped[str] = mapped_column(Text, nullable=True)
    deadline: Mapped[str] = mapped_column(Text, nullable=True)
    residual_risk: Mapped[str] = mapped_column(Text, nullable=True)

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
    # T6: a reference is scored against a participant decision, and decisions are per period.
    # Nullable so references written before 0012 keep their meaning; see that migration.
    period: Mapped[str] = mapped_column(Text, nullable=True)
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


class ProjectMember(Base):
    """
    Per-project membership (B8). One active PM who decides; any number of observers who watch.

    project_id is a real foreign key into the facade's projects table — a deliberate departure
    from this schema's no-facade-FK rule, because membership is ABOUT a facade project and is
    meaningless without it. Revocation sets revoked_at; rows are never deleted, so membership
    history is itself audit evidence. The one-active-PM rule is enforced by a partial unique
    index in migration 0006, not only here.
    """

    __tablename__ = "project_members"

    member_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    project_id = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"),
                               nullable=False, index=True)
    user_key: Mapped[str] = mapped_column(
        ULID, ForeignKey("participants.participant_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    project_role: Mapped[str] = mapped_column(Text, nullable=False)
    added_by: Mapped[str] = mapped_column(Text, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                               server_default=func.now())
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[str] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("project_role IN ('PM','Observer')", name="ck_project_members_role"),
    )


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
    # 0015. What was exported: "participant_inputs" or "project_health" — the two kinds have
    # different scopes (one filtered to research accounts, one not) and different sheet sets,
    # so a fetch needs to know which builder produced the stored checksum. NOT NULL with a
    # server default of the only kind that existed before this column: a record from before
    # the selector existed was a participant-inputs export, by construction.
    kind: Mapped[str] = mapped_column(Text, nullable=False, server_default="participant_inputs")


# --------------------------------------------------------------------- B7b: documents & results


class Document(Base):
    """
    One row per UNIQUE FILE, ever — keyed on the sha256 of the bytes.

    The extraction lives here rather than on the upload event, and that placement is the whole
    design. Two PMs who upload the identical file get byte-identical signalInputs because they
    are reading the SAME extraction row, not because some later step compared two extractions
    and found them equal. Identity of the research stimulus is established by construction
    rather than by verification. It also means one model call per unique document for the
    lifetime of the platform.
    """

    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    # As FIRST uploaded. A later uploader's filename does not overwrite it: the extraction was
    # performed against this name, and the classifier may have used it.
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    content: Mapped[bytes] = mapped_column(BytesType, nullable=True)
    doc_type: Mapped[str] = mapped_column(Text, nullable=True)
    extraction: Mapped[dict] = mapped_column(JSONType, nullable=True)
    # Model identifier AND version — "claude-opus" alone would not let a later reader tell which
    # weights produced a stored figure.
    extraction_model: Mapped[str] = mapped_column(Text, nullable=True)
    # 0016. The classifier's own confidence in `doc_type`, 0..1, or NULL.
    #
    # The classify prompt has always asked the model for `{"docType", "confidence"}`; until
    # this column existed the confidence was parsed and then dropped, so nothing on the
    # platform had ever seen it. It is a property of classifying THESE BYTES, so it belongs on
    # the content-addressed row beside the doc_type it qualifies.
    #
    # NULL is meaningful and is not "unknown so assume fine": it means the model's own claim
    # was NOT the thing that decided the type — the filename heuristic did, or the type is
    # UNMAPPED. `jdrive_tree.needs_review` treats NULL as reviewable for that reason, which
    # preserves `classify`'s existing rule that a rejected classification's confidence is never
    # inherited.
    classification_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now()
    )
    first_uploaded_by: Mapped[str] = mapped_column(Text, nullable=True)


class DocumentUpload(Base):
    """
    One row per upload EVENT. Three PMs uploading the same file produce three rows here and one
    row in `documents`.

    Keeping these separate is what makes "which documents does this project hold for period 2"
    answerable without conflating it with "what have we ever extracted", and it is where
    `was_cached` records whether that particular upload paid for a model call.
    """

    __tablename__ = "document_uploads"

    upload_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    project_id: Mapped[str] = mapped_column(
        Uuid(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    document_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("documents.document_id"), nullable=False, index=True
    )
    # From the session, never the request body.
    uploaded_by: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    was_cached: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false",
                                             default=False)
    # 0013. The document THIS upload replaces, within this project and period. NULL means it
    # replaced nothing, which is the ordinary case and the state of every pre-0013 row.
    #
    # It lives here and not on `documents` because `documents` is content-addressed and shared:
    # the same bytes can be current evidence in one project and superseded in another, so
    # supersession is a statement about a (project, period, document), not about the bytes.
    #
    # The pointer runs NEW -> OLD so that superseding is an INSERT and never an UPDATE of a row
    # a stored decision may reference, and so that a revision can itself be revised as a chain.
    # See migration 0013 for the full argument.
    supersedes_document_id: Mapped[str] = mapped_column(ULID, nullable=True)

    # 0016. WHERE THIS UPLOAD WAS FILED in the Arora project directory, as a `/`-joined path of
    # real folder names with every placeholder already instantiated
    # ("5_CONST ADMIN/8_CLAIMS/CLAIM 7/2026-06-15").
    #
    # It lives here and not on `documents` for exactly the reason `supersedes_document_id`
    # does: `documents` is content-addressed and shared, so the same bytes can be a payment
    # application filed under construction administration in one project and a reference
    # specification in another. Filing is a statement about a (project, period, document), not
    # about the bytes.
    #
    # NO `folders` TABLE EXISTS, and none is needed. The template is code (`jdrive_tree.py`)
    # and a project's real tree is the template plus the distinct values of THIS column. That
    # is what makes "the PM prunes the template" unnecessary: an empty folder never exists.
    folder_path: Mapped[str] = mapped_column(Text, nullable=True, index=True)
    # 0016. What this document IS: 'analysed', 'reference' or 'filed'. Stored rather than
    # recomputed from doc_type, so a document keeps the class it was filed under even if the
    # rules later change; recomputing would silently rewrite history.
    filing_class: Mapped[str] = mapped_column(Text, nullable=True)
    # 0016. The placement needs a human to confirm it: an unknown type, or a classification the
    # model was not confident enough about to file silently into a discipline folder. Mutable:
    # moving the document resolves the review.
    needs_filing_review: Mapped[bool] = mapped_column(Boolean, nullable=False,
                                                      server_default="false", default=False)


class ComputedResult(Base):
    """
    One row per (project, period) computation. Every surface downstream READS this; none of them
    recompute.

    Append-only. A recompute writes a NEW row and sets `superseded_by` on the old one, which
    stays readable forever — a decision that referenced it must still resolve years later. Once
    a submitted decision references a row, a database trigger (migration 0009) rejects any
    UPDATE to it except setting `superseded_by`. Superseding is permitted; changing is not.

    `simulation_version`, `seed` and `period_cutoff` are NOT NULL by design. A stored result
    without them cannot be reproduced, and a later change to the analytical layer becomes
    undetectable in already-collected data.
    """

    __tablename__ = "computed_results"

    result_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    project_id: Mapped[str] = mapped_column(
        Uuid(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    signal_inputs: Mapped[dict] = mapped_column(JSONType, nullable=True)
    module_results: Mapped[dict] = mapped_column(JSONType, nullable=True)
    category_statuses: Mapped[dict] = mapped_column(JSONType, nullable=True)
    project_status: Mapped[str] = mapped_column(Text, nullable=True)
    # Holds `compute_portfolio`'s own return value verbatim, including its insufficient_data
    # shape (with the human-readable message) when the portfolio is too small — see
    # documents.py's `_compute_and_store`. Not stored as a bare NULL: a viewer needs the
    # message, not just the absence of one.
    portfolio_snapshot: Mapped[dict] = mapped_column(JSONType, nullable=True)
    simulation_version: Mapped[str] = mapped_column(Text, nullable=False)
    seed: Mapped[str] = mapped_column(Text, nullable=False)
    period_cutoff: Mapped[date] = mapped_column(Date, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    superseded_by: Mapped[str] = mapped_column(ULID, nullable=True)
    # 0013. Which document VERSIONS produced this result: a list of
    # {document_id, sha256, doc_type, filename}, in the order assembly consumed them.
    #
    # `signal_inputs.sources` records a docType per field and never a document, so before this
    # column a result could not answer "which version of the pay application produced this
    # status" once the period's document set had moved on. NULL on rows computed before 0013.
    source_documents: Mapped[dict] = mapped_column(JSONType, nullable=True)


class Observation(Base):
    """
    0014. One observation per (project, period, document, field, entity). Append-only.

    The storage layer under `signalInputs`: rows are DERIVED from stored extractions by
    `extraction_merge.emit_observations` and persisted at upload and compute time, so a stored
    row can always be re-derived and compared. `signalInputs` is no longer storage — it is the
    OUTPUT of selecting over these rows at a cutoff (see `select_signal_inputs`).

    `kind` is declared per FIELD in `field_registry`, not per document type: a pay application
    is a series source for CPI and an event source for a change record from the same
    extraction. `as_of` is the date the value speaks about, taken from the document's own date
    fields and NULL when none parses — never the clock. `revision_of` is
    `supersedes_document_id` promoted onto every observation the superseding document produces.
    """

    __tablename__ = "observations"

    observation_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    project_id: Mapped[str] = mapped_column(
        Uuid(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    field: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[dict] = mapped_column(JSONType, nullable=True)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    # '' for snapshots so the unique index can include it; see migration 0014.
    entity_key: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    entity_state: Mapped[str] = mapped_column(Text, nullable=True)
    as_of: Mapped[date] = mapped_column(Date, nullable=True)
    document_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("documents.document_id"), nullable=False
    )
    revision_of: Mapped[str] = mapped_column(ULID, nullable=True)
    source_doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("kind IN ('SNAPSHOT','EVENT','DELTA','PERMANENT')",
                        name="ck_observations_kind"),
    )
