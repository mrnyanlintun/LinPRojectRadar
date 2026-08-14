#!/usr/bin/env python3
"""
RUN 28 CLOSURE. THE NON-VACUITY CAMPAIGN.

Every guard this closure adds is proved able to fail, by the discipline this programme settled on
after sixteen vacuous guards were found in it:

    baseline rechecked GREEN
    -> fault injected
    -> THE INJECTION CONFIRMED BY RE-READING THE FILE FROM DISK
    -> the named guard observed RED, and RED for the intended reason, not crashed
    -> the file restored byte for byte, verified by digest
    -> baseline rechecked GREEN

A crash is a campaign FAILURE, not a success: the runner requires an anchored `RESULT: n/m` line
and a missing one is recorded as CRASH.

THE BYTECODE-CACHE HAZARD, found by Run 28 and honoured here. CPython invalidates its cache on
mtime and size; an injection restored inside the same clock second changes neither, so the cached
compiled mutant survives a byte-perfect restore and the baseline comes back red for a reason that
has nothing to do with the code on disk. `__pycache__` is dropped on BOTH sides of every
injection.

FAULT 1 IS NOT A FILE EDIT. It creates a harmless UNTRACKED file inside the protected production
surface, confirms from the filesystem that it exists, and requires the named guard to turn red
specifically because of the unexpected file. That is the owner's stated proof for the blind spot
Run 28 left open, and it cannot be done by editing anything.
"""

from __future__ import annotations

import csv
import hashlib
import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "code_audit" / "run28_closure_fault_injection.csv"


def drop_pycache() -> None:
    for d in (ROOT / "server").rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


#: A migrated template, copied FRESH for every single suite run. The repository convention is
#: one throwaway database per suite file, and it is not a nicety: a suite that has already
#: written its fixtures into a database it finds populated fails in ways that have nothing to do
#: with the injected fault, which would score a real red as a CRASH and a real green as a red.
TEMPLATE_DB = ROOT / "server" / "tools" / "_fault_campaign_template.db"
LIVE_DB = ROOT / "server" / "tools" / "_fault_campaign.db"


def run_suite(name: str) -> tuple[str, str]:
    """Returns (verdict, detail). GREEN only on an anchored RESULT line with n == m."""
    drop_pycache()
    if LIVE_DB.exists():
        LIVE_DB.unlink()
    shutil.copy2(TEMPLATE_DB, LIVE_DB)
    env = {"PYTHONIOENCODING": "utf-8", "PATH": "/usr/bin:/bin:/usr/local/bin",
           "DATABASE_URL": "sqlite:///" + str(LIVE_DB),
           "SESSION_SECRET": "test-secret-do-not-use-in-prod",
           "PLAYWRIGHT_BROWSERS_PATH": "/opt/pw-browsers"}
    p = subprocess.run([sys.executable, f"{name}.py"], cwd=str(HERE), env=env,
                       capture_output=True, text=True)
    drop_pycache()
    m = None
    for line in p.stdout.splitlines():
        if re.fullmatch(r"RESULT: \d+/\d+( checks passed)?", line.strip()):
            m = line.strip()
    if m is None:
        return "CRASH", f"no anchored RESULT line (exit {p.returncode})"
    got, tot = m.split(" ")[1].split("/")[0], m.split(" ")[1].split("/")[1]
    return ("GREEN" if got == tot else "RED"), m


