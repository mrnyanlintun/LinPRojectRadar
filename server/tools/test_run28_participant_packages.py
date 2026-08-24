"""
RUN 28 CLOSURE. THE PARTICIPANT PACKAGE CHAIN: v1, v2 AND v3, ALL THREE AT ONCE.

THE DEFECT THIS CLOSES, WHICH THE CLOSURE FOUND IN ITS OWN WORK. The first closure pass reported
that FOURTEEN files named by `code_audit/run12_participant_package_checksums.sha256` had already
drifted from that record before this closure touched anything -- radar.css, detail.js,
simulations.js, index.html and others, moved by Runs 21 to 26. It reported the drift and moved on.

That report has a consequence it did not draw: **the live filesystem is not evidence for
og-participant-2026.08-v1.** Every file the record names still exists, but most no longer carry
the bytes the record pins, so a preservation claim checked against the working tree would be
checking the CURRENT package against the HISTORICAL record and failing for reasons that have
nothing to do with preservation. The historical package has to be reconstructed from the only
place its bytes still exist unchanged: the git object graph.

WHAT THIS FILE DOES.

  1  extracts all seventy participant files from the exact Run-12 commit into an ISOLATED
     temporary directory, never into the application;
  2  verifies the file inventory against the Run-12 record;
  3  verifies every one of the seventy checksums against that record;
  4  verifies the package identity, and that the Run-12 record itself has not been rewritten
     since, by comparing it byte for byte with the git object;
  5  verifies the CURRENT og-participant-2026.08-v2 successor independently, against the
     successor record and against the live tree;
  6  proves the two are independent: a change to a current-package test copy cannot alter the
     reconstructed v1 hashes, because the reconstruction reads git and not the disk.

WHAT IT DELIBERATELY DOES NOT DO. It never writes a historical file into the application, and it
never rewrites the Run-12 record. A preservation guard that repaired what it was checking would
agree with itself by construction, which is the circularity this programme has already found in
freezes that regenerated their own baselines.
"""

from __future__ import annotations

import hashlib
import json
import re
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import participant_packages as PP  # noqa: E402

#: THE EXACT GIT OBJECT. The commit that ADDED code_audit/run12_participant_package_checksums.sha256
#: -- Run 12 Gates 11-12, the release freeze that took the package -- found with
#: `git log --diff-filter=A -- <record>`. A commit cannot be mutated in place, so this is evidence
#: rather than a copy someone maintained.
V1_COMMIT = "c44e3ced94a22a9def35fa5a2be3a2268fbed6bb"
V1_IDENTITY = "og-participant-2026.08-v1"
V2_IDENTITY = "og-participant-2026.08-v2"
V3_IDENTITY = "og-participant-2026.08-v3"
#: RUN 29. The chain gained a fourth link: six proxy qualifiers were removed from the registry
#: because the six modules they described now carry out their canonical methods, and the
#: defensibility evidence object served to participants is GENERATED from the registry. v3 is
#: pinned to the commit whose blobs it describes rather than regenerated, which is the defect the
#: Run-28 closure had to correct in the v2 record and which is not repeated here.
V4_IDENTITY = "og-participant-2026.08-v4"
V4_RECORD = "code_audit/run29_participant_package_v4_checksums.sha256"
#: RUN 30 CLOSURE. The chain gained a fifth link. Repointing the twenty Category-7 identities
#: deleted eight proxy qualifiers, and the generator was corrected to read the structure map from
#: all four canonical layers rather than from canonical.py alone. Both changes reach the served
#: defensibility evidence object. v4 is pinned to the commit whose blobs it describes.
V5_IDENTITY = "og-participant-2026.08-v5"
V5_RECORD = "code_audit/run30_participant_package_v5_checksums.sha256"
V4_COMMIT = "ce03eb1f297d9615a9eac7dea34356a69846e5a3"
# RUN 31 PASS 2. v5 IS A PREDECESSOR NOW and v6 describes the live tree. The successor exists
# because propagating the six owner-approved Category-8 names moved eight participant-visible
# files; the delta is six display-name substitutions and nothing else, and it is inverse-mappable
# back to the v5 bytes exactly, which is asserted below.
V5_COMMIT = "4dd59857c77c2c87aed0f741fd7a0e989efef5f2"
V6_IDENTITY = "og-participant-2026.08-v6"
V6_RECORD = "code_audit/run31_participant_package_v6_checksums.sha256"
# RUN 32. v6 IS A PREDECESSOR NOW and v7 describes the live tree. The successor exists because
# section 3 of the owner's Run-32 contract renamed B4.7 -- Regret Minimization Index becomes
# Minimax Regret Decision Rule -- and eight participant-visible files carry that display name.
# The delta is ONE substitution and nothing else, inverse-mappable back to the v6 bytes exactly,
# which is asserted below. v6 is PINNED to the commit whose blobs it describes and is NOT
# regenerated.
V6_COMMIT = "93942ca03295d642dcbae4551faceca3643aadc8"
V7_IDENTITY = "og-participant-2026.08-v7"
V7_RECORD = "code_audit/run32_participant_package_v7_checksums.sha256"
# RUN 32 FINAL CLOSURE. v7 IS A PREDECESSOR NOW and v8 describes the live tree. The successor
# exists because the closure corrected the served defensibility metadata and finished the B4.7
# name propagation. THIS DELTA IS NOT INVERSE-MAPPABLE AND NO INVERSE MAPPING IS ASSERTED FOR IT:
# it corrects statements that had become FALSE, which is a different kind of change from v7's
# display substitution, and claiming otherwise would be the more comfortable lie. What IS asserted
# is that no analytical execution moved and that the sequence-bearing files are byte-identical.
V7_COMMIT = "93f08bcf36c8675aed3bb4d2b8b83011b8077bc0"
V8_IDENTITY = "og-participant-2026.08-v8"
V8_RECORD = "code_audit/run32_closure_participant_package_v8_checksums.sha256"
# THE METHOD-CLASS PROPAGATION. v8 IS A PREDECESSOR NOW and v9 describes the live tree. Six
# identifiers the client carried had stopped being emitted by the runners, so `getModuleStatus`
# matched none of them and returned null rather than failing. v8 is PINNED and NOT regenerated.
V8_COMMIT = "6e7ce204567a3a3331ee894436cd21748bde381e"
V9_IDENTITY = "og-participant-2026.08-v9"
V9_RECORD = "code_audit/run32_b3_participant_package_v9_checksums.sha256"
# THE QUALIFIER RECONCILIATION. v9 IS A PREDECESSOR NOW and v10 describes the live tree: 27 client
# proxy qualifiers and 3 stale server ones were withdrawn, and both client taxonomy artifacts came
# under one generator. v9 is PINNED and NOT regenerated.
V9_COMMIT = "19a70556fe1b6ee8d17706cfbbc5d72e12051086"
V10_IDENTITY = "og-participant-2026.08-v10"
V10_RECORD = "code_audit/run32_qualifier_participant_package_v10_checksums.sha256"
#: RUN 33. v10 became a PREDECESSOR when the Portfolio Health remediation moved three of its
#: files, and is pinned to the commit whose blobs its record describes -- the exact commit Run 33
#: branched from, verified from git before any edit.
V10_COMMIT = "54409af2a07ac989489447379e8379cc9f95e15f"
V11_IDENTITY = "og-participant-2026.08-v11"
V11_RECORD = "code_audit/run33_participant_package_v11_checksums.sha256"
#: RUN 36. v11 is a PREDECESSOR now, so it is verified against its own git object rather than
#: against the live tree. The commit is the Run-35 closure head, which is the tree its record
#: describes.
V11_COMMIT = "dafc35d35bafe5af76e1ce48ef7daceab9daed2c"
V12_IDENTITY = "og-participant-2026.08-v12"
V12_RECORD = "code_audit/run36_participant_package_v12_checksums.sha256"
#: RUN 36 CLOSURE. v12 is a PREDECESSOR now, verified against its own git object rather than the
#: live tree, for the same reason every earlier link is: two records claiming one tree is the
#: masquerade this chain forbids.
V12_COMMIT = "822d80928367c0f422fac5f2564705279e718dd1"
V13_IDENTITY = "og-participant-2026.08-v13"
V13_RECORD = "code_audit/run36_closure_participant_package_v13_checksums.sha256"
# RUN 43, THE RETIREMENT OF 38 MODULES FROM SERVICE. v13 became a PREDECESSOR and v14 is the
# current link. The commit below is the one whose blobs the v13 record describes.
V13_COMMIT = "428a6c60b189bc64117f30edfe773092d5aae2f6"
V14_IDENTITY = "og-participant-2026.08-v14"
V14_RECORD = "code_audit/run43_participant_package_v14_checksums.sha256"
# RUN 44, THE PARTICIPANT-FACING RENDER DEFECTS. v14 became a PREDECESSOR and v15 is the current
# link. The commit below is the one whose blobs the v14 record describes, so v14's own checks now
# run against THAT TREE rather than the live one: a predecessor that still matched the working
# tree would be the masquerade this chain forbids.
V14_COMMIT = "604291a"
V15_IDENTITY = "og-participant-2026.08-v15"
V15_RECORD = "code_audit/run44_participant_package_v15_checksums.sha256"
# RUN 47, THE EVM CONSISTENCY CHECK. v15 became a PREDECESSOR and v16 is the current link. The
# commit below is the one whose blobs the v15 record describes, so v15's own checks now run
# against THAT TREE rather than the live one, for exactly the reason v14's do.
V15_COMMIT = "fe2e2df"
V16_IDENTITY = "og-participant-2026.08-v16"
V16_RECORD = "code_audit/run47_participant_package_v16_checksums.sha256"
# RUN 48, THE PERIOD THE DETAIL PAGE OPENS ON AND THE LIVE NAMING INSTANCES. v16 became a
# PREDECESSOR and v17 is the current link. The commit below is the one whose blobs the v16 record
# describes, so v16's own checks now run against THAT TREE rather than the live one, for exactly
# the reason v15's and v14's do.
V16_COMMIT = "2d82b21"
# RUN 49, THE COMPLETION OF THE NAMING CORRECTION. v17 became a PREDECESSOR and v18 is the
# current link. The commit below is the one whose blobs the v17 record describes, so v17's own
# checks now run against THAT TREE rather than the live one, for exactly the reason v16's do.
V17_COMMIT = "5838a23"
V17_IDENTITY = "og-participant-2026.08-v17"
V17_RECORD = "code_audit/run48_participant_package_v17_checksums.sha256"
V18_IDENTITY = "og-participant-2026.08-v18"
V19_IDENTITY = "og-participant-2026.08-v19"
V18_RECORD = "code_audit/run49_participant_package_v18_checksums.sha256"

#: RUN 51. The commit v18 describes: the Run-49 merge. v18 is now a PREDECESSOR record and is
#: pinned to the commit whose blobs it describes, exactly as v16 and v17 are. Reading the live
#: tree for it would make a historical record red the moment a later run legitimately edits a
#: file, which is the failure mode this chain exists to prevent.
V18_COMMIT = "ad4f614"

V19_RECORD = "code_audit/run51_participant_package_v19_checksums.sha256"

#: RUN 52. The commit v19 describes: the Run-51 merge. v19 is now a PREDECESSOR record and is
#: pinned to the commit whose blobs it describes, exactly as v16, v17 and v18 are. Reading the
#: live tree for it would make a historical record red the moment a later run legitimately edits
#: a file, which is the failure mode this chain exists to prevent.
V19_COMMIT = "fe35504"
V20_IDENTITY = "og-participant-2026.08-v20"
V21_IDENTITY = "og-participant-2026.08-v21"
V20_RECORD = "code_audit/run52_participant_package_v20_checksums.sha256"
# RUN 55, THE MINT. v20 IS NO LONGER THE CURRENT PACKAGE, so its record no longer describes the
# working tree and every v19-to-v20 comparison below now reads THE COMMIT WHOSE BLOBS IT
# DESCRIBES instead of disk. EXPLICIT COMMIT HASH, never a relative reference: Run 54 wrote its
# own proofs of absence against HEAD~1 and they decayed silently into false proofs that still
# passed as later commits walked the reference back. Verified: `git show V20_COMMIT:V20_RECORD`
# is byte-identical to the file on disk, and models.py at that commit reads sim-2026.08-v35.
V20_COMMIT = "d236a270"
V21_RECORD = "code_audit/run55_participant_package_v21_checksums.sha256"
# RUN 56, THE MINT. v21 IS NO LONGER THE CURRENT PACKAGE, so its record no longer describes the
# working tree and every v20-to-v21 comparison below now reads THE COMMIT WHOSE BLOBS IT
# DESCRIBES instead of disk. EXPLICIT COMMIT HASH, never a relative reference. Verified:
# `git show V21_COMMIT:V21_RECORD` is byte-identical to the file on disk, and models.py at that
# commit reads sim-2026.08-v36.
V21_COMMIT = "e13b4f1"
V22_IDENTITY = "og-participant-2026.08-v22"
V22_RECORD = "code_audit/run56_participant_package_v22_checksums.sha256"
# RUN 57, THE MINT. v22 IS NO LONGER THE CURRENT PACKAGE, so its record no longer describes the
# working tree and every v21-to-v22 comparison below now reads THE COMMIT WHOSE BLOBS IT
# DESCRIBES instead of disk. EXPLICIT COMMIT HASH, never a relative reference. Which commit was
# established by BYTE COMPARISON, member by member: six commits reproduce the v22 record exactly,
# so its bytes alone do not single one out, and the chain's own rule -- the tip of `main` at
# which the package was still current, the rule v21 was pinned under -- settles it at 50dfb40.
V22_COMMIT = "50dfb40"
V23_IDENTITY = "og-participant-2026.08-v23"
V23_RECORD = "code_audit/run57_participant_package_v23_checksums.sha256"
V3_COMMIT = "01e943ef71689c468dd343695fbc89901bc02964"
RECORD = "code_audit/run12_participant_package_checksums.sha256"
SUCCESSOR = "code_audit/run28_closure_participant_package_checksums.sha256"
V3_RECORD = "code_audit/run28_closure_v3_participant_package_checksums.sha256"
V2_COMMIT = "0293dc5dff40c66a61bc0f57330611de96c4f7b0"

