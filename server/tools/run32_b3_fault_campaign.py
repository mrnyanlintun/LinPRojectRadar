"""
RUN 32 FINAL CLOSURE. THE SIX-FAULT NON-VACUITY CAMPAIGN FOR THE METHOD-CLASS GUARDS.

The defect being closed here was invisible for two and four runs behind entirely green suites,
because a stale join key does not raise -- it returns null. So the guards that now watch it are
broken on purpose and required to go RED FOR THE INTENDED REASON.

Same discipline as the campaigns before it: a crash is NOT red; an unrelated failure is not
evidence; the mutation is verified by re-reading the bytes from disk; __pycache__ is cleared on
both sides; every file is restored byte for byte and the baseline re-run and required green.

Writes code_audit/run32_b3_fault_injection.csv.
"""
from __future__ import annotations

import csv, os, pathlib, re, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
SERVER = HERE.parent
ROOT = SERVER.parent

# --- CAMPAIGN SAFETY (Run 54, phase A) -----------------------------------------------------
# THE START-AND-END DIRTY-TREE GUARD. A campaign must not BEGIN on a dirty tree: Run 53
# established that a leaked fault is snapshotted from disk by the next campaign, faithfully
# restored by its `finally`, and thereby CERTIFIED by its own passing assertion. An end-only
# check cannot see that, because the leak began in an earlier process. See
# server/tools/campaign_safety.py for the full mechanism and the proof.
import sys as _cs_sys, pathlib as _cs_pl                                       # noqa: E402
_cs_sys.path.insert(0, str(_cs_pl.Path(ROOT) / "server" / "tools"))
from campaign_safety import (arm as _cs_arm, restore_guard, head_text,          # noqa: E402,F401
                             snapshot_text, CampaignTreeDirty)
_cs_arm(_cs_pl.Path(ROOT), "run32_b3_fault_campaign.py",
        allow=["code_audit/run32_b3_fault_injection.csv"])
# -------------------------------------------------------------------------------------------

AGREE = "test_run32_method_class_agreement.py"
GENERATED = "test_run11_defensibility_claims.py"
CATEGORIES = ROOT / "assets" / "js" / "categories.js"
TAXONOMY = ROOT / "assets" / "js" / "taxonomy.js"
EVIDENCE = ROOT / "assets" / "js" / "ds_defensibility_evidence.js"

RENAMES = [("B3.2", "EVMS_Applicability", "FAR_Threshold"),
           ("B3.3", "A11_Conformance", "OMB_A11_Check"),
           ("B3.4", "EVMS_Reporting_Compliance", "EVM_Reporting_Threshold"),
           ("B3.5", "Modification_Governance", "Contract_Mod_Frequency")]


def clear_pycache():
    for d in SERVER.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


_T = None


def template_db():
    global _T
    if _T is None:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="run32b3-"))
        db = tmp / "t.db"
        env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}", SESSION_SECRET="test-secret")
        r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                           cwd=SERVER, env=env, capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("alembic failed:\n" + r.stdout + r.stderr)
        _T = db
    return _T


def run_guard(suite):
    t = template_db()
    db = t.parent / f"{suite}.{os.getpid()}.db"
    shutil.copy(t, db)
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}", SESSION_SECRET="test-secret",
               PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, suite], cwd=HERE, env=env,
                       capture_output=True, text=True, timeout=1800)
    out = (r.stdout or "") + (r.stderr or "")
    res = None
    for ln in out.splitlines():
        s = ln.strip()
        if s.startswith("RESULT: ") and "/" in s:
            res = s
    db.unlink(missing_ok=True)
    return r.returncode, out, res


def failing_lines(out):
    L = []
    for raw in out.splitlines():
        s = raw.strip()
        if s.startswith(("FAIL: ", "FAILED: ")):
            L.append(s.split(": ", 1)[1])
        elif s.startswith("FAIL "):
            L.append(s[5:])
        elif s.startswith("**** "):
            L.append(s[5:].strip())
        elif s.startswith("- "):
            L.append(s[2:])
    return L


def is_green(res):
    if not res:
        return False
    a, b = res.split("RESULT: ", 1)[1].split()[0].split("/")
    return a == b


def faults():
    F = []
    for i, (mid, cur, old) in enumerate(RENAMES, start=1):
        F.append((i, f"{mid}, client taxonomy identifier",
                  f"{mid}'s client method class is the identifier its production runner emits; a "
                  f"superseded one makes the status lookup return null instead of failing",
                  TAXONOMY, f"method_class: '{cur}'", f"method_class: '{old}'", AGREE,
                  "no module carries a method class its production runner has stopped emitting"))
    # 5 -- a client lookup silently returns an empty result. The alias matcher is neutered so
    #      every join misses. This is the exact failure mode the defect had: null, not an error.
    F.append((5, "assets/js/categories.js linMethodClassMatches",
              "the status lookup RESOLVES; a join that silently returns null rather than raising "
              "is the failure mode that hid this defect for four runs",
              CATEGORIES,
              "  if (candidate === wanted) return true;",
              "  if (false) return true;",
              AGREE,
              "every renamed module's status RESOLVES rather than silently returning null"))
    # 6 -- a generated file disagrees with its authority source.
    m = re.search(r'"B3\.2": \{.*?\},\n', EVIDENCE.read_text(encoding="utf-8"), re.S)
    F.append((6, "assets/js/ds_defensibility_evidence.js, a GENERATED file",
              "a generated file matches what its generator produces from the authority; a hand "
              "edit that leaves the source stale is the shape of the root cause this run closed",
              EVIDENCE, m.group(0),
              m.group(0).replace('"B3.2": {', '"B3.2": { tampered: "yes",', 1), GENERATED,
              "the committed evidence object is byte-identical to what the generator produces"))
    return F


