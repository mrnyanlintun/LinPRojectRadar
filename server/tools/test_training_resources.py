#!/usr/bin/env python3
"""
Training upgrade run 2: the resources thread, and the thread-opening spacing rule.

Run (from server/):

    PYTHONIOENCODING=utf-8 DATABASE_URL=... python tools/test_training_resources.py

The brief's required coverage: low crew adequacy slows productivity across the whole run, not
only the resource thread's own work; accelerating with low adequacy costs more than with high;
paying premium holds the schedule and spends contingency from the shared pool; the resource
thread and the others draw on the same float; the spacing rule prevents collision with the
scheduled near miss and with the quality opening.
"""
from __future__ import annotations

import copy
import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402

import app.main as main  # noqa: E402
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
PERIOD_EARN = CV / eng.PERIODS_TOTAL


def fresh(form="A201-2017", conditions="exacting", facility="standard"):
    return eng.initial_state(form, CV, conditions, facility)


def step(state, preferred):
    """Advance one period, stepping around the standing period-4 stop work order."""
    if state.get("incident", {}).get("status") == "stopped":
        return eng.advance(copy.deepcopy(state), "respond_strong")
    return eng.advance(copy.deepcopy(state), preferred)


print("=" * 78)
print("THE SPACING RULE: openings are derived, not hand-picked, and cannot collide")
print("=" * 78)

openings = eng.thread_opening_periods()
check(openings == {"dsc": 5, "quality": 6, "resources": 7},
      "the rule allocates the three secondary threads to periods 5, 6 and 7", str(openings))
check(eng.EVENT_FIGURES["near_miss_period"] not in openings.values(),
      "NO thread opens on the scheduled near miss period, which is the collision run 1 hit "
      "and fixed by hand", f"near miss at {eng.EVENT_FIGURES['near_miss_period']}")
check(len(set(openings.values())) == len(openings),
      "and no two threads share a period, so none can be silently invisible", str(openings))
check(eng.DSC_PERIOD == openings["dsc"] and eng.QUALITY_INSPECTION_PERIOD == openings["quality"]
      and eng.RESOURCE_SHORTAGE_PERIOD == openings["resources"],
      "the three constants are DERIVED from the rule, not written down beside it")
check(eng.DSC_PERIOD == 5 and eng.QUALITY_INSPECTION_PERIOD == 6,
      "and the rule REPRODUCES the periods run 4 and run 1 were verified against, rather than "
      "renumbering them", f"dsc={eng.DSC_PERIOD} quality={eng.QUALITY_INSPECTION_PERIOD}")
check(min(openings.values()) > eng.EVENT_FIGURES["near_miss_period"],
      "every secondary thread opens after the near miss, so a trainee meets the spine and the "
      "stop work order before a second thread arrives")
try:
    eng.thread_opening_periods(("a", "b", "c", "d"))
    check(False, "a fourth thread is refused rather than crowded into the run's end")
except ValueError as exc:
    check("too few periods" in str(exc),
          "a fourth thread is REFUSED with the reason rather than crowded into the run's end: "
          "loud refusal, not a period nobody can play", str(exc))
check(eng.THREAD_OPENING_LAST_PERIOD == eng.PERIODS_TOTAL - 3,
      "the last allowed opening leaves three periods of play, enough for a compounding thread "
      "to reach its own cliff inside the run", str(eng.THREAD_OPENING_LAST_PERIOD))

print()
print("=" * 78)
print("THE THREAD OPENS BY THE RULE, UNDISCLOSED UNTIL THEN")
print("=" * 78)

s0 = fresh()
check(s0["resources"] is None, "no shortage state before the run starts")
check(s0["crew_adequacy"] == eng.RESOURCE_FIGURES["adequacy_full"],
      "but crew adequacy IS live from period one, at full: it is a property of the project, "
      "not of the thread, which is why the thread can degrade it", str(s0["crew_adequacy"]))
s = s0
while s["period"] < eng.RESOURCE_SHORTAGE_PERIOD:
    check(s["resources"] is None, f"still no shortage in period {s['period']}")
    s = step(s, "defer")
short = s
check(short["period"] == eng.RESOURCE_SHORTAGE_PERIOD and short["resources"] is not None
      and short["resources"]["status"] == "open",
      f"the trade shortage opens as period {eng.RESOURCE_SHORTAGE_PERIOD} begins",
      str(short["resources"]))
check(short["crew_adequacy"] == eng.RESOURCE_FIGURES["shortage_adequacy"],
      "and crew adequacy drops to the designed shortage level", str(short["crew_adequacy"]))
check(short["dispute"]["status"] == "open" and short["quality"]["status"] == "open",
      "with the dispute AND the quality thread still open: three threads live at once")

print()
print("=" * 78)
print("THE COUPLING: low adequacy slows the WHOLE run, not the shortage's own work")
print("=" * 78)

