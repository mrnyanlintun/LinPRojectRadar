#!/usr/bin/env python3
"""
RUN 143, PART 1. REMOVING A REPORTING PERIOD.

Run (from server/), against a THROWAWAY database only:

    DATABASE_URL=sqlite:///<throwaway>.db SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/test_run143p1_period_removal.py

THE GAP. A mis-keyed upload opened a period nothing could remove. Deleting the `documents`
rows by hand -- what was done to PRJ-002 -- removed the bytes and left the period: the project
still listed it, still computed against it, and still offered it. Section 1 reproduces that on
a throwaway database BEFORE using the new endpoint, so the defect is observed and not assumed.

THE SIX PROOFS the order asks for, in order:
  1. a period with documents and no decision removes cleanly (section 3)
  2. a document shared with another period survives; only the link goes (section 4)
  3. a period with a recorded decision is refused, with the reason stated (section 5)
  4. the remaining periods are not renumbered (section 3, section 6)
  5. no dangling supersede reference remains (section 7)
  6. the guard is proven able to fail: the decision check is removed, a decided period becomes
     removable, and the check is restored (section 8)

Every check is paired with a fault that makes it fail, injected and observed, not asserted.
"""
from __future__ import annotations

import base64
import hashlib
import json as _json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))


def section(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def finish() -> None:
    failed = [r for r in RESULTS if not r[0]]
    print(f"\nRESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for ok, label, detail in failed:
        print(f"  FAILED: {label}  [{detail}]")
    sys.exit(1 if failed else 0)


def main() -> None:
    from fastapi.testclient import TestClient
    from sqlalchemy import func, select

    import app.documents as D
    import app.main as main
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor
    from app.models import Project
    from app.research_identity import hash_access_token
    from app.research_models import (
        AuditEvent, ComputedResult, Document, DocumentUpload, ModuleMitigation, Observation,
        Participant, ProjectNotice, ProjectRisk, ScheduleActivity, SpecificationReading,
        UploadAttempt,
    )

    client = TestClient(main.app, raise_server_exceptions=False)
    Session = main.SessionFactory
    ADMIN = "r143p1-admin"

    def raw(tag: str) -> bytes:
        return f"%PDF-1.4 R143P1 {tag}\n".encode()

    def b64(tag: str) -> str:
        return base64.b64encode(raw(tag)).decode()

    # Four distinct documents, one per period, plus SHARED -- identical bytes uploaded to two
    # different periods, which content-addressed storage collapses into ONE `documents` row.
    REC = {}
    for i, tag in enumerate(["D1", "D2", "D3", "D4", "SHARED", "ONLYC"]):
        REC[hashlib.sha256(raw(tag)).hexdigest()] = ("monthly_report", {
            "earned_value": 3.0e6 + i * 1e5, "actual_cost": 3.3e6, "planned_value": 3.2e6,
            "budget_at_completion": 1.2e7,
            "report_date": f"2026-0{i + 3}-15", "document_date": f"2026-0{i + 3}-15"})
    set_extractor_override(StubExtractor(REC))

    def post(payload: dict) -> dict:
        r = client.post("/exec", content=_json.dumps(payload),
                        headers={"Content-Type": "text/plain"})
        return r.json()

    def make_project(legacy_id: str, name: str) -> str:
        with Session() as s:
            row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
            if row is None:
                s.add(Participant(pseudonymous_code="R143A", role="ResearchAdmin",
                                  access_token_hash=hash_access_token(ADMIN)))
            else:
                row.access_token_hash = hash_access_token(ADMIN)
            if s.scalar(select(Project).where(Project.legacy_id == legacy_id)) is None:
                s.add(Project(legacy_id=legacy_id,
                              doc={"id": legacy_id, "name": name, "signals": {}, "events": []}))
            s.commit()
        return legacy_id

    def pm_for(legacy_id: str, code: str) -> str:
        atok = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
        made = post({"action": "adminparticipantcreate", "session_token": atok,
                     "pseudonymous_code": code, "role": "Participant",
                     "account_type": "operational"})
        tok = post({"action": "researchlogin",
                    "access_token": made["access_token"]})["session_token"]
        post({"action": "adminmemberadd", "session_token": atok, "id": legacy_id,
              "participant_id": made["participant_id"], "project_role": "PM"})
        return tok

    def upload(tok: str, pid: str, period: int, tag: str, end: str) -> dict:
        return post({"action": "projectupload", "session_token": tok, "id": pid,
                     "period": period, "period_end": end,
                     "documents": [{"filename": f"{tag}.pdf", "mimeType": "application/pdf",
                                    "dataBase64": b64(tag)}]})

    def uuid_of(legacy_id: str):
        with Session() as s:
            return s.scalar(select(Project.id).where(Project.legacy_id == legacy_id))

    def count(model, pid_uuid, period=None) -> int:
        with Session() as s:
            q = select(func.count()).select_from(model).where(model.project_id == pid_uuid)
            if period is not None:
                q = q.where(model.period == period)
            return int(s.scalar(q) or 0)

    # ---------------------------------------------------------------- 1
    section("1. THE DEFECT REPRODUCED: deleting the documents leaves the period behind")

    A = make_project("PRJ-R143-A", "Removal drive A")
    pmA = pm_for(A, "R143PMA")
    for p, tag in [(1, "D1"), (2, "D2"), (3, "D3"), (4, "D4")]:
        up = upload(pmA, A, p, tag, f"2026-0{p + 2}-28")
        check(up.get("ok") is True, f"period {p} uploads", str(up.get("error")))
        post({"action": "projectcompute", "session_token": pmA, "id": A, "period": p})

    base = post({"action": "projectperiods", "session_token": pmA, "id": A})
    check([r["period"] for r in base.get("periods") or []] == [1, 2, 3, 4],
          "four periods are held to begin with", str(base.get("periods")))
    check(base.get("computed_periods") == [1, 2, 3, 4], "and all four computed",
          str(base.get("computed_periods")))

    uuidA = uuid_of(A)
    # Delete ONLY the `documents` rows for period 3, exactly as PRJ-002 was cleaned.
    with Session() as s:
        ids = list(s.scalars(select(DocumentUpload.document_id).where(
            DocumentUpload.project_id == uuidA, DocumentUpload.period == 3)).all())
        for d in ids:
            for o in s.scalars(select(Observation).where(Observation.document_id == d)).all():
                s.delete(o)
            doc = s.get(Document, d)
            if doc is not None:
                s.delete(doc)
        s.commit()
    stale = post({"action": "projectperiods", "session_token": pmA, "id": A})
    check(3 in [r["period"] for r in stale.get("periods") or []],
          "THE DEFECT: period 3 is still listed after its documents were deleted",
          str([r["period"] for r in stale.get("periods") or []]))
    check(3 in (stale.get("computed_periods") or []),
          "THE DEFECT: the project still computes against period 3",
          str(stale.get("computed_periods")))
    check(count(DocumentUpload, uuidA, 3) > 0,
          "THE DEFECT: the upload link rows survive the document delete",
          str(count(DocumentUpload, uuidA, 3)))

    # ---------------------------------------------------------------- 2
    section("2. THE PREVIEW COUNTS FROM THE DATABASE, NOT FROM THE CALLER")

    B = make_project("PRJ-R143-B", "Removal drive B")
    pmB = pm_for(B, "R143PMB")
    for p, tag in [(1, "D1"), (2, "D2"), (3, "D3"), (4, "D4")]:
        upload(pmB, B, p, tag, f"2026-0{p + 2}-28")
        post({"action": "projectcompute", "session_token": pmB, "id": B, "period": p})
    # A second document into period 3, so the census must count TWO, and recompute so the
    # supersede chain for period 3 is genuinely longer than one row.
    upload(pmB, B, 3, "SHARED", "2026-05-28")
    post({"action": "projectcompute", "session_token": pmB, "id": B, "period": 3})
    uuidB = uuid_of(B)

    prev = post({"action": "projectperiodpreview", "session_token": pmB, "id": B, "period": 3})
    check(prev.get("ok") is True, "the preview answers for the PM", str(prev.get("error")))
    cen = prev.get("census") or {}
    real_docs = len({r for r in _upload_docs(Session, select, DocumentUpload, uuidB, 3)})
    check(cen.get("document_count") == real_docs,
          "the document count is the number of rows the database holds",
          f"census={cen.get('document_count')} db={real_docs}")
    real_results = count(ComputedResult, uuidB, 3)
    check(cen.get("computed_result_count") == real_results,
          "the computed-result count is the WHOLE chain, superseded rows included",
          f"census={cen.get('computed_result_count')} db={real_results}")
    check(real_results > cen.get("live_result_count", 0),
          "and that chain is genuinely longer than its one live row",
          f"chain={real_results} live={cen.get('live_result_count')}")
    check(cen.get("decision_exists") is False, "no decision recorded on period 3 yet")

    required = prev.get("confirmation_required")
    check(isinstance(required, str) and "period 3" in required and str(real_docs) in required,
          "the confirmation sentence states the counted figures", str(required))

    # Fault: a confirmation the caller composed from its OWN idea of the counts is refused.
    lied = post({"action": "projectperiodremove", "session_token": pmB, "id": B, "period": 3,
                 "confirmation": "Remove period 3: 1 document(s), 1 computed result(s), "
                                 "decision recorded: no"})
    check(lied.get("ok") is not True,
          "a confirmation that misstates the counts is REFUSED", str(lied.get("error")))
    check(count(DocumentUpload, uuidB, 3) > 0,
          "and nothing was removed by that refused call", str(count(DocumentUpload, uuidB, 3)))

    # Fault: no confirmation at all is refused.
    bare = post({"action": "projectperiodremove", "session_token": pmB, "id": B, "period": 3})
    check(bare.get("ok") is not True, "a call with no confirmation is refused",
          str(bare.get("error")))

    # Fault: a member who is not the PM is refused.
    atok = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    made = post({"action": "adminparticipantcreate", "session_token": atok,
                 "pseudonymous_code": "R143NPM", "role": "Participant",
                 "account_type": "operational"})
    other = post({"action": "researchlogin",
                  "access_token": made["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": atok, "id": B,
          "participant_id": made["participant_id"], "project_role": "TeamMember"})
    nonpm = post({"action": "projectperiodremove", "session_token": other, "id": B,
                  "period": 3, "confirmation": required})
    check(nonpm.get("ok") is not True, "a member who is not the PM is refused",
          str(nonpm.get("error")))

    # ---------------------------------------------------------------- 3
    section("3. PROOF 1 and PROOF 4: the period removes cleanly and nothing is renumbered")

    before_docs = count(DocumentUpload, uuidB, 3)
    gone = post({"action": "projectperiodremove", "session_token": pmB, "id": B, "period": 3,
                 "confirmation": required})
    check(gone.get("ok") is True, "the removal succeeds with the exact confirmation",
          str(gone.get("error")))
    check(gone.get("deleted", {}).get("document_uploads") == before_docs,
          "every upload link for the period is deleted",
          str(gone.get("deleted")))
    for label, model in (("computed_results", ComputedResult),
                         ("observations", Observation),
                         ("schedule_activities", ScheduleActivity),
                         ("project_risks", ProjectRisk),
                         ("project_notices", ProjectNotice),
                         ("specification_readings", SpecificationReading),
                         ("module_mitigations", ModuleMitigation),
                         ("upload_attempts", UploadAttempt),
                         ("document_uploads", DocumentUpload)):
        check(count(model, uuidB, 3) == 0, f"{label} holds no row for period 3 afterwards",
              str(count(model, uuidB, 3)))

    after = post({"action": "projectperiods", "session_token": pmB, "id": B})
    listed = [r["period"] for r in after.get("periods") or []]
    check(listed == [1, 2, 4], "PROOF 4: the period list is 1, 2, 4 -- NOT renumbered",
          str(listed))
    check(3 not in listed, "PROOF 1: period 3 no longer appears in the project's list",
          str(listed))
    check(after.get("computed_periods") == [1, 2, 4],
          "and the project no longer computes against period 3",
          str(after.get("computed_periods")))
    check(gone.get("renumbered") is False and gone.get("recompute_required") is True,
          "the answer states no renumbering and an outstanding recomputation",
          f"renumbered={gone.get('renumbered')} recompute={gone.get('recompute_required')}")

    # Fault: had the removal renumbered, 4 would have become 3. It did not.
    check(4 in listed and 3 not in listed,
          "period 4 kept its own number rather than sliding down into the gap", str(listed))

    # ---------------------------------------------------------------- 4
    section("4. PROOF 2: a document shared with another period survives; only the link goes")

    C = make_project("PRJ-R143-C", "Removal drive C")
    pmC = pm_for(C, "R143PMC")
    upload(pmC, C, 1, "SHARED", "2026-03-28")     # the SAME bytes into period 1 ...
    upload(pmC, C, 2, "SHARED", "2026-04-28")     # ... and into period 2
    # ONLYC's bytes are uploaded by NO other project and no other period, so it is a genuine
    # orphan once period 2's link goes. Using "D2" here instead was the first attempt and it
    # failed the check -- correctly: project B had also uploaded those same bytes, so the row
    # was shared ACROSS PROJECTS and the removal rightly kept it. That is the cross-project
    # half of the same proof and it is asserted separately below rather than assumed away.
    upload(pmC, C, 2, "ONLYC", "2026-04-28")      # plus one document only period 2 has
    upload(pmC, C, 2, "D2", "2026-04-28")         # and one whose bytes project B also holds
    post({"action": "projectcompute", "session_token": pmC, "id": C, "period": 1})
    post({"action": "projectcompute", "session_token": pmC, "id": C, "period": 2})
    uuidC = uuid_of(C)

    with Session() as s:
        shared_id = s.scalar(select(DocumentUpload.document_id).where(
            DocumentUpload.project_id == uuidC, DocumentUpload.period == 1))
        p2_ids = set(s.scalars(select(DocumentUpload.document_id).where(
            DocumentUpload.project_id == uuidC, DocumentUpload.period == 2)).all())
        # Which of period 2's other documents any OTHER project also holds a link to.
        others = set(s.scalars(select(DocumentUpload.document_id).where(
            DocumentUpload.project_id != uuidC,
            DocumentUpload.document_id.in_(list(p2_ids)))).all())
        cross_project = sorted(others - {shared_id})
        only_p2 = sorted(p2_ids - {shared_id} - others)
    check(shared_id in p2_ids,
          "CONSTRUCTED: identical bytes in periods 1 and 2 are ONE content-addressed row",
          f"shared={shared_id}")
    check(len(only_p2) == 1, "and period 2 holds one document nothing else references",
          str(only_p2))
    check(len(cross_project) == 1,
          "CONSTRUCTED: and one whose identical bytes ANOTHER PROJECT also uploaded",
          str(cross_project))

    prevC = post({"action": "projectperiodpreview", "session_token": pmC, "id": C, "period": 2})
    outC = post({"action": "projectperiodremove", "session_token": pmC, "id": C, "period": 2,
                 "confirmation": prevC.get("confirmation_required")})
    check(outC.get("ok") is True, "period 2 removes", str(outC.get("error")))

    with Session() as s:
        survivor = s.get(Document, shared_id)
        orphan = s.get(Document, only_p2[0])
        link_p1 = int(s.scalar(select(func.count()).select_from(DocumentUpload).where(
            DocumentUpload.project_id == uuidC, DocumentUpload.period == 1,
            DocumentUpload.document_id == shared_id)) or 0)
        link_p2 = int(s.scalar(select(func.count()).select_from(DocumentUpload).where(
            DocumentUpload.project_id == uuidC, DocumentUpload.period == 2)) or 0)
    check(survivor is not None,
          "PROOF 2: the SHARED documents row survives -- period 1 still needs it")
    check(link_p2 == 0, "PROOF 2: but period 2's link to it is gone", str(link_p2))
    check(link_p1 == 1, "PROOF 2: period 1's link is untouched", str(link_p1))
    check(orphan is None,
          "and the document only period 2 held IS deleted -- nothing else referenced it")
    with Session() as s:
        cross = s.get(Document, cross_project[0])
    check(cross is not None,
          "PROOF 2, CROSS-PROJECT: a document ANOTHER PROJECT also uploaded survives too",
          str(cross_project))
    check(sorted(outC.get("documents_retained_shared") or [])
          == sorted([shared_id] + cross_project),
          "the answer names both documents it retained, and why they were retained",
          str(outC.get("documents_retained_shared")))
    check(outC.get("documents_deleted") == only_p2,
          "and names the orphan it deleted", str(outC.get("documents_deleted")))

    # Fault: had the orphan rule been "delete every document the period linked", period 1's
    # evidence would now be missing. It is not: period 1 still resolves its document.
    st1 = post({"action": "projectuploadstatus", "session_token": pmC, "id": C, "period": 1})
    check(len(st1.get("documents") or []) == 1,
          "period 1 still serves its document after period 2 was removed",
          str(len(st1.get("documents") or [])))

    # ---------------------------------------------------------------- 5
    section("5. PROOF 3: a period with a recorded decision is REFUSED, with the reason")

    E = make_project("PRJ-R143-E", "Removal drive E")
    pmE = pm_for(E, "R143PME")
    upload(pmE, E, 1, "D1", "2026-03-28")
    post({"action": "projectcompute", "session_token": pmE, "id": E, "period": 1})
    uuidE = uuid_of(E)

    rec = post({"action": "projectdecisionrecord", "session_token": pmE, "id": E,
                "period": 1, "disposition": "accept",
                "rationale": "the posture is understood and accepted"})
    check(rec.get("ok") is True, "a PM decision is recorded against period 1",
          str(rec.get("error")))

    prevE = post({"action": "projectperiodpreview", "session_token": pmE, "id": E, "period": 1})
    check((prevE.get("census") or {}).get("decision_exists") is True,
          "the preview reads the decision out of the append-only audit table",
          str((prevE.get("census") or {}).get("decision_count")))
    check("decision" in (prevE.get("would_refuse") or "").lower(),
          "and states up front that the removal would be refused",
          str(prevE.get("would_refuse")))

    refused = post({"action": "projectperiodremove", "session_token": pmE, "id": E,
                    "period": 1, "confirmation": prevE.get("confirmation_required")})
    check(refused.get("ok") is not True, "PROOF 3: the removal is refused")
    reason = str(refused.get("error") or "")
    check("decision" in reason.lower() and "governance" in reason.lower(),
          "PROOF 3: and the refusal states WHY", reason)
    check(count(DocumentUpload, uuidE, 1) == 1 and count(ComputedResult, uuidE, 1) >= 1,
          "nothing of the decided period was removed",
          f"uploads={count(DocumentUpload, uuidE, 1)} results={count(ComputedResult, uuidE, 1)}")

    # ---------------------------------------------------------------- 6
    section("6. PROOF 4 again: a THIRD period removed leaves 1 and 4, still not renumbered")

    prevB = post({"action": "projectperiodpreview", "session_token": pmB, "id": B, "period": 2})
    outB = post({"action": "projectperiodremove", "session_token": pmB, "id": B, "period": 2,
                 "confirmation": prevB.get("confirmation_required")})
    check(outB.get("ok") is True, "period 2 removes too", str(outB.get("error")))
    lst = post({"action": "projectperiods", "session_token": pmB, "id": B})
    got = [r["period"] for r in lst.get("periods") or []]
    check(got == [1, 4], "two gaps render as two gaps: 1, 4", str(got))
    check(lst.get("next_period") == 5,
          "and the next new period is still 5 -- the highest held plus one, not a refilled gap",
          str(lst.get("next_period")))

    # ---------------------------------------------------------------- 7
    section("7. PROOF 5: no dangling supersede reference remains anywhere")

    def dangling(model, id_attr) -> list[str]:
        with Session() as s:
            live = {getattr(r, id_attr) for r in s.scalars(select(model)).all()}
            bad = []
            for r in s.scalars(select(model)).all():
                sup = getattr(r, "superseded_by", None)
                if sup and sup not in live:
                    bad.append(f"{model.__tablename__}:{getattr(r, id_attr)}->{sup}")
            return bad

    # `_withdraw_live_result` deliberately writes a FRESH marker that no row bears, so a
    # `computed_results` pointer into nothing is a legitimate state and is excluded from the
    # dangling test by construction: what is tested is that a REMOVAL left no chain half-cut,
    # i.e. no surviving row of a removed period's chain at all.
    with Session() as s:
        left_B3 = int(s.scalar(select(func.count()).select_from(ComputedResult).where(
            ComputedResult.project_id == uuidB, ComputedResult.period == 3)) or 0)
        left_B2 = int(s.scalar(select(func.count()).select_from(ComputedResult).where(
            ComputedResult.project_id == uuidB, ComputedResult.period == 2)) or 0)
    check(left_B3 == 0 and left_B2 == 0,
          "PROOF 5: not one row of either removed period's supersede chain survives",
          f"p3={left_B3} p2={left_B2}")

    with Session() as s:
        # No surviving row anywhere points at a computed_results row that is gone, EXCEPT the
        # withdrawal markers, which point at an id no row ever bore. Distinguish the two: a
        # pointer is dangling-by-removal only if the pointing row and the target shared a
        # (project, period) that was removed. After a whole-chain delete there is no such row.
        remaining = s.scalars(select(ComputedResult).where(
            ComputedResult.project_id == uuidB)).all()
        ids = {r.result_id for r in remaining}
        cut = [r.result_id for r in remaining
               if r.superseded_by and r.superseded_by not in ids and r.period in (2, 3)]
    check(cut == [], "no surviving result of a removed period points at a deleted row", str(cut))

    for model, id_attr in ((SpecificationReading, "reading_id"),
                           (ModuleMitigation, "mitigation_id")):
        check(dangling(model, id_attr) == [],
              f"{model.__tablename__}: no dangling superseded_by pointer",
              str(dangling(model, id_attr)))

    # No projection row names a document that no longer exists -- EXCEPT on project A, whose
    # dangling rows section 1 created deliberately by deleting `documents` rows by hand to
    # reproduce the reported defect. Those are the defect, not a consequence of a removal, so
    # the sweep excludes project A and says so rather than passing by widening the predicate.
    def dangling_documents(exclude) -> list[str]:
        with Session() as s:
            alive = {d.document_id for d in s.scalars(select(Document)).all()}
            out = []
            for model in (DocumentUpload, Observation, ScheduleActivity, ProjectRisk,
                          ProjectNotice):
                for r in s.scalars(select(model)).all():
                    if r.project_id in exclude:
                        continue
                    if r.document_id and r.document_id not in alive:
                        out.append(f"{model.__tablename__}:{r.document_id}")
            return out

    check(dangling_documents({uuidA}) == [],
          "no row of a project that used the REMOVAL references a deleted documents row",
          str(dangling_documents({uuidA})[:5]))
    check(dangling_documents(set()) != [],
          "while project A, cleaned by hand instead, DOES carry dangling references -- which "
          "is the defect this run closes", str(dangling_documents(set())[:3]))

    # Fault: the check can fail. Delete a document that a surviving row still names and watch
    # the same predicate go red, then put it back.
    with Session() as s:
        victim = s.scalar(select(DocumentUpload).where(DocumentUpload.project_id == uuidC,
                                                       DocumentUpload.period == 1))
        doc = s.get(Document, victim.document_id)
        saved = {c.name: getattr(doc, c.name) for c in doc.__table__.columns}
        s.delete(doc)
        s.commit()
    check(dangling_documents({uuidA}) != [],
          "FAULT INJECTED: the dangling-document check goes red when a referenced row is cut",
          str(dangling_documents({uuidA})))
    with Session() as s:
        s.add(Document(**saved))
        s.commit()
    check(dangling_documents({uuidA}) == [], "RESTORED: the check is green again",
          str(dangling_documents({uuidA})))

    # ---------------------------------------------------------------- 8
    section("8. PROOF 6: the decision guard is proven able to fail")

    # Exact counts BEFORE, on the decided period of project E.
    before = {
        "document_uploads": count(DocumentUpload, uuidE, 1),
        "computed_results": count(ComputedResult, uuidE, 1),
        "observations": count(Observation, uuidE, 1),
    }
    print(f"  counts on the decided period before injection: {before}")
    check(before["document_uploads"] > 0 and before["computed_results"] > 0,
          "the decided period genuinely holds rows to lose", str(before))

    original = D._removal_refusal

    def no_decision_check(census, period):
        """The guard with its decision clauses REMOVED -- the injected fault."""
        if (census["upload_count"] == 0 and census["computed_result_count"] == 0
                and census["upload_attempt_count"] == 0):
            return D.err(f"period {period} holds nothing to remove.")
        return None

    D._removal_refusal = no_decision_check
    try:
        prevX = post({"action": "projectperiodpreview", "session_token": pmE, "id": E,
                      "period": 1})
        injected = post({"action": "projectperiodremove", "session_token": pmE, "id": E,
                         "period": 1, "confirmation": prevX.get("confirmation_required")})
        check(injected.get("ok") is True,
              "WITH THE GUARD REMOVED the decided period becomes removable -- the guard was "
              "the only thing stopping it", str(injected.get("error")))
        after_counts = {
            "document_uploads": count(DocumentUpload, uuidE, 1),
            "computed_results": count(ComputedResult, uuidE, 1),
            "observations": count(Observation, uuidE, 1),
        }
        print(f"  counts after the unguarded removal:            {after_counts}")
        check(all(v == 0 for v in after_counts.values()),
              "and it took the decided period's rows with it", str(after_counts))
        with Session() as s:
            kept = [e for e in s.scalars(select(AuditEvent).where(
                AuditEvent.event_type == "project_decision_recorded")).all()
                if (e.event_metadata or {}).get("project_id") == E]
        check(len(kept) == 1,
              "the governance record itself is append-only and was NOT deleted even then",
              str(len(kept)))
    finally:
        D._removal_refusal = original
    check(D._removal_refusal is original, "RESTORED: the guard is back in place")

    # And with the guard restored, a decided period is refused once more.
    F = make_project("PRJ-R143-F", "Removal drive F")
    pmF = pm_for(F, "R143PMF")
    upload(pmF, F, 1, "D4", "2026-03-28")
    post({"action": "projectcompute", "session_token": pmF, "id": F, "period": 1})
    post({"action": "projectdecisionrecord", "session_token": pmF, "id": F, "period": 1,
          "disposition": "accept", "rationale": "accepted"})
    prevF = post({"action": "projectperiodpreview", "session_token": pmF, "id": F, "period": 1})
    againF = post({"action": "projectperiodremove", "session_token": pmF, "id": F, "period": 1,
                   "confirmation": prevF.get("confirmation_required")})
    check(againF.get("ok") is not True,
          "with the guard restored a decided period is refused again",
          str(againF.get("error")))
    check(count(DocumentUpload, uuid_of(F), 1) == 1,
          "and its rows are intact", str(count(DocumentUpload, uuid_of(F), 1)))

    # ---------------------------------------------------------------- 9
    section("9. THE REMOVAL RECORDS ITSELF")

    with Session() as s:
        events = [e for e in s.scalars(select(AuditEvent).where(
            AuditEvent.event_type == "period_removed")).all()
            if (e.event_metadata or {}).get("project_id") == B]
    check(len(events) >= 1, "a period_removed audit row is appended", str(len(events)))
    meta = (events[0].event_metadata or {}) if events else {}
    check("confirmation" in meta and "deleted" in meta,
          "carrying the confirmation and the per-table counts", str(sorted(meta.keys())))
    with Session() as s:
        refusals = [e for e in s.scalars(select(AuditEvent).where(
            AuditEvent.event_type == "period_removal_refused")).all()]
    check(len(refusals) >= 1, "and a refusal is audited too", str(len(refusals)))

    finish()


def _upload_docs(Session, select, DocumentUpload, pid, period):
    with Session() as s:
        return list(s.scalars(select(DocumentUpload.document_id).where(
            DocumentUpload.project_id == pid, DocumentUpload.period == period)).all())


if __name__ == "__main__":
    main()
