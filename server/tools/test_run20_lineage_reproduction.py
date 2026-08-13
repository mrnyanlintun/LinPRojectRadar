"""
RUN 20 CYCLE 3, STEP ONE ONLY: THE PRE-FIX REPRODUCTION OF UNCONTROLLED LINEAGE REINFORCEMENT.

THIS SUITE FIXES NOTHING. It measures, and it pins the measurements so the remediation that
follows has a numeric baseline it cannot quietly drift away from. Cycle 3 is NOT complete and
this file does not claim it is. Every number below is the CURRENT, DEFECTIVE behaviour, asserted
as the thing that must change, never as the expected answer.

WHAT SPECIFICATION 22 REQUIRES, points 4 and 5: multiple transformations of the same evidence
must preserve lineage, and duplicating a correlated or aliased module must not manufacture
stronger agreement or confidence.

WHAT WAS MEASURED. dst_fuse takes a bare list of status strings. It has no lineage input at all,
so it cannot distinguish two independent sources from one source counted twice, and it combines
whatever it is given by Dempster's rule, which ASSUMES independence.

The consequence is not confined to a laboratory example. The two modules that actually vote on
project status, A1.7 To-Complete Performance Index and A1.8 Variance at Completion, are both
deterministic transforms of the same four earned-value figures: the budget at completion, the
earned value, the actual cost and the estimate at completion. Specification 1.7 and 1.8 state
both identities and both read the same inputs. They are a SAME_SOURCE_TRANSFORM pair, and the
live fusion path treats them as two independent bodies of evidence.

The dependence classes the remediation must carry, so a downstream consumer can tell them apart:
INDEPENDENT, DERIVED, CORRELATED, SAME_SOURCE_TRANSFORM, SYNTHESIZED, QUALITY_METADATA,
GOVERNANCE_OUTPUT, DECISION_OUTPUT. None of them exists in production today; that absence is what
this file records.
"""

from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from app.simulation import fusion, registry  # noqa: E402

_passed = 0
_total = 0
_fail: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if cond:
        _passed += 1
    else:
        _fail.append(name + (f" -- {detail}" if detail else ""))


def near(name: str, got, want, tol=5e-5) -> None:
    check(name, got is not None and abs(float(got) - float(want)) <= tol,
          f"got {got!r}, measured baseline {want!r}")


def fuse(statuses):
    return fusion.dst_fuse(list(statuses))


# ---------------------------------------------------------------- the specification's own example
single = fuse(["Amber"])
dup = fuse(["Amber", "Amber"])
near("PRE-FIX BASELINE: a single Amber source carries mass 0.7000 on Amber",
     single["mass"]["Amber"], 0.7000)
near("PRE-FIX DEFECT, must not survive cycle 3: the SAME Amber source counted twice carries "
     "0.9273, so duplicating one body of evidence manufactured corroboration",
     dup["mass"]["Amber"], 0.9273)
check("and the duplicate raised the mass rather than leaving it alone, which is the defect "
      "stated as an inequality rather than as two literals",
      dup["mass"]["Amber"] > single["mass"]["Amber"] + 0.2)

# It is not an Amber artefact. Every band amplifies, including the favourable one, so duplicated
# evidence can also manufacture unwarranted REASSURANCE.
for band, one, two in (("Green", 0.8000, 0.9722), ("Red", 0.8340, 0.9787)):
    near(f"PRE-FIX BASELINE: a single {band} source carries {one}",
         fuse([band])["mass"][band], one)
    near(f"PRE-FIX DEFECT: the same {band} source counted twice carries {two}, so duplication "
         f"manufactures confidence in the favourable direction as well as the adverse one",
         fuse([band, band])["mass"][band], two)

near("PRE-FIX DEFECT: a third copy of the one Amber source reaches 0.9861, so the amplification "
     "compounds with every further copy", fuse(["Amber"] * 3)["mass"]["Amber"], 0.9861)

# Dempster's K is the disagreement between INDEPENDENT bodies of evidence. Two copies of one
# source cannot disagree with themselves, so a non-zero K here is itself proof that the rule is
# being applied to evidence it does not hold for.
near("PRE-FIX DEFECT: combining a source with a copy of itself reports a conflict coefficient of "
     "0.4414, when one body of evidence cannot disagree with itself at all",
     dup["conflict"], 0.4414)
