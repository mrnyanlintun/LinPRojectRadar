"""
RUN 20 CYCLE 2. The declared-production-change manifest, checked against production BYTES.

WHY THIS FILE EXISTS. Cycle 1 built `run20_production_changes.py` as the one declared list of
modules Run 20 changed in production, and had both the category suites and the consolidator
check every result row against it. Cycle 2's mutation campaign tried to break that guard by
removing a module from the manifest, and the guard did not notice.

It could not have noticed. The category suites WRITE `production_change_made` by calling
`expected_flag(mid)`, and the consolidator then READS that column and compares it to
`expected_flag(mid)`. Both sides of the comparison come from the same function, so the two can
never disagree whatever the manifest says. It is the failure mode this programme has already
found nine times in other forms: a check asserted against a hand-maintained copy of the thing it
is supposed to be checking. It passes forever and proves nothing.

WHAT THIS FILE CHECKS INSTEAD. The manifest is compared to `code_audit/run20_production_freeze.sha256`,
production as it stood at the Run-20 starting commit. The set of production files whose bytes now
differ from that baseline must equal exactly the set of files the manifest names. Neither side is
derived from the other: one is a hash of the bytes on disk, the other is a hand-written
declaration. An undeclared production edit and a declared file that was never touched both make
this red.

WHAT IT DOES NOT CHECK, STATED PLAINLY. File-level hashes cannot show that a particular MODULE
inside a shared file changed. Three of cycle 2's four modules live in the same file. That
direction is covered three ways instead: the manifest's module ids are checked against the
hundred scientific targets and against a Run-20 note in the category suite that assesses each
one, the category suites assert each module's corrected behaviour by name, and the mutation
campaign proves each of those assertions can fail. What remains genuinely uncovered is a
manifest entry that names a REAL target in an ALREADY-DECLARED file and changes nothing; that
one is caught by the category suite for that module, not here.
"""

from __future__ import annotations

import hashlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

sys.path.insert(0, str(HERE / "run17"))

from run20_production_changes import (  # noqa: E402
    RUN20_ARCHITECTURAL_CHANGES,
    RUN20_NEW_PRODUCTION_FILES,
    RUN20_PRODUCTION_CHANGES,
)
from run21_production_changes import RUN21_PRODUCTION_CHANGES  # noqa: E402
from run23_production_changes import RUN23_PRODUCTION_CHANGES  # noqa: E402
from run25_production_changes import RUN25_PRODUCTION_CHANGES  # noqa: E402
from population import population  # noqa: E402

ROOT = HERE.parent.parent
#: The IMMOVABLE reference: production as it stood at the Run-20 starting commit, before any
#: cycle changed anything. It is a copy of run20_production_baseline.sha256 as that file read at
#: commit 54e8591, taken because cycle 1 REGENERATED the baseline after making its fix. A
#: baseline that is rewritten every time production changes agrees with production by
#: construction and can never catch an undeclared edit, which is the same circularity this file
#: was written to remove. This copy is never regenerated during Run 20.
BASELINE = ROOT / "code_audit" / "run20_production_freeze.sha256"

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


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


baseline: dict[str, str] = {}
for line in BASELINE.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        continue
    digest, _, rel = line.partition("  ")
    baseline[rel] = digest

check("the frozen Run-20 starting-state production manifest is present and covers the whole "
      "file list", len(baseline) == 143, f"{len(baseline)} rows")
check("the freeze is genuinely frozen: it still records the pre-cycle-1 bytes of the file cycle "
      "1 changed, so it has not been regenerated against current production",
      baseline.get("server/app/simulation/models_ext.py")
      == "8911c9d86fc73fd913907cb9b489a5649d2b400cfaa7cc26dcdf9c66e65bb5d3")

missing = [rel for rel in baseline if not (ROOT / rel).is_file()]
check("every file the baseline names still exists", not missing, str(missing))

differing = {rel for rel, digest in baseline.items()
             if (ROOT / rel).is_file() and sha(ROOT / rel) != digest}
run20_declared = ({entry[1] for entry in RUN20_PRODUCTION_CHANGES.values()}
                  | {entry[1] for entry in RUN20_ARCHITECTURAL_CHANGES.values()})
