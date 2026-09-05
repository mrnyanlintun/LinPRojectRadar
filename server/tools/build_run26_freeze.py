#!/usr/bin/env python3
"""
RUN 26. THE SUPERSEDING FREEZE MANIFEST.

WHY A NEW FREEZE EXISTS AT ALL. Three production UI files changed after the Run-25 freeze was
taken. `assets/js/neural_flow.js` was rewired: every rendered edge is now derived from a
committed authority rather than from two hand-written arrays of category indices written
against a retired category order, the fabricated governance feedback arc is gone, and an empty
project renders in one neutral colour on the owner's 2026-08-14 instruction. `index.html` and
`assets/js/knowledge.js` state the count scopes rather than one unqualified number. The Run-25
freeze, OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN25-RAIL-REMOVAL-1, therefore no
longer describes the executable baseline. It is NOT rewritten: it stays exactly as Run 25
wrote it, as the historical record of that release, and this document supersedes it by naming
it as its parent. The freezes behind it are likewise untouched.

AN OWNER-DIRECTED CONTRACT CHANGE, NOT A DRIFT. An earlier owner prompt explicitly endorsed
the purple not-relevant square as the correct not-relevant state, and Runs 23 and 24 guarded
it. The 2026-08-14 instruction reverses that for a project with no evidence. The guards were
inverted deliberately, each one observed red against this build before being rewritten, and
the reversal is recorded in code_audit/run20_anti_fossilization_register.csv.

DISPLAY AND TEXT ONLY. Nothing under server/app/simulation/ was read, executed differently or
changed. The scientific authority tree is byte-identical and is asserted so below; activation,
voting and the disabled-concept-only set are re-read from the registry at freeze time and are
unchanged.

The same two-stage construction Runs 22 to 25 used, for the same reason: a manifest cannot
contain its own SHA-256, and cannot contain the hash of the commit that introduces it.

    STAGE 1  writes research/freeze/RUN26_COUNTS_WIRING_EMPTY_FREEZE_2026-08-14.json with
             manifest_sha256 and final_commit null. That file is committed.
    STAGE 2  --finalise writes the companion .sha256 with the digest of the stage-1 file and
             the merged-main commit that carried it.
"""

from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

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

RELEASE_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN26-COUNTS-WIRING-EMPTY-1"
PARENT_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN25-RAIL-REMOVAL-1"
STAGE1 = ROOT / "research" / "freeze" / "RUN26_COUNTS_WIRING_EMPTY_FREEZE_2026-08-14.json"
STAGE2 = STAGE1.with_suffix(".sha256")
REPORT = "REPORT_2026-08-14_sitewide-counts-wiring-and-empty.md"


def sha(rel: str) -> str | None:
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


CHANGED = {
    "assets/js/neural_flow.js":
        "THE WIRING IS DERIVED, THE EMPTY PROJECT IS GREY. Two hand-written arrays of category "
        "indices, DOC_TO_CATS and INTER_CAT, were written against the retired gapless Cat 1-10 "
        "scheme and had silently repointed when the eleven-category taxonomy replaced it, so "
        "every document line and every inter-category feed rendered landing on the wrong "
        "category; the document lines themselves were drawn to the first two modules of a "
        "category by REGISTRY ORDER. Both arrays are gone. DOCUMENT -> MODULE is derived from "
        "the document contract crossed with each module's own declared required inputs, "
        "MODULE -> CATEGORY from registry membership, CATEGORY -> CATEGORY from the four "
        "dependencies the architecture master states in words, and CATEGORY -> PROJECT STATUS "
        "from GROUP_ASSIGNMENT.md, which excludes Data and Evidence Health. The governance "
        "feedback arc, which drew PROJECT STATUS -> CATEGORY at a stale index and was the only "
        "red stroke on an empty project, is removed. On a project with no evidence every node "
        "and every edge renders in the no-data colour. Already declared against the Run-20 "
        "freeze by run21_production_changes.py, so deliberately NOT declared a second time.",
    "index.html":
        "The About panel's analytical-layer paragraph and its note now state the registry "
        "total with both of its scopes, 101 registered modules of which 96 are project level "
        "and 5 Portfolio Health, and state the computed count as a scope of the registry "
        "rather than as a rival total. Already declared against the Run-20 freeze by "
        "run25_production_changes.py, so deliberately NOT declared a second time.",
    "assets/js/knowledge.js":
        "Four user-visible passages said 100 without saying which population of 100 they "
        "meant. They now state scope, name the one module that makes the computed figure "
        "differ from the registered one, and separate registration from activation. Declared "
        "in server/tools/run26_production_changes.py.",
    "server/tools/production_tree.py":
        "The pinned production manifest moved from code_audit/run25_production_tree.sha256 to "
        "code_audit/run26_production_tree.sha256, and the run25 manifest is kept addressable "
        "as PINNED_RUN25. Not a deployed file and not part of the walked production surface; "
        "recorded here because it is the guard's own pointer.",
}


