"""
Per-user feature flags (T1 Part 3).

Some capabilities — the assistant, the Knowledge Library, the portfolio Health dialog, the
technical auditor — must be unavailable to a participant during a research decision period, but
are wanted for real project work run on the same platform. The switch is per user and set by an
admin.

TWO RULES CARRY THE WEIGHT.

Defaults fail safe. An absent key is NOT "off"; it resolves from participants.account_type:
operational accounts default to enabled, research accounts to disabled. An admin who forgets to
configure a research participant therefore gets the restrictive behaviour. Forgetting to enable
a feature for a VP is an annoyance; forgetting to disable one for a participant is contaminated
data that cannot be repaired afterwards. `effective_features` is the only place this resolution
happens, so no call site can invent its own default.

Hiding is not enforcement. The frontend hides a disabled feature, but every action behind a
flagged feature is checked here, server-side, before dispatch, and a refusal is audited. The
check runs in one place — `gate_action`, called from the /exec entry points — rather than being
repeated per handler, for the same reason the consent gate is a flush listener: an endpoint-level
check is only as good as the discipline of whoever adds the next endpoint.

THE HEALTH DIALOG HAS A SECOND CONDITION. Even when `health_dialog` is enabled, portfolio health
is refused while any project the caller belongs to has an unlocked current-period pre-judgment.
That reuses B8's `recommendation_visible` predicate rather than restating the rule; there is
deliberately no second implementation of "may this person see analysis yet".

SCOPE NOTE, stated rather than hidden: /exec has no mandatory authentication, which predates this
phase. The gate refuses any call presenting a session whose flag is off — for a participant using
the instrument that is every call the app makes — but an unauthenticated caller still reaches the
ungated facade actions, exactly as before T1. Closing that requires making authentication
mandatory on /exec, which would break the legacy frontend and every A1b contract test, and is a
separate phase.

NO MODEL CHANGE. participants.features is read and written with dialect-aware SQL here rather
than by adding a column to research_models.Participant, because another session may be editing
server/app/research_* concurrently and this phase must not touch those files.
"""

from __future__ import annotations

import json
from typing import Any, Callable

import sqlalchemy as sa
from sqlalchemy.orm import Session

from .facade import err
from .research_identity import audit, resolve_caller
from .research_models import Participant

# The recognised keys, all boolean. A key outside this set is rejected on write rather than
# stored: an unrecognised flag that nothing reads is indistinguishable from a typo in the key
# an admin meant to set.
FEATURE_KEYS: tuple[str, ...] = ("chat", "knowledge_library", "health_dialog", "auditor",
                                 "training")

FEATURE_LABELS = {
    "chat": "the assistant",
    "knowledge_library": "the Knowledge Library",
    "health_dialog": "the portfolio Health view",
    "auditor": "the technical auditor",
    "training": "training mode",
}

# Which /exec action belongs to which feature. Lowercased action names, matching the facade's
# case-insensitive dispatch.
#
# Actions that do not exist yet (chat, audit, knowledgeget) are listed deliberately. The gate
# runs BEFORE dispatch, so the refusal is already in place for the day the handler lands and
# nobody has to remember to add it.
GATED_ACTIONS: dict[str, str] = {
    # the assistant
    "chat": "chat",
    # Knowledge Library content. See the delivery note in the module docstring of the T1 PR:
    # today the library is embedded in static JS bundles, so this gate covers the server-side
    # content actions that will replace them.
    "knowledgeget": "knowledge_library",
    "knowledgelist": "knowledge_library",
    "getlib": "knowledge_library",
    # portfolio Health
    "getportfoliohealth": "health_dialog",
    "saveportfoliohealth": "health_dialog",
    "portfolioanalyze": "health_dialog",
    # technical auditor
    "audit": "auditor",
    "runaudit": "auditor",
    "saveauditresult": "auditor",
    "listauditresults": "auditor",
    # The technical reviewer's reference corpus: specifications, codes of practice and client
    # or user requirements. Gated under the SAME flag as the rest of the reviewer rather than
    # under a third scheme of its own, per the standing rule that an optional feature is a
    # feature flag and an audience distinction is account_type.
    #
    # ONLY READING IS GATED. Filing is not: with this flag off, a specification is still filed
    # into the Arora tree, still classed `reference`, and still kept out of the analytical
    # path. Turning the reviewer off must not change how a document is stored, or turning it
    # back on would find a corpus with holes in it.
    "projectcorpus": "auditor",
    # Training mode (run 1). `trainingstatus` is the only action this run implements; the rest
    # are listed deliberately, the same way `chat` and `audit` are above, so the gate already
    # covers them the day their handlers land and nobody has to remember to add the line.
    "trainingstatus": "training",
    "trainingstart": "training",
    "trainingstate": "training",
    "trainingdecision": "training",
    "trainingadvance": "training",
    "trainingdebrief": "training",
}


