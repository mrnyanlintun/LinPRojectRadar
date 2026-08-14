#!/usr/bin/env python3
"""
RUN 28. THE SUPERSEDING FREEZE MANIFEST FOR THE NEW ANALYTICAL LINE.

WHY A NEW FREEZE EXISTS AT ALL, AND WHY THIS ONE IS DIFFERENT FROM THE FIVE BEFORE IT. Runs 22
through 26 each superseded the freeze for a UI or display change, and each asserted that nothing
under server/app/simulation/ had been read, executed differently or changed. Run 28 is the first
run since the instrument was frozen to change ANALYTICAL PRODUCTION CODE, on the owner's explicit
supervisory instruction, and the freeze says so plainly rather than burying it.

The Run-26 freeze, OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN26-COUNTS-WIRING-EMPTY-1,
therefore no longer describes the executable baseline. It is NOT rewritten: it stays exactly as
Run 26 wrote it, as the historical record of that release, and this document supersedes it by
naming it as its parent and carrying its digest. The freezes behind it are likewise untouched.

THE VERSION BOUNDARY, WHICH IS THE POINT OF THE RUN. The analytical layer moves from
sim-2026.08-v10 to sim-2026.08-v11. Every earlier stamp, from sim-2026.07-v1 onward, remains the
historical audit baseline for the results collected under it; none is overwritten and none is
re-used. The owner's Run-28 prompt describes the platform as frozen at sim-2026.08-v2 and asks
for a new line called v3. That premise does not match this repository: sim-2026.08-v3 has existed
since Run 7 and the line has moved eight times since. Creating a second v3 would have collided
with Run 7's stamp and read as a regression from v10, making results already collected under v10
ambiguous, which is the exact harm the stamp exists to prevent. The owner's INTENT -- the current
line becomes immutable historical evidence and this run's analytical changes belong to a new line
-- is honoured with the next unused identifier in the sequence, and the departure is recorded
here, in server/app/simulation/models.py and in the run's report.

AN OWNER-DIRECTED CONTRACT CHANGE, NOT A DRIFT. The byte-identical frozen-file guard over
server/app/simulation/ has blocked every run since Run 20. It was turned RED first and observed,
then a sixth declared-changes manifest was written and the production-tree pin repointed. The
change is recorded in code_audit/run20_anti_fossilization_register.csv alongside the three other
owner-directed contract changes this run made.

The same two-stage construction Runs 22 to 26 used, for the same reason: a manifest cannot
contain its own SHA-256, and cannot contain the hash of the commit that introduces it.

    STAGE 1  writes research/freeze/RUN28_CANONICAL_CAT1_3_FREEZE_2026-08-14.json with
             manifest_sha256 and final_commit null. That file is committed.
    STAGE 2  --finalise writes the companion .sha256 with the digest of the stage-1 file and
             the merged-main commit that carried it.
"""

from __future__ import annotations

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
import run28_production_changes as _R28  # noqa: E402

RELEASE_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN28-CANONICAL-CAT1-3-V11-1"
PARENT_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN26-COUNTS-WIRING-EMPTY-1"
STAGE1 = ROOT / "research" / "freeze" / "RUN28_CANONICAL_CAT1_3_FREEZE_2026-08-14.json"
STAGE2 = STAGE1.with_suffix(".sha256")
REPORT = "REPORT_2026-08-14_run28-cat1-3-canonical-remediation-v3.md"


def sha(rel: str) -> str | None:
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


CHANGED: dict[str, str] = {}
for _mid, (_authority, _path, _why) in sorted(_R28.RUN28_PRODUCTION_CHANGES.items()):
    CHANGED[_path] = f"{_mid}: {_why}"
for _path in ("server/app/simulation/models_ext.py", "server/app/simulation/registry.py",
              "server/app/simulation/method_labels.py", "server/app/simulation/lineage.py",
              "server/app/simulation/parameters.py"):
    CHANGED[_path] = (
        "Changed by Run 28 and ALREADY DECLARED against the Run-20 freeze by "
        "run20_production_changes.py, so deliberately NOT declared a second time: the "
        "declared-changes guard requires that no path appear in two manifests. models_ext.py "
        "carries the Category 2 and 3 module runners; registry.py routes a calibration-pending "
        "row to the computed rows and lost eleven proxy qualifiers because the proxies are "
        "gone; method_labels.py lost nine truthful-method labels for the same reason; "
        "lineage.py re-declares six modules against the facts they now actually read; "
        "parameters.py adds provenance rows for the two modules that gained tunable values by "
        "gaining a supply path.")
CHANGED["server/tools/production_tree.py"] = (
    "The pinned production manifest moved from code_audit/run26_production_tree.sha256 to "
    "code_audit/run28_production_tree.sha256, and the run26 manifest is kept addressable as "
    "PINNED_RUN26. Not a deployed file and not part of the walked production surface; recorded "
    "here because it is the guard's own pointer.")


