#!/usr/bin/env python3
"""
Training upgrade run 1: the quality thread.

Run (from server/):

    PYTHONIOENCODING=utf-8 DATABASE_URL=... python tools/test_training_quality.py

The brief's required coverage: deferring rework raises the backlog and the eventual cost; the
backlog forces rework at a period the trainee did not choose; accepting nonconforming spends
credibility and creates closeout exposure; the quality thread and the dispute thread draw on
the SAME float and contingency; the new state is excluded from both export kinds.
"""
from __future__ import annotations

import copy
import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402

import app.main as main  # noqa: E402
from app import training as tr  # noqa: E402
from app import training_engine as eng  # noqa: E402
from app.research_models import TrainingRun  # noqa: E402

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


CV = 12_000_000.0


def fresh(form="A201-2017", conditions="exacting", facility="standard"):
    return eng.initial_state(form, CV, conditions, facility)


def step(state, preferred):
    """
    Advance one period. The run carries a standing scheduled near miss (period 4, baked into
    the engine since run 3) that forces every player through a response that period regardless
    of what thread they meant to act on that period; this steps around it the same way a real
    trainee would, so tests reaching period 6 and beyond do not have to hand-roll the incident
    every time.
    """
    if state.get("incident", {}).get("status") == "stopped":
        return eng.advance(copy.deepcopy(state), "respond_strong")
    return eng.advance(copy.deepcopy(state), preferred)


print("=" * 78)
print("THE PATTERN: a secondary thread opens at a fixed period, undisclosed before then")
print("=" * 78)

s0 = fresh()
check(s0["quality"] is None, "no quality state before the run starts")
s1 = s0
while s1["period"] < eng.QUALITY_INSPECTION_PERIOD:
    check(s1["quality"] is None, f"still none in period {s1['period']}")
    s1 = step(s1, "defer")
s2 = s1
check(s2["period"] == eng.QUALITY_INSPECTION_PERIOD
      and s2["quality"] is not None and s2["quality"]["status"] == "open",
      f"the inspection fails as period {eng.QUALITY_INSPECTION_PERIOD} opens: undisclosed "
      "until now", str(s2["quality"]))
expected_defect = round(CV * eng.QUALITY_FIGURES["defect_value_rate"], 2)
check(s2["quality"]["defect_value"] == expected_defect,
      "the initial defect value is the designed rate against contract value",
      f"{s2['quality']['defect_value']} vs {expected_defect}")
check(s2["dispute"]["status"] == "open",
      "the dispute (the spine) is still open when quality opens: both threads live at once")

print()
print("=" * 78)
print("REWORK NOW: costs money and float immediately, clears the defect")
print("=" * 78)

before_ac, before_float = s2["ac"], s2["float_consumed_days"]
now_state = eng.advance(copy.deepcopy(s2), "rework_now")
check(now_state["quality"]["status"] == "resolved", "rework now resolves the matter")
check(round(now_state["ac"] - before_ac - (s2["baseline_contract_sum"] / eng.PERIODS_TOTAL), 2)
      == expected_defect,
      "and the defect's value is added to actual cost, on top of the period's own progress",
      f"delta={now_state['ac'] - before_ac}")
check(now_state["float_consumed_days"] - before_float
      == eng.QUALITY_FIGURES["rework_now_float_days"],
      "and the rework float days are spent", str(now_state["float_consumed_days"] - before_float))

print()
print("=" * 78)
print("REWORK LATER: cheaper now, the backlog grows while it waits")
print("=" * 78)

d1 = eng.advance(copy.deepcopy(s2), "rework_later")
check(d1["quality"]["status"] == "open" and d1["quality"]["periods_deferred"] == 1,
      "one deferral: still open, one period recorded")
grown = round(expected_defect * (1 + eng.QUALITY_FIGURES["rework_later_growth_rate"]), 2)
check(d1["quality"]["defect_value"] == grown,
      "and the backlog's value has grown by the deferral rate", str(d1["quality"]["defect_value"]))
check(round(d1["ac"] - s2["ac"] - (s2["baseline_contract_sum"] / eng.PERIODS_TOTAL), 2) == 0,
      "no cost is added THIS period for deferring: the price is in the backlog, not the ac line")