# Two states differing ONLY in crew_adequacy. A constructed input to a pure function, stated as
# such: the point is to isolate adequacy from every other difference, which no sequence of real
# decisions can do (reaching low adequacy necessarily spends float or money on the way).
low = copy.deepcopy(short)
full = copy.deepcopy(short)
full["crew_adequacy"] = eng.RESOURCE_FIGURES["adequacy_full"]


def earned(before: dict, decision: str) -> float:
    return round(eng.advance(copy.deepcopy(before), decision)["ev"] - before["ev"], 2)


for decision, what in (("escalate", "escalating the claim"),
                       ("rework_now", "reworking the quality defect"),
                       ("absorb", "absorbing the change"),
                       ("accelerate", "accelerating")):
    low_earn = earned(low, decision)
    full_earn = earned(full, decision)
    check(low_earn < full_earn,
          f"a period spent {what} earns LESS with crews short than with crews full: the "
          "shortage is a rate the whole project runs at, not a cost on its own work",
          f"low={low_earn} full={full_earn}")
check(earned(low, "escalate") == round(PERIOD_EARN * eng.RESOURCE_FIGURES["shortage_adequacy"], 2),
      "and the earning is exactly adequacy times a full period, so the coupling is the "
      "multiplier it claims to be and not an unrelated penalty",
      str(earned(low, "escalate")))
check(earned(full, "escalate") == round(PERIOD_EARN, 2),
      "while a full-adequacy period earns a full increment: a run that never meets the "
      "shortage is untouched by this thread", str(earned(full, "escalate")))
note_state = eng.advance(copy.deepcopy(low), "escalate")
check(any("percent of full productivity" in n and "not" in n
          for n in note_state["period_changes"]["notes"]),
      "and the period's own notes say the rate applies to all the work, so a trainee does not "
      "read the lost earning as bad luck", str(note_state["period_changes"]["notes"]))

print()
print("=" * 78)
print("ACCELERATION IS WORSE WITH SCARCE TRADES, on both axes")
print("=" * 78)

acc_low = eng.advance(copy.deepcopy(low), "accelerate")
acc_full = eng.advance(copy.deepcopy(full), "accelerate")
low_cost = round(acc_low["ac"] - low["ac"], 2)
full_cost = round(acc_full["ac"] - full["ac"], 2)
check(low_cost > full_cost,
      "accelerating with crews short costs MORE than accelerating with crews available: you "
      "are bidding for people who are already unavailable",
      f"low={low_cost} full={full_cost}")
expected_ratio = eng.RESOURCE_FIGURES["accelerate_low_adequacy_cost_multiplier"]
check(round((low_cost - PERIOD_EARN) / (full_cost - PERIOD_EARN), 3) == round(expected_ratio, 3),
      "and it costs exactly the designed multiplier more, not an arbitrary amount",
      f"ratio={(low_cost - PERIOD_EARN) / (full_cost - PERIOD_EARN)}")
check(acc_low["hazard"] > acc_full["hazard"],
      "AND the incident hazard rises further: compressing work you are already short handed "
      "for is how people get hurt", f"low={acc_low['hazard']} full={acc_full['hazard']}")
check(round(acc_low["hazard"] - acc_full["hazard"], 4)
      == eng.RESOURCE_FIGURES["accelerate_low_adequacy_hazard_extra"],
      "by exactly the designed extra", str(acc_low["hazard"] - acc_full["hazard"]))
check(any("short handed" in n or "already short" in n
          for n in acc_low["period_changes"]["notes"]),
      "and the interaction is stated in the period's notes, so the debrief's attribution is a "
      "read rather than a reconstruction", str(acc_low["period_changes"]["notes"]))

print()
print("=" * 78)
print("PAY PREMIUM: holds the schedule, spends the SHARED contingency")
print("=" * 78)

paid = eng.advance(copy.deepcopy(short), "pay_premium")
expected_cost = round(CV * eng.RESOURCE_FIGURES["pay_premium_cost_rate"], 2)
check(paid["crew_adequacy"] == eng.RESOURCE_FIGURES["adequacy_full"],
      "the crews are back to full: the schedule is held", str(paid["crew_adequacy"]))
check(paid["resources"]["status"] == "resolved"
      and paid["resources"]["resolution"] == "premium",
      "and the thread closes, with how it closed recorded for the debrief",
      str(paid["resources"]))
check(round(short["contingency_remaining"] - paid["contingency_remaining"], 2) == expected_cost,
      "the premium is drawn from contingency_remaining -- the SAME pool absorbing a change "
      "draws from, not a resource pool", str(paid["contingency_remaining"]))
check(paid["float_consumed_days"] == short["float_consumed_days"],
      "and no float is spent: this option trades money for time, which is the choice")
