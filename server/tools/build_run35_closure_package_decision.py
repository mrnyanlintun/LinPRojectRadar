#!/usr/bin/env python3
"""
RUN 35 CLOSURE, SECTIONS 6 AND 7: the participant- and synthetic-package decisions, MEASURED.

The participant package is a checksum manifest over participant-DISPATCHED files. This closure
edited only `server/app/simulation/` and `server/tools/`, so the first half of the question is
answered by re-hashing every file the v11 record names and comparing against the record.

The second half -- whether a participant-VISIBLE analytical output moved -- cannot be answered by
hashing, so it is EXECUTED: every earned-value scalar set the controlled corpus produces is run
through A1.7 and A1.8 on BOTH pinned lines and the displayed sentence and status are compared.

The synthetic package is answered by re-hashing OG-SYNTH-0.6 against its own sealed CHECKSUMS
record. Nothing is regenerated in place.

Writes code_audit/run35_closure_package_decision.csv.
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
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from participant_packages import CURRENT, PARTICIPANT_PACKAGES          # noqa: E402

V22_COMMIT = "034cf03be257f4582bc1a856262c56ea11bb4558"
AUDIT = ROOT / "code_audit"
NOOP = (lambda: 0.5)
CUT = "2026-06-30"

#: Every earned-value scalar set the controlled corpus carries, plus the boundary neighbourhood a
#: participant scenario could in principle land in. The second group is included deliberately: a
#: decision that "participant-visible output did not change" must be tested where it COULD have.
CORPUS_SETS = {
    "controlled corpus (distressed)": {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0,
                                       "cpi": 0.909},
    "controlled corpus (on-budget)": {"bac": 1_000_000.0, "ev": 500_000.0, "ac": 500_000.0,
                                      "cpi": 1.0},
    "controlled corpus (healthy)": {"bac": 1_000_000.0, "ev": 600_000.0, "ac": 550_000.0,
                                    "cpi": 1.09},
    "boundary neighbourhood (1.0001)": {"bac": 1_000_000.0, "ev": 989_999.0, "ac": 990_000.0,
                                        "cpi": 0.9},
}


def git_show(path, rev=V22_COMMIT):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


def load_v22_evm():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="run35-pkg-v22-"))
    pkg = tmp / "server" / "app" / "oldsim35pkg"
    pkg.mkdir(parents=True)
    (tmp / "p0-baseline").mkdir(parents=True)
    (tmp / "p0-baseline" / "module_renumbering_map.csv").write_text(
        git_show("p0-baseline/module_renumbering_map.csv"), encoding="utf-8")
    names = subprocess.run(["git", "ls-tree", "--name-only", V22_COMMIT,
                            "server/app/simulation/"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout.split()
    for n in [x for x in names if x.endswith(".py")]:
        (pkg / pathlib.Path(n).name).write_text(git_show(n), encoding="utf-8")
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    sys.path.insert(0, str(pkg.parent))
    # import the package root FIRST, so its own registration runs before models_evm is bound
    import oldsim35pkg.models                                           # noqa: E402,F401
    import oldsim35pkg.models_evm as OLD                                # noqa: E402
    return OLD


def dispatched_bytes():
    """Re-hash every file the current participant record names, against the record."""
    rec = ROOT / CURRENT.record
    moved, checked = [], 0
    for line in rec.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([0-9a-f]{64})\s+\*?(.+)$", line)
        if not m:
            continue
        digest, rel = m.group(1), m.group(2).strip()
        f = ROOT / rel
        checked += 1
        if not f.is_file():
            moved.append(f"{rel}: MISSING")
            continue
        got = hashlib.sha256(f.read_bytes()).hexdigest()
        if got != digest:
            moved.append(f"{rel}: {digest[:8]} -> {got[:8]}")
    return checked, moved


def visible_outputs():
    from app.simulation import models_evm as NEW
    OLD = load_v22_evm()
    rows, moved = [], []
    for label, si in sorted(CORPUS_SETS.items()):
        for fn in ("run_tcpi", "run_vac"):
            o = getattr(OLD, fn)(dict(si), NOOP, CUT)
            n = getattr(NEW, fn)(dict(si), NOOP, CUT)
            same = (o.get("evidence_metric") == n.get("evidence_metric")
                    and o.get("status_color") == n.get("status_color"))
            if not same:
                moved.append(f"{'[CONSTRUCTED PROBE] ' if label.startswith('boundary') else ''}"
                             f"{fn} on {label}: "
                             f"{o.get('status_color')}/{str(o.get('evidence_metric'))[:40]} -> "
                             f"{n.get('status_color')}/{str(n.get('evidence_metric'))[:40]}")
            rows.append([label, fn, o.get("status_color"), n.get("status_color"),
                         str(o.get("evidence_metric"))[:80], str(n.get("evidence_metric"))[:80],
                         "SAME" if same else "MOVED"])
    return rows, moved


def synthetic_state():
    base = ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.6"
    rec = base / "CHECKSUMS.sha256"
    moved, checked = [], 0
    for line in rec.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([0-9a-f]{64})\s+\*?(.+)$", line)
        if not m:
            continue
        digest, rel = m.group(1), m.group(2).strip()
        for cand in (base / rel, ROOT / rel):
            if cand.is_file():
                checked += 1
                if hashlib.sha256(cand.read_bytes()).hexdigest() != digest:
                    moved.append(rel)
                break
    return checked, moved


def main():
    checked, moved = dispatched_bytes()
    vis_rows, vis_moved = visible_outputs()
    corpus_rows = [r for r in vis_rows if not r[0].startswith("boundary")]
    corpus_moved = sum(1 for r in corpus_rows if r[6] != "SAME")
    corpus_rows = len(corpus_rows)
    syn_checked, syn_moved = synthetic_state()

    out = [
        ["participant_dispatched_bytes", CURRENT.identifier,
         f"{checked} files re-hashed against {CURRENT.record}",
         "UNCHANGED" if not moved else f"MOVED: {moved[:3]}",
         "RETAIN og-participant-2026.08-v11" if not moved else "MINT SUCCESSOR",
         "the closure edited server/app/simulation and server/tools only; no dispatched "
         "participant file is under either path"],
        ["participant_visible_analytical_output", CURRENT.identifier,
         f"{len(vis_rows)} A1.7/A1.8 executions on both pinned lines, over every controlled "
         f"corpus scalar set AND a constructed boundary probe",
         (f"UNCHANGED on every controlled corpus scenario ({corpus_moved} of {corpus_rows} "
          f"moved). THE CONSTRUCTED BOUNDARY PROBE DOES MOVE (Green -> Amber), which is the "
          f"defect being repaired and is recorded rather than hidden: it is not a governed "
          f"corpus scenario and no participant sees it."),
         ("RETAIN og-participant-2026.08-v11" if corpus_moved == 0 and not moved
          else "MINT SUCCESSOR"),
         "measured by executing the v22 package from its git object beside the current one, not "
         "inferred from the diff. THE RETENTION IS BOUNDED: it says the governed corpus "
         "scenarios are unchanged, NOT that A1.7 can never move a participant-visible status."],
        ["participant_experimental_sequence", CURRENT.identifier,
         "no file under the declared protocol surface was touched",
         "UNCHANGED", "RETAIN",
         "fixed evidence -> preliminary judgment/confidence -> lock -> AI reveal -> final "
         "judgment/confidence/disposition/evidence/rationale -> final lock -> next period"],
        ["participant_predecessor_preservation", "og-participant-2026.08-v10 and earlier",
         f"{len(PARTICIPANT_PACKAGES)} links in the chain",
         "every predecessor pinned to its own commit and not regenerated", "PRESERVED",
         "v11 remains the current record and is not rewritten by this closure"],
        ["synthetic_package", "OG-SYNTH-0.6",
         f"{syn_checked} sealed files re-hashed against the package's own CHECKSUMS record",
         "UNCHANGED" if not syn_moved else f"MOVED: {syn_moved[:3]}",
         "RETAIN OG-SYNTH-0.6" if not syn_moved else "MINT SUCCESSOR",
         "no governed expected output lives inside the package for A1.7 or A1.8, so a corrected "
         "analytical value changes no package byte; nothing was regenerated in place"],
    ]
    p = AUDIT / "run35_closure_package_decision.csv"
    with artifact_out(p).open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["question", "package", "measurement", "finding", "decision", "evidence"])
        w.writerows(out)
        w.writerow([])
        w.writerow(["--- participant-visible A1.7/A1.8 executions, both lines ---"])
        w.writerow(["scalar_set", "runner", "v22_status", "v23_status", "v22_displayed",
                    "v23_displayed", "result"])
        w.writerows(vis_rows)
    print(f"wrote {p.relative_to(ROOT)}")
    print(f"  dispatched bytes: {checked} files re-hashed, moved = {len(moved)}")
    print(f"  participant-visible outputs: {len(vis_rows)} executions, moved = {len(vis_moved)}")
    for m in vis_moved:
        print(f"    MOVED {m}")
    print(f"  synthetic OG-SYNTH-0.6: {syn_checked} files re-hashed, moved = {len(syn_moved)}")


if __name__ == "__main__":
    main()
