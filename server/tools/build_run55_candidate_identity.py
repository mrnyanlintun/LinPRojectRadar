#!/usr/bin/env python3
"""
RUN 55. THE SUCCESSOR FREEZE CANDIDATE IDENTITY.

Writes research/freeze/run55_freeze_candidate_identity.json in exactly the shape Run 41 wrote its
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

Usage: python tools/build_run55_candidate_identity.py [--candidate <commit>]
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
PARENT_IDENTITY = FREEZE / "run52_freeze_candidate_identity.json"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import participant_packages as PP  # noqa: E402

#: THE ONLY DISAPPEARANCES THIS BUILDER WILL ACCEPT, and they are not written here by hand: they
#: are read from participant_packages.V20_TO_V21_DELETED, the record the package chain already
#: carries. A file may only leave a pinned identity group by being named there.
DECLARED_DELETIONS = tuple(PP.V20_TO_V21_DELETED)

#: The commit at which every declared deletion must still have existed. EXPLICIT HASH, never a
#: relative reference: Run 54 wrote its own proofs of absence against HEAD~1 and they decayed
#: silently into false proofs that still passed as later commits walked the reference back.
RUN54_PREDELETION_COMMIT = "bf36ef6"


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
            "RUNS 54 AND 55, TAKEN AS ONE SUPERSESSION because Run 54 completed four phases and "
            "could not mint them: the acceptance generator hashed a pinned identity that still "
            "named a file Run 54 had deleted, so rows 2 and 3 of the freeze gate failed and "
            "nothing could be merged. Run 55 completes the same body of work and mints it. "
            "RUN 54 PHASE A: server/tools/campaign_safety.py -- a start-AND-end dirty-tree "
            "guard and pristine-HEAD snapshots for all 39 fault campaigns, after Run 52 found "
            "three guards in canonical_v8.py replaced by `if False:` and five consecutive runs "
            "certified rather than caught it. RUN 54 PHASE B: the client-side deep-dive surface "
            "is DELETED -- assets/js/deepdive.js, research/deepdive.html and the route in "
            "server/app/main.py that served it. It was reached by no route the service serves "
            "and every one of its 78 panels gated on the legacy client-side blob, so the "
            "guarantee that no served route loads a client-side model is now unconditional "
            "rather than confined. RUN 54 PHASE C: the project list's Manage control NAVIGATES "
            "to the project detail page, and the redundant Open control is removed -- in that "
            "order, Manage verified in a real browser per row and per surface BEFORE Open was "
            "removed, so no project's detail page was unreachable at any point. This REVERSES "
            "Run 52's stop under its section 8.1, on the owner's ruling, and both guards that "
            "enforced that stop are revised rather than deleted. RUN 54 PHASE D: the naming "
            "authority records that displayed identifiers are acceptable; NOT ONE WORD OF "
            "RENDERED TEXT CHANGED. RUN 55 PHASE A: the six operational controls the removed "
            "accordion carried -- Save info, Upload documents, Recompute this project, Reset "
            "signals, Archive, Close -- are MOVED onto the project detail page, built by the "
            "same function from the same markup with the same six handlers, mounted on a host "
            "stamped with the viewed project's id. Measured in a real browser on three "
            "projects: each control renders exactly once and acts on that project and no other. "
            "The four dead .li-open rules in radar.css go with the control they styled. RUN 55 "
            "PHASE B: the fifteen remaining fault campaigns restore inside a `finally`, "
            "server/tests/ is inside server/run_all_suites.sh so the campaign most implicated "
            "in the leak now runs inside the pass meant to catch it, and arm()'s allow lists "
            "are tightened to declared outputs in the four campaigns that over-permitted. RUN "
            "55 PHASE C: the two guards that asserted the pre-Run-54 state -- "
            "test_run28_participant_packages.py and run52_injection_campaign.py fault 4 -- are "
            "REVISED to assert the current one, and a third found by sweep, tests_render.html's "
            "row-actions group, with it. NOTHING IS COMPUTED DIFFERENTLY AND NO STORED FIGURE "
            "MOVED: no formula, band, threshold, calibration, abstention rule or population "
            "moved, voting is still exactly A1.7 and A1.8, 63 modules are in service of 101 "
            "registered, and the behaviour digest is RE-DERIVED and unchanged. ONE "
            "SEQUENCE-BEARING FILE MOVED ACROSS v20 TO v21 AND ITS DELTA IS A DELETION -- "
            "assets/js/deepdive.js -- the first link in this chain to move the SET rather than "
            "a member of it, and it carries its own named exception record in "
            "participant_packages.py as V20_TO_V21_SEQUENCE_EXCEPTION and in the v21 checksum "
            "record's header. THE SUITE POPULATION THIS IDENTITY MEASURES GREW from 193 to 203 "
            "because the runner now runs server/tests/ as well as server/tools/. The v35 "
            "candidate, its identity, its gate and its release records are preserved unchanged "
            "as the historical evidence for anything computed under v35."),
        "simulation_version": "sim-2026.08-v36",
        "participant_package": "og-participant-2026.08-v21",
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

    target = FREEZE / "run55_freeze_candidate_identity.json"
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
