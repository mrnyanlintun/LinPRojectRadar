#!/usr/bin/env python3
"""
RUN 34. THE REQUIRED 20-FAULT CALIBRATION CAMPAIGN.

Baseline GREEN; mutation APPLIED and CONFIRMED APPLIED by reading it back; a NAMED GUARD RED for
the intended reason; restore; caches cleared; baseline GREEN again. A crash is reported as a
CRASH and scored ZERO -- it is not a RED.

THE SHAPE TO WATCH FOR, which cost six faults a first pass in Run 33's campaign: a "mutation"
that changes only the INPUT while the property genuinely holds is not a fault injection. Every
fault below either mutates PRODUCTION SOURCE or mutates a GOVERNED ARTEFACT that production
actually reads, so that what the guard names really changes.

THREE FAULTS GUARD THE PROTOCOL DISCIPLINE ITSELF rather than any single method -- 4, 19 and 20 --
and they are the reason the protocol was committed before the campaign was written: without that
ordering there would be nothing for them to check.

Writes code_audit/run34_fault_injection_results.csv.
"""

from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

# ---------------------------------------------------------------------------------------------
# RUN 135C. RETIRED ARTEFACT. This script is kept for the record and is NOT executed.
#
# Ruling R4 requires a retired artefact to be retired EXPLICITLY rather than left to crash. Its
# subject is D1.1,D1.2,D1.3,D1.4 -- 4 module ids removed from the registry at Run 96 or Run 97 and no module
# in service -- so there is nothing here for it to qualify. Before this guard it died with
# campaign_safety.CampaignTreeDirty: tree dirty at start of run34 20-fault calibration campaign:  M REPORT_2026-08-14_run27-98-module-remediation-matrix
# which prints no RESULT line and reads, in a scan of fleet output, exactly like a clean run.
#
# It exits 0 with the line below rather than raising, so a fleet run records a retirement rather
# than a crash, and tools/TOOLS_CLASSIFICATION.csv excludes it from qualification coverage.
# Delete the guard to run it again; expect it to fail, because the modules it measures are gone.
import sys as _sys135c
print("RETIRED: test_run34_fault_campaign.py measures D1.1,D1.2,D1.3,D1.4, removed at Run 96/97 (88e6ca0); excluded from qualification coverage "
      "by tools/TOOLS_CLASSIFICATION.csv")
_sys135c.exit(0)
# ---------------------------------------------------------------------------------------------

import csv
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
ROOT = _HERE.parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / "tools"))

from campaign_safety import arm, snapshot_text   # noqa: E402

OUT = ROOT / "code_audit" / "run34_fault_injection_results.csv"
FX5 = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.5" / "package_D_portfolio_health")
FX6 = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.6"
       / "package_D_portfolio_calibration")
V8_SRC = "server/app/simulation/canonical_v8.py"
PROTOCOL = "research/methodology/run34_portfolio_calibration_protocol.md"
CAMPAIGN = "server/tools/run34_ph1_tree_count_calibration.py"
GENERATOR = "server/tools/build_run34_calibration_fixtures.py"

REQUIRED = 20
PASSED = FAILED = 0
FAILURES: list[str] = []
ROWS = [["fault", "target", "mutation", "applied", "confirmed_applied", "guard", "intended_red",
         "crash_accepted_as_red", "restored_green", "result"]]
APPLIED = REDS = RESTORED = CRASHES = 0


def check(ok, label, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}" + (f"  [{detail}]" if detail else ""))
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  FAIL  {label}  [{detail}]")
    return bool(ok)


def head(t):
    print("\n" + "=" * 94 + f"\n{t}\n" + "=" * 94)


def drop_pycache():
    for d in (ROOT / "server").rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


PROBE_HEAD = """
import json, sys, pathlib
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[1] + "/tools")
def emit(d):
    print("VERDICT" + json.dumps(d, default=str))
try:
"""
PROBE_TAIL = """
except Exception as exc:                                              # noqa: BLE001
    emit({"ok": False, "crash": repr(exc)})
"""


def run_probe(body, arg=""):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        src = (PROBE_HEAD + "\n".join("    " + ln for ln in body.strip("\n").splitlines())
               + "\n" + PROBE_TAIL)
        (tmp / "probe.py").write_text(src, encoding="utf-8")
        r = subprocess.run([sys.executable, str(tmp / "probe.py"), str(ROOT / "server"), arg],
                           capture_output=True, text=True,
                           env={"PYTHONIOENCODING": "utf-8", "PATH": "/usr/bin:/bin",
                                "PYTHONDONTWRITEBYTECODE": "1"})
    for line in r.stdout.splitlines():
        if line.startswith("VERDICT"):
            return json.loads(line[len("VERDICT"):])
    return {"ok": False, "crash": f"no verdict (rc={r.returncode}) {r.stderr[-400:]}"}


