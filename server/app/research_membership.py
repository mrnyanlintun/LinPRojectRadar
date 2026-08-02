"""
Project membership, the observer role, and the reveal predicate (B8).

A project has one PM who decides and any number of observers who watch. Membership is granted
per project by an audited admin action; there is no role that sees everything. A non-member
cannot read a project at all; an observer can read everything the PM can read — at the same
time, never sooner.

THE REVEAL PREDICATE — load-bearing, and deliberately a single function.

    recommendation_visible(decision)

A project's recommendation package is not readable by ANY member — including observers — until
that project's PM has locked their preliminary judgment for the current period. This exists
because observers may be senior to the PM: a director who can read the recommendation and
mention it in conversation defeats the independence of the pre-judgment more effectively than
any technical bypass. The lock must hold socially, which means the package must not be visible
to anyone before it is locked.

Every read path that can return package content calls this one predicate:

    research_decision.a_researchreveal   — the PM's own reveal
    a_researchpackageget (this module)   — any member's read of the package

There is intentionally no other path that returns a package to a member, and no per-endpoint
re-implementation of the rule.

Membership guards. Reads require an active membership of either role; the five decision-flow
writes (prejudgment, reveal, decision, advance, upload/save) require the active PM. Projects
with no membership rows at all — everything created before B8 — behave exactly as before, so
the guard changes nothing for the existing flows until an admin grants membership. Observer
reads are audited: who looked at what, and when, is recorded.
"""

from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .facade import err
from .models import File, Project, ProjectSnapshot
from .research_identity import audit, resolve_caller
from .research_models import (
    Assignment, Decision, DecisionSupportPackage, Participant, ProjectMember, Scenario,
)

ROLE_PM = "PM"
ROLE_OBSERVER = "Observer"


# ---------------------------------------------------------------- membership lookups


def _project_by_legacy(session: Session, legacy_id: str | None) -> Project | None:
    if not legacy_id:
        return None
    return session.scalar(select(Project).where(Project.legacy_id == legacy_id))


def active_membership(session: Session, project: Project,
                      participant_id: str) -> ProjectMember | None:
    return session.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_key == participant_id,
            ProjectMember.revoked_at.is_(None),
        )
    )


def has_members(session: Session, project: Project) -> bool:
    return session.scalar(
        select(ProjectMember).where(ProjectMember.project_id == project.id).limit(1)
    ) is not None


def active_pm(session: Session, project: Project) -> ProjectMember | None:
    return session.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.project_role == ROLE_PM,
            ProjectMember.revoked_at.is_(None),
        )
    )


def require_member(session: Session, caller, payload: dict,
                   action: str) -> tuple[Project | None, ProjectMember | None, dict | None]:
    """
    Resolve the target project and refuse anyone who is not an active member.

    Guarantee 1 lives here. The refusal is the standard ok:false shape and the attempt is
    audited: an attempt to read a project one does not belong to is exactly the event the
    audit trail exists to hold. Membership history rows with revoked_at set do not count —
    revocation removes access immediately (Guarantee 8).
    """
    legacy_id = str(payload.get("id") or payload.get("project_id") or "").strip()
    if not legacy_id:
        return None, None, err("id is required")
    project = _project_by_legacy(session, legacy_id)
    if project is None:
        return None, None, err(f"Project not found: {legacy_id}")

    member = active_membership(session, project, caller.participant_id)
    if member is None:
        audit(session, "project_access_denied", participant_id=caller.participant_id,
              action=action, project_id=legacy_id)
        session.commit()
        return None, None, err("not authorized: not a member of this project")
    return project, member, None


def _audit_member_read(session: Session, member: ProjectMember, caller, action: str,
                       legacy_id: str) -> None:
    """Observer reads append to audit_events: who looked at what, and when."""
    audit(session, "project_read", participant_id=caller.participant_id,
          action=action, project_id=legacy_id, project_role=member.project_role)
    session.commit()


# ---------------------------------------------------------------- the reveal predicate


def recommendation_visible(decision: Decision | None) -> bool:
    """
    THE reveal predicate. The recommendation package for a period may be shown to anyone —
    the PM included — only once this period's preliminary judgment row exists and is locked.

    Called by research_decision.a_researchreveal (the PM's own reveal) and by
    a_researchpackageget below (any member's read). No other read path returns a package.
    """
    return decision is not None and bool(decision.pre_judgment_locked)


