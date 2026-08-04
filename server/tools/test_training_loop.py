#!/usr/bin/env python3
"""
Training mode run 2: the loop. Determinism, the two clocks, the effect table, the normal
computation path, and run 1's isolation after everything this run added.

Run (from server/):

    PYTHONIOENCODING=utf-8 DATABASE_URL=... SESSION_SECRET=... python tools/test_training_loop.py

The brief's required coverage, each proven able to fail by fault injection (see the report):
same decision, same conditions, same state change; a deferral runs the notice clock and can
close it; the notice period matches the contract form and changes when the form changes; a
training project's signals compute through the normal path; and training isolation from run 1
still holds now that training ComputedResult rows actually exist.
"""
from __future__ import annotations

import copy
import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import ComputedResult, Participant, TrainingRun  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_export import build_module_results_rows  # noqa: E402
from app import training_engine as eng  # noqa: E402

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
print("SETUP")
print("=" * 78)

ADMIN_TOKEN = "training-loop-admin"
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="LOOP-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN_TOKEN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN_TOKEN)
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN_TOKEN})["session_token"]


def make(code: str, account_type: str) -> tuple[str, str]:
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": code, "role": "Participant",
                    "account_type": account_type})
    assert created.get("ok"), created
    tok = post({"action": "researchlogin",
                "access_token": created["access_token"]})["session_token"]
    return created["participant_id"], tok


ops_id, ops = make("LOOP-OPS", "operational")
ops2_id, ops2 = make("LOOP-OPS-2", "operational")
res_id, res = make("LOOP-RES", "research")
check(bool(ops and ops2 and res), "three accounts established")

# A REAL project with a live ComputedResult, inserted BEFORE any training run exists and dated
# before every training cutoff. This is what makes the portfolio-boundary checks below able to
# fail: without a real vector in the table, "training portfolios exclude real projects" would
# pass whether or not the filter exists.
with Session() as s:
    real = Project(legacy_id="REAL-LOOP", doc={"projectId": "REAL-LOOP", "sector": "test"},
                   is_training=False)
    s.add(real)
    s.flush()
    real_project_uuid = real.id
    import sqlalchemy as sa
    s.execute(sa.text(
        "INSERT INTO computed_results (result_id, project_id, period, signal_inputs, "
        "module_results, simulation_version, seed, period_cutoff) VALUES "
        "(:rid, :pid, 1, :si, :mods, 'v1', 'seed', '2026-01-01')"
    ), {"rid": "REALLOOPRES1", "pid": str(real_project_uuid),
        "si": json.dumps({"cpi": 0.95, "spi": 0.97, "docRiskScore": 0.2,
                          "actualPctComplete": 40}),
        "mods": json.dumps([{"module_id": "A1", "group": "A", "status_color": "green"}])})
    s.commit()

print()
print("=" * 78)
print("GUARANTEE 1: determinism — same decision, same conditions, same state change")
print("=" * 78)

# The ENGINE itself, the logic the application runs — not a copy of it.
s0 = eng.initial_state("A201-2017", 12_000_000.0, "exacting")
a = eng.advance(copy.deepcopy(s0), "escalate")
b = eng.advance(copy.deepcopy(s0), "escalate")
check(json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True),
      "advance() twice from the same state and decision is byte-identical")
check(json.dumps(s0, sort_keys=True) ==
      json.dumps(eng.initial_state("A201-2017", 12_000_000.0, "exacting"), sort_keys=True),
      "initial_state is itself deterministic")

# And over real HTTP: two accounts, identical runs, identical decisions, identical states.
r1 = post({"action": "trainingstart", "session_token": ops,
           "contract_form": "A201-2017", "conditions": "exacting",
           "contract_value": 12_000_000})
r2 = post({"action": "trainingstart", "session_token": ops2,
           "contract_form": "A201-2017", "conditions": "exacting",
           "contract_value": 12_000_000})
check(r1.get("ok") is True and r2.get("ok") is True, "two identical runs started",
      str(r1)[:120])
d1 = post({"action": "trainingdecision", "session_token": ops,
           "run_id": r1["run_id"], "decision": "escalate"})
