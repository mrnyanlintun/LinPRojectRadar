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
    # Migration 0017 added participants.theme. IT IS DELIBERATELY NOT MAPPED HERE.
    #
    # 2026-08-02 OUTAGE. It was mapped, and every `select(Participant)` therefore selected the
    # new column, including the one in a_researchlogin. Production applies migrations by hand
    # after the code deploys, so for the whole gap between "0279d7b lands" and "someone runs
    # alembic upgrade head", production's participants table had no theme column and EVERY
    # sign-in raised ProgrammingError: column participants.theme does not exist. Reproduced
    # locally against a database held at 0016 and confirmed as the cause before this was written.
    #
    # Nothing reads .theme as an ORM attribute anywhere in this codebase — app/theme.py always
    # reads and writes it through raw SQL (`stored_theme`, `_write_theme`), specifically so that
    # code can degrade when the column is absent instead of the ORM failing the query before any
    # of that handling runs. Re-adding this as a Mapped column reintroduces the outage; if a
    # future column needs ORM access, add it only once schema and code deploy together, or gate
    # the read behind the same try/except stored_theme() uses.
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
    # 0023. The reporting period's ending date, as the person stated it at upload. NULL where
    # none was stated, including every row written before the selector existed: there is no
    # honest value to backfill for an upload nobody was asked about.
    #
    # It is NOT the period cutoff. `computed_results.period_cutoff` stays derived from the
    # period's own evidence dates (`documents._derive_cutoff`), because two checks depend on
    # that derivation and because bounding selection by a stated date would silently drop the
    # observations of a document this column exists to FLAG. See migration 0023.
    period_end: Mapped[date] = mapped_column(Date, nullable=True)
    # 0027. WITHDRAWN FROM THIS PROJECT'S LIVE FIGURES, and from nothing else.
    #
    # It lives here and not on `documents` for exactly the reason `supersedes_document_id` and
    # `folder_path` do: `documents` is content-addressed and shared, so the same bytes can be
    # live evidence in one project and withdrawn in another. Archival is a statement about a
    # (project, period, document), not about the bytes.
    #
    # NOTHING IS DESTROYED. `documents.content` is untouched and `/documents/{id}/content`
    # keeps serving it. The mark removes the document from the period's LIVE set
    # (`documents._period_documents`), which is the single place supersession is already
    # excluded from computation, so no module can hold a value from an archived document and no
    # other document's observations are touched — both by construction rather than by sweep.
    #
    # NULL means live. Non-NULL names the moment the withdrawal was staged; it does NOT mean the
    # figures have moved, because archiving stages and recomputing applies. `archived_by` is the
    # participant id from the session, never from a request body. Both are NULL on every
    # pre-0027 row, which is the truthful state for an upload nobody ever archived.
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_by: Mapped[str] = mapped_column(Text, nullable=True)


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
    # 0020. Which modules abstained on this row and why, verbatim from `run_all()`'s own
    # `abstained` list: [{module_id, reason}], reason=None when the module gave none. NULL on
    # rows computed before 0020 — the message was never stored for them, so there is nothing to
    # backfill. Never fabricated on read: a NULL here means "no reason on record", not "nothing
    # abstained" (module_results already answers whether something abstained).
    abstained: Mapped[dict] = mapped_column(JSONType, nullable=True)


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