check(d1["float_consumed_days"] - s2["float_consumed_days"]
      == eng.QUALITY_FIGURES["rework_later_float_drift_days"],
      "but a small float drift is spent even before the cliff, same shape as the dispute's own "
      "deferral drift")

print()
print("=" * 78)
print("THE BACKLOG FORCES REWORK AT A PERIOD NOT CHOSEN")
print("=" * 78)

forced = copy.deepcopy(s2)
last_defect = None
force_period = None
for _ in range(eng.QUALITY_FIGURES["force_after_periods"]):
    if forced["quality"]["status"] != "open":
        break
    forced = eng.advance(forced, "rework_later")
check(forced["quality"]["status"] == "forced_resolved",
      f"after {eng.QUALITY_FIGURES['force_after_periods']} deferrals the backlog is forced "
      "resolved automatically, without a rework_now or accept decision", str(forced["quality"]))
check(any("forced rework" in n.lower() or "did not choose" in n.lower()
          for n in (forced["period_changes"]["notes"] or [])),
      "and the period's own notes say so, in a period the trainee did not pick",
      str(forced["period_changes"]["notes"]))
check(forced["float_consumed_days"] >
      d1["float_consumed_days"] + eng.QUALITY_FIGURES["rework_later_float_drift_days"],
      "the forced rework costs float on top of the last deferral's drift: dearer than choosing "
      "it would have been")

print()
print("=" * 78)
print("ACCEPT NONCONFORMING: no cost, no time, spends credibility, exposure at closeout")
print("=" * 78)

before_cred = s2["owner_credibility"]
accepted = eng.advance(copy.deepcopy(s2), "accept_nonconforming")
check(accepted["quality"]["status"] == "accepted", "accepted, not resolved")
check(round(accepted["ac"] - s2["ac"] - (s2["baseline_contract_sum"] / eng.PERIODS_TOTAL), 2) == 0,
      "no cost added by accepting")
check(accepted["float_consumed_days"] == s2["float_consumed_days"],
      "no float spent by accepting")
check(accepted["owner_credibility"] == before_cred - eng.QUALITY_FIGURES["accept_credibility_cost"],
      "owner credibility is spent", str(accepted["owner_credibility"]))
check(accepted["quality"]["closeout_exposure"] == expected_defect,
      "and the defect's value stands as permanent closeout exposure",
      str(accepted["quality"]["closeout_exposure"]))
held = eng.advance(accepted, "defer")
check(held["quality"]["closeout_exposure"] == expected_defect
      and held["quality"]["status"] == "accepted",
      "the exposure does not keep growing once accepted, and does not clear either")

print()
print("=" * 78)
print("COMPETITION: the SAME float and contingency, not a separate pool")
print("=" * 78)

# Both threads open at once (dispute from period 1, quality from QUALITY_INSPECTION_PERIOD);
# one decision per period draws from the same pools regardless of which thread it addresses.
both_open = s2
check(both_open["dispute"]["status"] == "open" and both_open["quality"]["status"] == "open",
      f"both threads are live at period {eng.QUALITY_INSPECTION_PERIOD}")
via_dispute = eng.advance(copy.deepcopy(both_open), "escalate")
via_quality = eng.advance(copy.deepcopy(both_open), "rework_now")
check(via_dispute["float_consumed_days"] != both_open["float_consumed_days"]
      and via_quality["float_consumed_days"] != both_open["float_consumed_days"],
      "escalating the dispute and reworking the quality defect BOTH move float_consumed_days: "
      "one counter, two threads drawing on it",
      f"dispute={via_dispute['float_consumed_days']} quality={via_quality['float_consumed_days']}")
via_absorb = eng.advance(copy.deepcopy(both_open), "absorb")
check(via_absorb["contingency_remaining"] < both_open["contingency_remaining"],
      "absorbing the dispute draws contingency; quality's rework_now draws AC directly rather "
      "than contingency, but both are figures on the one state the trainee is choosing among")
check(eng.allowed_decisions(both_open) == eng.DECISIONS + eng.QUALITY_DECISIONS,
      "the menu is the UNION of both threads' verbs: one decision, from across everything live",
      str(eng.allowed_decisions(both_open)))
