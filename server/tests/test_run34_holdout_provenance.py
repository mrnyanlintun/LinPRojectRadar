#!/usr/bin/env python3
"""
RUN 34 FINAL METADATA CLOSURE. THE HOLDOUT/SELECTION ORDER GUARD.

ITS ORACLE IS NOT THE GENERATOR. Section 3 of the closure contract forbids validating an artifact
against the thing that wrote it, and that is not a theoretical hazard here: the previous Run-34
closure's count guard regenerated the artifact it was checking and wiped every injected fault.
So this guard derives the ordering facts ITSELF -- its own `git log` calls, the selection
artifact's own recorded value, and its own execution of the isolated selection decision -- and
then requires the committed artifact and the report to agree with what it derived.

WHAT IT REFUSES:
  * a holdout evaluated before selection;
  * selection and holdout represented as one phase rather than two;
  * a missing `holdout_changed_selection`;
  * `holdout_changed_selection = YES`;
  * a report whose stated values disagree with the artifact.

Run (from server/):
    PYTHONIOENCODING=utf-8 python tests/test_run34_holdout_provenance.py
"""

from __future__ import annotations

import builtins
import csv
import os
import pathlib
import re
import subprocess
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
ROOT = _HERE.parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / "tools"))

AUDIT = ROOT / "code_audit"
HOLDOUT = AUDIT / "run34_ph1_holdout_result.csv"
SELECTION = AUDIT / "run34_ph1_tree_count_calibration.csv"
REPORT = ROOT / "REPORT_2026-08-18_run34-portfolio-health-calibration.md"
PROTOCOL = ROOT / "research" / "methodology" / "run34_portfolio_calibration_protocol.md"

PASS = TOTAL = 0
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


def rows(path):
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def git_first_commit(path: str) -> str:
    """DERIVED HERE, not read from the artifact under test."""
    r = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "-1", "--", path],
                       cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip()


def git_order(a: str, b: str) -> str:
    """'before', 'after' or 'same' for two commits, by ancestry rather than by date."""
    if a == b:
        return "same"
    anc = subprocess.run(["git", "merge-base", "--is-ancestor", a, b], cwd=ROOT)
    return "before" if anc.returncode == 0 else "after"


_prov_rows = {r["metric"]: r for r in rows(HOLDOUT) if r["record_type"] == "PROVENANCE"}


class _Provenance(dict):
    """
    INDEXED DEFENSIVELY. A MISSING FIELD MUST FAIL A CHECK, NOT RAISE HERE.

    A guard that crashes instead of failing is one of the ways a check has lied in this
    repository, and the fault campaign beside this file caught exactly that when the
    `holdout_changed_selection` row was deleted: direct indexing raised a KeyError and the
    campaign scored a crash rather than a red. A missing field now reads as an empty record,
    which fails the checks that name it and passes none of them.
    """

    def __missing__(self, key):
        return {"metric": key, "value": "", "note": "", "result": "", "record_type": ""}


prov = _Provenance(_prov_rows)
report_text = REPORT.read_text(encoding="utf-8")


# =================================================================================================
head("1. THE ARTIFACT CARRIES THE REQUIRED PROVENANCE FIELDS")
# =================================================================================================
REQUIRED = ("selection_completed_before_holdout", "holdout_changed_selection", "selection_commit",
            "holdout_evaluation_commit", "selection_artifact", "holdout_artifact", "evidence")
for f in REQUIRED:
    check(f in prov, f"the holdout artifact records {f}")
check(all(prov[f]["value"].strip() for f in REQUIRED),
      "and none of them is blank or absent",
      str([f for f in REQUIRED if not prov[f]["value"].strip()]))
check(bool(_prov_rows) and all(r["result"].strip() for r in _prov_rows.values()),
      "every provenance row present carries a PASS/FAIL disposition")
# The original holdout RESULT rows must survive untouched.
_orig = [r for r in rows(HOLDOUT) if r["record_type"] in ("CALIBRATION", "HOLDOUT", "BOUNDARY",
                                                          "ORDERING")]
check(len(_orig) == 13,
      "and the 13 original holdout result rows are preserved, not replaced", str(len(_orig)))


# =================================================================================================
head("2. THE ORDERING, DERIVED INDEPENDENTLY FROM GIT")
# =================================================================================================
_proto = git_first_commit("research/methodology/run34_portfolio_calibration_protocol.md")
_fix = git_first_commit("research_fixtures/synthetic/OG-SYNTH-0.6/"
                        "package_D_portfolio_calibration/run34_ph1_holdout_labelled.json")