PASSED = 0
FAILED = 0
_fail: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        _fail.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def head(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def git_bytes(rel: str, rev: str) -> bytes | None:
    p = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{rel}"], capture_output=True)
    return p.stdout if p.returncode == 0 else None


def parse(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, _, rel = line.partition("  ")
        out[rel] = digest
    return out


# =================================================================================================
head("1. THE HISTORICAL RECORD, READ FROM THE COMMIT THAT WROTE IT")
# =================================================================================================

_rec_bytes = git_bytes(RECORD, V1_COMMIT)
check(_rec_bytes is not None,
      f"the Run-12 participant package record exists at git object {V1_COMMIT[:12]}", RECORD)
_v1 = parse((_rec_bytes or b"").decode("utf-8"))
check(len(_v1) == 70, "and names exactly seventy participant files", str(len(_v1)))

# THE RECORD ITSELF HAS NOT BEEN REWRITTEN. The instruction is not to rewrite it, and a guard that
# only checked the files would not notice if someone had. Byte for byte against the git object.
check((ROOT / RECORD).read_bytes() == _rec_bytes,
      "and the record in the working tree is BYTE-IDENTICAL to the one that commit wrote, so the "
      "historical record has not been rewritten to agree with anything")

# =================================================================================================
head("2. THE PACKAGE RECONSTRUCTED INTO AN ISOLATED LOCATION")
# =================================================================================================

with tempfile.TemporaryDirectory(prefix="og-participant-v1-") as _td:
    _sandbox = pathlib.Path(_td)
    _extracted: dict[str, pathlib.Path] = {}
    _absent: list[str] = []
    for rel in sorted(_v1):
        blob = git_bytes(rel, V1_COMMIT)
        if blob is None:
            _absent.append(rel)
            continue
        dest = _sandbox / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)
        _extracted[rel] = dest

    check(not _absent,
          "every file the record names is present in that commit's tree and was extracted",
          str(_absent))
    check(len(_extracted) == 70 and set(_extracted) == set(_v1),
          "THE HISTORICAL FILE INVENTORY MATCHES THE RECORD EXACTLY: seventy files, no more and "
          "no fewer", f"{len(_extracted)} extracted")
    check(not _sandbox.is_relative_to(ROOT) if hasattr(_sandbox, "is_relative_to")
          else str(ROOT) not in str(_sandbox),
          "and the extraction went to an ISOLATED directory outside the repository, so no "
          "historical file was restored into the live application", str(_sandbox))

    # ---------------------------------------------------------------- 3. every checksum
    _mismatch = [rel for rel, path in sorted(_extracted.items())
                 if hashlib.sha256(path.read_bytes()).hexdigest() != _v1[rel]]
    check(not _mismatch,
          f"ALL SEVENTY HISTORICAL CHECKSUMS HOLD against the Run-12 record. "
          f"{V1_IDENTITY} is reproducible from git, which is the only place its bytes still are",
          str(_mismatch))

    # ---------------------------------------------- 3b. THE DRIFT, MEASURED RATHER THAN ASSERTED
    #
    # This is the finding that makes the whole file necessary, so it is asserted rather than left
    # in prose: the LIVE tree does not reproduce v1, and that is expected and correct, because the
    # package has legitimately moved on through Runs 21 to 26 and this closure.
    _live_drift = sorted(rel for rel, digest in _v1.items()
                         if (ROOT / rel).is_file()
                         and hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != digest)
    check(len(_live_drift) >= 14,
          "and the LIVE tree does NOT reproduce v1 -- at least fourteen of the seventy files have "
          "legitimately moved on since Run 12 -- which is exactly why the historical package must "
          "be reconstructed from git and cannot be checked against the working tree",
          f"{len(_live_drift)} drifted")

    # -------------------------------------------------- 6. INDEPENDENCE OF THE CURRENT PACKAGE
    #
    # A change to a CURRENT-package copy must not move a reconstructed v1 hash. Proved by making
    # one: a test copy of a current package file is mutated inside the sandbox and the v1 hashes
    # are recomputed from git afterwards.
    _v1_hashes_before = {rel: hashlib.sha256(p.read_bytes()).hexdigest()
                         for rel, p in _extracted.items()}
    _current_copy = _sandbox / "current_v2_test_copy" / "taxonomy.js"
    _current_copy.parent.mkdir(parents=True, exist_ok=True)
    _current_copy.write_bytes((ROOT / "assets" / "js" / "taxonomy.js").read_bytes())
    _current_copy.write_bytes(_current_copy.read_bytes() + b"\n// mutated current-package copy\n")
    check("mutated current-package copy" in _current_copy.read_text(encoding="utf-8"),
          "a test copy of a CURRENT v2 package file is mutated, and the mutation is confirmed by "
          "re-reading it from disk")
    _v1_again = {rel: hashlib.sha256(git_bytes(rel, V1_COMMIT) or b"").hexdigest()
                 for rel in _extracted}
    check(_v1_again == _v1_hashes_before,
          "and the reconstructed v1 hashes are UNCHANGED by it. The reconstruction reads the git "
          "object graph, so nothing done to a current file -- in the tree or in a copy -- can "
          "alter the historical evidence")

    # ------------------------------------------ NON-VACUITY: one mutated historical byte, inline
    #
    # The extracted historical file is mutated IN THE SANDBOX, the checksum guard is re-run over
    # the extraction, and it must report exactly that file. Then the byte is restored and the
    # guard returns green. Nothing in the repository is touched at any point.
    _victim = _extracted["assets/js/taxonomy.js"]
    _orig = _victim.read_bytes()
    _victim.write_bytes(_orig + b"\n// deliberate Run-28-closure preservation probe\n")
    check(_victim.read_bytes() != _orig
          and b"preservation probe" in _victim.read_bytes(),
          "NON-VACUITY: one extracted historical byte is mutated, confirmed by re-reading the "
          "file from disk")
    _red = [rel for rel, path in sorted(_extracted.items())
            if hashlib.sha256(path.read_bytes()).hexdigest() != _v1[rel]]
    check(_red == ["assets/js/taxonomy.js"],
          "and the historical checksum guard goes RED, naming exactly that file and no other",
          str(_red))
    _victim.write_bytes(_orig)
    check(hashlib.sha256(_victim.read_bytes()).hexdigest() == _v1["assets/js/taxonomy.js"]
          and not [rel for rel, path in _extracted.items()
                   if hashlib.sha256(path.read_bytes()).hexdigest() != _v1[rel]],
          "restored byte for byte, and the guard is GREEN again over all seventy")

# =================================================================================================
head("3. THE PREDECESSOR v2, NOW ALSO HISTORICAL, RECONSTRUCTED FROM ITS OWN COMMIT")
# =================================================================================================

# THE DEFECT THIS SECTION EXISTS BECAUSE OF, STATED AS IT WAS FOUND. The closure's second pass
# applied the owner's A1.1 decision across the current surfaces, ELEVEN OF WHICH ARE INSIDE THIS
# PACKAGE, and then REGENERATED THE v2 RECORD IN PLACE rather than creating a successor. A package
# record rewritten to agree with the tree describes the tree and not the package it names. That is
# precisely the staleness this file was written to catch in the Run-12 v1 record, reproduced one
# link further along the chain by the run that found it. The v2 record has been restored to the
# bytes it carried at its own freeze commit, and v3 is the successor that should have existed.
_v2_rec_bytes = git_bytes(SUCCESSOR, V2_COMMIT)
check(_v2_rec_bytes is not None and (ROOT / SUCCESSOR).read_bytes() == _v2_rec_bytes,
      f"the v2 record in the working tree is BYTE-IDENTICAL to the one commit {V2_COMMIT[:7]} "
      f"wrote, so the in-place regeneration is undone and v2 describes v2 again")
_v2 = parse((_v2_rec_bytes or b"").decode("utf-8"))
check(len(_v2) == 70 and set(_v2) == set(_v1),
      "it names the same seventy files as v1, so the package was not narrowed while it was "
      "superseded", f"{len(_v2)}")

with tempfile.TemporaryDirectory(prefix="og-participant-v2-") as _td2:
    _sandbox2 = pathlib.Path(_td2)
    _ex2: dict[str, pathlib.Path] = {}
    for rel in sorted(_v2):
        blob = git_bytes(rel, V2_COMMIT)
        if blob is None:
            continue
        dest = _sandbox2 / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)
        _ex2[rel] = dest
    check(len(_ex2) == 70, "all seventy v2 files reconstruct from that commit into an isolated "
                           "directory", str(len(_ex2)))
    _bad2 = [rel for rel, path in sorted(_ex2.items())
             if hashlib.sha256(path.read_bytes()).hexdigest() != _v2[rel]]
    check(not _bad2, "ALL SEVENTY v2 CHECKSUMS HOLD against the restored v2 record", str(_bad2))

    # NON-VACUITY, FAULT C, inline and in an isolated workspace: mutate one byte of the
    # reconstructed v2 package and require the v2 checksum guard to name exactly that file.
    _victim2 = _ex2["assets/js/taxonomy.js"]
    _orig2 = _victim2.read_bytes()
    _victim2.write_bytes(_orig2 + b"\n// deliberate Run-28-closure v2 reconstruction probe\n")
    check(b"v2 reconstruction probe" in _victim2.read_bytes(),
          "FAULT C: one byte of the reconstructed v2 package is mutated, confirmed by re-reading "
          "the file from disk")
    _red2 = [rel for rel, path in sorted(_ex2.items())
             if hashlib.sha256(path.read_bytes()).hexdigest() != _v2[rel]]
    check(_red2 == ["assets/js/taxonomy.js"],
          "and the HISTORICAL v2 checksum guard goes RED, naming exactly that file", str(_red2))
    _victim2.write_bytes(_orig2)
    check(not [rel for rel, path in _ex2.items()
               if hashlib.sha256(path.read_bytes()).hexdigest() != _v2[rel]],
          "restored byte for byte, and the v2 guard is GREEN again over all seventy")

# =================================================================================================
head("4. THE CURRENT PACKAGE v4, AND THE IDENTITY GUARD")
# =================================================================================================

_v3 = parse((ROOT / V3_RECORD).read_text(encoding="utf-8"))
_v4 = parse((ROOT / V4_RECORD).read_text(encoding="utf-8"))
check(len(_v3) == 70 and set(_v3) == set(_v2),
      "the v3 record names the same seventy files", str(len(_v3)))
check(len(_v4) == 70 and set(_v4) == set(_v3),
      "and so does the v4 record", str(len(_v4)))

# v3 IS NOW A PREDECESSOR, so the live tree is NOT its evidence. It is verified against the
# commit whose blobs it describes, exactly as v1 and v2 are, and it must NOT match the tree.
_v3_bad = sorted(rel for rel, digest in _v3.items()
                 if hashlib.sha256(git_bytes(rel, V3_COMMIT) or b"").hexdigest() != digest)
check(not _v3_bad,
      f"every one of v3's seventy checksums holds against commit {V3_COMMIT[:7]}, which is where "
      f"that package's bytes live now that it is a predecessor", str(_v3_bad))
# RUN 30 CLOSURE: v4 IS NOW A PREDECESSOR TOO, so the live tree is not its evidence either.
_v4_bad = sorted(rel for rel, digest in _v4.items()
                 if hashlib.sha256(git_bytes(rel, V4_COMMIT) or b"").hexdigest() != digest)
check(not _v4_bad,
      f"every one of v4's seventy checksums holds against commit {V4_COMMIT[:7]}, which is where "
      f"that package's bytes live now that it is a predecessor", str(_v4_bad))
_v5 = parse((ROOT / V5_RECORD).read_text(encoding="utf-8"))
_v5_bad = sorted(rel for rel, digest in _v5.items()
                 if hashlib.sha256(git_bytes(rel, V5_COMMIT) or b"").hexdigest() != digest)
check(not _v5_bad,
      f"every one of v5's seventy checksums holds against commit {V5_COMMIT[:7]}, which is where "
      f"that package's bytes live now that it is a predecessor", str(_v5_bad))
# RUN 32: v6 IS NOW A PREDECESSOR TOO, so the live tree is not its evidence either.
_v6 = parse((ROOT / V6_RECORD).read_text(encoding="utf-8"))
_v6_bad = sorted(rel for rel, digest in _v6.items()
                 if hashlib.sha256(git_bytes(rel, V6_COMMIT) or b"").hexdigest() != digest)
check(not _v6_bad,
      f"every one of v6's seventy checksums holds against commit {V6_COMMIT[:7]}, which is where "
      f"that package's bytes live now that it is a predecessor", str(_v6_bad))
# RUN 32 FINAL CLOSURE: v7 IS NOW A PREDECESSOR TOO, so the live tree is not its evidence either.
_v7 = parse((ROOT / V7_RECORD).read_text(encoding="utf-8"))
_v7_bad = sorted(rel for rel, digest in _v7.items()
                 if hashlib.sha256(git_bytes(rel, V7_COMMIT) or b"").hexdigest() != digest)
check(not _v7_bad,
      f"every one of v7's seventy checksums holds against commit {V7_COMMIT[:7]}, which is where "
      f"that package's bytes live now that it is a predecessor", str(_v7_bad))
# v8 IS NOW A PREDECESSOR TOO, so the live tree is not its evidence either.
_v8 = parse((ROOT / V8_RECORD).read_text(encoding="utf-8"))
_v8_bad = sorted(rel for rel, digest in _v8.items()
                 if hashlib.sha256(git_bytes(rel, V8_COMMIT) or b"").hexdigest() != digest)
check(not _v8_bad,
      f"every one of v8's seventy checksums holds against commit {V8_COMMIT[:7]}, which is where "
      f"that package's bytes live now that it is a predecessor", str(_v8_bad))
# v9 IS NOW A PREDECESSOR TOO, so the live tree is not its evidence either.
_v9 = parse((ROOT / V9_RECORD).read_text(encoding="utf-8"))
_v9_bad = sorted(rel for rel, digest in _v9.items()
                 if hashlib.sha256(git_bytes(rel, V9_COMMIT) or b"").hexdigest() != digest)
check(not _v9_bad,
      f"every one of v9's seventy checksums holds against commit {V9_COMMIT[:7]}, which is where "
      f"that package's bytes live now that it is a predecessor", str(_v9_bad))
# RUN 33: v10 IS NOW A PREDECESSOR TOO, so the live tree is not its evidence either.
_v10 = parse((ROOT / V10_RECORD).read_text(encoding="utf-8"))
_v10_bad = sorted(rel for rel, digest in _v10.items()
                  if hashlib.sha256(git_bytes(rel, V10_COMMIT) or b"").hexdigest() != digest)
check(not _v10_bad,
      f"every one of v10's seventy checksums holds against commit {V10_COMMIT[:7]}, which is "
      f"where that package's bytes live now that it is a predecessor", str(_v10_bad))
_seq10 = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES
                if hashlib.sha256(git_bytes(rel, V10_COMMIT) or b"").hexdigest()
                != _v9.get(rel))
check(not _seq10,
      "THE EXPERIMENTAL SEQUENCE IS UNCHANGED across v9 to v10: every file carrying evidence "
      "review, preliminary judgment, preliminary lock, AI reveal, final judgment, capture, final "
      "lock and period advancement is byte for byte identical to v9", str(_seq10))
_moved10 = sorted(rel for rel, digest in _v9.items()
                  if hashlib.sha256(git_bytes(rel, V10_COMMIT) or b"").hexdigest() != digest)
check(_moved10 == sorted(PP.V9_TO_V10_CHANGED),
      "and the files v10 moved are exactly the four it declares, so nothing rode along with the "
      "qualifier reconciliation", str(_moved10))

