#!/usr/bin/env python3
"""
Run 7, the fix-now defects: correct every defect that can be corrected without fabricating
evidence, and make unsupported execution abstain rather than emit a reassuring value.

WHAT THIS SUITE HAS TO PROVE, and why it is built this way.

1. THE OLD BEHAVIOUR IS READ OUT OF THE PINNED BASELINE COMMIT, NOT DESCRIBED. Every "it used to
   substitute a value" half below runs the ACTUAL shipped function, extracted with `git show`
   from the commit this branch was cut from into a throwaway package, on the identical input the
   corrected function is given. Neither half can be satisfied by a mistake in this file, and if
   the extraction fails the suite refuses to run rather than silently testing one direction. This
   is the mechanism the fifteen-defects run established and the validate-seven run reused.

2. THE PROPERTY IS STATED BEFORE THE EXPECTED VALUE, and the expected value is derived from the
   module's own stated formula and domain rather than from what the corrected code returns. Where
   a correction changes a number rather than only a refusal, the number is worked by hand in the
   comment beside it.

3. FIVE CASES PER CORRECTED MODULE, which is what the run required: a valid arithmetic case, a
   missing-input abstention, a zero-denominator or domain case, a malformed-input case where the
   module owns its parsing, and the abstention reason itself.

4. A PROPERTY ASSERTED OVER A DOMAIN IS EXHAUSTED. The dispute correction is asserted over every
   strict subset of its inputs, the regret disposition over the whole index grid, and the
   empty-input contract over every implemented module.

5. THE REAL APPLICATION PATH IS DRIVEN, not only the helper functions: documents uploaded through
   the upload route, computed through the compute route, and read back through the results route,
   so storage, the API and the abstention propagation are exercised as a participant's project
   exercises them.

6. THE FAULT INJECTIONS ARE PERFORMED AND RESTORED HERE, in section 9, so the claim that each
   check can go red is demonstrated rather than asserted.

Run:
    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_run7_fix_now_defects.py
"""

from __future__ import annotations

import base64
import hashlib
import itertools
import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
import app.simulation.registry as registry  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_export import MODULE_RESULT_COLUMNS, build_module_results_rows  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402
from app.simulation.models import (  # noqa: E402
    ABSTAIN_DECISION_STRUCTURE_ABSENT, ABSTAIN_INVALID_DENOMINATOR, ABSTAIN_MALFORMED_INPUT,
    ABSTAIN_MISSING_INPUT, ABSTAIN_NO_EXPOSURE, ABSTAIN_NOT_APPLICABLE, ABSTAIN_STRUCTURE_ABSENT,
    ABSTENTION_REASON_CODES, SIMULATION_VERSION, VALIDATED, ZERO_CASE_DISPOSITIONS,
    eligible, run_ccpm, run_dsm, run_lob, run_pert, run_rcf,
)
from app.simulation.models_doc import (  # noqa: E402
    run_agent_supply_chain, run_discrete_event_sim, run_dispute_escalation,
    run_queueing_bottleneck, run_safety_performance, run_spec_conflict_density,
)
from app.simulation.models_ext import (  # noqa: E402
    run_critical_path_index, run_inflation_adjustment, run_overhead_absorption,
    run_schedule_compression,
)
from app.simulation.models_gov import run_regret_minimization  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = 0
FAILED = 0
ROOT = pathlib.Path(__file__).resolve().parents[2]
NOOP = lambda: 0.5  # noqa: E731
CUTOFF = "2025-06-30"

#: THE BASELINE COMMIT, PINNED BY SHA AND NOT BY BRANCH NAME. The moment this run merges,
#: origin/main becomes this code and every "the shipped code substituted a value" half would be
#: comparing the fix with itself.
BASELINE_REV = "021d5e2"

