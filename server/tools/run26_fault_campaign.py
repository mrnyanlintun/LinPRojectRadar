#!/usr/bin/env python3
"""
RUN 26. THE NON-VACUITY CAMPAIGN.

Every guard this run added or rewrote is proved capable of failing, one deliberate fault at a
time. For each fault the campaign:

  1. applies it to a SANDBOX COPY of the tree, never to the real checkout;
  2. CONFIRMS THE MUTATION ACTUALLY LANDED by reading the mutated bytes back and requiring
     them to differ from the original in the expected place -- a mutation that silently failed
     to apply is one of the five ways a check has lied in this project;
  3. runs the NAMED guard against the mutated tree;
  4. requires RED, and requires the failure text to name the intended property rather than
     merely being a nonzero exit;
  5. restores, and requires GREEN again.

A CRASH IS NOT RED. A guard whose process dies without printing a canonical RESULT line is
recorded as CRASHED and counted as a failure of the campaign, not as a caught fault.

The browser-level faults -- the empty-project colour rule, the derived-category rule and the
three edge faults -- are driven separately by drive_run26_faults.py, which needs Chromium.

Run:
    PYTHONIOENCODING=utf-8 python tools/run26_fault_campaign.py
"""
from __future__ import annotations

import csv
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

RESULT_RE = re.compile(r"^RESULT: (\d+)/(\d+)( checks passed)?$", re.M)

