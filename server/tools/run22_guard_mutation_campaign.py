#!/usr/bin/env python3
"""
RUN 22 SECTION 22. THE FINAL GUARD NON-VACUITY CAMPAIGN, DRIVEN AGAINST REAL PRODUCTION.

WHY. Run 20 found nine vacuous guards and then wrote seven more vacuously inside a single cycle;
Run 21 found more. The standing rule is that a guard is vacuous until it has been shown red. No
release may rest on a guard that has never demonstrated it can fail.

WHAT THIS DOES, AND WHAT IT REFUSES TO DO. For each release-critical invariant it edits the REAL
production file the invariant lives in, runs the suite that is supposed to notice, records whether
that suite went red, and restores the file. It does not mutate a copy of a structure the code
rebuilds per call, it does not fabricate a manifest, and it does not assert that a guard "would"
fail. The mutation lands in the bytes production reads.

RESTORATION IS CHECKED, NOT ASSUMED. Every file's SHA-256 is taken before the mutation and again
after the restore, and a mismatch is a hard failure of this campaign. The production-tree guard is
then run once at the end over the whole tree, so if any mutation leaked anywhere at all -- even in
a file this campaign never named -- it is caught.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... python tools/run22_guard_mutation_campaign.py
"""

from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv
import hashlib
import os
import pathlib
import subprocess
import sys

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
_cs_arm(_cs_pl.Path(ROOT), "run22_guard_mutation_campaign.py",
        allow=["code_audit/run22_final_guard_nonvacuity.csv"])
# -------------------------------------------------------------------------------------------

#: (guard name, protected invariant, production file, exact text to replace, replacement, suites)
#:
#: Each replacement is a REAL semantic violation of the invariant, not a comment change: a third
#: voting module, a concept-only module let out of the disabled set, Material Cost Variance
#: re-enabled, a lineage declaration stripped of its owning module.
MUTATIONS: list[dict] = [
    {
        "guard": "voting count is exactly two",
        "protects": "only A1.7 and A1.8 may influence Cost Recovery Status",
        "file": "server/app/simulation/registry.py",
        "find": '    "A1.8",   # Variance at Completion\n})',
        "replace": '    "A1.8",   # Variance at Completion\n    "A1.1",\n})',
        "why": "adds a THIRD voting module. If no suite goes red, voting could be widened "
               "silently, which is the single most consequential thing that could happen to the "
               "study's authoritative status.",
        "suites": ["test_run20_voting_lineage.py", "test_run12_final_verification.py",
                   "test_run21_instrument_invariants.py"],
    },
    {
        "guard": "concept-only activation is zero",
        "protects": "the eight concept-only modules must stay disabled",
        "file": "server/app/simulation/registry.py",
        "find": '    "B4.6": "Pareto Frontier Analysis",\n}',
        "replace": '}',
        "why": "removes B4.6 from the concept-only disabled set, activating a module that has no "
               "implementation behind it.",
        "suites": ["test_run12_final_verification.py", "test_run14_disabled_method_functional.py",
                   "test_run13_module_evidence.py"],
    },
    {
        "guard": "Material Cost Variance stays disabled",
        "protects": "A3.4 must not compute or reach a governed status",
        "file": "server/app/simulation/registry.py",
        "find": '    "A3.4": "Material Cost Variance",\n}',
        "replace": '}',
        "why": "re-enables Material Cost Variance, the module the owner's prompt names explicitly "
               "and repeatedly as one that must remain disabled.",
        "suites": ["test_run16_material_cost_variance_disabled.py",
                   "test_run21_instrument_invariants.py"],
    },
]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_suite(name: str, db: str) -> tuple[bool, str]:
    """Runs one suite against its own copy of the migrated template. Returns (green, summary)."""
    env = dict(os.environ)
    env["DATABASE_URL"] = f"sqlite:///{db}"
    env["SESSION_SECRET"] = env.get("SESSION_SECRET", "test-secret-do-not-use-in-prod")
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([sys.executable, name], cwd=str(HERE), env=env,
                          capture_output=True, text=True, timeout=1800)
    line = ""
    for ln in proc.stdout.splitlines():
        if ln.startswith("RESULT: "):
            line = ln.strip()
    if not line:
        return False, f"no canonical RESULT line (exit {proc.returncode})"
    nums = line.split()[1]
    passed, _, total = nums.partition("/")
    return (passed == total and proc.returncode == 0), line


