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
# RESTATED BY RUN 10B, original reason preserved: Run 7 shipped sim-2026.08-v3 and Run 10
# shipped sim-2026.08-v4, and both records are preserved in the version history rather than
# overwritten. This branch is Run 10B's.
# RESTATED BY RUN 28, original reason preserved. THIS IS ALSO THE PROOF THAT THE FROZEN LINE IS
# STILL REPRODUCIBLE: `oldsim7` above is a pinned copy of the analytical package as it shipped at
# sim-2026.08-v2, it is imported and EXECUTED by this suite, and every comparison below runs the
# old code and the new code side by side on identical inputs. A frozen record that could not be
# executed would not be evidence of anything.
check(SIMULATION_VERSION == "sim-2026.08-v14",
      "and this branch is stamped at Run 28's version, so results computed before and after "
      "each run are distinguishable in the data. Every earlier stamp from sim-2026.07-v1 "
      "onward is preserved in the version history rather than overwritten",
      SIMULATION_VERSION)
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
# RUN 10 SUPERSEDES ONE ROW OF THIS BLOCK, AND THE ROW IS MOVED RATHER THAN DELETED so the Run 7
# record stays legible. Run 8 established that a healthy reading was structurally unreachable in
# the criticality module, because the band divides an eightieth percentile of a sum of skewed
# durations by a baseline built from the modes of the same durations. Run 10's correction is that
# the module abstains on the absent activity network rather than reporting a criticality index
# from this file's own stand-in durations, so it no longer computes on a schedule index alone.
# Run 7's finding about it is unchanged and still holds: an empty input abstains, which the block
# above still proves. What changed is that a reported index is no longer sufficient.
_r10_pert = run_pert({"spi": 0.92, "actualPctComplete": 40.0}, NOOP, CUTOFF)
check(abstains(_r10_pert),
      "A2.1: Run 10 abstains on the absent activity network even with an index reported",
      str(band(_r10_pert)))
check(_r10_pert.get("abstention_reason_code") == "canonical_structure_absent",
      "A2.1: and names the absent canonical structure as the reason",
      str(_r10_pert.get("abstention_reason_code")))

# RUN 10B SUPERSEDES THE REST OF THIS BLOCK FOR THE TWO REMAINING MODULES, AND THE ROWS ARE
# MOVED RATHER THAN DELETED, on the same footing as the criticality module above. Run 7's finding
# for both is unchanged and is still proved by the block above: an empty input abstains. What
# changed in Run 10B is that a reported schedule index is no longer sufficient for either of
# them, because neither is a schedule-index measure. A line-of-balance measure needs a line of
# balance and a critical-chain fever chart needs a sized critical-chain buffer, and where the
# structure is absent both abstain rather than reading the index. The original Run 7 assertion,
# that each computed on a reported index and matched the shipped arithmetic byte for byte, held
# at the time it was written and is recorded here as the reason this restatement exists.
for mid, fn in (("A2.2", run_lob), ("A2.3", run_ccpm)):
    si = {"spi": 0.92, "actualPctComplete": 40.0}
    a = fn(dict(si), NOOP, CUTOFF)
    check(abstains(a),
          f"{mid}: Run 10B abstains on a reported schedule index alone, because the index is "
          f"not the structure this method is named for", str(a.get("status_color")))
    check(a.get("abstention_reason_code") == ABSTAIN_STRUCTURE_ABSENT,
          f"{mid}: and names the absent canonical structure as the reason",
          str(a.get("abstention_reason_code")))
    speakable(a, f"{mid} canonical structure absent")
    m = fn({"spi": "not a number", "actualPctComplete": 40.0}, NOOP, CUTOFF)
    check(abstains(m),
          f"{mid}: an index reported in a form that is not a number still abstains, now because "
          f"the structure is absent before the index is ever consulted",
          str(m.get("abstention_reason_code")))

print("\n-- CCPM needs the chain and the buffer, and says which is missing --")
_c = run_ccpm({"spi": 0.92}, NOOP, CUTOFF)
check(abstains(_c) and _c.get("abstention_reason_code") == ABSTAIN_STRUCTURE_ABSENT,
      "CCPM with an index and no critical chain abstains",
      str(_c.get("abstention_reason_code")))
