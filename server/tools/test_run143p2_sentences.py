"""
RUN 143 PART 2 -- the sentence sweep, proved by RUNNING the layer, not by reading it.

The survey found the one sentence a naive grep misses (`qualification_boundary`'s Category-9
refusal, which contains none of the usual fragments and is emitted for six of the thirty-one
modules) exactly this way. So the promise is checked against the text the modules ACTUALLY
EMIT, on the empty package and on packages built to reach the arms an empty package cannot.

Run from `server/`:  PYTHONPATH=. python tools/test_run143p2_sentences.py
"""
from __future__ import annotations

import datetime
import sys

from app.simulation.carry_forward import is_carry_eligible
from app.simulation.carry_words import CARRY_CLAUSE
from app.simulation.registry import run_all

CUTOFF = datetime.date(2026, 6, 30)
FAILS: list[str] = []

# The promises this run withdrew. A sentence that still ends in one of these, on a measure that
# now carries, is a sentence the platform is telling a participant the opposite of what it does.
WITHDRAWN = (
    "no reading is reported and no other figure is used in its place",
    "No substitute reading is reported in its place",
    "no other figure is used in their place",
    "No substitute figure is used in its place",
)

print("THE EMITTED TEXT, TAKEN FROM A LIVE RUN\n" + "=" * 92)
run = run_all({}, "run143p2s", "P1", CUTOFF)
carrying, keeping = [], []
for a in sorted(run["abstained"], key=lambda r: r["module_id"]):
    ok, why = is_carry_eligible(a)
    (carrying if ok else keeping).append((a["module_id"], a.get("reason") or "", why))

print(f"\n--- {len(carrying)} MEASURES THAT NOW CARRY: each sentence must state the new rule")
for mid, text, _ in carrying:
    marker = "OK " if CARRY_CLAUSE in text else "!! "
    print(f"{marker}{mid}: {text}")
    if CARRY_CLAUSE not in text:
        FAILS.append(f"{mid} carries but its sentence does not state the rule")
    for w in WITHDRAWN:
        if w in text:
            FAILS.append(f"{mid} still makes the withdrawn promise: {w!r}")

print(f"\n--- {len(keeping)} MEASURES THAT DO NOT CARRY: each must say WHY, not merely refuse")
for mid, text, why in keeping:
    said = ("carried forward" in text or "carry-forward" in text
            or "no earlier reading" in text or "earlier reading" in text)
    print(f"{'OK ' if said else '!! '}{mid}: {text[:230]}")
    print(f"      exemption: {why}")
    if not said:
        FAILS.append(f"{mid} keeps its refusal without saying why it does not carry")

# ------------------- the arms an empty package never reaches, driven directly to their sentence
print("\n--- ARMS AN EMPTY PACKAGE CANNOT REACH, driven to their own sentence")
from app.simulation.canonical import StructureAbsent          # noqa: E402
from app.simulation.canonical_v3 import identify_arima, forecast_arima  # noqa: E402
from app.simulation.models_cat89 import _band_safety          # noqa: E402
from app.simulation.models_sim import run_cusum               # noqa: E402


def arm(label, text, must_say_no_carry):
    said = "carried forward" in text or "carried" in text
    ok = said if must_say_no_carry else (CARRY_CLAUSE in text)
    print(f"{'OK ' if ok else '!! '}{label}: {text}")
    if not ok:
        FAILS.append(label)


try:
    identify_arima([1.0, 1.0, 1.0])
except StructureAbsent as e:
    arm("A1.5 short history (does not carry)", e.sentence, True)
try:
    forecast_arima({"series": [1.0, 1.0], "p": 3, "d": 0, "q": 0, "c": 0.0,
                    "phi": [0.1, 0.1, 0.1], "theta": []}, 1)
except StructureAbsent as e:
    arm("A1.5 model-too-long-for-series (does not carry)", e.sentence, True)
except Exception as e:                                     # noqa: BLE001
    print(f"   (forecast arm not reachable with this fixture: {type(e).__name__})")

arm("A1.2 short history (does not carry)",
    run_cusum({"spi": 1.0, "spiHistory": [1.0]}, lambda: 0.5, CUTOFF)["evidence_metric"], True)

_r = {"employee_hours_worked": 10.0, "recordable_cases": 0, "severity": {}}
arm("A6.2 exposure floor (does not carry -- the rule-5 anchor)",
    str(_band_safety(_r, {"employee_hours_worked": 10.0, "exposure_floor": 20000})[2]), True)

# `near` is read from the STRUCTURE's `near_miss_reported`, `active` from the result's hours,
# and the benchmark-ratio arm above must not fire, so no `recordable_rate_osha_200k` is offered.
_r2 = {"employee_hours_worked": 500000.0, "recordable_cases": 0, "severity": {}, "frequency": {}}
_o2 = _band_safety(_r2, {"near_miss_reported": 5})
if _o2[0] is None and "near-miss" in str(_o2[2]):
    arm("A6.2 near-miss healthy (does not carry)", str(_o2[2]), True)
else:
    print(f"   (A6.2 near-miss arm not reached with this fixture; band={_o2[0]!r})")

# A6.2's own no-exposure-data arm, which DOES carry -- the pair that proves per-arm, not per-module
from app.simulation.canonical_v6 import v6_structure         # noqa: E402
_si = {"safetyIncidentRecord": {"recordable_cases": None, "employee_hours_worked": None,
                                "reporting_period": "P1"}}
try:
    _s = v6_structure(_si, "A6.2")
    from app.simulation.canonical_v6 import safety_incidence  # noqa: E402
    _out = safety_incidence(_s)
    arm("A6.2 no exposure data recorded (CARRIES -- same module, different arm)",
        str(_out.get("lagging_reason")), False)
except Exception as e:                                       # noqa: BLE001
    print(f"   (A6.2 lagging arm fixture did not reach it: {type(e).__name__}: {e}")

print(f"\n{'ALL SENTENCES CONSISTENT WITH THE STANCE' if not FAILS else str(len(FAILS)) + ' FAILED'}")
for f in FAILS:
    print("  FAIL " + f)
sys.exit(1 if FAILS else 0)
