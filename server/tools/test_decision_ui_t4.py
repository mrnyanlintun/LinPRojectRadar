#!/usr/bin/env python3
"""
T4 guarantees: the decision sequence.

Run (from server/):

    DATABASE_URL=... SESSION_SECRET=... python tools/test_decision_ui_t4.py

This is the phase the study rests on. The locked preliminary judgment is the entire comparison
in the research design — there is no unsupported condition, so the pre/post contrast within each
decision is the only place the AI's influence is observable. A leak before the lock does not
annoy a user; it silently converts every decision made through this interface into an
uninterpretable data point.

GUARANTEE 1 IS WRITTEN TO FAIL.

B7b's leak survived eight phases because its grep had a clause that could never be false.
`scan_for_leak` below is therefore proven against a deliberately planted leak BEFORE it is
trusted against the real response — see GUARANTEE 1 for the self-test. It scans for the package
vocabulary AND for the action tokens in free prose, because the leak this phase actually found
was in prose (`evidence_metric`), not in a key.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient
from sqlalchemy import select, text

import app.main as main
from app.research_identity import hash_access_token
from app.research_models import (
    Assignment, AuditEvent, Decision, DecisionSupportPackage, Participant,
)

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def audit_count(event_type: str) -> int:
    with Session() as s:
        return len(s.scalars(select(AuditEvent).where(
            AuditEvent.event_type == event_type)).all())


# --------------------------------------------------------------- the leak detector
#
# T6 needs this identical detector for the expert reference lock. It lives in tools/leak_detector
# so there is ONE definition of what counts as a leak — two copies would drift, and a drifted
# copy reports green while proving something weaker than it claims. The self-test below is
# unchanged: the detector is still proven able to FAIL before it is trusted.

from tools.leak_detector import (  # noqa: E402
    ACTION_PROSE_MARKERS, MARK_ALTERNATIVE, MARK_BOUNDARY, MARK_CONDITION, MARK_LIMITATION,
    MARK_RECOMMENDATION, MARK_UNCERTAINTY, PACKAGE_FIELD_NAMES, PACKAGE_MARKERS, scan_for_leak,
)


ADMIN = "t4-admin"

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="T4-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

print("=" * 78)
print("T4 — the decision sequence")
print("=" * 78)
print("\nSETUP: scenario, frozen package with planted markers, action families, participants")

# MOVED ABOVE THE SCENARIOS on 2026-08-03. `adminscenariocreate` now refuses a scenario
# whose evidence_package_id does not name an existing project, so the projects a scenario
# points at have to exist before it is created. The ordering is the dependency made
# explicit; nothing about what these projects are has changed.
_writer = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "T4-WRITER", "role": "Participant",
                "account_type": "operational"})
writer = post({"action": "researchlogin",
               "access_token": _writer["access_token"]})["session_token"]
post({"action": "create", "id": "PRJ-T4-EVIDENCE", "name": "T4 Evidence Project",
      "session_token": writer})
post({"action": "create", "id": "PRJ-T4-MEMBERED", "name": "T4 Membered Project",
      "session_token": writer})
# A separate project for the analytical-layer leak test: it needs real documents and a computed
# result, which needs a PM, which would block every other participant on the shared scenario.
post({"action": "create", "id": "PRJ-T4-ANALYTICS", "name": "T4 Analytics Project",
      "session_token": writer})

scenario = post({"action": "adminscenariocreate", "session_token": admin,
                 "scenario_version": "t4-v1", "project_type": "construction",
                 "period_count": 2, "evidence_package_id": "PRJ-T4-EVIDENCE"})["scenario_id"]
post({"action": "adminconfigurationcreate", "session_token": admin,
      "code": "C0", "version": "t4", "label": "C0", "freeze": True})
post({"action": "adminsequencecreate", "session_token": admin, "order_group": "GT4",
      "scenario_set": "SET-T4", "version": "t4", "positions": ["C0", "C0"], "freeze": True})
post({"action": "adminactionfamilycreate", "session_token": admin, "version": "t4",
      "mappings": {"monitor": "accept", "investigate": "modify", "escalate": "escalate",
                   "re-baseline": "modify", "defer": "defer"}, "freeze": True})
for fam in ("accept", "modify", "escalate", "defer"):
    post({"action": "admintransitionrulecreate", "session_token": admin,
          "scenario_id": scenario, "period": "P1", "action_family": fam, "version": "t4",
          "freeze": True,
          "branches": [{"branch_id": f"B-{fam}", "branch_version": "t4",
                        "probability": "1.0", "next_state_id": "PRJ-T4-EVIDENCE"}]})

# A SECOND scenario whose evidence project HAS membership rows, used only by Guarantee 8. The
# main scenario's project deliberately has none: refuse_unless_pm_for_assignment only engages
# when a project has members, so leaving the main one unmembered lets several test participants
# share one scenario, while this one exercises the PM/Observer split.
scenario_obs = post({"action": "adminscenariocreate", "session_token": admin,
                     "scenario_version": "t4-obs", "project_type": "construction",
                     "period_count": 1,
                     "evidence_package_id": "PRJ-T4-MEMBERED"})["scenario_id"]
post({"action": "adminsequencecreate", "session_token": admin, "order_group": "GT4OBS",
      "scenario_set": "SET-T4OBS", "version": "t4", "positions": ["C0"], "freeze": True})

pkg = post({"action": "adminpackagecreate", "session_token": admin, "version": "t4-pkg",
            "provider_id": "frozen-store", "model_version": "t4-model",
            "recommended_action": MARK_RECOMMENDATION,
            "alternatives": {"a": MARK_ALTERNATIVE},
            "detected_condition": MARK_CONDITION,
            "limitations": MARK_LIMITATION,
            "uncertainty": {"u": MARK_UNCERTAINTY},
            "applicability_boundary": MARK_BOUNDARY,
            "freeze": True})
check(pkg.get("ok") is True, "frozen package created with planted markers", str(pkg)[:110])


# The facade fails closed on writes as of 2026-08-02, and `create` is additionally refused for a
# research account, so the fixture projects below are created by an OPERATIONAL participant.
_WRITER_TOKEN = "t4-writer"


def hand_pm_to(legacy_id: str, participant_id: str) -> dict:
    """
    Move PM on a project that already has one.

    Creating a project now writes its creator's PM row in the same transaction, and only one
    active PM is permitted per project, so a fixture that wants a different owner must revoke
    before it adds. Every check below that used a bare adminmemberadd goes through here instead.
    """
    for m in post({"action": "adminmemberlist", "session_token": admin,
                   "id": legacy_id}).get("members") or []:
        if m.get("active") and m.get("project_role") == "PM":
            post({"action": "adminmemberrevoke", "session_token": admin,
                  "member_id": m["member_id"]})
    return post({"action": "adminmemberadd", "session_token": admin, "id": legacy_id,
                 "participant_id": participant_id, "project_role": "PM"})


def enrol(code: str, do_intake: bool = True, scen: str = None,
          group: str = "GT4", scen_set: str = "SET-T4"):
    c = post({"action": "adminparticipantcreate", "session_token": admin,
              "pseudonymous_code": code})
    tok = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    post({"action": "consentgrant", "session_token": tok, "consent_version": "t4-v1"})
    if do_intake:
        post({"action": "intakesave", "session_token": tok,
              "responses": {"experience_level": "senior", "years_experience": 12}})
    post({"action": "adminassign", "session_token": admin, "participant_id": c["participant_id"],
          "order_group": group, "scenario_set": scen_set,
          "scenario_ids": [scen or scenario]})
    with Session() as s:
        a = s.scalar(select(Assignment).where(Assignment.participant_id == c["participant_id"]))
        aid = a.assignment_id
    post({"action": "adminpackageattach", "session_token": admin, "assignment_id": aid,
          "package_id": pkg["package_id"]})
    return c["participant_id"], tok, aid


p_id, p, p_aid = enrol("T4-P1")
nointake_id, nointake, _ = enrol("T4-NOINTAKE", do_intake=False)

# Real documents on the analytics project, so the ACTION-BEARING modules actually compute.
# Without evm inputs, B4.4 Regret Minimization abstains and the leak test would pass vacuously
# against a result that contains no recommendation to leak in the first place.
import hashlib as _hashlib

from app.documents import set_extractor_override
from app.extraction_client import StubExtractor

MONTHLY = b"%PDF-1.4 T4 MONTHLY REPORT EV/AC/PV\n"
set_extractor_override(StubExtractor({
    _hashlib.sha256(MONTHLY).hexdigest(): ("monthly_report", {
        "earned_value": 4000000, "actual_cost": 4800000, "planned_value": 5000000,
        "actual_percent_complete": 40, "planned_percent_complete": 50,
        "budget_at_completion": 10000000, "report_date": "2026-06-30",
    }),
}))
hand_pm_to("PRJ-T4-ANALYTICS", p_id)
import base64 as _b64
up = post({"action": "projectupload", "session_token": p, "id": "PRJ-T4-ANALYTICS", "period": 1,
           "documents": [{"filename": "monthly-06.pdf", "mimeType": "application/pdf",
                          "dataBase64": _b64.b64encode(MONTHLY).decode("ascii")}]})
check(up.get("ok") is True, "evidence document uploaded to the analytics project", str(up)[:110])


# --------------------------------------------------------------- Guarantee 5 (first: gates the rest)

print("\nGuarantee 5 — no preliminary judgment without a completed intake questionnaire")
before = audit_count("pre_judgment_denied_no_intake")
r = post({"action": "researchprejudgment", "session_token": nointake,
          "pre_action": "monitor", "pre_confidence": 50})
check(r.get("ok") is False, "refused without intake", str(r)[:130])
check("intake questionnaire" in (r.get("error") or ""), "refusal names the questionnaire")
check(audit_count("pre_judgment_denied_no_intake") == before + 1, "refusal audited")
post({"action": "intakesave", "session_token": nointake,
      "responses": {"experience_level": "mid", "years_experience": 5}})
r2 = post({"action": "researchprejudgment", "session_token": nointake,
           "pre_action": "monitor", "pre_confidence": 50})
check(r2.get("ok") is True, "accepted once intake is complete", str(r2)[:110])


# --------------------------------------------------------------- Guarantee 1

print("\nGuarantee 1 — the evidence screen carries no recommendation, in any field")

print("  [self-test] the detector must FAIL on a planted leak before it is trusted")
planted_key = json.dumps({"module_results": [{"module_id": "B4.4",
                                              "recommended_action": "escalate"}]})
planted_prose = json.dumps({"module_results": [
    {"evidence_metric": "Minimax regret recommends: escalate (expected regret score 5/30)"}]})
planted_marker = json.dumps({"anything": MARK_RECOMMENDATION})
check(len(scan_for_leak(planted_key)) > 0,
      "detector catches a planted KEY leak", str(scan_for_leak(planted_key)))
check(len(scan_for_leak(planted_prose)) > 0,
      "detector catches a planted PROSE leak", str(scan_for_leak(planted_prose)))
check(len(scan_for_leak(planted_marker)) > 0,
      "detector catches a planted package MARKER", str(scan_for_leak(planted_marker)))
check(len(scan_for_leak(json.dumps({"status_color": "Green", "period": "P1"}))) == 0,
      "detector does NOT fire on clean content (it can pass, so passing means something)")

print("  [real] every pre-lock response a participant can reach")
pre_lock_bodies = {
    "researchsequencestate": post({"action": "researchsequencestate", "session_token": p}),
    "researchevidenceget": post({"action": "researchevidenceget", "session_token": p}),
    "researchmyassignments": post({"action": "researchmyassignments", "session_token": p}),
    "researchcurrent": post({"action": "researchcurrent", "session_token": p}),
    "researchreveal(refused)": post({"action": "researchreveal", "session_token": p}),
}
for name, body in pre_lock_bodies.items():
    findings = scan_for_leak(json.dumps(body))
    check(len(findings) == 0, f"{name} leaks nothing", str(findings))

# The analytical-layer path — the one B7b's redaction covers, and where this phase found the
# prose leak. Runs against the analytics project, which has real evm inputs, so the
# action-bearing modules genuinely compute and there is a real recommendation to leak.
post({"action": "projectcompute", "session_token": p, "id": "PRJ-T4-ANALYTICS", "period": 1})
pr = post({"action": "projectresults", "session_token": p, "id": "PRJ-T4-ANALYTICS",
           "period": 1})
pr_body = json.dumps(pr)
findings = scan_for_leak(pr_body)
check(pr.get("ok") is True, "projectresults readable pre-lock (the evidence screen's source)")
check(len(findings) == 0, "projectresults leaks nothing pre-lock", str(findings))
check(pr["result"]["recommendation"] is None, "recommendation is null pre-lock")
mods = pr["result"]["module_results"] or []
withheld = [m for m in mods if isinstance(m, dict) and m.get("recommendation_withheld")]
check(len(withheld) > 0, "action-bearing modules are marked withheld",
      f"{len(withheld)} of {len(mods)}")
check(all("recommends:" not in json.dumps(m).lower() for m in mods),
      "no module's prose restates a recommendation")


# --------------------------------------------------------------- Guarantee 2

print("\nGuarantee 2 — reveal refused before the lock, and the refusal leaks nothing")
fresh_id, fresh, fresh_aid = enrol("T4-FRESH")
before = audit_count("reveal_denied_unlocked")
rv = post({"action": "researchreveal", "session_token": fresh})
check(rv.get("ok") is False, "reveal refused before lock", str(rv)[:130])
check(audit_count("reveal_denied_unlocked") == before + 1, "refusal audited")
findings = scan_for_leak(json.dumps(rv))
check(len(findings) == 0, "refusal body leaks nothing", str(findings))
check("package" not in rv, "refusal has no package key at all")
check(set(rv.keys()) == {"ok", "error"}, "refusal is exactly {ok, error}", str(set(rv.keys())))


# --------------------------------------------------------------- Guarantee 3

print("\nGuarantee 3 — the locked pre-judgment is irreversible, four ways")
pj = post({"action": "researchprejudgment", "session_token": fresh,
           "pre_action": "monitor", "pre_confidence": 55})
check(pj.get("ok") is True and pj.get("pre_judgment_locked") is True, "pre-judgment locked")
with Session() as s:
    d = s.scalar(select(Decision).where(Decision.assignment_id == fresh_aid))
    fresh_did, orig_action, orig_conf = d.decision_id, d.pre_action, d.pre_confidence

# (a) direct API resubmission
before = audit_count("pre_judgment_resubmission_denied")
again = post({"action": "researchprejudgment", "session_token": fresh,
              "pre_action": "escalate", "pre_confidence": 99})
check(again.get("ok") is False and "already locked" in (again.get("error") or ""),
      "direct API resubmission refused", str(again)[:110])
check(audit_count("pre_judgment_resubmission_denied") == before + 1, "resubmission audited")

# (b) the database trigger, bypassing the application entirely
db_refused, detail = False, ""
with Session() as s:
    try:
        s.execute(text("UPDATE decisions SET pre_action = 'TAMPERED', pre_confidence = 1 "
                       "WHERE decision_id = :d"), {"d": fresh_did})
        s.commit()
    except Exception as exc:
        s.rollback()
        db_refused = True
        detail = str(exc)[:110]
check(db_refused, "database trigger rejects a direct UPDATE of the locked judgment", detail)

# (c) the stored values are untouched after both attempts
with Session() as s:
    d = s.scalar(select(Decision).where(Decision.decision_id == fresh_did))
check(d.pre_action == orig_action and d.pre_confidence == orig_conf,
      "stored judgment is byte-identical after both attempts",
      f"{d.pre_action}/{d.pre_confidence}")

# (d) a reload cannot re-open the form: the server reports a stage past evidence, and never
#     returns the locked values for a form to repopulate.
st = post({"action": "researchsequencestate", "session_token": fresh})
check(st["current_stage"] == "awaiting_reveal",
      "server reports awaiting_reveal, so a reload cannot render the form", st["current_stage"])
check("pre_action" not in json.dumps(st) and "pre_confidence" not in json.dumps(st),
      "sequence state never returns the locked judgment values")


# --------------------------------------------------------------- Guarantee 4

print("\nGuarantee 4 — pre_locked_at <= reveal_at, enforced by the database")
rv = post({"action": "researchreveal", "session_token": fresh})
check(rv.get("ok") is True, "reveal succeeds after the lock", str(rv)[:110])
check(MARK_RECOMMENDATION in json.dumps(rv), "the package IS delivered after the lock")
with Session() as s:
    d = s.scalar(select(Decision).where(Decision.decision_id == fresh_did))
    locked_at, reveal_at = d.pre_locked_at, d.reveal_at
check(locked_at is not None and reveal_at is not None and locked_at <= reveal_at,
      "stored row satisfies pre_locked_at <= reveal_at", f"{locked_at} <= {reveal_at}")

check_refused, detail = False, ""
with Session() as s:
    try:
        s.execute(text("UPDATE decisions SET reveal_at = :early WHERE decision_id = :d"),
                  {"early": "2020-01-01 00:00:00+00", "d": fresh_did})
        s.commit()
    except Exception as exc:
        s.rollback()
        check_refused = True
        detail = str(exc)[:110]
check(check_refused, "CHECK rejects a reveal timestamped before the lock", detail)

check_refused2, detail2 = False, ""
with Session() as s:
    try:
        s.execute(text("UPDATE decisions SET pre_locked_at = NULL WHERE decision_id = :d"),
                  {"d": fresh_did})
        s.commit()
    except Exception as exc:
        s.rollback()
        check_refused2 = True
        detail2 = str(exc)[:110]
check(check_refused2, "CHECK rejects clearing the lock on a revealed row", detail2)


# --------------------------------------------------------------- Guarantee 9

print("\nGuarantee 9 — deliberation time computes from the stored timestamps")
PAUSE_SECONDS = 2.0
time.sleep(PAUSE_SECONDS)
dec = post({"action": "researchdecision", "session_token": fresh,
            "final_action": "escalate", "disposition": "accept_with_conditions",
            "rationale": "Cost variance is material and the trend is not self-correcting.",
            "final_confidence": 78, "reason_code": "cost_variance",
            "evidence_items": ["Cost & EVM Performance", "pay-app-06.pdf"],
            "deadline": "next reporting cycle", "residual_risk": "Schedule float stays thin.",
            "owner_role": "project_manager", "authority_role": "sponsor"})
check(dec.get("ok") is True, "final decision recorded", str(dec)[:110])
with Session() as s:
    d = s.scalar(select(Decision).where(Decision.decision_id == fresh_did))
    delib = (d.final_submitted_at - d.reveal_at).total_seconds()
check(delib >= PAUSE_SECONDS,
      f"deliberation >= the real {PAUSE_SECONDS}s pause", f"{delib:.2f}s")
check(delib < PAUSE_SECONDS + 60, "deliberation is not absurdly large", f"{delib:.2f}s")
check(d.reason_code == "cost_variance" and d.deadline == "next reporting cycle"
      and d.residual_risk and isinstance(d.evidence_items, list),
      "the new structured capture fields all persisted")

exp = post({"action": "adminexportcreate", "session_token": admin, "format": "json"})
fetched = post({"action": "adminexportfetch", "session_token": admin,
                "export_id": exp["export_id"]})
payload = json.loads(fetched["payload"])
row = next((r for r in payload["rows"] if r.get("pseudonymous_code") == "T4-FRESH"), None)
check(row is not None, "the decision reaches the export")
check(row and row.get("deliberation_seconds") is not None
      and float(row["deliberation_seconds"]) >= PAUSE_SECONDS,
      "export's deliberation_seconds matches the real pause",
      str(row.get("deliberation_seconds") if row else None))
check(row and row.get("reason_code") == "cost_variance",
      "new capture fields are in the export allowlist")
check("residual_risk" in (fetched.get("free_text_columns") or []),
      "residual_risk is flagged for free-text review",
      str(fetched.get("free_text_columns")))


# --------------------------------------------------------------- Guarantee 6

print("\nGuarantee 6 — stage is server-derived and survives reload, re-login, and a long gap")
st1 = post({"action": "researchsequencestate", "session_token": fresh})
check(st1["current_stage"] == "complete", "stage after deciding is complete", st1["current_stage"])

# a "reload" is simply asking again — no client state carries over
st2 = post({"action": "researchsequencestate", "session_token": fresh})
check(st1["current_stage"] == st2["current_stage"], "stage identical across a reload")

# sign out and in: a brand-new session token for the same participant
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.participant_id == fresh_id))
    row.access_token_hash = hash_access_token("t4-relogin")
    s.commit()
relogin = post({"action": "researchlogin", "access_token": "t4-relogin"})["session_token"]
check(relogin != fresh, "a genuinely different session token")
st3 = post({"action": "researchsequencestate", "session_token": relogin})
check(st3["current_stage"] == st1["current_stage"],
      "stage identical after sign-out and sign-in", st3["current_stage"])

# a simulated multi-day gap: age every timestamp on the row by a week
with Session() as s:
    s.execute(text("UPDATE decisions SET pre_submitted_at = :t, pre_locked_at = :t, "
                   "reveal_at = :t2, final_submitted_at = :t3 WHERE decision_id = :d"),
              {"t": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
               "t2": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
               "t3": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
               "d": fresh_did})
    s.commit()
st4 = post({"action": "researchsequencestate", "session_token": relogin})
check(st4["current_stage"] == "complete", "stage survives a seven-day gap", st4["current_stage"])


# --------------------------------------------------------------- Guarantee 7

print("\nGuarantee 7 — no idle timeout interrupts an open decision")
idle_id, idle, idle_aid = enrol("T4-IDLE")
post({"action": "researchprejudgment", "session_token": idle,
      "pre_action": "monitor", "pre_confidence": 40})
post({"action": "researchreveal", "session_token": idle})
IDLE_SECONDS = 3.0
time.sleep(IDLE_SECONDS)
still = post({"action": "researchsequencestate", "session_token": idle})
check(still.get("ok") is True, f"session still valid after a {IDLE_SECONDS}s idle gap")
check(still["current_stage"] == "deciding", "still mid-decision", still["current_stage"])
late = post({"action": "researchdecision", "session_token": idle, "final_action": "monitor",
             "disposition": "accept", "final_confidence": 50,
             "rationale": "No change warranted."})
check(late.get("ok") is True, "the decision submits after the idle gap", str(late)[:110])

with Session() as s:
    settings_ttl = main.settings.session_ttl_seconds
check(settings_ttl >= 8 * 3600,
      "the configured session TTL is long enough to never expire mid-session",
      f"{settings_ttl}s")


# --------------------------------------------------------------- Guarantee 8

print("\nGuarantee 8 — an observer sees evidence but cannot judge, reveal, or decide")
# Runs on the membered scenario: refuse_unless_pm_for_assignment only engages when the
# assignment's project has membership rows, so this is the fixture that exercises it.
pm2_id, pm2, _ = enrol("T4-OBS-PM", scen=scenario_obs, group="GT4OBS", scen_set="SET-T4OBS")
obs_id, obs, _ = enrol("T4-OBS", scen=scenario_obs, group="GT4OBS", scen_set="SET-T4OBS")
hand_pm_to("PRJ-T4-MEMBERED", pm2_id)
post({"action": "adminmemberadd", "session_token": admin, "id": "PRJ-T4-MEMBERED",
      "participant_id": obs_id, "project_role": "Observer"})
post({"action": "projectcompute", "session_token": pm2, "id": "PRJ-T4-MEMBERED", "period": 1})

obs_read = post({"action": "projectresults", "session_token": obs,
                 "id": "PRJ-T4-MEMBERED", "period": 1})
check(obs_read.get("ok") is True, "observer CAN read the evidence", str(obs_read)[:100])
findings = scan_for_leak(json.dumps(obs_read))
check(len(findings) == 0, "and it leaks nothing to them either", str(findings))

before = audit_count("pm_only_action_denied")
for act, extra in (("researchprejudgment", {"pre_action": "monitor", "pre_confidence": 50}),
                   ("researchreveal", {}),
                   ("researchdecision", {"final_action": "monitor", "disposition": "accept"})):
    r = post(dict({"action": act, "session_token": obs}, **extra))
    check(r.get("ok") is False, f"observer refused: {act}", str(r)[:100])
check(audit_count("pm_only_action_denied") > before, "observer refusals audited")


# --------------------------------------------------------------- Guarantee 10

print("\nGuarantee 10 — no module id or number in participant-facing text")
import re as _re
# A module id is a letter, a digit, a dot, a digit — e.g. A1.1, B4.4, C1.2, D1.5.
MODULE_ID = _re.compile(r"\b[ABCD]\d+\.\d+\b")
ui_text = []
# T6 folded decision.html into index.html and deleted it, so the markup half of this pair is
# now index.html. The check is unchanged in substance: both the markup that shows the decision
# sequence and the script that renders it must be free of module ids.
for path in ("index.html", "assets/js/decision-ui.js"):
    import pathlib
    f = pathlib.Path(__file__).resolve().parents[2] / path
    if f.is_file():
        ui_text.append((path, f.read_text(encoding="utf-8")))
check(len(ui_text) == 2, "both T4 UI files found", str([p for p, _ in ui_text]))
for path, body in ui_text:
    # Strip comments: a comment citing models_gov.py:633 is documentation, not user-facing text.
    stripped = _re.sub(r"/\*.*?\*/", "", body, flags=_re.S)
    stripped = _re.sub(r"^\s*//.*$", "", stripped, flags=_re.M)
    stripped = _re.sub(r"<!--.*?-->", "", stripped, flags=_re.S)
    # Strip the NAME LOOKUP TABLES. Their keys are module ids by necessity — they are the
    # mapping whose entire purpose is that an id is never rendered, and `moduleName()` returns
    # only their values. A scan that flagged them would be flagging the fix as the defect.
    # Narrow and explicit: only these three named literals are removed, so an id appearing
    # anywhere else in the file still fails this check.
    for table in ("MODULE_NAMES", "CATEGORY_NAMES", "GROUP_NAMES"):
        stripped = _re.sub(r"var\s+" + table + r"\s*=\s*\{.*?\n\s*\};", "", stripped, flags=_re.S)
    hits = MODULE_ID.findall(stripped)
    check(len(hits) == 0, f"{path} renders no module id outside the name lookup",
          str(sorted(set(hits))[:6]))

# The lookup itself must actually translate — an id that fell through would be rendered raw.
# Indexed by name rather than position: the pair above is order-dependent and a future edit
# that reorders it should not silently start asserting against the wrong file.
_ui = dict(ui_text)
check("moduleName(m.module_id)" in _ui.get("assets/js/decision-ui.js", ""),
      "module rows render moduleName(...), never the raw id")
check('esc(m.module_id)' not in _ui.get("assets/js/decision-ui.js", "")
      and '+ m.module_id' not in _ui.get("assets/js/decision-ui.js", ""),
      "the raw module_id is never concatenated into markup")


# --------------------------------------------------------------- sequence integrity

print("\nSequence integrity — order cannot be skipped")
skip_id, skip, skip_aid = enrol("T4-SKIP")
r = post({"action": "researchdecision", "session_token": skip, "final_action": "monitor",
          "disposition": "accept"})
check(r.get("ok") is False and "revealed" in (r.get("error") or ""),
      "cannot decide before revealing", str(r)[:110])
r = post({"action": "researchadvance", "session_token": skip})
check(r.get("ok") is False, "cannot advance before deciding", str(r)[:110])
post({"action": "researchprejudgment", "session_token": skip,
      "pre_action": "monitor", "pre_confidence": 50})
r = post({"action": "researchadvance", "session_token": skip})
check(r.get("ok") is False, "cannot advance after locking but before deciding", str(r)[:110])
post({"action": "researchreveal", "session_token": skip})
post({"action": "researchdecision", "session_token": skip, "final_action": "monitor",
      "disposition": "accept", "final_confidence": 50})
adv = post({"action": "researchadvance", "session_token": skip})
check(adv.get("ok") is True, "advance succeeds once the decision is complete", str(adv)[:110])
check(adv.get("period") == "P2", "advanced to the next period", str(adv.get("period")))
st = post({"action": "researchsequencestate", "session_token": skip})
check(st["current_stage"] == "evidence", "next period starts at evidence", st["current_stage"])
check(st["period"] == "P2", "and reports the new period", st["period"])
findings = scan_for_leak(json.dumps(st))
check(len(findings) == 0, "the new period's state leaks nothing", str(findings))


# --------------------------------------------------------------- tail

print()
print("=" * 78)
passed = sum(1 for ok, _, _ in results if ok)
for ok, label, detail in results:
    if not ok:
        print(f"  FAILED: {label}  {detail}")
print(f"RESULT: {passed}/{len(results)} checks passed")
print("=" * 78)
sys.exit(0 if passed == len(results) else 1)
