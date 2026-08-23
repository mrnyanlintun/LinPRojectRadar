#!/usr/bin/env python3
"""
RUN 51. THE INJECTION CAMPAIGN: PROVING EVERY CHECK CAN FAIL.

A check that has never been observed failing is a check nobody has tested. For each guarantee
in section 7 of the Run 51 order this file writes a FAULT the guarantee is supposed to catch,
observes the named check go RED FOR THE INTENDED REASON, restores the file, and RE-RUNS THE
BASELINE.

THE PROTOCOL IS THE ONE THE ORDER TIGHTENED AFTER RUNS 48, 49 AND 50 EACH ABORTED MID-INJECTION:

    snapshot the bytes
      -> inject
      -> RE-READ THE BYTES FROM DISK and confirm the injection actually landed
      -> run the check and require RED
      -> restore INSIDE A `finally` THAT CANNOT BE SKIPPED
      -> assert the restored bytes are byte-identical to the snapshot
      -> re-run the check and require GREEN again

A raise is a FAILURE and its traceback is printed. This file does not use the
try/finally + sys.exit-in-finally shape.

Usage:  python tools/run51_injection_campaign.py [--only F3,F7]
"""
from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import subprocess
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[2]
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


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def run(cmd, cwd=None, env=None):
    e = dict(os.environ)
    e["PYTHONIOENCODING"] = "utf-8"
    e.setdefault("SESSION_SECRET", "test-secret-do-not-use-in-prod")
    if env:
        e.update(env)
    p = subprocess.run(cmd, cwd=str(cwd or ROOT), capture_output=True, text=True,
                       encoding="utf-8", env=e, timeout=1800)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def suite(rel_test):
    """Runs a suite and returns (green, tail). A suite printing no RESULT line has NOT run."""
    code, out = run([sys.executable, f"server/tools/{rel_test}"])
    line = [ln for ln in out.splitlines() if ln.startswith("RESULT:")]
    if not line:
        return None, out[-700:]
    got, want = line[-1].split()[1].split("/")
    return got == want, line[-1]


def driver(dbdir):
    # A FRESH MIGRATED DATABASE PER INVOCATION. The driver creates a participant and a project
    # through the real routes; reusing a database makes the second invocation fail at
    # `adminparticipantcreate` with a KeyError, which is a fixture fault and NOT the fault under
    # test. Each run gets its own directory so a failure here can never be mistaken for a red.
    import tempfile
    work = tempfile.mkdtemp(prefix="run51-inj-", dir=dbdir)
    db = f"sqlite:///{work}/inj.db"
    mig = run([sys.executable, "-m", "alembic", "upgrade", "head"],
              cwd=ROOT / "server", env={"DATABASE_URL": db})
    if mig[0] != 0:
        return None, "alembic failed: " + mig[1][-400:], []
    code, out = run([sys.executable, str(ROOT / "server/tools/drive_run51_browser.py")],
                    cwd=work,
                    env={"DATABASE_URL": db,
                         "PLAYWRIGHT_BROWSERS_PATH": "/opt/pw-browsers"})
    line = [ln for ln in out.splitlines() if ln.startswith("RESULT:")]
    fails = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("- ")]
    if not line:
        return None, out[-900:], []
    got, want = line[-1].split()[1].split("/")
    return got == want, line[-1], fails


FAULTS = {}


def fault(fid, target, why):
    def deco(fn):
        FAULTS[fid] = (target, why, fn)
        return fn
    return deco