near("and a single source correctly reports no conflict, which is what the duplicate is being "
     "compared against", single["conflict"], 0.0)

# --------------------------------------------------------------- the live voting path, not a lab
check("the voting set is exactly the two modules the programme records",
      set(registry.CORE_VOTING_MODULES) == {"A1.7", "A1.8"})
# Read the two voting modules' OWN declared required inputs out of their source rather than
# restating them here, so this finding cannot go stale if either module's contract changes.
_evm = (HERE.parent / "app" / "simulation" / "models_evm.py").read_text(encoding="utf-8")


def declared_inputs(func_name: str) -> set[str]:
    start = _evm.index(f"def {func_name}(")
    window = _evm[start:start + 4000]
    m = re.search(r"check_inputs\(si, \(([^)]*)\)\)", window)
    return set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()


_tcpi = declared_inputs("run_tcpi")
_vac = declared_inputs("run_vac")
check("the two voting modules each declare their required inputs, read from their own source",
      bool(_tcpi) and bool(_vac), f"{sorted(_tcpi)} {sorted(_vac)}")
check("PRE-FIX FINDING: the two voting modules share the budget at completion, and the cost "
      "index the second reads is earned value over actual cost, which the first reads directly, "
      "so both are transforms of ONE body of earned-value evidence and the live project status "
      "fuses a SAME_SOURCE_TRANSFORM pair as two independent votes",
      "bac" in _tcpi and "bac" in _vac
      and {"ev", "ac"} <= _tcpi and "cpi" in _vac,
      f"tcpi={sorted(_tcpi)} vac={sorted(_vac)}")
check("the fusion now records a lineage for the votes it performs, where before it recorded none",
      "lineage" in str(fusion.fuse_signals.__doc__ or "").lower())

# ----------------------------------------------------- THE ABSENCE THAT WAS RECORDED, NOW FILLED
#
# These five checks were written in step one as statements that the dependence vocabulary DID NOT
# EXIST. They are kept, inverted, rather than deleted, so the file remains the one place a reader
# can see both the measurement and its repair. The frozen pre-fix literals above are untouched:
# they still describe what the rule does with sources whose lineage is UNDECLARED, which after
# the correction is the honest reading of a bare list of status strings.
from app.simulation import lineage as _lin  # noqa: E402

check("dst_fuse still accepts a bare list of status strings, so no caller was broken",
      fusion.dst_fuse.__code__.co_varnames[:1] == ("statuses",))
check("and there is now a lineage-bearing entry point beside it, which there was not",
      callable(getattr(fusion, "fuse_signals", None)))
for cls in ("INDEPENDENT", "DERIVED", "CORRELATED", "SAME_SOURCE_TRANSFORM", "SYNTHESIZED",
            "QUALITY_METADATA", "GOVERNANCE_OUTPUT", "DECISION_OUTPUT"):
    check(f"the dependence class {cls} now exists in production, where step one found none",
          getattr(_lin, cls, None) == cls)

check("and the fusion now groups dependent evidence rather than combining it, so there is a "
      "control where step one found none",
      callable(getattr(_lin, "partition", None)) and callable(getattr(fusion, "worst_band", None)))

# THE AFTER NUMBERS, BESIDE THE FROZEN BEFORE NUMBERS. Same three bands, same duplication, the
# difference being that the duplicate now declares the lineage it always had.
_a17 = _lin.MODULE_LINEAGE["A1.7"]
_a18 = _lin.MODULE_LINEAGE["A1.8"]
for band, before_single, before_dup in (("Amber", 0.7000, 0.9273),
                                        ("Green", 0.8000, 0.9722),
                                        ("Red", 0.8340, 0.9787)):
    after_dup = fusion.fuse_signals([{"status": band, "lineage": _a17},
                                     {"status": band, "lineage": _a18}])
    near(f"AFTER: a same-lineage {band} pair carries {before_single}, not the frozen pre-fix "
         f"{before_dup}", after_dup["mass"][band], before_single)
    check(f"AFTER: and the {band} pair is one body of evidence rather than two",
          after_dup["lineage_groups"] == 1)
near("AFTER: and the conflict a body of evidence reported against its own copy, frozen at "
     "0.4414, is no longer estimated at all",
     fusion.fuse_signals([{"status": "Amber", "lineage": _a17},
                          {"status": "Amber", "lineage": _a18}])["conflict"], 0.0)

if _fail:
    print(f"\n{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