after_paid = eng.advance(paid, "escalate")
check(round(after_paid["ev"] - paid["ev"], 2) == round(PERIOD_EARN, 2),
      "the period AFTER paying earns a full increment again: holding the schedule means the "
      "rate recovers, not just the thread closing", str(after_paid["ev"] - paid["ev"]))

print()
print("=" * 78)
print("RESEQUENCE: no money, float and a partial fill")
print("=" * 78)

reseq = eng.advance(copy.deepcopy(short), "resequence")
check(reseq["contingency_remaining"] == short["contingency_remaining"],
      "resequencing draws no contingency")
check(round(reseq["ac"] - short["ac"] - PERIOD_EARN, 2) == 0,
      "and adds no direct cost beyond the period's own progress",
      str(reseq["ac"] - short["ac"]))
check(reseq["float_consumed_days"] - short["float_consumed_days"]
      == eng.RESOURCE_FIGURES["resequence_float_days"],
      "it spends float instead", str(reseq["float_consumed_days"] - short["float_consumed_days"]))
check(eng.RESOURCE_FIGURES["shortage_adequacy"] < reseq["crew_adequacy"]
      < eng.RESOURCE_FIGURES["adequacy_full"],
      "and only PARTLY fills the shortage: reordering moves a shortage rather than filling it",
      str(reseq["crew_adequacy"]))
check(reseq["resources"]["status"] == "open",
      "so the thread stays open and still competes for the next period's single decision")

print()
print("=" * 78)
print("ACCEPT THE DELAY: float outright, and it compounds while it persists")
print("=" * 78)

d1 = eng.advance(copy.deepcopy(short), "accept_delay")
check(d1["float_consumed_days"] - short["float_consumed_days"]
      == eng.RESOURCE_FIGURES["accept_delay_float_days"],
      "accepting the delay spends float outright")
check(d1["crew_adequacy"] < short["crew_adequacy"],
      "and the shortage DEEPENS rather than holding still",
      f"{short['crew_adequacy']} -> {d1['crew_adequacy']}")
d2 = eng.advance(copy.deepcopy(d1), "accept_delay")
check(d2["crew_adequacy"] < d1["crew_adequacy"],
      "a second acceptance deepens it again: the delay compounds if the shortage persists",
      str(d2["crew_adequacy"]))
check(round(d2["ev"] - d1["ev"], 2) < round(d1["ev"] - short["ev"], 2),
      "so the second accepted period earns LESS than the first: the compounding is visible in "
      "the schedule, which is where it hurts",
      f"first={d1['ev'] - short['ev']} second={d2['ev'] - d1['ev']}")
floored = copy.deepcopy(d1)
for _ in range(12):
    floored["crew_adequacy"] = max(
        eng.RESOURCE_FIGURES["adequacy_floor"],
        round(floored["crew_adequacy"] - eng.RESOURCE_FIGURES["accept_delay_adequacy_decay"], 4))
check(floored["crew_adequacy"] == eng.RESOURCE_FIGURES["adequacy_floor"],
      "adequacy never falls below the floor: even a badly handled shortage leaves a crew on "
      "site, so the run cannot reach zero earning", str(floored["crew_adequacy"]))

print()
print("=" * 78)
print("COMPETITION: one float counter, one contingency pool, three threads")
print("=" * 78)

check(eng.allowed_decisions(short)
      == eng.DECISIONS + eng.QUALITY_DECISIONS + eng.RESOURCE_DECISIONS,
      "the menu is the union of every live thread's verbs: one decision, from across all three",
      str(eng.allowed_decisions(short)))
via_dispute = eng.advance(copy.deepcopy(short), "escalate")
via_quality = eng.advance(copy.deepcopy(short), "rework_now")
via_resource = eng.advance(copy.deepcopy(short), "resequence")
check(via_dispute["float_consumed_days"] != short["float_consumed_days"]
      and via_quality["float_consumed_days"] != short["float_consumed_days"]
      and via_resource["float_consumed_days"] != short["float_consumed_days"],
      "all THREE threads' actions move the same float_consumed_days: one counter, no resource "
      "pool", f"dispute={via_dispute['float_consumed_days']} "
              f"quality={via_quality['float_consumed_days']} "
              f"resource={via_resource['float_consumed_days']}")
via_absorb = eng.advance(copy.deepcopy(short), "absorb")
check(via_absorb["contingency_remaining"] < short["contingency_remaining"]
      and paid["contingency_remaining"] < short["contingency_remaining"],
      "and absorbing a change and paying the trade premium draw on the SAME contingency, so "
      "spending it on one is not spending it on the other",
      f"absorb={via_absorb['contingency_remaining']} premium={paid['contingency_remaining']}")
check(via_resource["quality"]["status"] == "open"
      and via_resource["dispute"]["status"] == "open",
      "acting on the shortage this period leaves the other two exactly where they were: one "
      "decision, not three")
