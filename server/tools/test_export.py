#!/usr/bin/env python3
"""
B6 verification: de-identified export and archive chain.

Seeds a full two-period run for two participants in different conditions, exports it, and proves:

  1. No forbidden field appears in any export payload.
  2. The allowlist is explicit: a column added to a model does NOT appear in the export.
  3. The checksum recomputed on fetch matches; a tampered payload fails loudly.
  4. Derived variables match hand-computed values.
  5. A Participant cannot call any export action. Refused and audited.
  6. An empty range produces a valid empty export with row_count 0, not an error.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_export.py
"""

from __future__ import annotations

import csv
import io
import json
import pathlib
import sys
import time

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select, text  # noqa: E402

import app.main as main  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_export import EXPORT_COLUMNS, FORBIDDEN_FIELDS  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import (  # noqa: E402
    Assignment, AuditEvent, Decision, Participant,
)

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((ok, label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


# ---------------------------------------------------------------- seed a real run

ADMIN = "b6-bootstrap-admin"
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PM-000", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for legacy in ("ST-OPEN", "ST-RECOVERY", "ST-DRIFT"):
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy, doc={"id": legacy, "name": legacy}))
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

print("=" * 78)
print("SEED: two participants, different conditions, two periods each")
print("=" * 78)

scenario = post({"action": "adminscenariocreate", "session_token": admin,
                 "scenario_version": "b6-v1", "period_count": 2,
                 "evidence_package_id": "ST-OPEN"})["scenario_id"]
for code in ("C0", "C1"):
    post({"action": "adminconfigurationcreate", "session_token": admin, "code": code,
          "version": "v1", "freeze": True})
post({"action": "adminsequencecreate", "session_token": admin, "order_group": "GA",
      "scenario_set": "SET-B6", "version": "v1", "positions": ["C0"], "freeze": True})
post({"action": "adminsequencecreate", "session_token": admin, "order_group": "GB",
      "scenario_set": "SET-B6", "version": "v1", "positions": ["C1"], "freeze": True})
pkg = post({"action": "adminpackagecreate", "session_token": admin, "version": "b6-pkg",
            "provider_id": "frozen-store", "recommended_action": "Escalate", "freeze": True})
post({"action": "adminactionfamilycreate", "session_token": admin, "version": "fam-v1",
      "mappings": {"escalate": "escalate", "monitor": "accept"}, "freeze": True})
for family, branch, state in (("escalate", "B-REC", "ST-RECOVERY"), ("accept", "B-DRI", "ST-DRIFT")):
    post({"action": "admintransitionrulecreate", "session_token": admin,
          "scenario_id": scenario, "period": "P1", "action_family": family,
          "version": "rules-v1", "freeze": True,
          "branches": [{"branch_id": branch, "branch_version": "bv1", "probability": "1.0",
                        "next_state_id": state}]})


def run(group, final_1, pre_conf, final_conf, rationale):
    c = post({"action": "adminparticipantcreate", "session_token": admin})
    tok = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    post({"action": "consentgrant", "session_token": tok, "consent_version": "v1.0"})
    # T4: a_researchprejudgment now requires a completed intake questionnaire.
    post({"action": "intakesave", "session_token": tok,
          "responses": {"experience_level": "mid", "years_experience": 8}})
    post({"action": "adminassign", "session_token": admin, "participant_id": c["participant_id"],
          "order_group": group, "scenario_set": "SET-B6", "scenario_ids": [scenario]})
    with Session() as s:
        aid = s.scalar(select(Assignment).where(
            Assignment.participant_id == c["participant_id"])).assignment_id
    post({"action": "adminpackageattach", "session_token": admin, "assignment_id": aid,
          "package_id": pkg["package_id"]})
    # period 1
    post({"action": "researchevidenceget", "session_token": tok})
    time.sleep(0.05)
    post({"action": "researchprejudgment", "session_token": tok, "pre_action": "monitor",
          "pre_confidence": pre_conf})
    post({"action": "researchreveal", "session_token": tok})
    time.sleep(0.05)
    post({"action": "researchdecision", "session_token": tok, "final_action": final_1,
          "disposition": "modify", "final_confidence": final_conf, "rationale": rationale})
    post({"action": "researchadvance", "session_token": tok})
    # period 2
    post({"action": "researchevidenceget", "session_token": tok})
    post({"action": "researchprejudgment", "session_token": tok, "pre_action": "monitor",
          "pre_confidence": 40})
    post({"action": "researchreveal", "session_token": tok})
    post({"action": "researchdecision", "session_token": tok, "final_action": "monitor",
          "disposition": "accept", "final_confidence": 45, "rationale": "period two"})
    return c["participant_id"], tok