def project_decision_state(session: Session, project: Project):
    """
    Resolve (assignment, current decision, package) for a project's PM.

    The project's recommendation package hangs off the PM's assignment for the scenario whose
    evidence_package_id names this project. Observers have no assignment of their own; what
    they may see is defined entirely by the PM's decision row, which is what makes
    "exactly what the decider sees, at the same time" implementable as one predicate.
    """
    from .research_decision import _decision_for, current_period

    pm = active_pm(session, project)
    if pm is None:
        return None, None, None
    scenario_ids = session.scalars(
        select(Scenario.scenario_id).where(Scenario.evidence_package_id == project.legacy_id)
    ).all()
    if not scenario_ids:
        return None, None, None
    assignment = session.scalar(
        select(Assignment).where(Assignment.participant_id == pm.user_key,
                                 Assignment.scenario_id.in_(scenario_ids))
    )
    if assignment is None:
        return None, None, None
    scenario = session.get(Scenario, assignment.scenario_id)
    period = current_period(session, assignment, scenario)
    decision = _decision_for(session, assignment.assignment_id, period)
    package = (session.get(DecisionSupportPackage, assignment.package_id)
               if assignment.package_id else None)
    return assignment, decision, package


# ---------------------------------------------------------------- PM-only write guard


def refuse_unless_pm_for_assignment(session: Session, caller, assignment,
                                    action: str) -> dict | None:
    """
    The PM-only guard for the decision flow (prejudgment, reveal, decision, advance).

    Resolves the assignment's scenario to its facade project. If that project has membership
    rows, the caller must be its ACTIVE PM; an observer or a revoked member is refused and
    audited. A project with no membership rows — everything that predates B8 — is unguarded,
    so existing flows and their tests behave exactly as before.
    """
    scenario = session.get(Scenario, assignment.scenario_id)
    project = _project_by_legacy(session, scenario.evidence_package_id if scenario else None)
    if project is None or not has_members(session, project):
        return None
    member = active_membership(session, project, caller.participant_id)
    if member is None or member.project_role != ROLE_PM:
        audit(session, "pm_only_action_denied", participant_id=caller.participant_id,
              action=action, project_id=project.legacy_id,
              project_role=member.project_role if member else None)
        session.commit()
        return err("not authorized: only the project's PM may perform this action")
    return None


PROJECT_WRITE_ACTIONS = frozenset({
    # facade writes that modify a project, plus the (deferred) upload/ingestion paths.
    "save", "archive", "restore", "setprojectnumber", "resetsignals", "overwritesignal",
    "savehistory", "saveauditresult", "ingestcorpus", "extractsignals", "audit",
})


# Facade write actions that may be reached WITHOUT a session token. Deliberately empty.
#
# The guard below fails CLOSED: an action reaches a project write only with a valid session. Any
# action that genuinely needs to be public must name itself here, at its own site, with a reason —
# rather than inheriting permission from a guard that waves through whatever it does not
# recognise. A new write action added to POST_ACTIONS is therefore authenticated by default.
PUBLIC_WRITE_ACTIONS: frozenset[str] = frozenset()


def guard_project_write(session: Session, payload: dict, settings) -> dict | None:
    """
    Authentication and PM-only authorisation for facade project writes, applied in dispatch_post.

    THIS USED TO FAIL OPEN, AND THAT WAS LIVE. It returned None — allow — whenever the caller
    presented no session token, because B8 layered authorisation onto a facade that had never
    been authenticated and its commit message set out to keep "projects with no membership rows
    behave exactly as before, so nothing changes for pre-B8 flows". The consequence, measured
    through /exec: a completely unauthenticated POST could rename, archive, restore, renumber,
    reset the signals of, overwrite a signal on, or write history and audit rows against ANY
    project, including one owned by a PM with membership rows. The legacy frontend was the reason
    it was left open — assets/js/store.js posted no token — and that reason has expired: store.js
    now attaches the session it already holds.

    The order of the checks below is the fix. Authentication first, for every caller: no token,
    or a token that does not resolve, is a refusal. Only then the B8 authorisation question of
    whether this caller is the project's PM.

    A project with NO membership rows is still writable by any authenticated caller. That is the
    pre-B8 legacy shape and it is an authorisation gap, not an authentication one; closing it
    would lock every imported Apps Script project out of the interface at once and needs its own
    decision. It is reported rather than changed here.
    """
    if settings is None:
        # No session secret configured means no token can be verified, so nothing can be
        # authenticated. Refusing is the only safe reading: the previous code allowed the write.
        return err("not authorized: this build cannot verify a session")

    action = str(payload.get("action") or "").lower()
    if action in PUBLIC_WRITE_ACTIONS:
        return None

    if not payload.get("session_token"):
        return err("not authorized: sign in to make this change")

    # AUTHENTICATION, BEFORE ANYTHING ABOUT THE PROJECT. This resolve used to sit BELOW the
    # membership check, so a token that did not resolve was never examined on a project with no
    # membership rows — the write went through on a forged or expired session. Resolving first
    # makes the token's validity a precondition of every facade write, whatever the project is.
    caller, problem = resolve_caller(session, payload, settings.session_secret)
    if problem:
        return problem

    # `save` carries its project id NESTED, as payload["project"]["id"] — every other action puts
    # it at the top level. Reading only payload["id"] meant `save` resolved no project, fell into
    # the "no membership rows" arm, and was allowed: the B8 PM-only rule has never applied to the
    # single most powerful write on the facade, the one that replaces the whole document. The old
    # test asserted that outcome as correct ("sessionless save still works on a membered
    # project"), so nothing caught it.
    legacy_id = str(payload.get("id")
                    or (payload.get("project") or {}).get("id")
                    or "").strip()
    project = _project_by_legacy(session, legacy_id)
    if project is None or not has_members(session, project):
        # Authenticated, and the project has no membership rows to authorise against. This is the
        # pre-B8 legacy shape; see the docstring. Allowed, and reported as the remaining gap.
        return None
    member = active_membership(session, project, caller.participant_id)
    if member is None or member.project_role != ROLE_PM:
        audit(session, "pm_only_action_denied", participant_id=caller.participant_id,
              action=str(payload.get("action") or "").lower(), project_id=legacy_id,
              project_role=member.project_role if member else None)
        session.commit()
        return err("not authorized: only the project's PM may perform this action")
    return None


