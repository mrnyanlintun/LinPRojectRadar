#!/usr/bin/env python3
"""
Training mode run 3: the four effect-table corrections, discrete events, and narration.

Run (from server/):

    PYTHONIOENCODING=utf-8 DATABASE_URL=... SESSION_SECRET=... python tools/test_training_events.py

The brief's required coverage: deferral costs something before the window closes; escalating
early costs less float than escalating late for the same position; credibility takes more than
one action to rebuild after being spent; the LD rate follows the brief condition; a stop work
order costs differently on a float-rich and a float-poor state from the same incident; and the
engine produces identical state transitions with narration disabled.
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
from app.research_models import Participant  # noqa: E402
from app import training as tr  # noqa: E402
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


CV = 12_000_000.0


def fresh(form="A201-2017", conditions="exacting", facility="standard"):
    return eng.initial_state(form, CV, conditions, facility)


print("=" * 78)
print("CORRECTION 1: deferral is not free, and its price is visible")
print("=" * 78)

s0 = fresh()
d = eng.advance(copy.deepcopy(s0), "defer")
check(d["float_consumed_days"] == 3 and d["ac"] > s0["ac"] + CV / 10,
      "one deferral with the dispute open costs 3 float days and cost drift, BEFORE any "
      "window closes", f"float={d['float_consumed_days']}")
pc = d["period_changes"]
check(pc is not None and pc["decision"] == "defer" and pc["float_days_spent"] == 3
      and pc["cost_added"] == round(CV * eng.DEFER_DRIFT_COST_RATE, 2),
      "and the drift is STATED in the period's figures (period_changes), not archaeology",
      str(pc))
check(any("price" in n.lower() or "drift" in n.lower() for n in pc["notes"]),
      "with a note a trainee can reason about", str(pc["notes"]))
closed = eng.advance(copy.deepcopy(s0), "absorb")
neutral = eng.advance(closed, "defer")
check(neutral["float_consumed_days"] == closed["float_consumed_days"]
      and neutral["period_changes"]["float_days_spent"] == 0,
      "deferring with the dispute CLOSED stays the neutral close of a period: drift is a "
      "property of the unmanaged change, not of time")

print()
print("=" * 78)
print("CORRECTION 2: escalating early costs less float than escalating late")
print("=" * 78)

early = eng.advance(copy.deepcopy(s0), "escalate")
check(early["float_consumed_days"] == 4,
      "immediate escalation (position open 10 days): 4 float days, the base of the curve",
      str(early["float_consumed_days"]))
one_late = eng.advance(eng.advance(copy.deepcopy(s0), "defer"), "escalate")
check(one_late["float_consumed_days"] - 3 == 6,
      "after one deferred period (open 40 days): 6 days for the escalation itself",
      str(one_late["float_consumed_days"]))
two_late = eng.advance(eng.advance(eng.advance(copy.deepcopy(s0), "defer"), "defer"),
                       "escalate")
check(two_late["float_consumed_days"] - 6 == 8,
      "after two (open 70 days): 8 days — the same position costs twice the float when "
      "recognised late", str(two_late["float_consumed_days"]))
check(eng.ESCALATE_FLOAT_CAP_DAYS == 12,
      "the curve is capped, so a very old position cannot cost more than 12 days")
steady_early = eng.advance(fresh(conditions="steady"), "escalate")
check(steady_early["float_consumed_days"] == 3,
      "steady conditions: base 3 — the curve's base is a profile figure",
      str(steady_early["float_consumed_days"]))

print()
print("=" * 78)
print("CORRECTION 3: credibility is asymmetric — slow to earn, quick to spend")
print("=" * 78)

a1 = eng.advance(copy.deepcopy(s0), "absorb")
check(a1["owner_credibility"] == 3 and a1["credibility_progress"] == 1,
      "ONE concession does not move credibility; it earns one progress step",
      f"cred={a1['owner_credibility']} progress={a1['credibility_progress']}")
esc = eng.advance(copy.deepcopy(s0), "escalate")
check(esc["owner_credibility"] == 2,
      "ONE escalation spends a whole point at once", str(esc["owner_credibility"]))
# A state carrying earn progress INTO an escalation of an open dispute cannot be produced by
# this run's single standing dispute (absorbing it closes it), so the reset property is
# exercised on the pure function directly with progress pre-set — a constructed input to a
# pure function, stated as such, not a fixture pretending to be an application route. The
# property matters now because run 4's events will create exactly this sequence.
carrying = copy.deepcopy(s0)
carrying["credibility_progress"] = 1
lost = eng.advance(carrying, "escalate")
check(lost["credibility_progress"] == 0,
      "an escalation destroys accumulated earn progress: rebuilding starts from zero",
      str(lost["credibility_progress"]))
check(eng.CRED_EARN_CONCESSIONS == 2,
      "earning a point takes two concessions where losing one takes a single escalation")

print()
print("=" * 78)
print("CORRECTION 4: the liquidated damages rate follows the brief's facility condition")
print("=" * 78)

for facility, ld in (("critical", 6_000.0), ("standard", 4_000.0), ("utilitarian", 2_500.0)):
    check(eng.derive_ld_per_day(CV, facility) == ld,
          f"{facility}: {ld:,.0f} dollars per day on a 12 million dollar contract", str(ld))
b_crit = eng.build_brief("A201-2017", CV, "exacting", "critical")
b_util = eng.build_brief("A201-2017", CV, "exacting", "utilitarian")
check(b_crit["liquidated_damages_per_day"] == 6_000.0
      and b_util["liquidated_damages_per_day"] == 2_500.0,
      "the brief states the facility's rate; same value, different daily exposure")
check("band" in b_crit["liquidated_damages_rule"],
      "and the rule names the band rather than a bare coefficient",
      b_crit["liquidated_damages_rule"])
crit_state = fresh(facility="critical")
util_state = fresh(facility="utilitarian")
for st in (crit_state, util_state):
    for dec in ("defer", "defer", "escalate"):
        st = eng.advance(st, dec)
    if st["facility"] == "critical":
        crit_after = st
    else:
        util_after = st
check(crit_after["float_consumed_days"] == util_after["float_consumed_days"] == 14
      and crit_after["liquidated_damages_exposure"] == 12_000.0
      and util_after["liquidated_damages_exposure"] == 5_000.0,
      "the same decisions on the same value carry different LD exposure by facility alone",
      f"crit={crit_after['liquidated_damages_exposure']} "
      f"util={util_after['liquidated_damages_exposure']}")

print()
print("=" * 78)
print("EVENTS 1: the near miss is discrete, undisclosed, and the SWO is the mechanism")
print("=" * 78)

x = copy.deepcopy(s0)
for dec in ("absorb", "defer", "defer"):
    x = eng.advance(x, dec)
check(x["period"] == 4 and x["incident"]["status"] == "stopped"
      and x["incident"]["cause"] == "scheduled",
      "the scheduled near miss arrives at period four as a stop work order", str(x["incident"]))
check(eng.allowed_decisions(x) == eng.RESPONSES,
      "during the stoppage the ONLY decision is the response", str(eng.allowed_decisions(x)))
try:
    eng.advance(copy.deepcopy(x), "defer")
    check(False, "a standard decision during a stop work order is refused")
except ValueError as exc:
    check("stop work order" in str(exc), "a standard decision during a stop work order is "
          "refused, with the reason", str(exc))
try:
    eng.advance(copy.deepcopy(s0), "respond_strong")
    check(False, "a response with no stop work order is refused")
except ValueError as exc:
    check("nothing to respond to" in str(exc),
          "a response with no stop work order is refused, with the reason", str(exc))

direct_cost = round(CV * eng.EVENT_FIGURES["incident_direct_cost_rate"], 2)
check(direct_cost == 12_000.0,
      "the incident itself costs little (0.1 percent); the days are where the money goes")

strong = eng.advance(copy.deepcopy(x), "respond_strong")
minimal = eng.advance(copy.deepcopy(x), "respond_minimal")
check(strong["incident"]["days_lost"] == 6 and minimal["incident"]["days_lost"] == 18,
      "duration follows the RESPONSE, not the incident: 6 days strong, 18 minimal (exacting)",
      f"{strong['incident']['days_lost']} vs {minimal['incident']['days_lost']}")
check(strong["incident"]["restart_periods_left"] == 1
      and minimal["incident"]["restart_periods_left"] == 2,
      "and the restart shadow is longer after the minimal response")
after_restart = eng.advance(copy.deepcopy(strong), "defer")
check(after_restart["ev"] - strong["ev"] < CV / 10,
      "a restart period earns less than a full period: productivity does not recover "
      "immediately", f"earned {after_restart['ev'] - strong['ev']:.0f}")
check(after_restart["incident"]["status"] == "none",
      "and the shadow clears when the restart periods run out")

print()
print("=" * 78)
print("EVENTS 2: severity depends on state the trainee influenced")
print("=" * 78)

# The SAME incident, the same response, on two states that differ only by earlier decisions.
rich = copy.deepcopy(s0)
for dec in ("absorb", "defer", "defer"):        # dispute absorbed early: float untouched
    rich = eng.advance(rich, dec)
poor = copy.deepcopy(s0)
for dec in ("defer", "defer", "escalate"):      # float spent on the dispute: 14 of 12 gone
    poor = eng.advance(poor, dec)
check(rich["incident"]["status"] == "stopped" and poor["incident"]["status"] == "stopped",
      "both runs meet the same stop work order at period four")
rich_after = eng.advance(rich, "respond_minimal")
poor_after = eng.advance(poor, "respond_minimal")
check(rich_after["liquidated_damages_exposure"] == 24_000.0,
      "float-rich: the 18 lost days breach 12 float days by 6, a bounded exposure",
      str(rich_after["liquidated_damages_exposure"]))
check(poor_after["liquidated_damages_exposure"] == 80_000.0,
      "float-poor: the SAME event and response land 20 days over, because the float was "
      "already spent on the dispute — same incident, different consequence",
      str(poor_after["liquidated_damages_exposure"]))

print()
print("=" * 78)
print("EVENTS 3: acceleration raises the incident hazard, attributably")
print("=" * 78)

acc = copy.deepcopy(s0)
acc = eng.advance(acc, "absorb")
acc = eng.advance(acc, "accelerate")
check(acc["hazard"] == 0.5, "one accelerated period: hazard 0.5, no incident yet",
      str(acc["hazard"]))
acc = eng.advance(acc, "accelerate")
# period 4: the scheduled near miss fires first; the hazard-triggered one queues behind it.
check(acc["incident"]["status"] == "stopped" and acc["incident"]["cause"] == "scheduled",
      "the scheduled incident arrives at period four regardless")
acc = eng.advance(acc, "respond_strong")
acc = eng.advance(acc, "defer")
check(acc["incident"]["status"] == "stopped" and acc["incident"]["cause"] == "acceleration",
      "and the hazard the trainee built by accelerating fires a SECOND stop work order, "
      "attributed to the acceleration — consequence, not bad luck", str(acc["incident"]))
check(any(i.get("cause") == "acceleration" for i in acc["incidents"]),
      "the attribution is in the incident record the debrief will read")
no_acc = copy.deepcopy(s0)
for dec in ("absorb", "defer", "defer"):
    no_acc = eng.advance(no_acc, dec)
no_acc = eng.advance(no_acc, "respond_strong")
no_acc = eng.advance(no_acc, "defer")
no_acc = eng.advance(no_acc, "defer")
check(all(i.get("cause") != "acceleration" for i in no_acc["incidents"]),
      "a run that never accelerated never meets an acceleration incident: deterministic, "
      "so the debrief's attribution cannot be wrong")

print()
print("=" * 78)
print("NARRATION: a layer, never a dependency, and never the judge")
print("=" * 78)

# The engine is untouched by narration BY CONSTRUCTION (training_engine never imports the
# narrator), and the loop proves it end to end: the same decisions with narration disabled
# and with a stub installed produce byte-identical STATE, differing only in the sentence.
ADMIN_TOKEN = "training-events-admin"
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="EVENTS-ADMIN", role="ResearchAdmin",
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


_, tok_a = make("EVT-OPS-A", "operational")
_, tok_b = make("EVT-OPS-B", "operational")

tr.set_narrator_override(None)   # narration OFF (no key in this environment resolves to None)
ra = post({"action": "trainingstart", "session_token": tok_a, "contract_form": "A201-2017",
           "conditions": "exacting", "contract_value": 12_000_000, "facility": "critical"})
da = post({"action": "trainingdecision", "session_token": tok_a,
           "run_id": ra["run_id"], "decision": "defer"})
check(da.get("ok") is True and da.get("narrative") is None,
      "with narration unavailable the run continues on the figures alone", str(da)[:100])

seen_views: list[dict] = []


def stub_narrator(view):
    seen_views.append(view)
    return "The site held its position this period. Figures are stated in the tables."


tr.set_narrator_override(stub_narrator)
rb = post({"action": "trainingstart", "session_token": tok_b, "contract_form": "A201-2017",
           "conditions": "exacting", "contract_value": 12_000_000, "facility": "critical"})
db = post({"action": "trainingdecision", "session_token": tok_b,
           "run_id": rb["run_id"], "decision": "defer"})
tr.set_narrator_override(None)
check(db.get("narrative") == stub_narrator(None) and len(seen_views) >= 2,
      "with a narrator present the sentence is carried on the response")
seen_views.clear()
check(json.dumps(da["state"], sort_keys=True) == json.dumps(db["state"], sort_keys=True),
      "IDENTICAL state transitions with narration disabled and enabled: the generator is "
      "not the judge, structurally")


def broken_narrator(view):
    raise RuntimeError("narration exploded")


tr.set_narrator_override(broken_narrator)
db2 = post({"action": "trainingdecision", "session_token": tok_b,
            "run_id": rb["run_id"], "decision": "escalate"})
tr.set_narrator_override(None)
check(db2.get("ok") is True and db2.get("narrative") is None,
      "a narrator that RAISES does not stop the run: narration is a layer, not a dependency",
      str(db2)[:100])

print()
print("=" * 78)
print("THE VIEW DOES NOT FORECAST: hazard is redacted")
print("=" * 78)

view_b = post({"action": "trainingstate", "session_token": tok_b, "run_id": rb["run_id"]})
check("hazard" not in (view_b.get("state") or {}),
      "the hazard accumulator never leaves the server: at the threshold it would forecast "
      "the next incident deterministically", str(sorted((view_b.get("state") or {}).keys()))[:120])
check("allowed_decisions" in view_b and "accelerate" in view_b["allowed_decisions"],
      "the view states what may be decided, including acceleration")

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