d2 = post({"action": "trainingdecision", "session_token": ops2,
           "run_id": r2["run_id"], "decision": "escalate"})
check(json.dumps(d1["state"], sort_keys=True) == json.dumps(d2["state"], sort_keys=True),
      "two trainees making the same decision under the same conditions reach byte-identical "
      "state")

print()
print("=" * 78)
print("GUARANTEE 2: the two clocks — a deferral runs the notice clock and can close it")
print("=" * 78)

s0 = eng.initial_state("A201-2017", 12_000_000.0, "exacting")
check(s0["dispute"]["days_since_event"] == 10,
      "at the first decision the event is 10 days old (event day 10, decision day 20)")
n0 = eng.notice_position(s0)
check(n0["days_remaining"] == 11 and not n0["expired"],
      "A201: 11 of 21 days remain at the first decision", str(n0))

s1 = eng.advance(copy.deepcopy(s0), "defer")
check(s1["period"] == 2 and s1["dispute"]["days_since_event"] == 40,
      "ONE deferral advances ONE period but 30 clock days: the two axes do not blur",
      str(s1["dispute"]))
n1 = eng.notice_position(s1)
check(n1["expired"] is True, "and the 21 day window is now closed", str(n1))
check(s1["dispute"]["entitlement"] == "lost",
      "the deferral that ran the clock out marks entitlement lost", s1["dispute"]["entitlement"])
s2 = eng.advance(copy.deepcopy(s1), "escalate")
check(s2["dispute"]["entitlement"] == "lost" and s2["dispute"]["pending_recovery"] is None,
      "escalating after the window closed recovers nothing", str(s2["dispute"]))

print()
print("=" * 78)
print("GUARANTEE 3: the notice period matches the form and changes when the form changes")
print("=" * 78)

for form, days in (("A201-2017", 21), ("ConsensusDocs 200", 14)):
    n = eng.notice_position(eng.initial_state(form, 12_000_000.0, "exacting"))
    check(n["kind"] == "notice_bar" and n["window_days"] == days,
          f"{form}: a {days} day notice bar, per training_us_contract_regimes.md", str(n))
check(eng.notice_position(eng.initial_state("ConsensusDocs 200", 12_000_000.0, "exacting"))
      ["days_remaining"] == 4,
      "ConsensusDocs at the first decision: 4 days remain where A201 had 11 — the form changed "
      "the clock")
nf = eng.notice_position(eng.initial_state("Federal FAR", 12_000_000.0, "exacting"))
check(nf["kind"] == "cost_lookback" and nf["lookback_days"] == 20,
      "Federal FAR: no notice bar at all, a 20 day cost lookback instead", str(nf))
far1 = eng.advance(eng.initial_state("Federal FAR", 12_000_000.0, "exacting"), "defer")
nfar = eng.notice_position(far1)
check(nfar["expired"] is False and nfar["recoverable_fraction"] == 0.5,
      "FAR after one deferral: nothing is time barred, but only 20 of 40 days of cost is "
      "recoverable", str(nfar))
far2 = eng.advance(far1, "escalate")
# Run 4: a deferred federal claim GROWS (180,000 plus 0.25 percent of value = 210,000), and
# the lookback then halves what notice can reach. Both mechanics bite the same deferral.
check(far2["dispute"]["entitlement"] == "preserved"
      and far2["dispute"]["pending_recovery"] == 105_000.0,
      "escalating under FAR after a deferral preserves entitlement at half the GROWN claim "
      "(210,000 after growth, 105,000 recoverable)", str(far2["dispute"]))
check(far1["dispute"]["entitlement"] == "undecided",
      "and the FAR deferral did NOT mark entitlement lost, unlike A201",
      far1["dispute"]["entitlement"])

print()
print("=" * 78)
print("GUARANTEE 4: the effect table, decision by decision")
print("=" * 78)

cv = 12_000_000.0
s0 = eng.initial_state("A201-2017", cv, "exacting")