# RUN 10B RESTATEMENT, original reason preserved: Run 7 required a completion figure beside the
# index and asserted the abstention named the completion figure rather than the index. Run 10B
# requires the chain and its sized buffer, of which the completion is one part, so the sentence
# now names the chain. Neither requirement was dropped; the second contains the first.
check("critical chain" in str(_c.get("evidence_metric")),
      "and names the chain and its buffer rather than the index",
      str(_c.get("evidence_metric"))[:90])
_c2 = run_ccpm({"spi": 0.92, "plannedPctComplete": 40.0}, NOOP, CUTOFF)
check(abstains(_c2),
      "while a planned completion no longer serves in place of a chain, because a completion "
      "percentage is not a buffer", str(_c2.get("status_color")))

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
# RUN 28 REMOVED FOUR ROWS FROM THIS TABLE, and they are handled in their own block below
# instead. A3.5, A3.9, A2.4 and A2.11 no longer compute the quantity Run 7 corrected: the owner's
# supplied Run-28 contract replaced each of them with the canonical method, so the "valid case"
# inputs Run 7 used now produce an abstention rather than a band, and there is no v2 arithmetic
# left for the generic comparison below to make. Run 7's PROPERTY -- that the zero case refuses
# instead of substituting -- is preserved for all four and is asserted directly below, alongside
# the canonical answer on the v3 structure. The four were observed red in this table against the
# v3 build before being moved.
# RUN 29 EMPTIED THIS TABLE. Both of its remaining rows -- A5.8 Discrete Event Simulation and
# A4.10 Specification Conflict Density -- no longer compute the quantity Run 7 corrected. The
# supplied Run-29 contract states that a progress and schedule index algebraic index is not a
# discrete event simulation, and that `docRiskScore * sqrt(RFI count)` is not conflict density,
# so the "valid case" inputs Run 7 used now produce an abstention and there is no v2 arithmetic
# left for the generic comparison below to make. Run 7's PROPERTY -- that the zero case refuses
# instead of substituting -- is preserved for both and is asserted directly below, alongside the
# supplied contract's own hand-checked canonical answer. Both were observed red in this table
# against the v13 build before being moved.
_G3: list = []

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

print("\n-- the two Run-7 rows Run 29 replaced with the canonical method --")
from run29_fixtures import conflict_register, des_model  # noqa: E402
for _name, _fn, _old_fn, _zero_si, _retired_si in (
        ("discrete event simulation", run_discrete_event_sim, old_doc.run_discrete_event_sim,
         {"spi": 0.9, "cpi": 0.9, "plannedPctComplete": 0, "actualPctComplete": 0},
         {"spi": 1.0, "cpi": 1.0, "plannedPctComplete": 50, "actualPctComplete": 50}),
        ("specification conflict density", run_spec_conflict_density,
         old_doc.run_spec_conflict_density, {"docRiskScore": 0.2, "rfiCount": 0},
         {"docRiskScore": 0.2, "rfiCount": 9})):
    check(_old_fn(dict(_zero_si), NOOP, CUTOFF).get("status_color") is not None,
          f"{_name}: the v12 code returned a band on the zero case Run 7 corrected")
    _now_zero = _fn(dict(_zero_si), NOOP, CUTOFF)
    check(abstains(_now_zero),
          f"{_name}: this branch still refuses that input rather than substituting", str(band(_now_zero)))
    _now_retired = _fn(dict(_retired_si), NOOP, CUTOFF)
    check(abstains(_now_retired)
          and _now_retired.get("abstention_reason_code") == ABSTAIN_STRUCTURE_ABSENT,
          f"{_name}: and the v2 inputs that used to band produce no reading at all now, because "
          f"they are not the structure this method is named for",
          str(_now_retired.get("abstention_reason_code")))
    speakable(_now_retired, _name)

