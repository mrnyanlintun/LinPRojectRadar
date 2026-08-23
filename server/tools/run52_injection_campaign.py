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

# --- CAMPAIGN SAFETY (Run 54, phase A) -----------------------------------------------------
# THE START-AND-END DIRTY-TREE GUARD. A campaign must not BEGIN on a dirty tree: Run 53
# established that a leaked fault is snapshotted from disk by the next campaign, faithfully
# restored by its `finally`, and thereby CERTIFIED by its own passing assertion. An end-only
# check cannot see that, because the leak began in an earlier process. See
# server/tools/campaign_safety.py for the full mechanism and the proof.
import sys as _cs_sys, pathlib as _cs_pl                                       # noqa: E402
_cs_sys.path.insert(0, str(_cs_pl.Path(ROOT) / "server" / "tools"))
from campaign_safety import (arm as _cs_arm, restore_guard, head_text, head_bytes,  # noqa: E402,F401
                             snapshot_text, CampaignTreeDirty)
_cs_arm(_cs_pl.Path(ROOT), "run52_injection_campaign.py",
        allow=[])
# -------------------------------------------------------------------------------------------
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
    # RUN 55: THE SNAPSHOT IS TAKEN FROM THE COMMITTED BYTES AT HEAD, NOT FROM DISK. Run 53
    # established the cementing sequence: a fault left on disk by a process that died before its
    # `finally` is SNAPSHOTTED by the next campaign, faithfully restored, and its own assertion
    # `restored == snapshot` then PASSES while the guard stays neutered. A snapshot that cannot
    # see the corruption cannot restore it. The campaign is armed, so it has already refused to
    # begin on a dirty tree before reaching this line.
    # RUN 55: A FAULT MAY NOW ALSO BE A RESURRECTION.
    # Run 54 phase B DELETED assets/js/deepdive.js, so fault 1's subject no longer exists at
    # HEAD and its injection could not apply -- a fault that cannot apply proves nothing. The
    # guarantee it existed to prove has not gone away; it has become STRICTER, from "the button
    # renders nowhere" to "the file renders nowhere because it does not exist". So the way to
    # prove that guarantee can still fail is to PUT THE FILE BACK, which is what this branch
    # does. `absent` faults create the file with `new` and DELETE it again in the `finally`;
    # everything else -- confirm from disk, require red for the intended reason, restore,
    # recheck the baseline -- is unchanged.
    absent = subprocess.run(["git", "cat-file", "-e", f"HEAD:{relpath}"], cwd=ROOT,
                            capture_output=True).returncode != 0
    snapshot = None if absent else head_bytes(ROOT, relpath)   # SNAPSHOT FROM HEAD, NOT DISK
    if absent:
        check(not p.is_file(),
              f"NON-VACUITY: {relpath} really is absent before this fault, so recreating it is "
              f"a real change")
    try:
        if absent:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(new)
        else:
            assert old in snapshot, f"the text to replace is not in {relpath}"
            p.write_bytes(snapshot.replace(old, new, 1))
        # RE-READ FROM DISK. Not from the variable that was written.
        landed = p.read_bytes()
        if not check(landed != (snapshot or b"") and new in landed,
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
        if absent:
            if p.is_file():
                p.unlink()
            check(not p.is_file(),
                  f"RESTORED: {relpath} is absent again, as it is at HEAD")
        else:
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
          b'',
          b'/* RUN 55 INJECTION: this file was DELETED by Run 54 phase B. Recreating it is the\n'
          b'   fault. */\nwindow.LinDeepDive = { render: function () {} };\n'
          b'// healthLine.innerHTML = `${escg(anomaly)} <button type="button" class="dd-link" '
          b'data-goto-health>see Health &rarr;</button>`;\n',
          "test_run28_participant_packages.py",
          "really is absent from the tree",
          "RUN 55 REVISES THIS FAULT. It used to PUT THE DEAD see-Health BUTTON BACK into "
          "assets/js/deepdive.js. Run 54 phase B deleted that file on the owner's ruling, so "
          "the anchor no longer existed and the injection could not apply. The guarantee it "
          "proved has become STRICTER rather than going away -- from 'the button renders "
          "nowhere' to 'the file renders nowhere because it does not exist' -- so the fault is "
          "revised to the inverse: THE FILE IS PUT BACK. The v21 package guard must go red, or "
          "the declared-deletion record was never measuring anything.")

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
    # RUN 55, PHASE C. FAULT 4 IS REVISED, NOT DELETED.
    #
    # WHAT IT INJECTED BEFORE: it REMOVED the Open control from the project list and required
    # test_run28_participant_packages.py to go red, because Run 52's section 8.1 had stopped
    # that removal and the campaign proved the stop was enforced rather than merely written
    # down. Run 54 phase C carried out the removal on the owner's ruling, so THE ANCHOR THIS
    # FAULT SEARCHED FOR NO LONGER EXISTS IN app.js: the injection could not apply, and a fault
    # that cannot apply proves nothing.
    #
    # WHAT IT INJECTS NOW: THE EXACT INVERSE. It PUTS THE Open CONTROL BACK, byte for byte as
    # Run 52 recorded it, and requires the revised guard to go red. That is the proof section 9
    # of the Run 55 order asks for -- restore Open, confirm red, restore -- run inside this
    # campaign's own protocol: snapshot from the committed bytes, restore in a `finally`, and
    # recheck the baseline afterwards.
    fault(4, "assets/js/app.js",
          '<button class="btn small li-manage" data-manage="${esc(p.id)}" title="Open project '
          'detail">Manage</button>`'.encode("utf-8"),
          '<button class="btn small li-manage" data-manage="${esc(p.id)}" title="Open project '
          'detail">Manage</button>` +\n            `<button class="btn small li-open" '
          'data-open="${esc(p.id)}" title="Open project detail">Open \u2192</button>`'
          .encode("utf-8"),
          "test_run28_participant_packages.py",
          "the project list no longer renders the Open control",
          "the Open control is PUT BACK into the project list, which is the state Run 54 "
          "phase C reversed. The revised package guard must go red, proving the revision "
          "measures the CURRENT state and is not merely asserted in prose.")

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