# ---------------------------------------------------------------- facade read guard


# Reads that name ONE project through an `id` parameter. Membership is checked against that
# project. The rest of the guarded reads are collections and are filtered per row instead.
_PROJECT_SCOPED_READS = frozenset({"get", "gethistory", "listcorpus", "listauditresults"})


def guard_project_read(session: Session, params: dict, settings, action: str) -> dict | None:
    """
    Authentication and membership for facade READS, the mirror of guard_project_write.

    Every GET that can return project data used to be open. Measured through /exec against a
    project owned by a signed-in PM: `get` returned the whole document including its event log,
    `listslim` returned cpi / spi / docRiskScore for every project on the deployment, `gethistory`
    returned stored period snapshots, and none of it needed a credential.

    THE TERMS ARE THE WRITE GUARD'S, with one difference that is deliberate. Authentication first,
    for every caller. Then, where the project has membership rows, the caller must be an ACTIVE
    MEMBER — not necessarily the PM. An Observer is a member precisely so they can read; requiring
    PM here would break the role rather than protect anything, and `require_member` has drawn that
    line for the research read paths since B8.

    A project with NO membership rows stays readable by any authenticated caller, exactly as it
    stays writable by one. That is the pre-B8 legacy shape and closing it is a separate decision
    that needs a membership backfill first; it is reported, not changed here.

    Collection reads are FILTERED, not refused. `list`, `listslim` and `listarchived` return rows
    the caller may see and omit the rest, because refusing the whole call would make a portfolio
    unusable for anyone who is a member of some projects and not others. The filtering lives in
    the handlers, which is where the rows are; this function authenticates and hands them the
    resolved caller.
    """
    if settings is None:
        # No session secret means no token can be verified, so nothing can be authenticated.
        return err("not authorized: this build cannot verify a session")

    caller, problem = resolve_caller(session, params, settings.session_secret)
    if problem:
        return problem
    # Handed to the handlers so a collection read can filter without resolving the caller again.
    params["_caller_participant_id"] = caller.participant_id

    if action not in _PROJECT_SCOPED_READS:
        return None

    legacy_id = str(params.get("id") or "").strip()
    project = _project_by_legacy(session, legacy_id)
    if project is None or not has_members(session, project):
        # Either it does not exist — the handler returns its own "Not found", which is the
        # existing wording and must not be replaced by an authorisation error that would tell an
        # attacker the difference — or it predates B8 and has nobody to authorise against.
        return None
    if active_membership(session, project, caller.participant_id) is None:
        audit(session, "project_access_denied", participant_id=caller.participant_id,
              action=action, project_id=legacy_id)
        session.commit()
        return err("not authorized: not a member of this project")
    return None


def readable_project_ids(session: Session, params: dict) -> set | None:
    """
    The project ids a collection read may return, or None for "no filtering needed".

    None is returned only when the caller could not be resolved, which cannot happen through
    dispatch_get — guard_project_read refuses first. It exists so a handler called directly in a
    test does not silently filter everything away.
    """
    participant_id = params.get("_caller_participant_id")
    if not participant_id:
        return None
    visible = set()
    for project in session.scalars(select(Project)).all():
        if not has_members(session, project):
            visible.add(project.legacy_id)          # pre-B8 legacy: unowned, see the docstring
        elif active_membership(session, project, participant_id) is not None:
            visible.add(project.legacy_id)
    return visible