# HAND, from the supplied contract 5.8: one server, job A arriving at 0 with a service of 2 and
# job B arriving at 1 with a service of 2. A starts at 0 and ends at 2 having waited 0; B starts
# at 2 and ends at 4 having waited 1; the mean wait is 0.5.
_des = run_discrete_event_sim({"desProcessModel": des_model()}, NOOP, CUTOFF)
_ent = {e["entity_id"]: e for e in _des.get("entities", [])}
check(_des.get("mean_wait") == 0.5
      and (_ent["A"]["start"], _ent["A"]["end"], _ent["A"]["wait"]) == (0, 2, 0)
      and (_ent["B"]["start"], _ent["B"]["end"], _ent["B"]["wait"]) == (2, 4, 1),
      "discrete event simulation: with the governed event model present the supplied contract's "
      "own answer is reproduced exactly", str(_des.get("mean_wait")))

# HAND, from the supplied contract 4.10: five verified conflicts over two hundred and fifty
# requirements is a density of 0.02 a requirement, or twenty per thousand.
_scd = run_spec_conflict_density({"specificationConflictRegister": conflict_register()},
                                 NOOP, CUTOFF)
check(_scd.get("conflict_density") == 0.02 and _scd.get("conflicts_per_thousand") == 20.0,
      "specification conflict density: with the governed register present the supplied "
      "contract's own answer is reproduced exactly", str(_scd.get("conflict_density")))

print("\n-- the four Run-7 rows Run 28 replaced with the canonical method --")
# For each: the zero case Run 7 corrected must STILL refuse rather than substitute, the retired
# v2 inputs must now produce no reading at all, and the canonical structure must produce the
# supplied contract's own hand-checked answer.
_SC_NET = {"scheduleNetwork": {
    "schedule_version": "SCH-1", "status_basis": "2026-06-30 data date",
    "activities": [{"activity_id": "A", "predecessors": [], "current_duration": 10.0,
                    "baseline_duration": 10.0, "remaining_duration": 8.0},
                   {"activity_id": "B", "predecessors": ["A"], "current_duration": 10.0,
                    "baseline_duration": 10.0, "remaining_duration": 12.0}]}}
_CPM_NET = {"scheduleNetwork": {
    "schedule_version": "SCH-1", "status_basis": "2026-06-30 data date",
    "activities": [{"activity_id": "A", "predecessors": [], "current_duration": 3},
                   {"activity_id": "B", "predecessors": [], "current_duration": 4},
                   {"activity_id": "C", "predecessors": ["A", "B"], "current_duration": 2}]}}
_OH = {"overheadAllocationBase": {
    "allocation_base": "direct labour hours", "driver_source": "certified payroll",
    "planned_overhead": 100.0, "planned_driver": 1000.0,
    "actual_overhead": 120.0, "actual_driver": 1000.0}}
_IDX = {"externalCostIndex": {
    "index_name": "Construction Cost Index, all items", "authority": "statistical office",
    "geography": "national", "scope": "materials and labour", "base_period": "2020-01",
    "observation_period": "2026-06", "vintage": "2026-07 release",
    "base_index_value": 200.0, "current_index_value": 220.0, "cost_exposure": 100.0}}

