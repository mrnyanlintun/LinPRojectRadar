#!/usr/bin/env python3
"""
Training mode, run 1: the flag, the gate, and the isolation of training data from the research
record.

Run (from server/):

    PYTHONIOENCODING=utf-8 DATABASE_URL=... SESSION_SECRET=... python tools/test_training_gating.py

TWO GUARANTEES, PROBED OVER REAL HTTP WHERE THE BRIEF ASKS FOR IT, NOT ONLY READ FROM CODE.

GUARANTEE 1, THE GATE: an operational account with the `training` flag on reaches
`trainingstatus`; off, it is refused; a research account is refused whatever the flag says;
an unauthenticated caller is refused. All four probed against the live /exec endpoint.

GUARANTEE 2, THE ISOLATION: a training-marked project's ComputedResult rows never leave through
`project_health`, in any of the three formats (json, csv, xlsx). The check can fail: the same
row is proven to APPEAR once the project is unmarked, so "absent" is shown to mean something.

Every fault below is injected against the RUNNING SERVER (module state, not a copy of the
logic), and the baseline is re-checked clean after each one, per the standing rule that a check
which cannot fail is worse than none.
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

import sqlalchemy as sa  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import AuditEvent, Participant  # noqa: E402
from app.features import (  # noqa: E402
    FEATURE_KEYS, GATED_ACTIONS, RESEARCH_FORBIDDEN_ACTIONS, default_for_account,
)
from app.models import Project  # noqa: E402
from app.research_export import EXPORT_FORMATS, build_module_results_rows  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


print("=" * 78)
print("SETUP: an admin, an operational account, a research account")
print("=" * 78)

ADMIN_TOKEN = "training-bootstrap-admin"
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="TRAINING-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN_TOKEN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN_TOKEN)
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN_TOKEN})["session_token"]
check(bool(admin), "admin session established")


def make(code: str, account_type: str) -> tuple[str, str]:
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": code, "role": "Participant",
                    "account_type": account_type})
    assert created.get("ok"), created
    tok = post({"action": "researchlogin",
                "access_token": created["access_token"]})["session_token"]
    return created["participant_id"], tok


ops_id, ops_tok = make("TRN-OPS", "operational")
res_id, res_tok = make("TRN-RES", "research")

print()
print("=" * 78)
print("GUARANTEE 0: the flag exists, follows the technical-reviewer pattern")
print("=" * 78)

check("training" in FEATURE_KEYS, "training is a recognised feature key", str(FEATURE_KEYS))
check(GATED_ACTIONS.get("trainingstatus") == "training",
      "trainingstatus is gated on the training key, the same mechanism auditor/health_dialog use")
check(default_for_account("research") is False,
      "a research account's unset flags default to disabled")
check(default_for_account("operational") is True,
      "an operational account's unset flags default to enabled")
check("trainingstatus" in RESEARCH_FORBIDDEN_ACTIONS,
      "trainingstatus is ALSO in the unconditional research-forbidden set, not left to the flag "
      "default alone", str(sorted(a for a in RESEARCH_FORBIDDEN_ACTIONS if "training" in a)))

print()
print("=" * 78)
print("GUARANTEE 1a: operational, flag OFF -> refused")
print("=" * 78)

# An operational account's UNSET flags default to enabled (default_for_account), so probing
# before the flag is ever touched would prove nothing about "off" — it would prove the default.
# Set the flag OFF explicitly first, then probe.
set_off = post({"action": "adminfeaturesset", "session_token": admin,
                "participant_id": ops_id, "features": {"training": False}})
check(set_off.get("ok") is True, "admin sets training=False for the operational account",
      str(set_off)[:140])
off2 = post({"action": "trainingstatus", "session_token": ops_tok})
check(off2.get("ok") is False, "operational + flag OFF is refused", str(off2)[:140])
check("disabled" in (off2.get("error") or "").lower(),
      "and the reason names the feature as disabled", str(off2.get("error"))[:100])

print()
print("=" * 78)
print("GUARANTEE 1b: operational, flag ON -> reaches the action")
print("=" * 78)

set_on = post({"action": "adminfeaturesset", "session_token": admin,
              "participant_id": ops_id, "features": {"training": True}})
check(set_on.get("ok") is True, "admin sets training=True", str(set_on)[:140])
on = post({"action": "trainingstatus", "session_token": ops_tok})
check(on.get("ok") is True, "operational + flag ON reaches the action", str(on)[:140])
check(on.get("enabled") is True, "and is told training is enabled", str(on.get("enabled")))
check(on.get("account_type") == "operational", "and its own account_type is reported",
      str(on.get("account_type")))

print()
print("=" * 78)
print("GUARANTEE 1c: research is refused whatever the flag says")
print("=" * 78)

before_deny = 0
with Session() as s:
    before_deny = len(s.scalars(select(AuditEvent).where(
        AuditEvent.event_type == "training_denied_research")).all())

res_default = post({"action": "trainingstatus", "session_token": res_tok})
check(res_default.get("ok") is False,
      "research account, flag never touched (defaults to disabled): refused", str(res_default)[:140])

# The load-bearing case: an admin explicitly turns the flag ON for a research account anyway.
# The default-off protection is gone the moment this write happens; the refusal must not have
# depended on it.
set_on_research = post({"action": "adminfeaturesset", "session_token": admin,
                        "participant_id": res_id, "features": {"training": True}})
check(set_on_research.get("ok") is True,
      "admin CAN set training=True on a research account (nothing stops the write)",
      str(set_on_research)[:140])
res_on = post({"action": "trainingstatus", "session_token": res_tok})
check(res_on.get("ok") is False,
      "still refused, even with the flag explicitly ON for this research account",
      str(res_on)[:140])
check("operational feature" in (res_on.get("error") or "").lower(),
      "and the reason says training is an operational feature", str(res_on.get("error"))[:100])

with Session() as s:
    after_deny = len(s.scalars(select(AuditEvent).where(
        AuditEvent.event_type == "training_denied_research")).all())
check(after_deny > before_deny, "each research refusal is audited",
      f"{before_deny} then {after_deny}")

# The inner layer, proven independently of gate_action — the same defence-in-depth proof
# test_theme_plain.py uses for themeset, called with the pre-dispatch gate bypassed entirely.
from app.training import a_trainingstatus  # noqa: E402
import os  # noqa: E402
_secret = os.environ.get("SESSION_SECRET", "")
with Session() as s:
    direct = a_trainingstatus(s, {"session_token": res_tok}, _secret, 28800)
check(direct.get("ok") is False,
      "the handler itself refuses a research account, with gate_action bypassed entirely",
      str(direct)[:140])

print()
print("=" * 78)
print("GUARANTEE 1d: an unauthenticated caller is refused")
print("=" * 78)

# gate_action itself leaves a sessionless caller alone (documented scope note in features.py) —
# the previous session found exactly that gap letting an anonymous getportfoliohealth bypass a
# flag a signed-in user with it off was held to. This is the case that proves the handler does
# not rely on the gate for authentication: no session_token at all.
anon = post({"action": "trainingstatus"})
check(anon.get("ok") is False, "no session_token at all: refused", str(anon)[:140])
anon_bad = post({"action": "trainingstatus", "session_token": "not-a-real-token"})
check(anon_bad.get("ok") is False, "a garbage token: refused", str(anon_bad)[:140])

print()
print("=" * 78)
print("ISOLATION SETUP: a training project with computed results")
print("=" * 78)

with Session() as s:
    real = Project(legacy_id="TRN-ISO-REAL", doc={"projectId": "TRN-ISO-REAL", "sector": "test"},
                   is_training=False)
    training = Project(legacy_id="TRN-ISO-TRAIN", doc={"projectId": "TRN-ISO-TRAIN",
                                                       "sector": "test"}, is_training=True)
    s.add_all([real, training])
    s.flush()
    real_id, training_id = real.id, training.id
    check(training.is_training is True, "the training project is marked at creation")
    check(real.is_training is False, "and an ordinary project is not, by default")
    s.execute(sa.text(
        "INSERT INTO computed_results (result_id, project_id, period, module_results, "
        "simulation_version, seed, period_cutoff) VALUES "
        "(:rid, :pid, 1, :mods, 'v1', 'seed', '2026-08-01')"
    ), {"rid": "TRNRESREAL01", "pid": str(real_id),
        "mods": json.dumps([{"module_id": "A1", "group": "A", "status_color": "green"}])})
    s.execute(sa.text(
        "INSERT INTO computed_results (result_id, project_id, period, module_results, "
        "simulation_version, seed, period_cutoff) VALUES "
        "(:rid, :pid, 1, :mods, 'v1', 'seed', '2026-08-01')"
    ), {"rid": "TRNRESTRAIN1", "pid": str(training_id),
        "mods": json.dumps([{"module_id": "A1", "group": "A", "status_color": "red"}])})
    s.commit()

print()
print("=" * 78)
print("GUARANTEE 2a: the training project's results are ABSENT from project_health")
print("=" * 78)

with Session() as s:
    rows = build_module_results_rows(s, None, None, None)
projects_seen = {r["project"] for r in rows}
check("TRN-ISO-REAL" in projects_seen,
      "the ordinary project's results ARE present, so absence below is not an empty query",
      str(sorted(p for p in projects_seen if p and p.startswith("TRN-ISO"))))
check("TRN-ISO-TRAIN" not in projects_seen,
      "the training project's results are NOT present", str(sorted(projects_seen))[:200])

for fmt in EXPORT_FORMATS:
    created = post({"action": "adminexportcreate", "session_token": admin,
                    "kind": "project_health", "format": fmt})
    check(created.get("ok") is True, f"project_health export created ({fmt})",
          str(created)[:140])
    export_id = created.get("export_id")
    fetched = post({"action": "adminexportfetch", "session_token": admin,
                    "export_id": export_id})
    check(fetched.get("ok") is True, f"project_health export fetched ({fmt})",
          str(fetched)[:140])
    if fmt == "xlsx":
        # Binary, base64-encoded (payload_base64) — a substring search on the JSON envelope
        # would search compressed, encoded bytes and could "pass" for a reason that has nothing
        # to do with the filter. Decode and read the actual cells, the way test_export_workbook.py
        # verifies a produced workbook: opened with openpyxl and read back, not only asserted
        # against the code that wrote it.
        import base64
        import io
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(base64.b64decode(fetched["payload_base64"])))
        ws = wb["Module results"]
        cells = {str(cell) for row in ws.iter_rows(values_only=True) for cell in row
                if cell is not None}
        check("TRN-ISO-TRAIN" not in cells,
              "the training project's legacy_id appears in no cell of the xlsx Module results "
              "sheet")
        check("TRN-ISO-REAL" in cells,
              "the ordinary project's legacy_id DOES appear in a cell, so the absence above is "
              "a real filter and not a broken export")
    else:
        payload_text = fetched.get("payload") or ""
        check("TRN-ISO-TRAIN" not in payload_text,
              f"the training project's legacy_id appears nowhere in the fetched {fmt} payload")
        check("TRN-ISO-REAL" in payload_text,
              f"the ordinary project's legacy_id DOES appear in the fetched {fmt} payload, so "
              "the absence above is a real filter and not a broken export")

print()
print("=" * 78)
print("GUARANTEE 2b: the check CAN fail — unmark the project and watch it appear")
print("=" * 78)

with Session() as s:
    t = s.get(Project, training_id)
    t.is_training = False
    s.commit()

with Session() as s:
    rows_after = build_module_results_rows(s, None, None, None)
projects_after = {r["project"] for r in rows_after}
check("TRN-ISO-TRAIN" in projects_after,
      "once unmarked, the SAME project's results now appear — the filter is real, not a "
      "coincidence of the fixture", str(sorted(p for p in projects_after if p and
                                               p.startswith("TRN-ISO"))))

created2 = post({"action": "adminexportcreate", "session_token": admin,
                 "kind": "project_health", "format": "json"})
fetched2 = post({"action": "adminexportfetch", "session_token": admin,
                 "export_id": created2.get("export_id")})
check("TRN-ISO-TRAIN" in json.dumps(fetched2),
      "and the unmarked project now appears in a fresh fetch too")

# Restore, so a re-run of this file starts from the same fixture state.
with Session() as s:
    t = s.get(Project, training_id)
    t.is_training = True
    s.commit()
with Session() as s:
    rows_restored = build_module_results_rows(s, None, None, None)
check("TRN-ISO-TRAIN" not in {r["project"] for r in rows_restored},
      "re-marking it training makes it absent again, confirming the flag (not something else "
      "about the fixture) is what changed")

print()
print("=" * 78)
print("GUARANTEE 2c: a training project cannot become research evidence")
print("=" * 78)

sc = post({"action": "adminscenariocreate", "session_token": admin,
          "scenario_version": "TRAIN-EVIDENCE-PROBE", "evidence_package_id": "TRN-ISO-TRAIN"})
check(sc.get("ok") is False,
      "a scenario naming a training project as evidence is refused at creation", str(sc)[:160])
check("training project" in (sc.get("error") or "").lower(), "and says why", str(sc.get("error")))

sc_ok = post({"action": "adminscenariocreate", "session_token": admin,
             "scenario_version": "TRAIN-EVIDENCE-PROBE-OK", "evidence_package_id": "TRN-ISO-REAL"})
check(sc_ok.get("ok") is True,
      "an ordinary project is still accepted as evidence", str(sc_ok)[:140])

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