# ---------------------------------------------------------------- admin actions


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


def _member_view(m: ProjectMember, participant: Participant | None) -> dict[str, Any]:
    return {
        "member_id": m.member_id,
        "user_key": m.user_key,
        "pseudonymous_code": participant.pseudonymous_code if participant else None,
        "project_role": m.project_role,
        "added_by": m.added_by,
        "added_at": m.added_at.isoformat() if m.added_at else None,
        "revoked_at": m.revoked_at.isoformat() if m.revoked_at else None,
        "revoked_by": m.revoked_by,
        "active": m.revoked_at is None,
    }


def a_adminmemberadd(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "adminmemberadd")
    if problem:
        return problem

    legacy_id = str(payload.get("id") or payload.get("project_id") or "").strip()
    user_key = str(payload.get("participant_id") or payload.get("user_key") or "").strip()
    role = str(payload.get("project_role") or "").strip()
    if not legacy_id or not user_key:
        return err("id and participant_id are required")
    if role not in (ROLE_PM, ROLE_OBSERVER):
        return err("project_role must be 'PM' or 'Observer'")

    project = _project_by_legacy(session, legacy_id)
    if project is None:
        return err(f"Project not found: {legacy_id}")
    participant = session.get(Participant, user_key)
    if participant is None:
        return err(f"participant not found: {user_key}")

    if active_membership(session, project, user_key) is not None:
        return err("participant is already an active member of this project")
    # Application-level refusal of a second active PM. The database enforces it too, through
    # the partial unique index in migration 0006, so a bypassed application still cannot.
    if role == ROLE_PM and active_pm(session, project) is not None:
        audit(session, "member_add_denied_second_pm", participant_id=caller.participant_id,
              project_id=legacy_id, attempted_user_key=user_key)
        session.commit()
        return err("this project already has an active PM; revoke them first")

    member = ProjectMember(project_id=project.id, user_key=user_key, project_role=role,
                           added_by=caller.participant_id)
    session.add(member)
    audit(session, "member_added", participant_id=user_key, project_id=legacy_id,
          project_role=role, added_by=caller.participant_id)
    session.commit()

    session.refresh(member)
    return {"ok": True, "member_id": member.member_id, "project_id": legacy_id,
            "user_key": user_key, "project_role": role,
            "added_at": member.added_at.isoformat() if member.added_at else None}


def a_adminmemberrevoke(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "adminmemberrevoke")
    if problem:
        return problem

    member_id = str(payload.get("member_id") or "").strip()
    if not member_id:
        return err("member_id is required")
    member = session.get(ProjectMember, member_id)
    if member is None:
        return err(f"member not found: {member_id}")
    if member.revoked_at is not None:
        return err("membership is already revoked")

    # Revocation, never deletion: the row is the audit evidence of who had access when.
    member.revoked_at = func.now()
    member.revoked_by = caller.participant_id
    audit(session, "member_revoked", participant_id=member.user_key,
          member_id=member_id, revoked_by=caller.participant_id,
          project_role=member.project_role)
    session.commit()

    session.refresh(member)
    return {"ok": True, "member_id": member_id,
            "revoked_at": member.revoked_at.isoformat() if member.revoked_at else None}


def a_adminmemberlist(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "adminmemberlist")
    if problem:
        return problem

    legacy_id = str(payload.get("id") or payload.get("project_id") or "").strip()
    project = _project_by_legacy(session, legacy_id)
    if project is None:
        return err(f"Project not found: {legacy_id}")

    rows = session.scalars(
        select(ProjectMember).where(ProjectMember.project_id == project.id)
        .order_by(ProjectMember.added_at, ProjectMember.member_id)
    ).all()
    return {"ok": True, "project_id": legacy_id, "members": [
        _member_view(m, session.get(Participant, m.user_key)) for m in rows
    ]}


# ---------------------------------------------------------------- member actions