class ScheduleActivity(Base):
    """
    0021. One row per (project, period, document, activity). The schedule, kept as data.

    A CHART CANNOT BE COMPARED ACROSS PERIODS. That is the whole reason this table exists. The
    document's activity table was already stored, as raw `milestones_json` on the document row,
    keyed by whatever headings the source printed and holding dates no parser in this codebase
    could read. Nothing could ask it whether an activity had moved.

    One observation per reporting period, the same rule the observations store follows: the
    same activity seen in four periods is FOUR ROWS, one per period, not four rows competing to
    be current. Which row is "now" is decided by the period being asked about, never by an
    update in place, and an earlier period's account of an activity is never rewritten by a
    later one.

    Dates are stored as the ISO strings `schedule_dates.parse_schedule_date` produced, with a
    `_kind` beside each: 'actual' where the source marked the date actual (the trailing `A` of
    a Primavera P6 export) and 'forecast' otherwise. AN ACTUAL DATE AND A FORECAST DATE ARE
    DIFFERENT FACTS and the distinction is stored, not stripped.

    `unparsed` holds one entry per cell that REFUSED, with the reason. A row whose current
    finish refused has `usable_for_trend` false: it is a missing row, and a missing row is not
    a slip of zero.
    """

    __tablename__ = "schedule_activities"

    schedule_activity_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    project_id: Mapped[str] = mapped_column(
        Uuid(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    document_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("documents.document_id"), nullable=False
    )
    activity_key: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    baseline_start: Mapped[str] = mapped_column(Text, nullable=True)
    baseline_start_kind: Mapped[str] = mapped_column(Text, nullable=True)
    baseline_finish: Mapped[str] = mapped_column(Text, nullable=True)
    baseline_finish_kind: Mapped[str] = mapped_column(Text, nullable=True)
    current_finish: Mapped[str] = mapped_column(Text, nullable=True)
    current_finish_kind: Mapped[str] = mapped_column(Text, nullable=True)
    percent_complete: Mapped[float] = mapped_column(Float, nullable=True)
    unparsed: Mapped[dict] = mapped_column(JSONType, nullable=True)
    usable_for_trend: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    as_of: Mapped[date] = mapped_column(Date, nullable=True)
    source_doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "current_finish_kind IS NULL OR current_finish_kind IN ('actual','forecast')",
            name="ck_schedule_activities_finish_kind",
        ),
    )


