#!/usr/bin/env python3
"""
RUN 22 SECTION 19. THE FINAL FREEZE MANIFEST.

THE SELF-REFERENCE PROBLEM, AND THE HONEST WAY ROUND IT. A manifest cannot contain its own
SHA-256: adding the digest changes the bytes whose digest it is. Nor can the Run-22 report contain
the hash of the commit that introduces it. The owner's instruction is to use a two-stage process
and document it precisely rather than invent an impossible circular guarantee, so:

    STAGE 1  This tool writes research/freeze/FINAL_RESEARCH_INSTRUMENT_FREEZE_<date>.json with
             every hash it can compute -- the production and authority manifests, the supervisory
             specification, the scientific results, the registry, the Run-20/21/22 reports -- and
             with `manifest_sha256` and `final_commit` explicitly null. That file is committed.
    STAGE 2  The digest of the STAGE-1 file is computed and recorded in a separate small file,
             research/freeze/FINAL_RESEARCH_INSTRUMENT_FREEZE_<date>.sha256, together with the
             commit that carried stage 1. That is committed as the finalisation commit.

So the freeze manifest's own digest is a fact about a file that already exists and is immutable,
rather than a value the file claims about itself. Verification is `sha256sum -c` on the companion
file: no circularity, and nothing is asserted that cannot be checked.

WHAT IS NOT HASHED HERE AND WHY. The repository TREE hash is git's own `rev-parse HEAD^{tree}`,
recorded rather than recomputed, because git already provides a canonical content hash of the
whole tree and reimplementing it would be a second, worse implementation of the same thing.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "server"))

import production_tree as pt  # noqa: E402

RELEASE_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN22"


def sha(rel: str) -> str | None:
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def main() -> None:
    from app.simulation import registry as R  # noqa: E402

    reaudit = list(csv.DictReader(
        (ROOT / "code_audit" / "run20_cycle12_100_reaudit.csv").open(encoding="utf-8")))
    dispositions: dict[str, int] = {}
    for r in reaudit:
        dispositions[r["scientific_disposition"]] = \
            dispositions.get(r["scientific_disposition"], 0) + 1

    reg = R.load_registry()
    project_modules = [m for m in reg if m["group"] in ("A", "B", "C")]
    portfolio_modules = [m for m in reg if m["group"] == "D"]

    prod = pt.walk_production()
    auth = pt.walk_production(None, pt.AUTHORITY_ROOTS)

    doc = {
        "release_identifier": RELEASE_ID,
        "release_date": "2026-08-14",
        "generated_by": "server/tools/build_run22_freeze.py",
        "self_reference_note":
            "manifest_sha256 and final_commit are null BY CONSTRUCTION. A file cannot contain "
            "its own digest, and a manifest cannot contain the hash of the commit that "
            "introduces it. Both are recorded in the companion .sha256 file written by the "
            "finalisation commit. See the module docstring for the two-stage process.",
        "manifest_sha256": None,
        "final_commit": None,
        "stage1_parent_commit": git("rev-parse", "HEAD"),
        "stage1_repository_tree_hash": git("rev-parse", "HEAD^{tree}"),
        "run22_starting_commit": "ba5bfaf0e1c7d517abd0563119c9aa36c072f251",
        "run21_final_report_commit": "dc02fe8",
        "run21_hash_stamp_commit": "ba5bfaf",

        "production_surface": {
            "discovery": "walked from the deployed roots in server/tools/production_tree.py; "
                         "NOT enumerated from a fixed list",
            "roots": [{"path": r, "recursive": rec, "why": why}
                      for r, rec, why in pt.PRODUCTION_ROOTS],
            "exclusions": [{"pattern": p, "why": w} for p, w in pt.EXCLUSIONS],
            "file_count": len(prod),
            "manifest_file": "code_audit/run22_production_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(),
            "superseded_manifest": "code_audit/run20_production_freeze.sha256",
            "superseded_manifest_file_count": 143,
            "files_previously_invisible_to_the_freeze": len(prod) - 143,
            "files": [{"path": rel, "sha256": digest, "bytes": size, "git_tracked": tracked}
                      for rel, digest, size, tracked in prod],
        },

        "scientific_authority": {
            "file_count": len(auth),
            "manifest_file": "code_audit/run22_authority_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(None, pt.AUTHORITY_ROOTS),
            "supervisory_specification":
                "research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md",
            "supervisory_specification_sha256": sha(
                "research/methodology/"
                "PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md"),
            "supervisory_specification_metadata_sha256": sha(
                "research/methodology/"
                "PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.metadata.json"),
            "files": [{"path": rel, "sha256": digest} for rel, digest, _s, _t in auth],
        },

        "scientific_baseline": {
            "authoritative_result_set": "code_audit/run20_cycle12_100_reaudit.csv",
            "authoritative_result_set_sha256": sha("code_audit/run20_cycle12_100_reaudit.csv"),
            "superseded_result_set": "server/tools/run17/scientific_results.csv",
            "superseded_result_set_sha256": sha("server/tools/run17/scientific_results.csv"),
            "superseded_note":
                "the Run-17 file is a HISTORICAL record and is NOT the final baseline. It still "
                "carries METHOD_LABEL_MISMATCH 23, IMPLEMENTATION_DEFECT 6 and "
                "MISSING_CANONICAL_DATA_STRUCTURE 13, all of which Run 20 subsequently closed. "
                "It is frozen so the history is auditable, and named here so it can never be "
                "mistaken for the current one.",
            "registered_project_modules": len(project_modules),
            "portfolio_modules": len(portfolio_modules),
            "material_cost_variance_excluded_from_active_population": 1,
            "project_scientific_targets": len(project_modules) - 1,
            "portfolio_scientific_targets": len(portfolio_modules),
            "total_scientific_targets": len(reaudit),
            "unique_canonical_ids": len({r["module_id"] for r in reaudit}),
            "dispositions": dict(sorted(dispositions.items())),
            "NOT_REACHED": dispositions.get("NOT_REACHED", 0),
            "NOT_ASSESSED": dispositions.get("NOT_ASSESSED", 0),
            "IMPLEMENTATION_DEFECT": dispositions.get("IMPLEMENTATION_DEFECT", 0),
            "METHOD_LABEL_MISMATCH": dispositions.get("METHOD_LABEL_MISMATCH", 0),
            "MISSING_CANONICAL_DATA_STRUCTURE":
                dispositions.get("MISSING_CANONICAL_DATA_STRUCTURE", 0),
        },

        "activation_and_voting": {
            "derivation": "read from server/app/simulation/registry.py at freeze time",
            "voting_modules": sorted(R.CORE_VOTING_MODULES),
            "voting_count": len(R.CORE_VOTING_MODULES),
            "concept_only_disabled": sorted(R.DISABLED_CONCEPT_ONLY),
            "concept_only_activation": 0,
            "material_cost_variance_canonical_id": "A3.4",
            "material_cost_variance_enabled": "A3.4" not in R.DISABLED_MODULES,
            "disabled_modules_total": len(R.DISABLED_MODULES),
            "registry_sha256": sha("server/app/simulation/registry.py"),
        },

        "version_identities": {
            "simulation_engine": sha("server/app/simulation/compute.py"),
            "simulation_registry": sha("server/app/simulation/registry.py"),
            "lineage_layer": sha("server/app/simulation/lineage.py"),
            "qualification_gate": sha("server/app/simulation/qualification_gate.py"),
            "client_algorithm_version_file": sha("assets/js/client_algorithm_version.js"),
            "synthetic_package_version": "v0.3 (Monte Carlo / DSM correction), "
                                         "REPORT_2026-08-12_synthetic-v0.3-monte-carlo-dsm-"
                                         "correction.md",
            "participant_package_provisioning_record":
                sha("code_audit/run12_participant_provisioning.csv"),
            "scientific_specification_version": "v1, Run 19, CONTROLLING",
            "freeze_release_version": RELEASE_ID,
        },

        "qualification_evidence": {
            "run20_report_sha256": sha(
                "REPORT_2026-08-14_run20-supervised-scientific-remediation-loop.md"),
            "run21_report_sha256": sha(
                "REPORT_2026-08-14_run21-final-instrument-qualification.md"),
            "run22_report_sha256": None,
            "run22_report_note":
                "null at stage 1 for the same reason as manifest_sha256: the report records this "
                "manifest's digest, so the manifest cannot also record the report's. The "
                "report's digest is in the companion .sha256 file.",
            "registers": {name: sha(f"code_audit/{name}") for name in sorted([
                "run22_freeze_qualification_register.csv",
                "run22_git_baseline_reconciliation.csv",
                "run22_reload_diagnostics.csv",
                "run22_reload_attribution.csv",
                "run22_final_guard_nonvacuity.csv",
                "run22_owner_decisions_remaining.csv",
                "run22_release_definition.csv",
                "run20_cycle12_lineage_campaign.csv",
                "run20_cycle12_guard_nonvacuity.csv",
                "run21_reset_reload_results.csv",
            ])},
        },

        "known_limitations": [
            "Queue item 1: whether the participant-surface method names should be renamed is an "
            "OPEN OWNER DECISION. This release renames nothing a participant reads.",
            "Queue item 2: B1.4 Worst-N-of-M has no source for its fixed N. "
            "PARAMETER_PROVENANCE_BLOCKED, advisory, non-voting.",
            "Queue item 3: PH.5 Anomaly Score weights have no calibration evidence. "
            "THRESHOLD_CALIBRATION_BLOCKED, advisory, non-voting.",
            "Queue item 4: empirical validation is an unstarted research programme. No module is "
            "empirically validated and this release claims no validated performance.",
            "Item 7 residual: the instrument becomes usable 288 ms after the server responds, but "
            "a participant machine that falls back to SOFTWARE WebGL would meet the same "
            "CPU rasterisation cost this GPU-less container does, bounded to the 3D surfaces on "
            "the project detail view. A screening question for participant machines.",
            "Tavily and live web were unavailable in this session; no item was closed by guessing "
            "an external fact.",
        ],

        "release_status": "RECORDED SEPARATELY IN code_audit/run22_release_definition.csv AND IN "
                          "THE RUN-22 REPORT",
    }

    out_dir = ROOT / "research" / "freeze"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "FINAL_RESEARCH_INSTRUMENT_FREEZE_2026-08-14.json"
    # sort_keys=False keeps the document's own reading order; the determinism that matters is the
    # file list's, and that is byte-sorted by the walk.
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    print(f"  production files: {len(prod)}  authority files: {len(auth)}")
    print(f"  targets: {len(reaudit)}  voting: {len(R.CORE_VOTING_MODULES)}  "
          f"MCV enabled: {'A3.4' not in R.DISABLED_MODULES}")
    print(f"  STAGE-1 digest (goes in the companion file): "
          f"{hashlib.sha256(out.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
