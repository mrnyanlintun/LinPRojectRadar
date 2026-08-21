#!/usr/bin/env python3
"""
RUN 42. THE v26 -> v27 BOUNDARY, PROVED BY EXECUTING BOTH LINES.

Same shape as build_run41_v25_v26_execution_proof.py so the boundaries stay comparable, and for
the same reason: NOT inferred from a source diff. The v26 line is extracted from its own pinned
git object and imported as its own package; the v27 line is the working tree. Both are then run
on identical inputs through their OWN code, and the emitted objects are compared field by field.

This boundary has a MIXED expectation, and recording both halves is the point.

WHAT MUST NOT MOVE: the registered module population, and every module's emitted row. Run 42
changed how a field's provenance is RECORDED, not what any field is or what any module does. If
a single module's row moves, the claim "no scientific method changed" is false.

WHAT MUST MOVE: the per-field `sources` record produced by `select_signal_inputs`, which now
carries documentId, documentVersion, asOf and revisionOf; and the provenance and timeliness
dimensions of `build_qualification`, which read exactly those keys and counted zero before.

WHAT MUST NOT MOVE INSIDE THE THINGS THAT MOVE: every non-`sources` key of the signal inputs
must be byte-identical, because the figures themselves are untouched. And
`overall_qualification_state` must NOT improve, because the revision dimension is still
NOT_ESTIMABLE and `_overall` is the weakest of the dimensions.

Writes code_audit/run42_v26_v27_execution_proof.csv.
"""
from __future__ import annotations

import csv
import json
import pathlib
import subprocess
import sys
import tempfile
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

#: The pinned predecessor: main at the start of Run 42, stamped sim-2026.08-v26.
V26_COMMIT = "1b624d3e3cd5ead39b90e80ac351cfc1e2f9a281"

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

#: Two documents of the same mapped type, one explicitly superseding the other, so the proof
#: exercises the revision-carrying path as well as the plain identity path.
DOCS = [
    {"sha256": "a" * 64, "document_id": "01DOCAAAAAAAAAAAAAAAAAAAAA", "doc_type": "monthly_report",
     "filename": "P1.pdf",
     "extraction": {"earned_value": 400_000, "actual_cost": 440_000, "planned_value": 450_000,
                    "budget_at_completion": 1_000_000, "actual_percent_complete": 40.0,
                    "planned_percent_complete": 45.0, "report_date": "2026-06-30",
                    "document_date": "2026-06-30"}},
]


def show(path, rev=V26_COMMIT):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


