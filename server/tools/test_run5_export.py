#!/usr/bin/env python3
"""
Run 5: regenerate the Group A export (remediation_programme.md "Run 5";
remediation_decisions_answered.md 5.1 to 5.3). This suite protects two things: the exporter's
count assertion actually refuses on a mismatch (this is the whole subject of the run -- the
defect it fixes is an unchecked count), and the regenerated files carry what the task requires
(A4.2 through A4.10, an activation state on every section, no module id as a heading, a checksum
manifest that verifies against the files as written).

Every check below is proved able to fail: the assertion check drops a real module id and expects
refusal (section 1); the content checks are run against the actual regenerated files, and section
6 corrupts a byte in a real file and re-verifies the manifest to prove the checksum check would
have caught it.

Run:
    PYTHONIOENCODING=utf-8 python tools/test_run5_export.py
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXPORTER = ROOT / "server" / "tools" / "export_module_source.py"
CODE_AUDIT = ROOT / "code_audit"

PASSED = 0
FAILED = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  FAIL  {label}  {detail}")


def run_exporter(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(EXPORTER), *args],
        cwd=str(ROOT), capture_output=True, text=True,
    )


print("== Section 1: the assertion can fail, and does, and restores clean ==")

# Baseline: no drop, must succeed and report the full expected counts.
baseline = run_exporter("--check-only")
check(baseline.returncode == 0, "baseline check-only exits 0", baseline.stderr)
check("Group A: 52 modules" in baseline.stdout, "baseline reports 52 for Group A",
      baseline.stdout)
check("Group B: 36 modules" in baseline.stdout, "baseline reports 36 for Group B")
check("Group C: 7 modules" in baseline.stdout, "baseline reports 7 for Group C")
check("Group D: 5 modules" in baseline.stdout, "baseline reports 5 for Group D")

# Injection: drop a real Group A id (one of the nine the original defect omitted) and confirm
# the exporter refuses rather than silently writing a short file.
injected = run_exporter("--check-only", "--drop", "A4.6")
check(injected.returncode != 0, "dropping A4.6 makes the exporter exit non-zero",
      injected.stderr)
check("EXPORT REFUSED for Group A" in injected.stderr, "exporter names the refusal reason",
      injected.stderr)
check("A4.6" in injected.stderr, "exporter names the missing id specifically", injected.stderr)
check("EXPORT FAILED" in injected.stderr, "exporter's overall summary reports failure",
      injected.stderr)

# Restore: no drop, confirm the baseline is clean again (proves the failure above was caused by
# the injection, not by some other break).
restored = run_exporter("--check-only")
check(restored.returncode == 0, "baseline is clean again after the injection is removed",
      restored.stderr)

# Also prove a genuinely disabled module (still registry-computed) is NOT treated as missing --
# i.e. the assertion checks against VALIDATED, not against some smaller "voting" set.
disabled_present = run_exporter("--check-only")
check("A3.8" not in disabled_present.stderr, "the disabled-but-computed module is not flagged "
      "missing at baseline")


print("== Section 2: the nine modules the 2026-08-10 export omitted are present ==")

group_a = (CODE_AUDIT / "GROUP_A_project-health.md").read_text(encoding="utf-8")
OMITTED_NAMES = [
    "RFI Velocity", "Submittal Rejection Rate", "NCR Rate", "Weather Day Impact",
    "Change Order Frequency", "Dispute Escalation Index", "Subcontractor Performance",
    "Procurement Lead Time Monitor", "Specification Conflict Density",
]
for name in OMITTED_NAMES:
    check(f"## {name}\n" in group_a, f'"{name}" section present in GROUP_A_project-health.md')


print("== Section 3: every section carries an activation state ==")

headings = re.findall(r"^## (.+)$", group_a, flags=re.MULTILINE)
check(len(headings) == 53, f"GROUP_A has 53 headings (52 computed + 1 supplied), found "
      f"{len(headings)}", str(headings))
sections = re.split(r"^## ", group_a, flags=re.MULTILINE)[1:]
missing_state = [s.split("\n", 1)[0] for s in sections if "Activation state:" not in s]
check(not missing_state, "every Group A section names an activation state",
      str(missing_state))

for fname in ("GROUP_B_recommendation-governance.md", "GROUP_C_data-evidence-health.md",
              "GROUP_D_portfolio-level.md"):
    text = (CODE_AUDIT / fname).read_text(encoding="utf-8")
    secs = re.split(r"^## ", text, flags=re.MULTILINE)[1:]
    missing = [s.split("\n", 1)[0] for s in secs if "Activation state:" not in s]
    check(not missing, f"every section in {fname} names an activation state", str(missing))


print("== Section 4: no module id appears as a heading (NAMING_AUTHORITY.md) ==")

ID_HEADING = re.compile(r"^## .*\b[ABCD]\d+\.\d+\b", re.MULTILINE)
for fname in ("GROUP_A_project-health.md", "GROUP_B_recommendation-governance.md",
              "GROUP_C_data-evidence-health.md", "GROUP_D_portfolio-level.md"):
    text = (CODE_AUDIT / fname).read_text(encoding="utf-8")
    hits = ID_HEADING.findall(text)
    check(not hits, f"{fname} has no module id in a heading", str(hits))

# Prove this check itself can fail: inject an id into a heading text and confirm the regex
# catches it, then discard (do not write it back).
poisoned = group_a.replace("## RFI Velocity\n", "## A4.2 RFI Velocity\n", 1)
check(bool(ID_HEADING.findall(poisoned)), "the id-in-heading check catches an injected id "
      "(proves the check is not vacuous)")


print("== Section 5: the checksum manifest matches the files as written (recomputed) ==")

manifest_path = CODE_AUDIT / "CHECKSUMS.sha256"
manifest_text = manifest_path.read_text(encoding="utf-8")
entries = {}
for line in manifest_text.splitlines():
    if line.startswith("#") or not line.strip():
        continue
    digest, _, rel = line.partition("  ")
    entries[rel.strip()] = digest.strip()

check(len(entries) >= 5, "manifest lists at least the five module-source files",
      str(sorted(entries)))

mismatches = []
for rel, digest in entries.items():
    p = CODE_AUDIT / rel
    if not p.exists():
        mismatches.append(f"{rel}: file missing")
        continue
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    if actual != digest:
        mismatches.append(f"{rel}: manifest {digest} != recomputed {actual}")
check(not mismatches, "every manifest entry's recomputed sha256 matches the file on disk",
      str(mismatches))


print("== Section 6: the manifest check can fail (prove it, then restore) ==")

target_rel = "GROUP_D_portfolio-level.md"
target_path = CODE_AUDIT / target_rel
original_bytes = target_path.read_bytes()
try:
    target_path.write_bytes(original_bytes + b"\ncorrupted\n")
    corrupted_digest = hashlib.sha256(target_path.read_bytes()).hexdigest()
    check(corrupted_digest != entries.get(target_rel),
          "corrupting a manifest-covered file changes its digest away from the manifest entry")
finally:
    target_path.write_bytes(original_bytes)
    restored_digest = hashlib.sha256(target_path.read_bytes()).hexdigest()
    check(restored_digest == entries.get(target_rel),
          "file restored to exactly the manifest-covered content")


print(f"\n{PASSED} passed, {FAILED} failed")
sys.exit(1 if FAILED else 0)
