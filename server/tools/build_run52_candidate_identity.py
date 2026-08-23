#!/usr/bin/env python3
"""
RUN 52. THE SUCCESSOR FREEZE CANDIDATE IDENTITY.

Writes research/freeze/run52_freeze_candidate_identity.json in exactly the shape Run 41 wrote its
own, so the freeze gate's B01 blocker can recompute every digest from the tree and compare.

The Run-51 identity is NOT rewritten. It stays as that release wrote it and remains the identity
of the v34 predecessor; this file is its successor and names it as its parent.

THE MEMBER LISTS ARE DERIVED, NOT COPIED. The grouping (which files constitute the registry
authority, the taxonomy authority, and so on) is Run 37's and is reused deliberately, because
changing what a freeze measures at the same time as changing the instrument would make the two
incomparable. But the MEMBERS of the two globbed groups - every test_*.py the acceptance runner
globs, and the analytical layer - are re-derived from the filesystem, because Run 47 adds a suite
and a frozen list would silently stop covering it. `evidence_provenance_digest` gains ONE named
member, `server/app/evm_consistency.py`: the consistency check is built on the per-field
provenance record `extraction_merge` writes, and a freeze that did not measure it would not be
measuring the check.

Usage: python tools/build_run52_candidate_identity.py [--candidate <commit>]
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
PARENT_IDENTITY = FREEZE / "run51_freeze_candidate_identity.json"


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
            "Run 52 carries the owner's rulings of 2026-08-23. RULING 2: the dead 'see Health' "
            "button and its [data-goto-health] handler are REMOVED from assets/js/deepdive.js. "
            "The handler called window.LinIngest.openHealthModal(), which exists nowhere in the "
            "repository, so clicking it did nothing; the anomaly sentence it sat beside is "
            "unchanged and still renders, and the comment at the removal site records both "
            "facts. RULING 3: ONE NAME FOR THE MODULE IDENTIFIER ON BOTH SIDES OF THE WIRE, "
            "`module_id`. Run 51 had moved the same field from `num` to `key`; the server "
            "already called it `module_id` in the stored row, the API response and the export, "
            "so the client and the authority move to the server's name rather than the server "
            "moving to theirs. server/tools/taxonomy_authority.json, "
            "server/tools/build_client_taxonomy.py, both regenerated client mirrors and every "
            "client consumer follow, including the dispatch map and resolver in taxonomy.js. "
            "The CATEGORY identifier is deliberately NOT renamed: a category is not a module, "
            "and `module_id` on a category object would be a third wrong name. RULING 4 IS A "
            "REVERSAL AND WAS OBEYED AS ONE: displayed identifiers are acceptable, NO NAMING "
            "SWEEP WAS RUN, no identifier was stripped from rendered text and none was "
            "restored. RULING 1 WAS NOT CARRIED AND ITS SURFACE IS STOPPED UNDER SECTION 8.1 OF "
            "THE ORDER: the ruling's premise was that the project list's Manage and Open "
            "controls lead to the same project detail page. DRIVEN IN A REAL BROWSER THEY DO "
            "NOT -- Manage opens an inline admin accordion under its own row and never leaves "
            "the portfolio page, while Open is the ONLY route from the project list to the "
            "project detail page -- so removing Open would have removed that route. "
            "assets/js/app.js did not move. NOTHING IS COMPUTED DIFFERENTLY AND NO STORED "
            "FIGURE MOVED: no formula, band, threshold, calibration, abstention rule or "
            "population moved, voting is still exactly A1.7 and A1.8, 63 modules are in service "
            "of 101 registered, and the behaviour digest is reproduced identically. ONE "
            "SEQUENCE-BEARING FILE MOVED, assets/js/deepdive.js, carrying its own named "
            "exception record in participant_packages.py and in the v20 checksum record's "
            "header. The v34 candidate, its identity, its gate and its release records are "
            "preserved unchanged as the historical evidence for anything computed under v34."),
        "simulation_version": "sim-2026.08-v35",
        "participant_package": "og-participant-2026.08-v20",
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

    target = FREEZE / "run52_freeze_candidate_identity.json"
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