esc_ = eng.advance(copy.deepcopy(s0), "escalate")
# Run 3 correction 2: the flat 8 became a curve, base 4 plus 2 per full period left open.
# An immediate escalation is the cheap end of it.
check(esc_["float_consumed_days"] == 4, "escalate (exacting, immediately): float minus 4 days",
      str(esc_["float_consumed_days"]))
check(esc_["owner_credibility"] == 2, "escalate: owner credibility minus 1",
      str(esc_["owner_credibility"]))
check(esc_["contingency_remaining"] == s0["contingency_remaining"],
      "escalate: contingency untouched")
check(esc_["dispute"]["entitlement"] == "preserved"
      and esc_["dispute"]["pending_recovery"] == 180_000.0,
      "escalate in window: entitlement preserved, full 1.5 percent impact recoverable",
      str(esc_["dispute"]))
after = eng.advance(copy.deepcopy(esc_), "defer")
check(after["bac"] == cv + 180_000.0 and after["change_order_count"] == 1
      and after["dispute"]["status"] == "resolved",
      "the preserved escalation books a change order the NEXT period: contract value up, "
      "change order count 1", f"bac={after['bac']}")

ab = eng.advance(copy.deepcopy(s0), "absorb")
check(ab["contingency_remaining"] == round(s0["contingency_remaining"] - 180_000.0, 2),
      "absorb: contingency minus the impact cost", str(ab["contingency_remaining"]))
# Run 3 correction 3: credibility is asymmetric — one concession earns a progress step,
# not a point. The step itself is asserted in test_training_events.py.
check(ab["owner_credibility"] == 3 and ab["credibility_progress"] == 1,
      "absorb: one concession earns one progress step toward a credibility point",
      f"cred={ab['owner_credibility']} progress={ab['credibility_progress']}")
check(ab["float_consumed_days"] == 0, "absorb: float untouched")
check(ab["dispute"]["status"] == "absorbed" and ab["dispute"]["entitlement"] == "waived",
      "absorb: dispute closed, entitlement waived", str(ab["dispute"]))

df = eng.advance(copy.deepcopy(s0), "defer")
check(df["float_consumed_days"] == 3, "defer (exacting): float minus 3 days of drift",
      str(df["float_consumed_days"]))
check(df["owner_credibility"] == 3, "defer: credibility unchanged")
check(df["ev"] < df["pv"], "defer: a disturbed period earns less than planned, so schedule "
      "performance falls", f"ev={df['ev']} pv={df['pv']}")

st = eng.advance(eng.initial_state("A201-2017", cv, "steady"), "escalate")
check(st["float_consumed_days"] == 3,
      "the same decision under STEADY conditions costs 3 float days, not 4 — conditions "
      "modulate, decisions do not randomise", str(st["float_consumed_days"]))

# Liquidated damages follow float mechanically. Drift applies only while the dispute is OPEN,
# so the exhausting sequence is defer, defer, THEN escalate: 3 + 3 + (4 + 2 per period open,
# here 8) = 14 against 12 — under run 3's curve the same procrastinate-then-panic run still
# lands at 14 days, arriving with the notice window already spent.
over = eng.advance(eng.advance(eng.advance(copy.deepcopy(s0), "defer"), "defer"), "escalate")
check(over["float_consumed_days"] == 14 and over["liquidated_damages_exposure"] == 8_000.0,
      "float exhausted puts liquidated damages in play: 2 days over at the standard facility "
      "rate of 4,000 per day",
      f"consumed={over['float_consumed_days']} ld={over['liquidated_damages_exposure']}")
check(over["dispute"]["entitlement"] == "lost",
      "and that same sequence arrives with the window spent: liquidated damages exposure AND "
      "no recovery, the compounding the chain describes")
still4 = eng.advance(copy.deepcopy(esc_), "defer")
check(still4["float_consumed_days"] == 4,
      "after escalation the dispute is no longer open, so deferral drift stops: drift is a "
      "property of the UNMANAGED change, not of time itself",
      str(still4["float_consumed_days"]))
# Run 3 correction 4: the rate follows the facility. The default facility is standard
# (0.035 percent); critical carries the top of the band, which is what the old flat rate was.
check(eng.derive_ld_per_day(12_000_000.0, "critical") == 6_000.0
      and eng.derive_ld_per_day(50_000_000.0, "critical") == 25_000.0,
      "the liquidated damages derivation from contract value, at the top of the band")

