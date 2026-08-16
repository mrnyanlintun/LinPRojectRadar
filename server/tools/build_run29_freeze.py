"""
RUN 29. THE SUPERSEDING PRODUCTION-TREE FREEZE for the Category 4 and 5 canonical remediation.

WHY A SUCCESSOR RATHER THAN A REGENERATION. The whole distinction the freeze rests on is that a
baseline rewritten in place agrees with production by construction and can never catch an
undeclared edit. So the Run-28 closure freeze is NOT touched: it stays exactly as that release
wrote it, still verifies against its own companion .sha256, and this record names it as its
parent and carries its digest. Repointing, never editing.

TWO STAGES, for the same reason every freeze in this chain has two. The manifest cannot contain
its own hash or the commit that lands it, so stage 1 writes the JSON with both fields null and
stage 2 (`--finalise`, run from the commit that ships) writes the companion .sha256 carrying the
digest and the commit.
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
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import production_tree as pt                                   # noqa: E402
import participant_packages as PP                              # noqa: E402
import run29_production_changes as _R29                        # noqa: E402

RELEASE_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-16-RUN29-CANONICAL-CAT4-5-V13-1"
PARENT_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN28-CLOSURE-V12-2"
STAGE1 = ROOT / "research" / "freeze" / "RUN29_CANONICAL_CAT4_5_FREEZE_2026-08-16.json"
STAGE2 = STAGE1.with_suffix(".sha256")
#: THE REPORT COULD NOT BE WRITTEN AS ITS OWN FILE in the session that produced this run: the
#: harness refused to create it. Per the run instruction covering exactly that case the report is
#: reproduced VERBATIM AND IN FULL at the end of T6_HANDOFF.md, and the supervising session is to
#: land it under the name below unchanged. Both are recorded here so the freeze does not claim a
#: file that is not in the tree.
REPORT = "REPORT_2026-08-16_run29-cat4-5-canonical-remediation-v13.md"
REPORT_CARRIER = "T6_HANDOFF.md"
PARENT_FREEZE = "research/freeze/RUN28_PARTICIPANT_V3_FREEZE_2026-08-14.json"


def sha(rel: str) -> str | None:
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def build() -> None:
    from app.simulation import registry as R                                  # noqa: E402
    from app.simulation.canonical_v4 import V4_STRUCTURE_KEYS                 # noqa: E402
    from app.simulation.models import (                                       # noqa: E402
        SIMULATION_VERSION, SIMULATION_VERSION_HISTORY,
    )

    prod = pt.walk_production()
    auth = pt.walk_production(None, pt.AUTHORITY_ROOTS)
    changed = {p: f"{k}: {why}"
               for k, (_a, p, why) in sorted(
                   _R29.RUN29_CHANGES_TO_POST_BASELINE_FILES.items())}

    doc = {
        "release_identifier": RELEASE_ID,
        "supersedes": PARENT_ID,
        "supersedes_manifest": PARENT_FREEZE,
        "supersedes_manifest_sha256": sha(PARENT_FREEZE),
        "supersedes_note":
            "the Run-28 closure freeze and every freeze behind it are preserved unchanged as the "
            "historical record of those releases and still verify against their own companion "
            ".sha256 files. This one supersedes, it does not rewrite. It exists because Run 29 "
            "moved the analytical line to sim-2026.08-v13, replaced sixteen Category-4 and "
            "Category-5 computations with the canonical methods the owner's supplied contract "
            "states, created the v4 canonical layer, and changed eight further production files, "
            "so its parent no longer describes the executable baseline.",
        "release_date": dt.date(2026, 8, 16).isoformat(),
        "generated_by": "server/tools/build_run29_freeze.py",
        "reason":
            "implement the supplied Category 4 and Category 5 canonical contracts: supply the "
            "seventeen governed evidence and model structures those eighteen methods are defined "
            "on, build the production intake for every one of them, and abstain where a project "
            "does not possess them.",
        "scope_authority":
            "owner supervisory method contract of 2026-08-16 for Run 29. The scientific theory "
            "is SUPPLIED by that contract; this run implements it and does not review it.",

        "version_boundary": {
            "new_line": SIMULATION_VERSION,
            "superseded_line": "sim-2026.08-v12",
            "line_moved_by_this_run": True,
            "why_it_moved":
                "a stamp identifies EXECUTABLE ANALYTICAL BEHAVIOUR. Proved by execution rather "
                "than asserted: the v12 analytical package is extracted from git object 01e943e, "
                "imported and run beside the current one on identical governed inputs. On a "
                "queue model declaring an arrival rate of two against a service rate of three, "
                "v12 ABSTAINS and the current line computes rho = 2/3, L = 2, W = 1. On a "
                "document risk score with a request count and a change count, v12 emits a "
                "dispute escalation index of 0.5 and the current line REFUSES. On a dependency "
                "matrix, v12 abstains unconditionally and the current line propagates it.",
            "proof": "server/tools/test_run29_version_boundary.py",
            "history_preserved": list(SIMULATION_VERSION_HISTORY),
            "history_is_append_only":
                "the tuple recorded at commit 01e943e is asserted to be a strict PREFIX of the "
                "tuple now, read out of git rather than out of a note, so a run that overwrote a "
                "stamp instead of appending one is detectable.",
        },

        "self_reference_note":
            "manifest_sha256 and final_commit are null BY CONSTRUCTION; both are recorded in the "
            "companion .sha256 file written by the finalisation commit.",
        "manifest_sha256": None,
        "final_commit": None,
        "starting_commit": "01e943ef71689c468dd343695fbc89901bc02964",
        "stage1_parent_commit": git("rev-parse", "HEAD"),
        "stage1_repository_tree_hash": git("rev-parse", "HEAD^{tree}"),

        "production_files_changed": [
            {"path": p, "sha256": sha(p), "why": why} for p, why in sorted(changed.items())
        ],
        "production_files_changed_note":
            "the four files Run 29 changed that the Run-20 byte freeze DOES cover -- "
            "models_doc.py, registry.py, models.py and documents.py -- are declared by Runs 20 "
            "and 28 in their own manifests, because no path may appear in two and one change is "
            "never counted twice. The list above is the files created after that freeze was "
            "taken, which the byte comparison structurally cannot reach.",
        "production_files_created": [
            {"path": p, "sha256": sha(p), "why": why}
            for p, why in sorted(_R29.RUN29_NEW_PRODUCTION_FILES.items())
        ],

        "production_surface": {
            "discovery": "walked from the deployed roots in server/tools/production_tree.py",
            "file_count": len(prod),
            "manifest_file": "code_audit/run29_production_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(),
            "parent_manifest_file": "code_audit/run28_closure_production_tree.sha256",
            "parent_manifest_sha256": hashlib.sha256(
                (ROOT / "code_audit"
                 / "run28_closure_production_tree.sha256").read_bytes()).hexdigest(),
            "untracked_production_files": sorted(
                rel for rel, _d, _s, tracked in prod if not tracked),
            "untracked_note":
                "the blind spot the Run-28 closure found and closed: a guard reasoning about "
                "production change through git diff cannot see a file never added to the index. "
                "canonical_v4.py was added to the index in this run and the walk reports tracked "
                "state as an attribute, which test_run22_production_tree_completeness.py asserts.",
            "files": [{"path": rel, "sha256": digest, "bytes": size, "git_tracked": tracked}
                      for rel, digest, size, tracked in prod],
        },

        "canonical_layer": {
            "file": "server/app/simulation/canonical_v4.py",
            "sha256": sha("server/app/simulation/canonical_v4.py"),
            "module_to_key_entries": len(V4_STRUCTURE_KEYS),
            "distinct_structure_keys": len(set(V4_STRUCTURE_KEYS.values())),
            "shared_key_note":
                "eighteen entries over seventeen keys, because one sensitivity model serves both "
                "A5.2 and A5.3. That sharing IS the parsimony decision the contract makes: 5.3 "
                "ranks what 5.2 computed and creates no second evidence body.",
            "intake_path":
                "server/app/writes.py::w_saveprojectdata -> server/app/project_data.py -> "
                "server/app/documents.py::run_and_store",
            "supply_path_reconciliation": "code_audit/run29_supply_path_reconciliation.csv",
            "supply_path_reconciliation_sha256": sha(
                "code_audit/run29_supply_path_reconciliation.csv"),
            "supply_path_guard": "server/tools/test_run29_supply_path_guard.py",
            "reasonably_supplyable_structures_with_no_production_path": 0,
            "scope": "code_audit/run29_cat4_5_scope.csv",
            "scope_sha256": sha("code_audit/run29_cat4_5_scope.csv"),
            "oracles": "server/tools/test_run29_canonical_oracles.py",
            "non_vacuity_campaign": "code_audit/run29_fault_injection.csv",
            "non_vacuity_campaign_sha256": sha("code_audit/run29_fault_injection.csv"),
        },

        "participant_package_chain": {
            "current": PP.CURRENT.identifier,
            "current_record": PP.CURRENT.record,
            "current_record_sha256": sha(PP.CURRENT.record),
            "chain": [{"identifier": p.identifier, "record": p.record,
                       "record_sha256": sha(p.record), "source_commit": p.source_commit}
                      for p in PP.PARTICIPANT_PACKAGES],
            "declaration": "server/tools/participant_packages.py",
            "guard": "server/tools/test_run28_participant_packages.py",
            "why_v4":
                "Run 29 removed six proxy qualifiers from the registry because the six modules "
                "they described now carry out their canonical methods, and the defensibility "
                "evidence object served to participants is GENERATED from the registry. ONE "
                "package file moved and the change is the DELETION of six sentences that would "
                "now be false.",
            "identity_rule":
                "EXACTLY ONE record in the chain may describe the live tree and it must be the "
                "one declared current. v3 is pinned to commit 01e943e, whose blobs it describes, "
                "and its bytes in the tree are asserted byte-identical to that commit's, so this "
                "run created a successor rather than rewriting a predecessor.",
            "protocol_unchanged":
                "every file carrying a step of the participant sequence, the randomization, the "
                "reveal timing, the lock enforcement, the server contract, the append-only "
                "record or the treatment logic is byte-identical across v2, v3 and v4.",
        },

        "scientific_authority": {
            "file_count": len(auth),
            "manifest_file": "code_audit/run22_authority_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(None, pt.AUTHORITY_ROOTS),
            "unchanged_by_this_run": True,
            "note": "no rename was authorised or made in Run 29.",
        },

        "activation_and_voting": {
            "derivation": "read from server/app/simulation/registry.py at freeze time",
            "voting_modules": sorted(R.CORE_VOTING_MODULES),
            "voting_count": len(R.CORE_VOTING_MODULES),
            "material_cost_variance_canonical_id": "A3.4",
            "material_cost_variance_enabled": "A3.4" not in R.DISABLED_MODULES,
            "concept_only_disabled": sorted(R.DISABLED_CONCEPT_ONLY),
            "registry_sha256": sha("server/app/simulation/registry.py"),
        },

        "not_closed_by_this_run": {
            "category_9_qualification_gate":
                "UNIMPLEMENTED and disclosed by production itself: signal_package.py records "
                "SIGNAL_QUALIFICATION = 'unqualified' and CATEGORY_9_DEVIATION. Run 31 owns it. "
                "Run 29 preserved the provenance that gate will need and closed no LINEAGE "
                "finding.",
            "calibration":
                "no status band was introduced for any Category 4 or 5 quantity. Sixteen of the "
                "eighteen assert no colour and carry calibration pending; A4.2 and A4.3 keep the "
                "ladders they always carried, which are recorded as uncited. Run 33 owns it.",
            "empirical_validation":
                "A4.1's extraction precision and recall, and A4.10's conflict-detection "
                "precision and recall, are PENDING RUN 33. No labelled corpus exists in this "
                "repository and none was invented.",
            "orphan_field_document_types":
                "the Environmental, Quality and Safety report package Run 27 established is "
                "explicitly excluded from Run 29 by the owner's section 2 and belongs to Run 31.",
        },

        "report": REPORT,
        "report_present_in_tree": (ROOT / REPORT).is_file(),
        "report_sha256": sha(REPORT),
        "report_carrier": REPORT_CARRIER,
        "report_carrier_sha256": sha(REPORT_CARRIER),
        "report_note":
            "the harness that produced this run refused to create the report as its own file. The "
            "report is reproduced VERBATIM AND IN FULL at the end of T6_HANDOFF.md, whose digest "
            "is recorded above, and the supervising session is to land it under the report name "
            "unchanged. report_present_in_tree records honestly whether that has happened.",
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
