#!/usr/bin/env python3
"""
RUN 67, PART A. THE INJECTION THAT PROVES EACH RE-POINTED SUITE CAN STILL FAIL.

Eight suites were re-pointed from the two-module voting rule Run 65 overrode to the rule that
replaced it. A suite that cannot fail is worse than no suite, so each one is proved able to go
red HERE, by injection, rather than by argument.

THE INJECTION IS PINNED TO THE EXACT SITE RUN 65 MOVED, and to no other. Run 65's change was the
removal of one line from the COMPUTED loop in `compute.py`:

    if row["module_id"] not in CORE_VOTING_MODULES: continue

The fault puts that line back, at that site, and nowhere else. Nothing is renamed, no name is
matched file-wide, and the site is proved to be the live one by the fact that restoring it
returns the platform to the pre-Run-65 behaviour every one of these suites used to assert. A
check that stays green under this injection is a check that is not reading the rule it claims to.

DISCIPLINE (Runs 52, 53, 61, 62, 63):
  * the tree is required clean at start AND at end;
  * the snapshot is taken from the COMMITTED bytes at HEAD, never from disk;
  * the injected bytes are RE-READ FROM DISK to confirm the injection landed before any suite is
    run, because an injection that did not take turns this whole campaign into a silent pass;
  * the restore is in a `finally`, and the restored bytes are compared with HEAD.

argv[1] (optional) = a single suite name to run instead of all eight.
"""
from __future__ import annotations
import os, pathlib, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from campaign_safety import require_clean_tree, head_text  # noqa: E402

TARGET = "server/app/simulation/compute.py"
ANCHOR = ('    for row in run["computed"]:\n'
          '        pre = preflight(si, (), period_cutoff)\n')
FAULT = ('    for row in run["computed"]:\n'
         '        if row["module_id"] not in CORE_VOTING_MODULES:\n'
         '            continue\n'
         '        pre = preflight(si, (), period_cutoff)\n')

SUITES = [
    ("test_run1_disable_and_relabel.py",
     "layer (a): every category carrying a module that COMPUTED has a rollup"),
    ("test_run2_fifteen_defects.py",
     "a category rollup exists exactly where a module computed"),
    ("test_run3_adapter.py",
     "keeping exactly one computed row leaves exactly that module's own category"),
    ("test_run4_validate_seven.py",
     "layer one: the rollup reaches every category that computed"),
    ("test_run6_known_answer.py",
     "rollup: exactly the categories carrying a module that COMPUTED have a rollup entry"),
    ("test_run10b_canonical_integration.py",
     "a structure adds a reading and never removes one"),
    ("test_run20_voting_lineage.py",
     "the voters are exactly the computed rows"),
    ("test_training_detail.py",
     "exactly the categories carrying a module that COMPUTED have a rollup to open"),
]

ONLY = sys.argv[1] if len(sys.argv) > 1 else None
if ONLY:
    SUITES = [s for s in SUITES if s[0] == ONLY]

require_clean_tree(ROOT, "start", "run67 voting-rule fault campaign")

TMP = pathlib.Path(tempfile.mkdtemp(prefix="run67-campaign-"))
subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=str(ROOT / "server"),
               env={**os.environ, "DATABASE_URL": f"sqlite:///{TMP}/template.db",
                    "SESSION_SECRET": "test-secret-do-not-use-in-prod"},
               check=True, capture_output=True)


def result_line(name: str, tag: str) -> tuple[int, int, str]:
    db = TMP / f"{tag}-{name}.db"
    shutil.copy(TMP / "template.db", db)
    r = subprocess.run([sys.executable, str(HERE / name)], cwd=str(ROOT / "server"),
                       env={**os.environ, "DATABASE_URL": f"sqlite:///{db}",
                            "SESSION_SECRET": "test-secret-do-not-use-in-prod"},
                       capture_output=True, text=True)
    lines = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.startswith("RESULT:")]
    if not lines:
        # A crash is not a pass and it is not a red for the intended reason either.
        return (-1, -1, (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else "no output")
    got = lines[-1].split()[1]
    p, total = got.split("/")
    return (int(p), int(total), lines[-1])


TARGET_PATH = ROOT / TARGET
COMMITTED = head_text(ROOT, TARGET)
assert ANCHOR in COMMITTED, "the anchor is not in the committed bytes: the site has moved"
assert FAULT not in COMMITTED, "the fault is already in the committed bytes"

print("=" * 96)
print("RUN 67 PART A: THE VOTING-RULE FAULT CAMPAIGN")
print(f"  target site: {TARGET}, the computed-row loop that fills by_category")
print("=" * 96)

print("\n--- BASELINE (the committed tree) ---")
base = {}
for name, _ in SUITES:
    base[name] = result_line(name, "base")
    print(f"  {name:44} {base[name][2]}")

print("\n--- INJECTING the pre-Run-65 filter at its exact site ---")
ok = True
try:
    TARGET_PATH.write_text(COMMITTED.replace(ANCHOR, FAULT), encoding="utf-8")
    # RE-READ FROM DISK. An injection that did not land makes every red below meaningless.
    on_disk = TARGET_PATH.read_text(encoding="utf-8")
    assert FAULT in on_disk, "THE INJECTION DID NOT LAND ON DISK"
    assert on_disk.count("if row[\"module_id\"] not in CORE_VOTING_MODULES") == 1, \
        "the injection landed more than once"
    print("  confirmed on disk: the filter is back in the computed loop, exactly once")

    print("\n--- EACH SUITE UNDER THE FAULT ---")
    red = {}
    for name, prop in SUITES:
        red[name] = result_line(name, "red")
        b, r_ = base[name], red[name]
        # A RED IS A FAILED CHECK, NOT A SMALLER PASS COUNT. A suite that aborts early under
        # the injection reports fewer checks in total and would otherwise be scored as having
        # gone red while actually having crashed -- and a crash is not a red for the intended
        # reason any more than it is a pass. So the verdict reads the FAILURES, and requires the
        # suite to have run to completion with the same number of checks it ran at baseline.
        went_red = (r_[0] >= 0 and b[0] >= 0
                    and r_[1] == b[1] and (r_[1] - r_[0]) > (b[1] - b[0]))
        ok = ok and went_red
        print(f"  {'RED  ' if went_red else 'GREEN'}  {name:44} {b[2]}  ->  {r_[2]}")
        print(f"         property under injection: {prop}")
finally:
    TARGET_PATH.write_text(COMMITTED, encoding="utf-8")
    assert TARGET_PATH.read_text(encoding="utf-8") == COMMITTED, "RESTORE FAILED"
    print("\n--- RESTORED, and the bytes on disk equal the committed bytes ---")

print("\n--- BASELINE RECHECKED after the restore ---")
for name, _ in SUITES:
    again = result_line(name, "again")
    same = again[:2] == base[name][:2]
    ok = ok and same
    print(f"  {'OK  ' if same else 'DRIFT'}  {name:44} {again[2]}")

require_clean_tree(ROOT, "end", "run67 voting-rule fault campaign")
print("\n" + "=" * 96)
_verdict = ("every re-pointed suite went red under the injection and green again after it"
            if ok else "A SUITE DID NOT GO RED -- it is not reading the rule it claims to")
print(f"RESULT: {_verdict}")
print("=" * 96)
sys.exit(0 if ok else 1)