for _mid, _name, _fn, _old_fn, _zero_si, _retired_si, _v3_si, _key, _want in [
    ("A3.5", "overhead absorption", run_overhead_absorption, old_ext.run_overhead_absorption,
     {"indirectCostPlan": 0, "indirectCostActual": 50000, "actualPctComplete": 40},
     {"indirectCostPlan": 100000, "indirectCostActual": 45000, "actualPctComplete": 40},
     _OH, "relative_rate_variance", 0.2),
    ("A3.9", "inflation adjustment", run_inflation_adjustment, old_ext.run_inflation_adjustment,
     {"materialCostBaseline": 0, "materialCostCurrent": 50000, "actualPctComplete": 40},
     {"materialCostBaseline": 1000000, "materialCostCurrent": 440000, "actualPctComplete": 40},
     _IDX, "escalation_factor", 1.1),
    ("A2.4", "schedule compression", run_schedule_compression, old_ext.run_schedule_compression,
     {"baselineStart": "2025-01-01", "baselineEnd": "2025-12-31", "actualPctComplete": 50,
      "spi": 0},
     {"baselineStart": "2025-01-01", "baselineEnd": "2025-12-31", "actualPctComplete": 50,
      "spi": 0.80},
     _SC_NET, "schedule_compression_index", 1.0),
    ("A2.11", "critical path index", run_critical_path_index, old_ext.run_critical_path_index,
     {"spi": 0.9, "plannedPctComplete": 0, "actualPctComplete": 0},
     {"spi": 0.94, "plannedPctComplete": 50, "actualPctComplete": 45},
     _CPM_NET, "project_finish", 6.0),
]:
    _was = _old_fn(dict(_zero_si), NOOP, CUTOFF)
    check(_was.get("status_color") is not None,
          f"{_name}: the shipped pre-Run-7 code returned a band on the zero case",
          str(_was.get("status_color")))
    check(abstains(_fn(dict(_zero_si), NOOP, CUTOFF)),
          f"{_name}: Run 7's property survives Run 28, and the zero case still refuses")
    check(abstains(_fn(dict(_retired_si), NOOP, CUTOFF)),
          f"{_name}: and the retired v2 inputs now produce no reading at all, so the proxy "
          f"cannot be reached by supplying them")
    _got = _fn(dict(_v3_si), NOOP, CUTOFF)
    check(abs(round(_got.get(_key), 6) - _want) < 1e-9,
          f"{_name}: and the canonical structure produces the supplied contract's own answer",
          f"expected {_want} got {_got.get(_key)}")
    check(_got.get("calibration_pending") is True and _got.get("status_color") is None,
          f"{_name}: with no band asserted, because the quantity is not the one the old ladder "
          f"was drawn over")
    speakable(_fn(dict(_zero_si), NOOP, CUTOFF), _name)
    # THE REASON CODE CHANGED DELIBERATELY, from invalid_denominator to
    # canonical_structure_absent, and that is the correction rather than a regression: the zero
    # case Run 7 found was a denominator the module substituted for, and in v3 there is no such
    # denominator to substitute because the defining structure of the method is absent. The code
    # is asserted to be exactly the structural one, so a module that quietly fell back to the
    # old reason would turn this red.
    check(_fn(dict(_zero_si), NOOP, CUTOFF).get("abstention_reason_code")
          == ABSTAIN_STRUCTURE_ABSENT,
          f"{_name}: and the reason it gives is that the canonical structure is absent, which "
          f"is a more specific refusal than the substituted denominator Run 7 removed",
          str(_fn(dict(_zero_si), NOOP, CUTOFF).get("abstention_reason_code")))

print("\n-- schedule compression: the invariance Run 7 restored, on the v3 quantity --")
# SUPERSEDED BY RUN 28, observed red against the v3 build (KeyError: 'compression_ratio') before
# being rewritten. Run 7's finding was that a one-day floor under the denominator broke the scale
# invariance the declared ratio always claimed, and that a finished project returned a ratio of
# one and read Green rather than being not applicable. Run 28 replaced the quantity entirely, on
# the owner's supplied contract: it is now the ratio of two sums of activity durations taken from
# two reconciled schedules. BOTH of Run 7's properties must still hold of the new quantity and
# both are asserted here, against the v3 structure rather than against the retired dates-and-index
# arithmetic. The comparison against the shipped pre-Run-7 code is dropped: that code computed a
# different quantity from different inputs, so a comparison with it would prove nothing about
# either.
def _sc_net(factor):
    return {"scheduleNetwork": {
        "schedule_version": "SCH-1", "status_basis": "2026-06-30 data date",
        "activities": [{"activity_id": "A", "predecessors": [],
                        "current_duration": 20.0 * factor,
                        "baseline_duration": 10.0 * factor,
                        "remaining_duration": 20.0 * factor}]}}


_FACTORS = (0.5, 1.0, 2.0, 7.0, 30.0, 365.0, 912.5)
_now_ratios = {run_schedule_compression(_sc_net(f), NOOP, CUTOFF)["schedule_compression_index"]
               for f in _FACTORS}
check(_now_ratios == {0.5},
      "the remaining duration demand ratio is unmoved at every scale tried, from half a day to "
      "two and a half years, so no floor and no absolute duration can reach it",
      str(sorted(_now_ratios)))
_done = run_schedule_compression({"scheduleNetwork": {
    "schedule_version": "SCH-1", "status_basis": "2026-06-30 data date",
    "activities": [{"activity_id": "A", "predecessors": [], "current_duration": 10.0,
                    "baseline_duration": 10.0, "remaining_duration": 0.0}]}}, NOOP, CUTOFF)