print()
print("=" * 78)
print("GUARANTEE 5: training signals compute through the NORMAL path")
print("=" * 78)

with Session() as s:
    run_row = s.get(TrainingRun, r1["run_id"])
    project = s.get(Project, run_row.project_id)
    check(project.is_training is True, "the run's project is marked training at creation")
    rows = s.scalars(select(ComputedResult).where(
        ComputedResult.project_id == project.id).order_by(ComputedResult.period)).all()
    check(len(rows) == 2, "one ComputedResult row per generated period (1 and 2)",
          str([r.period for r in rows]))
    # Guarded, not indexed: with no rows this section must FAIL its checks and print the
    # RESULT line, never die on an IndexError that leaves no result at all. Fault F5 (period
    # generation severed from the normal path) crashed the first version of this file exactly
    # that way.
    p1 = rows[0] if rows else None
    if p1 is None:
        for label in ("the row carries module results and the simulation's own version stamp",
                      "source_documents is an empty list",
                      "docRiskScore abstains", "cpi and spi open at 1.0",
                      "the period fuses to a project status"):
            check(False, label, "no ComputedResult row exists at all")
    if p1 is not None:
        check(bool(p1.module_results) and bool(p1.simulation_version),
              "the row carries module results and the simulation's own version stamp — the "
              "same analytical layer, not a training copy", p1.simulation_version)
        check(p1.source_documents == [],
              "source_documents is an empty list: no document produced this period, and no "
              "provenance was invented", str(p1.source_documents))
        si = p1.signal_inputs or {}
        check(si.get("docRiskScore") is None,
              "docRiskScore is None — a training run has no documents, so document risk "
              "ABSTAINS rather than being fabricated")
        check(si.get("cpi") == 1.0 and si.get("spi") == 1.0,
              "period one opens at cpi and spi 1.0 (20 days of clean progress)",
              f"cpi={si.get('cpi')} spi={si.get('spi')}")
        check(p1.project_status is not None,
              "and the period still fuses to a project status from what CAN compute",
              str(p1.project_status))

view = post({"action": "trainingstate", "session_token": ops, "run_id": r1["run_id"]})
check(view.get("ok") is True and view.get("brief", {}).get("claim_notice_days") == 21,
      "trainingstate returns the brief at any point in the run, not only at the start")
check((view.get("result") or {}).get("project_status") is not None,
      "and the platform's signals render from the stored row")

print()
print("=" * 78)
print("GUARANTEE 6: run 1's isolation still holds after everything this run added")
print("=" * 78)

with Session() as s:
    legacy_id = project.legacy_id
    module_rows = build_module_results_rows(s, None, None, None)
projects_seen = {r["project"] for r in module_rows}
check(legacy_id not in projects_seen,
      "the training run's ComputedResult rows do NOT appear in the project_health scope",
      str(sorted(p for p in projects_seen if p and p.startswith("TRN"))))

# The check can fail: unmark, look again, re-mark.
with Session() as s:
    p = s.scalars(select(Project).where(Project.legacy_id == legacy_id)).first()
    p.is_training = False
    s.commit()
with Session() as s:
    now_seen = {r["project"] for r in build_module_results_rows(s, None, None, None)}
check(legacy_id in now_seen,
      "unmarked, the same rows DO appear — the isolation filter is what excludes them")
with Session() as s:
    p = s.scalars(select(Project).where(Project.legacy_id == legacy_id)).first()
    p.is_training = True
    s.commit()

# The portfolio boundary, both directions, against the stored snapshots themselves.
ev_probe = post({"action": "adminscenariocreate", "session_token": admin,
                 "scenario_version": "LOOP-EVIDENCE-PROBE", "evidence_package_id": legacy_id})
check(ev_probe.get("ok") is False and "training" in (ev_probe.get("error") or "").lower(),
      "a training project still cannot become research evidence", str(ev_probe)[:120])

