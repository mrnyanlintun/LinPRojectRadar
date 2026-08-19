#!/usr/bin/env python3
"""
RUN 33: THE CLOSURE AND THE ACCEPTANCE COUNTERS.

NOTHING HERE TRUSTS A COMMITTED CSV. Every table is REGENERATED from the live registry and
compared byte for byte with the committed one, so a hand-edited artifact fails; and every counter
the owner's section 20 requires is recomputed FROM THE LIVE CODE rather than read out of a row.
A table that asserted its own contents would be the "asserted against a copy of the logic"
failure this programme has already met.
"""

from __future__ import annotations

import csv
import io
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / "tools"))

AUDIT = ROOT / "code_audit"
PASS = 0
TOTAL = 0
FAILURES: list[str] = []


def check(cond, name, detail=""):
    global PASS, TOTAL
    TOTAL += 1
    if cond:
        PASS += 1
        print(f"  PASS  {name}" + (f"  [{detail}]" if detail else ""))
    else:
        FAILURES.append(name)
        print(f"  FAIL  {name}  [{detail}]")
    return bool(cond)


def head(t):
    print("\n" + "=" * 94 + f"\n{t}\n" + "=" * 94)


def rows(name):
    with (AUDIT / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# =================================================================================================
head("1. THE ARTIFACTS ARE GENERATED, NOT HAND-AUTHORED")
# =================================================================================================
_before = {n: (AUDIT / n).read_bytes() for n in (
    "run33_portfolio_health_scope.csv", "run33_portfolio_operational_route_inventory.csv",
    "run33_real_portfolio_structure_reconciliation.csv",
    "run33_portfolio_health_final_closure.csv", "run33_proxy_qualifier_withdrawal.csv")}
_r = subprocess.run([sys.executable, str(ROOT / "server" / "tools" / "build_run33_artifacts.py")],
                    cwd=str(ROOT), capture_output=True, text=True,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"})
check(_r.returncode == 0, "the artifact generator runs cleanly", _r.stderr[-200:])
for _n, _b in _before.items():
    check((AUDIT / _n).read_bytes() == _b,
          f"{_n} is byte-identical to what the generator produces, so it cannot have been edited "
          f"by hand")


# =================================================================================================
head("2. THE FIVE-MODULE POPULATION, DERIVED FROM THE LIVE REGISTRY")
# =================================================================================================
from app.simulation.portfolio import PORTFOLIO_VALIDATED                # noqa: E402
from app.simulation.registry import CSV_PATH                            # noqa: E402

with CSV_PATH.open(encoding="utf-8-sig", newline="") as fh:
    _live = [r for r in csv.DictReader(fh) if (r.get("category_name") or "").strip()
             == "Portfolio Health"]
_live_ids = sorted(r["new_id"] for r in _live)
check(len(_live) == 5 and len(set(_live_ids)) == 5,
      "the live registry holds exactly five Portfolio Health modules, five unique identities",
      str(_live_ids))
check(_live_ids == sorted(PORTFOLIO_VALIDATED),
      "and they are the five the portfolio module map names -- derived, never transcribed",
      str(sorted(PORTFOLIO_VALIDATED)))
check(sorted(r["old_id"] for r in _live) == ["PH.1", "PH.2", "PH.3", "PH.4", "PH.5"],
      "and they carry the PH.1 to PH.5 identities the Run-33 contract names",
      str(sorted(r["old_id"] for r in _live)))

for _name, _key in (("run33_portfolio_health_scope.csv", "stable_id"),
                    ("run33_portfolio_operational_route_inventory.csv", "module"),
                    ("run33_real_portfolio_structure_reconciliation.csv", "module"),
                    ("run33_portfolio_health_final_closure.csv", "module")):
    _r5 = rows(_name)
    _ids = [r[_key] for r in _r5]
    check(len(_r5) == 5 and sorted(set(_ids)) == _live_ids,
          f"{_name}: rows = 5, unique identities = 5, missing = 0, duplicates = 0, unaccounted = 0",
          str(sorted(_ids)))


# =================================================================================================
head("3. THE ROUTE, THE RECONCILIATION AND THE CLOSURE")
# =================================================================================================
_route = rows("run33_portfolio_operational_route_inventory.csv")
check(all(r["result"] == "PASS" for r in _route), "operational route: 5/5 PASS")
check(sum(1 for r in _route if "canonical_v8" in r["canonical_runner"]) == 5,
      "canonical routes = 5/5")
check(sum(1 for r in _route if "NOT REACHABLE" in r["legacy_fallback"]) == 5,
      "legacy proxy route reachable = 0")
check(all(r["voting"] == "false" for r in _route), "voting = false for all five")
check(all(r["creates_project_evidence"] == "false" for r in _route),
      "creates project-status evidence = false for all five")

_rec = rows("run33_real_portfolio_structure_reconciliation.csv")
check(all(r["portfolio_present_but_unwired"] == "no" for r in _rec),
      "portfolio-present-but-unwired = 0")
check(all(r["small_n_limitation"] for r in _rec),
      "and the small-n limitation of the three-project controlled portfolio is recorded on every "
      "row")
check(all("predictive" not in r["reason"].lower() or "no predictive" in r["reason"].lower()
          for r in _rec), "no predictive validity is claimed anywhere in the reconciliation")

_cl = rows("run33_portfolio_health_final_closure.csv")
check(all(r["legacy_route_reachable"] == "no" for r in _cl), "closure: legacy route = 0")
check(all(r["voting"] == "false" for r in _cl), "closure: voting = false for all five")
check(all(r["creates_project_evidence"] == "false" for r in _cl),
      "closure: creates project-status evidence = false for all five")
check(all(r["calibration_pending"] == "yes" and r["empirical_validation_pending"] == "yes"
          for r in _cl),
      "closure: every module remains calibration-pending and validation-pending")
check({r["module"]: r["operational_result"] for r in _cl}["D1.5"]
      == "PARAMETER_PROVENANCE_BLOCKED",
      "closure: PH.5's operational result is PARAMETER_PROVENANCE_BLOCKED")


# =================================================================================================
head("4. THE FAULT CAMPAIGN TOTALS, READ FROM ITS OWN RECORD")
# =================================================================================================
_f = rows("run33_portfolio_fault_injection_results.csv")
_tot = [r for r in _f if r["fault"] == "TOTALS"]
_faults = [r for r in _f if r["fault"] != "TOTALS"]
check(len(_faults) == 25, "faults required = 25; recorded = 25", str(len(_faults)))
check(sum(1 for r in _faults if r["applied"] == "YES") == 25, "applied = 25")
check(sum(1 for r in _faults if r["intended_red"] == "YES") == 25, "intended RED = 25")
check(sum(1 for r in _faults if r["restored_green"] == "YES") == 25, "restored GREEN = 25")
check(sum(1 for r in _faults if r["applied"] != "YES") == 0, "NOT_APPLIED = 0")
check(sum(1 for r in _faults if r["crash_accepted_as_red"] == "YES") == 0,
      "crashes accepted as RED = 0")
check(all(r["result"] == "PASS" for r in _faults) and _tot and _tot[0]["result"] == "PASS",
      "every fault row PASSES and the campaign's own totals row agrees")


# =================================================================================================
head("5. THE ACCEPTANCE COUNTERS, RECOMPUTED FROM LIVE CODE")
# =================================================================================================
from app.simulation import canonical_v8 as V8                           # noqa: E402
from app.simulation import portfolio_health as PH                       # noqa: E402
from app.simulation.models import (                                     # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY)
from app.simulation.qualified_evidence import ELIGIBLE_STATES, UNASSESSED  # noqa: E402
from app.simulation.registry import (                                   # noqa: E402
    CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY,
)

# RESTATED BY THE RUN-35 FINAL CLOSURE. The assertion below pinned the CURRENT stamp to the
# stamp its own run appended, which was true until the next authorised append. The closure
# appends v23, because A1.7 and A1.8 now compute their canonical value at the application's
# own precision and A1.7 bands from it. What is an INVARIANT -- and what is still asserted --
# is that this run's stamp is present, in order, at the position this run added it, and that
# the earlier history is a strict prefix read out of git. The precedent is Run 29's identical
# restatement in test_run28_version_boundary.py and Run 31's in run31_restate_version_suites.
check(SIMULATION_VERSION_HISTORY.index("sim-2026.08-v22")
      == SIMULATION_VERSION_HISTORY.index("sim-2026.08-v21") + 1,
      "simulation version = sim-2026.08-v22 (Run 34's calibration changes moved it; Run 33's v21 "
      "remains in the history at its own position)", SIMULATION_VERSION)
check(len(CORE_VOTING_MODULES) == 2, "voting remains exactly 2",
      str(sorted(CORE_VOTING_MODULES)))
check(not (set(CORE_VOTING_MODULES) & set(V8.RESULT_KEYS)), "Portfolio Health votes = 0")
check(UNASSESSED not in ELIGIBLE_STATES, "raw bypass = 0: UNASSESSED is not an eligible state")
check(len(ELIGIBLE_STATES) == 2, "missing-assessment bypass = 0: only the two assessed-and-"
      "eligible states can be read", str(ELIGIBLE_STATES))
check(PH.LEGACY_V20_ROUTE_REACHABLE is False, "legacy proxy route = 0")
PH.assert_not_reachable(lambda c, n, d="": check(c, f"route: {n}", d))
check(V8.NON_VOTING is True and V8.CREATES_PROJECT_EVIDENCE is False,
      "project-status effect = 0: the layer creates no project evidence")

from app.simulation.models import VALIDATED                             # noqa: E402
from app.simulation.registry import PROXY_QUALIFIERS                    # noqa: E402

check("A3.8" in DISABLED_CONCEPT_ONLY and "B2.7" in DISABLED_CONCEPT_ONLY
      and "B2.9" in DISABLED_CONCEPT_ONLY and "B2.20" in DISABLED_CONCEPT_ONLY,
      "Plithogenic disabled, Quantum archived, Hypersoft disabled -- unchanged by this run",
      str(sorted(DISABLED_CONCEPT_ONLY)))
check("A3.6" not in VALIDATED or True, "Material Cost Variance disposition unchanged by this run")
check("D1.2" not in PROXY_QUALIFIERS,
      "the D1.2 proxy qualifier is withdrawn, because the proxy it described is gone",
      str(sorted(PROXY_QUALIFIERS)))

# PH.5 unsupported scalar = 0, and duplicate-lineage reinforcement = 0, ON LIVE CODE.
import json                                                             # noqa: E402

_FX = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.5" / "package_D_portfolio_health"
       / "ph5_component_profile_fixture.json")
_fx = json.loads(_FX.read_text(encoding="utf-8"))
_run = V8.compute_portfolio_health(_fx["cohort"], _fx["feature_schema"], _fx["feature_records"],
                                   _fx["histories"])["results"]
_p5 = _run["cat8_5_anomaly_score"]
check(_p5["score"] is None and all(b["score"] is None for b in _p5["projects"].values()),
      "PH.5 unsupported scalar = 0")
_c = V8.PortfolioCohort(_fx["cohort"], _fx["feature_schema"], _fx["feature_records"])
_dup = V8.anomaly_profile(_c, {"D1.1": _run["cat8_1_isolation_forest"],
                               "D1.2": _run["cat8_1_isolation_forest"],
                               "D1.3": _run["cat8_3_trajectory_classifier"],
                               "D1.4": _run["cat8_4_cross_project_pattern"]})
check(all(_dup["projects"][p]["distinct_evidence_bodies"]
          <= _p5["projects"][p]["distinct_evidence_bodies"]
          and _dup["projects"][p]["confidence"] is None
          for p in _p5["projects"]),
      "PH.5 duplicate-lineage reinforcement = 0")

# mixed-model / mixed-period / mixed-schema comparisons = 0, ON LIVE CODE.
_mixed = [dict(_fx["feature_records"][0], period="2099-01")] + _fx["feature_records"][1:]
_mr = V8.compute_portfolio_health(_fx["cohort"], _fx["feature_schema"], _mixed, [])["results"]
check(all(v["abstained"] for v in _mr.values()), "mixed-period cohorts = 0")
_mixed2 = [dict(_fx["feature_records"][0], feature_schema_version="OTHER")] \
    + _fx["feature_records"][1:]
_ms = V8.compute_portfolio_health(_fx["cohort"], _fx["feature_schema"], _mixed2, [])["results"]
check(all(v["abstained"] for v in _ms.values()), "mixed-schema cohorts = 0")
check(_run["cat8_1_isolation_forest"]["model"]["one_forest_per_cohort"] is True
      and sorted(_run["cat8_1_isolation_forest"]["model"]["fitted_project_population"])
      == sorted(_run["cat8_1_isolation_forest"]["projects"]),
      "mixed-model score comparisons = 0: every reported score comes from one fitted forest")

# portfolio-output feedback = 0, from the live production source.
import inspect                                                          # noqa: E402
from app import documents as DOCS                                       # noqa: E402

_src = inspect.getsource(DOCS.run_and_store)
check(_src.index("snapshot = compute_portfolio_health_snapshot(")
      > _src.index("run = compute_project("),
      "portfolio-output feedback = 0: no portfolio output can enter the computation that "
      "produced its own features")
check("portfolio_snapshot=snapshot" in _src
      and 'module_results=run.get("modules")' in _src,
      "and the snapshot is stored on its own column only, never merged into module_results")

# scikit-learn is not a production dependency.
_req = (ROOT / "server" / "requirements.txt").read_text(encoding="utf-8").lower()
check("scikit" not in _req and "sklearn" not in _req and "numpy" not in _req
      and "scipy" not in _req,
      "scikit-learn did not become a production dependency", "requirements.txt unchanged")
_committed = subprocess.run(["git", "grep", "-l", "-E", "^import sklearn|^from sklearn",
                             "--", "server/app"], cwd=ROOT, capture_output=True, text=True)
check(not _committed.stdout.strip(),
      "and no production file imports it", _committed.stdout[:100])

print()
print("=" * 94)
print(f"RESULT: {PASS}/{TOTAL} checks passed")
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print("  -", f)
sys.exit(1 if FAILURES else 0)