PASSED = 0
FAILED = 0
ROWS: list[list[str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def run_guard(tree: pathlib.Path, suite: str) -> tuple[str, str]:
    """Run a suite inside `tree`. Returns (verdict, output). Verdict is GREEN/RED/CRASHED."""
    db = tempfile.mkdtemp()
    env = dict(os.environ)
    env.update({"DATABASE_URL": f"sqlite:///{db}/t.db",
                "SESSION_SECRET": "campaign", "PYTHONIOENCODING": "utf-8"})
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                   cwd=tree / "server", env=env, capture_output=True)
    p = subprocess.run([sys.executable, suite], cwd=tree / "server" / "tools",
                       env=env, capture_output=True, text=True, timeout=900)
    out = p.stdout + p.stderr
    m = RESULT_RE.search(out)
    if not m:
        return "CRASHED", out
    return ("GREEN" if m.group(1) == m.group(2) else "RED"), out


def sandbox() -> pathlib.Path:
    d = pathlib.Path(tempfile.mkdtemp(prefix="run26-"))
    tree = d / "tree"
    shutil.copytree(ROOT, tree, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", "*.pyc", ".venv", "node_modules", "*.db"))
    # THE SANDBOX NEEDS ITS GIT DIRECTORY. test_run23_signal_flow_truthfulness.py verifies that
    # a historical manifest is preserved byte-for-byte by reading it out of the object store at
    # a named commit, and a checkout with no .git makes that check fail for a reason that has
    # nothing to do with any injected fault. The campaign measured exactly that: the sandbox
    # baseline for that suite read RED while the real tree was green. A guard failing for an
    # unrelated environmental reason is not evidence about a fault, so the sandbox is made
    # faithful rather than the anomaly explained away.
    (tree / ".git").symlink_to(ROOT / ".git")
    return tree


FAULTS = [
    # (id, suite, relative file, find, replace, the property the red must name)
    ("F1 registry-project-count",
     "test_run26_counts_and_wiring.py", "p0-baseline/module_renumbering_map.csv",
     "A1.11,ICE Ratio,1.12,A,Project Health,A1,Cost & EVM Performance,",
     "A1.11,ICE Ratio,1.12,D,Portfolio Level,D1,Portfolio Health,",
     "project level"),
    ("F2 omit-one-portfolio-entry",
     "test_run26_counts_and_wiring.py", "p0-baseline/module_renumbering_map.csv",
     "D1.5,Anomaly Score,PH.5,D,Portfolio Level,D1,Portfolio Health,parked on portfolio page; "
     "requires 3+ projects",
     "RETIRED,Anomaly Score,PH.5,-,-,-,-,retired for the campaign",
     "Portfolio Health"),
    ("F3 scientific-targets-99",
     "test_run26_counts_and_wiring.py", "code_audit/run20_cycle12_100_reaudit.csv",
     "\nPH.5,D1.5,", "\nZZ.9,ZZ.9,",
     "scientific"),
    ("F4 substitute-95-into-96-display",
     "test_run24_empty_project_diagram.py", "assets/js/taxonomy.js",
     "{ id: 'a1_11', module_id: 'A1.11', name: 'ICE Ratio'",
     "{ id: 'zz_11', module_id: 'ZZ.11', name: 'ICE Ratio'",
     "96"),
    ("F5 substitute-101-into-the-computed-display",
     "test_run26_counts_and_wiring.py", "index.html",
     "The analytical server computes 100 of the 101 registered modules.",
     "The analytical server computes 101 of the 101 registered modules.",
     "computed count"),
    ("F6 emission-block-drift",
     "test_run26_counts_and_wiring.py", "assets/js/neural_flow.js",
     "'contract_value': [", "'contract_value': ['bogusKey',",
     "byte-identical"),
    ("F7 reinstate-positional-wiring",
     "test_run26_counts_and_wiring.py", "assets/js/neural_flow.js",
     "  var QUALIFIER_CAT = 'c1';",
     "  var DOC_TO_CATS = [[0,2]];\n  var QUALIFIER_CAT = 'c1';",
     "positional category-index array"),
    ("F8 resolve-an-architecture-silence-into-an-edge",
     "test_run26_counts_and_wiring.py", "code_audit/signal_flow_authoritative_edges.csv",
     "CATEGORY,(not stated),CATEGORY,Signal Synthesis,CATEGORY -> CATEGORY",
     "CATEGORY,Cost Risk,CATEGORY,Signal Synthesis,CATEGORY -> CATEGORY",
     "SILENT row names an upstream node"),
    ("F9 restore-the-purple-square-on-an-empty-project",
     "test_document_rows.py", "assets/js/neural_flow.js",
     "var notApplicable = !uploaded && !projectIsEmpty && !!DOC_NOT_APPLICABLE[key];",
     "var notApplicable = !uploaded && !!DOC_NOT_APPLICABLE[key];",
     "empty project draws no purple square"),
    ("F10 restore-the-red-governance-arc",
     "test_run23_signal_flow_truthfulness.py", "assets/js/neural_flow.js",
     "    var fbEl = null, fbLabelEl = null;",
     "    var fbEl = se('path', { d:'M0,0', fill:'none', "
     "stroke:COL.Red, 'stroke-width':'1.5', opacity:'0.30' }, interG);\n"
     "    var fbLabelEl = null;",
     "pre-correction illumination rule"),
    ("F11 material-cost-variance-deleted-to-make-numbers-match",
     "test_run26_counts_and_wiring.py", "p0-baseline/module_renumbering_map.csv",
     "A3.4,Material Cost Variance,", "RETIRED,Material Cost Variance,",
     "Material Cost Variance"),
]


def main() -> None:
    print("=" * 78)
    print("RUN 26 NON-VACUITY CAMPAIGN")
    print("=" * 78)

    # BASELINE FIRST, on the real tree, so a red below is attributable to the fault.
    baseline_suites = sorted({f[1] for f in FAULTS})
    base_tree = sandbox()
    for suite in baseline_suites:
        verdict, _ = run_guard(base_tree, suite)
        check(verdict == "GREEN", f"BASELINE {suite} is green before any fault", verdict)
        ROWS.append(["baseline", suite, "-", "n/a", verdict, "GREEN", "yes"])
    shutil.rmtree(base_tree.parent, ignore_errors=True)

    for fid, suite, rel, find, repl, prop in FAULTS:
        print()
        print("-" * 78)
        print(f"{fid}   {rel}   guard: {suite}")
        tree = sandbox()
        target = tree / rel
        original = target.read_text(encoding="utf-8", errors="surrogateescape")

        applied = find in original
        check(applied, f"{fid}: the text the fault replaces is present in the unmutated file",
              rel)
        if not applied:
            ROWS.append([fid, suite, rel, "NOT APPLIED", "-", "-", "no"])
            shutil.rmtree(tree.parent, ignore_errors=True)
            continue

        mutated = original.replace(find, repl, 1)
        target.write_text(mutated, encoding="utf-8", errors="surrogateescape")

        # CONFIRM THE MUTATION LANDED, by reading the bytes back off disk.
        back = target.read_text(encoding="utf-8", errors="surrogateescape")
        landed = back != original and repl in back
        check(landed, f"{fid}: the mutation is present in the bytes on disk", rel)
        if not landed:
            ROWS.append([fid, suite, rel, "DID NOT LAND", "-", "-", "no"])
            shutil.rmtree(tree.parent, ignore_errors=True)
            continue

        verdict, out = run_guard(tree, suite)
        named = prop.lower() in out.lower()
        check(verdict == "RED", f"{fid}: {suite} goes RED, and does not crash", verdict)
        check(verdict == "RED" and named,
              f"{fid}: and the failure names the intended property ({prop!r})",
              "not named" if verdict == "RED" else verdict)

        # RESTORE and require green again.
        target.write_text(original, encoding="utf-8", errors="surrogateescape")
        restored, _ = run_guard(tree, suite)
        check(restored == "GREEN", f"{fid}: restoring the file returns the guard to green",
              restored)
        ROWS.append([fid, suite, rel, prop, verdict, restored,
                     "yes" if (verdict == "RED" and named and restored == "GREEN") else "no"])
        shutil.rmtree(tree.parent, ignore_errors=True)

    out = ROOT / "code_audit" / "run26_fault_injection_results.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["fault", "guard", "file_mutated", "property_the_red_must_name",
                    "verdict_under_fault", "verdict_after_restore", "non_vacuity_proved"])
        w.writerows(ROWS)
    print(f"\nwrote {out}")
    print(f"\nRESULT: {PASSED}/{PASSED + FAILED} checks passed")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        print("\nRESULT: 0/1 checks passed")
        sys.exit(1)
    sys.exit(0 if FAILED == 0 else 1)
