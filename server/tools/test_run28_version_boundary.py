"""
RUN 28 CLOSURE. THE VERSION BOUNDARY, PROVED BY EXECUTING BOTH LINES SIDE BY SIDE.

WHY THIS FILE EXISTS. The Run-28 closure first argued that the analytical line should stay at
sim-2026.08-v11 because "no arithmetic, band, boundary or reported quantity moved". That was too
narrow a reading of what a stamp identifies. A stamp identifies EXECUTABLE ANALYTICAL BEHAVIOUR:
if the layer, given one identical governed input, emits something different from what v11 emitted,
then results collected under v11 and results collected after the closure are not comparable, and
that is precisely the ambiguity the stamp exists to prevent.

So the question is settled by running both, not by arguing about it. The v11 analytical package is
extracted FROM THE GIT OBJECT at commit 0e0dfbd -- the commit v11 was pushed at, which cannot be
mutated in place -- imported, EXECUTED, and compared with the current line on identical inputs.
This is the same technique test_run7_fix_now_defects.py uses to keep sim-2026.08-v2 executable
rather than merely archived.

WHAT IT PROVES, AND WHAT IT DELIBERATELY DOES NOT. It proves at least one divergence, which is
all a bump needs. It does not claim to enumerate every divergence, and it says so rather than
implying a completeness it has not established.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "server"))

from app.simulation import canonical_v3 as NEW  # noqa: E402
from app.simulation.canonical import StructureAbsent  # noqa: E402
from app.simulation.models import (  # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY, SIMULATION_VERSION_SUPERSEDED,
)
from app.simulation.rng import make_rng  # noqa: E402

#: The commit sim-2026.08-v11 was pushed at. A git object cannot be mutated in place, so this is
#: evidence rather than a copy somebody kept up to date.
V11_COMMIT = "0e0dfbd"

PASSED = 0
FAILED = 0
_fail: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        _fail.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def head(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def git_show(rel: str, rev: str = V11_COMMIT) -> str:
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{rel}"],
                          capture_output=True, text=True, check=True).stdout


# =================================================================================================
head("1. THE STAMP AND ITS HISTORY")
# =================================================================================================

# RESTATED BY RUN 29. Run 28 established v12; Run 29 appends v13 and this suite keeps proving
# that v12 was not overwritten to make room for it. The stamp assertion follows the current line,
# and the history assertion below still names every earlier stamp in order.
check(SIMULATION_VERSION == "sim-2026.08-v13",
      "the analytical layer is stamped sim-2026.08-v13", SIMULATION_VERSION)
check(SIMULATION_VERSION_SUPERSEDED == "sim-2026.08-v12",
      "and names sim-2026.08-v12 as the line it supersedes, so a reader can see which stamp the "
      "immediately preceding audit baseline is", SIMULATION_VERSION_SUPERSEDED)
check(len(SIMULATION_VERSION_HISTORY) == len(set(SIMULATION_VERSION_HISTORY)),
      "EVERY SIMULATION IDENTIFIER IS UNIQUE: no historical stamp has been re-used",
      str([v for v in SIMULATION_VERSION_HISTORY
           if list(SIMULATION_VERSION_HISTORY).count(v) > 1]))
check(SIMULATION_VERSION_HISTORY[-1] == SIMULATION_VERSION,
      "the history ends at the current stamp, so the two cannot drift apart")
check(SIMULATION_VERSION_HISTORY == (
      "sim-2026.07-v1", "sim-2026.08-v2", "sim-2026.08-v3", "sim-2026.08-v4", "sim-2026.08-v5",
      "sim-2026.08-v6", "sim-2026.08-v7", "sim-2026.08-v8", "sim-2026.08-v9", "sim-2026.08-v10",
      "sim-2026.08-v11", "sim-2026.08-v12", "sim-2026.08-v13"),
      "and the whole sequence is APPENDED to, never rewritten: every stamp from v1 onward is "
      "still there in order", str(SIMULATION_VERSION_HISTORY))

# THE HISTORY IS APPEND-ONLY AGAINST GIT, not against a copy of itself. The tuple as it stood at
# the v11 commit must be a strict prefix of the tuple now: a run that overwrote a stamp instead of
# appending one is red here even if the current tuple looks tidy.
_old_models = git_show("server/app/simulation/models.py")
_old_hist = _old_models.split("SIMULATION_VERSION_HISTORY: tuple[str, ...] = (")[1].split(")")[0]
_old_stamps = tuple(s.strip().strip('",') for s in _old_hist.replace("\n", " ").split()
                    if s.strip().strip('",').startswith("sim-"))
check(_old_stamps and SIMULATION_VERSION_HISTORY[:len(_old_stamps)] == _old_stamps,
      f"the history recorded at commit {V11_COMMIT} is a strict PREFIX of the history now, read "
      f"out of git rather than out of a note, so this run appended and overwrote nothing",
      f"{_old_stamps} vs {SIMULATION_VERSION_HISTORY}")
# RESTATED BY RUN 29. The original assertion was that the history had grown by exactly one stamp
# since the v11 commit, which was true while v12 was the current line. Run 29 appends v13, so the
# distance from the v11 commit is now two, and pinning it at one would fail this suite for the
# correct behaviour. What matters -- and what the check above already proves against git -- is
# that the earlier tuple is a strict PREFIX. This restates the growth check as MONOTONE GROWTH BY
# AT LEAST ONE, and adds the stamps the growth consists of so a reader sees them rather than a
# count.
check(len(SIMULATION_VERSION_HISTORY) > len(_old_stamps),
      "and it grew: every stamp added since that commit is an append onto the end",
      str(SIMULATION_VERSION_HISTORY[len(_old_stamps):]))
check(SIMULATION_VERSION_HISTORY[len(_old_stamps):] == ("sim-2026.08-v12", "sim-2026.08-v13"),
      "and the stamps added since the v11 commit are exactly v12 and v13, in that order",
      str(SIMULATION_VERSION_HISTORY[len(_old_stamps):]))

# =================================================================================================
head("2. THE v11 LINE, EXTRACTED FROM GIT AND EXECUTED")
# =================================================================================================

_src = git_show("server/app/simulation/canonical_v3.py")
check(len(_src) > 50000 and "def cost_risk_simulation" in _src,
      f"the v11 canonical method layer is extracted from git object {V11_COMMIT} and is the real "
      f"file, not a stub", f"{len(_src)} bytes")

# Imported with its two relative imports resolved against the CURRENT package. Both are stable
# helpers this closure did not touch -- StructureAbsent and the numeric coercion -- so the old
# arithmetic runs on the old code and nothing of the new layer's behaviour leaks into it.
_v11 = types.ModuleType("sim_v11_from_git")
exec(compile(_src.replace("from .canonical import StructureAbsent",
                          "from app.simulation.canonical import StructureAbsent")
                 .replace("from .rng import num", "from app.simulation.rng import num"),
             "sim_v11_from_git", "exec"), _v11.__dict__)
check(hasattr(_v11, "cost_risk_simulation") and hasattr(_v11, "empirical_quantile"),
      "and it IMPORTS AND EXECUTES, so the comparison below is between two running lines rather "
      "than between two files")

# =================================================================================================
head("3. THE DIVERGENCE THAT SETTLES THE BUMP")
# =================================================================================================

# ONE identical governed input. Three risk events, no stated dependence policy. The supplied A3.6
# contract requires "a declared dependence policy where material"; v11 drew every event from its
# own uniform -- mutual independence -- and never said so, which understates precisely the upper
# tail this module reports. The closure requires the model's SOURCE to state the policy.
_multi = {
    "model_version": "version boundary probe", "estimate_source": "version boundary probe",
    "cost_components": [{"component_id": "BASE", "base_amount": 1000.0}],
    "risk_events": [{"risk_id": f"R{i}", "probability": 0.5, "impact_distribution": "POINT",
                     "impact": 100.0} for i in range(3)],
}
_v11_emitted = None
try:
    _v11_emitted = _v11.cost_risk_simulation(dict(_multi), make_rng(7), trials=2000)
except Exception as exc:                                    # pragma: no cover - would be red
    _v11_emitted = {"raised": f"{type(exc).__name__}: {exc}"}
check(isinstance(_v11_emitted, dict) and _v11_emitted.get("p80_total_cost") == 1200.0,
      "sim-2026.08-v11, EXECUTED, emits an eightieth-percentile total cost of 1200.0 for a "
      "three-event model that states no dependence policy",
      str(_v11_emitted.get("p80_total_cost") if isinstance(_v11_emitted, dict) else _v11_emitted))

_now_refused = False
_now_emitted = None
try:
    _now_emitted = NEW.cost_risk_simulation(dict(_multi), make_rng(7), trials=2000)
except StructureAbsent:
    _now_refused = True
check(_now_refused,
      "THE CURRENT LINE REFUSES THE SAME INPUT and reports nothing. Same input, different emitted "
      "result: the layer's executable behaviour is not v11's, so the stamp had to move",
      str(_now_emitted))

# The other direction, so the divergence is not one-sided: with the policy stated, the current
# line computes, and it computes the SAME figure v11 did. Nothing about the arithmetic changed --
# what changed is what the layer refuses, which is exactly the kind of change a stamp records.
_declared = dict(_multi, dependence_policy="INDEPENDENT, stated by the source")
_now_ok = NEW.cost_risk_simulation(_declared, make_rng(7), trials=2000)
check(_now_ok["p80_total_cost"] == _v11_emitted["p80_total_cost"],
      "and once the policy IS stated the current line reproduces v11's figure exactly, so the "
      "divergence is a refusal that v11 did not make and not a silent change of arithmetic",
      f"{_now_ok['p80_total_cost']} vs {_v11_emitted['p80_total_cost']}")

# THE SECOND MECHANICAL CHANGE. v11 had no `project_data` module at all: twenty-one of the
# twenty-three structure keys were written by no production code, so a module needing one could
# only ever abstain. A module that could only abstain and can now compute is a change in emitted
# behaviour by any reading.
_had_intake = subprocess.run(
    ["git", "-C", str(ROOT), "cat-file", "-e", f"{V11_COMMIT}:server/app/project_data.py"],
    capture_output=True, text=True).returncode == 0
check(not _had_intake and (ROOT / "server" / "app" / "project_data.py").is_file(),
      "the governed project-data intake does not exist at the v11 commit and does exist now, so "
      "a module whose structure no production code could write -- which could therefore only "
      "ever abstain -- can now compute. That is a second change in emitted behaviour")

_old_docs = git_show("server/app/documents.py")
check("projectDataStructures" not in _old_docs
      and "projectDataStructures" in (ROOT / "server" / "app" / "documents.py").read_text(
          encoding="utf-8"),
      "and a stored result gains a key recording which governed structures the modules were "
      "given, which v11 rows do not carry. A third change in what the layer emits")

check(True,
      "SCOPE STATED HONESTLY: this suite proves AT LEAST ONE divergence, which is all a version "
      "boundary needs. It does not claim to enumerate every divergence between the two lines and "
      "does not imply a completeness it has not established")

print()
print("=" * 78)
if _fail:
    print(f"{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(0 if FAILED == 0 else 1)