pa_id, pa_tok = run("GA", "escalate", 50, 80, "escalated after review")
pb_id, pb_tok = run("GB", "monitor", 60, 55, "held position")
check(True, "two participants completed two periods each")

print()
print("=" * 78)
print("EXPORT")
print("=" * 78)

exp = post({"action": "adminexportcreate", "session_token": admin, "format": "json"})
check(exp.get("ok") is True, "export created", str(exp)[:160])
check(exp.get("row_count") == 4, "one row per participant x period (4)", str(exp.get("row_count")))
check(len(exp.get("checksum") or "") == 64, "checksum is a sha256 digest")
check(exp.get("review_required") is True and "rationale" in exp.get("free_text_columns", []),
      "free text flagged as requiring review")

fetched = post({"action": "adminexportfetch", "session_token": admin,
                "export_id": exp["export_id"]})
check(fetched.get("ok") is True and fetched.get("checksum_verified") is True,
      "fetch re-verified the checksum", str(fetched)[:160])
check(fetched.get("checksum") == exp["checksum"], "recomputed checksum matches the stored one")

body = json.loads(fetched["payload"])
rows = body["rows"]
check(len(rows) == 4, "payload carries 4 rows")

print()
print("--- exported rows ---")
show = ("pseudonymous_code", "order_group", "config_code", "period", "pre_action", "final_action",
        "pre_confidence", "final_confidence", "judgment_shift_action", "confidence_shift",
        "branch_id")
print("  " + " | ".join(f"{c}" for c in show))
for r in sorted(rows, key=lambda x: (x["pseudonymous_code"], x["period"])):
    print("  " + " | ".join(str(r[c]) for c in show))

print()
print("=" * 78)
print("GUARANTEE 1: no forbidden field in any payload")
print("=" * 78)

for fmt in ("json", "csv"):
    e = post({"action": "adminexportcreate", "session_token": admin, "format": fmt})
    f = post({"action": "adminexportfetch", "session_token": admin, "export_id": e["export_id"]})
    blob = f["payload"]
    for forbidden in FORBIDDEN_FIELDS:
        check(forbidden not in blob, f"{fmt}: payload contains no {forbidden}")
    with Session() as s:
        p = s.get(Participant, pa_id)
        check(p.access_token_hash not in blob, f"{fmt}: no literal token hash value")
        check(pa_id not in blob, f"{fmt}: no raw participant_id value")
    check("PM-" in blob, f"{fmt}: pseudonymous_code IS present")

csv_e = post({"action": "adminexportcreate", "session_token": admin, "format": "csv"})
csv_f = post({"action": "adminexportfetch", "session_token": admin,
              "export_id": csv_e["export_id"]})
reader = list(csv.DictReader(io.StringIO(csv_f["payload"])))
check(len(reader) == 4, "csv has 4 data rows", str(len(reader)))
check(list(reader[0].keys()) == list(EXPORT_COLUMNS), "csv header equals the allowlist exactly")

print()
print("=" * 78)
print("GUARANTEE 2: the allowlist is explicit, not everything-except")
print("=" * 78)

# Add a column to the live table AND to the model, exactly as a future migration would.
with Session() as s:
    s.execute(text("ALTER TABLE decisions ADD COLUMN secret_side_channel TEXT"))
    s.commit()
    s.execute(text("UPDATE decisions SET secret_side_channel = 'LEAK-CANARY-123'"))
    s.commit()

