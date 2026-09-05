#!/usr/bin/env python3
"""
RUN 26. THE BROWSER-LEVEL NON-VACUITY PROOFS.

The three faults Addition D names that can only be proved in a rendered page: the architecture
edge comparison, the empty-project colour rule, and the derived-category estimability rule.
Each fault is injected into a SANDBOX COPY of the tree, the mutation is CONFIRMED TO HAVE
LANDED IN THE RENDERED DOM (not merely in the source file), the named browser guard is run
against the mutated tree and required to go RED for the intended reason, then restored and
required GREEN.

CONFIRMING THE MUTATION IN THE BROWSER is the point. The programme has already had a mutation
that silently failed to apply read as evidence, so a source-level diff is not enough here:
each fault below is read back off the rendered element before its guard's verdict is believed.

Run:
    PYTHONIOENCODING=utf-8 python tools/drive_run26_faults.py
"""
from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

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
_cs_arm(_cs_pl.Path(ROOT), "drive_run26_faults.py",
        allow=["code_audit/run26_browser_fault_injection.csv"])
# -------------------------------------------------------------------------------------------
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


def sandbox() -> pathlib.Path:
    d = pathlib.Path(tempfile.mkdtemp(prefix="run26f-"))
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


def drive(tree: pathlib.Path, label: str, port: int) -> tuple[str, str]:
    """Run the Run-26 browser driver inside `tree`. Returns (verdict, output)."""
    db = tempfile.mkdtemp()
    env = dict(os.environ)
    env.update({"DATABASE_URL": f"sqlite:///{db}/t.db", "SESSION_SECRET": "campaign",
                "PYTHONIOENCODING": "utf-8", "RUN26_LABEL": label, "RUN26_PORT": str(port)})
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                   cwd=tree / "server", env=env, capture_output=True)
    p = subprocess.run([sys.executable, "drive_run26_counts_wiring_empty.py"],
                       cwd=tree / "server" / "tools", env=env,
                       capture_output=True, text=True, timeout=1800)
    out = p.stdout + p.stderr
    m = RESULT_RE.search(out)
    if not m:
        return "CRASHED", out
    return ("GREEN" if m.group(1) == m.group(2) else "RED"), out


#: (id, file, find, replace, the DOM fact that proves the mutation landed, the property the
#: red must name)
FAULTS = [
    ("NV-A remove one authoritative edge",
     "assets/js/neural_flow.js",
     "    var modCatEls = MODULES.map(function(m, mi) {\n      var ci=m.catI,",
     "    var modCatEls = MODULES.map(function(m, mi) {\n"
     "      if (mi === 0) return null;\n      var ci=m.catI,",
     "missing_edge_count", "every established architectural edge is rendered"),

    ("NV-B add a fabricated edge",
     "assets/js/neural_flow.js",
     "    var interCatEls = [];\n    var qualI = catIndexOf(QUALIFIER_CAT);",
     "    var interCatEls = [];\n"
     "    se('path', { d:'M0,0 L10,10', fill:'none', stroke:COL.None,\n"
     "      'data-edge-type':'CATEGORY -> CATEGORY', 'data-edge-src':'Cost Risk',\n"
     "      'data-edge-dst':'Signal Synthesis' }, interG);\n"
     "    var qualI = catIndexOf(QUALIFIER_CAT);",
     "fabricated_edge_count", "absent from the inventory"),

    ("NV-C reverse a valid edge",
     "assets/js/neural_flow.js",
     "          'data-edge-type':'CATEGORY -> CATEGORY', 'data-edge-src':CATS[qualI].name,\n"
     "          'data-edge-dst':CATS[dst].name",
     "          'data-edge-type':'CATEGORY -> CATEGORY', 'data-edge-src':CATS[dst].name,\n"
     "          'data-edge-dst':CATS[qualI].name",
     "wrong_direction_edge_count", "against the architecture"),

    ("NV-D a non-grey colour on an empty project",
     "assets/js/neural_flow.js",
     "      if (!projectIsEmpty) return color;\n      // An empty project has one vocabulary: "
     "no current result.\n      return COL.None;",
     "      if (!projectIsEmpty) return color;\n      return COL.Amber;",
     "non_grey_node_count", "analytical colour"),

    ("NV-E a derived category forced to a status colour with no upstream evidence",
     "assets/js/neural_flow.js",
     "      var cAttrs = { fill:neutralOnEmpty(color, cs),",
     "      var cAttrs = { fill:(DERIVED_CATS.indexOf(cat.taxId) >= 0 ? COL.Green "
     ": neutralOnEmpty(color, cs)),",
     "derived_categories_with_status_colour", "derived category renders a computed-status"),
]


