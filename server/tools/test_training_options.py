#!/usr/bin/env python3
"""
Training mode run 6: the courses of action open each period, and what follows from each.

Run (from server/):

    PYTHONIOENCODING=utf-8 DATABASE_URL=... SESSION_SECRET=... python tools/test_training_options.py

The property under test is TRACEABILITY, not prose. Every consequence a trainee reads must be
a stated rule of the effect table computed with the same arithmetic `advance` uses, or a
contract period transcribed with its citation, or an explicit "Not established". So this suite
asserts the figures against the effect-table constants directly, exercises every form against
every decision so no branch can raise unseen, and proves the option set is exactly what
`allowed_decisions` permits, in that order, deterministically.
"""
from __future__ import annotations

import json
import random
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app import training_engine as eng  # noqa: E402

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


def opt(bundle: dict, decision: str) -> dict:
    for o in bundle["options"]:
        if o["decision"] == decision:
            return o
    raise AssertionError(f"no option for {decision}: "
                         f"{[o['decision'] for o in bundle['options']]}")


VALUE = 12_000_000.0

print("=" * 78)
print("Training mode: courses of action and their consequences")
print("=" * 78)

# ---------------------------------------------------------------- period one, A201, exacting
state = eng.initial_state("A201-2017", VALUE, "exacting", "standard")
bundle = eng.build_options(state)

check([o["decision"] for o in bundle["options"]] == list(eng.allowed_decisions(state)),
      "the options are exactly the decisions allowed this period, in that order",
      str([o["decision"] for o in bundle["options"]]))

check(bundle == eng.build_options(state),
      "the same state produces byte-identical options (deterministic)")

profile = eng.CONDITION_PROFILES["exacting"]

# Escalate: float cost, preparation cost and credibility all from the effect table.
esc = opt(bundle, "escalate")
days = eng.escalation_float_cost(state)
check(f"{days} days of float" in esc["costs"][0],
      "escalating quotes the escalation curve's own float cost",
      f"{days} vs {esc['costs'][0]}")
prep = round(VALUE * eng.ESCALATE_PREP_COST_RATE, 2)
check(eng._fmt_money(prep) in esc["costs"][1],
      "escalating quotes the claim preparation rate from the effect table",
      esc["costs"][1])
check(f"from {state['owner_credibility']} to {max(eng.CRED_MIN, state['owner_credibility'] - 1)}"
      in esc["costs"][2],
      "escalating quotes the credibility movement and the asymmetric earn rule",
      esc["costs"][2])
check(str(eng.CRED_EARN_CONCESSIONS) + " concessions" in esc["costs"][2],
      "and states how many concessions earn a point back")

# The entitlement it protects, and the contract period it is protected inside, with citation.
form = eng.CONTRACT_FORMS["A201-2017"]
check(form["claim_notice_citation"] in esc["protects"],
      "the entitlement it protects cites the clause the period comes from", esc["protects"])
check(eng._fmt_money(state["dispute"]["estimated_cost"]) in esc["protects"],
      "and quotes the matter's stored estimated cost exactly", esc["protects"])

# Absorb: the contingency arithmetic is the effect table's, not a rounded restatement.
ab = opt(bundle, "absorb")
after = round(state["contingency_remaining"] - state["dispute"]["estimated_cost"], 2)
check(eng._fmt_money(after) in ab["costs"][0],
      "absorbing quotes the contingency left after it, computed the same way", ab["costs"][0])
check("waives the entitlement permanently" in ab["forecloses"],
      "absorbing states the entitlement it forecloses")

# Defer: the two clocks must not blur. One deferral spends a 21 day window.
de = opt(bundle, "defer")
check(f"{profile['defer_drift_float_days']} days of float" in de["costs"][0],
      "deferring quotes this profile's drift, not the other profile's", de["costs"][0])
check(f"{int(eng.DEFER_EV_FACTOR * 100)} per cent" in de["costs"][2],
      "deferring quotes the disturbed-period earning factor", de["costs"][2])
check(f"{eng.PERIOD_DAYS} more days" in de["forecloses"]
      and "the window will have closed" in de["forecloses"],
      "deferring says the 21 day window closes before the next decision point",
      de["forecloses"])

# Accelerate: the hazard is WITHHELD, and says so, rather than being asserted or invented.
ac = opt(bundle, "accelerate")
check("deliberately not stated in advance" in ac["costs"][1],
      "accelerating states that its safety exposure is not disclosed in advance",
      ac["costs"][1])
check("hazard" not in json.dumps(bundle).lower(),
      "and the hazard accumulator appears nowhere in the option set")