def a_researchmyprojects(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """Lists only the caller's own active memberships. Never a project they do not belong to."""
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    rows = session.scalars(
        select(ProjectMember).where(ProjectMember.user_key == caller.participant_id,
                                    ProjectMember.revoked_at.is_(None))
        .order_by(ProjectMember.added_at)
    ).all()
    projects = []
    for m in rows:
        project = session.get(Project, m.project_id)
        if project is None:
            continue
        projects.append({
            "project_id": project.legacy_id,
            "name": (project.doc or {}).get("name"),
            "project_role": m.project_role,
            "added_at": m.added_at.isoformat() if m.added_at else None,
        })
    return {"ok": True, "projects": projects}


def a_researchprojectmembers(session: Session, payload: dict, secret: str,
                             ttl: int) -> dict[str, Any]:
    """Co-members of a project the caller belongs to. Membership is checked first."""
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload,
                                              "researchprojectmembers")
    if problem:
        return problem
    rows = session.scalars(
        select(ProjectMember).where(ProjectMember.project_id == project.id,
                                    ProjectMember.revoked_at.is_(None))
        .order_by(ProjectMember.added_at, ProjectMember.member_id)
    ).all()
    _audit_member_read(session, member, caller, "researchprojectmembers", project.legacy_id)
    return {"ok": True, "project_id": project.legacy_id, "members": [
        {
            "pseudonymous_code": (p := session.get(Participant, m.user_key))
            and p.pseudonymous_code,
            "project_role": m.project_role,
            "added_at": m.added_at.isoformat() if m.added_at else None,
        }
        for m in rows
    ]}


def a_researchprojectget(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """The project document, for active members of either role. Reads are audited."""
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "researchprojectget")
    if problem:
        return problem
    _audit_member_read(session, member, caller, "researchprojectget", project.legacy_id)
    return {"ok": True, "project_role": member.project_role, "project": project.doc}


def a_researchprojectdocs(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """The project's uploaded documents, for active members of either role."""
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "researchprojectdocs")
    if problem:
        return problem
    rows = session.scalars(
        select(File).where(File.project_id == project.id)
        .order_by(File.ingested_at, File.name)
    ).all()
    _audit_member_read(session, member, caller, "researchprojectdocs", project.legacy_id)
    return {"ok": True, "project_role": member.project_role, "documents": [
        {"fileId": f.drive_file_id, "name": f.name, "docType": f.doc_type,
         "ingestedAt": f.ingested_at.isoformat() if f.ingested_at else None}
        for f in rows
    ]}


def a_researchprojectresults(session: Session, payload: dict, secret: str,
                             ttl: int) -> dict[str, Any]:
    """
    The project's stored computed results, for active members of either role.

    Returns the stored module results and snapshot history. Never the recommendation package:
    the only paths that return package content are the two behind the reveal predicate.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload,
                                              "researchprojectresults")
    if problem:
        return problem
    snapshots = session.scalars(
        select(ProjectSnapshot).where(ProjectSnapshot.project_id == project.id)
        .order_by(ProjectSnapshot.saved_at)
    ).all()
    _audit_member_read(session, member, caller, "researchprojectresults", project.legacy_id)
    doc = project.doc or {}
    return {"ok": True, "project_role": member.project_role,
            "simulation_signals": doc.get("simulationSignals"),
            "signals": doc.get("signals"),
            "history": [s.snapshot for s in snapshots]}


def a_researchpackageget(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    A member's read of the project's recommendation package, behind THE reveal predicate.

    The refusal names only the state. It carries no package content, no package_id and no hash,
    because a refusal that leaked any of those would defeat the gate it is enforcing — the
    entire point is that a director cannot mention the recommendation in conversation before
    the PM has locked.
    """
    from .research_decision import _package_view

    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "researchpackageget")
    if problem:
        return problem

    assignment, decision, package = project_decision_state(session, project)
    if not recommendation_visible(decision):
        audit(session, "package_read_denied_unlocked", participant_id=caller.participant_id,
              project_id=project.legacy_id, project_role=member.project_role)
        session.commit()
        return err("the recommendation package is not available until the project's PM has "
                   "locked their preliminary judgment for the current period")

    if package is None:
        return err("no decision support package is attached to this project's assignment")

    _audit_member_read(session, member, caller, "researchpackageget", project.legacy_id)
    return {"ok": True, "project_role": member.project_role,
            "reveal_at": decision.reveal_at.isoformat() if decision.reveal_at else None,
            "package": _package_view(package)}


MEMBERSHIP_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "adminmemberadd": a_adminmemberadd,
    "adminmemberrevoke": a_adminmemberrevoke,
    "adminmemberlist": a_adminmemberlist,
    "researchmyprojects": a_researchmyprojects,
    "researchprojectmembers": a_researchprojectmembers,
    "researchprojectget": a_researchprojectget,
    "researchprojectdocs": a_researchprojectdocs,
    "researchprojectresults": a_researchprojectresults,
    "researchpackageget": a_researchpackageget,
}
