#!/usr/bin/env python3
"""
RUN 48. THE SUCCESSOR FREEZE CANDIDATE IDENTITY.

Writes research/freeze/run48_freeze_candidate_identity.json in exactly the shape Run 41 wrote its
own, so the freeze gate's B01 blocker can recompute every digest from the tree and compare.

The Run-47 identity is NOT rewritten. It stays as that release wrote it and remains the identity
of the v31 predecessor; this file is its successor and names it as its parent.

THE MEMBER LISTS ARE DERIVED, NOT COPIED. The grouping (which files constitute the registry
authority, the taxonomy authority, and so on) is Run 37's and is reused deliberately, because
changing what a freeze measures at the same time as changing the instrument would make the two
incomparable. But the MEMBERS of the two globbed groups - every test_*.py the acceptance runner
globs, and the analytical layer - are re-derived from the filesystem, because Run 47 adds a suite
and a frozen list would silently stop covering it. `evidence_provenance_digest` gains ONE named
member, `server/app/evm_consistency.py`: the consistency check is built on the per-field
provenance record `extraction_merge` writes, and a freeze that did not measure it would not be
measuring the check.

Usage: python tools/build_run47_candidate_identity.py [--candidate <commit>]
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
PARENT_IDENTITY = FREEZE / "run47_freeze_candidate_identity.json"


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

    out: dict = {
        "candidate_git_commit": candidate,
        "candidate_commit_verified_is_head": (
            candidate == subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                        capture_output=True, text=True,
                                        check=True).stdout.strip()),
        "supersedes_candidate": parent["candidate_git_commit"],
        "supersedes_simulation_version": parent["simulation_version"],
        "supersession_reason": (
            "Run 48 makes the project detail page read the CURRENT period and corrects the live "
            "instances of the retired naming scheme, on the owner's three rulings of "
            "2026-08-22. RULING 1: the page shows the latest period that has documents and has "
            "been computed from them. It read back the stored row with a hard-coded `period: 1`, "
            "so on a project whose current period was not 1 every panel on the page -- the key "
            "drivers, the abstention reasons, `recommendation_basis` and the Run 47 "
            "disagreement findings -- held period 1's row. The period is now DERIVED BY THE "
            "SERVER and read from `projectperiods`, which gains two read-only fields, "
            "`computed_periods` and `latest_computed_period`, taken from the live computed "
            "results themselves: no contiguity is assumed, the highest period number is not "
            "assumed to have results, and no maximum period count is assumed. A project with no "
            "computed result in any period keeps the empty state the page already renders. "
            "RULING 2: the live naming instances are corrected. deepdive.js's panel labels are "
            "groups and purposes with no identifier, including the fallback, and the panel "
            "GROUPING number is declared separately from the displayed text so correcting one "
            "cannot move the other; charts3d.js's synthesis node label names its purpose; "
            "detail.js sends no category identifier into the executive brief's model prompt. "
            "RULING 3: the dead category label map in detail.js is deleted. NOTHING IS COMPUTED "
            "DIFFERENTLY AND NO STORED FIGURE MOVED: every change is on the READ path, no "
            "formula, band, threshold, calibration, abstention rule or population moved, voting "
            "is still exactly A1.7 and A1.8, and 63 modules are in service of 101 registered. NO "
            "USER-FACING CONTROL WAS ADDED, MOVED OR REMOVED and the detail page still holds no "
            "period selector, measured in the real browser DOM. ONE SEQUENCE-BEARING FILE MOVED, "
            "assets/js/deepdive.js, on ruling 2's own authority, and it carries its own named "
            "exception record in participant_packages.py; the other five are byte-identical. The "
            "v31 candidate, its identity, its gate and its release records are preserved "
            "unchanged as the historical evidence for anything computed under v31."),
        "simulation_version": "sim-2026.08-v32",
        "participant_package": "og-participant-2026.08-v17",
        "synthetic_package": "OG-SYNTH-0.6",
    }

    # Groups whose membership is fixed by what they mean, carried over unchanged.
    for key in ("registry_digest", "taxonomy_authority_digest", "qualification_authority_digest",
                "participant_protocol_digest", "controlled_stimuli_digest"):
        members = list(parent[key]["members"])
        missing = [m for m in members if not (ROOT / m).is_file()]
        if missing:
            raise SystemExit(f"{key}: member files have disappeared, refusing to emit an "
                             f"identity that silently stops measuring them: {missing}")
        out[key] = {"label": parent[key]["label"], "files": len(members),
                    "digest": digest_of(members), "members": members}

    # DERIVED FROM THE FILESYSTEM, because Run 45 adds to both of these.
    sim = rel((ROOT / "server" / "app" / "simulation").glob("*.py"))
    out["simulation_authority_digest"] = {
        "label": parent["simulation_authority_digest"]["label"],
        "files": len(sim), "digest": digest_of(sim), "members": sim}

    tests = rel((ROOT / "server" / "tools").glob("test_*.py"))
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

    target = FREEZE / "run48_freeze_candidate_identity.json"
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