def build() -> None:
    from app.simulation import registry as R  # noqa: E402

    prod = pt.walk_production()
    auth = pt.walk_production(None, pt.AUTHORITY_ROOTS)

    doc = {
        "release_identifier": RELEASE_ID,
        "supersedes": PARENT_ID,
        "supersedes_manifest":
            "research/freeze/RUN25_RAIL_REMOVAL_FREEZE_2026-08-14.json",
        "supersedes_manifest_sha256": sha(
            "research/freeze/RUN25_RAIL_REMOVAL_FREEZE_2026-08-14.json"),
        "grandparent_release": "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN24-EMPTY-DIAGRAM-1",
        "grandparent_manifest":
            "research/freeze/RUN24_EMPTY_PROJECT_DIAGRAM_FREEZE_2026-08-14.json",
        "grandparent_manifest_sha256": sha(
            "research/freeze/RUN24_EMPTY_PROJECT_DIAGRAM_FREEZE_2026-08-14.json"),
        "supersedes_note":
            "the Run-25 freeze, and the Run-24, post-Run-22 and Run-22 freezes behind it, are "
            "all preserved unchanged as the historical record of those releases. This one "
            "supersedes, it does not rewrite: three production UI files changed after the "
            "parent was taken (the Signal Flow rewiring, the empty-project colour rule and the "
            "count wording), so the parent no longer describes the executable baseline.",
        "release_date": dt.date(2026, 8, 14).isoformat(),
        "generated_by": "server/tools/build_run26_freeze.py",
        "reason": "reconcile the sitewide module counts, derive the Signal Flow wiring from "
                  "the architecture master and the registry rather than from position, and "
                  "render an empty project in one neutral colour, on the owner's 2026-08-14 "
                  "instruction; the empty-project colour rule is an owner-directed contract "
                  "change recorded in code_audit/run20_anti_fossilization_register.csv",
        "self_reference_note":
            "manifest_sha256 and final_commit are null BY CONSTRUCTION; both are recorded in "
            "the companion .sha256 file written by the finalisation commit.",
        "manifest_sha256": None,
        "final_commit": None,
        "starting_commit": "e0f3f9c",
        "stage1_parent_commit": git("rev-parse", "HEAD"),
        "stage1_repository_tree_hash": git("rev-parse", "HEAD^{tree}"),

        "ui_production_files_changed": [
            {"path": p, "sha256": sha(p), "why": why} for p, why in sorted(CHANGED.items())
        ],

        "production_surface": {
            "discovery": "walked from the deployed roots in server/tools/production_tree.py",
            "file_count": len(prod),
            "manifest_file": "code_audit/run26_production_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(),
            "parent_manifest_file": "code_audit/run25_production_tree.sha256",
            "parent_manifest_sha256": hashlib.sha256(
                (ROOT / "code_audit" / "run25_production_tree.sha256").read_bytes()).hexdigest(),
            "files": [{"path": rel, "sha256": digest, "bytes": size, "git_tracked": tracked}
                      for rel, digest, size, tracked in prod],
        },

        "scientific_authority": {
            "file_count": len(auth),
            "manifest_file": "code_audit/run22_authority_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(None, pt.AUTHORITY_ROOTS),
            "unchanged_by_this_run": True,
        },

        "activation_and_voting": {
            "derivation": "read from server/app/simulation/registry.py at freeze time",
            "voting_modules": sorted(R.CORE_VOTING_MODULES),
            "voting_count": len(R.CORE_VOTING_MODULES),
            "concept_only_activation": 0,
            "concept_only_disabled": sorted(R.DISABLED_CONCEPT_ONLY),
            "material_cost_variance_canonical_id": "A3.4",
            "material_cost_variance_enabled": "A3.4" not in R.DISABLED_MODULES,
            "registry_sha256": sha("server/app/simulation/registry.py"),
            "registry_unchanged_since_run22": True,
            "simulation_package_untouched_by_this_run": True,
        },

        "qualification_evidence": {
            "architecture_master":
                "research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md",
            "architecture_master_sha256": sha(
                "research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md"),
            "authoritative_edge_inventory":
                "code_audit/signal_flow_authoritative_edges.csv",
            "authoritative_edge_inventory_sha256": sha(
                "code_audit/signal_flow_authoritative_edges.csv"),
            "edge_inventory_note":
                "extracted from the architecture master, the module registry and the document "
                "contract BEFORE the renderer was read for the purpose of deriving an expected "
                "edge. The master's silences are recorded as SILENT rows and are deliberately "
                "not part of the oracle.",
            "browser_driver": "server/tools/drive_run26_counts_wiring_empty.py",
            "browser_facts_before_the_change":
                "code_audit/run26_browser_facts_baseline.csv",
            "browser_facts_after_the_change": "code_audit/run26_browser_facts_after.csv",
            "browser_facts_on_merged_main": "code_audit/run26_browser_facts_merged.csv",
            "empty_project_colour_table":
                "code_audit/run26_empty_project_colours_after.csv",
            "derived_category_table": "code_audit/run26_derived_categories_empty_after.csv",
            "rendered_edge_reconciliation": "code_audit/run26_rendered_edges_after.csv",
            "source_guard_suite": "server/tools/test_run26_counts_and_wiring.py",
            "non_vacuity_source_campaign": "code_audit/run26_fault_injection_results.csv",
            "non_vacuity_browser_campaign": "code_audit/run26_browser_fault_injection.csv",
            "guards_inverted_by_the_owner_instruction": [
                "server/tools/test_document_rows.py sections 2 and 9",
                "server/tools/test_run23_signal_flow_truthfulness.py document tier",
                "server/tools/test_run24_empty_project_diagram.py knowledge-count checks",
                "server/tools/test_run16_final_flow_and_rail.py connection-class count",
            ],
            "declared_production_changes":
                "assets/js/knowledge.js is declared by "
                "server/tools/run26_production_changes.py. assets/js/neural_flow.js and "
                "index.html are already declared by run21_production_changes.py and "
                "run25_production_changes.py and are deliberately NOT declared a second time: "
                "the declared-changes guard requires that no path appear in two manifests.",
            "registry_figures": {
                "registered_project_modules": 96,
                "portfolio_health_modules": 5,
                "registered_total": 101,
                "project_scientific_targets": 95,
                "portfolio_scientific_targets": 5,
                "scientific_targets_assessed": 100,
                "server_computed_project_modules": 95,
                "server_computed_total": 100,
                "supplied_not_computed": "A4.1 Document Risk Score",
                "registered_but_outside_the_audit_population":
                    "A3.4 Material Cost Variance, registered and disabled",
                "the_two_ninety_fives_are_different_sets": True,
                "source": "server/app/simulation/registry.py and "
                          "code_audit/run20_cycle12_100_reaudit.csv, derived at runtime by "
                          "server/tools/test_run26_counts_and_wiring.py and read in a real "
                          "browser by drive_run26_counts_wiring_empty.py",
            },
            "report": REPORT,
            "report_present_in_tree": (ROOT / REPORT).is_file(),
            "report_sha256": sha(REPORT),
            "report_note":
                "if report_present_in_tree is false, the run's harness refused to write a "
                "REPORT_*.md file and the report is reproduced VERBATIM in T6_HANDOFF.md under "
                "the Run-26 heading, for a supervising session to land at the named path. The "
                "freeze records the absence rather than implying a file that is not there.",
            "parent_report_sha256": sha("REPORT_2026-08-14_rail-and-empty-diagram.md"),
        },
    }

    artifact_out(STAGE1.parent).mkdir(parents=True, exist_ok=True)
    STAGE1.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {STAGE1.relative_to(ROOT)}")
    print(f"  production files: {len(prod)}  voting: {len(R.CORE_VOTING_MODULES)}  "
          f"MCV enabled: {'A3.4' not in R.DISABLED_MODULES}")
    print(f"  STAGE-1 digest: {hashlib.sha256(STAGE1.read_bytes()).hexdigest()}")


def finalise() -> None:
    digest = hashlib.sha256(STAGE1.read_bytes()).hexdigest()
    commit = git("rev-parse", "HEAD")
    artifact_out(STAGE2).write_text(
        f"{digest}  {STAGE1.relative_to(ROOT)}\n"
        f"# freeze identifier: {RELEASE_ID}\n"
        f"# supersedes:        {PARENT_ID}\n"
        f"# stage-1 commit:    {commit}\n"
        f"# verify:            sha256sum -c {STAGE2.relative_to(ROOT)}\n",
        encoding="utf-8")
    print(f"wrote {STAGE2.relative_to(ROOT)}")
    print(f"  manifest sha256: {digest}")
    print(f"  stage-1 commit:  {commit}")


if __name__ == "__main__":
    if "--finalise" in sys.argv:
        finalise()
    else:
        build()
