#!/usr/bin/env python3
"""
RUN 59. THE SUCCESSOR FREEZE CANDIDATE IDENTITY.

Writes research/freeze/run59_freeze_candidate_identity.json in exactly the shape Run 41 wrote its
own, so the freeze gate's B01 blocker can recompute every digest from the tree and compare.

The Run-52 identity is NOT rewritten. It stays as that release wrote it and remains the identity
of the v35 predecessor; this file is its successor and names it as its parent.

TWO GROUPS MOVE IN THIS MINT, AND BOTH MOVE BY DECLARATION RATHER THAN BY SILENCE.

  1. `participant_protocol_digest` LOSES ONE MEMBER, `assets/js/deepdive.js`, because Run 54
     phase B DELETED that file on the owner's ruling. The parent builder raised SystemExit when
     any member had disappeared, and that refusal is the right default: a member vanishing is
     normally a freeze that has silently stopped measuring something. THE REFUSAL IS NOT
     WEAKENED. It is narrowed by a DECLARED deletion list, `DECLARED_DELETIONS` below, whose
     every entry must (a) be named in participant_packages.V20_TO_V21_DELETED, (b) actually be
     absent from the tree, and (c) have existed at the pinned predeletion commit. An UNDECLARED
     disappearance still raises, and a declaration for a file that is still present raises too,
     so the declaration cannot be used to drop a live file.

  2. `test_suite_identity` GAINS TEN MEMBERS. Run 55 phase B brought `server/tests/` inside
     `server/run_all_suites.sh`, so the suite population the freeze records is now what the
     runner actually runs: `server/tools/test_*.py` AND `server/tests/test_*.py`. The identity
     measured 193; it now measures 203. Leaving it at 193 would mean the freeze did not measure
     the ten suites the pass runs, which is the same defect as a member vanishing unnoticed.

THE MEMBER LISTS ARE DERIVED, NOT COPIED. The grouping (which files constitute the registry
authority, the taxonomy authority, and so on) is Run 37's and is reused deliberately, because
changing what a freeze measures at the same time as changing the instrument would make the two
incomparable. But the MEMBERS of the two globbed groups - every test_*.py the acceptance runner
globs, and the analytical layer - are re-derived from the filesystem, because Run 47 adds a suite
and a frozen list would silently stop covering it. `evidence_provenance_digest` gains ONE named
member, `server/app/evm_consistency.py`: the consistency check is built on the per-field
provenance record `extraction_merge` writes, and a freeze that did not measure it would not be
measuring the check.

Usage: python tools/build_run59_candidate_identity.py [--candidate <commit>]
"""
from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
FREEZE = ROOT / "research" / "freeze"
PARENT_IDENTITY = FREEZE / "run57_freeze_candidate_identity.json"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import participant_packages as PP  # noqa: E402

#: THE ONLY DISAPPEARANCES THIS BUILDER WILL ACCEPT, and they are not written here by hand: they
#: are read from participant_packages.V20_TO_V21_DELETED, the record the package chain already
#: carries. A file may only leave a pinned identity group by being named there.
DECLARED_DELETIONS = tuple(PP.V23_TO_V24_DELETED)

#: The commit at which every declared deletion must still have existed. EXPLICIT HASH, never a
#: relative reference: Run 54 wrote its own proofs of absence against HEAD~1 and they decayed
#: silently into false proofs that still passed as later commits walked the reference back.
RUN54_PREDELETION_COMMIT = "e13b4f1"


def digest_of(members: list[str]) -> str:
    body = "\n".join(f"{hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}  {p}"
                     for p in members) + "\n"
    return hashlib.sha256(body.encode()).hexdigest()


