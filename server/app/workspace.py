"""
T3/T5 — self-service project creation and the project-list read the workspace uses.

Two things live here that B7b and B8 did not need:

SELF-SERVICE CREATION. Every existing path that creates a `Project` (`writes.w_create`) or grants
membership (`research_membership.a_adminmemberadd`) is either unauthenticated or admin-gated.
Neither lets a signed-in participant create a project and become its own PM in one step, which is
how a PM actually starts using the instrument. `a_projectcreate` does both in one transaction: it
inserts the `Project` row (same `doc` shape `w_create` already produces, so every existing reader
of `doc` keeps working) and a `ProjectMember` row with `project_role=PM` for the caller. The
one-active-PM constraint is not reimplemented — a brand-new project has no existing PM, so the
same partial unique index (`uq_project_members_one_active_pm`, migration 0006) that guards
`adminmemberadd` guards this insert for free.

WORKSPACE PROJECT LIST. `a_researchmyprojects` (research_membership.py) already lists "projects
this participant belongs to," and Part 1 says to use it rather than write a second membership
query — so `a_workspaceprojects` below runs the IDENTICAL select (copied, not reinvented) and
adds only what that action does not return: current period and whether it is computed. Modifying
`a_researchmyprojects` itself was avoided deliberately, since it is exercised by the B8 suite and
this phase must not touch validated behaviour to add a workspace-specific presentation field.
"""
from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .documents import _live_result, _resolve_period
from .facade import err, now_iso
from .research_identity import audit, resolve_caller
from .research_membership import ROLE_PM, ProjectMember
from .research_models import Participant, new_ulid
from .models import Project


def _generate_legacy_id() -> str:
    """
    "PRJ-" plus the tail of a fresh ULID. ULIDs are already unique by construction (48-bit
    timestamp + 80 bits of randomness — see `new_ulid`'s docstring in research_models.py), so
    there is no retry-on-collision loop here: the database's unique constraint on `legacy_id`
    is the backstop, and a Crockford-base32 collision in the last 10 characters is not a
    scenario worth a query round-trip to defend against.
    """
    return "PRJ-" + new_ulid()[-10:]


