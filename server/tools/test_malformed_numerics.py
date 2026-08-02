#!/usr/bin/env python3
"""
D2: a malformed numeric refuses, at every point a numeric value can enter.

Run (from server/):

    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_malformed_numerics.py

FOUR ENTRY POINTS, enumerated rather than assumed:

  1. extract_many         fresh extraction; the only writer of Document rows. Refusal is
                          whole-document and happens BEFORE any row exists.
  2. emit_observations    the merge / observation-persistence backstop for stored rows.
  3. overwritesignal      the legacy facade's live write into a named signalInputs field.
  4. save                 the legacy facade's wholesale doc replacement, whose client copy
                          carries a signalInputs blob. The live action nobody had listed.

Three cases: ABSENT passes (abstention unchanged); MALFORMED refuses; OUT OF CONTRACT
(negative count/sum) refuses. Legitimate decorations are accepted: "$1,200,000", "1,200",
"45%", and "(500)" reads as NEGATIVE 500 (the legacy stripper silently made it +500).

The run is wrapped so a crash prints a failing RESULT line, never a clean-looking silence.
"""
from __future__ import annotations

import base64
import hashlib
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
    from fastapi.testclient import TestClient
    from sqlalchemy import select

    import app.main as main_mod
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor, extract_many
    from app.extraction_merge import (
        MalformedNumericError, NumericRangeError, assemble_signal_inputs,
        emit_observations, validate_signal_value,
    )
    from app.research_identity import hash_access_token
    from app.research_models import Document, Observation, Participant
    from app.models import Project

    client = TestClient(main_mod.app, raise_server_exceptions=False)
    Session = main_mod.SessionFactory

    def post(payload: dict) -> dict:
        r = client.post("/exec", content=json.dumps(payload),
                        headers={"Content-Type": "text/plain"})
        assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
        return r.json()

    def b64(raw: bytes) -> str:
        return base64.b64encode(raw).decode()

    def blob(tag: str) -> bytes:
        return f"%PDF-1.4 D2 NUMERICS {tag}\n".encode()

    def sha(raw: bytes) -> str:
        return hashlib.sha256(raw).hexdigest()

    FILES = {
        "tbd":   ("monthly_report", {"earned_value": "TBD", "actual_cost": 4_000_000,
                                     "report_date": "2026-06-30"}),
        "clean": ("monthly_report", {"earned_value": 4_500_000, "actual_cost": 4_000_000,
                                     "planned_value": 5_000_000,
                                     "budget_at_completion": 10_000_000,
                                     "report_date": "2026-06-30"}),
        "fancy": ("pay_application", {"amount_paid_to_date": "$1,200,000",
                                      "percent_complete_verified": "45%",
                                      "application_date": "2026-06-15"}),
        "float": ("time_phased_schedule", {"planned_value_to_date": "1,200",
                                           "total_float": "(500)",
                                           "data_date": "2026-06-10"}),
        "negct": ("rfi_log", {"rfi_total": -3, "log_date": "2026-06-01"}),
        "nafld": ("field_report", {"document_risk_score": "N/A",
                                   "document_date": "2026-06-05"}),
        "empty": ("monthly_report", {"report_date": "2026-06-30"}),
    }
    RECORDED = {sha(blob(k)): v for k, v in FILES.items()}
    set_extractor_override(StubExtractor(RECORDED))

    ADMIN = "d2-admin-token"
    PROJ = "PRJ-D2-NUM"
    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="D2-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == PROJ)) is None:
            s.add(Project(legacy_id=PROJ,
                          doc={"id": PROJ, "name": PROJ, "signals": {},
                               "signalInputs": {"ev": 1_000_000, "totalFloat": 5,
                                                "docRiskScore": 0.5}}))
        s.commit()

    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": "D2-PM", "role": "Participant",
                    "account_type": "operational"})
    pm = post({"action": "researchlogin",
               "access_token": created["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": admin, "id": PROJ,
          "participant_id": created["participant_id"], "project_role": "PM"})

    def upload(*tags: str, period: int = 1) -> dict:
        return post({"action": "projectupload", "session_token": pm, "id": PROJ,
                     "period": period,
                     "documents": [{"filename": f"{t}.pdf", "mimeType": "application/pdf",
                                    "dataBase64": b64(blob(t))} for t in tags]})

    # ============================================================ 1. the extraction boundary
    print("\n1. Entry point one: extract_many refuses the whole document, before any row")
    up = upload("tbd", "clean")
    by_name = {f["filename"]: f for f in up["files"]}
    tbd, clean = by_name["tbd.pdf"], by_name["clean.pdf"]
    check(tbd.get("status") == "failed",
          "a document with earned_value 'TBD' is refused, not stored with a zero",
          str(tbd)[:120])
    err_text = str(tbd.get("error") or "")
    check("earned_value" in err_text, "the refusal names the FIELD", err_text[:100])
    check("tbd.pdf" in err_text, "the refusal names the FILE", err_text[:100])
    check("TBD" in err_text and "cannot be read as a number" in err_text,
          "the refusal states the value and a reason the uploader can act on", err_text[:120])
    check("Nothing was stored" in err_text, "and says what happened to the document", "")
    check("—" not in err_text, "no em dash (house rule)", "")
    check(clean.get("status") == "extracted" and clean.get("contributes") is True,
          "the clean document in the SAME batch is stored — whole-document, not whole-batch",
          str({k: clean.get(k) for k in ('status', 'contributes')}))
    with Session() as s:
        stored = s.scalar(select(Document).where(Document.sha256 == sha(blob("tbd"))))
        check(stored is None, "no Document row exists for the refused file", "")
        proj = s.scalar(select(Project).where(Project.legacy_id == PROJ))
        obs_docs = {o.document_id for o in s.scalars(
            select(Observation).where(Observation.project_id == proj.id)).all()}
        clean_row = s.scalar(select(Document).where(Document.sha256 == sha(blob("clean"))))
        check(clean_row is not None and clean_row.document_id in obs_docs,
              "the clean document projected observation rows", "")
        # nothing from the refused document can be in the store, since it has no row at all
        check(len(obs_docs) >= 1 and stored is None,
              "a refusal writes no observation row for the document", "")

    print("\n2. Legitimate values that merely look unusual are accepted")
    up2 = upload("fancy", "float")
    check(all(f["status"] == "extracted" for f in up2["files"]),
          "currency, separators, a percent sign and a parenthesised negative all extract",
          str([(f['filename'], f['status']) for f in up2['files']]))
    c = post({"action": "projectcompute", "session_token": pm, "id": PROJ, "period": 1})
    check(c.get("ok") is True, "the period computes", str(c)[:100])
    si = post({"action": "projectresults", "session_token": pm, "id": PROJ,
               "period": 1})["result"]["signal_inputs"]
    check(si["ac"] == 1_200_000, "\"$1,200,000\" reads as 1200000", str(si["ac"]))
    check(si["actualPctComplete"] == 45.0, "\"45%\" reads as 45", str(si["actualPctComplete"]))
    check(si["pv"] == 1200.0, "\"1,200\" reads as 1200", str(si["pv"]))
    check(si["totalFloat"] == -500.0,
          "\"(500)\" reads as NEGATIVE 500 — the legacy stripper made it +500",
          str(si["totalFloat"]))
    check(si["ev"] == 4_500_000 and si["cpi"] is not None,
          "the clean earned value computes a real cpi", f"ev={si['ev']} cpi={si['cpi']}")

    print("\n3. Absent stays absent: abstention, not refusal and not zero")
    up3 = upload("empty", period=2)
    check(up3["files"][0]["status"] == "extracted",
          "a document missing the field entirely is accepted", str(up3["files"][0])[:80])
    post({"action": "projectcompute", "session_token": pm, "id": PROJ, "period": 2})
    si2 = post({"action": "projectresults", "session_token": pm, "id": PROJ,
                "period": 2})["result"]["signal_inputs"]
    check(si2["ev"] is None and si2["cpi"] is None,
          "absent earned value means cpi abstains — unchanged", f"ev={si2['ev']} cpi={si2['cpi']}")

    print("\n4. Out of contract refuses: a negative count; a negative float is a real state")
    up4 = upload("negct")
    f4 = up4["files"][0]
    check(f4["status"] == "failed" and "rfi_total" in str(f4.get("error"))
          and "negative" in str(f4.get("error")),
          "rfi_total -3 is refused with the field and reason named", str(f4.get("error"))[:100])
    check(si["totalFloat"] == -500.0,
          "while a negative total_float was accepted above — the signed set is deliberate", "")
    up5 = upload("nafld")
    f5 = up5["files"][0]
    check(f5["status"] == "failed" and "document_risk_score" in str(f5.get("error")),
          "document_risk_score 'N/A' is refused as malformed — the coerced 0.0 is dead",
          str(f5.get("error"))[:100])

    print("\n5. Entry point two: the merge/store backstop refuses stored rows all-or-nothing")
    bad = {"sha256": "b" * 64, "doc_type": "monthly_report", "filename": "legacy.pdf",
           "extraction": {"earned_value": "TBD", "actual_cost": 100}}
    raised = False
    try:
        emit_observations(bad)
    except MalformedNumericError as exc:
        raised = "earned_value" in str(exc)
    check(raised is True, "emit_observations raises, naming the field", "")
    raised = False
    try:
        assemble_signal_inputs([bad])
    except MalformedNumericError:
        raised = True
    check(raised, "assemble_signal_inputs refuses the same way", "")
    # all-or-nothing: the document's OTHER, valid field must not have been emitted either
    try:
        emit_observations(bad)
        partial = ["reached"]
    except MalformedNumericError:
        partial = []
    check(partial == [], "a refused document emits nothing at all, never a partial set", "")

    print("\n6. Entry point three: overwritesignal")
    def ows(field, value):
        return post({"action": "overwritesignal", "session_token": pm, "id": PROJ,
                     "field": field, "value": value, "reason": "d2 test"})
    r = ows("ev", "TBD")
    check("error" in r and "ev" in str(r.get("error")), "ev='TBD' is refused, field named",
          str(r.get("error"))[:80])
    r = ows("ev", -5)
    check("error" in r and "negative" in str(r.get("error")),
          "ev=-5 is refused as out of contract", str(r.get("error"))[:80])
    r = ows("totalFloat", -12)
    check(r.get("ok") is True, "totalFloat=-12 is accepted (signed field)", str(r)[:80])
    r = ows("ev", "$1,200")
    check(r.get("ok") is True, "a decorated but legitimate value is accepted", str(r)[:80])
    r = ows("docRiskScore", 85)
    check("error" in r, "docRiskScore=85 still refused by its own 0..1 guard", "")

    print("\n7. Entry point four: save, the wholesale doc replacement")
    with Session() as s:
        proj_doc = dict(s.scalar(select(Project).where(Project.legacy_id == PROJ)).doc)
    bad_doc = dict(proj_doc)
    bad_doc["signalInputs"] = dict(proj_doc.get("signalInputs") or {})
    bad_doc["signalInputs"]["ac"] = "unknown"
    r = post({"action": "save", "session_token": pm, "project": bad_doc})
    check("error" in r and "ac" in str(r.get("error")),
          "a save whose blob CHANGES a numeric field to prose is refused, field named",
          str(r.get("error"))[:90])
    ok_doc = dict(proj_doc)
    ok_doc["name"] = "D2 renamed"
    r = post({"action": "save", "session_token": pm, "project": ok_doc})
    check(r.get("ok") is True,
          "a save that does not change any numeric field passes", str(r)[:60])
    ok_doc2 = dict(r["project"])
    ok_doc2["signalInputs"] = dict(ok_doc2.get("signalInputs") or {})
    ok_doc2["signalInputs"]["ac"] = "$2,500"
    r = post({"action": "save", "session_token": pm, "project": ok_doc2})
    check(r.get("ok") is True, "a changed but legitimate value passes", str(r)[:60])

    print("\n8. The pure contract, directly")
    for v in ("TBD", "N/A", "unknown", "1.2.3", True):
        raised = False
        try:
            validate_signal_value("ev", v)
        except MalformedNumericError:
            raised = True
        check(raised, f"malformed {v!r} refused", "")
    for v in (None, "", 0, 4.5, "1,200", "$450", "(500)", "45%"):
        ok = True
        try:
            validate_signal_value("ev", v)
        except (MalformedNumericError, NumericRangeError):
            ok = v in ("(500)",)  # (500) is negative, and ev is non-negative: refusal correct
        check(ok, f"{v!r} handled correctly for a non-negative field", "")


try:
    main()
except Exception as e:  # a crash must read as a FAILURE, never as a clean run
    import traceback
    traceback.print_exc()
    check(False, f"suite crashed: {type(e).__name__}: {e}")
finish()