from sqlalchemy import Text as SAText  # noqa: E402
from sqlalchemy.orm import mapped_column  # noqa: E402

if not hasattr(Decision, "secret_side_channel"):
    Decision.secret_side_channel = mapped_column(SAText, nullable=True)
    Decision.__mapper__.add_property("secret_side_channel", Decision.secret_side_channel)

with Session() as s:
    got = s.scalar(text("SELECT secret_side_channel FROM decisions LIMIT 1"))
check(got == "LEAK-CANARY-123", "dummy column exists and is populated in the database")

after = post({"action": "adminexportcreate", "session_token": admin, "format": "json"})
after_f = post({"action": "adminexportfetch", "session_token": admin,
                "export_id": after["export_id"]})
check("LEAK-CANARY-123" not in after_f["payload"],
      "the new column's VALUE does not appear in the export")
check("secret_side_channel" not in after_f["payload"],
      "the new column's NAME does not appear in the export")
check(json.loads(after_f["payload"])["columns"] == list(EXPORT_COLUMNS),
      "column set is unchanged by the new model column")

print()
print("=" * 78)
print("GUARANTEE 4: derived variables match hand computation")
print("=" * 78)

with Session() as s:
    pa = s.get(Participant, pa_id)
    code_a = pa.pseudonymous_code
row_a1 = [r for r in rows if r["pseudonymous_code"] == code_a and r["period"] == "P1"][0]

check(row_a1["pre_action"] == "monitor" and row_a1["final_action"] == "escalate",
      "participant A period 1 actions as submitted")
check(row_a1["judgment_shift_action"] is True,
      "judgment_shift_action True when final != pre", str(row_a1["judgment_shift_action"]))
check(row_a1["confidence_shift"] == 30, "confidence_shift = 80 - 50 = 30",
      str(row_a1["confidence_shift"]))
check(row_a1["config_code"] == "C0", "config_code present for the analyst (C0 for group GA)",
      str(row_a1["config_code"]))
check(row_a1["branch_id"] == "B-REC", "branch_id recorded for the escalate family",
      str(row_a1["branch_id"]))
check(row_a1["deliberation_seconds"] is not None and row_a1["deliberation_seconds"] >= 0,
      "deliberation_seconds computed and non-negative", str(row_a1["deliberation_seconds"]))
check(row_a1["pre_assessment_seconds"] is not None and row_a1["pre_assessment_seconds"] >= 0,
      "pre_assessment_seconds computed and non-negative",
      str(row_a1["pre_assessment_seconds"]))

with Session() as s:
    pb = s.get(Participant, pb_id)
    code_b = pb.pseudonymous_code
row_b1 = [r for r in rows if r["pseudonymous_code"] == code_b and r["period"] == "P1"][0]
check(row_b1["judgment_shift_action"] is False,
      "judgment_shift_action False when final == pre", str(row_b1["judgment_shift_action"]))
check(row_b1["confidence_shift"] == -5, "confidence_shift = 55 - 60 = -5",
      str(row_b1["confidence_shift"]))
check(row_b1["config_code"] == "C1", "second participant is in a different condition",
      str(row_b1["config_code"]))
check(row_b1["branch_id"] == "B-DRI", "different action family reached a different branch")
check(row_a1["rationale"] == "escalated after review", "rationale exported as a dependent variable")

print()
print("=" * 78)
print("GUARANTEE 3: tampering is detected loudly")
print("=" * 78)

# RUN 41. This guarantee is about the EXPORT CHECKSUM noticing that the underlying data moved,
# not about which column moved. It used to demonstrate that by rewriting `rationale` on a
# final-locked decision; migration 0026 now refuses exactly that, because rationale is part of
# the final participant judgment. The subject under test is unchanged - an exported column is
# altered behind the export's back - but it is done through `pre_assessment`, which is exported
# and is not covered by either lock guard.
with Session() as s:
    d = s.scalar(select(Decision).where(Decision.rationale == "escalated after review"))
    ORIGINAL_PRE_ASSESSMENT = d.pre_assessment
    s.execute(text("UPDATE decisions SET pre_assessment = 'TAMPERED' WHERE decision_id = :i"),
              {"i": d.decision_id})
    s.commit()

