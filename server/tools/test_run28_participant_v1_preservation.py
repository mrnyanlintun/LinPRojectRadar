"""
RUN 28 CLOSURE. HISTORICAL PARTICIPANT PACKAGE v1, PRESERVED EXECUTABLY.

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

#: THE EXACT GIT OBJECT. The commit that ADDED code_audit/run12_participant_package_checksums.sha256
#: -- Run 12 Gates 11-12, the release freeze that took the package -- found with
#: `git log --diff-filter=A -- <record>`. A commit cannot be mutated in place, so this is evidence
#: rather than a copy someone maintained.
V1_COMMIT = "c44e3ced94a22a9def35fa5a2be3a2268fbed6bb"
V1_IDENTITY = "og-participant-2026.08-v1"
V2_IDENTITY = "og-participant-2026.08-v2"
RECORD = "code_audit/run12_participant_package_checksums.sha256"
SUCCESSOR = "code_audit/run28_closure_participant_package_checksums.sha256"

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
head("3. THE CURRENT SUCCESSOR, VERIFIED INDEPENDENTLY")
# =================================================================================================

_v2 = parse((ROOT / SUCCESSOR).read_text(encoding="utf-8"))
check(len(_v2) == 70,
      f"the successor record for {V2_IDENTITY} names the same seventy files, so the package was "
      f"not narrowed while it was superseded", str(len(_v2)))
check(set(_v2) == set(_v1),
      "over exactly the same inventory as v1", str(sorted(set(_v2) ^ set(_v1))))
_v2_bad = sorted(rel for rel, digest in _v2.items()
                 if not (ROOT / rel).is_file()
                 or hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != digest)
check(not _v2_bad,
      "and every one of its seventy checksums holds against the LIVE tree, which is where the "
      "current package correctly lives", str(_v2_bad))
_header = (ROOT / SUCCESSOR).read_text(encoding="utf-8")
check(V2_IDENTITY in _header and V1_IDENTITY in _header and RECORD in _header,
      "the successor states its own identity, names v1 as its predecessor and points at the "
      "record it does not replace")
check(_v2 != _v1,
      "the two records genuinely differ, so the successor is a real supersession and not a copy "
      "of its predecessor under a new name",
      str(len([r for r in _v2 if _v2[r] != _v1[r]])))
check(_v2["assets/js/taxonomy.js"] != _v1["assets/js/taxonomy.js"],
      "and the participant ledger's own name source is one of the files that moved, which is the "
      "change that required a successor package at all")

print()
print("=" * 78)
if _fail:
    print(f"{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(0 if FAILED == 0 else 1)
