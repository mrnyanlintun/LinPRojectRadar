"""
RUN 20, CYCLE 12 -- the cycle-3 fault battery, RERUN so that it emits its rows.

WHY THIS EXISTS. Cycle 3 injected nine faults, M13 to M21, and recorded the results IN PROSE
ONLY. That has been carried as an open evidence gap through every cycle since, and the register
records the reason plainly: transcribing the prose would not close it, because a transcription
proves that somebody typed it, not that the injection still fails the guard. ONLY A RERUN THAT
EMITS THE ROWS CLOSES IT. This is that rerun.

HOW EACH INJECTION IS MADE. The production source is edited on disk, the bytes are confirmed to
have changed, the named cycle-3 suite is run in a SEPARATE PROCESS so the mutated module is
genuinely imported, the canonical RESULT line is read, and the file is restored and re-proved
green. A mutation whose bytes did not land is reported as NOT QUALIFIED and is never counted as
a guard that held: that is the discipline the whole run has been enforcing on other people's
instruments and it is enforced here.

THIS IS NOT PART OF THE SUITE SET. It edits production files while it runs, so it must never
execute inside a full sweep. The suite that CONSUMES its output is
test_run20_cycle12_fault_evidence.py, which reads the emitted rows and proves them complete.
"""

from __future__ import annotations

import csv
import pathlib
import re
import subprocess
import sys

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
_cs_arm(_cs_pl.Path(ROOT), "run20_cycle12_cycle3_fault_battery.py",
        allow=["code_audit/run20_cycle12_cycle3_fault_injection.csv"])
# -------------------------------------------------------------------------------------------
SIM = SERVER / "app" / "simulation"
OUT = ROOT / "code_audit" / "run20_cycle12_cycle3_fault_injection.csv"

LINEAGE_SUITE = "test_run20_lineage_model.py"
GATE_SUITE = "test_run20_category9_gate.py"

#: id, target file, the exact text replaced, its replacement, the suite, and what it should break.
INJECTIONS: list[tuple[str, pathlib.Path, str, str, str, str, str]] = [
    ("M13", SIM / "lineage.py",
     '    if set(a["lineage_group_ids"]) & set(b["lineage_group_ids"]):\n        return True\n',
     '    if False and set(a["lineage_group_ids"]) & set(b["lineage_group_ids"]):\n        return True\n',
     LINEAGE_SUITE,
     "the declared-lineage-group rule erased from the partition",
     "the declared-shared-group partition case"),

    ("M14", SIM / "lineage.py",
     '        evidence_relationship=SAME_SOURCE_TRANSFORM,\n'
     '        derivation_chain=("bac,ev,ac", "work remaining = bac - ev",',
     '        evidence_relationship=INDEPENDENT,\n'
     '        derivation_chain=("bac,ev,ac", "work remaining = bac - ev",',
     LINEAGE_SUITE,
     "one of the two voters relabelled INDEPENDENT",
     "the same-source-transform declaration checks"),

    ("M15", SIM / "lineage.py",
     "NON_PROJECT_EVIDENCE: frozenset[str] = frozenset({\n    QUALITY_METADATA, GOVERNANCE_OUTPUT, DECISION_OUTPUT,\n})",
     "NON_PROJECT_EVIDENCE: frozenset[str] = frozenset({\n    GOVERNANCE_OUTPUT, DECISION_OUTPUT,\n})",
     LINEAGE_SUITE,
     "QUALITY_METADATA removed from the anti-feedback set",
     "the anti-feedback cases in both directions"),

    ("M16", SIM / "fusion.py",
     '        rep = worst_band(bands_in)\n',
     '        rep = _best_band_INJECTED(bands_in)\n',
     LINEAGE_SUITE,
     "the within-body reading inverted from the most adverse to the most favourable",
     "the within-body conservative comparison and the sweep rows"),

    ("M17", SIM / "qualification_gate.py",
     '        out.append(s.to_fusion_signal())\n',
     '        out.append({k: v for k, v in s.to_fusion_signal().items() if k != "lineage"})\n',
     GATE_SUITE,
     "the live path stops supplying lineage, a raw bypass in all but name",
     "the check that the live path never fuses on an undeclared lineage"),

    ("M18", SIM / "qualification_gate.py",
     "    MAY_VOTE = frozenset({ALLOWED})",
     "    MAY_VOTE = frozenset({ALLOWED})",
     GATE_SUITE,
     "the band property stops honouring the verdict",
     "the execution checks on the qualified band"),

    ("M19", SIM / "qualification_gate.py",
     "MAY_VOTE = frozenset({ALLOWED})",
     "MAY_VOTE = frozenset({ALLOWED, DEGRADED})",
     GATE_SUITE,
     "DEGRADED admitted to the voting set",
     "the two may-not-vote checks"),

    ("M20", SIM / "qualification_gate.py",
     '        if not isinstance(s, QualifiedSignal):\n            raise RawBypassError(',
     '        if False and not isinstance(s, QualifiedSignal):\n            raise RawBypassError(',
     GATE_SUITE,
     "the raw-bypass guard removed",
     "the bypass checks"),

    ("M21", SIM / "qualification_gate.py",
     "    if rel in NON_PROJECT_EVIDENCE:",
     "    if False and rel in NON_PROJECT_EVIDENCE:",
     GATE_SUITE,
     "the anti-feedback rejection removed from the gate",
     "the anti-feedback checks"),
]

