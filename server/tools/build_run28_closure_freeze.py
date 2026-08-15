#!/usr/bin/env python3
"""
RUN 28 CLOSURE. THE SUPERSEDING FREEZE MANIFEST.

WHY THIS EXISTS. The owner's closure instruction requires Run 28's own defects closed before
Run 29, and three of them change production: the two approved Category-1 renames were declared in
the registry and never propagated to the surfaces a reader is shown; the A1.1 naming drift was
recorded and left open; and the twenty abstaining Category 1 to 3 modules had no intake path
behind them, because twenty-one of the twenty-three v3 structure keys were written by no
production code at all. Fourteen production files moved and one was created.

The Run-28 freeze, OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN28-CANONICAL-CAT1-3-V11-1,
therefore no longer describes the executable baseline. It is NOT rewritten: it stays exactly as
Run 28 wrote it, as that release's historical record, and this document supersedes it by naming
it as its parent and carrying its digest. Every freeze behind it is likewise untouched.

THE ANALYTICAL LINE MOVES TO sim-2026.08-v12, AND THE FIRST DRAFT OF THIS FILE ARGUED THE
OPPOSITE. It said the line should stay at v11 because "no module's arithmetic, band, boundary or
reported quantity changed". That reading of what a stamp identifies was too narrow, and the
counter-example is mechanical: on one identical governed input -- a cost risk model with three
risk events and no stated dependence policy -- canonical_v3.py as it shipped at commit 0e0dfbd
emits an eightieth-percentile total cost of 1200.0, and canonical_v3.py after the closure refuses
and reports nothing. server/tools/test_run28_version_boundary.py extracts the v11 file from that
git object, EXECUTES it beside the current one and asserts the divergence. Two further changes
move what the layer emits: the governed project-data intake lets a module that could only ever
abstain compute, and a stored row gains a key recording which structures the modules were given.

THE PARTICIPANT PACKAGE DOES MOVE, and that is the one thing here the owner had to authorise
explicitly. Run 28 refused to rename assets/js/taxonomy.js because it is the participant ledger's
own name source inside a checksummed package and the study is mid-sequence. The closure
instruction reverses that, requires the current surface to be consistent, and permits a successor
package record with the predecessor preserved. og-participant-2026.08-v2 is that successor;
code_audit/run12_participant_package_checksums.sha256 is untouched.

The same two-stage construction every freeze since Run 22 has used, for the same reason: a
manifest cannot contain its own SHA-256, nor the hash of the commit that introduces it.

    STAGE 1  writes research/freeze/RUN28_CLOSURE_FREEZE_2026-08-14.json with manifest_sha256
             and final_commit null. That file is committed.
    STAGE 2  --finalise writes the companion .sha256 with the digest of the stage-1 file and the
             merged-main commit that carried it.
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

RELEASE_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN28-CLOSURE-V12-1"
PARENT_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN28-CLOSURE-V11-2"
STAGE1 = ROOT / "research" / "freeze" / "RUN28_CLOSURE_V12_FREEZE_2026-08-14.json"
STAGE2 = STAGE1.with_suffix(".sha256")
REPORT = "REPORT_2026-08-14_run28-closure.md"
PARENT_FREEZE = "research/freeze/RUN28_CLOSURE_FREEZE_2026-08-14.json"


def sha(rel: str) -> str | None:
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def build() -> None:
    from app.simulation import registry as R  # noqa: E402
    from app.simulation.models import SIMULATION_VERSION, SIMULATION_VERSION_HISTORY  # noqa: E402

    prod = pt.walk_production()
    auth = pt.walk_production(None, pt.AUTHORITY_ROOTS)
    changed = {p: f"{mid}: {why}"
               for mid, (_auth, p, why) in sorted(_R28.RUN28_PRODUCTION_CHANGES.items())}

    doc = {
        "release_identifier": RELEASE_ID,
        "supersedes": PARENT_ID,
        "supersedes_manifest": PARENT_FREEZE,
        "supersedes_manifest_sha256": sha(PARENT_FREEZE),
        "grandparent_release":
            "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN28-CANONICAL-CAT1-3-V11-1",
        "grandparent_manifest":
            "research/freeze/RUN28_CANONICAL_CAT1_3_FREEZE_2026-08-14.json",
        "grandparent_manifest_sha256": sha(
            "research/freeze/RUN28_CANONICAL_CAT1_3_FREEZE_2026-08-14.json"),
        "supersedes_note":
            "the first closure freeze RUN28-CLOSURE-V11-2, the Run-28 freeze behind it and "
            "every freeze behind that are preserved unchanged as the historical record of those "
            "releases; RUN28_CLOSURE_FREEZE_2026-08-14.json still verifies against its own "
            "companion .sha256. This one supersedes, it does not rewrite. It exists because the "
            "second closure pass moved the analytical line to sim-2026.08-v12, renamed A1.1 in "
            "the naming authority on the owner's decision, and changed eleven production files "
            "again, so its parent no longer describes the executable baseline.",
        "release_date": dt.date(2026, 8, 14).isoformat(),
        "generated_by": "server/tools/build_run28_closure_freeze.py",
        "reason":
            "close the five defects the owner named in Run 28 before Run 29: re-verify on the "
            "exact final head; propagate the two approved Category-1 renames to every current "
            "surface and close the A1.1 drift to the name the designated authority records; hold "
            "A2.7 to repeated forecasts for a stable milestone identity; enumerate the protected "
            "production surface independently of git tracked status; and BUILD the intake path "
            "the twenty abstentions rest on rather than describing it.",
        "version_boundary": {
            "new_line": SIMULATION_VERSION,
            "superseded_line": "sim-2026.08-v11",
            "line_moved_by_this_closure": True,
            "why_it_moved":
                "a stamp identifies EXECUTABLE ANALYTICAL BEHAVIOUR, and this layer's behaviour "
                "is not v11's. Proved by execution rather than asserted: on one identical "
                "governed input -- a cost risk model with three risk events and no stated "
                "dependence policy -- the v11 file extracted from git object 0e0dfbd emits "
                "p80_total_cost = 1200.0 and the current file refuses. Two further changes move "
                "what the layer emits for some input: the governed project-data intake means a "
                "module whose structure no production code could write, and which could "
                "therefore only ever abstain, can now compute; and a stored row gains a "
                "projectDataStructures key that v11 rows do not carry.",
            "first_draft_judgement_corrected":
                "the first closure pass held the line at v11 on the grounds that no arithmetic, "
                "band, boundary or reported quantity moved. That was too narrow and is recorded "
                "here rather than quietly replaced.",
            "proof": "server/tools/test_run28_version_boundary.py",
            "history_preserved": list(SIMULATION_VERSION_HISTORY),
            "history_is_append_only":
                "the tuple recorded at commit 0e0dfbd is asserted to be a strict PREFIX of the "
                "tuple now, read out of git rather than out of a note, so a run that overwrote a "
                "stamp instead of appending one is detectable.",
        },
        "self_reference_note":
            "manifest_sha256 and final_commit are null BY CONSTRUCTION; both are recorded in the "
            "companion .sha256 file written by the finalisation commit.",
        "manifest_sha256": None,
        "final_commit": None,
        "starting_commit": "0e0dfbd",
        "stage1_parent_commit": git("rev-parse", "HEAD"),
        "stage1_repository_tree_hash": git("rev-parse", "HEAD^{tree}"),

        "production_files_changed": [
            {"path": p, "sha256": sha(p), "why": why} for p, why in sorted(changed.items())
        ],

        "production_surface": {
            "discovery": "walked from the deployed roots in server/tools/production_tree.py",
            "file_count": len(prod),
            "manifest_file": "code_audit/run28_closure_production_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(),
            "parent_manifest_file": "code_audit/run28_production_tree.sha256",
            "parent_manifest_sha256": hashlib.sha256(
                (ROOT / "code_audit" / "run28_production_tree.sha256").read_bytes()).hexdigest(),
            "untracked_production_files": sorted(
                rel for rel, _d, _s, tracked in prod if not tracked),
            "untracked_note":
                "THE BLIND SPOT RUN 28 LEFT OPEN. A guard that reasons about production change "
                "through `git diff` cannot see a file that was never added to the index, and "
                "Run 28's canonical_v3.py was exactly that. The walk discovers names from the "
                "filesystem and reports tracked state as an attribute; "
                "test_run22_production_tree_completeness.py now ASSERTS that attribute, "
                "test_run8_retest_classify_27.py enumerates untracked paths alongside the diff, "
                "and this field records the answer at freeze time.",
            "files": [{"path": rel, "sha256": digest, "bytes": size, "git_tracked": tracked}
                      for rel, digest, size, tracked in prod],
        },

        "participant_package": {
            "identifier": "og-participant-2026.08-v2",
            "supersedes": "og-participant-2026.08-v1",
            "checksums": "code_audit/run28_closure_participant_package_checksums.sha256",
            "checksums_sha256": sha(
                "code_audit/run28_closure_participant_package_checksums.sha256"),
            "predecessor_checksums": "code_audit/run12_participant_package_checksums.sha256",
            "predecessor_checksums_sha256": sha(
                "code_audit/run12_participant_package_checksums.sha256"),
            "predecessor_preserved_unchanged": True,
            "why":
                "assets/js/taxonomy.js, the participant ledger's own name source, carries the two "
                "approved Category-1 renames and the A1.1 alignment. Run 28 refused this because "
                "the study is mid-sequence; the owner's closure instruction requires the current "
                "surface to be consistent and permits a successor record with the predecessor "
                "preserved.",
            "what_changed": "display strings only",
            "decision_sequence_unchanged":
                "preliminary, lock, reveal, final, lock. No experimental logic was touched.",
            "predecessor_record_was_already_stale":
                "REPORTED RATHER THAN QUIETLY CORRECTED. Fourteen package files already differed "
                "from the Run-12 record before this closure -- radar.css, detail.js, "
                "simulations.js, index.html and others, from Runs 21 to 26 -- so the successor "
                "records the bytes as they actually stand rather than only this closure's edits.",
        },

        "scientific_authority": {
            "file_count": len(auth),
            "manifest_file": "code_audit/run22_authority_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(None, pt.AUTHORITY_ROOTS),
            "unchanged_by_this_closure": True,
        },

        "activation_and_voting": {
            "derivation": "read from server/app/simulation/registry.py at freeze time",
            "voting_modules": sorted(R.CORE_VOTING_MODULES),
            "voting_count": len(R.CORE_VOTING_MODULES),
            "material_cost_variance_canonical_id": "A3.4",
            "material_cost_variance_enabled": "A3.4" not in R.DISABLED_MODULES,
            "concept_only_disabled": sorted(R.DISABLED_CONCEPT_ONLY),
            "registry_sha256": sha("server/app/simulation/registry.py"),
            "registry_unchanged_by_this_closure": True,
        },

        "closure_evidence": {
            "supply_path_closure": "code_audit/run28_supply_path_closure.csv",
            "supply_path_closure_sha256": sha("code_audit/run28_supply_path_closure.csv"),
            "operational_closure_28": "code_audit/run28_operational_closure_28.csv",
            "operational_closure_28_sha256": sha("code_audit/run28_operational_closure_28.csv"),
            "guard_suite": "server/tools/test_run28_closure.py",
            "non_vacuity_campaign": "code_audit/run28_closure_fault_injection.csv",
            "intake_path":
                "server/app/writes.py::w_saveprojectdata -> server/app/project_data.py -> "
                "server/app/documents.py::run_and_store",
            "structure_key_reconciliation":
                "code_audit/run28_v3_structure_key_reconciliation.csv",
            "structure_key_reconciliation_sha256": sha(
                "code_audit/run28_v3_structure_key_reconciliation.csv"),
            "structure_key_arithmetic":
                "the first closure pass reported 23 keys, 2 production-reachable and 19 exercised "
                "through the intake, and 19 + 2 = 21. The gap is a conflation: V3_STRUCTURE_KEYS "
                "holds 23 MODULE-TO-KEY ENTRIES over 18 DISTINCT KEYS, because one schedule "
                "network serves five Category-2 methods and one time-phased baseline serves two. "
                "Per entry: 19 need the intake and 4 do not -- A1.1 computes without its "
                "structure, A2.7 and A3.6 have theirs PRODUCED by document extraction rather than "
                "supplied, and A3.8 is registered disabled and never executed.",
            "participant_v1_preservation":
                "server/tools/test_run28_participant_v1_preservation.py",
            "participant_v1_git_object": "c44e3ced94a22a9def35fa5a2be3a2268fbed6bb",
            "participant_v1_note":
                "the live filesystem is NOT evidence for og-participant-2026.08-v1: fourteen of "
                "its seventy files had legitimately moved on before this closure. The package is "
                "reconstructed from the commit that wrote the Run-12 record, into an isolated "
                "temporary directory, and all seventy checksums are verified there. No "
                "historical file is restored into the application and the Run-12 record is not "
                "rewritten.",
            "a1_1_naming_conflict":
                "RESOLVED BY THE OWNER. The first closure pass found the authority recording "
                "`Monte Carlo EAC` against an owner prose name of `Monte Carlo EAC Forecast`, "
                "aligned the surfaces TO the authority, refused to edit the authority on the "
                "strength of a prose sentence, and reported the conflict as an owner decision. "
                "The owner decided: A1.1 IS `Monte Carlo EAC Forecast`, final, and the current "
                "naming authority is to be updated. p0-baseline/module_renumbering_map.csv line "
                "2 now records it, every generated surface was re-propagated from it, and the "
                "stale `owner_prose_alias` label in the production-contract fixture is "
                "reconciled: the decided name is canonical and the retired name is the "
                "backward-compatible alias. Current active naming conflicts for A1.1 = 0, "
                "asserted by a guard that fails if any current surface reintroduces the old "
                "name in a table, a heading, a node label or a sentence of prose. This is a "
                "THIRD rename beyond Run 28's two and it is explicitly authorised.",
            "report": REPORT,
            "report_present_in_tree": (ROOT / REPORT).is_file(),
            "report_sha256": sha(REPORT),
            "parent_report_sha256": sha(
                "REPORT_2026-08-14_run28-cat1-3-canonical-remediation-v3.md"),
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