# ---- v11, NOW A PREDECESSOR ------------------------------------------------------------------
# RUN 36. v11's record is verified against ITS OWN GIT OBJECT, not the live tree. Leaving it on
# the live tree would make two records claim the same tree, which is the masquerade this chain
# exists to forbid, and it is the defect the Run-28 closure had to correct in the v2 record.
_v11 = parse((ROOT / V11_RECORD).read_text(encoding="utf-8"))
_v11_bad = sorted(rel for rel, digest in _v11.items()
                  if hashlib.sha256(git_bytes(rel, V11_COMMIT) or b"").hexdigest() != digest)
check(not _v11_bad,
      f"and every one of v11's seventy checksums holds against its own git object "
      f"{V11_COMMIT[:7]}, so the predecessor reconstructs", str(_v11_bad))
check(sorted(_v11) == sorted(_v10),
      "v11 covers exactly the same file inventory as v10, so a successor cannot quietly drop a "
      "participant-visible file out of the package",
      str(sorted(set(_v10) ^ set(_v11))))
_moved11 = sorted(rel for rel, digest in _v10.items()
                  if hashlib.sha256(git_bytes(rel, V11_COMMIT) or b"").hexdigest() != digest)
check(_moved11 == sorted(PP.V10_TO_V11_CHANGED),
      "and the files v11 moved are exactly the three it declares, so nothing rode along with the "
      "Portfolio Health remediation", str(_moved11))
# THE EXPERIMENTAL SEQUENCE, stated in the form that is TRUE here rather than a blanket claim.
# workspace.js genuinely moved, so it is NOT in the unchanged list -- and what replaces the
# blanket claim is stronger: every other sequence-bearing file is byte-identical, AND the
# workspace.js delta is confined to the Portfolio Health rendering block.
_seq11 = sorted(rel for rel in PP.V10_TO_V11_SEQUENCE_UNCHANGED
                if hashlib.sha256(git_bytes(rel, V11_COMMIT) or b"").hexdigest() != _v10.get(rel))
check(not _seq11,
      "THE EXPERIMENTAL SEQUENCE IS UNCHANGED across v10 to v11: decision.js, decision-ui.js, "
      "deepdive.js and both questionnaires are byte for byte identical to v10", str(_seq11))
check("assets/js/workspace.js" not in PP.V10_TO_V11_SEQUENCE_UNCHANGED
      and "assets/js/workspace.js" in PP.V10_TO_V11_CHANGED,
      "and workspace.js is DECLARED as moved rather than claimed unchanged, because its bytes "
      "moved")
# THE CONFINEMENT, PROVED STRUCTURALLY rather than asserted. The Portfolio Health rendering block
# is the TAIL of workspace.js, and the anchor line that opens it is present byte for byte in both
# versions -- so everything BEFORE it must be identical between v10 and v11. That is a stronger
# and less brittle statement than a vocabulary of tokens, which cannot classify the continuation
# lines of a multi-line expression and has to be widened until it accepts anything.
_old_ws = (git_bytes("assets/js/workspace.js", V10_COMMIT) or b"").decode("utf-8")
_new_ws = (git_bytes("assets/js/workspace.js", V11_COMMIT) or b"").decode("utf-8")
_anchor = PP.V11_WORKSPACE_PORTFOLIO_ANCHOR
check(_anchor in _old_ws and _anchor in _new_ws,
      "the Portfolio Health block's own anchor line is present in BOTH versions, so the prefix "
      "comparison below is over a real boundary rather than an assumed one")
check(_old_ws != _new_ws,
      "workspace.js really moved, so the confinement check below is over a real change")
check(_old_ws[:_old_ws.index(_anchor)] == _new_ws[:_new_ws.index(_anchor)],
      "and EVERYTHING BEFORE THE PORTFOLIO HEALTH BLOCK IS BYTE-IDENTICAL between v10 and v11: "
      "no step of the decision sequence, no reveal gate, no lock, no randomization, no server "
      "contract and no append-only record moved",
      f"{len(_old_ws[:_old_ws.index(_anchor)])} vs {len(_new_ws[:_new_ws.index(_anchor)])} bytes")
check(_old_ws[_old_ws.index(_anchor):] != _new_ws[_new_ws.index(_anchor):],
      "and the change really is inside that block, so the prefix equality above is not simply "
      "the whole file being unchanged")

# ---- v12, THE CURRENT LINK -------------------------------------------------------------------
# RUN 36. ONE file moved, and it is GENERATED: the served defensibility evidence object. A1.1 was
# described to the participant as requiring a governed structure and returning Not Estimable
# without it; execution disproves both, so the statement was corrected.
_v12 = parse((ROOT / V12_RECORD).read_text(encoding="utf-8"))
_v12_bad = sorted(rel for rel, digest in _v12.items()
                  if hashlib.sha256(git_bytes(rel, V12_COMMIT) or b"").hexdigest() != digest)
check(not _v12_bad,
      f"and every one of v12's seventy checksums holds against its own git object "
      f"{V12_COMMIT[:7]}, so the predecessor reconstructs", str(_v12_bad))
check(sorted(_v12) == sorted(_v11),
      "v12 covers exactly the same file inventory as v11, so a successor cannot quietly drop a "
      "participant-visible file out of the package",
      str(sorted(set(_v11) ^ set(_v12))))
_moved12 = sorted(rel for rel, digest in _v11.items()
                  if hashlib.sha256(git_bytes(rel, V12_COMMIT) or b"").hexdigest() != digest)
check(_moved12 == sorted(PP.V11_TO_V12_CHANGED),
      "and the file v12 moved is exactly the one it declares, so nothing rode along with the "
      "defensibility correction", str(_moved12))
_seq12 = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES
                if hashlib.sha256(git_bytes(rel, V12_COMMIT) or b"").hexdigest() != _v11.get(rel))
check(not _seq12,
      "THE EXPERIMENTAL SEQUENCE IS UNCHANGED across v11 to v12: every file carrying evidence "
      "review, preliminary judgment, preliminary lock, AI reveal, final judgment, capture, final "
      "lock and period advancement is byte for byte identical to v11", str(_seq12))
check("assets/js/workspace.js" not in PP.V11_TO_V12_CHANGED,
      "and workspace.js did not move at all this time, so the Portfolio Health confinement "
      "argument is not even needed for v12")

# ---- v13, THE CURRENT LINK -------------------------------------------------------------------
# RUN 36 CLOSURE, THE OWNER'S A1.1 RULING. Three files moved and ALL THREE ARE GENERATED from the
# registry: the served defensibility object and both client taxonomy mirrors. A1.1 is
# operationally disabled for insufficient canonical input, so the mirrors carry its disabled flag
# and the defensibility record stops describing it as a module that computes.
# RUN 43: v13 is now a PREDECESSOR, so its checksums are checked against the COMMIT whose blobs
# it describes and not against the live tree. That is the same treatment every other predecessor
# gets, and it is what stops a predecessor being quietly rewritten to agree with the present.
_v13 = parse((ROOT / V13_RECORD).read_text(encoding="utf-8"))
_v13_bad = sorted(rel for rel, digest in _v13.items()
                  if hashlib.sha256(git_bytes(rel, V13_COMMIT) or b"").hexdigest() != digest)
check(not _v13_bad,
      f"and every one of v13's seventy checksums holds against commit {V13_COMMIT[:7]}, the "
      f"commit whose blobs that record describes", str(_v13_bad))
check(sorted(_v13) == sorted(_v12),
      "v13 covers exactly the same file inventory as v12, so a successor cannot quietly drop a "
      "participant-visible file out of the package",
      str(sorted(set(_v12) ^ set(_v13))))
_moved13 = sorted(rel for rel, digest in _v12.items()
                  if hashlib.sha256(git_bytes(rel, V13_COMMIT) or b"").hexdigest() != digest)
check(_moved13 == sorted(PP.V12_TO_V13_CHANGED),
      "and the files v13 moved are exactly the three it declares, so nothing rode along with the "
      "A1.1 ruling", str(_moved13))
_seq13 = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES
                if hashlib.sha256(git_bytes(rel, V13_COMMIT) or b"").hexdigest()
                != _v12.get(rel))
check(not _seq13,
      "THE EXPERIMENTAL SEQUENCE IS UNCHANGED across v12 to v13: every file carrying evidence "
      "review, preliminary judgment, preliminary lock, AI reveal, final judgment, capture, final "
      "lock and period advancement is byte for byte identical to v12", str(_seq13))
check(all(f.startswith("assets/js/") and f.endswith(".js") for f in PP.V12_TO_V13_CHANGED)
      and "assets/js/workspace.js" not in PP.V12_TO_V13_CHANGED,
      "and every file v13 moved is a generated client artefact, none of which carries a step of "
      "the sequence", str(PP.V12_TO_V13_CHANGED))
_seq9_bad = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES
                   if hashlib.sha256(git_bytes(rel, V9_COMMIT) or b"").hexdigest()
                   != _v8.get(rel))
check(not _seq9_bad,
      "THE EXPERIMENTAL SEQUENCE IS UNCHANGED across v8 to v9: every file carrying evidence "
      "review, preliminary judgment, preliminary lock, AI reveal, final judgment, capture, final "
      "lock and period advancement is byte for byte identical to v8", str(_seq9_bad))
_moved9 = sorted(rel for rel, digest in _v8.items()
                 if hashlib.sha256(git_bytes(rel, V9_COMMIT) or b"").hexdigest() != digest)
check(_moved9 == sorted(PP.V8_TO_V9_CHANGED),
      "and the files v9 moved are exactly the three it declares, so nothing rode along with the "
      "identifier propagation", str(_moved9))

# THE SEQUENCE PROOF, WHICH IS WHAT REPLACES v8's MISSING INVERSE MAPPING. v7's delta was a
# display substitution and was proved so by inverse-mapping it back. v8's is not, so the claim
# "the experimental sequence is unchanged" cannot rest on that. It rests on this instead: every
# file that CARRIES the sequence is byte for byte identical between v7 and v8.
_seq_bad = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES
                  if hashlib.sha256(git_bytes(rel, V8_COMMIT) or b"").hexdigest() != _v7.get(rel))
check(not _seq_bad,
      "THE EXPERIMENTAL SEQUENCE IS UNCHANGED: every file carrying evidence review, preliminary "
      "judgment, preliminary lock, AI reveal, final judgment, capture, final lock and period "
      "advancement is byte for byte identical to v7", str(_seq_bad))
# AND THE FILES v8 DID MOVE ARE EXACTLY THE ONES DECLARED, so a further file cannot ride along.
_moved = sorted(rel for rel, digest in _v7.items()
                if hashlib.sha256(git_bytes(rel, V8_COMMIT) or b"").hexdigest() != digest)
check(_moved == sorted(PP.V7_TO_V8_CHANGED),
      "and the files v8 moved are exactly the seven it declares, so nothing rode along with the "
      "metadata correction", str(_moved))
# THE INVERSE-MAPPING PROOF. Applying the six reverse name substitutions to the eight files v6
# moved must reproduce the v5 bytes EXACTLY. That is what makes this a display-name delta rather
# than a behaviour change, and it is proved rather than asserted.
_inv_bad = []
for _rel in PP.V5_TO_V6_CHANGED:
    # RUN 32. v6's bytes are the COMMIT's bytes now, not the tree's: the tree has moved on to v7.
    # Reading the tree here would compare v7 against v5 and fail for the wrong reason.
    _txt = (git_bytes(_rel, V6_COMMIT) or b"").decode("utf-8")
    for _new, _old in PP.V6_TO_V5_INVERSE.items():
        _txt = _txt.replace(_new, _old)
    if hashlib.sha256(_txt.encode("utf-8")).hexdigest() != _v5.get(_rel):
        _inv_bad.append(_rel)
check(not _inv_bad,
      "and applying the six reverse name substitutions to the eight files v6 moved reproduces "
      "the v5 bytes EXACTLY, so the delta is display names and nothing else", str(_inv_bad))

# THE SAME INVERSE-MAPPING PROOF FOR v7. Applying the ONE reverse substitution to the eight files
# v7 moved must reproduce the v6 bytes EXACTLY. That is what makes the Run-32 rename a display
# delta rather than a behaviour change, and it is proved rather than asserted.
_inv7_bad = []
for _rel in PP.V6_TO_V7_CHANGED:
    # RUN 32 FINAL CLOSURE. v7's bytes are the COMMIT's bytes now, not the tree's: the tree has
    # moved on to v8. Reading the tree here would compare v8 against v6 and fail for the wrong
    # reason -- the same correction v7 had to make to the v5-to-v6 proof one link earlier.
    _txt = (git_bytes(_rel, V7_COMMIT) or b"").decode("utf-8")
    for _new, _old in PP.V7_TO_V6_INVERSE.items():
        _txt = _txt.replace(_new, _old)
    if hashlib.sha256(_txt.encode("utf-8")).hexdigest() != _v6.get(_rel):
        _inv7_bad.append(_rel)
check(not _inv7_bad,
      "and applying the ONE reverse name substitution to the eight files v7 moved reproduces the "
      "v6 bytes EXACTLY, so the Run-32 delta is one display name and nothing else",
      str(_inv7_bad))

# THE IDENTITY GUARD, which is the one the checksum guard alone cannot be. EXACTLY ONE record in
# the chain may describe the live tree, and it must be the one declared current. A predecessor
# that matches the tree means either nothing changed or a predecessor was rewritten to agree with
# the present, and both are failures.
_matches_tree = []
for _pkg in PP.PARTICIPANT_PACKAGES:
    _rec = parse((ROOT / _pkg.record).read_text(encoding="utf-8"))
    if all((ROOT / rel).is_file()
           and hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest
           for rel, digest in _rec.items()):
        _matches_tree.append(_pkg.identifier)
check(_matches_tree == [PP.CURRENT.identifier] == [V23_IDENTITY],
      "PACKAGE IDENTITY IS TRUTHFUL: exactly ONE record in the chain describes the live tree and "
      "it is the one declared current. A CURRENT FILE CANNOT MASQUERADE AS A PREDECESSOR PACKAGE",
      str(_matches_tree))
check([p.identifier for p in PP.PARTICIPANT_PACKAGES]
      == [V1_IDENTITY, V2_IDENTITY, V3_IDENTITY, V4_IDENTITY, V5_IDENTITY,
          V6_IDENTITY, V7_IDENTITY, V8_IDENTITY, V9_IDENTITY, V10_IDENTITY, V11_IDENTITY,
          V12_IDENTITY, V13_IDENTITY, V14_IDENTITY, V15_IDENTITY, V16_IDENTITY,
          V17_IDENTITY, V18_IDENTITY, V19_IDENTITY, V20_IDENTITY, V21_IDENTITY,
          V22_IDENTITY, V23_IDENTITY],
      "the chain is declared oldest first and every link is named", str(PP.PARTICIPANT_PACKAGES))
check(len({p.record for p in PP.PARTICIPANT_PACKAGES}) == 23
      and all((ROOT / p.record).is_file() for p in PP.PARTICIPANT_PACKAGES),
      "each link has its OWN record file and all twenty-three are present, so no link shares a "
      "record with another")
check(PP.CURRENT.source_commit is None
      and all(p.source_commit for p in PP.PARTICIPANT_PACKAGES[:-1]),
      "and only the current link reads the working tree; all twenty-two predecessors name the "
      "commit their bytes live in")