def main():
    HDR = ["fault_id", "module/system", "invariant", "baseline command", "mutation target",
           "mutation description", "mutation applied?", "fault command", "process exit code",
           "anchored RESULT present?", "expected RED reason", "actual RED reason", "crash?",
           "unrelated failure?", "restored?", "restored GREEN?", "final status", "notes"]
    rows, t = [], dict(att=0, app=0, red=0, rest=0, na=0, crash=0, unrel=0)
    for fid, system, inv, target, old, new, guard, reason in faults():
        t["att"] += 1
        cmd = f"cd server/tools && python3 {guard}"
        clear_pycache()
        brc, bout, bres = run_guard(guard)
        if not is_green(bres):
            rows.append([fid, system, inv, cmd, str(target), "-", "NO", cmd, brc,
                         "YES" if bres else "NO", reason, "-", "NO", "NO", "n/a", "NO",
                         "NOT_ATTEMPTED_BASELINE_RED", f"baseline not green ({bres})"])
            t["na"] += 1
            continue
        baseline = bres
        orig = target.read_bytes()
        text = orig.decode("utf-8")
        if text.count(old) != 1:
            rows.append([fid, system, inv, cmd, str(target.relative_to(ROOT)),
                         "anchor not unique", "NO", cmd, "-", "YES", reason, "-", "NO", "NO",
                         "n/a", "n/a", "NOT_APPLIED", f"anchor occurs {text.count(old)} times"])
            t["na"] += 1
            continue
        clear_pycache()
        target.write_bytes(text.replace(old, new, 1).encode("utf-8"))
        disk = target.read_bytes().decode("utf-8")
        if not (new in disk and disk != text):
            target.write_bytes(orig)
            clear_pycache()
            rows.append([fid, system, inv, cmd, str(target.relative_to(ROOT)), "byte replacement",
                         "NO", cmd, "-", "YES", reason, "-", "NO", "NO", "YES", "n/a",
                         "NOT_APPLIED", "mutation did not survive a re-read from disk"])
            t["na"] += 1
            continue
        t["app"] += 1
        # RUN 55, PHASE B. THE GUARD RUN IS INSIDE A `try` AND THE RESTORE IS ITS
        # `finally`. The restore was a bare statement after run_guard(), so a raise in
        # run_guard -- a timeout, a decode error, a kill -- left the mutated bytes on
        # disk. Run 53 established that the next campaign then snapshots the corruption
        # and cements it with its own correct restore. The arm() guard is the fix; this
        # is the hygiene, and a known-incomplete repair is not left half-done.
        try:
            frc, fout, fres = run_guard(guard)
            crash = fres is None
            red = fres is not None and not is_green(fres)
            fails = failing_lines(fout)
            intended = red and any(reason.strip().lower() in f.strip().lower() for f in fails)
            actual = ("no RESULT line (crash)" if crash else
                      ("; ".join(dict.fromkeys(f.strip()[:110] for f in fails)) or fres) if red
                      else "GREEN - guard did not notice")
        finally:
            clear_pycache()
            target.write_bytes(orig)
        restored = target.read_bytes() == orig
        clear_pycache()
        rrc, rout, rres = run_guard(guard)
        rgreen = is_green(rres) and rres == baseline
        notes = []
        if crash:
            t["crash"] += 1
            status = "CRASH_NOT_ACCEPTED_AS_RED"
            notes.append("guard died without an anchored RESULT line; a crash is NOT red")
        elif not red:
            status = "GUARD_DID_NOT_FIRE"
            notes.append("guard stayed green under the mutation")
        elif not intended:
            t["unrel"] += 1
            status = "RED_FOR_AN_UNRELATED_REASON"
            notes.append("red, but its output did not name the intended property")
        else:
            t["red"] += 1
            status = "RED_FOR_THE_INTENDED_REASON"
        if rgreen:
            t["rest"] += 1
        else:
            notes.append(f"baseline did not return to {baseline} (got {rres})")
        rows.append([fid, system, inv, cmd, str(target.relative_to(ROOT)),
                     f"replace {old.strip().splitlines()[0][:70]!r}", "YES", cmd, frc,
                     "NO" if crash else "YES", reason, actual, "YES" if crash else "NO",
                     "YES" if (red and not intended) else "NO", "YES" if restored else "NO",
                     "YES" if rgreen else "NO", status, "; ".join(notes) or "clean"])
        print(f"fault {fid}  {status:32s}  {actual[:80]}")
    out = ROOT / "code_audit" / "run32_b3_fault_injection.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HDR)
        w.writerows(rows)
    print()
    print("attempted", t["att"], "| applied", t["app"], "| intended RED", t["red"],
          "| restored GREEN", t["rest"])
    print("NOT_APPLIED", t["na"], "| crashes accepted as RED 0 (%d recorded)" % t["crash"],
          "| unrelated accepted as RED 0 (%d recorded)" % t["unrel"])
    print("wrote", out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