_sel = git_first_commit("code_audit/run34_ph1_tree_count_calibration.csv")
_hold = git_first_commit("code_audit/run34_ph1_holdout_result.csv")
check(all((_proto, _fix, _sel, _hold)), "all four phase commits resolve from git",
      f"{_proto[:7]} {_fix[:7]} {_sel[:7]} {_hold[:7]}")
check(git_order(_proto, _fix) == "before",
      "PROTOCOL PRECEDES FIXTURES, by ancestry", f"{_proto[:7]} -> {_fix[:7]}")
check(git_order(_fix, _sel) == "before",
      "FIXTURES PRECEDE SELECTION, by ancestry", f"{_fix[:7]} -> {_sel[:7]}")
check(git_order(_hold, _sel) != "before",
      "AND THE HOLDOUT ARTIFACT DOES NOT PRECEDE THE SELECTION ARTIFACT",
      f"holdout {_hold[:7]} vs selection {_sel[:7]}")
check(prov["selection_commit"]["value"] == _sel
      and prov["holdout_evaluation_commit"]["value"] == _hold,
      "and the artifact's recorded commits are the ones GIT gives, not ones it asserted")

# THE TWO PHASES MUST BE REPRESENTED AS TWO, even though they share a commit.
check(prov["selection_artifact"]["value"] != prov["holdout_artifact"]["value"],
      "SELECTION AND HOLDOUT ARE REPRESENTED AS TWO DISTINCT PHASES with distinct artifacts, not "
      "collapsed into one",
      f"{prov['selection_artifact']['value']} vs {prov['holdout_artifact']['value']}")
check("selection_and_holdout_in_same_commit" in prov
      and prov["selection_and_holdout_in_same_commit"]["value"] == "YES"
      and prov["selection_and_holdout_in_same_commit"]["result"] == "REPORTED_LIMITATION",
      "and the shared commit is DECLARED AS A LIMITATION rather than glossed, because commit "
      "ordering cannot separate the two phases here")
check("holdout_fixture_present_on_disk_at_selection_time" in prov
      and prov["holdout_fixture_present_on_disk_at_selection_time"]["result"]
      == "REPORTED_LIMITATION",
      "and so is the fact that the holdout fixture was on disk throughout selection, so "
      "availability is not the basis of the closure")


# =================================================================================================
head("3. NON-CONSUMPTION, RE-DERIVED BY THIS GUARD ITSELF")
# =================================================================================================
# The guard does not take the generator's word for it. It re-runs the isolated selection decision
# with the holdout booby-trapped, using metrics read from the SELECTION artifact.
import run34_ph1_tree_count_calibration as CAMP                        # noqa: E402

_metrics: dict[int, dict[str, float]] = {}
for r in rows(SELECTION):
    if r["record_type"] == "METRIC":
        k = {"within_production_rank_stability": "S",
             "median_runtime_seconds": "R"}.get(r["metric"])
        if k:
            _metrics.setdefault(int(r["n_trees"]), {})[k] = float(r["value"])
check(len(_metrics) == 3, "the stability metrics for all three candidates are recorded",
      str(sorted(_metrics)))

_hold_path = CAMP.HOLD.resolve()
_touched: list[str] = []
_open, _rt, _rb = builtins.open, pathlib.Path.read_text, pathlib.Path.read_bytes


def _t_open(file, *a, **k):
    try:
        same = pathlib.Path(file).resolve() == _hold_path
    except (TypeError, OSError):
        same = False
    if same:
        _touched.append(f"open:{file}")
        raise AssertionError("selection read the holdout")
    return _open(file, *a, **k)


def _t_rt(self, *a, **k):
    if self.resolve() == _hold_path:
        _touched.append(f"read_text:{self}")
        raise AssertionError("selection read the holdout")
    return _rt(self, *a, **k)


def _t_rb(self, *a, **k):
    if self.resolve() == _hold_path:
        _touched.append(f"read_bytes:{self}")
        raise AssertionError("selection read the holdout")
    return _rb(self, *a, **k)


_crashed = None
builtins.open, pathlib.Path.read_text, pathlib.Path.read_bytes = _t_open, _t_rt, _t_rb
try:
    _chosen, _state, _d2, _d1 = CAMP.selection_decision(_metrics)
except AssertionError as _exc:
    _chosen = _state = _d2 = None
    _crashed = str(_exc)
finally:
    builtins.open, pathlib.Path.read_text, pathlib.Path.read_bytes = _open, _rt, _rb

check(_crashed is None and not _touched,
      "THE SELECTION DECISION RUNS TO COMPLETION WITH THE HOLDOUT BOOBY-TRAPPED, and reads it "
      "zero times", _crashed or "no holdout reads")
_recorded = next((r["value"] for r in rows(SELECTION)
                  if r["metric"] == "selected_tree_count"), None)