class UploadAttempt(Base):
    """
    0022. What was uploaded, and what happened to it. Recorded at upload time.

    THE CONSTRAINT THAT MAKES THIS NECESSARY. Extraction refuses a whole document rather than
    storing part of it, so a failure leaves no `documents` row and no `document_uploads` row.
    The document is not marked bad, it is ABSENT, and no query over what is stored can recover
    which files did not make it. "What failed" therefore has to be written down when the attempt
    is made; it cannot be derived afterwards.

    APPEND ONLY. A retry writes a new row and the failed one stays, because a document that
    failed twice and one that failed once are different facts about that document.

    `error` carries the words of the actual failure verbatim, never a category. The thing that
    refused the document wrote a sentence naming what it saw; replacing it with "extraction
    failed" is exactly the loss this record exists to stop.
    """

    __tablename__ = "upload_attempts"

    upload_attempt_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    project_id: Mapped[str] = mapped_column(
        Uuid(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_id: Mapped[str] = mapped_column(ULID, nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    doc_type: Mapped[str] = mapped_column(Text, nullable=True)
    error: Mapped[str] = mapped_column(Text, nullable=True)
    attempted_by: Mapped[str] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('extracted','matched','filed','failed')",
            name="ck_upload_attempts_status",
        ),
        CheckConstraint(
            "status <> 'failed' OR error IS NOT NULL",
            name="ck_upload_attempts_failure_has_reason",
        ),
    )


class TrainingRun(Base):
    """
    Training mode run 2: one row per training run, the deterministic state store.

    BESIDE the observations store, never inside it (roadmap item 6): a training run has no
    documents, no extractions and no observations. `state` is the CURRENT state the engine
    advances; `history` appends one entry per decision so a run can be replayed and a
    determinism check can compare replays byte for byte. Both are written only by
    `training_engine.advance`, a pure function — this table stores what the engine produced
    and never computes anything itself.

    `project_id` points at a project with `is_training = true`, created together with the run
    in one transaction. The FK cascade mirrors the platform's others, with the same caveat
    run 2's report repeats from the user-lifecycle work: SQLite does not enforce it without a
    PRAGMA the app never sets, so nothing may rely on the cascade for correctness.
    """

    __tablename__ = "training_runs"

    run_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    project_id: Mapped[str] = mapped_column(
        Uuid(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    participant_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("participants.participant_id"), nullable=False, index=True
    )
    contract_form: Mapped[str] = mapped_column(Text, nullable=False)
    contract_value: Mapped[float] = mapped_column(Float, nullable=False)
    conditions: Mapped[str] = mapped_column(Text, nullable=False)
    period: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active",
                                        server_default="active")
    state: Mapped[dict] = mapped_column(JSONType, nullable=False)
    history: Mapped[dict] = mapped_column(JSONType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("status IN ('active','complete')", name="ck_training_runs_status"),
    )


class ProjectRisk(Base):
    """
    0024. One row per (project, period, document, risk). The risk register, kept as data.

    WHY THIS TABLE EXISTS. The register yielded a document risk score and a date and nothing
    else, so the recommendation was made with no knowledge of what the project was already
    worried about, and the three cost-forecasting modules had no calibration data at all. The
    measured consequence: on a design project whose authored estimate at completion was
    4,835,600 dollars, the platform produced an eightieth percentile of 10,555,811. The document
    sets supply no distribution and no percentile of any kind, so that figure came from
    literals. A register carries probability and cost impact per risk, which is a real input.

    ONE OBSERVATION PER REPORTING PERIOD, the rule the observations store and the schedule store
    both follow: the same risk seen in four periods is FOUR ROWS, one per period, not four rows
    competing to be current. An earlier period's account of a risk is never rewritten by a later
    one, which is what makes recomputing that earlier period reproduce it byte for byte.

    WHY NOT THE OBSERVATIONS TABLE. An `Observation` row is one VALUE per (field, entity). A
    risk is a dozen attributes that only mean anything together: a probability without its cost
    impact cannot enter an exposure, and an owner without its risk names nobody. Splitting one
    risk across twelve observation rows would make every read a reassembly, and the schedule
    store set the precedent for exactly this shape.

    A BAND IS NOT A PROBABILITY, AND THE DISTINCTION IS A COLUMN. `probability` holds a number
    only where the register stated one numerically. Where it said "High", or scored the risk 4
    of 5, `probability` is NULL and `probability_band` carries the words verbatim. Nothing in
    this platform converts the second into the first: "High" has no numeric value the document
    states, and every mapping of it to 0.7 or 0.8 imports a number from outside the document and
    presents it as read. That import is the defect this table exists to end, so it is refused at
    the point of storage rather than guarded downstream.

    `usable_for_exposure` is true when the row carries BOTH a numeric probability and a numeric
    cost impact, which is exactly the pair a cost distribution needs. It derives nothing; it
    records whether the two numbers are present. A forecasting module with no usable rows
    abstains, and this column is how it knows.

    `unparsed` holds one entry per cell that REFUSED, with the field and the reason. A risk
    whose probability would not parse is still stored: a register of two hundred risks that
    yielded ninety usable probabilities has to be able to say which hundred and ten refused and
    why, and a dropped row cannot.
    """

    __tablename__ = "project_risks"

    project_risk_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    project_id: Mapped[str] = mapped_column(
        Uuid(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    document_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("documents.document_id"), nullable=False
    )
    risk_key: Mapped[str] = mapped_column(Text, nullable=False)
    # True where the register did not number its rows and the key is the row's position in the
    # table. Stored so a reader is never told a positional key is the register's own identifier.
    keyed_by_position: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(Text, nullable=True)
    probability: Mapped[float] = mapped_column(Float, nullable=True)
    probability_band: Mapped[str] = mapped_column(Text, nullable=True)
    probability_raw: Mapped[str] = mapped_column(Text, nullable=True)
    cost_impact: Mapped[float] = mapped_column(Float, nullable=True)
    time_impact_days: Mapped[float] = mapped_column(Float, nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=True)
    owner: Mapped[str] = mapped_column(Text, nullable=True)
    response_strategy: Mapped[str] = mapped_column(Text, nullable=True)
    mitigation_status: Mapped[str] = mapped_column(Text, nullable=True)
    residual_position: Mapped[str] = mapped_column(Text, nullable=True)
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=True)
    unparsed: Mapped[dict] = mapped_column(JSONType, nullable=True)
    usable_for_exposure: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    as_of: Mapped[date] = mapped_column(Date, nullable=True)
    source_doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "probability IS NULL OR (probability >= 0 AND probability <= 1)",
            name="ck_project_risks_probability_band",
        ),
    )