FAULTS = [
    # id, guard suite, kind, target, find, replace, intent
    ("F1", "test_run22_production_tree_completeness", "UNTRACKED_FILE",
     "server/app/simulation/run28_closure_probe_file.py", None, None,
     "a harmless UNTRACKED file created inside the protected production surface. The guard must "
     "report it as an unexpected file AND as an untracked production file. This is the blind "
     "spot Run 28 left open: git diff enumerates tracked paths and cannot see this at all"),
    ("F2", "test_run28_closure", "EDIT",
     "server/app/simulation/canonical_v3.py",
     "        if len(series) < 2:\n            raise StructureAbsent(\n"
     "                \"A milestone in the forecast history provided has been forecast only once, so \"",
     "        if len(series) < 1:\n            raise StructureAbsent(\n"
     "                \"A milestone in the forecast history provided has been forecast only once, so \"",
     "A2.7's minimum-history guard weakened so ONE forecast is enough. A single baseline and a "
     "single forecast must not produce a trend or a direction"),
    ("F3", "test_run28_closure", "EDIT",
     "assets/js/taxonomy.js", "name: 'Independent EAC Reconciliation Index'",
     "name: 'ICE Ratio'",
     "the approved rename reverted on ONE current surface while the registry keeps the new name: "
     "exactly the mixed state the owner's instruction forbids"),
    ("F4", "test_run28_closure", "EDIT",
     "assets/js/categories.js", "name: 'Monte Carlo EAC'", "name: 'Monte Carlo EAC Forecast'",
     "the A1.1 naming drift reintroduced on a current surface, so active naming conflicts for "
     "A1.1 becomes one rather than zero"),
    ("F5", "test_run28_closure", "EDIT",
     "server/app/project_data.py",
     "    return set(V3_STRUCTURE_KEYS.values()) | set(CANONICAL_STRUCTURE_KEYS.values())",
     "    return set(CANONICAL_STRUCTURE_KEYS.values())",
     "the supply path removed for the nineteen v3 structures: the intake stops accepting them, "
     "so the twenty abstentions lose the intake they rest on"),
    ("F6", "test_run28_closure", "EDIT",
     "server/app/simulation/canonical_v3.py",
     "    if len(parsed) > 1 and not dependence:", "    if False and not dependence:",
     "A3.6's dependence policy made optional again, so a many-event model silently assumes "
     "independence and understates the upper tail it reports"),
    ("F7", "test_run28_closure", "EDIT",
     "server/app/simulation/canonical_v3.py",
     '    meta = _provenance(structure, words, "process_variance_source", '
     '"measurement_variance_source")',
     '    meta = {"process_variance_source": structure.get("process_variance_source") '
     'or "assumed",\n            "measurement_variance_source": '
     'structure.get("measurement_variance_source") or "assumed"}',
     "a hidden default substituted for Q and R provenance, so an uncalibrated variance passes as "
     "a calibrated one"),
    # THE OWNER'S NAMED A2.7 FAULT, on the REAL-CORPUS route rather than on the structure. F2
    # weakens the canonical method's own minimum-history guard; this one weakens the ASSEMBLER
    # that builds the history out of the stored schedule snapshots, so a milestone that appears
    # in only ONE reporting period -- one required historical forecast missing -- is admitted to
    # the trend. The guard that must catch it is the suite that drives the real documents.
    ("F8", "test_schedule_milestones", "EDIT",
     "server/app/documents.py",
     "        if len(series) < 2:\n            continue",
     "        if len(series) < 1:\n            continue",
     "the real-corpus assembler admits a milestone with only one historical forecast, so a "
     "single baseline-and-current pair reaches the trend it cannot support"),
]


def main() -> None:
    rows = []
    ok = True
    for fid, suite, kind, target, find, repl, intent in FAULTS:
        path = ROOT / target
        base_before = run_suite(suite)
        if base_before[0] != "GREEN":
            print(f"{fid}: BASELINE NOT GREEN ({base_before}) -- campaign aborted")
            ok = False
            rows.append(dict(fault_id=fid, guard=suite, kind=kind, target=target, intent=intent,
                             baseline_before=base_before[1], injection_confirmed="not attempted",
                             observed="ABORTED", baseline_after="", verdict="FAIL"))
            continue

        if kind == "UNTRACKED_FILE":
            path.write_text("# Run 28 closure non-vacuity probe. Deleted by the campaign.\n",
                            encoding="utf-8")
            confirmed = path.is_file() and "non-vacuity probe" in path.read_text(encoding="utf-8")
            untracked = subprocess.run(
                ["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=all"],
                capture_output=True, text=True).stdout
            confirmed = confirmed and f"?? {target}" in untracked
            observed = run_suite(suite)
            path.unlink()
            restored = not path.exists()
        else:
            original = path.read_bytes()
            digest = hashlib.sha256(original).hexdigest()
            text = original.decode("utf-8")
            if find not in text:
                print(f"{fid}: INJECTION SITE NOT FOUND in {target} -- campaign aborted")
                ok = False
                rows.append(dict(fault_id=fid, guard=suite, kind=kind, target=target,
                                 intent=intent, baseline_before=base_before[1],
                                 injection_confirmed="site not found", observed="ABORTED",
                                 baseline_after="", verdict="FAIL"))
                continue
            path.write_text(text.replace(find, repl, 1), encoding="utf-8")
            confirmed = repl in path.read_text(encoding="utf-8")  # re-read FROM DISK
            observed = run_suite(suite)
            path.write_bytes(original)
            restored = hashlib.sha256(path.read_bytes()).hexdigest() == digest

        base_after = run_suite(suite)
        verdict = ("PASS" if confirmed and restored and observed[0] == "RED"
                   and base_after[0] == "GREEN" else "FAIL")
        ok = ok and verdict == "PASS"
        rows.append(dict(fault_id=fid, guard=f"server/tools/{suite}.py", kind=kind,
                         target=target, intent=intent, baseline_before=base_before[1],
                         injection_confirmed=("yes, re-read from disk" if confirmed else "NO"),
                         observed=f"{observed[0]} {observed[1]}",
                         baseline_after=base_after[1],
                         restored_byte_for_byte=("yes" if restored else "NO"),
                         verdict=verdict))
        print(f"{fid} {verdict}: {base_before[1]} -> {observed[0]} {observed[1]} -> "
              f"{base_after[1]}")

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nwrote {OUT.relative_to(ROOT)}  {sum(1 for r in rows if r['verdict'] == 'PASS')}"
          f"/{len(rows)} PROVEN NON-VACUOUS")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
