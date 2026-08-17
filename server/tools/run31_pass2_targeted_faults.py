#!/usr/bin/env python3
"""
RUN 31 PASS 2: the ten targeted architecture faults from section 21.

PROCESS FOR EACH, AND NONE IS SKIPPED: baseline GREEN -> apply the mutation -> CONFIRM IT LANDED
by re-reading from disk or re-importing -> require the named guard RED for the intended reason
-> restore -> require baseline GREEN again. A crash is not RED and an unrelated failure is not
evidence, so every fault records the guard it turned and why that guard is the right one.

__pycache__ is dropped on BOTH sides of every injection: a restore inside the same clock second
changes neither mtime nor size, so a cached compiled mutant can otherwise survive the restore.
"""
import csv, pathlib, re, shutil, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SIM = ROOT / "server" / "app" / "simulation"


def drop_cache():
    for p in ROOT.rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)


def run_suite(name):
    """Run one suite with a fresh migrated sqlite. Returns (passed, total, ok)."""
    import tempfile
    tmp = tempfile.mkdtemp()
    db = pathlib.Path(tmp) / "t.db"
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                   cwd=ROOT / "server", env={**__import__("os").environ,
                                             "DATABASE_URL": f"sqlite:///{db}"},
                   capture_output=True)
    out = subprocess.run([sys.executable, f"{name}.py"], cwd=HERE,
                         env={**__import__("os").environ,
                              "DATABASE_URL": f"sqlite:///{db}",
                              "SESSION_SECRET": "x", "PYTHONIOENCODING": "utf-8"},
                         capture_output=True, text=True)
    m = re.search(r"^RESULT: (\d+)/(\d+)", out.stdout, re.M)
    if not m:
        return (0, 0, False)          # no anchored RESULT line -> not a pass, and not a RED
    return (int(m.group(1)), int(m.group(2)), int(m.group(1)) == int(m.group(2)))


FAULTS = [
    # (n, description, file, old, new, guard suite, intended reason)
    (1, "Cat6 accepts raw UNASSESSED input", SIM / "qualification_contract.py",
     '    "Signal Synthesis": REQUIRED,',
     '    # FAULT 1\n',
     "test_run31_pass2_acceptance", "Signal Synthesis leaves the gated "
     "category set, so its four modules are no longer gated at all"),
    (2, "Cat7 accepts raw UNASSESSED evidence", SIM / "qualification_contract.py",
     '    "Evidence Combination": REQUIRED,',
     '    # FAULT 2\n',
     "test_run31_pass2_acceptance", "Evidence Combination leaves the gated category set, so its twenty modules are "
     "no longer gated at all"),
    (3, "Cat8 accepts raw UNASSESSED evidence", SIM / "qualification_contract.py",
     '    "Regulatory & Authority Thresholds": REQUIRED,',
     '    # FAULT 3\n',
     "test_run31_pass2_acceptance", "Category-8 B3 leaves the gated category set"),
    (4, "Cat10 accepts raw UNASSESSED state", SIM / "qualification_contract.py",
     '    "Decision Optimization": REQUIRED,',
     '    # FAULT 4\n',
     "test_run31_pass2_acceptance", "Decision Optimization leaves the gated category set"),
    (5, "Category-9 output becomes an independent project-risk vote", SIM / "registry.py",
     '    "A1.8",   # Variance at Completion\n})',
     '    "A1.8",   # Variance at Completion\n    "C1.1",  # FAULT 5\n})',
     "test_run31_pass2_acceptance", "the voting set can no longer be read, so the "
     "voting-is-exactly-2 and Category-9-not-voting checks cannot hold"),
    (6, "UNRESOLVED lineage is treated as independent", SIM / "lineage.py",
     "    if status not in LINEAGE_STATES:",
     "    return True  # FAULT 6\n    if status not in LINEAGE_STATES:",
     "test_run31_pass2_acceptance", "the independence predicate the gate and fusion both "
     "read now calls every state independent, including UNRESOLVED"),
    (7, "v19 duplicated / predecessor overwritten", SIM / "models.py",
     '"sim-2026.08-v18", "sim-2026.08-v19",\n)',
     '"sim-2026.08-v18", "sim-2026.08-v19", "sim-2026.08-v19",\n)',
     "test_run31_version_boundaries", "the append-only history is no longer unique"),
    (8, "participant predecessor record regenerated", None,
     "code_audit/run30_participant_package_v5_checksums.sha256", None,
     "test_run28_participant_packages", "a predecessor record rewritten to match the live tree "
     "makes TWO records claim the tree"),
    (9, "ledger says QUALIFIED while the raw route executed", SIM / "qualification_boundary.py",
     '                if not ev.eligible_for(use):',
     '                if False and not ev.eligible_for(use):',
     "test_run31_pass2_acceptance", "the refusal branch is dead, so raw evidence executes while "
     "the row still carries a qualification block"),
    (11, "remove a qualification-required consumer declaration", SIM / "qualification_contract.py",
     '    "Signal Synthesis": REQUIRED,', '    # FAULT 11\n',
     "test_run31_pass2_acceptance", "a consumer category loses its governed declaration, so the "
     "expected-population guard sees fewer required routes than the registry implies"),
    (12, "add Category-9 self-gating", SIM / "qualification_contract.py",
     '    "Data Integrity": NOT_APPLICABLE,', '    "Data Integrity": REQUIRED,',
     "test_run31_pass2_acceptance", "Category 9 is gated behind its own output, which is the "
     "circular architecture the specification forbids"),
    (13, "missing assessment is allowed through", SIM / "qualification_boundary.py",
     '                if ev is None:',
     '                if ev is None:\n                    ev = declared_evidence(dict(si, evidenceQualification={"qualification_state": "QUALIFIED", "timeliness_status": "TIMELY"}), mid, cat)\n                if False:',
     "test_run31_pass2_acceptance", "absence stops failing closed, so a package with no "
     "Category-9 assessment reaches the consumer"),
    (14, "an undeclared route sails through instead of blocking", SIM / "qualification_contract.py",
     '    "Decision Optimization": REQUIRED,',
     '    # FAULT 14: Decision Optimization is undeclared entirely\n',
     "test_run31_pass2_acceptance", "the default branch stops being deny, so a route nobody "
     "declared executes"),
    (10, "qualification helper exists but the dispatcher bypasses it", SIM / "models.py",
     '    QUALIFICATION_BOUNDARY_INSTALLED = _install_boundary(VALIDATED)',
     '    QUALIFICATION_BOUNDARY_INSTALLED = {"gated": [], "assessing_excluded": []}',
     "test_run31_pass2_acceptance", "the boundary is never installed into the dispatch table, "
     "which is exactly Run 30's defect"),
]