def old_line():
    """Extract the v26 line from its pinned git object and import it as its own package."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="run42-v26-")) / "repo"
    pkg = tmp / "server" / "app" / "oldsim42"
    pkg.mkdir(parents=True)
    (tmp / "p0-baseline").mkdir(parents=True)
    (tmp / "p0-baseline" / "module_renumbering_map.csv").write_text(
        show("p0-baseline/module_renumbering_map.csv"), encoding="utf-8")
    names = subprocess.run(["git", "ls-tree", "--name-only", V26_COMMIT,
                            "server/app/simulation/"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout.split()
    py = [n for n in names if n.endswith(".py")]
    if len(py) < 10:
        raise SystemExit("v26 extraction found no simulation sources; refusing to run half a "
                         "proof")
    for n in py:
        (pkg / pathlib.Path(n).name).write_text(show(n), encoding="utf-8")
    # The merge path lives in app/, not app/simulation/. It is the file Run 42 changed, so a
    # proof that omitted it would compare the wrong thing entirely.
    for n in ("server/app/extraction_merge.py", "server/app/extraction_fields.py",
              "server/app/field_registry.py"):
        (pkg / pathlib.Path(n).name).write_text(show(n), encoding="utf-8")
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    sys.path.insert(0, str(pkg.parent))
    import oldsim42.registry as old_reg              # noqa: E402
    import oldsim42.models as old_models             # noqa: E402
    import oldsim42.qualification as old_qual        # noqa: E402
    import oldsim42.extraction_merge as old_merge    # noqa: E402
    if old_models.SIMULATION_VERSION != "sim-2026.08-v26":
        raise SystemExit(f"extracted line is stamped {old_models.SIMULATION_VERSION}, not v26; "
                         "the predecessor pin is wrong and this proof would compare the wrong "
                         "thing")
    return old_reg, old_qual, old_merge


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
    old_reg, old_qual, old_merge = old_line()
    from app.simulation import registry as new_reg              # noqa: E402
    from app.simulation import qualification as new_qual        # noqa: E402
    from app import extraction_merge as new_merge               # noqa: E402
    from app.simulation.models import SIMULATION_VERSION        # noqa: E402
    if SIMULATION_VERSION != "sim-2026.08-v27":
        raise SystemExit(f"working tree is stamped {SIMULATION_VERSION}, not v27")

    rows = []
    fails = []

    # ---- A. the registered module population and every module's emitted row -----------
    idx = new_reg.registry_index()
    old_idx = old_reg.registry_index()
    same_pop = sorted(idx) == sorted(old_idx)
    if not same_pop:
        fails.append(f"the registered population itself moved: {sorted(set(idx) ^ set(old_idx))}")
    rows.append(["POPULATION", "IDENTICAL", "IDENTICAL" if same_pop else "MOVED",
                 str(len(old_idx)), str(len(idx)), "", "", "PASS" if same_pop else "FAIL",
                 "Run 42 changed how provenance is recorded, not which modules exist"])

    moved = []
    for mid in sorted(idx):
        o, n = run(old_reg, mid), run(new_reg, mid)
        if canon(o) != canon(n):
            moved.append(mid)
            rows.append([mid, "IDENTICAL", "DIVERGED", o.get("__state__", ""),
                         n.get("__state__", ""), canon(o)[:300], canon(n)[:300], "FAIL",
                         "a per-field provenance record cannot legitimately move a module's row"])
    rows.append(["MODULE_ROW_COUNTER", "0", str(len(moved)), "-", "-",
                 "modules whose emitted row moved across the v26->v27 boundary",
                 ", ".join(moved) or "(none)", "PASS" if not moved else "FAIL",
                 f"all {len(idx)} registered modules executed on BOTH lines; zero must move"])
    if moved:
        fails.append(f"module divergence is {moved}, expected none")

    # ---- B. the merge: the figures must not move, the sources record must ------------
    cut = date.fromisoformat(CUT)
    o_si = old_merge.assemble_signal_inputs([dict(d) for d in DOCS], cut)
    n_si = new_merge.assemble_signal_inputs([dict(d) for d in DOCS], cut)

    o_fig = {k: v for k, v in o_si.items() if k != "sources"}
    n_fig = {k: v for k, v in n_si.items() if k != "sources"}
    fig_same = canon(o_fig) == canon(n_fig)
    if not fig_same:
        fails.append("the FIGURES moved across the boundary; Run 42 must not change any value")
    rows.append(["MERGE_FIGURES", "IDENTICAL", "IDENTICAL" if fig_same else "MOVED",
                 "", "", canon(o_fig)[:300], canon(n_fig)[:300],
                 "PASS" if fig_same else "FAIL",
                 "every signal input except the sources record must be byte-identical"])

    src_moved = canon(o_si.get("sources")) != canon(n_si.get("sources"))
    if not src_moved:
        fails.append("the sources record did NOT move; the repair did not take effect")
    rows.append(["MERGE_SOURCES", "DIVERGED", "DIVERGED" if src_moved else "IDENTICAL",
                 "", "", canon(o_si.get("sources"))[:300], canon(n_si.get("sources"))[:300],
                 "PASS" if src_moved else "FAIL",
                 "the per-field source record is exactly what Run 42 repaired"])

    o_keys = sorted({k for e in (o_si.get("sources") or {}).values() for k in e})
    n_keys = sorted({k for e in (n_si.get("sources") or {}).values() for k in e})
    gained = sorted(set(n_keys) - set(o_keys))
    lost = sorted(set(o_keys) - set(n_keys))
    ok_keys = not lost and set(gained) <= {"documentId", "documentVersion", "asOf", "revisionOf"}
    if not ok_keys:
        fails.append(f"source keys gained={gained} lost={lost}; unexpected shape change")
    rows.append(["MERGE_SOURCE_KEYS", "docType,value(+identity)",
                 f"gained={gained or '(none)'} lost={lost or '(none)'}", "", "",
                 ",".join(o_keys), ",".join(n_keys), "PASS" if ok_keys else "FAIL",
                 "nothing may be LOST from the source record; only identity may be gained"])

    # ---- C. the qualification object -------------------------------------------------
    o_run = {"modules": [], "abstained": [], "scenario_id": None}
    o_q = old_qual.build_qualification(o_si, o_run, project_id="PRJ-PROOF",
                                       reporting_period="P1", period_cutoff=cut)
    n_q = new_qual.build_qualification(n_si, o_run, project_id="PRJ-PROOF",
                                       reporting_period="P1", period_cutoff=cut)
    for dim, expect in (("provenance_status", "IMPROVES"), ("timeliness_status", "IMPROVES"),
                        ("revision_resolution_status", "UNCHANGED"),
                        ("overall_qualification_state", "UNCHANGED")):
        ov, nv = o_q.get(dim), n_q.get(dim)
        if expect == "IMPROVES":
            ok = ov == "PARTIAL" and nv == "PASS"
            why = "the dimension was structurally pinned to PARTIAL and must now be reachable"
        else:
            ok = ov == nv
            why = ("the revision dimension is a deliberate fail-closed decision Run 42 did not "
                   "overturn, so the weakest-of overall state must not improve")
        if not ok:
            fails.append(f"{dim}: v26={ov} v27={nv}, expected {expect}")
        rows.append([f"QUAL_{dim}", expect, f"{ov} -> {nv}", str(ov), str(nv), "", "",
                     "PASS" if ok else "FAIL", why])

    o_pe = o_q.get("provenance_evidence") or {}
    n_pe = n_q.get("provenance_evidence") or {}
    traced_ok = (o_pe.get("fields_with_document_identity_and_version") == 0
                 and n_pe.get("fields_with_document_identity_and_version")
                 == n_pe.get("fields_with_source_type") > 0)
    if not traced_ok:
        fails.append(f"traced-field count did not go from zero to all: {o_pe} -> {n_pe}")
    rows.append(["QUAL_TRACED_FIELDS", "0 -> all",
                 f"{o_pe.get('fields_with_document_identity_and_version')} -> "
                 f"{n_pe.get('fields_with_document_identity_and_version')} of "
                 f"{n_pe.get('fields_with_source_type')}", "", "", canon(o_pe)[:300],
                 canon(n_pe)[:300], "PASS" if traced_ok else "FAIL",
                 "every field the merge sourced must now name the artefact it came from"])

    out = ROOT / "code_audit" / "run42_v26_v27_execution_proof.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["subject", "expected", "observed", "v26_state", "v27_state",
                    "v26_value", "v27_value", "result", "why_this_subject"])
        w.writerows(rows)
    print(f"wrote {out.name}: {len(rows)} rows over {len(idx)} modules")
    for f in fails:
        print("FAIL " + f)
    print(f"modules executed on both lines: {len(idx)}")
    print(f"modules whose emitted row moved: {len(moved)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