# ---------------------------------------------------------------- account-type gate
#
# Project creation is not a feature flag — it is a property of what kind of account is asking, so
# it is refused by account_type rather than by a per-user toggle nobody would remember to set.
#
# WHY A RESEARCH PARTICIPANT MAY NOT CREATE A PROJECT
#
# The researcher creates the project and its assignment together. A participant who could create
# their own would end up holding a project with no assignment, which the decision sequence cannot
# act on: it is keyed to assignments, so such a project reaches upload and signals and then stops,
# reporting that every assigned period is complete when in fact none was ever assigned. Removing
# the ability to create one removes that state from the research population entirely, which is a
# better fix than wording the dead end more carefully.
#
# Operational accounts keep it. A director running a real project is exactly who should be
# creating one, and they are outside the research record by construction (account_type
# 'operational' can never obtain a consents row, so nothing they do enters an export).
#
# Enforced HERE, before dispatch, for the same reason the feature flags are: hiding the control in
# the interface is not enforcement, and a per-handler check is only as good as whoever adds the
# next handler. `create` is listed alongside `projectcreate` because it is the legacy facade path
# to the same outcome; sessionless callers are unaffected, exactly as with the flags above, so the
# A1b contract fixtures are untouched.
#
# `themeset` is here for a different reason from the two below it, and the reason is worth
# stating. Project creation is refused because a participant would end up holding a project the
# decision sequence cannot act on. A theme change is refused because it would change the
# STIMULUS: on the plain theme a status is a dark mark on white, on the dark themes a bright
# mark on near-black, and how prominent a Red reads is exactly the kind of thing that could move
# a decision. A participant who changed theme would be running a different experiment, and
# nothing in the export would say which one. Hiding the control is a suggestion; this is the
# enforcement. `themeget` is NOT gated: a research account may ask what it renders, and it is
# told the fixed theme.
#
# TRAINING MODE IS FORBIDDEN TO RESEARCH ACCOUNTS UNCONDITIONALLY, not by the flag defaulting off.
# `default_for_account` already resolves an unset `training` key to disabled for a research
# account, so this refusal is redundant on the common path — deliberately, because an admin CAN
# set `training: true` on a research participant's stored row (nothing stops that write) and the
# moment they do, the default-off protection is gone. Listed here the same way `themeset` and
# `projectcreate` are, so the refusal holds regardless of what is stored.
RESEARCH_FORBIDDEN_ACTIONS: frozenset[str] = frozenset({
    "projectcreate",
    "create",
    "themeset",
    "trainingstatus",
    "trainingstart",
    "trainingstate",
    "trainingdecision",
    "trainingadvance",
    "trainingdebrief",
})

# Per action: the audit event to write, and the sentence the participant reads. Keyed by the
# lowered action, with None as the fallback for a forbidden action nobody has written a reason
# for yet, so adding to the set above without adding here degrades to a true-but-vague message
# rather than to a false one about projects.
_RESEARCH_REFUSALS: dict[str | None, tuple[str, str]] = {
    "projectcreate": ("project_creation_denied",
                      "not available: projects are created by the researcher for this study. "
                      "Your assigned projects appear in your portfolio."),
    "create": ("project_creation_denied",
               "not available: projects are created by the researcher for this study. "
               "Your assigned projects appear in your portfolio."),
    "themeset": ("theme_change_denied",
                 "not available: the interface theme is fixed for this account so that every "
                 "participant sees the same thing."),
    "trainingstatus": ("training_denied_research",
                        "not available for this account: training mode is an operational "
                        "feature."),
    "trainingstart": ("training_denied_research",
                       "not available for this account: training mode is an operational "
                       "feature."),
    "trainingstate": ("training_denied_research",
                       "not available for this account: training mode is an operational "
                       "feature."),
    "trainingdecision": ("training_denied_research",
                          "not available for this account: training mode is an operational "
                          "feature."),
    "trainingadvance": ("training_denied_research",
                         "not available for this account: training mode is an operational "
                         "feature."),
    "trainingdebrief": ("training_denied_research",
                         "not available for this account: training mode is an operational "
                         "feature."),
    None: ("research_action_denied", "not available for this account."),
}