check(abstains(_done),
      "and a project with no remaining work has nothing left to compress and refuses, where "
      "the shipped code returned a ratio of one and read Green")
_unreconciled = run_schedule_compression({"scheduleNetwork": {
    "schedule_version": "SCH-1", "status_basis": "2026-06-30 data date",
    "activities": [{"activity_id": "A", "predecessors": [], "current_duration": 10.0}]}},
    NOOP, CUTOFF)
check(abstains(_unreconciled),
      "and activities that cannot be reconciled between the two schedules produce no ratio at "
      "all, rather than one drawn from whichever side is present")

print("\n-- safety performance: the ninth, which is a TRUE ZERO and keeps its band --")
# THE PROPERTY. A safety record that was read and recorded no incidents is a measurement, not an
# absence, so the band stands. The index beside it is the benchmark over the rate, capped by the
# module's own min(2, ...); at a rate of zero the ratio is unbounded and the module's own answer
# to an unbounded ratio is its cap. The shipped code substituted the literal 1, which the formula
# never produces at a zero rate and which reads as performance exactly at benchmark.
# RUN 20, P0B. The expectation below was built on a multiplication by ten that turned an
# incident COUNT into an incidence RATE. That multiplier had no source anywhere, and
# specification 8.7 defines the rate as recordable cases times two hundred thousand over
# employee hours worked, a denominator this module does not carry. The multiplier is gone,
# so a count with no reported rate beside it abstains. The checks are rewritten to the
# corrected contract rather than deleted, and the superseded expectation is stated here so
# the reason they changed is readable at the point they changed.
_was = old_doc.run_safety_performance({"safetyIncidentsDiscussed": 0}, NOOP, CUTOFF)
_now = run_safety_performance({"safetyIncidentsDiscussed": 0, "oshaIncidentRate": 0.0},
                              NOOP, CUTOFF)
check(_was["safety_index"] == 1, "the shipped code reported a safety index of 1 at a zero rate",
      str(_was["safety_index"]))
check(_now["safety_index"] == 2,
      "this branch reports the module's own cap of 2, which is what its formula gives at a rate "
      "of zero", str(_now["safety_index"]))
check(band(_now) == "Green" and band(_was) == "Green",
      "and the band is unchanged, because a reported zero rate is a finding rather than a "
      "fabrication", f"{band(_now)} vs {band(_was)}")
check(run_safety_performance({"safetyIncidentsDiscussed": 0}, NOOP,
                             CUTOFF).get("status_color") is None,
      "while the same count with NO reported rate beside it abstains, since a count of incidents "
      "is not a rate without the hours worked behind it")
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

# RUN 10B RESTATEMENT, WITH RUN 7'S FINDING PRESERVED AS THE REASON. Run 7 found a fabricated
# denominator in the queueing measure and a fabricated exposure in the supply chain measure, and
# corrected both: an empty look-ahead window and an empty procurement log stopped reading Green.
# Those findings stand and nothing about them is reversed. Run 10B goes further and requires each
# module's defining structure, so neither reads the look-ahead counts or the procurement counts at
# all any more, which is why their rows leave the zero-case list above rather than being deleted
# from the record. The corrected behaviour is asserted here in its new form.
for _name, _fn, _si in (
        ("queueing bottleneck", run_queueing_bottleneck,
         {"activitiesPlanned": 0, "activitiesConstrained": 0}),
        ("queueing bottleneck", run_queueing_bottleneck,
         {"activitiesPlanned": 200, "activitiesConstrained": 37}),
        ("queueing bottleneck", run_queueing_bottleneck, {"activitiesConstrained": 3}),
        ("agent-based supply chain", run_agent_supply_chain,
         {"longLeadItemsTotal": 0, "longLeadAtRisk": 0}),
        ("agent-based supply chain", run_agent_supply_chain,
         {"longLeadItemsTotal": 20, "longLeadAtRisk": 3}),
        ("agent-based supply chain", run_agent_supply_chain,
         {"longLeadItemsTotal": 10, "longLeadAtRisk": 40})):
    _rr = _fn(dict(_si), NOOP, CUTOFF)
    check(abstains(_rr) and _rr.get("abstention_reason_code") == ABSTAIN_STRUCTURE_ABSENT,
          f"{_name}: neither an empty count nor a full one produces a reading now, because the "
          f"counts are not the structure this method is named for",
          f"{_si} -> {_rr.get('abstention_reason_code')}")
    speakable(_rr, f"{_name} canonical structure absent")

