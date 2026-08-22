#!/usr/bin/env python3
"""
RUN 45 §5.3. THE MODULE CENSUS, BEFORE AND AFTER THE RETRIEVAL CHANGE.

Retrieval changing means stored computed results can change. That is the point of the fix, and
it has to be VISIBLE rather than absorbed. This script computes every module's result, on every
period of every fixture corpus, through the REAL routes — upload, extract (stubbed to the
fixture's own recorded figures), `projectcomputeall`, `projectresults` — and writes one CSV row
per (corpus, project, period, module). Run it on this tree and on a worktree at the predecessor
commit, and diff the two CSVs: every differing row is a result the retrieval change moved.

It is NOT a copy of the retrieval logic. It drives the server and records what the server said.

THREE CORPORA, chosen so the census has both a control and a subject:

  * `dev_fixtures` — the repository's own document fixtures, `server/dev_fixtures/*.txt`, one
    document in one period per project. A single-period corpus CANNOT exhibit a carry-forward,
    so every row here must be IDENTICAL before and after. It is the control on the claim that
    period-field retrieval did not change.
  * `four_period` — Run 42's shape: one monthly report per period, four periods. A monthly
    report writes `bac` (tier 4) in every period, so the identity carry-forward has nothing to
    add; this is the second control, and it is the one that would catch a carry-forward that
    fires where it should not.
  * `carry_forward` — the Run 45 shape: a contract and a pay application at period 1, a change
    order alone at period 2, pay applications at periods 3 and 4. This is the subject. The
    contract and the original contingency are stated ONCE, at period 1.

Usage:
    DATABASE_URL=sqlite:///<throwaway> SESSION_SECRET=... python tools/build_run45_census.py \
        --out code_audit/run45_census_after.csv
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
ADMIN = "run45-census-admin"
PERIOD_END = {1: "2026-03-31", 2: "2026-04-30", 3: "2026-05-31", 4: "2026-06-30"}


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


# --------------------------------------------------------------- corpora

def dev_fixture_docs() -> list[tuple[str, int, str, str, dict]]:
    """(project, period, tag, doc_type, extraction) from server/dev_fixtures/*.txt."""
    root = pathlib.Path(__file__).resolve().parents[1] / "dev_fixtures"
    out = []
    for path in sorted(root.glob("monthly_report_*.txt")):
        figures = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()
            try:
                figures[key] = float(value) if "." in value else int(value)
            except ValueError:
                figures[key] = value
        ex = {"earned_value": figures.get("earned_value"),
              "actual_cost": figures.get("actual_cost"),
              "planned_value": figures.get("planned_value"),
              "budget_at_completion": figures.get("budget_at_completion"),
              "report_date": PERIOD_END[1], "document_date": PERIOD_END[1]}
        name = path.stem.replace("monthly_report_", "")
        out.append((f"PRJ-C45-DEV-{name.upper()[:6]}", 1, path.stem, "monthly_report", ex))
    return out


def four_period_docs() -> list[tuple[str, int, str, str, dict]]:
    out = []
    for p in (1, 2, 3, 4):
        out.append(("PRJ-C45-FOUR", p, f"mr{p}", "monthly_report",
                    {"earned_value": 1_000_000 + 100_000 * p,
                     "actual_cost": 1_050_000 + 100_000 * p,
                     "planned_value": 1_010_000 + 100_000 * p,
                     "budget_at_completion": 10_000_000,
                     "actual_percent_complete": 40.0 + p,
                     "planned_percent_complete": 41.0 + p,
                     "report_date": PERIOD_END[p], "document_date": PERIOD_END[p]}))
    return out


def carry_forward_docs() -> list[tuple[str, int, str, str, dict]]:
    proj = "PRJ-C45-CARRY"
    payapp = {1: (1_800_000, 2_000_000, 34.0, 250_000),
              3: (2_500_000, 2_600_000, 44.0, 150_000),
              4: (2_900_000, 3_000_000, 51.0, 100_000)}
    out = [(proj, 1, "contract", "contract_value",
            {"original_contract_sum": 5_874_620, "project_start_date": "2026-01-01",
             "project_end_date": "2027-06-30"})]
    for p, (ac, ev, pct, remaining) in payapp.items():
        ex = {"amount_paid_to_date": ac, "completed_to_date": ev,
              "percent_complete_verified": pct, "original_contract_sum": 4_463_290,
              "remaining_contingency": remaining,
              "application_date": PERIOD_END[p], "document_date": PERIOD_END[p]}
        if p == 1:
            ex["original_contingency"] = 300_000
        out.append((proj, p, f"payapp{p}", "pay_application", ex))
    out.append((proj, 2, "co", "change_order",
                {"revised_contract_sum": 6_100_000, "baseline_contract_sum": 6_100_000,
                 "revised_completion_date": "2027-09-30",
                 "change_order_date": PERIOD_END[2], "document_date": PERIOD_END[2]}))
    return out


CORPORA = {"dev_fixtures": dev_fixture_docs,
           "four_period": four_period_docs,
           "carry_forward": carry_forward_docs}


def main_(out_path: str) -> None:
    docs: list[tuple[str, str, int, str, str, dict]] = []
    for corpus, builder in CORPORA.items():
        for project, period, tag, doc_type, ex in builder():
            docs.append((corpus, project, period, tag, doc_type, ex))

    recorded = {}
    for corpus, project, period, tag, doc_type, ex in docs:
        recorded[hashlib.sha256(f"%PDF-1.4 R45C {project} {tag}\n".encode()).hexdigest()] = (
            doc_type, ex)
    set_extractor_override(StubExtractor(recorded))

    projects = sorted({(c, p) for c, p, *_ in docs})
    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="R45-CENSUS", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        for _corpus, legacy in projects:
            if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
                s.add(Project(legacy_id=legacy,
                              doc={"id": legacy, "name": legacy, "signals": {}, "events": []}))
        s.commit()

    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": "R45-CENSUS-PM", "role": "Participant",
                    "account_type": "operational"})
    pm = post({"action": "researchlogin",
               "access_token": created["access_token"]})["session_token"]
    for _corpus, legacy in projects:
        post({"action": "adminmemberadd", "session_token": admin, "id": legacy,
              "participant_id": created["participant_id"], "project_role": "PM"})

    for corpus, project, period, tag, doc_type, ex in docs:
        r = post({"action": "projectupload", "session_token": pm, "id": project,
                  "period": period, "period_end": PERIOD_END[period],
                  "documents": [{"filename": f"{tag}.pdf", "mimeType": "application/pdf",
                                 "dataBase64": b64(
                                     f"%PDF-1.4 R45C {project} {tag}\n".encode())}]})
        assert r.get("ok") is True, str(r)[:300]

    rows = []
    for corpus, legacy in projects:
        r = post({"action": "projectcomputeall", "session_token": pm, "id": legacy})
        assert r.get("ok") is True, str(r)[:300]
        periods = sorted({p for c, pr, p, *_ in docs if pr == legacy})
        for period in periods:
            res = post({"action": "projectresults", "session_token": pm, "id": legacy,
                        "period": period})
            assert res.get("ok") is True, str(res)[:300]
            result = res["result"]
            si = {k: v for k, v in (result.get("signal_inputs") or {}).items()
                  if k not in ("sources", "events")}
            for key in sorted(si):
                rows.append({"corpus": corpus, "project": legacy, "period": period,
                             "row_kind": "signal_input", "id": key,
                             "status": "", "value": json.dumps(si[key], sort_keys=True)})
            for m in result.get("module_results") or []:
                rows.append({"corpus": corpus, "project": legacy, "period": period,
                             "row_kind": "module", "id": m.get("module_id"),
                             "status": m.get("status") or "",
                             "value": json.dumps(
                                 {k: v for k, v in sorted(m.items())
                                  if k not in ("module_id", "parameter_provenance")},
                                 sort_keys=True, default=str)})
            for m in result.get("abstained") or []:
                rows.append({"corpus": corpus, "project": legacy, "period": period,
                             "row_kind": "abstained", "id": m.get("module_id"),
                             "status": "ABSTAINED",
                             "value": json.dumps(
                                 {k: v for k, v in sorted(m.items())
                                  if k not in ("module_id", "parameter_provenance")},
                                 sort_keys=True, default=str)})

    rows.sort(key=lambda r: (r["corpus"], r["project"], r["period"], r["row_kind"], r["id"]))
    path = pathlib.Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["corpus", "project", "period", "row_kind", "id",
                                           "status", "value"])
        w.writeheader()
        w.writerows(rows)
    print(f"CENSUS: {len(rows)} rows over {len(projects)} projects -> {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main_(ap.parse_args().out)
