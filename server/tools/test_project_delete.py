#!/usr/bin/env python3
"""
Project delete: admin-only permanent deletion of a project, and the PM/Observer archive-restore
fix that makes those two match the rule "PM and observer can archive and restore; they cannot
delete."

Run (from server/):

    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_project_delete.py

Covers:
  1. Archive and restore work for both PM and Observer (server-side, not just UI absence).
  2. A PM cannot delete: refused server-side even calling the action directly.
  3. An Observer cannot delete: refused server-side.
  4. An admin can delete, and the project is gone for every member, not only the admin — checked
     from a second user's (the PM's) own read, not merely that the row vanished from the DB.
  5. No orphaned row survives in any project-keyed table, queried directly.
  6. The audit event survives the deletion and still names the project.

The whole run is wrapped so a crash prints a failing RESULT line, never a clean-looking silence.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))


def finish() -> None:
    failed = [r for r in RESULTS if not r[0]]
    print(f"\nRESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    sys.exit(1 if failed else 0)


def main() -> None:
    from datetime import date

    from fastapi.testclient import TestClient
    from sqlalchemy import select

    import app.main as main_mod
    from app.models import File, Project, ProjectSnapshot
    from app.research_identity import hash_access_token
    from app.research_models import (
        AuditEvent, ComputedResult, DocumentUpload, Document, Observation, Participant,
        ProjectMember, ScheduleActivity, TrainingRun,
    )

    client = TestClient(main_mod.app, raise_server_exceptions=False)
    Session = main_mod.SessionFactory

    def post(payload: dict) -> dict:
        r = client.post("/exec", content=json.dumps(payload),
                        headers={"Content-Type": "text/plain"})
        assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
        return r.json()

    ADMIN = "pd-admin-token"
    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="PD-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        s.commit()
    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

    def make_operational(code: str) -> str:
        created = post({"action": "adminparticipantcreate", "session_token": admin,
                        "pseudonymous_code": code, "role": "Participant",
                        "account_type": "operational"})
        return post({"action": "researchlogin",
                     "access_token": created["access_token"]})["session_token"], created["participant_id"]

    pm_token, pm_id = make_operational("PD-PM")
    obs_token, obs_id = make_operational("PD-OBS")

    # -------------------------------------------------------------- setup: one project, PM + Observer
    print("\n0. Setup: PM creates a project, Observer is added")
    created = post({"action": "create", "session_token": pm_token, "id": "PRJ-PD-1",
                    "name": "project delete test"})
    check(created.get("ok") is True, "project created", str(created)[:150])
    add_obs = post({"action": "adminmemberadd", "session_token": admin, "id": "PRJ-PD-1",
                    "participant_id": obs_id, "project_role": "Observer"})
    check(add_obs.get("ok") is True, "observer added", str(add_obs)[:150])

    # -------------------------------------------------------------- 1. archive/restore for PM and Observer
    print("\n1. Archive and restore work for both PM and Observer")
    arch_pm = post({"action": "archive", "session_token": pm_token, "id": "PRJ-PD-1"})
    check(arch_pm.get("ok") is True, "PM can archive", str(arch_pm)[:150])
    rest_obs = post({"action": "restore", "session_token": obs_token, "id": "PRJ-PD-1"})
    check(rest_obs.get("ok") is True, "Observer can restore", str(rest_obs)[:150])
    arch_obs = post({"action": "archive", "session_token": obs_token, "id": "PRJ-PD-1"})
    check(arch_obs.get("ok") is True, "Observer can archive", str(arch_obs)[:150])
    rest_pm = post({"action": "restore", "session_token": pm_token, "id": "PRJ-PD-1"})
    check(rest_pm.get("ok") is True, "PM can restore", str(rest_pm)[:150])

    # A caller with NO membership at all is still refused archive/restore.
    stranger_token, _ = make_operational("PD-STRANGER")
    stranger_arch = post({"action": "archive", "session_token": stranger_token, "id": "PRJ-PD-1"})
    check(stranger_arch.get("ok") is not True,
          "a non-member is still refused archive", str(stranger_arch)[:150])

    # -------------------------------------------------------------- 2/3. delete refused for PM/Observer
    print("\n2. A PM cannot delete: refused server-side")
    pm_delete = post({"action": "admindeleteproject", "session_token": pm_token,
                      "project_id": "PRJ-PD-1"})
    check(pm_delete.get("ok") is not True and "not authorized" in str(pm_delete.get("error", "")),
          "PM's own delete call is refused", str(pm_delete)[:150])

    print("\n3. An Observer cannot delete: refused server-side")
    obs_delete = post({"action": "admindeleteproject", "session_token": obs_token,
                       "project_id": "PRJ-PD-1"})
    check(obs_delete.get("ok") is not True and "not authorized" in str(obs_delete.get("error", "")),
          "Observer's own delete call is refused", str(obs_delete)[:150])

    with Session() as s:
        still_there = s.scalar(select(Project).where(Project.legacy_id == "PRJ-PD-1"))
    check(still_there is not None, "the project still exists after both refused attempts", "")

    # -------------------------------------------------------------- seed every project-keyed table
    print("\n4. Seed every project-keyed table before deletion")
    with Session() as s:
        project = s.scalar(select(Project).where(Project.legacy_id == "PRJ-PD-1"))
        pid = project.id

        doc = Document(sha256="f" * 64, filename="test.pdf", doc_type="pay_app")
        s.add(doc)
        s.flush()
        document_id = doc.document_id

        s.add(ProjectSnapshot(project_id=pid, period="1", snapshot={"x": 1}))
        s.add(File(project_id=pid, drive_file_id="drv-1", name="audit.pdf", doc_type="audit_result"))
        s.add(DocumentUpload(project_id=pid, period=1, document_id=document_id,
                             uploaded_by=pm_id))
        s.add(ComputedResult(project_id=pid, period=1, simulation_version="v1", seed="1",
                             period_cutoff=date(2026, 1, 1)))
        s.add(Observation(project_id=pid, period=1, field="ev", value={"v": 1}, kind="SNAPSHOT",
                          document_id=document_id, source_doc_type="pay_app"))
        s.add(ScheduleActivity(project_id=pid, period=1, document_id=document_id,
                               activity_key="A1", source_doc_type="schedule"))
        s.add(TrainingRun(project_id=pid, participant_id=pm_id, contract_form="fixed",
                          contract_value=1.0, conditions="none", state={}, history=[]))
        s.commit()

        seeded = {
            "project_snapshots": s.scalar(select(ProjectSnapshot).where(ProjectSnapshot.project_id == pid)) is not None,
            "files": s.scalar(select(File).where(File.project_id == pid)) is not None,
            "document_uploads": s.scalar(select(DocumentUpload).where(DocumentUpload.project_id == pid)) is not None,
            "computed_results": s.scalar(select(ComputedResult).where(ComputedResult.project_id == pid)) is not None,
            "observations": s.scalar(select(Observation).where(Observation.project_id == pid)) is not None,
            "schedule_activities": s.scalar(select(ScheduleActivity).where(ScheduleActivity.project_id == pid)) is not None,
            "training_runs": s.scalar(select(TrainingRun).where(TrainingRun.project_id == pid)) is not None,
            "project_members": s.scalar(select(ProjectMember).where(ProjectMember.project_id == pid)) is not None,
        }
    check(all(seeded.values()), "every project-keyed table has a seeded row before delete",
          str(seeded))

    # -------------------------------------------------------------- 5. admin deletes; gone for everyone
    print("\n5. Admin deletes the project; it is gone for every member, not only the admin")
    del_resp = post({"action": "admindeleteproject", "session_token": admin,
                     "project_id": "PRJ-PD-1"})
    check(del_resp.get("ok") is True, "admin delete succeeds", str(del_resp)[:200])

    # From the PM's OWN read path, not the database directly.
    pm_read = post({"action": "researchprojectget", "session_token": pm_token, "id": "PRJ-PD-1"})
    check(pm_read.get("ok") is not True, "the PM can no longer read the project", str(pm_read)[:150])
    obs_read = post({"action": "researchprojectget", "session_token": obs_token, "id": "PRJ-PD-1"})
    check(obs_read.get("ok") is not True, "the Observer can no longer read it either",
          str(obs_read)[:150])
    pm_projects = post({"action": "researchmyprojects", "session_token": pm_token})
    check(all(p.get("project_id") != "PRJ-PD-1" for p in (pm_projects.get("projects") or [])),
          "it no longer appears in the PM's own project list", str(pm_projects)[:200])

    # -------------------------------------------------------------- 6. no orphans anywhere
    print("\n6. No orphaned row survives in any project-keyed table")
    with Session() as s:
        orphans = {
            "projects": s.scalar(select(Project).where(Project.legacy_id == "PRJ-PD-1")) is not None,
            "project_snapshots": s.scalar(select(ProjectSnapshot).where(ProjectSnapshot.project_id == pid)) is not None,
            "files": s.scalar(select(File).where(File.project_id == pid)) is not None,
            "document_uploads": s.scalar(select(DocumentUpload).where(DocumentUpload.project_id == pid)) is not None,
            "computed_results": s.scalar(select(ComputedResult).where(ComputedResult.project_id == pid)) is not None,
            "observations": s.scalar(select(Observation).where(Observation.project_id == pid)) is not None,
            "schedule_activities": s.scalar(select(ScheduleActivity).where(ScheduleActivity.project_id == pid)) is not None,
            "training_runs": s.scalar(select(TrainingRun).where(TrainingRun.project_id == pid)) is not None,
            "project_members": s.scalar(select(ProjectMember).where(ProjectMember.project_id == pid)) is not None,
        }
    check(not any(orphans.values()), "not one of the eight cleared tables has a surviving row",
          str(orphans))
    # The document itself is content-addressed and shared: it is NOT removed by a project delete.
    with Session() as s:
        doc_survives = s.scalar(select(Document).where(Document.document_id == document_id)) is not None
    check(doc_survives, "the shared document row itself survives (content-addressed, not project-owned)", "")

    # -------------------------------------------------------------- 7. audit event survives
    print("\n7. The audit event survives the deletion and still names the project")
    with Session() as s:
        events = s.scalars(
            select(AuditEvent).where(AuditEvent.event_type == "project_deleted")
        ).all()
        matching = [e for e in events
                    if isinstance(e.event_metadata, dict)
                    and e.event_metadata.get("project_id") == "PRJ-PD-1"]
    check(len(matching) == 1, "exactly one project_deleted audit row names PRJ-PD-1",
          f"{len(matching)} matches out of {len(events)} project_deleted rows")
    if matching:
        removed = matching[0].event_metadata.get("removed") or {}
        check(removed.get("computed_results", 0) >= 1 and removed.get("project_members", 0) >= 1,
              "the audit row's removed counts reflect the real deletion", str(removed))

    finish()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"RESULT: CRASHED — {exc!r}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