def main() -> None:
    print("=" * 78)
    print("RUN 26 BROWSER-LEVEL NON-VACUITY PROOFS")
    print("=" * 78)

    port = 8300
    base = sandbox()
    verdict, out = drive(base, "nv-baseline", port)
    check(verdict == "GREEN", "BASELINE: the Run-26 browser guard is green before any fault",
          verdict)
    ROWS.append(["baseline", "-", "n/a", verdict, "GREEN",
                 "yes" if verdict == "GREEN" else "no"])
    shutil.rmtree(base.parent, ignore_errors=True)

    for fid, rel, find, repl, dom_fact, prop in FAULTS:
        print()
        print("-" * 78)
        print(fid)
        port += 1
        tree = sandbox()
        target = tree / rel
        original = target.read_text(encoding="utf-8")
        check(find in original, f"{fid}: the text the fault replaces is present", rel)
        if find not in original:
            ROWS.append([fid, rel, dom_fact, "NOT APPLIED", "-", "no"])
            shutil.rmtree(tree.parent, ignore_errors=True)
            continue
        # RUN 55, PHASE B. THE RESTORE IS IN A `finally`. It was a bare statement at the end of
        # the loop body, so any raise between the mutation and it -- a driver timeout, a regex
        # failure, a kill -- left the mutated bytes on disk. Run 53 established that a fault left
        # on disk is then SNAPSHOTTED by the next campaign and cemented by its own correct
        # restore, which is how three guards stayed neutered for five runs. The `finally` is
        # hygiene rather than the fix (the fix is the arm()/require_clean_tree guard above), but
        # a known-incomplete repair is not left half-done.
        try:
            target.write_text(original.replace(find, repl, 1), encoding="utf-8")
            back = target.read_text(encoding="utf-8")
            check(back != original and repl.split("\n")[0] in back,
                  f"{fid}: the mutation is present in the bytes on disk")

            verdict, out = drive(tree, "nv-" + fid.split()[0], port)

            # THE MUTATION MUST BE VISIBLE IN THE RENDERED DOM, not only in the file. The driver
            # prints the measured DOM fact for every fault; a fault that did not change what the
            # browser drew cannot be evidence about a guard.
            m = re.search(rf"{re.escape(dom_fact)} = (.+)", out)
            measured = m.group(1).strip() if m else "(not measured)"
            landed_in_dom = bool(m) and measured not in ("0", "[]")
            check(landed_in_dom,
                  f"{fid}: and the rendered DOM changed, measured as {dom_fact} = {measured}",
                  measured)

            named = prop.lower() in out.lower()
            check(verdict == "RED", f"{fid}: the browser guard goes RED, and does not crash",
                  verdict)
            check(verdict == "RED" and named,
                  f"{fid}: and the failure names the intended property ({prop!r})",
                  "not named" if verdict == "RED" else verdict)
        finally:
            target.write_text(original, encoding="utf-8")
        port += 1
        try:
            restored, _ = drive(tree, "nv-restore", port)
            check(restored == "GREEN", f"{fid}: restoring returns the guard to green", restored)
            ROWS.append([fid, rel, f"{dom_fact}={measured}", verdict, restored,
                         "yes" if (verdict == "RED" and named and landed_in_dom
                                   and restored == "GREEN") else "no"])
        finally:
            shutil.rmtree(tree.parent, ignore_errors=True)

    out_path = ROOT / "code_audit" / "run26_browser_fault_injection.csv"
    with artifact_out(out_path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["fault", "file_mutated", "rendered_dom_fact_under_fault",
                    "verdict_under_fault", "verdict_after_restore", "non_vacuity_proved"])
        w.writerows(ROWS)
    print(f"\nwrote {out_path}")
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
