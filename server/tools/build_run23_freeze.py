#!/usr/bin/env python3
"""
POST-RUN-22 UI CORRECTION. THE SUPERSEDING FREEZE MANIFEST.

WHY A NEW FREEZE EXISTS AT ALL. Production UI code changed after Run 22. The Run-22 freeze,
OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN22, therefore no longer describes the
executable baseline, and leaving it presented as the current one would be false. It is NOT
rewritten: it stays exactly as Run 22 wrote it, as the historical record of that release, and
this document supersedes it by naming it as its parent.

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

RELEASE_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-POSTRUN22-UI-1"
PARENT_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN22"
STAGE1 = ROOT / "research" / "freeze" / "POST_RUN22_UI_CORRECTION_FREEZE_2026-08-14.json"
STAGE2 = STAGE1.with_suffix(".sha256")
REPORT = "REPORT_2026-08-14_post-run22-signal-flow-ui-correction.md"


def sha(rel: str) -> str | None:
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


CHANGED = {
    "assets/js/neural_flow.js":
        "Signal Flow empty-state truthfulness: a node reaches the active tier (glow filter and "
        "0.85/0.88/0.92 opacity) only when isEstimable(status) -- a current stored verdict. "
        "Registry facts (a platform-disabled or sector-excluded module, a document type marked "
        "absent from the corpus) no longer illuminate anything, and every node now carries "
        "data-active so the decision is readable in the DOM.",
    "assets/js/detail.js":
        "Signals navigation: the rail marks its chosen entry `selected` + aria-current instead "
        "of `active`, so a navigation selection can never be confused with analytical activity; "
        "a click sets the selection itself rather than waiting on the scroll-spy observer.",
    "assets/css/radar.css":
        "Signals navigation: the rail is opaque instead of .7-until-hovered, the selected-state "
        "rules key on `selected`/aria-current only, and below 700px the rail lays out as a "
        "horizontal bottom row instead of `display: none`, so all controls stay reachable.",
}


def build() -> None:
    from app.simulation import registry as R  # noqa: E402

    prod = pt.walk_production()
    auth = pt.walk_production(None, pt.AUTHORITY_ROOTS)

    doc = {
        "release_identifier": RELEASE_ID,
        "supersedes": PARENT_ID,
        "supersedes_manifest": "research/freeze/FINAL_RESEARCH_INSTRUMENT_FREEZE_2026-08-14.json",
        "supersedes_manifest_sha256": sha(
            "research/freeze/FINAL_RESEARCH_INSTRUMENT_FREEZE_2026-08-14.json"),
        "supersedes_note":
            "the Run-22 freeze is preserved unchanged as the historical record of that release. "
            "It is superseded, not rewritten: production UI code changed after it was taken, so "
            "it no longer describes the executable baseline.",
        "release_date": dt.date(2026, 8, 14).isoformat(),
        "generated_by": "server/tools/build_run23_freeze.py",
        "reason": "Signal Flow empty-state truthfulness + Signals navigation correction",
        "self_reference_note":
            "manifest_sha256 and final_commit are null BY CONSTRUCTION; both are recorded in the "
            "companion .sha256 file written by the finalisation commit.",
        "manifest_sha256": None,
        "final_commit": None,
        "starting_commit": "7226a59",
        "stage1_parent_commit": git("rev-parse", "HEAD"),
        "stage1_repository_tree_hash": git("rev-parse", "HEAD^{tree}"),

        "ui_production_files_changed": [
            {"path": p, "sha256": sha(p), "why": why} for p, why in sorted(CHANGED.items())
        ],

        "production_surface": {
            "discovery": "walked from the deployed roots in server/tools/production_tree.py",
            "file_count": len(prod),
            "manifest_file": "code_audit/run23_production_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(),
            "parent_manifest_file": "code_audit/run22_production_tree.sha256",
            "parent_manifest_sha256": hashlib.sha256(
                (ROOT / "code_audit" / "run22_production_tree.sha256").read_bytes()).hexdigest(),
            "files": [{"path": rel, "sha256": digest, "bytes": size, "git_tracked": tracked}
                      for rel, digest, size, tracked in prod],
        },

        "scientific_authority": {
            "file_count": len(auth),
            "manifest_file": "code_audit/run22_authority_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(None, pt.AUTHORITY_ROOTS),
            "unchanged_by_this_correction": True,
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
        },

        "qualification_evidence": {
            "browser_driver": "server/tools/drive_run23_signal_flow_ui.py",
            "browser_facts": "code_audit/run16_final_flow_run23_merged.csv",
            "source_guard_suite": "server/tools/test_run23_signal_flow_truthfulness.py",
            "declared_production_changes": "server/tools/run23_production_changes.py",
            "report": REPORT,
            "report_sha256": sha(REPORT),
            "run22_report_sha256": sha(
                "REPORT_2026-08-14_run22-final-freeze-release-qualification.md"),
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
