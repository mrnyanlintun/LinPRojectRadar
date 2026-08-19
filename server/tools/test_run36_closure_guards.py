"""
RUN 36 CLOSURE. THE FIFTEEN NAMED ORACLES FOR THE CLOSURE FAULT CAMPAIGN.

ONE NAMED CHECK PER FAULT in the closure contract's section-14 list, so the campaign can require
that the guard that goes red is the one the fault was aimed at. Every oracle is derived from live
authority or from execution; none asserts a defect's own sentence back at itself.

A CRASH IS NOT A RED. Everything that executes a module is wrapped and a raised exception is
reported as its own state, so a module that dies is red for dying rather than counted as an
abstention.
"""

from __future__ import annotations

import csv
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from app.simulation import registry as REG                       # noqa: E402
from app.simulation import models_sim as MS                      # noqa: E402
from app.simulation.models import (                              # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY)
import participant_packages as PP                                # noqa: E402

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(name, ok, why, got=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {name}  {why}")
    else:
        FAILED += 1
        FAILURES.append(f"{name}  {why}")
        print(f"FAIL  {name}  {why}  [{got}]")


AUDIT = ROOT / "code_audit"
PKG = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.2"
       / "Opus_Gubernatio_Synthetic_Programme_v0.2" / "package_A_project_structures")
SI = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
      "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
      "evidenceQualification": {"qualification_state": "QUALIFIED",
                                "timeliness_status": "TIMELY",
                                "verification_status": "verified",
                                "source_authority": "system_of_record"}}


def run(mid):
    try:
        r = REG.run_module(mid, dict(SI), (lambda: 0.5), "2026-06-30")
    except Exception as exc:                                     # noqa: BLE001
        return {"__state__": "CRASHED", "__why__": f"{type(exc).__name__}: {exc}"[:160]}
    r["__state__"] = "ABSTAINS" if r.get("insufficient_data") else "COMPUTES"
    return r


def rows(name):
    p = AUDIT / name
    if not p.is_file():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def text(rel):
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.is_file() else ""


print("=" * 94)
print("RUN 36 CLOSURE ORACLES")
print("=" * 94)

_a11 = run("A1.1")
_ds = text("assets/js/ds_defensibility_evidence.js")
_a11_served = (re.search(r'"A1\.1": \{(.*?)\},\n', _ds, re.S) or type("x", (), {"group":
                                                                               lambda *a: ""})()).group(1)

# ---------------------------------------------------------------- 1-5 A1.1
_gate_ok = []
MS.assert_retained_adaptation_not_reachable(lambda ok, what, got="": _gate_ok.append(bool(ok)))
check("run36c.fault01.retained_adaptation_not_a_fallback",
      all(_gate_ok) and _a11.get("__state__") == "ABSTAINS",
      "the retained scalar adaptation cannot be reached from production and cannot become a "
      "fallback when the canonical inputs are absent",
      f"gate_checks={_gate_ok} state={_a11.get('__state__')}")
check("run36c.fault02.no_canonical_result_without_the_contract",
      _a11.get("p50_eac") is None and _a11.get("p80_eac") is None
      and _a11.get("overrun_pct_p80") is None,
      "A1.1 emits no numeric canonical result while its required structure and driver-to-EAC "
      "mapping are absent",
      json.dumps({k: _a11.get(k) for k in ("p50_eac", "p80_eac", "overrun_pct_p80")}))
check("run36c.fault03.no_status_colour",
      _a11.get("status_color") is None and _a11.get("band_asserted") is False,
      "A1.1 emits no status colour", f"{_a11.get('status_color')!r}")
check("run36c.fault04.a1_1_does_not_vote",
      "A1.1" not in REG.CORE_VOTING_MODULES
      and sorted(REG.CORE_VOTING_MODULES) == ["A1.7", "A1.8"],
      "A1.1 does not vote and the voting set is still exactly the two",
      str(sorted(REG.CORE_VOTING_MODULES)))
check("run36c.fault05.defensibility_does_not_call_the_adaptation_canonical",
      "DISABLED_INSUFFICIENT_INPUT" in _a11_served
      and "COMPUTES_FROM_AVAILABLE_EVIDENCE" not in _a11_served
      and "is not the canonical operational method" in _a11_served,
      "the served defensibility record does not describe the retained adaptation as the "
      "canonical method", _a11_served[:160])