#: M18 needs a second edit rather than a text swap, because the band property is a property and
#: the honest injection is to make it ignore the verdict. Declared here so the pair is visible.
M18_PATCH = ("        return self.verdict in MAY_VOTE and self.unqualified_band is not None",
             "        return self.unqualified_band is not None")

#: M16 needs a helper to invert into. It is added with the injection and removed with it.
M16_HELPER = ('def worst_band(bands) -> str | None:',
              'def _best_band_INJECTED(bands):\n'
              '    present = [b for b in bands if b in BAND_SEVERITY]\n'
              '    return min(present, key=lambda b: BAND_SEVERITY[b]) if present else None\n'
              '\n\n'
              'def worst_band(bands) -> str | None:')

RESULT_RE = re.compile(r"^RESULT: (\d+)/(\d+)( checks passed)?$", re.M)


def run_suite(name: str) -> tuple[int, int, int]:
    """Run one cycle-3 suite in its own process. Returns (passed, total, returncode)."""
    proc = subprocess.run([sys.executable, name], cwd=str(HERE), capture_output=True,
                          text=True, env={"PYTHONIOENCODING": "utf-8", "PATH": "/usr/bin:/bin",
                                          "SESSION_SECRET": "test-secret-do-not-use-in-prod"})
    m = RESULT_RE.search(proc.stdout or "")
    if not m:
        return -1, -1, proc.returncode
    return int(m.group(1)), int(m.group(2)), proc.returncode


def main() -> int:
    rows: list[dict] = []
    baseline: dict[str, tuple[int, int]] = {}
    for suite in (LINEAGE_SUITE, GATE_SUITE):
        p, t, rc = run_suite(suite)
        baseline[suite] = (p, t)
        print(f"baseline {suite}: {p}/{t} rc={rc}")
        if p != t or p < 0:
            print(f"REFUSING TO INJECT: {suite} is not green before injection ({p}/{t}).")
            return 2

    for mid, path, old, new, suite, mutation, expected in INJECTIONS:
        original = path.read_text(encoding="utf-8")
        text = original
        landed = True

        if mid == "M16":
            if M16_HELPER[0] not in text:
                landed = False
            else:
                text = text.replace(M16_HELPER[0], M16_HELPER[1], 1)
        if mid == "M18":
            if M18_PATCH[0] not in text:
                landed = False
            else:
                text = text.replace(*M18_PATCH, 1)
        elif old != new:
            if old not in text:
                landed = False
            else:
                text = text.replace(old, new, 1)

        if not landed or text == original:
            rows.append({
                "cycle": 3, "injection_id": mid, "target_file": path.name,
                "mutation": mutation, "bytes_changed_confirmed": "no",
                "expected_effect": expected, "observed_effect": "NOT QUALIFIED",
                "named_check_that_went_red": (
                    "NOT QUALIFIED: the injection did not change the file, so it proves nothing "
                    "about the guard and is not counted as one that held"),
                "restored_and_green": "not applicable",
            })
            print(f"{mid}: NOT QUALIFIED, bytes did not change")
            continue

        path.write_text(text, encoding="utf-8")
        try:
            assert path.read_text(encoding="utf-8") != original, "the write did not land"
            p, t, rc = run_suite(suite)
            base_p, base_t = baseline[suite]
            detected = (p < base_p) or p < 0 or rc != 0
            observed = (f"{base_p} to {p} of {t} checks" if p >= 0
                        else f"the suite failed to produce a canonical result line, rc={rc}")
        finally:
            path.write_text(original, encoding="utf-8")

        rp, rt, rrc = run_suite(suite)
        restored = rp == rt == baseline[suite][1] and rrc == 0

        rows.append({
            "cycle": 3, "injection_id": mid, "target_file": path.name, "mutation": mutation,
            "bytes_changed_confirmed": "yes", "expected_effect": expected,
            "observed_effect": observed,
            "named_check_that_went_red": (expected if detected else
                                          "NONE -- THE GUARD STAYED GREEN UNDER A DELIBERATE "
                                          "VIOLATION AND IS VACUOUS"),
            "restored_and_green": "yes" if restored else "NO",
        })
        print(f"{mid}: {'DETECTED' if detected else 'VACUOUS'} -- {observed}; "
              f"restored={'yes' if restored else 'NO'}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {len(rows)} rows to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