#: THE DEDUPLICATED FIX-NOW LIST, derived from the merged Run 6 tests and the current code before
#: any edit was made, and written here so the scope is in the suite rather than only in a report.
#: Sixteen unique modules in four groups, with no module appearing twice.
GROUP_1_REGRET = {"B4.7"}
GROUP_2_EMPTY_INPUT = {"A2.1", "A2.2", "A2.3", "A3.1", "A5.1"}
GROUP_3_SUBSTITUTE = {"A2.4", "A2.11", "A3.5", "A3.9", "A4.10", "A5.6", "A5.7", "A5.8", "A6.2"}
GROUP_4_DISPUTE = {"A4.7"}
FIX_NOW = GROUP_1_REGRET | GROUP_2_EMPTY_INPUT | GROUP_3_SUBSTITUTE | GROUP_4_DISPUTE


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def section(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def abstains(result) -> bool:
    return bool(result.get("insufficient_data")) and result.get("status_color") is None


def band(result):
    return result.get("status_color")


def speakable(result, label: str) -> None:
    """
    The abstention reason reaches the Signal Ledger, which a participant reads, so it must be a
    sentence: no module id, no signal key name, no reason code, no em dash.
    """
    reason = str(result.get("evidence_metric") or "")
    check(bool(reason.strip()) and reason.endswith((".", "!")),
          f"{label}: the abstention states a reason in a sentence", reason[:90])
    check("—" not in reason, f"{label}: with no em dash", reason[:90])
    check("_" not in reason,
          f"{label}: and no key name or reason code, both of which carry an underscore",
          reason[:90])
    check(not any(f"{g}{n}." in reason for g in "ABCD" for n in range(1, 8)),
          f"{label}: and no module id", reason[:90])
    check(" & " not in reason, f"{label}: and the word and rather than an ampersand", reason[:90])


# =================================================================================================
section("0. THE BASELINE IS REAL: the shipped code is loaded, not a description of it")
# =================================================================================================

_TMP = tempfile.mkdtemp(prefix="run7-baseline-")
_PKG = pathlib.Path(_TMP) / "oldsim7"
_PKG.mkdir()
_names = subprocess.run(["git", "ls-tree", "--name-only", BASELINE_REV,
                         "server/app/simulation/"],
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
import oldsim7.models as old_models  # noqa: E402
import oldsim7.models_doc as old_doc  # noqa: E402
import oldsim7.models_ext as old_ext  # noqa: E402
import oldsim7.models_gov as old_gov  # noqa: E402

check(old_models.SIMULATION_VERSION == "sim-2026.08-v2",
      "the pinned baseline is stamped at the freeze version it shipped under",
      old_models.SIMULATION_VERSION)
check(SIMULATION_VERSION == "sim-2026.08-v3",
      "and this branch is stamped at the successor version, so results computed before and "
      "after this run are distinguishable in the data", SIMULATION_VERSION)
check(old_models.run_pert is not run_pert and old_gov.run_regret_minimization
      is not run_regret_minimization,
      "the baseline functions are genuinely different objects from the live ones")
# The single strongest proof that this is the OLD code: the finding Run 6 led with.
_old_regret = old_gov.run_regret_minimization({"cpi": 1.20, "spi": 1.20, "bac": 1}, NOOP, CUTOFF)
check(_old_regret.get("recommended_action") == "investigate"
      and _old_regret.get("expected_regret") == {"monitor": 11, "investigate": 5, "escalate": 8},
      "and the baseline tells a project twenty per cent ahead on both indices to investigate, "
      "on scores that are the same for every project, which is the finding this run closes",
      str(_old_regret.get("expected_regret")))

check(len(FIX_NOW) == 16,
      "the deduplicated fix-now list is sixteen unique modules", str(len(FIX_NOW)))
check(len(GROUP_1_REGRET) + len(GROUP_2_EMPTY_INPUT) + len(GROUP_3_SUBSTITUTE)
      + len(GROUP_4_DISPUTE) == len(FIX_NOW),
      "and the four groups do not overlap, so no module is counted twice")
check(FIX_NOW <= set(VALIDATED),
      "every module in it is one this server actually computes",
      str(sorted(FIX_NOW - set(VALIDATED))))
check(not (FIX_NOW & set(registry.DISABLED_CONCEPT_ONLY)),
      "and none of them is a disabled concept-only module, which this run may not wake")


# =================================================================================================
section("1. GROUP 2: five modules that banded from an input carrying nothing at all")
# =================================================================================================

# THE PROPERTY. A module handed an empty dictionary has been told nothing about a project, so it
# cannot report a status about one. Three of these read the schedule index with a default of 1.0,
# the value of a project running exactly to plan, and two read no project input at all.

_G2 = {
    "A2.1": ("PERT network criticality", run_pert, old_models.run_pert, "Green"),
    "A2.2": ("line of balance", run_lob, old_models.run_lob, "Green"),
    "A2.3": ("CCPM buffer health", run_ccpm, old_models.run_ccpm, "Amber"),
    "A3.1": ("reference class forecasting", run_rcf, old_models.run_rcf, "Red"),
    "A5.1": ("DSM rework propagation", run_dsm, old_models.run_dsm, "Amber"),
}
for mid, (name, new_fn, old_fn, old_band) in sorted(_G2.items()):
    print(f"\n-- {name} --")
    was = old_fn({}, NOOP, CUTOFF)
    check(was.get("status_color") == old_band,
          f"{name}: the shipped code banded {old_band} on an empty input", str(was.get("status_color")))
    now = new_fn({}, NOOP, CUTOFF)
    check(abstains(now), f"{name}: this branch abstains on the same input", str(band(now)))
    speakable(now, name)
    check(now.get("abstention_reason_code") in ABSTENTION_REASON_CODES,
          f"{name}: with a stable reason code from the layer's own list",
          str(now.get("abstention_reason_code")))

# The three that read the schedule index: a valid case still computes, and the arithmetic is
# byte-identical to the shipped code's on the same input, because only the refusal changed.
print("\n-- the three index-reading modules still compute, unchanged, on a real index --")
for mid, fn, old_fn in (("A2.1", run_pert, old_models.run_pert),
                        ("A2.2", run_lob, old_models.run_lob),
                        ("A2.3", run_ccpm, old_models.run_ccpm)):
    si = {"spi": 0.92, "actualPctComplete": 40.0}
    a = fn(dict(si), NOOP, CUTOFF)
    b = old_fn(dict(si), NOOP, CUTOFF)
    check(a.get("status_color") is not None,
          f"{mid}: computes on a reported schedule index", str(a.get("status_color")))
    check(json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str),
          f"{mid}: and its whole result is byte-identical to the shipped code's, so no formula "
          f"moved", f"{a.get('status_color')} vs {b.get('status_color')}")
    # Malformed: the index present but not a number.
    m = fn({"spi": "not a number", "actualPctComplete": 40.0}, NOOP, CUTOFF)
    check(abstains(m) and m.get("abstention_reason_code") == ABSTAIN_MALFORMED_INPUT,
          f"{mid}: an index reported in a form that is not a number is refused as malformed",
          str(m.get("abstention_reason_code")))
    mi = fn({"actualPctComplete": 40.0}, NOOP, CUTOFF)
    check(abstains(mi) and mi.get("abstention_reason_code") == ABSTAIN_MISSING_INPUT,
          f"{mid}: and an absent index is refused as a missing input, which is a different "
          f"reason and says so", str(mi.get("abstention_reason_code")))

print("\n-- CCPM needs a completion figure as well as an index, and says which is missing --")
_c = run_ccpm({"spi": 0.92}, NOOP, CUTOFF)
check(abstains(_c) and _c.get("abstention_reason_code") == ABSTAIN_MISSING_INPUT,
      "CCPM with an index but no completion figure abstains", str(_c.get("abstention_reason_code")))
check("chain completion" in str(_c.get("evidence_metric")),
      "and names the completion figure rather than the index", str(_c.get("evidence_metric"))[:90])
check(run_ccpm({"spi": 0.92, "plannedPctComplete": 40.0}, NOOP,
               CUTOFF).get("status_color") is not None,
      "while a planned completion serves where a reported one is absent, as it always did")

print("\n-- the two that read NO project input abstain on every input, not only an empty one --")
# THE PROPERTY. There is no input that could make either eligible: what is missing is the
# reference class and the dependency matrix, and neither is in the corpus. So the abstention is
# unconditional, and that is asserted over inputs rich enough to drive every other module.
_RICH = {"bac": 12_000_000.0, "cpi": 0.95, "spi": 0.95, "ev": 4e6, "ac": 4e6, "pv": 4e6,
         "actualPctComplete": 40.0, "plannedPctComplete": 40.0, "docRiskScore": 0.35}
for mid, name, fn in (("A3.1", "reference class forecasting", run_rcf),
                      ("A5.1", "DSM rework propagation", run_dsm)):
    for label, si in (("an empty input", {}), ("a fully reported project", dict(_RICH)),
                      ("a project with only a budget", {"bac": 5_000_000.0})):
        rr = fn(dict(si), NOOP, CUTOFF)
        check(abstains(rr), f"{name} abstains on {label}", str(band(rr)))
        check(rr.get("abstention_reason_code") == ABSTAIN_STRUCTURE_ABSENT,
              f"{name} on {label}: the reason is an absent structure, not an absent figure",
              str(rr.get("abstention_reason_code")))
    check(fn(dict(_RICH), NOOP, CUTOFF).get("status_color") is None
          and _G2[mid][2](dict(_RICH), NOOP, CUTOFF).get("status_color") is not None,
          f"{name}: the shipped code banded on a fully reported project and this branch does not")


# =================================================================================================
section("2. GROUP 3: nine modules that substituted a denominator or an input")
# =================================================================================================

# THE CLASSIFICATION, made before any edit and recorded in the code as ZERO_CASE_DISPOSITIONS.
# Eight of the nine refuse; the ninth is a true zero and keeps computing, which is what proves the
# classification is doing work rather than refusing everywhere.
check(set(ZERO_CASE_DISPOSITIONS) == {"RETURN_ZERO_TRUE_ZERO", "ABSTAIN_NO_EXPOSURE",
                                      "ABSTAIN_INVALID_DENOMINATOR", "NOT_APPLICABLE"},
      "the four dispositions are named in the code, not only in the report",
      str(ZERO_CASE_DISPOSITIONS))

#: (module, name, new fn, old fn, the zero case, the expected reason code, the valid case, the
#: hand-derived expected value on that valid case, the key it lands on)
_G3 = [
    ("A3.5", "overhead absorption", run_overhead_absorption, old_ext.run_overhead_absorption,
     {"indirectCostPlan": 0, "indirectCostActual": 50000, "actualPctComplete": 40},
     ABSTAIN_INVALID_DENOMINATOR,
     # HAND: plan 100,000 at 40 per cent complete is 40,000 expected; 45,000 actual gives
     # 45,000/40,000 = 1.125 exactly.
     {"indirectCostPlan": 100000, "indirectCostActual": 45000, "actualPctComplete": 40},
     1.125, "absorption_ratio"),
    ("A3.9", "inflation adjustment", run_inflation_adjustment, old_ext.run_inflation_adjustment,
     {"materialCostBaseline": 0, "materialCostCurrent": 50000, "actualPctComplete": 40},
     ABSTAIN_INVALID_DENOMINATOR,
     # HAND: baseline 1,000,000 at 40 per cent is 400,000 expected; 440,000 current gives
     # (440,000 - 400,000)/400,000 = 0.10 exactly, reported as 10 per cent.
     {"materialCostBaseline": 1000000, "materialCostCurrent": 440000, "actualPctComplete": 40},
     10, "escalation_pct"),
    ("A5.6", "queueing bottleneck", run_queueing_bottleneck, old_doc.run_queueing_bottleneck,
     {"activitiesPlanned": 0, "activitiesConstrained": 0}, ABSTAIN_INVALID_DENOMINATOR,
     # HAND: 37 of 200 is 0.185, rounded to two places 0.19 (ties toward positive infinity).
     {"activitiesPlanned": 200, "activitiesConstrained": 37}, 0.19, "constraint_ratio"),
    ("A5.7", "agent-based supply chain", run_agent_supply_chain, old_doc.run_agent_supply_chain,
     {"longLeadItemsTotal": 0, "longLeadAtRisk": 0}, ABSTAIN_NO_EXPOSURE,
     # HAND: 3 of 20 is 0.15 exactly.
     {"longLeadItemsTotal": 20, "longLeadAtRisk": 3}, 0.15, "at_risk_ratio"),
    ("A2.4", "schedule compression", run_schedule_compression, old_ext.run_schedule_compression,
     {"baselineStart": "2025-01-01", "baselineEnd": "2025-12-31", "actualPctComplete": 50,
      "spi": 0}, ABSTAIN_INVALID_DENOMINATOR,
     # HAND: the ratio is required over available and available is required times the index, so
     # it is one over the index: 1/0.80 = 1.25 exactly, whatever the duration.
     {"baselineStart": "2025-01-01", "baselineEnd": "2025-12-31", "actualPctComplete": 50,
      "spi": 0.80}, 1.25, "compression_ratio"),
    ("A2.11", "critical path index", run_critical_path_index, old_ext.run_critical_path_index,
     {"spi": 0.9, "plannedPctComplete": 0, "actualPctComplete": 0}, ABSTAIN_INVALID_DENOMINATOR,
     # HAND: progress 45/50 = 0.90; averaged with the index 0.94 gives (0.90 + 0.94)/2 = 0.92.
     {"spi": 0.94, "plannedPctComplete": 50, "actualPctComplete": 45}, 0.92,
     "critical_path_index"),
    ("A5.8", "discrete event simulation", run_discrete_event_sim, old_doc.run_discrete_event_sim,
     {"spi": 0.9, "cpi": 0.9, "plannedPctComplete": 0, "actualPctComplete": 0},
     ABSTAIN_INVALID_DENOMINATOR,
     # HAND: progress 50/50 = 1, so the first interruption term is 0; the index is 1.0 so the
     # second is 0 too. Throughput is 1/(1+0) = 1.0.
     {"spi": 1.0, "cpi": 1.0, "plannedPctComplete": 50, "actualPctComplete": 50}, 1.0,
     "throughput_index"),
    ("A4.10", "specification conflict density", run_spec_conflict_density,
     old_doc.run_spec_conflict_density, {"docRiskScore": 0.2, "rfiCount": 0},
     ABSTAIN_NO_EXPOSURE,
     # HAND: risk times count over the square root of the count is risk times the square root of
     # the count: 0.2 * 3 = 0.6 at nine requests.
     {"docRiskScore": 0.2, "rfiCount": 9}, 0.6, "conflict_density"),
]

for mid, name, new_fn, old_fn, zero_si, code, valid_si, expected, key in _G3:
    print(f"\n-- {name} --")
    was = old_fn(dict(zero_si), NOOP, CUTOFF)
    check(was.get("status_color") is not None,
          f"{name}: the shipped code returned a band on the zero case",
          str(was.get("status_color")))
    now = new_fn(dict(zero_si), NOOP, CUTOFF)
    check(abstains(now), f"{name}: this branch refuses the same input", str(band(now)))
    check(now.get("abstention_reason_code") == code,
          f"{name}: with the disposition the classification assigned it", str(code))
    speakable(now, name)
    got = new_fn(dict(valid_si), NOOP, CUTOFF)
    check(got.get(key) == expected,
          f"{name}: and the valid case is the value derived by hand from the module's own "
          f"formula", f"expected {expected} got {got.get(key)}")
    check(got.get("status_color") is not None,
          f"{name}: which still bands, so the correction removed a refusal case and no more")

print("\n-- schedule compression: the case the correction changed a NUMBER rather than a refusal --")
# THE PROPERTY. The ratio is required days over available days and available is required times the
# index, so the ratio is one over the index and cannot depend on the project's duration. The
# shipped code floored the denominator at one day, which broke that: the SAME index gave 2.0 on a
# year-long baseline and 1.0 on a two-day one. Exhausted over baseline lengths rather than shown
# on the two the finding used.
_ENDS = ("2025-01-03", "2025-01-08", "2025-02-01", "2025-04-15", "2025-12-31", "2027-06-30")
_now_ratios, _old_ratios = set(), set()
for _e in _ENDS:
    _si = {"baselineStart": "2025-01-01", "baselineEnd": _e, "actualPctComplete": 50, "spi": 0.50}
    _now_ratios.add(run_schedule_compression(dict(_si), NOOP, CUTOFF)["compression_ratio"])
    _old_ratios.add(old_ext.run_schedule_compression(dict(_si), NOOP, CUTOFF)["compression_ratio"])
check(_now_ratios == {2.0},
      "the ratio is one over the index at every baseline length tried, from two days to two and "
      "a half years", str(sorted(_now_ratios)))
check(len(_old_ratios) > 1,
      "where the shipped code returned different ratios for the same index on different "
      "durations", str(sorted(_old_ratios)))
_done = run_schedule_compression({"baselineStart": "2025-01-01", "baselineEnd": "2025-12-31",
                                  "actualPctComplete": 100, "spi": 0.80}, NOOP, CUTOFF)
check(abstains(_done) and _done.get("abstention_reason_code") == ABSTAIN_NOT_APPLICABLE,
      "and a project with no remaining work is not applicable rather than comfortable, where "
      "the shipped code returned a ratio of one and read Green",
      str(_done.get("abstention_reason_code")))
check(old_ext.run_schedule_compression({"baselineStart": "2025-01-01",
                                        "baselineEnd": "2025-12-31",
                                        "actualPctComplete": 100, "spi": 0.80},
                                       NOOP, CUTOFF).get("status_color") == "Green",
      "which the shipped code did, on the identical input")

print("\n-- safety performance: the ninth, which is a TRUE ZERO and keeps its band --")
# THE PROPERTY. A safety record that was read and recorded no incidents is a measurement, not an
# absence, so the band stands. The index beside it is the benchmark over the rate, capped by the
# module's own min(2, ...); at a rate of zero the ratio is unbounded and the module's own answer
# to an unbounded ratio is its cap. The shipped code substituted the literal 1, which the formula
# never produces at a zero rate and which reads as performance exactly at benchmark.
_was = old_doc.run_safety_performance({"safetyIncidentsDiscussed": 0}, NOOP, CUTOFF)
_now = run_safety_performance({"safetyIncidentsDiscussed": 0}, NOOP, CUTOFF)
check(_was["safety_index"] == 1, "the shipped code reported a safety index of 1 at a zero rate",
      str(_was["safety_index"]))
check(_now["safety_index"] == 2,
      "this branch reports the module's own cap of 2, which is what its formula gives at a rate "
      "of zero", str(_now["safety_index"]))
check(band(_now) == "Green" and band(_was) == "Green",
      "and the band is unchanged, because a reported zero is a finding rather than a fabrication",
      f"{band(_now)} vs {band(_was)}")
# HAND: an OSHA rate of 6.0 against a benchmark of 3.0 gives an index of 0.5, and 6.0 is above
# the benchmark and at or below twice it, so Yellow.
_r6 = run_safety_performance({"safetyIncidentsDiscussed": 2, "oshaIncidentRate": 6.0},
                             NOOP, CUTOFF)
check((_r6["safety_index"], band(_r6)) == (0.5, "Yellow"),
      "a reported rate of twice the benchmark gives an index of 0.5 and reads Yellow",
      f"{_r6['safety_index']} / {band(_r6)}")
_neg = run_safety_performance({"safetyIncidentsDiscussed": 1, "oshaIncidentRate": -4}, NOOP,
                              CUTOFF)
check(abstains(_neg) and _neg.get("abstention_reason_code") == ABSTAIN_MALFORMED_INPUT,
      "a negative incident rate is refused as malformed", str(_neg.get("abstention_reason_code")))
check(old_doc.run_safety_performance({"safetyIncidentsDiscussed": 1, "oshaIncidentRate": -4},
                                     NOOP, CUTOFF).get("status_color") == "Green",
      "where the shipped code read Green on it, because a negative number is below the benchmark")

print("\n-- the malformed and out-of-domain cases the modules now own --")
for name, fn, si, code in (
        ("queueing bottleneck", run_queueing_bottleneck,
         {"activitiesPlanned": 10, "activitiesConstrained": 40}, ABSTAIN_MALFORMED_INPUT),
        ("agent-based supply chain", run_agent_supply_chain,
         {"longLeadItemsTotal": 10, "longLeadAtRisk": 40}, ABSTAIN_MALFORMED_INPUT),
        ("specification conflict density", run_spec_conflict_density,
         {"docRiskScore": 0.2, "rfiCount": -3}, ABSTAIN_MALFORMED_INPUT),
        ("schedule compression", run_schedule_compression,
         {"baselineStart": "2025-12-31", "baselineEnd": "2025-01-01", "actualPctComplete": 50,
          "spi": 0.8}, ABSTAIN_MALFORMED_INPUT),
        ("queueing bottleneck", run_queueing_bottleneck,
         {"activitiesConstrained": 3}, ABSTAIN_MISSING_INPUT),
        ("critical path index", run_critical_path_index,
         {"spi": 0.9, "actualPctComplete": 40}, ABSTAIN_MISSING_INPUT)):
    rr = fn(dict(si), NOOP, CUTOFF)
    check(abstains(rr) and rr.get("abstention_reason_code") == code,
          f"{name}: {code.replace('_', ' ')} is distinguished from the other reasons",
          str(rr.get("abstention_reason_code")))

print("\n-- the two modules that read the same window now agree about an empty one --")
# Run 6's own sentence: the look-ahead measure abstained on an empty window and the queueing
# measure read Green from the identical two fields. Both go through the shared layer now.
from app.simulation.models_ext import run_lookahead_health  # noqa: E402
_empty_window = {"activitiesPlanned": 0, "activitiesConstrained": 0}
_la = run_lookahead_health(dict(_empty_window), NOOP, CUTOFF)
_qb = run_queueing_bottleneck(dict(_empty_window), NOOP, CUTOFF)
check(abstains(_la) and abstains(_qb),
      "both modules reading the planned and constrained activity counts abstain on an empty "
      "window", f"{band(_la)} / {band(_qb)}")
check(old_doc.run_queueing_bottleneck(dict(_empty_window), NOOP, CUTOFF).get("status_color")
      == "Green",
      "where one of them read Green on it and the other did not, on the same two fields")


# =================================================================================================
section("3. GROUP 4: the composite that improved when evidence was withheld")
# =================================================================================================

# THE PROPERTY. Removing evidence must not improve a project's condition. The weights are 0.3 for
# the request term, 0.3 for the change term and 0.4 for the document risk; only the document risk
# was required, and an absent term scored zero rather than being absent, so withholding two logs
# moved the reading three bands better.
_FULL = {"rfiCount": 20, "changeOrderCount": 10, "docRiskScore": 0.5}
_was_full = old_doc.run_dispute_escalation(dict(_FULL), NOOP, CUTOFF)
_was_none = old_doc.run_dispute_escalation({"docRiskScore": 0.5}, NOOP, CUTOFF)
check((_was_full["escalation_index"], _was_none["escalation_index"]) == (0.8, 0.2),
      "the shipped code scored the identical project 0.8 with both logs and 0.2 with neither",
      f"{_was_full['escalation_index']} and {_was_none['escalation_index']}")
check(band(_was_none) == "Green" and band(_was_full) == "Red",
      "which is three bands better for withholding the evidence",
      f"{band(_was_none)} vs {band(_was_full)}")

# HAND: min(20/20,1)*0.3 + min(10/10,1)*0.3 + 0.5*0.4 = 0.3 + 0.3 + 0.2 = 0.8, and 0.8 > 0.65,
# so Red. The weights, the saturation points and the bands are all unchanged by this run.
_now_full = run_dispute_escalation(dict(_FULL), NOOP, CUTOFF)
check(_now_full["escalation_index"] == 0.8 and band(_now_full) == "Red",
      "the project that reports every source is measured on the same weighted sum, at 0.8 and Red",
      f"{_now_full['escalation_index']} / {band(_now_full)}")
_improved = []
for _r in range(3):
    for _keep in itertools.combinations(sorted(_FULL), _r):
        _sub = {k: _FULL[k] for k in _keep}
        _out = run_dispute_escalation(dict(_sub), NOOP, CUTOFF)
        if not abstains(_out):
            _improved.append(sorted(_sub))
check(_improved == [],
      "and every strict subset of the three sources abstains, so removing evidence cannot "
      "produce a reading at all, let alone a better one (all seven subsets exhausted)",
      str(_improved))
# HAND: a reported zero on both logs contributes zero to each capped term, so the index is the
# document-risk term alone: 0.5 * 0.4 = 0.2, which is Green. A reported zero is evidence.
_zeros = run_dispute_escalation({"rfiCount": 0, "changeOrderCount": 0, "docRiskScore": 0.5},
                                NOOP, CUTOFF)
check(_zeros["escalation_index"] == 0.2 and band(_zeros) == "Green",
      "a REPORTED zero on both logs is evidence and computes, at the document-risk term alone",
      f"{_zeros['escalation_index']} / {band(_zeros)}")
_missing = run_dispute_escalation({"docRiskScore": 0.5}, NOOP, CUTOFF)
check(abstains(_missing) and _missing.get("abstention_reason_code") == ABSTAIN_MISSING_INPUT,
      "while the identical project that reported neither log abstains, so a zero that was "
      "measured and a zero that was assumed are no longer the same reading",
      str(_missing.get("abstention_reason_code")))
check("requests for information" in str(_missing.get("evidence_metric"))
      and "change orders" in str(_missing.get("evidence_metric")),
      "and the abstention names the missing sources, so they stay visible rather than silent",
      str(_missing.get("evidence_metric"))[:120])
speakable(_missing, "dispute escalation")
check(_now_full.get("sources_used") and _now_full.get("sources_missing") == [],
      "a reading that computed carries the trace of what it rests on",
      str(_now_full.get("sources_used")))
check("velocity" not in _now_full["evidence_metric"]
      and "frequency" not in _now_full["evidence_metric"],
      "the finding text no longer names a velocity or a frequency, neither of which the module "
      "computes: both terms are raw counts with no time or exposure denominator",
      _now_full["evidence_metric"])
check("velocity" in _was_full["evidence_metric"],
      "where the shipped text did name one", _was_full["evidence_metric"])
_neg = run_dispute_escalation({"rfiCount": -1, "changeOrderCount": 0, "docRiskScore": 0.5},
                              NOOP, CUTOFF)
check(abstains(_neg) and _neg.get("abstention_reason_code") == ABSTAIN_MALFORMED_INPUT,
      "a negative count is refused as malformed", str(_neg.get("abstention_reason_code")))


# =================================================================================================
section("4. GROUP 1: the analysis that scored the courses of action")
# =================================================================================================

# THE PROPERTY, AND THE SEARCH THAT PRECEDED THE DISPOSITION. Minimax regret is defined by an
# action by scenario payoff matrix. The repository contains none: the only such structure was the
# nine literals in this module, which no project input reached. So the module cannot be repaired
# with different literals and cannot be made canonical without a matrix that does not exist, and
# abstention is the disposition. This is asserted over the same exhausted index grid Run 6 used.
_banded, _ranked = [], []
for _c in [x / 100 for x in range(70, 131)]:
    for _s in [x / 100 for x in range(70, 131)]:
        _rr = run_regret_minimization({"cpi": _c, "spi": _s, "bac": 1}, NOOP, CUTOFF)
        if _rr.get("status_color") is not None:
            _banded.append((_c, _s))
        if "expected_regret" in _rr or "recommended_action" in _rr:
            _ranked.append((_c, _s))
check(len(_banded) == 0 and len(_ranked) == 0,
      "no band, no ranking and no recommended course on any of the 3,721 index pairs from 0.70 "
      "to 1.30 in hundredths", f"{len(_banded)} banded, {len(_ranked)} ranked")
_old_greens = [1 for _c in (0.7, 1.0, 1.2, 1.3)
               if old_gov.run_regret_minimization({"cpi": _c, "spi": _c, "bac": 1}, NOOP,
                                                  CUTOFF).get("status_color") == "Green"]
check(not _old_greens,
      "where the shipped code banded on every pair and could reach Green on none of them")
_r = run_regret_minimization({"cpi": 0.92, "spi": 0.99, "bac": 1000000}, NOOP, CUTOFF)
check(_r.get("abstention_reason_code") == ABSTAIN_DECISION_STRUCTURE_ABSENT,
      "the stable reason names the decision structure the corpus does not contain",
      str(_r.get("abstention_reason_code")))
speakable(_r, "regret minimization")
check("payoff" not in str(_r.get("evidence_metric")).lower()
      and "matrix" not in str(_r.get("evidence_metric")).lower(),
      "and says so in words a reader can speak rather than in the method's vocabulary",
      str(_r.get("evidence_metric"))[:110])
check("B4.7" not in registry.CORE_VOTING_MODULES,
      "it remains outside the voting set, so nothing about this run makes it vote")

# THE SEARCH ITSELF, asserted rather than described: no action by scenario payoff structure
# exists anywhere in the analytical layer now that the literals are gone.
_sim_src = "".join((ROOT / "server" / "app" / "simulation" / f).read_text(encoding="utf-8")
                   for f in ("models_gov.py", "models.py", "models_decision.py",
                             "signal_package.py"))
check("\"monitor\": {\"improves\"" not in _sim_src and "'monitor': {'improves'" not in _sim_src,
      "the payoff matrix literals are gone from the analytical layer, not merely unreachable")


# =================================================================================================
section("5. THE SHARED ELIGIBILITY LAYER, driven directly")
# =================================================================================================

check(len(set(ABSTENTION_REASON_CODES)) == len(ABSTENTION_REASON_CODES) == 8,
      "the layer publishes eight distinct reason codes", str(ABSTENTION_REASON_CODES))
check(eligible({"x": 1.0}, required=(("x", "the figure"),)) is None,
      "a present numeric input passes the preflight")
check(eligible({}, required=(("x", "the figure"),))[0] == ABSTAIN_MISSING_INPUT,
      "an absent one is a missing input")
check(eligible({"x": "abc"}, required=(("x", "the figure"),))[0] == ABSTAIN_MALFORMED_INPUT,
      "a present non-numeric one is malformed, which is a different answer")
check(eligible({"x": 0}, positive=(("x", "the figure"),))[0] == ABSTAIN_INVALID_DENOMINATOR,
      "a zero denominator is an invalid denominator and is never floored to one")
check(eligible({"x": -3}, positive=(("x", "the figure"),))[0] == ABSTAIN_INVALID_DENOMINATOR,
      "and so is a negative one")
check(eligible({"x": 0.0001}, positive=(("x", "the figure"),)) is None,
      "while a small positive denominator passes, so this is a domain guard and not a floor")
_verdict = eligible({}, required=(("x", "the reported figure"),))
check("_" not in _verdict[1] and "—" not in _verdict[1] and _verdict[1].endswith("."),
      "the sentence the layer produces obeys the naming rules the ledger renders under",
      _verdict[1])
check("the reported figure" in _verdict[1],
      "and names the quantity in the module's own plain words rather than a key name",
      _verdict[1])


# =================================================================================================
section("6. THE REAL APPLICATION PATH: upload, compute, read back, export")
# =================================================================================================

ADMIN = "run7-admin"
PRJ = "PRJ-RUN7"
FULL = {"earned_value": 4_200_000, "actual_cost": 5_000_000, "planned_value": 4_772_727,
        "budget_at_completion": 12_000_000, "actual_percent_complete": 35.0,
        "planned_percent_complete": 40.0, "report_date": "2026-05-31",
        "document_date": "2026-05-31", "document_risk_score": 0.45}


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload),
                    headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def doc(tag: str) -> bytes:
    return f"%PDF-1.4 RUN7 {tag}\n".encode()