# ---------------------------------------------------------------- 6-7 the version boundary
_v24 = subprocess.run(["git", "show",
                       "822d80928367c0f422fac5f2564705279e718dd1:server/app/simulation/models.py"],
                      cwd=ROOT, capture_output=True, text=True)
# RESTATED BY RUN 41, RUN 36'S FINDING PRESERVED. The subject of this guard is that the v24
# PREDECESSOR was not rewritten when v25 superseded it, and that claim is unchanged and still
# checked below. What cannot survive an authorised append is the clause pinning the LIVE stamp to
# v25; Run 41 appends v26. It is replaced by the invariant it was standing in for: v25 is still
# present exactly once, still directly after v24, so v25 was appended BESIDE v24 rather than over
# it and has itself since been superseded rather than overwritten.
check("run36c.fault06.v24_predecessor_not_rewritten",
      _v24.returncode == 0 and 'SIMULATION_VERSION = "sim-2026.08-v24"' in _v24.stdout
      and SIMULATION_VERSION_HISTORY.count("sim-2026.08-v24") == 1
      and SIMULATION_VERSION_HISTORY.count("sim-2026.08-v25") == 1
      and (SIMULATION_VERSION_HISTORY.index("sim-2026.08-v25")
           == SIMULATION_VERSION_HISTORY.index("sim-2026.08-v24") + 1),
      "the v24 predecessor reconstructs from its own git object and still says v24, and v25 was "
      "appended beside it rather than over it",
      f"live={SIMULATION_VERSION}")
_proof = rows("run36_v24_v25_a1_1_execution_proof.csv")
_moved = [r for r in _proof if r["module_id"] == "ACCEPTANCE_COUNTER"]
_claims = {r["module_id"]: (r["expected"], r["observed"], r["result"]) for r in _proof
           if r["module_id"] != "ACCEPTANCE_COUNTER"}
check("run36c.fault07.execution_proof_claims_no_false_divergence",
      bool(_claims)
      and all(res == "PASS" for _e, _o, res in _claims.values())
      and _claims.get("A1.1", (None, None, None))[1] == "DIVERGED"
      and all(_claims[m][1] == "IDENTICAL" for m in ("A1.7", "A1.8", "A6.2", "B4.3", "D1.1"))
      and bool(_moved) and _moved[0]["v25_row"] == "A1.1"
      and _moved[0]["observed"] == "1" and _moved[0]["result"] == "PASS",
      "the v24 to v25 proof claims divergence only where both executed lines actually diverged, "
      "and exactly one module moved across the boundary",
      json.dumps(_claims)[:220])

# ---------------------------------------------------------------- 8-10 parsimony
_cr = rows("run36_parsimony_crossrun_reconciliation.csv")
_disc_rows = [r for r in _cr if r["module_id"] not in ("ACCEPTANCE_COUNTER",
                                                       "REPORTED_LIMITATION")]
_counters = {r["module_name"]: r for r in _cr if r["module_id"] == "ACCEPTANCE_COUNTER"}
_r35 = {m for m, r in
        {x["module_id"]: x for x in rows("run35_parsimony_reconciliation.csv")}.items()
        if r["unique_analytical_contribution"] == "NO"}
_r36 = {m for m, r in
        {x["module_id"]: x for x in rows("run36_parsimony_reconciliation.csv")
         if x["row_type"] == "TARGET"}.items() if r["distinct_analytical_function"] == "NO"}
_expected_disc = sorted(_r35 ^ _r36)
check("run36c.fault08.no_discrepancy_silently_dropped",
      sorted(r["module_id"] for r in _disc_rows) == _expected_disc
      and _counters.get("DISCREPANCIES", {}).get("final_current_classification")
      == str(len(_expected_disc)),
      "every Run-35 versus Run-36 parsimony discrepancy derived here appears in the "
      "reconciliation; one has been silently dropped",
      f"artefact={sorted(r['module_id'] for r in _disc_rows)} derived={_expected_disc}")