# ---------------------------------------------------------------- storage


def _stored_features(session: Session, participant_id: str) -> dict[str, Any]:
    """
    Read participants.features. Postgres returns a dict through psycopg's jsonb adaptation;
    SQLite returns the TEXT it stored. Both are normalised here.
    """
    raw = session.execute(
        sa.text("SELECT features FROM participants WHERE participant_id = :pid"),
        {"pid": participant_id},
    ).scalar()
    if raw is None:
        return {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw or "{}")
        except ValueError:
            return {}
    return raw if isinstance(raw, dict) else {}


def _write_features(session: Session, participant_id: str, features: dict[str, bool]) -> None:
    payload = json.dumps(features, sort_keys=True, separators=(",", ":"))
    if session.bind.dialect.name == "postgresql":
        stmt = sa.text("UPDATE participants SET features = CAST(:f AS JSONB) "
                       "WHERE participant_id = :pid")
    else:
        stmt = sa.text("UPDATE participants SET features = :f WHERE participant_id = :pid")
    session.execute(stmt, {"f": payload, "pid": participant_id})


# ---------------------------------------------------------------- resolution


def default_for_account(account_type: str | None) -> bool:
    """Operational accounts default to enabled; everything else defaults to disabled."""
    return account_type == "operational"


def effective_features(session: Session, participant: Participant) -> dict[str, bool]:
    """
    The resolved flags for one participant. The ONLY place a default is applied.

    A stored value is honoured only when it is a real boolean. Anything else — a string "false",
    a null left by hand-editing — is treated as absent and falls back to the account default,
    because a value the resolver cannot read must not silently become permissive.
    """
    stored = _stored_features(session, participant.participant_id)
    fallback = default_for_account(participant.account_type)
    return {
        key: (stored[key] if isinstance(stored.get(key), bool) else fallback)
        for key in FEATURE_KEYS
    }


def feature_enabled(session: Session, participant: Participant, key: str) -> bool:
    return effective_features(session, participant).get(key, False)


# ---------------------------------------------------------------- the gate


def _health_block_reason(session: Session, caller) -> str | None:
    """
    The Health dialog's SECOND condition, on top of the flag.

    Portfolio health is refused while any project the caller belongs to is mid-period with its
    pre-judgment unlocked. Reuses B8's recommendation_visible; there is no second predicate.

    A membered project with no research assignment in flight — a real operational project — has
    no pre-judgment to wait for and does not block. The condition applies to the research path
    only, which is the path it exists to protect.
    """
    from .models import Project
    from .research_membership import (
        project_decision_state, recommendation_visible,
    )
    from .research_models import ProjectMember

    memberships = session.scalars(
        sa.select(ProjectMember).where(ProjectMember.user_key == caller.participant_id,
                                       ProjectMember.revoked_at.is_(None))
    ).all()
    for m in memberships:
        project = session.get(Project, m.project_id)
        if project is None:
            continue
        assignment, decision, _ = project_decision_state(session, project)
        if assignment is None:
            continue  # no research assignment in flight; nothing to gate on
        if not recommendation_visible(decision):
            return project.legacy_id
    return None