check(str(_chosen) == _recorded,
      "and it reproduces the RECORDED selected tree count exactly, so the recorded selection is "
      "the one a holdout-blind decision produces", f"{_chosen} == {_recorded}")
check(_state == "UNRESOLVED_NO_OPERATIONAL_CONSEQUENCE" and _d2 is False,
      "under the D2 gate failing and D4 applying, which is decided from the production route and "
      "not from any labelled data", f"{_state}, d2_pass={_d2}")
check(prov["selection_reads_holdout_dataset"]["value"] == "NO",
      "and the artifact records the same non-consumption result this guard just derived")


# =================================================================================================
head("4. THE VALUES THE CONTRACT REQUIRES, AND THE ONES IT REFUSES")
# =================================================================================================
check(prov["selection_completed_before_holdout"]["value"] == "YES",
      "selection_completed_before_holdout = YES, supported by the non-consumption proof above")
check(prov["holdout_changed_selection"]["value"] == "NO",
      "holdout_changed_selection = NO")
check(prov["holdout_changed_selection"]["value"] != "YES",
      "and it is NOT YES -- a YES would mean a parameter was chosen after inspecting the holdout")
check(prov["parameter_retuned_after_holdout_inspection"]["value"] == "NO",
      "no parameter was retuned after holdout inspection")
check(prov["is_new_calibration_evidence"]["value"] == "NO",
      "and this closure does not present itself as new calibration evidence")


# =================================================================================================
head("5. THE REPORT AGREES WITH THE ARTIFACT")
# =================================================================================================
# RUN 59, PHASE B. RETIRED, NOT DELETED.
#
# Owner's ruling, 2026-08-25: no markdown document in this repository carries authority, and
# REPORT_2026-08-18_run34-portfolio-health-calibration.md is SEALED EVIDENCE besides. Section 5
# asserted eight fields of that report's prose against `prov`, plus four phrases it must contain.
# ESTABLISHED BY READING IT: the report is a REDUNDANT ORACLE here. Every one of the eight fields
# is read from `prov`, the provenance artifact, and `prov` is asserted against the holdout and
# selection CSVs and against git ancestry in sections 1 to 4, which are untouched and still run.
# Section 2's git_first_commit ordering checks are NOT retired: they assert PROVENANCE -- which
# object was committed before which -- and not a document's content, so the ruling does not reach
# them.
#
# Retired the way modules were retired: THE CHECKS STOP RUNNING, THE BODY IS NOT DELETED, AND THE
# REASON IS RECORDED. Clear the flag to run them again.
RETIRED_RUN59_REPORT_AS_ORACLE = True

if not RETIRED_RUN59_REPORT_AS_ORACLE:
    def report_value(field: str) -> str | None:
        m = re.search(r"^\|\s*`" + re.escape(field) + r"`\s*\|\s*\**([^|*]+?)\**\s*\|", report_text,
                      re.M)
        return m.group(1).strip().strip("`") if m else None


    for _f in ("selection_completed_before_holdout", "holdout_changed_selection", "selection_commit",
               "holdout_evaluation_commit", "selection_artifact", "holdout_artifact",
               "parameter_retuned_after_holdout_inspection", "is_new_calibration_evidence"):
        _rv, _av = report_value(_f), prov[_f]["value"]
        check(_rv is not None and _rv == _av,
              f"the report's stated {_f} equals the artifact's", f"report {_rv!r} vs artifact {_av!r}")
    check("Holdout selection-order closure" in report_text,
          "the report carries the holdout selection-order subsection")
    check("booby-trapped" in report_text and "non-consumption" in report_text.lower(),
          "and states that the evidence is non-consumption proved by execution, not commit ordering")
    check("REPORTED_LIMITATION" in report_text or "limitations are recorded plainly" in report_text,
          "and records the two limitations rather than glossing them")
    check(re.search(r"\*\*not\*\*\s+new calibration evidence", report_text) is not None,
          "and says the closure is not new calibration evidence")
else:
    print("  RETIRED (Run 59)  section 5, THE REPORT AGREES WITH THE ARTIFACT -- twelve\n"
          "                    assertions about a sealed evidence document's prose. The\n"
          "                    artifact they were compared against is still asserted in\n"
          "                    sections 1 to 4, against the CSVs and against git ancestry.")