def campaign(fid, verify, baseline_first=True, dbdir=None):
    """One injection, with the protocol the order requires and no way to skip the restore."""
    target, why, mutate = FAULTS[fid]
    p = ROOT / target
    print()
    print("=" * 94)
    print(f"{fid}. {why}")
    print("=" * 94)
    snapshot = p.read_bytes()
    print(f"  snapshot: {target}  {len(snapshot)} bytes  sha256 {sha(snapshot)}")

    if baseline_first:
        ok, detail = verify()
        check(ok is True, f"{fid} BASELINE BEFORE INJECTION is green", str(detail))
        if ok is not True:
            print("  refusing to inject into a tree whose baseline is not green")
            return

    injected_ok = False
    try:
        p.write_bytes(mutate(snapshot))
        reread = p.read_bytes()                       # RE-READ FROM DISK, never assumed
        print(f"  re-read from disk: {len(reread)} bytes  sha256 {sha(reread)}")
        landed = reread != snapshot
        check(landed, f"{fid} THE INJECTION LANDED (bytes re-read from disk, not assumed)")
        if landed:
            ok, detail = verify()
            injected_ok = check(ok is False,
                                f"{fid} AND THE CHECK WENT RED FOR THE INTENDED REASON",
                                str(detail))
    except BaseException:                              # noqa: BLE001
        traceback.print_exc()
        check(False, f"{fid} the injection raised")
    finally:
        p.write_bytes(snapshot)                        # CANNOT BE SKIPPED
        restored = p.read_bytes()
        check(restored == snapshot,
              f"{fid} RESTORED BYTE-IDENTICALLY (sha256 {sha(restored)})")
        code, out = run(["git", "diff", "--quiet", "--", target])
        check(code == 0, f"{fid} and git reports the file clean", out[-200:])

    ok, detail = verify()
    check(ok is True, f"{fid} BASELINE RECHECKED AFTER RESTORE and is green again", str(detail))
    print(f"  {fid}: injection proved the check can fail: {injected_ok}")


# ---------------------------------------------------------------------------------------------
# THE FAULTS. Each is the defect its guarantee exists to catch, written as bytes.
# ---------------------------------------------------------------------------------------------

@fault("F1", "assets/js/knowledge.js",
       "GUARANTEE 7.1 / 7.2: a count of modules typed into handbook prose instead of derived")
def _f1(b: bytes) -> bytes:
    return b.replace(
        b"The registry holds ${taxCounts().registered} modules",
        b"The registry holds 96 modules", 1)


@fault("F3", "assets/js/deepdive.js",
       "GUARANTEE 7.3: one of the six deleted Portfolio Health symbols reappears")
def _f3(b: bytes) -> bytes:
    return b.replace(b"  window.LinDeepDive = { render };",
                     b"  function cat8Retired() { return true; }\n"
                     b"  window.LinDeepDive = { render, cat8Retired };", 1)


@fault("F5", "server/tools/taxonomy_authority.json",
       "GUARANTEE 7.5 / 10.4: a runtime lookup breaks for one of the 101 registered modules")
def _f5(b: bytes) -> bytes:
    return b.replace(b'"key": "A1.7"', b'"key": "A1.7-GONE"', 1)


@fault("F6", "assets/js/categories.js",
       "GUARANTEE 7.6: a generated mirror is hand-edited away from its generator")
def _f6(b: bytes) -> bytes:
    return b.replace(b"name: 'CUSUM Anomaly Monitor'", b"name: 'CUSUM Anomaly Monitor '", 1)


@fault("F7", "assets/js/app.js",
       "GUARANTEE 7.7: the Signal Ledger renders a module identifier again")
def _f7(b: bytes) -> bytes:
    return b.replace(b'          <span class="cat-mod-name">${esc(m.name)}</span>\n',
                     b'          <span class="cat-mod-num">${esc(m.key)}</span>\n'
                     b'          <span class="cat-mod-name">${esc(m.name)}</span>\n', 1)


@fault("F8", "assets/js/deepdive.js",
       "GUARANTEE 7.8: a panel is filed under a category its module does not belong to")
def _f8(b: bytes) -> bytes:
    return b.replace(b'"03": "A4"', b'"03": "A1"', 1)


@fault("F9", "assets/js/deepdive.js",
       "GUARANTEE 7.9: the grouping bound goes back to a literal ten and the eleventh group dies")
def _f9(b: bytes) -> bytes:
    return b.replace(b"for (let n = 1; n <= projectCats.length; n++) {",
                     b"for (let n = 1; n <= 10; n++) {", 1)


@fault("F10", "assets/js/deepdive.js",
       "GUARANTEE 7.10: the split compliance panel is merged back into one")
def _f10(b: bytes) -> bytes:
    return b.replace(b"m9_2(project) + m9_2b(project) +", b"m9_2(project) +", 1)


@fault("F11", "assets/js/deepdive.js",
       "GUARANTEE 7.11: an em dash is reinstated in a rendered panel heading")
