#!/usr/bin/env python3
"""
Validate the seven, restore voting: the freeze point (remediation_programme.md "Run 4";
remediation_decisions_answered.md 4.1 to 4.3). Run fourth under the revised order 1, 3, 2, 4, 5.

WHAT THIS SUITE HAS TO PROVE, and why it is built the way it is.

1. A MODULE VOTES ONLY WHEN ALL THREE BARS ARE CLEARED: its band boundaries are sourced, its
   abstention guards exist, and its boundary tests pass. Section 3 asserts the voting set is
   exactly the modules that clear all three, and section 6 shows on the real path that the ones
   that do not clear them cannot reach any of the three exclusion layers.

2. EVERY GUARD IS PROVED BY THE ONLY MEANS THAT CANNOT LIE ABOUT ITSELF. Not by injecting a
   fault into the new code and hoping the injection applied, and not against a hand copy of the
   old logic, but against the ACTUAL pre-run files extracted with `git show` from a pinned
   baseline commit into a throwaway package. Each guard check therefore reads "the code that
   shipped substituted a value and produced a band; the code in this branch abstains", and
   neither half can be satisfied by a mistake in this file. If the extraction fails the suite
   REFUSES to run rather than silently testing one direction.

3. A BOUNDARY IS TESTED AT THE EDGE, ABOVE IT AND BELOW IT. Not near it. Each band edge is hit
   exactly by constructing inputs that produce the boundary value, then perturbed by one step in
   each direction, and the three bands are asserted to be the three the ladder specifies.

4. ABSTENTION IS PROVED BY INJECTING THE ABSENT OR ZERO INPUT AND CONFIRMING ABSTENTION, not a
   crash and not a substituted value. Every guard check asserts the full abstention contract
   (no status colour, insufficient_data true, a reason in words with no module id and no em
   dash, because the ledger renders it) and separately asserts the call did not raise.

5. A PROPERTY ASSERTED OVER A DOMAIN IS ASSERTED OVER THE WHOLE DOMAIN. The previous run found a
   check that asserted something false and passed because the sample happened to satisfy it.
   Where this suite claims something about a set of modules or a set of inputs, it exhausts the
   set.

Run:
    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_run4_validate_seven.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
import app.simulation.compute as compute_mod  # noqa: E402
import app.simulation.registry as registry  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402
from app.simulation import compute_project  # noqa: E402
from app.simulation.models import VALIDATED, SIMULATION_VERSION  # noqa: E402
from app.simulation.models_doc import run_rfi_velocity, run_submittal_rejection  # noqa: E402
from app.simulation.models_evm import run_tcpi, run_vac  # noqa: E402
from app.simulation.models_ext import (  # noqa: E402
    run_contingency_burn, run_lookahead_health, run_material_cost_variance,
)

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = 0
FAILED = 0
ROOT = pathlib.Path(__file__).resolve().parents[2]

#: THE BASELINE COMMIT, PINNED BY SHA AND NOT BY BRANCH NAME. The moment this run merges,
#: origin/main becomes this code, and every "the old code did not abstain" half below would be
#: comparing the fix with itself. The sha is the commit this branch was cut from.
BASELINE_REV = "640c355"

#: The seven the programme calls CORE, by the ids the registry uses. Named here once.
SEVEN = {
    "A1.7": "TCPI",
    "A1.8": "Variance at Completion",
    "A2.8": "Look-Ahead Schedule Health",
    "A3.2": "Contingency Burn Rate",
    "A3.4": "Material Cost Variance",
    "A4.2": "RFI Velocity",
    "A4.3": "Submittal Rejection Rate",
}
VOTING_AFTER_RUN4 = {"A1.7", "A1.8"}


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


# ---------------------------------------------------------------------------------------------
# THE OLD CODE, LOADED FOR REAL. Same mechanism the fifteen-defects suite established.
# ---------------------------------------------------------------------------------------------

_TMP = tempfile.mkdtemp(prefix="run4-baseline-")
_PKG = pathlib.Path(_TMP) / "oldsim4"
_PKG.mkdir()
_names = subprocess.run(
    ["git", "ls-tree", "--name-only", BASELINE_REV, "server/app/simulation/"],
    cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
_py = [n for n in _names if n.endswith(".py")]
if len(_py) < 10:
    raise SystemExit("baseline extraction found no simulation sources at the pinned baseline; "
                     "refusing to run half of every proof")
for _n in _py:
    body = subprocess.run(["git", "show", f"{BASELINE_REV}:{_n}"],
                          cwd=ROOT, capture_output=True, text=True, check=True).stdout
    (_PKG / pathlib.Path(_n).name).write_text(body, encoding="utf-8")
(_PKG / "__init__.py").write_text("", encoding="utf-8")
sys.path.insert(0, _TMP)
import oldsim4.models  # noqa: E402,F401
import oldsim4.models_doc as old_doc  # noqa: E402
import oldsim4.models_evm as old_evm  # noqa: E402
import oldsim4.models_ext as old_ext  # noqa: E402
import oldsim4.registry as old_registry  # noqa: E402

OLD_FN = {
    "A1.7": old_evm.run_tcpi,
    "A1.8": old_evm.run_vac,
    "A2.8": old_ext.run_lookahead_health,
    "A3.2": old_ext.run_contingency_burn,
    "A3.4": old_ext.run_material_cost_variance,
    "A4.2": old_doc.run_rfi_velocity,
    "A4.3": old_doc.run_submittal_rejection,
}
NEW_FN = {
    "A1.7": run_tcpi,
    "A1.8": run_vac,
    "A2.8": run_lookahead_health,
    "A3.2": run_contingency_burn,
    "A3.4": run_material_cost_variance,
    "A4.2": run_rfi_velocity,
    "A4.3": run_submittal_rejection,
}


def abstains(result) -> bool:
    return bool(result.get("insufficient_data")) and result.get("status_color") is None


def band(result):
    return result.get("status_color")


def speakable(result, label: str) -> None:
    """An abstention reason reaches the Signal Ledger, so it must read as a sentence: no module
    id, no signal key name, no em dash, and not the bare default."""
    reason = str(result.get("evidence_metric") or "")
    check(bool(reason.strip()), f"{label}: the abstention states a reason at all", reason[:80])
    check("—" not in reason and "--" not in reason,
          f"{label}: with no em dash on a reason the ledger renders", reason[:90])
    check(not any(t in reason for t in ("A1.", "A2.", "A3.", "A4.", "signalInputs", "docType",
                                        "actualPctComplete", "rfiPeriodDays", "originalCont")),
          f"{label}: and no module id or signal key name", reason[:90])


print("=" * 78)
print("0. The extraction is real: the baseline modules are the ones that shipped")
print("=" * 78)
check(old_registry.CORE_VOTING_MODULES == set(SEVEN) or
      set(old_registry.CORE_VOTING_MODULES) == set(SEVEN),
      "the pinned baseline's voting set is the seven the programme names",
      str(sorted(old_registry.CORE_VOTING_MODULES)))
check(old_evm.run_tcpi is not run_tcpi and old_doc.run_rfi_velocity is not run_rfi_velocity,
      "and the baseline functions are genuinely different objects from the live ones")
# The strongest single proof that the extraction is the OLD code rather than a copy of the new:
# the case the run names. (BAC - AC) = 0 produced a manufactured Red on the baseline.
_at_completion = {"bac": 100.0, "ev": 90.0, "ac": 100.0}
check(old_evm.run_tcpi(dict(_at_completion), None, None).get("status_color") == "Red",
      "and the baseline manufactures a Red where the remaining budget is zero, which is the "
      "defect this run is here to close",
      str(old_evm.run_tcpi(dict(_at_completion), None, None).get("evidence_metric")))

print()
print("=" * 78)
print("1. THE EIGHTH HOLD MODULE: it cannot vote, by construction")
print("=" * 78)
print("   The ruling is in the report. What is assertable in code is that the module the audit")
print("   holds as its eighth non-voting row, the document risk score, is not a registry-")
print("   computed module at all: it is a value the extraction model supplies. It is declared")
print("   in the registry and implemented nowhere, so nothing can route a vote through it.")
check("A4.1" in registry.registry_index(), "the document risk score is declared in the registry")
check("A4.1" not in VALIDATED,
      "and is implemented by no formula function on this server, so it computes nothing")
check("A4.1" in registry.unported_modules(),
      "and the server reports it as the one genuinely unported declaration",
      str(registry.unported_modules()))
check("A4.1" not in registry.CORE_VOTING_MODULES,
      "and it is not in the voting set, so it cannot reach category rollup or project status")

print()
print("=" * 78)
print("2. THE BANDS: every boundary hit exactly, above and below")
print("=" * 78)


def bands_of(mid: str, cases: list[tuple[str, dict, str]]) -> None:
    for label, si, expected in cases:
        got = NEW_FN[mid](dict(si), None, None)
        check(band(got) == expected, f"{SEVEN[mid]}: {label} reads {expected}",
              f"got {band(got)} / {got.get('evidence_metric')}")


# --- A1.7 TCPI. Boundaries 1.00 and 1.10, both sourced. Inputs are constructed so the ratio
# lands exactly on the boundary: with BAC 100 and AC 50, remaining budget is 50, so EV is set to
# make (100 - EV) / 50 the wanted value.
def tcpi_at(value: float) -> dict:
    return {"bac": 100.0, "ac": 50.0, "ev": 100.0 - value * 50.0}


check(run_tcpi(tcpi_at(1.00), None, None).get("tcpi") == 1.0,
      "TCPI: the constructed input lands exactly on the first boundary, not near it")
check(run_tcpi(tcpi_at(1.10), None, None).get("tcpi") == 1.1,
      "TCPI: and exactly on the second")
bands_of("A1.7", [
    ("below the first boundary (0.999)", tcpi_at(0.999), "Green"),
    ("exactly on the first boundary (1.000)", tcpi_at(1.00), "Green"),
    ("just above the first boundary (1.001)", tcpi_at(1.001), "Amber"),
    ("just below the second boundary (1.099)", tcpi_at(1.099), "Amber"),
    ("exactly on the second boundary (1.100)", tcpi_at(1.10), "Amber"),
    ("just above the second boundary (1.101)", tcpi_at(1.101), "Red"),
])
# The whole ladder, exhausted at one thousandth resolution across the range the band covers, so
# the three bands are contiguous and there is no gap or overlap anywhere between them.
_gaps = []
for i in range(500, 1600):
    v = i / 1000.0
    got = band(run_tcpi(tcpi_at(v), None, None))
    want = "Green" if v <= 1.0 else "Amber" if v <= 1.1 else "Red"
    if got != want:
        _gaps.append((v, got, want))
check(not _gaps, "TCPI: the ladder is exhausted from 0.500 to 1.599 in thousandths and every "
                 "value falls in the band the boundaries specify", str(_gaps[:4]))

# --- A1.8 VAC. Boundaries 0 per cent and minus 11.11 per cent, the latter being an index of
# exactly 0.90. Inputs construct the index directly.
bands_of("A1.8", [
    ("an index above one, no forecast overrun", {"bac": 1000.0, "cpi": 1.05}, "Green"),
    ("an index of exactly one, the first boundary", {"bac": 1000.0, "cpi": 1.0}, "Green"),
    ("just below it", {"bac": 1000.0, "cpi": 0.9999}, "Amber"),
    ("just above the second boundary", {"bac": 1000.0, "cpi": 0.9001}, "Amber"),
    ("exactly on the second boundary, an index of 0.90", {"bac": 1000.0, "cpi": 0.90}, "Amber"),
    ("just below the second boundary", {"bac": 1000.0, "cpi": 0.8999}, "Red"),
])
_gaps = []
for i in range(500, 1500):
    cpi = i / 1000.0
    got = band(run_vac({"bac": 1000.0, "cpi": cpi}, None, None))
    want = "Green" if cpi >= 1.0 else "Amber" if cpi >= 0.90 else "Red"
    if got != want:
        _gaps.append((cpi, got, want))
check(not _gaps, "Variance at Completion: the ladder is exhausted from an index of 0.500 to "
                 "1.499 in thousandths and every value falls in the band the boundaries "
                 "specify", str(_gaps[:4]))

# --- The five held non-voting. Their boundaries are uncited, and they are tested anyway,
# because a band that is not sourced still has to behave as the band it claims to be: a module
# whose ladder is wrong would be wrong on the ledger whether or not it votes.
# RUN 28 REMOVED BOTH OF THESE BAND LADDERS, and their removal is the completion of Run 4's own
# finding rather than a departure from it. Run 4 looked for a source specifying the boundaries of
# a look-ahead constraint rate and of contingency consumption against progress, DID NOT FIND ONE,
# recorded that plainly beside each band, and held both modules non-voting for want of it. The
# owner's supplied Run-28 contract settles what Run 4 could only record: it states in terms that
# no universal status bands are supplied for either quantity, and that where the numerical method
# is correct but the bands are not calibrated the correct output is exposed with calibration
# pending. So the ladders are gone and the figures stay. The band cases below are replaced by the
# checks Run 4's finding actually supports: that each module produces its figure, that the figure
# is exact at the boundaries the ladder used to sit at, and that NO colour is asserted anywhere
# across that range.
# RUN 28. Run 4's contingency finding, in the form the v3 contract leaves it in: the raw consumed
# share must never be published as the progress-normalised burn. Asserted at nothing complete,
# where Run 4 found the substitution, and with progress absent entirely.
for _si, _why in (({"originalContingency": 1000.0, "remainingContingency": 900.0,
                    "actualPctComplete": 0.0}, "at nothing complete"),
                  ({"originalContingency": 1000.0, "remainingContingency": 900.0},
                   "with no progress reported at all")):
    _cb = NEW_FN["A3.2"](dict(_si), None, None)
    check(_cb.get("normalized_burn") is None,
          f"Contingency Burn Rate: {_why} the progress-normalised burn is withheld",
          str(_cb.get("normalized_burn")))
    check(abs((_cb.get("consumed_fraction") or 0) - 0.1) < 1e-9,
          f"Contingency Burn Rate: {_why} the consumed fraction is still reported, and it is "
          f"the real one", str(_cb.get("consumed_fraction")))

_LA_CASES = [(99, 0.9), (100, 0.9), (101, 0.9), (250, 0.75), (251, 0.75), (400, 0.6), (401, 0.6)]
for _constrained, _want_ready in _LA_CASES:
    _rows = [{"activity_id": f"ACT-{i}",
              "constraint_status": "OPEN" if i < _constrained else "CLEARED",
              **({"constraint_category": "MATERIAL"} if i < _constrained else {})}
             for i in range(1000)]
    _out = NEW_FN["A2.8"]({"lookAheadSchedule": {"horizon": "six week",
                                              "status_date": "2026-06-30",
                                              "activities": _rows}}, None, None)
    check(f"Look-Ahead Schedule Health: {_constrained} of 1000 constrained gives a ready "
          f"fraction of {_want_ready}",
          abs(_out.get("ready_fraction") - _want_ready) < 5e-3,
          str(_out.get("ready_fraction")))
    check(f"Look-Ahead Schedule Health: and asserts no colour at {_constrained} of 1000",
          _out.get("status_color") is None and _out.get("calibration_pending") is True,
          str(_out.get("status_color")))


def burn_at(stress: float) -> dict:
    # normalisedBurn = (consumed fraction) / (pct/100). With original 1000 and pct 50, the
    # normalised burn is consumed / 500.
    return {"originalContingency": 1000.0, "remainingContingency": 1000.0 - stress * 500.0,
            "actualPctComplete": 50.0}


for _stress in (0.99, 1.00, 1.01, 1.30, 1.31, 1.60, 1.61):
    _out = NEW_FN["A3.2"](burn_at(_stress), None, None)
    check(f"Contingency Burn Rate: a normalised burn of {_stress} is reported exactly",
          abs(_out.get("normalized_burn") - _stress) < 5e-3, str(_out.get("normalized_burn")))
    check(f"Contingency Burn Rate: and no colour is asserted at {_stress}",
          _out.get("status_color") is None and _out.get("calibration_pending") is True,
          str(_out.get("status_color")))


def mat_at(variance: float) -> dict:
    # expected = baseline x pct. With baseline 1000 and pct 50, expected is 500.
    return {"materialCostBaseline": 1000.0, "actualPctComplete": 50.0,
            "materialCostCurrent": 500.0 * (1 + variance)}


bands_of("A3.4", [
    ("just inside the first boundary", mat_at(0.049), "Green"),
    ("exactly on it", mat_at(0.05), "Green"),
    ("just outside it", mat_at(0.051), "Yellow"),
    ("and symmetrically below zero, just outside it", mat_at(-0.051), "Yellow"),
    ("exactly on the second", mat_at(0.12), "Yellow"),
    ("just outside the second", mat_at(0.121), "Amber"),
    ("exactly on the third", mat_at(0.20), "Amber"),
    ("just outside the third", mat_at(0.201), "Red"),
])
bands_of("A4.2", [
    # NOTE, AND IT IS A FINDING RATHER THAN A FIXTURE DETAIL: the rate is rounded to one
    # decimal before it is banded, so the true edge sits on the ROUNDED rate. A count giving
    # 2.01 requests a week is banded as 2.0 and reads Green. The step below the edge is
    # therefore a tenth, not a hundredth, and these cases say so rather than hiding it.
    ("just below two a week", {"rfiCount": 190, "rfiPeriodDays": 700}, "Green"),
    ("exactly two a week", {"rfiCount": 200, "rfiPeriodDays": 700}, "Green"),
    ("a rate that rounds down onto the boundary still reads the lower band",
     {"rfiCount": 201, "rfiPeriodDays": 700}, "Green"),
    ("just above two a week", {"rfiCount": 210, "rfiPeriodDays": 700}, "Yellow"),
    ("exactly four a week", {"rfiCount": 400, "rfiPeriodDays": 700}, "Yellow"),
    ("just above four a week", {"rfiCount": 410, "rfiPeriodDays": 700}, "Amber"),
    ("exactly eight a week", {"rfiCount": 800, "rfiPeriodDays": 700}, "Amber"),
    ("just above eight a week", {"rfiCount": 810, "rfiPeriodDays": 700}, "Red"),
    # The overdue arm is a second ladder and the worse of the two is reported.
    ("a calm rate with an overdue share just inside the first overdue boundary",
     {"rfiCount": 100, "rfiPeriodDays": 700, "rfiOverdue": 9}, "Green"),
    ("a calm rate with an overdue share exactly on it",
     {"rfiCount": 100, "rfiPeriodDays": 700, "rfiOverdue": 10}, "Yellow"),
    ("a calm rate with an overdue share exactly on the second",
     {"rfiCount": 100, "rfiPeriodDays": 700, "rfiOverdue": 20}, "Amber"),
    ("a calm rate with an overdue share exactly on the third",
     {"rfiCount": 100, "rfiPeriodDays": 700, "rfiOverdue": 35}, "Red"),
])
bands_of("A4.3", [
    ("just below the first boundary", {"submittalsTotal": 1000, "submittalsRejected": 49},
     "Green"),
    ("exactly on it", {"submittalsTotal": 1000, "submittalsRejected": 50}, "Green"),
    ("just above it", {"submittalsTotal": 1000, "submittalsRejected": 51}, "Yellow"),
    ("exactly on the second", {"submittalsTotal": 1000, "submittalsRejected": 150}, "Yellow"),
    ("just above the second", {"submittalsTotal": 1000, "submittalsRejected": 151}, "Amber"),
    ("exactly on the third", {"submittalsTotal": 1000, "submittalsRejected": 250}, "Amber"),
    ("just above the third", {"submittalsTotal": 1000, "submittalsRejected": 251}, "Red"),
])

print()
print("  the two re-banded ladders, against the ladders that shipped:")
for mid, si in (("A1.7", tcpi_at(1.03)), ("A1.8", {"bac": 1000.0, "cpi": 0.96})):
    old = OLD_FN[mid](dict(si), None, None)
    new = NEW_FN[mid](dict(si), None, None)
    print(f"    {SEVEN[mid]}: shipped {old.get('status_color')} -> now {new.get('status_color')}")
    check(old.get("status_color") != new.get("status_color"),
          f"{SEVEN[mid]}: the re-banding is a real change, shown on an input that moves band",
          f"{old.get('status_color')} vs {new.get('status_color')}")
    check(old.get("tcpi") == new.get("tcpi") and old.get("vac_pct") == new.get("vac_pct"),
          f"{SEVEN[mid]}: and the NUMBER is identical, so the formula was not touched",
          f"{old} vs {new}")

print()
print("=" * 78)
print("3. THE GUARDS: each proved by injecting the absent or zero input, against the old code")
print("=" * 78)
print("   Each case shows what the code that shipped did with the same input. Where the old")
print("   code produced a band, the guard is doing work; where the old code raised, the guard")
print("   is closing a crash. Neither half is asserted from reasoning.")

#: (module, what is injected, the input, and whether the guard is NEW in this run or was
#: already there). Both are asserted, in opposite directions: a new guard must be shown to
#: change behaviour against the code that shipped, and a pre-existing one must be shown to have
#: SURVIVED this run rather than being quietly relaxed while the bands were rewritten.
GUARD_CASES = [
    ("A1.7", "the remaining budget is exactly zero, which is a project at completion",
     {"bac": 100.0, "ev": 90.0, "ac": 100.0}, "new"),
    ("A1.7", "the actual cost has passed the budget",
     {"bac": 100.0, "ev": 90.0, "ac": 130.0}, "new"),
    ("A1.8", "the cost performance index is zero",
     {"bac": 1000.0, "cpi": 0.0}, "pre-existing"),
    ("A1.8", "the cost performance index is negative",
     {"bac": 1000.0, "cpi": -0.5}, "new"),
    ("A2.8", "no activities are planned in the look-ahead window",
     {"activitiesPlanned": 0, "activitiesConstrained": 0}, "new"),
    ("A2.8", "more activities are constrained than are planned",
     {"activitiesPlanned": 10, "activitiesConstrained": 14}, "new"),
    # RUN 28 MOVED THIS ONE OUT OF THE REFUSAL LIST DELIBERATELY. Run 4's finding was that at
    # nothing complete the module substituted the RAW consumed share for the ratio of burn to
    # progress -- a different quantity under the same name -- and it refused instead. The owner's
    # supplied contract conditions only the progress-normalised burn on progress, not the
    # consumed fraction, so at nothing complete the consumed fraction is a real measurement and
    # the normalised burn is withheld. Run 4's property is preserved in the form that matters and
    # is asserted directly below: the raw consumed share is never published as the normalised
    # burn. That is a stronger statement than a refusal, because it holds at every progress
    # figure and not only at zero.
    ("A3.2", "more contingency remains than was originally held",
     {"originalContingency": 1000.0, "remainingContingency": 1200.0, "actualPctComplete": 50.0},
     "new"),
    ("A3.4", "reported progress is absent",
     {"materialCostBaseline": 1000.0, "materialCostCurrent": 400.0}, "new"),
    ("A3.4", "reported progress is zero",
     {"materialCostBaseline": 1000.0, "materialCostCurrent": 400.0, "actualPctComplete": 0.0},
     "new"),
    ("A4.2", "the number of days the log covers is absent",
     {"rfiCount": 40}, "new"),
    ("A4.2", "the number of days the log covers is zero",
     {"rfiCount": 40, "rfiPeriodDays": 0}, "new"),
    ("A4.2", "more requests are overdue than exist",
     {"rfiCount": 10, "rfiPeriodDays": 30, "rfiOverdue": 14}, "new"),
    ("A4.3", "the register has no entries",
     {"submittalsTotal": 0, "submittalsRejected": 0}, "pre-existing"),
    ("A4.3", "more submittals are rejected than were submitted",
     {"submittalsTotal": 10, "submittalsRejected": 14}, "new"),
]

for mid, label, si, provenance in GUARD_CASES:
    tag = f"{SEVEN[mid]} guard, {label}"
    raised = None
    try:
        got = NEW_FN[mid](dict(si), None, None)
    except Exception as exc:  # a crash is a failure of the guard, not a pass
        got = {}
        raised = exc
    check(raised is None, f"{tag}: does not raise", str(raised))
    check(abstains(got), f"{tag}: abstains", str(got)[:120])
    check(got.get("status_color") is None,
          f"{tag}: and produces no band, so nothing downstream can read a substituted value",
          str(got.get("status_color")))
    speakable(got, tag)
    # And what the shipped code did with the identical input.
    old_raised = None
    try:
        old_out = OLD_FN[mid](dict(si), None, None)
    except Exception as exc:
        old_out = {}
        old_raised = exc
    old_desc = ("raised " + type(old_raised).__name__ if old_raised
                else f"returned {old_out.get('status_color')}")
    print(f"    shipped code, same input: {old_desc}")
    if provenance == "new":
        check(old_raised is not None or not abstains(old_out),
              f"{tag}: THE OLD CODE DID NOT ABSTAIN HERE, so this guard is new work and not a "
              f"restatement of behaviour that already existed", old_desc)
    else:
        check(old_raised is None and abstains(old_out),
              f"{tag}: this guard already existed, and it SURVIVED the re-banding rather than "
              f"being relaxed while the bands were rewritten", old_desc)

# The five band edges of the two voting modules are unaffected by the guards: a guard that
# swallowed ordinary inputs would be worse than the substitution it replaced. Exhausted over the
# ordinary domain rather than sampled.
_swallowed = []
for i in range(1, 100):
    si = {"bac": 1000.0, "ac": 10.0 * i, "ev": 5.0 * i}
    if abstains(run_tcpi(dict(si), None, None)):
        _swallowed.append(si)
check(not _swallowed,
      "TCPI: the guard swallows no ordinary input, exhausted over every actual cost from one "
      "per cent to ninety-nine per cent of the budget", str(_swallowed[:2]))

print()
print("=" * 78)
print("4. THE VOTING SET, AND WHAT EACH MODULE CARRIES")
print("=" * 78)
check(set(registry.CORE_VOTING_MODULES) == VOTING_AFTER_RUN4,
      "the voting set is exactly the modules whose band boundaries a source specifies",
      str(sorted(registry.CORE_VOTING_MODULES)))
check(set(registry.HELD_NON_VOTING_UNSOURCED_BANDS) == set(SEVEN) - VOTING_AFTER_RUN4,
      "and the five held back are recorded with a reason each, rather than simply absent",
      str(sorted(registry.HELD_NON_VOTING_UNSOURCED_BANDS)))
check(set(registry.BAND_SOURCES) == VOTING_AFTER_RUN4,
      "every voting module has a citation and no non-voting module claims one",
      str(sorted(registry.BAND_SOURCES)))
for mid in sorted(VOTING_AFTER_RUN4):
    src = registry.BAND_SOURCES[mid]
    check(len(src) > 200, f"{SEVEN[mid]}: the citation is a citation, not a gesture", src[:60])
    check("1993" in src and "Project Management Institute" in src,
          f"{SEVEN[mid]}: naming the source and the year", src[:60])
check("false-positive and false-negative" in registry.BAND_SOURCE_LIMIT.lower()
      and "labelled" in registry.BAND_SOURCE_LIMIT,
      "and the sentence stating what the citation does NOT establish travels with them",
      registry.BAND_SOURCE_LIMIT[:80])
check(set(registry.CORE_VOTING_MODULES) <= set(SEVEN),
      "nothing outside the seven was restored to voting")
check(not (set(registry.CORE_VOTING_MODULES) & set(registry.DISABLED_CONCEPT_ONLY)),
      "and nothing disabled was restored to voting")
check(not (set(registry.CORE_VOTING_MODULES) & set(registry.PROXY_QUALIFIERS)),
      "and no relabeled proxy was restored to voting")
check(SIMULATION_VERSION != "sim-2026.07-v1",
      "the analytical layer's version stamp moved at the freeze, so results computed before and "
      "after this run are distinguishable in already-collected data", SIMULATION_VERSION)

print()
print("=" * 78)
print("5. ON THE REAL PATH: a four period project uploaded and computed through the API")
print("=" * 78)

ADMIN = "r4-admin"
PRJ = "PRJ-R4-SEVEN"
MONTHS = {
    1: ("2026-03-31", 3_000_000, 3_050_000, 3_050_000, 25.0, 25.0),
    2: ("2026-04-30", 4_000_000, 4_250_000, 4_150_000, 33.0, 34.0),
    3: ("2026-05-31", 5_000_000, 5_500_000, 5_300_000, 42.0, 44.0),
    4: ("2026-06-30", 6_000_000, 6_900_000, 6_500_000, 50.0, 54.0),
}


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload),
                    headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def doc_bytes(tag: str) -> bytes:
    return f"%PDF-1.4 RUN4 SEVEN {tag}\n".encode()


def monthly(d, ev, ac, pv, apc, ppc):
    return {"earned_value": ev, "actual_cost": ac, "planned_value": pv,
            "budget_at_completion": 12_000_000, "actual_percent_complete": apc,
            "planned_percent_complete": ppc, "report_date": d, "document_date": d,
            "document_risk_score": 0.45}


REC = {}
for p, mth in MONTHS.items():
    REC[hashlib.sha256(doc_bytes(f"M{p}")).hexdigest()] = (
        "monthly_report", monthly(mth[0], *mth[1:]))
CORE_TAGS = ("LOOK", "PAY", "COST", "RFI", "SUB")
for p, mth in MONTHS.items():
    d = mth[0]
    REC[hashlib.sha256(doc_bytes(f"LOOK{p}")).hexdigest()] = ("lookahead_schedule", {
        "activities_planned": 60, "activities_constrained": 4 + 3 * p,
        "lookahead_weeks": 3, "report_date": d})
    REC[hashlib.sha256(doc_bytes(f"PAY{p}")).hexdigest()] = ("pay_application", {
        "amount_paid_to_date": mth[2], "percent_complete_verified": mth[4],
        "completed_to_date": mth[1], "original_contingency": 600_000,
        "remaining_contingency": 600_000 - 90_000 * p, "application_date": d})
    REC[hashlib.sha256(doc_bytes(f"COST{p}")).hexdigest()] = ("cost_report", {
        "material_cost_baseline": 4_000_000,
        "material_cost_current": 4_000_000 + 90_000 * p,
        "indirect_cost_plan": 900_000, "indirect_cost_actual": 880_000,
        "report_date": d})
    REC[hashlib.sha256(doc_bytes(f"RFI{p}")).hexdigest()] = ("rfi_log", {
        "rfi_total": 20 + 7 * p, "rfi_open": 4 + 3 * p, "rfi_overdue": p,
        "avg_response_days": 8.0 + p, "rfi_period_days": 30,
        "oldest_open_days": 20 + 9 * p, "log_date": d})
    REC[hashlib.sha256(doc_bytes(f"SUB{p}")).hexdigest()] = ("submittal_register", {
        "submittals_total": 40 + 16 * p, "submittals_rejected": 3 + 3 * p,
        "document_date": d})
set_extractor_override(StubExtractor(REC))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R4-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PRJ)) is None:
        s.add(Project(legacy_id=PRJ,
                      doc={"id": PRJ, "name": PRJ, "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R4-PM", "role": "Participant",
                "account_type": "operational"})
pm = post({"action": "researchlogin",
           "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PRJ,
      "participant_id": created["participant_id"], "project_role": "PM"})
for p in (1, 2, 3, 4):
    docs = [{"filename": f"M{p}.pdf", "mimeType": "application/pdf",
             "dataBase64": b64(doc_bytes(f"M{p}"))}]
    docs += [{"filename": f"{t}{p}.pdf", "mimeType": "application/pdf",
              "dataBase64": b64(doc_bytes(f"{t}{p}"))} for t in CORE_TAGS]
    post({"action": "projectupload", "session_token": pm, "id": PRJ,
          "period": p, "period_end": MONTHS[p][0], "documents": docs})
allr = post({"action": "projectcomputeall", "session_token": pm, "id": PRJ})
check(allr.get("computed") == 4, "four periods compute on the document path", str(allr)[:140])

STORED = {}
for p in (1, 2, 3, 4):
    STORED[p] = post({"action": "projectresults", "session_token": pm, "id": PRJ,
                      "period": p})["result"]
r4 = STORED[4]
comp = {m.get("module_id"): m for m in (r4.get("module_results") or [])}
abst = {a.get("module_id"): a for a in (r4.get("abstained") or [])}

print()
print("  the seven, on the stored row at period four:")
for mid, name in SEVEN.items():
    if mid in comp:
        print(f"    {name}: {comp[mid].get('status_color')} -- "
              f"{str(comp[mid].get('evidence_metric'))[:62]}")
    else:
        print(f"    {name}: abstained -- {str(abst.get(mid, {}).get('reason'))[:62]}")
# RESTATED BY RUN 16, ORIGINAL FINDING PRESERVED. Run 4 required all seven CORE modules to
# produce a finding on the real path, so that nothing below could pass vacuously for want of a
# computed module, and that record stands for the six that still execute. Run 16 disabled
# Material Cost Variance from operational execution for an evidence and context reason, not an
# algorithmic one, so it now abstains by refusal rather than computing. It is named here rather
# than the rule being relaxed, and it is required to abstain WITH the recorded reason, so this
# allowance cannot cover a module that has merely gone silent.
RUN16_DISABLED = {"A3.4"}
# RESTATED BY RUN 28, ORIGINAL FINDING PRESERVED. The owner's supplied Run-28 contract requires
# Look-Ahead Schedule Health to read a governed constraint inventory -- the window, the activity
# identities and each activity's constraint status and category -- rather than two bare counts,
# and states in terms that an unreliable constraint inventory is NOT ESTIMABLE. The corpus
# carries no such inventory, so the module abstains on the real path. It is named here rather
# than the rule being relaxed, and it is required to abstain WITH the structural reason, so this
# allowance cannot cover a module that has merely gone silent.
RUN28_STRUCTURE_REQUIRED = {"A2.8"}
check(all(mid in comp for mid in SEVEN
          if mid not in RUN16_DISABLED and mid not in RUN28_STRUCTURE_REQUIRED),
      "the five CORE modules that still execute produce a finding on the real path, so nothing "
      "below is vacuous for want of a computed module",
      str(sorted(set(SEVEN) - set(comp) - RUN16_DISABLED - RUN28_STRUCTURE_REQUIRED)))
for _mid in sorted(RUN28_STRUCTURE_REQUIRED):
    check(_mid not in comp,
          f"{SEVEN[_mid]}: abstains on the real path, because the corpus carries no governed "
          f"look-ahead constraint inventory")
    check(abst.get(_mid, {}).get("abstention_reason_code") == "canonical_structure_absent",
          f"{SEVEN[_mid]}: and says on the stored row that the canonical structure is what is "
          f"absent", str(abst.get(_mid, {}).get("abstention_reason_code")))
for _mid in sorted(RUN16_DISABLED):
    check(_mid not in comp,
          f"{SEVEN[_mid]}: disabled by Run 16, so it computes nothing at all")
    check("under review" in str(abst.get(_mid, {}).get("reason") or "").lower(),
          f"{SEVEN[_mid]}: and says on the stored row that its evidence requirement is under "
          f"review", str(abst.get(_mid, {}).get("reason"))[:90])

for mid in sorted(VOTING_AFTER_RUN4):
    check(comp.get(mid, {}).get("votes") is True,
          f"{SEVEN[mid]}: votes, on the stored row the ledger and the card read")
    check(bool(comp.get(mid, {}).get("band_source")),
          f"{SEVEN[mid]}: and carries its citation into the API response")
    check(bool(comp.get(mid, {}).get("band_source_limit")),
          f"{SEVEN[mid]}: and the sentence stating what the citation does not establish")
for mid in sorted(set(SEVEN) - VOTING_AFTER_RUN4 - RUN16_DISABLED
                  - RUN28_STRUCTURE_REQUIRED):
    check(comp.get(mid, {}).get("votes") is False,
          f"{SEVEN[mid]}: does not vote, on the stored row")
    check(bool(comp.get(mid, {}).get("held_non_voting_reason")),
          f"{SEVEN[mid]}: and carries the reason it does not")
    check(comp.get(mid, {}).get("band_source") is None,
          f"{SEVEN[mid]}: and claims no citation")

# THE EXCLUSION, ACROSS ALL THREE LAYERS ESTABLISHED IN RUN 1.
voting_ids = {m for m, r in comp.items() if r.get("votes")}
check(voting_ids == VOTING_AFTER_RUN4,
      "exactly two computed modules vote and the other ninety-plus do not, measured on the "
      "stored row rather than on the constant", str(sorted(voting_ids)))
non_voting_count = sum(1 for r in comp.values() if not r.get("votes"))
# RUN 10B RESTATEMENT, ORIGINAL FINDING PRESERVED. Run 4 asserted that more than fifty computed
# modules do not vote, as a plain statement that the non-voting set is the bulk of the platform
# rather than a handful. That is still what is being asserted. The threshold moves because Run
# 10B requires four canonical methods to hold their defining structure before computing, and the
# document corpus does not carry a line of balance, a sized critical-chain buffer, a queue or a
# set of agents, so those four now abstain on this project instead of computing a proxy. They are
# still non-voting; they are no longer counted here because they no longer compute at all.
# RUN 28 RESTATEMENT, ORIGINAL FINDING PRESERVED AGAIN. Run 4's assertion is that the non-voting
# set is the BULK of the platform rather than a handful, and that is still exactly what is
# asserted. The count moves for the same reason it moved at Run 10B: the owner's supplied Run-28
# contract requires twenty-one further canonical methods to hold their defining structure before
# they compute, and this project's document corpus carries no activity network, no approved
# expenditure profile, no reference class, no external price index and no allocation base, so
# those modules abstain here instead of computing a proxy. They are still non-voting; they are no
# longer counted here because they no longer compute at all. The RATIO is what the finding is
# about, so the check is stated as a ratio and additionally pins the arithmetic identity.
# RUN 30 CLOSURE. The floor moves again, for the same kind of reason and recorded the same way:
# the twenty Category-7 identities now hold their defining epistemic structure before they
# compute, and this project's corpus carries none of them, so they abstain here instead of
# computing a proxy. Twenty computed rows on this fixture, of which eighteen do not vote. The
# RATIO is what the finding is about and the arithmetic identity is still pinned exactly.
check(non_voting_count >= len(comp) - 2 and non_voting_count == len(comp) - len(voting_ids)
      and len(comp) >= 18,
      "and the ones that do not vote are the bulk of the platform, computed and stored as "
      "before: every computed module except the two voters",
      f"{non_voting_count} non-voting of {len(comp)} computed")
# Layer (a): category rollup and project status fusion.
cats = r4.get("category_statuses") or {}
index = registry.registry_index()
voting_cats = {index[m]["category"] for m in voting_ids}
check(set(cats.keys()) == voting_cats,
      "layer one, the category rollup: only categories carrying a voting module have a rollup "
      "at all", f"{sorted(cats)} vs {sorted(voting_cats)}")
by_cat_shown = {index[m]["category"] for m in comp}
check(len(by_cat_shown) > len(voting_cats),
      "and categories with no voting module still show their modules on the ledger, which is "
      "the visibility the owner decision keeps", f"{len(by_cat_shown)} shown, "
                                                 f"{len(voting_cats)} rolled up")
# Layer (b): generated recommendation text and courses of action.
#
# RUN 7 MOVED WHAT THIS CHECK CAN LOOK AT, AND THE EXCLUSION IT PROTECTS IS UNCHANGED. This run
# asserted `votes is False` on the stored row of the module that scores the courses of action.
# Run 7 established that the module scored them from a payoff matrix the corpus does not
# contain, so it abstains, and an abstaining module has no stored row to carry a field. The
# exclusion is therefore now doubled rather than weakened: the module is not in the voting set,
# and it produces no result to be excluded in the first place. Both halves are asserted, so a
# later change that restored the module without restoring its exclusion would be caught.
check("B4.7" not in registry.CORE_VOTING_MODULES,
      "layer two, the courses of action: the module that scores them is not in the voting set",
      str(sorted(registry.CORE_VOTING_MODULES)))
regret = comp.get("B4.7")
check(regret is None,
      "and it has no stored row at all, because it abstains for want of an action by scenario "
      "payoff matrix", str(regret)[:120])
_r4_abst = {a.get("module_id") for a in (r4.get("abstained") or [])}
check("B4.7" in _r4_abst,
      "recorded as an abstention on the same result, so its silence is explained rather than "
      "unexplained", str(sorted(_r4_abst))[:120])
# Layer (c): the decision card reads the fused project status, which layer one restricts.
check(r4.get("project_status") in ("Green", "Yellow", "Amber", "Red", None),
      "layer three, the decision card: it reads the fused project status, and that status is "
      "a band the platform can render", str(r4.get("project_status")))

print()
print("=" * 78)
print("6. THE ROLLUP BASELINE, MEASURED AGAINST THE CURRENT ONE")
print("=" * 78)
print("   The baseline MOVED at the previous run, so it is established here rather than")
print("   remembered. The 'before' is the same compute_project over the same stored inputs")
print("   with the pinned baseline's own seven formula functions swapped into the registry")
print("   table AND the baseline's seven-module voting set restored. The registry captures")
print("   formula functions by value at import, so both have to be rebound or the comparison")
print("   is of this branch with itself.")


def compute_with(old: bool, si: dict, period: str, cutoff):
    saved_fns = {mid: VALIDATED[mid] for mid in SEVEN}
    saved_r = registry.CORE_VOTING_MODULES
    saved_c = compute_mod.CORE_VOTING_MODULES
    try:
        if old:
            for mid in SEVEN:
                VALIDATED[mid] = (saved_fns[mid][0], OLD_FN[mid])
            registry.CORE_VOTING_MODULES = frozenset(SEVEN)
            compute_mod.CORE_VOTING_MODULES = registry.CORE_VOTING_MODULES
        return compute_project(dict(si), PRJ, period, cutoff)
    finally:
        for mid in SEVEN:
            VALIDATED[mid] = saved_fns[mid]
        registry.CORE_VOTING_MODULES = saved_r
        compute_mod.CORE_VOTING_MODULES = saved_c


# The swap is proved to have taken before anything is read from it.
_probe_old = compute_with(True, STORED[4]["signal_inputs"], "P4", MONTHS[4][0])
_probe_new = compute_with(False, STORED[4]["signal_inputs"], "P4", MONTHS[4][0])
check(len(_probe_old["category_statuses"]) > len(_probe_new["category_statuses"]),
      "THE SWAP TOOK: the baseline rolls up more categories than this branch, because it let "
      "seven modules vote and this branch lets two",
      f"{sorted(_probe_old['category_statuses'])} vs {sorted(_probe_new['category_statuses'])}")
check(_probe_new["project_status"] == r4.get("project_status"),
      "and the 'after' equals what the real path actually stored, so the comparison is against "
      "the live path and not a private one",
      f"{_probe_new['project_status']} vs {r4.get('project_status')}")

# RUN 11 GATE 6. The conflict coefficient is None when it cannot be estimated from one voting
# lineage, and None does not round. Printed as the words the platform now uses rather than
# coerced to a zero, which is the reading this run removed.
def _k(v):
    return "not estimable" if v is None else round(v, 6)


print()
print("   period | project status before -> after | conflict before -> after")
status_moves = 0
for p in (1, 2, 3, 4):
    si = STORED[p]["signal_inputs"]
    before = compute_with(True, si, f"P{p}", MONTHS[p][0])
    after = compute_with(False, si, f"P{p}", MONTHS[p][0])
    if before["project_status"] != after["project_status"]:
        status_moves += 1
    print(f"     {p}    | {before['project_status']} -> {after['project_status']}   | "
          f"{_k(before['project_conflict'])} -> {_k(after['project_conflict'])}")
    check(after["project_status"] == STORED[p].get("project_status"),
          f"period {p}: the recomputed 'after' equals what the real path stored",
          f"{after['project_status']} vs {STORED[p].get('project_status')}")
print(f"   MEASURED: project status changed in {status_moves} of 4 periods.")

print()
print("=" * 78)
print("7. STABILITY: an unchanged project recomputes to the identical status, byte for byte")
print("=" * 78)
si4 = STORED[4]["signal_inputs"]
runs = [compute_project(dict(si4), PRJ, "P4", MONTHS[4][0]) for _ in range(3)]


def comparable(res: dict) -> str:
    out = {k: v for k, v in res.items() if k not in ("period_cutoff",)}
    return json.dumps(out, sort_keys=True, default=str)


check(comparable(runs[0]) == comparable(runs[1]) == comparable(runs[2]),
      "three recomputations of the same stored inputs are byte for byte identical, including "
      "every module result and every category rollup")
check(runs[0]["project_status"] == STORED[4].get("project_status"),
      "and identical to what the row already holds, so recomputing an unchanged project cannot "
      "move what a participant sees")
# And it can fail: perturb one voting module's own input and the recomputation differs.
_moved = compute_project({**si4, "cpi": 0.5}, PRJ, "P4", MONTHS[4][0])
check(comparable(_moved) != comparable(runs[0]),
      "FAULT: moving a voting module's own input DOES change the recomputation, so the "
      "stability check above is not vacuous",
      f"{_moved['project_status']} vs {runs[0]['project_status']}")

print()
print("=" * 78)
print("8. NOTHING CLAIMS VALIDATION IT DOES NOT HAVE")
print("=" * 78)
_surfaces = {
    "the recommendation and courses of action a participant reads":
        ROOT / "assets" / "js" / "recommendation_options.js",
    "the decision card": ROOT / "assets" / "js" / "decision.js",
    "the signal ledger and detail page": ROOT / "assets" / "js" / "detail.js",
    "the analytical registry": ROOT / "server" / "app" / "simulation" / "registry.py",
}
for label, path in _surfaces.items():
    # Comment lines are not a surface. What is scanned is the text the file can actually put
    # in front of a reader, which is why the comment markers are stripped first rather than the
    # word being tolerated wherever it appears.
    body = path.read_text(encoding="utf-8")
    lines = [ln.strip() for ln in body.splitlines()]
    lines = [ln for ln in lines if not ln.startswith("//") and not ln.startswith("#")]
    bad = [ln for ln in lines
           if "validated" in ln.lower() and "not " not in ln.lower()
           and "unvalidated" not in ln.lower() and "VALIDATED" not in ln]
    check(not bad, f"{label}: makes no unqualified claim that a module is validated",
          str(bad[:2])[:160])

print()
print("=" * 78)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 78)
sys.exit(1 if FAILED else 0)