# RUN 21. Runs after Run 20 declare their own production changes in their own manifest. The
# Run-20 freeze stays IMMOVABLE and the Run-20 manifest stays the record of what RUN 20 changed;
# folding a later run's edits into it would falsify that record. The guard's property is
# unchanged: the differing set must equal the UNION exactly, so an undeclared edit is still red
# and a declared-but-untouched file is still red. Section "later-run manifests" below proves
# this addition did not turn the guard into one that accepts anything.
run21_declared = {entry[1] for entry in RUN21_PRODUCTION_CHANGES.values()}
# POST-RUN-22 UI CORRECTION. Its own manifest, read alongside the other two for the same reason:
# the Run-20 and Run-21 records stay exactly what those runs changed, and the union is still
# required to equal the differing set exactly, so nothing here loosens the guard.
run23_declared = {entry[1] for entry in RUN23_PRODUCTION_CHANGES.values()}
# RUN 25, THE RAIL REMOVAL. Its own manifest, same construction, same property: the union of
# all manifests must still equal the differing set exactly. detail.js and radar.css are NOT
# in it -- Run 23 already declares both -- so one change is still never counted twice.
run25_declared = {entry[1] for entry in RUN25_PRODUCTION_CHANGES.values()}
declared = run20_declared | run21_declared | run23_declared | run25_declared

check("every production file that differs from the Run-20 freeze is declared in the Run-20 "
      "manifest or a later run's manifest, so an undeclared production edit cannot pass",
      differing <= declared, f"undeclared: {sorted(differing - declared)}")
check("every production file a manifest declares actually differs from the Run-20 "
      "freeze, so a declared fix that was never delivered cannot pass",
      declared <= differing, f"declared but unchanged: {sorted(declared - differing)}")
check("the Run-20 manifest still declares only files RUN 20 changed: no Run-21 path was folded "
      "into it, which would falsify Run 20's own record",
      not (run20_declared & run21_declared),
      f"in both manifests: {sorted(run20_declared & run21_declared)}")
check("and no path is declared by two manifests at all, so one change cannot be counted twice",
      not (run23_declared & (run20_declared | run21_declared))
      and not (run25_declared & (run20_declared | run21_declared | run23_declared)),
      f"in more than one manifest: "
      f"{sorted((run23_declared & (run20_declared | run21_declared)) | (run25_declared & (run20_declared | run21_declared | run23_declared)))}")
for mid, (why_item, path, why) in sorted(RUN25_PRODUCTION_CHANGES.items()):
    check(f"the Run-25 manifest entry for {mid} names an authority, a real file and a "
          f"reason", bool(why_item) and bool(why) and (ROOT / path).is_file(),
          f"{why_item!r} {path!r}")
for mid, (why_item, path, why) in sorted(RUN23_PRODUCTION_CHANGES.items()):
    check(f"the post-Run-22 manifest entry for {mid} names an authority, a real file and a "
          f"reason", bool(why_item) and bool(why) and (ROOT / path).is_file(),
          f"{why_item!r} {path!r}")
for mid, (why_item, path, why) in sorted(RUN21_PRODUCTION_CHANGES.items()):
    check(f"the Run-21 manifest entry for {mid} names an authority, a real file and a reason",
          bool(why_item) and bool(why) and (ROOT / path).is_file(), f"{why_item!r} {path!r}")
check("and the two sets are therefore exactly equal, which is the whole guard",
      differing == declared, f"{sorted(differing)} vs {sorted(declared)}")

check("no file outside the baseline's own list is treated as production by this check, so the "
      "guard cannot be widened by adding a file to the manifest",
      declared <= set(baseline), f"not in baseline: {sorted(declared - set(baseline))}")

for mid, (cycle, path, why) in sorted(RUN20_PRODUCTION_CHANGES.items()):
    check(f"the manifest entry for {mid} names a cycle, a real file and a reason",
          bool(cycle) and bool(why) and (ROOT / path).is_file(), f"{cycle!r} {path!r}")

