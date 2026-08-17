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
_v8 = parse((ROOT / V8_RECORD).read_text(encoding="utf-8"))
_v8_bad = sorted(rel for rel, digest in _v8.items()
                 if not (ROOT / rel).is_file()
                 or hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != digest)
check(not _v8_bad,
      "and every one of v8's seventy checksums holds against the LIVE TREE, which is where the "
      "current package correctly lives", str(_v8_bad))

# THE SEQUENCE PROOF, WHICH IS WHAT REPLACES v8's MISSING INVERSE MAPPING. v7's delta was a
# display substitution and was proved so by inverse-mapping it back. v8's is not, so the claim
# "the experimental sequence is unchanged" cannot rest on that. It rests on this instead: every
# file that CARRIES the sequence is byte for byte identical between v7 and v8.
_seq_bad = sorted(rel for rel in PP.SEQUENCE_BEARING_FILES
                  if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != _v7.get(rel))
check(not _seq_bad,
      "THE EXPERIMENTAL SEQUENCE IS UNCHANGED: every file carrying evidence review, preliminary "
      "judgment, preliminary lock, AI reveal, final judgment, capture, final lock and period "
      "advancement is byte for byte identical to v7", str(_seq_bad))
# AND THE FILES v8 DID MOVE ARE EXACTLY THE ONES DECLARED, so a further file cannot ride along.
_moved = sorted(rel for rel, digest in _v7.items()
                if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != digest)
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
check(_matches_tree == [PP.CURRENT.identifier] == [V8_IDENTITY],
      "PACKAGE IDENTITY IS TRUTHFUL: exactly ONE record in the chain describes the live tree and "
      "it is the one declared current. A CURRENT FILE CANNOT MASQUERADE AS A PREDECESSOR PACKAGE",
      str(_matches_tree))
check([p.identifier for p in PP.PARTICIPANT_PACKAGES]
      == [V1_IDENTITY, V2_IDENTITY, V3_IDENTITY, V4_IDENTITY, V5_IDENTITY,
          V6_IDENTITY, V7_IDENTITY, V8_IDENTITY],
      "the chain is declared oldest first and every link is named", str(PP.PARTICIPANT_PACKAGES))
check(len({p.record for p in PP.PARTICIPANT_PACKAGES}) == 8
      and all((ROOT / p.record).is_file() for p in PP.PARTICIPANT_PACKAGES),
      "each link has its OWN record file and all eight are present, so no link shares a record "
      "with another")
check(PP.CURRENT.source_commit is None
      and all(p.source_commit for p in PP.PARTICIPANT_PACKAGES[:-1]),
      "and only the current link reads the working tree; all seven predecessors name the commit "
      "their bytes live in")
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

print()
print("=" * 78)
if _fail:
    print(f"{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(0 if FAILED == 0 else 1)