def fault(n, target, path, edits, mutation, guard_name, guard, body, arg=""):
    """One fault against a FILE the platform reads: production source, or a governed artefact."""
    global APPLIED, REDS, RESTORED, CRASHES
    f = ROOT / path
    # Snapshot from the COMMITTED bytes at HEAD, never from disk. A disk snapshot taken after
    # an earlier leak captures the corruption and the restore then cements it.
    original = snapshot_text(ROOT, path)
    drop_pycache()
    base = run_probe(body, arg)
    green = check(base.get("ok") is True and guard(base) is True,
                  f"F{n} GREEN BEFORE: {guard_name}", str(base.get("crash", ""))[:140])
    applied = confirmed = red = crash = False
    try:
        bad = [o for o, _ in edits if original.count(o) != 1]
        if bad:
            check(False, f"F{n} NOT APPLIED: a mutation anchor is not unique in {path}",
                  str(len(bad)))
        else:
            mutated = original
            for o, nw in edits:
                mutated = mutated.replace(o, nw, 1)
            f.write_text(mutated, encoding="utf-8")
            drop_pycache()
            applied = True
            back = f.read_text(encoding="utf-8")
            confirmed = check(back != original and all(nw in back for _, nw in edits),
                              f"F{n} INJECTION CONFIRMED: read back from disk, not assumed",
                              f"{len(edits)} edit(s)")
            got = run_probe(body, arg)
            if got.get("ok") is False:
                crash = True
                check(False, f"F{n} CRASHED rather than failing a guard -- NOT counted as RED",
                      str(got.get("crash"))[:200])
            else:
                red = check(guard(got) is False, f"F{n} RED for the intended reason: {guard_name}",
                            json.dumps({k: v for k, v in got.items() if k != "ok"})[:150])
    finally:
        f.write_text(original, encoding="utf-8")
        drop_pycache()
    after = run_probe(body, arg)
    restored = check(f.read_text(encoding="utf-8") == original and after.get("ok") is True
                     and guard(after) is True,
                     f"F{n} RESTORED GREEN: file byte-identical, guard green again")
    APPLIED += 1 if applied else 0
    REDS += 1 if red else 0
    RESTORED += 1 if restored else 0
    CRASHES += 1 if crash else 0
    ROWS.append([str(n), target, mutation, "YES" if applied else "NO",
                 "YES" if confirmed else "NO", guard_name, "YES" if red else "NO",
                 "YES" if crash else "NO", "YES" if restored else "NO",
                 "PASS" if (green and applied and confirmed and red and restored and not crash)
                 else "FAIL"])


PH1 = str(FX5 / "ph1_isolation_forest_fixture.json")
PH2 = str(FX5 / "ph2_midrank_percentile_fixture.json")
PH3 = str(FX5 / "ph3_trajectory_slope_fixture.json")
PH4 = str(FX5 / "ph4_nearest_neighbour_fixture.json")
PH5 = str(FX5 / "ph5_component_profile_fixture.json")
CALFX = str(FX6 / "run34_ph1_calibration_labelled.json")

RUN = '''
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
run = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], fx["feature_records"],
                                  fx.get("histories", []))
'''


# =================================================================================================
# THE START GUARD. A campaign must not begin on a dirty tree: it would snapshot the corruption,
# faithfully restore it, and then CERTIFY it. See server/tools/campaign_safety.py.
arm(ROOT, "run34 20-fault calibration campaign", allow=[OUT])

# =================================================================================================
head("FAULTS 1-5: PH.1 THRESHOLD, COHORT SIZE, AND MODEL IDENTITY")
# =================================================================================================

fault(1, "PH.1 frozen threshold, schema binding", V8_SRC,
      [('                if (cohort.schema_version == RUN15_FROZEN_SCHEMA\n'
        '                    and _band == COHORT_CANONICAL) else None),',
        '                if _band == COHORT_CANONICAL else None),')],
      "the frozen Run-15 threshold is applied under ANY feature schema, so a laboratory "
      "threshold fitted on one representation of a project flags projects under another",
      "no exploratory flag is derived from the frozen synthetic threshold under a schema that is "
      "not the one it was fitted on",
      lambda v: v.get("flags") == ["None"] and v.get("schema") != v.get("frozen_schema"),
      RUN + '''
d = run["results"]["cat8_1_isolation_forest"]
emit({"ok": True, "schema": d["cohort"]["feature_schema_version"],
      "frozen_schema": V8.RUN15_FROZEN_SCHEMA,
      "flags": sorted({str(p["exploratory_flag"]) for p in d["projects"].values()})})
''', PH1)

