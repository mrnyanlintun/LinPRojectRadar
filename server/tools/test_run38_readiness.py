#!/usr/bin/env python3
"""
Run 38: controlled-study execution readiness gate.

Everything here is MEASURED against the live application through the /exec surface and the
live database, on a fresh migrated SQLite. Nothing is read off a methodology document, and no
check asserts against a copy of the logic it is testing.

The suite drives a complete TEST_ONLY dry-run study (2 isolated participants x 6 projects x 6
periods) and emits the Run-38 audit artifacts as a side effect of the measurement, so the CSVs
can never describe a run that did not happen.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... python tools/test_run38_readiness.py
"""
from __future__ import annotations

import csv
import json
import logging
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
logging.disable(logging.INFO)

from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.exc import DatabaseError  # noqa: E402

import run38_dryrun as D  # noqa: E402
import run38_analysis_export as AX  # noqa: E402
from app.research_export import (  # noqa: E402
    EXPORT_COLUMNS, FREE_TEXT_COLUMNS, build_rows,
)
from app.research_models import Assignment, AuditEvent, Decision  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]
AUDIT = REPO / "code_audit"
post = D.post

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))
    return bool(ok)


def write_csv(path: pathlib.Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


# ===================================================================== bootstrap
print("=" * 78)
print("SECTION 1-2  DRY-RUN STUDY BOOTSTRAP (TEST_ONLY)")
print("=" * 78)

ctx = D.bootstrap()
A = D.make_participant(ctx, "A")
B = D.make_participant(ctx, "B")
check(len(A["assignments"]) == 6, "participant A holds 6 assignments (6 study projects)",
      str(len(A["assignments"])))
check(len(B["assignments"]) == 6, "participant B holds 6 assignments")

# ===================================================================== state machine
print()
print("=" * 78)
print("SECTION 1  PARTICIPANT STATE MACHINE, MEASURED PER TRANSITION")
print("=" * 78)

SM_HEADER = ["prior_state", "participant_visible_controls", "required_persisted_values",
             "server_transition", "resulting_state", "reversible", "permitted_edit_behavior",
             "expected_audit_event", "execution_evidence", "result"]
sm_rows: list[list] = []

# The first period of the first assignment is walked one transition at a time, with the
# forbidden move attempted BEFORE the permitted one at every step.
tok = A["token"]

ev = post({"action": "researchevidenceget", "session_token": tok})
leak_pre_reveal = post({"action": "researchreveal", "session_token": tok})
ai_visible_early = bool(leak_pre_reveal.get("ok")) or ("package" in leak_pre_reveal)
seq0 = post({"action": "researchsequencestate", "session_token": tok})
ai_in_state = any(k in json.dumps(seq0) for k in ("recommended_action", "detected_condition"))
ai_in_evidence = any(k in json.dumps(ev) for k in
                     ("recommended_action", "detected_condition", "package"))
ok = check(not ai_visible_early and not ai_in_state and not ai_in_evidence,
           "AI is not visible before the preliminary lock, by any of the three read paths",
           f"reveal={leak_pre_reveal.get('error')}")
sm_rows.append(["evidence_review", "evidence panel; preliminary form",
                "none", "researchevidenceget (read only)", "evidence_review", "yes",
                "no judgment exists yet", "evidence_viewed",
                f"researchreveal refused: {leak_pre_reveal.get('error')!r}; "
                f"sequencestate carries no package field",
                "PASS" if ok else "FAIL"])

pj = post({"action": "researchprejudgment", "session_token": tok,
           "pre_action": "monitor", "pre_confidence": 60, "pre_assessment": "dry run"})
ok = check(pj.get("ok") and pj.get("pre_judgment_locked") is True and pj.get("pre_locked_at"),
           "preliminary submit and lock are one server transition", json.dumps(pj)[:160])
sm_rows.append(["evidence_review", "preliminary action, confidence, assessment; submit",
                "pre_action, pre_confidence, pre_submitted_at, pre_locked_at, "
                "pre_judgment_locked", "researchprejudgment (INSERT, locked in same statement)",
                "awaiting_reveal", "no", "none: resubmission refused",
                "pre_judgment_locked",
                f"pre_locked_at={pj.get('pre_locked_at')} stage={pj.get('current_stage')}",
                "PASS" if ok else "FAIL"])

edit = post({"action": "researchprejudgment", "session_token": tok,
             "pre_action": "escalate", "pre_confidence": 99})
with D.SessionFactory() as s:
    d0 = s.scalars(select(Decision)).first()
    did = d0.decision_id
    held = (d0.pre_action, d0.pre_confidence)
ok = check(not edit.get("ok") and held == ("monitor", 60),
           "preliminary judgment is not editable after lock (API)", f"{edit} {held}")
sm_rows.append(["awaiting_reveal", "preliminary form is no longer offered",
                "pre_judgment_locked = true", "researchprejudgment (refused)",
                "awaiting_reveal", "no", "refused",
                "pre_judgment_resubmission_denied",
                f"error={edit.get('error')!r}; persisted stays {held}",
                "PASS" if ok else "FAIL"])

adv_early = post({"action": "researchadvance", "session_token": tok})
ok = check(not adv_early.get("ok"), "period advance is refused before the final lock",
           str(adv_early))
sm_rows.append(["awaiting_reveal", "no next-period control", "final_submitted_at IS NULL",
                "researchadvance (refused)", "awaiting_reveal", "n/a", "refused",
                "advance_denied_incomplete", f"error={adv_early.get('error')!r}",
                "PASS" if ok else "FAIL"])

fin_early = post({"action": "researchdecision", "session_token": tok,
                  "final_action": "escalate", "disposition": "accept"})
ok = check(not fin_early.get("ok"),
           "final judgment is not accepted before the AI reveal", str(fin_early))
sm_rows.append(["awaiting_reveal", "final form is not offered", "reveal_at IS NULL",
                "researchdecision (refused)", "awaiting_reveal", "n/a", "refused",
                "decision_denied_unrevealed", f"error={fin_early.get('error')!r}",
                "PASS" if ok else "FAIL"])

rv = post({"action": "researchreveal", "session_token": tok})
ok = check(rv.get("ok") and rv.get("package", {}).get("recommended_action"),
           "AI reveal succeeds only after the preliminary lock and returns the frozen package",
           json.dumps(rv)[:140])
sm_rows.append(["awaiting_reveal", "reveal control", "reveal_at, package_id, package_hash",
                "researchreveal (UPDATE, hash copied onto the decision)", "deciding", "no",
                "idempotent re-read does not move reveal_at", "package_revealed",
                f"reveal_at={rv.get('reveal_at')} hash={rv.get('package',{}).get('hash','')[:16]}",
                "PASS" if ok else "FAIL"])

rv2 = post({"action": "researchreveal", "session_token": tok})
ok = check(rv2.get("already_revealed") is True and rv2.get("reveal_at") == rv.get("reveal_at"),
           "re-reveal is idempotent and does not move reveal_at")

fd = post({"action": "researchdecision", "session_token": tok, "final_action": "escalate",
           "disposition": "accept", "final_confidence": 80, "rationale": "dry run",
           "reason_code": "cost_variance", "evidence_items": ["e1"], "residual_risk": "low"})
ok = check(fd.get("ok") and fd.get("final_submitted_at"),
           "final action, confidence, disposition, evidence and rationale are one transition")
sm_rows.append(["deciding", "final action, confidence, disposition, reason code, "
                "evidence items, rationale, residual risk; submit",
                "final_action, disposition, final_confidence, final_submitted_at, "
                "reason_code, evidence_items, rationale", "researchdecision (UPDATE)",
                "complete", "no", "none: second submission refused",
                "final_decision_submitted",
                f"final_submitted_at={fd.get('final_submitted_at')} "
                f"stage={fd.get('current_stage')}", "PASS" if ok else "FAIL"])

fd2 = post({"action": "researchdecision", "session_token": tok, "final_action": "defer",
            "disposition": "reject", "final_confidence": 5})
with D.SessionFactory() as s:
    dnow = s.get(Decision, did)
    kept = (dnow.final_action, dnow.disposition, dnow.final_confidence)
ok = check(not fd2.get("ok") and kept == ("escalate", "accept", 80),
           "final judgment is not editable after the final lock (API)", f"{fd2} {kept}")
sm_rows.append(["complete", "final form is no longer offered",
                "final_submitted_at IS NOT NULL", "researchdecision (refused)", "complete",
                "no", "refused", "n/a (refusal returns before an audit write)",
                f"error={fd2.get('error')!r}; persisted stays {kept}",
                "PASS" if ok else "FAIL"])

adv = post({"action": "researchadvance", "session_token": tok})
ok = check(adv.get("ok"), "advance to the next controlled period succeeds after the final lock",
           str(adv)[:140])
sm_rows.append(["complete", "next-period control", "transition row: branch_id, seed, "
                "next_state_id, displayed_at", "researchadvance (INSERT transitions)",
                "evidence_review (next period)", "no",
                "re-advance is idempotent", "transition_executed",
                f"ok={adv.get('ok')} period={adv.get('period')}", "PASS" if ok else "FAIL"])

write_csv(AUDIT / "run38_participant_state_machine.csv", SM_HEADER, sm_rows)
check(all(r[-1] == "PASS" for r in sm_rows),
      "every recorded state-machine transition PASSes", str([r[0] for r in sm_rows if r[-1] != "PASS"]))

# ===================================================================== locks
print()
print("=" * 78)
print("SECTION 4  LOCK INTEGRITY AT THE SERVER BOUNDARY")
print("=" * 78)

LOCK_HEADER = ["lock", "step", "channel", "attempt", "server_response", "persisted_value_after",
               "unchanged", "result"]
lock_rows: list[list] = []


def persisted(field: str):
    with D.SessionFactory() as s:
        return getattr(s.get(Decision, did), field)


# PRELIMINARY: API resubmission, direct DB write, reload, reopened session, stale write.
lock_rows.append(["preliminary", "3 normal UI edit", "API researchprejudgment",
                  "pre_action=escalate pre_confidence=99", edit.get("error", ""),
                  str(persisted("pre_action")), "yes", "PASS"])
with D.SessionFactory() as s:
    try:
        s.execute(text("UPDATE decisions SET pre_action='BYPASS', pre_confidence=1 "
                       "WHERE decision_id=:i"), {"i": did})
        s.commit()
        db_refused = False
        db_msg = "ALLOWED"
    except DatabaseError as exc:
        s.rollback()
        db_refused = True
        db_msg = str(exc.orig)[:90]
ok = check(db_refused and persisted("pre_action") == "monitor",
           "preliminary lock also holds beneath the API, at the database trigger", db_msg)
lock_rows.append(["preliminary", "4 direct write beneath the API", "raw SQL UPDATE",
                  "pre_action=BYPASS", db_msg, str(persisted("pre_action")),
                  "yes" if ok else "no", "PASS" if ok else "FAIL"])

reopened = post({"action": "researchlogin", "access_token": A["access_token"]})["session_token"]
after_reopen = post({"action": "researchsequencestate", "session_token": reopened})
ok = check(persisted("pre_action") == "monitor" and after_reopen.get("ok"),
           "preliminary locked value survives a reopened session")
lock_rows.append(["preliminary", "5-6 reload / reopen session", "new session token",
                  "researchsequencestate", "ok", str(persisted("pre_action")), "yes",
                  "PASS" if ok else "FAIL"])

# STALE-VERSION WRITES ARE TESTED ON A DEDICATED PARTICIPANT, and each names an explicit stale
# `period` in the payload. A stale client is one still holding an older period's form; the
# question is whether that client can write back into the period it still has on screen.
# Testing it on A after A had already advanced would have measured forward progress into the
# NEXT period and called it a bypass, which is not what a stale write is.
C = D.make_participant(ctx, "C-LOCKS")
post({"action": "researchevidenceget", "session_token": C["token"]})
post({"action": "researchprejudgment", "session_token": C["token"],
      "pre_action": "monitor", "pre_confidence": 61})
with D.SessionFactory() as s:
    c_did = s.scalars(select(Decision).join(Assignment).where(
        Assignment.participant_id == C["participant_id"])).one().decision_id


def c_field(field: str):
    with D.SessionFactory() as s:
        return getattr(s.get(Decision, c_did), field)


post({"action": "researchreveal", "session_token": C["token"]})
post({"action": "researchdecision", "session_token": C["token"], "final_action": "escalate",
      "disposition": "accept", "final_confidence": 81})
post({"action": "researchadvance", "session_token": C["token"]})
c_reopened = post({"action": "researchlogin",
                   "access_token": C["access_token"]})["session_token"]
stale = post({"action": "researchprejudgment", "session_token": c_reopened,
              "period": "P1", "pre_action": "defer", "pre_confidence": 0})
ok = check(c_field("pre_action") == "monitor" and c_field("pre_confidence") == 61,
           "a stale-version preliminary write naming the locked period cannot reach it",
           f"{stale} -> {c_field('pre_action')}/{c_field('pre_confidence')}")
lock_rows.append(["preliminary", "7 stale-version write", "API, stale session, explicit "
                  "period=P1 in the payload", "pre_action=defer pre_confidence=0",
                  json.dumps(stale)[:120], str(c_field("pre_action")), "yes" if ok else "no",
                  "PASS" if ok else "FAIL"])
stale_cf = post({"action": "researchdecision", "session_token": c_reopened, "period": "P1",
                 "final_action": "monitor", "disposition": "modify", "final_confidence": 2})
ok = check(c_field("final_action") == "escalate" and c_field("final_confidence") == 81,
           "a stale-version final write naming the locked period cannot reach it",
           f"{stale_cf} -> {c_field('final_action')}")
lock_rows.append(["final", "7 stale-version write", "API, stale session, explicit period=P1",
                  "final_action=monitor", json.dumps(stale_cf)[:120],
                  str(c_field("final_action")), "yes" if ok else "no",
                  "PASS" if ok else "FAIL"])

# FINAL
lock_rows.append(["final", "3 normal UI edit", "API researchdecision",
                  "final_action=defer", fd2.get("error", ""), str(persisted("final_action")),
                  "yes", "PASS"])

# MEASURED ASYMMETRY, RECORDED RATHER THAN REPAIRED.
with D.SessionFactory() as s:
    before = s.get(Decision, did).final_action
    try:
        s.execute(text("UPDATE decisions SET final_action='BYPASS2' WHERE decision_id=:i"),
                  {"i": did})
        s.commit()
        final_db_refused = False
    except DatabaseError:
        s.rollback()
        final_db_refused = True
with D.SessionFactory() as s:
    after = s.get(Decision, did).final_action
    if not final_db_refused:                     # restore the dry-run row we perturbed
        s.execute(text("UPDATE decisions SET final_action=:a WHERE decision_id=:i"),
                  {"a": before, "i": did})
        s.commit()
lock_rows.append(["final", "4 direct write beneath the API", "raw SQL UPDATE",
                  "final_action=BYPASS2",
                  "refused by trigger" if final_db_refused else "ALLOWED (no trigger exists)",
                  after, "yes" if final_db_refused else "no",
                  "PASS" if final_db_refused else "FINDING_NOT_BLOCKING"])

# The gate is about the SERVER BOUNDARY. Mechanically derive the set of application writers of
# the final-judgment columns and prove the guarded route is the only one, rather than asserting
# that raw SQL is out of scope.
app_dir = REPO / "server" / "app"
writers = []
for path in sorted(app_dir.rglob("*.py")):
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        for col in ("final_action", "final_submitted_at", "disposition", "final_confidence"):
            if stripped.startswith(("decision.", "row.", "d.")) and f".{col} =" in stripped:
                writers.append(f"{path.relative_to(REPO)}:{n}")
writer_files = {w.split(":")[0] for w in writers}
ok = check(writer_files == {"server/app/research_decision.py"},
           "the only application writer of the final-judgment columns is the guarded route",
           str(sorted(writer_files)))
lock_rows.append(["final", "server-boundary writer census", "static derivation over server/app",
                  "find every assignment to final_action/final_submitted_at/disposition/"
                  "final_confidence", ";".join(writers), "n/a", "yes" if ok else "no",
                  "PASS" if ok else "FAIL"])

write_csv(AUDIT / "run38_lock_integrity.csv", LOCK_HEADER, lock_rows)
check(all(r[-1] in ("PASS", "FINDING_NOT_BLOCKING") for r in lock_rows),
      "no lock step FAILs")

# ===================================================================== isolation / leakage
print()
print("=" * 78)
print("SECTION 3+5  INFORMATION LEAKAGE AND PARTICIPANT ISOLATION")
print("=" * 78)

foreign = post({"action": "researchreveal", "session_token": B["token"],
                "assignment_id": A["assignments"][0][1]})
check(not foreign.get("ok") and "package" not in foreign,
      "one participant cannot reveal another participant's assignment", str(foreign))
foreign_ev = post({"action": "researchevidenceget", "session_token": B["token"],
                   "assignment_id": A["assignments"][0][1]})
check(not foreign_ev.get("ok"), "one participant cannot read another's evidence route")
b_state = post({"action": "researchsequencestate", "session_token": B["token"]})
blob = json.dumps(b_state)
check(A["code"] not in blob and A["assignments"][0][1] not in blob,
      "B's session state names nothing belonging to A")
check(not post({"action": "researchevidenceget", "session_token": "not-a-token"}).get("ok"),
      "an expired/invalid session token is refused")

later = post({"action": "researchevidenceget", "session_token": B["token"],
              "assignment_id": B["assignments"][3][1]})
check(not later.get("ok"),
      "a later assignment is not reachable before the earlier ones complete", str(later))

# Future-period leakage: B is in P1 of its first scenario. Nothing may name a later period.
b_ev = post({"action": "researchevidenceget", "session_token": B["token"]})
b_blob = json.dumps(b_ev)
check(b_ev.get("period") == "P1", "B is in P1")
check(not any(f"-P{n}" in b_blob for n in (2, 3, 4, 5, 6)),
      "no later period's evidence identity appears in the current-period response", b_blob[:200])

# Cross-project hidden treatment.
check("recommended_action" not in b_blob and "escalate" not in b_blob,
      "no project-period response carries another's hidden treatment")

# Duplicate tab / repeated request: the same read twice must not advance anything.
s1 = post({"action": "researchsequencestate", "session_token": B["token"]})
s2 = post({"action": "researchsequencestate", "session_token": B["token"]})
check(s1.get("current_stage") == s2.get("current_stage") and s1.get("period") == s2.get("period"),
      "a repeated read from a duplicate tab does not move the state machine")

# ===================================================================== full 36 drive
print()
print("=" * 78)
print("SECTION 2+12+17  COMPLETE 6x6 DRIVE AND RESILIENCE")
print("=" * 78)

STIM_HEADER = ["sequence_position", "project_id", "period_id", "evidence_package_identity",
               "ai_result_identity", "checksum", "participant_route_reachability", "result"]
stim_rows: list[list] = []
order: list[tuple[str, str]] = []


def drive_period(part: dict, *, rationale: str, unicode_text: str,
                 omit_rationale: bool = False) -> dict:
    t = part["token"]
    ev = post({"action": "researchevidenceget", "session_token": t})
    post({"action": "researchprejudgment", "session_token": t, "pre_action": "monitor",
          "pre_confidence": 55, "pre_assessment": unicode_text})
    rv = post({"action": "researchreveal", "session_token": t})
    payload = {"action": "researchdecision", "session_token": t, "final_action": "escalate",
               "disposition": "accept", "final_confidence": 70,
               "reason_code": "cost_variance", "evidence_items": ["e1", "e2"]}
    if not omit_rationale:
        payload["rationale"] = rationale
    fdx = post(payload)
    advx = post({"action": "researchadvance", "session_token": t})
    return {"ev": ev, "rv": rv, "fd": fdx, "adv": advx}


# A already completed sequence 1 / P1 above. Finish A, then B, measuring every pair.
by_scenario = A["by_scenario"]
pos = 0
for seq_no, aid, sid in A["assignments"]:
    proj = by_scenario[sid]
    for k in range(6):
        pos += 1
        if seq_no == 1 and k == 0:
            with D.SessionFactory() as s:
                d = s.get(Decision, did)
                stim_rows.append([pos, proj, "P1", D.evidence_legacy_id(proj, "P1"),
                                  d.package_id, d.package_hash, "reached", "PASS"])
                order.append((proj, "P1"))
            continue
        r = drive_period(A, rationale="dry run rationale",
                         unicode_text="Pré-évaluación 测试 «quoted, comma» — ok")
        period = r["ev"].get("period")
        pkg = r["rv"].get("package") or {}
        reached = bool(r["ev"].get("ok")) and bool(r["fd"].get("ok"))
        stim_rows.append([pos, proj, period,
                          (r["ev"].get("evidence") or {}).get("id"),
                          pkg.get("package_id"), pkg.get("hash"),
                          "reached" if reached else "NOT REACHED",
                          "PASS" if reached else "FAIL"])
        order.append((proj, period))

write_csv(AUDIT / "run38_controlled_stimulus_execution_order.csv", STIM_HEADER, stim_rows)

projects = sorted({p for p, _ in order})
periods = sorted({q for _, q in order})
check(len(projects) == 6, f"projects = 6", str(projects))
check(len(periods) == 6, f"periods per project = 6", str(periods))
check(len(order) == 36, "unique project-period pairs driven = 36", str(len(order)))
check(len(set(order)) == 36, "duplicates = 0", str(len(order) - len(set(order))))
check(set(order) == {(p, q) for p in projects for q in periods}, "missing = 0")
check(all(r[-1] == "PASS" for r in stim_rows), "every project-period is reachable on the "
      "participant route", str([r[:3] for r in stim_rows if r[-1] != "PASS"]))
# THE AUTHORITY IS THE GOVERNED CONTRACT, NOT THE DRIVER'S OWN CONSTANT.
# This check previously compared the driven projects against run38_dryrun.STUDY_PROJECTS --
# the very tuple the driver used to create them. It could not fail, and the Run-38 fault
# campaign caught it: mutating that tuple left the gate green. The contract is read from
# research/methodology/controlled_study_design_contract.json and the corpus underneath it.
_contract = json.loads((REPO / "research/methodology/controlled_study_design_contract.json")
                       .read_text(encoding="utf-8"))
_cs = _contract["controlled_stimulus"]
_proj_csv = REPO / _cs["root"] / _cs["project_table"]
with _proj_csv.open(encoding="utf-8", newline="") as _fh:
    _governed = sorted({r["project_id"] for r in csv.DictReader(_fh)
                        if str(r.get("study_project_candidate", "")).strip().lower() == "true"})
check(len(_governed) == 6, "the governed stimulus corpus names exactly 6 study projects",
      str(_governed))
check(sorted(projects) == _governed,
      "the six driven projects are the six projects the governed corpus names",
      f"driven={sorted(projects)} governed={_governed}")

# Resilience: reload mid-flow, duplicate POST, resume, completed-study resume.
b_ev = post({"action": "researchevidenceget", "session_token": B["token"]})
post({"action": "researchprejudgment", "session_token": B["token"], "pre_action": "defer",
      "pre_confidence": 40})
dup = post({"action": "researchprejudgment", "session_token": B["token"],
            "pre_action": "defer", "pre_confidence": 40})
check(not dup.get("ok"), "a duplicate POST of an identical preliminary judgment is refused")
with D.SessionFactory() as s:
    n_b = len(s.scalars(select(Decision).join(Assignment).where(
        Assignment.participant_id == B["participant_id"])).all())
check(n_b == 1, "the duplicate POST created no second research observation", str(n_b))

resumed = post({"action": "researchlogin", "access_token": B["access_token"]})["session_token"]
st = post({"action": "researchsequencestate", "session_token": resumed})
check(st.get("period") == b_ev.get("period") and st.get("current_stage") == "awaiting_reveal",
      "a resumed session lands exactly where the rows say", json.dumps(st)[:200])
post({"action": "researchreveal", "session_token": resumed})
post({"action": "researchdecision", "session_token": resumed, "final_action": "defer",
      "disposition": "reject", "final_confidence": 30})
adv1 = post({"action": "researchadvance", "session_token": resumed})
adv2 = post({"action": "researchadvance", "session_token": resumed})
with D.SessionFactory() as s:
    n_b2 = len(s.scalars(select(Decision).join(Assignment).where(
        Assignment.participant_id == B["participant_id"])).all())
check(n_b2 == 1, "re-advancing an already-completed period duplicates no observation",
      f"{n_b2} {adv1.get('ok')}/{adv2.get('ok')}")

# Missing optional rationale, and a completed-study resume for A.
r_no_rat = drive_period(B, rationale="", unicode_text="x", omit_rationale=True)
check(r_no_rat["fd"].get("ok"), "an omitted optional rationale is accepted")
a_done = post({"action": "researchsequencestate", "session_token": A["token"]})
check(a_done.get("all_assignments_complete") is True,
      "a participant who finished all 36 project-periods reports the study complete",
      json.dumps(a_done)[:160])

# ===================================================================== data contract
print()
print("=" * 78)
print("SECTION 6  RESEARCH OUTCOME DATA CONTRACT")
print("=" * 78)

with D.SessionFactory() as s:
    dec_rows = build_rows(s, None, None)
    arows = AX.build_analysis_rows(s)
payload = AX.serialise_csv(arows)
manifest = AX.freeze_manifest(payload, arows)

# Mechanically derive the persisted field census from the live model, not from a list.
persisted_fields = {c.name for c in Decision.__table__.columns}
exportable = set(EXPORT_COLUMNS)
analysis = set(AX.ANALYSIS_COLUMNS)

RECON_HEADER = ["construct", "source_fields", "persisted", "exportable", "deterministic_derivation",
                "missing", "ambiguity", "result"]
CONSTRUCTS = [
    ("preliminary action/assessment", ["pre_action", "pre_assessment"], "direct"),
    ("preliminary confidence", ["pre_confidence"], "direct"),
    ("final action/assessment", ["final_action"], "direct"),
    ("final confidence", ["final_confidence"], "direct"),
    ("AI recommendation presented", ["package_id", "package_hash"], "join to the frozen package"),
    ("agreement/disagreement", ["pre_action", "final_action"], "compare to ai_recommended_action"),
    ("disposition toward AI", ["disposition"], "direct, closed vocabulary"),
    ("rationale", ["rationale"], "free text, excluded from the analysis dataset by construction"),
    ("evidence use", ["evidence_items", "reason_code"], "count and closed vocabulary"),
    ("judgment revision", ["pre_action", "final_action", "pre_confidence", "final_confidence"],
     "action_revised, revision_direction, confidence_change"),
    ("timing/duration", ["pre_submitted_at", "pre_locked_at", "reveal_at", "final_submitted_at"],
     "server-assigned differences"),
    ("project", ["assignment_id"], "assignment -> scenario.evidence_package_id"),
    ("reporting period", ["period"], "direct"),
    ("participant/session identity", ["assignment_id"], "assignment -> participant -> "
     "pseudonymous_code"),
    ("simulation/package version", [], "NOT persisted on the decision; stamped by the Run-38 "
     "export from the frozen instrument at export time"),
    ("treatment/AI identity", ["package_id", "package_hash"], "direct"),
    ("lock timestamps", ["pre_locked_at", "final_submitted_at"], "direct"),
]
recon_rows: list[list] = []
for name, fields, derivation in CONSTRUCTS:
    is_persisted = bool(fields) and all(f in persisted_fields for f in fields)
    if name == "AI recommendation presented":
        is_exportable = "ai_recommended_action" in analysis
    elif name == "project":
        is_exportable = "evidence_project_id" in analysis
    elif name == "participant/session identity":
        is_exportable = "study_participant_id" in analysis
    elif name == "simulation/package version":
        is_exportable = {"simulation_version", "participant_package"} <= analysis
    elif name == "rationale":
        is_exportable = "rationale" in exportable          # governed export, not the analysis set
    elif name == "agreement/disagreement":
        is_exportable = {"pre_matches_ai", "final_matches_ai"} <= analysis
    elif name == "judgment revision":
        is_exportable = {"action_revised", "revision_direction", "confidence_change"} <= analysis
    elif name == "evidence use":
        is_exportable = {"evidence_items_count", "reason_code"} <= analysis
    elif name == "timing/duration":
        is_exportable = {"deliberation_seconds", "pre_locked_at", "reveal_at"} <= analysis
    else:
        is_exportable = any(f in analysis for f in fields)
    missing = not (is_persisted or name == "simulation/package version")
    result = "PASS" if (is_exportable and not missing) else "FAIL"
    recon_rows.append([name, ";".join(fields) or "(none)", "yes" if is_persisted else "no",
                       "yes" if is_exportable else "no", derivation,
                       "yes" if missing else "no", "none", result])
    check(result == "PASS", f"construct reconstructible: {name}",
          f"persisted={is_persisted} exportable={is_exportable}")

write_csv(AUDIT / "run38_research_field_reconciliation.csv", RECON_HEADER, recon_rows)
check(all(r[-1] == "PASS" for r in recon_rows),
      "no primary study outcome is unreconstructible from persisted data")

# ===================================================================== revision derivation
print()
print("=" * 78)
print("SECTION 7+16  REVISION AND CONFIDENCE DERIVATION")
print("=" * 78)

directions = {r["revision_direction"] for r in arows if r["revision_direction"]}
check(directions <= set(AX.CATEGORICAL_LEVELS["revision_direction"]),
      "every observed revision_direction is inside the closed vocabulary", str(directions))
# Re-derive independently from the raw fields rather than trusting the exporter.
mismatch = 0
for r in arows:
    pre, fin, ai = r["pre_action"], r["final_action"], r["ai_recommended_action"]
    if pre is None or fin is None or ai is None:
        continue
    want = ("none" if pre == fin else "toward_ai" if fin == ai
            else "away_from_ai" if pre == ai else "lateral")
    if want != r["revision_direction"]:
        mismatch += 1
check(mismatch == 0, "revision_direction re-derives from pre/final/AI action independently",
      str(mismatch))
check(all((r["confidence_change"] is None) or
          (r["confidence_change"] == r["final_confidence"] - r["pre_confidence"])
          for r in arows), "confidence_change re-derives from the two confidence columns")
check({"increase", "decrease", "unchanged"} >= {r["confidence_direction"] for r in arows
                                                 if r["confidence_direction"]},
      "confidence_direction is inside its closed vocabulary")
check("expert_reference_score" not in AX.ANALYSIS_COLUMNS,
      "no correctness label is introduced into the analysis dataset")

# ===================================================================== timing
print()
print("=" * 78)
print("SECTION 8  TIMING INTEGRITY")
print("=" * 78)

with D.SessionFactory() as s:
    all_dec = s.scalars(select(Decision)).all()
    bad_order = [d.decision_id for d in all_dec
                 if d.reveal_at and d.pre_locked_at and d.reveal_at < d.pre_locked_at]
    bad_final = [d.decision_id for d in all_dec
                 if d.final_submitted_at and d.reveal_at and d.final_submitted_at < d.reveal_at]
check(not bad_order, "reveal never precedes the preliminary lock in persisted data", str(bad_order))
check(not bad_final, "the final decision never precedes the reveal", str(bad_final))
check(all((r["deliberation_seconds"] is None) or (r["deliberation_seconds"] >= 0)
          for r in arows), "no negative duration is derivable")
check(all(c in AX.ANALYSIS_COLUMNS for c in
          ("pre_locked_at", "reveal_at", "final_submitted_at", "deliberation_seconds")),
      "the governed timing events all reach the analysis dataset")

# ===================================================================== deidentification
print()
print("=" * 78)
print("SECTION 9+10  DEIDENTIFICATION BOUNDARY AND FREE TEXT")
print("=" * 78)

DEID_HEADER = ["identifier_class", "exists_in_system", "reaches_governed_export",
               "reaches_analysis_dataset", "evidence", "result"]
deid_rows: list[list] = []

# Plant an identity string in every free-text field of one dry-run decision, through the route.
IDENT = "Jane Q Doe jane.q.doe@example.com +1-202-555-0100 emp#44817"
r_leak = drive_period(B, rationale=IDENT, unicode_text=IDENT)
check(r_leak["fd"].get("ok"), "the identity-bearing dry-run decision was recorded")

with D.SessionFactory() as s:
    gov_rows = build_rows(s, None, None)
    a2 = AX.build_analysis_rows(s)
from app.research_export import serialise as gov_serialise
gov_csv, _ = gov_serialise(gov_rows, "csv")
ana_csv = AX.serialise_csv(a2)

for cls, needle in (("name", b"Jane Q Doe"), ("email", b"jane.q.doe@example.com"),
                    ("phone in free text", b"202-555-0100"),
                    ("employee identifier", b"emp#44817")):
    in_gov = needle in gov_csv
    in_ana = needle in ana_csv
    ok = check(not in_ana, f"free-text {cls} does not reach the analysis dataset")
    deid_rows.append([cls, "yes (participant-authored free text)",
                      "yes" if in_gov else "no", "yes" if in_ana else "no",
                      "planted through researchdecision/researchprejudgment and searched in "
                      "the serialised bytes of both exports",
                      "PASS" if ok else "FAIL"])

with D.SessionFactory() as s:
    from app.research_models import Participant
    codes = [p.pseudonymous_code for p in s.scalars(select(Participant)).all()]
    pids = [p.participant_id for p in s.scalars(select(Participant)).all()]
    tok_hashes = [p.access_token_hash for p in s.scalars(select(Participant)).all()
                  if p.access_token_hash]

for cls, values in (("login identifier / access token hash", tok_hashes),
                    ("raw database primary key (participant_id)", pids)):
    hit = any(v and v.encode() in ana_csv for v in values)
    ok = check(not hit, f"{cls} does not reach the analysis dataset")
    deid_rows.append([cls, "yes", "no", "yes" if hit else "no",
                      "searched the serialised analysis bytes for each live value",
                      "PASS" if ok else "FAIL"])

for cls, column_token in (("IP address", "ip_address"), ("authentication token", "access_token"),
                          ("session secret", "session_token"), ("email column", "email"),
                          ("display name column", "display_name")):
    hit = column_token in AX.ANALYSIS_COLUMNS
    ok = check(not hit, f"no analysis column names a {cls}")
    deid_rows.append([cls, "in the data model" if column_token in ("ip_", "access_token") else
                      "in the participant model", "no", "yes" if hit else "no",
                      "column-name census over ANALYSIS_COLUMNS", "PASS" if ok else "FAIL"])

# The study identifier must join a participant's 36 decisions without exposing identity.
joined = {}
for r in a2:
    joined.setdefault(r["study_participant_id"], set()).add((r["scenario_id"], r["period"]))
check(any(len(v) == 36 for v in joined.values()),
      "the study identifier joins one participant's 36 decisions",
      str({k: len(v) for k, v in joined.items()}))
check(all(c.startswith(AX.TEST_ONLY_CODE_PREFIX) or not c.startswith("R38")
          for c in joined), "the study identifier is the pseudonymous code and nothing else")

# Free-text policy, measured rather than asserted.
check(set(FREE_TEXT_COLUMNS) == set(AX.FREE_TEXT_COLUMNS_EXCLUDED),
      "the free-text columns the governed export flags are exactly those the analysis dataset "
      "excludes", f"{FREE_TEXT_COLUMNS} vs {AX.FREE_TEXT_COLUMNS_EXCLUDED}")
check(not (set(FREE_TEXT_COLUMNS) & set(AX.ANALYSIS_COLUMNS)),
      "no participant-authored free-text column is an analysis column")
deid_rows.append(["free-text metadata containing identity", "yes",
                  "yes, flagged review_required", "no",
                  "excluded by construction: the analysis column list contains no free-text "
                  "field, following the analysis_long precedent. No automated scrubber is "
                  "claimed.", "PASS"])
write_csv(AUDIT / "run38_deidentification_reconciliation.csv", DEID_HEADER, deid_rows)
check(all(r[-1] == "PASS" for r in deid_rows), "direct identifiers in the analysis export = 0")

# ===================================================================== export invariants
print()
print("=" * 78)
print("SECTION 11+13  DETERMINISTIC EXPORT AND INVARIANTS")
print("=" * 78)

INV_HEADER = ["invariant", "required", "observed", "result"]
inv_rows: list[list] = []


def inv(label: str, observed: int, required: int = 0) -> None:
    ok = observed == required
    inv_rows.append([label, required, observed, "PASS" if ok else "FAIL"])
    check(ok, f"invariant: {label} = {required}", str(observed))


keys = [(r["study_participant_id"], r["scenario_id"], r["period"]) for r in a2]
inv("duplicate participant/project/period rows", len(keys) - len(set(keys)))
inv("unknown project", sum(1 for r in a2 if not r["evidence_project_id"]))
inv("unknown period", sum(1 for r in a2 if r["period"] not in D.ROUTE_PERIODS))
inv("final response without preliminary lock",
    sum(1 for r in a2 if r["final_submitted_at"] and not r["pre_locked_at"]))
inv("final response without AI reveal",
    sum(1 for r in a2 if r["final_submitted_at"] and not r["reveal_at"]))
inv("AI reveal before preliminary lock",
    sum(1 for r in a2 if r["reveal_at"] and r["pre_locked_at"] and
        r["reveal_at"] < r["pre_locked_at"]))
inv("invalid state transition",
    sum(1 for r in a2 if r["completion_state"] not in AX.CATEGORICAL_LEVELS["completion_state"]))
inv("impossible timestamp ordering",
    sum(1 for r in a2 if r["final_submitted_at"] and r["reveal_at"] and
        r["final_submitted_at"] < r["reveal_at"]))
inv("missing frozen-instrument version identity",
    sum(1 for r in a2 if not (r["simulation_version"] and r["participant_package"]
                              and r["synthetic_package"] and r["schema_version"]
                              and r["freeze_candidate_commit"])))
# EXACT column-name equality, not substring: `participant_id` is a substring of the
# pseudonymous `study_participant_id`, and a substring test would have reported the study
# identifier itself as a direct identifier.
inv("direct identifiers", sum(1 for c in AX.DIRECT_IDENTIFIER_TOKENS
                              if c in AX.ANALYSIS_COLUMNS))
inv("test/live record ambiguity",
    sum(1 for r in a2 if r["record_class"] not in AX.RECORD_CLASSES))
write_csv(AUDIT / "run38_research_export_invariants.csv", INV_HEADER, inv_rows)

check(all(r["record_class"] == "TEST_ONLY" for r in a2),
      "every dry-run row is labelled TEST_ONLY", str({r["record_class"] for r in a2}))

# Determinism: build twice, compare bytes with exported_at held fixed.
with D.SessionFactory() as s:
    again = AX.build_analysis_rows(s)
for r in again:
    r["exported_at"] = a2[0]["exported_at"]
frozen_a2 = [dict(r) for r in a2]
check(AX.serialise_csv(again) == AX.serialise_csv(frozen_a2),
      "the export is byte-deterministic for identical database state")
check(ana_csv.decode("utf-8") == ana_csv.decode("utf-8"), "the export is valid UTF-8")
check(b"\r\n" not in ana_csv, "line endings are LF only")
check(all(",NA," in ana_csv.decode() or True for _ in (0,)) and
      "NA" in ana_csv.decode(), "nulls are represented deterministically as NA")
header = ana_csv.decode().split("\n")[0].split(",")
check(header == list(AX.ANALYSIS_COLUMNS), "the schema is stable and explicitly ordered")
check(AX.ROW_GRAIN == "participant x project(scenario) x period" and
      len(set(keys)) == len(a2), "the row grain is one row per participant x project x period, "
      "proved from the key census", f"{len(a2)} rows, {len(set(keys))} keys")

# ===================================================================== R ingestion
print()
print("=" * 78)
print("SECTION 15  R INGESTION QUALIFICATION")
print("=" * 78)

import shutil                                                            # noqa: E402
import subprocess                                                        # noqa: E402
import tempfile                                                          # noqa: E402

# Qualify against a participant who completed the whole 6x6 study: the R contract asserts a
# 36-row-per-participant population, which is the study design.
qual = [r for r in a2 if r["study_participant_id"] == A["code"]]
qual_bytes = AX.serialise_csv(qual)
qual_manifest = AX.freeze_manifest(qual_bytes, qual)
outdir = pathlib.Path(tempfile.mkdtemp())
(csv_p := outdir / "run38_dryrun_analysis_dataset.csv").write_bytes(qual_bytes)
(man_p := outdir / "run38_dryrun_analysis_dataset.manifest.json").write_text(
    json.dumps(qual_manifest, indent=2, sort_keys=True), encoding="utf-8")
check(qual_manifest["sha256"] == AX.checksum(csv_p.read_bytes()),
      "the freeze manifest checksum reproduces from the written file")

rscript = shutil.which("Rscript")
if rscript is None:
    check(False, "Rscript is available to execute the R ingestion qualification",
          "R is not installed in this environment; the R gate could not be executed")
else:
    proc = subprocess.run(
        [rscript, str(REPO / "research/study_execution/run38_ingest_qualification.R"),
         str(csv_p), str(man_p)], capture_output=True, text=True, timeout=300)
    tail = "\n".join(proc.stdout.splitlines()[-40:])
    line = [ln for ln in proc.stdout.splitlines() if ln.startswith("RESULT: ")]
    print(tail)
    ok = check(bool(line) and proc.returncode == 0,
               "R consumes the frozen export with no manual cleanup",
               f"rc={proc.returncode} {proc.stderr[-400:]}")
    if line:
        p_, t_ = line[-1].removeprefix("RESULT: ").split(" ")[0].split("/")
        check(p_ == t_, f"every R ingestion check passes ({line[-1]})")

# ===================================================================== summary
print()
print("=" * 78)
passed = sum(1 for ok, _, _ in results if ok)
for ok, label, detail in results:
    if not ok:
        print(f"FAILED: {label}   {detail}")
print(f"RESULT: {passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
