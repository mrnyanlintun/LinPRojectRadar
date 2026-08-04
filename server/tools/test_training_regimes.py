#!/usr/bin/env python3
"""
Training mode run 4: the three regimes across the whole run, the four traps, the debrief and
its counterfactual, and the disclaimer.

Run (from server/):

    PYTHONIOENCODING=utf-8 DATABASE_URL=... SESSION_SECRET=... python tools/test_training_regimes.py

The brief's required coverage: changing the form changes the deadlines that apply and the
failure a late trainee gets; each of the four traps behaves as its form dictates; the debrief
attributes an incident to acceleration where acceleration preceded it; a counterfactual that
cannot be computed honestly is reported unavailable rather than estimated.
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
from app import training_engine as eng  # noqa: E402
from app.training_debrief import build_debrief  # noqa: E402

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
META = {"contract_value": CV, "conditions": "exacting", "facility": "standard"}


def fresh(form):
    return eng.initial_state(form, CV, "exacting", "standard")


def to_dsc_period(form, first="absorb"):
    """Absorb the claim at once, ride to period five, where the site condition is discovered."""
    s = fresh(form)
    for d in (first, "defer", "defer", "respond_strong"):
        s = eng.advance(s, d)
    assert s["period"] == 5, s["period"]
    return s


print("=" * 78)
print("PART 1: the form changes the deadlines, and the failure a late trainee gets")
print("=" * 78)

# The SAME late escalation (one deferred period) under the three forms, three different fates.
late = {}
for form in ("A201-2017", "ConsensusDocs 200", "Federal FAR"):
    late[form] = eng.advance(eng.advance(fresh(form), "defer"), "escalate")
check(late["A201-2017"]["dispute"]["entitlement"] == "lost",
      "A201 late: time barred outright (21 days ran during the deferral)",
      late["A201-2017"]["dispute"]["entitlement"])
check(late["ConsensusDocs 200"]["dispute"]["entitlement"] == "lost",
      "ConsensusDocs late: time barred too (its bar is 14 days, shorter still)",
      late["ConsensusDocs 200"]["dispute"]["entitlement"])
far_late = late["Federal FAR"]["dispute"]
check(far_late["entitlement"] == "preserved" and far_late["pending_recovery"] == 105_000.0,
      "FAR late: never barred, but the claim GREW while deferred and the lookback halves it "
      "(210,000 grown, 105,000 recoverable)", str(far_late))

# The same immediate escalation: A201 books at once, ConsensusDocs holds it conditional.
a_now = eng.advance(fresh("A201-2017"), "escalate")
c_now = eng.advance(fresh("ConsensusDocs 200"), "escalate")
check(a_now["dispute"]["status"] == "escalated"
      and a_now["dispute"]["pending_recovery"] == 180_000.0,
      "A201 immediate: one step, recovery pending at once")
check(c_now["dispute"]["status"] == "noticed"
      and c_now["dispute"]["entitlement"] == "conditional"
      and c_now["dispute"]["pending_recovery"] is None,
      "ConsensusDocs immediate: notice is STEP ONE, the recovery is conditional on the "
      "documentation", str(c_now["dispute"]))

print()
print("=" * 78)
print("TRAP 1: 21 days applied to a differing site condition under A201, where it is 14")
print("=" * 78)

s = to_dsc_period("A201-2017")
check(s["dsc"] is not None and s["dsc"]["days_since_event"] == 17,
      "the site condition is 17 days old at the first decision after discovery: inside the "
      "21 day claim window, outside the 14 day site-conditions window — the trap's geometry")
pos = eng.dsc_position(s)
check(pos["kind"] == "dsc_notice_bar" and pos["window_days"] == 14 and pos["expired"] is True,
      "A201: the site condition's own clock (Section 3.7.4) has already run", str(pos))
claim_pos_days = eng.CONTRACT_FORMS["A201-2017"]["claim_notice_days"]
check(s["dsc"]["days_since_event"] < claim_pos_days,
      "while the CLAIM window would still be open at 17 of 21 days — believing 21 applies "
      "is exactly the mistake")
e = eng.advance(s, "escalate")
check(e["dsc"]["entitlement"] == "lost"
      and any("3.7.4" in n and "does not apply" in n for n in e["period_changes"]["notes"]),
      "escalating on the 21 day belief fails with the Section 3.7.4 explanation: REACHABLE",
      str(e["period_changes"]["notes"])[:160])

print()
print("=" * 78)
print("TRAP 2: ConsensusDocs notice given, then silence")
print("=" * 78)

c1 = eng.advance(fresh("ConsensusDocs 200"), "escalate")   # step one, in window
quiet = eng.advance(copy.deepcopy(c1), "defer")
check(quiet["dispute"]["entitlement"] == "lost"
      and any("8.4" in n and "quiet" in n for n in quiet["period_changes"]["notes"]),
      "notice then a deferred period: the documentation step lapses and the claim dies with "
      "the Section 8.4 citation: REACHABLE", str(quiet["period_changes"]["notes"])[:160])
active = eng.advance(copy.deepcopy(c1), "accelerate")
check(active["dispute"]["entitlement"] == "preserved"
      and active["dispute"]["pending_recovery"] == 180_000.0,
      "an active period after notice files the documentation and preserves the claim")
booked = eng.advance(active, "defer")
check(booked["change_order_count"] == 1 and booked["bac"] == CV + 180_000.0,
      "and the change order books the period after — one period later than A201, the price "
      "of the two-step clock")

print()
print("=" * 78)
print("TRAP 3: the federal 20 day lookback (built in run 2, restated against growth)")
print("=" * 78)

f1 = eng.advance(fresh("Federal FAR"), "defer")
pos = eng.notice_position(f1)
check(pos["kind"] == "cost_lookback" and pos["recoverable_fraction"] == 0.5,
      "after one deferred period only 20 of 40 days of cost is reachable: nothing is barred, "
      "the money is simply gone: REACHABLE", str(pos))
f2 = eng.advance(f1, "escalate")
check(f2["dispute"]["entitlement"] == "preserved"
      and f2["dispute"]["pending_recovery"] == 105_000.0,
      "the recoverable amount is the GROWN claim times the fraction", str(f2["dispute"]))

print()
print("=" * 78)
print("TRAP 4: the claim grows past 100,000 dollars and is submitted uncertified")
print("=" * 78)

# Contract value chosen so the claim STARTS under the threshold: 6M -> 90,000.
small = eng.initial_state("Federal FAR", 6_000_000.0, "exacting", "standard")
check(small["dispute"]["estimated_cost"] == 90_000.0,
      "on a 6 million dollar contract the claim starts at 90,000: under the threshold")
grown = eng.advance(small, "defer")
check(grown["dispute"]["estimated_cost"] == 105_000.0
      and grown["claim_crossed_threshold_last_period"] is True,
      "one deferred period grows it to 105,000, crossing the threshold during preparation",
      str(grown["dispute"]["estimated_cost"]))
uncert = eng.advance(copy.deepcopy(grown), "escalate")
check(uncert["dispute"]["entitlement"] == "lost"
      and any("52.233-1" in n for n in uncert["period_changes"]["notes"]),
      "escalated at once on the old form: uncertified over the threshold is not a claim at "
      "all: REACHABLE", str(uncert["period_changes"]["notes"])[:160])
waited = eng.advance(eng.advance(copy.deepcopy(grown), "defer"), "escalate")
check(waited["dispute"]["entitlement"] == "preserved",
      "a further period passes, the team knows the size, the certification is carried: the "
      "trap is the CROSSING, not the amount", waited["dispute"]["entitlement"])
big = eng.advance(eng.advance(fresh("Federal FAR"), "defer"), "escalate")
check(big["dispute"]["entitlement"] == "preserved",
      "a claim already over the threshold at the previous decision point was known to need "
      "certification and carries it")

print()
print("=" * 78)
print("THE DSC UNDER THE OTHER TWO FORMS: same discovery, different duties")
print("=" * 78)

cd = to_dsc_period("ConsensusDocs 200")
cd_now = eng.advance(copy.deepcopy(cd), "escalate")
check(cd_now["dsc"]["entitlement"] == "preserved",
      "ConsensusDocs: notice at the first opportunity is prompt, and preserves")
cd_late = eng.advance(eng.advance(copy.deepcopy(cd), "defer"), "escalate")
check(cd_late["dsc"]["entitlement"] == "lost"
      and any("3.16.2" in n for n in cd_late["period_changes"]["notes"]),
      "a period later is not prompt (Section 3.16.2)", str(cd_late["period_changes"]["notes"])[:120])
far = to_dsc_period("Federal FAR")
far_now = eng.advance(copy.deepcopy(far), "escalate")
check(far_now["dsc"]["entitlement"] == "preserved",
      "FAR: notice before the conditions are disturbed preserves")
far_late = eng.advance(eng.advance(copy.deepcopy(far), "defer"), "escalate")
check(far_late["dsc"]["entitlement"] == "lost"
      and any("52.236-2" in n for n in far_late["period_changes"]["notes"]),
      "a period of continued work disturbs them (FAR 52.236-2(a))",
      str(far_late["period_changes"]["notes"])[:120])

print()
print("=" * 78)
print("PART 2: the debrief — the why, and the honest counterfactual")
print("=" * 78)

# A run that accelerates twice and meets a second, acceleration-caused stop work order.
s = fresh("A201-2017")
# The hazard-triggered stop work order queues behind the scheduled one and fires once the
# restart shadow clears: scheduled SWO at period four, response, one restart period, then the
# acceleration's own SWO at period six.
for d in ("absorb", "accelerate", "accelerate", "respond_strong", "defer",
          "respond_strong", "defer", "defer", "defer", "defer"):
    s = eng.advance(s, d)
check(s["period"] > eng.PERIODS_TOTAL, "the accelerated run is complete", str(s["period"]))
db = build_debrief({"contract_form": "A201-2017", **META}, s)
acc_findings = [f for f in db["incidents"] if f["cause"] == "acceleration"]
check(len(acc_findings) == 1
      and "acceleration raises the chance" in acc_findings[0]["why"],
      "the debrief ATTRIBUTES the second stop work order to the acceleration, in words — "
      "consequence, not bad luck", str(acc_findings)[:160])
sched = [f for f in db["incidents"] if f["cause"] == "scheduled"]
check(len(sched) == 1 and "no decision of yours caused" in sched[0]["why"],
      "and the scheduled one is honestly NOT attributed to the trainee")
# This run's replay happens to align (the SWO schedule is unchanged by swapping the first
# decision), so the counterfactual IS honestly computable here — availability is decided by
# the replay, not assumed either way.
check(db["counterfactual"]["available"] is True,
      "this run's counterfactual replays cleanly and is therefore available",
      str(db["counterfactual"])[:120])

# A deferred run: the counterfactual IS computable, and shows what early escalation kept.
s2 = fresh("A201-2017")
for d in ("defer", "defer", "escalate", "respond_strong", "defer",
          "defer", "defer", "defer", "defer", "defer"):
    s2 = eng.advance(s2, d)
db2 = build_debrief({"contract_form": "A201-2017", **META}, s2)
cf = db2["counterfactual"]
check(cf["available"] is True and cf["claim"]["entitlement"] == "preserved"
      and cf["position"]["recovered_by_change_order"] == 180_000.0,
      "the replayed counterfactual: escalating at the first decision would have preserved "
      "the claim and recovered 180,000", str(cf.get("claim")))
check(s2["dispute"]["entitlement"] == "lost",
      "where the played run lost it — the comparison the trainee carries")
check(cf["position"]["float_spent_days"] != db2["spent"]["float_spent_days"],
      "and the two positions genuinely differ, so the comparison is not decorative")

# The escalate-first run: the counterfactual is the run itself, said plainly.
s3 = fresh("A201-2017")
for d in ("escalate", "defer", "defer", "respond_strong", "defer",
          "defer", "defer", "defer", "defer", "defer"):
    s3 = eng.advance(s3, d)
db3 = build_debrief({"contract_form": "A201-2017", **META}, s3)
check(db3["counterfactual"]["available"] is False
      and "first opportunity" in db3["counterfactual"]["reason"],
      "escalated first: the counterfactual is the run played, stated rather than recomputed")

# A structurally divergent replay: constructed decisions with a response where the replay has
# no stop work order. A constructed input to a pure function, stated as such — the point is
# that the divergence is REPORTED, never estimated across.
broken_state = copy.deepcopy(s2)
broken_state["decisions"] = [{"period": 1, "decision": "defer"},
                             {"period": 2, "decision": "respond_strong"}]
db4 = build_debrief({"contract_form": "A201-2017", **META}, broken_state)
# .get, not [], so a counterfactual that wrongly claims availability reads as a RED CHECK
# rather than a KeyError that kills the suite with no RESULT line (fault R6 did exactly that
# to the first version of this check).
check(db4["counterfactual"].get("available") is False
      and "diverges structurally" in db4["counterfactual"].get("reason", ""),
      "a replay that diverges structurally is reported unavailable with the reason, never "
      "estimated", str(db4["counterfactual"])[:140])

print()
print("=" * 78)
print("PART 3: the disclaimer")
print("=" * 78)

for form in ("A201-2017", "ConsensusDocs 200", "Federal FAR"):
    d = eng.build_disclaimer(form)
    check(eng.CONTRACT_FORMS[form]["label"] in d["governing_form"]
          and "routinely amended in negotiation" in d["amendment_note"]
          and "check which rules actually govern" in d["amendment_note"],
          f"{form}: names the governing form and says the first move is to check the real "
          "rules", str(d["governing_form"]))
d = eng.build_disclaimer("A201-2017")
check("designed training figure" in d["designed_figures"]
      and "liquidated damages band" in d["designed_figures"]
      and "acceleration" in d["designed_figures"],
      "the designed figures are marked as designed: the elicited constants, the LD band, the "
      "acceleration and productivity figures")
check("training_us_contract_regimes.md" in d["sourced_figures"],
      "and the sourced figures point at their source")
whole = json.dumps(d).lower()
check("liability" not in whole and "warranty" not in whole and "consent" not in whole,
      "no liability or consent language was composed: the approved notice text stands "
      "unchanged elsewhere")
brief = eng.build_brief("A201-2017", CV, "exacting", "standard")
check(brief.get("disclaimer", {}).get("amendment_note") == d["amendment_note"],
      "the brief carries the disclaimer, so it reaches the trainee before period one")

print()
print("=" * 78)
print("OVER HTTP: the debrief action, gated and complete-only")
print("=" * 78)

ADMIN_TOKEN = "training-regimes-admin"
with Session() as s_:
    row = s_.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s_.add(Participant(pseudonymous_code="REG-ADMIN", role="ResearchAdmin",
                           access_token_hash=hash_access_token(ADMIN_TOKEN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN_TOKEN)
    s_.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN_TOKEN})["session_token"]


def make(code: str, account_type: str) -> tuple[str, str]:
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": code, "role": "Participant",
                    "account_type": account_type})
    assert created.get("ok"), created
    tok = post({"action": "researchlogin",
                "access_token": created["access_token"]})["session_token"]
    return created["participant_id"], tok


_, ops = make("REG-OPS", "operational")
_, res = make("REG-RES", "research")

r = post({"action": "trainingstart", "session_token": ops, "contract_form": "A201-2017",
          "conditions": "exacting", "contract_value": 12_000_000})
mid = post({"action": "trainingdebrief", "session_token": ops, "run_id": r["run_id"]})
check(mid.get("ok") is False and "complete" in (mid.get("error") or ""),
      "mid-run, the debrief is refused with the reason", str(mid)[:100])
res_try = post({"action": "trainingdebrief", "session_token": res})
check(res_try.get("ok") is False,
      "a research account is refused trainingdebrief like every training action")

view = r
for _ in range(eng.PERIODS_TOTAL):
    allowed = view.get("allowed_decisions") or ["defer"]
    choice = "defer" if "defer" in allowed else allowed[0]
    view = post({"action": "trainingdecision", "session_token": ops,
                 "run_id": r["run_id"], "decision": choice})
check(view.get("status") == "complete", "a run driven to completion over HTTP")
final = post({"action": "trainingdebrief", "session_token": ops, "run_id": r["run_id"]})
check(final.get("ok") is True and final["debrief"]["counterfactual"] is not None
      and final["debrief"]["disclaimer"]["governing_form"] == "AIA A201-2017",
      "the debrief arrives complete, with the counterfactual verdict and the disclaimer",
      str(final)[:140])
check(view.get("dsc_notice") is not None or (view.get("state", {}).get("dsc") is not None),
      "the site condition reached the HTTP view during the run")
check("hazard" not in (view.get("state") or {}),
      "and the hazard is still redacted after everything run 4 added")

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