check(via_quality["resources"]["status"] == "open"
      and via_quality["crew_adequacy"] == short["crew_adequacy"],
      "and acting on quality leaves the shortage untouched, still degrading every period")

print()
print("=" * 78)
print("VALIDATION AND THE VIEW")
print("=" * 78)

try:
    eng.advance(copy.deepcopy(s0), "pay_premium")
    check(False, "a resource verb before the shortage opens is refused")
except ValueError as exc:
    check("nothing to decide about resources" in str(exc),
          "a resource verb before the shortage opens is refused, with the reason", str(exc))
try:
    eng.advance(copy.deepcopy(paid), "resequence")
    check(False, "a resource verb after the shortage closed is refused")
except ValueError as exc:
    check("nothing to decide about resources" in str(exc),
          "and after it closes, with the same reason", str(exc))
check(eng.resource_position(s0) is None, "no position before discovery")
rp = eng.resource_position(short)
check(rp is not None and rp["productivity_pct"] == 75 and rp["scarce"] is True,
      "the position states the productivity RATE, which is the figure a trainee needs, and "
      "whether the crews count as scarce", str(rp))
# Found by the browser drive, not by this suite's first version: the position omitted
# `resolution`, so the screen could not tell the two closures apart and told a trainee who paid
# a premium that they had resequenced. A closure the screen has to GUESS at is a closure the
# screen gets wrong.
check(eng.resource_position(paid).get("resolution") == "premium",
      "the position carries HOW the thread closed, so the screen states the closure the "
      "trainee actually chose", str(eng.resource_position(paid)))
reseq_done = eng.advance(copy.deepcopy(short), "resequence")
while reseq_done["resources"]["status"] == "open" and reseq_done["period"] <= eng.PERIODS_TOTAL:
    reseq_done = eng.advance(reseq_done, "resequence")
check(eng.resource_position(reseq_done).get("resolution") == "resequenced",
      "and it distinguishes resequencing to full from paying a premium, which are different "
      "things a trainee did", str(eng.resource_position(reseq_done)))

print()
print("=" * 78)
print("ISOLATION: the new state never reaches either export kind")
print("=" * 78)

import app.research_export as rex  # noqa: E402
src = open(rex.__file__, encoding="utf-8").read()
check("TrainingRun" not in src,
      "research_export.py never references TrainingRun: crew_adequacy and the resources dict "
      "live in the JSON state column no export path reads")

ADMIN_TOKEN = "resources-test-admin"
with Session() as sess:
    from sqlalchemy import select
    from app.research_identity import hash_access_token
    from app.research_models import Participant
    row = sess.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        sess.add(Participant(pseudonymous_code="RESOURCES-ADMIN", role="ResearchAdmin",
                             access_token_hash=hash_access_token(ADMIN_TOKEN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN_TOKEN)
    sess.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN_TOKEN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "RES-OPS-A", "role": "Participant",
                "account_type": "operational"})
op_tok = post({"action": "researchlogin",
               "access_token": created["access_token"]})["session_token"]

run = post({"action": "trainingstart", "session_token": op_tok, "contract_form": "A201-2017",
            "conditions": "exacting", "contract_value": 12_000_000, "facility": "standard"})
run_id = run["run_id"]
view = run
while view["period"] < eng.RESOURCE_SHORTAGE_PERIOD:
    dec = "respond_strong" if "respond_strong" in view["allowed_decisions"] else "defer"
    view = post({"action": "trainingdecision", "session_token": op_tok, "run_id": run_id,
                 "decision": dec})
check(view.get("resource_notice") is not None
      and view["resource_notice"]["status"] == "open",
      "the live run's resource notice surfaces once the shortage has opened",
      str(view.get("resource_notice")))
check(set(eng.RESOURCE_DECISIONS).issubset(set(view["allowed_decisions"])),
      "and the three resource verbs are offered through the real action",
      str(view["allowed_decisions"]))
with Session() as sess:
    row = sess.get(TrainingRun, run_id)
    check(row.state.get("resources") is not None and row.state.get("crew_adequacy") is not None,
          "and both new state fields are stored on the run's state column")
check("crew_adequacy" not in str(view.get("result") or {}),
      "the crew adequacy figure does not leak into the computed signals result: it acts on the "
      "run through ev, which the merge already projects, and adds no signal key of its own")

paid_view = post({"action": "trainingdecision", "session_token": op_tok, "run_id": run_id,
                  "decision": "pay_premium"})
check(paid_view.get("ok") is True
      and paid_view["resource_notice"]["status"] == "resolved"
      and paid_view["state"]["crew_adequacy"] == eng.RESOURCE_FIGURES["adequacy_full"],
      "and paying the premium through the real action closes the thread and restores the rate",
      str(paid_view.get("resource_notice")))

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