# THE PORTFOLIO BOUNDARY, BOTH DIRECTIONS, against the stored snapshot and the live logic.
#
# The snapshot stores portfolio statistics, not member ids, so the boundary is asserted through
# `insufficient_data`: the FIRST training run's period one was computed when that run was the
# ONLY training project, while REAL-LOOP's live vector (fixture, dated before every training
# cutoff) already sat in the table. With the boundary in place the training compute sees one
# vector — its own — and stores the insufficient shape. Were training portfolios ingesting real
# projects, it would have seen two and stored a full analysis, so this check fails exactly when
# the filter is removed.
with Session() as s:
    first_p1 = s.scalar(select(ComputedResult).where(
        ComputedResult.project_id == project.id, ComputedResult.period == 1))
    snap = (first_p1.portfolio_snapshot if first_p1 else None) or {}
    check(snap.get("insufficient_data") is True,
          "the first training compute saw ONLY its own vector, though a real project's live "
          "result predated it: real vectors do not enter a training portfolio",
          str(snap)[:140])

# The other direction is asserted against the LOGIC ITSELF, not a copy: run_and_store for the
# real project, minimal signalInputs. Three training results now exist with cutoffs after
# 2026-01-24; computing the real project at a later cutoff sees only real vectors (its own),
# so it must store the insufficient shape too. Were the boundary gone, the training vectors
# would make a portfolio of four.
from datetime import date as _date  # noqa: E402
from app.documents import run_and_store  # noqa: E402
from app.extraction_merge import SIGNAL_INPUT_KEYS  # noqa: E402
with Session() as s:
    real = s.scalars(select(Project).where(Project.legacy_id == "REAL-LOOP")).first()
    si_real = {k: None for k in SIGNAL_INPUT_KEYS}
    si_real.update({"bac": 1_000_000, "ev": 400_000, "ac": 420_000, "pv": 410_000,
                    "sources": {}, "cpi": 0.952, "spi": 0.976, "events": []})
    stored = run_and_store(s, real, 2, si_real, _date(2026, 6, 1), source_documents=[])
    real_snap = stored["row"].portfolio_snapshot or {}
    check(real_snap.get("insufficient_data") is True,
          "a REAL project's compute, run after three training results exist, still sees no "
          "training vector: the boundary holds in both directions",
          str(real_snap)[:140])
    s.rollback()

res_start = post({"action": "trainingstart", "session_token": res,
                  "contract_form": "A201-2017"})
check(res_start.get("ok") is False,
      "a research account is still refused trainingstart, whatever run 2 added",
      str(res_start)[:120])

other = post({"action": "trainingstate", "session_token": ops2, "run_id": r1["run_id"]})
check(other.get("ok") is False and "not found" in (other.get("error") or ""),
      "one trainee cannot read another's run, and absent is indistinguishable from refused",
      str(other)[:120])

print()
print("=" * 78)
print("GUARANTEE 7: the run completes and refuses further decisions")
print("=" * 78)

fast = post({"action": "trainingstart", "session_token": ops2,
             "contract_form": "Federal FAR", "conditions": "steady",
             "contract_value": 2_000_000})
check(fast.get("ok") is True, "a second run for the same account starts cleanly")
last = None
for _ in range(eng.PERIODS_TOTAL):
    # Run 3: period four brings a stop work order, during which the only decision is the
    # response. Decide from the server's own allowed list, deferring wherever permitted.
    current = post({"action": "trainingstate", "session_token": ops2,
                    "run_id": fast["run_id"]})
    allowed = current.get("allowed_decisions") or ["defer"]
    choice = "defer" if "defer" in allowed else allowed[0]
    last = post({"action": "trainingdecision", "session_token": ops2,
                 "run_id": fast["run_id"], "decision": choice})
check(last.get("ok") is True and last.get("status") == "complete",
      "ten decisions complete the run", str(last.get("status")))
refused = post({"action": "trainingdecision", "session_token": ops2,
                "run_id": fast["run_id"], "decision": "defer"})
check(refused.get("ok") is False and "complete" in (refused.get("error") or ""),
      "an eleventh decision is refused with the reason", str(refused)[:100])

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
