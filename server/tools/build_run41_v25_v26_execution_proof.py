#!/usr/bin/env python3
"""
RUN 41 SECTION 12. THE v25 -> v26 BOUNDARY, PROVED BY EXECUTING BOTH LINES.

Follows the method established for the v24 -> v25 boundary in
build_run36_v25_execution_proof.py, and is deliberately the same shape so the two boundaries are
comparable. NOT inferred from a source diff: the v25 line is extracted from its own pinned git
object and imported as its own package; the v26 line is the working tree. Both are then run on
identical inputs through each line's OWN dispatch table, and the emitted rows are compared field
by field.

WHAT MUST DIVERGE: nothing at all.

This is the opposite expectation to Run 36's, and it is the whole point. S1 changes an HTTP
response header policy; S2 adds a database trigger. Neither touches a module, a formula, a
qualification rule, a vote or a boundary. If ANY module's emitted row moves across this boundary,
the claim "analytical output changes attributable to S1 = 0 and to S2 = 0" is false and this run
must report that rather than absorb it.

The whole registered population is executed on both lines, not a sample, because a scoped claim
about science is only worth what its coverage is.

Writes code_audit/run41_v25_v26_execution_proof.csv.
"""
from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

#: The pinned predecessor: main at the start of Run 41, stamped sim-2026.08-v25.
V25_COMMIT = "4bd14684abadd3ab8a94d68964b686993a5d6718"

SI = {
    "bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
    "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
    "actualPctComplete": 40.0, "plannedPctComplete": 45.0,
    "qualityAuditScore": 92, "totalFindings": 18, "criticalFindings": 1,
    "oshaRecordableIncidents": 3, "totalManhours": 200_000,
    "environmentalComplianceRate": 0.925, "environmentalViolations": 3,
    "evidenceQualification": {"qualification_state": "QUALIFIED",
                              "timeliness_status": "TIMELY",
                              "verification_status": "verified",
                              "source_authority": "system_of_record"},
}
CUT = "2026-06-30"


def show(path, rev=V25_COMMIT):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


def old_line():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="run41-v25-")) / "repo"
    pkg = tmp / "server" / "app" / "oldsim41"
    pkg.mkdir(parents=True)
    (tmp / "p0-baseline").mkdir(parents=True)
    (tmp / "p0-baseline" / "module_renumbering_map.csv").write_text(
        show("p0-baseline/module_renumbering_map.csv"), encoding="utf-8")
    names = subprocess.run(["git", "ls-tree", "--name-only", V25_COMMIT,
                            "server/app/simulation/"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout.split()
    py = [n for n in names if n.endswith(".py")]
    if len(py) < 10:
        raise SystemExit("v25 extraction found no simulation sources; refusing to run half a "
                         "proof")
    for n in py:
        (pkg / pathlib.Path(n).name).write_text(show(n), encoding="utf-8")
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    sys.path.insert(0, str(pkg.parent))
    import oldsim41.registry as old_reg          # noqa: E402
    import oldsim41.models as old_models         # noqa: E402
    if old_models.SIMULATION_VERSION != "sim-2026.08-v25":
        raise SystemExit(f"extracted line is stamped {old_models.SIMULATION_VERSION}, not v25; "
                         "the predecessor pin is wrong and this proof would compare the wrong "
                         "thing")
    return old_reg


def run(reg, mid):
    try:
        row = reg.run_module(mid, dict(SI), (lambda: 0.5), CUT)
    except Exception as exc:                                     # noqa: BLE001
        return {"__state__": f"{type(exc).__name__}", "__why__": str(exc)[:120]}
    row["__state__"] = "ABSTAINS" if row.get("insufficient_data") else "COMPUTES"
    return row


def canon(row):
    return json.dumps({k: v for k, v in sorted(row.items()) if k != "__why__"},
                      sort_keys=True, default=str)


def main() -> int:
    old_reg = old_line()
    from app.simulation import registry as new_reg          # noqa: E402
    from app.simulation.models import SIMULATION_VERSION    # noqa: E402
    if SIMULATION_VERSION != "sim-2026.08-v26":
        raise SystemExit(f"working tree is stamped {SIMULATION_VERSION}, not v26")

    rows = []
    fails = []

    idx = new_reg.registry_index()
    old_idx = old_reg.registry_index()
    if sorted(idx) != sorted(old_idx):
        fails.append(f"the registered population itself moved: "
                     f"{sorted(set(idx) ^ set(old_idx))}")
    rows.append(["POPULATION", "IDENTICAL",
                 "IDENTICAL" if sorted(idx) == sorted(old_idx) else "MOVED",
                 str(len(old_idx)), str(len(idx)), "", "",
                 "PASS" if sorted(idx) == sorted(old_idx) else "FAIL",
                 "the set of registered modules must not move across an S1/S2 boundary"])

    moved = []
    for mid in sorted(idx):
        o, n = run(old_reg, mid), run(new_reg, mid)
        diverged = canon(o) != canon(n)
        if diverged:
            moved.append(mid)
            rows.append([mid, "IDENTICAL", "DIVERGED", o.get("__state__", ""),
                         n.get("__state__", ""), canon(o)[:300], canon(n)[:300], "FAIL",
                         "neither S1 (an HTTP response header policy) nor S2 (a database "
                         "trigger) can legitimately move a module's emitted row"])

    rows.append(["ACCEPTANCE_COUNTER", "0", str(len(moved)), "-", "-",
                 "modules whose emitted row moved across the v25->v26 boundary",
                 ", ".join(moved) or "(none)",
                 "PASS" if not moved else "FAIL",
                 f"all {len(idx)} registered modules executed on BOTH lines; zero must move"])
    if moved:
        fails.append(f"population divergence is {moved}, expected none")

    out = ROOT / "code_audit" / "run41_v25_v26_execution_proof.csv"
    with artifact_out(out).open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["module_id", "expected", "observed", "v25_state", "v26_state",
                    "v25_row", "v26_row", "result", "why_this_module"])
        w.writerows(rows)
    print(f"wrote {out.name}: {len(rows)} rows over {len(idx)} modules")
    for f in fails:
        print("FAIL " + f)
    print(f"modules executed on both lines: {len(idx)}")
    print(f"modules whose emitted row moved: {len(moved)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