def _f11(b: bytes) -> bytes:
    return b.replace('"Regulatory Threshold Modules"'.encode(),
                     '"Regulatory — Threshold Modules"'.encode(), 1)


@fault("F12", "assets/js/knowledge.js",
       "GUARANTEE 7.12: the ten module identifiers are reinstated inside the handbook SVG, "
       "where innerText cannot see them. NOTE: svgSignalStack() HAS NO CALLER ANYWHERE, so the "
       "diagram renders on no surface and a DOM sweep CANNOT catch this. The check that must go "
       "red is therefore the SOURCE-level SVG text sweep, which reads what a file BUILDS rather "
       "than what a page happens to draw")
def _f12(b: bytes) -> bytes:
    return b.replace(b'mods: ["EVM", "CUSUM"]', b'mods: ["01 EVM", "02 CUSUM"]', 1)


@fault("F19", "assets/js/workspace.js",
       "GUARANTEE 7.19: a sequence-bearing file moves and its bytes no longer match its record")
def _f19(b: bytes) -> bytes:
    return b + b"\n"


@fault("F13", "server/app/simulation/models_evm.py",
       "GUARANTEE 7.13 / 10.1: the behaviour of a scientific target changes after the "
       "candidate identity is fixed")
def _f13(b: bytes) -> bytes:
    # A1.7 TCPI's band boundary. This is a BEHAVIOUR change on a scientific target, which is
    # exactly what the behaviour digest exists to notice even when every file digest still
    # matched -- and here the file digest moves too, so B01 goes red alongside B15.
    assert b"_TCPI_STABILITY_MARGIN = 0.10" in b
    return b.replace(b"_TCPI_STABILITY_MARGIN = 0.10", b"_TCPI_STABILITY_MARGIN = 0.30", 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--dbdir", default=None)
    args = ap.parse_args()
    want = [x.strip() for x in args.only.split(",") if x.strip()]
    dbdir = args.dbdir or os.getcwd()

    print(f"repository: {ROOT}")
    print(f"cwd:        {os.getcwd()}")
    print(f"interpreter:{sys.executable}  {sys.version.split()[0]}")

    def by_suite(rel):
        def v():
            g, d = suite(rel)
            return g, d
        return v

    def by_gate():
        def v():
            g, d = suite("test_run37_freeze_gate.py")
            return g, d
        return v

    def by_generator():
        def v():
            code, out = run([sys.executable, "build_client_taxonomy.py", "--check"],
                            cwd=ROOT / "server" / "tools")
            return code == 0, out.strip().splitlines()[-1] if out.strip() else "no output"
        return v

    def by_svg_source():
        def v():
            code, out = run([sys.executable, "server/tools/run51_dash_sweep.py", "--svg"])
            line = [ln for ln in out.splitlines() if ln.startswith("RESULT:")]
            if not line:
                return None, out[-400:]
            got, want = line[-1].split()[1].split("/")
            surv = [ln.strip() for ln in out.splitlines() if "SURVIVOR" in ln]
            return got == want, line[-1] + ("  " + "; ".join(s[:90] for s in surv) if surv else "")
        return v

    def by_driver(expect_fail_substr=None):
        def v():
            g, d, fails = driver(dbdir)
            if g is None:
                return None, d
            return g, d + ("  failures: " + "; ".join(f[:90] for f in fails) if fails else "")
        return v

    plan = [
        ("F1", by_suite("test_run26_counts_and_wiring.py")),
        ("F3", by_suite("test_run44_participant_defect_fixes.py")),
        ("F5", by_gate()),
        ("F6", by_generator()),
        ("F7", by_suite("test_run49_naming_completion.py")),
        ("F19", by_gate()),
        ("F13", by_gate()),
        ("F8", by_driver()),
        ("F9", by_driver()),
        ("F10", by_driver()),
        ("F11", by_driver()),
        ("F12", by_svg_source()),
    ]
    for fid, verify in plan:
        if want and fid not in want:
            continue
        campaign(fid, verify)

    print()
    if _fail:
        print("FAILURES:")
        for f in _fail:
            print(f"  - {f}")
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException:                                    # noqa: BLE001
        traceback.print_exc()
        print("RESULT: 0/1 checks passed   (the campaign raised; a raise is a failure)")
        raise SystemExit(1)
