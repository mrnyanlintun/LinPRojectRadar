"""
RUN 30. THE SUPERSEDING PRODUCTION-TREE FREEZE.

WHY A SUCCESSOR RATHER THAN A REGENERATION, for the fifth time in this chain and for exactly the
same reason. A baseline rewritten in place agrees with production by construction and can never
catch an undeclared edit. RUN29_CLOSURE_FREEZE_2026-08-16.json is therefore NOT touched: it stays
exactly as the Run-29 closure wrote it, still verifies against its own companion .sha256, and this
record names it as its parent and carries its digest.

TWO STAGES, for the same reason every freeze in this chain has two. The manifest cannot contain
its own hash or the commit that lands it, so stage 1 writes the JSON with both fields null and
stage 2 (`--finalise`, run from the commit that ships) writes the companion .sha256.
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

import participant_packages as PP                              # noqa: E402
import production_tree as pt                                   # noqa: E402
import synthetic_packages as SP                                # noqa: E402

RELEASE_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-16-RUN30-CANONICAL-CAT6-7-V15-1"
PARENT_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-16-RUN29-CLOSURE-V14-1"
STAGE1 = ROOT / "research" / "freeze" / "RUN30_CANONICAL_CAT6_7_FREEZE_2026-08-16.json"
STAGE2 = STAGE1.with_suffix(".sha256")
PARENT_FREEZE = "research/freeze/RUN29_CLOSURE_FREEZE_2026-08-16.json"
PARENT_FREEZE_STAGE2 = "research/freeze/RUN29_CLOSURE_FREEZE_2026-08-16.sha256"
REPORT = "REPORT_2026-08-16_run30-cat6-7-canonical-remediation-v15.md"

#: The production files this run changed, and who already declares each.
RUN30_CHANGED = {
    "server/app/simulation/models_gov.py": (
        "declared by Run 20",
        "THE THREE CATEGORY-6 COMPARISON ENSEMBLES. B1.2, B1.3 and B1.4 stopped voting the whole "
        "simulation signal array -- transformations of the same four assembled arms, which the "
        "supplied contract states are not independent project facts -- and started synthesising "
        "the independent governed signals with duplicate lineage collapsed. B1.2 abstains "
        "without a governed weighting policy; B1.3 counts one vote per independent body with an "
        "explicit tie and quorum policy; B1.4 is the frozen Worst-2 mean statistic and asserts "
        "no traffic-light boundary. B2.1 Dempster-Shafer in the same file is UNTOUCHED, so Run "
        "20 cycle 7's same-lineage fix is preserved."),
    "server/app/project_data.py": (
        "declared by Run 29",
        "the governed intake vocabulary reads the v5 structure map as well, so the nineteen "
        "Category-6 and -7 structures are writable through the same append-only, "
        "period-effective store every other structure uses rather than describable only in a "
        "test."),
    "server/app/simulation/models.py": (
        "declared by Run 28",
        "the analytical stamp moves to sim-2026.08-v15, with v14 named as superseded and the "
        "history appended to rather than overwritten."),
}


def sha(rel: str) -> str | None:
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def build() -> None:
    from app.simulation import registry as R                                  # noqa: E402
    from app.simulation.models import (                                       # noqa: E402
        SIMULATION_VERSION, SIMULATION_VERSION_HISTORY, SIMULATION_VERSION_SUPERSEDED,
    )
    from app.simulation.canonical_v5 import QUANTUM_ARCHIVE, V5_STRUCTURE_KEYS  # noqa: E402

    prod = pt.walk_production()
    auth = pt.walk_production(None, pt.AUTHORITY_ROOTS)

    doc = {
        "release_identifier": RELEASE_ID,
        "supersedes": PARENT_ID,
        "supersedes_manifest": PARENT_FREEZE,
        "supersedes_manifest_sha256": sha(PARENT_FREEZE),
        "supersedes_manifest_stage2": PARENT_FREEZE_STAGE2,
        "supersedes_manifest_stage2_sha256": sha(PARENT_FREEZE_STAGE2),
        "supersedes_note":
            "the Run-29 closure freeze and every freeze behind it are preserved UNCHANGED as the "
            "historical record of those releases and still verify against their own companion "
            ".sha256 files. This one supersedes, it does not rewrite.",
        "release_date": dt.date(2026, 8, 16).isoformat(),
        "generated_by": "server/tools/build_run30_freeze.py",
        "reason":
            "implement the supplied Category-6 and Category-7 supervisory contracts: synthesise "
            "governed signals rather than the registered module array, supply the nineteen "
            "epistemic and decision structures those methods are defined on, remove the "
            "crisp-KPI proxies from the canonical layer, and abstain wherever a project does not "
            "possess the defining structure.",
        "scope_authority":
            "owner supervisory method contract of 2026-08-16 for Run 30, Categories 6 and 7 "
            "only. Categories 8 to 10 and Portfolio Health are out of scope and untouched.",

        "version_boundary": {
            "new_line": SIMULATION_VERSION,
            "superseded_line": SIMULATION_VERSION_SUPERSEDED,
            "line_moved_by_this_run": True,
            "why_it_moved":
                "a stamp identifies EXECUTABLE ANALYTICAL BEHAVIOUR, and this run changed it. "
                "Proved by execution rather than asserted: the v14 analytical package is "
                "extracted from git object ac7c011, imported, and run beside the current one on "
                "identical assembled packages. On identical adverse evidence B1.4 reported Red "
                "beside a three-module array and Yellow beside a sixty-three-module array under "
                "v14, and reports the same Worst-2 mean of 3.0 in both under v15; B1.2 reported "
                "Red from four unsourced weight literals under v14 and abstains under v15; B1.3 "
                "counted sixty-six voters and reported Green under v14 and counts two "
                "independent bodies and reports Red under v15.",
            "proof": "server/tools/test_run30_version_boundary.py",
            "scope_stated_honestly":
                "that suite proves three divergences on identical input, which is more than a "
                "version boundary needs. It does not claim to enumerate every divergence.",
            "history_preserved": list(SIMULATION_VERSION_HISTORY),
            "history_is_append_only":
                "the tuple recorded at commit ac7c011 is asserted to be a strict PREFIX of the "
                "tuple now, read out of git rather than out of a note, and to have grown by "
                "exactly the one stamp this run is authorised to add.",
        },

        "self_reference_note":
            "manifest_sha256 and final_commit are null BY CONSTRUCTION; both are recorded in the "
            "companion .sha256 file written by the finalisation commit.",
        "manifest_sha256": None,
        "final_commit": None,
        "starting_commit": "ac7c011996dc60ed4fea1e068dead945036dc821",
        "stage1_parent_commit": git("rev-parse", "HEAD"),
        "stage1_repository_tree_hash": git("rev-parse", "HEAD^{tree}"),

        "production_files_changed": [
            {"path": p, "sha256": sha(p), "already_declared_by": who, "why": why}
            for p, (who, why) in sorted(RUN30_CHANGED.items())
        ],
        "production_files_created": [
            {"path": "server/app/simulation/canonical_v5.py",
             "sha256": sha("server/app/simulation/canonical_v5.py"),
             "declared_by": "server/tools/run30_production_changes.py "
                            "RUN30_NEW_PRODUCTION_FILES",
             "why": "the v5 canonical method layer for Categories 6 and 7"},
        ],
        "declared_changes_note":
            "A NEW DECLARED-CHANGES MANIFEST WAS WRITTEN, server/tools/run30_production_changes.py, "
            "and its changed-file list is EMPTY, which is the guard working rather than a gap. "
            "The one baseline file this run changed, models_gov.py, is already declared by Run "
            "20; project_data.py is already declared by Run 29 and is re-declared only on the "
            "post-baseline list it belongs to; models.py is already declared by Run 28. No path "
            "may appear in two manifests, because one change is never counted twice. The new "
            "production file canonical_v5.py is declared on this run's own new-file list, which "
            "is the direction the byte comparison structurally cannot reach.",

        "production_surface": {
            "discovery": "walked from the deployed roots in server/tools/production_tree.py",
            "file_count": len(prod),
            "manifest_file": "code_audit/run30_production_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(),
            "parent_manifest_file": "code_audit/run29_closure_production_tree.sha256",
            "parent_manifest_sha256": hashlib.sha256(
                (ROOT / "code_audit"
                 / "run29_closure_production_tree.sha256").read_bytes()).hexdigest(),
            "files_added_since_parent": 1,
            "files_removed_since_parent": 0,
            "files_changed_since_parent": sorted(RUN30_CHANGED),
            "untracked_production_files": sorted(
                rel for rel, _d, _s, tracked in prod if not tracked),
            "files": [{"path": rel, "sha256": digest, "bytes": size, "git_tracked": tracked}
                      for rel, digest, size, tracked in prod],
        },

        "scope": {
            "record": "code_audit/run30_cat6_7_scope.csv",
            "record_sha256": sha("code_audit/run30_cat6_7_scope.csv"),
            "targets": 24,
            "category_6": 4,
            "category_7": 20,
            "derived_from":
                "code_audit/run20_cycle12_100_reaudit.csv filtered to categories 6 and 7, "
                "mechanically, by server/tools/build_run30_artifacts.py. Not transcribed.",
        },

        "supply_path_reconciliation": {
            "record": "code_audit/run30_supply_path_reconciliation.csv",
            "record_sha256": sha("code_audit/run30_supply_path_reconciliation.csv"),
            "structures": len(set(V5_STRUCTURE_KEYS.values())),
            "reasonably_supplyable_structures_with_no_production_path": 0,
            "intake": "server/app/writes.py saveprojectdata -> server/app/project_data.py, whose "
                      "vocabulary is the union of the canonical, v3, v4 and v5 structure maps",
        },

        "real_corpus_reconciliation": {
            "record": "code_audit/run30_real_corpus_structure_reconciliation.csv",
            "record_sha256": sha("code_audit/run30_real_corpus_structure_reconciliation.csv"),
            "corpus_present_but_unwired": 0,
            "reconciled_individually":
                "each of the twenty-four rows states its own case against the extraction "
                "registry rather than resting on one blanket sentence, because Run 29 proved a "
                "blanket 'none are populated' can hide a wiring gap. Three rows are POSITIVE: "
                "the assembled arms Category 6 synthesises are in the corpus and do reach their "
                "modules.",
        },

        "closure_table": {
            "record": "code_audit/run30_cat6_7_final_closure.csv",
            "record_sha256": sha("code_audit/run30_cat6_7_final_closure.csv"),
            "rows": 24,
            "regenerated_from": "the registry and code_audit/run30_cat6_7_scope.csv, not by hand",
            "unaccounted": 0,
        },

        "non_vacuity": {
            "record": "code_audit/run30_fault_injection.csv",
            "record_sha256": sha("code_audit/run30_fault_injection.csv"),
            "guard": "server/tools/test_run30_non_vacuity.py",
            "faults_mandated": 39,
            "faults_proven_red_then_green": 39,
            "injection_not_applied": 0,
            "method":
                "each fault replaces a production function or constant with a mutant that "
                "reintroduces the named defect; the injection is CONFIRMED APPLIED by re-reading "
                "the attribute off the module; the guard must go red for the intended reason, "
                "with both probe values recorded; then restored and observed green. A crash is "
                "reported as a crash and never counted as red.",
        },

        "decision_ranking_oracles": {
            "record": "code_audit/run30_decision_ranking_oracles.csv",
            "record_sha256": sha("code_audit/run30_decision_ranking_oracles.csv"),
            "benchmark_class": "HAND_DERIVED_CANONICAL_FIXTURE",
            "not_published": "neither benchmark is taken from a published worked example and "
                             "neither is presented as one",
            "independent_reference": "server/tools/run30/reference_mcdm.py, which imports "
                                     "nothing from app",
        },

        "blocked_operators": {
            "karnik_mendel_type_reduction":
                "NOT FROZEN in the supervisory artifacts. "
                "research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md "
                "cites it by DOI at line 341 and asks only that a centroid type reduction 'if' "
                "used be verified (line 2152). A citation is not a formulation, so B2.13 "
                "implements the interval type-2 membership and footprint of uncertainty and "
                "leaves type reduction explicitly blocked. Midpoint averaging is not used.",
            "rimer_er_multi_rule_aggregation":
                "NOT FROZEN. The same specification cites RIMER by DOI at line 338 and asks for "
                "testing 'for the selected ER formulation' without selecting one, so B2.8 "
                "implements the rule structure and the single fully activated rule and refuses "
                "multi-rule aggregation.",
            "z_number_reduction":
                "NOT FROZEN. B2.5 implements representation and provenance only.",
            "plithogenic_operator":
                "NOT FROZEN. B2.7 remains disabled future research and no operator is chosen.",
        },

        "quantum_archive": dict(QUANTUM_ARCHIVE),

        "disabled_and_archived": {
            "B2.7_plithogenic": {"in_registry_disabled_concept_only":
                                 "B2.7" in R.DISABLED_CONCEPT_ONLY,
                                 "operational": False},
            "B2.9_quantum": {"in_registry_disabled_concept_only":
                             "B2.9" in R.DISABLED_CONCEPT_ONLY,
                             "operational": False},
            "B2.20_hypersoft": {"laboratory_only": True, "operational": False,
                                "note": "the canonical laboratory function returns "
                                        "operational=False on a COMPLETE structure as well as an "
                                        "incomplete one, so completeness cannot become "
                                        "activation"},
        },

        "synthetic_package_chain": {
            "current": SP.CURRENT.identifier,
            "current_record": SP.CURRENT.record,
            "current_record_sha256": sha(SP.CURRENT.record) if SP.CURRENT.record else None,
            "chain": [{"identifier": s.identifier, "root": s.root, "record": s.record,
                       "record_sha256": sha(s.record) if s.record else None,
                       "current": s.current}
                      for s in SP.SYNTHETIC_PACKAGES],
            "successor_created_by_this_run": False,
            "why_not":
                "section 15 requires an in-scope fixture that encodes the OLD PROXY to be "
                "replaced now. Every Category-6/7 fixture in the package was inspected and none "
                "does. The only Category-7 fixture the package carries is B2.19 CRITIC-TOPSIS, "
                "and its structure is already a real alternatives-by-criteria decision problem "
                "(package_B_reference_training_decisions/B3_decision_optimization: "
                "alternative_criteria_matrix.csv, criteria.csv, ground_truth_decisions.csv), "
                "which is exactly what the supplied contract requires and is not a proxy. "
                "Creating an empty successor to satisfy the letter of the section would put a "
                "package identifier on a set of bytes nobody changed, which is the masquerade "
                "this chain's own rule 4 forbids. The Run-30 canonical fixtures live in "
                "server/tools/run30/fixtures_cat67.py, are test-only, and every one carries "
                "data_origin = SYNTHETIC_RESEARCH_FIXTURE and not_for_empirical_validation.",
            "predecessors_unchanged": True,
            "masquerade_rule":
                "no file outside a predecessor's own record may carry that predecessor's "
                "programme version.",
        },

        "participant_package_chain": {
            "current": PP.CURRENT.identifier,
            "current_record": PP.CURRENT.record,
            "current_record_sha256": sha(PP.CURRENT.record),
            "chain": [{"identifier": p.identifier, "record": p.record,
                       "record_sha256": sha(p.record), "source_commit": p.source_commit}
                      for p in PP.PARTICIPANT_PACKAGES],
            "unchanged_by_this_run": True,
            "why":
                "the three Category-6 comparison ensembles are ADVISORY_ONLY and were already "
                "off the participant operational surface; Quantum and Plithogenic were already "
                "disabled and stay disabled; no registry qualifier was removed and no served "
                "participant evidence object changed. No participant-facing byte moved, so v4 "
                "stands and no successor was created.",
            "experimental_sequence_unchanged": True,
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
            "material_cost_variance_canonical_id": "A3.4",
            "material_cost_variance_enabled": "A3.4" not in R.DISABLED_MODULES,
            "registry_sha256": sha("server/app/simulation/registry.py"),
            "unchanged_by_this_run": True,
        },

        "not_closed_by_this_run": {
            "category_9_qualification_gate":
                "RUN 31 OWNS IT AND RUN 30 DID NOT TOUCH IT. Every Category-6/7 input still "
                "carries signal_qualification = 'unqualified' and the CATEGORY_9_DEVIATION "
                "sentence. No LINEAGE finding is marked resolved. The Run-17 register entry "
                "ARCH/raw-bypass is deliberately KEPT and its probe was moved onto a module that "
                "still computes, so an unrelated abstention cannot answer it.",
            "calibration":
                "no status band was introduced for any Category-6 or -7 quantity, and the "
                "Worst-2 mean statistic asserts none. Run 33 owns it.",
            "parsimony":
                "no fuzzy-family consolidation was carried out and none is authorised here. "
                "Run 33 owns final parsimony and value assessment.",
            "category_placement":
                "MARCOS and CRITIC-TOPSIS keep stable identities in Category 7. Run 32 owns "
                "operational Category-10 placement.",
            "operational_activation":
                "no Category-7 method was activated. The nineteen structures are supplyable and "
                "unsupplied on the real corpus, so the modules abstain, which is the correct "
                "answer and not a gap.",
        },

        "report": REPORT,
        "report_present_in_tree": (ROOT / REPORT).is_file(),
        "report_sha256": sha(REPORT),
    }

    STAGE1.parent.mkdir(parents=True, exist_ok=True)
    STAGE1.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {STAGE1.relative_to(ROOT)}")
    print(f"  production files: {len(prod)}  changed since parent: {len(RUN30_CHANGED)}")
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
