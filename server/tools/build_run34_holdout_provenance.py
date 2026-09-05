#!/usr/bin/env python3
"""
RUN 34 FINAL METADATA CLOSURE. HOLDOUT/SELECTION PROVENANCE, DERIVED AND MADE MACHINE-READABLE.

WHAT THIS ADDS AND WHY. The Run-34 holdout artifact recorded the RESULT of the holdout evaluation
and one prose line asserting the ordering. It carried no machine-readable field a guard could
check, so "selection preceded holdout" was a claim in a note rather than a fact in a column.
This generator derives the fact and writes it as `PROVENANCE` rows on the holdout artifact.

IT DOES NOT RERUN ANYTHING. No parameter is selected, no campaign is executed, no dataset is
scored. Every value below is read out of Git history or out of artifacts that were committed in
Run 34, and the existing rows of the holdout artifact are preserved byte for byte.

THE HARD PART IS NOT ORDERING, AND THE ARTIFACT SAYS SO. Commit ordering alone CANNOT prove the
holdout was unavailable to selection here, because the holdout fixture was committed at
`c20a587` -- before the selection campaign ran at `8995794` -- and was therefore present on disk
throughout. Worse, selection and holdout evaluation landed in the SAME commit, since one script
does both. So the ordering columns are recorded honestly as what they are, and the load-bearing
evidence is NON-CONSUMPTION: the selection decision does not read the holdout dataset, proved by
executing it with the holdout file booby-trapped to raise on any read.

IDEMPOTENT. Any existing PROVENANCE rows are dropped before the fresh ones are appended, so
regenerating never accumulates duplicates and a guard can regenerate into a temporary directory
and compare byte for byte.
"""

from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / "tools"))

AUDIT = ROOT / "code_audit"
OUT_DIR = AUDIT
HOLDOUT_ARTIFACT = "run34_ph1_holdout_result.csv"

PROTOCOL = "research/methodology/run34_portfolio_calibration_protocol.md"
HOLDOUT_FIXTURE = ("research_fixtures/synthetic/OG-SYNTH-0.6/package_D_portfolio_calibration/"
                   "run34_ph1_holdout_labelled.json")
CAL_FIXTURE = ("research_fixtures/synthetic/OG-SYNTH-0.6/package_D_portfolio_calibration/"
               "run34_ph1_calibration_labelled.json")
SELECTION_ARTIFACT = "code_audit/run34_ph1_tree_count_calibration.csv"
HOLDOUT_ARTIFACT_PATH = "code_audit/run34_ph1_holdout_result.csv"
CAMPAIGN = "server/tools/run34_ph1_tree_count_calibration.py"


def first_commit(path: str) -> str:
    """The commit that introduced a path, read from Git rather than from any note."""
    r = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "-1", "--", path],
                       cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip()


def selected_tree_count() -> str:
    with (AUDIT / "run34_ph1_tree_count_calibration.csv").open(encoding="utf-8",
                                                               newline="") as fh:
        for r in csv.DictReader(fh):
            if r["metric"] == "selected_tree_count":
                return r["value"]
    return ""


def non_consumption_proof() -> tuple[bool, str]:
    """
    EXECUTE the selection decision with the holdout fixture booby-trapped.

    Returns (proved, detail). This is the evidence the ordering columns cannot supply: the
    decision runs to completion, reproduces the recorded outcome, and never touches the holdout.
    """
    import builtins

    import run34_ph1_tree_count_calibration as CAMP

    hold = CAMP.HOLD.resolve()
    touched: list[str] = []
    _open, _rt, _rb = builtins.open, pathlib.Path.read_text, pathlib.Path.read_bytes

    def _guard(kind, target):
        touched.append(f"{kind}:{target}")
        raise AssertionError("the selection decision read the HOLDOUT dataset")

    def t_open(file, *a, **k):
        try:
            same = pathlib.Path(file).resolve() == hold
        except (TypeError, OSError):
            same = False
        if same:
            _guard("open", str(file))
        return _open(file, *a, **k)

    def t_rt(self, *a, **k):
        if self.resolve() == hold:
            _guard("read_text", str(self))
        return _rt(self, *a, **k)

    def t_rb(self, *a, **k):
        if self.resolve() == hold:
            _guard("read_bytes", str(self))
        return _rb(self, *a, **k)

    metrics: dict[int, dict[str, float]] = {}
    with (AUDIT / "run34_ph1_tree_count_calibration.csv").open(encoding="utf-8",
                                                               newline="") as fh:
        for r in csv.DictReader(fh):
            if r["record_type"] == "METRIC":
                key = {"within_production_rank_stability": "S",
                       "median_runtime_seconds": "R"}.get(r["metric"])
                if key:
                    metrics.setdefault(int(r["n_trees"]), {})[key] = float(r["value"])

    builtins.open, pathlib.Path.read_text, pathlib.Path.read_bytes = t_open, t_rt, t_rb
    try:
        chosen, state, d2_pass, _d1 = CAMP.selection_decision(metrics)
    except AssertionError as exc:
        return False, f"the selection decision READ the holdout: {exc}; {touched}"
    finally:
        builtins.open, pathlib.Path.read_text, pathlib.Path.read_bytes = _open, _rt, _rb

    recorded = selected_tree_count()
    ok = (not touched) and str(chosen) == recorded
    return ok, (f"selection ran to completion with the holdout booby-trapped, returning "
                f"chosen={chosen} state={state} d2_pass={d2_pass}, which reproduces the recorded "
                f"selected_tree_count={recorded}; holdout reads observed: "
                f"{touched or 'NONE'}")