def a_projectcreate(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Any signed-in participant. Creates a project and grants ONE named person PM on it in the same
    transaction, so there is no window where the project exists with no PM and no later step that
    can fail and leave it that way.

    `pm_participant_id` names someone other than the caller and is ADMIN ONLY. It exists because
    the administration surface creates projects on behalf of participants, and the two-step it
    used before could not work: `projectcreate` made the ADMIN the PM, and the `adminmemberadd`
    that followed was then refused by the one-active-PM rule ("this project already has an active
    PM; revoke them first"). Measured through /exec before this change — the project was created,
    the assignment failed, and the intended owner never saw it. The selector was labelled
    optional, so the failure read as a partial success rather than a broken flow.

    Omitted, the caller is the PM, which is the self-service path and is unchanged.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    name = str(payload.get("name") or "").strip()
    if not name:
        return err("name is required")
    sector = str(payload.get("sector") or "").strip()
    address = str(payload.get("address") or "").strip()

    # Who will hold PM. Resolved BEFORE anything is written, so a bad participant id refuses the
    # whole call rather than leaving a project behind for someone to notice later.
    pm_id = str(payload.get("pm_participant_id") or "").strip() or caller.participant_id
    if pm_id != caller.participant_id:
        if not caller.is_admin:
            audit(session, "admin_action_denied", participant_id=caller.participant_id,
                  action="projectcreate", reason="assigning PM to another participant")
            session.commit()
            return err("not authorized: only a ResearchAdmin may assign another person as PM")
        if session.get(Participant, pm_id) is None:
            return err(f"participant not found: {pm_id}")

    pid = _generate_legacy_id()
    now = now_iso()
    # Identical shape to writes.w_create's doc, so nothing that reads Project.doc (signals,
    # events, status) needs a second code path for a workspace-created project.
    doc = {
        "id": pid,
        "name": name,
        "sector": sector,
        "signals": {},
        "events": [{"event": "project_created", "at": now}],
        "status": "",
        "createdAt": now,
        "updatedAt": now,
    }
    # Geocode before the insert, so the project is stored complete rather than written twice.
    #
    # This CANNOT stop the project being created. geocode.apply_to_doc never raises and never
    # waits longer than its own timeout, so an unreachable geocoder costs a few seconds and then
    # the project saves with a geocodeError the interface shows the user. Reporting that plainly
    # is the point: a project silently without coordinates looks identical to one the geocoder
    # could not find, and those need different things done about them.
    geo = None
    if address:
        from .geocode import apply_to_doc
        geo = apply_to_doc(doc, address)

    project = Project(legacy_id=pid, doc=doc, archived=False, record_version=1)
    session.add(project)
    session.flush()

    # THE SAME TRANSACTION as the project row above. Nothing is committed until both exist, so a
    # failure anywhere below leaves neither and the unmembered state is unreachable by
    # construction rather than by a later repair.
    session.add(ProjectMember(project_id=project.id, user_key=pm_id,
                              project_role=ROLE_PM, added_by=caller.participant_id))
    self_service = pm_id == caller.participant_id
    audit(session, "project_created", participant_id=caller.participant_id, project_id=pid,
          name=name, sector=sector, self_service=self_service, pm_participant_id=pm_id)
    audit(session, "member_added", participant_id=pm_id, project_id=pid,
          project_role=ROLE_PM, self_service=self_service, added_by=caller.participant_id)
    session.commit()

    return {"ok": True, "project_id": pid, "name": name, "sector": sector,
           # The caller's OWN role on the project. An admin who assigned someone else is not a
           # member, and saying "PM" to them would be false.
           "project_role": ROLE_PM if self_service else None,
           "pm_participant_id": pm_id,
           "period": 1, "computed": False,
           # Reported so the interface can say what happened rather than leaving the PM to
           # notice later that their project is missing from the map.
           "address": address or None,
           "lat": doc.get("lat"), "lng": doc.get("lng"),
           "formattedAddress": doc.get("formattedAddress"),
           "geocodeError": doc.get("geocodeError"),
           "geocodeStale": doc.get("geocodeStale"),
           "server_time": now_iso()}


def a_workspaceprojects(session: Session, payload: dict, secret: str,
                        ttl: int) -> dict[str, Any]:
    """
    The caller's own projects, with the fields the workspace list needs: role, current period,
    and whether that period has been computed. Never a project the caller does not belong to.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    # Same select as research_membership.a_researchmyprojects — reused, not reinvented.
    rows = session.scalars(
        select(ProjectMember).where(ProjectMember.user_key == caller.participant_id,
                                    ProjectMember.revoked_at.is_(None))
        .order_by(ProjectMember.added_at)
    ).all()

    projects: list[dict] = []
    for m in rows:
        project = session.get(Project, m.project_id)
        if project is None:
            continue
        period, _problem = _resolve_period(session, project, {})
        result = _live_result(session, project, period) if period is not None else None
        projects.append({
            "project_id": project.legacy_id,
            "name": (project.doc or {}).get("name"),
            "sector": (project.doc or {}).get("sector"),
            # WHAT THE GEOCODER MATCHED, not what the PM typed. These differ more often than is
            # comfortable: "Philadelphia International Airport, Philadelphia, PA" resolves to a
            # hotel on Bartram Avenue about 1.5 km from the airport. A blank map signals a
            # problem; a pin on the wrong building signals nothing, so the matched address has to
            # be visible rather than buried in the stored document.
            "address": (project.doc or {}).get("address"),
            "formattedAddress": (project.doc or {}).get("formattedAddress"),
            "geocodeError": (project.doc or {}).get("geocodeError"),
            # Whether the coordinates above belong to an EARLIER address than the one stored.
            # Without it a surface cannot tell a current match from a retained one.
            "geocodeStale": (project.doc or {}).get("geocodeStale"),
            "lat": (project.doc or {}).get("lat"),
            "lng": (project.doc or {}).get("lng"),
            "project_role": m.project_role,
            "period": period,
            "computed": result is not None,
            "added_at": m.added_at.isoformat() if m.added_at else None,
        })
    return {"ok": True, "projects": projects, "server_time": now_iso()}


WORKSPACE_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "projectcreate": a_projectcreate,
    "workspaceprojects": a_workspaceprojects,
}
