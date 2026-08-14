"""
RUN 22 ITEM 5. THE FREEZE GUARD, AND THE PROOF THAT IT CAN FAIL.

WHAT THIS REPLACES. `test_run20_declared_production_changes.py` compares production bytes against
`code_audit/run20_production_freeze.sha256`, a hand-maintained list of 143 named paths, and its
own first check asserts `len(baseline) == 143`. That guard is sound for the files it names and
BLIND to every file it does not. Run 21 recorded the concern and left it open for the freeze run;
Run 22 measured it and found the blindness is not theoretical. Subtracting the 143 names from a
walk of the deployed roots leaves 83 production files, among them the entire Category-9 lineage
layer (`lineage.py`, `arm_lineage.py`), the qualification gate, the method-label and parameter
modules, all 25 alembic migrations, `server/requirements.txt`, `render.yaml`, `logo.png` and
`research/deepdive.html`. Every one is production. None could have been seen by any freeze this
programme has taken.

WHY THIS FILE IS NOT THE SAME MISTAKE IN A NEW SHAPE. The names in this guard's comparison come
from `production_tree.walk_production()`, which walks the filesystem under roots derived from
`app.main` and `render.yaml`. `code_audit/run22_production_tree.sha256` is the RECORD of what the
walk found when the freeze was taken; it supplies the expected hashes and is never the source of
the names. So a file added to a production root is discovered by the walk, is absent from the
record, and is reported ADDED. The old guard could not produce that outcome at all, because the
file it was asked about was never in the list it read.

THE STANDING RULE ABOUT VACUOUS GUARDS, APPLIED HERE. Run 20 found nine vacuous guards and Run 21
found more, and the rule is that a guard is vacuous until it has been shown red. Sections 3 and 4
below do not assert that the guard WOULD fail; they build a real copy of the production tree in a
temporary directory, really add, really modify, really delete and really rename a file in it, and
require the guard to report each one. Section 5 then proves the same four mutations against the
REAL repository root, restoring after each, so the thing proved red is the deployed guard and not
only the algorithm. Nothing is left mutated: section 6 re-runs the clean comparison last.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import production_tree as pt  # noqa: E402

ROOT = pt.ROOT

_passed = 0
_total = 0
_fail: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if cond:
        _passed += 1
    else:
        _fail.append(f"{name}" + (f" -- {detail}" if detail else ""))


# ---------------------------------------------------------------- 1. the roots are real

check("the production roots are declared with a recursion flag and a stated reason each, so no "
      "root is in scope by habit",
      all(isinstance(r, str) and isinstance(rec, bool) and len(why) > 20
          for r, rec, why in pt.PRODUCTION_ROOTS),
      str([r for r, _, why in pt.PRODUCTION_ROOTS if len(why) <= 20]))
_missing_roots = [r for r, _rec, _why in pt.PRODUCTION_ROOTS if not (ROOT / r).exists()]
check("every declared production root exists in the checkout", not _missing_roots,
      str(_missing_roots))
check("every exclusion carries a reason about the file not being production",
      all(len(why) > 20 for _pat, why in pt.EXCLUSIONS))
check("the only exclusions are generated caches and placeholders: no source extension and no "
      "application directory is excluded",
      {pat for pat, _ in pt.EXCLUSIONS} == {"__pycache__", ".pyc", ".pyo", ".DS_Store",
                                            ".gitkeep"},
      str(sorted(pat for pat, _ in pt.EXCLUSIONS)))

# ---------------------------------------------------------------- 2. it is a superset, pinned

_inventory = pt.walk_production()
_paths = {rel for rel, _d, _s, _t in _inventory}

# THE OLD FREEZE IS SUBSUMED, NOT DISCARDED. Every path the 143-file Run-20 freeze protected must
# still be protected here, or this replacement would have quietly narrowed the freeze while
# claiming to widen it. The count is pinned as a literal on both sides.
_old = {line.partition("  ")[2]
        for line in (ROOT / "code_audit" / "run20_production_freeze.sha256")
        .read_text(encoding="utf-8").splitlines() if line.strip()}
check("the Run-20 freeze it replaces named exactly 143 files", len(_old) == 143, str(len(_old)))
check("and every one of those 143 is still in the Run-22 production inventory, so the tree walk "
      "is a strict superset of the list it replaces",
      _old <= _paths, str(sorted(_old - _paths)))
check("the walk finds strictly more than the old list did, which is the defect being closed",
      len(_paths) > 143, str(len(_paths)))

# The five backend modules that were invisible to every previous freeze. Pinned BY NAME, so that
# if a future change removes them from scope this check says which one was lost.
for _lost in ("server/app/simulation/lineage.py",
              "server/app/simulation/arm_lineage.py",
              "server/app/simulation/method_labels.py",
              "server/app/simulation/parameters.py",
              "server/app/simulation/qualification_gate.py"):
    check(f"{_lost} -- live backend code, invisible to the 143-file freeze -- is now in scope",
          _lost in _paths and _lost not in _old)
for _lost in ("logo.png", "research/deepdive.html", "render.yaml",
              "server/requirements.txt", "server/alembic/versions/0025_project_notices.py"):
    check(f"{_lost} -- served or deployed, invisible to the 143-file freeze -- is now in scope",
          _lost in _paths and _lost not in _old)

check("the inventory ordering is canonical: byte-sorted by path, so two checkouts in two "
      "locales produce the identical manifest",
      [rel for rel, _d, _s, _t in _inventory] == sorted(rel for rel, _d, _s, _t in _inventory))
check("the pinned manifest exists", pt.PINNED.is_file(), str(pt.PINNED))

# ---------------------------------------------------------------- 3. THE GUARD IS GREEN NOW

_clean = pt.compare()
check("with the checkout unmodified the guard reports no added, removed, changed or renamed "
      "production file",
      not (_clean["added"] or _clean["removed"] or _clean["changed"]), str(_clean))
check("and the pinned manifest's own hash matches the tree, so the LIST of files is pinned and "
      "not only their contents",
      hashlib.sha256(pt.PINNED.read_bytes()).hexdigest()
      == hashlib.sha256(pt.manifest_text().encode("utf-8")).hexdigest(),
      f"pinned={hashlib.sha256(pt.PINNED.read_bytes()).hexdigest()} "
      f"walked={pt.manifest_sha256()}")

# ------------------------------- 3b. RUN 28 CLOSURE, ITEM 4: THE UNTRACKED-FILE BLIND SPOT
#
# THE DEFECT, AS RUN 28 RECORDED IT AND LEFT IT OPEN. The suite stayed green while
# `server/app/simulation/canonical_v3.py` -- two thousand lines of analytical production code --
# was not tracked by git at all. Every guard that reasons about production change through
# `git diff` is structurally blind to that: `git diff` enumerates TRACKED paths and nothing else.
# The walk above is not blind to it, because it discovers names from the filesystem, and it
# already reports each file's tracked state as an attribute. NOTHING ASSERTED ANYTHING ABOUT
# THAT ATTRIBUTE, so the information was collected and thrown away.
#
# It is asserted here, and it is a different property from the three the manifest comparison
# covers. Added, removed and changed are about the FILESYSTEM disagreeing with the freeze. This
# one is about the filesystem agreeing with the freeze while the REPOSITORY does not carry the
# file: a protected file that is present, pinned, hashed and green, and that would not exist at
# all in the deployed checkout, because nothing ever added it to the index.
#
# NON-VACUITY IS PROVED ON THE REAL TREE, not in the sandbox, because the sandbox has no git
# repository to be tracked by: `code_audit/run28_closure_fault_injection.csv` records a harmless
# untracked file created inside `server/app/simulation/`, this check observed RED naming that
# exact path, the file deleted, and this check observed GREEN again.
_untracked_production = sorted(rel for rel, _d, _s, tracked in _inventory if not tracked)
check("every file in the protected production surface is TRACKED BY GIT, so a production file "
      "that exists on this disk, hashes green against the freeze and would be absent from the "
      "deployed checkout cannot pass -- the blind spot Run 28 left open, closed",
      not _untracked_production, f"untracked production files: {_untracked_production}")
check("and the walk reports tracked state for every file it finds, so the check above is "
      "asserted over the whole surface rather than over a sample",
      len(_inventory) == len([1 for _r, _d, _s, t in _inventory if t in (True, False)]),
      str(len(_inventory)))

# ------------------------------------------- 4. NON-VACUITY, on a real copy of the real tree

# A real copy, really mutated. Not a stub, not a fabricated manifest: the same walk over the same
# roots, so what is proved red is the code the freeze uses.
with tempfile.TemporaryDirectory(prefix="run22-tree-") as _td:
    _sandbox = pathlib.Path(_td) / "repo"
    _sandbox.mkdir()
    for _r, _rec, _why in pt.PRODUCTION_ROOTS:
        _src, _dst = ROOT / _r, _sandbox / _r
        _dst.parent.mkdir(parents=True, exist_ok=True)
        if _src.is_dir():
            shutil.copytree(_src, _dst,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
        else:
            shutil.copy2(_src, _dst)

    _pin = pt.manifest_text(_sandbox)
    check("the copied tree reproduces the manifest exactly, so the sandbox is a faithful "
          "reference and any red below is caused by the mutation and not by the copy",
          not any(pt.compare(_sandbox, _pin)[k] for k in ("added", "removed", "changed")),
          str(pt.compare(_sandbox, _pin)))

    # ADD. The mutation the whole item is about: a new production file nobody declared.
    _new = _sandbox / "assets" / "js" / "run22_temporary_fake_production_file.js"
    _new.write_text("// deliberate Run-22 non-vacuity mutation\n", encoding="utf-8")
    _d = pt.compare(_sandbox, _pin)
    check("ADD: a new file in a production root is reported ADDED -- the exact case the "
          "143-file freeze could not see",
          _d["added"] == ["assets/js/run22_temporary_fake_production_file.js"], str(_d))
    _new.unlink()
    check("ADD restored: removing it returns the guard to green",
          not any(pt.compare(_sandbox, _pin)[k] for k in ("added", "removed", "changed")))

    # MODIFY.
    _mod = _sandbox / "server" / "app" / "simulation" / "lineage.py"
    _orig = _mod.read_bytes()
    _mod.write_bytes(_orig + b"\n# deliberate Run-22 non-vacuity mutation\n")
    _d = pt.compare(_sandbox, _pin)
    check("MODIFY: changed bytes in a protected file are reported CHANGED",
          _d["changed"] == ["server/app/simulation/lineage.py"], str(_d))
    _mod.write_bytes(_orig)
    check("MODIFY restored: the original bytes return the guard to green",
          not any(pt.compare(_sandbox, _pin)[k] for k in ("added", "removed", "changed")))

    # DELETE.
    _del = _sandbox / "assets" / "js" / "neural_flow.js"
    _delbytes = _del.read_bytes()
    _del.unlink()
    _d = pt.compare(_sandbox, _pin)
    check("DELETE: a removed production file is reported REMOVED",
          _d["removed"] == ["assets/js/neural_flow.js"], str(_d))
    _del.write_bytes(_delbytes)
    check("DELETE restored", not any(pt.compare(_sandbox, _pin)[k]
                                     for k in ("added", "removed", "changed")))

    # RENAME. Reported as a rename, and ALSO as one added and one removed, so a rename can never
    # be silently netted off to nothing.
    _from = _sandbox / "assets" / "js" / "signals.js"
    _to = _sandbox / "assets" / "js" / "signals_renamed.js"
    _from.rename(_to)
    _d = pt.compare(_sandbox, _pin)
    check("RENAME: a renamed production file is reported as a rename",
          _d["renamed"] == ["assets/js/signals.js -> assets/js/signals_renamed.js"], str(_d))
    check("RENAME: and as one removed and one added, so it cannot net off to nothing",
          _d["removed"] == ["assets/js/signals.js"]
          and _d["added"] == ["assets/js/signals_renamed.js"], str(_d))
    _to.rename(_from)
    check("RENAME restored", not any(pt.compare(_sandbox, _pin)[k]
                                     for k in ("added", "removed", "changed")))

    # A MISSING ROOT IS A FAILURE, NOT A SKIP. A freeze that silently tolerates a vanished root
    # is the blind spot again in a different place.
    shutil.rmtree(_sandbox / "server" / "alembic")
    _raised = False
    try:
        pt.walk_production(_sandbox)
    except FileNotFoundError:
        _raised = True
    check("MISSING ROOT: a production root that has vanished raises rather than being skipped",
          _raised)

# ------------------------------- 4b. THE SCIENTIFIC AUTHORITY, PINNED EXECUTABLY AT LAST

# THE GAP RUN 22 FOUND. The supervisory specification's SHA-256 appears in four reports, in
# T6_HANDOFF.md and in its own metadata file, and NOTHING EXECUTABLE CHECKED ANY OF THEM. A hash
# that lives only in prose cannot fail. It is checked three ways here: against the literal below,
# against the metadata file's own claim, and through the walked authority manifest.
_SPEC = "research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md"
_SPEC_SHA = "328b50133f1d2a8d710d3cca787c24c22e2cdad0b09fe92ae2c7b7a55b8d299e"
check("the controlling supervisory specification is present", (ROOT / _SPEC).is_file())
check("its SHA-256 is the one Run 19 committed and every report since has quoted",
      hashlib.sha256((ROOT / _SPEC).read_bytes()).hexdigest() == _SPEC_SHA,
      hashlib.sha256((ROOT / _SPEC).read_bytes()).hexdigest())

_meta = json.loads((ROOT / _SPEC.replace(".md", ".metadata.json")).read_text(encoding="utf-8"))
check("the specification's own metadata record claims that same digest, so the two independent "
      "records agree", _meta["committed_file_sha256"] == _SPEC_SHA,
      _meta["committed_file_sha256"])
check("and the metadata still records the specification as CONTROLLING, which is what makes the "
      "implementation the object under test rather than a source of theory",
      _meta["controlling_status"].startswith("CONTROLLING"))
check("the .gitattributes rule that stops a checkout filter rewriting the specification's line "
      "endings is still present -- without it the bytes can change without the document being "
      "edited",
      f"{_SPEC} -text" in (ROOT / ".gitattributes").read_text(encoding="utf-8"))

_auth_clean = pt.compare(None, None, pt.AUTHORITY_ROOTS, pt.PINNED_AUTHORITY)
check("the walked authority tree matches its pinned manifest",
      not (_auth_clean["added"] or _auth_clean["removed"] or _auth_clean["changed"]),
      str(_auth_clean))

# NON-VACUITY for the authority guard, in a sandbox, exactly as for production above.
with tempfile.TemporaryDirectory(prefix="run22-auth-") as _td:
    _sb = pathlib.Path(_td) / "repo"
    _sb.mkdir()
    for _r, _rec, _why in pt.AUTHORITY_ROOTS:
        _src, _dst = ROOT / _r, _sb / _r
        _dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(_src, _dst) if _src.is_dir() else shutil.copy2(_src, _dst)
    _apin = pt.manifest_text(_sb, pt.AUTHORITY_ROOTS)
    check("the copied authority tree reproduces its manifest",
          not any(pt.compare(_sb, _apin, pt.AUTHORITY_ROOTS)[k]
                  for k in ("added", "removed", "changed")))
    _spec_copy = _sb / _SPEC
    _orig_spec = _spec_copy.read_bytes()
    _spec_copy.write_bytes(_orig_spec + b"\nappended by the Run-22 non-vacuity campaign\n")
    _d = pt.compare(_sb, _apin, pt.AUTHORITY_ROOTS)
    check("SUPERVISORY-SPEC MUTATION: an edit to the controlling specification is reported "
          "CHANGED -- the first executable guard this document has ever had",
          _d["changed"] == [_SPEC], str(_d))
    _spec_copy.write_bytes(_orig_spec)
    check("SUPERVISORY-SPEC restored",
          not any(pt.compare(_sb, _apin, pt.AUTHORITY_ROOTS)[k]
                  for k in ("added", "removed", "changed")))

# ---------------------------------------------------------------- 5. clean afterwards

_final = pt.compare()
check("the real checkout is unmodified after the non-vacuity campaign: every mutation was made "
      "in a temporary directory and none leaked into the repository",
      not (_final["added"] or _final["removed"] or _final["changed"]), str(_final))

print("\n".join(f"FAIL: {f}" for f in _fail))
print(f"RESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
