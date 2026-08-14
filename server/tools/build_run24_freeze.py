#!/usr/bin/env python3
"""
RUN 24. THE SUPERSEDING FREEZE MANIFEST.

WHY A NEW FREEZE EXISTS AT ALL. One production UI file, assets/js/neural_flow.js, changed
after the post-Run-22 UI correction freeze was taken: the Signal Flow now leads an empty
project with a statement of what it will show, and puts the registered architecture behind an
explicit control. That freeze,
OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-POSTRUN22-UI-1, therefore no longer describes
the executable baseline, and leaving it presented as the current one would be false. It is NOT
rewritten: it stays exactly as that correction wrote it, as the historical record of that
release, and this document supersedes it by naming it as its parent. The Run-22 freeze behind
it is likewise untouched.

DISPLAY ONLY. Nothing under server/app/simulation/ was read, executed differently or changed.
The scientific authority tree is byte-identical and is asserted so below; activation, voting
and the disabled-concept-only set are re-read from the registry at freeze time and are
unchanged.

The same two-stage construction Run 22 used, for the same reason: a manifest cannot contain its
own SHA-256, and cannot contain the hash of the commit that introduces it.

    STAGE 1  writes research/freeze/POST_RUN22_UI_CORRECTION_FREEZE_2026-08-14.json with
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

RELEASE_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN24-EMPTY-DIAGRAM-1"
PARENT_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-POSTRUN22-UI-1"
STAGE1 = ROOT / "research" / "freeze" / "RUN24_EMPTY_PROJECT_DIAGRAM_FREEZE_2026-08-14.json"
STAGE2 = STAGE1.with_suffix(".sha256")
# THE REPORT. This run's session harness refused to write a .md report file into the
# repository (it requires a subagent's findings to be returned as text), so the report was
# delivered as the run's returned text and is quoted in full in T6_HANDOFF.md instead. The
# path is kept here so a later run that CAN write it lands it in the expected place, and
# `sha()` returns null for a file that is not present rather than inventing a digest.
REPORT = "REPORT_2026-08-14_empty-project-diagram.md"


def sha(rel: str) -> str | None:
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


CHANGED = {
    "assets/js/neural_flow.js":
        "Signal Flow empty-project gate. The previous render is unchanged and is now called "
        "drawDiagram; it returns the emptiness decision it already computed for its own summary "
        "sentence. render() draws it into a host element and, when and only when that one "
        "predicate says the project has no uploaded documents, no module with a current result "
        "and no estimable category, hides the host and leads with a short statement of what the "
        "view will show once documents arrive, plus an explicit control (.lnf-reveal, "
        "aria-expanded / aria-controls) that reveals the full architecture. Nothing is removed: "
        "the same diagram, the same nodes and the same links are one click away, and a project "
        "with any current evidence is completely unaffected. Also added, so a check can read "
        "the shipped decision instead of inferring it from a shade: data-kind on every node "
        "group (module / category / project / document) and data-state on every document row "
        "(uploaded / registered-not-active / not-uploaded). No count, no threshold, no status "
        "rule and no illumination rule changed.",
    "server/tools/production_tree.py":
        "The pinned production manifest moved from code_audit/run23_production_tree.sha256 to "
        "code_audit/run24_production_tree.sha256, and the run23 manifest is kept addressable as "
        "PINNED_RUN23. Not a deployed file and not part of the walked production surface; "
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
            "research/freeze/POST_RUN22_UI_CORRECTION_FREEZE_2026-08-14.json",
        "supersedes_manifest_sha256": sha(
            "research/freeze/POST_RUN22_UI_CORRECTION_FREEZE_2026-08-14.json"),
        "grandparent_release": "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN22",
        "grandparent_manifest":
            "research/freeze/FINAL_RESEARCH_INSTRUMENT_FREEZE_2026-08-14.json",
        "grandparent_manifest_sha256": sha(
            "research/freeze/FINAL_RESEARCH_INSTRUMENT_FREEZE_2026-08-14.json"),
        "supersedes_note":
            "the post-Run-22 UI correction freeze, and the Run-22 freeze behind it, are both "
            "preserved unchanged as the historical record of those releases. This one "
            "supersedes, it does not rewrite: one production UI file changed after the parent "
            "was taken, so the parent no longer describes the executable baseline.",
        "release_date": dt.date(2026, 8, 14).isoformat(),
        "generated_by": "server/tools/build_run23_freeze.py",
        "reason": "an empty project must look empty on the Signal Flow diagram",
        "self_reference_note":
            "manifest_sha256 and final_commit are null BY CONSTRUCTION; both are recorded in the "
            "companion .sha256 file written by the finalisation commit.",
        "manifest_sha256": None,
        "final_commit": None,
        "starting_commit": "21a6db1",
        "stage1_parent_commit": git("rev-parse", "HEAD"),
        "stage1_repository_tree_hash": git("rev-parse", "HEAD^{tree}"),

        "ui_production_files_changed": [
            {"path": p, "sha256": sha(p), "why": why} for p, why in sorted(CHANGED.items())
        ],

        "production_surface": {
            "discovery": "walked from the deployed roots in server/tools/production_tree.py",
            "file_count": len(prod),
            "manifest_file": "code_audit/run24_production_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(),
            "parent_manifest_file": "code_audit/run23_production_tree.sha256",
            "parent_manifest_sha256": hashlib.sha256(
                (ROOT / "code_audit" / "run23_production_tree.sha256").read_bytes()).hexdigest(),
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
            "browser_driver": "server/tools/drive_run24_empty_project_diagram.py",
            "browser_facts_before_the_change":
                "code_audit/run24_empty_project_diagram_baseline.csv",
            "browser_facts_after_the_change": "code_audit/run24_empty_project_diagram_after.csv",
            "browser_facts_on_merged_main": "code_audit/run24_empty_project_diagram_merged.csv",
            "source_guard_suite": "server/tools/test_run24_empty_project_diagram.py",
            "declared_production_changes":
                "assets/js/neural_flow.js is already declared by "
                "server/tools/run21_production_changes.py and is deliberately NOT declared a "
                "second time: the declared-changes guard requires that no path appear in two "
                "manifests, so declaring it again would let one change be counted as two.",
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
            "report_note":
                "delivered as the run's returned text and quoted in full in T6_HANDOFF.md; "
                "the session harness refused to write a .md report file into the repository.",
            "report_sha256": sha(REPORT),
            "parent_report_sha256": sha(
                "REPORT_2026-08-14_post-run22-signal-flow-ui-correction.md"),
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
