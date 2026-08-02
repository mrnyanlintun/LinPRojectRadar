#!/usr/bin/env python3
"""
Run 2: portfolio health retention, overwritesignal field validation, user archive and delete.

Run (from server/):

    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_facade_and_user_lifecycle.py

Part 1. w_saveportfoliohealth APPENDS. The prior snapshot is retained, not deleted; the read
side (`getportfoliohealth`) still answers with the LATEST snapshot only, unchanged.

Part 2. w_overwritesignal refuses a field name outside `field_registry.ALL_SI_FIELDS`, by name.

Part 3. Admin-only, audited, user archive (retention: cannot sign in, everything kept) and
delete (removes everything a row is keyed to, including cascaded research records). Covers:
an archived account cannot sign in and retains every row, including membership history; a
deleted account leaves no orphaned rows in memberships, consents, profiles, assignments,
decisions, transitions; both write an audit event.

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
    from datetime import datetime, timezone

    from fastapi.testclient import TestClient
    from sqlalchemy import select

    import app.main as main_mod
    from app.facade import PORTFOLIO_HEALTH_PERIOD
    from app.field_registry import ALL_SI_FIELDS
    from app.models import Project, ProjectSnapshot
    from app.research_identity import hash_access_token
    from app.research_models import (
        Assignment, AuditEvent, Configuration, Consent, Decision, Participant,
        ParticipantProfile, ProjectMember, Scenario, Transition, new_ulid,
    )

    client = TestClient(main_mod.app, raise_server_exceptions=False)
    Session = main_mod.SessionFactory

    def post(payload: dict) -> dict:
        r = client.post("/exec", content=json.dumps(payload),
                        headers={"Content-Type": "text/plain"})
        assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
        return r.json()

    def get(params: dict) -> dict:
        r = client.get("/exec", params=params)
        assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
        return r.json()

    ADMIN = "run2-admin-token"
    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="RUN2-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        s.commit()
    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

    # An OPERATIONAL writer, for the legacy facade actions: `create`, `saveportfoliohealth` and
    # `overwritesignal` gate on the feature flags default_for_account resolves for account_type
    # (operational defaults enabled; research defaults disabled), the same pattern
    # test_writes_a1b.py uses. The ResearchAdmin token above is for the admin-only actions.
    writer_created = post({"action": "adminparticipantcreate", "session_token": admin,
                          "pseudonymous_code": "RUN2-WRITER", "role": "Participant",
                          "account_type": "operational"})
    writer = post({"action": "researchlogin",
                  "access_token": writer_created["access_token"]})["session_token"]

    # ================================================================== Part 1
    print("\n1. w_saveportfoliohealth appends; the prior snapshot is retained, not deleted")
    with Session() as s:
        before = len(s.scalars(
            select(ProjectSnapshot).where(ProjectSnapshot.period == PORTFOLIO_HEALTH_PERIOD)
        ).all())
    r1 = post({"action": "saveportfoliohealth", "session_token": writer,
              "results": {"alpha": {"modules": []}},
              "projectCount": 1, "computedAt": "2026-08-02T00:00:00.000Z"})
    check(r1.get("ok") is True, "first portfolio health save ok", str(r1)[:100])
    r2 = post({"action": "saveportfoliohealth", "session_token": writer,
              "results": {"beta": {"modules": []}},
              "projectCount": 2, "computedAt": "2026-08-02T01:00:00.000Z"})
    check(r2.get("ok") is True, "second portfolio health save ok", str(r2)[:100])
    with Session() as s:
        rows = s.scalars(
            select(ProjectSnapshot).where(ProjectSnapshot.period == PORTFOLIO_HEALTH_PERIOD)
        ).all()
    check(len(rows) == before + 2,
          "both snapshots are present in the store — nothing was deleted",
          f"before={before} after={len(rows)}")
    has_alpha = any(isinstance(r.snapshot, dict) and "alpha" in (r.snapshot.get("results") or {})
                    for r in rows)
    check(has_alpha, "the FIRST snapshot (alpha) is still IN THE STORE", "")
    health = get({"action": "getportfoliohealth", "session_token": writer})
    check("beta" in health.get("results", {}) and "alpha" not in health.get("results", {}),
          "getportfoliohealth still answers with only the LATEST snapshot", str(health)[:100])

    # ================================================================== Part 2
    print("\n2. w_overwritesignal refuses a field name outside the declared vocabulary")
    # `create` through the facade so `writer` becomes the project's PM in the same transaction
    # — an unmembered project is writable by nobody, per guard_project_write.
    post({"action": "create", "session_token": writer, "id": "PRJ-RUN2-OWS",
         "name": "run2 ows"})
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == "PRJ-RUN2-OWS"))
        fresh = dict(proj.doc or {})
        fresh["signalInputs"] = {"ev": 1000, "cpi": 1.0}
        proj.doc = fresh
        s.commit()
    r = post({"action": "overwritesignal", "session_token": writer, "id": "PRJ-RUN2-OWS",
             "field": "totallyMadeUpField", "value": 123, "reason": "probe"})
    check(r.get("ok") is not True and "totallyMadeUpField" in str(r.get("error")),
          "an unknown field name is refused and named", str(r.get("error"))[:100])
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == "PRJ-RUN2-OWS"))
        check("totallyMadeUpField" not in ((proj.doc or {}).get("signalInputs") or {}),
              "and nothing was written", "")
    r2 = post({"action": "overwritesignal", "session_token": writer, "id": "PRJ-RUN2-OWS",
              "field": "ev", "value": 5_000_000, "reason": "probe"})
    check(r2.get("ok") is True, "a known field name is still accepted", str(r2)[:100])
    check("ev" in ALL_SI_FIELDS and "cpi" in ALL_SI_FIELDS,
          "the declared vocabulary comes from field_registry, not a second list", "")

    # ================================================================== Part 3 setup
    print("\n3. Archive: cannot sign in, everything retained, including membership history")
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": "RUN2-ARCHIVE", "role": "Participant",
                    "account_type": "operational"})
    target_id = created["participant_id"]
    target_token = created["access_token"]
    with Session() as s:
        if s.scalar(select(Project).where(Project.legacy_id == "PRJ-RUN2-ARCH")) is None:
            s.add(Project(legacy_id="PRJ-RUN2-ARCH",
                          doc={"id": "PRJ-RUN2-ARCH", "name": "archive test", "signals": {}}))
        s.commit()
    post({"action": "adminmemberadd", "session_token": admin, "id": "PRJ-RUN2-ARCH",
         "participant_id": target_id, "project_role": "PM"})

    login_before = post({"action": "researchlogin", "access_token": target_token})
    check(login_before.get("ok") is True, "the account can sign in before archiving", "")

    with Session() as s:
        audit_before = len(s.scalars(
            select(AuditEvent).where(AuditEvent.participant_id == target_id,
                                     AuditEvent.event_type == "account_deactivated")
        ).all())

    r = post({"action": "setactive", "session_token": admin,
             "participant_id": target_id, "is_active": False})
    check(r.get("ok") is True and r.get("is_active") is False, "archive (setactive false) ok",
          str(r)[:100])

    login_after = post({"action": "researchlogin", "access_token": target_token})
    check(login_after.get("ok") is not True and "deactivated" in str(login_after.get("error")),
          "the account CANNOT sign in after archiving", str(login_after)[:100])

    with Session() as s:
        still_there = s.get(Participant, target_id)
        check(still_there is not None and still_there.is_active is False,
              "the participant row still exists, marked inactive — not deleted", "")
        members = s.scalars(
            select(ProjectMember).where(ProjectMember.user_key == target_id)
        ).all()
        check(len(members) == 1,
              "the membership row survives archiving — not vanished from history",
              str(len(members)))
        audit_after = len(s.scalars(
            select(AuditEvent).where(AuditEvent.participant_id == target_id,
                                     AuditEvent.event_type == "account_deactivated")
        ).all())
        check(audit_after == audit_before + 1, "archiving wrote an audit event",
              f"{audit_before} -> {audit_after}")

    memlist = post({"action": "adminmemberlist", "session_token": admin, "id": "PRJ-RUN2-ARCH"})
    check(any(m.get("user_key") == target_id or m.get("participant_id") == target_id
             for m in memlist.get("members", [])),
          "the archived user is still visible in the project's membership list",
          str(memlist)[:200])

    # restore, and confirm sign-in works again
    post({"action": "setactive", "session_token": admin,
         "participant_id": target_id, "is_active": True})
    login_restored = post({"action": "researchlogin", "access_token": target_token})
    check(login_restored.get("ok") is True, "restoring reverses it: sign-in works again", "")

    # ================================================================== Part 3 delete
    print("\n4. Delete: removes everything enumerated, no orphaned rows, audited")
    created2 = post({"action": "adminparticipantcreate", "session_token": admin,
                     "pseudonymous_code": "RUN2-DELETE", "role": "Participant",
                     "account_type": "research"})
    del_id = created2["participant_id"]

    with Session() as s:
        if s.scalar(select(Project).where(Project.legacy_id == "PRJ-RUN2-DEL")) is None:
            s.add(Project(legacy_id="PRJ-RUN2-DEL",
                          doc={"id": "PRJ-RUN2-DEL", "name": "delete test", "signals": {}}))
        s.commit()
    post({"action": "adminmemberadd", "session_token": admin, "id": "PRJ-RUN2-DEL",
         "participant_id": del_id, "project_role": "Observer"})
    post({"action": "consentgrant", "session_token":
         post({"action": "researchlogin", "access_token": created2["access_token"]})["session_token"],
         "consent_version": "v1"})

    with Session() as s:
        s.add(ParticipantProfile(participant_id=del_id, experience_level="senior"))
        scenario = Scenario(scenario_version="v1", project_type="construction", period_count=1)
        config = Configuration(code="C1", version="v1", label="single-model")
        s.add_all([scenario, config])
        s.flush()
        assignment = Assignment(participant_id=del_id, scenario_id=scenario.scenario_id,
                                sequence_number=1, config_id=config.config_id)
        s.add(assignment)
        s.flush()
        decision = Decision(assignment_id=assignment.assignment_id, period="P1",
                            pre_action="monitor", pre_confidence=60,
                            pre_submitted_at=datetime.now(timezone.utc))
        s.add(decision)
        s.flush()
        s.add(Transition(decision_id=decision.decision_id, branch_id="b1",
                         branch_version="v1", seed="42", probability="0.5",
                         next_state_id="s1"))
        s.commit()
        assignment_id, decision_id = assignment.assignment_id, decision.decision_id

    with Session() as s:
        pre = {
            "participant": s.get(Participant, del_id) is not None,
            "profile": bool(s.scalars(select(ParticipantProfile).where(
                ParticipantProfile.participant_id == del_id)).all()),
            "consent": bool(s.scalars(select(Consent).where(
                Consent.participant_id == del_id)).all()),
            "membership": bool(s.scalars(select(ProjectMember).where(
                ProjectMember.user_key == del_id)).all()),
            "assignment": bool(s.scalars(select(Assignment).where(
                Assignment.participant_id == del_id)).all()),
            "decision": s.get(Decision, decision_id) is not None,
            "transition": bool(s.scalars(select(Transition).where(
                Transition.decision_id == decision_id)).all()),
        }
    check(all(pre.values()), "PRECONDITION: every row exists before deletion", str(pre))

    with Session() as s:
        audit_before2 = len(s.scalars(
            select(AuditEvent).where(AuditEvent.event_type == "participant_deleted")
        ).all())

    r = post({"action": "admindeleteparticipant", "session_token": admin,
             "participant_id": del_id})
    check(r.get("ok") is True, "delete ok", str(r)[:150])
    removed = r.get("removed") or {}
    check(removed.get("decisions") == 1 and removed.get("transitions") == 1
          and removed.get("assignments") == 1 and removed.get("consents") == 1
          and removed.get("participant_profiles") == 1
          and removed.get("project_memberships") == 1,
          "the response reports exactly what was removed, one of each", str(removed))

    with Session() as s:
        post_state = {
            "participant": s.get(Participant, del_id) is not None,
            "profile": bool(s.scalars(select(ParticipantProfile).where(
                ParticipantProfile.participant_id == del_id)).all()),
            "consent": bool(s.scalars(select(Consent).where(
                Consent.participant_id == del_id)).all()),
            "membership": bool(s.scalars(select(ProjectMember).where(
                ProjectMember.user_key == del_id)).all()),
            "assignment": bool(s.scalars(select(Assignment).where(
                Assignment.participant_id == del_id)).all()),
            "decision": s.get(Decision, decision_id) is not None,
            "transition": bool(s.scalars(select(Transition).where(
                Transition.decision_id == decision_id)).all()),
        }
    check(not any(post_state.values()),
          "NO ORPHANED ROWS: every enumerated table is clear of this participant",
          str(post_state))

    with Session() as s:
        audit_after2 = len(s.scalars(
            select(AuditEvent).where(AuditEvent.event_type == "participant_deleted")
        ).all())
        deletion_row = s.scalar(
            select(AuditEvent).where(AuditEvent.participant_id == del_id,
                                     AuditEvent.event_type == "participant_deleted")
        )
    check(audit_after2 == audit_before2 + 1, "deletion wrote an audit event",
          f"{audit_before2} -> {audit_after2}")
    check(deletion_row is not None,
          "the audit row records participant_id even though the participant is GONE — "
          "audit_events is not a foreign key, by design", "")

    # deleting again refuses cleanly (the row is gone)
    r2 = post({"action": "admindeleteparticipant", "session_token": admin,
              "participant_id": del_id})
    check(r2.get("ok") is not True, "deleting an already-deleted id is refused, not a crash", "")

    # unknown field / missing id validation
    r3 = post({"action": "admindeleteparticipant", "session_token": admin})
    check(r3.get("ok") is not True and "participant_id" in str(r3.get("error")),
          "a delete with no participant_id is refused, named", str(r3.get("error"))[:80])

    # non-admin cannot delete
    other = post({"action": "adminparticipantcreate", "session_token": admin,
                 "pseudonymous_code": "RUN2-NONADMIN", "role": "Participant",
                 "account_type": "operational"})
    other_tok = post({"action": "researchlogin",
                      "access_token": other["access_token"]})["session_token"]
    r4 = post({"action": "admindeleteparticipant", "session_token": other_tok,
              "participant_id": created["participant_id"]})
    check(r4.get("ok") is not True and "not authorized" in str(r4.get("error") or "").lower(),
          "a non-admin cannot delete anyone", str(r4.get("error"))[:80])


try:
    main()
except Exception as e:  # a crash must read as a FAILURE, never as a clean run
    import traceback
    traceback.print_exc()
    check(False, f"suite crashed: {type(e).__name__}: {e}")
finish()