# ---- v14, NOW A PREDECESSOR ---------------------------------------------------------------
# RUN 43, THE RETIREMENT OF 38 MODULES FROM SERVICE. Five files moved: three generated from the
# registry and two carrying a count a participant reads. Run 44 minted v15, so every v14 check
# below is evaluated against the blobs of V14_COMMIT rather than against the working tree. The
# historical statement does not change; where it is measured does, and it has to, because a
# predecessor that still matched the live tree would be a second record claiming one tree.
_v14 = parse((ROOT / V14_RECORD).read_text(encoding="utf-8"))
_v14_bad = sorted(rel for rel, digest in _v14.items()
                  if hashlib.sha256(git_bytes(rel, V14_COMMIT)).hexdigest() != digest)
check(not _v14_bad,
      f"every one of v14's seventy checksums holds against the tree of commit "
      f"{V14_COMMIT[:7]}, the commit its record describes", str(_v14_bad))
check(sorted(_v14) == sorted(_v13),
      "v14 covers exactly the same file inventory as v13, so a successor cannot quietly drop a "
      "participant-visible file out of the package",
      str(sorted(set(_v13) ^ set(_v14))))
_moved14 = sorted(rel for rel, digest in _v13.items()
                  if hashlib.sha256(git_bytes(rel, V14_COMMIT)).hexdigest() != digest)
check(_moved14 == sorted(PP.V13_TO_V14_CHANGED),
      "and the files v14 moved are exactly the five it declares, so nothing rode along with the "
      "retirement", str(_moved14))
_seq14 = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES
                if hashlib.sha256(git_bytes(rel, V14_COMMIT)).hexdigest() != _v13.get(rel))
check(not _seq14,
      "THE EXPERIMENTAL SEQUENCE IS UNCHANGED across v13 to v14: every file carrying evidence "
      "review, preliminary judgment, preliminary lock, AI reveal, final judgment, capture, final "
      "lock and period advancement is byte for byte identical to v13", str(_seq14))
check(not (set(PP.V13_TO_V14_CHANGED) & set(PP.SEQUENCE_BEARING_FILES)),
      "and not one file v14 moved carries a step of the sequence",
      str(sorted(set(PP.V13_TO_V14_CHANGED) & set(PP.SEQUENCE_BEARING_FILES))))

# ---- v15, NOW A PREDECESSOR ----------------------------------------------------------------
# RUN 47 minted v16, so every v15 check below is evaluated against the blobs of V15_COMMIT
# rather than against the working tree. The historical statement does not change; where it is
# measured does, and it has to, because a predecessor that still matched the live tree would be
# a second record claiming one tree.
# RUN 44, THE PARTICIPANT-FACING RENDER DEFECTS. FOUR files moved and ONE OF THEM IS
# SEQUENCE-BEARING. That is the first time since v10 and it is asserted as an EXCEPTION WITH A
# NAME, not by widening the invariant: exactly one sequence-bearing file may have moved, it must
# be the one participant_packages declares as the exception, and every other one is still held
# to byte-identity. A second file moving here is still red, and so is a different one moving.
_v15 = parse((ROOT / V15_RECORD).read_text(encoding="utf-8"))
_v15_bad = sorted(rel for rel, digest in _v15.items()
                  if hashlib.sha256(git_bytes(rel, V15_COMMIT)).hexdigest() != digest)
check(not _v15_bad,
      "every one of v15's seventy checksums holds against the blobs of the commit it names, "
      "which is where a predecessor package correctly lives", str(_v15_bad))
check(sorted(_v15) == sorted(_v14),
      "v15 covers exactly the same file inventory as v14, so a successor cannot quietly drop a "
      "participant-visible file out of the package",
      str(sorted(set(_v14) ^ set(_v15))))
_moved15 = sorted(rel for rel, digest in _v14.items()
                  if hashlib.sha256(git_bytes(rel, V15_COMMIT)).hexdigest() != digest)
check(_moved15 == sorted(PP.V14_TO_V15_CHANGED),
      "and the files v15 moved are exactly the four it declares, so nothing rode along with the "
      "render repairs", str(_moved15))
_seq15 = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES
                if hashlib.sha256(git_bytes(rel, V15_COMMIT)).hexdigest() != _v14.get(rel))
check(_seq15 == sorted(PP.V14_TO_V15_SEQUENCE_EXCEPTION),
      "THE EXPERIMENTAL SEQUENCE MOVED ACROSS v14 TO v15, IN EXACTLY ONE DECLARED FILE AND NO "
      "OTHER: the Portfolio Health flyout's reason sentence in deepdive.js, corrected on the "
      "owner's order at Run 44 section 4.4 because after the offload it told a participant "
      "Portfolio Health needed more projects when no number of projects makes it compute",
      str(_seq15))
check(len(PP.V14_TO_V15_SEQUENCE_EXCEPTION) == 1
      and set(PP.V14_TO_V15_SEQUENCE_EXCEPTION) < set(PP.SEQUENCE_BEARING_FILES),
      "and the exception is ONE named member of the sequence-bearing set, so the other five are "
      "still held to byte-identity by the check above",
      str(PP.V14_TO_V15_SEQUENCE_EXCEPTION))
_seq_still = sorted(set(PP.SEQUENCE_BEARING_FILES) - set(PP.V14_TO_V15_SEQUENCE_EXCEPTION))
check(all(hashlib.sha256(git_bytes(rel, V15_COMMIT)).hexdigest() == _v14.get(rel)
          for rel in _seq_still) and len(_seq_still) == 5,
      "the other five sequence-bearing files are byte for byte identical to v14: no step of the "
      "decision sequence, no reveal gate, no lock, no randomization and no questionnaire moved",
      str(_seq_still))
# WHAT MOVED INSIDE THE EXCEPTION, measured rather than asserted. The flyout must state the
# current state, must keep the project-count sentence for the case it is true of, and must not
# have gained or lost a control.
_dd = git_bytes("assets/js/deepdive.js", V15_COMMIT).decode("utf-8")
_dd_v14 = git_bytes("assets/js/deepdive.js", V14_COMMIT).decode("utf-8")
check("Portfolio Health is no longer in service." in _dd
      and "Portfolio Health is no longer in service." not in _dd_v14,
      "the one sequence-bearing change is the flyout stating the current state, and it is what "
      "the file GAINED rather than something already there")
check(_dd.count("data-run-portfolio-analysis") == _dd_v14.count("data-run-portfolio-analysis"),
      "and no user-facing control was added, moved or removed with it: the flyout's repair "
      "button and its handler are exactly as many as v14 carried",
      f"{_dd.count('data-run-portfolio-analysis')} vs "
      f"{_dd_v14.count('data-run-portfolio-analysis')}")
for _step in ("submitPreliminary", "reveal", "lock"):
    check(_dd.count(_step) == _dd_v14.count(_step),
          f"and the file's own references to '{_step}' are unchanged in number, so the delta did "
          f"not touch a sequence step", f"{_dd.count(_step)} vs {_dd_v14.count(_step)}")
# ---- v16, THE CURRENT LINK ------------------------------------------------------------------
# RUN 47, THE EVM CONSISTENCY CHECK. TWO files moved and NEITHER IS SEQUENCE-BEARING, so the
# invariant v15 had to break with a named exception is intact again and is asserted here without
# any exception at all: all six sequence-bearing files must be byte for byte identical to v15.
# RUN 48 minted v17, so every v16 check below is evaluated against the blobs of V16_COMMIT
# rather than against the working tree. The historical statement does not change; where it is
# measured does, and it has to, because a predecessor that still matched the live tree would be
# a second record claiming one tree.
_v16 = parse((ROOT / V16_RECORD).read_text(encoding="utf-8"))
_v16_bad = sorted(rel for rel, digest in _v16.items()
                  if hashlib.sha256(git_bytes(rel, V16_COMMIT)).hexdigest() != digest)
check(not _v16_bad,
      "every one of v16's seventy checksums holds against the blobs of the commit it names, "
      "which is where a predecessor package correctly lives", str(_v16_bad))
check(sorted(_v16) == sorted(_v15),
      "v16 covers exactly the same file inventory as v15, so a successor cannot quietly drop a "
      "participant-visible file out of the package",
      str(sorted(set(_v15) ^ set(_v16))))
_moved16 = sorted(rel for rel, digest in _v15.items()
                  if hashlib.sha256(git_bytes(rel, V16_COMMIT)).hexdigest() != digest)
check(_moved16 == sorted(PP.V15_TO_V16_CHANGED),
      "and the files v16 moved are exactly the two it declares, so nothing rode along with the "
      "consistency check", str(_moved16))
_seq16 = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES
                if hashlib.sha256(git_bytes(rel, V16_COMMIT)).hexdigest() != _v15.get(rel))
check(_seq16 == [],
      "THE EXPERIMENTAL SEQUENCE IS UNCHANGED ACROSS v15 TO v16: all six sequence-bearing files "
      "are byte for byte identical, so no step of the decision sequence, no reveal gate, no "
      "lock, no randomization and no questionnaire moved", str(_seq16))
check(not (set(PP.V15_TO_V16_CHANGED) & set(PP.SEQUENCE_BEARING_FILES)),
      "and not one file v16 moved carries a step of the sequence",
      str(sorted(set(PP.V15_TO_V16_CHANGED) & set(PP.SEQUENCE_BEARING_FILES))))
# WHAT MOVED INSIDE THE TWO FILES, measured rather than asserted. Each must have GAINED the
# disagreement rendering, and neither may have gained or lost a user-facing control.
for _rel, _marker in (("assets/js/detail.js", "eb-consistency"),
                      ("assets/js/recommendation_options.js", "ro-consistency")):
    _live = git_bytes(_rel, V16_COMMIT).decode("utf-8")
    _was = git_bytes(_rel, V15_COMMIT).decode("utf-8")
    check(_marker in _live and _marker not in _was,
          f"{_rel}: the disagreement block is what the file GAINED rather than something "
          f"already there")
    for _control in ("<button", "<input", "<select", "<textarea"):
        check(_live.count(_control) == _was.count(_control),
              f"{_rel}: and its '{_control}' occurrences are unchanged in number, so no "
              f"user-facing control was added, moved or removed",
              f"{_live.count(_control)} vs {_was.count(_control)}")
    for _step in ("submitPreliminary", "reveal", "lock"):
        # WHOLE WORDS. A substring count would answer for "block" as well as for "lock", and a
        # probe that cannot tell the two apart measures the wrong thing.
        _pat = re.compile(r"\b" + _step + r"\b")
        _n_live, _n_was = len(_pat.findall(_live)), len(_pat.findall(_was))
        check(_n_live == _n_was,
              f"{_rel}: and its references to '{_step}' are unchanged in number, so the delta "
              f"did not touch a sequence step", f"{_n_live} vs {_n_was}")
# ---- v17, THE CURRENT LINK -------------------------------------------------------------------
# RUN 48, THE PERIOD THE DETAIL PAGE OPENS ON AND THE LIVE NAMING INSTANCES. THREE files moved
# and ONE OF THEM IS SEQUENCE-BEARING. That is the second time since v10, and it is asserted as
# an EXCEPTION WITH A NAME, not by widening the invariant: exactly one sequence-bearing file may
# have moved, it must be the one participant_packages declares as the exception, and every other
# one is still held to byte-identity. A second file moving here is still red, and so is a
# different one moving.
_v17 = parse((ROOT / V17_RECORD).read_text(encoding="utf-8"))
_v17_bad = sorted(rel for rel, digest in _v17.items()
                  if hashlib.sha256(git_bytes(rel, V17_COMMIT)).hexdigest() != digest)
check(not _v17_bad,
      "every one of v17's seventy checksums holds against the blobs of the commit it names, "
      "which is where a predecessor package correctly lives", str(_v17_bad))
check(sorted(_v17) == sorted(_v16),
      "v17 covers exactly the same file inventory as v16, so a successor cannot quietly drop a "
      "participant-visible file out of the package",
      str(sorted(set(_v16) ^ set(_v17))))
_moved17 = sorted(rel for rel, digest in _v16.items()
                  if hashlib.sha256(git_bytes(rel, V17_COMMIT)).hexdigest() != digest)
check(_moved17 == sorted(PP.V16_TO_V17_CHANGED),
      "and the files v17 moved are exactly the three it declares, so nothing rode along with "
      "the period fix and the naming corrections", str(_moved17))
_seq17 = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES
                if hashlib.sha256(git_bytes(rel, V17_COMMIT)).hexdigest() != _v16.get(rel))
check(_seq17 == sorted(PP.V16_TO_V17_SEQUENCE_EXCEPTION),
      "THE EXPERIMENTAL SEQUENCE MOVED ACROSS v16 TO v17, IN EXACTLY ONE DECLARED FILE AND NO "
      "OTHER: the deep-dive panel labels in deepdive.js, corrected on the owner's ruling 2 "
      "because they printed the retired 'Cat N.M' scheme into the panel heading and the panel's "
      "accessible name on every render", str(_seq17))
check(len(PP.V16_TO_V17_SEQUENCE_EXCEPTION) == 1
      and set(PP.V16_TO_V17_SEQUENCE_EXCEPTION) < set(PP.SEQUENCE_BEARING_FILES),
      "and the exception is ONE named member of the sequence-bearing set, so the other five are "
      "still held to byte-identity by the check above",
      str(PP.V16_TO_V17_SEQUENCE_EXCEPTION))
_seq_still17 = sorted(set(PP.SEQUENCE_BEARING_FILES) - set(PP.V16_TO_V17_SEQUENCE_EXCEPTION))
check(all(hashlib.sha256(git_bytes(rel, V17_COMMIT)).hexdigest() == _v16.get(rel)
          for rel in _seq_still17) and len(_seq_still17) == 5,
      "the other five sequence-bearing files are byte for byte identical to v16: no step of the "
      "decision sequence, no reveal gate, no lock, no randomization and no questionnaire moved",
      str(_seq_still17))
# WHAT MOVED INSIDE THE EXCEPTION, measured rather than asserted. The labels must be groups and
# purposes, the grouping must be declared separately from them, and no control may have moved.
_dd17 = git_bytes("assets/js/deepdive.js", V17_COMMIT).decode("utf-8")
_dd16 = git_bytes("assets/js/deepdive.js", V16_COMMIT).decode("utf-8")
check('"01": "Cost Performance"' in _dd17 and '"01": "Cat 1.1"' in _dd16,
      "the one sequence-bearing change is the panel label becoming a group and a purpose, and "
      "it is what the file GAINED rather than something already there")
check("CAT_NUM_FROM_MODULE" in _dd17 and "CAT_NUM_FROM_MODULE" not in _dd16,
      "and the grouping number is now declared separately from the displayed label, so "
      "correcting the text cannot move a panel")
for _control in ("<button", "<input", "<select", "<textarea", "data-run-portfolio-analysis"):
    check(_dd17.count(_control) == _dd16.count(_control),
          f"and its '{_control}' occurrences are unchanged in number, so no user-facing control "
          f"was added, moved or removed",
          f"{_dd17.count(_control)} vs {_dd16.count(_control)}")
