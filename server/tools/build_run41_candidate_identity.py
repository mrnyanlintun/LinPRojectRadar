#!/usr/bin/env python3
"""
RUN 41. THE SUCCESSOR FREEZE CANDIDATE IDENTITY.

Writes research/freeze/run41_freeze_candidate_identity.json in exactly the shape Run 37 wrote its
own, so the freeze gate's B01 blocker can recompute every digest from the tree and compare.

The Run-37 identity is NOT rewritten. It stays as that release wrote it and remains the identity
of the v25 predecessor; this file is its successor and names it as its parent.

THE MEMBER LISTS ARE DERIVED, NOT COPIED. The grouping (which files constitute the registry
authority, the taxonomy authority, and so on) is Run 37's and is reused deliberately, because
changing what a freeze measures at the same time as changing the instrument would make the two
incomparable. But the MEMBERS of the two globbed groups - every test_*.py the acceptance runner
globs, and the analytical layer - are re-derived from the filesystem, because Run 41 adds suites
and a frozen list would silently stop covering them.

Usage: python tools/build_run41_candidate_identity.py [--candidate <commit>]
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
PARENT_IDENTITY = FREEZE / "run37_freeze_candidate_identity.json"


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
            "Run 40 confirmed two HIGH defects on the v25 instrument - stored XSS and "
            "content-type spoofing at GET /documents/{id}/content, and raw-SQL mutability of the "
            "substantive final participant judgment after the final lock - and the owner ruled "
            "that both be fixed before participant use rather than accepted for the study "
            "period. Both fixes change executable behaviour, so the freeze is superseded rather "
            "than amended. The v25 candidate, its identity, its gate and its release records are "
            "preserved unchanged as the historical evidence for anything computed under v25."),
        "simulation_version": "sim-2026.08-v26",
        "participant_package": "og-participant-2026.08-v13",
        "synthetic_package": "OG-SYNTH-0.6",
    }

    # Groups whose membership is fixed by what they mean, carried over from Run 37 unchanged.
    for key in ("registry_digest", "taxonomy_authority_digest", "qualification_authority_digest",
                "participant_protocol_digest", "controlled_stimuli_digest"):
        members = list(parent[key]["members"])
        missing = [m for m in members if not (ROOT / m).is_file()]
        if missing:
            raise SystemExit(f"{key}: member files have disappeared, refusing to emit an "
                             f"identity that silently stops measuring them: {missing}")
        out[key] = {"label": parent[key]["label"], "files": len(members),
                    "digest": digest_of(members), "members": members}

    # DERIVED FROM THE FILESYSTEM, because Run 41 adds to both of these.
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

    # The migration that carries finding S2. Named as its own group because it is the whole of
    # the S2 remediation and it lives outside every group Run 37 defined.
    mig = ["server/alembic/versions/0026_final_lock_guard.py"]
    out["final_lock_guard_digest"] = {
        "label": "the final-lock database guard (finding S2)",
        "files": len(mig), "digest": digest_of(mig), "members": mig}

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

    target = FREEZE / "run41_freeze_candidate_identity.json"
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