check(f"buys back {eng.EVENT_FIGURES['acceleration_float_recovered_days']} days of float"
      in ac["protects"],
      "accelerating quotes the float it recovers from the event figures", ac["protects"])

# ---------------------------------------------------------------- the form decides the words
far = eng.build_options(eng.initial_state("Federal FAR", VALUE, "steady", "standard"))
far_defer = opt(far, "defer")
check("52.243-4(d)" in far_defer["forecloses"] and "lookback" in far_defer["forecloses"],
      "under the federal form deferring states the cost lookback, not a notice bar",
      far_defer["forecloses"])
check("Nothing is time barred" in far_defer["forecloses"],
      "and says nothing is time barred: the money is simply gone")

cd = eng.build_options(eng.initial_state("ConsensusDocs 200", VALUE, "steady", "standard"))
check("Section 8.4" in opt(cd, "escalate")["protects"],
      "under ConsensusDocs the entitlement is protected inside its own clause",
      opt(cd, "escalate")["protects"])
check("14 day period" in opt(cd, "escalate")["protects"],
      "and its 14 day period, not the 21 remembered from another form")

# ---------------------------------------------------------------- abstention, not assertion
# A period with nothing open: the recommendation is absent, and the reason says so rather than
# inventing one.
quiet = eng.initial_state("A201-2017", VALUE, "steady", "standard")
quiet["dispute"]["status"] = "absorbed"
quiet_bundle = eng.build_options(quiet)
check(quiet_bundle["recommended_decision"] is None,
      "with nothing open there is no recommended decision")
check(quiet_bundle["reason"].startswith(eng.NOT_ESTABLISHED),
      "and the reason states that nothing is open rather than recommending anyway",
      quiet_bundle["reason"])
check(opt(quiet_bundle, "escalate")["protects"].startswith(eng.NOT_ESTABLISHED),
      "escalating with no open matter states that there is no entitlement to protect",
      opt(quiet_bundle, "escalate")["protects"])
check(opt(quiet_bundle, "absorb")["costs"][0].startswith(eng.NOT_ESTABLISHED),
      "absorbing with no open matter states that there is no cost to absorb",
      opt(quiet_bundle, "absorb")["costs"][0])

# ---------------------------------------------------------------- every form, every decision
# Run the loop exhaustively so no branch of the option builder can raise unseen, and so the
# recommendation cannot crash on a form whose site-condition rule carries no lookback fraction
# (which it did, before this pass).
random.seed(11)
covered: set[str] = set()
crashed = ""
for contract in eng.CONTRACT_FORMS:
    for conditions in eng.CONDITION_PROFILES:
        for _ in range(40):
            s = eng.initial_state(contract, VALUE, conditions, "standard")
            for _ in range(eng.PERIODS_TOTAL):
                try:
                    b = eng.build_options(s)
                except Exception as exc:   # noqa: BLE001
                    crashed = f"{contract}/{conditions}: {type(exc).__name__}: {exc}"
                    break
                allowed = list(eng.allowed_decisions(s))
                if [o["decision"] for o in b["options"]] != allowed:
                    crashed = f"option order diverged from allowed_decisions: {allowed}"
                    break
                for o in b["options"]:
                    covered.add(o["decision"])
                    if not (o["title"] and o["what"] and o["forecloses"] and o["protects"]
                            and o["costs"]):
                        crashed = f"empty field on {o['decision']}"
                        break
                s = eng.advance(s, random.choice(allowed))
            if crashed:
                break
        if crashed:
            break
    if crashed:
        break

check(not crashed, "every form against every decision, ten periods deep, builds options",
      crashed)
expected = set(eng.DECISIONS + eng.RESPONSES + eng.QUALITY_DECISIONS + eng.RESOURCE_DECISIONS)
check(covered == expected, "and every decision the engine defines was actually exercised",
      str(sorted(expected - covered)))

# ---------------------------------------------------------------- the recommendation is marked
live = eng.initial_state("A201-2017", VALUE, "exacting", "standard")
live_bundle = eng.build_options(live)
check(live_bundle["recommended_decision"] == "escalate",
      "the recommended decision names one of the options open this period",
      str(live_bundle["recommended_decision"]))
check(live_bundle["recommended_decision"] in [o["decision"] for o in live_bundle["options"]],
      "and it is one of the options laid out, so it can be marked against them")
check(live_bundle["reason"] == eng.build_recommendation(live)["why"],
      "and its reason is the recommendation's own reason, not a second one written here")

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