# THE MUTATION IS v21's OWN GATE, restored. Setting the minimum to zero instead would make a
# one-project cohort reach `IsolationForest`, which raises -- and a crash is NOT a RED, so the
# campaign would have scored nothing. The two-project case is the one that discriminates: it runs
# on both sides, and only the correct gate refuses it.
fault(2, "PH.1 cohort-size policy, n < 3", V8_SRC,
      [("    if n < MIN_COHORT_FOR_RANKING:\n        return COHORT_BELOW_MINIMUM, (",
        "    if n < 2:\n        return COHORT_BELOW_MINIMUM, (")],
      "the minimum cohort for a cross-project anomaly model is lowered back to v21's two, so a "
      "two-project cohort is scored although each project is the other's entire reference "
      "population",
      "a cohort of two eligible projects is NOT_ESTIMABLE and produces no score",
      lambda v: v.get("two") == "NOT_ESTIMABLE" and v.get("two_scores") == 0,
      '''
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
recs = fx["feature_records"][:2]
c = dict(fx["cohort"], project_ids=[r["project_id"] for r in recs])
d = V8.compute_portfolio_health(c, fx["feature_schema"], recs, [])["results"][
    "cat8_1_isolation_forest"]
emit({"ok": True, "two": d.get("disposition"), "two_scores": len(d.get("projects") or {})})
''', PH1)

fault(3, "PH.1 small-cohort authoritative flag", V8_SRC,
      [('        "authoritative_flag_permitted": _band == COHORT_CANONICAL\n'
        '        and cohort.schema_version == RUN15_FROZEN_SCHEMA,',
        '        "authoritative_flag_permitted": True,')],
      "a small cohort is declared to permit an authoritative anomaly flag, although no "
      "calibration protocol establishes one at that cohort size",
      "a cohort below the canonical size does not permit an authoritative flag, and its "
      "limitation record says so",
      lambda v: v.get("permitted") is False and v.get("limitation_permitted") is False
      and v.get("band") == "COHORT_SMALL",
      '''
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
recs = fx["feature_records"][:4]
c = dict(fx["cohort"], project_ids=[r["project_id"] for r in recs])
d = V8.compute_portfolio_health(c, fx["feature_schema"], recs, [])["results"][
    "cat8_1_isolation_forest"]
emit({"ok": True, "band": d.get("cohort_size_class"),
      "permitted": d.get("authoritative_flag_permitted"),
      "limitation_permitted": d["limitation"]["authoritative_flag_permitted"]})
''', PH1)

# FAULT 4 GUARDS THE PROTOCOL ORDERING ITSELF. The campaign records that selection completed
# before the holdout was read; the mutation makes the holdout artefact claim the opposite.
fault(4, "the protocol ordering (tree-count selection vs holdout inspection)",
      "code_audit/run34_ph1_holdout_result.csv",
      [("ORDERING,-,selection_completed_before_holdout_read,YES",
        "ORDERING,-,selection_completed_before_holdout_read,NO")],
      "the recorded ordering is inverted: the artefact now says the tree count was selected "
      "AFTER the holdout was inspected, which is exactly the post-hoc selection the protocol "
      "prohibits",
      "the campaign records that selection completed BEFORE the holdout was read, and the "
      "selected tree count is the published default rather than a value fitted to the holdout",
      lambda v: v.get("ordering") == "YES" and v.get("selected") == "100",
      '''
import csv as _csv, pathlib as _p
root = _p.Path(sys.argv[1]).parent
h = list(_csv.DictReader(open(root / "code_audit/run34_ph1_holdout_result.csv")))
t = list(_csv.DictReader(open(root / "code_audit/run34_ph1_tree_count_calibration.csv")))
ordering = next((r["value"] for r in h
                 if r["metric"] == "selection_completed_before_holdout_read"), None)
selected = next((r["value"] for r in t if r["metric"] == "selected_tree_count"), None)
emit({"ok": True, "ordering": ordering, "selected": selected})
''')

fault(5, "PH.1 cross-cohort comparability", V8_SRC,
      [('            if str(raw["feature_schema_version"]) != self.schema_version:',
        "            if False:")],
      "the feature-schema check is disabled, so members written under two different schemas -- "
      "and therefore scored by two different models -- enter one cohort and are ranked as one "
      "scale",
      "a member on a different feature schema is refused, so scores from different cohort/model "
      "identities are never compared as one scale",
      lambda v: v.get("rejected") is True,
      '''
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
recs = [dict(fx["feature_records"][0], feature_schema_version="OTHER")] + fx["feature_records"][1:]
d = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], recs, [])["results"][
    "cat8_1_isolation_forest"]
emit({"ok": True, "rejected": bool(d.get("abstained"))
      and "feature schema" in (d.get("abstention_reason") or "")})
''', PH1)


