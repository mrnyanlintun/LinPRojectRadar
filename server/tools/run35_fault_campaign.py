#!/usr/bin/env python3
"""
RUN 35 FAULT CAMPAIGN. Thirty failure modes, each injected into a real file, confirmed applied by
re-reading the bytes from disk, and each expected to turn ONE NAMED GUARD red for its own reason.

RULES THIS CAMPAIGN ENFORCES ON ITSELF:
 * baseline must be GREEN before anything is injected;
 * an injection that does not change the bytes on disk is NOT_APPLIED and is not counted;
 * a crash is NOT accepted as RED -- the guard must report its own failure sentence;
 * a RED in some other guard is not evidence: the named guard must be the one that fails, and its
   failure text must contain the intended-reason fragment;
 * __pycache__ is dropped on BOTH sides of every injection, because a restore inside the same
   clock second changes neither mtime nor size and a cached mutant survives;
 * every file is restored from the bytes captured before injection and re-verified byte-for-byte.

Writes code_audit/run35_fault_injection_results.csv.
"""
from __future__ import annotations

import csv
import pathlib
import shutil
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
_cs_arm(_cs_pl.Path(ROOT), "run35_fault_campaign.py",
        allow=[])
# -------------------------------------------------------------------------------------------
SERVER = ROOT / "server"
AUDIT = ROOT / "code_audit"
GUARD = HERE / "test_run35_validation_governance.py"

A = AUDIT
S = SERVER / "app" / "simulation"


def csvcell(path, key_col, key, col, old, new):
    """A mutation expressed as a cell edit in a CSV, applied by rewriting the file."""
    return ("csv", path, (key_col, key, col, old, new))


def text(path, old, new):
    return ("text", path, (old, new))