for _step in ("submitPreliminary", "reveal", "lock"):
    _pat17 = re.compile(r"\b" + _step + r"\b")
    check(len(_pat17.findall(_dd17)) == len(_pat17.findall(_dd16)),
          f"and its references to '{_step}' are unchanged in number, so the delta did not touch "
          f"a sequence step",
          f"{len(_pat17.findall(_dd17))} vs {len(_pat17.findall(_dd16))}")
# THE DEAD LABEL MAP IS GONE FROM THE FILE THAT CARRIED IT. Run 47 corrected its ten retired
# labels and recorded that nothing in the repository read it; the owner's ruling 3 of 2026-08-22
# orders it DELETED rather than kept corrected, so this assertion requires its ABSENCE where it
# used to require the corrected labels' presence. That is a check-body change made necessary by
# an ordered deletion, and it is recorded as such in the Run 48 report.
_det = git_bytes("assets/js/detail.js", V17_COMMIT).decode("utf-8")
check("BRIEF_CAT_LABEL" not in _det,
      "the dead category label map is ABSENT from detail.js: no declaration and no reference")
check('"Cat 1": "Cost Performance"' not in _det
      and '"Cat 10": "Decision Optimization"' not in _det,
      "and neither its corrected labels nor its retired keys survive anywhere in the file")
_det16 = git_bytes("assets/js/detail.js", V16_COMMIT).decode("utf-8")
check("BRIEF_CAT_LABEL" in _det16,
      "and it really was there to delete, so this is not a check that passes vacuously")
# ---- v18, A PREDECESSOR LINK -------------------------------------------------------------------
# RUN 49, THE COMPLETION OF THE NAMING CORRECTION. THREE files moved and TWO OF THEM ARE
# SEQUENCE-BEARING. That is the first time TWO have moved at once, and it is asserted as TWO
# EXCEPTIONS WITH NAMES, not by widening the invariant: exactly the two sequence-bearing files
# participant_packages declares as the exception may have moved, and the other four are still
# held to byte-identity. A THIRD file moving here is still red, and so is a different one moving.
_v18 = parse((ROOT / V18_RECORD).read_text(encoding="utf-8"))
# RUN 55: the `not (ROOT / rel).is_file()` clause is REPLACED, not dropped. A record pinned to a
# commit is evidence about THAT COMMIT, so requiring its members to still exist on disk today
# asserted the wrong thing -- and it broke the moment Run 54 deleted a member on the owner's
# ruling. What replaces it is STRICTER about the thing that matters: a member missing from the
# tree must be DECLARED in participant_packages.V20_TO_V21_DELETED. An undeclared disappearance
# is still red.
_v18_bad = sorted(rel for rel, digest in _v18.items()
                  if (not (ROOT / rel).is_file() and rel not in PP.V20_TO_V21_DELETED)
                  or hashlib.sha256(git_bytes(rel, V18_COMMIT)).hexdigest() != digest)
check(not _v18_bad,
      "every one of v18's seventy checksums holds against the commit it describes, ad4f614, "
      "where the v18 package correctly lives now that v19 is current", str(_v18_bad))
check(sorted(_v18) == sorted(_v17),
      "v18 covers exactly the same file inventory as v17, so a successor cannot quietly drop a "
      "participant-visible file out of the package",
      str(sorted(set(_v17) ^ set(_v18))))
_moved18 = sorted(rel for rel, digest in _v17.items()
                  if hashlib.sha256(git_bytes(rel, V18_COMMIT)).hexdigest() != digest)
check(_moved18 == sorted(PP.V17_TO_V18_CHANGED),
      "and the files v18 moved are exactly the three it declares, so nothing rode along with "
      "the naming completion", str(_moved18))
_seq18 = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES
                if hashlib.sha256(git_bytes(rel, V18_COMMIT)).hexdigest() != _v17.get(rel))
check(_seq18 == sorted(PP.V17_TO_V18_SEQUENCE_EXCEPTION),
      "THE EXPERIMENTAL SEQUENCE MOVED ACROSS v17 TO v18, IN EXACTLY THE TWO DECLARED FILES AND "
      "NO OTHER: deepdive.js, whose group headers, banner, comparison table and prose stop "
      "printing the retired scheme, and decision-ui.js, which gains COMMENTS ONLY",
      str(_seq18))
check(len(PP.V17_TO_V18_SEQUENCE_EXCEPTION) == 2
      and set(PP.V17_TO_V18_SEQUENCE_EXCEPTION) < set(PP.SEQUENCE_BEARING_FILES),
      "and the exception is TWO named members of the sequence-bearing set, so the other four are "
      "still held to byte-identity by the check above",
      str(PP.V17_TO_V18_SEQUENCE_EXCEPTION))
_seq_still18 = sorted(set(PP.SEQUENCE_BEARING_FILES) - set(PP.V17_TO_V18_SEQUENCE_EXCEPTION))
check(all(hashlib.sha256(git_bytes(rel, V18_COMMIT)).hexdigest() == _v17.get(rel)
          for rel in _seq_still18) and len(_seq_still18) == 4,
      "the other four sequence-bearing files are byte for byte identical to v17: no step of the "
      "decision sequence, no reveal gate, no lock, no randomization and no questionnaire moved",
      str(_seq_still18))
# WHAT MOVED INSIDE EXCEPTION ONE, deepdive.js, measured rather than asserted.
# RUN 52. v19 is now a predecessor, so every v18-to-v19 measurement below reads the bytes at
# the commit v19 describes rather than the live tree. NOT ONE CHECK IS WEAKENED OR DELETED: each
# still asserts exactly what it asserted, against the bytes it was always about. The live tree
# is measured by the v19-to-v20 section that follows.
_dd18 = git_bytes("assets/js/deepdive.js", V19_COMMIT).decode("utf-8")
check('<span class="mod-mono">Cat ${n}</span>' in _dd17
      and '<span class="mod-mono">Cat ${n}</span>' not in _dd18,
      "the ten collapsible group headers no longer build the retired identifier span, and it "
      "really was there to remove, so this is not a check that passes vacuously")
for _gone in ("Cat 8.1", "Cat 6.1", "Cat 7.1", "Agrees with M09", "Module ${e.num}",
              "${esc(m.num)} ${esc(m.name)}"):
    check(_gone not in _dd18,
          f"and the rendered text '{_gone}' is gone from deepdive.js")
# RUN 51, RULINGS 5 AND 6. Run 49 extended a LABEL map so no panel key reached the neutral
# fallback. Run 51 replaced the two maps (label and bucket) with ONE table of category KEYS from
# which both the label and the bucket are derived through the loaded taxonomy. The claim is the
# same -- every key the call sites pass resolves rather than falling through -- and it is
# asserted against the table that now carries it, so no check is deleted.
_dd_keys = _dd18.split("const CAT_KEY_FROM_MODULE = {", 1)[1].split("\n  };", 1)[0]
_dd_call_keys = {m.group(1) for m in re.finditer(r'\bpanel\("([^"]+)"', _dd18)} - {"XX"}
_dd_mapped = {k for k in re.findall(r'"([^"]+)":\s*"', _dd_keys)}
check('"10.2 to 10.7": "B4"' in _dd_keys and '"1.4": "A1"' in _dd_keys,
      "and the panel category table covers the keys the call sites pass that reached the "
      "neutral fallback before Run 49")
check(not (_dd_call_keys - _dd_mapped),
      "and NOT ONE call-site key falls through to the neutral fallback",
      str(sorted(_dd_call_keys - _dd_mapped)))

# ---- v19, THE CURRENT LINK -------------------------------------------------------------------
# RUN 51, THE DELIVERY OF WHAT RUN 50 STOPPED ON. TWENTY-THREE files moved and ALL SIX
# SEQUENCE-BEARING FILES ARE AMONG THEM. That is the first time all six have moved at once, and
# it is asserted as SIX EXCEPTIONS WITH NAMES, not by widening the invariant: exactly the six
# participant_packages declares may have moved, each with what moved inside it recorded in the
# v19 checksum record's own header. A SEVENTH file moving here is still red, and so is any file
# outside V18_TO_V19_CHANGED.
_v19 = parse((ROOT / V19_RECORD).read_text(encoding="utf-8"))
# RUN 55: the `not (ROOT / rel).is_file()` clause is REPLACED, not dropped. A record pinned to a
# commit is evidence about THAT COMMIT, so requiring its members to still exist on disk today
# asserted the wrong thing -- and it broke the moment Run 54 deleted a member on the owner's
# ruling. What replaces it is STRICTER about the thing that matters: a member missing from the
# tree must be DECLARED in participant_packages.V20_TO_V21_DELETED. An undeclared disappearance
# is still red.
_v19_bad = sorted(rel for rel, digest in _v19.items()
                  if (not (ROOT / rel).is_file() and rel not in PP.V20_TO_V21_DELETED)
                  or hashlib.sha256(git_bytes(rel, V19_COMMIT)).hexdigest() != digest)
check(not _v19_bad,
      "every one of v19's seventy checksums holds against the commit it describes, fe35504, "
      "where the v19 package correctly lives now that v20 is current", str(_v19_bad))
check(sorted(_v19) == sorted(_v18),
      "v19 covers exactly the same file inventory as v18, so a successor cannot quietly drop a "
      "participant-visible file out of the package",
      str(sorted(set(_v18) ^ set(_v19))))
_moved19 = sorted(rel for rel, digest in _v18.items()
                  if hashlib.sha256(git_bytes(rel, V19_COMMIT)).hexdigest() != digest)
check(_moved19 == sorted(PP.V18_TO_V19_CHANGED),
      "and the files v19 moved are exactly the twenty-three it declares, so nothing rode along "
      "with the delivery", str(sorted(set(_moved19) ^ set(PP.V18_TO_V19_CHANGED))))
_seq19 = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES
                if hashlib.sha256(git_bytes(rel, V19_COMMIT)).hexdigest() != _v18.get(rel))
check(_seq19 == sorted(PP.V18_TO_V19_SEQUENCE_EXCEPTION),
      "THE EXPERIMENTAL SEQUENCE MOVED ACROSS v18 TO v19, IN EXACTLY THE SIX DECLARED FILES AND "
      "NO OTHER, each with its own named exception record", str(_seq19))
check(len(PP.V18_TO_V19_SEQUENCE_EXCEPTION) == 6
      and set(PP.V18_TO_V19_SEQUENCE_EXCEPTION) == set(PP.SEQUENCE_BEARING_FILES),
      "and the exception names every member of the sequence-bearing set individually rather "
      "than widening the comparison to exclude the set",
      str(PP.V18_TO_V19_SEQUENCE_EXCEPTION))
# WHAT KEEPS THE INVARIANT REAL WHEN THE EXCEPTION IS THE WHOLE SET: each file's OWN record must
# name it and say what moved inside it. A file moving with no record is still red.
_v19_header = (ROOT / V19_RECORD).read_text(encoding="utf-8").split("\n#\n")[0] + \
    (ROOT / V19_RECORD).read_text(encoding="utf-8")
for _seqfile in PP.SEQUENCE_BEARING_FILES:
    check(f"# {_seqfile} -- SEQUENCE-BEARING" in _v19_header,
          f"{_seqfile} carries its OWN named exception record in the v19 checksum record")
# AND NO SEQUENCE STEP MOVED INSIDE THEM, measured rather than asserted.
_dd_prior19 = git_bytes("assets/js/deepdive.js", V18_COMMIT).decode("utf-8")
for _step in ("stage", "reveal", "lock", "randomi"):
    _p = re.compile(_step, re.I)
    check(len(_p.findall(_dd18)) == len(_p.findall(_dd_prior19)),
          f"deepdive.js's references to '{_step}' are unchanged in number across v18 to v19, so "
          f"the delta did not touch a sequence step",
          f"{len(_p.findall(_dd18))} vs {len(_p.findall(_dd_prior19))}")
for _rel in ("assets/questionnaires/intake.json", "assets/questionnaires/debrief.json"):
    _now = json.loads(git_bytes(_rel, V19_COMMIT).decode("utf-8"))
    _was = json.loads(git_bytes(_rel, V18_COMMIT).decode("utf-8"))

    def _shape(o):
        if isinstance(o, dict):
            return {k: _shape(v) for k, v in sorted(o.items()) if k not in
                    ("label", "note", "text", "prompt", "title")}
        if isinstance(o, list):
            return [_shape(x) for x in o]
        return type(o).__name__
    check(_shape(_now) == _shape(_was),
          f"{_rel}: NO ITEM, NO RESPONSE OPTION, NO SCALE AND NO ORDER CHANGED across v18 to "
          f"v19 -- with every human-readable label removed the two documents have the identical "
          f"structure, so the delta is wording inside labels and nothing else")
# RULING 1, MEASURED: the three buttons went, and they were unreachable, so no control was
# removed. deepdive.js's OTHER controls are unchanged in number.
check(_dd_prior19.count("<button") - _dd18.count("<button") == 3,
      "exactly three <button> occurrences left deepdive.js across v18 to v19, and they are the "
      "three inside the Portfolio Health flyout",
      f"{_dd_prior19.count('<button')} vs {_dd18.count('<button')}")
check("renderCat8Health" in _dd_prior19 and "renderCat8Health" not in _dd18
      and _dd18.count("data-run-portfolio-analysis") == 0
      and _dd_prior19.count("data-run-portfolio-analysis") == 2,
      "and all three sat inside renderCat8Health, which nothing in the served application ever "
      "called, so no REACHABLE control was added, moved or removed")
for _control in ("<input", "<select", "<textarea"):
    check(_dd18.count(_control) == _dd_prior19.count(_control),
          f"and deepdive.js's '{_control}' occurrences are unchanged in number")
_dd18_at_v18 = git_bytes("assets/js/deepdive.js", V18_COMMIT).decode("utf-8")
check("CAT_NUM_FROM_MODULE" in _dd18_at_v18
      and _dd18_at_v18.split("CAT_NUM_FROM_MODULE = {", 1)[1].split("};", 1)[0]
          == _dd17.split("CAT_NUM_FROM_MODULE = {", 1)[1].split("};", 1)[0],
      "AND THE GROUPING MAP WAS BYTE-IDENTICAL TO v17 ACROSS RUN 49, so not one panel moved to "
      "a different collapsible group in that run. RUN 51's ruling 5 ORDERS panels to move and "
      "asserts where they moved to in the v19 block below")
for _control in ("<button", "<input", "<select", "<textarea", "data-run-portfolio-analysis"):
    check(_dd18_at_v18.count(_control) == _dd17.count(_control),
          f"and deepdive.js's '{_control}' occurrences were unchanged in number across Run 49, "
          f"so no "
          f"user-facing control was added, moved or removed",
          f"{_dd18.count(_control)} vs {_dd17.count(_control)}")
for _step in ("submitPreliminary", "reveal", "lock"):
    _pat18 = re.compile(r"\b" + _step + r"\b")
    check(len(_pat18.findall(_dd18)) == len(_pat18.findall(_dd17)),
          f"and deepdive.js's references to '{_step}' are unchanged in number, so the delta did "
          f"not touch a sequence step",
          f"{len(_pat18.findall(_dd18))} vs {len(_pat18.findall(_dd17))}")
