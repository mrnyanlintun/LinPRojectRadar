#!/usr/bin/env python3
"""
RUN 67. THE SUCCESSOR FREEZE CANDIDATE IDENTITY.

Writes research/freeze/run67_freeze_candidate_identity.json in exactly the shape Run 41 wrote its
own, so the freeze gate's B01 blocker can recompute every digest from the tree and compare.

The Run-59 identity is NOT rewritten. It stays as that release wrote it and remains the identity
of the v39 predecessor; this file is its successor and names it as its parent.

WHAT MOVES IN THIS MINT, AND IT IS THE PUBLICATION OF TWO FINISHED BRANCHES.

  Run 60 diagnosed, in a rendered browser, that the stored-signal row a project detail page reads
  was not necessarily the row of the period the page holds. Run 61 fixed it by making the caller
  state its question. Three production-tree members moved -- assets/js/detail.js,
  assets/js/taxonomy.js and assets/js/workspace.js -- and TWO FILES WERE ADDED under server/tools:
  drive_run61_caller_shapes.py and test_run61_caller_states_its_question.py. The added test file
  enters `test_suite_identity`, which is DERIVED from the filesystem rather than copied, so the
  suite population this freeze measures becomes 204.

  assets/js/workspace.js is SEQUENCE-BEARING and its move carries a NAMED EXCEPTION OF RECORD in
  participant_packages.V24_TO_V25_SEQUENCE_EXCEPTION. assets/js/taxonomy.js is NOT sequence-
  bearing, MEASURED against SEQUENCE_BEARING_FILES_FROM_V21 and not assumed.

THE MEMBER LISTS ARE DERIVED, NOT COPIED, for the reason Run 59 stated: the grouping is Run 37's
and is reused deliberately, but the members of the globbed groups are re-derived from the
filesystem so that a new suite cannot be silently left unmeasured.

Usage: python tools/build_run67_candidate_identity.py --candidate <commit>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
FREEZE = ROOT / "research" / "freeze"
PARENT_IDENTITY = FREEZE / "run63_freeze_candidate_identity.json"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import participant_packages as PP  # noqa: E402

#: THE ONLY DISAPPEARANCES THIS BUILDER WILL ACCEPT, and they are not written here by hand: they
#: are read from participant_packages.V20_TO_V21_DELETED, the record the package chain already
#: carries. A file may only leave a pinned identity group by being named there.
# RUN 67. NOTHING LEFT ANY PINNED IDENTITY GROUP ACROSS THIS SUPERSESSION, and the empty
#: tuple is DECLARED here rather than omitted. It is NOT read from the package chain this time,
#: and that is stated rather than glossed: THE PARTICIPANT PACKAGE DID NOT MOVE ACROSS RUNS 65
#: TO 67 -- not one of its sixty-nine governed files changed -- so there is no v26-to-v27 link to
#: read a declaration from, and minting one for a package whose bytes are identical would be a
#: false claim of a new package. A member disappearing without being named here still raises.
DECLARED_DELETIONS: tuple[str, ...] = ()

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
            "RUN 67, THE RESIDUE AND THE CATEGORY-9 GAP. THIS MINT PUBLISHES RUNS 65, 66 AND 67, "
            "which were finished and gated nowhere. THREE of the 242 production-tree members "
            "moved and NOTHING was added, removed or renamed: server/app/simulation/compute.py, "
            "server/app/documents.py and server/app/simulation/models.py. NONE of the three is "
            "SEQUENCE-BEARING, MEASURED against SEQUENCE_BEARING_FILES_FROM_V21 and not assumed, "
            "so this link declares its sequence exception as the EMPTY TUPLE rather than "
            "omitting an exception record. THE PARTICIPANT PACKAGE DID NOT MOVE: not one of its "
            "sixty-nine governed files changed, so no package link is minted and no release "
            "record is derived for this candidate; that is reported rather than worked around. "
            "WHAT MOVED. RUN 65 removed the CORE_VOTING_MODULES filter from the computed loop in "
            "compute.py with the owner's authority, so EVERY MODULE THAT PRODUCED A VALUE VOTES "
            "INTO ITS OWN CATEGORY; a module that declined does not vote and does not drag its "
            "category down; each category records which module set it. RUN 67 supplied the "
            "period's Category-9 assessment in documents.py, which no production code had ever "
            "written -- stating only facts the platform already holds and asserting NO "
            "verification status, NO source authority, NO reliability weight, NO timeliness "
            "verdict and NO self-declared qualification state, because none of those is "
            "established and each would be an invented value. RUN 67 also corrected the comment "
            "governing the calibration-pending contract in models.py, which still said such a "
            "row cannot reach status fusion; Run 65 made that false, and what actually happens "
            "was established by execution and pinned by a suite. NO CONTROL was added, moved or "
            "removed. NO DOCUMENT OR CORPUS FILE was modified. THE BEHAVIOUR DIGEST HAS MOVED "
            "AND THAT IS CORRECT: categories now carry statuses they did not carry before, and "
            "on the measurement fixture the modules holding a result go from 9 to 14 and the "
            "categories carrying a status from 2 to 3, fixture and browser agreeing. The v41 "
            "candidate, its identity, its gate and its release records are preserved unchanged "
            "as the historical evidence for anything computed under v41."),
        "simulation_version": "sim-2026.08-v42",
        "participant_package": "og-participant-2026.08-v26",
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

    target = FREEZE / "run67_freeze_candidate_identity.json"
    target.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
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