def rel(paths) -> list[str]:
    return sorted(p.relative_to(ROOT).as_posix() for p in paths)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", default="HEAD")
    args = ap.parse_args()
    candidate = subprocess.run(["git", "rev-parse", args.candidate], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.strip()

    parent = json.loads(PARENT_IDENTITY.read_text(encoding="utf-8"))

    # THE DECLARATION IS VALIDATED BEFORE ANYTHING IS EMITTED. A declaration for a file that is
    # still present, or for a file that never existed at the pinned predeletion commit, is
    # refused: otherwise the declaration would be a way to drop a live file from the freeze.
    for d in DECLARED_DELETIONS:
        if (ROOT / d).is_file():
            raise SystemExit(f"declared deletion {d} is STILL PRESENT in the tree. A declaration "
                             f"may record a deletion; it may not cause one.")
        r = subprocess.run(["git", "cat-file", "-e", f"{RUN54_PREDELETION_COMMIT}:{d}"],
                           cwd=ROOT, capture_output=True)
        if r.returncode != 0:
            raise SystemExit(f"declared deletion {d} did not exist at "
                             f"{RUN54_PREDELETION_COMMIT}; the declaration is vacuous.")
        print(f"  declared deletion verified: {d} existed at {RUN54_PREDELETION_COMMIT} "
              f"and is absent now")

    out: dict = {
        "candidate_git_commit": candidate,
        "candidate_commit_verified_is_head": (
            candidate == subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                        capture_output=True, text=True,
                                        check=True).stdout.strip()),
        "supersedes_candidate": parent["candidate_git_commit"],
        "supersedes_simulation_version": parent["simulation_version"],
        "supersession_reason": (
            "RUN 59. NO MARKDOWN DOCUMENT IN THIS REPOSITORY CARRIES AUTHORITY. The owner's ruling of "
            "2026-08-25: production code is the truth, REPORT_*.md / code_audit/REPORT_*.md / "
            "research/freeze/*.md / the fixture records are SEALED EVIDENCE, and everything else is "
            "transport or history and governs nothing. SIX of the 242 production-tree members moved and "
            "EVERY ONE OF THE SIX EDITS IS A COMMENT OR A DOCUMENT HEADING: assets/js/decision-ui.js, "
            "p0-baseline/MODULE_TAXONOMY.md, server/app/research_export.py, server/app/document_evidence.py, "
            "server/app/evm_consistency.py and server/app/simulation/portfolio_health.py. Five of them "
            "cited a module-identifier prohibition the owner SUPERSEDED on 2026-08-23 -- research_export.py "
            "by number as 'NAMING_AUTHORITY.md rule 6', and portfolio_health.py as 'NAMING_AUTHORITY "
            "section 4', which is the very section that RECORDED THE REVERSAL, so the code cited the "
            "reversal as the source of the rule. In all five the citation is DROPPED and the reason stated "
            "directly, established by execution: no test anywhere reads any of those comment strings. "
            "assets/js/decision-ui.js is SEQUENCE-BEARING and its move is a NAMED EXCEPTION OF RECORD in "
            "V23_TO_V24_SEQUENCE_EXCEPTION, declared rather than discovered by a checksum. THE STAMP MOVES "
            "BECAUSE THE MANIFEST MOVES, NOT BECAUSE BEHAVIOUR DID: not one executable byte, not one "
            "rendered string, not one control. PHASE B REMOVED THE GUARDS THAT ASSERTED A MARKDOWN "
            "DOCUMENT'S CONTENT. Four were RE-POINTED at non-markdown production oracles and each was "
            "proved still able to fail BY BREAKING PRODUCTION -- test_group_assignment.py, which used to "
            "raise SystemExit and ABORT THE SUITE when a fenced block went missing, now reads "
            "p0-baseline/module_renumbering_map.csv; test_disclaimers.py's meta-description check now "
            "reads assets/js/knowledge.js; and both DISCLAIMERS_DRAFT.md comparisons, in "
            "test_disclaimers.py and test_export_workbook.py, now read assets/js/disclaimers.js. Fifteen "
            "further checks were RETIRED THE WAY MODULES WERE RETIRED: they stop running, their bodies are "
            "NOT deleted, and the reason is recorded beside each. NO CHECK WAS DELETED. Run 58's finding "
            "of the first order is closed: REPORT_2026-08-18_run34-portfolio-health-calibration.md, an "
            "EVIDENCE document, was read as an AUTHORITY by four live suites, one of them out of a merged "
            "commit so that even a correct edit could not restore green; those halves stop, and the CSV "
            "artefact they were redundant with is still asserted at HEAD and at 41f01e8. TWO GUARDS WERE "
            "STOPPED RATHER THAN RE-POINTED, because re-pointing would have meant inventing an oracle: "
            "test_run39_launch_gate.py's assertion about STUDY_ADMINISTRATION_RUNBOOK.md and "
            "test_run22_production_tree_completeness.py's controlling_status assertion. NOTHING IS "
            "COMPUTED DIFFERENTLY AND NO STORED FIGURE MOVED: 101 registered, 63 in service, voting "
            "exactly A1.7 and A1.8, and the behaviour digest is RE-DERIVED and unchanged. THE AUTHORITY "
            "TREE DID NOT MOVE: its manifest sha256 b52c47a68a20ab1629681ea240abdea2167c67f289d181f446a"
            "8170704dc1596 is unmoved for a FIFTH run, and the supervisory specification is NOT deleted, "
            "NOT renamed and NOT removed from it -- only its CONTROLLING designation is withdrawn. The v23 "
            "candidate, its identity, its gate and its release records are preserved unchanged as the "
            "historical evidence for anything computed under v38."),
        "simulation_version": "sim-2026.08-v39",
        "participant_package": "og-participant-2026.08-v24",
        "synthetic_package": "OG-SYNTH-0.6",
    }

    # Groups whose membership is fixed by what they mean, carried over unchanged.
    for key in ("registry_digest", "taxonomy_authority_digest", "qualification_authority_digest",
                "participant_protocol_digest", "controlled_stimuli_digest"):
        members = list(parent[key]["members"])
        missing = [m for m in members if not (ROOT / m).is_file()]
        # THE REFUSAL IS NARROWED BY DECLARATION, NOT WEAKENED. See the module docstring.
        undeclared = [m for m in missing if m not in DECLARED_DELETIONS]
        if undeclared:
            raise SystemExit(f"{key}: member files have disappeared, refusing to emit an "
                             f"identity that silently stops measuring them: {undeclared}")
        for m in missing:
            print(f"  {key}: DECLARED DELETION, dropped from the identity -- {m}")
        members = [m for m in members if m not in missing]
        out[key] = {"label": parent[key]["label"], "files": len(members),
                    "digest": digest_of(members), "members": members}

    # DERIVED FROM THE FILESYSTEM, because Run 45 adds to both of these.
    sim = rel((ROOT / "server" / "app" / "simulation").glob("*.py"))
    out["simulation_authority_digest"] = {
        "label": parent["simulation_authority_digest"]["label"],
        "files": len(sim), "digest": digest_of(sim), "members": sim}

    # RUN 55, PHASE B. BOTH DIRECTORIES, because server/run_all_suites.sh now runs both. The
    # glob is the runner's glob; if the two ever diverge the freeze would stop measuring what
    # the pass runs, which is exactly the defect this group exists to prevent.
    tests = rel(list((ROOT / "server" / "tools").glob("test_*.py"))
                + list((ROOT / "server" / "tests").glob("test_*.py")))
    out["test_suite_identity"] = {
        "label": parent["test_suite_identity"]["label"],
        "files": len(tests), "digest": digest_of(tests), "members": tests}

    browser = list(parent["browser_suite_identity"]["members"])
    out["browser_suite_identity"] = {
        "label": parent["browser_suite_identity"]["label"], "files": len(browser),
        "digest": digest_of(browser), "members": browser}

    # Carried forward from Run 41: the migration that carries finding S2 is still part of what
    # this freeze measures, and dropping it would silently stop measuring it.
    mig = list(parent["final_lock_guard_digest"]["members"])
    out["final_lock_guard_digest"] = {
        "label": parent["final_lock_guard_digest"]["label"],
        "files": len(mig), "digest": digest_of(mig), "members": mig}

    # THE EXTRACTION-MERGE PATH. Named as its own group because it is the whole of the Run 42
    # remediation and it lives in app/, outside every group Run 37 or Run 41 defined -- the
    # per-field provenance record is written here and nowhere else.
    # RUN 48 ADDS NOTHING HERE, and says so rather than leaving it unstated: the current-period
    # determination lives inside documents.py, which this group already measures. A future file
    # in app/ still does not enter this group silently.
    merge = sorted(set(parent["evidence_provenance_digest"]["members"]))
    out["evidence_provenance_digest"] = {
        "label": parent["evidence_provenance_digest"]["label"],
        "files": len(merge), "digest": digest_of(merge), "members": merge}

    # THE RETIREMENT AUTHORITY. Carried forward from Run 43 unchanged. Named as its own group
    # because it is the ONE file that decides which modules are in service, and a freeze that did
    # not measure it would not be measuring the retirement. Run 44 does not touch it, which is
    # itself a thing this digest asserts.
    # (Run 43's own comment follows.) Named as its own group because it is the whole of the Run 43
    # change and because it is the ONE file that decides which modules are in service: the
    # `notes` column of the registry map. No list of retired identifiers exists anywhere else,
    # so a freeze that did not measure this file would not be measuring the retirement.
    retire = ["p0-baseline/module_renumbering_map.csv"]
    out["service_roster_digest"] = {
        "label": "the retirement authority: the registry map whose notes decide service (Run 43)",
        "files": len(retire), "digest": digest_of(retire), "members": retire}

    for key, path in (("candidate_manifest_digest",
                       "research/freeze/INSTRUMENT_FREEZE_CANDIDATE_MANIFEST.json"),
                      ("candidate_companion_digest",
                       "research/freeze/INSTRUMENT_FREEZE_CANDIDATE.md")):
        p = ROOT / path
        obj = subprocess.run(["git", "hash-object", str(p)], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        out[key] = {"path": path,
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                    "git_object": obj}

    out["method"] = parent["method"]
    body = json.dumps({k: v["digest"] for k, v in out.items()
                       if isinstance(v, dict) and "digest" in v}, sort_keys=True)
    out["candidate_identity_digest"] = hashlib.sha256(body.encode()).hexdigest()

    target = FREEZE / "run59_freeze_candidate_identity.json"
    artifact_out(target).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {target.relative_to(ROOT)}")
    print(f"  candidate            {candidate}")
    print(f"  supersedes           {out['supersedes_candidate']}")
    for k, v in out.items():
        if isinstance(v, dict) and "digest" in v:
            print(f"  {k:34s} {v['files']:4d} files  {v['digest'][:16]}")
    print(f"  candidate_identity_digest  {out['candidate_identity_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