#: (fault number, description, kind, file, payload, guard name, intended-reason fragment)
FAULTS = [
    (1, "synthetic calibration labelled empirical validation",
     csvcell(A / "run35_empirical_validation_results.csv", "module_id", "D1.1",
             "synthetic_claimed_as_empirical", "NO", "YES"),
     "run35.fault01.synthetic_not_called_empirical", "synthetic-as-empirical claim"),
    (2, "method output used as its own reference standard",
     csvcell(A / "run35_reference_standard_independence.csv", "module", "A1.7",
             "reference_derived_from_method", None, "YES - recomputed from the module's output"),
     "run35.fault02.output_not_its_own_reference", "derived from the method"),
    (3, "direct method input used as an independent reference outcome",
     csvcell(A / "run35_reference_standard_independence.csv", "module", "A1.8",
             "supports_class_A_empirical_claim", "NO", "YES"),
     "run35.fault03.direct_input_not_a_field_outcome", "claims class-A support"),
    (4, "future-period leakage into an earlier-period prediction",
     csvcell(A / "run35_reference_standard_independence.csv", "module", "A6.2",
             "independence_tests",
             "leaks future-period information into an earlier-period prediction: NO",
             "leaks future-period information into an earlier-period prediction: YES"),
     "run35.fault04.no_future_period_leakage", "does not answer the leakage test NO"),
    (5, "reference-standard independence field omitted",
     csvcell(A / "run35_reference_standard_independence.csv", "module", "A1.7", "lineage",
             None, ""),
     "run35.fault05.independence_fields_complete", "is empty"),
    (6, "partial reference standard promoted to whole-module validation",
     csvcell(A / "run35_validation_metric_contract.csv", "module_id", "A1.7",
             "component_NOT_scored", None, "nothing"),
     "run35.fault06.partial_not_promoted", "names nothing as unscored"),
    (7, "a module with no qualified reference marked empirical PASS",
     csvcell(A / "run35_empirical_validation_results.csv", "module_id", "B2.18",
             "verdict", "NOT_APPLICABLE", "PASS",
             ), "run35.fault07.no_reference_no_pass", "without an admitted reference standard"),
    (8, "an unsupported parameter applied and validation read as calibrated",
     csvcell(A / "run35_unresolved_calibration_inventory.csv", "module", "A1.1",
             "empirical_validation_interpretable", None,
             "YES - the ladder is calibrated enough to interpret"),
     "run35.fault08.applied_unsupported_not_calibrated", "applied yet called interpretable"),
    (9, "a validation threshold selected after the results were seen",
     text(HERE / "build_run35_results.py",
          "    equal = got == ref",
          "    equal = abs(float(got) - float(ref)) < 0.01"),
     "run35.fault09.no_threshold_after_results", "numeric literal"),
    (10, "the validation metric changed after the results were observed",
     csvcell(A / "run35_empirical_validation_results.csv", "module_id", "A6.2", "metric",
             None, "mean absolute error against the recorded rate"),
     "run35.fault10.metric_not_changed_after_results", "metric the contract does not declare"),
    (11, "a disabled module activated to obtain a score",
     text(S / "registry.py", '    "B4.1": "Multi-Objective Optimization",\n', ""),
     "run35.fault11.disabled_not_activated", "disabled set moved"),
    (12, "archived Quantum Probability becomes operational",
     ("multi", None, [
         csvcell(A / "run35_operational_disposition.csv", "module_id", "B2.9",
                 "run35_disposition", "ARCHIVED", "KEEP_ABSTENTION_CAPABLE"),
         csvcell(A / "run35_parsimony_reconciliation.csv", "module_id", "B2.9",
                 "proposed_disposition", "ARCHIVED", "KEEP_ABSTENTION_CAPABLE")]),
     "run35.fault12.quantum_stays_archived", "B2.9 disposition is"),
    (13, "Plithogenic Sets becomes operational",
     ("multi", None, [
         csvcell(A / "run35_operational_disposition.csv", "module_id", "B2.7",
                 "run35_disposition", "DISABLED_INSUFFICIENT_PROVENANCE",
                 "KEEP_ABSTENTION_CAPABLE"),
         csvcell(A / "run35_parsimony_reconciliation.csv", "module_id", "B2.7",
                 "proposed_disposition", "DISABLED_INSUFFICIENT_PROVENANCE",
                 "KEEP_ABSTENTION_CAPABLE")]),
     "run35.fault13.plithogenic_stays_disabled", "B2.7 disposition is"),
    (14, "Hypersoft Sets becomes operational",
     ("multi", None, [
         csvcell(A / "run35_operational_disposition.csv", "module_id", "B2.20",
                 "run35_disposition", "DISABLED_INSUFFICIENT_PROVENANCE",
                 "KEEP_ABSTENTION_CAPABLE"),
         csvcell(A / "run35_parsimony_reconciliation.csv", "module_id", "B2.20",
                 "proposed_disposition", "DISABLED_INSUFFICIENT_PROVENANCE",
                 "KEEP_ABSTENTION_CAPABLE")]),
     "run35.fault14.hypersoft_stays_disabled", "B2.20 disposition is"),
    (15, "Material Cost Variance becomes active without the required structures",
     text(S / "registry.py",
          'DISABLED_EVIDENCE_UNDER_REVIEW: dict[str, str] = {\n    "A3.4": "Material Cost '
          'Variance",\n}',
          'DISABLED_EVIDENCE_UNDER_REVIEW: dict[str, str] = {}'),
     "run35.fault15.mcv_not_active", "A3.4 activation is"),
    (16, "the voting count becomes 3",
     text(S / "registry.py", '    "A1.8",   # Variance at Completion\n})',
          '    "A1.8",   # Variance at Completion\n    "A1.9",\n})'),
     "run35.fault16.voting_is_exactly_two", "the voting set is"),
    (17, "a Category-9 qualification-gate bypass appears",
     text(S / "qualification_boundary.py", "                if not ev.eligible_for(use):",
          "                if False and not ev.eligible_for(use):"),
     "run35.fault17.category9_no_bypass", "missing-assessment bypass"),
    (18, "Category-9 quality becomes a risk vote",
     text(S / "registry.py", '    "A1.8",   # Variance at Completion\n})',
          '    "A1.8",   # Variance at Completion\n    "C1.1",\n})'),
     "run35.fault18.category9_not_a_risk_vote", "C1.1 is in the voting set"),
    (19, "a Category-10 recommendation becomes project-condition evidence",
     text(S / "models_cat10.py", '"creates_project_evidence": False,',
          '"creates_project_evidence": True,'),
     "run35.fault19.category10_creates_no_evidence", "does not deny creating project evidence"),
    (20, "a Category-10 method exercises approval authority",
     text(S / "models_cat10.py", '"human_authorization_required": True,',
          '"human_authorization_required": False,'),
     "run35.fault20.category10_no_approval_authority", "does not require human authorization"),
    (21, "duplicate lineage counted as independent confirmation",
     None,   # filled at run time: the first genuinely overlapping row
     "run35.fault21.duplicate_lineage_not_independent", "claims uniqueness"),
    (22, "unknown lineage treated as independent lineage",
     text(S / "lineage.py", "    return status == LINEAGE_ESTABLISHED_INDEPENDENT",
          "    return status in (LINEAGE_ESTABLISHED_INDEPENDENT, LINEAGE_UNRESOLVED)"),
     "run35.fault22.unknown_lineage_not_independent", "establishes independence"),
    (23, "a synthetic Portfolio Health holdout called field validation",
     csvcell(A / "run34_portfolio_health_calibration_closure.csv", "module", "D1.3",
             "layer5_real_empirical_validation", "PENDING", "FIELD_VALIDATED"),
     "run35.fault23.ph_holdout_not_field_validation", "layer 5 is no longer PENDING"),
    (24, "PH.5 receives invented equal weights",
     text(S / "canonical_v8.py",
          'applied=False,\n           note="NOT APPLIED: composite score is NONE under '
          'PARAMETER_PROVENANCE_BLOCKED."),',
          'applied=True,\n           note="NOT APPLIED: composite score is NONE under '
          'PARAMETER_PROVENANCE_BLOCKED."),'),
     "run35.fault24.ph5_no_invented_weights", "D1.5 applies UNSUPPORTED parameter"),
    (25, "PH.2 receives invented equal weights",
     text(S / "canonical_v8.py",
          'applied=False,\n           note="NOT APPLIED: without governed weights the module '
          'returns the per-feature "',
          'applied=True,\n           note="NOT APPLIED: without governed weights the module '
          'returns the per-feature "'),
     "run35.fault25.ph2_no_invented_weights", "D1.2 applies UNSUPPORTED parameter"),
    (26, "a non-validatable target omitted from the 100-row result artifact",
     ("droprow", A / "run35_empirical_validation_results.csv", ("module_id", "C1.7")),
     "run35.fault26.every_target_present", "has 99 rows"),
    (27, "NOT_APPLICABLE rewritten as PASS",
     csvcell(A / "run35_empirical_validation_results.csv", "module_id", "B3.4",
             "verdict", "NOT_APPLICABLE", "PASS"),
     "run35.fault27.not_applicable_is_not_a_pass", "no applicable metric yet verdict PASS"),
    (28, "an operational disposition with no evidence or rationale",
     csvcell(A / "run35_operational_disposition.csv", "module_id", "A2.5", "rationale",
             None, ""),
     "run35.fault28.every_disposition_has_evidence", "no substantive rationale"),
    (29, "an archived or disabled target deleted from the registry",
     ("droprow", ROOT / "p0-baseline" / "module_renumbering_map.csv", ("new_id", "B2.9")),
     "run35.fault29.nothing_deleted_from_history", "B2.9 is gone from the registry"),
    (30, "a report count disagreeing with the 100-row artifacts",
     None,   # filled at run time against the committed Run-35 report
     "run35.fault30.report_counts_match", "the report states no line carrying"),
]