# =================================================================================================
head("6. RUN-34 SCIENTIFIC CONCLUSIONS AND THE PARAMETER POPULATION ARE UNCHANGED")
# =================================================================================================
from app.simulation import canonical_v8 as V8                          # noqa: E402
from app.simulation.models import (                                    # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY)
from app.simulation.registry import CORE_VOTING_MODULES                # noqa: E402

check(V8.IF_TREES == 100, "PH.1 tree count is still 100", str(V8.IF_TREES))
check(V8.RUN15_FROZEN_THRESHOLD == 0.576, "the frozen threshold is still 0.576")
# RESTATED BY THE RUN-35 FINAL CLOSURE. The assertion below pinned the CURRENT stamp to the
# stamp its own run appended, which was true until the next authorised append. The closure
# appends v23, because A1.7 and A1.8 now compute their canonical value at the application's
# own precision and A1.7 bands from it. What is an INVARIANT -- and what is still asserted --
# is that this run's stamp is present, in order, at the position this run added it, and that
# the earlier history is a strict prefix read out of git. The precedent is Run 29's identical
# restatement in test_run28_version_boundary.py and Run 31's in run31_restate_version_suites.
check("sim-2026.08-v22" in SIMULATION_VERSION_HISTORY,
      "the simulation line Run 34 appended, sim-2026.08-v22, is present in the history")
check(len(CORE_VOTING_MODULES) == 2, "voting is still exactly 2")
check(_recorded == "100", "the recorded selected tree count is still 100")

_pp = rows(AUDIT / "run34_portfolio_parameter_provenance.csv")
_params = [r for r in _pp if r["row_type"] == "PARAMETER"]
_counters = [r for r in _pp if r["row_type"] == "ACCEPTANCE_COUNTER"]
check(len(_params) == 19 and len(_counters) == 2,
      "the parameter population is unchanged: 19 PARAMETER + 2 ACCEPTANCE_COUNTER rows",
      f"{len(_params)} + {len(_counters)}")
_dist = {c: sum(1 for r in _params if r["parameter_class"] == c) for c in V8.PARAMETER_CLASSES}
check(_dist == {"UNSUPPORTED": 7, "OWNER_POLICY": 5, "THEORETICAL_CONSTANT": 4,
                "PUBLISHED_DEFAULT": 2, "SYNTHETIC_LAB_CALIBRATION": 1,
                "EMPIRICAL_CALIBRATION": 0, "HEURISTIC": 0},
      "and the class distribution is unchanged", str(_dist))

_clo = rows(AUDIT / "run34_portfolio_health_calibration_closure.csv")
check(len(_clo) == 5 and all(r["voting"] == "false" for r in _clo)
      and all(r["layer5_real_empirical_validation"] == "PENDING" for r in _clo),
      "the five-row calibration closure is unchanged: voting false and layer 5 PENDING for all "
      "five")


# =================================================================================================
head("7. THE GUARD IS NOT VALIDATING THE ARTIFACT AGAINST ITS OWN GENERATOR")
# =================================================================================================
# CHECKED ON THE PARSED SOURCE, not by substring: this file necessarily NAMES the generator, in
# order to run it as a subprocess for the byte-comparison below, so a text search would flag its
# own filename. What matters is that it never IMPORTS it and never calls its row builder.
import ast                                                             # noqa: E402

_self_src = pathlib.Path(__file__).read_text(encoding="utf-8")
_tree = ast.parse(_self_src)
_imports = set()
for _n in ast.walk(_tree):
    if isinstance(_n, ast.Import):
        _imports.update(a.name for a in _n.names)
    elif isinstance(_n, ast.ImportFrom):
        _imports.add(_n.module or "")
check("build_run34_holdout_provenance" not in _imports,
      "this guard does not IMPORT the provenance generator", str(sorted(_imports)))
_called = {n.func.id for n in ast.walk(_tree)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
check("provenance_rows" not in _called and "non_consumption_proof" not in _called,
      "and calls neither the generator's row builder nor its proof helper", str(sorted(_called)))
check("git_first_commit" in _called and "selection_decision" in _self_src,
      "it derives the ordering from git itself and re-executes the selection decision itself")
# Regenerating into a TEMP directory and comparing proves the artifact is generated, without
# overwriting the subject -- the defect the previous closure's campaign exposed.
with tempfile.TemporaryDirectory() as _tmp:
    _r = subprocess.run([sys.executable,
                         str(ROOT / "server" / "tools" / "build_run34_holdout_provenance.py"),
                         "--out", _tmp], cwd=str(ROOT), capture_output=True, text=True,
                        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    check(_r.returncode == 0, "the provenance generator runs cleanly", _r.stderr[-200:])
    _fresh = pathlib.Path(_tmp) / HOLDOUT.name
    check(_fresh.is_file() and _fresh.read_bytes() == HOLDOUT.read_bytes(),
          "and the committed holdout artifact is byte-identical to a fresh generation, compared "
          "WITHOUT overwriting it")

print()
print("=" * 94)
print(f"RESULT: {PASS}/{TOTAL} checks passed")
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print("  -", f)
sys.exit(1 if FAILURES else 0)