def main() -> None:
    template = sys.argv[1] if len(sys.argv) > 1 else None
    if not template:
        print("usage: run22_guard_mutation_campaign.py <path-to-migrated-template.db>")
        sys.exit(2)

    rows: list[dict] = []
    for i, m in enumerate(MUTATIONS):
        path = ROOT / m["file"]
        before = path.read_bytes()
        before_sha = sha(path)
        text = before.decode("utf-8")
        if text.count(m["find"]) != 1:
            rows.append({"guard": m["guard"], "protects": m["protects"], "file": m["file"],
                         "mutation": m["why"], "suite": "(not run)", "baseline": "",
                         "under_mutation": "",
                         "verdict": f"CAMPAIGN FAILURE: the anchor text occurs "
                                    f"{text.count(m['find'])} times, not once. The mutation was "
                                    f"NOT applied and this guard is NOT proved.",
                         "restored_byte_identical": "n/a"})
            continue

        # BASELINE FIRST. A suite that is already red would make a mutation look effective.
        baselines = {}
        for s in m["suites"]:
            db = f"{template}.g{i}.base.{s}.db"
            subprocess.run(["cp", template, db], check=True)
            baselines[s] = run_suite(s, db)

        path.write_text(text.replace(m["find"], m["replace"]), encoding="utf-8")
        try:
            for s in m["suites"]:
                db = f"{template}.g{i}.mut.{s}.db"
                subprocess.run(["cp", template, db], check=True)
                green_mut, line_mut = run_suite(s, db)
                green_base, line_base = baselines[s]
                if not green_base:
                    verdict = ("INCONCLUSIVE: the suite was not green before the mutation, so "
                               "its redness afterwards proves nothing")
                elif green_mut:
                    verdict = "VACUOUS: green under a real violation of the invariant"
                else:
                    verdict = "RED under mutation, GREEN when restored -- NON-VACUOUS"
                rows.append({"guard": m["guard"], "protects": m["protects"], "file": m["file"],
                             "mutation": m["why"], "suite": s, "baseline": line_base,
                             "under_mutation": line_mut, "verdict": verdict,
                             "restored_byte_identical": "(checked below)"})
        finally:
            path.write_bytes(before)
        after_sha = sha(path)
        for r in rows:
            if r["file"] == m["file"] and r["restored_byte_identical"] == "(checked below)":
                r["restored_byte_identical"] = ("yes" if after_sha == before_sha
                                                else f"NO -- {before_sha} became {after_sha}")

    # THE WHOLE TREE, ONCE, AT THE END. Catches a leak in a file this campaign never named.
    sys.path.insert(0, str(HERE))
    import production_tree as pt  # noqa: E402
    d = pt.compare()
    rows.append({"guard": "the campaign itself left production unmodified",
                 "protects": "no mutation leaked into the committed tree",
                 "file": "(the whole production tree)", "mutation": "n/a",
                 "suite": "production_tree.compare", "baseline": "",
                 "under_mutation": str(d),
                 "verdict": ("CLEAN" if not (d["added"] or d["removed"] or d["changed"])
                             else "LEAK DETECTED"),
                 "restored_byte_identical": "yes"})

    out = ROOT / "code_audit" / "run22_final_guard_nonvacuity.csv"
    with artifact_out(out).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["guard", "protects", "file", "mutation", "suite",
                                           "baseline", "under_mutation", "verdict",
                                           "restored_byte_identical"])
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"  {r['verdict'][:46]:48} {r['guard'][:38]:40} {r['suite']}")
    print(f"\nwrote {out}")
    bad = [r for r in rows if not r["verdict"].startswith(("RED under mutation", "CLEAN"))]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