# --------------------------------------------------------------------------- mechanics
def drop_pycache():
    for d in SERVER.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


def apply_csvcell(path, key_col, key, col, old, new):
    with path.open(encoding="utf-8", newline="") as fh:
        r = list(csv.DictReader(fh))
        hdr = list(r[0])
    hit = False
    for row in r:
        if row[key_col] == key:
            if old is not None and old not in row[col]:
                return False, f"the cell does not carry {old!r}"
            row[col] = row[col].replace(old, new) if old is not None else new
            hit = True
    if not hit:
        return False, f"no row keyed {key}"
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, hdr, lineterminator="\n")
        w.writeheader()
        w.writerows(r)
    return True, ""


def apply_droprow(path, key_col, key):
    with path.open(encoding="utf-8", newline="") as fh:
        r = list(csv.DictReader(fh))
        hdr = list(r[0])
    keep = [x for x in r if x[key_col] != key]
    if len(keep) == len(r):
        return False, f"no row keyed {key}"
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, hdr, lineterminator="\n")
        w.writeheader()
        w.writerows(keep)
    return True, ""


def apply_text(path, old, new):
    s = path.read_text(encoding="utf-8")
    if old not in s:
        return False, "the anchor text is not present"
    path.write_text(s.replace(old, new, 1), encoding="utf-8")
    return True, ""


def apply_one(mut):
    kind = mut[0]
    if kind == "csv":
        return apply_csvcell(mut[1], *mut[2])
    if kind == "text":
        return apply_text(mut[1], *mut[2])
    if kind == "droprow":
        return apply_droprow(mut[1], *mut[2])
    if kind == "multi":
        for sub in mut[2]:
            ok, why = apply_one(sub)
            if not ok:
                return False, why
        return True, ""
    raise ValueError(kind)


def files_of(mut):
    if mut[0] == "multi":
        out = []
        for sub in mut[2]:
            out += files_of(sub)
        return out
    return [mut[1]]


def run_guard(name):
    drop_pycache()
    p = subprocess.run([sys.executable, str(GUARD)], cwd=str(HERE), capture_output=True,
                       text=True, env={**__import__("os").environ,
                                       "PYTHONIOENCODING": "utf-8"})
    out = p.stdout + p.stderr
    if "RESULT: " not in out:
        return "CRASH", out[-400:]
    lines = [ln for ln in out.splitlines() if ln.startswith(f"FAIL  {name}")]
    return ("RED" if lines else "GREEN"), (lines[0] if lines else
                                           [ln for ln in out.splitlines()
                                            if ln.startswith("RESULT:")][0])