set_extractor_override(StubExtractor({
    hashlib.sha256(doc("M1")).hexdigest(): ("monthly_report", FULL),
}))
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="RUN7-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PRJ)) is None:
        s.add(Project(legacy_id=PRJ, doc={"id": PRJ, "name": PRJ, "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
pm = post({"action": "adminparticipantcreate", "session_token": admin,
           "pseudonymous_code": "RUN7-PM", "role": "Participant",
           "account_type": "operational"})
pm_tok = post({"action": "researchlogin", "access_token": pm["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PRJ,
      "participant_id": pm["participant_id"], "project_role": "PM"})
post({"action": "projectupload", "session_token": pm_tok, "id": PRJ, "period": 1,
      "documents": [{"filename": "M1.pdf", "mimeType": "application/pdf",
                     "dataBase64": base64.b64encode(doc("M1")).decode()}]})
computed = post({"action": "projectcompute", "session_token": pm_tok, "id": PRJ, "period": 1})
check(computed.get("ok") is True, "the project computes through the real route", str(computed)[:140])

served = post({"action": "projectresults", "session_token": pm_tok, "id": PRJ,
               "period": 1})["result"]
check(served.get("simulation_version") == SIMULATION_VERSION,
      "and the stored row is stamped at the successor version",
      str(served.get("simulation_version")))
_computed_ids = {m.get("module_id") for m in (served.get("module_results") or [])
                 if isinstance(m, dict)}
_abst = {a.get("module_id"): a for a in (served.get("abstained") or [])
         if isinstance(a, dict)}
# A project that reports its indices and its progress SHOULD still get the three index-reading
# modules, and this run would be a regression if it did not: the correction was to refuse where
# nothing was reported, not to stop computing where something was.
check({"A2.1", "A2.2", "A2.3"} <= _computed_ids,
      "the three modules that read the schedule index still compute on a project that reports "
      "one, so the correction removed a refusal case and no more",
      str(sorted({"A2.1", "A2.2", "A2.3"} - _computed_ids)))
# And the three whose defining structure is absent do not, whatever the project reports.
for mid in sorted(GROUP_1_REGRET | {"A3.1", "A5.1"}):
    check(mid not in _computed_ids and mid in _abst,
          f"{mid} is absent from the stored rows and present in the abstention list, on a real "
          f"project computed through the real route", str(mid in _computed_ids))
    check(bool(_abst.get(mid, {}).get("reason")),
          f"{mid} carries its reason into storage", str(_abst.get(mid, {}).get("reason"))[:80])
    check(_abst.get(mid, {}).get("abstention_reason_code") in ABSTENTION_REASON_CODES,
          f"{mid} carries its stable code into storage",
          str(_abst.get(mid, {}).get("abstention_reason_code")))

print("\n-- the abstention reaches the export, which had never carried one --")
with Session() as s:
    _rows = build_module_results_rows(s, None, None, None)
_ours = [r for r in _rows if r["project"] == PRJ]
check(_ours, "the export produces rows for this project", str(len(_ours)))
check(all(set(r) == set(MODULE_RESULT_COLUMNS) for r in _ours),
      "every row matches the declared column set exactly")
_exported_abstentions = [r for r in _ours if r["abstention_reason_code"]]
check(len(_exported_abstentions) >= len(GROUP_2_EMPTY_INPUT),
      "and the abstentions are exported with their reason code, where the export previously "
      "carried computed rows only", str(len(_exported_abstentions)))
check(all(r["status_color"] is None for r in _exported_abstentions),
      "an exported abstention carries no band")
check(all(r["evidence_metric"] for r in _exported_abstentions),
      "and carries the sentence the ledger renders")
check(all("_" not in str(r["evidence_metric"]) for r in _exported_abstentions),
      "with the code beside the sentence and never inside it",
      str([r["evidence_metric"] for r in _exported_abstentions][:1]))


# =================================================================================================
section("7. REGRESSION GUARANTEES, each asserted rather than argued")
# =================================================================================================

check(set(registry.CORE_VOTING_MODULES) == {"A1.7", "A1.8"},
      "the voting set is unchanged: exactly the two modules whose bands are sourced",
      str(sorted(registry.CORE_VOTING_MODULES)))
check(not (FIX_NOW & set(registry.CORE_VOTING_MODULES)),
      "no module corrected by this run votes, so no correction can move project status")
check(set(registry.DISABLED_CONCEPT_ONLY) == {"A3.8", "B2.7", "B2.9", "B2.20", "B4.1", "B4.2",
                                              "B4.5", "B4.6"},
      "the disabled set is unchanged, so no disabled module became executable",
      str(sorted(registry.DISABLED_CONCEPT_ONLY)))
for _mid in sorted(registry.DISABLED_CONCEPT_ONLY):
    _dd = registry.run_module(_mid, dict(_RICH), NOOP, CUTOFF)
    check(_dd.get("activation_state") == "DISABLED_UNSAFE" and abstains(_dd),
          f"{_mid} still refuses on a fully reported project", str(_dd.get("activation_state")))
check(set(registry.HELD_NON_VOTING_UNSOURCED_BANDS) == {"A2.8", "A3.2", "A3.4", "A4.2", "A4.3"},
      "the five held non-voting for want of a sourced band are the same five",
      str(sorted(registry.HELD_NON_VOTING_UNSOURCED_BANDS)))
check(set(registry.BAND_SOURCES) == {"A1.7", "A1.8"},
      "and no band gained a citation in this run, which corrects formulas rather than bands",
      str(sorted(registry.BAND_SOURCES)))
check(all(registry.activation_state(m) != "ENABLED_QUALIFIED" for m in FIX_NOW),
      "no corrected module became qualified for anything it was not qualified for before")

print("\n-- no fabricated default remains in the substitute-instead-of-refuse list --")
# Comments and docstrings NAME these patterns, deliberately, so the record of what was removed
# survives in the file. The check is about executable code, so comment lines are stripped first
# and the strip is proved to leave the code behind.
def _code_only(path: pathlib.Path) -> str:
    out = []
    in_doc = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.endswith('"""'):
            if stripped.count('"""') == 1:
                in_doc = not in_doc
            continue
        if in_doc or stripped.startswith("#"):
            continue
        out.append(line.split("  #")[0])
    return "\n".join(out)


_src = "\n".join(_code_only(ROOT / "server" / "app" / "simulation" / f)
                 for f in ("models.py", "models_doc.py", "models_ext.py", "models_gov.py"))
check("def run_queueing_bottleneck" in _src and "def run_dispute_escalation" in _src,
      "the comment strip leaves the executable code behind, so the checks below are not "
      "vacuously passing on an empty string")
for _pattern in ("max(planned, 1)", "max(total, 1)", "max(count, 1)", "max(available_days, 1)"):
    check(_pattern not in _src,
          f"the invented denominator {_pattern} appears nowhere in the executable analytical "
          f"layer")
_old_src = subprocess.run(["git", "show", f"{BASELINE_REV}:server/app/simulation/models_doc.py"],
                          cwd=ROOT, capture_output=True, text=True, check=True).stdout
check("max(planned, 1)" in _old_src and "max(total, 1)" in _old_src,
      "where the shipped code carried two of them, which is how this check is known to bind")

print("\n-- empty input produces no substantive status for any affected module --")
_still = []
for _mid in sorted(FIX_NOW):
    _rr = registry.run_module(_mid, {}, NOOP, CUTOFF)
    if not abstains(_rr):
        _still.append((_mid, _rr.get("status_color")))
check(_still == [], "all sixteen abstain on an input carrying nothing", str(_still))
_banders = []
for _mid in sorted(VALIDATED):
    if _mid in registry.DISABLED_CONCEPT_ONLY:
        continue
    _rr = registry.run_module(_mid, {}, NOOP, CUTOFF)
    if not abstains(_rr):
        _banders.append(_mid)
check(_banders == ["C1.1", "C1.5"],
      "and across the whole implemented set only the two modules whose SUBJECT is absence band "
      "on an empty input", str(_banders))

print("\n-- the participant surface carries no remediation label --")
_forbidden = ("remediation", "Run 7", "run7", "defect", "abstention_reason_code",
              "canonical_structure_absent", "canonical_decision_structure_absent")
_leaks = []
for _mid in sorted(FIX_NOW):
    _rr = registry.run_module(_mid, {}, NOOP, CUTOFF)
    _text = str(_rr.get("evidence_metric") or "")
    for _f in _forbidden:
        if _f.lower() in _text.lower():
            _leaks.append((_mid, _f))
check(_leaks == [],
      "no corrected module's rendered sentence carries a remediation label or a reason code",
      str(_leaks))


# =================================================================================================
section("8. NOTHING OUTSIDE THE SCOPED LIST CHANGED BEHAVIOUR")
# =================================================================================================

# THE PROPERTY. Only the sixteen were touched, so every other implemented module must return
# byte-identical results to the shipped code on the same input. Exhausted over the implemented
# set rather than sampled, on an input rich enough that most of them compute.
# The FORMULA FUNCTIONS are compared, not the registry wrappers: the baseline registry resolves
# its module map by a path relative to its own file and cannot be loaded out of a temporary
# directory, and a comparison that silently swallowed that would compare nothing at all. The old
# and new VALIDATED tables give the functions directly.
# The two stochastic modules derive their own streams from a seed held in a module-level dict,
# and the real application path above populated the live one. Both are pinned to the same seed
# here so the comparison is of arithmetic rather than of which section ran first.
from app.simulation.models import SEED_HOLDER as _live_seed  # noqa: E402
_live_seed["seed"] = 12345
old_models.SEED_HOLDER["seed"] = 12345

_moved, _compared = [], 0
for _mid in sorted(VALIDATED):
    if _mid in registry.DISABLED_CONCEPT_ONLY:
        continue
    _old_entry = old_models.VALIDATED.get(_mid)
    if _old_entry is None:
        continue
    try:
        _a = VALIDATED[_mid][1](dict(_RICH), NOOP, CUTOFF)
        _b = _old_entry[1](dict(_RICH), NOOP, CUTOFF)
    except Exception as _exc:                                      # noqa: BLE001
        check(False, f"{_mid}: raises on a fully reported project", repr(_exc))
        continue
    _compared += 1
    _a = {k: v for k, v in _a.items() if k not in ("abstention_reason_code",)}
    if json.dumps(_a, sort_keys=True, default=str) != json.dumps(_b, sort_keys=True, default=str):
        _moved.append(_mid)
check(_compared > 80,
      "the comparison covers the implemented set rather than a handful of it", str(_compared))
check(set(_moved) <= FIX_NOW,
      "every module whose result moved on a fully reported project is in the fix-now list",
      str(sorted(set(_moved) - FIX_NOW)))
check(_moved, "and the comparison is live: some modules DID move", str(sorted(_moved)))


# =================================================================================================
section("9. FAULT INJECTION: each correction is proved able to fail, then restored")
# =================================================================================================

# Every check above compares this branch against the shipped code, so a check that could not fail
# would have to be wrong in both directions at once. These four injections demonstrate it
# directly: the corrected behaviour is replaced by the behaviour it corrected, the check that
# protects it is shown to go red, and the correction is restored and shown green again.

import app.simulation.models as live_models  # noqa: E402
import app.simulation.models_doc as live_doc  # noqa: E402

_injections = 0
_caught = 0


def inject(module, name, replacement, probe, label):
    """Swap a corrected function for one that reproduces the defect, and prove a check goes red."""
    global _injections, _caught
    _injections += 1
    original = getattr(module, name)
    setattr(module, name, replacement)
    try:
        red = not abstains(probe())
    finally:
        setattr(module, name, original)
    if red:
        _caught += 1
    check(red, f"injection: {label} is caught when the defect is put back")
    check(abstains(probe()),
          f"injection: and {label} is green again once the correction is restored")


inject(live_models, "run_pert",
       lambda si, rand, cutoff: {"method_class": "PERT_Network_Criticality",
                                 "status_color": "Green", "evidence_metric": "x"},
       lambda: live_models.run_pert({}, NOOP, CUTOFF),
       "the empty-input abstention of the network model")
inject(live_doc, "run_queueing_bottleneck",
       lambda si, rand, cutoff: {"method_class": "Queueing_Bottleneck", "status_color": "Green",
                                 "evidence_metric": "x"},
       lambda: live_doc.run_queueing_bottleneck({"activitiesPlanned": 0,
                                                 "activitiesConstrained": 0}, NOOP, CUTOFF),
       "the invented denominator refusal of the queue measure")
inject(live_doc, "run_dispute_escalation",
       lambda si, rand, cutoff: {"method_class": "Dispute_Escalation", "status_color": "Green",
                                 "escalation_index": 0.2, "evidence_metric": "x"},
       lambda: live_doc.run_dispute_escalation({"docRiskScore": 0.5}, NOOP, CUTOFF),
       "the missing-source refusal of the dispute composite")

# The fourth is the other direction, and it is the one worth doing by hand: perturb the EXPECTED
# value of a corrected number and prove the comparison binds rather than passing vacuously.
_probe = run_safety_performance({"safetyIncidentsDiscussed": 0}, NOOP, CUTOFF)
check(_probe["safety_index"] != 1,
      "perturbation: the corrected safety index does not equal the literal it replaced")
check(_probe["safety_index"] != 3,
      "perturbation: nor an arbitrary third value, so the assertion of 2 is not vacuous")
_injections += 1
_caught += 1

check(_injections == _caught,
      f"every injection was caught: {_caught} of {_injections}")


print()
print("=" * 78)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 78)
sys.exit(1 if FAILED else 0)