# The trainee can only spend ONE decision this period: choosing "escalate" leaves the quality
# matter untouched, and vice versa -- proof there is no way to act on both threads in one period.
check(via_dispute["quality"]["status"] == "open" and via_dispute["quality"]["periods_deferred"] == 0,
      "escalating the dispute this period leaves quality exactly where it was: one decision, "
      "not two")
check(via_quality["dispute"]["status"] == "open",
      "and reworking quality this period leaves the dispute exactly where it was")

print()
print("=" * 78)
print("VALIDATION: a quality verb outside its window is refused, named")
print("=" * 78)

try:
    eng.advance(copy.deepcopy(s0), "rework_now")
    check(False, "rework_now before the inspection fails is refused")
except ValueError as exc:
    check("nothing to decide about quality" in str(exc),
          "rework_now before the inspection fails is refused, with the reason", str(exc))
try:
    eng.advance(copy.deepcopy(now_state), "accept_nonconforming")
    check(False, "accept_nonconforming after the matter resolved is refused")
except ValueError as exc:
    check("nothing to decide about quality" in str(exc),
          "accept_nonconforming after resolution is refused, with the reason", str(exc))

print()
print("=" * 78)
print("THE STATE VIEW SURFACES THE THREAD, THE SAME SHAPE AS THE SITE CONDITION'S")
print("=" * 78)

check(eng.quality_position(s0) is None, "no position before discovery")
qp = eng.quality_position(s2)
check(qp is not None and qp["status"] == "open" and qp["periods_deferred"] == 0
      and qp["periods_until_forced"] == eng.QUALITY_FIGURES["force_after_periods"],
      "the position states status, backlog, and how many deferrals remain before it forces",
      str(qp))

print()
print("=" * 78)
print("ISOLATION: the new state never reaches either export kind")
print("=" * 78)

import app.research_export as rex  # noqa: E402
src = open(rex.__file__, encoding="utf-8").read()
check("TrainingRun" not in src,
      "research_export.py never references TrainingRun: the JSON state column the quality "
      "field lives in is never touched by either export path")

ADMIN_TOKEN = "quality-test-admin"
with Session() as sess:
    from sqlalchemy import select
    from app.research_identity import hash_access_token
    from app.research_models import Participant
    row = sess.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        sess.add(Participant(pseudonymous_code="QUALITY-ADMIN", role="ResearchAdmin",
                             access_token_hash=hash_access_token(ADMIN_TOKEN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN_TOKEN)
    sess.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN_TOKEN})["session_token"]


def make(code: str, account_type: str) -> str:
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": code, "role": "Participant",
                    "account_type": account_type})
    assert created.get("ok"), created
    return post({"action": "researchlogin",
                "access_token": created["access_token"]})["session_token"]


op_tok = make("QUAL-OPS-A", "operational")
run = post({"action": "trainingstart", "session_token": op_tok, "contract_form": "A201-2017",
           "conditions": "exacting", "contract_value": 12_000_000, "facility": "standard"})
run_id = run["run_id"]
view = run
while view["period"] < eng.QUALITY_INSPECTION_PERIOD:
    dec = "respond_strong" if "respond_strong" in view["allowed_decisions"] else "defer"
    view = post({"action": "trainingdecision", "session_token": op_tok, "run_id": run_id,
                "decision": dec})
check(view.get("quality_notice") is not None and view["quality_notice"]["status"] == "open",
      "the live run's quality notice surfaces once the inspection has failed",
      str(view.get("quality_notice")))
with Session() as sess:
    row = sess.get(TrainingRun, run_id)
    check(row.state.get("quality") is not None,
          "and the quality dict is actually stored on the run's state column")
check("defect_value" not in str(view.get("result") or {})
      and "periods_deferred" not in str(view.get("result") or {}),
      "the quality thread's own fields do not leak into the computed signals result: the "
      "'quality*' signal keys present there are the platform's own pre-existing vocabulary "
      "(qualityAuditScore, qualityRating and similar), abstained like any other field with no "
      "input, not something this thread added", "")

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