# =================================================================================================
head("FAULTS 6-8: PH.2 ORIENTATION, WEIGHTS AND BANDS")
# =================================================================================================

fault(6, "PH.2 orientation declaration", V8_SRC,
      # THE COERCION MUST BE COMPLETE, or the fault is caught for the wrong reason: leaving the
      # invalid string in place and only disabling the vocabulary check still refuses downstream,
      # because an unrecognised orientation is not in the rankable set either. The defect being
      # modelled is a silent DEFAULT, so the mutation defaults.
      [('        orientation = str(raw["orientation"])\n'
        "        if orientation not in ORIENTATIONS:",
        "        orientation = raw['orientation'] if raw.get('orientation') in ORIENTATIONS \\\n"
        "            else HIGHER_IS_MORE_ADVERSE\n"
        "        if False:")],
      "an orientation that is not one of the declared vocabulary is silently coerced to "
      "higher-is-worse, so a feature nobody validly oriented is ranked anyway -- and a "
      "lower-is-worse feature would read exactly backwards",
      "a feature whose declared orientation is not in the governed vocabulary is refused; no "
      "orientation is defaulted or inferred",
      lambda v: v.get("refused") is True,
      '''
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
sch = {"version": fx["feature_schema"]["version"],
       "features": [dict(f, orientation="PROBABLY_WORSE_WHEN_HIGHER")
                    for f in fx["feature_schema"]["features"]]}
try:
    run = V8.compute_portfolio_health(fx["cohort"], sch, fx["feature_records"], [])
    d = run["results"]["cat8_2_portfolio_outlier"]
    refused = bool(d.get("abstained"))
except V8.StructureAbsent:
    refused = True
emit({"ok": True, "refused": refused})
''', PH2)

fault(7, "PH.2 weight policy", V8_SRC,
      [("    if weights is None:\n"
        '        return None, ("No governed feature weights were supplied, so NO COMPOSITE IS '
        'PRODUCED. "',
        "    if weights is None:\n"
        "        return {fid: Fraction(1, len(feature_ids)) for fid in feature_ids}, (\n"
        '            "No governed feature weights were supplied, so NO COMPOSITE IS PRODUCED. "')],
      "equal weights appear as a DEFAULT when no governed weight set was supplied, so a "
      "composite nobody authorised the weighting of is emitted anyway",
      "absent governed weights, PH.2 emits NO composite and returns the per-feature percentile "
      "profile under PARAMETER_PROVENANCE_BLOCKED",
      lambda v: v.get("composites") == ["None"]
      and v.get("disposition") == "PARAMETER_PROVENANCE_BLOCKED"
      and v.get("weights") is None,
      RUN + '''
d = run["results"]["cat8_2_portfolio_outlier"]
emit({"ok": True, "disposition": d.get("disposition"),
      "weights": d.get("composite_weights"),
      "composites": sorted({str(p["portfolio_outlier_percentile"])
                            for p in d["projects"].values()})})
''', PH2)

fault(8, "PH.2 status bands", V8_SRC,
      [('        "status_bands": None,\n        "features_ranked": [f.feature_id for f in feats],',
        '        "status_bands": {"Red": 0.15, "Amber": 0.30, "Yellow": 0.45},\n'
        '        "status_color": "Red",\n'
        '        "features_ranked": [f.feature_id for f in feats],')],
      "the removed percentile-to-status colour mapping is restored, with no governed calibration "
      "dataset and no predeclared decision objective behind it",
      "PH.2 declares no status bands and emits no status colour",
      lambda v: v.get("bands") is None and v.get("has_color") is False,
      RUN + '''
d = run["results"]["cat8_2_portfolio_outlier"]
emit({"ok": True, "bands": d.get("status_bands"), "has_color": "status_color" in d})
''', PH2)


# =================================================================================================
head("FAULTS 9-11: PH.3 HISTORY, TIME BASIS AND TOLERANCE")
# =================================================================================================