tampered = post({"action": "adminexportfetch", "session_token": admin,
                 "export_id": exp["export_id"]})
check(tampered.get("ok") is False and "checksum verification failed" in tampered.get("error", ""),
      "fetch fails loudly after the underlying data changed", str(tampered)[:200])
check("payload" not in tampered, "payload withheld on checksum mismatch")
with Session() as s:
    n = s.scalar(select(func.count()).select_from(AuditEvent)
                 .where(AuditEvent.event_type == "export_checksum_mismatch")) or 0
check(n >= 1, "the mismatch was audited")

with Session() as s:
    s.execute(text("UPDATE decisions SET pre_assessment = :orig "
                   "WHERE pre_assessment = 'TAMPERED'"), {"orig": ORIGINAL_PRE_ASSESSMENT})
    s.commit()
restored = post({"action": "adminexportfetch", "session_token": admin,
                 "export_id": exp["export_id"]})
check(restored.get("ok") is True, "verification passes again once the data is restored")

print()
print("=" * 78)
print("GUARANTEE 5: a Participant cannot export")
print("=" * 78)

with Session() as s:
    before = s.scalar(select(func.count()).select_from(AuditEvent)
                      .where(AuditEvent.event_type == "export_action_denied")) or 0
for act in ("adminexportcreate", "adminexportlist", "adminexportfetch"):
    r = post({"action": act, "session_token": pa_tok, "export_id": exp["export_id"],
              "role": "ResearchAdmin"})
    check(r.get("ok") is False and "not authorized" in r.get("error", ""),
          f"participant refused for {act}", str(r)[:120])
with Session() as s:
    after_n = s.scalar(select(func.count()).select_from(AuditEvent)
                       .where(AuditEvent.event_type == "export_action_denied")) or 0
check(after_n == before + 3, "all three refusals audited", f"{after_n - before}")

print()
print("=" * 78)
print("GUARANTEE 6: an empty range is a valid empty export")
print("=" * 78)

empty = post({"action": "adminexportcreate", "session_token": admin, "format": "json",
              "date_from": "1990-01-01T00:00:00Z", "date_to": "1990-01-02T00:00:00Z"})
check(empty.get("ok") is True, "empty range succeeded rather than erroring", str(empty)[:140])
check(empty.get("row_count") == 0, "row_count is 0", str(empty.get("row_count")))
check(len(empty.get("checksum") or "") == 64, "empty export still has a checksum")

empty_f = post({"action": "adminexportfetch", "session_token": admin,
                "export_id": empty["export_id"]})
check(empty_f.get("ok") is True and json.loads(empty_f["payload"])["rows"] == [],
      "empty payload fetches and verifies")
check(json.loads(empty_f["payload"])["columns"] == list(EXPORT_COLUMNS),
      "empty export still declares the full column set")

bad = post({"action": "adminexportcreate", "session_token": admin, "date_from": "not-a-date"})
check(bad.get("ok") is False and "ISO 8601" in bad.get("error", ""),
      "a malformed date is refused clearly", str(bad)[:120])

listing = post({"action": "adminexportlist", "session_token": admin})
check(listing.get("ok") is True and len(listing["exports"]) >= 5, "export list returns prior runs")
check(all(len(e["checksum"]) == 64 for e in listing["exports"]),
      "every listed export carries its checksum")

print()
print("=" * 78)
print("GUARANTEE 8: the export carries the approved notice, and says when it cannot")
print("=" * 78)
# An export leaves the platform and is read by people who never saw a footer. It used to carry no
# notice, no attribution and no copyright at all.
import app.research_export as rx  # noqa: E402


def payload_of(resp: dict) -> str:
    """
    The payload, or empty, never a KeyError.

    A refused fetch has no `payload` key. Indexing it directly is how this file dies with a
    KeyError instead of failing a check, and a crashed suite prints no RESULT line and reads
    exactly like a clean run. Fault injection produced precisely that.
    """
    return resp.get("payload") or ""


