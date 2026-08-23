#!/usr/bin/env python3
"""
RUN 52. THE INJECTION CAMPAIGN: PROVING EVERY GUARANTEE THIS RUN MAKES CAN FAIL.

An absence check that cannot be made to fail proves nothing. Each fault below writes a real
byte change into a real file, RE-READS THE FILE FROM DISK to confirm the injection landed,
runs the guard, requires RED for the INTENDED reason, RESTORES FROM THE PRE-INJECTION SNAPSHOT
INSIDE A FINALLY THAT CANNOT BE SKIPPED, asserts the restored bytes equal the snapshot exactly,
and RE-RUNS THE BASELINE. The baseline recheck happens after EVERY SINGLE injection, because
Runs 48 through 51 all recorded an injection pass aborting after writing a fault and before
restoring it -- and this run found a LEAKED INJECTION in server/app/simulation/canonical_v8.py
left behind by a campaign in the very first full-suite pass.

A RAISE IS A FAILURE AND ITS TRACEBACK IS PRINTED.

Usage: python tools/run52_injection_campaign.py
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOLS = ROOT / "server" / "tools"
PASSED = 0
FAILED = 0
_fail: list[str] = []


def check(ok, label, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        _fail.append(label)
        print(f"  ****  {label}" + (f"   [{detail}]" if detail else ""))
    return bool(ok)


def suite(name: str) -> tuple[int, str]:
    import os
    import shutil
    import tempfile
    d = tempfile.mkdtemp()
    db = pathlib.Path(d) / "x.db"
    shutil.copyfile(BASE_DB, db)
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}",
               SESSION_SECRET="test-secret-do-not-use-in-prod", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, name], cwd=str(TOOLS), capture_output=True,
                       text=True, encoding="utf-8", env=env)
    shutil.rmtree(d, ignore_errors=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


BASE_DB = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
assert BASE_DB and BASE_DB.is_file(), "pass a migrated throwaway sqlite as argv[1]"


def fault(n, relpath, old, new, guard, expect_in_red, why):
    """Inject, confirm it landed, require RED for the intended reason, restore, recheck."""
    print()
    print("=" * 94)
    print(f"FAULT {n}: {why}")
    print("=" * 94)
    p = ROOT / relpath
    snapshot = p.read_bytes()                      # PRE-INJECTION SNAPSHOT
    try:
        assert old in snapshot, f"the text to replace is not in {relpath}"
        p.write_bytes(snapshot.replace(old, new, 1))
        # RE-READ FROM DISK. Not from the variable that was written.
        landed = p.read_bytes()
        if not check(landed != snapshot and new in landed,
                     f"INJECTION LANDED in {relpath}, confirmed by re-reading the bytes from "
                     f"disk"):
            return
        rc, out = suite(guard)
        red = rc != 0
        reason = expect_in_red in out
        check(red, f"{guard} goes RED with the fault in place", f"exit {rc}")
        check(reason,
              f"and it goes red FOR THE INTENDED REASON, not incidentally",
              f"expected {expect_in_red!r} in the output")
    finally:
        # RESTORE. Inside a finally that cannot be skipped, whatever happened above.
        p.write_bytes(snapshot)
        restored = p.read_bytes()
        check(restored == snapshot,
              f"RESTORED: {relpath} is byte-identical to its pre-injection snapshot")
    # BASELINE RECHECK, after EVERY injection.
    rc, out = suite(guard)
    check(rc == 0, f"BASELINE RECHECKED after fault {n}: {guard} is green again",
          out.strip().splitlines()[-1] if out.strip() else f"exit {rc}")


try:
    # ---------------------------------------------------------------------------------------
    # GUARANTEE 4/5: the see-Health button renders nowhere, and that check is not vacuous.
    fault(1, "assets/js/deepdive.js",
          b'healthLine.innerHTML = `${escg(anomaly)}`;',
          b'healthLine.innerHTML = `${escg(anomaly)} <button type="button" class="dd-link" '
          b'data-goto-health>see Health &rarr;</button>`;',
          "test_run28_participant_packages.py",
          "neither the button nor its handler survives",
          "the dead see-Health button is PUT BACK into deepdive.js. The guarantee that it "
          "renders nowhere must go red, or it was never measuring anything.")

    # ---------------------------------------------------------------------------------------
    # GUARANTEE 7: one name for the module identifier, on both sides.
    fault(2, "server/tools/taxonomy_authority.json",
          b'"module_id": "A1.7"',
          b'"key": "A1.7"',
          "test_run32_client_authority.py",
          "KeyError",
          "ONE module row in the authority is reverted to the old name `key`. The client "
          "authority guard must go red, or the single-name claim is unmeasured.")

    # ---------------------------------------------------------------------------------------
    # GUARANTEE 8: both generated mirrors match their generator.
    fault(3, "assets/js/taxonomy.js",
          b"module_id: 'A1.7'",
          b"module_id: 'A1.7-DRIFTED'",
          "test_run32_client_authority.py",
          "BOTH client taxonomy artifacts",
          "a mirror is hand-edited away from what the generator produces. The "
          "generated-from-authority guard must go red.")

    # ---------------------------------------------------------------------------------------
    # SECTION 8.1: the project list's only route to the detail page.
    fault(4, "assets/js/app.js",
          '<button class="btn small li-open" data-open="${esc(p.id)}" title="Open project '
          'detail">Open \u2192</button>'.encode("utf-8"),
          b'',
          "test_run28_participant_packages.py",
          "BYTE FOR BYTE identical to v19: ruling 1 was stopped",
          "the Open control is REMOVED from the project list, which is what ruling 1 asked "
          "for and what section 8.1 stopped. The package guard must go red, proving the "
          "stop is enforced and not merely asserted in prose.")

    # ---------------------------------------------------------------------------------------
    # GUARANTEE 9 / SECTION 9.4: dispatch across all 101.
    fault(5, "assets/js/taxonomy.js",
          b'if (m && m.method_class && m.module_id) METHOD_TO_MODULE_ID[m.method_class] = '
          b'm.module_id;',
          b'if (m && m.method_class && m.key) METHOD_TO_MODULE_ID[m.method_class] = m.key;',
          "test_run32_method_class_agreement.py",
          "every renamed module's status RESOLVES",
          "THE DISPATCH PATH is reverted to reading the old field name, so the "
          "method_class-to-module_id join goes empty. The dispatch guard must go red.")

    # ---------------------------------------------------------------------------------------
    # GUARANTEE 17: a sequence-bearing file moving with no exception record.
    fault(6, "server/tools/participant_packages.py",
          b'V19_TO_V20_SEQUENCE_EXCEPTION = ("assets/js/deepdive.js",)',
          b'V19_TO_V20_SEQUENCE_EXCEPTION = ()',
          "test_run28_participant_packages.py",
          "THE EXPERIMENTAL SEQUENCE MOVED ACROSS v19 TO v20",
          "the one sequence-bearing exception record is DELETED while the file still moved. "
          "The invariant must go red: a sequence-bearing file moving without its own named "
          "record is exactly what this check exists to catch.")

except Exception:
    traceback.print_exc()
    FAILED += 1
    _fail.append("the campaign raised -- traceback above")

print()
print("=" * 94)
if _fail:
    print(f"{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(0 if FAILED == 0 else 1)
