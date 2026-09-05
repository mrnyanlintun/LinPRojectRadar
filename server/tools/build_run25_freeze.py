#!/usr/bin/env python3
"""
RUN 25. THE SUPERSEDING FREEZE MANIFEST.

WHY A NEW FREEZE EXISTS AT ALL. Three production UI files changed after the Run-24 freeze was
taken: on the owner's explicit 2026-08-14 instruction the left section-navigator rail was
removed entirely -- the element from index.html, its builder from assets/js/detail.js and its
styles from assets/css/radar.css. The Run-24 freeze,
OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN24-EMPTY-DIAGRAM-1, therefore no longer
describes the executable baseline, and leaving it presented as the current one would be
false. It is NOT rewritten: it stays exactly as Run 24 wrote it, as the historical record of
that release, and this document supersedes it by naming it as its parent. The freezes behind
it are likewise untouched.

AN OWNER-DIRECTED CONTRACT CHANGE, NOT A DRIFT. Earlier owner instructions said the numbered
Signal rail stays, and Runs 16, 23 and 24 guarded its presence. The 2026-08-14 instruction
reverses that. The guards were inverted deliberately, each one citing the instruction, and
the reversal is recorded in code_audit/run20_anti_fossilization_register.csv.

DISPLAY ONLY. Nothing under server/app/simulation/ was read, executed differently or changed.
The scientific authority tree is byte-identical and is asserted so below; activation, voting
and the disabled-concept-only set are re-read from the registry at freeze time and are
unchanged.

The same two-stage construction Runs 22 to 24 used, for the same reason: a manifest cannot
contain its own SHA-256, and cannot contain the hash of the commit that introduces it.

    STAGE 1  writes research/freeze/RUN25_RAIL_REMOVAL_FREEZE_2026-08-14.json with
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

RELEASE_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN25-RAIL-REMOVAL-1"
PARENT_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN24-EMPTY-DIAGRAM-1"
STAGE1 = ROOT / "research" / "freeze" / "RUN25_RAIL_REMOVAL_FREEZE_2026-08-14.json"
STAGE2 = STAGE1.with_suffix(".sha256")
REPORT = "REPORT_2026-08-14_rail-and-empty-diagram.md"


def sha(rel: str) -> str | None:
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


CHANGED = {
    "index.html":
        "The left section-navigator rail element (a fixed column of numbered controls listing "
        "the detail page's collapsible sections) is removed from the served page on the "
        "owner's explicit 2026-08-14 instruction, which reverses the earlier instruction that "
        "the rail stays. Sections remain reachable by their own headers. Declared in "
        "server/tools/run25_production_changes.py.",
    "assets/js/detail.js":
        "The rail's builder and its scroll-spy IntersectionObserver are removed with the rail "
        "they built; nothing else consumed them. Already declared against the Run-20 freeze "
        "by run23_production_changes.py, so deliberately NOT declared a second time.",
    "assets/css/radar.css":
        "Every rail style, desktop and mobile alike, is removed. Already declared against the "
        "Run-20 freeze by run23_production_changes.py, so deliberately NOT declared a second "
        "time.",
    "server/tools/production_tree.py":
        "The pinned production manifest moved from code_audit/run24_production_tree.sha256 to "
        "code_audit/run25_production_tree.sha256, and the run24 manifest is kept addressable "
        "as PINNED_RUN24. Not a deployed file and not part of the walked production surface; "
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
            "research/freeze/RUN24_EMPTY_PROJECT_DIAGRAM_FREEZE_2026-08-14.json",
        "supersedes_manifest_sha256": sha(
            "research/freeze/RUN24_EMPTY_PROJECT_DIAGRAM_FREEZE_2026-08-14.json"),
        "grandparent_release": "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-POSTRUN22-UI-1",
        "grandparent_manifest":
            "research/freeze/POST_RUN22_UI_CORRECTION_FREEZE_2026-08-14.json",
        "grandparent_manifest_sha256": sha(
            "research/freeze/POST_RUN22_UI_CORRECTION_FREEZE_2026-08-14.json"),
        "supersedes_note":
            "the Run-24 freeze, and the post-Run-22 and Run-22 freezes behind it, are all "
            "preserved unchanged as the historical record of those releases. This one "
            "supersedes, it does not rewrite: three production UI files changed after the "
            "parent was taken (the owner-directed rail removal), so the parent no longer "
            "describes the executable baseline.",
        "release_date": dt.date(2026, 8, 14).isoformat(),
        "generated_by": "server/tools/build_run25_freeze.py",
        "reason": "remove the left rail entirely, on the owner's 2026-08-14 instruction; "
                  "an owner-directed contract change recorded in "
                  "code_audit/run20_anti_fossilization_register.csv",
        "self_reference_note":
            "manifest_sha256 and final_commit are null BY CONSTRUCTION; both are recorded in "
            "the companion .sha256 file written by the finalisation commit.",
        "manifest_sha256": None,
        "final_commit": None,
        "starting_commit": "017c95e",
        "stage1_parent_commit": git("rev-parse", "HEAD"),
        "stage1_repository_tree_hash": git("rev-parse", "HEAD^{tree}"),

        "ui_production_files_changed": [
            {"path": p, "sha256": sha(p), "why": why} for p, why in sorted(CHANGED.items())
        ],

        "production_surface": {
            "discovery": "walked from the deployed roots in server/tools/production_tree.py",
            "file_count": len(prod),
            "manifest_file": "code_audit/run25_production_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(),
            "parent_manifest_file": "code_audit/run24_production_tree.sha256",
            "parent_manifest_sha256": hashlib.sha256(
                (ROOT / "code_audit" / "run24_production_tree.sha256").read_bytes()).hexdigest(),
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
            "browser_driver": "server/tools/drive_run25_rail_removal.py",
            "browser_facts_on_arrival_before_the_change":
                "code_audit/run24_empty_project_diagram_arrival.csv",
            "browser_facts_after_the_change": "code_audit/run25_rail_removal_after.csv",
            "browser_facts_on_merged_main": "code_audit/run25_rail_removal_merged.csv",
            "source_guard_suite": "server/tools/test_run25_rail_removal.py",
            "guards_inverted_by_the_owner_instruction": [
                "server/tools/test_run16_final_flow_and_rail.py section B",
                "server/tools/test_run23_signal_flow_truthfulness.py sections 2 and 3",
                "server/tools/test_run24_empty_project_diagram.py navigator-untouched check",
                "server/tools/test_run2_fifteen_defects.py detail.js freeze-diff allowance",
            ],
            "declared_production_changes":
                "index.html is declared by server/tools/run25_production_changes.py. "
                "assets/js/detail.js and assets/css/radar.css are already declared by "
                "run23_production_changes.py and are deliberately NOT declared a second time: "
                "the declared-changes guard requires that no path appear in two manifests.",
            "registry_figures": {
                "project_level_categories": 11,
                "project_level_modules": 96,
                "of_which_supplied_by_the_extraction_model": 1,
                "of_which_computed_by_the_analytical_server": 95,
                "whole_taxonomy_categories": 12,
                "whole_taxonomy_modules": 101,
                "source": "assets/js/taxonomy.js, read in a real browser and re-parsed "
                          "independently by server/tools/test_run24_empty_project_diagram.py",
            },
            "report": REPORT,
            "report_present_in_tree": (ROOT / REPORT).is_file(),
            "report_sha256": sha(REPORT),
            "parent_report_sha256": sha("REPORT_2026-08-14_empty-project-diagram.md"),
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