class ProjectNotice(Base):
    """
    0025. One row per (project, period, document). A notice served, kept as the event it is.

    WHY THIS TABLE EXISTS. `correspondence_notice` extracted a document risk score and a date, so
    a notice served on a project was, to this platform, a number between zero and one. A notice
    is not a number. Someone served it, on someone, it asserts something, and under the contract
    form it starts a clock that can extinguish a right. That is the treatment change orders
    already have, and a served notice had none of it.

    ONE ROW PER DOCUMENT, not per field. The `observations` store holds one VALUE per (field,
    entity), which fits a change order's revised contract sum and does not fit a notice: who
    served it, on whom, what it claims and what it references only mean anything together, and
    splitting them across seven observation rows would make every read a reassembly. This
    follows `schedule_activities` and `project_risks` instead, keyed by (project, period,
    document) because a notice document IS one notice.

    ONE OBSERVATION PER REPORTING PERIOD, the rule the other two stores keep: a notice is written
    once for the period it was filed to and never rewritten by a later one, so recomputing an
    earlier period reproduces it.

    THE DEADLINE IS DERIVED AND ITS BASIS IS STORED BESIDE IT. `deadline_date` is non-NULL only
    where the document named a contract form this platform holds periods for AND that form puts a
    fixed day count on this kind of notice AND the date served could be read. `deadline_basis`
    always says which of those held or did not, so a reader is never shown a blank where a rule
    should be. `deadline_kind` separates a DEADLINE from a LOOKBACK: the federal twenty-day
    figure is a cost cutoff, not an expiry, and printing it as a date would tell a reader their
    claim dies when it does not.

    `date_served_refusal` carries the reason a served date would not parse, using the same
    parser the schedule uses, which refuses rather than inferring a year. A notice whose date
    cannot be read starts no clock this platform will state.
    """

    __tablename__ = "project_notices"

    project_notice_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    project_id: Mapped[str] = mapped_column(
        Uuid(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    document_id: Mapped[str] = mapped_column(
        ULID, ForeignKey("documents.document_id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(Text, nullable=True)
    served_by: Mapped[str] = mapped_column(Text, nullable=True)
    served_on: Mapped[str] = mapped_column(Text, nullable=True)
    claim: Mapped[str] = mapped_column(Text, nullable=True)
    date_served: Mapped[date] = mapped_column(Date, nullable=True)
    date_served_raw: Mapped[str] = mapped_column(Text, nullable=True)
    date_served_refusal: Mapped[str] = mapped_column(Text, nullable=True)
    contract_form: Mapped[str] = mapped_column(Text, nullable=True)
    notice_kind: Mapped[str] = mapped_column(Text, nullable=True)
    references_text: Mapped[str] = mapped_column(Text, nullable=True)
    deadline_date: Mapped[date] = mapped_column(Date, nullable=True)
    deadline_days: Mapped[int] = mapped_column(Integer, nullable=True)
    deadline_kind: Mapped[str] = mapped_column(Text, nullable=True)
    deadline_citation: Mapped[str] = mapped_column(Text, nullable=True)
    deadline_basis: Mapped[str] = mapped_column(Text, nullable=False)
    second_step: Mapped[dict] = mapped_column(JSONType, nullable=True)
    as_of: Mapped[date] = mapped_column(Date, nullable=True)
    source_doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "deadline_kind IS NULL OR deadline_kind IN ('deadline','lookback')",
            name="ck_project_notices_deadline_kind",
        ),
    )


class SpecificationReading(Base):
    """
    RUN 76. What a written specification read, for one project, period and category.

    Append-only, one row per press of a category button. A re-press writes a NEW row and sets
    `superseded_by` on the previous live row for that (project, period, category); the old row
    stays readable forever, for the same reason `computed_results` keeps its history.

    `state` is one of the FOUR the Run 76 order forbids blurring: computed, abstained,
    out_of_order, failed. It is stored as the word, so a reader of the raw table can tell an
    absence of evidence from a platform fault without consulting any code.

    `served_by` says what produced the reading -- "model" for a live call, "recorded" for a
    fixture served where no API key is present. It is NOT NULL: a reading whose origin is
    unknown is worse than no reading.
    """

    __tablename__ = "specification_readings"

    reading_id: Mapped[str] = mapped_column(ULID, primary_key=True, default=new_ulid)
    project_id: Mapped[str] = mapped_column(
        Uuid(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    category_key: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=True)
    counts: Mapped[dict] = mapped_column(JSONType, nullable=True)
    modules: Mapped[dict] = mapped_column(JSONType, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    missing_upstream: Mapped[dict] = mapped_column(JSONType, nullable=True)
    served_by: Mapped[str] = mapped_column(Text, nullable=False)
    model_id: Mapped[str] = mapped_column(Text, nullable=True)
    specification_sha256: Mapped[str] = mapped_column(Text, nullable=True)
    simulation_version: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    superseded_by: Mapped[str] = mapped_column(ULID, nullable=True)