def gate_action(session: Session, action: str, payload: dict, settings) -> dict | None:
    """
    Refuse a flagged action for a caller whose flag is off. Returns a refusal dict, or None to
    let dispatch proceed.

    Applies to callers presenting a session token. A sessionless call is left alone: /exec has
    never authenticated the facade actions, and requiring it here would break the legacy frontend
    and every A1b contract test. See the scope note in the module docstring.
    """
    lowered = (action or "").lower()
    key = GATED_ACTIONS.get(lowered)
    # The account-type gate applies to actions that carry no feature key, so the early return
    # below has to consider both before deciding there is nothing to check.
    if (key is None and lowered not in RESEARCH_FORBIDDEN_ACTIONS) or settings is None:
        return None
    if not payload.get("session_token"):
        return None

    caller, problem = resolve_caller(session, payload, settings.session_secret)
    if problem:
        return problem

    if lowered in RESEARCH_FORBIDDEN_ACTIONS \
            and caller.participant.account_type == "research":
        # The audit event and the sentence are per action, not one generic pair. An audit row
        # reading `project_creation_denied` for a refused theme change would be a false record
        # of what the participant tried to do, and a message about projects would not tell them
        # anything true about what just happened.
        event, reason = _RESEARCH_REFUSALS.get(lowered, _RESEARCH_REFUSALS[None])
        audit(session, event, participant_id=caller.participant_id,
              action=lowered, account_type=caller.participant.account_type)
        session.commit()
        return err(reason)

    if key is None:
        return None

    if not feature_enabled(session, caller.participant, key):
        audit(session, "feature_denied", participant_id=caller.participant_id,
              action=(action or "").lower(), feature=key,
              account_type=caller.participant.account_type)
        session.commit()
        return err(f"not available: {FEATURE_LABELS.get(key, key)} is disabled for this account")

    if key == "health_dialog":
        blocked_on = _health_block_reason(session, caller)
        if blocked_on is not None:
            # Named only by project, never by anything the analysis contains.
            audit(session, "health_denied_unlocked", participant_id=caller.participant_id,
                  action=(action or "").lower(), project_id=blocked_on)
            session.commit()
            return err("portfolio health is not available until the preliminary judgment for "
                       "the current period is locked")

    return None


# ---------------------------------------------------------------- actions


def _require_admin(session: Session, payload: dict, secret: str, action: str):
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return None, problem
    if not caller.is_admin:
        audit(session, "admin_action_denied", participant_id=caller.participant_id,
              action=action, role=caller.role)
        session.commit()
        return None, err("not authorized: ResearchAdmin role required")
    return caller, None


def a_adminfeaturesset(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """Set flags for one user. Audited with both the previous and the new values."""
    caller, problem = _require_admin(session, payload, secret, "adminfeaturesset")
    if problem:
        return problem

    target_id = str(payload.get("participant_id") or "").strip()
    if not target_id:
        return err("participant_id is required")
    target = session.get(Participant, target_id)
    if target is None:
        return err(f"participant not found: {target_id}")

    requested = payload.get("features")
    if not isinstance(requested, dict) or not requested:
        return err("features must be a non-empty object of boolean flags")
    unknown = sorted(set(requested) - set(FEATURE_KEYS))
    if unknown:
        return err(f"unknown feature key(s): {', '.join(unknown)}; "
                   f"recognized keys are {', '.join(FEATURE_KEYS)}")
    non_bool = sorted(k for k, v in requested.items() if not isinstance(v, bool))
    if non_bool:
        return err(f"feature values must be true or false: {', '.join(non_bool)}")

    previous_stored = _stored_features(session, target_id)
    previous_effective = effective_features(session, target)

    merged = {k: v for k, v in previous_stored.items() if k in FEATURE_KEYS
              and isinstance(v, bool)}
    merged.update(requested)
    _write_features(session, target_id, merged)

    audit(session, "features_set", participant_id=target_id, changed_by=caller.participant_id,
          previous=previous_stored, previous_effective=previous_effective, applied=requested,
          now_stored=merged)
    session.commit()

    return {"ok": True, "participant_id": target_id, "stored": merged,
            "effective": effective_features(session, target),
            "previous_stored": previous_stored, "previous_effective": previous_effective}


def a_adminfeaturesget(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "adminfeaturesget")
    if problem:
        return problem
    target_id = str(payload.get("participant_id") or "").strip()
    if not target_id:
        return err("participant_id is required")
    target = session.get(Participant, target_id)
    if target is None:
        return err(f"participant not found: {target_id}")
    return {"ok": True, "participant_id": target_id,
            "account_type": target.account_type,
            "stored": _stored_features(session, target_id),
            "effective": effective_features(session, target),
            "defaults_from_account_type": default_for_account(target.account_type),
            "recognised_keys": list(FEATURE_KEYS)}


def a_researchmyfeatures(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """Any signed-in user: their own effective flags, already resolved against the defaults."""
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    return {"ok": True, "participant_id": caller.participant_id,
            "account_type": caller.participant.account_type,
            "features": effective_features(session, caller.participant)}


FEATURE_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "adminfeaturesset": a_adminfeaturesset,
    "adminfeaturesget": a_adminfeaturesget,
    "researchmyfeatures": a_researchmyfeatures,
}
