#!/usr/bin/env python3
"""
RUN 42. THE PERIOD-BINDING AND EVIDENCE-LINEAGE MECHANISM, DRIVEN THROUGH THE REAL ROUTES.

WHAT THIS SUITE EXISTS TO PROTECT. The owner's rule is that the reporting period a person
SELECTS at upload is authoritative, and that nothing else -- upload order, document date,
filename, database insertion order, extraction completion order -- may decide which period a
document's figures land in. Around that rule Run 42 proved and repaired two identity losses.
Both were losses in the PATH, not absences in the data, and this suite fails if either returns.

  1. THE PER-FIELD SOURCE RECORD DROPPED THE DOCUMENT IDENTITY. Every observation
     `extraction_merge.emit_observations` builds has always carried document_id, sha256,
     revision_of and as_of, and the stored result has always listed the same identity per
     document in `source_documents`. The per-field `sources` entry recorded only docType and
     value. `qualification._provenance` counts a field as traced only when it carries BOTH a
     document identity and a document version, so it counted ZERO on every project ever
     computed and the provenance dimension could never leave PARTIAL; `_timeliness` counted
     as-of dates and was pinned the same way.

  2. THE QUALIFICATION RECORD NAMED A NULL PROJECT. `compute.py` read the project identity from
     `si.get("projectId")`, a key the signal-inputs dict does not have and never had, and the
     read path hard-coded None -- while both callers held the project the whole time.

NOTHING HERE ASSERTS THAT A CATEGORY LIGHTS UP. The fixture supplies one monthly report per
period, so most modules legitimately abstain for want of their governed structure, and this
suite deliberately pins the ABSTENTIONS as well as the computations. A later run that makes a
category compute by relaxing a gate rather than by supplying evidence breaks this file.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_run42_period_binding_mechanism.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import DocumentUpload, Participant  # noqa: E402

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
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


# --------------------------------------------------------------- fixture

ADMIN = "run42-admin-token"
#: Two projects uploaded in an INTERLEAVED, NON-CHRONOLOGICAL order, so neither database
#: insertion order nor upload order can coincide with reporting-period order by accident.
A = "PRJ-R42A"
B = "PRJ-R42B"
#: A third project uploaded strictly chronologically, to compare A against.
C = "PRJ-R42C"

PERIOD_END = {1: "2026-03-31", 2: "2026-04-30", 3: "2026-05-31", 4: "2026-06-30"}
#: A distinct earned value per (project, period) so a leak is identifiable by VALUE alone.
EV = {("A", 1): 1_100_000, ("A", 2): 1_200_000, ("A", 3): 1_300_000, ("A", 4): 1_400_000,
      ("B", 1): 2_100_000, ("B", 2): 2_200_000, ("B", 3): 2_300_000, ("B", 4): 2_400_000,
      ("C", 1): 1_100_000, ("C", 2): 1_200_000, ("C", 3): 1_300_000, ("C", 4): 1_400_000}


def fields(tag: str, period: int) -> dict:
    return {"earned_value": EV[(tag, period)],
            "actual_cost": EV[(tag, period)] + 50_000,
            "planned_value": EV[(tag, period)] + 10_000,
            "budget_at_completion": 10_000_000,
            "actual_percent_complete": 40.0 + period,
            "planned_percent_complete": 41.0 + period,
            "report_date": PERIOD_END[period],
            "document_date": PERIOD_END[period]}


def doc_bytes(tag: str, period: int) -> bytes:
    # A and C carry BYTE-IDENTICAL evidence per period, so any difference between them is a
    # difference the upload ORDER produced and nothing else.
    body = "AC" if tag in ("A", "C") else tag
    return f"%PDF-1.4 RUN42 {body} {period}\n".encode()


RECORDED = {}
for _tag in ("A", "B", "C"):
    for _p in (1, 2, 3, 4):
        RECORDED[hashlib.sha256(doc_bytes(_tag, _p)).hexdigest()] = (
            "monthly_report", fields(_tag, _p))
set_extractor_override(StubExtractor(RECORDED))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R42-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for legacy, name in ((A, "Run42 A"), (B, "Run42 B"), (C, "Run42 C")):
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy, doc={"id": legacy, "name": name, "signals": {},
                                                 "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R42-PM", "role": "Participant",
                "account_type": "operational"})
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
for legacy in (A, B, C):
    post({"action": "adminmemberadd", "session_token": admin, "id": legacy,
          "participant_id": created["participant_id"], "project_role": "PM"})


def upload(legacy: str, tag: str, period: int) -> dict:
    return post({"action": "projectupload", "session_token": pm, "id": legacy, "period": period,
                 "period_end": PERIOD_END[period],
                 "documents": [{"filename": f"{tag}{period}.pdf",
                                "mimeType": "application/pdf",
                                "dataBase64": b64(doc_bytes(tag, period))}]})


#: THE ORDER UNDER TEST. A and B interleaved and out of order; C chronological.
UPLOAD_ORDER = [(A, "A", 4), (B, "B", 3), (A, "A", 1), (B, "B", 1),
                (A, "A", 3), (B, "B", 4), (A, "A", 2), (B, "B", 2)]
_assigned = {}
for _legacy, _tag, _p in UPLOAD_ORDER:
    _assigned[(_tag, _p)] = upload(_legacy, _tag, _p)
for _p in (1, 2, 3, 4):
    upload(C, "C", _p)

for _legacy in (A, B, C):
    _r = post({"action": "projectcomputeall", "session_token": pm, "id": _legacy})
    assert _r.get("ok") is True, str(_r)[:300]


def result(legacy: str, period: int) -> dict:
    r = post({"action": "projectresults", "session_token": pm, "id": legacy, "period": period})
    assert r.get("ok") is True, str(r)[:300]
    return r["result"]


try:
    # ================================================================
    print("=" * 78)
    print("1. THE SELECTED PERIOD IS THE PERIOD THE UPLOAD WRITES TO")
    print("=" * 78)

    for (tag, p), resp in sorted(_assigned.items()):
        check(resp.get("ok") is True and resp.get("period") == p,
              f"{tag}{p}: the upload was bound to the period the caller selected",
              f"requested {p}, got {resp.get('period')}")

    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == A))
        rows = s.execute(select(DocumentUpload.period, DocumentUpload.period_end)
                         .where(DocumentUpload.project_id == pid)).all()
    stored = {int(p): str(e) for p, e in rows}
    check(stored == {p: PERIOD_END[p] for p in (1, 2, 3, 4)},
          "each period's stored ending date is the one selected, not the one uploaded first",
          str(stored))

    # NON-VACUITY: the upload order really was not the period order.
    check([p for _l, _t, p in UPLOAD_ORDER if _t == "A"] != [1, 2, 3, 4],
          "the fixture really did upload out of order, so this suite tested something",
          str([p for _l, _t, p in UPLOAD_ORDER if _t == "A"]))

    print()
    print("=" * 78)
    print("2. OUT-OF-ORDER UPLOAD PRODUCES THE SAME ANALYTICAL STATE AS CHRONOLOGICAL")
    print("=" * 78)

    # WHAT IS COMPARED, AND WHAT IS DELIBERATELY NOT. A and C are two DIFFERENT projects
    # carrying byte-identical evidence per period; A was uploaded interleaved and out of order,
    # C strictly chronologically. Three things legitimately differ between any two distinct
    # projects and are therefore excluded by name rather than by a wildcard: the result_id and
    # the document ids (per-row identifiers), the RNG SEED (derived from the project's own
    # identity, so the stochastic modules draw differently), and the portfolio snapshot (whose
    # cohort is the OTHER projects, which is a different set for each of them). Everything that
    # the reporting period's evidence determines must be identical, and that is what is asserted.
    #
    # The complementary proof -- the SAME project id in two separate databases, differing in
    # nothing but upload order, compared byte for byte -- is code_audit/run42_probe_order.py and
    # its two recorded states. It is not run here because it needs two migrated databases.
    QUAL_DIMENSIONS = ("required_inputs_status", "canonical_structure_status",
                       "period_applicability_status", "provenance_status", "timeliness_status",
                       "revision_resolution_status", "overall_qualification_state")

    for p in (1, 2, 3, 4):
        a, c = result(A, p), result(C, p)

        figures_a = {k: v for k, v in a["signal_inputs"].items() if k != "sources"}
        figures_c = {k: v for k, v in c["signal_inputs"].items() if k != "sources"}
        check(figures_a == figures_c,
              f"period {p}: the reported figures are identical",
              f"{figures_a} vs {figures_c}")
        check(a["category_statuses"] == c["category_statuses"],
              f"period {p}: the category statuses are identical",
              f"{a['category_statuses']} vs {c['category_statuses']}")
        check(a["project_status"] == c["project_status"],
              f"period {p}: the project status is identical",
              f"{a['project_status']} vs {c['project_status']}")
        check(sorted(x["module_id"] for x in (a["abstained"] or []))
              == sorted(x["module_id"] for x in (c["abstained"] or [])),
              f"period {p}: exactly the same modules abstain")
        bands_a = {m["module_id"]: m.get("status") for m in a["module_results"]}
        bands_c = {m["module_id"]: m.get("status") for m in c["module_results"]}
        check(bands_a == bands_c,
              f"period {p}: every module reaches the same band",
              str([k for k in bands_a if bands_a[k] != bands_c.get(k)]))
        qa, qc = a["evidence_qualification"], c["evidence_qualification"]
        check(all(qa.get(d) == qc.get(d) for d in QUAL_DIMENSIONS),
              f"period {p}: every qualification dimension is identical",
              str([d for d in QUAL_DIMENSIONS if qa.get(d) != qc.get(d)]))
        check(sorted(qa.get("missing_canonical_structures") or [])
              == sorted(qc.get("missing_canonical_structures") or []),
              f"period {p}: the same governed structures are reported absent")

    # NON-VACUITY. These comparisons are worthless if the two sides are empty or if the fixture
    # accidentally uploaded C out of order too.
    _r3 = result(A, 3)
    _considered = len(_r3["module_results"]) + len(_r3.get("abstained") or [])
    check(len(_r3["module_results"]) >= 1 and _considered > 50,
          "the comparison covered a real module population, computed and abstained alike",
          f"computed={len(_r3['module_results'])} abstained="
          f"{len(_r3.get('abstained') or [])} considered={_considered}")
    check([p for _l, _t, p in UPLOAD_ORDER if _t == "A"] != [1, 2, 3, 4],
          "project A really was uploaded out of chronological order")

    print()
    print("=" * 78)
    print("3. NO CROSS-PERIOD OR CROSS-PROJECT RETRIEVAL")
    print("=" * 78)

    for tag, legacy in (("A", A), ("B", B)):
        for p in (1, 2, 3, 4):
            r = result(legacy, p)
            check(r["signal_inputs"].get("ev") == EV[(tag, p)],
                  f"{tag}{p}: the period's earned value is its OWN",
                  f"{r['signal_inputs'].get('ev')} vs {EV[(tag, p)]}")
            names = sorted(d["filename"] for d in (r["source_documents"] or []))
            check(names == [f"{tag}{p}.pdf"],
                  f"{tag}{p}: the result names exactly its own period's document", str(names))
            blob = json.dumps(r, default=str)
            foreign = [f"{ot}{op}" for (ot, op), v in EV.items()
                       if (ot, op) != (tag, p) and ot != "C"
                       and v != EV[(tag, p)]
                       and (f'"ev": {v}' in blob or f'"ev": {v}.0' in blob)]
            check(not foreign,
                  f"{tag}{p}: no other period's or project's earned value appears in its state",
                  str(foreign))

    print()
    print("=" * 78)
    print("4. THE QUALIFICATION RECORD NAMES ITS PROJECT AND ITS PERIOD")
    print("=" * 78)

    for tag, legacy in (("A", A), ("B", B)):
        for p in (1, 2, 3, 4):
            q = result(legacy, p)["evidence_qualification"]
            check(q.get("project_id") == legacy,
                  f"{tag}{p}: the qualification record names its project",
                  str(q.get("project_id")))
            check(q.get("reporting_period") == f"P{p}",
                  f"{tag}{p}: the qualification record names its reporting period",
                  str(q.get("reporting_period")))

    print()
    print("=" * 78)
    print("5. DOCUMENT-TO-FACT-TO-MODULE LINEAGE: EVERY SOURCED FIELD NAMES ITS ARTEFACT")
    print("=" * 78)

    for p in (1, 2, 3, 4):
        r = result(A, p)
        sources = r["signal_inputs"].get("sources") or {}
        check(bool(sources), f"period {p}: the result carries a per-field source record",
              str(len(sources)))
        known = {(d["document_id"], d["sha256"]) for d in (r["source_documents"] or [])}
        missing = [k for k, e in sources.items()
                   if not (e.get("documentId") and e.get("documentVersion"))]
        check(not missing,
              f"period {p}: every sourced field names a document identity AND version",
              str(missing))
        foreign = [k for k, e in sources.items()
                   if (e.get("documentId"), e.get("documentVersion")) not in known]
        check(not foreign,
              f"period {p}: every field's named artefact is one of THIS period's documents",
              str(foreign))
        undated = [k for k, e in sources.items() if not e.get("asOf")]
        check(not undated, f"period {p}: every sourced field carries an as-of date", str(undated))

        q = r["evidence_qualification"]
        pe = q.get("provenance_evidence") or {}
        check(pe.get("fields_with_document_identity_and_version") == pe.get(
                  "fields_with_source_type") == len(sources),
              f"period {p}: the qualification layer counts every field as traced", str(pe))
        check(q.get("provenance_status") == "PASS",
              f"period {p}: the provenance dimension reaches PASS", str(q.get("provenance_status")))
        check(q.get("timeliness_status") == "PASS",
              f"period {p}: the timeliness dimension reaches PASS", str(q.get("timeliness_status")))

    print()
    print("=" * 78)
    print("6. THE DELIBERATE ABSTENTIONS ARE STILL ABSTENTIONS")
    print("=" * 78)

    # Run 42 repaired a path. It did NOT relax a gate, and these are the pins that say so.
    for p in (1, 2, 3, 4):
        q = result(A, p)["evidence_qualification"]
        check(q.get("revision_resolution_status") == "NOT_ESTIMABLE",
              f"period {p}: revision resolution is STILL NOT_ESTIMABLE",
              str(q.get("revision_resolution_status")))
        check(q.get("overall_qualification_state") == "NOT_ESTIMABLE",
              f"period {p}: the weakest-of overall state is STILL NOT_ESTIMABLE",
              str(q.get("overall_qualification_state")))
        check(q.get("canonical_structure_status") == "PARTIAL",
              f"period {p}: absent governed structures are STILL reported absent",
              str(q.get("canonical_structure_status")))
        check(bool(q.get("missing_canonical_structures")),
              f"period {p}: the missing structures are named rather than glossed over",
              str(len(q.get("missing_canonical_structures") or [])))

    r3 = result(A, 3)
    check(bool(r3.get("abstained")),
          "modules whose governed structure is absent still abstain",
          str(len(r3.get("abstained") or [])))
    lit = sorted(r3.get("category_statuses") or {})
    check(lit == ["A1"],
          "only the category the evidence actually supports carries a status", str(lit))
    check(r3.get("project_status") in ("Green", "Amber", "Red"),
          "the project status is a real band derived from what did compute",
          str(r3.get("project_status")))

    print()
    print("=" * 78)
    print("7. THE COMPUTE PATH'S OWN QUALIFICATION RECORD NAMES ITS PROJECT")
    print("=" * 78)

    # WHY THIS SECTION EXISTS AT THE FUNCTION BOUNDARY AND NOT THROUGH A ROUTE. The compute
    # path attaches `evidence_qualification` to the run it returns, and that object is NOT
    # persisted: `documents._result_view` re-derives the record at read time from the stored
    # row. So reverting the compute path's identity while the read path keeps its own leaves
    # every route-level assertion above green -- which is exactly what happened when this
    # suite's fault injection was run, and why asserting only through the routes would have
    # been a check that never reached the boundary it names. `compute_project` is therefore
    # called directly here.
    from app.simulation.compute import compute_project  # noqa: E402
    from datetime import date as _date  # noqa: E402

    _si = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
           "cpi": 0.909, "spi": 0.889, "actualPctComplete": 40.0,
           "plannedPctComplete": 45.0}
    _run = compute_project(_si, "PRJ-DIRECT", "P2", _date(2026, 6, 30),
                           project_id="PRJ-DIRECT")
    _q = _run.get("evidence_qualification") or {}
    check(_q.get("project_id") == "PRJ-DIRECT",
          "the compute path records the project it was given", str(_q.get("project_id")))
    check(_q.get("reporting_period") == "P2",
          "the compute path records the reporting period it was given",
          str(_q.get("reporting_period")))

    # And the identity carried IN the signal inputs still wins, because a caller that really
    # holds it there is more specific than the project the run was launched for.
    _run2 = compute_project({**_si, "projectId": "PRJ-FROM-SI"}, "PRJ-DIRECT", "P2",
                            _date(2026, 6, 30), project_id="PRJ-DIRECT")
    check((_run2.get("evidence_qualification") or {}).get("project_id") == "PRJ-FROM-SI",
          "an identity carried in the signal inputs takes precedence",
          str((_run2.get("evidence_qualification") or {}).get("project_id")))

    # NON-VACUITY: omitting the identity entirely must still produce None, so the check above
    # is reading a value that was genuinely threaded through rather than a constant.
    _run3 = compute_project(_si, "PRJ-DIRECT", "P2", _date(2026, 6, 30))
    check((_run3.get("evidence_qualification") or {}).get("project_id") is None,
          "with no identity supplied the record honestly says none",
          str((_run3.get("evidence_qualification") or {}).get("project_id")))

except AssertionError as exc:                                    # noqa: BLE001
    # A crash is NOT a pass. Record it as a failure so the runner cannot read a green line.
    FAILED += 1
    print(f"  ****  the suite raised before finishing: {exc}")

print()
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