fault(9, "PH.3 minimum observations", V8_SRC,
      # TWO ANCHORS. The minimum-count gate and the distinct-times gate both refuse a
      # two-point history, so moving one alone leaves the property standing and the campaign
      # would credit a fault it had not proved.
      [("    if len(times) < MIN_TRAJECTORY_OBSERVATIONS:\n        raise PortfolioAbstention(\n"
        '            f"NOT_ESTIMABLE: {len(times)} observation(s) of {signal_id!r}; at least "',
        "    if len(times) < 2:\n        raise PortfolioAbstention(\n"
        '            f"NOT_ESTIMABLE: {len(times)} observation(s) of {signal_id!r}; at least "'),
       ("    if len(set(times)) < MIN_TRAJECTORY_OBSERVATIONS:",
        "    if len(set(times)) < 2:")],
      "two observations are accepted as a trajectory, although two points determine a line "
      "exactly and carry no evidence that the line is a trend",
      "a history of two observations is refused: at least three are required before a trend is "
      "fitted",
      lambda v: v.get("two_refused") is True and v.get("three_ok") is True,
      '''
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
base = [h for h in fx["histories"] if h["project_id"] == "P-EVEN"][0]
c = {"cohort_id": "C", "portfolio_id": "P", "project_ids": ["P-EVEN"], "period": "2026-01",
     "inclusion_rule": "a", "exclusion_rule": "n", "feature_schema_version": "s",
     "qualification_policy": "q", "model_version": "m"}
sch = {"version": "s", "features": [{"feature_id": "f", "label": "f", "units": "u",
       "orientation": "HIGHER_IS_MORE_ADVERSE", "scaling_rule": "n", "missingness_rule": "a",
       "source_module": "t", "qualification_requirement": "c"}]}
rec = [{"project_id": "P-EVEN", "cohort_id": "C", "period": "2026-01", "values": {"f": 1.0},
        "qualification_state": "QUALIFIED", "missing_fields": [], "invalid_fields": [],
        "source_lineage": "L", "source_provenance": "P", "feature_schema_version": "s"}]


def cls(nobs):
    h = [dict(base, observations=base["observations"][:nobs])]
    d = V8.compute_portfolio_health(c, sch, rec, h)["results"]["cat8_3_trajectory_classifier"]
    return d


two = cls(2)
three = cls(3)
emit({"ok": True, "two_refused": bool(two.get("abstained")),
      "three_ok": not three.get("abstained")})
''', PH3)

fault(10, "PH.3 time basis", V8_SRC,
      [("    pairs = sorted(zip(times, values))\n"
        "    b = ols_slope([t for t, _ in pairs], [x for _, x in pairs])",
        "    pairs = sorted(zip(times, values))\n"
        "    b = ols_slope([Fraction(i) for i in range(len(pairs))],\n"
        "                  [x for _, x in pairs])")],
      "unequally spaced reporting dates are treated as equally spaced: the slope is fitted "
      "against the position index instead of the actual reporting time",
      "an unequally spaced history is fitted against its ACTUAL reporting times, so its slope "
      "per day differs from the slope over positions 0, 1, 2",
      lambda v: v.get("irregular_slope") != v.get("position_slope"),
      '''
from fractions import Fraction
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
irr = [h for h in fx["histories"] if h["project_id"] == "P-IRREGULAR"][0]
c = {"cohort_id": "C", "portfolio_id": "P", "project_ids": ["P-IRREGULAR"], "period": "2026-01",
     "inclusion_rule": "a", "exclusion_rule": "n", "feature_schema_version": "s",
     "qualification_policy": "q", "model_version": "m"}
sch = {"version": "s", "features": [{"feature_id": "f", "label": "f", "units": "u",
       "orientation": "HIGHER_IS_MORE_ADVERSE", "scaling_rule": "n", "missingness_rule": "a",
       "source_module": "t", "qualification_requirement": "c"}]}
rec = [{"project_id": "P-IRREGULAR", "cohort_id": "C", "period": "2026-01", "values": {"f": 1.0},
        "qualification_state": "QUALIFIED", "missing_fields": [], "invalid_fields": [],
        "source_lineage": "L", "source_provenance": "P", "feature_schema_version": "s"}]
d = V8.compute_portfolio_health(c, sch, rec, [irr])["results"]["cat8_3_trajectory_classifier"]
body = d["projects"]["P-IRREGULAR"][0]
# The position-index slope, computed independently here from the same values.
vals = [Fraction(str(o["value"])) for o in irr["observations"]]
ts = [Fraction(i) for i in range(len(vals))]
tb = sum(ts, Fraction(0)) / len(ts)
xb = sum(vals, Fraction(0)) / len(vals)
num = sum(((t - tb) * (x - xb) for t, x in zip(ts, vals)), Fraction(0))
den = sum(((t - tb) ** 2 for t in ts), Fraction(0))
emit({"ok": True, "irregular_slope": body["ols_slope_exact"],
      "position_slope": f"{(num/den).numerator}/{(num/den).denominator}",
      "equally_spaced": body["equally_spaced"]})
''', PH3)