_src = text("server/tools/build_run36_parsimony_reconciliation.py")
check("run36c.fault09.shared_lineage_is_not_identical_function",
      "COMMON_LINEAGE_ONLY" in _src
      and 'overlap[m] = (("COMMON_LINEAGE_ONLY", peers_lin) if peers_lin' in _src
      and "R5" in _src,
      "the reconciler treats common lineage as an overlap CLASS and never as identity of "
      "analytical function", "the COMMON_LINEAGE_ONLY arm is gone")
check("run36c.fault10.unknown_lineage_is_not_independent",
      "LINEAGE_UNRESOLVED" in _src and 'else "LINEAGE_UNRESOLVED"' in _src
      and "UNKNOWN LINEAGE IS NOT INDEPENDENT" in _src,
      "the reconciler records an absent lineage record as UNRESOLVED and never as independent",
      "the unresolved arm is gone")

# ---------------------------------------------------------------- 11-14 the study population
_projects = [r for r in csv.DictReader((PKG / "projects.csv").open(encoding="utf-8"))
             if str(r["study_project_candidate"]).strip().lower() == "true"]
_periods = list(csv.DictReader((PKG / "reporting_periods.csv").open(encoding="utf-8")))
_pids = {p["project_id"] for p in _projects}
_combos = [(r["project_id"], r["period_id"]) for r in _periods]
_per = {p: {r["period_id"] for r in _periods if r["project_id"] == p} for p in _pids}
_contract = json.loads((ROOT / "research" / "methodology"
                        / "controlled_study_design_contract.json").read_text(encoding="utf-8"))
_d = _contract["design"]
check("run36c.fault11.no_project_omitted",
      len(_pids) == _d["project_count"],
      "the enumerated study projects number exactly what the owner contract requires; one has "
      "been omitted", f"{len(_pids)} vs {_d['project_count']}: {sorted(_pids)}")
check("run36c.fault12.no_period_omitted",
      all(len(v) == _d["period_count_per_project"] for v in _per.values()),
      "every study project carries all of its governed periods; one has been omitted",
      json.dumps({k: len(v) for k, v in sorted(_per.items())}))
check("run36c.fault13.no_duplicate_project_period",
      len(set(_combos)) == len(_combos) == _d["project_period_count"],
      "the project-period combinations are unique and number exactly what the contract requires; "
      "a duplicate has been introduced",
      f"{len(_combos)} rows, {len(set(_combos))} unique, contract {_d['project_period_count']}")
_pop = rows("run36_controlled_study_population.csv")
_pc = {r["name_or_metric"]: r for r in _pop if r["row_type"] == "ACCEPTANCE_COUNTER"}
check("run36c.fault14.reported_counts_match_enumerated_stimuli",
      _pc.get("UNIQUE STUDY PROJECTS", {}).get("value") == str(len(_pids))
      and _pc.get("UNIQUE PROJECT-PERIOD COMBINATIONS", {}).get("value") == str(len(set(_combos)))
      and all(r["result"] != "FAIL" for r in _pop),
      "the recorded controlled-study counts are the ones enumeration actually produces; the "
      "record claims a design the stimuli do not carry",
      json.dumps({k: v.get("value") for k, v in _pc.items()}))

# ---------------------------------------------------------------- 15 the freeze gate
_qual = rows("run36_instrument_qualification.csv")
_open = [r for r in _qual if r["row_type"] == "INSTRUMENT_BLOCKING_DEFECT"]
_targets = rows("run36_100_target_scientific_reaudit.csv")
_target_blocking = [r for r in _targets if r["blocking_defect"] != "NO"]
_blocking = len(_open) + len(_target_blocking)
_manifest = ROOT / "research" / "freeze" / "INSTRUMENT_FREEZE_CANDIDATE_MANIFEST.json"
_companion = ROOT / "research" / "freeze" / "INSTRUMENT_FREEZE_CANDIDATE.md"
check("run36c.fault15.no_freeze_while_blocked",
      not (_blocking > 0 and (_manifest.is_file() or _companion.is_file())),
      "no freeze candidate exists while any blocking defect remains; the freeze gate has been "
      "opened with a defect standing",
      f"blocking={_blocking} manifest={_manifest.is_file()} companion={_companion.is_file()}")

print()
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
raise SystemExit(1 if FAILED else 0)
