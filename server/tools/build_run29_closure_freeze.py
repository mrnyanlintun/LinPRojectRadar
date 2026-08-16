"""
RUN 29 CLOSURE. THE SUPERSEDING PRODUCTION-TREE FREEZE.

WHY A SUCCESSOR RATHER THAN A REGENERATION, for the fourth time in this chain and for exactly
the same reason. A baseline rewritten in place agrees with production by construction and can
never catch an undeclared edit. RUN29_CANONICAL_CAT4_5_FREEZE_2026-08-16.json is therefore NOT
touched: it stays exactly as Run 29 wrote it, still verifies against its own companion .sha256,
and this record names it as its parent and carries its digest.

THE ONE FIELD THAT COULD HAVE BEEN RECONCILED, AND THE CHOICE MADE. Run 29's stage-1 record
wrote `report_present_in_tree: false`, truthfully, because the harness that produced the run
could not create the report file and the report travelled in T6_HANDOFF.md. The supervising
session then landed it at its named path in commit 9cc6793, so the field is now stale. The
closure instruction permits reconciling it, at the price of re-taking that freeze's stage-2
companion. IT WAS NOT RECONCILED. Editing a sealed predecessor to make a historical statement
agree with a later world is precisely the move this whole chain exists to forbid, and the field
was TRUE OF THE TREE AT THE MOMENT THAT RECORD WAS TAKEN. The successor states the current fact
instead, in `parent_report_field_reconciliation` below, so nothing is hidden and no stage-2
companion had to be re-taken. The Run-29 stage-2 file and its digest are untouched and still
verify.

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

RELEASE_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-16-RUN29-CLOSURE-V14-1"
PARENT_ID = "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-16-RUN29-CANONICAL-CAT4-5-V13-1"
STAGE1 = ROOT / "research" / "freeze" / "RUN29_CLOSURE_FREEZE_2026-08-16.json"
STAGE2 = STAGE1.with_suffix(".sha256")
PARENT_FREEZE = "research/freeze/RUN29_CANONICAL_CAT4_5_FREEZE_2026-08-16.json"
PARENT_FREEZE_STAGE2 = "research/freeze/RUN29_CANONICAL_CAT4_5_FREEZE_2026-08-16.sha256"
REPORT = "REPORT_2026-08-16_run29-cat4-5-canonical-remediation-v13.md"

#: The four production files this closure changed. Every one is ALREADY DECLARED by an earlier
#: manifest, which is why the closure adds no declared-changes manifest of its own: no path may
#: appear in two, and one change is never counted twice.
CLOSURE_CHANGED = {
    "server/app/documents.py": (
        "declared by Run 28",
        "THE CORPUS-TO-STRUCTURE ASSEMBLY, which is the whole reason the line moved. Run 29 "
        "reported `real_corpus_populated = no` for all seventeen Category-4 and -5 structures. "
        "That one sentence covered two different cases and the closure decomposed it: sixteen "
        "are genuinely absent from the corpus, but `ncrExposureRecord` was not. The "
        "nonconformance log already yielded `ncrIssued` and the inspection report already "
        "yielded `itemsInspected`; both reached signalInputs and neither reached a module. The "
        "assembler builds the governed record from exactly those two extracted fields, records "
        "the derivation on the stored row, and fabricates no identity, date or severity."),
    "server/app/simulation/canonical_v4.py": (
        "declared by Run 29 as new production code",
        "THE COUNT FORM of `ncr_rate`, so a project whose evidence is a COUNT of nonconformances "
        "over a declared exposure gets a reading, while the quantities that genuinely require "
        "per-event detail -- severities, closure rate, open ages -- are reported ABSENT rather "
        "than invented, and `event_detail_available` says so on the result. Also the uniqueness "
        "enforcement in `_unique_ids`, which previously accepted the same identifier twice and "
        "would have counted one entry as two."),
    "server/app/simulation/models_doc.py": (
        "declared by Run 20",
        "the A4.4 runner carries the count form's fields through to the stored finding, "
        "including the honest `event_detail_available` flag, and tolerates the absent backlog "
        "quantities rather than treating their absence as a failure."),
    "server/app/simulation/models.py": (
        "declared by Run 28",
        "the analytical stamp moves to sim-2026.08-v14, with v13 named as superseded and the "
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
            "the Run-29 canonical freeze and every freeze behind it are preserved UNCHANGED as "
            "the historical record of those releases and still verify against their own "
            "companion .sha256 files. This one supersedes, it does not rewrite.",
        "release_date": dt.date(2026, 8, 16).isoformat(),
        "generated_by": "server/tools/build_run29_closure_freeze.py",
        "reason":
            "close the eight gaps the owner's Run-29 closure instruction names: re-take the "
            "complete suite on the true final head, replace the three stale synthetic fixtures "
            "with the canonical shapes the supplied contracts are defined on, decompose the "
            "too-broad real-corpus claim into genuinely-absent versus unwired-but-present and "
            "wire what was present, prove the scenario-modeling leakage guard, regenerate the "
            "eighteen-row closure table from the registry, settle the version identity by "
            "execution, and prove package preservation across all three chains.",
        "scope_authority":
            "owner supervisory closure instruction of 2026-08-16 for Run 29. This is Run 29's "
            "closure and not a new numbered run.",

        "parent_report_field_reconciliation": {
            "field": "report_present_in_tree",
            "value_in_parent_record": False,
            "value_now": (ROOT / REPORT).is_file(),
            "parent_record_edited": False,
            "parent_stage2_retaken": False,
            "why":
                "the parent's value was TRUE OF THE TREE WHEN THAT RECORD WAS TAKEN: the harness "
                "could not create the report file and the report travelled verbatim in "
                "T6_HANDOFF.md. The supervising session landed it at its named path in commit "
                "9cc6793. Reconciling the field would have meant editing a sealed predecessor to "
                "agree with a later world, which is the exact move this chain forbids, and would "
                "have required re-taking that freeze's stage-2 companion. The successor states "
                "the current fact here instead. Both records are true of their own moment.",
            "report": REPORT,
            "report_sha256": sha(REPORT),
        },

        "version_boundary": {
            "new_line": SIMULATION_VERSION,
            "superseded_line": SIMULATION_VERSION_SUPERSEDED,
            "line_moved_by_this_closure": True,
            "why_it_moved":
                "a stamp identifies EXECUTABLE ANALYTICAL BEHAVIOUR, and this closure changed "
                "it. Proved by execution rather than asserted: the v13 analytical package is "
                "extracted from git object 9cc6793, imported, and run beside the current one on "
                "the identical governed record production now assembles. On four nonconformances "
                "against one hundred inspections, v13 ABSTAINS -- it required a list of events, "
                "and a count extracted as a count is not a list -- and the current line reports "
                "the supplied contract's own 0.04. Same input, different emitted result. On a "
                "record carrying real nonconformance EVENTS both lines agree exactly, so this "
                "closure WIDENED what can be read rather than changing what was already "
                "readable.",
            "proof": "server/tools/test_run29_closure_version_boundary.py",
            "scope_stated_honestly":
                "that suite proves ONE divergence on identical input, which is all a version "
                "boundary needs. It does not claim to enumerate every divergence.",
            "history_preserved": list(SIMULATION_VERSION_HISTORY),
            "history_is_append_only":
                "the tuple recorded at commit 9cc6793 is asserted to be a strict PREFIX of the "
                "tuple now, read out of git rather than out of a note, and to have grown by "
                "exactly the one stamp this closure is authorised to add.",
        },

        "self_reference_note":
            "manifest_sha256 and final_commit are null BY CONSTRUCTION; both are recorded in the "
            "companion .sha256 file written by the finalisation commit.",
        "manifest_sha256": None,
        "final_commit": None,
        "starting_commit": "9cc6793a998fdd9d6ec3693035bb4826bed4e117",
        "stage1_parent_commit": git("rev-parse", "HEAD"),
        "stage1_repository_tree_hash": git("rev-parse", "HEAD^{tree}"),

        "production_files_changed": [
            {"path": p, "sha256": sha(p), "already_declared_by": who, "why": why}
            for p, (who, why) in sorted(CLOSURE_CHANGED.items())
        ],
        "production_files_created": [],
        "declared_changes_note":
            "NO NEW DECLARED-CHANGES MANIFEST WAS WRITTEN, and that is the guard working rather "
            "than a gap. All four files this closure changed are already declared: models_doc.py "
            "and registry.py by Run 20, models.py and documents.py by Run 28, canonical_v4.py by "
            "Run 29 as new production code. No path may appear in two manifests, because one "
            "change is never counted twice.",

        "production_surface": {
            "discovery": "walked from the deployed roots in server/tools/production_tree.py",
            "file_count": len(prod),
            "manifest_file": "code_audit/run29_closure_production_tree.sha256",
            "manifest_sha256": pt.manifest_sha256(),
            "parent_manifest_file": "code_audit/run29_production_tree.sha256",
            "parent_manifest_sha256": hashlib.sha256(
                (ROOT / "code_audit" / "run29_production_tree.sha256").read_bytes()).hexdigest(),
            "files_added_since_parent": 0,
            "files_removed_since_parent": 0,
            "files_changed_since_parent": sorted(CLOSURE_CHANGED),
            "untracked_production_files": sorted(
                rel for rel, _d, _s, tracked in prod if not tracked),
            "files": [{"path": rel, "sha256": digest, "bytes": size, "git_tracked": tracked}
                      for rel, digest, size, tracked in prod],
        },

        "real_corpus_reconciliation": {
            "record": "code_audit/run29_real_corpus_structure_reconciliation.csv",
            "record_sha256": sha("code_audit/run29_real_corpus_structure_reconciliation.csv"),
            "guard": "server/tools/test_run29_corpus_reconciliation.py",
            "structures": 17,
            "wired_by_this_closure": ["ncrExposureRecord"],
            "genuinely_absent": 16,
            "unwired_but_present_remaining": 0,
            "acceptance":
                "structures whose defining fields exist in the corpus but remain unwired = 0. "
                "Each of the sixteen states its case against the extraction registry rather than "
                "against prose: no index manufactures a dependency matrix, no activity count "
                "manufactures a queue, no procurement ratio manufactures an agent population and "
                "no progress percentage manufactures a discrete-event trace.",
        },

        "closure_table": {
            "record": "code_audit/run29_closure_18_target_table.csv",
            "record_sha256": sha("code_audit/run29_closure_18_target_table.csv"),
            "rows": 18,
            "regenerated_from": "the registry and code_audit/run29_cat4_5_scope.csv, not by hand",
            "unaccounted": 0,
        },

        "leakage_guard": {
            "module": "A5.4 Scenario Modeling",
            "guard": "server/tools/test_run29_a54_leakage.py",
            "property":
                "the module cannot emit a recommended action, a preferred option, a decision "
                "ranking, an optimization result or a participant recommendation, on any input.",
            "non_vacuity":
                "the predicate is proved capable of failing by executing a mutated copy of the "
                "runner that emits each forbidden shape in turn and observing the guard go red, "
                "then restoring and observing green.",
        },

        "synthetic_package_chain": {
            "current": SP.CURRENT.identifier,
            "current_record": SP.CURRENT.record,
            "current_record_sha256": sha(SP.CURRENT.record),
            "chain": [{"identifier": s.identifier, "root": s.root, "record": s.record,
                       "record_sha256": sha(s.record) if s.record else None,
                       "current": s.current}
                      for s in SP.SYNTHETIC_PACKAGES],
            "declaration": "server/tools/synthetic_packages.py",
            "guard": "server/tools/test_run29_synthetic_packages.py",
            "why_v0_4":
                "three Category-4 and -5 modules were still exercised against the shapes the "
                "PREVIOUS analytical line read -- an audited findings cohort for the "
                "nonconformance rate, an occupancy log for the queueing measure and a typed-in "
                "state history for the agent based model -- and the supplied contracts name all "
                "three as not being the method. The six projects' real evidence is imported into "
                "the canonical shapes directly from v0.3, UNCHANGED; the successor adds only the "
                "known-answer tables at the figures the contracts state, including the one "
                "supplier, one carrier, one project model v0.3 cannot express because all "
                "forty-eight of its agents are suppliers.",
            "predecessors_unchanged":
                "every predecessor build still sits in the tree untouched and its own record "
                "still verifies. The three replaced importers are KEPT, because the Run-19 and "
                "Run-10B suites read them as the record of what the previous line was integrated "
                "against, and rewriting them would destroy that record.",
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
            "unchanged_by_this_closure": True,
            "why":
                "the closure removed no registry qualifier and changed no served evidence "
                "object, so no participant-facing byte moved and v4 stands.",
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
            "registry_sha256": sha("server/app/simulation/registry.py"),
            "unchanged_by_this_closure": True,
        },

        "not_closed_by_this_closure": {
            "calibration":
                "no status band was introduced for any Category 4 or 5 quantity. Run 33 owns it.",
            "empirical_validation":
                "A4.1's and A4.10's precision and recall remain PENDING RUN 33. No labelled "
                "corpus exists in this repository and none was invented.",
            "orphan_field_document_types": "Run 31 owns it.",
            "category_9_qualification_gate": "Run 31 owns it.",
            "sixteen_absent_structures":
                "sixteen of the seventeen Category-4 and -5 structures remain unpopulated on the "
                "real corpus and their modules still abstain on it. That is the honest state and "
                "not a defect: the corpus does not carry the evidence, and inventing it is the "
                "one thing this instrument may never do.",
        },

        "report": REPORT,
        "report_present_in_tree": (ROOT / REPORT).is_file(),
        "report_sha256": sha(REPORT),
    }

    STAGE1.parent.mkdir(parents=True, exist_ok=True)
    STAGE1.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {STAGE1.relative_to(ROOT)}")
    print(f"  production files: {len(prod)}  changed since parent: {len(CLOSURE_CHANGED)}")
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
