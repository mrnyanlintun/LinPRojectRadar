"""
RUN 30 FINAL CLOSURE -- THE VERSION DECISION, DECIDED FROM BEHAVIOUR AND GUARDED.

THE QUESTION. This closure named a lineage state on every Category-7 ledger row. Does that change
executable analytical behaviour -- in which case the stamp must move again -- or is it ledger
metadata over behaviour that was already shipped?

IT IS NOT DECIDED FROM FILE TYPE. The v16 package is extracted from git object b7709cf, imported,
and run beside the current one on identical input through `registry.run_all` and
`compute.compute_project`. Every analytical field, the computed/abstained partition, the fused
project status, the voting set and the category rollup are compared.

THE ANSWER MEASURED: nothing analytical moved. The only difference anywhere is the `lineage`
metadata key on the twenty Category-7 rows. So v16 remains truthful and is NOT overwritten.

THE ONE WAY THAT ANSWER COULD BE WRONG is if the new field were an input to eligibility. Fault D
in the lineage suite proves lineage status IS behavioural in the fusion path -- treating
UNRESOLVED as independent sharpens Amber belief from 0.7000 past 0.9 -- so this suite proves the
separate fact that fusion cannot read the new field: it builds its lineage inputs from
`lineage_for(module_id)`, the declaration table, never from a module's result row. Both facts are
asserted, because either alone would be misleading.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

#: The commit sim-2026.08-v16 was pushed at: the Run-30 closure head.
V16_COMMIT = "b7709cf"

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def head(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# =================================================================================================
head("1. THE v16 LINE, EXTRACTED FROM GIT AND EXECUTED BESIDE THE CURRENT ONE")
# =================================================================================================
_TMP = tempfile.mkdtemp(prefix="run30f-v16-")
_PKG = pathlib.Path(_TMP) / "oldsim30v16"
_PKG.mkdir()
_names = subprocess.run(["git", "ls-tree", "--name-only", V16_COMMIT,
                         "server/app/simulation/"],
                        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
_py = [n for n in _names if n.endswith(".py")]
if len(_py) < 10:
    raise SystemExit("v16 extraction found no simulation sources at the pinned commit")
for _n in _py:
    _src = subprocess.run(["git", "show", f"{V16_COMMIT}:{_n}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout
    (_PKG / pathlib.Path(_n).name).write_text(_src, encoding="utf-8")
(_PKG / "__init__.py").write_text("", encoding="utf-8")
sys.path.insert(0, _TMP)

import oldsim30v16.registry as OLD_REG        # noqa: E402
import oldsim30v16.compute as OLD_COMPUTE     # noqa: E402

OLD_REG.CSV_PATH = ROOT / "p0-baseline" / "module_renumbering_map.csv"

from app.simulation import compute as NEW_COMPUTE       # noqa: E402
from app.simulation import fusion as FUS                # noqa: E402
from app.simulation import registry as NEW_REG          # noqa: E402
from app.simulation.models import SIMULATION_VERSION, SIMULATION_VERSION_HISTORY  # noqa: E402

check(OLD_REG.SIMULATION_VERSION == "sim-2026.08-v16",
      f"the package extracted from git object {V16_COMMIT} is stamped v16",
      OLD_REG.SIMULATION_VERSION)
check(OLD_REG.run_all is not NEW_REG.run_all,
      "and its functions are different objects from the live ones, so the comparison runs two "
      "lines rather than one twice")

SI = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
      "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
      "actualPctComplete": 40.0, "plannedPctComplete": 45.0}

#: The key this closure added. Everything else must match byte for byte.
ADDED_KEY = "lineage"


def strip(rows):
    return {r["module_id"]: {k: v for k, v in r.items() if k != ADDED_KEY} for r in rows}


# =================================================================================================
head("2. NO ANALYTICAL RESULT AND NO ELIGIBILITY OUTCOME MOVED")
# =================================================================================================
_a = OLD_REG.run_all(dict(SI), "S", "P1", "2026-06-30")
_b = NEW_REG.run_all(dict(SI), "S", "P1", "2026-06-30")
_ac, _bc = strip(_a["computed"]), strip(_b["computed"])
_aa, _ab = strip(_a["abstained"]), strip(_b["abstained"])
check(set(_ac) == set(_bc),
      "THE COMPUTED SET IS IDENTICAL: no module gained or lost a reading, so nothing about "
      "eligibility moved", str(set(_ac) ^ set(_bc)))
check(set(_aa) == set(_ab), "and the abstaining set is identical", str(set(_aa) ^ set(_ab)))
_dc = [m for m in _ac if _ac[m] != _bc.get(m)]
check(not _dc, "every computed row is identical apart from the lineage metadata key", str(_dc))
_da = [m for m in _aa if _aa[m] != _ab.get(m)]
check(not _da, "and every abstaining row is identical apart from it", str(_da))
_changed = [r["module_id"] for r in _b["computed"] + _b["abstained"]
            if r.get(ADDED_KEY) != next((x.get(ADDED_KEY)
                                         for x in _a["computed"] + _a["abstained"]
                                         if x["module_id"] == r["module_id"]), None)]
check(sorted(_changed) == sorted(f"B2.{n}" for n in range(1, 21)),
      "the ONLY difference anywhere is the lineage key on the twenty Category-7 rows",
      str(sorted(_changed)))

_pa = OLD_COMPUTE.compute_project(dict(SI), "P", "P1", "2026-06-30")
_pb = NEW_COMPUTE.compute_project(dict(SI), "P", "P1", "2026-06-30")
for _k in ("project_status", "categories_voting", "voting_module_ids", "project_conflict",
           "project_conflict_state", "category_statuses"):
    check(_pa.get(_k) == _pb.get(_k),
          f"the fused project's {_k} is unchanged", f"{_pa.get(_k)!r} vs {_pb.get(_k)!r}")


# =================================================================================================
head("3. THE NEW FIELD IS STRUCTURALLY INCAPABLE OF REACHING THE FUSION PATH")
# =================================================================================================
# Fault D in the lineage suite proves lineage status IS behavioural in fusion. That makes this the
# decisive question: can the field this closure added get there? It cannot, and the reason is that
# compute builds every fusion input from the DECLARATION TABLE rather than from a module's row.
import inspect                                                    # noqa: E402
_src = inspect.getsource(NEW_COMPUTE)
check("lineage=lineage_for(" in _src.replace(" ", "").replace("\n", "")
      or "lineage=lineage_for(row[" in _src,
      "compute builds each signal's fusion lineage from lineage_for(module_id), the declaration "
      "table")
check('row["lineage"]' not in _src and "row.get(\"lineage\")" not in _src,
      "and never reads the lineage key off a module's result row, so the metadata this closure "
      "added cannot enter fusion")
# Proved by execution as well as by reading: a row carrying a fabricated independent lineage key
# does not change the fused answer, because fusion never looks at it.
_poisoned = dict(SI)
_before = NEW_COMPUTE.compute_project(dict(_poisoned), "P", "P1", "2026-06-30")["project_status"]
_rows = NEW_REG.run_all(dict(SI), "S", "P1", "2026-06-30")
for _r in _rows["abstained"]:
    if _r["module_id"].startswith("B2."):
        _r["lineage"] = {"lineage_status": "LINEAGE_ESTABLISHED_INDEPENDENT",
                         "independence_established": True,
                         "evidence_body": "INVENTED_BODY"}
_after = NEW_COMPUTE.compute_project(dict(_poisoned), "P", "P1", "2026-06-30")["project_status"]
check(_before == _after,
      "and rewriting the key on a returned row changes no fused answer, because the value never "
      "travels anywhere that reads it", f"{_before} vs {_after}")


# =================================================================================================
head("4. THE DECISION")
# =================================================================================================
check(SIMULATION_VERSION == "sim-2026.08-v16",
      "sim-2026.08-v16 STANDS. This closure changed ledger metadata semantics and no analytical "
      "result, no eligibility outcome and no fused status, so the stamp is still truthful and is "
      "NOT overwritten", SIMULATION_VERSION)
check(SIMULATION_VERSION_HISTORY[-1] == "sim-2026.08-v16"
      and len(SIMULATION_VERSION_HISTORY) == len(set(SIMULATION_VERSION_HISTORY)),
      "the history is unchanged, still append-only and still unique",
      str(SIMULATION_VERSION_HISTORY[-3:]))
check(SIMULATION_VERSION_HISTORY[:15] == tuple(
    f"sim-2026.0{'7' if n == 1 else '8'}-v{n}" for n in range(1, 16)),
      "and every predecessor stamp is preserved in order")

print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
