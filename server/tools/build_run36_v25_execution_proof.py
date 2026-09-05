#!/usr/bin/env python3
"""
RUN 36 CLOSURE, SECTION 5. THE v24 -> v25 VERSION BOUNDARY, PROVED BY EXECUTING BOTH LINES.

NOT INFERRED FROM A SOURCE DIFF. The v24 line is extracted from its own git object and imported as
its own package; the v25 line is the working tree. Both are then run on IDENTICAL inputs through
each line's OWN dispatch table, and the rows are compared field by field.

WHAT MUST DIVERGE: A1.1 only. WHAT MUST NOT: A1.7, A1.8, A6.2, a Category-10 target and a
Portfolio Health target, which are named in the contract precisely so that a run cannot claim a
scoped change without demonstrating the scope.

Writes code_audit/run36_v24_v25_a1_1_execution_proof.csv.
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

V24_COMMIT = "822d80928367c0f422fac5f2564705279e718dd1"

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


def show(path, rev=V24_COMMIT):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


def old_line():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="run36c-v24-")) / "repo"
    pkg = tmp / "server" / "app" / "oldsim36c"
    pkg.mkdir(parents=True)
    (tmp / "p0-baseline").mkdir(parents=True)
    (tmp / "p0-baseline" / "module_renumbering_map.csv").write_text(
        show("p0-baseline/module_renumbering_map.csv"), encoding="utf-8")
    names = subprocess.run(["git", "ls-tree", "--name-only", V24_COMMIT,
                            "server/app/simulation/"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout.split()
    py = [n for n in names if n.endswith(".py")]
    if len(py) < 10:
        raise SystemExit("v24 extraction found no simulation sources; refusing to run half a "
                         "proof")
    for n in py:
        (pkg / pathlib.Path(n).name).write_text(show(n), encoding="utf-8")
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    sys.path.insert(0, str(pkg.parent))
    import oldsim36c.registry as old_reg          # noqa: E402
    import oldsim36c.models as old_models         # noqa: E402
    if old_models.SIMULATION_VERSION != "sim-2026.08-v24":
        raise SystemExit(f"extracted line is stamped {old_models.SIMULATION_VERSION}, not v24")
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
    if SIMULATION_VERSION != "sim-2026.08-v25":
        raise SystemExit(f"working tree is stamped {SIMULATION_VERSION}, not v25")

    rows = []
    fails = []

    def record(mid, expect, why):
        o, n = run(old_reg, mid), run(new_reg, mid)
        diverged = canon(o) != canon(n)
        ok = diverged if expect == "DIVERGE" else not diverged
        if not ok:
            fails.append(f"{mid}: expected {expect}, observed "
                         f"{'DIVERGED' if diverged else 'IDENTICAL'}")
        rows.append([mid, expect, "DIVERGED" if diverged else "IDENTICAL",
                     o.get("__state__", ""), n.get("__state__", ""),
                     canon(o)[:300], canon(n)[:300], "PASS" if ok else "FAIL", why])

    record("A1.1", "DIVERGE",
           "the owner's ruling: v24 reaches the retained scalar adaptation and reports a figure; "
           "v25 is operationally disabled because the canonical input contract is not governed")
    for mid, why in (
            ("A1.7", "TCPI votes and is outside this closure's scope"),
            ("A1.8", "VAC votes and is outside this closure's scope"),
            ("A6.2", "the one target with an exact published-identity pass"),
            ("B4.3", "a Category-10 target, named by the contract"),
            ("D1.1", "a Portfolio Health target, named by the contract")):
        record(mid, "IDENTICAL", why)

    # THE WHOLE POPULATION, so a scoped claim is demonstrated rather than asserted from six rows.
    idx = new_reg.registry_index()
    moved = []
    for mid in sorted(idx):
        if canon(run(old_reg, mid)) != canon(run(new_reg, mid)):
            moved.append(mid)
    rows.append(["ACCEPTANCE_COUNTER", "-", str(len(moved)), "-", "-",
                 "modules whose emitted row moved across the boundary", ", ".join(moved),
                 "PASS" if moved == ["A1.1"] else "FAIL",
                 "every one of the 101 registered modules executed on both lines; exactly one "
                 "must move"])
    if moved != ["A1.1"]:
        fails.append(f"population divergence is {moved}, expected exactly ['A1.1']")

    out = ROOT / "code_audit" / "run36_v24_v25_a1_1_execution_proof.csv"
    with artifact_out(out).open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["module_id", "expected", "observed", "v24_state", "v25_state",
                    "v24_row", "v25_row", "result", "why_this_module"])
        w.writerows(rows)
    print(f"wrote {out.name}: {len(rows)} rows")
    print(f"modules that moved across the boundary: {moved}")
    for f in fails:
        print("FAIL " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
