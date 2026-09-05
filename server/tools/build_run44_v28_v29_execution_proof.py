#!/usr/bin/env python3
"""
RUN 44. THE v28 -> v29 BOUNDARY, PROVED BY EXECUTING BOTH LINES.

Same shape as build_run41_v25_v26_execution_proof.py and build_run42_v26_v27_execution_proof.py,
and for the same reason: NOT inferred from a source diff. The v28 line is extracted from its own
pinned git object and imported as its own package; the v29 line is the working tree. Both are
then run on identical inputs through their OWN code, and the emitted objects are compared field
by field.

This boundary has an UNMIXED expectation, which is what makes it worth recording. Run 44 changed
four render surfaces and one docstring. NOTHING on the analytical side may move:

  * the registered population, all 101 identifiers;
  * every module's emitted row, on both a full and a starved evidence package -- the starved one
    matters because the run touched a null-handling defect, and a fix that quietly changed what
    an ABSTAINING module emits would look identical on the full package alone;
  * the modules in service, the modules available, and the voting set;
  * the merged signal inputs and their per-field source record;
  * the fused category status for the voting pair.

If any of those moves, the claim "no server computation changed" is false and the run must stop.

Writes code_audit/run44_v28_v29_execution_proof.csv.
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
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

#: The pinned predecessor: main at the start of Run 44, stamped sim-2026.08-v28.
V28_COMMIT = "604291a"

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

#: THE SECOND PACKAGE, AND THE REASON IT EXISTS. Run 44's document-risk fix turns on the
#: difference between a key that is absent and a key that is PRESENT AND NULL. Every module is
#: therefore also executed against a package carrying that exact shape, so a change in what an
#: abstaining module says cannot hide behind a package rich enough for everything to compute.
SI_STARVED = {"bac": None, "ev": None, "ac": None, "pv": None,
              "cpi": None, "spi": None, "docRiskScore": None}

CUT = "2026-06-30"

DOCS = [
    {"sha256": "a" * 64, "document_id": "01DOCAAAAAAAAAAAAAAAAAAAAA", "doc_type": "monthly_report",
     "filename": "P1.pdf",
     "extraction": {"earned_value": 400_000, "actual_cost": 440_000, "planned_value": 450_000,
                    "budget_at_completion": 1_000_000, "actual_percent_complete": 40.0,
                    "planned_percent_complete": 45.0, "report_date": "2026-06-30",
                    "document_date": "2026-06-30"}},
]


def show(path, rev=V28_COMMIT):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


def old_line():
    """Extract the v28 line from its pinned git object and import it as its own package."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="run44-v28-")) / "repo"
    pkg = tmp / "server" / "app" / "oldsim44"
    pkg.mkdir(parents=True)
    (tmp / "p0-baseline").mkdir(parents=True)
    (tmp / "p0-baseline" / "module_renumbering_map.csv").write_text(
        show("p0-baseline/module_renumbering_map.csv"), encoding="utf-8")
    names = subprocess.run(["git", "ls-tree", "--name-only", V28_COMMIT,
                            "server/app/simulation/"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout.split()
    py = [n for n in names if n.endswith(".py")]
    if len(py) < 10:
        raise SystemExit("v28 extraction found no simulation sources; refusing to run half a "
                         "proof")
    for n in py:
        (pkg / pathlib.Path(n).name).write_text(show(n), encoding="utf-8")
    for n in ("server/app/extraction_merge.py", "server/app/extraction_fields.py",
              "server/app/field_registry.py"):
        (pkg / pathlib.Path(n).name).write_text(show(n), encoding="utf-8")
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    sys.path.insert(0, str(pkg.parent))
    import oldsim44.registry as old_reg              # noqa: E402
    import oldsim44.models as old_models             # noqa: E402
    import oldsim44.extraction_merge as old_merge    # noqa: E402
    import oldsim44.fusion as old_fusion             # noqa: E402
    import oldsim44.qualification_gate as old_gate   # noqa: E402
    import oldsim44.lineage as old_lineage           # noqa: E402
    if old_models.SIMULATION_VERSION != "sim-2026.08-v28":
        raise SystemExit(f"extracted line is stamped {old_models.SIMULATION_VERSION}, not v28; "
                         "the predecessor pin is wrong and this proof would compare the wrong "
                         "thing")
    return old_reg, old_merge, old_fusion, old_gate, old_lineage


def run(reg, mid, si):
    try:
        row = reg.run_module(mid, dict(si), (lambda: 0.5), CUT)
    except Exception as exc:                                     # noqa: BLE001
        return {"__state__": f"{type(exc).__name__}", "__why__": str(exc)[:120]}
    row["__state__"] = "ABSTAINS" if row.get("insufficient_data") else "COMPUTES"
    return row


def canon(row):
    return json.dumps({k: v for k, v in sorted(row.items()) if k != "__why__"},
                      sort_keys=True, default=str)


#: THE ONE PERMITTED DIFFERENCE, AND WHY IT IS NAMED RATHER THAN IGNORED. Every row a module
#: emits carries the stamp of the line that produced it -- that is the whole point of the stamp,
#: and a v29 row that still said v28 would be the defect, not the proof. So the stamp is
#: normalised out of the row comparison and asserted SEPARATELY below: it must move on every
#: row it appears on, and nothing else may move on any row. Normalising it away without also
#: requiring it to have moved would let a run that forgot to mint a stamp pass this proof.
def canon_unstamped(row):
    return canon(row).replace('"sim-2026.08-v28"', '"__STAMP__"') \
                     .replace('"sim-2026.08-v29"', '"__STAMP__"')


def fuse_pair(fusion, gate, lineage, bands):
    pre = gate.preflight(SI, (), None)
    voters = ("A1.7", "A1.8")
    sigs = [gate.qualify(voters[i], b, f"metric {b}", pre, lineage=lineage.lineage_for(voters[i]))
            for i, b in enumerate(bands)]
    return fusion.fuse_signals(gate.fuse_qualified(sigs))


def main() -> int:
    old_reg, old_merge, old_fusion, old_gate, old_lineage = old_line()
    from app.simulation import registry as new_reg                  # noqa: E402
    from app.simulation import fusion as new_fusion                 # noqa: E402
    from app.simulation import qualification_gate as new_gate       # noqa: E402
    from app.simulation import lineage as new_lineage               # noqa: E402
    from app import extraction_merge as new_merge                   # noqa: E402
    from app.simulation.models import SIMULATION_VERSION            # noqa: E402
    if SIMULATION_VERSION != "sim-2026.08-v29":
        raise SystemExit(f"working tree is stamped {SIMULATION_VERSION}, not v29")

    rows = []
    fails = []
    stamp_counts: list[tuple[str, int, int]] = []

    # ---- A. the registered population -------------------------------------------------
    idx, old_idx = new_reg.registry_index(), old_reg.registry_index()
    same_pop = sorted(idx) == sorted(old_idx)
    if not same_pop:
        fails.append(f"the registered population moved: {sorted(set(idx) ^ set(old_idx))}")
    rows.append(["POPULATION", "IDENTICAL", "IDENTICAL" if same_pop else "MOVED",
                 str(len(old_idx)), str(len(idx)), "", "", "PASS" if same_pop else "FAIL",
                 "Run 44 changed four render surfaces; the registry is not one of them"])

    for name, fn in (("SERVICE", lambda r: sorted(r.service_index())),
                     ("AVAILABLE", lambda r: sorted(r.available_modules())),
                     ("VOTING", lambda r: sorted(r.CORE_VOTING_MODULES)),
                     ("RETIRED", lambda r: sorted(r.retired_modules()))):
        o, n = fn(old_reg), fn(new_reg)
        ok = o == n
        if not ok:
            fails.append(f"{name} moved: {sorted(set(o) ^ set(n))}")
        rows.append([f"ROSTER_{name}", "IDENTICAL", "IDENTICAL" if ok else "MOVED",
                     str(len(o)), str(len(n)), ",".join(o)[:300], ",".join(n)[:300],
                     "PASS" if ok else "FAIL",
                     "every roster is derived from the registry CSV, which this run did not "
                     "touch"])

    # ---- B. every module's emitted row, on both packages -------------------------------
    for pkg_name, pkg in (("FULL", SI), ("STARVED_PRESENT_AND_NULL", SI_STARVED)):
        moved = []
        stamped_old = stamped_new = 0
        for mid in sorted(idx):
            o, n = run(old_reg, mid, pkg), run(new_reg, mid, pkg)
            if "sim-2026.08-v28" in canon(o):
                stamped_old += 1
            if "sim-2026.08-v29" in canon(n):
                stamped_new += 1
            if canon_unstamped(o) != canon_unstamped(n):
                moved.append(mid)
                rows.append([f"{mid}@{pkg_name}", "IDENTICAL", "DIVERGED",
                             o.get("__state__", ""), n.get("__state__", ""),
                             canon(o)[:300], canon(n)[:300], "FAIL",
                             "a render fix cannot legitimately move a module's emitted row"])
        rows.append([f"MODULE_ROW_COUNTER@{pkg_name}", "0", str(len(moved)), "-", "-",
                     "modules whose emitted row moved across the v28->v29 boundary",
                     ", ".join(moved) or "(none)", "PASS" if not moved else "FAIL",
                     f"all {len(idx)} registered modules executed on BOTH lines against the "
                     f"{pkg_name} package; zero must move"])
        if moved:
            fails.append(f"module divergence on {pkg_name} is {moved}, expected none")
        # Not every module's row carries the stamp: on the FULL package none does, because the
        # stamp is written by the qualification boundary, which those rows do not reach. That is
        # a fact about the rows, not a failure, so the count only has to MATCH here; that at
        # least one row somewhere carried it is asserted once, globally, below.
        stamp_counts.append((pkg_name, stamped_old, stamped_new))
        stamp_ok = stamped_old == stamped_new
        if not stamp_ok:
            fails.append(f"the stamp on {pkg_name} rows did not advance cleanly: "
                         f"{stamped_old} rows said v28, {stamped_new} say v29")
        rows.append([f"STAMP_ADVANCED@{pkg_name}", "every stamped row moves v28 -> v29",
                     f"{stamped_old} -> {stamped_new}", str(stamped_old), str(stamped_new),
                     "", "", "PASS" if stamp_ok else "FAIL",
                     "the stamp is normalised out of the row comparison above, so it is "
                     "asserted here instead: a run that forgot to mint one would otherwise "
                     "pass this proof by having nothing to normalise"])

    total_stamped = sum(n for _, _, n in stamp_counts)
    if total_stamped <= 0:
        fails.append("no emitted row anywhere carried the v29 stamp, so the stamp normalisation "
                     "above had nothing to normalise and this proof would be vacuous")
    rows.append(["STAMP_PRESENT_SOMEWHERE", ">0 rows carry the new stamp", str(total_stamped),
                 str(sum(o for _, o, _ in stamp_counts)), str(total_stamped),
                 str(stamp_counts), "", "PASS" if total_stamped > 0 else "FAIL",
                 "the guard on the normalisation: a run that minted no stamp must not pass"])

    # ---- C. the merge: nothing at all may move ----------------------------------------
    cut = date.fromisoformat(CUT)
    o_si = old_merge.assemble_signal_inputs([dict(d) for d in DOCS], cut)
    n_si = new_merge.assemble_signal_inputs([dict(d) for d in DOCS], cut)
    same = canon(o_si) == canon(n_si)
    if not same:
        fails.append("the merged signal inputs moved; Run 44 touches no merge path")
    rows.append(["MERGE_SIGNAL_INPUTS", "IDENTICAL", "IDENTICAL" if same else "MOVED", "", "",
                 canon(o_si)[:300], canon(n_si)[:300], "PASS" if same else "FAIL",
                 "the figures AND their per-field source record, which the render reads"])

    # the present-and-null shape the document-risk fix turns on
    null_ok = ("docRiskScore" in n_si and n_si["docRiskScore"] is None
               and ("docRiskScore" in o_si and o_si["docRiskScore"] is None))
    if not null_ok:
        fails.append("docRiskScore is no longer present-and-null on an absent observation")
    rows.append(["MERGE_DOCRISK_SHAPE", "PRESENT AND NULL", "PRESENT AND NULL" if null_ok
                 else "CHANGED", str(o_si.get("docRiskScore")), str(n_si.get("docRiskScore")),
                 "", "", "PASS" if null_ok else "FAIL",
                 "storage was already correct and stays correct; only the render was repaired"])

    # ---- D. the fused category status --------------------------------------------------
    for bands in (("Green", "Green"), ("Green", "Amber"), ("Amber", "Amber"), ("Red", "Green")):
        o = fuse_pair(old_fusion, old_gate, old_lineage, bands)
        n = fuse_pair(new_fusion, new_gate, new_lineage, bands)
        ok = canon(o or {}) == canon(n or {})
        if not ok:
            fails.append(f"the fusion moved for {bands}")
        rows.append([f"FUSION_{'_'.join(bands)}", "IDENTICAL", "IDENTICAL" if ok else "MOVED",
                     str((o or {}).get("status")), str((n or {}).get("status")),
                     canon(o or {})[:300], canon(n or {})[:300], "PASS" if ok else "FAIL",
                     "the category status a participant reads is the fusion's output"])

    out = ROOT / "code_audit" / "run44_v28_v29_execution_proof.csv"
    with artifact_out(out).open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["subject", "expected", "observed", "v28_state", "v29_state",
                    "v28_value", "v29_value", "result", "why_this_subject"])
        w.writerows(rows)
    print(f"wrote {out.name}: {len(rows)} rows over {len(idx)} modules x 2 packages")
    for f in fails:
        print("FAIL " + f)
    print(f"modules executed on both lines: {len(idx)} x 2 packages = {len(idx) * 2}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