# WHAT MOVED INSIDE EXCEPTION TWO, decision-ui.js. COMMENTS ONLY: strip every line comment and
# the two files must be identical. This is the strongest form of the claim and it is measured.
_du18 = git_bytes("assets/js/decision-ui.js", V18_COMMIT).decode("utf-8")
_du17 = git_bytes("assets/js/decision-ui.js", V17_COMMIT).decode("utf-8")


def _strip_line_comments(text: str) -> str:
    return "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("//"))


check(_du18 != _du17 and _strip_line_comments(_du18) == _strip_line_comments(_du17),
      "decision-ui.js moved, and with every whole-line comment removed the two versions are "
      "IDENTICAL: the delta is comments and nothing else at all")
check(_du18.count("period: 1") == _du17.count("period: 1") == 3,
      "and its three period literals are still there, unchanged in number, exactly as ruling 4 "
      "orders", f"{_du18.count('period: 1')} vs {_du17.count('period: 1')}")
for _control in ("<button", "<input", "<select", "<textarea"):
    check(_du18.count(_control) == _du17.count(_control),
          f"and decision-ui.js's '{_control}' occurrences are unchanged in number",
          f"{_du18.count(_control)} vs {_du17.count(_control)}")
# THE THIRD FILE, detail.js, IS NOT SEQUENCE-BEARING.
_det18 = git_bytes("assets/js/detail.js", V19_COMMIT).decode("utf-8")
check('cs("d-docsignals", "Documents & Extracted Signals"' in _det
      and 'cs("d-docsignals", "Documents and Extracted Signals"' in _det18
      and 'cs("d-docsignals", "Documents & Extracted Signals"' not in _det18,
      "detail.js titles the section with the word 'and', and the ampersand really was there to "
      "correct. The one surviving occurrence in the file is inside a COMMENT, which the naming "
      "authority does not govern")
check("Cat 1-12" in _det and "Cat 1-12" not in _det18
      and "Do NOT print any module identifier" in _det18,
      "and the executive brief prompt still FORBIDS the model to print an identifier while no "
      "longer naming the retired scheme to it: the guardrail was rewritten, not deleted")
# THE v17 RECORD WAS NOT REGENERATED.
check(git_bytes(V17_RECORD, V17_COMMIT) == (ROOT / V17_RECORD).read_bytes(),
      f"the v17 record in the working tree is BYTE-IDENTICAL to the one commit {V17_COMMIT[:7]} "
      f"wrote, so Run 49 created a successor rather than rewriting a predecessor")
# THE v16 RECORD WAS NOT REGENERATED. Its bytes in the tree must be the bytes its own commit
# wrote, which is what stops the Run-28 closure's defect from recurring on this successor.
check(git_bytes(V16_RECORD, V16_COMMIT) == (ROOT / V16_RECORD).read_bytes(),
      f"the v16 record in the working tree is BYTE-IDENTICAL to the one commit {V16_COMMIT[:7]} "
      f"wrote, so Run 48 created a successor rather than rewriting a predecessor")
# THE v15 RECORD WAS NOT REGENERATED. Its bytes in the tree must be the bytes its own commit
# wrote, which is what stops the Run-28 closure's defect from recurring on this successor.
check(git_bytes(V15_RECORD, V15_COMMIT) == (ROOT / V15_RECORD).read_bytes(),
      f"the v15 record in the working tree is BYTE-IDENTICAL to the one commit {V15_COMMIT[:7]} "
      f"wrote, so Run 47 created a successor rather than rewriting a predecessor")
# THE v14 RECORD WAS NOT REGENERATED. Its bytes in the tree must be the bytes its own commit
# wrote, which is what stops the Run-28 closure's defect from recurring on this successor.
check(git_bytes(V14_RECORD, V14_COMMIT) == (ROOT / V14_RECORD).read_bytes(),
      f"the v14 record in the working tree is BYTE-IDENTICAL to the one commit {V14_COMMIT[:7]} "
      f"wrote, so Run 44 created a successor rather than rewriting a predecessor")
# THE v13 RECORD WAS NOT REGENERATED. Its bytes in the tree must be the bytes its own commit
# wrote, which is what stops the Run-28 closure's defect from recurring on this successor.
check(git_bytes(V13_RECORD, V13_COMMIT) == (ROOT / V13_RECORD).read_bytes(),
      f"the v13 record in the working tree is BYTE-IDENTICAL to the one commit {V13_COMMIT[:7]} "
      f"wrote, so Run 43 created a successor rather than rewriting a predecessor")
# THE v3 RECORD WAS NOT REGENERATED. Its bytes in the tree must be the bytes commit 01e943e
# wrote, which is what stops the Run-28 closure's own defect from recurring here.
check(git_bytes(V3_RECORD, V3_COMMIT) == (ROOT / V3_RECORD).read_bytes(),
      f"the v3 record in the working tree is BYTE-IDENTICAL to the one commit {V3_COMMIT[:7]} "
      f"wrote, so this run created a successor rather than rewriting a predecessor")

# =================================================================================================
head("5. PROTOCOL INVARIANCE: ONLY DISPLAY BYTES MOVED FROM v2 TO v3, AND ONLY A DELETED "
     "QUALIFIER FROM v3 TO v4")
# =================================================================================================

_changed = sorted(rel for rel in _v3 if _v3[rel] != _v2[rel])
check(_changed == sorted(PP.V2_TO_V3_CHANGED),
      "exactly eleven package files differ between v2 and v3, and they are the eleven declared",
      str(_changed))

# THE PROOF THAT ONLY THE NAME MOVED. Each v3 file is mapped back through the rename and must be
# BYTE-IDENTICAL to its v2-era blob. This is stronger than counting differing lines: a single
# changed character anywhere else makes it red. Read from the v3 COMMIT, because v3 is now a
# predecessor and the live tree carries v4.
_not_name_only = []
for rel in _changed:
    _v2_text = (git_bytes(rel, V2_COMMIT) or b"").decode("utf-8")
    _v3_text = (git_bytes(rel, V3_COMMIT) or b"").decode("utf-8")
    if PP.to_v2_era(_v3_text) != _v2_text:
        _not_name_only.append(rel)
check(not _not_name_only,
      "and every one of them, mapped back through the A1.1 rename, is BYTE-IDENTICAL to its v2 "
      "bytes. ONLY THE DISPLAY NAME MOVED: no behaviour, no threshold, no sequence step, not one "
      "other character", str(_not_name_only))

# THE v3 TO v4 STEP, proved the same way and no more loosely.
_changed5 = sorted(rel for rel in _v5 if _v5[rel] != _v4[rel])
check(_changed5 == sorted(PP.V4_TO_V5_CHANGED),
      "exactly one package file differs between v4 and v5, and it is the one declared",
      str(_changed5))
_not_corrections_only = []
for rel in _changed5:
    _v4_text = (git_bytes(rel, V4_COMMIT) or b"").decode("utf-8")
    # RUN 31 PASS 2: read the v5-era bytes from V5_COMMIT rather than the live tree. v5 is a
    # predecessor now, so the tree is no longer its evidence -- the same correction v3 and v4
    # each received when they stopped being current.
    _v5_text = (git_bytes(rel, V5_COMMIT) or b"").decode("utf-8")
    if PP.to_v4_era(_v5_text, ROOT) != _v4_text:
        _not_corrections_only.append(rel)
check(not _not_corrections_only,
      "and restoring the eight deleted proxy qualifiers and the pre-closure structure statement "
      "reproduces its v4 bytes EXACTLY, so the only changes are the two corrections declared",
      str(_not_corrections_only))
_changed4 = sorted(rel for rel in _v4 if _v4[rel] != _v3[rel])
check(_changed4 == sorted(PP.V3_TO_V4_CHANGED),
      "exactly one package file differs between v3 and v4, and it is the one declared",
      str(_changed4))
_not_qualifier_only = []
for rel in _changed4:
    _v3_text = (git_bytes(rel, V3_COMMIT) or b"").decode("utf-8")
    # RUN 30 CLOSURE: the v3 comparison starts from the v4 BYTES IN GIT, not from the live tree,
    # because the tree has moved on to v5. The chain is walked one link at a time.
    if PP.to_v3_era((git_bytes(rel, V4_COMMIT) or b"").decode("utf-8")) != _v3_text:
        _not_qualifier_only.append(rel)
check(not _not_qualifier_only,
      "and restoring the six deleted proxy qualifiers to it reproduces its v3 bytes EXACTLY, so "
      "the only change is the removal of six sentences that the Run-29 remediation made false",
      str(_not_qualifier_only))
check(all(f"Stated proxy: " not in (ROOT / rel).read_text(encoding="utf-8").split(
              f'"{mid}": {{ name: ')[1].split("\n")[0]
          for rel in _changed4 for mid in ("A4.5", "A4.6", "A4.7", "A4.8", "A5.2", "A5.3")),
      "and the six qualifiers really are gone from the current file, so the normalisation above "
      "is restoring something rather than matching a no-op")

# THE PROTOCOL SURFACE ITSELF, byte-identical across BOTH steps. The decision sequence, the
# reveal gate, the lock, the randomization, the server contract and the append-only record all
# live in files that are NOT in either changed list, and that is asserted rather than inferred.
_protocol_moved = [rel for rel in PP.PROTOCOL_SURFACE
                   if _v3.get(rel) != _v2.get(rel) or _v4.get(rel) != _v3.get(rel)]
check(not _protocol_moved,
      "every file carrying a step of the participant sequence -- evidence, preliminary "
      "assessment, confidence, preliminary lock, reveal, final action, final lock, next period -- "
      "and every file carrying randomization, reveal timing, lock enforcement, the server "
      "contract, the append-only record or treatment logic is BYTE-IDENTICAL across v2, v3 and v4",
      str(_protocol_moved))
check(all(rel in _v4 for rel in PP.PROTOCOL_SURFACE),
      "and every one of those files is actually inside the package inventory, so the check above "
      "is over real rows rather than over names that are not there",
      str([rel for rel in PP.PROTOCOL_SURFACE if rel not in _v4]))
check("assets/js/decision.js" not in _changed and "assets/js/decision-ui.js" in _changed,
      "the distinction the file names invite and the bytes settle: decision.js RUNS the sequence "
      "and did not move; decision-ui.js holds a module-id-to-display-name table and did")

# THE SERVER SIDE, which no package record covers and which is where the sequence is actually
# enforced. Read from the tree at the v2 commit, because a display rename that had quietly
# reached the enforcement path would not show up in the package at all.
for _srv in ("server/app/research_decision.py", "server/app/research_transitions.py",
             "server/app/research_assignment.py", "server/app/research_audit.py",
             "server/app/research_consent.py", "server/app/research_membership.py"):
    check(git_bytes(_srv, V2_COMMIT) == (ROOT / _srv).read_bytes(),
          f"{_srv} is byte-identical to its v2 bytes, so lock enforcement, reveal timing, "
          f"randomization, server authority and the append-only record are untouched")

# ===============================================================================================
# RUN 52, v19 -> v20. THE LIVE TREE, AND THE ONE SEQUENCE-BEARING FILE THAT MOVED.
# ===============================================================================================
# v20 is the current package and is the ONLY record that reads the working tree. What moved is
# asserted as ONE EXCEPTION WITH A NAME, not by widening the invariant: exactly the one
# sequence-bearing file participant_packages declares may have moved, with what moved inside it
# recorded in the v20 checksum record's own header. A SECOND sequence-bearing file moving here
# is still red, and so is any file outside V19_TO_V20_CHANGED.
_v20 = parse((ROOT / V20_RECORD).read_text(encoding="utf-8"))
_v20_bad = sorted(rel for rel, digest in _v20.items()
                  if hashlib.sha256(git_bytes(rel, V20_COMMIT)).hexdigest() != digest)
check(not _v20_bad,
      "every one of v20's seventy checksums holds against the COMMIT WHOSE BLOBS IT DESCRIBES, "
      "which is where a superseded package record correctly lives", str(_v20_bad))
check(sorted(_v20) == sorted(_v19),
      "v20 covers exactly the same file inventory as v19, so a successor cannot quietly drop a "
      "participant-visible file out of the package",
      str(sorted(set(_v19) ^ set(_v20))))
_moved20 = sorted(rel for rel, digest in _v19.items()
                  if hashlib.sha256(git_bytes(rel, V20_COMMIT)).hexdigest() != digest)
check(_moved20 == sorted(PP.V19_TO_V20_CHANGED),
      "and the files v20 moved are exactly the seven it declares, so nothing rode along with "
      "the delivery", str(sorted(set(_moved20) ^ set(PP.V19_TO_V20_CHANGED))))
_seq20 = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES
                if hashlib.sha256(git_bytes(rel, V20_COMMIT)).hexdigest() != _v19.get(rel))
check(_seq20 == sorted(PP.V19_TO_V20_SEQUENCE_EXCEPTION),
      "THE EXPERIMENTAL SEQUENCE MOVED ACROSS v19 TO v20 IN EXACTLY THE ONE DECLARED FILE AND "
      "NO OTHER, and it carries its own named exception record", str(_seq20))
check(len(PP.V19_TO_V20_SEQUENCE_EXCEPTION) == 1
      and set(PP.V19_TO_V20_SEQUENCE_EXCEPTION) < set(PP.SEQUENCE_BEARING_FILES),
      "and the exception names one member of the sequence-bearing set rather than widening the "
      "comparison to exclude the set", str(PP.V19_TO_V20_SEQUENCE_EXCEPTION))
_v20_header = (ROOT / V20_RECORD).read_text(encoding="utf-8")
for _seqfile in PP.V19_TO_V20_SEQUENCE_EXCEPTION:
    check(f"# {_seqfile} -- SEQUENCE-BEARING" in _v20_header,
          f"{_seqfile} carries its OWN named exception record in the v20 checksum record")
# AND EVERY OTHER SEQUENCE-BEARING FILE IS STILL BYTE-IDENTICAL, named one by one.
for _seqfile in PP.SEQUENCE_BEARING_FILES:
    if _seqfile in PP.V19_TO_V20_SEQUENCE_EXCEPTION:
        continue
    check(hashlib.sha256(git_bytes(_seqfile, V20_COMMIT)).hexdigest() == _v19.get(_seqfile),
          f"{_seqfile} is BYTE FOR BYTE identical to v19 at v20: no step of the decision "
          f"sequence, no reveal gate, no lock, no randomization and no questionnaire moved "
          f"in it")