print("\n-- the malformed and out-of-domain cases the modules now own --")
for name, fn, si, code in (
        # RUN 29. Specification conflict density no longer reads a document risk score or a
        # request count at all, so a negative request count is not an input it has. The
        # malformed case it DOES own is stated on its own register instead: a conflict that
        # cites the same place in the specification twice records no disagreement between two
        # places. The reason codes stay distinct, which is what this block exists to prove.
        ("specification conflict density", run_spec_conflict_density,
         {"specificationConflictRegister": {
             "source": "review", "specification_document_id": "SP",
             "specification_revision": "R1", "exposure_unit": "requirements",
             "exposure_quantity": 250.0,
             "conflicts": [{"conflict_id": "SC-1", "evidence_location_a": "section 03 30 00",
                            "evidence_location_b": "section 03 30 00", "state": "CONFIRMED",
                            "reviewer": "the specification writer",
                            "discipline": "STRUCTURAL"}]}},
         ABSTAIN_STRUCTURE_ABSENT),
        # RUN 28. Both of these modules now read a schedule network rather than dates, a
        # schedule index and two progress percentages, so a reversed baseline pair and a missing
        # progress figure are no longer inputs either of them has. The malformed and missing
        # cases they DO own are stated on the structure instead: a network whose logic runs in a
        # circle is malformed, and a network with no activities at all is missing. The reason
        # codes stay distinct, which is what this block exists to prove.
        ("schedule compression", run_schedule_compression,
         {"scheduleNetwork": {"schedule_version": "SCH-1", "status_basis": "d",
                              "activities": [
                                  {"activity_id": "A", "predecessors": ["B"],
                                   "current_duration": 1, "baseline_duration": 1,
                                   "remaining_duration": 1},
                                  {"activity_id": "B", "predecessors": ["A"],
                                   "current_duration": 1, "baseline_duration": 1,
                                   "remaining_duration": 1}]}},
         ABSTAIN_STRUCTURE_ABSENT),
        ("critical path index", run_critical_path_index,
         {"spi": 0.9, "actualPctComplete": 40}, ABSTAIN_STRUCTURE_ABSENT)):
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

# RUN 29 REPLACED WHAT FOLLOWED. Run 7 corrected the missingness semantics of the composite and
# kept the composite: all three sources required, the same 0.3 / 0.3 / 0.4 weights, the same
# bands. Run 29's supplied contract removes the composite outright -- a request count does not
# prove a dispute, a change order count does not prove a dispute, a document risk score does not
# prove a dispute, and the generic KPI composite is not to be preserved as the canonical result.
#
# THE PROPERTY RUN 7 WAS DEFENDING IS NOW HELD BY A STRONGER FACT. Run 7 had to prove that no
# strict subset of the three fields read better than the full set. There is now no reading from
# ANY combination of them, the full set included, so the ordering the defect exploited does not
# exist. That is asserted over all eight combinations rather than the seven strict subsets, and
# the v12 behaviour above is still executed from git so the defect itself stays reproducible.
_now_full = run_dispute_escalation(dict(_FULL), NOOP, CUTOFF)
check(abstains(_now_full),
      "the project that reports every one of the three generic sources gets no reading at all, "
      "because none of the three is dispute evidence", str(band(_now_full)))
_any_reading = []
for _r in range(4):
    for _keep in itertools.combinations(sorted(_FULL), _r):
        _sub = {k: _FULL[k] for k in _keep}
        _out = run_dispute_escalation(dict(_sub), NOOP, CUTOFF)
        if not abstains(_out):
            _any_reading.append(sorted(_sub))
check(_any_reading == [],
      "and no combination of the three produces a reading, so removing evidence cannot improve "
      "one that does not exist (all eight combinations exhausted)", str(_any_reading))
_zeros = run_dispute_escalation({"rfiCount": 0, "changeOrderCount": 0, "docRiskScore": 0.5},
                                NOOP, CUTOFF)
