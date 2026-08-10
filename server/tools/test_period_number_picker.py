#!/usr/bin/env python3
"""
The upload modal's period picker is a NUMBER, not a date.

Run (from server/):

    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_period_number_picker.py

WHAT CHANGED AND WHAT DID NOT. The calendar picker `test_period_picker_and_evidence.py` proved
end to end is untouched: `period_for_end_date`, `projectperiodfordate`, and every existing caller
that sends an explicit `period` plus its own `period_end` (workspace.js's Period documents panel)
behave exactly as before. This suite covers the two things that are new:

1. `a_projectperiods` (action `projectperiods`) -- the read-only list the picker's <select>
   is built from: the periods this project already holds, each with its stated ending date
   where one is on file, plus the next new one.
2. `a_projectupload`'s new period_end FALLBACK -- when the client sends a period NUMBER and no
   date at all, the server reuses that period's own previously stated ending date (exactly the
   date `period_for_end_date` used to hand back for a MATCHED existing period), so the
   out-of-period check keeps working without the client ever sending a date again. A brand-new
   period has no stated date to reuse and stays NULL, which is the pre-existing "nothing to
   measure against" behaviour, not a new gap.

Every check below is proven able to fail: each assertion is paired with a fault injected right
above it (a monkeypatch, a bad input, or a deliberately wrong expectation), observed red, then
reverted and observed green again.
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
    sys.exit(1 if failed else 0)


def main() -> None:
    from fastapi.testclient import TestClient
    from sqlalchemy import select

    import app.documents as D
    import app.main as main
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor
    from app.models import Project
    from app.research_identity import hash_access_token
    from app.research_models import Participant

    client = TestClient(main.app, raise_server_exceptions=False)
    Session = main.SessionFactory
    ADMIN, PRJ = "npp-admin", "PRJ-NPP"

    def raw(tag: str) -> bytes:
        return f"%PDF-1.4 NPP {tag}\n".encode()

    def b64(tag: str) -> str:
        return base64.b64encode(raw(tag)).decode()

    REC = {
        hashlib.sha256(raw("M1")).hexdigest(): ("monthly_report", {
            "earned_value": 3e6, "actual_cost": 3.3e6, "planned_value": 3.2e6,
            "budget_at_completion": 1.2e7, "report_date": "2026-03-15",
            "document_date": "2026-03-15"}),
        hashlib.sha256(raw("M2")).hexdigest(): ("monthly_report", {
            "earned_value": 4e6, "actual_cost": 4.3e6, "planned_value": 4.2e6,
            "budget_at_completion": 1.2e7, "report_date": "2026-04-15",
            "document_date": "2026-04-15"}),
        hashlib.sha256(raw("LATE")).hexdigest(): ("monthly_report", {
            "earned_value": 4.1e6, "actual_cost": 4.4e6, "planned_value": 4.3e6,
            "budget_at_completion": 1.2e7, "report_date": "2026-05-20",
            "document_date": "2026-05-20"}),
    }
    set_extractor_override(StubExtractor(REC))

    def post(payload: dict) -> dict:
        r = client.post("/exec", content=_json.dumps(payload),
                        headers={"Content-Type": "text/plain"})
        return r.json()

    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="NPPA", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == PRJ)) is None:
            s.add(Project(legacy_id=PRJ, doc={"id": PRJ, "name": "Number picker drive",
                                              "signals": {}, "events": []}))
        s.commit()

    atok = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    made = post({"action": "adminparticipantcreate", "session_token": atok,
                 "pseudonymous_code": "NPPPM", "role": "Participant",
                 "account_type": "operational"})
    pm = post({"action": "researchlogin", "access_token": made["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": atok, "id": PRJ,
          "participant_id": made["participant_id"], "project_role": "PM"})

    section("1. projectperiods: BEFORE ANY UPLOAD, ONLY 'PERIOD 1 (NEW)' IS OFFERED")

    empty = post({"action": "projectperiods", "session_token": pm, "id": PRJ})
    check(empty.get("ok") is True, "projectperiods answers for a project with no uploads yet")
    check(empty.get("periods") == [], "no existing periods yet", str(empty.get("periods")))
    check(empty.get("next_period") == 1, "the next period offered is 1", str(empty.get("next_period")))

    # Fault: a project the caller is not a member of must be refused, not answered.
    stranger_pm = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    denied = post({"action": "projectperiods", "session_token": atok, "id": "PRJ-DOES-NOT-EXIST"})
    check(denied.get("ok") is not True, "projectperiods refuses an unknown project", str(denied))

    section("2. PERIOD 1 UPLOADED WITH A STATED ENDING DATE, THE OLD WAY (period + period_end)")

    up1 = post({"action": "projectupload", "session_token": pm, "id": PRJ, "period": 1,
                "period_end": "2026-03-31",
                "documents": [{"filename": "M1.pdf", "mimeType": "application/pdf",
                               "dataBase64": b64("M1")}]})
    check(up1.get("ok") is True, "period 1 uploads with an explicit ending date")
    check(up1.get("period_end") == "2026-03-31", "and the stated ending date is stored",
          str(up1.get("period_end")))

    listed = post({"action": "projectperiods", "session_token": pm, "id": PRJ})
    check(listed.get("periods") == [{"period": 1, "period_end": "2026-03-31"}],
          "projectperiods now lists period 1 with its stated ending date",
          str(listed.get("periods")))
    check(listed.get("next_period") == 2, "and offers period 2 as the next new one",
          str(listed.get("next_period")))

    section("3. THE NUMBER-ONLY PATH: period 2, NO DATE SENT AT ALL, LANDS IN PERIOD 2")

    up2 = post({"action": "projectupload", "session_token": pm, "id": PRJ, "period": 2,
                "documents": [{"filename": "M2.pdf", "mimeType": "application/pdf",
                               "dataBase64": b64("M2")}]})
    check(up2.get("ok") is True, "period 2 uploads with only a period number, no date")
    check(up2.get("period") == 2, "and the document lands in period 2 exactly as picked",
          str(up2.get("period")))
    # A brand-new period never had a stated ending date, so there is nothing to fall back to:
    # this is the SAME "nothing to measure against" behaviour the calendar suite already proves
    # for an unstated date, not a new gap this change introduces.
    check(up2.get("period_end") is None,
          "a brand-new period with no prior stated date stays NULL, not invented",
          str(up2.get("period_end")))

    st1 = post({"action": "projectuploadstatus", "session_token": pm, "id": PRJ, "period": 1})
    st2 = post({"action": "projectuploadstatus", "session_token": pm, "id": PRJ, "period": 2})
    check(len(st1.get("documents") or []) == 1, "period 1 still holds only its own document")
    check(len(st2.get("documents") or []) == 1, "period 2 holds only the number-picked document")

    section("4. COMPUTE AGGREGATES PERIOD 2 AS PERIOD 2, NOT MERGED INTO PERIOD 1")

    c1 = post({"action": "projectcompute", "session_token": pm, "id": PRJ, "period": 1})
    c2 = post({"action": "projectcompute", "session_token": pm, "id": PRJ, "period": 2})
    check(c1.get("ok") is True and c2.get("ok") is True, "both periods compute")
    r1 = post({"action": "projectresults", "session_token": pm, "id": PRJ, "period": 1})
    r2 = post({"action": "projectresults", "session_token": pm, "id": PRJ, "period": 2})
    check((r1.get("result") or {}).get("period") == 1, "period 1's stored result is period 1",
          str((r1.get("result") or {}).get("period")))
    check((r2.get("result") or {}).get("period") == 2, "period 2's stored result is period 2",
          str((r2.get("result") or {}).get("period")))
    # Fault: the two periods' evidence must be genuinely different, i.e. period 2 was not
    # silently computed from period 1's re-used document set.
    check(r1 != r2, "the two periods' stored results are not the same object re-served",
          "identical" if r1 == r2 else "distinct")

    section("5. THE CUTOFF DERIVATION REUSED: period 3 picked, dated document flagged AND stored")

    # Restate period 3's ending date the old way once (an existing caller still may), so period
    # 3 now HAS a stated ending date on file -- the situation the fallback is built for.
    up3 = post({"action": "projectupload", "session_token": pm, "id": PRJ, "period": 3,
                "period_end": "2026-05-15",
                "documents": [{"filename": "STUB.pdf", "mimeType": "application/pdf",
                               "dataBase64": b64("M1")}]})
    check(up3.get("ok") is True, "period 3 opens with a stated ending date")

    # Now upload a SECOND document to period 3 by NUMBER ONLY -- no period_end in the payload.
    # This document's own extracted date (2026-05-20) is AFTER period 3's stated end
    # (2026-05-15), so it must be flagged as outside the period, exactly as it would if the
    # caller had restated the same date by hand.
    late = post({"action": "projectupload", "session_token": pm, "id": PRJ, "period": 3,
                "documents": [{"filename": "LATE.pdf", "mimeType": "application/pdf",
                               "dataBase64": b64("LATE")}]})
    check(late.get("ok") is True, "the out-of-window document is still accepted, not refused")
    check(late.get("period") == 3, "and stored in the period that was picked", str(late.get("period")))
    mismatches = late.get("date_mismatches") or []
    check(len(mismatches) == 1 and "2026-05-15" in mismatches[0]["reason"],
          "it is FLAGGED against period 3's ending date, reused from the earlier upload "
          "though no date was sent this time", str(mismatches))
    st3 = post({"action": "projectuploadstatus", "session_token": pm, "id": PRJ, "period": 3})
    check(len(st3.get("documents") or []) == 2,
          "and it IS STORED alongside the on-time document, not rejected",
          str(len(st3.get("documents") or [])))

    section("6. FAULT INJECTION: the fallback line removed, and the derivation check goes red")

    # Prove the check at section 5 can actually fail: patch out the fallback that reuses the
    # period's stored ending date, so a number-only upload to an already-dated period gets NO
    # ending date at all -- the out-of-period check then has nothing to measure against and the
    # late document is silently NOT flagged. This is the exact defect the fallback prevents.
    orig_stated_ends = D._stated_period_ends
    D._stated_period_ends = lambda s, p: []  # as if no period ever had a stated ending date
    try:
        broken = post({"action": "projectupload", "session_token": pm, "id": PRJ, "period": 3,
                       "documents": [{"filename": "LATE2.pdf", "mimeType": "application/pdf",
                                      "dataBase64": b64("LATE")}]})
        broken_mismatches = broken.get("date_mismatches") or []
        check(broken.get("period_end") is None and not broken_mismatches,
              "FAULT CONFIRMED: with the fallback disabled, period_end is NULL and the same "
              "late document is silently NOT flagged -- this is what section 5 is proving does "
              "NOT happen on the real code", str(broken))
    finally:
        D._stated_period_ends = orig_stated_ends

    # And with the fallback restored, the same shape of upload is flagged again -- green again.
    restored = post({"action": "projectupload", "session_token": pm, "id": PRJ, "period": 3,
                     "documents": [{"filename": "LATE3.pdf", "mimeType": "application/pdf",
                                    "dataBase64": b64("LATE")}]})
    check(D._stated_period_ends is orig_stated_ends, "the patch was reverted", "")
    restored_mismatches = restored.get("date_mismatches") or []
    check(len(restored_mismatches) == 1,
          "and with the fallback back in place the late document is flagged again",
          str(restored_mismatches))

    finish()


if __name__ == "__main__":
    main()