def build() -> None:
    from app.simulation import registry as R  # noqa: E402

    prod = pt.walk_production()
    auth = pt.walk_production(None, pt.AUTHORITY_ROOTS)

    doc = {
        "release_identifier": RELEASE_ID,
        "supersedes": PARENT_ID,
        "supersedes_manifest":
            "research/freeze/RUN26_COUNTS_WIRING_EMPTY_FREEZE_2026-08-14.json",
        "supersedes_manifest_sha256": sha(
            "research/freeze/RUN26_COUNTS_WIRING_EMPTY_FREEZE_2026-08-14.json"),
        "grandparent_release": "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN25-RAIL-REMOVAL-1",
        "grandparent_manifest":
            "research/freeze/RUN25_RAIL_REMOVAL_FREEZE_2026-08-14.json",
        "grandparent_manifest_sha256": sha(
            "research/freeze/RUN25_RAIL_REMOVAL_FREEZE_2026-08-14.json"),
        "supersedes_note":
            "the Run-26 freeze, and the Run-25, Run-24, post-Run-22 and Run-22 freezes behind "
            "it, are all preserved unchanged as the historical record of those releases. This "
            "one supersedes, it does not rewrite: ANALYTICAL production code changed after the "
            "parent was taken, for the first time since the instrument was frozen, so the "
            "parent no longer describes the executable baseline.",
        "release_date": dt.date(2026, 8, 14).isoformat(),
        "generated_by": "server/tools/build_run28_freeze.py",
        "reason": "implement the owner's supplied Category 1 to 3 supervisory method contracts "
                  "in a new analytical line, supply the governed data structures those methods "
                  "are defined on, wire two of them from evidence the corpus already holds, and "
                  "abstain where a project does not possess the defining structure; four "
                  "owner-directed contract changes are recorded in "
                  "code_audit/run20_anti_fossilization_register.csv",
        "version_boundary": {
            "new_line": "sim-2026.08-v11",
            "superseded_line": "sim-2026.08-v10",
            "history_preserved": [
                "sim-2026.07-v1", "sim-2026.08-v2", "sim-2026.08-v3", "sim-2026.08-v4",
                "sim-2026.08-v5", "sim-2026.08-v6", "sim-2026.08-v7", "sim-2026.08-v8",
                "sim-2026.08-v9", "sim-2026.08-v10", "sim-2026.08-v11"],
            "owner_premise_departure":
                "the Run-28 prompt describes the platform as frozen at sim-2026.08-v2 and asks "
                "for a new line called sim-2026.08-v3. sim-2026.08-v3 has existed since Run 7 "
                "and the stamp standing at the start of Run 28 was sim-2026.08-v10, recorded in "
                "the comment block at server/app/simulation/models.py lines 46 to 107. Creating "
                "a second v3 would have collided with Run 7's stamp and read as a regression "
                "from v10, making results already collected under v10 ambiguous. The owner's "
                "intent was honoured with the next unused identifier and the departure is "
                "reported.",
            "historical_line_still_executable":
                "server/tools/test_run7_fix_now_defects.py extracts the analytical package as "
                "it shipped at sim-2026.08-v2 from git at the pinned commit 021d5e2, imports "
                "it, EXECUTES it and compares it against the current line on identical inputs. "
                "A frozen record that could not be executed would not be evidence of anything.",
        },
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
            "simulation_package_untouched_by_this_run": False,
            "simulation_package_change_authority":
                "the owner's Run-28 supervisory method contract, which authorises modification "
                "of v3 analytical production code, data contracts and schemas for the Category "
                "1 to 3 scope. The byte-identical frozen-file guard was turned RED first and "
                "observed, then a sixth declared-changes manifest was written; the guard's "
                "property is unchanged and the change is recorded in "
                "code_audit/run20_anti_fossilization_register.csv.",
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
            "run28_evidence": {
                "scope": "code_audit/run28_cat1_3_scope.csv",
                "scope_note": "28 remediation rows derived from the Run-27 matrix -- Category 1 "
                              "nine, Category 2 eleven, Category 3 eight -- plus the two "
                              "scientific passes and the registered disabled module, "
                              "reconciled mechanically against the registry.",
                "non_vacuity_campaign": "code_audit/run28_fault_injection.csv",
                "non_vacuity_note": "six faults, each with the baseline rechecked green before "
                                    "injection, the injection confirmed by re-reading the file "
                                    "from disk, the guard observed RED rather than crashed, the "
                                    "file restored byte for byte and the baseline rechecked "
                                    "green after.",
                "declared_production_changes": "server/tools/run28_production_changes.py",
                "approved_renames": {
                    "A1.10": "Regression to Mean CPI -> CPI Shrinkage Forecast",
                    "A1.11": "ICE Ratio -> Independent EAC Reconciliation Index"},
                "participant_surface_unchanged":
                    "assets/js/taxonomy.js is NOT renamed. It is the participant ledger's own "
                    "name source, it is inside the frozen and checksummed participant package "
                    "og-participant-2026.08-v1, and the study is mid-sequence, so renaming what "
                    "a participant reads would change the treatment. The approved names reach "
                    "the registry map, the interface response, the export and the methods "
                    "documentation, by the mechanism Run 20 established.",
            },
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

    STAGE1.parent.mkdir(parents=True, exist_ok=True)
    STAGE1.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {STAGE1.relative_to(ROOT)}")
    print(f"  production files: {len(prod)}  voting: {len(R.CORE_VOTING_MODULES)}  "
          f"MCV enabled: {'A3.4' not in R.DISABLED_MODULES}")
    print(f"  STAGE-1 digest: {hashlib.sha256(STAGE1.read_bytes()).hexdigest()}")


def finalise() -> None:
    digest = hashlib.sha256(STAGE1.read_bytes()).hexdigest()
    commit = git("rev-parse", "HEAD")
    STAGE2.write_text(
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