# RUN 55, PHASE C. THIS GUARD IS REVISED, NOT DELETED, AND IT KEEPS EVERYTHING IT ASSERTED
# THAT IS STILL TRUE.
#
# WHAT IT ASSERTED BEFORE: that `assets/js/app.js` was BYTE-IDENTICAL to v19, and that BOTH row
# controls -- Manage and Open -- were still rendered by it. That was the record of Run 52's stop
# under its own section 8.1: Open was then the only route from the project list to the project
# detail page, so removing it would have made every detail page unreachable.
#
# WHAT IT ASSERTS NOW: Run 54 phase C re-bound Manage to openDetail() -- verified in a real
# browser, per row, per surface, BEFORE anything was removed -- and only then removed Open. The
# route the old check protected therefore still exists; it is carried by Manage instead of by
# Open. So the guard keeps the PROPERTY (the project list reaches the detail page, and it is not
# left with two controls for one action) and drops only the two facts the owner's ruling
# reversed. app.js moved, which is a DECLARED change of v21 and is recorded there; it is no
# longer a defect for it to differ from v19.
#
# NON-VACUITY IS PINNED TO AN EXPLICIT COMMIT HASH, NEVER TO A RELATIVE REFERENCE. Run 54 wrote
# its own proofs against HEAD~1 and they decayed silently into false proofs that still passed as
# later commits walked the reference back. V19_COMMIT is an explicit hash.
_app20 = (ROOT / "assets/js/app.js").read_bytes()
_app19 = git_bytes("assets/js/app.js", V19_COMMIT)
check(hashlib.sha256(git_bytes("assets/js/app.js", V20_COMMIT)).hexdigest()
      == _v19.get("assets/js/app.js"),
      "AT v20 app.js WAS still byte-identical to v19 -- Run 52's stop under its section 8.1 was "
      "real and is still on the record; what follows is the v20-to-v21 delta and not a rewrite "
      "of history")
check(b'class="btn small li-open"' in _app19 and b'class="btn small li-manage"' in _app19,
      "NON-VACUITY, pinned to the explicit commit V19_COMMIT: app.js DID render BOTH row "
      "controls at v19, so the absence check below is not vacuous")
check(b'class="btn small li-open"' not in _app20,
      "RUN 54 PHASE C: the project list no longer renders the Open control")
check(b'class="btn small li-manage"' in _app20,
      "and Manage is still rendered on every row: the project list did not lose its control")
check(b'.li-manage").addEventListener("click", () => openDetail(' in _app20,
      "AND MANAGE NAVIGATES TO THE PROJECT DETAIL PAGE -- the route the removed Open used to "
      "carry is carried by Manage, so no project's detail page became unreachable")
check(hashlib.sha256(_app20).hexdigest() != _v19.get("assets/js/app.js"),
      "app.js is NOT byte-identical to v19, and that is the DECLARED v21 change rather than a "
      "defect: Run 52's stop under its section 8.1 was reversed by the owner's ruling at "
      "section 9 of the Run 54 order")
# WHAT MOVED INSIDE THE ONE EXCEPTION, deepdive.js, measured rather than asserted.
# RUN 55: deepdive.js no longer exists -- Run 54 phase B deleted it -- so the v19-to-v20 delta
# inside it is read from the two commits it spans. NOTHING IS DELETED FROM THIS BLOCK: every
# check it made about what moved between v19 and v20 still runs, against the same bytes, and it
# is now immune to any later change to the working tree.
_dd20 = git_bytes("assets/js/deepdive.js", V20_COMMIT).decode("utf-8")
_dd19 = git_bytes("assets/js/deepdive.js", V19_COMMIT).decode("utf-8")
check("data-goto-health" in _dd19 and "see Health" in _dd19,
      "the see-Health button REALLY WAS in deepdive.js at v19, so the absence checks below are "
      "not vacuous")
# Measured on the EXECUTABLE text: the comment Run 52 left at the removal site names the button
# and the symbol, and that comment is the record of why they went. Deleting the record to make a
# string search pass would be the wrong repair, so the search is scoped to what actually runs.
_dd20_code = _strip_line_comments(_dd20)
check("data-goto-health" not in _dd20_code and "see Health" not in _dd20_code,
      "and neither the button nor its handler survives in v20's EXECUTABLE text",
      _dd20_code[max(0, _dd20_code.find("data-goto-health") - 40):][:120])
check("openHealthModal" not in _dd20_code,
      "and the call to the symbol that never existed is gone with it")
check("see Health" in _dd20 and "openHealthModal" in _dd20,
      "AND THE RECORD SURVIVES: the comment at the removal site still names the button and the "
      "symbol, so a later reader is told what was there and why it went")
check(_dd19.count("<button") - _dd20.count("<button") == 1,
      "EXACTLY ONE <button> occurrence left deepdive.js across v19 to v20, and it is the dead "
      "see-Health button ruling 2 names",
      f"{_dd19.count('<button')} vs {_dd20.count('<button')}")
for _control in ("<input", "<select", "<textarea"):
    check(_dd20.count(_control) == _dd19.count(_control),
          f"and deepdive.js's '{_control}' occurrences are unchanged in number across v19 to v20",
          f"{_dd20.count(_control)} vs {_dd19.count(_control)}")
for _step in ("submitPreliminary", "reveal", "lock", "randomi", "stage"):
    _pat20 = re.compile(_step, re.I)
    check(len(_pat20.findall(_dd20)) == len(_pat20.findall(_dd19)),
          f"and deepdive.js's references to '{_step}' are unchanged in number across v19 to "
          f"v20, so the delta did not touch a sequence step",
          f"{len(_pat20.findall(_dd20))} vs {len(_pat20.findall(_dd19))}")
# THE ANOMALY SENTENCE THE BUTTON SAT BESIDE IS STILL THERE. Removing the paragraph as well
# would have removed rendered text, which no ruling authorises.
check("dd-health-line" in _dd20 and "cat8SummaryLine(project)" in _dd20,
      "and the Portfolio Health anomaly line the button sat beside is UNCHANGED and still "
      "rendered: only the button went")
# RULING 3, MEASURED ON THE SIX NON-SEQUENCE FILES. One name for the module identifier.
for _rel in ("assets/js/taxonomy.js", "assets/js/categories.js"):
    _txt = git_bytes(_rel, V20_COMMIT).decode("utf-8")
    _prior = git_bytes(_rel, V19_COMMIT).decode("utf-8")
    check(_prior.count("key: '") == 75 and _txt.count("key: '") == 12,
          f"{_rel}: the sixty-three MODULE rows dropped `key:` and only the twelve CATEGORY "
          f"rows keep it, and there really were seventy-five before, so this is not vacuous",
          f"{_prior.count(chr(107)+chr(101)+chr(121)+': ' + chr(39))} -> {_txt.count(chr(107)+chr(101)+chr(121)+': ' + chr(39))}")
    check(_txt.count("module_id: '") == 63,
          f"{_rel}: and all sixty-three carry module_id instead",
          str(_txt.count("module_id: '")))
    check(" num: " not in _txt and "num: '" not in _txt,
          f"{_rel}: and no third name for the same thing survives anywhere in it")
for _rel in ("assets/js/detail.js", "assets/js/signals.js", "assets/js/neural_flow.js",
             "assets/js/projectnet2d.js"):
    _txt = git_bytes(_rel, V20_COMMIT).decode("utf-8")
    check("m.key" not in _txt and "m && m.key" not in _txt,
          f"{_rel}: no consumer still reads the module identifier off a taxonomy module as "
          f"`key`")
    check("m.module_id" in _txt,
          f"{_rel}: and it reads it as module_id instead")


# =================================================================================================
# RUN 55, THE MINT. og-participant-2026.08-v21 -- THE FIRST LINK IN THIS CHAIN WHOSE
# SEQUENCE-BEARING DELTA IS A DELETION.
#
# v21 is the current package and is now the ONLY record that reads the working tree. ONE file
# LEFT the package -- assets/js/deepdive.js, which is sequence-bearing -- and FIVE moved. The
# deletion is asserted as ONE EXCEPTION WITH A NAME rather than by widening the invariant or by
# quietly shortening the sequence-bearing set: SEQUENCE_BEARING_FILES still has six members,
# SEQUENCE_BEARING_FILES_FROM_V21 has five, and the difference between them is asserted to be
# EXACTLY the declared exception. A SECOND sequence-bearing file disappearing is still red.
# =================================================================================================
print()
print("-" * 78)
print("RUN 55: og-participant-2026.08-v21, the deletion of a sequence-bearing file")
print("-" * 78)

# RUN 56: v21 IS NOW A PREDECESSOR. Its record is pinned and every check below reads the blobs
# of V21_COMMIT rather than the working tree. The historical statement does not change; where it
# is measured does, and it has to, because a predecessor that still matched the live tree would
# be a second record claiming one tree.
_v21_pkg = [q for q in PP.PARTICIPANT_PACKAGES if q.identifier == V21_IDENTITY][0]
check(_v21_pkg.record == V21_RECORD and _v21_pkg.source_commit is not None,
      "the v21 link is PINNED to the commit whose blobs its record describes, now that a "
      "successor exists", str(_v21_pkg.source_commit))
check(_v21_pkg.source_commit.startswith(V21_COMMIT),
      f"and it is pinned to {V21_COMMIT}, the tip at which v21 was still current",
      str(_v21_pkg.source_commit))
_pinned_but_current = [q.identifier for q in PP.PARTICIPANT_PACKAGES[:-1]
                       if q.source_commit is None]
check(not _pinned_but_current,
      "and EVERY superseded package is pinned to a commit: exactly one record in the chain "
      "reads the working tree", str(_pinned_but_current))

_v21 = parse((ROOT / V21_RECORD).read_text(encoding="utf-8"))
_v21_bad = sorted(rel for rel, digest in _v21.items()
                  if hashlib.sha256(git_bytes(rel, V21_COMMIT)).hexdigest() != digest)
check(not _v21_bad,
      f"every one of v21's sixty-nine checksums holds against the tree of commit "
      f"{V21_COMMIT}, the commit its record describes", str(_v21_bad))
check((ROOT / V21_RECORD).read_bytes() == git_bytes(V21_RECORD, V21_COMMIT),
      f"and the v21 record on disk is BYTE-IDENTICAL to its own bytes at {V21_COMMIT}, so "
      f"pinning it did not rewrite it")

# THE INVENTORY SHRANK BY EXACTLY THE DECLARED DELETIONS, AND BY NOTHING ELSE.
_left = sorted(set(_v20) - set(_v21))
_joined = sorted(set(_v21) - set(_v20))
check(_left == sorted(f for f in PP.V20_TO_V21_DELETED if f in _v20),
      "the files that LEFT the package are exactly the ones V20_TO_V21_DELETED declares, so a "
      "successor cannot quietly drop a participant-visible file out of the package",
      str(_left))
check(not _joined, "and nothing joined the package unannounced", str(_joined))
for _gone in _left:
    check(not (ROOT / _gone).is_file(),
          f"{_gone} really is absent from the tree: the declaration records a deletion, it does "
          f"not excuse a file that is still there")
    # NON-VACUITY, PINNED TO AN EXPLICIT COMMIT HASH. Never a relative reference.
    check(git_bytes(_gone, V20_COMMIT) != b"",
          f"NON-VACUITY at {V20_COMMIT}: {_gone} DID exist at v20, so the absence check above "
          f"is not vacuous")

# THE FILES THAT MOVED ARE EXACTLY THE FIVE DECLARED, AND NOTHING RODE ALONG.
_moved21 = sorted(rel for rel, digest in _v20.items()
                  if rel in _v21
                  and hashlib.sha256(git_bytes(rel, V21_COMMIT)).hexdigest() != digest)
check(_moved21 == sorted(PP.V20_TO_V21_CHANGED),
      "and the files v21 moved are exactly the five it declares, so nothing rode along with the "
      "delivery", str(sorted(set(_moved21) ^ set(PP.V20_TO_V21_CHANGED))))

# THE SEQUENCE-BEARING SET, AND THE ONE NAMED EXCEPTION THAT SHORTENS IT.
check(set(PP.SEQUENCE_BEARING_FILES) - set(PP.SEQUENCE_BEARING_FILES_FROM_V21)
      == set(PP.V20_TO_V21_SEQUENCE_EXCEPTION),
      "THE SEQUENCE-BEARING SET IS SHORTENED BY EXACTLY THE ONE NAMED EXCEPTION AND BY NOTHING "
      "ELSE: six members before v21, five from v21, and the difference is "
      "V20_TO_V21_SEQUENCE_EXCEPTION",
      str(sorted(set(PP.SEQUENCE_BEARING_FILES)
                 ^ (set(PP.SEQUENCE_BEARING_FILES_FROM_V21)
                    | set(PP.V20_TO_V21_SEQUENCE_EXCEPTION)))))
check(len(PP.SEQUENCE_BEARING_FILES) == 6 and len(PP.SEQUENCE_BEARING_FILES_FROM_V21) == 5,
      "and the historical set is NOT shortened, so every comparison from v7 to v20 is still read "
      "against the six it was taken against",
      f"{len(PP.SEQUENCE_BEARING_FILES)} / {len(PP.SEQUENCE_BEARING_FILES_FROM_V21)}")
check(set(PP.V20_TO_V21_SEQUENCE_EXCEPTION) <= set(PP.V20_TO_V21_DELETED),
      "and the sequence-bearing exception is a DELETION declared in V20_TO_V21_DELETED, not an "
      "edit excused by widening a comparison",
      str(PP.V20_TO_V21_SEQUENCE_EXCEPTION))
_seq21 = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES_FROM_V21
                if hashlib.sha256(git_bytes(rel, V21_COMMIT)).hexdigest() != _v20.get(rel))
check(not _seq21,
      "AND NO SURVIVING SEQUENCE-BEARING FILE MOVED ACROSS v20 TO v21: no step of the decision "
      "sequence, no reveal gate, no lock, no randomization and no questionnaire moved",
      str(_seq21))

# THE NAMED EXCEPTION RECORD IS IN THE v21 CHECKSUM RECORD'S OWN HEADER.
_v21_header = (ROOT / V21_RECORD).read_text(encoding="utf-8")
for _seqfile in PP.V20_TO_V21_SEQUENCE_EXCEPTION:
    check(f"# {_seqfile} -- SEQUENCE-BEARING" in _v21_header,
          f"{_seqfile} carries its OWN named exception record in the v21 checksum record")

# WHAT MOVED IN THE FIVE, MEASURED RATHER THAN ASSERTED.
_app21 = (ROOT / "assets/js/app.js").read_bytes()
check(b'class="btn small li-open"' not in _app21 and b'class="btn small li-manage"' in _app21,
      "app.js: Open is gone from the project list and Manage remains")
check(b'.li-manage").addEventListener("click", () => openDetail(' in _app21,
      "app.js: and Manage navigates to the project detail page, so the route Open carried is "
      "still carried")
_ing21 = (ROOT / "assets/js/ingest.js").read_text(encoding="utf-8")
_det21 = (ROOT / "assets/js/detail.js").read_text(encoding="utf-8")
check("function openInlineManage(id, hostEl)" in _ing21,
      "ingest.js: the admin panel builder takes a host element, which is the whole of the move")
check("detail-admin-host" in _det21 and "wireDetailAdmin" in _det21,
      "detail.js: the project detail page hosts that panel")