# MODULE-LEVEL, the direction file hashes cannot reach. A manifest entry naming something that
# is not one of the hundred scientific targets is a fabricated declaration, and a target the
# manifest names must have a Run-20 note against it in the category suite that assesses it, so
# a module cannot be declared changed with nothing anywhere demonstrating the change.
_targets = {t["module_id"] for t in population()}
for mid in sorted(RUN20_PRODUCTION_CHANGES):
    check(f"the manifest entry {mid} is one of the hundred scientific targets",
          mid in _targets)
    # RUN 20 CYCLE 9 FOUND A GAP IN THIS GUARD AND IT IS FIXED HERE RATHER THAN WORKED AROUND.
    # The guard assumed every one of the hundred targets is assessed by a suite named
    # test_run19_category_N. Categories 1 and 6 have no such file: their targets are assessed in
    # test_run17_scientific_methods.py, which carries the Run-17 canonical propositions for them.
    # So a change to a category 1 or category 6 module could be declared in the manifest with
    # NOTHING anywhere demonstrating it, and this check -- which exists precisely to prevent that
    # -- would have failed for the wrong reason (a missing file) rather than passing for the
    # right one. The suite that actually assesses the target is looked up now, and the note is
    # required in whichever file that is. A target assessed by NO suite at all is still a failure.
    cat = mid.split(".")[0]
    _candidates = [HERE / f"test_run19_category_{cat}.py",
                   HERE / "test_run17_scientific_methods.py"]
    suite = next((c for c in _candidates
                  if c.is_file() and f'"{mid}"' in c.read_text(encoding="utf-8")), None)
    body = suite.read_text(encoding="utf-8") if suite is not None else ""
    check(f"the suite that assesses {mid} carries a Run-20 note recording the change",
          "RUN 20 CYCLE" in body,
          f"assessed by {suite.name if suite else 'NO SUITE'}")

# THE ARCHITECTURAL DECLARATIONS, checked the same three ways the module ones are: a cycle, a
# real file, a reason, and an id that is a real architectural row of the Run-20 register rather
# than a name invented to make a change declarable.
_register = (ROOT / "code_audit" / "run20_master_remediation_register.csv").read_text(
    encoding="utf-8")
for aid, (cycle, path, why) in sorted(RUN20_ARCHITECTURAL_CHANGES.items()):
    check(f"the architectural manifest entry for {aid} names a cycle, a real file and a reason",
          bool(cycle) and bool(why) and (ROOT / path).is_file(), f"{cycle!r} {path!r}")
    check(f"and {aid} is an architectural row the Run-20 register actually carries",
          f"\n{aid.split(chr(32))[0]}," in _register)
check("an architectural entry may not name a file the module manifest already declares, so one "
      "change cannot be counted as two declarations",
      not ({e[1] for e in RUN20_ARCHITECTURAL_CHANGES.values()}
           & {e[1] for e in RUN20_PRODUCTION_CHANGES.values()}))

# NEW production files, the direction the byte comparison structurally cannot reach: a file that
# did not exist when the freeze was taken has no baseline row to differ from.
for rel, (cycles, why) in sorted(RUN20_NEW_PRODUCTION_FILES.items()):
    check(f"the declared new production file {rel} exists and names a cycle and a reason",
          (ROOT / rel).is_file() and bool(cycles) and bool(why))
    check(f"and {rel} declares its cycles as a tuple rather than one string, so a later cycle "
          f"that changes it has somewhere to say so",
          isinstance(cycles, tuple) and all(isinstance(c, str) for c in cycles), repr(cycles))
    check(f"and {rel} is genuinely new rather than a baseline file smuggled onto the new list",
          rel not in baseline)
_undeclared_new = sorted(
    str(p.relative_to(ROOT)) for p in (ROOT / "server" / "app" / "simulation").glob("*.py")
    if str(p.relative_to(ROOT)) not in baseline
    and str(p.relative_to(ROOT)) not in RUN20_NEW_PRODUCTION_FILES)
check("and no OTHER file has appeared in the simulation package undeclared, which is the check "
      "that makes the new-file list mean something",
      not _undeclared_new, str(_undeclared_new))

# The cycles so far, so a fourth cycle that forgets to declare itself is visible here.
# THE CYCLE SET, AND THE GAP CYCLE 4 FOUND IN IT. This read the cycles off the baseline-file
# declarations only. Cycle 4 changes nothing but lineage.py, a file created by cycle 3, which has
# no baseline row to differ from and so appears in neither of the first two dictionaries: the
# cycle would have declared itself nowhere and this check, which exists precisely to catch a
# cycle that forgets to declare itself, would have stayed green while it did. The new-file
# declarations are read too now.
_declared_cycles = ({e[0] for e in RUN20_PRODUCTION_CHANGES.values()}
                    | {e[0] for e in RUN20_ARCHITECTURAL_CHANGES.values()}
                    | {c for e in RUN20_NEW_PRODUCTION_FILES.values() for c in e[0]})
check("the manifest records exactly the eight Run-20 cycles that have changed production",
      _declared_cycles == {"1 P0B", "2 P0C", "3 P0D", "4 P0D", "5 P0D", "9 P1", "10 P2",
                           "11 P3"},
      str(sorted(_declared_cycles)))

if _fail:
    print(f"\n{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
