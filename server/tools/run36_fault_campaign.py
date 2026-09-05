#!/usr/bin/env python3
"""
RUN 36 FAULT CAMPAIGN. Forty failure modes, one per item of the contract's section-24 list, each
injected into a real file, confirmed applied by re-reading the bytes from disk, and each expected
to turn ONE NAMED ORACLE in `test_run36_fault_guards.py` red for its own reason.

RULES THIS CAMPAIGN ENFORCES ON ITSELF, unchanged from Run 35's:
 * baseline must be GREEN before anything is injected;
 * an injection that does not change the bytes on disk is NOT_APPLIED and is not counted;
 * a CRASH IS NOT ACCEPTED AS RED -- the guard must print its own RESULT line and its own named
   failure, and a crashing guard is recorded as CRASH and credited to nothing;
 * a RED somewhere else is not evidence: the named oracle must be the one that fails AND its
   failure line must carry the intended-reason fragment;
 * __pycache__ is dropped on BOTH sides of every injection, because a restore inside the same
   clock second changes neither mtime nor size and a cached mutant would survive;
 * every file is restored from the bytes captured before injection and re-verified byte-for-byte,
   and the oracle must be GREEN again afterwards.

Writes code_audit/run36_fault_injection_results.csv.
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
_cs_arm(_cs_pl.Path(ROOT), "run36_fault_campaign.py",
        allow=[])
# -------------------------------------------------------------------------------------------
AUDIT = ROOT / "code_audit"
GUARD = HERE / "test_run36_fault_guards.py"
S = ROOT / "server" / "app" / "simulation"
APP = ROOT / "server" / "app"
JS = ROOT / "assets" / "js"


def text(path, old, new):
    return ("text", path, (old, new))


def textall(path, old, new):
    """Replace EVERY occurrence. An oracle that tests for ANY occurrence of a property is not
    falsified by editing only the first one, and a mutation that leaves the property in place is
    not a fault -- it is a NOT_APPLIED dressed up as one."""
    return ("textall", path, (old, new))


def csvcell(path, key_col, key, col, old, new):
    return ("csv", path, (key_col, key, col, old, new))


def droprow(path, key_col, key):
    return ("droprow", path, (key_col, key))


def duprow(path, key_col, key):
    return ("duprow", path, (key_col, key))


def addrow(path, key_col, key):
    return ("addrow", path, (key_col, key))


def touchfile(path, body):
    return ("newfile", path, (body,))


T100 = AUDIT / "run36_100_target_scientific_reaudit.csv"
QUALCSV = AUDIT / "run36_instrument_qualification.csv"
PARCSV = AUDIT / "run36_parameter_provenance_reaudit.csv"

FAULTS = [
    (1, "a scientific target removed from the 100-target inventory",
     droprow(T100, "module_id", "A2.5"),
     "run36.fault01", "a target is missing"),
    (2, "a scientific target duplicated in the inventory",
     duprow(T100, "module_id", "A2.5"),
     "run36.fault02", "a duplicate row would inflate the population"),
    (3, "a fabricated target added to the inventory",
     addrow(T100, "module_id", "Z9.9"),
     "run36.fault03", "an unregistered target is fabricated"),
    (4, "A1.1's served record claims it computes when execution says it does not",
     # REPOINTED after the owner's 2026-08-19 ruling. The original fault injected the OLD lie --
     # "conditional" over a module that computed. That string is no longer in the served record,
     # so the injection could not land. The MIRROR-IMAGE lie is injected instead, which is the
     # one the corrected oracle now guards against: claiming a disabled module computes.
     text(JS / "ds_defensibility_evidence.js",
          'operationalState: "DISABLED_INSUFFICIENT_INPUT"',
          'operationalState: "COMPUTES_FROM_AVAILABLE_EVIDENCE"'),
     "run36.fault04", "or claims to compute when it does not"),
    (5, "an unresolved parameter restored to authorize an output",
     # REPOINTED after the owner's 2026-08-19 ruling. A1.1 no longer reaches its runner at all,
     # so restoring the mc_status call site changes no emitted row and is not a fault. The
     # PROPERTY the oracle guards -- that no reachable UNSUPPORTED parameter authorizes an
     # authoritative output -- is attacked instead where it CAN now be reached: A6.2 computes on
     # the controlled corpus, carries an UNSUPPORTED ladder, and asserts no colour. Giving it one
     # is exactly the defect section 6 forbids.
     # The injection removes the DEFENCE, which is where the property actually lives: line 350
     # of models_cat89 re-asserts `row["status_color"] = None` after the update, with the comment
     # "no band is invented". A dict-level edit is overridden by it, which is the code working.
     text(S / "models_cat89.py",
          '        row["status_color"] = None          # re-asserted after the update; '
          'no band is invented',
          '        row["status_color"] = "red"         # INJECTED'),
     "run36.fault05", "no reachable UNSUPPORTED parameter authorizes an authoritative output"),
    (6, "A1.7 banded on the rounded value again",
     text(S / "models_evm.py",
          "    tcpi = remaining_work / remaining_budget\n"
          "    color = (\"Green\" if tcpi <= _TCPI_PLANNED_EFFICIENCY",
          "    tcpi = _round3(remaining_work / remaining_budget)\n"
          "    color = (\"Green\" if tcpi <= _TCPI_PLANNED_EFFICIENCY"),
     "run36.fault06", "rounding before banding is restored"),
    (7, "A1.8's analytical value replaced by its formatted output",
     text(S / "models_evm.py", '"vac": vac,', '"vac": round(vac),'),
     "run36.fault07", "replaced by its formatted output"),
    (8, "a third voter added",
     text(S / "registry.py",
          'CORE_VOTING_MODULES: frozenset[str] = frozenset({\n    "A1.7",   # TCPI',
          'CORE_VOTING_MODULES: frozenset[str] = frozenset({\n    "A1.2",   # injected third '
          'voter\n    "A1.7",   # TCPI'),
     "run36.fault08", "a third voter has been added"),
    (9, "the Category-9 gate name withdrawn so nothing can be refused for a missing assessment",
     text(APP / "simulation" / "qualification_contract.py",
          'ASSESSMENT_MISSING = "CATEGORY9_ASSESSMENT_MISSING"',
          'ASSESSMENT_MISSING = "CATEGORY9_ASSESSMENT_PRESENT"'),
     "run36.fault09", "the gate is bypassed"),
    (10, "Category 9 made a contributor to project status",
     text(S / "compute.py", 'def contributes_to_project_status(group: str) -> bool:',
          'def contributes_to_project_status(group: str) -> bool:\n    return True  # noqa'),
     "run36.fault10", "it has become a risk vote"),
    (11, "Category-10 output made human-authoritative",
     text(S / "canonical_v7.py", '"human_authorization_required": True',
          '"human_authorization_required": False'),
     "run36.fault11", "exercises no approval authority"),
    (12, "Category-10 output fed back as project evidence",
     text(S / "canonical_v7.py", '"creates_project_evidence": False',
          '"creates_project_evidence": True'),
     "run36.fault12", "a feedback loop into upstream project evidence has been opened"),
    (13, "Material Cost Variance reactivated",
     textall(S / "registry.py", '    "A3.4": "Material Cost Variance",\n', ''),
     "run36.fault13", "it has been reactivated"),
    (14, "Plithogenic Sets reactivated",
     text(S / "registry.py", '"B2.7": "Plithogenic Sets",', ''),
     "run36.fault14", "it has been reactivated"),
    (15, "Hypersoft Sets reactivated",
     text(S / "registry.py", '"B2.20": "Hypersoft Sets",', ''),
     "run36.fault15", "it has been reactivated"),
    (16, "Quantum Probability made operational",
     text(S / "registry.py", '"B2.9": "Quantum Probability",', ''),
     "run36.fault16", "it has been reactivated"),
    (17, "the PH.1 synthetic threshold declared a project-status band",
     text(S / "canonical_v8.py", '"is_project_status_band": False',
          '"is_project_status_band": True'),
     "run36.fault17", "it has been applied on the wrong schema"),
    (18, "a small cohort allowed to produce an authoritative flag",
     text(S / "canonical_v8.py", "NO authoritative anomaly flag is produced",
          "An authoritative anomaly flag is produced"),
     "run36.fault18", "carries an explicit limitation rather than an authoritative flag"),
    (19, "PH.2 equal weights invented",
     textall(S / "canonical_v8.py", "composite is NONE", "composite is EQUALLY WEIGHTED"),
     "run36.fault19", "equal weights have been invented"),
    (20, "PH.3 trajectory allowed from two observations",
     text(S / "canonical_v8.py", "MIN_TRAJECTORY_OBSERVATIONS = 3",
          "MIN_TRAJECTORY_OBSERVATIONS = 2"),
     "run36.fault20", "a trajectory from two observations is allowed"),
    (21, "the PH.4 0.15 radius restored",
     text(S / "canonical_v8.py", "No match threshold is applied",
          "A match threshold of 0.15 is applied"),
     "run36.fault21", "the radius has been restored"),
    (22, "PH.5 weights invented",
     textall(S / "canonical_v8.py", "PARAMETER_PROVENANCE_BLOCKED",
          "PARAMETER_PROVENANCE_ASSUMED"),
     "run36.fault22", "rather than a composite under invented weights"),
    (23, "PH.5 duplicate lineage reinforced",
     textall(S / "canonical_v8.py", 'relative_distance', 'reldistdup'),
     "run36.fault23", "does not reinforce a project's score by counting one lineage twice"),
    (24, "unknown lineage treated as independent lineage",
     csvcell(T100, "module_id", "A2.5", "lineage", None, "LINEAGE_ESTABLISHED_INDEPENDENT"),
     "run36.fault24", "unknown lineage is being treated as independent"),
    (25, "a conditional method described as unconditionally computing",
     text(JS / "ds_defensibility_evidence.js",
          '"A1.3": { name: "Bayesian EAC", implementation: "the canonical production runner '
          'exists, but execution requires a named defining structure; when that structure is '
          'absent the module returns Not Estimable", '
          'operationalState: "CONDITIONAL_ON_GOVERNED_STRUCTURE"',
          '"A1.3": { name: "Bayesian EAC", implementation: "the current production runner '
          'computes the canonical method from the governed evidence the platform already holds", '
          'operationalState: "COMPUTES_FROM_AVAILABLE_EVIDENCE"'),
     "run36.fault25", "no conditional method is described as unconditionally computing"),
    (26, "a disabled method described as active",
     text(JS / "ds_defensibility_evidence.js",
          'operationalState: "DISABLED_CONCEPT_ONLY"',
          'operationalState: "COMPUTES_FROM_AVAILABLE_EVIDENCE"'),
     "run36.fault26", "no disabled method is described as active"),
    (27, "a second taxonomy authority created",
     text(JS / "categories.js", "build_client_taxonomy.py", "hand_maintained_second_authority"),
     "run36.fault27", "a second authority exists"),
    (28, "a stale proxy qualifier restored, naming a disabled module",
     text(S / "registry.py", 'PROXY_QUALIFIERS: dict[str, str] = {',
          'PROXY_QUALIFIERS: dict[str, str] = {\n    "B2.7": "a stale qualifier", '),
     "run36.fault28", "a stale qualifier has been restored"),
    (29, "the client method-class lookup broken",
     text(JS / "categories.js", 'case "Monte_Carlo":', 'case "Monte_Carlo_BROKEN":'),
     "run36.fault29", "statuses silently never render"),
    (30, "recursion introduced in the participant taxonomy path",
     text(JS / "taxonomy.js", "/* GENERATED BLOCK. Do not edit by hand.",
          "function methodClassStatus(x){ return methodClassStatus(x); }\n"
          "/* GENERATED BLOCK. Do not edit by hand."),
     "run36.fault30", "recursion has been introduced"),
    (31, "the preliminary lock broken",
     text(APP / "research_decision.py",
          '"preliminary judgment is already locked and cannot be resubmitted"',
          '"preliminary judgment may be resubmitted"'),
     "run36.fault31", "the lock has been broken"),
    (32, "the AI package revealed before the preliminary lock",
     text(APP / "research_models.py",
          '"reveal_at IS NULL OR (pre_locked_at IS NOT NULL AND pre_locked_at <= reveal_at)"',
          '"reveal_at IS NULL OR reveal_at IS NOT NULL"'),
     "run36.fault32", "the reveal has been let through early"),
    (33, "a final response edited after the final lock",
     text(APP / "research_decision.py",
          '"a final decision has already been recorded for this assignment"',
          '"a final decision may be amended for this assignment"'),
     "run36.fault33", "the refusal has been removed"),
    (34, "the ordered project-period sequence removed so a period can be skipped",
     textall(APP / "research_assignment.py", "ConditionSequence", "ConditionSeqRemoved"),
     "run36.fault34", "none may be skipped"),
    (35, "the participant experimental sequence altered",
     text(JS / "workspace.js", "\n", "\n/* run36 sequence mutation probe */\n"),
     "run36.fault35", "the sequence has been altered"),
    (36, "the evidence and rationale capture omitted",
     text(APP / "research_decision.py", 'decision.rationale = payload.get("rationale")',
          'pass  # rationale not captured'),
     "run36.fault36", "capture has been omitted"),
    (37, "a sealed predecessor package record rewritten in place",
     text(AUDIT / "run33_participant_package_v11_checksums.sha256",
          "# OPUS GUBERNATIO PARTICIPANT PACKAGE og-participant-2026.08-v11",
          "# OPUS GUBERNATIO PARTICIPANT PACKAGE og-participant-2026.08-v11 (rewritten)"),
     "run36.fault37", "has been rewritten in place"),
    (38, "synthetic laboratory calibration recorded as empirical field validation",
     csvcell(T100, "module_id", "D1.1", "empirical_validation_class",
             None, "EMPIRICALLY_VALIDATABLE_NOW"),
     "run36.fault38", "recorded as empirical field validation"),
    (39, "a target with no evidence to score promoted to a bounded-use pass",
     csvcell(QUALCSV, "module_id", "A2.5", "final_qualification",
             None, "QUALIFIED_FOR_BOUNDED_STUDY_USE"),
     "run36.fault39", "NOT_APPLICABLE is being read as PASS"),
    (40, "a freeze candidate created while a blocking defect remains",
     # REPOINTED after the owner's 2026-08-19 ruling closed the A1.1 blocking defect. Creating
     # the manifest alone is no longer a violation, because nothing is blocking: the gate would
     # be right to stay green. The fault must therefore inject a BLOCKING DEFECT and the manifest
     # TOGETHER, which is what actually tests the gate rather than the file's absence.
     ("multi", None, (
         csvcell(T100, "module_id", "A2.5", "blocking_defect", None,
                 "YES - injected for fault 40"),
         touchfile(ROOT / "research" / "freeze" / "INSTRUMENT_FREEZE_CANDIDATE_MANIFEST.json",
                   '{"label": "FREEZE_CANDIDATE", "injected_by": "run36 fault 40"}\n'))),
     "run36.fault40", "the freeze gate has been opened with a defect standing"),
]


def drop_pycache():
    for d in ROOT.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


def _read_csv(path):
    with path.open(encoding="utf-8", newline="") as fh:
        r = list(csv.DictReader(fh))
    return r, list(r[0]) if r else []


def _write_csv(path, hdr, r):
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, hdr, lineterminator="\n")
        w.writeheader()
        w.writerows(r)


def apply_one(mut):
    kind, path = mut[0], mut[1]
    if kind == "multi":
        for sub in mut[2]:
            ok, why = apply_one(sub)
            if not ok:
                return False, why
        return True, ""
    if kind in ("text", "textall"):
        old, new = mut[2]
        s = path.read_text(encoding="utf-8")
        if old not in s:
            return False, "the anchor text is not present"
        path.write_text(s.replace(old, new, 1 if kind == "text" else -1), encoding="utf-8")
        return True, ""
    if kind == "csv":
        key_col, key, col, old, new = mut[2]
        r, hdr = _read_csv(path)
        hit = False
        for row in r:
            if row[key_col] == key:
                if old is not None and old not in row[col]:
                    return False, f"the cell does not carry {old!r}"
                row[col] = row[col].replace(old, new) if old is not None else new
                hit = True
        if not hit:
            return False, f"no row keyed {key}"
        _write_csv(path, hdr, r)
        return True, ""
    if kind == "droprow":
        key_col, key = mut[2]
        r, hdr = _read_csv(path)
        keep = [x for x in r if x[key_col] != key]
        if len(keep) == len(r):
            return False, f"no row keyed {key}"
        _write_csv(path, hdr, keep)
        return True, ""
    if kind == "duprow":
        key_col, key = mut[2]
        r, hdr = _read_csv(path)
        hits = [x for x in r if x[key_col] == key]
        if not hits:
            return False, f"no row keyed {key}"
        _write_csv(path, hdr, r + [dict(hits[0])])
        return True, ""
    if kind == "addrow":
        key_col, key = mut[2]
        r, hdr = _read_csv(path)
        fake = {k: "" for k in hdr}
        fake[key_col] = key
        for k in ("voting", "blocking_defect", "lineage", "empirical_validation_class"):
            if k in fake:
                fake[k] = {"voting": "NO", "blocking_defect": "NO",
                           "lineage": "LINEAGE_UNRESOLVED",
                           "empirical_validation_class": "STRUCTURE_OR_DATA_ABSENT"}[k]
        _write_csv(path, hdr, r + [fake])
        return True, ""
    if kind == "newfile":
        (body,) = mut[2]
        if path.exists():
            return False, "the file already exists, so creating it proves nothing"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return True, ""
    raise ValueError(kind)


def run_guard(name):
    drop_pycache()
    p = subprocess.run([sys.executable, str(GUARD)], cwd=str(HERE), capture_output=True,
                       text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    out = p.stdout + p.stderr
    if "RESULT: " not in out:
        # A CRASH IS NOT A RED. It is its own state and it is credited to nothing.
        return "CRASH", out[-400:]
    lines = [ln for ln in out.splitlines() if ln.startswith(f"FAIL  {name}")]
    result = [ln for ln in out.splitlines() if ln.startswith("RESULT:")][0]
    return ("RED" if lines else "GREEN"), (lines[0] if lines else result)


def main():
    drop_pycache()
    base, detail = run_guard("__baseline__")
    if base != "GREEN":
        print(f"BASELINE NOT GREEN, refusing to run the campaign: {detail}")
        return 1
    print(f"baseline {detail}\n")

    rows = []
    counts = {"applied": 0, "red": 0, "restored": 0, "not_applied": 0, "crash_as_red": 0,
              "crashed": 0}
    def _targets(mut):
        if mut[0] == "multi":
            out = []
            for sub in mut[2]:
                out += _targets(sub)
            return out
        return [(mut[1], mut[0] == "newfile")]

    for num, desc, mut, guard, fragment in FAULTS:
        targets = _targets(mut)
        saved = {p: (None if created else p.read_bytes()) for p, created in targets}
        path, created = targets[0]
        before = saved[path]
        drop_pycache()
        ok, why = apply_one(mut)
        landed = ok and any((p.exists() if c else p.read_bytes() != saved[p])
                            for p, c in targets)
        if not landed:
            for p, c in targets:
                if c:
                    if p.exists():
                        p.unlink()
                elif saved[p] is not None:
                    p.write_bytes(saved[p])
            drop_pycache()
            rows.append([num, desc, "NOT_APPLIED", guard, "", "", why, "", "NOT_COUNTED"])
            counts["not_applied"] += 1
            print(f"fault {num:2d}  NOT_APPLIED  ({why})")
            continue
        counts["applied"] += 1
        # RUN 55, PHASE B. THE RESTORE IS IN A `finally`. It was a bare loop after
        # run_guard(), so a raise there left every mutated file on disk. Run 53
        # established that the next campaign then snapshots the corruption and cements it
        # with its own correct restore. The arm() guard is the fix; this is the hygiene.
        try:
            state, detail = run_guard(guard)
            intended = state == "RED" and fragment in detail
            if state == "CRASH":
                counts["crashed"] += 1
            if intended:
                counts["red"] += 1
        finally:
            for p, c in targets:
                if c:
                    if p.exists():
                        p.unlink()
                else:
                    p.write_bytes(saved[p])
        drop_pycache()
        restored = all((not p.exists()) if c else p.read_bytes() == saved[p]
                       for p, c in targets)
        state2, detail2 = run_guard(guard)
        good = restored and state2 == "GREEN"
        if good:
            counts["restored"] += 1
        rows.append([num, desc, "APPLIED", guard, state, "YES" if intended else "NO",
                     detail[:400], "YES" if good else "NO",
                     "COUNTED" if intended and good else "NOT_COUNTED"])
        print(f"fault {num:2d}  applied  guard {state:5s}  intended-reason "
              f"{'YES' if intended else 'NO ':3s}  restored-green {'YES' if good else 'NO'}")

    with (artifact_out(AUDIT / "run36_fault_injection_results.csv")).open("w", encoding="utf-8",
                                                            newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["fault", "failure_mode", "injection", "named_guard", "guard_state",
                    "red_for_intended_reason", "guard_output", "restored_green", "counted"])
        w.writerows(rows)
    counted = len([r for r in rows if r[8] == "COUNTED"])
    print(f"\nfaults declared {len(FAULTS)}; applied {counts['applied']}; "
          f"intended RED {counts['red']}; restored GREEN {counts['restored']}; "
          f"NOT_APPLIED {counts['not_applied']}; guards that CRASHED {counts['crashed']}; "
          f"crash accepted as RED 0; COUNTED {counted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