j_e = post({"action": "adminexportcreate", "session_token": admin, "format": "json"})
j_f = post({"action": "adminexportfetch", "session_token": admin, "export_id": j_e["export_id"]})
j_body = json.loads(payload_of(j_f) or "{}")
check(j_body.get("notice") == list(rx.NOTICE_RESEARCH),
      "json payload carries the approved research notice verbatim",
      str(j_body.get("notice"))[:60])
check(j_body.get("attribution") == rx.ATTRIBUTION, "json payload carries the attribution")
check(j_body.get("copyright") == rx.COPYRIGHT, "json payload carries the copyright")
check(j_f.get("notice_in_payload") is True, "and the fetch says the notice is in the file")

# The CSV gap is asserted, not glossed. If someone later makes the CSV carry the notice, this
# check fails and is updated deliberately rather than the gap being rediscovered.
c_f = post({"action": "adminexportfetch", "session_token": admin, "export_id": csv_e["export_id"]})
check(rx.NOTICE_RESEARCH[0][:40] not in payload_of(c_f),
      "csv still carries no notice, which is the reported gap")
check(c_f.get("notice_in_payload") is False,
      "and the fetch says so rather than leaving it to be discovered")
check(list(csv.DictReader(io.StringIO(payload_of(c_f))))[0].keys().__iter__().__next__()
      == EXPORT_COLUMNS[0],
      "because nothing was prepended above the csv header row")

# THE NO-SWITCH DECISION RESTS ENTIRELY ON THIS FILTER. research_export.py carries only the
# research variant because an operational account's rows cannot reach an export. If that ever
# stops being true, the notice is wrong and this check is the alarm.
#
# MATCH THE STATEMENT, NOT THE PHRASE. Searching for `participant.account_type != "research"`
# alone passed for the wrong reason: research_export.py's own comment explaining the filter quotes
# that expression, so deleting the actual guard left the check green. Fault injection caught it.
src = pathlib.Path(rx.__file__).read_text(encoding="utf-8")
guard = 'if participant is None or participant.account_type != "research":'
check(guard in src,
      "build_rows still excludes every non-research account unconditionally", guard)
# And the guard must be reached on every row, not sitting in a branch that is skipped.
check(src.count(guard) == 1, "the guard appears exactly once", str(src.count(guard)))

# An export taken before the notice existed must still verify. Its stored checksum covers the
# pre-notice bytes; recomputing with the notice would otherwise report the data as changed, which
# would be a false accusation of tampering.
with Session() as s:
    legacy_body, _ = rx.serialise(rx.build_rows(s, None, None), "json", include_notice=False)
# Raw SQL: the ORM before_flush consent guard refuses a direct write to research_exports, and the
# point here is to age an existing row, not to exercise that guard.
def _set_checksum(export_id: str, value: str) -> None:
    with Session() as s:
        s.execute(text("UPDATE research_exports SET checksum = :c WHERE export_id = :e"),
                  {"c": value, "e": export_id})
        s.commit()


_set_checksum(j_e["export_id"], rx.checksum(legacy_body))
old_f = post({"action": "adminexportfetch", "session_token": admin, "export_id": j_e["export_id"]})
check(old_f.get("ok") is True, "an export taken before the notice still fetches",
      str(old_f)[:90])
check(old_f.get("predates_notice") is True, "and is reported as predating the notice")
check(json.loads(payload_of(old_f) or "{}").get("notice") == list(rx.NOTICE_RESEARCH),
      "and the file served now carries the notice")

_set_checksum(j_e["export_id"], "0" * 64)
tampered = post({"action": "adminexportfetch", "session_token": admin,
                 "export_id": j_e["export_id"]})
check(tampered.get("ok") is False,
      "a genuinely wrong checksum is still refused, not waved through as legacy",
      str(tampered)[:90])

print()
print("=" * 78)
failed = [x for x in results if not x[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