def main():
    # --------- late-bound mutations that need the current artifact content
    with (A / "run35_parsimony_reconciliation.csv").open(encoding="utf-8", newline="") as fh:
        par = list(csv.DictReader(fh))
    dup = next(r for r in par if r["overlap_type"].startswith(
        ("SHARED_GOVERNED_STRUCTURE", "IDENTICAL_PRIMITIVE_SOURCE_SET")))
    faults = list(FAULTS)
    faults[20] = (21, faults[20][1],
                  csvcell(A / "run35_parsimony_reconciliation.csv", "module_id",
                          dup["module_id"], "unique_analytical_contribution", "NO", "YES"),
                  faults[20][3], faults[20][4])
    reports = sorted(ROOT.glob("REPORT_*_run35-*.md"))
    if reports:
        faults[29] = (30, faults[29][1],
                      text(reports[-1], "| E `STRUCTURE_OR_DATA_ABSENT` | **96** |",
                           "| E `STRUCTURE_OR_DATA_ABSENT` | **71** |"),
                      faults[29][3], faults[29][4])
    else:
        faults[29] = (30, faults[29][1], None, faults[29][3], faults[29][4])

    drop_pycache()
    base, detail = run_guard("__baseline__")
    if base != "GREEN":
        print(f"BASELINE NOT GREEN: {detail}")
        return 1
    print(f"baseline {detail}")

    rows = []
    counts = {"applied": 0, "red": 0, "restored": 0, "not_applied": 0, "crash_as_red": 0}
    for num, desc, mut, guard, fragment in faults:
        if mut is None:
            rows.append([num, desc, "ILL_POSED_NOT_COUNTED", guard, "", "",
                         "no executable defect could be constructed for this mutation", "",
                         "NOT_COUNTED"])
            counts["not_applied"] += 1
            continue
        files = files_of(mut)
        before = {f: f.read_bytes() for f in files}
        # RESTORE IN A `finally` THAT CANNOT BE SKIPPED. Run 53 singled this campaign out: its
        # restore was straight-line code with NO `try` at all, while faults 24 and 25 target
        # server/app/simulation/canonical_v8.py through the `S / "canonical_v8.py"` join at :157
        # and :164 -- a variable join, so a path-STRING sweep of the campaigns does not see it.
        # Any raise inside run_guard() left a neutered production guard on disk.
        # Hygiene, not the fix -- see server/tools/campaign_safety.py.
        with restore_guard(before, after=drop_pycache):
            drop_pycache()
            ok, why = apply_one(mut)
            after = {f: f.read_bytes() for f in files}
            landed = ok and any(after[f] != before[f] for f in files)
            if not landed:
                rows.append([num, desc, "NOT_APPLIED", guard, "", "", why, "", "NOT_COUNTED"])
                counts["not_applied"] += 1
                print(f"fault {num:2d}  NOT_APPLIED  ({why})")
                continue
            counts["applied"] += 1
            state, detail = run_guard(guard)
            intended = state == "RED" and fragment in detail
            if state == "CRASH":
                counts["crash_as_red"] += 0     # never accepted
            if intended:
                counts["red"] += 1
        # ---- verify byte-for-byte, after the guaranteed restore above
        restored = all(f.read_bytes() == before[f] for f in files)
        state2, detail2 = run_guard(guard)
        if restored and state2 == "GREEN":
            counts["restored"] += 1
        rows.append([num, desc, "APPLIED", guard, state,
                     "YES" if intended else "NO", detail[:400],
                     "YES" if (restored and state2 == "GREEN") else "NO",
                     "COUNTED" if intended and restored and state2 == "GREEN" else "NOT_COUNTED"])
        print(f"fault {num:2d}  applied  guard {state:5s}  intended-reason "
              f"{'YES' if intended else 'NO ':3s}  restored-green "
              f"{'YES' if (restored and state2 == 'GREEN') else 'NO'}")

    with (A / "run35_fault_injection_results.csv").open("w", encoding="utf-8",
                                                        newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["fault", "failure_mode", "injection", "named_guard", "guard_state",
                    "red_for_intended_reason", "guard_output", "restored_green", "counted"])
        w.writerows(rows)
    print(f"\nfaults declared 30; applied {counts['applied']}; intended RED {counts['red']}; "
          f"restored GREEN {counts['restored']}; NOT_APPLIED {counts['not_applied']}; "
          f"crash accepted as RED {counts['crash_as_red']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