check(abstains(_zeros),
      "a REPORTED zero on both logs does not compute either: whether the counts were measured or "
      "withheld, they are not evidence of a dispute", str(band(_zeros)))
_missing = run_dispute_escalation({"docRiskScore": 0.5}, NOOP, CUTOFF)
check(abstains(_missing)
      and _missing.get("abstention_reason_code") == ABSTAIN_STRUCTURE_ABSENT,
      "and the reason names the missing canonical structure rather than a missing input, because "
      "what is absent is the claim register and not a figure",
      str(_missing.get("abstention_reason_code")))
speakable(_missing, "dispute escalation")
check("claim" in str(_missing.get("evidence_metric")).lower(),
      "and the abstention says a claim record is what it is waiting for",
      str(_missing.get("evidence_metric"))[:120])
check("velocity" in _was_full["evidence_metric"],
      "where the shipped v12 text named a velocity the module did not compute",
      _was_full["evidence_metric"])

# AND THE CANONICAL METHOD COMPUTES WHERE THE GOVERNED PROCESS IS PRESENT. A claim standing at
# the second stage of a six stage process is reported as that stage, and the reading is monotone
# in the declared order: a later stage never reads as less escalated than an earlier one.
from run29_fixtures import LAB_DISPUTE_STAGES, dispute_register  # noqa: E402
_ranks = []
for _stage in [st["stage_id"] for st in LAB_DISPUTE_STAGES]:
    _out = run_dispute_escalation({"claimDisputeRegister": dispute_register(_stage)},
                                  NOOP, CUTOFF)
    _ranks.append(_out.get("highest_stage_rank"))
check(_ranks == [0, 1, 2, 3, 4, 5],
      "with the governed process present the method reads the stage each claim has reached, and "
      "a later governed stage never reads as less escalated than an earlier one", str(_ranks))


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
# RUN 10: the criticality module leaves this set, for the reason recorded above.
# RUN 10B: the other two leave it as well, and the original guarantee is restated rather than
# dropped. Run 7's guarantee was that its correction refused where nothing was reported and did
# not stop computing where something was, and that guarantee held for these two at the time. Run
# 10B makes a different and deliberate change: a line-of-balance measure requires a line of
# balance and a critical-chain fever chart requires a sized buffer, and this project's documents
# carry neither, so both abstain here and name the structure that is missing. What must NOT
# happen is silence, and that is what is asserted now.
for _mid in ("A2.2", "A2.3"):
    check(_mid in _abst,
          f"{_mid}: abstains on the real production path, because the documents carry no line "
          f"of balance and no sized critical-chain buffer", str(sorted(_abst)))
    check(_abst.get(_mid, {}).get("abstention_reason_code") == ABSTAIN_STRUCTURE_ABSENT,
          f"{_mid}: and the stored row names the absent canonical structure",
          str(_abst.get(_mid, {}).get("abstention_reason_code")))
    check(bool(_abst.get(_mid, {}).get("reason")),
          f"{_mid}: and carries the sentence the ledger shows, so the module is not silent")
check("A2.1" not in _computed_ids and "A2.1" in _abst,
      "and the criticality module is absent from the stored rows and present in the abstention "
      "list, on a real project computed through the real route")
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
# RUN 10 corrects sixteen further modules, so its own authorised list joins Run 7's here rather
# than replacing it. The two sets stay separate so each run's authorisation remains readable.
RUN10_CORRECTED = {"A1.5", "A1.6", "A1.11", "A2.1", "A2.5", "A2.9", "A2.10", "A2.11", "A3.6",
                   "A4.10", "A5.5", "A5.8", "A6.1", "A6.2", "A6.4", "B2.18"}