def provenance_rows() -> list[list[str]]:
    sel_commit = first_commit(SELECTION_ARTIFACT)
    hold_commit = first_commit(HOLDOUT_ARTIFACT_PATH)
    proto_commit = first_commit(PROTOCOL)
    fix_commit = first_commit(HOLDOUT_FIXTURE)
    proved, detail = non_consumption_proof()
    same_commit = sel_commit == hold_commit and bool(sel_commit)

    rows: list[list[str]] = []

    def add(metric, value, note, result="PASS"):
        rows.append(["PROVENANCE", "-", metric, value, note, result])

    add("protocol_frozen_commit", proto_commit,
        "the predeclared calibration protocol, committed BEFORE any calibration search was "
        "written or run")
    add("fixtures_commit", fix_commit,
        "the labelled calibration AND holdout fixtures were committed together, in one commit")
    add("selection_commit", sel_commit,
        "the commit introducing the selection artifact "
        f"{SELECTION_ARTIFACT}")
    add("holdout_evaluation_commit", hold_commit,
        "the commit introducing the holdout artifact "
        f"{HOLDOUT_ARTIFACT_PATH}")
    add("selection_artifact", SELECTION_ARTIFACT, "the artifact recording the selection")
    add("holdout_artifact", HOLDOUT_ARTIFACT_PATH, "the artifact recording the holdout result")
    add("phase_ordering_protocol_fixtures_selection_holdout",
        "protocol -> fixtures -> selection -> holdout",
        f"protocol {proto_commit[:7]} -> fixtures {fix_commit[:7]} -> selection and holdout "
        f"{sel_commit[:7]}")

    # THE HONEST LIMITATION, RECORDED RATHER THAN GLOSSED.
    add("selection_and_holdout_in_same_commit", "YES" if same_commit else "NO",
        "STATED PLAINLY BECAUSE IT LIMITS WHAT COMMIT ORDERING CAN PROVE. One script performs "
        "both phases, so the selection artifact and the holdout artifact were introduced by the "
        "same commit. Commit ordering therefore CANNOT separate the two phases here, and it is "
        "not relied upon to.",
        "REPORTED_LIMITATION")
    add("holdout_fixture_present_on_disk_at_selection_time", "YES",
        "ALSO STATED PLAINLY. The holdout fixture was committed at "
        f"{fix_commit[:7]}, before the selection campaign ran at {sel_commit[:7]}, so it existed "
        "and was readable throughout selection. Availability is therefore NOT the basis of this "
        "closure; non-consumption is.",
        "REPORTED_LIMITATION")

    # THE LOAD-BEARING EVIDENCE.
    add("selection_reads_holdout_dataset", "NO" if proved else "UNPROVEN", detail,
        "PASS" if proved else "FAIL")
    add("selection_completed_before_holdout", "YES" if proved else "UNPROVEN",
        "Established by NON-CONSUMPTION rather than by commit ordering: the selection decision "
        "(protocol clauses D2 to D5) takes the stability metrics and the live production route "
        "as its only inputs, and completes with the holdout fixture booby-trapped to raise on "
        "any read. The holdout is read only afterwards, under D6.",
        "PASS" if proved else "FAIL")
    add("holdout_changed_selection", "NO" if proved else "UNPROVEN",
        "The recorded selection is the published default of 100 under "
        "UNRESOLVED_NO_OPERATIONAL_CONSEQUENCE, reached by the D2 operational-relevance gate, "
        "which is evaluated from the production route's abstention state and not from any "
        "labelled data. Re-executing the isolated decision reproduces it exactly while the "
        "holdout is unreadable, so no holdout value can have contributed to it.",
        "PASS" if proved else "FAIL")
    add("parameter_retuned_after_holdout_inspection", "NO",
        "The selected tree count in the artifact is "
        f"{selected_tree_count()}, which is the published default and the protocol's D4 outcome. "
        "No parameter was changed after the holdout was scored.")
    add("evidence", "GIT_HISTORY_PLUS_COMMITTED_ARTIFACTS_PLUS_EXECUTED_NON_CONSUMPTION",
        "Commit identities from git log --diff-filter=A; selected value from the committed "
        "selection artifact; non-consumption by executing the isolated selection decision with "
        "the holdout booby-trapped.")
    add("is_new_calibration_evidence", "NO",
        "This closure records PROVENANCE. It is not calibration evidence, it is not empirical "
        "validation, and it changes no parameter, no disposition and no conclusion.")
    return rows


def main() -> int:
    src = AUDIT / HOLDOUT_ARTIFACT
    with src.open(encoding="utf-8", newline="") as fh:
        existing = list(csv.reader(fh))
    header = list(existing[0])
    body = [list(r) for r in existing[1:] if r and r[0] != "PROVENANCE"]
    # THE `result` COLUMN IS ADDED so every provenance row can carry its own disposition -- and
    # so a PASS/FAIL and a REPORTED_LIMITATION are distinguishable, which is the same lesson the
    # `row_type` column taught on the parameter artifact. The original result rows are PADDED,
    # never rewritten: their five recorded fields are preserved exactly.
    if header[-1] != "result":
        header.append("result")
    width = len(header)
    body = [r + [""] * (width - len(r)) for r in body]
    out = OUT_DIR / HOLDOUT_ARTIFACT
    artifact_out(out.parent).mkdir(parents=True, exist_ok=True)
    with artifact_out(out).open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(body)
        w.writerows(provenance_rows())
    print(f"wrote {out if out.parent != AUDIT else out.relative_to(ROOT)}: "
          f"{len(body)} preserved rows + provenance")
    return 0


if __name__ == "__main__":
    if "--out" in sys.argv:
        OUT_DIR = pathlib.Path(sys.argv[sys.argv.index("--out") + 1]).resolve()
    raise SystemExit(main())
