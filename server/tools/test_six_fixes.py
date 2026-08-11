#!/usr/bin/env python3
"""
The two substantive fixes: the period reaches the upload surface people use, and the
recommendation states the rule that set it.

WHY THE PERIOD FIX NEEDED A THIRD ROUND. The selector was added to the Workspace "Period
documents" panel and the Files tab, and the project detail page's own upload path was reported
as unchanged. That path is the one a project manager actually uses: the detail page's "Upload
documents" button opens `LinIngest.openUploadModal`, which mounts `LinSignals.dropzoneHtml` and
posts `extractsignals` with no period. So a second reporting period's documents kept landing in
period one, and the detail page's own control then reported "1 period(s) recomputed: period 1
(27 document(s) added)". The server was never the problem: `a_extractsignals` forwards its whole
payload to the upload path, so the period travels the moment the client sends it.

WHY THE RECOMMENDATION NEEDED A RULE. The card scored three courses, recommended the one scoring
8 over the one scoring 5, and said the reason "is not established here". The rule is in the
regret module and it is a threshold on the period's own cost and schedule performance. These
checks drive the REAL module across each threshold and assert the basis this platform states is
the branch that actually fires, so a change to the module's rule turns them red rather than
leaving `recommendation_basis.py` quietly wrong.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_six_fixes.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.recommendation_basis import (  # noqa: E402
    ESCALATE_BELOW, INVESTIGATE_BELOW, recommendation_basis,
)
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import ComputedResult, DocumentUpload, Participant  # noqa: E402
from app.simulation.models_gov import run_regret_minimization  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = 0
FAILED = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload),
                    headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


_COMPARED = ("period", "signal_inputs", "module_results", "category_statuses", "project_status",
             "portfolio_snapshot", "simulation_version", "seed", "period_cutoff",
             "source_documents")


def payload_bytes(legacy: str, period: int) -> bytes:
    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == legacy))
        row = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == pid, ComputedResult.period == period,
            ComputedResult.superseded_by.is_(None)))
        assert row is not None
        return json.dumps({k: (str(getattr(row, k)) if k == "period_cutoff"
                               else getattr(row, k)) for k in _COMPARED},
                          sort_keys=True, default=str).encode()


def result_id(legacy: str, period: int) -> str:
    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == legacy))
        return s.scalar(select(ComputedResult.result_id).where(
            ComputedResult.project_id == pid, ComputedResult.period == period,
            ComputedResult.superseded_by.is_(None)))


ADMIN = "sf-admin"
PRJ = "PRJ-SF-DETAIL"

P1 = ("2026-03-15", 3_000_000, 3_300_000, 3_200_000, 25.0, 27.0)
P2 = ("2026-04-15", 4_000_000, 4_400_000, 4_300_000, 33.0, 36.0)


def fields(d, ev, ac, pv, apc, ppc):
    return {"earned_value": ev, "actual_cost": ac, "planned_value": pv,
            "budget_at_completion": 12_000_000, "actual_percent_complete": apc,
            "planned_percent_complete": ppc, "report_date": d, "document_date": d}


def doc(tag: str) -> bytes:
    return f"%PDF-1.4 SIX FIXES {tag}\n".encode()


REC = {hashlib.sha256(doc("A1")).hexdigest(): ("monthly_report", fields(*P1))}
for i in range(4):
    REC[hashlib.sha256(doc(f"B{i}")).hexdigest()] = ("monthly_report", fields(*P2))
set_extractor_override(StubExtractor(REC))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="SF-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PRJ)) is None:
        s.add(Project(legacy_id=PRJ,
                      doc={"id": PRJ, "name": PRJ, "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "SF-PM", "role": "Participant",
                "account_type": "operational"})
pm = post({"action": "researchlogin",
           "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PRJ,
      "participant_id": created["participant_id"], "project_role": "PM"})

try:
    print("=" * 78)
    print("1. The detail page's upload path carries the stated period")
    print("=" * 78)

    # Period one, filed through the same action the detail dropzone posts.
    r1 = post({"action": "extractsignals", "session_token": pm, "id": PRJ,
               "docType": "auto", "dataBase64": b64(doc("A1")),
               "mimeType": "application/pdf", "fileName": "A1.pdf",
               "period": 1, "period_end": "2026-03-31"})
    check(r1.get("ok") is True and r1.get("period") == 1,
          "extractsignals files a document to the period stated", str(r1.get("period")))
    post({"action": "projectcompute", "session_token": pm, "id": PRJ, "period": 1})
    before_p1 = payload_bytes(PRJ, 1)
    id_p1 = result_id(PRJ, 1)

    # A SECOND reporting period's documents, through that same path. This is the case that
    # was landing in period one.
    for i in range(4):
        rb = post({"action": "extractsignals", "session_token": pm, "id": PRJ,
                   "docType": "auto", "dataBase64": b64(doc(f"B{i}")),
                   "mimeType": "application/pdf", "fileName": f"B{i}.pdf",
                   "period": 2, "period_end": "2026-04-30"})
        check(rb.get("period") == 2,
              f"a second period's document {i} is filed to period 2", str(rb.get("period")))

    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == PRJ))
        counts = dict(s.execute(
            select(DocumentUpload.period, func.count())
            .where(DocumentUpload.project_id == pid)
            .group_by(DocumentUpload.period)).all())
    check(counts == {1: 1, 2: 4},
          "the store holds two periods, not one", str(counts))

    # A caller that states nothing still defaults, which is the remaining inference point and
    # is asserted so it stays visible rather than becoming a surprise.
    rq = post({"action": "extractsignals", "session_token": pm, "id": PRJ,
               "docType": "auto", "dataBase64": b64(doc("A1")),
               "mimeType": "application/pdf", "fileName": "A1.pdf"})
    check(rq.get("period") == 1,
          "a caller stating no period still defaults to 1, unchanged and reported")

    print()
    print("=" * 78)
    print("2. Two periods compute as two, and period one is untouched")
    print("=" * 78)

    allr = post({"action": "projectcomputeall", "session_token": pm, "id": PRJ})
    check(allr.get("periods") == [1, 2],
          "the control finds two periods", str(allr.get("periods")))
    by = {r["period"]: r for r in (allr.get("results") or [])}
    check(by[1].get("skipped") is True,
          "period one is skipped: its own evidence did not change", str(by.get(1)))
    check(by[2].get("computed") is True,
          "period two computes for the first time", str(by.get(2)))
    check(payload_bytes(PRJ, 1) == before_p1,
          "PERIOD ONE IS BYTE-IDENTICAL after the second period computed")
    check(result_id(PRJ, 1) == id_p1,
          "and it kept its result_id: left alone, not rewritten identically")

    r2 = post({"action": "projectresults", "session_token": pm, "id": PRJ,
               "period": 2})["result"]
    check(len(r2.get("source_documents") or []) == 4,
          "period two computed from its own four documents",
          str(len(r2.get("source_documents") or [])))

    print()
    print("=" * 78)
    print("3, 4 and 5. THE RULE THIS SECTION USED TO PIN NO LONGER HAS A MODULE.")
    print("=" * 78)

    # WHAT THIS SECTION PROTECTED, AND WHAT IT PROTECTS NOW.
    #
    # The six-fixes run corrected the courses-of-action card to state WHY the recommended
    # course was recommended, and pinned the served sentence against the scoring module's own
    # threshold rule so a mirrored constant could not drift. That was the right property while
    # the module produced a ranking.
    #
    # Run 7 established that it never produced one. The three expected regrets were literals,
    # so the minimum was the same course on every project in every period, the healthy course
    # was unreachable from any input, and the ranking the card explained was a property of the
    # file rather than a finding about a project. The module abstains now, and no payoff matrix
    # exists to replace it with.
    #
    # So the property is restated rather than deleted: there is no ranking, on any input, and
    # nothing downstream invents one. The threshold constants stay imported and are driven over
    # the same grid this section always drove, to prove that no branch of the old rule fires
    # anywhere, rather than to prove a constant matches.

    grid = ((0.5, 0.5), (0.84, 0.88), (0.84, 0.99), (0.99, 0.84),
            (ESCALATE_BELOW, 0.99), (0.92, 0.99), (INVESTIGATE_BELOW, INVESTIGATE_BELOW),
            (1.05, 1.05), (1.20, 1.20), (2.0, 2.0))
    abstained_all = True
    ranked_any = False
    basis_any = False
    for cpi, spi in grid:
        mod = run_regret_minimization({"cpi": cpi, "spi": spi, "bac": 1e7}, lambda: 0.5, None)
        abstained_all = abstained_all and mod.get("status_color") is None \
            and mod.get("insufficient_data") is True
        ranked_any = ranked_any or ("expected_regret" in mod) or ("recommended_action" in mod)
        basis_any = basis_any or recommendation_basis({"cpi": cpi, "spi": spi}, mod) is not None
    check(abstained_all,
          "the scoring analysis abstains on every pair of indices, including the pairs that "
          "used to trip each branch of the threshold rule")
    check(not ranked_any,
          "and it emits no ranking and no recommended course anywhere on that grid")
    check(not basis_any,
          "so the served basis has nothing to state, on every one of them")
    check(str(ESCALATE_BELOW) and str(INVESTIGATE_BELOW),
          "the threshold constants are still imported here, and now describe no live module")

    served = post({"action": "projectresults", "session_token": pm, "id": PRJ,
                   "period": 2})["result"]
    check(served.get("recommendation_basis") is None,
          "the API serves no basis beside a result whose scoring analysis abstained",
          str(served.get("recommendation_basis"))[:140])
    _mods = {m.get("method_class"): m for m in (served.get("module_results") or [])
             if isinstance(m, dict)}
    check("Regret_Minimization" not in _mods,
          "and the abstaining module is absent from the stored module rows, as every "
          "abstention is", str(sorted(_mods))[:140])
    _abst = {a.get("module_id"): a for a in (served.get("abstained") or [])}
    check("B4.7" in _abst and _abst["B4.7"].get("reason"),
          "while the abstention row carries a reason the ledger can speak",
          str(_abst.get("B4.7"))[:160])
    check(_abst.get("B4.7", {}).get("abstention_reason_code")
          == "canonical_decision_structure_absent",
          "and the stable code names the structure that is missing, beside the sentence and "
          "never inside it", str(_abst.get("B4.7", {}).get("abstention_reason_code")))

    # The helper itself still refuses to invent, which was always its own property.
    check(recommendation_basis(None, None) is None,
          "no module, no basis: nothing is invented")
    check(recommendation_basis({"cpi": 0.8}, {"method_class": "Regret_Minimization"}) is None,
          "a module with no scores yields no basis either")
    nb = recommendation_basis({}, {"expected_regret": {"a": 1, "b": 2},
                                   "recommended_action": "a"})
    check(nb and nb["rule"] == "unknown",
          "without the figures the rule reads, the branch is reported as unestablished",
          str(nb and nb["rule"]))

except Exception as exc:  # noqa: BLE001
    FAILED += 1
    print(f"  ****  UNCAUGHT EXCEPTION: {type(exc).__name__}: {exc}")
    import traceback
    traceback.print_exc()

print()
print("=" * 78)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 78)
sys.exit(1 if FAILED else 0)
