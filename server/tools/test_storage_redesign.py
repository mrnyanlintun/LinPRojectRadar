#!/usr/bin/env python3
"""
Storage redesign (0014): observations, selection, and the four defects.

Run (from server/):

    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_storage_redesign.py

Covers, end to end through /exec plus the pure layer:

  1. A register revised within one period yields the revised figure, not the sum.
  2. A register across two periods yields two observations, and the later is current.
  3. The original contract baseline survives an executed change order — both readable.
  4. P1: two projects computed for the same period see the same portfolio regardless of when
     each was computed; recomputing an earlier period after another project advanced is
     byte-identical.
  5. The observation store: rows persisted, append-only, revisions retained.
  6. docDate has ONE answer: the latest as_of, the same rule as the cutoff.
  7. Individual rfi forms route to unmapped; the accumulating branch and the
     "rfi" < "rfi_log" ordering dependency are gone — checked, not assumed.

The WHOLE run is wrapped so a crash still prints a RESULT line with a failure, never a clean-
looking silence.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
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
    from app.extraction_client import StubExtractor
    from app.extraction_fields import DOC_TYPES, is_mapped, guess_type_from_filename
    from app.extraction_merge import assemble_signal_inputs, emit_observations, \
        select_signal_inputs
    from app.field_registry import FIELD_KINDS, PERMANENT
    from app.research_identity import hash_access_token
    from app.research_models import ComputedResult, Observation, Participant
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

    # ------------------------------------------------------------------ fixtures
    def blob(tag: str) -> bytes:
        return f"%PDF-1.4 STORAGE REDESIGN {tag}\n".encode()

    def sha(raw: bytes) -> str:
        return hashlib.sha256(raw).hexdigest()

    def monthly(ev, ac, rd):
        return ("monthly_report", {"earned_value": ev, "actual_cost": ac,
                                   "planned_value": 5_000_000,
                                   "budget_at_completion": 10_000_000, "report_date": rd})

    FILES = {
        # register replace within a period, then a new period
        "reg1": ("rfi_log", {"rfi_total": 10, "rfi_open": 4, "log_date": "2026-06-15"}),
        "reg2": ("rfi_log", {"rfi_total": 12, "rfi_open": 5, "log_date": "2026-06-20"}),
        "reg3": ("rfi_log", {"rfi_total": 15, "rfi_open": 6, "log_date": "2026-07-15"}),
        # baseline + executed change order
        "cv":  ("contract_value", {"original_contract_sum": 10_000_000,
                                   "project_start_date": "2026-01-01",
                                   "project_end_date": "2026-12-31"}),
        "co":  ("change_order", {"revised_contract_sum": 11_000_000,
                                 "revised_completion_date": "2027-03-31",
                                 "change_order_date": "2026-06-10"}),
        # portfolio projects
        "pa1": monthly(4_000_000, 4_000_000, "2026-06-30"),
        "pb1": monthly(3_000_000, 4_000_000, "2026-06-30"),
        "pb2": monthly(6_000_000, 4_000_000, "2026-07-31"),
        "pc1": monthly(5_000_000, 4_000_000, "2026-06-30"),
        # an individual RFI form
        "ind": ("rfi", {"rfi_count": 3, "document_risk_score": 0.4,
                        "document_date": "2026-06-01"}),
    }
    RECORDED = {sha(blob(k)): v for k, v in FILES.items()}
    set_extractor_override(StubExtractor(RECORDED))

    ADMIN = "storage-admin-token"
    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="STORAGE-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        for pid in ("PRJ-STOR-REG", "PRJ-STOR-CO", "PRJ-STOR-A", "PRJ-STOR-B", "PRJ-STOR-C"):
            if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
                s.add(Project(legacy_id=pid, doc={"id": pid, "name": pid, "signals": {}}))
        s.commit()

    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": "STORAGE-PM", "role": "Participant",
                    "account_type": "operational"})
    pm = post({"action": "researchlogin",
               "access_token": created["access_token"]})["session_token"]
    for pid in ("PRJ-STOR-REG", "PRJ-STOR-CO", "PRJ-STOR-A", "PRJ-STOR-B", "PRJ-STOR-C"):
        post({"action": "adminmemberadd", "session_token": admin, "id": pid,
              "participant_id": created["participant_id"], "project_role": "PM"})

    def upload(pid: str, period: int, *tags: str) -> dict:
        return post({"action": "projectupload", "session_token": pm, "id": pid,
                     "period": period,
                     "documents": [{"filename": f"{t}.pdf", "mimeType": "application/pdf",
                                    "dataBase64": b64(blob(t))} for t in tags]})

    def compute(pid: str, period: int) -> dict:
        return post({"action": "projectcompute", "session_token": pm, "id": pid,
                     "period": period})

    def recompute(pid: str, period: int, reason: str) -> dict:
        return post({"action": "adminrecompute", "session_token": admin, "id": pid,
                     "period": period, "reason": reason})

    def result(pid: str, period: int, result_id: str | None = None) -> dict:
        p = {"action": "projectresults", "session_token": pm, "id": pid, "period": period}
        if result_id:
            p["result_id"] = result_id
        return post(p)["result"]

    def project_uuid(s, pid: str):
        return s.scalar(select(Project).where(Project.legacy_id == pid)).id

    # ================================================================== 1. register replace
    print("\n1. A register revised within one period yields the revised figure, not the sum")
    upload("PRJ-STOR-REG", 1, "reg1", "reg2")
    c = compute("PRJ-STOR-REG", 1)
    check(c.get("ok") is True, "period 1 computed", str(c)[:120])
    r1 = result("PRJ-STOR-REG", 1)
    check(r1["signal_inputs"]["rfiCount"] == 12,
          "the revised register's total is the observation — 12, not 22 and not 10",
          str(r1["signal_inputs"]["rfiCount"]))
    check(r1["signal_inputs"]["rfiOpen"] == 5,
          "every field of the register follows the revision", str(r1["signal_inputs"]["rfiOpen"]))

    # ================================================================== 2. two periods
    print("\n2. A register across two periods yields two observations; the later is current")
    upload("PRJ-STOR-REG", 2, "reg3")
    c = compute("PRJ-STOR-REG", 2)
    check(c.get("ok") is True, "period 2 computed", str(c)[:120])
    r2 = result("PRJ-STOR-REG", 2)
    check(r2["signal_inputs"]["rfiCount"] == 15,
          "period 2's observation is the current value", str(r2["signal_inputs"]["rfiCount"]))
    r1_again = result("PRJ-STOR-REG", 1)
    check(r1_again["signal_inputs"]["rfiCount"] == 12,
          "period 1's observation is untouched — a new period is a new point, not a replacement",
          str(r1_again["signal_inputs"]["rfiCount"]))
    with Session() as s:
        rows = s.scalars(select(Observation).where(
            Observation.project_id == project_uuid(s, "PRJ-STOR-REG"),
            Observation.field == "rfiCount")).all()
        periods = sorted(r.period for r in rows)
        check(periods == [1, 1, 2],
              "the store holds every revision and every period — append-only, nothing deleted",
              str(periods))

    # docDate: one rule, one answer
    check(r1["signal_inputs"]["docDate"] == "2026-06-20",
          "docDate is the latest as_of in the period's evidence",
          str(r1["signal_inputs"]["docDate"]))
    check(r1["period_cutoff"] == "2026-06-20",
          "and the cutoff is the SAME date — one rule, not two", str(r1["period_cutoff"]))

    # ================================================================== 3. baseline
    print("\n3. The original baseline survives an executed change order — both readable")
    upload("PRJ-STOR-CO", 1, "cv", "co")
    c = compute("PRJ-STOR-CO", 1)
    check(c.get("ok") is True, "computed with contract and executed CO", str(c)[:120])
    rco = result("PRJ-STOR-CO", 1)["signal_inputs"]
    check(rco["bac"] == 11_000_000,
          "bac is the amended contract value (the executed CO applies)", str(rco["bac"]))
    check(rco["baselineContractSum"] == 10_000_000,
          "the ORIGINAL baseline persists in signalInputs", str(rco["baselineContractSum"]))
    check(rco["baselineEnd"] == "2027-03-31",
          "the effective end date is the amendment's", str(rco["baselineEnd"]))
    status = post({"action": "projectuploadstatus", "session_token": pm,
                   "id": "PRJ-STOR-CO", "period": 1})
    orig = (status.get("baseline") or {}).get("original") or {}
    amends = (status.get("baseline") or {}).get("amendments") or []
    check(orig.get("contractSum") == 10_000_000 and orig.get("end") == "2026-12-31",
          "the original baseline (sum AND end date) is readable from the store", str(orig))
    check(len(amends) == 1 and amends[0].get("revisedContractSum") == 11_000_000
          and amends[0].get("revisedEnd") == "2027-03-31"
          and amends[0].get("state") == "executed",
          "the executed change order is readable as an amendment layered on it", str(amends))
    with Session() as s:
        perm = s.scalars(select(Observation).where(
            Observation.project_id == project_uuid(s, "PRJ-STOR-CO"),
            Observation.field == "baselineContractSum",
            Observation.source_doc_type == "contract_value")).all()
        check(len(perm) == 1 and perm[0].kind == PERMANENT and perm[0].value == 10_000_000,
              "the original is a PERMANENT observation — nothing later replaces it",
              str([(p.kind, p.value) for p in perm]))

    # ================================================================== 4. P1
    print("\n4. P1: portfolio vectors are cutoff-aligned, never max(period)")
    upload("PRJ-STOR-A", 1, "pa1")
    compute("PRJ-STOR-A", 1)
    upload("PRJ-STOR-B", 1, "pb1")
    compute("PRJ-STOR-B", 1)
    upload("PRJ-STOR-C", 1, "pc1")
    compute("PRJ-STOR-C", 1)
    # Period-1 views of the portfolio once every project holds a period-1 result:
    ra = recompute("PRJ-STOR-A", 1, "P1 check: baseline snapshot with all at period 1")
    a_before = result("PRJ-STOR-A", 1, ra["result_id"])["portfolio_snapshot"]
    rb0 = recompute("PRJ-STOR-B", 1, "P1 check: baseline snapshot with all at period 1")
    b_before = result("PRJ-STOR-B", 1, rb0["result_id"])["portfolio_snapshot"]
    # B advances to period 2 with very different figures and a later cutoff.
    upload("PRJ-STOR-B", 2, "pb2")
    compute("PRJ-STOR-B", 2)
    ra2 = recompute("PRJ-STOR-A", 1, "P1 check: recompute after another project advanced")
    a_after = result("PRJ-STOR-A", 1, ra2["result_id"])["portfolio_snapshot"]
    check(json.dumps(a_before, sort_keys=True) == json.dumps(a_after, sort_keys=True),
          "recomputing A's period 1 after B reached period 2 is byte-identical — "
          "the period-2 result is excluded by its later cutoff", "")
    rb1 = recompute("PRJ-STOR-B", 1, "P1 check: same period, recomputed at a later moment")
    b_after = result("PRJ-STOR-B", 1, rb1["result_id"])["portfolio_snapshot"]
    check(json.dumps(b_before, sort_keys=True) == json.dumps(b_after, sort_keys=True),
          "B's OWN period 1, recomputed after its period 2 exists, is byte-identical too —"
          " a project's later periods cannot contaminate its earlier ones", "")
    # Both computed for period 1 must have seen the SAME portfolio population, whatever the
    # wall-clock order of computation. RUN 33: at v21 the population is the GOVERNED COHORT, not
    # "the rows this query returned", and neither of these projects supplies one -- so what the
    # two saw is the same cohort identity (none) and the same cutoff. The property under test is
    # unchanged: two projects computed for one period must not see different portfolios.
    check(isinstance(a_after, dict) and isinstance(b_after, dict)
          and a_after.get("cohort") == b_after.get("cohort")
          and a_after.get("portfolio_size") == b_after.get("portfolio_size")
          and a_after.get("structure_absent") == b_after.get("structure_absent")
          and a_after.get("period_cutoff") == b_after.get("period_cutoff"),
          "two projects computed for the same period see the same portfolio: same governed "
          "cohort identity, same size, same cutoff, regardless of when each was computed",
          f"A size={a_after.get('portfolio_size')} B size={b_after.get('portfolio_size')} "
          f"cutoffs {a_after.get('period_cutoff')}/{b_after.get('period_cutoff')} "
          f"cohorts {a_after.get('cohort')}/{b_after.get('cohort')}")

    # ================================================================== 5. store integrity
    print("\n5. The observation store is append-only and idempotent")
    with Session() as s:
        before = s.scalars(select(Observation)).all()
        n_before = len(before)
    # Re-uploading the same file is a no-op for the store too.
    upload("PRJ-STOR-REG", 1, "reg2")
    with Session() as s:
        n_after = len(s.scalars(select(Observation)).all())
    check(n_after == n_before,
          "re-deriving the same document inserts nothing — same rows, by construction",
          f"{n_before} -> {n_after}")

    # ================================================================== 6. registers only
    print("\n6. Individual forms route to unmapped; the ordering dependency is gone")
    up = upload("PRJ-STOR-REG", 1, "ind")
    f = up["files"][0]
    check(f.get("doc_type") == "rfi" and f.get("contributes") is False,
          "an individual RFI is stored but contributes nothing — never asked for totals",
          str({k: f.get(k) for k in ('doc_type', 'contributes')}))
    check("rfi" not in DOC_TYPES and not is_mapped("rfi"),
          "the individual rfi form is no longer offered or mapped", "")
    check(guess_type_from_filename("rfi-0042.pdf") is None,
          "a bare rfi filename resolves to unmapped, not to a register it cannot be", "")
    check(emit_observations({"sha256": "x", "doc_type": "rfi", "filename": "r.pdf",
                             "extraction": {"rfi_count": 3}}) == [],
          "an rfi-typed document emits no observations", "")
    # The "rfi" < "rfi_log" dependency is gone BY CONSTRUCTION, verified not assumed:
    # rfiCount has exactly one emitting doc type, so no ordering between two writers exists.
    import app.extraction_merge as em
    writers = {dt for dt, pairs in em._NUMERIC_EMISSIONS.items()
               for _src, field in pairs if field == "rfiCount"}
    check(writers == {"rfi_log"},
          "rfiCount has exactly one writer; nothing depends on sort order between writers",
          str(sorted(writers)))
    src = open(os.path.join(os.path.dirname(__file__), "..", "app",
                            "extraction_merge.py"), encoding="utf-8").read()
    check(".add(" not in src.replace("RESULTS.append", "").replace("out.append", "")
          .replace("seen.add", "").replace("existing.add", ""),
          "no additive accumulator survives in the merge source", "")

    # ================================================================== 7. pure selection
    print("\n7. Selection semantics at the pure layer")
    def docd(shav, dt, ex):
        return {"sha256": shav, "doc_type": dt, "filename": shav + ".pdf", "extraction": ex}

    # recency by as_of, not hash: lower hash carries the later date and wins
    si = assemble_signal_inputs([
        docd("aaa", "rfi_log", {"rfi_total": 12, "log_date": "2026-06-20"}),
        docd("fff", "rfi_log", {"rfi_total": 10, "log_date": "2026-06-15"}),
    ])
    check(si["rfiCount"] == 12, "recency by the value's own date, never by content hash",
          str(si["rfiCount"]))
    # the cutoff bounds every selection
    from datetime import date as _date
    si_cut = assemble_signal_inputs([
        docd("aaa", "rfi_log", {"rfi_total": 12, "log_date": "2026-06-20"}),
        docd("fff", "rfi_log", {"rfi_total": 10, "log_date": "2026-06-15"}),
    ], cutoff=_date(2026, 6, 16))
    check(si_cut["rfiCount"] == 10,
          "an observation dated after the cutoff is not selected", str(si_cut["rfiCount"]))
    # an EVENT revision supersedes the record, not the population
    obs = (emit_observations(docd("c1", "change_order",
                                  {"revised_contract_sum": 10_500_000,
                                   "change_order_date": "2026-03-01"}))
           + emit_observations(docd("c2", "change_order",
                                    {"revised_contract_sum": 10_800_000,
                                     "change_order_date": "2026-05-01"})))
    two = select_signal_inputs(obs)
    check(two["changeOrderCount"] == 2, "two distinct change orders are two events",
          str(two["changeOrderCount"]))
    rev = [dict(o) for o in obs]
    for o in rev:
        if o["sha256"] == "c2" and o["field"] == "changeOrderCount":
            o["entity_key"] = "c1-entity"
    for o in rev:
        if o["sha256"] == "c1" and o["field"] == "changeOrderCount":
            o["entity_key"] = "c1-entity"
    one = select_signal_inputs(rev)
    check(one["changeOrderCount"] == 1,
          "a revision of the same entity supersedes that record — one event, not two",
          str(one["changeOrderCount"]))
    # every emittable field has a declared kind; the registry owns the rule
    check(all(o["field"] in FIELD_KINDS for o in obs),
          "every emitted field carries a registry-declared kind", "")

    # unemittable legacy keys stay present and None (the computations expect the keys)
    check(si["rfiNumber"] is None and si["rfiResponseTimeDays"] is None
          and "rfiNumber" in si and "rfiResponseTimeDays" in si,
          "legacy keys nothing can emit remain in the dict as None — abstention, not KeyError",
          "")


try:
    main()
except Exception as e:  # a crash must read as a FAILURE, never as a clean run
    import traceback
    traceback.print_exc()
    check(False, f"suite crashed: {type(e).__name__}: {e}")
finish()