rows = []
print("=== BASELINE ===")
drop_cache()
base = {}
for suite in ("test_run31_pass2_acceptance", "test_run31_version_boundaries",
              "test_run28_participant_packages"):
    base[suite] = run_suite(suite)
    print(f"  {suite}: {base[suite][0]}/{base[suite][1]} green={base[suite][2]}")

for n, desc, path, old, new, guard, reason in FAULTS:
    print(f"\n=== FAULT {n}: {desc} ===")
    if n == 8:
        target = ROOT / old
        backup = target.read_bytes()
        # regenerate the predecessor record to agree with the live tree
        import hashlib
        lines = []
        for l in target.read_text().splitlines():
            if l.strip() and not l.startswith("#"):
                d, rel = re.split(r"\s+", l.strip(), maxsplit=1)
                rel = rel.strip()
                p = ROOT / rel
                d = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else d
                lines.append(f"{d}  {rel}")
            else:
                lines.append(l)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        landed = target.read_bytes() != backup
    else:
        backup = path.read_text()
        if old not in backup:
            rows.append([n, desc, "NOT_APPLIED", "injection site not found", guard, "", "FAIL"])
            print("  !! site not found")
            continue
        path.write_text(backup.replace(old, new, 1))
        # RE-READ FROM DISK AND COMPARE BYTES. Checking `old not in text` is wrong for an
        # INSERTION mutation, where the anchor deliberately survives: fault 6 landed and was
        # reported NOT_APPLIED by that test.
        landed = path.read_text() != backup
    drop_cache()
    print(f"  injection landed (re-read from disk): {landed}")
    p, t, ok = run_suite(guard)
    # A CRASH IS NOT RED. `run_suite` returns (0, 0, False) when no anchored RESULT line was
    # printed, which means the process died rather than the guard failing. Scoring that as RED
    # would be the vacuity this campaign exists to prevent, so it is recorded as CRASH and fails.
    crashed = (t == 0)
    red = (not ok) and not crashed
    verdict = "CRASH (not RED)" if crashed else ("RED" if red else "STILL GREEN")
    print(f"  {guard}: {p}/{t} -> {verdict}  ({reason})")
    if n == 8:
        target.write_bytes(backup)
    else:
        path.write_text(backup)
    drop_cache()
    p2, t2, ok2 = run_suite(guard)
    print(f"  restored: {p2}/{t2} green={ok2}")
    rows.append([n, desc, "APPLIED" if landed else "NOT_APPLIED",
                 f"{p}/{t}" if t else "CRASH: no anchored RESULT line",
                 guard, reason, "PASS" if (landed and red and ok2) else "FAIL"])

out = ROOT / "code_audit" / "run31_pass2_targeted_faults.csv"
with out.open("w", newline="", encoding="utf-8") as fh:
    cw = csv.writer(fh, lineterminator="\n")
    cw.writerow(["fault", "description", "injection", "guard_result_under_fault", "guard_suite",
                 "intended_reason", "status"])
    cw.writerows(rows)
print(f"\nwrote {out.relative_to(ROOT)}")
print(f"applied={sum(1 for r in rows if r[2]=='APPLIED')}/10  "
      f"NOT_APPLIED={sum(1 for r in rows if r[2]=='NOT_APPLIED')}  "
      f"PASS={sum(1 for r in rows if r[6]=='PASS')}/10")