fault(11, "PH.3 numerical tolerance", V8_SRC,
      [("NUMERICAL_ZERO = Fraction(1, 10 ** 12)", "NUMERICAL_ZERO = Fraction(5, 100)")],
      "the floating-point zero tolerance is inflated into an operational magnitude band: a real "
      "adverse slope of 0.01 per day would now be reported STABLE",
      "the tolerance is numerical only -- a genuine non-zero slope is classified by its sign and "
      "no magnitude of slope is graded",
      lambda v: v.get("small_slope_class") == "DETERIORATING" and v.get("bands") is None,
      '''
from app.simulation import canonical_v8 as V8
c = {"cohort_id": "C", "portfolio_id": "P", "project_ids": ["P"], "period": "2026-01",
     "inclusion_rule": "a", "exclusion_rule": "n", "feature_schema_version": "s",
     "qualification_policy": "q", "model_version": "m"}
sch = {"version": "s", "features": [{"feature_id": "f", "label": "f", "units": "u",
       "orientation": "HIGHER_IS_MORE_ADVERSE", "scaling_rule": "n", "missingness_rule": "a",
       "source_module": "t", "qualification_requirement": "c"}]}
rec = [{"project_id": "P", "cohort_id": "C", "period": "2026-01", "values": {"f": 1.0},
        "qualification_state": "QUALIFIED", "missing_fields": [], "invalid_fields": [],
        "source_lineage": "L", "source_provenance": "P", "feature_schema_version": "s"}]
h = [{"project_id": "P", "signal_id": "s1", "units": "ratio",
      "orientation": "HIGHER_IS_MORE_ADVERSE", "source": "t", "history_version": "h",
      "observations": [{"reporting_time": t, "value": v, "qualification_state": "QUALIFIED"}
                       for t, v in ((0, 1.00), (1, 1.01), (2, 1.02))]}]
d = V8.compute_portfolio_health(c, sch, rec, h)["results"]["cat8_3_trajectory_classifier"]
b = d["projects"]["P"][0]
emit({"ok": True, "small_slope_class": b["classification"], "bands": b["magnitude_bands"]})
''')


# =================================================================================================
head("FAULTS 12-14: PH.4 RADIUS, SCHEMA AND ORDERING")
# =================================================================================================

fault(12, "PH.4 match radius", V8_SRC,
      [('        "match_threshold": None,', '        "match_threshold": 0.15,')],
      "the retired unvalidated 0.15 radius reappears as an operational threshold",
      "PH.4 applies NO match threshold and reports the continuous relationship only",
      lambda v: v.get("threshold") is None,
      RUN + '''
d = run["results"]["cat8_4_cross_project_pattern"]
emit({"ok": True, "threshold": d.get("match_threshold")})
''', PH4)

fault(13, "PH.4 schema comparability", V8_SRC,
      [('            if str(raw["feature_schema_version"]) != self.schema_version:',
        "            if False:")],
      "a member on a different feature schema, and therefore a different normalization version, "
      "is accepted into the cohort and compared by distance",
      "a schema mismatch is refused, so no distance is computed across incompatible feature "
      "representations",
      lambda v: v.get("rejected") is True,
      '''
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
recs = [dict(fx["feature_records"][0], feature_schema_version="OTHER")] + fx["feature_records"][1:]
d = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], recs, [])["results"][
    "cat8_4_cross_project_pattern"]
emit({"ok": True, "rejected": bool(d.get("abstained"))
      and "feature schema" in (d.get("abstention_reason") or "")})
''', PH4)

fault(14, "PH.4 ordering invariance", V8_SRC,
      [("        nearest = sorted(q for q in peers if dists[q] == best)",
        "        nearest = [q for q in peers if dists[q] == best][:1]"),
       ('        self.members.sort(key=lambda m: m["project_id"])',
        "        pass  # members left in arrival order"),
       ("        peers = sorted(q for q in ids if q != pid)      # SELF-MATCH EXCLUDED",
        "        peers = [q for q in ids if q != pid]")],
      "the declared tie rule and the stable member ordering are both dropped, so the nearest "
      "neighbour a project is given depends on the order its record happened to arrive in",
      "every nearest-neighbour set and distance is identical whichever order the records arrive "
      "in",
      lambda v: v.get("order_independent") is True,
      '''
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())


def key(recs):
    d = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], recs,
                                    [])["results"]["cat8_4_cross_project_pattern"]
    return {p: [b["nearest_neighbour_project_ids"], round(b["distance"], 12)]
            for p, b in d["projects"].items()}


emit({"ok": True, "order_independent":
      key(fx["feature_records"]) == key(list(reversed(fx["feature_records"])))})
''', PH4)