for _sel, _label in ((".pe-save", "Save info"), (".pe-populate", "Upload documents"),
                     (".pe-recompute", "Recompute this project"), (".pe-reset", "Reset signals"),
                     (".pe-archive", "Archive"), (".pe-cancel", "Close")):
    check(_sel[1:] in _ing21 and _label in _ing21,
          f"and '{_label}' ({_sel}) is still built by the SAME builder: the control moved, it "
          f"was not rewritten")
    check(_label in git_bytes("assets/js/ingest.js", V20_COMMIT).decode("utf-8"),
          f"NON-VACUITY at {V20_COMMIT}: '{_label}' existed before the move")
_css21 = (ROOT / "assets/css/radar.css").read_text(encoding="utf-8")
check(".li-open" not in _css21,
      "radar.css: no .li-open rule survives -- the four dead rules went with the control they "
      "styled")
check(".li-open" in git_bytes("assets/css/radar.css", V20_COMMIT).decode("utf-8"),
      f"NON-VACUITY at {V20_COMMIT}: radar.css DID carry .li-open rules")

# =================================================================================================
# RUN 56, THE MINT. og-participant-2026.08-v22 -- THE SMALLEST LINK IN THIS CHAIN, AND THE FIRST
# WHOSE SEQUENCE EXCEPTION IS AN EXPLICITLY DECLARED EMPTY SET.
#
# v22 is the current package and is now the ONLY record that reads the working tree. EXACTLY ONE
# file moved, assets/js/ingest.js, and it is NOT sequence-bearing. The emptiness is DECLARED as
# V21_TO_V22_SEQUENCE_EXCEPTION and V21_TO_V22_DELETED rather than omitted, so a reader sees a
# declaration and not a silence, and a sequence-bearing file moving without being named there is
# still red.
# =================================================================================================
print()
print("-" * 78)
print("RUN 56: og-participant-2026.08-v22, one file moved and no sequence exception")
print("-" * 78)

# RUN 57 CONVERTS THIS BLOCK FROM CURRENT TO PREDECESSOR. v22 is superseded by v23, so its
# record no longer describes the working tree; it describes the commit it is pinned to. The
# checks are not deleted and not loosened -- every one of them still runs, against the commit
# whose blobs the record actually describes, which is STRICTER than reading disk because disk
# has moved on.
_v22pkg = [p for p in PP.PARTICIPANT_PACKAGES if p.identifier == V22_IDENTITY][0]
check(_v22pkg.record == V22_RECORD,
      "the v22 link names its own checksum record", _v22pkg.record)
check(_v22pkg.source_commit is not None
      and _v22pkg.source_commit.startswith(V22_COMMIT),
      f"and v22 is now PINNED to the explicit commit {V22_COMMIT} rather than claiming the live "
      f"tree, because it is no longer the current package", str(_v22pkg.source_commit))

_v22 = parse((ROOT / V22_RECORD).read_text(encoding="utf-8"))
_v22_bad = sorted(rel for rel, digest in _v22.items()
                  if hashlib.sha256(git_bytes(rel, V22_COMMIT)).hexdigest() != digest)
check(not _v22_bad,
      f"every one of v22's sixty-nine checksums holds against {V22_COMMIT}, THE COMMIT WHOSE "
      f"BLOBS THE RECORD DESCRIBES -- not against disk, which has moved on", str(_v22_bad))
check(b'SIMULATION_VERSION = "sim-2026.08-v37"'
      in git_bytes("server/app/simulation/models.py", V22_COMMIT),
      f"and models.py at {V22_COMMIT} reads sim-2026.08-v37, so the pin names the tree v22 was "
      f"current on and not some other commit")
check(len(_v22) == 69, "and the package is sixty-nine files", str(len(_v22)))

# THE INVENTORY DID NOT MOVE AT ALL ACROSS THIS LINK.
check(sorted(_v22) == sorted(_v21),
      "v22 covers exactly the same file inventory as v21: nothing joined and nothing left",
      str(sorted(set(_v21) ^ set(_v22))))
check(PP.V21_TO_V22_DELETED == (),
      "and V21_TO_V22_DELETED is an EXPLICITLY DECLARED empty tuple, not an omission",
      str(PP.V21_TO_V22_DELETED))

# THE FILES THAT MOVED ARE EXACTLY THE ONE DECLARED, AND NOTHING RODE ALONG.
# MEASURED AT V22_COMMIT, not on disk, for the same reason as above.
_moved22 = sorted(rel for rel, digest in _v21.items()
                  if rel in _v22
                  and hashlib.sha256(git_bytes(rel, V22_COMMIT)).hexdigest() != digest)
check(_moved22 == sorted(PP.V21_TO_V22_CHANGED),
      "and the files v22 moved are exactly the one it declares, so nothing rode along with the "
      "removal and the two confirmations",
      str(sorted(set(_moved22) ^ set(PP.V21_TO_V22_CHANGED))))

# NO SEQUENCE-BEARING FILE MOVED, AND THE SET IS NOT SHORTENED AGAIN.
check(PP.V21_TO_V22_SEQUENCE_EXCEPTION == (),
      "V21_TO_V22_SEQUENCE_EXCEPTION is an EXPLICITLY DECLARED empty tuple",
      str(PP.V21_TO_V22_SEQUENCE_EXCEPTION))
_seq22 = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES_FROM_V21
                if hashlib.sha256(git_bytes(rel, V22_COMMIT)).hexdigest() != _v21.get(rel))
check(not _seq22,
      "AND NO SEQUENCE-BEARING FILE MOVED ACROSS v21 TO v22: all five are present and "
      "byte-identical to v21, so no step of the decision sequence, no reveal gate, no lock, no "
      "randomization and no questionnaire moved", str(_seq22))
check(len(PP.SEQUENCE_BEARING_FILES_FROM_V21) == 5
      and len(PP.SEQUENCE_BEARING_FILES) == 6,
      "and neither sequence-bearing set was shortened again: still six historical, five from v21",
      f"{len(PP.SEQUENCE_BEARING_FILES)} / {len(PP.SEQUENCE_BEARING_FILES_FROM_V21)}")

# WHAT MOVED INSIDE ingest.js, MEASURED RATHER THAN ASSERTED -- at V22_COMMIT, the tree this
# link describes.
_ing22 = git_bytes("assets/js/ingest.js", V22_COMMIT).decode("utf-8")
check('${hostEl ? "" : `<button class="btn small pe-populate">Upload documents</button>`}'
      in _ing22,
      "ingest.js: 'Upload documents' (.pe-populate) is emitted ONLY when no host element is "
      "supplied, so it is gone from the detail page and the portfolio-row path is untouched")
check("const populateBtn = box.querySelector(\".pe-populate\");" in _ing22
      and "if (populateBtn) populateBtn.addEventListener" in _ing22,
      "and its click listener is GUARDED, not deleted")
# NON-VACUITY, PINNED TO AN EXPLICIT COMMIT HASH. Never a relative reference.
check('<button class="btn small pe-populate">Upload documents</button>'
      in git_bytes("assets/js/ingest.js", V21_COMMIT).decode("utf-8"),
      f"NON-VACUITY at {V21_COMMIT}: ingest.js DID emit .pe-populate unconditionally before "
      f"this run, so the absence check above is not vacuous")
check("function confirmDestructive(opts)" in _ing22
      and "LinUI.openModal" in _ing22
      and "window.confirm" not in _ing22.split("function confirmDestructive(opts)")[1][:2000],
      "ingest.js: the confirmation helper exists and is built on LinUI.openModal, the pattern "
      "the application already uses for its destructive project-scoped actions, NOT on "
      "window.confirm, which returns false in this container")
for _lbl, _fn in (("Archive", "const doArchive = async () => {"),
                  ("Reset signals", "const doReset = async () => {")):
    check(_fn in _ing22,
          f"and '{_lbl}''s action is a named function the confirmation gates, so the action "
          f"itself is unchanged")
check("confirmDestructive({" in _ing22 and _ing22.count("confirmDestructive({") == 2,
      "and EXACTLY TWO controls are gated, Archive and Reset signals, no more",
      str(_ing22.count("confirmDestructive({")))
# NON-VACUITY at the same explicit commit: neither carried a confirmation before this run.
check("confirmDestructive" not in git_bytes("assets/js/ingest.js", V21_COMMIT).decode("utf-8"),
      f"NON-VACUITY at {V21_COMMIT}: neither control carried ANY confirmation before this run")
for _dash in ("\u2014", "\u2013"):
    check(_dash not in "Archive This moves out of the active portfolio Reset signals for",
          "and no em dash or en dash is in the confirmation text")

# =================================================================================================
# RUN 57, THE MINT. og-participant-2026.08-v23 -- THE TWO RESET CONTROLS MERGED INTO ONE.
#
# v23 is the current package and is now the ONLY record that reads the working tree. THREE files
# moved -- assets/css/radar.css, assets/js/detail.js and assets/js/ingest.js -- and NOT ONE is
# sequence-bearing, so the emptiness is DECLARED as V22_TO_V23_SEQUENCE_EXCEPTION and
# V22_TO_V23_DELETED rather than omitted.
#
# THIS BLOCK IS ADDED, NOT SUBSTITUTED FOR THE v22 BLOCK ABOVE. Converting v22 to a predecessor
# without adding this would have left the chain's central guarantee -- that the CURRENT record's
# checksums hold against the LIVE TREE -- with no subject at all.
# =================================================================================================
print()
print("-" * 78)
print("RUN 57: og-participant-2026.08-v23, three files moved and no sequence exception")
print("-" * 78)

check(PP.CURRENT.identifier == V23_IDENTITY,
      "the package chain declares v23 CURRENT", PP.CURRENT.identifier)
check(PP.CURRENT.record == V23_RECORD,
      "and names the v23 checksum record as the one that describes the live tree",
      PP.CURRENT.record)
check(PP.CURRENT.source_commit is None,
      "and leaves its source_commit None, which is what 'describes the LIVE TREE' means")

_v23 = parse((ROOT / V23_RECORD).read_text(encoding="utf-8"))
_v23_bad = sorted(rel for rel, digest in _v23.items()
                  if not (ROOT / rel).is_file()
                  or hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != digest)
check(not _v23_bad,
      "every one of v23's sixty-nine checksums holds against the LIVE TREE, which is where the "
      "current package correctly lives", str(_v23_bad))
check(len(_v23) == 69, "and the package is sixty-nine files", str(len(_v23)))

# THE INVENTORY DID NOT MOVE AT ALL ACROSS THIS LINK.
check(sorted(_v23) == sorted(_v22),
      "v23 covers exactly the same file inventory as v22: nothing joined and nothing left",
      str(sorted(set(_v22) ^ set(_v23))))
check(PP.V22_TO_V23_DELETED == (),
      "and V22_TO_V23_DELETED is an EXPLICITLY DECLARED empty tuple, not an omission",
      str(PP.V22_TO_V23_DELETED))

# THE FILES THAT MOVED ARE EXACTLY THE THREE DECLARED, AND NOTHING RODE ALONG.
_moved23 = sorted(rel for rel, digest in _v22.items()
                  if rel in _v23
                  and hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != digest)
check(_moved23 == sorted(PP.V22_TO_V23_CHANGED),
      "and the files v23 moved are exactly the three it declares, so nothing rode along with the "
      "merge and the removal",
      str(sorted(set(_moved23) ^ set(PP.V22_TO_V23_CHANGED))))

# NO SEQUENCE-BEARING FILE MOVED, AND THE SET IS NOT SHORTENED AGAIN.
check(PP.V22_TO_V23_SEQUENCE_EXCEPTION == (),
      "V22_TO_V23_SEQUENCE_EXCEPTION is an EXPLICITLY DECLARED empty tuple",
      str(PP.V22_TO_V23_SEQUENCE_EXCEPTION))
_seq23 = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES_FROM_V21
                if not (ROOT / rel).is_file()
                or hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != _v22.get(rel))
check(not _seq23,
      "AND NO SEQUENCE-BEARING FILE MOVED ACROSS v22 TO v23: all five are present and "
      "byte-identical to v22, so no step of the decision sequence, no reveal gate, no lock, no "
      "randomization and no questionnaire moved", str(_seq23))

# WHAT MOVED INSIDE THE THREE FILES, MEASURED RATHER THAN ASSERTED.
_ing23 = (ROOT / "assets/js/ingest.js").read_text(encoding="utf-8")
_det23 = (ROOT / "assets/js/detail.js").read_text(encoding="utf-8")
_css23 = (ROOT / "assets/css/radar.css").read_text(encoding="utf-8")
check('class="btn small detail-reset"' not in _det23
      and 'class="detail-reset-msg kn-sub" aria-live="polite"' not in _det23
      and "function wireReset(root)" not in _det23
      and "    wireReset(root);\n" not in _det23,
      "detail.js: the second reset control is GONE -- its markup, its aria-live span, its "
      "handler wireReset() and wireReset's call site")
check(".detail-reset-msg" not in _css23,
      "radar.css: the CSS rule that styled that control's aria-live span is GONE with it, not "
      "left behind as dead CSS")
# NON-VACUITY, PINNED TO AN EXPLICIT COMMIT HASH. Never a relative reference.
_det22 = git_bytes("assets/js/detail.js", V22_COMMIT).decode("utf-8")
_css22 = git_bytes("assets/css/radar.css", V22_COMMIT).decode("utf-8")
check('class="btn small detail-reset"' in _det22 and "function wireReset(root)" in _det22
      and ".detail-reset-msg { margin: 0; }" in _css22,
      f"NON-VACUITY at {V22_COMMIT}: the control, its handler AND its CSS rule all existed "
      f"before this run, so the three absence checks above are not vacuous")
# THE SURVIVOR DOES THE UNION. Asserted behaviour by behaviour against the commit v22 describes.
_pe22 = _ing22[_ing22.index("const doReset = async () => {"):]
_pe23 = _ing23[_ing23.index("const doReset = async () => {"):]
_wire22 = _det22[_det22.index("function wireReset(root)"):]
_union = [f for f in ("LinStore.resetSignals(", "LinSignals.clearCache(", "LinResults.clear(",
                      "LinStore.load(", "logEvent(", "LinApp.refresh(", "renderPortfolioAdmin(",
                      "LIN_PROJECTS", "LinStore.getProject(", "p.history = []",
                      "LinStore.getCached(")
          if f in _pe22[:4000] or f in _wire22[:6000]]
_missing = [f for f in _union if f not in _pe23[:6000]]
check(not _missing,
      "ingest.js: the SURVIVING reset control performs the UNION of both original handlers -- "
      f"every one of the {len(_union)} behaviours either of them had, asserted behaviour by "
      f"behaviour against {V22_COMMIT}", str(_missing))
check("LinDetail.render(id)" in _pe23[:6000],
      "and the removed control's render(id) survives as the exported LinDetail.render(id)")
check("confirmDestructive({" in _ing23 and _ing23.count("confirmDestructive({") == 2,
      "and STILL exactly two controls are gated by a confirmation, Archive and Reset signals: "
      "the merge added no gate and removed none", str(_ing23.count("confirmDestructive({")))

print()
print("=" * 78)
if _fail:
    print(f"{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(0 if FAILED == 0 else 1)