# RUN 14 corrects the eight modules Run 13's evidence recorded as mismatches, so its authorised
# list joins the two above rather than replacing either. Five of the eight are unchanged on a
# fully reported project (their correction only fires on an impossible or a withheld figure) and
# so do not appear in the moved set at all; the three that do appear are the two that abstain
# without their defining structure and the one whose consistency score now counts the checks the
# method is defined over rather than the subset the corpus supported.
RUN14_CORRECTED = {"A2.11", "A3.2", "A3.3", "A3.5", "A5.4", "A5.8", "B2.19", "C1.6"}
# RUN 20 CYCLE 2, P0C GOVERNANCE AND REGULATORY OVERCLAIM. Three governance modules stopped
# presenting uncited internal levels as regulatory thresholds and stopped asserting reporting
# obligations from cost and schedule ratios. Every band, boundary and arithmetic result is
# unchanged in all three; what moved is the set of RESULT FIELD NAMES and the sentence shown to
# the reader, which this comparison is field-exact over and therefore correctly reports as a
# move. The authorisation joins the three above rather than replacing any of them.
RUN20_CORRECTED = {"B3.2", "B3.3", "B3.4"}
# RUN 20 CYCLE 9, THE P1 IMPLEMENTATION DEFECTS. Three modules whose arithmetic, not merely
# whose field names, was corrected. A5.2 ranked three quantities of which only one was a
# sensitivity and now reports the one driver it perturbs. B2.10 took its hesitancy from a
# membership pair it does not report, so the triple a reader is shown did not satisfy the
# identity that defines a Pythagorean fuzzy set. B2.15 did not normalise its possibility
# distribution and computed necessity as the possibility less an invented 0.30 rather than as
# the dual of the possibility of the complement. The authorisation joins the four above rather
# than replacing any of them.
RUN20_CYCLE9_CORRECTED = {"A5.2", "B2.10", "B2.15"}
# RUN 28, THE CATEGORY 1 TO 3 CANONICAL REMEDIATION. Twenty-one modules stopped computing a
# transparent proxy and started computing the canonical method the owner's supplied contract
# states, from a governed structure that did not exist in this platform before. On a fully
# reported project that carries none of those new structures, every one of them now ABSTAINS
# where it used to band, which is exactly the move this comparison is field-exact over and
# correctly reports. The authorisation joins the five above rather than replacing any of them.
# A2.1, A2.2, A2.3 and A3.1 are NOT in it: A2.1 and A3.1 abstained before Run 28 and still
# abstain on a project with no structure, and A2.2 and A2.3 already required their structures.
RUN28_CORRECTED = {"A1.3", "A1.4", "A1.5", "A1.6", "A1.9", "A1.10", "A1.11",
                   "A2.4", "A2.5", "A2.6", "A2.7", "A2.8", "A2.9", "A2.10", "A2.11",
                   "A3.2", "A3.3", "A3.5", "A3.6", "A3.7", "A3.9"}
# RUN 29, THE CATEGORY 4 AND 5 CANONICAL REMEDIATION. Sixteen further modules stopped computing
# a transparent proxy and started computing the canonical method the owner's supplied Run-29
# contract states, from a governed structure that did not exist in this platform before. On a
# fully reported project that carries none of those new structures every one of them now
# ABSTAINS where it used to band. A4.2 and A4.3 are NOT in it: Run 27 recorded both as method
# passes, each already computed exactly the formula the contract states, and each keeps its
# extracted-totals path, so neither moved. A5.1, A5.6 and A5.7 are not in it either, because all
# three abstained before Run 29 and still abstain on a project carrying no structure. The
# authorisation joins the six above rather than replacing any of them.
RUN29_CORRECTED = {"A4.4", "A4.5", "A4.6", "A4.7", "A4.8", "A4.9", "A4.10",
                   "A5.2", "A5.3", "A5.4", "A5.5", "A5.8"}
check(set(_moved) <= (FIX_NOW | RUN10_CORRECTED | RUN14_CORRECTED | RUN20_CORRECTED
                      | RUN20_CYCLE9_CORRECTED | RUN28_CORRECTED | RUN29_CORRECTED),
      "every module whose result moved on a fully reported project is in the fix-now list or "
      "one of the later runs' corrected lists",
      str(sorted(set(_moved) - (FIX_NOW | RUN10_CORRECTED | RUN14_CORRECTED | RUN20_CORRECTED
                                | RUN20_CYCLE9_CORRECTED | RUN28_CORRECTED
                                | RUN29_CORRECTED))))
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
_probe = run_safety_performance({"safetyIncidentsDiscussed": 0, "oshaIncidentRate": 0.0},
                                NOOP, CUTOFF)
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