# =================================================================================================
head("FAULTS 15-18: PH.5 WEIGHTS, MISSINGNESS, LINEAGE AND THE SCALAR")
# =================================================================================================

fault(15, "PH.5 weight provenance", V8_SRC,
      [('        "governed_missingness_policy": None,\n        "weights": None,',
        '        "governed_missingness_policy": None,\n'
        '        "weights": {"D1.1": 0.25, "D1.2": 0.25, "D1.3": 0.25, "D1.4": 0.25},'),
       ('        "governed_weights_supplied": weights is not None,\n'
        '        "governed_missingness_policy": None,\n        "weights":',
        '        "governed_weights_supplied": True,\n'
        '        "governed_missingness_policy": None,\n        "weights":')],
      "equal constituent weights appear with no governed weight record behind them",
      "PH.5 reports no weights and does not claim governed weights were supplied when none were",
      lambda v: v.get("weights") is None and v.get("claimed") is False,
      RUN + '''
d = run["results"]["cat8_5_anomaly_score"]
emit({"ok": True, "weights": d.get("weights"), "claimed": d.get("governed_weights_supplied")})
''', PH5)

fault(16, "PH.5 missingness policy", V8_SRC,
      [('            "governed_missingness_policy": None,\n'
        '            "missingness_policy_note": (',
        '            "governed_missingness_policy": "RENORMALISE_OVER_PRESENT",\n'
        '            "missingness_policy_note": (')],
      "a missingness policy is asserted that would renormalise the composite over whichever "
      "constituents happen to be present, silently reweighting the remainder",
      "no governed missingness policy exists, and PH.5 says so rather than adopting one",
      lambda v: v.get("policies") == ["None"],
      RUN + '''
d = run["results"]["cat8_5_anomaly_score"]
emit({"ok": True,
      "policies": sorted({str(p.get("governed_missingness_policy"))
                          for p in d["projects"].values()})})
''', PH5)

fault(17, "PH.5 duplicate lineage", V8_SRC,
      [('        bodies = sorted({(c["cohort_id"], c["feature_schema_version"], c["period"])\n'
        "                         for c in present.values()})",
        "        bodies = sorted(present)"),
       ('            "corroboration_established": False,',
        '            "corroboration_established": len(present) > 2,')],
      "the evidence-body count is replaced by a count of CONSTITUENTS and corroboration is "
      "derived from it, so the same result offered twice reads as two supporting observations",
      "offering the same constituent twice does not raise the evidence-body count and does not "
      "establish corroboration",
      lambda v: v.get("bodies_unchanged") is True and v.get("no_corroboration") is True,
      '''
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
run = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], fx["feature_records"],
                                  fx.get("histories", []))["results"]
c = V8.PortfolioCohort(fx["cohort"], fx["feature_schema"], fx["feature_records"])
honest = V8.anomaly_profile(c, None, {"D1.1": run["cat8_1_isolation_forest"],
                                      "D1.2": run["cat8_2_portfolio_outlier"],
                                      "D1.3": run["cat8_3_trajectory_classifier"],
                                      "D1.4": run["cat8_4_cross_project_pattern"]})
dup = V8.anomaly_profile(c, None, {"D1.1": run["cat8_1_isolation_forest"],
                                   "D1.2": run["cat8_1_isolation_forest"],
                                   "D1.3": run["cat8_3_trajectory_classifier"],
                                   "D1.4": run["cat8_4_cross_project_pattern"]})
emit({"ok": True,
      "bodies_unchanged": all(dup["projects"][p]["distinct_evidence_bodies"]
                              == honest["projects"][p]["distinct_evidence_bodies"]
                              for p in honest["projects"]),
      "no_corroboration": all(b["corroboration_established"] is False
                              for b in dup["projects"].values())})
''', PH5)

fault(18, "PH.5 blocked scalar", V8_SRC,
      [('        "score": None,\n        "score_blocked_reason": _blocked_reason,',
        '        "score": 0.61,\n        "score_blocked_reason": _blocked_reason,')],
      "a numeric composite is emitted while the disposition still says the parameter provenance "
      "is blocked",
      "PH.5 emits no scalar while its disposition is PARAMETER_PROVENANCE_BLOCKED",
      lambda v: v.get("score") is None and v.get("disposition") == "PARAMETER_PROVENANCE_BLOCKED",
      RUN + '''
d = run["results"]["cat8_5_anomaly_score"]
emit({"ok": True, "score": d.get("score"), "disposition": d.get("disposition")})
''', PH5)


# =================================================================================================
head("FAULTS 19-20: THE CALIBRATION BOUNDARY AND THE PROTOCOL DISCIPLINE")
# =================================================================================================

fault(19, "the synthetic/empirical boundary", "research_fixtures/synthetic/OG-SYNTH-0.6/"
      "package_D_portfolio_calibration/run34_ph1_calibration_labelled.json",
      [('"data_origin": "SYNTHETIC_RESEARCH_CALIBRATION"',
        '"data_origin": "EMPIRICAL_FIELD_VALIDATION"'),
       ('"not_for_empirical_validation": true', '"not_for_empirical_validation": false')],
      "the calibration fixture relabels itself as empirical field validation, which would make a "
      "generated separation statistic read as evidence about real projects",
      "every calibration fixture declares data_origin SYNTHETIC_RESEARCH_CALIBRATION, "
      "not_for_empirical_validation true, and ground truth defined before the detector",
      lambda v: v.get("origin") == "SYNTHETIC_RESEARCH_CALIBRATION"
      and v.get("not_for_validation") is True and v.get("gt_first") is True,
      '''
import json as _j, pathlib as _p
root = _p.Path(sys.argv[1]).parent
f = _j.loads((root / "research_fixtures/synthetic/OG-SYNTH-0.6/"
              "package_D_portfolio_calibration/run34_ph1_calibration_labelled.json"
              ).read_text())
emit({"ok": True, "origin": f.get("data_origin"),
      "not_for_validation": f.get("not_for_empirical_validation"),
      "gt_first": f.get("ground_truth_defined_before_detector")})
''')

# FAULT 20 GUARDS THE HOLDOUT ITSELF. The mutation makes the calibration dataset AND the holdout
# dataset the same dataset, which is the reuse the protocol prohibits.
fault(20, "the holdout independence", GENERATOR,
      [('HOLDOUT_SEED = 340002', 'HOLDOUT_SEED = 340001')],
      "the holdout generator seed is set equal to the calibration seed, so the 'holdout' is the "
      "same draw as the calibration set and parameter selection would be evaluated on the data "
      "it was chosen from",
      "the calibration and holdout datasets are independent draws: different generator seeds and "
      "different feature values for the same project index",
      lambda v: v.get("seeds_differ") is True and v.get("values_differ") is True,
      '''
import json as _j, pathlib as _p, re as _re
root = _p.Path(sys.argv[1]).parent
src = (root / "server/tools/run34_ph1_tree_count_calibration.py").read_text()
gen = (root / "server/tools/build_run34_calibration_fixtures.py").read_text()
cal_seed = int(_re.search(r"CALIBRATION_SEED = (\\d+)", gen).group(1))
hold_seed = int(_re.search(r"HOLDOUT_SEED = (\\d+)", gen).group(1))
c = _j.loads((root / "research_fixtures/synthetic/OG-SYNTH-0.6/"
              "package_D_portfolio_calibration/run34_ph1_calibration_labelled.json").read_text())
h = _j.loads((root / "research_fixtures/synthetic/OG-SYNTH-0.6/"
              "package_D_portfolio_calibration/run34_ph1_holdout_labelled.json").read_text())
emit({"ok": True, "seeds_differ": cal_seed != hold_seed,
      "values_differ": c["feature_records"][0]["values"] != h["feature_records"][0]["values"]})
''')


# =================================================================================================
head("CAMPAIGN TOTALS")
# =================================================================================================
_rows = ROWS[1:]
check(len(_rows) == REQUIRED, f"faults required = {REQUIRED}; recorded = {len(_rows)}",
      str(len(_rows)))
check(APPLIED == REQUIRED, f"applied = {APPLIED}", f"NOT_APPLIED = {REQUIRED - APPLIED}")
check(REDS == REQUIRED, f"intended RED = {REDS}", str(REDS))
check(RESTORED == REQUIRED, f"restored GREEN = {RESTORED}", str(RESTORED))
check(CRASHES == 0, f"crashes accepted as RED = {CRASHES}", str(CRASHES))
check(all(r[-1] == "PASS" for r in _rows), "every fault row PASSES")
ROWS.append(["TOTALS", "-", "-", str(APPLIED), "-", "-", str(REDS), str(CRASHES), str(RESTORED),
             "PASS" if (APPLIED == REDS == RESTORED == REQUIRED and CRASHES == 0) else "FAIL"])
with artifact_out(OUT).open("w", encoding="utf-8", newline="") as fh:
    csv.writer(fh, lineterminator="\n").writerows(ROWS)
print(f"\nwrote {OUT.relative_to(ROOT)}")

print()
print("=" * 94)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print("  -", f)
sys.exit(1 if FAILED else 0)
